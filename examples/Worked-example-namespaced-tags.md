# Worked example: namespaced tags and the wrong revision number

This records a real failure and the exact reasoning that avoids it. Observed
2026-09-15 against `canonical/opensearch-operator` and
`canonical/opensearch-dashboards-operator`, both on track branch `2/edge`.

There is deliberately no script for this: the resolution is two `git ls-remote`
and `ls` commands, documented in `SKILL.md` under "Resolving the range and the
revision number". What matters is the reasoning below, not the parsing.

## What went wrong

The skill picked the revision number for the document title with:

```bash
gh api "repos/canonical/opensearch-operator/tags" --jq '.[0:5][].name'
```

which returned five flat `rev34x` tags, the highest being `rev349`. The draft
was therefore titled **"Revision 350"**. The correct answer was **366**.

Two independent causes combined:

1. **`GET /repos/{owner}/{repo}/tags` orders refs lexicographically** — not by
   tag date, not by revision number. A `.[0:5]` slice is "the five tags whose
   names sort highest", not "the five newest tags".
2. **The repo namespaces tags per charm.** The live series is
   `opensearch/rev*`; the flat `rev*` tags are frozen legacy leftovers from
   before several charms were merged into one single-kernel repo.

Because `r` sorts after `o`, *every* stale flat tag sorted ahead of *every*
`opensearch/*` tag. The slice never saw the live series at all.

It then got worse in two follow-on ways:

- The sibling dashboards component was numbered rev73 (next after the flat
  `rev72`) instead of rev79.
- A verification call, `gh api .../git/refs/tags/rev366`, returned 404 — the
  ref is `opensearch/rev366` — and the 404 was misread as "that tag doesn't
  exist" rather than "that ref name is wrong".

The repo already contained a correct `revision-366.md` from an earlier run, so
two contradictory documents ended up side by side. The discrepancy was spotted
by the user, not by the skill.

## The actual ref data

Complete listing, in one unauthenticated call with no pagination:

```bash
git ls-remote --tags --heads https://github.com/canonical/opensearch-operator.git
```

`canonical/opensearch-operator` — 349 tags, in four groups:

| Series | Count | Highest | Status |
|--------|-------|---------|--------|
| `<flat>` (`rev1`…`rev349`) | 324 | `rev349` | **legacy**, frozen |
| `opensearch/rev*` | 12 | `opensearch/rev366` | live series for this charm |
| `opensearch-k8s/rev*` | 12 | `opensearch-k8s/rev16` | live series for a *different* charm |
| `discourse-gatekeeper/base-content` | 1 | — | bookkeeping, not a release tag |

Note what the numbers do: the flat series **stops** at 349 and the namespaced one
**continues** from 350. Revision numbering is monotonic per repo, so the plain
numeric maximum over *all* tags is the latest release — no namespace ranking
required. The only thing the naive approach got wrong was slicing instead of
enumerating, and sorting names instead of comparing numbers.

`canonical/opensearch-dashboards-operator` — 81 tags:

| Series | Count | Highest | Status |
|--------|-------|---------|--------|
| `<flat>` (`rev1`…`rev72`) | 70 | `rev72` | **legacy**, frozen |
| `opensearch-dashboards/rev*` | 6 | `opensearch-dashboards/rev78` | live series |
| `opensearch-dashboards-k8s/rev*` | 4 | `opensearch-dashboards-k8s/rev5` | different charm |
| `discourse-gatekeeper/base-content` | 1 | — | bookkeeping |

## HEAD comparison (note the peel lines)

Both release tags are **annotated**, so the ref points at a tag object and
`git ls-remote` emits a second `^{}` line with the underlying commit. Only that
peeled SHA can be compared against a branch head:

```
73177e12…  refs/heads/2/edge
98304479…  refs/tags/opensearch/rev366        <- tag object, never matches a commit
73177e12…  refs/tags/opensearch/rev366^{}     <- the commit; equals 2/edge HEAD
```

```
9e4daef6…  refs/heads/2/edge
e97c74c8…  refs/tags/opensearch-dashboards/rev78
1f5db4fe…  refs/tags/opensearch-dashboards/rev78^{}   <- behind HEAD
```

## Revisions come in per-architecture pairs

Grouping the peeled commits reveals that each release allocates **two**
consecutive revisions, one per architecture:

