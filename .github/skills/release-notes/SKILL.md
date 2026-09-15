---
name: release-notes
description: 'Generate DA186-compliant release notes for Canonical Data & AI charms. Use when the user asks to "generate release notes", "create release notes", "compile a changelog", "prepare release notes draft", or a similar phrasing/verb, for one or multiple charm repositories (e.g. canonical/kafka-operator) or a link to a previously published release-notes page, optionally for a branch, track, or a commit range. Gathers changes via GitHub API, discovers sibling components from prior release notes, merges multi-repo notes into a single product draft, writes intro and compatibility sections, and saves the result locally for review. Never publishes anything.'
argument-hint: '[repo ...] [--track TRACK] [--branch BRANCH] [--from-ref REF] [--to-ref REF]'
---

# Release Notes Generation (DA186)

Generate a DA186-spec-compliant release notes document for one or more GitHub
repositories (charm components of a single product), saved locally as a
Markdown file for human review. The output must read as a **finished,
publishable release notes document** — see "Fully publishable output" below.
**Never push, post, or publish anything** — all output stays in this local
repository.

## When to Use

- "Generate release notes for canonical/kafka-operator"
- "Prepare release notes for Kafka 4.2 from rev247 to rev248"
- "Compile release notes for https://github.com/canonical/kafka-operator and https://github.com/canonical/kafka-connect-operator as one product"
- "Draft release notes for the 14/stable channel of postgresql-operator"
- "Create release notes for https://canonical.com/data/opensearch/docs/2/reference/release-notes/revision-315/"
  (a link to a *previous* published release; see "Starting from a link to
  previously published release notes" below — generate the *next* release
  after the one that link documents, not that release itself)
- "Write the next OpenSearch release notes" (any generation verb — create,
  write, build, draft, compile, prepare — is treated the same; see "Any
  generation verb triggers this skill" below)

## Running this skill from another repository (the common case)

The automation script (`build_release_notes.py`) and templates (`templates/`)
live in the **release-notes-builder** repository, but the normal way to use
this skill is with a **different** repository open as the workspace — the
charm/product repo you're actually generating release notes for (e.g.
`kafka-operator`, `opensearch-operator`). `release-notes-builder` itself does
not need to be open at all.

There are several ways to make the skill's instructions reach that workspace
(Options A–C below). Pick whichever fits — they all behave identically once
the skill is loaded, because `$BUILDER_HOME` resolution (below) works the
same way in every case.

Note that opening `release-notes-builder` itself and using the skill
normally (i.e. *not* doing any of this) remains fully supported and requires
no setup at all — it's not one of "the ways to reach another repo" because
it isn't reaching another repo; `--repo` can still point at any
`owner/repo`. This is referred to as **standalone mode** elsewhere in this
skill (see step 8's save-location rule and "Where the output goes"), as
opposed to **cross-repo mode** (Options A–C, target repo open instead).

### Option A: personal skill via symlink (recommended for repeat use)

Best when you'll generate release notes regularly across many product repos
and don't want to repeat any setup per repo.

1. Clone or keep a local checkout of `release-notes-builder` anywhere on
   disk — its path doesn't matter.
2. Make the skill available in every workspace by installing it as a
   **personal skill**: symlink (don't copy) its folder into whichever
   personal skills location your agent harness reads, e.g.:
   ```bash
   ln -s /absolute/path/to/release-notes-builder/.github/skills/release-notes \
       ~/.claude/skills/release-notes
   ```
   (also valid: `~/.copilot/skills/release-notes`, `~/.agents/skills/release-notes`
   — pick whichever your setup reads; one symlink is enough, it does not need
   to be repeated per target repo). **Symlink, don't copy** — a copy has no
   way to resolve back to the release-notes-builder checkout that contains
   the actual script and templates.
3. Open the target repository (the one to generate release notes *for*) as
   the workspace. Nothing needs to be added or copied into it.

### Option B: copy the skill into the target repo

Best when you'd rather not touch your personal skills folder, your agent
harness doesn't support personal skills, or you want the skill checked into
the target repo itself (e.g. so teammates get it automatically). No
symlinks or personal-skill install required. Two variants, depending on
whether the target repo should stay dependent on a release-notes-builder
chekout elsewhere on disk or not:

**B1. Lightweight copy (recommended default)** — copy only this skill's
instructions; the script and templates stay canonical in
release-notes-builder:

1. Copy (not symlink) `release-notes-builder`'s
   `.github/skills/release-notes/` folder into the target repository at the
   same relative path: `.github/skills/release-notes/`.
2. A plain copy has no path back to the release-notes-builder checkout, so
   `$BUILDER_HOME` resolution's real-path strategy will fail here by
   design — that's expected, not an error. On the first run in this repo,
   either:
   - answer the agent's one-time question for the checkout path (see
     "Locating the builder script and templates" below) — it writes the
     answer into a `.builder-home` file next to the copied `SKILL.md` so
     later runs in this repo don't ask again, or
   - create that file yourself first:
     `echo /absolute/path/to/release-notes-builder > .github/skills/release-notes/.builder-home`.
3. Decide whether to commit `.builder-home`: commit it only if every
   teammate's release-notes-builder checkout lives at the same path (e.g. a
   documented team convention or CI runner); otherwise add
   `.github/skills/release-notes/.builder-home` to the target repo's
   `.gitignore` and let each teammate generate their own on first use.
