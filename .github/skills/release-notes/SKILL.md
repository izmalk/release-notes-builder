---
name: release-notes
description: 'Generate DA186-compliant release notes for Canonical Data & AI charms. Use when the user asks to "generate release notes", "create release notes", "compile a changelog", "prepare release notes draft", or a similar phrasing/verb — including bare requests with no repository, product, or ref named at all ("generate release notes", "write the next release notes"), which mean the currently open repository, with the product, refs and components auto-detected from its own docs. Also accepts one or multiple charm repositories (e.g. canonical/kafka-operator), a link to a previously published release-notes page, or an explicit starting point named as a revision, version, tag or commit SHA ("since rev247", "from 2.1.0", "changes after revision 315"), optionally for a branch, track, or a commit range. Handles a product''s very first release notes, where no previous notes exist to build on. Gathers changes via GitHub API, discovers sibling components from prior release notes, merges multi-repo notes into a single product draft, writes intro and compatibility sections, and saves the result locally for review. Never publishes anything.'
argument-hint: '[repo ...] [--track TRACK] [--branch BRANCH] [--from-ref REF] [--to-ref REF] [auto-sort on|off]'
---

# Release Notes Generation (DA186)

Generate a DA186-spec-compliant release notes document for one or more GitHub
repositories (charm components of a single product), saved locally as a
Markdown file for human review. The output must read as a **finished,
publishable release notes document** — see "Fully publishable output" below.
**Never push, post, or publish anything** — all output stays in this local
repository.

## When to Use

- **"Generate release notes"** — with no repository, product, track or ref
  named at all. This is the most common request, and it means *this*
  repository: detect everything from the currently open workspace (see
  "Starting from the currently open repository" below). Never respond to a
  bare request by asking which repository is meant — the answer is the one
  that's open.
- "Write the next release notes", "time for release notes", "release notes
  for the upcoming revision", "changelog since the last release" — same
  thing, still no explicit target
- "Generate release notes for canonical/kafka-operator"
- "Prepare release notes for Kafka 4.2 from rev247 to rev248"
- "Release notes since rev247", "changes after revision 315", "everything
  since 2.1.0", "from a1b2c3d to HEAD" — an explicit starting point given as a
  revision, version, tag or commit SHA; see "Starting from a revision,
  version, tag or commit the user names" below
- "Write the first release notes for this charm" — a product with no published
  release notes yet; see "First release: a product with no release notes yet"
  below
- "Compile release notes for https://github.com/canonical/kafka-operator and https://github.com/canonical/kafka-connect-operator as one product"
- "Draft release notes for the 14/stable channel of postgresql-operator"
- "Create release notes for https://canonical.com/data/opensearch/docs/2/reference/release-notes/revision-315/"
  (a link to a *previous* published release; see "Starting from a link to
  previously published release notes" below — generate the *next* release
  after the one that link documents, not that release itself)
- "Write the next OpenSearch release notes" (any generation verb — create,
  write, build, draft, compile, prepare — is treated the same; see "Any
  generation verb triggers this skill" below)
- "Generate release notes for canonical/opensearch-operator with auto-sort on"
  (opts in to reclassifying the "Other improvements" catch-all by
  conventional-commit prefix; `auto-sort off` opts out — see "Auto-sort"
  below, which is off unless enabled)

## Installing and running this skill

The normal way to use this skill is with the **charm/product repo you're
releasing** open as the workspace (e.g. `kafka-operator`,
`opensearch-operator`). The automation script (`build_release_notes.py`) and
templates (`templates/`) live in the **release-notes-builder** repository, but
you do **not** need a checkout of it, and it does not need to be open.

### Installation: copy one file

`SKILL.md` is self-bootstrapping. Put this single file anywhere the agent will
read it, and it fetches the script and templates itself on first use (see
"Locating the builder script and templates" below). There is nothing else to
install, symlink, configure, or keep in sync.

Pick whichever location suits you:

| Where you put `SKILL.md` | Effect |
|---|---|
| Your personal skills folder — `~/.claude/skills/release-notes/SKILL.md`, `~/.copilot/skills/release-notes/SKILL.md`, or `~/.agents/skills/release-notes/SKILL.md` (whichever your harness reads) | Available in **every** workspace. Best for repeat use. |
| `.github/skills/release-notes/SKILL.md` inside the target repo | Available in that repo, and to teammates if you commit it. |
| Anywhere at all, then name the path in chat | Zero install; good for a one-off. See below. |

```bash
# Personal install (available everywhere) — one command, no clone:
mkdir -p ~/.claude/skills/release-notes && curl -fsSL -o ~/.claude/skills/release-notes/SKILL.md \
  https://raw.githubusercontent.com/izmalk/release-notes-builder/main/.github/skills/release-notes/SKILL.md
```

To install it into a target repo instead, change the output path to
`.github/skills/release-notes/SKILL.md` inside that repo.

If your harness doesn't discover skills, or you just want to try it once,
skip installation entirely and point the agent at the file in your message:

> Using the skill instructions at `<path or URL to SKILL.md>`, generate
> release notes for canonical/kafka-operator

A symlink to a local checkout also still works, and is the best choice if you
are *developing* this skill — edits take effect immediately with no re-copy.
For simply *using* it, prefer the copy above.

Opening `release-notes-builder` itself as the workspace also remains fully
supported and needs no setup at all; `--repo` still accepts any `owner/repo`.
That is referred to as **standalone mode** below (it changes only where the
result is saved — see step 8), as opposed to **cross-repo mode**, where a
target repo is open instead.

### Locating the builder script and templates ($BUILDER_HOME)

Every reference in this skill to `build_release_notes.py` or
`templates/<file>` resolves through `$BUILDER_HOME`, worked out once per run.
Try each source in order and stop at the first that yields a directory
containing `build_release_notes.py`:

1. **A local checkout around this `SKILL.md`.** Resolve the real path of
   whichever `SKILL.md` was loaded (following symlinks) and try the folder
   three levels up (`.github/skills/release-notes/../../..`); in standalone
   mode this is simply the workspace root. Also check whether
   `build_release_notes.py` sits directly *next to* `SKILL.md`, which is the
   case for a fully vendored copy. Using a real checkout ahead of the cache
   matters for development: local edits must win over a downloaded copy.
2. **`RELEASE_NOTES_BUILDER_HOME`**, if set — an explicit override always
   beats autodetection.
3. **A `.builder-home` file** next to this `SKILL.md`, whose first line is an
   absolute path to a checkout. Only relevant if someone created it; nothing
   writes it any more.
4. **The bootstrap cache**, `~/.cache/release-notes-builder/`. If it already
   contains `build_release_notes.py`, use it as-is.
5. **Bootstrap it.** Download the script, templates and tools from the public
   repository into the cache, then use that:
   ```bash
   BUILDER_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/release-notes-builder"
   mkdir -p "$BUILDER_HOME"
   curl -fsSL https://codeload.github.com/izmalk/release-notes-builder/tar.gz/refs/heads/main \
     | tar -xz -C "$BUILDER_HOME" --strip-components=1 --wildcards \
         '*/build_release_notes.py' '*/templates/*' '*/tools/*' '*/requirements.txt'
   ```
   One request, ~80 KB, no authentication and no `git` needed (the repository
   is public). Tell the user this happened and where the cache is.

   `'*/tools/*'` matters: without it, step 9's `tools/check_autolinks.py` is
   missing and the auto-link check silently can't run. Note that `tar` exits
   **2** with `*/tools/*: Not found in archive` if the pushed branch predates
   that directory, *even though the other files extracted correctly*. Don't
   treat that non-zero exit as a failed bootstrap: check which files actually
   landed, and if the checker is genuinely absent from the remote, say so and
   fall back to reviewing bare filenames by hand (see step 9) instead of
   skipping the check silently.

Then make sure the dependencies are importable — `build_release_notes.py` needs
`jinja2` and `requests`, and `tools/check_autolinks.py` needs `linkify-it-py`.
Try running them; if either fails on a missing import, install them
(`pip install -r "$BUILDER_HOME/requirements.txt"`, or into a virtualenv if
the environment is externally managed) rather than reporting failure.

**Refreshing the cache.** A bootstrapped cache is a snapshot, so it does not
pick up fixes by itself. Re-run the bootstrap command (it overwrites in place)
when the user asks for the latest version, or if the cache looks stale — for
example when a template the skill expects, such as
`templates/opensearch.md.j2`, or a tool such as `tools/check_autolinks.py`, is
missing. Never refresh a `$BUILDER_HOME` that
came from source 1: that is the user's own checkout, possibly with uncommitted
work, and overwriting it would destroy their edits.

**If bootstrapping is impossible** (no network, or an air-gapped machine), ask
the user for a local path to a `release-notes-builder` checkout and suggest
`export RELEASE_NOTES_BUILDER_HOME=…` so later runs skip the question. Only
ask once, and only after sources 1–5 have genuinely failed.

**`$BUILDER_HOME` is an input, never an output.** In cross-repo mode the
generated release notes are saved into the currently open target repository —
never into `$BUILDER_HOME`, and never into the bootstrap cache. This holds even
when `$BUILDER_HOME` happens to sit inside the target repo (a vendored copy).
See step 8 for the exact save rule.

## Any generation verb triggers this skill

Treat "generate", "create", "compile", "draft", "prepare", "write", "build",
and similar verbs applied to "release notes" / "changelog" as equivalent
requests — they all mean run this skill's full procedure. The verb used has
no bearing on scope or thoroughness: don't skip template selection, sibling-
component discovery, compatibility, or the DA186 checklist just because the
user said "create" instead of "generate".

## Infer what's determinable; ask about what isn't

Two failure modes matter equally, and the line between them is **confidence**,
not effort:

- **Interrogating the user about things you could have worked out** wastes
  their time. Anything with exactly one plausible answer available from the
  open workspace, the repos, or the GitHub API must be resolved silently and
  merely *reported* — never asked about.
- **Guessing at things you cannot actually determine** silently produces a
  document that misrepresents the release, which is worse. A release-notes
  document is a public factual record; a wrong revision number, a missing
  component or an invented compatibility value is a real defect.

So: **whenever an input is ambiguous, contradictory, undefined, or you are
not confident in an inference, stop and ask the user.** Concretely, ask when:

- **Several candidates fit and nothing decides between them** — e.g. two
  plausible release-notes folders, multiple git remotes, several tracks whose
  branches all look current, two files that both look like "the newest
  release".
- **Sources of truth disagree** — e.g. the current branch implies one track
  but the docs' default version implies another; `charmcraft.yaml` and the
  docs give different product names; the newest documented revision is *ahead*
  of the latest tag.
- **A value is required but absent** — no release-notes folder anywhere, no
  resolvable `from-ref`, a compatibility field with no source in the repo.
- **The request itself is unclear** — an unfamiliar term, an ambiguous ref
  ("the last release" in a repo with both tags and documented revisions), a
  product name matching several products, or a scope you can read two ways
  ("the Kafka release notes" when both `kafka-operator` and
  `kafka-k8s-operator` are in play and you can't tell if one document or two
  is wanted).
- **Something looks wrong rather than merely missing** — an empty commit
  range, a `from-ref` that isn't an ancestor of the branch, a range covering
  suspiciously many or few commits, a detached HEAD, or uncommitted changes to
  the very release-notes folder you're about to write into.

When you ask, ask **well**: state what you already established, name the
specific ambiguity, list the concrete candidates you found and where each came
from, say which one you'd pick and why, and — where it's safe — offer to
proceed with that default. A question the user can answer with one word beats
an open-ended one. Batch every open question you have into a single message
rather than drip-feeding them (see step 7), and never block on a question
whose answer you can look up yourself.

Never paper over an unresolved ambiguity with a `TODO` in the review notes
**when the user is available to settle it** — TODOs are for actions only the
release owner can take (final revision numbers, artefact links), not for
decisions you avoided making or asking about.

## Starting from the currently open repository (nothing named)

When the user asks for release notes **without naming a repository, product,
track or ref** — "generate release notes" and nothing more — they mean the
repository that is currently open. Do **not** ask which repo, which product or
which revision: infer all of it, then state what you inferred and proceed.
Only ask if a specific inference step below genuinely fails.

This is the default path in cross-repo mode. Resolve it like this:

1. **Identify the repository.** Read the workspace's `origin` remote:
   ```bash
   git -C . remote get-url origin    # → git@github.com:canonical/opensearch-operator.git
   git -C . rev-parse --abbrev-ref HEAD
   ```
   Normalise the remote to `owner/repo` (strip `git@github.com:`,
   `https://github.com/`, and a trailing `.git`). If the open workspace is
   **release-notes-builder itself**, this is standalone mode, and a bare
   request has no target — that is the one case where you must ask which
   repository or product to generate for, since this repo is the tool, not a
   product. Ask which repository to use, rather than guessing, if: there is no
   `origin` (list the remotes you did find and ask which to use); the
   workspace isn't a git repo at all; or it's a multi-root workspace with
   several candidate product repos open.
2. **Identify the product** from the repo: its `charmcraft.yaml` /
   `metadata.yaml` display name, its docs (`docs/index.md`, `README.md`), or
   its previous release notes' title. Prefer the product name the existing
   docs use verbatim (e.g. "Charmed OpenSearch", not "opensearch-operator") —
   the document is named after the product, never after one component. If
   these sources disagree on the product name, or the repo could belong to
   more than one product, ask which to use and quote what each source said.
3. **Find the product's release notes inside the open repo** — this is the
   richest source available and the reason this mode is preferred. Search the
   repo's own tree for an existing releases folder; common candidates:
   `docs/reference/release-notes/`, `docs/reference/releases/`,
   `release-notes/`, `docs/releases/`. Take the **newest** document in it,
   determined by the revision/version in the filename or title (e.g.
   `revision-315.md` over `revision-314.md`), not by file mtime. Ask the user
   which to use when **more than one** such folder exists and both hold
   revision-named files, or when the newest document can't be picked
   unambiguously (e.g. per-track subfolders, or files named inconsistently so
   ordering is unclear). Name the candidates and your preferred pick.
4. **Derive everything else from that newest document**, exactly as in
   "Starting from a link to previously published release notes" below — the
   only difference is that the page is a local file rather than a URL, so read
   it from disk instead of fetching it:
   - **from-ref** — the revision/tag it documents. Generate the release
     *after* it; never regenerate the revision it documents.
   - **Track** — from its path or frontmatter, cross-checked against the
     current branch and the docs' default track.
   - **The component list** — every component subheading and Compatibility
     row, which feeds the sibling-component confirmation in step 1.4.
   - **The structure to reproduce** — use it as the reference document for
     template selection in step 2, and save the new document into this same
     folder in step 8, following its naming convention.
5. **Set `to-ref` to the current branch's HEAD** (the default: omit
   `--to-ref`). A bare request means "everything released since the last
   documented release, up to where the branch is now". Use the branch that is
   currently checked out, unless it isn't the resolved track's branch — then
   prefer the track's branch and say so. If HEAD is detached, or the checked-out
   branch belongs to a different track than the newest release notes, ask which
   branch to release from rather than picking silently.
