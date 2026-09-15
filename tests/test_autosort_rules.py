"""Regression tests for the auto-sort rules defined in the release-notes skill.

Auto-sort itself is performed by the agent while it merges and polishes the
per-repo drafts (see "Auto-sort" in `.github/skills/release-notes/SKILL.md`) —
this file is NOT that implementation, and the skill does not call it. It is a
executable specification of the rule table: `classify()` below encodes the
documented signals, and the test cases pin the expected outcome for real entry
titles taken from actual Charmed Apache Kafka and Charmed OpenSearch releases.

Its purpose is to keep the rules honest. If someone edits the rule table in
SKILL.md, these tests show which real-world entries change category as a
result — in particular the infrastructure-only exception, which is the rule
most likely to be broken by a well-meaning simplification.

Run with:  python -m pytest tests/test_autosort_rules.py -q
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT = "Other improvements"
FEATURES = "Features"
BUG_FIXES = "Bug fixes"
SECURITY = "Security"
BREAKING = "Breaking changes"
LEAVE_AND_FLAG = "Other improvements (flagged)"

# The two lists below both mention `ci`, `test` and `build`, but they are
# consulted at different points and answer different questions. Keeping them
# separate is deliberate:
#
#   NEUTRAL_PREFIXES asks "did the author already classify this?" It matches
#   only the conventional-commit TYPE (the token before the colon), so `ci:` in
#   `ci: unpin juju agent` means the author declared this a CI change. Such an
#   entry never reaches the fix-verb rule, so it is never flagged.
#
#   INFRA_TERMS asks "what does this fix actually target?" It is consulted ONLY
#   for entries that already carry a fix signal, and it searches the WHOLE
#   title, because the giveaway usually sits in the description rather than the
#   prefix (`fix: action permissions`, `fix: monorepo release`).
#
# So `ci` appears in both because "the author labelled this a CI change" and
# "this fix touches CI" are independent facts, arrived at from different parts
# of the string.

# Prefixes that are already correctly served by "Other improvements" and must
# never trigger a move, per the skill's rule table. Matched against the parsed
# commit type only, never as a substring of the description.
NEUTRAL_PREFIXES = (
    "chore", "docs", "ci", "cicd", "build", "deps", "test", "style",
    "refactor", "patch",
)

# Terms that mark a change as targeting the project's own tooling rather than
# the shipped product. A fix signal on one of these stays in the catch-all,
# because DA186's "Bug fixes" means user-visible defects.
#
# Matched on WORD BOUNDARIES, not as bare substrings. Plain `in` matching is
# unsafe here: short terms hide inside ordinary words, so `ci` would match
# "precision", "decision", "explicit", "specific", "capacity", "circuit" and
# "efficiency", wrongly withholding genuine bug fixes such as
# "fix: precision loss in shard allocation". Likewise `tag` inside "stage",
# `pin` inside "pinning", `test` inside "testing", `build` inside "builder".
# Multi-word terms are matched as phrases; `metadata.yaml` needs its dot
# escaped, which `re.escape` handles.
INFRA_TERMS = (
    "ci", "cicd", "github action", "workflow", "runner", "permission",
    "lint", "spread", "tox", "pytest", "fixture", "flaky", "release",
    "tag", "pin", "cache", "coverage", "test", "docs", "documentation",
    "changelog", "metadata.yaml", "charmcraft", "build",
)

def _infra_pattern(term: str) -> str:
    """Build a boundary-safe pattern for one infra term.

    Two details that `\\b` alone gets wrong, both found by the tests:

    * `\\b` treats `_` as a word character, so `\\btest\\b` does NOT match inside
      `test_certificate_transfer` — a real entry that must be recognised as a
      test fix. Custom lookarounds against `[0-9a-z]` make `_` a boundary.
    * English doubles a final consonant before a suffix (`tag` → `tagging`,
      `pin` → `pinning`), so a plain `(?:s|es|ing|ed)?` suffix group misses
      them. The final consonant is therefore optionally doubled.

    A term ending in a non-alphanumeric character (`metadata.yaml`) takes no
    suffix group and no trailing boundary, since one could never match.
    """
    if not term[-1].isalnum():
        return r"(?<![0-9a-z])" + re.escape(term)
    doubled = re.escape(term[-1]) + "?" if term[-1].isalpha() else ""
    return (
        r"(?<![0-9a-z])"
        + re.escape(term)
        + doubled
        + r"(?:s|es|ing|ed)?"
        + r"(?![0-9a-z])"
    )


_INFRA_RE = re.compile(
    "|".join(_infra_pattern(term) for term in INFRA_TERMS), re.IGNORECASE
)

FIX_VERBS = (
    "fix", "fixes", "fixed", "fixing",
    "resolve", "resolves", "correct", "corrects",
)


def _prefix(title: str) -> tuple[str | None, bool]:
    """Return (conventional-commit type, breaking-bang) parsed from *title*.

    Handles an optional scope (`feat(api):`) and a leading bracketed Jira tag
    (`[DPE-123] fix: ...`), both of which occur in real entries.
    """
    stripped = re.sub(r"^\s*(\[[^\]]+\]\s*)+", "", title).strip()
    match = re.match(r"^([A-Za-z-]+)(\([^)]*\))?(!)?\s*:", stripped)
    if not match:
        return None, False
    return match.group(1).lower(), bool(match.group(3))


def _is_infra(title: str) -> bool:
    """True if *title* refers to the project's own tooling rather than the product."""
    return _INFRA_RE.search(title) is not None


