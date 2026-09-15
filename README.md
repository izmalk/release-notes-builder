# Release Notes Builder

Generate DA186-spec-compliant release notes for Canonical Data & AI charms from
GitHub commit and pull-request data, rendered through Jinja2 templates.

The repository contains two things:

- **`build_release_notes.py`** — a script that turns a commit range in *one*
  GitHub repository into a categorised changelog document.
- **`.github/skills/release-notes/SKILL.md`** — an agent skill that drives the
  whole release-notes workflow for a *product* (which usually spans several
  repositories), calling the script as one of its steps.

## End-to-end workflow

This is the intended path from "we want to release" to "a document ready for
review". Steps 3–10 are performed by the agent skill; you only do 1 and 2.

1. **You decide to release** a new charm revision (or a new product release).
2. **You open the product's own repository** (e.g. `kafka-operator`) as your
   workspace and make the skill reachable from it — via symlink, a copy, or by
   pointing the agent at `SKILL.md` directly (see
   [Running it from the repo you're releasing](#running-it-from-the-repo-youre-releasing-recommended-common-case)).
   This is a one-time setup for options A/B; option C needs none.
3. **You ask the agent for release notes**, identifying the release either by
   naming repositories and refs, or — most conveniently — by linking the
   **previously published** release-notes page. From that link the skill
   derives the product, the track, the starting ref, and the component list,
   and generates the *next* release after it.
4. **The skill resolves scope and references**: the track (one track per
   document by default), the branch, `from-ref` (user-specified → latest
   ancestor tag/release → last documented release in the docs → ask you), and
   `to-ref` (branch HEAD by default).
5. **The skill discovers the product's sibling components** — companion charms,
   snaps, rocks, Terraform modules, dashboards — from the previous release
   notes, and **asks you to confirm each one** before adding it to scope. It
   never adds a component silently, and asks for the repository address if a
   component can't be mapped to one automatically.
6. **The skill selects the product's Jinja template** from `templates/` (matched
   on product, not repository). If none exists, it **creates one** from the
   product's most recent published release notes and verifies it renders. It
   never falls back to the generic `base.md.j2` for a product that already has
   published release notes.
7. **The skill runs `build_release_notes.py` once per repository** in scope,
   writing per-repo drafts into a system temp directory (never into either
   repository's tree).
8. **The skill merges the drafts into one product document** and polishes it in
   the same pass — one `## <Component>` heading per component with changes,
   DA186-ordered categories beneath it, duplicates and miscategorised entries
   fixed, false Jira-ID links dropped. Facts are never rewritten; ambiguous
   cases are raised with you. There is deliberately no merge script.
9. **The skill writes the introduction and the Compatibility section** — the
   intro from the merged changelog, compatibility from repository sources of
   truth (`charmcraft.yaml`, `metadata.yaml`, snap/rock metadata, release tags)
   and the previous release notes' table.
10. **The skill saves the document and reports back**: into the open target
    repository's existing release-notes folder, following its naming convention
    (asking you if no such folder exists); or into `release-notes/` here when
    this repository is itself the workspace. It then deletes the temp drafts and
    summarises coverage, highlights, and any TODOs left for you in an invisible
    HTML comment at the top of the file.

The output is a **finished, publishable document** — open items live only in
that top comment, as imperative TODOs. **Nothing is ever pushed or published**;
all output stays local.

Invoke it from the agent chat with, for example:

> Generate release notes for canonical/kafka-operator and
> canonical/kafka-k8s-operator from rev247 to rev248

or:

> Create release notes for
> https://canonical.com/data/opensearch/docs/2/reference/release-notes/revision-315/

## Running it from the repo you're releasing (recommended, common case)

You normally don't need this repository open at all — the skill is meant to run
with the **target product repo** open as your workspace. Pick whichever option
suits your workflow; full details are in
[`SKILL.md`](.github/skills/release-notes/SKILL.md#running-this-skill-from-another-repository-the-common-case).

| Option | Setup | Best for |
| :--- | :--- | :--- |
| **A. Personal skill via symlink** | One-time: symlink `.github/skills/release-notes/` into `~/.claude/skills/` (or your harness's personal-skills folder) | Repeat use across many product repos, no per-repo setup |
| **B1. Copy the skill (lightweight)** | Copy `.github/skills/release-notes/` (instructions only) into the target repo at the same path | No personal-skill support, or you want it checked in for teammates, while the script and templates stay canonical here |
| **B2. Copy the skill (self-contained)** | Also vendor `build_release_notes.py`, `requirements.txt`, and the needed template(s) into the copied skill folder | The target repo must have zero runtime dependency on another checkout (CI, air-gapped) — at the cost of script/template duplication |
| **C. Zero setup** | None — tell the agent to follow the skill instructions at the absolute path to `SKILL.md` | A single one-off run, or trying the skill before installing it |

Opening `release-notes-builder` itself (**standalone mode**) also works and
needs no setup at all; it just isn't a way of *reaching* another repository.
`--repo` still accepts any `owner/repo`.

**Option A quick setup:**
```bash
ln -s /absolute/path/to/release-notes-builder/.github/skills/release-notes \
    ~/.claude/skills/release-notes
```
(or `~/.copilot/skills/release-notes`, `~/.agents/skills/release-notes` —
whichever your harness reads). **Symlink, don't copy** — the skill finds the
builder script and templates by following the symlink back here.

**Option B1 quick setup:**
```bash
cp -r /absolute/path/to/release-notes-builder/.github/skills/release-notes \
    /path/to/target-repo/.github/skills/release-notes
```
An instructions-only copy can't resolve back here on its own, so on first use
the agent asks for this repo's path once and stores it in a `.builder-home`
file next to the copied skill — or create it yourself:
`echo /absolute/path/to/release-notes-builder > .github/skills/release-notes/.builder-home`.
Commit `.builder-home` only if every teammate's checkout is at the same path;
otherwise `.gitignore` it. Re-copy the folder whenever this repo's skill
instructions change — copies don't auto-update.

**Option B2 quick setup** (on top of B1's copy):
```bash
cp /absolute/path/to/release-notes-builder/build_release_notes.py \
   /absolute/path/to/release-notes-builder/requirements.txt \
   /path/to/target-repo/.github/skills/release-notes/
cp -r /absolute/path/to/release-notes-builder/templates \
   /path/to/target-repo/.github/skills/release-notes/templates
```
No `.builder-home` is needed — the skill finds the script next to itself. The
trade-off: the generation logic and product template(s) are duplicated, won't
receive upstream fixes, and can drift from the template shared by the product's
other repos. Prefer B1 unless the target repo genuinely can't depend on
anything outside itself.

**Option C quick example** — with only the target repo open, ask:
> Using the skill instructions at
> `/home/you/release-notes-builder/.github/skills/release-notes/SKILL.md`,
> generate release notes for canonical/kafka-operator

### Where the output goes

- **Cross-repo** (target repo open): saved **inside the target repo**, in the
  folder its previous release notes already live in (e.g.
  `docs/reference/release-notes/revision-316.md`), following that folder's
  naming convention. If no such folder is found, the agent asks — it never
  guesses.
- **Standalone** (this repo is open): `release-notes/<product>-<to-ref>.md`.

## The builder script

`build_release_notes.py` handles a single repository and a single commit range:

1. Fetches commits between two Git references via the **GitHub Compare API**.
2. Looks up the **merged PR** associated with each commit.
3. **Categorises** changes by PR labels (mapping at the top of the script).
4. Extracts and links **Jira ticket IDs** (e.g. `DPE-1234`) from commit messages
   and PR descriptions, skipping known false positives (`CVE-*`).
5. Renders a **Markdown** document from a Jinja2 template.

Merging multiple repositories, the introduction, and the compatibility table are
*not* the script's job — the agent skill does those.

### Prerequisites

- Python 3.10+
- A GitHub personal access token (recommended for rate limits; required for
  private repos): `export GITHUB_TOKEN=$(gh auth token)`

```bash
pip install -r requirements.txt
```

### Usage

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

### Truncation warning

The GitHub Compare API returns at most **250 commits** per request. If the range
contains more, the script prints a red warning to stderr with the last commit
SHA, so you can re-run with `--from-ref <that SHA>` and merge the results.

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

* `templates/kafka.md.j2` — minimal extension: product links plus a
  compatibility table, keeping the base DA186 section names and order.
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

## Manual post-generation steps

If you run the script by hand rather than through the skill, the output is a
**draft**; you will need to:

1. Write the **Introduction** section (summary of key highlights).
2. Fill in the **Compatibility** table with exact revisions, versions, and
   artefact links.
3. Optionally add a **Known issues** section.
4. Review and polish individual changelog entries.

## Project structure

```
release-notes-builder/
├── build_release_notes.py          # Per-repository changelog generator
├── requirements.txt                # Python dependencies
├── templates/
│   ├── base.md.j2                  # Base DA186-compliant template
│   ├── kafka.md.j2                 # Charmed Apache Kafka extension
│   └── spark.md.j2                 # Charmed Apache Spark extension
├── examples/
│   ├── DA186 - Release notes for Data charms.md   # Spec reference
│   ├── Example-release-notes-spec.md              # PostgreSQL example
│   └── 205-248.md / 205-248-prs.md / 205-head.md  # Sample generated outputs
├── release-notes/                  # Standalone-mode output
├── spec/                           # DA186 / DA288 source documents
├── .github/skills/release-notes/SKILL.md   # Agent skill (the workflow above)
└── README.md                       # This file
```

## License

See [LICENSE](LICENSE).