4. Remember a copy doesn't auto-update: re-copy the folder whenever
   release-notes-builder's skill instructions change, to pick up fixes and
   new edge-case handling.

**B2. Fully self-contained copy** — also vendor `build_release_notes.py`,
`requirements.txt`, and the product's template(s) into the target repo, so
it has zero runtime dependency on another local checkout (useful for CI
runners, air-gapped machines, or once you're done needing
release-notes-builder itself):

1. Copy `build_release_notes.py`, `requirements.txt`, and a `templates/`
   subfolder containing `base.md.j2` plus the specific product template(s)
   this repo needs (e.g. `templates/kafka.md.j2`) into
   `.github/skills/release-notes/` in the target repo, alongside `SKILL.md`
   — i.e. reproduce the same layout release-notes-builder uses at its repo
   root, just nested one level deeper. Keep the `templates/` subfolder name;
   don't flatten template files directly next to `SKILL.md`, or
   `$BUILDER_HOME/templates/<file>` references elsewhere in this skill won't
   resolve.
2. No `.builder-home` file or env var is needed: `$BUILDER_HOME` resolves to
   this same skill folder because `build_release_notes.py` is found right
   next to `SKILL.md` (see resolution step 2 below).
3. **Trade-off to weigh before choosing B2 over B1**: this variant
   duplicates the actual release-generation logic and product templates
   rather than just the instructions.
   - Bug fixes and template refinements made in release-notes-builder won't
     reach this copy automatically — you have to notice and manually re-sync.
   - A product's template is meant to be a single source of truth shared by
     *all* of that product's repos (e.g. `kafka.md.j2` covers both
     `kafka-operator` and `kafka-k8s-operator`); vendoring a copy into just
     one of them risks the two drifting apart if the template is later
     tweaked in only one place.
   - The target repo now also needs `jinja2`/`requests` installed
     (`pip install -r requirements.txt` from its vendored copy) to run the
     script itself.
   Prefer B1 unless the target repo genuinely must not depend on anything
   outside itself at runtime.

### Option C: zero setup — point the agent at the file directly

Best for a single one-off run, or to try the skill before deciding whether
to install it any other way. Requires nothing beyond having a local checkout
of `release-notes-builder` somewhere:

1. Open the target repository as the workspace (`release-notes-builder` does
   not need to be added to it at all).
2. In your chat message, tell the agent to follow the skill by its absolute
   path instead of relying on discovery, e.g.:
   > Using the skill instructions at
   > `/home/you/release-notes-builder/.github/skills/release-notes/SKILL.md`,
   > generate release notes for canonical/kafka-operator
3. The agent reads that file directly like any other file — no skill
   registration, symlink, or workspace change happens. `$BUILDER_HOME`
   resolution (below) still works correctly because it only depends on the
   real path of the `SKILL.md` that was loaded, not on how it was found.

### Locating the builder script and templates ($BUILDER_HOME)

Every reference in this skill to `build_release_notes.py` or
`templates/<file>` means the copy inside the release-notes-builder checkout,
resolved once per run — the same way regardless of which option (A–C) above
was used to load these instructions, or standalone mode:

1. Resolve the real path of whichever `SKILL.md` these instructions were
   loaded from (following the symlink in Option A; the literal path given in
   Option C; simply the workspace root in standalone mode) and take the
   folder three levels up (`.github/skills/release-notes/../../..`) as
   `$BUILDER_HOME`. Verify `build_release_notes.py` exists there. This step
   is *expected* to fail for Option B1 (a plain instructions-only copy has
   no real path back to release-notes-builder) — fall through to step 2
   without treating it as an error.
