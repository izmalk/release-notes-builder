# Release Notes Builder

Generate DA186-spec-compliant release notes for Canonical Data & AI charms from
GitHub commit and pull-request data, rendered through Jinja2 templates.

## Overview

The tool:

1. Fetches commits between two Git references via the **GitHub Compare API**.
2. Looks up the **merged PR** associated with each commit.
3. **Categorises** changes by PR labels (configurable mapping at the top of the script).
4. Extracts **Jira ticket IDs** (e.g. `DPE-1234`) from commit messages and PR descriptions, and links them automatically.
5. Renders everything into a **Markdown** release-notes document using a Jinja2 template.

Product-specific templates (e.g. `kafka.md.j2`) extend the base template to inject
their own Charmhub links and compatibility table structure.

## Prerequisites

- Python 3.10+
- A GitHub personal access token (recommended for higher rate limits; required for private repos)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python build_release_notes.py \
    --repo canonical/kafka-operator \
    --from-ref rev247 \
    --to-ref rev248 \
    --template templates/kafka.md.j2
```

### CLI reference

| Argument | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `--repo` | Yes | — | Repository in `owner/repo` format or full GitHub URL. |
| `--from-ref` | Yes | — | Start reference (tag, branch, or SHA). Changes **after** this ref are included. |
| `--to-ref` | No | Branch HEAD | End reference (tag, branch, or SHA). Changes **before** this ref are included.|
| `--branch` | No | Repo default | Branch to resolve `--to-ref` against when omitted. |
| `--template` | Yes | — | Path to the Jinja2 template file. |
| `--title` | No | `--to-ref` value | Release title shown in the heading (e.g. `"Revision 248"`). |
| `--token` | No | `GITHUB_TOKEN` env var | GitHub personal access token (overrides env var). |
| `--output` | No | stdout | Write output to this file instead of stdout. |
| `--use-prs` | No | Off | Use PR titles instead of commit messages for changelog entries. |

### Authentication

The script checks for a token in this order:

1. `--token` CLI argument
2. `GITHUB_TOKEN` environment variable
3. Unauthenticated (public repos only, 60 requests/hour rate limit)

### Examples

**Basic — write to stdout:**

```bash
python build_release_notes.py \
    --repo canonical/kafka-operator \
    --from-ref rev247 \
    --to-ref rev248 \
    --template templates/kafka.md.j2
```

**Write to file, use PR titles, custom title:**

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

**From a tag to latest commit on default branch:**

```bash
python build_release_notes.py \
    --repo canonical/postgresql-operator \
    --from-ref rev550 \
    --template templates/base.md.j2
```

## Label → category mapping

The mapping lives at the top of `build_release_notes.py` and is easy to adjust:

```python
LABEL_CATEGORY_MAP = {
    "bug": "Bug fixes",
    "enhancement": "Features",
    "not bug or enhancement": "Other improvements",
    # "security": "Security",
    # "breaking": "Breaking changes",
}

