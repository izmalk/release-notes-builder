---
name: release-notes
description: 'Generate DA186-compliant release notes for Canonical Data & AI charms. Use when the user asks to "generate release notes", "compile a changelog", "prepare release notes draft" for one or multiple charm repositories (e.g. canonical/kafka-operator), optionally for a branch, track, or a commit range. Gathers changes via GitHub API, merges multi-repo notes into a single product draft, writes intro and compatibility sections, and saves the result locally for review. Never publishes anything.'
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
| Repositories | — (required) | `owner/repo` or full GitHub URL; one or more |
| Track | The documentation's default track (see above) | Ask if it can't be determined |
| Branch | The track's branch (repo default branch if single-track product) | Resolve via GitHub API |
| From-ref | See "Resolving from-ref" below | Tag/SHA/branch |
| To-ref | HEAD of the branch | Tag/SHA/branch |
| Product name / title | Derived from repos | e.g. "Charmed Apache Kafka" |
| Output file | `release-notes/<product>-<to-ref>.md` | Relative to repo root |

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

Record which source was used for each repo — it goes into the review notes.
If a repo's default branch is a single-track repo (e.g. `spark-k8s-toolkit-py`
with only `main`), it needs no track disambiguation at all — resolve it like
any single-branch repo.

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
  labels, which are often missing. Recategorise only when the message itself
  is unambiguous (e.g. a `fix:` prefix). Otherwise leave and flag.
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

### 4. Write the introduction

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
- **Cheap arch→revision pairing**: for charms/snaps released per-architecture,
  take the latest two consecutive tag numbers on the branch as the AMD64/ARM64
  pair by default (see "Keep data gathering lean") instead of confirming via
  workflow logs. Mark the pairing as a TODO for the release owner to verify.
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

### 7. Save the final document

1. Write the final document to `release-notes/<product>-<to-ref>.md`
   (create the `release-notes/` directory if needed).
2. Remove the temporary per-repo drafts in `.github/skills/release-notes/tmp/`.
3. Present the file to the user with a short summary of:
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
      Other improvements); each entry links a PR and/or commit; empty
      categories omitted.
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
      text in between (see step 3).
- [ ] Unless the user explicitly asked for a multi-track/product-wide
      document, the release notes cover a single track (see "Track /
      channel scope").

## Reference

- Spec: `examples/DA186 - Release notes for Data charms.md`
- Example output: `examples/Example-release-notes-spec.md`
- Builder script: `build_release_notes.py` (see `README.md` for CLI reference)
- Templates: `templates/base.md.j2`, product templates alongside it