def classify(title: str) -> str:
    """Return the category auto-sort should move *title* to, per SKILL.md.

    The return value is the category the entry ends up in; `LEAVE_AND_FLAG`
    means it stays in "Other improvements" but must be flagged for review.
    """
    lowered = title.lower()
    prefix, breaking = _prefix(title)

    # Breaking changes win outright, including via a bang on any prefix.
    if breaking or "breaking change" in lowered:
        return BREAKING

    # A revert is never auto-sorted; it may belong with whatever it reverted.
    if prefix == "revert" or lowered.startswith("revert "):
        return LEAVE_AND_FLAG

    # Security: explicit prefix, or a CVE reference anywhere in the title.
    if prefix == "security" or re.search(r"\bCVE-\d{4}-\d+", title):
        return SECURITY

    if prefix in ("feat", "feature", "perf"):
        return FEATURES

    has_fix_prefix = prefix in ("fix", "bugfix", "bug-fix", "hotfix")
    # A bare fix verb only counts at the very start of the title, and only when
    # no neutral prefix already classified the entry.
    starts_with_fix_verb = (
        prefix is None
        and re.match(r"^\s*(\[[^\]]+\]\s*)*(" + "|".join(FIX_VERBS) + r")\b", lowered)
        is not None
    )

    if has_fix_prefix or starts_with_fix_verb:
        # The infrastructure exception: tooling fixes stay put.
        return LEAVE_AND_FLAG if _is_infra(title) else BUG_FIXES

    # Everything else stays in the catch-all. A neutral prefix (NEUTRAL_PREFIXES)
    # lands here too: it is where an unrecognised prefix and a deliberately
    # neutral one converge, which is why there is no separate branch for it.
    # The list still documents which prefixes are *expected* here, and
    # test_every_neutral_prefix_is_inert pins that expectation.
    return DEFAULT


# ---------------------------------------------------------------------------
# Real entry titles from Charmed OpenSearch (opensearch-operator, rev315..2/edge)
# and Charmed Apache Kafka (kafka-operator et al., rev248..main).
# ---------------------------------------------------------------------------

MOVES_TO_FEATURES = [
    "feat: support GCS repository for snapshot operations",
    "feat: create buckets/containers if not available",
    "feat: HA",
    "feat: add common lib",
    "feat: remove zookeeper & use Kafka 4 snap",
    "perf: reduce startup latency",
]

MOVES_TO_BUG_FIXES = [
    "fix: handle the situation that opensearch_failover does not exist",
    "fix: set blocked status for invalid object-storage secrets",
    "fix: add missing LIBID to notifications manager",
    "fix: TLS setup failure if chain is missing",
    "fix: race condition in internal TLS setup",
    "[DPE-4546] fix: Juju `remove-unit` app/leader breaks TLS",
]

# Entries carrying a fix signal that must NOT move, because the fix targets the
# project's own tooling. These are the cases the infrastructure exception exists
# for: the signal is real, so the entry is flagged, but it stays put.
STAYS_DESPITE_FIX_SIGNAL = [
    "fix: Fix spread installation",
    "fix: Fix tutorial test",
    "Fix charm Build",
    "fix: action permissions",
    "fix: release output name",
    "fix: use full chain in test_certificate_transfer",
    "fix: monorepo release",
    "fix: Fix charmcraft revision",
    "Fixing Terraform Flaky Tests due to Limited storage on github runners",
]

# Entries whose *neutral* prefix already settles the category, even though a fix
# verb appears later in the title. These need no flag at all: `patch:`/`docs:`
# is decisive, so the fix verb is never consulted. Distinguishing these from
# STAYS_DESPITE_FIX_SIGNAL matters because flagging them would bury the entries
# that genuinely need a human decision.
STAYS_VIA_NEUTRAL_PREFIX = [
    "patch: Fix tag in metadata.yaml",
    "patch: fix spread installation",
    "docs: Fix spread install in GH workflow",
    "chore: Fix the changelog ordering",
]

# Neutral-prefix entries that belong in the catch-all and must stay there.
STAYS_NEUTRAL = [
    "chore: update rust toolchain",
    "docs: Homepage upgrade",
    "ci: unpin juju agent",
    "build: bump rust to latest stable",
    "deps: Update dependencies",
    "patch: Bump opensearch-charms-single-kernel to v0.0.14",
    "refactor: monorepo",
    "test: add smoke test",
    "chore: Add icon",
    "docs: Add autogenerated metadata description",
]


@pytest.mark.parametrize("title", MOVES_TO_FEATURES)
def test_feature_signals_move_to_features(title):
    assert classify(title) == FEATURES


@pytest.mark.parametrize("title", MOVES_TO_BUG_FIXES)
def test_fix_signals_on_shipped_behaviour_move_to_bug_fixes(title):
    assert classify(title) == BUG_FIXES