DEFAULT_CATEGORY = "Other improvements"   # catch-all for unlabelled PRs
```

Labels are matched **case-insensitively**. PRs whose labels don't match any
key land in `DEFAULT_CATEGORY`. Empty categories are omitted from output.

## Template customisation

### Base template (`templates/base.md.j2`)

Defines the full DA186-compliant structure with overridable Jinja2 blocks:

| Block | Purpose |
| :--- | :--- |
| `frontmatter` | Anything above the title (e.g. MyST `html_meta`, anchors) |
| `title` | Release heading |
| `date_line` | Date line below the title |
| `introduction` | Intro paragraph (edit manually after generation) |
| `intro_links` | Charmhub / Deploy / Upgrade / System requirements links |
| `changelog` | The whole "list of changes" section |
| `security` | Product-specific security / CVE section (empty by default) |
| `compatibility` | Compatibility table |
| `known_issues` | Known issues section (commented out by default) |
| `footer` | Anything after the known issues section |

The changelog section is generated automatically from the `categories` context
variable. Override the `changelog` block when a product renames or reorders its
sections (see `templates/spark.md.j2`).

### Product-specific templates

Create a new file that extends the base:

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

* `templates/kafka.md.j2` — minimal extension: product links plus a
  compatibility table, keeping the base DA186 section names and order.
* `templates/spark.md.j2` — full restructure modelled on the published
  Charmed Apache Spark release notes: MyST frontmatter, product-specific
  section names and order (`Enhancements` instead of `Other improvements`,
  plus `Documentation improvements`, `Security` and `Acknowledgements`), and
  reStructuredText grid tables for the CVE and compatibility matrices.

### If no product template exists

Don't render a product that already has published release notes through
`base.md.j2` — the generic skeleton won't match its established structure.
Create `templates/<product>.md.j2` from the product's newest published release
notes instead (usually `docs/reference/releases/revision-*.md` in the product's
docs repo), extending the base and overriding the blocks above. The agent skill
does this automatically as step 2 of its procedure.

## Agentic skill: automatic release notes

This repository ships an agent skill (`.github/skills/release-notes/`) that
automates the full DA186 release-notes workflow. Point your AI agent at one
or multiple repositories and it will:

1. Resolve the commit range per repo (default branch; from the most recent
   release/tag or the last documented release notes in the docs, to the
   branch HEAD — or user-specified refs).
2. Pick the product's Jinja template from `templates/` — or, if the product
   has none, build one from its published release notes before generating
   anything.
3. Run `build_release_notes.py` per repository to gather and categorise
   changes.
4. Merge the per-repo drafts into a single product document directly (the
   agent reads each draft and reorganises it under per-component headings) —
   each component gets its own set of categories; empty components/categories
   are omitted. There is no separate merge script: the agent has to read
   every draft in full to polish it anyway, so a mechanical pre-merge step
   would just duplicate that work and risks its own formatting bugs.
5. Polish the draft (duplicates, miscategorised entries, false Jira-ID
   matches, formatting) without altering the facts, querying the user on
   ambiguous cases.
6. Write the introduction (1–3 paragraphs) and populate the Compatibility
   section from repo sources of truth (`charmcraft.yaml`, `metadata.yaml`,
   snap/rock metadata, release tags).
7. Save the result for review (see "Where the output goes" below).

Nothing is ever pushed or posted — all output stays local.

Invoke it from the agent chat with, e.g.:

> Generate release notes for canonical/kafka-operator and
> canonical/kafka-k8s-operator from rev247 to rev248

### Running it from the repo you're releasing (recommended, common case)

You normally don't need this repository open at all — the skill is meant to
be run with the **target product repo** (e.g. `kafka-operator`) open as your
workspace instead. There are a few ways to make that work; pick whichever
suits your workflow (full details and prerequisites for each are in
[`SKILL.md`](.github/skills/release-notes/SKILL.md#running-this-skill-from-another-repository-the-common-case)):

| Option | Setup | Best for |
| :--- | :--- | :--- |
| **A. Personal skill via symlink** | One-time: symlink `.github/skills/release-notes/` into `~/.claude/skills/` (or your harness's personal-skills folder) | Repeat use across many product repos, no per-repo setup |
| **B1. Copy the skill (lightweight)** | Copy `.github/skills/release-notes/` (instructions only) into the target repo at the same path | No personal-skill support, or want it checked in for teammates, while still relying on a release-notes-builder checkout for the actual script/templates |
| **B2. Copy the skill (self-contained)** | Also vendor `build_release_notes.py`, `requirements.txt`, and the needed template(s) into the copied skill folder | Same as B1, but the target repo must have zero runtime dependency on another checkout (e.g. CI, air-gapped) — trades that for template/script duplication, see caveats in SKILL.md |
| **C. Zero setup** | None — just tell the agent to follow the skill instructions at the absolute path to `SKILL.md` in your chat message | A single one-off run, or trying the skill before installing it |

Options A–C keep the **target repo** as your workspace and save output there
(see "Where the output goes" below). Opening `release-notes-builder` itself
and using the skill normally isn't listed as an option here — it's not a way
of *reaching* another repo, since it doesn't involve one; it needs no setup
at all and behaves exactly like the standalone example earlier in this
section.

**Option A quick setup:**
```bash
ln -s /absolute/path/to/release-notes-builder/.github/skills/release-notes \
    ~/.claude/skills/release-notes
