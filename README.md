# Release Notes Builder

Generate DA186-spec-compliant release notes for Canonical Data & AI charms from
GitHub commit and pull-request data, rendered through Jinja2 templates.

The repository contains two things:

- **`build_release_notes.py`** — a script that turns a commit range in *one*
  GitHub repository into a categorised changelog document.
- **`.github/skills/release-notes/SKILL.md`** — an agent skill that drives the
  whole release-notes workflow for a *product* (which usually spans several
  repositories), calling the script as one of its steps.

## Choose how you'll run it

There are two ways to work, and they differ in installation, in what you type,
and in where the document ends up. Pick one before reading further:

| | [**A — From the target repo**](#a--from-the-target-repo-recommended) | [**B — From this repo**](#b--from-this-repo-standalone) |
| :--- | :--- | :--- |
| **Your workspace** | The product repo, e.g. `kafka-operator` | `release-notes-builder` |
| **Who it's for** | Anyone writing release notes for a product | Developing the skill or the builder; one-off experiments |
| **Setup** | Copy one file (`SKILL.md`) | `git clone` this repo |
| **This repo** | Not cloned, not open | Cloned and open |
| **Output goes to** | Inside the product repo, next to its existing release notes | `release-notes/` here |
| **Docs & sources on hand** | Yes — the agent can read `charmcraft.yaml`, previous notes, etc. | No — everything comes from the GitHub API |
| **Shortest request** | "Generate release notes" — target auto-detected | Must name the repo |

**Option A is the recommended one.** The skill needs to read the target repo's
metadata and previous release notes to write the compatibility table and to
match the product's established structure, and it can only do that when that
repo is the open workspace.

Either way you can also bypass the agent entirely and
[run the builder script by hand](#running-the-builder-script-by-hand).

## A — From the target repo (recommended)

### Installation: copy one file

You don't need this repository at all — not cloned, not open. `SKILL.md` is
**self-bootstrapping**: on first use it downloads the builder script and
templates from this public repo into `~/.cache/release-notes-builder/`. So
installing means copying a single file.

```bash
# Available in every workspace, no clone required:
mkdir -p ~/.claude/skills/release-notes && curl -fsSL -o ~/.claude/skills/release-notes/SKILL.md \
  https://raw.githubusercontent.com/izmalk/release-notes-builder/main/.github/skills/release-notes/SKILL.md
```

Use `~/.copilot/skills/…` or `~/.agents/skills/…` instead if that's what your
harness reads. To scope it to one repo rather than your whole machine, write it
to `.github/skills/release-notes/SKILL.md` inside the target repo and commit it
so teammates get it too.

If your harness doesn't discover skills — or you just want one run — skip
installation and name the file in your message:

> Using the skill instructions at
> `https://raw.githubusercontent.com/izmalk/release-notes-builder/main/.github/skills/release-notes/SKILL.md`,
> generate release notes for canonical/kafka-operator

Full details, including how `$BUILDER_HOME` is resolved, are in
[`SKILL.md`](.github/skills/release-notes/SKILL.md#installing-and-running-this-skill).

### Usage from the target repo

Open the **product's own repository** as your workspace and simply ask:

> Generate release notes

That's the whole request. With nothing named, the skill takes the open
repository as the target: it reads the `origin` remote for `owner/repo`, works
out the product name from `charmcraft.yaml` and the docs, finds the newest
release-notes file in the repo's own docs tree, and generates the release
*after* the one that file documents — up to the current branch HEAD. It reports
every inference it made instead of interrogating you first.

You can still be explicit when you need a different scope:

> Generate release notes for canonical/kafka-operator and
> canonical/kafka-k8s-operator from rev247 to rev248

Name a starting point as a revision, version, tag or commit SHA and it takes
priority over everything the skill would otherwise detect:

> Release notes since rev247

> Everything from 2.1.0

The skill matches the name you used against the repo's actual tags (which may
be `rev247`, `revision-247`, `v2.1.0`, or namespaced as `kafka/rev247` — see
[The range and the revision number](#the-range-and-the-revision-number)), checks
the ref really is an ancestor of the branch, and treats it **exclusively** — you
get the release *after* the one you named. If your phrasing could also mean
"document that release itself", it asks rather than shifting every entry by one
release.

Or point at a **previously published** release-notes page, from which the skill
derives the product, the track, the starting ref and the component list, and
generates the *next* release after it:

> Create release notes for
> https://canonical.com/data/opensearch/docs/2/reference/release-notes/revision-315/

Add `auto-sort on` (or `off`) to skip the question about reclassifying the
"Other improvements" catch-all:

> Create release notes for canonical/opensearch-operator with auto-sort on

### First release: no previous notes to build on

A brand-new charm has no published release notes, so there's nothing to derive
the starting ref, component list, structure or save location from. The skill
handles this explicitly rather than failing: it first confirms none exist
(checking the repo tree, the docs site and its own output folder and telling you
so), then falls back to the latest ancestor tag for the starting point — or, if
the repo has no tags at all, proposes the repo's first commit and asks you to
confirm, since a whole-history changelog can be long.

This is also the **only** case where the generic `base.md.j2` template is
correct: with no established structure to reproduce, there's nothing to model a
product template on. The skill asks where the release notes should live rather
than inventing a path, proposing the conventional one for your docs layout, and
writes the introduction as a first release rather than as a diff against a
predecessor.

The skill then resolves the refs, confirms the sibling components with you, runs
the builder once per repository, merges the drafts, and writes the introduction
and compatibility table. The full path is described in
[End-to-end workflow](#end-to-end-workflow).

### When it asks, and when it doesn't

The dividing line is whether exactly one answer is *determinable* — not whether
you happened to supply it:

- **Determinable → inferred and reported.** The repository, product, track,
  branch and starting ref all come from the open workspace and its docs. The
  skill states what it concluded instead of asking you to repeat it.
- **Ambiguous, contradictory, absent or unclear → it asks.** Two candidate
  release-notes folders; a branch that implies one track while the docs imply
  another; a compatibility value with no source in the repo; an empty commit
  range; a `from-ref` that isn't an ancestor of the branch; a request that can
  be read two ways. It also always asks before adding a sibling component it
  discovered but you didn't name.

Questions are batched into a single message, each stating what was already
established, the candidates found and where, and a recommended answer you can
confirm in one word. Unresolved ambiguities are never quietly buried as TODOs —
those are reserved for actions only you can take, such as the final published
revision number.

### Output location in the target repo

Saved **inside the target repo**, in the folder its previous release notes
already live in (e.g. `docs/reference/release-notes/revision-316.md`), following
that folder's naming convention. If no such folder is found, the agent asks — it
never guesses. Nothing is ever pushed or published.

### Keeping it current

The skill file and the cache are independent snapshots:

- **Update `SKILL.md`** by re-running the `curl` above; it overwrites in place.
- **Refresh the cached script and templates** by asking the agent for the latest
  version, or by deleting `~/.cache/release-notes-builder/` so the next run
  re-bootstraps.

## B — From this repo (standalone)

Use this mode when you're **developing** the skill, the builder script or the
templates, or when you just want a quick changelog without touching a product
repo.

### Installation: clone and install

```bash
git clone https://github.com/izmalk/release-notes-builder.git
cd release-notes-builder
pip install -r requirements.txt
export GITHUB_TOKEN=$(gh auth token)
```

Requires Python 3.10+. Opening this repo as your workspace needs **zero further
setup** — the skill lives at `.github/skills/release-notes/SKILL.md` and
`--repo` still accepts any `owner/repo`.

To also have your in-progress skill edits apply in *other* workspaces, symlink
the skill folder instead of re-copying it:

```bash
ln -s /absolute/path/to/release-notes-builder/.github/skills/release-notes \
    ~/.claude/skills/release-notes
```

A local checkout always wins over the bootstrap cache, so your uncommitted
changes are what actually runs. The skill never overwrites a checkout when
refreshing.

### Usage from this repo

Name the target repository explicitly — otherwise the requests are the same as
in [option A](#usage-from-the-target-repo), and `--repo` is not limited to this
repository:

> Generate release notes for canonical/kafka-operator from rev247 to rev248

Here the target **must** be named: a bare "generate release notes" has nothing
to detect, because the open workspace is the tool rather than a product. And
because the target repo isn't open, the agent can't read its `charmcraft.yaml`,
sibling metadata or previously published notes, so the compatibility table and
the product template may need more manual work than in option A.

### Output location in this repo

`release-notes/<product>-<to-ref>.md` in this repository.

## Running the builder script by hand

`build_release_notes.py` handles a single repository and a single commit range.
Merging multiple repositories, the introduction, and the compatibility table
are *not* the script's job — the agent skill does those.

### Prerequisites

- Python 3.10+
- A GitHub personal access token (recommended for rate limits; required for
  private repos): `export GITHUB_TOKEN=$(gh auth token)`

```bash
pip install -r requirements.txt
```

### Command line

```bash
python build_release_notes.py \
    --repo canonical/kafka-operator \
    --from-ref rev247 \
    --to-ref rev248 \
    --template templates/kafka.md.j2
```

| Argument | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `--repo` | Yes | — | Repository in `owner/repo` format or full GitHub URL. |
| `--from-ref` | Yes | — | Start reference (tag, branch, or SHA). Changes **after** this ref are included. |
| `--to-ref` | No | Branch HEAD | End reference (tag, branch, or SHA). |
| `--branch` | No | Repo default | Branch to resolve `--to-ref` against when omitted. |
| `--template` | Yes | — | Path to the Jinja2 template file. |
| `--title` | No | `--to-ref` value | Release title shown in the heading (e.g. `"Revision 248"`). |
| `--token` | No | `GITHUB_TOKEN` env var | GitHub personal access token (overrides the env var). |
| `--output` | No | stdout | Write output to this file instead of stdout. |
| `--use-prs` | No | Off | Use PR titles instead of commit messages for changelog entries. |

Token resolution order: `--token` → `GITHUB_TOKEN` → unauthenticated (public
repos only, 60 requests/hour).

**Example — write to file, use PR titles, custom title:**

```bash
python build_release_notes.py \
    --repo canonical/kafka-operator \
    --from-ref rev247 \
    --to-ref rev248 \
    --template templates/kafka.md.j2 \
    --title "Revision 248" \
    --use-prs \
    --output revision-248.md
```

**Example — from a tag to the latest commit on the default branch:**

```bash
python build_release_notes.py \
    --repo canonical/postgresql-operator \
    --from-ref rev550 \
    --template templates/base.md.j2
```

### Manual post-generation steps

If you run the script by hand rather than through the skill, the output is a
**draft**; you will need to:

1. Write the **Introduction** section (summary of key highlights).
2. Fill in the **Compatibility** table with exact revisions, versions, and
   artefact links.
3. Optionally add a **Known issues** section.
4. Review and polish individual changelog entries.

## End-to-end workflow

This is what the skill does in [option A](#a--from-the-target-repo-recommended),
from "we want to release" to "a document ready for review". Steps 3–13 are
performed by the agent skill; you only do 1 and 2.

1. **You decide to release** a new charm revision (or a new product release).
2. **You open the product's own repository** (e.g. `kafka-operator`) as your
   workspace, having copied `SKILL.md` into your personal skills folder once
   (see [Installation](#installation-copy-one-file)). No clone of this repo is
   needed — the skill downloads the script and templates itself on first use.
3. **You ask the agent for release notes** — usually with nothing else at all.
   The skill then detects the target from the open workspace: `owner/repo` from
   the `origin` remote, the product from `charmcraft.yaml` and the docs, and the
   previous release from the newest file in the repo's own release-notes folder.
   You can instead name repositories and refs explicitly, or link the
   **previously published** release-notes page, from which the skill derives the
   product, the track, the starting ref, and the component list, and generates
   the *next* release after it.
4. **The skill resolves scope and references**: the track (one track per
   document by default), the branch, `from-ref` (user-specified → the repo's
   newest documented release → the docs site → latest ancestor tag), and
   `to-ref` (branch HEAD by default). It reports what it inferred rather than
   asking you to supply it.
5. **The skill settles the revision number the document will be titled with**
   from the repo's tags, then cross-checks it against what the repo already
   documents — see
   [The range and the revision number](#the-range-and-the-revision-number). If
   the number isn't ahead of every documented release, it stops and asks you
   instead of generating. And if you pinned neither end of the range, it puts the
   inferred `from-ref`, `to-ref` and revision number to you for confirmation or
   override first, batched with its other questions.
6. **The skill discovers the product's sibling components** — companion charms,
   snaps, rocks, Terraform modules, dashboards — from the previous release
   notes, and **asks you to confirm each one** before adding it to scope. It
   never adds a component silently, and asks for the repository address if a
   component can't be mapped to one automatically.
7. **The skill selects the product's Jinja template** from `templates/` (matched
   on product, not repository). If none exists, it **creates one** from the
   product's most recent published release notes and verifies it renders. It
   never falls back to the generic `base.md.j2` for a product that already has
   published release notes.
8. **The skill runs `build_release_notes.py` once per repository** in scope,
   writing per-repo drafts into a system temp directory (never into either
   repository's tree).
9. **The skill merges the drafts into one product document** and polishes it in
   the same pass — one `## <Component>` heading per component with changes,
   DA186-ordered categories beneath it, duplicates and miscategorised entries
   fixed, false Jira-ID links dropped. Facts are never rewritten; ambiguous
   cases are raised with you. There is deliberately no merge script. If
   [auto-sort](#auto-sort-reclassifying-the-other-improvements-catch-all) is
   enabled, this is where it reclassifies the "Other improvements" catch-all.
10. **The skill writes the introduction and the Compatibility section** — the
    intro from the merged changelog, compatibility from repository sources of
    truth (`charmcraft.yaml`, `metadata.yaml`, snap/rock metadata, release tags)
    and the previous release notes' table.
11. **The skill saves the document**: into the open target repository's existing
    release-notes folder, following its naming convention (asking you if no such
    folder exists); or into `release-notes/` here when this repository is itself
    the workspace. It then deletes the temp drafts.
12. **The skill verifies the page with the repo's own docs checks** and fixes
    what they report, re-running until both are green — see
    [Docs checks as the final gate](#docs-checks-as-the-final-gate). It warns
    you first, because `make linkcheck` takes a few minutes.
13. **The skill reports back**, summarising coverage, highlights, the TODOs left
    for you in the review-notes comment, and every edit it made *outside* the
    new document (wordlist additions, `conf.py` linkcheck exceptions).

The output is a **finished, publishable document** — open items live only in the
review-notes comment, as imperative TODOs. **Nothing is ever pushed or
published**; all output stays local.

### The range and the revision number

Three defaults cover almost every run; anything you state explicitly wins over
all of them:

| What | Default |
|------|---------|
| `from-ref` | The **newest release notes already in the repo's docs tree** (usually `docs/reference/release-notes/revision-NNN.md`) — that revision's own tag, *not* that revision + 1 |
| `to-ref` | The **branch HEAD** — your checked-out branch, or the repo's default branch when targeting another repo |
| Revision number in the title | The **highest revision number in the repo's tags**; if that tag isn't at HEAD, the first number **no tag or document already uses** |

If you pinned neither end of the range, the skill infers all three and then **asks
you to confirm or override them** before generating — so a wrong inference costs
you one word, not a regenerated document.

You can pin either end, or both. Whichever you leave open keeps its default:

| You say | `from-ref` | `to-ref` | Title revision |
|---------|-----------|----------|----------------|
| nothing (just the repo) | newest documented revision | branch HEAD | from the tags — confirmed with you |
| "from 301" | `rev301` | branch HEAD | from the tags — confirmed with you |
| "to 314" | **the release before 314** | `rev314` | **314** |
| "from 299 to 399" | `rev299` | `rev399` | **399** |

Naming a `to` revision sets the title: the document ends at that release, so it
*is* that revision. And "to" alone deliberately does **not** keep the default
`from` — the newest documented revision is usually *later* than your `to`, which
would invert the range into silence (`rev315..rev314` yields zero commits and an
empty document). The skill walks back to the release before your `to` instead,
skipping a per-architecture pair-mate, since a pair shares a commit and would
also yield nothing.

Revision numbers are resolved to real tags and commits, never assumed. Two cases
get put back to you with options rather than guessed:

- **No such revision** — "to 399" when the highest tag is `rev366`. You're offered
  the nearest revisions below and above; a neighbour is never silently
  substituted, since an off-by-one shifts every entry in the document.
- **An ambiguous revision** — a repo that tags several charms can carry the same
  number twice at *different* commits (`rev9` and `opensearch-k8s/rev9` are
  unrelated releases; 11 numbers are duplicated this way in
  `opensearch-operator`). Both tags are listed with their commits so you can pick.

The revision number needs a separate source because the docs can't supply it:
when this was written, `opensearch-operator` documented up to revision 315 while
its tags had reached 366 — a 50-release gap. And it's load-bearing, since it also
sets the filename, the MyST anchor and the Compatibility table's revision column.

**Why `from-ref` isn't "documented + 1".** The range is already *exclusive* of
`from-ref`, so `rev315..HEAD` begins at the first commit after the release that
`revision-315.md` documents — incrementing first would apply that offset twice.
And because revisions are allocated in per-architecture pairs, consecutive numbers
often point at the **same commit**: `rev316..rev317` is *empty* where
`rev315..rev317` covers 2 commits. In `opensearch-operator`, 66 of 225 consecutive
revision pairs share a commit, so a `+1` default would silently swallow a release
roughly a third of the time.

One command answers all three — one request, no auth, no pagination, and it
returns the branch heads alongside the tags:

```bash
git ls-remote --tags --heads https://github.com/canonical/opensearch-operator.git
```

Then take the numerically highest `rev<N>` tag. Four things go wrong if you don't:

| Trap | Why it bites |
|------|--------------|
| `gh api .../tags --jq '.[0:5]'` | That endpoint orders refs **lexicographically** — not by date, not by revision number — so a top-N slice is "the tags whose names sort highest" |
| `rev9` vs `rev100` | String ordering puts `rev9` first; revision numbers must be compared numerically |
| Tags may be **namespaced per charm** (`opensearch/rev366`, `opensearch-k8s/rev16`) alongside stale flat `revNNN` tags | Since `r` sorts after `o`, every legacy flat tag sorts ahead of every `opensearch/*` tag, so a slice never sees the live series. No namespace ranking is needed to fix this — revision numbers are monotonic, so the flat series stops where namespacing began and the plain maximum is right anyway |
| Release tags are **annotated** | `git ls-remote` emits a second `<ref>^{}` line with the real commit. Comparing the ref's own SHA to a branch head never matches, silently turning a HEAD-tagged release into "latest + 1" |

Namespaces still matter for two things: API calls need the **full ref**
(`git/refs/tags/opensearch/rev366` — a 404 on a bare `revNNN` means the ref name
is wrong, not that the tag is missing), and the Compatibility table needs a
**specific charm's** number, so filter the tag list by its namespace.

Two more rules the skill applies:

- **A tag at HEAD means the release *is* that revision** — it has already been
  cut and tagged, so the document is titled with that number, not latest + 1.
  When the tag is *behind* HEAD, the next number is only a proposal: revisions
  are allocated in **per-architecture pairs** (`rev365` and `rev366` are the same
  commit), so a new release takes a whole pair and the final number may differ.
  The published convention titles with the higher member of the pair.
- **Never a revision at or below one already documented.** Before generating, the
  skill checks the release-notes folder *and its git history* — a correct
  `revision-366.md` can sit in history while a fresh draft is being numbered 350.
  If any documented revision is greater than or equal to the inferred one, it
  stops and asks you. This checks the *conclusion* rather than the inference, so
  it catches a bad number regardless of what caused it.

**There is no script for this.** It's two commands the agent reads directly —
deliberately, because the interesting part is the reasoning, not the parsing:

```bash
# The latest revision: anchor on the rev/revision prefix, take the digits after
# it, compare numerically.
git ls-remote --tags --heads https://github.com/<owner>/<repo>.git \
  | grep -oiE 'rev(ision)?[-_.]?[0-9]+' | grep -oE '[0-9]+$' | sort -n | tail -1

# The newest revision the docs already cover (sort NUMERICALLY, not alphabetically).
ls docs/reference/release-notes/ | grep -oE '[0-9]+' | sort -n | tail -1
```

The first command also returns the branch heads, which is what the HEAD check
below needs — drop the `grep` pipeline to see them.

That parsing rule is more particular than it looks.
"Strip all the letters and take the biggest number" turns `opensearch-k8s/rev16`
into **816**, so `opensearch-operator`'s highest "revision" comes out as 816
rather than 366 — a document titled "Revision 817". Taking runs of *adjacent*
digits is the fix, and the `rev` anchor is what makes it trustworthy: tag names
carry all sorts of unrelated numbers. `k8s` is the obvious one (it would
contribute an `8` that wins in any repo still on single-digit revisions), but so
are `v4/1.46.0`, `preview7/` and `release-2024-01-15` — that last yields **2024**,
which beats every real revision. Anchoring on `rev` excludes them all at once
instead of maintaining a list of things to strip.

Don't try to solve dates by stripping years, either: a `20[0-9][0-9]` filter would
delete `rev2019`…`rev2099`, and four-digit revisions are already here —
`postgresql-operator` is at **rev1215**.

Surveyed across 14 Canonical charm repos, **all 14 use `rev`-style tags** and the
anchored result matched a plain digit-run scan every time — so the anchor costs
nothing in practice and only guards the edges. If a repo genuinely has no `rev`
tags, the skill falls back to the biggest adjacent digit run (minus `k8s`) but
presents it as a suggestion to confirm, since unanchored it can return a date.

The full failure this prevents, with the real ref data, is written up in
[`examples/Worked-example-namespaced-tags.md`](examples/Worked-example-namespaced-tags.md).

### Docs checks as the final gate

Release notes are the most check-hostile page in a charm's documentation: the
body is largely raw PR titles written by developers, so it arrives full of
misspellings, bare filenames and tool jargon that the docs build treats as
prose. The skill therefore finishes by running the target repository's own
checks against the saved page and looping until they pass:

```bash
python tools/check_autolinks.py <saved-file>   # instant, no network
cd docs && make spelling                       # fast; fix before linkcheck
cd docs && make linkcheck                      # slow — several minutes
```

`make linkcheck` makes a real network request for every external link in the
whole docs set, and a release-notes page adds one per PR link, so the skill
**warns you before it starts**. While iterating, it can narrow the spellcheck
with `make spelling CHECK_PATH=reference/release-notes`, but always confirms
with a full run.

How findings are resolved, in order of preference:

| Finding | Fix |
| :--- | :--- |
| A genuine typo copied from a PR title (`acomodating`) | Correct it in the release notes. A spelling fix doesn't change what the entry says. |
| A code-like token: filename, module, flag, config key (`charm.py`, `metadata.yaml`, `README.md`) | Wrap it in backticks. This fixes the spellcheck **and** stops MyST's linkify turning `charm.py` into a broken `http://charm.py` link. |
| A wrong acronym case (`gcs`) | Fix the case to `GCS`; add `GCS` to the wordlist if needed — never add the lowercase form. |
| A correct word the dictionary lacks (`toolchain`, `rediraffe`, `READMEs`) | Add it to the repo's `docs/.custom_wordlist.txt`, one word per line, in the casing used. |
| A wrong or stale URL | Correct the URL in the document. |
| A URL that's correct but unreachable from CI (login-walled, chat invite, not-yet-published) | Add a narrow regex to `linkcheck_ignore` in `docs/conf.py`, with a comment saying why. |
| A transient `Read timed out` | Leave it alone. Network flakiness, not breakage — never add a valid URL to `linkcheck_ignore`. Raise `linkcheck_timeout` if it persists. |
| A finding in a file you didn't touch | Report it to the user; don't fix unrelated pages or add exceptions on their behalf. |

Fixing the page always beats adding an exception: a `linkcheck_ignore` entry is
permanent config debt that hides future breakage. Findings are never silenced by
deleting or vaguening a changelog entry.

### Domain squatting via auto-linked filenames

**A green linkcheck is not sufficient**, and this failure mode is a security and
reputation problem rather than a cosmetic one.

MyST enables `linkify` by default, with `myst_linkify_fuzzy_links` also
defaulting to `True`, so any bare `word.tld` token in prose becomes a link with
no scheme required. Release notes are made of raw PR titles, which mention
filenames constantly — and **many extensions are live TLDs** (`.md` Moldova,
`.py` Paraguay, `.sh` Saint Helena, plus `.io`, `.co`, `.in`, `.rs`, `.pl`,
`.tf`, `.so`, `.re`, `.cc`, `.ai`). So the bogus link frequently *resolves*, to
whoever squats the domain. Seen in a real build:

```
revision-366.md:147: [redirected with Found] http://README.md to https://dealsbe.com
```

That is a **redirect**, not `[broken]`, so linkcheck exits 0 and the page ships
with a live link to a stranger's site.

`tools/check_autolinks.py` is the gate for this. It asks `linkify-it-py` — the
library MyST itself uses — what it *would* linkify, so it stays correct as the
TLD list changes, and it ignores code spans, fenced blocks, real URLs, emails,
MyST anchors, frontmatter and the review-notes comment:

```console
$ python tools/check_autolinks.py docs/reference/release-notes/revision-366.md
revision-366.md:147:16: 'README.md' would be auto-linked as http://README.md
1 linkify hazard(s) found. Wrap each token in backticks.
Re-run with --explain for the conf.py root-cause fix.
```

A hand-written `grep` over a list of extensions is *not* an adequate substitute:
`.go` and `.html` are not TLDs (no hazard), while `install.sh` and `main.tf` are
— which isn't guessable, so a blocklist silently misses cases.

**The root-cause fix**, which the skill recommends but leaves to you, since it
affects the whole docs set:

```python
# docs/conf.py
myst_linkify_fuzzy_links = False
```

Verified: `README.md`, `charm.py`, `SECURITY.md` stay plain text, while
`https://canonical.com/data` and `foo@example.com` still link. The only
trade-off is that **scheme-less** domains in prose (`canonical.com/data`) stop
auto-linking and must be written as explicit Markdown links — better practice
anyway.

### Frontmatter goes on line 1

If the product's template emits frontmatter (MyST `html_meta`), the opening
`---` must be the **very first line** of the saved file — Sphinx/MyST only
recognises frontmatter there. The review-notes comment and the MyST anchor come
*after* it. Put anything before the frontmatter and the `---` fences are parsed
as body transitions, the `# Revision N` title stops being the document title,
and the build warns `Document headings start at H2, not H1`.

## How the builder script works

Internally, `build_release_notes.py`:

1. Fetches commits between two Git references via the **GitHub Compare API**.
2. Looks up the **merged PR** associated with each commit.
3. **Categorises** changes by PR labels (mapping at the top of the script).
4. Extracts and links **Jira ticket IDs** (e.g. `DPE-1234`) from commit messages
   and PR descriptions, skipping known false positives (`CVE-*`).
5. Renders a **Markdown** document from a Jinja2 template.

### Truncation warning

The GitHub Compare API returns at most **250 commits** per request. If the range
contains more, the script prints a red warning to stderr with the last commit
SHA, so you can re-run with `--from-ref <that SHA>` and merge the results.

### Transient API failures

The script makes one `/commits/{sha}/pulls` request per commit, and that
endpoint intermittently returns `500`. Such responses — along with `429` (rate
limited) and connection errors — are retried up to `HTTP_MAX_RETRIES` times
with exponential backoff (`HTTP_RETRY_BACKOFF`), printing a warning to stderr
on each retry. `4xx` responses are not retried, since retrying cannot help.
Without this, a single flaky response partway through a long range would abort
the run and discard every API call made so far.

### Label → category mapping

The changelog categories come from the
[DA186 spec](https://docs.google.com/document/d/1hR7EOnw_FfP6PFXH4C2NfReZhMdWdBIto0C9MBcwYPs/edit?usp=sharing):
**Features**, **Breaking changes**, **Security**, **Bug fixes**, **Other
improvements**. Each PR is assigned to exactly one of them based on its labels.

Two label vocabularies are supported out of the box, defined at the top of
`build_release_notes.py`. They do not conflict, so a repository can use either
one, or **mix both** — even within the same release.

**DA186 category labels** (recommended for new repos — the label *is* the
category name):

| PR label | Category |
| :--- | :--- |
| `Features` / `Feature` | Features |
| `Breaking changes` / `Breaking change` | Breaking changes |
| `Security` | Security |
| `Bug fixes` / `Bug fix` | Bug fixes |
| `Other improvements` / `Other improvement` | Other improvements |

**Legacy labels** (what Data charm repos use today — still supported, no
migration needed):

| PR label | Category |
| :--- | :--- |
| `bug` | Bug fixes |
| `enhancement` | Features |
| `not bug or enhancement` | Other improvements |
| `documentation` | Other improvements |
| `breaking` | Breaking changes |

Matching rules:

- **Case-insensitive**, and `-`, `_` are treated as spaces (`bug-fixes` ==
  `Bug fixes`).
- A grouping prefix of `type`, `category`, `kind` or `release notes`, separated
  by `:` or `/`, is stripped before matching — so `type: bug fixes` and
  `category/security` work too.
- If a PR carries labels from **several** categories, `CATEGORY_PRIORITY`
  decides the winner: Breaking changes → Security → Features → Bug fixes →
  Other improvements. So a PR labelled both `bug` and `Security` lands under
  Security.
- PRs with **no recognised label** (or no PR at all) land in `DEFAULT_CATEGORY`
  (`Other improvements`). The agent skill re-checks these against the commit
  message during the polish pass.

Categories render in `CATEGORY_ORDER`; empty ones are omitted, per DA186.

To add repo-specific labels, extend `LABEL_CATEGORY_MAP`:

```python
LABEL_CATEGORY_MAP = {
    **DA186_LABEL_CATEGORY_MAP,
    **LEGACY_LABEL_CATEGORY_MAP,
    "cve": "Security",          # your own additions
}
```

## Auto-sort: reclassifying the "Other improvements" catch-all

Because most Data charm PRs are unlabelled, `DEFAULT_CATEGORY` ("Other
improvements") tends to swallow most of a release — including real features and
bug fixes. Measured on actual releases: **59 of 65** entries for Charmed Apache
Kafka, and **67 of 67** for Charmed OpenSearch, whose own previous release notes
had populated Features and Bug fixes sections.

**Auto-sort** is a step performed by the agent skill (not the builder script)
that walks every entry in "Other improvements" and moves the ones whose text
unambiguously identifies a more specific category, using conventional-commit
prefixes and titles as evidence. Entry text is never edited — entries only move
between categories.

### Turning it on and off

Auto-sort is **off by default** and never runs silently. If you don't say either
way, the skill asks once, quantified against the generated drafts (e.g. "48 of 67
entries are in Other improvements; 14 look like features or fixes — run
auto-sort?"). To skip the question, say so in your request:

| Say this | Effect |
| :--- | :--- |
| `auto-sort on`, `autosort`, `sort the other improvements`, `sort the kitchen sink`, `recategorise the catch-all` | Enabled |
| `auto-sort off`, `no auto-sort`, `leave the categories alone`, `keep the builder's categories` | Disabled |

Hyphenation, spacing and capitalisation don't matter.

### Signals it acts on

| Evidence in the entry text | Move to |
| :--- | :--- |
| `feat:` / `feature:` / `perf:` prefix | Features |
| `fix:` / `bugfix:` / `bug-fix:` / `hotfix:` prefix, or a title starting "Fix…" / "Fixing…" / "Resolve…" / "Correct…" | Bug fixes |
| `security:` prefix, or a `CVE-NNNN-NNNNN` reference | Security |
| `!` before the colon (`feat!:`), or "BREAKING CHANGE" | Breaking changes |
| `revert:` prefix | Never moved — flagged instead |

`chore:`, `docs:`, `ci:`, `build:`, `deps:`, `test:`, `style:`, `refactor:` and
`patch:` never trigger a move, and a neutral prefix **beats** a fix verb later in
the title (`patch: Fix tag in metadata.yaml` stays put, unflagged).

Note that `ci`, `test` and `build` appear both as neutral prefixes and as
infrastructure terms (below). They answer different questions and are read from
different parts of the entry: a *prefix* is the author's own classification, so
`ci: re-enable cached builds` is left alone silently; an *infrastructure term* is
what a fix targets, so `fix: re-enable CI cached builds` is left alone **and**
flagged.

### The infrastructure exception

A `fix:` prefix alone does not make something a DA186 bug fix, which means a
*user-visible* defect. Entries whose fix targets CI, workflows, runners,
permissions, linting, test setup, flaky tests, release plumbing, tags, build
caches or docs builds stay in "Other improvements" and are flagged rather than
moved. So `fix: Fix spread installation` stays, while `fix: set blocked status
for invalid object-storage secrets` moves.

These terms match on **word boundaries**. Several are short enough to hide inside
ordinary product vocabulary — `ci` inside "precision", "decision", "capacity",
"circuit"; `tag` inside "stage"; `pin` inside "pinning" — so substring matching
would wrongly withhold real bug fixes like `fix: precision loss in shard
allocation`. Inflected forms ("tests", "tagging", "caches") do count, and `_` is
treated as a boundary so `test` is found in `test_certificate_transfer`.

When a fix signal is present but the title doesn't reveal whether the target is
shipped behaviour or tooling, the entry is left in place and flagged — a wrong
move silently misrepresents the release, so precision is preferred over recall.

### What it won't catch

Entries with no prefix and no fix verb are never moved, however feature-like
they read: `add smtp support` and `add rollback compatibility` (both real
OpenSearch entries) stay in the catch-all. Auto-sort *reduces* manual review; it
doesn't replace it. Guessing from prose would drag CI and docs entries along
with the genuine features.

### Auditability

Every move is recorded in the document's review-notes comment as `PR #N:
"<title>" — Other improvements → <category> (evidence: <signal>)`, together with
entries that carried a signal but were deliberately left alone. If auto-sort
moves nothing, it says so. Auto-sort also never moves an entry between
components.

The rules are pinned by tests in `tests/test_autosort_rules.py`, which encode
the table above and assert it against real entry titles from Charmed Apache
Kafka and Charmed OpenSearch releases:

```bash
python -m pytest tests/test_autosort_rules.py -q
```

## Templates

### Base template (`templates/base.md.j2`)

Defines the full DA186-compliant structure with overridable Jinja2 blocks:

| Block | Purpose |
| :--- | :--- |
| `frontmatter` | Anything above the title (e.g. MyST `html_meta`, anchors) |
| `title` | Release heading |
| `date_line` | Date line below the title |
| `introduction` | Intro paragraph (written by the skill, or manually) |
| `intro_links` | Charmhub / Deploy / Upgrade / System requirements links |
| `changelog` | The whole "list of changes" section |
| `security` | Product-specific security / CVE section (empty by default) |
| `compatibility` | Compatibility table |
| `known_issues` | Known issues section (commented out by default) |
| `footer` | Anything after the known issues section |

The changelog is generated from the `categories` context variable. Override the
`changelog` block when a product renames or reorders sections (see
`templates/spark.md.j2`).

### Product-specific templates

One template per **product**, shared by all of that product's repositories
(`kafka.md.j2` covers both `kafka-operator` and `kafka-k8s-operator`):

```jinja2
{% extends "base.md.j2" %}

{% block intro_links %}
[Charmhub](https://charmhub.io/my-charm) | [Deploy guide](...) | ...
{% endblock %}

{% block compatibility %}
| Column A | Column B | ... |
| :--- | :--- | :--- |
| ... | ... | ... |
{% endblock %}
```

Working examples:

* `templates/kafka.md.j2` — modelled on the published Charmed Apache Kafka
  notes: MyST frontmatter and anchor, no date line, Diátaxis cross-reference
  links, `Improvements` instead of `Other improvements`, and PR-only entry
  links.
* `templates/opensearch.md.j2` — modelled on the published Charmed OpenSearch
  notes: MyST frontmatter and anchor, a plain (non-bold) date line, category
  headings at `###` because the product groups changes under per-component
  `##` headings, bracketed Jira IDs with `([PR \#N](url))` links, and a
  compatibility table with OpenSearch version and minimum Juju version columns.
* `templates/spark.md.j2` — full restructure modelled on the published Charmed
  Apache Spark release notes: MyST frontmatter, product-specific section names
  and order (`Enhancements` instead of `Other improvements`, plus
  `Documentation improvements`, `Security`, `Acknowledgements`), and
  reStructuredText grid tables for the CVE and compatibility matrices.

### If no product template exists

Don't render a product that already has published release notes through
`base.md.j2` — the generic skeleton won't match its established structure.
Create `templates/<product>.md.j2` from the product's newest published release
notes instead (usually `docs/reference/releases/revision-*.md` in the product's
repo, or the rendered docs site), extending the base and overriding the blocks
above. The agent skill does this automatically as step 6 of the workflow.

## Project structure

```
release-notes-builder/
├── build_release_notes.py          # Per-repository changelog generator
├── requirements.txt                # Python dependencies
├── templates/
│   ├── base.md.j2                  # Base DA186-compliant template
│   ├── kafka.md.j2                 # Charmed Apache Kafka extension
│   ├── opensearch.md.j2            # Charmed OpenSearch extension
│   └── spark.md.j2                 # Charmed Apache Spark extension
├── tools/
│   └── check_autolinks.py          # Flags filenames MyST would linkify
├── examples/
│   ├── DA186 - Release notes for Data charms.md   # Spec reference
│   ├── Example-release-notes-spec.md              # PostgreSQL example
│   ├── Worked-example-namespaced-tags.md          # The rev350-vs-366 failure
│   └── 205-248.md / 205-248-prs.md / 205-head.md  # Sample generated outputs
├── release-notes/                  # Standalone-mode output
├── spec/                           # DA186 / DA288 source documents
├── tests/
│   ├── test_autosort_rules.py      # Pins the auto-sort rule table
│   └── test_check_autolinks.py     # Pins the linkify-hazard detector
├── .github/skills/release-notes/SKILL.md   # Agent skill — the only file users install
└── README.md                       # This file
```

Only `SKILL.md` is distributed to users; it fetches `build_release_notes.py`,
`templates/`, `tools/` and `requirements.txt` from this repo on demand into
`~/.cache/release-notes-builder/`. Nothing here needs to be cloned to use the
skill, and the cache lives outside every repository so it can never be committed
by accident.

Run the tests with `python -m pytest tests/ -q`.

## License

See [LICENSE](LICENSE).
