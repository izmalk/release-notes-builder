"""Validate and save a machine-readable release-notes review report.

The agent assembles the evidence; this helper checks the handoff contract and
refuses to replace an existing report. A report is not release approval.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


STATUSES = {"review_required", "blocked", "error"}
REQUIRED = {
    "schema_version", "status", "mode", "scope_source", "product", "track",
    "components", "discovered_not_included", "blockers", "checks", "markdown_path",
    "human_review_required",
}
REQUIRED_CHECKS = {"scope", "range", "completeness", "autolinks", "docs"}


def validate_report(report: dict) -> None:
    missing = REQUIRED - report.keys()
    if missing:
        raise ValueError(f"missing report fields: {', '.join(sorted(missing))}")
    if report["schema_version"] != 1 or report["mode"] != "autopilot":
        raise ValueError("expected schema_version 1 and mode 'autopilot'")
    if report["status"] not in STATUSES or report["human_review_required"] is not True:
        raise ValueError("invalid status or missing human review requirement")
    for key in ("components", "discovered_not_included", "blockers", "checks"):
        if not isinstance(report[key], list):
            raise ValueError(f"{key} must be a list")
    if report["status"] == "review_required" and report["blockers"]:
        raise ValueError("review_required cannot have unresolved blockers")
    if report["status"] == "review_required" and not report["markdown_path"]:
        raise ValueError("review_required needs a review page")
    if report["status"] == "review_required" and (
        {item.get("name") for item in report["checks"] if isinstance(item, dict)}
        < REQUIRED_CHECKS or any(
            not isinstance(check, dict) or check.get("result") != "pass"
            for check in report["checks"]
        )
    ):
        raise ValueError("review_required needs passing checks")
    if report["status"] == "blocked" and not report["blockers"]:
        raise ValueError("blocked status requires at least one blocker")
    if report["status"] == "review_required" and not report["components"]:
        raise ValueError("review_required needs at least one verified component")
    if report["markdown_path"] is not None and not isinstance(report["markdown_path"], str):
        raise ValueError("markdown_path must be a path string or null")
    for number, check in enumerate(report["checks"], 1):
        if (not isinstance(check, dict) or not check.get("name")
                or check.get("result") not in {"pass", "fail", "skipped"}):
            raise ValueError(f"check {number} needs a name and pass/fail/skipped result")
    for number, item in enumerate(report["components"], 1):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError(f"component {number} needs a name")
        for key in ("repo", "tag_namespace", "from_ref", "from_sha", "to_ref",
                    "to_sha", "entries", "exclusions", "evidence"):
            if key not in item:
                raise ValueError(f"component {number} missing {key}")
        if report["status"] == "review_required" and not all(
            item[key] for key in ("repo", "from_ref", "from_sha", "to_ref", "to_sha")
        ):
            raise ValueError(f"component {number} has an unresolved repo or ref")
        if not isinstance(item["entries"], dict) or any(
            type(item["entries"].get(key)) is not int or item["entries"][key] < 0
            for key in ("raw", "kept", "excluded", "deduplicated")
        ):
            raise ValueError(f"component {number} needs nonnegative entry counts")
        counts = item["entries"]
        if counts["raw"] != counts["kept"] + counts["excluded"] + counts["deduplicated"]:
            raise ValueError(f"component {number} entry counts do not reconcile")
        if not isinstance(item["exclusions"], list) or not isinstance(item["evidence"], list):
            raise ValueError(f"component {number} needs exclusions and evidence lists")
        if report["status"] == "review_required" and not item["evidence"]:
            raise ValueError(f"component {number} has no source evidence")


def save_report(report: dict, path: Path) -> None:
    validate_report(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def save_page(text: str, path: Path, status: str) -> None:
    """Save a staged review page without replacing any existing document."""
    if not text.strip() or status not in {"blocked", "review_required"}:
        raise ValueError("autopilot page needs content and a review status")
    if text.startswith("---\n"):
        closing = text.find("\n---\n", 4)
        if closing == -1:
            raise ValueError("unterminated frontmatter")
        body = text[closing + 5:].lstrip()
    else:
        body = text
    if not body.startswith("<!--") or "-->" not in body:
        raise ValueError("review notes must immediately follow frontmatter")
    comment = body[4:body.index("-->")]
    match = re.search(r"(?m)^AUTOPILOT STATUS: (BLOCKED|REVIEW REQUIRED)$", comment)
    expected = "BLOCKED" if status == "blocked" else "REVIEW REQUIRED"
    if not match or match.group(1) != expected:
        raise ValueError("review comment status must match JSON report")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSON assembled for this run")
    parser.add_argument("output", type=Path, help="Unique durable report path")
    parser.add_argument("--page-source", type=Path, help="Staged Markdown page (optional)")
    parser.add_argument("--page-output", type=Path, help="Unused Markdown destination")
    args = parser.parse_args()
    try:
        if bool(args.page_source) != bool(args.page_output):
            raise ValueError("pass --page-source and --page-output together")
        report = json.loads(args.source.read_text(encoding="utf-8"))
        validate_report(report)
        if args.page_output:
            if report["markdown_path"] != str(args.page_output):
                raise ValueError("markdown_path must match --page-output")
            # Do not write a page when the report cannot be saved without
            # replacement. Neither artifact is a publication operation.
            if args.output.exists() or args.page_output.exists():
                raise FileExistsError("report or page already exists")
            save_page(args.page_source.read_text(encoding="utf-8"), args.page_output,
                      report["status"])
        save_report(report, args.output)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"[error] cannot save report: {exc}\n")


if __name__ == "__main__":
    main()