6. **If the repo has no release-notes folder at all**, fall back in this
   order before asking anything: the product's docs site
   (`https://canonical.com/data/<product>/docs/`), then the tag-based
   `from-ref` resolution in step 1.3.b. Ask the user only if both fail.
   Likewise, if the resolved range turns out to be **empty** (nothing merged
   since the last documented release), don't produce an empty document — report
   it and ask whether to pick an earlier `from-ref` or stop.
7. **Report the inferences** in your first substantive reply and in the
   review-notes comment: repository, product, track, branch, `from-ref` and
   the file it came from. The user gave you nothing, so they must be able to
   check every assumption you made — but report it as a statement of what
   you're doing, not as a question blocking the run.

## Starting from a link to previously published release notes

Sometimes the user points at an already-published release-notes page instead
of naming repos/refs directly, e.g. "Create release notes for
https://canonical.com/data/opensearch/docs/2/reference/release-notes/revision-315/".
Treat that page as documenting the **previous** release, not the release to
generate:

1. Fetch the page (`fetch_webpage` for a docs-site URL like this — don't try
   to guess an underlying GitHub file path first). It gives you, for free,
   most of what step 1 (Resolve references) would otherwise have to discover:
   - **Product name** and **track** from the URL path and the page's own
     title/links.
   - **from-ref** for the primary component: the revision/tag documented on
     that page (e.g. `revision-315` → charm revision 315). Generate notes for
     the *next* release after it — from that revision forward to `HEAD` (or a
     `to-ref` the user gives) — never regenerate the revision the link itself
     documents.
   - **The full list of components** the product ships — read every
     component subheading and Compatibility subsection on the page, don't
     stop at the one component the user named in their message (see "Always
     check for sibling components" in step 1 below).
   - **The document structure to reproduce** — use this page directly as the
     "most recent published release notes" source for step 2 (template
     selection); if `templates/<product>.md.j2` doesn't exist yet, build it
     from this page instead of searching elsewhere.
2. Note in the review-notes comment that this link was the source used to
   resolve `from-ref`, the track, and the component list.

## Starting from a revision, version, tag or commit the user names

When the user names a starting point — "release notes from rev247", "since
2.1.0", "changes since revision 315", "from a1b2c3d to HEAD", "everything
after the 3.5.1 release" — that value is `from-ref` and takes priority over
every other source (step 1.3.a). Don't go looking for the last documented
release: the user has already told you where to start. Two things still need
care.

**Resolve the name they used to an actual Git ref.** Users say "revision 315" or
"rev315" or "315"; the repo's tags may be `rev315`, `revision-315`, `315`,
`v2.1.0`, `2.1.0` — or `opensearch/rev315`, namespaced per charm. List **all** the
repo's tags and match, rather than assuming a naming scheme; the mechanics,
including what to do when a number is missing or ambiguous, are in "Resolving a
named revision to a commit" below. Also note:

- A charm *revision* number is not always a Git tag: some products tag releases
  by workload version instead — `kafka-operator`'s `rev*` tags are frozen at
  `rev262` while its newest releases are tagged `v4/1.46.0` — in which case ask
  which tag or SHA corresponds to that revision.
- If the ref exists but is **not an ancestor of the resolved branch** (e.g. it
  was tagged on another track), say so and ask, rather than producing a range
  that spans tracks.
- **Always pass the full ref name to the API.** `compare` and
  `git/refs/tags/...` calls must use `opensearch/rev366`, not `rev366`. A 404
  from `gh api repos/{owner}/{repo}/git/refs/tags/rev366` means *the ref name
  is wrong*, not that the tag is missing — see "Resolving the range and the
  revision number" below.

## Resolving the range and the revision number

Three defaults cover almost every run. Anything the user states explicitly wins
over all of them.

| What | Default |
|------|---------|
| `from-ref` | The **newest release notes already in the repo's docs tree** (usually `docs/reference/release-notes/revision-NNN.md`) — that revision's own tag, **not** that revision + 1 |
| `to-ref` | The **branch HEAD** — the currently checked-out branch for the open repo, else the repo's default branch |
| Revision number in the title | The **highest revision number in the repo's tags**, `+1` if that tag isn't at HEAD |

Two commands produce all three. Read them yourself — there is no script to run:

```bash
# Every tag and branch head, in one unauthenticated, unpaginated request.
# Pipe through the parsing rule below to get the latest revision number; read it
# unpiped to get the branch heads for the HEAD check.
git ls-remote --tags --heads https://github.com/<owner>/<repo>.git

# The newest revision the docs already cover (sort NUMERICALLY, not alphabetically).
ls docs/reference/release-notes/ | grep -oE '[0-9]+' | sort -n | tail -1
```

The revision number needs its own source because the docs can't supply it: when
this was written, `opensearch-operator` documented up to revision 315 while its
tags had reached 366 — a 50-release gap.

### Reading the latest revision out of the tag list

Anchor on the **`rev`/`revision` prefix**, take the **run of digits immediately
after it**, and compare those **numerically**:

```bash
git ls-remote --tags <url> \
  | grep -oiE 'rev(ision)?[-_.]?[0-9]+' | grep -oE '[0-9]+$' | sort -n | tail -1
```

Three properties make that reliable, and each corresponds to a way of getting it
wrong:

- **A run of *adjacent* digits, not every digit in the string.** Deleting all
  non-digits from `opensearch-k8s/rev16` yields **816**, making 816 the apparent
  maximum in `opensearch-operator` instead of 366 — a document titled
  "Revision 817".
- **Anchored on the `rev` prefix, not on the end of the name.** An end-anchor
  (`rev[0-9]+$`) works but is brittle — it breaks the moment a repo appends
  anything to a tag (`rev366-rc1`, `rev366+arm64`). The prefix is the part that
  carries the meaning, so it survives suffixes.
- **Numeric comparison.** `rev9` sorts above `rev100` as a string.

The `rev` anchor is what makes the digit run trustworthy, and it is worth
preferring over a blocklist of known-noisy substrings. `k8s` is the obvious
offender — it contains a digit run, so a bare digit-run scan picks up an `8` from
every `*-k8s/*` tag, which **wins** in any repo whose revisions are still
single-digit (a dashboards-k8s charm at `rev5` would be titled "Revision 9").
Stripping `k8s` fixes that, but the same problem recurs with every other numeric
fragment a tag name can carry — `v4/1.46.0` (→ 46), `preview7/`,
`release-2024-01-15` (→ **2024**, which beats every real revision). Anchoring on
`rev` excludes all of them at once, so the list never has to grow.

In particular, **don't strip years to deal with dates.** A `20[0-9][0-9]` filter
destroys legitimate revisions: `rev2019` … `rev2099` are 81 real revision numbers
that would silently vanish, and this is not hypothetical —
`canonical/postgresql-operator` is already at **rev1215** and
`postgresql-k8s-operator` at rev960, so four-digit revisions are current, not
future. Anchoring on `rev` handles dates without deleting anything.

The regex tolerates the spellings that occur in practice — `rev366`,
`revision-366`, `revision366`, `rev_366` — because tag naming is not consistent
across products. It will also match a `rev` sitting inside a longer word
(`myrevision42`), which is harmless here: a tag has to be *shaped* like a revision
to match at all, and if the number it yields looks wrong against the rest of the
series, that is exactly the case to stop and ask about.

**How often is this anchor actually available?** Surveyed across 14 Canonical
charm repos (opensearch, opensearch-dashboards, kafka, kafka-k8s, kafka-connect,
kafka-ui, karapace, postgresql, postgresql-k8s, mysql, mysql-k8s, mongodb,
mongodb-k8s, spark-k8s-bundle): **all 14 have `rev`-style tags**, and the
rev-anchored answer matched a plain digit-run scan in all 14. So the anchor costs
nothing on real data and only protects against the edge cases. Version-style tags
never won either — revision numbers accumulate far faster than versions (e.g.
postgresql: rev1215 vs a highest version fragment of 374).

Two junk tags worth knowing about, both harmless to this rule: `revundefined`
(in `kafka-operator` and `mongodb-operator` — matches `rev` but yields no digits,
so it drops out) and `edge-v4r4` / `edge-v6r6` (in `mongodb-k8s-operator`).

Two more failure modes, unrelated to parsing:

- **Never use a top-N slice of `/tags`.** `gh api .../tags --jq '.[0:5]'` orders
  refs **lexicographically** — not by date, not by revision number — so a slice
  is "the tags whose names sort highest", and it hid a whole live tag series
  (canonical/opensearch-operator, 2026-09-15: a draft titled "Revision 350" when
  the answer was 366).
- **Peel annotated tags before comparing SHAs.** Release tags are annotated, so
  the ref points at a tag object; `git ls-remote` emits a second `<ref>^{}` line
  with the actual commit. Comparing the unpeeled SHA to a branch head never
  matches, which silently turns a HEAD-tagged release into "latest + 1".

### If nothing matches `rev` at all

This didn't occur in any of the 14 repos surveyed, but it is possible — some
products tag purely by workload version. In that case, *then* fall back to the
biggest run of adjacent digits, having first dropped `k8s` (the one substring
guaranteed to inject a spurious digit into charm tag names):

```bash
git ls-remote --tags <url> | sed 's|.*refs/tags/||;s/k8s//g' \
  | grep -oE '[0-9]+' | sort -n | tail -1
```

**Treat that result as a suggestion to confirm, never as the answer.** Unanchored,
it happily returns a date fragment: on a repo tagged `v1.2.3` /
`release-2024-01-15` it yields **2024**. Present it alongside the tags it came
from and let the user correct it.

Also beware the mixed-scheme case, where the anchor *does* match but is stale:
`kafka-operator` has 170 `rev*` tags frozen at `rev262`, while its 46 newest
releases are tagged `v4/1.46.0`. The highest `rev` number is real but is **not**
the latest release, so cross-check against Charmhub or ask.

Tags may be **namespaced per charm** (`opensearch/rev366`, `opensearch-k8s/rev16`)
in repos where several charms were merged into one codebase, which usually *also*
still hold the old flat `revNNN` tags. You do **not** need to rank namespaces:
revision numbers are monotonic per repo, so the flat series stops where
namespacing began and the plain numeric maximum is right either way. Namespaces
matter for two things only: use the **full ref** in API calls
(`git/refs/tags/opensearch/rev366`, not `rev366` — a 404 on a bare `revNNN` means
the ref name is wrong, not that the tag is missing), and filter by namespace when
you need a **specific charm's** number for the Compatibility table.

### Is the latest tag *at* the branch HEAD?

If the latest tag's **peeled** commit equals the branch HEAD, the release has
already been cut and tagged: title the document with **that** revision, not
latest + 1. Only a tag *behind* HEAD means the document covers the next release.
Getting this backwards shifts the title, the filename, the anchor and the
Compatibility table together.

```bash
refs=$(git ls-remote --tags --heads https://github.com/<owner>/<repo>.git)
echo "$refs" | awk '$2=="refs/heads/<branch>"'          # the branch head
echo "$refs" | grep 'rev<N>^{}'                          # the tag's real commit
```

When the tag is behind HEAD, use `latest + 1` and **leave an imperative TODO in
the review notes for the release owner to verify the final number**: revisions are
allocated in **per-architecture pairs** (`opensearch/rev365` and `rev366` are the
same commit, as are `rev77` and `rev78`), so a new release allocates a whole pair
and the published number may differ. The convention is to title with the
**higher** member of the pair.

### Reading the revision out of the docs, for `from-ref`

Prefer the **filename** (`revision-366.md` → 366): it is the most consistent
signal. Titles vary in wording even within one repo — `# Revision 366` and
`# Revision 168 release notes` both occur in `opensearch-operator` — so if you
match on the title, allow trailing words after the number rather than requiring
the line to end there.

Sort the numbers **numerically**: an alphabetical `ls | tail -1` picks
`revision-9.md` over `revision-168.md`.

### `from-ref` is the documented revision itself, never that revision + 1

The range is **exclusive of `from-ref`** (see "range direction" below), so
`rev315..HEAD` already starts at the first commit *after* the release that
`revision-315.md` documents. Incrementing first applies that offset twice.

This is not a harmless off-by-one. Because revisions are allocated in
per-architecture pairs, consecutive numbers frequently point at the **same
commit** — `rev316` and `rev317` both resolve to `10ec9a90`, so `rev316..rev317`
is **empty** where `rev315..rev317` correctly covers 2 commits. In
`opensearch-operator`, 66 of the 225 consecutive revision pairs between rev100
and rev349 share a commit, so a `+1` default would silently swallow a whole
release about a third of the time. The increment belongs on the **title number**,
never on `from-ref`.

### The four ways a user can specify the range

Whichever end the user pins, the other keeps its default:

| The user says | `from-ref` | `to-ref` | Title revision |
|---------------|-----------|----------|----------------|
| nothing (just the repo) | newest documented revision | branch HEAD | from the tags — confirm it |
| "from 301" | `rev301` | branch HEAD | from the tags — confirm it |
| "to 314" | **the release before 314**, *not* the documented default | `rev314` | **314** |
| "from 299 to 399" | `rev299` | `rev399` | **399** |

Two of these need care:

- **A named `to-ref` sets the title revision.** The document ends at that
  release, so it *is* that revision — no HEAD check and no "+1".
- **"to" alone must not keep the default `from`.** The documented default is
  usually a *later* revision than the user's `to`, which inverts the range into
  silence: `rev315..rev314` yields **zero commits** and an empty document with no
  error. Walk back to the release *before* the requested `to` instead — and skip
  a pair-mate while walking back, since a pair shares a commit and would also
  produce an empty range.

If the user pins both ends, check the direction: `from` must name an *earlier*
release than `to`. Whatever range you settle on, **verify it isn't empty** before
generating — `git rev-list --count <from>..<to>` — because every failure mode
above shows up as an empty document rather than an error.

### Resolving a named revision to a commit

A charm revision number is **not** a git ref, so match it against the repo's real
tags rather than assuming `rev<N>` exists. Two things can go wrong, and both must
be **put to the user with concrete options** rather than guessed:

- **No such tag.** Users name revisions that were never tagged, or that don't
  exist yet — "to 399" when the highest tag is `rev366`. Offer the nearest tags
  below and above and let the user choose. Never substitute a neighbouring
  revision: an off-by-one here shifts every entry in the document.
- **The number is ambiguous.** A repo that tags several charms can carry the same
  number twice at *different commits* — `rev9` and `opensearch-k8s/rev9` are
  unrelated releases of unrelated charms (11 numbers are duplicated this way in
  `opensearch-operator`). List both tags with their commits and ask which is
  meant. Two tags on the *same* commit are just a naming artefact, not a real
  choice — take the namespaced one.

```bash
# Everything carrying a given revision number, with the commit each resolves to.
git ls-remote --tags https://github.com/<owner>/<repo>.git | grep -E 'rev<N>(\^\{\})?$'
```

A 7–40 character hex string is a commit SHA and needs none of this; use it
directly.

### When the user pinned neither end, propose and confirm

If the request named no revisions, infer all three values, then **put them to the
user for confirmation or override before generating** — one short message, with
the reasoning visible so a wrong inference is obvious at a glance:

```text
  from-ref:  rev315   <- newest documented release notes (revision 315)
             (exclusive: the document starts at the next commit)
  to-ref:    opensearch/rev366 (branch HEAD)
  revision:  366   <- opensearch/rev366 is at the branch HEAD, so this release is
                      already tagged
```

Batch this with the other step-1 questions (sibling components, auto-sort) rather
than sending it on its own. If the user confirms, proceed; if they override any
value, use theirs verbatim. Record both the inference and their answer in the
review notes.

### Never generate a revision at or below one already documented

Before finalising the number, check what the repo already documents:

```bash
ls docs/reference/release-notes/            # or the repo's own notes folder
git log --all --name-only --pretty=format: -- docs/reference/release-notes
```

The git-history half matters: a correct `revision-366.md` can exist in history
(or on another branch) while a fresh draft is being numbered 350. **If any
documented revision is greater than or equal to your number, stop and ask the
user** — do not generate, and do not overwrite. This checks the *conclusion*
rather than the inference, so it catches a bad revision number regardless of
what caused it. Present the conflicting file(s) and ask whether to document a
later revision, update the existing document, or use a different `from-ref`.

## Starting from a revision the user names: range direction

**The range is exclusive of `from-ref` and inclusive of `to-ref`.** The builder
reports changes *after* `from-ref`, so "from revision 315" produces the release
*following* 315 — the same convention as starting from a published
release-notes page. If the user's phrasing suggests they meant to *include* the
named release ("the release notes for revision 315 itself", "document rev315"),
that's the opposite intent: they want `from-ref` to be the revision *before*
it. When the phrasing is genuinely ambiguous, ask which they mean — getting
this wrong shifts every entry in the document by one release.

Also note:

- **An explicit `to-ref`** ("from rev247 to rev248", "up to 2.2.0") is used
  verbatim; resolve it to a tag the same way. Without one, `to-ref` stays the
  branch HEAD.
- **Derive the title from `to-ref`** when the user gave one (e.g. `rev248` →
  "Revision 248"); when `to-ref` is HEAD, the release being documented is the
  *next* revision after `from-ref`, so title it accordingly and leave an
  imperative TODO to confirm the final published number.
- **A user-named `from-ref` doesn't remove the need for the other discovery
  steps.** Still resolve the track, still check the product's previous release
  notes for sibling components (step 1.4) and for the document structure to
  reproduce (step 2) — the user pinned the range, not the scope or the format.
- **Per-repo refs differ.** In a multi-component product, a revision number
  the user gives usually applies to the *primary* charm only; resolve each
  sibling component's own `from-ref` normally, and don't apply the primary's
  tag name to repos that don't have it.

## First release: a product with no release notes yet

A product may have no published release notes at all — a new charm, or one
whose notes have never been written. Nothing above can then supply `from-ref`,
the component list, the structure, or the save location, so handle it
explicitly instead of failing or inventing values.

First, **be sure that's actually the case**: absence of evidence here is easy
to get wrong. Check the repo's own tree (all the candidate folders in
"Starting from the currently open repository"), the product's docs site, and
`$BUILDER_HOME/release-notes/` for a previously generated document. Say
explicitly that you found none — don't let it pass silently, since the user
may know where they live.

