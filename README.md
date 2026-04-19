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
| `title` | Release heading |
| `date_line` | Date line below the title |
| `introduction` | Intro paragraph (edit manually after generation) |
| `intro_links` | Charmhub / Deploy / Upgrade / System requirements links |
| `compatibility` | Compatibility table |
| `known_issues` | Known issues section (commented out by default) |

The changelog section is generated automatically from the `categories` context variable.

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

See `templates/kafka.md.j2` for a working example.

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
│   └── kafka.md.j2                 # Kafka product extension
├── DA186 - Release notes for Data charms.md   # Spec reference
├── Example-release-notes-spec.md              # PostgreSQL example
└── README.md                       # This file
```

## License

See [LICENSE](LICENSE).