2. Check whether `build_release_notes.py` exists directly next to this
   `SKILL.md` (i.e. colocated in the same folder, not three levels up). If
   so, that folder itself is `$BUILDER_HOME` — this is what makes Option B2
   (fully self-contained copy) work with no further configuration.
3. Check for a `.builder-home` file colocated with this `SKILL.md` (i.e. at
   `.github/skills/release-notes/.builder-home`, relative to wherever it was
   loaded from). If present, its first line is the absolute path to
   `$BUILDER_HOME`. This is the primary mechanism for Option B1 (see its
   setup steps) but is checked in every option.
4. If all of the above fail, check the `RELEASE_NOTES_BUILDER_HOME`
   environment variable.
5. If that's unset too, ask the user for the local path to their
   release-notes-builder checkout (once). Then persist the answer so future
   runs skip this ask: for Option B1, write it to
   `.github/skills/release-notes/.builder-home` (per its setup steps 2–3);
   otherwise suggest `export RELEASE_NOTES_BUILDER_HOME=...` in the user's
   shell profile.

The generated release notes themselves are **not** saved into
`$BUILDER_HOME` when running in cross-repo mode (Options A–C) — they're
saved into the currently open target repository instead (for Option B,
that's the very repo the skill copy lives in, even for B2 where
`$BUILDER_HOME` also happens to be inside it). See step 8 for the exact
rule.

## Any generation verb triggers this skill

Treat "generate", "create", "compile", "draft", "prepare", "write", "build",
and similar verbs applied to "release notes" / "changelog" as equivalent
requests — they all mean run this skill's full procedure. The verb used has
no bearing on scope or thoroughness: don't skip template selection, sibling-
component discovery, compatibility, or the DA186 checklist just because the
user said "create" instead of "generate".

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
| Repositories | — (required, unless given as a previous release notes link) | `owner/repo` or full GitHub URL; one or more |
| Previous release notes link | — (optional alternate to naming repos) | A URL to an already-published release-notes page (e.g. a `revision-NNN` docs page); resolves product, track, from-ref, and component list — see "Starting from a link to previously published release notes" |
| Track | The documentation's default track (see above) | Ask if it can't be determined |
| Branch | The track's branch (repo default branch if single-track product) | Resolve via GitHub API |
| From-ref | See "Resolving from-ref" below | Tag/SHA/branch |
| To-ref | HEAD of the branch | Tag/SHA/branch |
| Product name / title | Derived from repos | e.g. "Charmed Apache Kafka" |
| Output file | See step 8: the target repo's existing release-notes location when run cross-repo, else `release-notes/<product>-<to-ref>.md` | Ask the user if no existing location can be found in the target repo |

If the user gives only repositories, proceed with defaults and only ask
about genuinely ambiguous things (see "Ask the user" below).

## Procedure

### 1. Resolve references

First resolve the track scope (see "Track / channel scope" above) — this is
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
   a. User-specified ref.
   b. The most recent tag/release that is an ancestor of the branch: list
      the latest few tags for all repos in one loop
      (`gh api repos/{owner}/{repo}/tags --jq '.[0:5]'`), then confirm
      ancestry with one `compare` call per candidate tag — stop at the first
      one that's an ancestor.
   c. Only for repos where (b) didn't resolve: the last documented release
      in the product's documentation — fetch the *one* release-notes page
      for the resolved track (not other tracks), and use the revision/tag it
      documents.
   d. If neither can be determined, ask the user which ref to start from.
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

Record which source was used for each repo — it goes into the review notes.
If a repo's default branch is a single-track repo (e.g. `spark-k8s-toolkit-py`
with only `main`), it needs no track disambiguation at all — resolve it like
any single-branch repo.

### 2. Select or create the product template

Before generating any draft, decide which Jinja template to render with.
**Never** fall back to `templates/base.md.j2` for a product that has published
release notes of its own — the base template produces a generic DA186 skeleton
that will not match the product's established structure, links or section
names.