Then adapt each step:

1. **`from-ref`** — there is no last-documented-release to start after. Use
   the latest tag/release that is an ancestor of the branch (step 1.3.b) if the
   repo has tags. If it has **no tags either**, this is a genuine first
   release: propose the repo's first commit (
   `git rev-list --max-parents=0 HEAD`, or the earliest commit on the branch)
   so the document covers the project's whole history, and confirm that with
   the user before generating — a first-release changelog can be very long,
   and they may prefer a shorter starting point.
2. **Template** — this is the one legitimate use of
   `templates/base.md.j2`: with no published notes to model on, there is no
   established structure to reproduce, so the generic DA186 skeleton is
   correct. The prohibition in step 2 applies only to products that *do* have
   published notes. Don't fabricate a `templates/<product>.md.j2` from a
   sibling product's notes — but do reuse the same product's template if one
   already exists for another of its components.
3. **Sibling components** — step 1.4's discovery source doesn't exist. Fall
   back to the repo itself: a bundle or Terraform module listing companion
   charms, `charmcraft.yaml`/`metadata.yaml` resources naming a rock or snap,
   or an obvious `*-k8s-operator` counterpart in the same org. Present
   whatever you find and ask which components this document should cover —
   still never adding one silently.
4. **Compatibility** — there is no previous table to bump, so build it from
   the repo's own sources of truth (`charmcraft.yaml` platforms/bases,
   `metadata.yaml`, snap/rock metadata, the release tag's assets). Ask for any
   value with no source in the repo rather than leaving the table thin.
5. **Introduction** — write it as a first release: what the product is and
   what it now supports, rather than a diff against a predecessor. Avoid
   phrasing that implies a previous revision the reader could consult.
6. **Save location** — step 8's "mirror the existing folder" rule has nothing
   to mirror. Ask the user where the product's release notes should live, and
   propose the conventional path for the repo's docs layout (e.g.
   `docs/reference/release-notes/revision-<N>.md` if the repo already uses a
   Diátaxis `docs/reference/` tree). Create the folder only once the user
   confirms it.
7. **Record it** — note in the review notes that this is the product's first
   release-notes document, which sources you checked to establish that, and
   the starting point the user agreed to.

## Track / channel scope (single track by default)

