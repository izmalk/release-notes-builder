#!/usr/bin/env python3
"""Build release notes from GitHub commits/PRs using Jinja2 templates.

Fetches commit and pull-request data between two Git references via the
GitHub API, categorises changes by PR labels, and renders a Markdown
release-notes document from a Jinja2 template.
"""

import argparse
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone

import jinja2
import requests

# ---------------------------------------------------------------------------
# Label → category mapping (adjust as needed)
# ---------------------------------------------------------------------------
# Keys are GitHub PR label names (matched case-insensitively).
# Values are the release-notes category the entry will appear under.
LABEL_CATEGORY_MAP: dict[str, str] = {
    "bug": "Bug fixes",
    "enhancement": "Features",
    "not bug or enhancement": "Other improvements",
    # Uncomment the lines below when you start using these labels:
    # "security": "Security",
    # "breaking": "Breaking changes",
}

# Where PRs with *no* matching label end up (kitchen-sink catch-all).
DEFAULT_CATEGORY: str = "Other improvements"

# Display order of categories in the rendered release notes.
# Empty categories are automatically omitted.
CATEGORY_ORDER: list[str] = [
    "Features",
    "Breaking changes",
    "Security",
    "Bug fixes",
    "Other improvements",
]

# Jira ticket ID pattern (e.g. "DPE-1234").
JIRA_TICKET_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")

# GitHub compare API returns at most 250 commits per response.
GITHUB_COMPARE_LIMIT = 250

# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _build_session(token: str | None) -> requests.Session:
    """Return a requests.Session pre-configured with auth and headers."""
    session = requests.Session()
    session.headers["Accept"] = "application/vnd.github+json"
    session.headers["X-GitHub-Api-Version"] = "2022-11-28"
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def github_get(session: requests.Session, url: str, params: dict | None = None) -> list | dict:
    """GET *url* and return parsed JSON. Raises on HTTP errors."""
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def github_get_paginated(session: requests.Session, url: str, params: dict | None = None) -> list:
    """GET all pages of a list endpoint and return concatenated results."""
    params = dict(params or {})
    params.setdefault("per_page", 100)
    results: list = []
    while url:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        results.extend(resp.json())
        # Follow Link: <…>; rel="next" header for subsequent pages.
        url = resp.links.get("next", {}).get("url")
        params = {}  # params are already baked into the "next" URL
    return results


def get_default_branch(session: requests.Session, owner: str, repo: str) -> str:
    """Return the default branch name for a repository."""
    data = github_get(session, f"https://api.github.com/repos/{owner}/{repo}")
    return data["default_branch"]


def get_commits_between(
    session: requests.Session,
    owner: str,
    repo: str,
    base: str,
    head: str,
) -> tuple[list[dict], bool]:
    """Return (commits, truncated) between *base* and *head*.

    Uses the compare API which caps at 250 commits. If the result is
    truncated, the caller receives ``truncated=True`` so it can warn
    the user.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
    data = github_get(session, url)
    commits = data.get("commits", [])
    # GitHub sets "total_commits" even when the list is truncated.
    total = data.get("total_commits", len(commits))
    truncated = total > len(commits)
    return commits, truncated


def get_prs_for_commit(session: requests.Session, owner: str, repo: str, sha: str) -> list[dict]:
    """Return PRs associated with a single commit SHA."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/pulls"
    return github_get(session, url)


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------

def extract_jira_ids(text: str) -> list[str]:
    """Return deduplicated Jira ticket IDs found in *text*."""
    seen: set[str] = set()
    result: list[str] = []
    for match in JIRA_TICKET_RE.finditer(text):
        ticket = match.group(1)
        if ticket not in seen:
            seen.add(ticket)
            result.append(ticket)
    return result


def strip_jira_ids(text: str) -> str:
    """Remove Jira ticket ID references like '[DPE-1234]' from *text*."""
    cleaned = re.sub(r"\[?" + JIRA_TICKET_RE.pattern + r"\]?\s*[-–—:]?\s*", "", text)
    return cleaned.strip()


def strip_pr_number(text: str) -> str:
    """Remove trailing '(#NNN)' PR references from squash-merge messages."""
    return re.sub(r"\s*\(#\d+\)\s*$", "", text).strip()


def _label_names(pr: dict) -> list[str]:
    """Return lowercased label names from a PR dict."""
    return [lbl["name"].lower() for lbl in pr.get("labels", [])]


def categorise_entry(labels: list[str]) -> str:
    """Map a list of lowercased PR labels to a release-notes category."""
    for label in labels:
        for config_label, category in LABEL_CATEGORY_MAP.items():
            if label == config_label.lower():
                return category
    return DEFAULT_CATEGORY