@pytest.mark.parametrize("title", STAYS_DESPITE_FIX_SIGNAL)
def test_infrastructure_fixes_are_not_moved(title):
    """The most important rule: a CI/test/release fix is not a DA186 bug fix."""
    assert classify(title) == LEAVE_AND_FLAG


@pytest.mark.parametrize("title", STAYS_VIA_NEUTRAL_PREFIX)
def test_neutral_prefix_beats_a_later_fix_verb(title):
    """A neutral prefix settles the category outright, with no flag needed."""
    assert classify(title) == DEFAULT


@pytest.mark.parametrize("title", STAYS_NEUTRAL)
def test_neutral_prefixes_stay_in_catch_all(title):
    assert classify(title) == DEFAULT


@pytest.mark.parametrize(
    "title",
    [
        "feat!: drop support for Juju 2.9",
        "refactor!: rename the cluster relation",
        "feat: new API\n\nBREAKING CHANGE: removes the old endpoint",
    ],
)
def test_breaking_signals_win_over_everything(title):
    assert classify(title) == BREAKING


@pytest.mark.parametrize(
    "title",
    [
        "security: patch the auth bypass",
        "Bump library to address CVE-2026-1234",
    ],
)
def test_security_signals_move_to_security(title):
    assert classify(title) == SECURITY


@pytest.mark.parametrize(
    "title",
    ["revert: feat: add common lib", "Revert \"feat: add common lib\""],
)
def test_reverts_are_never_auto_sorted(title):
    assert classify(title) == LEAVE_AND_FLAG


def test_unprefixed_entries_stay_put():
    """No signal at all means no move — auto-sort is not a guesser."""
    for title in [
        "Release notes for new release",
        "Pin Terraform Version",
        "Update rust in charmcraft.yaml",
        "Add promote workflow",
        "Rework Snapshots",
    ]:
        assert classify(title) == DEFAULT, title


def test_security_takes_precedence_over_fix():
    """A CVE fix is a Security entry, not a Bug fix."""
    assert classify("fix: bump urllib3 for CVE-2026-9999") == SECURITY


# ---------------------------------------------------------------------------
# The two term lists: why `ci`, `test` and `build` appear in both, and why
# INFRA_TERMS must match on word boundaries.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "title",
    [
        # `ci` inside precision/decision/explicit/specific/capacity/circuit/
        # efficiency — the reason bare substring matching is unsafe.
        "fix: precision loss in shard allocation",
        "fix: decision logic for leader election",
        "fix: explicit cast in config parser",
        "fix: specific node role not applied",
        "fix: capacity calculation for storage",
        "fix: circuit breaker never resets",
        "fix: efficiency of the rebalance loop",
        # `tag` inside stage, `pin` inside pinning, `build` inside builder.
        "fix: staged rollout never completes",
        "fix: repinning a shard drops replicas",
        "fix: query builder emits invalid JSON",
    ],
)
def test_infra_terms_do_not_match_inside_unrelated_words(title):
    """These are real product bug fixes, not tooling fixes.

    Every title here contains an INFRA_TERMS entry as a substring of an ordinary
    word. If infra matching ever regresses to plain `in` checks, these genuine
    bug fixes get silently withheld from the Bug fixes section.
    """
    assert classify(title) == BUG_FIXES


@pytest.mark.parametrize(
    "title",
    [
        "fix: CI is broken on noble",
        "fix: tests are flaky",
        "fix: tagging the wrong commit",
        "fix: pinning the charmcraft version",
        "fix: caches are never invalidated",
    ],
)
def test_infra_terms_still_match_real_tooling_fixes(title):
    """Word-boundary matching must not have broken the exception itself.

    Includes inflected forms (tests, tagging, pinning, caches) to pin that the
    suffix allowance works.
    """
    assert classify(title) == LEAVE_AND_FLAG


@pytest.mark.parametrize("prefix", NEUTRAL_PREFIXES)
def test_every_neutral_prefix_is_inert(prefix):
    """Each neutral prefix leaves an entry in the catch-all, unflagged.

    `classify()` has no dedicated NEUTRAL_PREFIXES branch — neutral and
    unrecognised prefixes both fall through to the same default. This test is
    what makes the list meaningful rather than decorative: it asserts the
    documented prefixes really are inert, including when the description carries
    a fix verb that would otherwise trigger a move.
    """
    assert classify(f"{prefix}: something entirely routine") == DEFAULT
    assert classify(f"{prefix}: Fix the thing") == DEFAULT


def test_ci_means_different_things_in_each_list():
    """`ci` appears in both lists, resolving two independent questions.

    As a *prefix* it records the author's own classification, so the entry is
    left alone without a flag. As an *infra term* it describes what a fix
    targets, so a `fix:` entry mentioning CI is flagged for review. Same token,
    different question, different outcome — which is why one list cannot simply
    be folded into the other.
    """
    assert classify("ci: re-enable cached builds") == DEFAULT
    assert classify("fix: re-enable CI cached builds") == LEAVE_AND_FLAG