For products that release on multiple tracks (e.g. Spark's 3.4 / 3.5 / 4.0, or
Kafka's multiple tracks), **generate release notes for a single track by
default** — do not cover every track in one document unless the user
explicitly asks for a multi-track/product-wide document or a specific track.

1. If the user names a track ("the 3.5 track", "kyuubi-k8s 4.0", a channel
   like `14/stable`), use it.
2. Otherwise, default to **the documentation's default track** — the version
   selector's pre-selected/default version on the product's docs site (e.g.
   `https://canonical.com/data/<product>/docs/` redirects to or highlights
   one version; that's the default). This is usually also the repos'
   default branch track (e.g. `3.5/edge` when the repo's `default_branch` is
   `3.5/edge`), but the docs site is the authoritative source — confirm the
   two agree, and if they disagree, ask the user.
3. If the default track cannot be determined confidently, ask the user which
   track to generate release notes for before proceeding — do not guess and
   do not silently generate a multi-track document.

When scoped to a single track, every per-repo `--branch`/`--from-ref`/
`--to-ref` below refers to that track's branch only (e.g. `3.5/edge`,
`track/3.5`) — not the repo's other tracks.

## Auto-sort: reclassifying the "Other improvements" catch-all

"Other improvements" is the builder's `DEFAULT_CATEGORY` — every entry whose
PR carries no recognised label lands there (see "Label → category mapping" in
the README). In practice most Data charm PRs are unlabelled, so this one
category routinely swallows the majority of a release's entries, including
genuine features and bug fixes. Observed in real runs: 59 of 65 entries for
Charmed Apache Kafka, and **67 of 67** for Charmed OpenSearch, whose previous
published release notes nonetheless had populated Features and Bug fixes
sections — proving the catch-all was hiding real content.

**Auto-sort** is an optional pass that walks every entry in "Other
improvements" and moves the ones whose own text unambiguously identifies a
more specific DA186 category, using conventional-commit prefixes and entry
titles as the evidence.

### Default: off, but always offered

Auto-sort is **off by default**. Do not run it silently.

1. If the user's request explicitly enables or disables it, obey that and do
   not ask (see "Recognising explicit instructions" below).
2. Otherwise, **ask once**, batched with the other step-1 questions where
   possible. Ask *after* the per-repo drafts exist, so the question can be
   quantified — e.g. "48 of 67 entries are in Other improvements; 14 of them
   look like features or bug fixes by their commit prefix. Run auto-sort?".
   A question the user can answer with real numbers in front of them is far
   more useful than an abstract one.
3. If the user declines or does not answer, leave every entry where the
   builder put it and fall back to the conservative behaviour in step 4's
   "Categorisation" bullet (flag, don't move).

### Recognising explicit instructions

Treat any of these as switching the feature **on**: "auto-sort on",
"autosort", "auto sort", "enable auto-sort", "sort the other improvements",
"sort the kitchen sink", "recategorise the catch-all", "reclassify entries by
commit prefix", "use conventional commits to categorise". Treat these as
switching it **off**: "auto-sort off", "no auto-sort", "disable auto-sort",
"don't recategorise", "don't move entries", "leave the categories alone",
"keep the builder's categories". Hyphenation, spacing and capitalisation are
irrelevant (`auto-sort`, `autosort`, `Auto Sort` are the same instruction).
If an instruction is ambiguous ("sort the changelog" — sort *how*?), ask
rather than assume.

### What auto-sort may move, and on what evidence

Move an entry **only** when its own text carries one of the signals below.
The entry text is never rewritten — auto-sort reorders entries between
categories, it does not edit them.

| Evidence in the entry text | Move to |
|---|---|
| `feat:` / `feature:` prefix | Features |
| `fix:` / `bugfix:` / `bug-fix:` / `hotfix:` prefix | Bug fixes |
| Title starts with a fix verb: "Fix …", "Fixes …", "Fixed …", "Fixing …", "Resolve …", "Correct …" | Bug fixes |
| `security:` prefix, or a `CVE-NNNN-NNNNN` reference | Security |
| `!` before the colon (`feat!:`, `refactor!:`), or "BREAKING CHANGE" | Breaking changes |
| `perf:` prefix | Features |
| `revert:` prefix | Leave in place, and flag it (a revert may belong with whatever it reverted) |

Prefixes that are **already** correctly served by "Other improvements" and
must never trigger a move: `chore:`, `docs:`, `ci:`, `cicd:`, `build:`,
`deps:`, `test:`, `style:`, `refactor:` (without `!`), `patch:`.

A leading bracketed Jira tag does not hide a prefix: `[DPE-4546] fix: …` is a
`fix:` entry, and a scope is likewise transparent (`feat(api): …` is `feat:`).

**A neutral prefix takes precedence over a fix verb appearing later in the
title.** `patch: Fix tag in metadata.yaml` and `docs: Fix spread install in GH
workflow` are settled by their `patch:`/`docs:` prefix and stay in "Other
improvements" — do not flag them, because the author already classified them.
Only consult the fix-verb rule when the entry has no conventional-commit
prefix at all.

The only exception to prefix precedence is a breaking or security signal:
`refactor!:` is a breaking change despite the neutral `refactor` type, and a
`CVE-NNNN-NNNNN` reference makes an entry a Security entry even when the
prefix is `fix:` or `deps:`.

### The exception that matters most: infrastructure-only fixes

A `fix:` prefix does **not** justify moving an entry to "Bug fixes" when the
fix targets the project's own tooling rather than the shipped product. DA186's
"Bug fixes" means user-visible defects; a repaired CI job is an "Other
improvement". Keep an entry in "Other improvements", despite a fix signal,
when its text refers to: CI, GitHub Actions, workflows, runners, permissions,
linting, spread/tox/pytest setup, test fixtures or flaky tests, release
plumbing, tags, version pinning, build caches, or documentation builds.

Match these terms as **whole words**, not as fragments. Several are short enough
to hide inside ordinary product vocabulary: `ci` sits inside "precision",
"decision", "explicit", "specific", "capacity", "circuit" and "efficiency";
`tag` inside "stage"; `pin` inside "pinning"; `build` inside "builder". Treating
them as substrings would withhold genuine bug fixes such as "fix: precision loss
in shard allocation". Do count inflected forms ("tests", "tagging", "caches")
and treat `_` as a word boundary, so "test" is found in
`test_certificate_transfer`.

Note the difference between this list and the neutral-prefix list above, which
overlap on `ci`, `test` and `build`. A neutral **prefix** records what the author
declared the change to be, and needs no flag. An infrastructure **term** describes
what a fix targets, and is only consulted once a fix signal is already present.
So `ci: re-enable cached builds` stays put unflagged, while `fix: re-enable CI
cached builds` stays put *and* is flagged.

Verified examples of `fix`-signalled entries that must NOT move:
"fix: Fix spread installation", "fix: Fix tutorial test", "patch: Fix tag in
metadata.yaml", "Fix charm Build", "fix: action permissions",
"fix: release output name", "fix: use full chain in test_certificate_transfer".

Verified examples that legitimately do move to Bug fixes:
"fix: handle the situation that opensearch_failover does not exist",
"fix: set blocked status for invalid object-storage secrets",
"fix: add missing LIBID to notifications manager".

When a fix signal is present but you cannot tell from the title whether the
target is shipped behaviour or tooling, **leave the entry in place and flag
it** — a wrong move is worse than an unsorted entry, because it silently
misrepresents the release.

### What auto-sort will not catch

Auto-sort keys off signals in the text, so an entry with no conventional-commit
prefix and no fix verb is never moved, however feature-like it reads. Verified
misses from a real Charmed OpenSearch range: "add smtp support" (#789) and "add
rollback compatibility" (#786) are both plainly features but carry no `feat:`
prefix, so auto-sort leaves them in "Other improvements". Enabling auto-sort
therefore **reduces** the manual review burden; it does not remove it. Still
read the catch-all afterwards.

This is deliberate. Guessing from prose ("add …", "support …", "introduce …")
would move CI and docs entries too, and a wrong move misrepresents the release
in published notes. Precision is worth more here than recall.

### Auto-sort is per-component

Run the pass separately within each component's block. Never move an entry
from one component to another; components are separate charms with separate
revisions.

### Every move must be recorded

Auto-sort changes what the published document claims about each change, so it
must be auditable. In the review-notes comment, state that auto-sort ran, and
list every entry it moved as `PR #N: "<title>" — Other improvements → <new
category> (evidence: <the signal>)`. Also list entries that carried a signal
but were deliberately left in place, with the reason. The release owner must
be able to reverse any single decision without re-deriving it.

If auto-sort moves nothing, say so explicitly rather than omitting the note.

## Keep data gathering lean

The reference-resolution phase (step 1) is the easiest place to burn an
excessive number of tool calls. With a single track in scope, it should take
a small, roughly-fixed number of calls regardless of how many repos are
involved. Follow these rules:

- **Batch, don't loop tool calls.** Never make one `gh api`/terminal call per
  repo per question. Write one shell loop (or one `gh api` call with a
  `--jq` that handles multiple items) that gathers the same fact for every
  repo in a single terminal invocation. Budget roughly 3–4 terminal calls
  total for step 1 across all repos, not 3–4 per repo.
- **Trust tags/releases first; don't mine docs speculatively.** Try
  `from-ref` priority (a) and (b) (user-specified, then latest tag/release
  that's an ancestor of the branch) with one batched call per check. Only
  fall through to (c) — searching the docs for the last documented release
  — for repos where (a)/(b) genuinely failed, and even then fetch the
  *single* release-notes page for the resolved track, not every revision
  page across every track/branch.
- **List tags completely and cheaply — never a top-N slice.** Use
  `git ls-remote --tags --heads https://github.com/<owner>/<repo>.git` (one
  call, no auth, no pagination, and it returns the branch heads in the same
  response so the HEAD check below is free), or
  **Do not** use
  `gh api repos/{owner}/{repo}/tags --jq '.[0:5]'`: that endpoint orders refs
  *lexicographically*, not by date or revision number, so a slice is not "the
  newest few tags" — it is "the tags whose names sort highest". See "Resolving
  the range and the revision number" for the real-world failure this caused.
- **Don't reverse-engineer arch→revision mapping from CI logs.** Fetching
  GitHub Actions workflow runs, then jobs, then full logs, then grepping
  them (per repo, per track) is by far the most expensive way to learn which
  charm/snap revision is AMD64 vs ARM64. Default to a cheap heuristic
  instead: take the latest tag pair for the branch (the two highest
  consecutive revision numbers are almost always the amd64/arm64 pair from
  the same release run) and mark the pairing itself as a TODO for the
  release owner to verify — don't spend calls confirming it via logs unless
  the user explicitly asks for verified per-architecture revisions.
- **Don't probe unknown APIs interactively.** Charmhub's `api.charmhub.io`
  requires a macaroon and will not return channel maps anonymously — don't
  try it. The Snap Store v2 API works without auth but requires the
  `Snap-Device-Series: 16` header (`curl -s -H "Snap-Device-Series: 16"
  https://api.snapcraft.io/v2/snaps/info/<snap>`); use it directly instead of
  trial-and-erroring the request shape.
- **Resolve the track once, cheaply.** One `fetch_webpage` of the product's
  docs landing page (or one `gh api repos/{owner}/{repo} --jq .default_branch`
  for the primary repo) is enough to confirm the default track — don't
  cross-check every repo's `default_branch` individually unless one
  disagrees with the others.
- If a step would need more than ~2 calls for a single repo, stop and ask
  whether the user wants that level of verification, rather than spending
  the calls automatically.

## Inputs (ask only if not given)

| Input | Default | Notes |
|-------|---------|-------|
| Repositories | **The currently open repository** (from its `origin` remote) | `owner/repo` or full GitHub URL; one or more. Never required: a bare request means the open repo — see "Starting from the currently open repository" |
| Previous release notes link | — (optional alternate to naming repos) | A URL to an already-published release-notes page (e.g. a `revision-NNN` docs page); resolves product, track, from-ref, and component list — see "Starting from a link to previously published release notes". The open repo's own newest release-notes file serves the same purpose automatically |
| Track | The documentation's default track (see above) | Ask if it can't be determined |
| Branch | The track's branch (repo default branch if single-track product) | Resolve via GitHub API |
| From-ref | **The newest release notes already in the repo's docs tree** (that revision's tag, *not* +1); then the docs site, then the latest ancestor tag, then the first commit (first release), then ask | Tag/SHA/branch, or a revision/version the user names — see "Resolving the range and the revision number" |
| To-ref | **HEAD of the branch** — the checked-out branch for the open repo, else its default branch | Tag/SHA/branch |
| Revision number (title) | **The highest revision number in the repo's tags**; that revision if the tag is at HEAD, else the first number no tag or document already uses | The docs can't supply this — tags routinely run dozens of revisions ahead of published notes |

When the user pinned **neither** end of the range, infer all three and **put them
to the user for confirmation or override** before generating (see "When the user
pinned neither end, propose and confirm").
| Product name / title | Derived from repos | e.g. "Charmed Apache Kafka" |
| Auto-sort | **Off** | Reclassify the "Other improvements" catch-all by conventional-commit prefix. Ask once if not specified; the user can say "auto-sort on/off" — see "Auto-sort" above |
| Output file | See step 8: the target repo's existing release-notes location when run cross-repo, else `release-notes/<product>-<to-ref>.md` | Ask the user if no existing location can be found in the target repo |

If the user gives only repositories — or nothing at all — proceed with
defaults and only ask about genuinely ambiguous things (see "Ask the user"
below).

## Procedure

### 1. Resolve references

First, if the user named no repository, resolve the target from the currently
open workspace and its own release notes (see "Starting from the currently
open repository" above). That single step usually settles the repo, product,
track, `from-ref` and component list at once, so do it before the batched
resolution below and treat its results as "user-specified" for the priority
rules that follow.

Then resolve the track scope (see "Track / channel scope" above) — this is
a fixed, small cost regardless of repo count (see "Keep data gathering lean").
Then resolve refs for all repositories **in one batched pass**, not
repo-by-repo:

1. Determine the branch for the resolved track for every repo with a single
   shell loop, e.g.:
   ```bash
   for r in repo1 repo2 repo3; do
       branch=$(gh api "repos/canonical/$r" --jq '.default_branch')
       echo "$r $branch"
   done
   ```
   (user-specified branch/track overrides this per repo where given).
2. Determine `to-ref` for every repo: user-specified, else omit `--to-ref`
   when invoking the builder script (it defaults to branch HEAD) — no API
   call needed here.
3. Determine `from-ref` for every repo (in priority order, batching each
   check across all repos before moving to the next priority level):
   a. User-specified ref — a revision, version, tag or SHA named in the
      request. Resolve the name to a real tag and settle the
      inclusive/exclusive question per "Starting from a revision, version,
      tag or commit the user names" above.
   b. **The default:** the newest release notes already published in the
      product's documentation — the newest release-notes file in the repo's
      own docs tree (`docs/reference/release-notes/`), which needs no network
      and is the product's own record of what has been documented. Failing
      that, fetch the *one* release-notes page for the resolved track (not
      other tracks) from the docs site. Use the revision/tag it documents.
   c. Only for repos where (b) didn't resolve: the most recent tag that is an
      ancestor of the branch. List **every** tag for all repos in one loop —
      never a top-N slice of `/tags` (see "Resolving the range and the revision
      number"):
      ```bash
      for r in repo1 repo2 repo3; do
          echo "== $r"
          git ls-remote --tags --heads "https://github.com/canonical/$r.git"
      done
      ```
      Then take the numerically highest revision, and confirm ancestry with one
      `compare` call per candidate tag — using the **full namespaced ref**.
   d. If the product has no release notes and no tags at all, treat it as a
      first release — see "First release: a product with no release notes
      yet" above — and confirm the starting point with the user.
   e. If neither can be determined, ask the user which ref to start from.
4. **Check for sibling components not named by the user.** Even when the
   user names (or links to) only one main charm/repo, a product's release
   notes often cover additional components that ship alongside it — a
   companion charm (e.g. a dashboards/UI charm), a snap, a rock, a Terraform
   module, COS/Grafana dashboards, etc. Before finalizing scope:
   a. Look at the product's most recently published release notes (the same
      page used to resolve `from-ref` in step 1.3, or the link from
      "Starting from a link to previously published release notes") and list
      every component subheading / Compatibility subsection it contains.
   b. **Ask the user before adding any detected sibling component that they
      didn't name.** Never add it to scope silently, even by default. List
      the detected component(s) (name + where you found them, e.g. "found
      `opensearch-dashboards` as a component in revision-315's release
      notes") and ask, in one batched question, whether to include each of
      them in this release-notes document. Proceed only with the ones the
      user confirms; skip a component the user declines, and note the
      decision in the review notes either way. Skip this ask entirely only
      if the user's original request already explicitly restricted scope to
      a single named component (e.g. "just the charm, nothing else").
   c. For every sibling component the user confirms, resolve its
      branch/from-ref/to-ref the same way as the named repo(s), check it for
      changes in range, and include it in the merged draft (or carry over
      its unchanged Compatibility entry, per step 6).
   d. If a confirmed sibling component can't be automatically mapped to a
      GitHub repo (e.g. it's a UI-only or docs-only entry with no obvious
      repo, or a name that doesn't match any `canonical/*` repo), **ask the
      user for that repository's address** (batch this with the step 1.4.b
      confirmation question when possible) rather than guessing or silently
      dropping it. Only fall back to a `TODO` in the review notes if the
      user doesn't know the repo either.
   e. Record in the review notes which components were added this way (and
      that the user confirmed them, and supplied the repo address if it
      wasn't auto-mapped) or explicitly declined.
5. **Settle each component's title revision, then guard it.** For every
   component in scope, take the numerically highest revision tag and decide
   whether it is *at* the branch HEAD — in which case the release IS that
   revision — or *behind* it, in which case use the first number no tag or
   document already uses (proposed, not confirmed). Each charm has its own
   revision series, so do this per component; never carry the primary charm's
   number across to a sibling. Then run the discrepancy check in "Never
   generate a revision at or below one already documented" against the repo's
   release-notes folder **and its git history**, and stop to ask the user if
   anything at or above your number is already documented. Finally, if the user
   pinned neither end of the range, put the inferred `from-ref`/`to-ref`/revision
   to them for confirmation. See "Resolving the range and the revision number".

Record which source was used for each repo — it goes into the review notes.
If a repo's default branch is a single-track repo (e.g. `spark-k8s-toolkit-py`
with only `main`), it needs no track disambiguation at all — resolve it like
any single-branch repo.

### 2. Select or create the product template

Before generating any draft, decide which Jinja template to render with.
**Never** fall back to `templates/base.md.j2` for a product that has published
release notes of its own — the base template produces a generic DA186 skeleton
that will not match the product's established structure, links or section
names. The single exception is a product with **no** published release notes,
where there is no established structure to match and the base template is the
right choice (see "First release: a product with no release notes yet").

1. **Look for an existing product template** in `$BUILDER_HOME/templates/`
   (see "Locating the builder script and templates" above — this is
   `templates/` at the release-notes-builder repo root, not the currently
   open target repo). Match on the *product*, not the repository:
   `templates/spark.md.j2` covers every Charmed Apache Spark repo
   (`spark-k8s-bundle`, `kyuubi-k8s-operator`, `charmed-spark-rock`,
   `spark-client-snap`, …), just as `templates/kafka.md.j2` covers the Kafka
   repos. List the directory rather than guessing a filename. If it's unclear
   whether an existing template belongs to this product (e.g. the product
   could plausibly map to two of them), ask rather than rendering through a
   template that may not match.
2. **If no template matches, create one** from the product's existing
   published release notes — do not proceed with the base template:
   a. Find the product's most recent published release notes. Best sources,
      in order: the currently open target repo's own releases folder if it
      has one (e.g. `docs/reference/release-notes/`, `docs/reference/releases/`
      — this is very likely, since that repo is the product's own repo in
      cross-repo mode, and this same folder is also where step 8 will save
      the new document), the product's docs site
      (`https://canonical.com/data/<product>/docs/<track>/reference/releases/`),
      or a previously generated document in `$BUILDER_HOME/release-notes/`.
      **If none of these yields any published release notes**, stop here and
      use `base.md.j2` — this is a first release (see "First release: a
      product with no release notes yet"). Don't model the template on a
      *different* product's notes, and don't write a
      `templates/<product>.md.j2` with invented structure; the product's
      conventions will be established by this very document.
   b. Read it in full and extract the structure that must be reproduced:
      frontmatter, title format, date format, intro wording, the links line,
      the **section names and their order** (products often rename or add
      sections — e.g. Spark uses "Enhancements" instead of "Other
      improvements" and adds "Documentation improvements", "Security" and
      "Acknowledgements"), per-component subheadings, entry link format, and
      the exact shape of the Security and Compatibility tables.
   c. Write `$BUILDER_HOME/templates/<product>.md.j2` that
      `{% extends "base.md.j2" %}` and overrides the blocks it needs:
      `frontmatter`, `title`, `date_line`,
      `introduction`, `intro_links`, `changelog`, `security`,
      `compatibility`, `known_issues`, `footer`. Map the builder's fixed
      categories (`Features`, `Breaking changes`, `Security`, `Bug fixes`,
      `Other improvements`) onto the product's section names inside the
      `changelog` block; leave product-specific sections the builder can't
      populate (CVE tables, per-component grouping) as clearly marked `TODO`
      comments for the polish pass.
   d. Head the template with a comment block explaining what it reproduces,
      how it differs from `base.md.j2` and why, and where the reference
      release notes live.
   e. Verify it renders: run the builder once against it and check the output
      before generating the real drafts. Also re-render `base.md.j2` and any
      other product template if you changed the base, to catch regressions.
3. **Name the document after the product, never after one component.** A
   Charmed Apache Spark release-notes document is titled "Charmed Apache
   Spark", even when the only repository in range is `spark-k8s-bundle` (the
   Terraform module). If the resolved scope covers a single component of a
   larger product, say so in the review notes and intro — do not retitle the
   document after that component.

### 3. Generate per-repo drafts

Create one system temp directory for this run's intermediate drafts, e.g.
`TMPDIR_DRAFTS=$(mktemp -d)` — never write intermediate files into either
repo's tree (neither `$BUILDER_HOME` nor the currently open target repo).
Then run the automation script once per repository, using `$BUILDER_HOME`
(see "Locating the builder script and templates" above) to find the script
and template:

```bash
python "$BUILDER_HOME/build_release_notes.py" \
    --repo <owner/repo> \
    --from-ref <from-ref> \
    [--to-ref <to-ref>] \
    [--branch <branch>] \
    --template "$BUILDER_HOME/templates/base.md.j2" \
    --title "<Component name>" \
    --use-prs \
    --output "$TMPDIR_DRAFTS/<repo>-draft.md"
```

Notes:
- Use the template resolved in step 2 (an existing
  `$BUILDER_HOME/templates/<product>.md.j2`, or the one you just created).
  `templates/base.md.j2` is only appropriate for a product with no published
  release notes to model on.
- `--use-prs` gives cleaner entries (PR titles) — prefer it.
- If the script warns that the commit range was **truncated** (>250 commits),
  re-run with `--from-ref <last-sha>` for the remainder and merge the two
  outputs, or ask the user how to proceed.
- If a repo has no changes in the range, skip it and note that in the review
  notes.

### 4. Merge the drafts and polish the changelog

Read every per-repo draft directly (they are short — typically well under
200 lines each) and merge + polish them **in a single pass**. Do not use a
separate merge script: the agent must read every draft's full content to
polish it anyway, so pre-merging mechanically first only adds an extra file
and a class of formatting bugs (verified: a naive text-based merge script
left dangling empty component headings when a component had a populated
compatibility table but zero changelog entries).

For a single repository, its draft is already the changelog — skip straight
to polishing.

For multiple repositories, build the merged "List of changes" like this:

- One `## <Component name>` heading per repository **that has at least one
  changelog entry**. Skip (omit entirely — no heading) components with zero
  changes in range; note the skip in the review notes.
- Under each component heading, one `### <Category>` subheading per
  category that has entries, in DA186 order: Features, Breaking changes,
  Security, Bug fixes, Other improvements. Omit empty categories.
- Carry every entry over verbatim (message text, Jira links, PR link,
  commit link) — merging is a reorganisation, not a rewrite.
- After all components, a single `## Compatibility` heading (see step 6).
- **No adjacent headings with nothing between them.** Every heading (`#`,
  `##`, `###`, ...) must be followed by at least a short sentence of body
  text before the next heading — even a one-line lead-in — never let one
  heading immediately follow another with zero text in between. This
  applies throughout the document: the title, the "List of changes"
  heading, each component/category heading, and the "Compatibility"
  heading and its subsections. If a section would otherwise have no natural
  lead-in (e.g. a category with only a bullet list), add a brief one-clause
  intro such as "This release includes the following bug fixes:".

While merging, check for obvious mistakes that can be fixed **without
altering the facts**:

- **Duplicates**: the same change appearing twice (e.g. a PR merged then
  reverted, or sync PRs between k8s/VM variants of the same charm). Remove
  exact duplicates; for near-duplicates across components, keep both but
  flag them in the review notes.
- **Categorisation**: entries with `fix:`/`Fix ...` in the message sitting
  outside "Bug fixes", or `feat:` outside "Features" — the builder maps PR
  labels, which are often missing. It understands two label vocabularies at
  once (see "Label → category mapping" in the README): the DA186 category
  labels (`Features`, `Breaking changes`, `Security`, `Bug fixes`, `Other
  improvements`) and the legacy ones (`bug`, `enhancement`, `not bug or
  enhancement`, `documentation`, `breaking`), so a repo may mix both.
  Anything unlabelled lands in "Other improvements", which is where most
  miscategorisation shows up.
  - **If auto-sort is enabled** (see "Auto-sort" above), run its pass now,
    per component, and record every move in the review notes.
  - **If auto-sort is off**, recategorise only when the message itself is
    unambiguous (e.g. a `fix:` prefix on a change to shipped behaviour).
    Otherwise leave the entry and flag it.
- **False Jira IDs**: the builder script links any `[A-Z][A-Z0-9]+-\d+`
  pattern as a Jira ticket. It automatically excludes `CVE-*` (Common
  Vulnerabilities and Exposures IDs, e.g. `CVE-2026-1234` truncated to
  `CVE-2026` in a title — never a Jira ticket) from linking. Other non-Jira
  strings can still slip through, such as `SHA-256`, `UTF-8`, `ISO-8601`,
  `RFC-822`, `SCTE-35`, or a GitHub username that happens to match the
  pattern (verified) — drop the fake link when the "ticket" is clearly not
  a Jira ID (not in a known project prefix like `DPE-`, `DA-`, `PRA-`,
  `KP-`, etc.), but leave the surrounding text untouched. If a new
  systematic false-positive prefix is found (like `CVE`), add it to
  `NON_JIRA_PREFIXES` in `build_release_notes.py` instead of special-casing
  it by hand every time.
- **Noise**: entries like "sync with k8s", "rename tests", CI-only churn —
  keep them (they belong in "Other improvements") but consider grouping
  trivial docs/CI entries; never delete a change outright.
- **Formatting**: broken Markdown links, stray `\[[` escapes, empty
  parentheses, trailing whitespace, entries missing PR links.
- **Code-like tokens**: wrap filenames, modules, CLI flags and config keys
  that appear in PR titles in backticks — `` `charm.py` ``,
  `` `metadata.yaml` ``, `` `README.md` ``, `` `test_charm.py` ``. Doing this
  here saves two classes of failure in step 9: the spellchecker flags them as
  misspelled words, and MyST's linkify turns anything shaped like a domain
  into a link, so a bare `charm.py` becomes a broken `http://charm.py` — and a
  bare `README.md` becomes `http://README.md`, which *resolves*, to a domain
  squatter. Don't hunt for these by eye: step 9 runs
  `tools/check_autolinks.py`, which decides using the same library MyST uses.
- **Typos in PR titles**: PR titles are copied verbatim, so their authors'
  misspellings come along. Correct them (`acomodating` →
  `accommodating`). A spelling correction doesn't change what the entry
  says, so it isn't covered by the "never rewrite a message" rule below.
- **Facts**: never rewrite a message to say something different, never
  invent Jira IDs, PR numbers, versions, or dates.

### 5. Write the introduction

Based on the contents of the merged draft, write the intro (replacing the
`INTRO-TODO` / TODO comment):

- 1–3 paragraphs, brief summary of the most important changes (new features,
  breaking changes, workload version bumps). Write it as the final,
  publishable summary — see "Fully publishable output" below; do not call
  the document a draft anywhere in this text.
- **For a first release** there is no predecessor to diff against: introduce
  what the product is and what this release supports, and don't imply an
  earlier revision the reader could compare with or upgrade from.
- Below it, the links line per DA186: Charmhub | Deploy guide | Upgrade
  instructions | System requirements. Derive the URLs from the product's
  docs (e.g. `https://canonical.com/data/docs/<product>/iaas/...`); if the
  product is unknown, leave `TODO` links and flag them for the user.

### 6. Populate the Compatibility section

Build a single `## Compatibility` heading at the end of the document, and
ensure it is correct and up to date:

- **Single repository**: carry over its per-repo compatibility table as-is
  (it already matches the product template's structure, e.g.
  `templates/kafka.md.j2`).
- **Multiple repositories**: add one `### <Component name>` subsection per
  component that has compatibility info, each with its own table, so the
  section stays a single source of truth for the whole product release.
  Include a component here even if it had zero code changes in range (its
  current revision/version is still part of what ships), unless the user
  says otherwise.
- For each component: charm revision (from the `to-ref` tag, e.g. `rev248`,
  or from the repo's latest release), hardware architecture, workload/rock/snap
  versions, and minimum/recommended Juju version. Take the revision from the
  component's **own** tag series (filter the tag list by its namespace) — not
  from a flat legacy tag and not from another charm's series in the same repo.
- Sources of truth: the repo's `charmcraft.yaml` (`platforms`/`bases`),
  `metadata.yaml`, `snapcraft.yaml` or rock's `rockcraft.yaml`, the release
  tag's assets, and the previous release notes' compatibility table (bump
  what changed).
- **Cheap arch→revision pairing**: charms released per-architecture allocate
  revisions in pairs, and both tags point at the **same commit** — so read the
  pairing straight off the peeled SHAs in `git ls-remote` output rather than
  mining workflow logs (see "Keep data gathering lean"). Two tags sharing a
  commit are the AMD64/ARM64 pair; `opensearch/rev365` and `rev366` are one
  release. Tags in *different* namespaces are different charms, never a pair.
  Mark the arch→number assignment within the pair as a TODO to verify.
- If a value cannot be determined from the repo, **ask the user for it** —
  batched with your other questions in step 7 — rather than guessing. Only
  fall back to a clearly marked `TODO`, flagged in the review notes, for
  values the user can't supply either or that genuinely can't be known until
  release time (e.g. the final published revision number).
- If two sources give conflicting values (e.g. `charmcraft.yaml` says one base
  and the previous release notes another), don't silently prefer one: quote
  both and ask which is correct.

### 7. Ask the user (whenever something is genuinely unclear)

The governing rule is "Infer what's determinable; ask about what isn't" above:
**anything ambiguous, contradictory, undefined, or not confidently inferable
must be raised with the user rather than guessed at or quietly left as a
TODO.** The list below is the set of cases known to recur, not an exhaustive
one — if you hit an ambiguity that isn't listed, ask anyway.

Always query the user for a preferred resolution when:

- The from-ref could not be determined automatically (step 1.3.d), or more
  than one candidate is equally plausible.
- The resolved range is **empty**, or the range's size looks implausible for
  the release being described.
- The commit range was truncated and the user should choose how to proceed.
- Two entries look like the same change but differ in wording (possible
  double-count) and it is not obvious which to keep.
- A suspicious entry appears (e.g. a revert without its original, a merge
  commit listed as a change, an entry whose message contradicts its PR).
- Compatibility values are missing and cannot be derived from the repo.
- **The user pinned neither end of the range** — infer `from-ref`, `to-ref` and
  the revision number, then confirm all three in one message before generating
  (see "When the user pinned neither end, propose and confirm"). This is a
  confirmation, not an open question: propose concrete values with their
  reasoning, so the user can simply agree.
- **A revision the user named has no tag** — list the nearest existing revisions
  below and above (and the newest), and ask which they meant. Never silently use
  a neighbour (see "Resolving a named revision to a commit").
- **A revision the user named matches several tags at different commits** — list
  each tag with its commit and ask which charm's series is meant.
- **The user's `from` is not earlier than their `to`** — the range would be
  inverted or empty; offer to swap them rather than generating an empty document.
- **The inferred title revision is not ahead of every revision the repo already
  documents** (see "Never generate a revision at or below one already
  documented") — stop and ask; never generate over or under an existing
  release-notes document.
- **A repo tags several charms and it isn't clear which series a component's
  revision should come from** — ask rather than picking one, since the wrong
  choice mis-numbers that component (see "Resolving the range and the revision
  number").
- One or more sibling components were detected in the product's previous
  release notes but weren't named by the user (step 1.4.b) — always ask,
  never include them by default.
- A confirmed sibling component's GitHub repo can't be determined
  automatically (step 1.4.d) — ask the user for the repository address
  instead of guessing.
- Auto-sort was neither enabled nor disabled in the user's request — ask once
  whether to run it, quantifying the offer with the actual counts from the
  generated drafts (see "Auto-sort" above).
- An entry carries a fix/feature signal but its title doesn't reveal whether
  it targets shipped behaviour or only tooling, and auto-sort is enabled —
  leave it in place and flag it rather than asking per entry; only ask if
  several such entries would materially change the release's shape.
- The track can't be determined confidently, or the branch and the docs'
  default version imply different tracks (see "Track / channel scope").
- Sources of truth contradict each other on any fact that reaches the
  document — product name, version, revision, component list.
- No save location can be established, or several candidate release-notes
  folders exist (step 8.1.c).
- The user's request contains a term, ref or scope you can read more than one
  way — ask which reading is meant instead of choosing one.

**How to ask.** Batch every open question into a single message; don't
drip-feed. For each one: state what you already established, name the
ambiguity, list the candidates and where you found them, and give your
recommended answer so the user can simply confirm it. Prefer questions
answerable in one word. Keep working on everything the question doesn't block
while you wait, and never ask about anything you can resolve yourself from the
repos.

**What not to ask about.** Do not ask which repository, product, track or
revision to generate for merely because the user didn't say — those are
inferable from the open workspace (see "Starting from the currently open
repository"): infer them, state what you inferred, and proceed. The exception
is a bare request made while release-notes-builder itself is the open
workspace, where there is no target repo to infer. The test is whether exactly
one answer is *determinable*, not whether the user happened to supply it.

## Fully publishable output

The saved document must read as the **final, ready-to-publish release
notes** — not a draft, not a work in progress:

- Never write the words "draft", "upcoming", or similar hedging in the
  title, introduction, or any visible body text. Write the title and intro
  as if this is the actual release (e.g. `# Charmed Apache Spark (revision
  8)` with the real/expected revision, not `(upcoming stable release —
  draft)`).
- It is fine, and expected, to leave an invisible HTML comment block
  (`<!-- ... -->`) with review notes, source-of-truth references, and
  imperative TODOs for the release owner (see below) — that comment is the
  *only* place allowed to acknowledge open items. It goes **immediately
  after the frontmatter**, never above it (see "Frontmatter must be the very
  first thing in the file").
- Every visible heading and section must be complete prose, not a stub —
  no bracketed placeholders in the rendered text.

### Frontmatter must be the very first thing in the file

If the product's template emits frontmatter (MyST `html_meta`, or YAML for
another docs stack), the opening `---` must be on **line 1, column 1**, with
nothing at all before it — no HTML comment, no blank line, no anchor.

This is not a style preference. Sphinx/MyST only recognises frontmatter at the
very start of the document. Anything before it means the `---` block is parsed
as body content instead: the `---` lines become transitions, the `# Revision N`
title stops being the document title, and the docs build fails with

```
WARNING: Document headings start at H2, not H1
```

The correct order at the top of the saved file is therefore:

1. The frontmatter block (`---` … `---`), starting on line 1.
2. The review-notes HTML comment (`<!-- ... -->`).
3. The MyST anchor (e.g. `(reference-release-notes-revision-316)=`).
4. The `# <title>` heading.

Because the review-notes comment is written by the agent (not the template),
it is the agent's job to insert it *after* the rendered frontmatter rather
than prepending it to the file. Verify this on the saved file before
presenting it: `head -1 <file>` must print `---` whenever the template has a
frontmatter block.

### Review-notes TODOs must be imperative and actionable

Write each TODO in the top comment as a direct instruction to the release
owner, naming the exact action, not a passive description of a limitation:

- Good: "Add the released revision number to the title and Charmhub links."
- Good: "Verify all artifacts and links are up to date before publishing."
- Bad: "The revision numbers for this release are TBD." (passive, no verb)
- Bad: "Charm/snap revisions listed are the latest edge revisions." (states
  a fact, not an instruction)

Only keep a TODO if it names a genuine action the release owner must still
take. If, upon review, a TODO's action isn't relevant to this release (e.g.
it doesn't apply to this document's scope), delete that TODO entry outright
rather than leaving it as an aside — don't accumulate stale TODOs.

### 8. Save the final document

1. Determine the save location:
   - **Cross-repo mode** (the currently open workspace is the target repo,
     not release-notes-builder — the common case, see "Installing and running
     this skill" above): save into *that* repository, following
     wherever its previous release notes already live — never into
     `$BUILDER_HOME/release-notes/`:
     a. If step 1 or step 2 already found the product's previously published
        release notes inside the currently open repo's own tree (e.g. a
        `docs/reference/release-notes/revision-315.md` the user linked to,
        or a `docs/reference/releases/revision-*.md` found while building
        the template), save the new document in that **same directory**,
        following its exact naming convention (e.g. one file per revision:
        `revision-316.md`).
     b. Otherwise, search the currently open repo for a plausible existing
        releases folder — common candidates: `docs/reference/release-notes/`,
        `docs/reference/releases/`, `release-notes/`, `docs/releases/` — and
        use whichever one contains existing revision/version-named files.
     c. If no existing release-notes location can be found in the repo, ask
        the user exactly where to save the file before writing anything —
        do not guess or invent a path. This is the normal case for a first
        release (see "First release: a product with no release notes yet"):
        propose the conventional path for the repo's existing docs layout
        (e.g. `docs/reference/release-notes/revision-<N>.md` when the repo
        already has a Diátaxis `docs/reference/` tree) and create the folder
        only after the user confirms.
   - **Standalone mode** (release-notes-builder is itself the open
     workspace — see the note above the cross-repo options; no setup
     needed): keep the existing default,
     `release-notes/<product>-<to-ref>.md` at the repo root.
2. Delete the temporary per-repo drafts directory created in step 3 (the
   system temp dir) — never leave scratch files behind in either repo.
3. Present the file to the user with a short summary of:
   - Which repository and folder it was saved into, and why (mirrored an
     existing folder's convention, or asked and used the user's answer).
   - Components covered and their commit ranges (and how from-ref was chosen).
   - Categories with notable highlights.
   - Any TODOs left in the review-notes comment for the user (compat values,
     links, flagged entries) — phrased imperatively, per the rule above.

### 9. Verify with the repo's own docs checks

The generated document is not finished until the target repository's own docs
checks pass on it. Release notes are the single most check-hostile page in a
charm's docs: they are full of raw PR titles written by developers, which
routinely contain misspellings, tool jargon and bare filenames that the docs
build treats as prose. Run the checks and fix what they report — do not hand
the user a document that will fail CI.

This step applies in **cross-repo mode** only (the target repo is the open
workspace, so its `docs/` tree and its checks are available). In standalone
mode there is no docs build to run against; say so and skip it.

**Warn the user before starting, and say why it takes a while.** `make
linkcheck` issues a real network request for every external link in the whole
docs set and commonly takes **several minutes**; a release-notes page adds one
request per PR link, so a 60-entry document makes this noticeably slower. Tell
the user, up front, something like:

> Now running the repo's docs checks against the new page: `make spelling`
> (fast) and `make linkcheck` (this hits every external link in the docs and
> usually takes a few minutes). I'll fix whatever they report and re-run until
> both pass.

Then loop until clean:

1. **Find the docs directory and its check targets.** Conventionally
   `docs/Makefile` with `spelling` (alias `spellcheck`) and `linkcheck`
   targets, run from inside `docs/`. Confirm the targets exist
   (`grep -E '^(spelling|spellcheck|linkcheck):' docs/Makefile`) rather than
   assuming; if the repo has no such targets, say so and skip this step.
2. **Run the auto-link checker first** — it is instant, needs no network, and
   catches the one class of failure that a green linkcheck will not
   (see "Domain squatting via auto-linked filenames" below):

   ```bash
   python "$BUILDER_HOME/tools/check_autolinks.py" <saved-file>
   ```

3. **Run the spellcheck next** — it is much faster than linkcheck, so fix its
   findings before spending minutes on the network checks:

   ```bash
   cd docs && make spelling
   ```

   Many Canonical docs Makefiles accept `CHECK_PATH=` to narrow the run, which
   is far quicker while iterating:

   ```bash
   cd docs && make spelling CHECK_PATH=reference/release-notes
   ```

   Always finish with a full, unnarrowed run before declaring success.
4. **Fix each spelling finding** — see "Fixing spellcheck findings" below.
5. **Re-run the spellcheck** until it reports nothing for the new page.
6. **Run the linkcheck** (re-state that this is the slow one):

   ```bash
   cd docs && make linkcheck
   ```

7. **Fix each broken link** — see "Fixing linkcheck findings" below. A zero
   exit code does not mean the page is clean: also audit the `[redirected ...]`
   lines in the build's link report, because a linkified filename that happens
   to resolve passes the check while publishing a link to a squatted domain.
   See "A clean exit code is not enough" below.
8. **Re-run all three checks** after any fix, and keep looping until they are
   green *for your page*. A spelling fix can introduce a link finding and vice
   versa (e.g. replacing a bare filename with a code span, or a word with a
   link), so the final confirmation must be a clean run of *all three*, not of
   only the one you last touched. "Green" here means no finding attributable to
   the document you generated — pre-existing findings in unrelated files, and
   transient timeouts, are reported to the user, not fixed (see below).
9. **Report what you changed.** List, in the summary you present to the user:
   every word added to the wordlist, every `linkcheck_ignore` entry added to
   `conf.py`, every edit made to the release-notes text itself, and — if the
   auto-link checker found anything — the recommendation to set
   `myst_linkify_fuzzy_links = False`. These are edits to files *outside* the
   new document, so the user must know about them: they will be part of the
   same commit.

#### Fixing spellcheck findings

Two legitimate fixes exist, and the choice between them is not arbitrary:

- **Correct the release-notes text** when the word is genuinely misspelled —
  a typo the PR author made (`acomodating` → `accommodating`, `exclusivness` →
  `exclusiveness`). PR titles are copied verbatim by the builder, so their
  typos land in the document. Fixing a *spelling error* is not "rewriting the
  message": it does not change what the entry says, so it does not violate the
  "never rewrite a message" rule in step 4. Correct the spelling and leave the
  meaning, the Jira IDs and the PR link untouched.
- **Add the word to the repo's custom wordlist** when the word is correct but
  simply not in the dictionary — product names, acronyms and established
  technical terms (`toolchain`, `autogenerated`, `rediraffe`, `GCS`, `READMEs`).
  The wordlist is usually `docs/.custom_wordlist.txt` (note the leading dot;
  some repos use `custom_wordlist.txt`). Find it rather than guessing:
  `find docs -name '*custom_wordlist*' -not -path '*/.venv/*'`. It is a
  one-word-per-line file appended to Vale's accepted vocabulary — add the word
  in the casing the document uses, and keep the trailing blank line at the end
  of the file (some Makefiles concatenate it with another file).

Three further rules:

- **Prefer a code span over either fix for code-like tokens.** If the flagged
  token is a filename, module, CLI flag, config key or API name (`charm.py`,
  `metadata.yaml`, `--use-prs`), wrap it in backticks in the release notes.
  That both silences the spellchecker and is more correct — and, importantly,
  it also prevents the linkcheck failure described below. Do this instead of
  polluting the wordlist with filenames.
- **Fix an acronym's case rather than adding the lowercase form.** `gcs` in a
  PR title should become `GCS`; add `GCS` to the wordlist if needed. Don't add
  `gcs`.
- **Never silence a finding by deleting the entry** or by rewording it into
  something vaguer.

#### Fixing linkcheck findings

Linkcheck reports each failure as `WARNING: broken link: <url>` with the source
file and line, e.g.

```
docs/reference/release-notes/revision-366.md:116: WARNING: broken link:
http://charm.py (... Failed to resolve 'charm.py' ...)
```

Work out which kind of failure it is before fixing it:

- **A bare filename auto-linked by MyST.** This is the common one in release
  notes and the cause of the example above: MyST's `linkify` extension turns
  any `something.tld`-looking token in prose into a link, and `.py` gets
  treated as a domain, so `charm.py` in a PR title becomes
  `http://charm.py`. **Fix it in the document, by wrapping the token in
  backticks** (`` `charm.py` ``) — a code span is never linkified. Do *not*
  add it to `linkcheck_ignore`: the link should not exist at all, and ignoring
  it leaves a nonsense hyperlink in the published page. The same applies to
  `test_charm.py`, `metadata.yaml`, `charmcraft.yaml` and any other bare
  filename a PR title mentions.
- **A genuinely wrong or stale URL** (a typo, a moved page, a private repo
  link). Fix the URL in the document.
- **A URL that is correct but unreachable from CI** — a login-walled page, a
  chat-room invite, a rate-limiting host, a link that only resolves once the
  release is published. Add a regex for it to `linkcheck_ignore` in
  `docs/conf.py`, in the existing list, with a brief comment saying why it
  can't be checked. Keep entries as narrow as possible — ignore the specific
  URL or host path, never a broad pattern that would mask future real
  breakage.
- **An anchor-only failure** on a host whose pages are JS-rendered belongs in
  `linkcheck_anchors_ignore_for_url`, not `linkcheck_ignore`.
- **A transient timeout**, reported as `Read timed out. (read timeout=30)`
  rather than a 404 or a DNS failure. These are network flakiness, not
  breakage — slow hosts like `readthedocs-hosted.com` and `canonical.com`
  time out routinely when linkcheck fires dozens of parallel requests.
  **Do not "fix" them**: don't edit the URL, and above all don't add them to
  `linkcheck_ignore` (that would permanently stop checking a link that is
  perfectly valid). Re-run to confirm they come and go, and if they persist,
  raise `linkcheck_timeout` in `conf.py` rather than ignoring the URL.

**Scope your attention to the page you generated.** Linkcheck runs over the
whole docs set, so it will surface pre-existing findings in files you never
touched. Fix only what your page introduced; mention any pre-existing failures
to the user as an observation, and do not silently "clean up" unrelated pages
or add exceptions on their behalf. Compare the reported file paths against the
document you just saved before acting on anything.

Prefer fixing the document over adding an exception every time both are
possible: an exception is permanent config debt that hides future breakage,
while a code span or corrected URL fixes the page itself.

##### Domain squatting via auto-linked filenames — check this explicitly

This is the one failure mode in release notes with a **security and reputation**
impact rather than a cosmetic one, and the one the docs build will *not* catch
for you. Treat it as mandatory, not best-effort.

**The mechanism.** MyST enables the `linkify` extension by default, and
`myst_linkify_fuzzy_links` also defaults to `True`. Together they turn any bare
`word.tld`-looking token in prose into a hyperlink *without needing a scheme*.
Release notes are built from raw PR titles, which mention filenames constantly,
so `README.md` silently becomes `http://README.md`.

**Why it is dangerous.** Many file extensions are also live TLDs — `.md` is
Moldova, `.py` Paraguay, `.sh` Saint Helena, plus `.io`, `.co`, `.in`, `.rs`,
`.pl`, `.tf`, `.so`, `.re`, `.cc`, `.ai`. So the bogus link often *resolves*, to
whoever squats that domain. Observed in a real Canonical docs build:

```
reference/release-notes/revision-366.md:147: [redirected with Found]
http://README.md to https://dealsbe.com
```

**Why linkcheck won't save you:** that is reported as a *redirect*, not as
`[broken]`, so the build **exits 0** and the page ships with a live hyperlink to
a stranger's site. A green linkcheck is not evidence of a clean page.

Do all three of the following:

1. **Run the checker** (the primary gate — before the slow linkcheck):

   ```bash
   python "$BUILDER_HOME/tools/check_autolinks.py" <saved-file>
   ```

   It asks `linkify-it-py` — the very library MyST uses — what it *would*
   linkify, so it stays correct as the TLD list evolves. It already ignores
   code spans, fenced blocks, real URLs, emails, MyST anchors, frontmatter and
   the review-notes comment, and it reports `file:line:col`, the token, and the
   URL it would become. Exit status 1 means hazards were found. Add `--explain`
   to print the fixes. **Do not hand-roll a `grep` for a list of extensions** —
   a hand-written list is a blocklist that silently misses cases (`.go` and
   `.html` are *not* TLDs, while `install.sh` and `main.tf` *are* hazards; that
   is not guessable).

   Fix every hit by **wrapping the token in backticks** (`` `README.md` ``). A
   code span is never linkified, and a filename belongs in code formatting
   anyway. Then re-run until clean. After a bulk edit, confirm backticks are
   balanced — an odd count means an unterminated code span that silently
   swallows the rest of a line: `grep -o '\`' <file> | wc -l` must be even.

2. **Recommend the root-cause fix to the user.** The per-document fix protects
   only this page; the next release notes will reintroduce the hazard. One line
   in the docs' `conf.py` disables the whole class:

   ```python
   # Don't turn scheme-less tokens (e.g. the "README.md" in a PR title) into
   # links: many file extensions are live TLDs, so such links resolve to domain
   # squatters and pass `make linkcheck` as mere redirects.
   myst_linkify_fuzzy_links = False
   ```

   Verified behaviour: `README.md`, `charm.py` and `SECURITY.md` stay plain
   text, while `https://canonical.com/data` and `foo@example.com` are still
   linked. The only trade-off is that a **bare** domain in prose
   (`canonical.com/data`, no scheme) stops auto-linking and must be written as
   an explicit Markdown link — which is better practice regardless. Because
   this affects the whole docs set and not just your page, **propose it and let
   the user decide** rather than editing `conf.py` unilaterally.

3. **Audit the link report after linkcheck**, not just its exit code:

   ```bash
   grep -F '[broken]'    docs/_build/output.txt
   grep -F '[redirected' docs/_build/output.txt
   ```

   Inspect every redirect whose target is an unrelated domain.

Never "fix" one of these by adding the bogus URL to `linkcheck_ignore` — that
hides the problem and leaves the squatted link live in the published page.

## DA186 compliance checklist

Verify the final document against the spec before saving:

- [ ] Title contains the charm revision (or other unique release designation)
      and the exact date follows it.
- [ ] Introduction: brief summary + Charmhub / upgrade / deploy / system
      requirements links.
- [ ] List of changes: full list since previous stable release, distributed
      among categories (Features, Breaking changes, Security, Bug fixes,
      Other improvements — or the product template's equivalents); each entry
      links a PR and/or commit; empty categories omitted.
- [ ] The document was rendered from the product's own template (an existing
      `templates/<product>.md.j2`, or one created in step 2 from the
      product's published release notes) — not from the generic
      `templates/base.md.j2`.
- [ ] The document is titled after the **product**, not after a single
      component of it (see step 2).
- [ ] Compatibility: workload versions, software dependencies (Juju
      versions), hardware architectures (with per-architecture revisions
      if applicable).
- [ ] Known issues section: optional; add only if the user asks or evidence
      exists — it can be appended later.
- [ ] Nothing was published — the file exists only in this local repository.
- [ ] The document reads as final/publishable: no "draft" wording in any
      visible text; open items live only in the top HTML comment, phrased
      as imperative TODOs (see "Fully publishable output").
- [ ] No heading is immediately followed by another heading with zero body
      text in between (see step 4).
- [ ] Unless the user explicitly asked for a multi-track/product-wide
      document, the release notes cover a single track (see "Track /
      channel scope").
- [ ] Checked the product's previous release notes for sibling/additional
      components beyond the one(s) the user named or linked to, and asked
      the user to confirm before including any of them (see step 1.4) —
      never added a detected sibling component silently.
- [ ] Auto-sort was either explicitly requested/declined by the user, or the
      user was asked about it — it never ran silently, and never ran at all
      unless enabled (see "Auto-sort"). If it ran, every move is listed in
      the review notes with its evidence, and no entry was moved across
      component boundaries or edited in the process.
- [ ] If the input was a link to a previously published release-notes page,
      the generated document covers the *next* release after that page, not
      the release the page itself documents.
- [ ] If the user named nothing at all, the repository, product, track,
      branch and `from-ref` were inferred from the open workspace and its
      newest release-notes file rather than asked about, and every inference
      is stated in the review notes (see "Starting from the currently open
      repository").
- [ ] Nothing ambiguous, contradictory or undeterminable was silently guessed:
      every such case was either resolved from a source of truth or put to the
      user, and no `TODO` in the review notes stands in for a decision the user
      could have settled (see "Infer what's determinable; ask about what
      isn't").
- [ ] If the user named a starting revision/version/tag/SHA, it was resolved
      against the repo's actual tags, confirmed to be an ancestor of the
      branch, and applied exclusively (the document covers the release *after*
      it) — unless the user meant to document that release itself, which was
      confirmed rather than assumed.
- [ ] The revision number came from a **complete** tag listing
      (`git ls-remote --tags`), never from a top-N slice of `gh api .../tags`,
      and was chosen by matching the **`rev`/`revision` prefix plus its adjacent
      digit run** and comparing those **numerically** — not by flattening whole ref
      names, and not by scanning for any digit run anywhere in the name (`k8s`,
      `v4/1.46.0` and `release-2024-01-15` all contribute stray numbers, the last
      of which beats every real revision). Years were **not** stripped to deal
      with dates — that would delete real four-digit revisions, and
      `postgresql-operator` is already at rev1215. If the repo genuinely had no
      `rev` tags, the digit-run fallback was presented to the user as a suggestion
      rather than used silently. See "Reading the latest revision out of the tag
      list".
- [ ] The resolved range is non-empty: `git rev-list --count <from>..<to>`
      returns more than zero. Every failure mode in this area surfaces as an
      empty document rather than an error.
- [ ] Every `compare` / `git/refs/tags` API call used the full namespaced ref
      (e.g. `opensearch/rev366`). A 404 on a bare `revNNN` was treated as a
      wrong ref name and followed up by searching for namespaced variants —
      never as evidence that the tag doesn't exist.
- [ ] The latest tag's **peeled** commit was compared to the branch HEAD, and
      the title revision follows from the result: that revision if the tag is at
      HEAD, otherwise the first number no tag or document already uses — left as
      a TODO to confirm, since revisions are allocated in per-architecture pairs
      (see "Is the latest tag *at* the branch HEAD?").
- [ ] `from-ref` is the newest documented revision **itself**, not that revision
      + 1: the range is already exclusive of `from-ref`, and consecutive
      revisions often share a commit, so a `+1` would silently drop a release
      (see "`from-ref` is the documented revision itself").
- [ ] If the user pinned neither end of the range, the inferred `from-ref`,
      `to-ref` and revision number were **put to the user for confirmation or
      override** before generating — batched with the other step-1 questions —
      and both the inference and their answer are recorded in the review notes.
- [ ] Every revision **number** the user named was resolved to an actual tag and
      commit; a number with no tag, or one matching several tags at different
      commits, was put to the user with concrete options rather than resolved to
      a neighbour or to one arbitrary match (see "Resolving a named revision to a
      commit").
- [ ] If the user named only a `to` revision, `from-ref` was taken from the
      release *before* it — not from the newest documented revision, which is
      usually later and would invert the range into an empty document (see "The
      four ways a user can specify the range").
- [ ] The resolved range is non-empty and runs forwards: `from-ref` names an
      earlier release than `to-ref`.
- [ ] The repo's release-notes folder **and its git history** were checked for
      already-documented revisions, and generation stopped for the user's
      decision if any documented revision was greater than or equal to the
      inferred one (see "Never generate a revision at or below one already
      documented"). No existing release-notes document was overwritten or
      contradicted.
- [ ] If this is the product's first release-notes document, that was verified
      across the repo, the docs site and `$BUILDER_HOME/release-notes/` and
      stated in the review notes; `base.md.j2` was used deliberately (not as a
      silent fallback); and the starting point and save location were agreed
      with the user.
- [ ] Saved to the correct location for this invocation mode (see step 8):
      the target repo's existing release-notes folder — confirmed with the
      user if none was found — in cross-repo mode; `release-notes/` in
      standalone mode. Never saved into `$BUILDER_HOME/release-notes/` while
      running in cross-repo mode.
- [ ] If the template emits frontmatter, the file's line 1 is the opening
      `---` — the review-notes comment and the anchor come *after* the
      frontmatter block, never before it (see "Frontmatter must be the very
      first thing in the file"). Verified with `head -1`.
- [ ] In cross-repo mode, the repo's own docs checks were run against the
      saved page and **both** pass: `make spelling` and `make linkcheck`
      (see step 9). The user was warned beforehand that linkcheck takes
      several minutes.
- [ ] Every spellcheck finding was resolved either by correcting a genuine
      typo in the release-notes text, by wrapping a code-like token in
      backticks, or by adding a correctly-cased word to the repo's
      `docs/.custom_wordlist.txt` — never by deleting or vaguening an entry.
- [ ] Every broken link was resolved at its source where possible (bare
      filenames such as `charm.py` wrapped in backticks so MyST stops
      linkifying them; wrong URLs corrected), and `linkcheck_ignore` in
      `docs/conf.py` was used only for URLs that genuinely can't be checked
      from CI, each with a narrow pattern and a reason.
- [ ] `tools/check_autolinks.py` reports no hazards for the saved document, so
      no bare filename can be auto-linked into a squatted domain (e.g.
      `README.md` → `http://README.md` → an unrelated site). The linkcheck
      report's `[redirected ...]` lines were audited too — not just its exit
      code — and if any hazard was found, setting
      `myst_linkify_fuzzy_links = False` in `docs/conf.py` was recommended to
      the user as the root-cause fix.
- [ ] All edits made outside the new document (wordlist additions,
      `conf.py` linkcheck exceptions) were listed for the user in the final
      summary.

## Reference

- Spec: `examples/DA186 - Release notes for Data charms.md`
- Example output: `examples/Example-release-notes-spec.md`
- Builder script: `build_release_notes.py` (see `README.md` for CLI reference)
- Auto-link checker: `tools/check_autolinks.py` — detects bare filenames that
  MyST would linkify into squatted domains (see step 9); `--explain` prints the
  `myst_linkify_fuzzy_links = False` root-cause fix
- Templates: `templates/base.md.j2` (generic DA186 skeleton),
  `templates/kafka.md.j2`, `templates/opensearch.md.j2`,
  `templates/spark.md.j2` — product templates live alongside the base and
  extend it (see step 2)