def build_entries(
    commits: list[dict],
    prs_by_sha: dict[str, list[dict]],
    use_prs: bool,
    repo_url: str,
) -> OrderedDict[str, list[dict]]:
    """Categorise commits into an ordered dict of release-notes entries.

    Returns an ``OrderedDict`` keyed by category name (in display order)
    with only non-empty categories present.
    """
    buckets: dict[str, list[dict]] = {cat: [] for cat in CATEGORY_ORDER}

    for commit in commits:
        sha = commit["sha"]
        message_full = commit["commit"]["message"]
        # Use the first line of the commit message as the short message.
        message_first_line = message_full.split("\n", 1)[0].strip()

        associated_prs = prs_by_sha.get(sha, [])
        pr = associated_prs[0] if associated_prs else None

        # Decide which text to show, and strip Jira IDs (they're shown as
        # linked references separately). Also strip trailing PR refs like
        # "(#123)" from squash-merge commit messages since the PR is linked
        # separately.
        if use_prs and pr:
            display_message = strip_jira_ids(pr["title"])
        else:
            display_message = strip_pr_number(strip_jira_ids(message_first_line))

        # Collect Jira IDs from both commit message and PR title/body.
        jira_sources = message_full
        if pr:
            jira_sources += " " + (pr.get("title") or "")
            jira_sources += " " + (pr.get("body") or "")
        jira_ids = extract_jira_ids(jira_sources)

        labels = _label_names(pr) if pr else []
        category = categorise_entry(labels)

        entry = {
            "message": display_message,
            "pr_number": pr["number"] if pr else None,
            "pr_url": pr["html_url"] if pr else None,
            "commit_sha": sha,
            "commit_url": f"{repo_url}/commit/{sha}",
            "jira_ids": jira_ids,
            "labels": labels,
        }
        buckets[category].append(entry)

    # Return only non-empty categories, preserving CATEGORY_ORDER.
    return OrderedDict((cat, items) for cat, items in buckets.items() if items)


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_template(template_path: str, context: dict) -> str:
    """Load a Jinja2 template from *template_path* and render it."""
    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_name = os.path.basename(template_path)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**context)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate release notes from GitHub commits and PRs.",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in 'owner/repo' format or full URL.",
    )
    parser.add_argument(
        "--from-ref",
        required=True,
        help="Start reference (tag, branch, or commit SHA). Changes *after* this ref are included.",
    )
    parser.add_argument(
        "--to-ref",
        default=None,
        help="End reference (default: latest commit on --branch or default branch).",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch to resolve --to-ref against when --to-ref is omitted.",
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Path to the Jinja2 template file.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Release title (e.g. 'Revision 248'). Defaults to --to-ref value.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="GitHub personal access token (overrides GITHUB_TOKEN env var).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path. Defaults to stdout.",
    )
    parser.add_argument(
        "--use-prs",
        action="store_true",
        help="Use PR titles instead of commit messages for changelog entries.",
    )
    return parser.parse_args(argv)


def parse_repo(repo_arg: str) -> tuple[str, str]:
    """Extract (owner, repo) from 'owner/repo' or a GitHub URL."""
    # Strip trailing .git and slashes.
    repo_arg = repo_arg.rstrip("/").removesuffix(".git")
    # Handle full URLs like https://github.com/owner/repo
    if "github.com" in repo_arg:
        parts = repo_arg.split("github.com/", 1)[-1].split("/")
    else:
        parts = repo_arg.split("/")
    if len(parts) < 2:
        raise ValueError(f"Cannot parse repository from '{repo_arg}'. Use 'owner/repo' format.")
    return parts[0], parts[1]


def resolve_token(cli_token: str | None) -> str | None:
    """Return the token to use: CLI arg > env var > None."""
    if cli_token:
        return cli_token
    return os.environ.get("GITHUB_TOKEN")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    owner, repo = parse_repo(args.repo)
    token = resolve_token(args.token)
    session = _build_session(token)
    repo_url = f"https://github.com/{owner}/{repo}"

    # Resolve the end reference.
    to_ref = args.to_ref
    if not to_ref:
        branch = args.branch or get_default_branch(session, owner, repo)
        to_ref = branch
        print(f"[info] No --to-ref specified; using branch '{to_ref}'.", file=sys.stderr)

    # Fetch commits in the range.
    print(f"[info] Comparing {args.from_ref}...{to_ref} in {owner}/{repo}", file=sys.stderr)
    commits, truncated = get_commits_between(session, owner, repo, args.from_ref, to_ref)
    print(f"[info] Found {len(commits)} commits.", file=sys.stderr)

    if truncated:
        last_sha = commits[-1]["sha"] if commits else "N/A"
        print(
            "\n\033[91m"  # red text
            "========================================================================\n"
            " WARNING: The commit range was TRUNCATED by the GitHub API.\n"
            f" Only {len(commits)} of the total commits were returned.\n"
            " The output is INCOMPLETE.\n"
            "\n"
            " To get the remaining commits, re-run with:\n"
            f"   --from-ref {last_sha}\n"
            " and merge the results manually.\n"
            "========================================================================\n"
            "\033[0m",
            file=sys.stderr,
        )

    # Fetch associated PRs for each commit.
    print("[info] Fetching associated PRs for each commit...", file=sys.stderr)
    prs_by_sha: dict[str, list[dict]] = {}
    for i, commit in enumerate(commits, 1):
        sha = commit["sha"]
        try:
            prs = get_prs_for_commit(session, owner, repo, sha)
            # Keep only merged PRs.
            prs_by_sha[sha] = [p for p in prs if p.get("merged_at")]
        except requests.HTTPError:
            prs_by_sha[sha] = []
        if i % 25 == 0 or i == len(commits):
            print(f"[info]   {i}/{len(commits)} commits processed.", file=sys.stderr)

    # Build categorised entries.
    categories = build_entries(commits, prs_by_sha, args.use_prs, repo_url)

    # Prepare template context.
    title = args.title or to_ref
    date = datetime.now(timezone.utc).strftime("%b %d, %Y")
    context = {
        "title": title,
        "date": date,
        "repo_url": repo_url,
        "from_ref": args.from_ref,
        "to_ref": to_ref,
        "categories": categories,
        "category_order": CATEGORY_ORDER,
    }

    # Validate and render the template.
    template_path = args.template
    if not os.path.isfile(template_path):
        print(f"[error] Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    output = render_template(template_path, context)

    # Write output.
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"[info] Release notes written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
