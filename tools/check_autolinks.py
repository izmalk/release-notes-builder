#!/usr/bin/env python3
"""Detect accidental auto-links (linkify hazards) in a Markdown release-notes page.

Why this exists
---------------
MyST enables the `linkify` extension by default, with `linkify_fuzzy_links`
also defaulting to True. That combination turns any bare `word.tld`-looking
token in prose into a hyperlink -- *without* requiring a scheme. Release notes
are built largely from raw PR titles, which mention filenames constantly, so
tokens like `README.md`, `charm.py` and `SECURITY.md` silently become
`http://README.md`, `http://charm.py`, `http://SECURITY.md`.

This is not merely cosmetic. Many file extensions are also live TLDs (`.md` is
Moldova, `.py` Paraguay, `.sh` Saint Helena, `.io`, `.co`, `.in`, ...), so the
bogus link often *resolves* -- to whoever squats that domain. Observed in a real
Canonical docs build:

    [redirected with Found] http://README.md to https://dealsbe.com

`make linkcheck` reports that as a *redirect*, not as `[broken]`, so the build
exits 0 and the page ships with a hyperlink to a stranger's site.

Rather than guessing at a blocklist of "dangerous extensions", this script asks
the very library MyST uses -- `linkify-it-py` -- what it would actually turn
into a link. That keeps the check correct as the TLD list evolves.

The real fix is one line in the docs' `conf.py`:

    myst_linkify_fuzzy_links = False

which stops scheme-less tokens being linkified while still linking explicit
`https://...` URLs and emails. Use `--explain` to print that guidance. This
script remains useful either way: it catches hazards before a build, and is the
only check that catches them when a project keeps fuzzy links enabled.

Usage
-----
    python tools/check_autolinks.py <file.md> [<file.md> ...]
    python tools/check_autolinks.py --explain <file.md>

Exit status is 1 if any hazard is found, so it can gate a release.
"""

from __future__ import annotations

import argparse
import re
import sys

try:
    from linkify_it import LinkifyIt
except ImportError:  # pragma: no cover - dependency guard
    sys.exit(
        "error: linkify-it-py is required.\n"
        "       pip install linkify-it-py  (it ships with myst-parser)"
    )


# A token that looks like a filename: NAME.EXT, where EXT is alphabetic.
# Deliberately permissive -- LinkifyIt decides what is actually a hazard.
FILENAME_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.[A-Za-z]{2,10}")

# Regions of a Markdown document where auto-linking cannot happen, or where a
# hit does not reach the reader. Order matters: fences before inline code.
_MASKED_REGIONS = (
    re.compile(r"<!--.*?-->", re.DOTALL),          # HTML comments (review notes)
    re.compile(r"^```.*?^```", re.DOTALL | re.M),  # fenced code blocks
    re.compile(r"``[^`]+``"),                      # double-backtick code spans
    re.compile(r"`[^`\n]+`"),                      # inline code spans
    re.compile(r"\]\([^)\s]+\)"),                  # link/image destinations
    re.compile(r"<[a-zA-Z][a-zA-Z0-9+.-]*:[^>\s]+>"),  # <https://...> autolinks
    re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://\S+"),  # explicit-scheme URLs
    re.compile(r"\bmailto:\S+"),                   # explicit mailto: links
    re.compile(r"\S+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # bare email addresses
    re.compile(r"^\s*(?:---|\+\+\+)\s*$", re.M),   # frontmatter fences
    re.compile(r"^\(.*?\)=\s*$", re.M),            # MyST anchors
)


def mask_safe_regions(text: str) -> str:
    """Blank out regions that cannot produce a rendered auto-link.

    Replaces each masked region with spaces/newlines of the same length so that
    line and column numbers of everything else are preserved exactly.
    """
    for pattern in _MASKED_REGIONS:
        text = pattern.sub(
            lambda m: "".join("\n" if c == "\n" else " " for c in m.group(0)),
            text,
        )
    return text


def find_hazards(text: str) -> list[tuple[int, int, str, str]]:
    """Return (line, column, token, would-be URL) for each linkify hazard."""
    linkify = LinkifyIt()
    masked = mask_safe_regions(text)
    hazards: list[tuple[int, int, str, str]] = []

    for lineno, line in enumerate(masked.split("\n"), start=1):
        for match in FILENAME_RE.finditer(line):
            token = match.group(0)
            # Ask linkify-it -- the library MyST itself uses -- for the verdict.
            found = linkify.match(token)
            if not found:
                continue
            # Only flag when the WHOLE token is the link: a substring match
            # means it is something else (e.g. a version string).
            hit = found[0]
            if hit.index != 0 or hit.last_index != len(token):
                continue
            hazards.append((lineno, match.start() + 1, token, hit.url))

    return hazards


EXPLANATION = """\
Root-cause fix (preferred, one line)
-----------------------------------
Add this to the docs' conf.py:

    # Do not turn scheme-less tokens (e.g. the "README.md" in a PR title) into
    # links. Many file extensions are live TLDs, so such links resolve to
    # domain squatters and pass `make linkcheck` as mere redirects.
    myst_linkify_fuzzy_links = False

Verified behaviour with that setting:
    README.md, charm.py, SECURITY.md    -> plain text  (was http://README.md, ...)
    https://canonical.com/data          -> still linked
    foo@example.com                     -> still linked (mailto:)
    canonical.com/data (no scheme)      -> no longer linked

The last line is the only trade-off: bare domains in prose stop auto-linking,
so write them as explicit Markdown links. That is better practice anyway.

Per-document fix (always correct, and needed if fuzzy links stay on)
--------------------------------------------------------------------
Wrap the token in backticks: `README.md`. A code span is never linkified, and
a filename belongs in code formatting regardless.

Do NOT "fix" these by adding the bogus URL to linkcheck_ignore -- that hides
the problem and leaves a live hyperlink to a squatted domain in the page.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect accidental auto-links (e.g. README.md -> http://README.md).",
    )
    parser.add_argument("files", nargs="+", metavar="FILE", help="Markdown file(s) to check.")
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print how to fix the findings, including the conf.py root-cause fix.",
    )
    args = parser.parse_args(argv)

    total = 0
    for path in args.files:
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2

        hazards = find_hazards(text)
        total += len(hazards)
        for lineno, col, token, url in hazards:
            print(f"{path}:{lineno}:{col}: {token!r} would be auto-linked as {url}")

    if total:
        print(f"\n{total} linkify hazard(s) found. Wrap each token in backticks.")
        if args.explain:
            print()
            print(EXPLANATION)
        else:
            print("Re-run with --explain for the conf.py root-cause fix.")
        return 1

    print("No linkify hazards found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
