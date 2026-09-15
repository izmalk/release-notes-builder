"""Tests for tools/check_autolinks.py — the linkify-hazard detector.

These encode the behaviour that matters: a bare filename whose extension is
also a live TLD gets auto-linked by MyST and can resolve to a domain squatter,
while genuinely safe constructs must never be flagged (or the check gets
ignored, which is worse than not having it).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from check_autolinks import find_hazards, mask_safe_regions  # noqa: E402


def tokens(text: str) -> list[str]:
    """Return just the hazardous tokens found in *text*."""
    return [token for _, _, token, _ in find_hazards(text)]


# ---------------------------------------------------------------------------
# Hazards that must be caught
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "line, expected",
    [
        # The two that were observed breaking a real Canonical docs build.
        ("* docs: update README.md ([PR #239](https://x/y/pull/239))", "README.md"),
        ("* patch: leaving only charm.py ([PR #818](https://x/y/pull/818))", "charm.py"),
        # Seen 6x in one real Spark release-notes document.
        ("* Add SECURITY.md ([PR #218](https://x/y/pull/218))", "SECURITY.md"),
        # Extensions that are live TLDs but are easy to forget in a hand-list.
        ("run install.sh to set up", "install.sh"),
        ("edit lib.rs and rebuild", "lib.rs"),
        ("check script.pl output", "script.pl"),
        ("see main.tf for the module", "main.tf"),
        ("load libfoo.so at runtime", "libfoo.so"),
    ],
)
def test_bare_filename_with_tld_extension_is_flagged(line, expected):
    assert tokens(line) == [expected]


def test_reports_the_url_it_would_become():
    (_, _, token, url), = find_hazards("* docs: update README.md now")
    assert token == "README.md"
    assert url == "http://README.md"


def test_reports_line_and_column():
    text = "# Title\n\nsome prose\n* fix charm.py now\n"
    (lineno, col, token, _), = find_hazards(text)
    assert (lineno, token) == (4, "charm.py")
    # Column is 1-based and points at the token.
    assert text.split("\n")[lineno - 1][col - 1:col - 1 + len(token)] == token


def test_multiple_hazards_on_one_line():
    assert tokens("update README.md and charm.py together") == ["README.md", "charm.py"]


# ---------------------------------------------------------------------------
# Constructs that must NOT be flagged (false positives kill adoption)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "line",
    [
        # Extension is not a TLD, so MyST never linkifies it.
        "* patch: Fix tag in metadata.yaml",
        "* Update rust in charmcraft.yaml",
        "* edit pyproject.toml",
        "* see requirements.txt",
        "* tweak config.json and settings.ini",
        "* check tox.cfg",
        # Verified NOT TLDs, despite looking risky -- this is exactly why the
        # check asks linkify-it-py instead of using a hand-written list.
        "* see main.go for details",
        "* open index.html locally",
        # Already correctly formatted as code spans.
        "* docs: update `README.md` here",
        "* leaving only `charm.py` behind",
        "* both `SECURITY.md` and `install.sh` are fine",
        # Version strings must not look like domains.
        "* Bump single-kernel to v0.0.14",
        "* upgrade to 2.19.6 now",
        "* Apache Kafka 4.3.0 support",
        # Real links, in every form.
        "* see https://canonical.com/data for info",
        "* [Charmhub](https://charmhub.io/opensearch) | [Docs](x)",
        "* <https://canonical.com/data>",
        "* mail foo@example.com for help",
    ],
)
def test_safe_constructs_are_not_flagged(line):
    assert tokens(line) == []


def test_review_notes_comment_is_ignored():
    """The review comment is never rendered, so hits there cannot linkify."""
    text = (
        "---\nmyst:\n  html_meta:\n    description: \"x\"\n---\n"
        "<!--\nREVIEW: mentions README.md and charm.py deliberately\n-->\n\n"
        "# Revision 9\n"
    )
    assert tokens(text) == []


def test_fenced_code_block_is_ignored():
    text = "# Title\n\n```\nREADME.md inside a fence\n```\n"
    assert tokens(text) == []


def test_hazard_after_a_masked_region_is_still_found():
    """Masking must not swallow the rest of the document."""
    text = "<!-- README.md ignored -->\n\n* real hazard: charm.py here\n"
    assert tokens(text) == ["charm.py"]


def test_masking_preserves_line_numbers():
    text = "<!--\na\nb\nc\n-->\n* fix charm.py\n"
    masked = mask_safe_regions(text)
    assert len(masked.split("\n")) == len(text.split("\n"))
    (lineno, _, _, _), = find_hazards(text)
    assert lineno == 6


def test_clean_document_yields_nothing():
    text = (
        "---\nmyst:\n  html_meta:\n    description: \"x\"\n---\n\n"
        "(reference-release-notes-revision-9)=\n# Revision 9\n\n"
        "September 15, 2026\n\n"
        "* patch: Fix tag in `metadata.yaml` ([PR #836](https://x/y/pull/836))\n"
    )
    assert find_hazards(text) == []
