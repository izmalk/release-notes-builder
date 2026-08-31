---
name: release-notes
description: 'Generate DA186-compliant release notes for Canonical Data & AI charms. Use when the user asks to "generate release notes", "compile a changelog", "prepare release notes draft" for one or multiple charm repositories (e.g. canonical/kafka-operator), optionally for a branch or a commit range. Gathers changes via GitHub API, merges multi-repo notes into a single product draft, writes intro and compatibility sections, and saves the result locally for review. Never publishes anything.'
argument-hint: '[repo ...] [--branch BRANCH] [--from-ref REF] [--to-ref REF]'
---

# Release Notes Generation (DA186)

Generate a DA186-spec-compliant release notes draft for one or more GitHub
repositories (charm components of a single product), saved locally as a
Markdown file for human review. **Never push, post, or publish anything** —
all output stays in this local repository.

## When to Use

- "Generate release notes for canonical/kafka-operator"
- "Prepare release notes for Kafka 4.2 from rev247 to rev248"
- "Compile release notes for https://github.com/canonical/kafka-operator and https://github.com/canonical/kafka-connect-operator as one product"
- "Draft release notes for the 14/stable channel of postgresql-operator"

## Inputs (ask only if not given)

| Input | Default | Notes |
|-------|---------|-------|
| Repositories | — (required) | `owner/repo` or full GitHub URL; one or more |
| Branch | Repo default branch | Resolve via GitHub API |
| From-ref | See "Resolving from-ref" below | Tag/SHA/branch |
| To-ref | HEAD of the branch | Tag/SHA/branch |
| Product name / title | Derived from repos | e.g. "Charmed Apache Kafka" |
| Output file | `release-notes/<product>-<to-ref>.md` | Relative to repo root |

If the user gives only repositories, proceed with defaults and only ask
about genuinely ambiguous things (see "Ask the user" below).

## Procedure

### 1. Resolve references

For each repository:

1. Determine the branch (user-specified, else the repo's default branch via
   `gh api repos/{owner}/{repo} --jq .default_branch` or the GitHub API).
2. Determine `to-ref`: user-specified, else the latest commit on the branch
   (omit `--to-ref` when invoking the builder script; it defaults to branch HEAD).
