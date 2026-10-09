"""Non-interactive review report status and no-overwrite contract."""

import json

import pytest

from tools.review_report import save_page, save_report, validate_report


def report(status="review_required", blockers=None, markdown_path="notes.md"):
    return {
        "schema_version": 1, "mode": "autopilot", "status": status,
        "scope_source": "file: components.txt", "product": "Kafka", "track": "4",
        "components": [{
            "name": "Kafka", "repo": "canonical/kafka-operator", "tag_namespace": "kafka",
            "from_ref": "rev1", "from_sha": "a" * 40,
            "to_ref": "rev2", "to_sha": "b" * 40,
            "entries": {"raw": 2, "kept": 2, "excluded": 0, "deduplicated": 0},
            "exclusions": [], "evidence": ["notes.md"],
        }],
        "discovered_not_included": [], "blockers": blockers or [],
        "checks": [{"name": name, "result": "pass"} for name in
               ("scope", "range", "completeness", "autolinks", "docs")],
        "markdown_path": markdown_path, "human_review_required": True,
    }


def test_review_required_and_blocked_statuses(tmp_path):
    page_report = report()
    save_report(page_report, tmp_path / "review.json")
    assert json.loads((tmp_path / "review.json").read_text()) == page_report
    blocked = report("blocked", [{"reason": "unknown repo", "component": "UI"}], None)
    save_report(blocked, tmp_path / "blocked.json")
    assert json.loads((tmp_path / "blocked.json").read_text())["status"] == "blocked"


def test_existing_report_is_never_overwritten(tmp_path):
    path = tmp_path / "report.json"
    path.write_text("original")
    with pytest.raises(FileExistsError):
        save_report(report(), path)
    assert path.read_text() == "original"


@pytest.mark.parametrize("bad", [
    {"status": "review_required", "blockers": [{"reason": "missing ref"}]},
    {"status": "blocked", "blockers": []},
    {"human_review_required": False}, {"components": [{}]},
    {"markdown_path": None},
    {"checks": [{"name": "autolinks", "result": "skipped"}]},
    {"checks": [{"name": "autolinks", "result": "pass"}]},
    {"components": []},
])
def test_invalid_or_misleading_report_is_rejected(bad):
    data = report()
    data.update(bad)
    with pytest.raises(ValueError):
        validate_report(data)


def test_review_required_rejects_unresolved_component():
    data = report()
    data["components"][0]["to_sha"] = None
    with pytest.raises(ValueError, match="unresolved"):
        validate_report(data)


def test_page_save_keeps_frontmatter_and_never_overwrites(tmp_path):
    page = tmp_path / "revision-2.md"
    text = "---\nmyst: true\n---\n<!--\nAUTOPILOT STATUS: REVIEW REQUIRED\n-->\n# Revision 2\n"
    save_page(text, page, "review_required")
    assert page.read_text() == text
    with pytest.raises(FileExistsError):
        save_page(text, page, "review_required")
    assert page.read_text() == text


@pytest.mark.parametrize("text", ["# Revision 2", "---\nmyst: true\n# Revision 2",
                                       "<!-- no status -->\n# Revision 2"])
def test_page_save_requires_review_comment(text, tmp_path):
    with pytest.raises(ValueError):
        save_page(text, tmp_path / "revision-2.md", "review_required")


def test_page_and_json_status_must_agree(tmp_path):
    text = "<!--\nAUTOPILOT STATUS: REVIEW REQUIRED\n-->\n# Revision 2\n"
    with pytest.raises(ValueError, match="match"):
        save_page(text, tmp_path / "revision-2.md", "blocked")


def test_entry_counts_must_reconcile():
    data = report()
    data["components"][0]["entries"]["raw"] = 3
    with pytest.raises(ValueError, match="reconcile"):
        validate_report(data)