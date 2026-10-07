"""Offline regression coverage for opt-in changelog exclusions."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_release_notes as builder


REPO_URL = "https://github.com/canonical/example"


def commit(sha="abc", title="docs: Improve the guide", author=None, committer=None):
    return {
        "sha": sha, "commit": {"message": title},
        "author": {"login": author} if author else None,
        "committer": {"login": committer} if committer else None,
    }


def pr(number=42, title="docs: Improve the guide", author="human", labels=()):
    return {
        "number": number, "html_url": f"{REPO_URL}/pull/{number}",
        "title": title, "body": "", "merged_at": "2026-01-01T00:00:00Z",
        "user": {"login": author}, "labels": [{"name": name} for name in labels],
    }


def run_policy(monkeypatch, commits, prs, *, docs=False, renovate=False, paths=None, total=None):
    policy = builder.ExclusionPolicy(Mock(), "canonical", "example", docs, renovate)
    if paths is not None:
        monkeypatch.setattr(builder, "github_get", lambda *_: {"changed_files": total if total is not None else len(paths)})
        monkeypatch.setattr(builder, "github_get_paginated", lambda *_: paths)
        monkeypatch.setattr(policy, "_commit_details", lambda commit: (
            policy.file_cache.setdefault(f"commit:{commit['sha']}", ("commit files are docs-only", None)),
            (commit, None),
        )[1])
    categories = builder.build_entries(commits, prs, True, REPO_URL, policy)
    return policy, categories


def count(categories):
    return sum(len(entries) for entries in categories.values())


def test_default_off_does_not_fetch_files(monkeypatch):
    monkeypatch.setattr(builder, "github_get", lambda *_: pytest.fail("Unexpected metadata request"))
    entries = builder.build_entries([commit()], {"abc": [pr(labels=("documentation",))]}, True, REPO_URL)
    assert entries["Other improvements"][0]["message"] == "docs: Improve the guide"


@pytest.mark.parametrize("paths", [
    [{"filename": "docs/conf.py"}, {"filename": "docs/assets/nav.js"}],
    [{"filename": "README.md"}, {"filename": "docs/tutorial.rst"}],
    [{"filename": "documentation/diagram.svg"}, {"filename": "release-notes/1.md"}],
])
def test_proven_docs_paths_are_removed(monkeypatch, paths):
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr()]}, docs=True, paths=paths)
    assert count(entries) == 0
    assert policy.excluded[0]["reasons"][0]["rule"] == "docs"
    assert policy.excluded[0]["pr_url"] == f"{REPO_URL}/pull/42"


@pytest.mark.parametrize("paths", [
    [{"filename": "docs/guide.md"}, {"filename": "src/charm.py"}],
    [{"filename": "renovate.json"}],
    [{"filename": "docs/new.md", "status": "renamed", "previous_filename": "src/old.py"}],
    [{"filename": "docs/new.md", "status": "renamed"}],
])
def test_mixed_or_unproven_paths_are_kept(monkeypatch, paths):
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr(labels=("documentation",))]}, docs=True, paths=paths)
    assert count(entries) == 1
    assert not policy.excluded
    assert len(policy.retained_for_review) == 1


def test_pr_file_count_must_be_complete(monkeypatch):
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr()]}, docs=True,
                                 paths=[{"filename": "docs/guide.md"}], total=2)
    assert count(entries) == 1
    assert "incomplete" in policy.retained_for_review[0]["review_reason"]


def test_pr_file_cap_fails_open_without_pagination_request(monkeypatch):
    monkeypatch.setattr(builder, "github_get", lambda *_: {"changed_files": 3000})
    monkeypatch.setattr(builder, "github_get_paginated", lambda *_: pytest.fail("Cannot trust capped list"))
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr()]}, docs=True)
    assert count(entries) == 1
    assert "cap" in policy.retained_for_review[0]["review_reason"]


def test_failed_file_lookup_keeps_entry(monkeypatch):
    monkeypatch.setattr(builder, "github_get", lambda *_: (_ for _ in ()).throw(ValueError("bad response")))
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr()]}, docs=True)
    assert count(entries) == 1
    assert "bad response" in policy.retained_for_review[0]["review_reason"]


def test_pr_net_docs_diff_does_not_hide_non_docs_commit(monkeypatch):
    policy = builder.ExclusionPolicy(Mock(), "canonical", "example", True, False)
    monkeypatch.setattr(builder, "github_get", lambda *_: {"changed_files": 1})
    monkeypatch.setattr(builder, "github_get_paginated", lambda *_: [{"filename": "docs/guide.md"}])
    monkeypatch.setattr(policy, "_commit_details", lambda change: (
        policy.file_cache.setdefault(f"commit:{change['sha']}", (None, None)),
        (change, None),
    )[1])
    entries = builder.build_entries([commit()], {"abc": [pr()]}, True, REPO_URL, policy)
    assert count(entries) == 1
    assert "non-doc" in policy.retained_for_review[0]["review_reason"]


def test_commit_only_docs_uses_paginated_commit_files(monkeypatch):
    response = Mock()
    response.json.return_value = {"files": [{"filename": "doc/how-to.md"}]}
    response.links = {}
    get = Mock(return_value=response)
    monkeypatch.setattr(builder, "_get_with_retry", get)
    policy, entries = run_policy(monkeypatch, [commit()], {}, docs=True)
    assert count(entries) == 0
    assert get.call_args.args[1].endswith("/commits/abc")
    assert policy.excluded[0]["pr_url"] is None


def test_commit_only_missing_file_data_fails_open(monkeypatch):
    response = Mock()
    response.json.return_value = {"commit": {"message": "docs"}}
    response.links = {}
    monkeypatch.setattr(builder, "_get_with_retry", lambda *_args, **_kwargs: response)
    policy, entries = run_policy(monkeypatch, [commit()], {}, docs=True)
    assert count(entries) == 1
    assert "missing" in policy.retained_for_review[0]["review_reason"]


def test_commit_only_pagination_is_followed(monkeypatch):
    first = Mock()
    first.json.return_value = {"files": [{"filename": "docs/a.md"}]}
    first.links = {"next": {"url": "https://api.github.com/next"}}
    second = Mock()
    second.json.return_value = {"files": [{"filename": "docs/b.md"}]}
    second.links = {}
    get = Mock(side_effect=[first, second])
    monkeypatch.setattr(builder, "_get_with_retry", get)
    policy, entries = run_policy(monkeypatch, [commit()], {}, docs=True)
    assert count(entries) == 0
    assert get.call_count == 2
    assert get.call_args.args[1] == "https://api.github.com/next"


def test_commit_only_cap_with_next_page_is_kept(monkeypatch):
    response = Mock()
    response.json.return_value = {"files": [{"filename": "docs/a.md"}] * 300}
    response.links = {"next": {"url": "https://api.github.com/next"}}
    monkeypatch.setattr(builder, "_get_with_retry", lambda *_args, **_kwargs: response)
    policy, entries = run_policy(monkeypatch, [commit()], {}, docs=True)
    assert count(entries) == 1
    assert "cap" in policy.retained_for_review[0]["review_reason"]


@pytest.mark.parametrize("login", ["renovate[bot]", "renovate-bot"])
def test_renovate_pr_removed_even_if_security(monkeypatch, login):
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr(title="deps: Fix CVE-2026-12345", author=login,
                                                              labels=("Security",))]}, renovate=True)
    assert count(entries) == 0
    assert policy.excluded[0]["reasons"][0]["rule"] == "renovate"


def test_human_renovate_configuration_is_kept(monkeypatch):
    policy, entries = run_policy(monkeypatch, [commit(title="Migrate Renovate config")],
                                 {"abc": [pr(title="Migrate Renovate config")]}, renovate=True)
    assert count(entries) == 1
    assert "Renovate" in policy.retained_for_review[0]["title"]


@pytest.mark.parametrize("author,committer,excluded", [
    ("renovate[bot]", "renovate[bot]", True),
    ("renovate[bot]", "human", False),
    ("renovate[bot]", None, False),
    (None, "renovate[bot]", False),
    (None, None, False),
])
def test_commit_only_renovate_requires_unambiguous_login(monkeypatch, author, committer, excluded):
    response = Mock()
    response.json.return_value = {
        **commit(author=author, committer=committer),
        "commit": {"message": "deps: update", "verification": {"verified": True, "reason": "valid"}},
        "files": [{"filename": "requirements.txt"}],
    }
    response.links = {}
    monkeypatch.setattr(builder, "_get_with_retry", lambda *_args, **_kwargs: response)
    policy, entries = run_policy(monkeypatch, [commit(author=author, committer=committer)], {}, renovate=True)
    assert count(entries) == (0 if excluded else 1)
    assert bool(policy.excluded) is excluded


def test_unsigned_commit_only_bot_login_is_not_enough(monkeypatch):
    response = Mock()
    response.json.return_value = {
        **commit(author="renovate[bot]", committer="renovate[bot]"),
        "files": [{"filename": "requirements.txt"}],
    }
    response.links = {}
    monkeypatch.setattr(builder, "_get_with_retry", lambda *_args, **_kwargs: response)
    policy, entries = run_policy(monkeypatch, [commit(author="renovate[bot]", committer="renovate[bot]")],
                                 {}, renovate=True)
    assert count(entries) == 1
    assert not policy.excluded


def test_selected_pr_is_same_for_title_and_exclusion(monkeypatch):
    commits = [commit()]
    prs = {"abc": [pr(author="human", title="Fix user-facing issue"),
                   pr(number=43, author="renovate[bot]", title="deps: update") ]}
    policy, entries = run_policy(monkeypatch, commits, prs, renovate=True)
    assert count(entries) == 1
    assert entries["Other improvements"][0]["message"] == "Fix user-facing issue"
    assert not policy.excluded


def test_reused_pr_files_are_fetched_once_but_commit_entries_are_counted(monkeypatch):
    get = Mock(return_value={"changed_files": 1})
    files = Mock(return_value=[{"filename": "docs/a.md"}])
    monkeypatch.setattr(builder, "github_get", get)
    monkeypatch.setattr(builder, "github_get_paginated", files)
    commits = [commit("abc"), commit("def")]
    policy = builder.ExclusionPolicy(Mock(), "canonical", "example", True, False)
    monkeypatch.setattr(policy, "_commit_details", lambda change: (
        policy.file_cache.setdefault(f"commit:{change['sha']}", ("commit files are docs-only", None)),
        (change, None),
    )[1])
    entries = builder.build_entries(commits, {"abc": [pr()], "def": [pr()]}, True, REPO_URL, policy)
    assert count(entries) == 0
    assert len(policy.excluded) == 2
    assert get.call_count == files.call_count == 1


def test_combined_filters_record_both_reasons(monkeypatch):
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr(author="renovate[bot]")]},
                                 docs=True, renovate=True, paths=[{"filename": "docs/a.md"}])
    assert count(entries) == 0
    assert [reason["rule"] for reason in policy.excluded[0]["reasons"]] == ["renovate", "docs"]


def test_renovate_only_does_not_fetch_file_details(monkeypatch):
    monkeypatch.setattr(builder, "github_get", lambda *_: pytest.fail("Unexpected file lookup"))
    policy, entries = run_policy(monkeypatch, [commit()], {"abc": [pr(author="renovate[bot]")]},
                                 renovate=True)
    assert count(entries) == 0
    assert len(policy.excluded) == 1


def test_cli_report_and_stdout_are_independent(monkeypatch, tmp_path, capsys):
    template = tmp_path / "draft.md.j2"
    template.write_text("{% for items in categories.values() %}{% for entry in items %}{{ entry.message }}\n{% endfor %}{% endfor %}")
    report_path = tmp_path / "audit.json"
    monkeypatch.setattr(builder, "_build_session", lambda *_: Mock())
    monkeypatch.setattr(builder, "get_commits_between", lambda *_: ([commit()], False))
    monkeypatch.setattr(builder, "get_prs_for_commit", lambda *_: [pr(author="renovate[bot]")])
    builder.main(["--repo", "canonical/example", "--from-ref", "old", "--to-ref", "new",
                  "--template", str(template), "--exclude-renovate", "--exclusions-report", str(report_path)])
    out = capsys.readouterr()
    data = json.loads(report_path.read_text())
    assert data["counts"] == {"raw_entries": 1, "kept_entries": 0, "excluded_entries": 1}
    assert data["filters"] == {"docs": False, "renovate": True}
    assert "Excluded" not in out.out
    assert "[info] Excluded" in out.err
    assert data["excluded"][0]["commit_url"].endswith("/commit/abc")


def test_failed_pr_lookup_prevents_commit_only_filter(monkeypatch, tmp_path):
    template = tmp_path / "draft.md.j2"
    template.write_text("{% for items in categories.values() %}{% for entry in items %}{{ entry.message }}{% endfor %}{% endfor %}")
    report_path = tmp_path / "audit.json"
    monkeypatch.setattr(builder, "_build_session", lambda *_: Mock())
    monkeypatch.setattr(builder, "get_commits_between", lambda *_: ([commit()], False))
    monkeypatch.setattr(builder, "get_prs_for_commit", lambda *_: (_ for _ in ()).throw(
        builder.requests.HTTPError("unavailable")))
    monkeypatch.setattr(builder, "github_get", lambda *_: pytest.fail("Filtering must fail open"))
    builder.main(["--repo", "canonical/example", "--from-ref", "old", "--to-ref", "new",
                  "--template", str(template), "--exclude-docs", "--exclude-renovate",
                  "--exclusions-report", str(report_path)])
    report = json.loads(report_path.read_text())
    assert report["counts"]["kept_entries"] == 1
    assert "associated-PR lookup failed" in report["retained_for_review"][0]["review_reason"]


def test_unfiltered_cli_has_no_report_or_extra_requests(monkeypatch, tmp_path):
    template = tmp_path / "draft.md.j2"
    template.write_text("{% for items in categories.values() %}{% for entry in items %}{{ entry.message }}{% endfor %}{% endfor %}")
    session = Mock()
    monkeypatch.setattr(builder, "_build_session", lambda *_: session)
    monkeypatch.setattr(builder, "get_commits_between", lambda *_: ([commit()], False))
    monkeypatch.setattr(builder, "get_prs_for_commit", lambda *_: [pr()])
    builder.main(["--repo", "canonical/example", "--from-ref", "old", "--to-ref", "new",
                  "--template", str(template)])
    session.get.assert_not_called()
    assert not list(tmp_path.glob("*.json"))


def test_base_template_omits_filtered_empty_category():
    root = Path(builder.__file__).resolve().parent
    rendered = builder.render_template(str(root / "templates/base.md.j2"), {
        "title": "Test", "date": "Oct 07, 2026", "repo_url": REPO_URL,
        "from_ref": "old", "to_ref": "new", "categories": {},
        "category_order": builder.CATEGORY_ORDER, "exclude_docs": True,
    })
    assert "### Other improvements" not in rendered


@pytest.mark.parametrize("exclude_docs", [False, True])
def test_spark_docs_placeholder_only_without_docs_filter(exclude_docs):
    root = Path(builder.__file__).resolve().parent
    rendered = builder.render_template(str(root / "templates/spark.md.j2"), {
        "title": "Test", "date": "Oct 07, 2026", "repo_url": REPO_URL,
        "from_ref": "old", "to_ref": "new", "categories": {},
        "category_order": builder.CATEGORY_ORDER, "exclude_docs": exclude_docs,
    })
    assert ("## Documentation improvements" in rendered) is not exclude_docs