3. Determine `from-ref` (in priority order):
   a. User-specified ref.
   b. The most recent release/tag in the repo: list tags via
      `gh api repos/{owner}/{repo}/releases --jq '.[0].tag_name'` (or
      `/tags`), and use the latest tag that is an ancestor of the branch.
   c. The last documented release in the product's documentation: search the
      `docs/` directory (or the repo's docs sources) for the most recent
      release-notes page (e.g. `docs/reference/release-notes/*`), and use the
      revision/tag it documents.
   d. If neither can be determined, ask the user which ref to start from.

Record which source was used for each repo — it goes into the review notes.

### 2. Generate per-repo drafts

Run the automation script once per repository, writing each draft to a
temporary file (do not leave intermediate files in the repo root):

```bash
python build_release_notes.py \
    --repo <owner/repo> \
    --from-ref <from-ref> \
    [--to-ref <to-ref>] \
    [--branch <branch>] \
    --template templates/base.md.j2 \
    --title "<Component name>" \
    --use-prs \
    --output .github/skills/release-notes/tmp/<repo>-draft.md
```

Notes:
- Use `templates/base.md.j2` unless a product-specific template exists in
  `templates/` that matches the repo (e.g. `templates/kafka.md.j2` for
  `canonical/kafka-operator`).
- `--use-prs` gives cleaner entries (PR titles) — prefer it.
- If the script warns that the commit range was **truncated** (>250 commits),
  re-run with `--from-ref <last-sha>` for the remainder and merge the two
  outputs, or ask the user how to proceed.
- If a repo has no changes in the range, skip it and note that in the review
  notes.

### 3. Merge the drafts and polish the changelog

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
- After all components, a single `## Compatibility` heading (see step 5).

While merging, check for obvious mistakes that can be fixed **without
altering the facts**:

- **Duplicates**: the same change appearing twice (e.g. a PR merged then
  reverted, or sync PRs between k8s/VM variants of the same charm). Remove
  exact duplicates; for near-duplicates across components, keep both but
  flag them in the review notes.
- **Categorisation**: entries with `fix:`/`Fix ...` in the message sitting
  outside "Bug fixes", or `feat:` outside "Features" — the builder maps PR
  labels, which are often missing. Recategorise only when the message itself
  is unambiguous (e.g. a `fix:` prefix). Otherwise leave and flag.
- **False Jira IDs**: the builder script links any `[A-Z][A-Z0-9]+-\d+`
  pattern as a Jira ticket. This misfires on non-Jira strings such as
  `UTF-8`, `ISO-8601`, `RFC-822`, `K8S-1` (verified). Drop the fake link
  when the "ticket" is clearly not a Jira ID (not in a known project prefix
  like `DPE-`, `DA-`, `KP-`, etc.), but leave the surrounding text untouched.
- **Noise**: entries like "sync with k8s", "rename tests", CI-only churn —
  keep them (they belong in "Other improvements") but consider grouping
  trivial docs/CI entries; never delete a change outright.
- **Formatting**: broken Markdown links, stray `\[[` escapes, empty
  parentheses, trailing whitespace, entries missing PR links.
- **Facts**: never rewrite a message to say something different, never
  invent Jira IDs, PR numbers, versions, or dates.

### 4. Write the introduction

Based on the contents of the merged draft, write the intro (replacing the
`INTRO-TODO` / TODO comment):

- 1–3 paragraphs, brief summary of the most important changes (new features,
  breaking changes, workload version bumps).
- Below it, the links line per DA186: Charmhub | Deploy guide | Upgrade
  instructions | System requirements. Derive the URLs from the product's
  docs (e.g. `https://canonical.com/data/docs/<product>/iaas/...`); if the
  product is unknown, leave `TODO` links and flag them for the user.

### 5. Populate the Compatibility section

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
  versions, and minimum/recommended Juju version.
- Sources of truth: the repo's `charmcraft.yaml` (`platforms`/`bases`),
  `metadata.yaml`, `snapcraft.yaml` or rock's `rockcraft.yaml`, the release
  tag's assets, and the previous release notes' compatibility table (bump
  what changed).
- If a value cannot be determined from the repo, leave a clearly marked
  `TODO` and flag it in the review notes — do not guess.

### 6. Ask the user (only when needed)

Query the user for a preferred resolution when:

- The from-ref could not be determined automatically (step 1.3.d).
- The commit range was truncated and the user should choose how to proceed.
- Two entries look like the same change but differ in wording (possible
  double-count) and it is not obvious which to keep.
- A suspicious entry appears (e.g. a revert without its original, a merge
  commit listed as a change, an entry whose message contradicts its PR).
- Compatibility values are missing and cannot be derived from the repo.

Batch unrelated small questions into one ask; never ask about anything you
can resolve yourself from the repos.

### 7. Save the final draft for review

1. Write the final document to `release-notes/<product>-<to-ref>.md`
   (create the `release-notes/` directory if needed).
2. Remove the temporary drafts in `.github/skills/release-notes/tmp/`.
3. Present the file to the user with a short summary of:
   - Components covered and their commit ranges (and how from-ref was chosen).
   - Categories with notable highlights.
   - Any TODOs left for the user (compat values, links, flagged entries).

## DA186 compliance checklist

Verify the final document against the spec before saving:

- [ ] Title contains the charm revision (or other unique release designation)
      and the exact date follows it.
- [ ] Introduction: brief summary + Charmhub / upgrade / deploy / system
      requirements links.
- [ ] List of changes: full list since previous stable release, distributed
      among categories (Features, Breaking changes, Security, Bug fixes,
      Other improvements); each entry links a PR and/or commit; empty
      categories omitted.
- [ ] Compatibility: workload versions, software dependencies (Juju
      versions), hardware architectures (with per-architecture revisions
      if applicable).
- [ ] Known issues section: optional; add only if the user asks or evidence
      exists — it can be appended later.
- [ ] Nothing was published — the file exists only in this local repository.

## Reference

- Spec: `examples/DA186 - Release notes for Data charms.md`
- Example output: `examples/Example-release-notes-spec.md`
- Builder script: `build_release_notes.py` (see `README.md` for CLI reference)
- Templates: `templates/base.md.j2`, product templates alongside it