```
(or `~/.copilot/skills/release-notes`, `~/.agents/skills/release-notes` —
whichever your agent harness reads). **Symlink, don't copy** — the skill
resolves the builder script and templates by following the symlink back to
this repo, so this only needs to be done once, ever, regardless of how many
target repos you use it with afterwards.

**Option B1 quick setup:**
```bash
cp -r /absolute/path/to/release-notes-builder/.github/skills/release-notes \
    /path/to/target-repo/.github/skills/release-notes
```
A plain (instructions-only) copy can't resolve back to this repo on its
own, so on first use the agent asks for this repo's path once and remembers
it in a `.builder-home` file next to the copied skill — or create that file
yourself upfront:
`echo /absolute/path/to/release-notes-builder > .github/skills/release-notes/.builder-home`.
Only commit `.builder-home` if every teammate's checkout is at the same
path; otherwise `.gitignore` it. Re-copy the skill folder whenever this
repo's skill instructions change — copies don't auto-update.

**Option B2 quick setup** (on top of B1's copy) — also vendor the script and
templates so nothing outside the target repo is needed at runtime:
```bash
cp /absolute/path/to/release-notes-builder/build_release_notes.py \
   /absolute/path/to/release-notes-builder/requirements.txt \
   /path/to/target-repo/.github/skills/release-notes/
cp -r /absolute/path/to/release-notes-builder/templates \
   /path/to/target-repo/.github/skills/release-notes/templates
```
No `.builder-home` needed here — the skill finds `build_release_notes.py`
right next to itself. The trade-off: this duplicates the release-generation
logic and product template(s), which then won't receive upstream fixes
automatically and can drift from a template shared by the product's other
repos — see the full caveats in
[`SKILL.md`](.github/skills/release-notes/SKILL.md#running-this-skill-from-another-repository-the-common-case).
Prefer B1 unless the target repo genuinely can't depend on anything outside
itself at runtime.

**Option C quick example** — with only the target repo open, ask:
> Using the skill instructions at
> `/home/you/release-notes-builder/.github/skills/release-notes/SKILL.md`,
> generate release notes for canonical/kafka-operator

### Where the output goes

- **Cross-repo** (target repo open, per above): the file is saved **inside
  the target repo**, in whatever folder its previous release notes already
  live in (e.g. `docs/reference/release-notes/revision-316.md`), following
  that folder's existing naming convention. If no such folder can be found,
  the agent asks where to save it — it never guesses.
- **Standalone** (this repo itself is open, e.g. while developing the tool):
  falls back to the local `release-notes/<product>-<to-ref>.md`.

## Truncation warning

The GitHub Compare API returns at most **250 commits** per request. If the
range contains more, the script prints a **red warning** to stderr with the
last commit SHA, so you can re-run with `--from-ref <that SHA>` and merge
the results.

## Post-generation steps

The generated file is a **draft**. You will typically need to:

1. Write the **Introduction** section (summary of key highlights).
2. Fill in the **Compatibility** table with exact revisions, versions, and artefact links.
3. Optionally add a **Known issues** section.
4. Review and polish individual changelog entries.

## Project structure

```
release-notes-builder/
├── build_release_notes.py          # Main script
├── requirements.txt                # Python dependencies
├── templates/
│   ├── base.md.j2                  # Base DA186-compliant template
│   ├── kafka.md.j2                 # Charmed Apache Kafka extension
│   └── spark.md.j2                 # Charmed Apache Spark extension
├── examples/
│   ├── DA186 - Release notes for Data charms.md   # Spec reference
│   ├── Example-release-notes-spec.md              # PostgreSQL example
│   ├── 205-248.md / 205-248-prs.md / 205-head.md   # Sample generated outputs
├── .github/
│   └── skills/
│       └── release-notes/
│           └── SKILL.md            # Agentic skill (see above)
└── README.md                       # This file
```

## License

See [LICENSE](LICENSE).