1. **Look for an existing product template** in `$BUILDER_HOME/templates/`
   (see "Locating the builder script and templates" above — this is
   `templates/` at the release-notes-builder repo root, not the currently
   open target repo). Match on the *product*, not the repository:
   `templates/spark.md.j2` covers every Charmed Apache Spark repo
   (`spark-k8s-bundle`, `kyuubi-k8s-operator`, `charmed-spark-rock`,
   `spark-client-snap`, …), just as `templates/kafka.md.j2` covers the Kafka
   repos. List the directory rather than guessing a filename.
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
  enhancement`, `breaking`), so a repo may mix both. Anything unlabelled
  lands in "Other improvements", which is where most miscategorisation shows
  up. Recategorise only when the message itself is unambiguous (e.g. a `fix:`
  prefix). Otherwise leave and flag.
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
- **Facts**: never rewrite a message to say something different, never
  invent Jira IDs, PR numbers, versions, or dates.

### 5. Write the introduction

Based on the contents of the merged draft, write the intro (replacing the
`INTRO-TODO` / TODO comment):

- 1–3 paragraphs, brief summary of the most important changes (new features,
  breaking changes, workload version bumps). Write it as the final,
  publishable summary — see "Fully publishable output" below; do not call
  the document a draft anywhere in this text.
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
  versions, and minimum/recommended Juju version.
- Sources of truth: the repo's `charmcraft.yaml` (`platforms`/`bases`),
  `metadata.yaml`, `snapcraft.yaml` or rock's `rockcraft.yaml`, the release
  tag's assets, and the previous release notes' compatibility table (bump
  what changed).
- **Cheap arch→revision pairing**: for charms/snaps released per-architecture,
  take the latest two consecutive tag numbers on the branch as the AMD64/ARM64
  pair by default (see "Keep data gathering lean") instead of confirming via
  workflow logs. Mark the pairing as a TODO for the release owner to verify.
- If a value cannot be determined from the repo, leave a clearly marked
  `TODO` and flag it in the review notes — do not guess.

### 7. Ask the user (only when needed)

Query the user for a preferred resolution when:

- The from-ref could not be determined automatically (step 1.3.d).
- The commit range was truncated and the user should choose how to proceed.
- Two entries look like the same change but differ in wording (possible
  double-count) and it is not obvious which to keep.
- A suspicious entry appears (e.g. a revert without its original, a merge
  commit listed as a change, an entry whose message contradicts its PR).
- Compatibility values are missing and cannot be derived from the repo.
- One or more sibling components were detected in the product's previous
  release notes but weren't named by the user (step 1.4.b) — always ask,
  never include them by default.
- A confirmed sibling component's GitHub repo can't be determined
  automatically (step 1.4.d) — ask the user for the repository address
  instead of guessing.

Batch unrelated small questions into one ask; never ask about anything you
can resolve yourself from the repos.

## Fully publishable output

The saved document must read as the **final, ready-to-publish release
notes** — not a draft, not a work in progress:

- Never write the words "draft", "upcoming", or similar hedging in the
  title, introduction, or any visible body text. Write the title and intro
  as if this is the actual release (e.g. `# Charmed Apache Spark (revision
  8)` with the real/expected revision, not `(upcoming stable release —
  draft)`).
- It is fine, and expected, to leave an invisible HTML comment block
  (`<!-- ... -->`) at the top with review notes, source-of-truth
  references, and imperative TODOs for the release owner (see below) — that
  comment is the *only* place allowed to acknowledge open items.
- Every visible heading and section must be complete prose, not a stub —
  no bracketed placeholders in the rendered text.

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
     not release-notes-builder — the common case, see "Running this skill
     from another repository" above): save into *that* repository, following
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
        do not guess or invent a path.
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
- [ ] If the input was a link to a previously published release-notes page,
      the generated document covers the *next* release after that page, not
      the release the page itself documents.
- [ ] Saved to the correct location for this invocation mode (see step 8):
      the target repo's existing release-notes folder — confirmed with the
      user if none was found — in cross-repo mode; `release-notes/` in
      standalone mode. Never saved into `$BUILDER_HOME/release-notes/` while
      running in cross-repo mode.

## Reference

- Spec: `examples/DA186 - Release notes for Data charms.md`
- Example output: `examples/Example-release-notes-spec.md`
- Builder script: `build_release_notes.py` (see `README.md` for CLI reference)
- Templates: `templates/base.md.j2` (generic DA186 skeleton),
  `templates/kafka.md.j2`, `templates/opensearch.md.j2`,
  `templates/spark.md.j2` — product templates live alongside the base and
  extend it (see step 2)