```
73177e12  opensearch/rev365  opensearch/rev366   opensearch-k8s/rev15  opensearch-k8s/rev16
1f5db4fe  opensearch-dashboards/rev77  opensearch-dashboards/rev78
186da447  opensearch-dashboards/rev73  opensearch-dashboards/rev74
cbaa552c  rev71  rev72        <- the legacy flat series paired the same way
```

Three consequences:

* The published document titles with the **higher** member of the pair — 366, and
  16 for the k8s charm.
* "latest + 1" is therefore a **convention, not a fact**: the next release after
  `rev78` allocates the pair 79+80. Propose 79 and flag it for confirmation
  rather than asserting it.
* **`from-ref` must never be "documented + 1".** The range is already exclusive of
  `from-ref`, and pairing makes the increment actively destructive:

  ```console
  $ git rev-parse --short rev315^{commit} rev316^{commit} rev317^{commit}
  40b31b75   # rev315
  10ec9a90   # rev316
  10ec9a90   # rev317  <- same commit as rev316

  $ git rev-list --count rev315..rev317
  2          # correct
  $ git rev-list --count rev316..rev317
  0          # a whole release silently disappears
  ```

  Between rev100 and rev349, **66 of 225** consecutive pairs share a commit, so
  this would misfire on roughly a third of releases. The real `revision-366.md`
  correctly used `from-ref: rev315`.

## Correct reasoning, per component

**OpenSearch** — `opensearch/rev366` is the highest revision in the series
belonging to this charm. Its peeled commit equals the `2/edge` HEAD, so the
release has already been cut and tagged: the document is **Revision 366**, not
367 and certainly not 350. The flat `rev349` is ignored as legacy.

**Dashboards** — `opensearch-dashboards/rev78` is the highest in its series,
but its peeled commit is *behind* the `2/edge` HEAD, so there are undocumented
commits after it and the release being documented is the next one:
**Revision 79**. Again the flat `rev72` is ignored.

Reproduce:

```console
$ for r in opensearch-operator opensearch-dashboards-operator; do
>   git ls-remote --tags "https://github.com/canonical/$r.git" \
>     | grep -v '\^{}' | grep -oE 'rev[0-9]+' | sed 's/rev//' | sort -n | tail -1
> done
366
78
```

`366` is at the `2/edge` HEAD, so that release is already cut and the document is
titled **366**. `78` is behind HEAD, so the next one is **79** — flagged for the
release owner to verify, because of the pairing below.

## The guard that would have caught it anyway

The tag heuristic is one link in a chain; the guard checks the *conclusion*,
which is why it catches this whole error class regardless of cause. Against the
real checkout, with the namespaced tags artificially removed to reproduce the
original wrong inference of 350:

```
REVISION:    350

STOP: this repository already documents a revision at or above the inferred 350:
  revision 366: docs/reference/release-notes/revision-366.md
  revision 315: docs/reference/release-notes/revision-315.md
  revision 314: docs/reference/release-notes/revision-314.md (git history)
Do not generate over this. Ask the user whether to document a later revision,
update the existing document, or use a different from-ref.
```

Git history is checked as well as the working tree, because the evidence may
have been committed and later moved or deleted.

## Rules extracted

1. Enumerate tags **completely**; a top-N slice of an API's default ordering is
   never "the latest".
2. Compare revision numbers **numerically** (`rev9` outranks `rev100` as a
   string). With monotonic numbering, that alone defeats stale flat tags — no
   namespace ranking needed.
2b. Anchor on the **`rev`/`revision` prefix** and take the adjacent digit run.
   Flattening the whole name by deleting non-digits turns `opensearch-k8s/rev16`
   into **816**, making 816 the apparent maximum instead of 366. Adjacent runs fix
   that; the `rev` anchor is what keeps unrelated numbers out — `k8s` (→ 8),
   `v4/1.46.0` (→ 46) and `release-2024-01-15` (→ 2024, beating every real
   revision) would otherwise all compete.
3. **Peel annotated tags** before comparing to a branch head.
4. A tag **at HEAD** means the release *is* that revision, not the next one.
5. When the tag is behind HEAD, `latest + 1` is a **proposal**: revisions come in
   per-architecture pairs, so confirm the number before publishing.
6. Use the **full namespaced ref** in every API call; a 404 on a bare `revNNN`
   means the ref name is wrong, not that the tag is missing.
7. Namespaces are needed only for the full ref and for a **specific charm's**
   number in the Compatibility table.
8. Never generate a revision **at or below** one the repo already documents.
9. `from-ref` comes from the **docs**; the revision number comes from the
   **tags**. Neither source can do the other's job — the docs lagged the tags by
   50 revisions here.
