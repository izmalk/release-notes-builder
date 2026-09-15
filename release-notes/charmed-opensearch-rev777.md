<!--
REVIEW NOTES — delete this whole comment before publishing.

Source of truth for scope, track and from-refs:
  https://canonical.com/data/opensearch/docs/2/reference/release-notes/revision-315/
  (raw: canonical/opensearch-operator, docs/reference/release-notes/revision-315.md)
That page documents the PREVIOUS release; this document covers the next one.

Track: 2 (single track; both repos' default branch is `2/edge`).
Rendered from templates/opensearch.md.j2, created for this run from the
revision-315 source — no OpenSearch template existed before.

Components and commit ranges (to-ref = HEAD of `2/edge` in each repo):
  Charmed OpenSearch             canonical/opensearch-operator             rev315..2/edge  49 commits
  Charmed OpenSearch Dashboards  canonical/opensearch-dashboards-operator  rev60..2/edge   18 commits
Both components were confirmed in scope by the release owner, as was the choice
of from-ref (see TODO 2).

TODOs — act on each before publishing:

1. Replace the revision number in the title, the anchor, the frontmatter
   description and the Compatibility table. `777` is a placeholder supplied for
   this run. Latest tags are `rev349` (opensearch) and `rev72` (dashboards).

2. Decide how to present the undocumented releases in this range, and adjust
   the introduction accordingly. Tags have advanced well past the last
   published notes: revision 315 is documented, but `rev316`–`rev349` were
   tagged without release notes (same for dashboards `rev61`–`rev72`). The
   release owner chose to generate from `rev315`/`rev60`, so this document
   covers that entire gap — roughly 34 charm revisions' worth of change — not
   just the newest release. Either say so explicitly in the introduction, or
   split this into per-revision documents.

3. Fill in the Compatibility table. Verified facts, and what is still open:
   - `opensearch` snap: `2/stable` is revision 98 / 2.19.4 (unchanged since
     revision 315); `2/edge` is revision 261 / **2.19.6**. Record the revision
     and version this release actually ships, and update the OpenSearch
     version column and its release-tag link to match.
   - `opensearch-dashboards` snap: `2/stable` is revision 54 / 2.19.4;
     `2/edge` is revision 155 / 2.19.6. Same instruction as above.
   - Confirm the minimum Juju version is still 3.5+ — carried over from
     revision 315 and not re-verified against the charms' metadata.
   - Confirm AMD64 is still the only published architecture.

4. Write the introduction, replacing the placeholder paragraph. It currently
   summarises what the commit range contains; rewrite it as the real product
   summary and drop anything that does not belong in this release.

5. Re-categorise entries by hand — this is the largest task in this document.
   Every one of the 67 entries landed in "Other improvements" because **no PR
   in either range carries a `bug` or `enhancement` label**; the only labels
   used were `documentation` (14) and `dependencies`/`not bug or enhancement`
   (1 each), all of which map to "Other improvements". Contrast this with
   revision 315, which published populated Features and Bug fixes sections
   for both components, so the sections are expected to be non-empty here too.
   Candidates spotted while merging, left in place because the wording alone
   is not decisive — verify each against its PR before moving it:
   - Likely **Features**: "feat: support GCS repository for snapshot
     operations" (#766), "feat: create buckets/containers if not available"
     (#782), "add smtp support" (#789), "add rollback compatibility" (#786).
   - Likely **Bug fixes**: "fix: handle the situation that opensearch_failover
     does not exist" (#781), "fix: set blocked status for invalid
     object-storage secrets" (#804), "fix: add missing LIBID to notifications
     manager" (#797), "Bug-fix: removing the hard-coded unit value…" (#799),
     "Fix charm Build" (#806), "Fix/temporary file service account gcs"
     (#815).
   - Deliberately NOT moved: `fix:`/`patch:` entries that touch tests, CI or
     release plumbing rather than shipped behaviour (#812, #834, #836, #848,
     #854, #246, #278).
   To avoid repeating this next release, consider labelling PRs — the builder
   accepts either the DA186 category labels or the legacy `bug`/`enhancement`
   ones (see "Label → category mapping" in the builder's README).

6. Verify these flagged entries:
   - `opensearch-operator` #830 and `opensearch-dashboards-operator` #275 both
     merge a Kubernetes charm into the VM charm's repository. Confirm whether
     this release now ships K8s variants from these repos, and whether the
     Compatibility table needs rows for them.
   - Eight "Bump …-single-kernel to v0.0.N" entries (#819, #839, #841, #845,
     #851, #855, #266, #281, #283) are incremental bumps of the same shared
     library. Consider collapsing them into one entry naming the final
     version, rather than listing each bump.
   - "chore: Update OpenSearch Dashboards docs submodule" appears twice in
     Charmed OpenSearch (#838, #849) — genuinely two separate commits, not a
     double-count.
   - #818 ("Remove unit tests, integration tests … leaving only charm.py") is
     a large deletion that reads as a refactor step rather than a user-visible
     change. Confirm it belongs in published notes at all.

7. Verify all artefacts and links resolve before publishing.
-->
---
myst:
  html_meta:
    description: "Charmed OpenSearch revision 777 release notes - GCS snapshot repositories, SMTP notifications, single-kernel migration, and a documentation revamp."
---

(reference-release-notes-revision-777)=
# Revision 777

September 15, 2026

<!-- TODO: Replace this paragraph with the real release summary; see review note 4. -->
This release adds Google Cloud Storage as a snapshot repository backend and SMTP-based notifications to Charmed OpenSearch, and migrates both Charmed OpenSearch and Charmed OpenSearch Dashboards onto the shared single-kernel charm library. Both components also consolidate their Kubernetes and machine charms into a single repository each, and the documentation for both has been revamped and republished.

[Charmhub](https://charmhub.io/opensearch) | [Deploy guide](how-to-deploy-standard) | [Upgrade instructions](how-to-minor-upgrade) | [System requirements](reference-system-requirements)

## Charmed OpenSearch

The primary charm gained new snapshot and notification capabilities, moved onto the shared single-kernel library, and absorbed the Kubernetes charm.

### Other improvements

* Release notes for new release ([PR \#761](https://github.com/canonical/opensearch-operator/pull/761))
* Pin Terraform Version ([PR \#778](https://github.com/canonical/opensearch-operator/pull/778))
* fix: handle the situation that opensearch_failover does not exist ([PR \#781](https://github.com/canonical/opensearch-operator/pull/781))
* chore: update rust toolchain ([PR \#784](https://github.com/canonical/opensearch-operator/pull/784))
* docs: Home page remodeling ([PR \#785](https://github.com/canonical/opensearch-operator/pull/785))
* feat: support GCS repository for snapshot operations ([PR \#766](https://github.com/canonical/opensearch-operator/pull/766))
* [[DPE-7579](https://warthogs.atlassian.net/browse/DPE-7579)] Fix manual upgrades tests for large deployments ([PR \#672](https://github.com/canonical/opensearch-operator/pull/672))
* [Docs] Fix the 404 error page ([PR \#787](https://github.com/canonical/opensearch-operator/pull/787))
* docs: add Dashboards documentation link to the Nav Menu ([PR \#776](https://github.com/canonical/opensearch-operator/pull/776))
* docs: Implement rediraffe redirects ([PR \#788](https://github.com/canonical/opensearch-operator/pull/788))
* feat: create buckets/containers if not available ([PR \#782](https://github.com/canonical/opensearch-operator/pull/782))
* [[DPE-9144](https://warthogs.atlassian.net/browse/DPE-9144)] add smtp support ([PR \#789](https://github.com/canonical/opensearch-operator/pull/789))
* docs: Add GA and cookie consent ([PR \#791](https://github.com/canonical/opensearch-operator/pull/791))
* docs: Add autogenerated metadata description ([PR \#793](https://github.com/canonical/opensearch-operator/pull/793))
* chore: add LIBID, LIBPATCH to notifications ([PR \#795](https://github.com/canonical/opensearch-operator/pull/795))
* fix: add missing LIBID to notifications manager ([PR \#797](https://github.com/canonical/opensearch-operator/pull/797))
* [[DPE-9280](https://warthogs.atlassian.net/browse/DPE-9280)] docs: Restructure documentation content ([PR \#790](https://github.com/canonical/opensearch-operator/pull/790))
* Bug-fix: removing the hard-coded unit value + acomodating for the mutual exclusivness of units and machines variables ([PR \#799](https://github.com/canonical/opensearch-operator/pull/799))
* docs: Update the cookie banner ([PR \#801](https://github.com/canonical/opensearch-operator/pull/801))
* [[DPE-4727](https://warthogs.atlassian.net/browse/DPE-4727)] docs: Add Dashboards mentions ([PR \#798](https://github.com/canonical/opensearch-operator/pull/798))
* Fix charm Build ([PR \#806](https://github.com/canonical/opensearch-operator/pull/806))
* Re-enable charmcraft build cache ([PR \#807](https://github.com/canonical/opensearch-operator/pull/807))
* [[DPE-9332](https://warthogs.atlassian.net/browse/DPE-9332)] docs: Add Dashboard docs content as a submodule ([PR \#803](https://github.com/canonical/opensearch-operator/pull/803))
* fix: set blocked status for invalid object-storage secrets ([PR \#804](https://github.com/canonical/opensearch-operator/pull/804))
* [[DPE-9411](https://warthogs.atlassian.net/browse/DPE-9411)] docs: Structure updates ([PR \#808](https://github.com/canonical/opensearch-operator/pull/808))
* fix: Fix spread installation ([PR \#812](https://github.com/canonical/opensearch-operator/pull/812))
* [[DPE-9412](https://warthogs.atlassian.net/browse/DPE-9412)] docs: Us spelling update ([PR \#810](https://github.com/canonical/opensearch-operator/pull/810))
* Fix/temporary file service account gcs ([PR \#815](https://github.com/canonical/opensearch-operator/pull/815))
* [[DPE-9022](https://warthogs.atlassian.net/browse/DPE-9022)] Add rollback docs ([PR \#743](https://github.com/canonical/opensearch-operator/pull/743))
* [[DPE-9134](https://warthogs.atlassian.net/browse/DPE-9134)] add rollback compatibility ([PR \#786](https://github.com/canonical/opensearch-operator/pull/786))
* patch: Remove unit tests, integration tests(except test_charm.py) and remove charm code leaving only charm.py ([PR \#818](https://github.com/canonical/opensearch-operator/pull/818))
* patch: Bump opensearch-charms-single-kernel to v0.0.5 ([PR \#819](https://github.com/canonical/opensearch-operator/pull/819))
* docs: Homepage upgrade ([PR \#823](https://github.com/canonical/opensearch-operator/pull/823))
* docs: Finalise Url migration ([PR \#826](https://github.com/canonical/opensearch-operator/pull/826))
* docs: Upgrade Sphinx Stack ([PR \#829](https://github.com/canonical/opensearch-operator/pull/829))
* docs: Add tutorial test ([PR \#824](https://github.com/canonical/opensearch-operator/pull/824))
* [[DPE-10677](https://warthogs.atlassian.net/browse/DPE-10677)] patch: Grouping the kubernetes charm and VM charm in single repo ([PR \#830](https://github.com/canonical/opensearch-operator/pull/830))
* patch: Remove tag job from release workflows ([PR \#834](https://github.com/canonical/opensearch-operator/pull/834))
* patch: Fix tag in metadata.yaml ([PR \#836](https://github.com/canonical/opensearch-operator/pull/836))
* chore: Update OpenSearch Dashboards docs submodule ([PR \#838](https://github.com/canonical/opensearch-operator/pull/838))
* patch: Bump opensearch-charms-single-kernel to v0.0.9 ([PR \#839](https://github.com/canonical/opensearch-operator/pull/839))
* [[DPE-10534](https://warthogs.atlassian.net/browse/DPE-10534)] patch: Bump opensearch-charms-single-kernel to v0.0.10 ([PR \#841](https://github.com/canonical/opensearch-operator/pull/841))
* [[DPE-10850](https://warthogs.atlassian.net/browse/DPE-10850)][[DPE-10867](https://warthogs.atlassian.net/browse/DPE-10867)] patch: Bump opensearch-charms-single-kernel to v0.0.12 ([PR \#845](https://github.com/canonical/opensearch-operator/pull/845))
* patch: Fix charmcraft revision ([PR \#848](https://github.com/canonical/opensearch-operator/pull/848))
* [[DPE-10428](https://warthogs.atlassian.net/browse/DPE-10428)] docs: Documentation revamp ([PR \#827](https://github.com/canonical/opensearch-operator/pull/827))
* chore: Update OpenSearch Dashboards docs submodule ([PR \#849](https://github.com/canonical/opensearch-operator/pull/849))
* [[DPE-11035](https://warthogs.atlassian.net/browse/DPE-11035)][[DPE-11026](https://warthogs.atlassian.net/browse/DPE-11026)][[DPE-10922](https://warthogs.atlassian.net/browse/DPE-10922)][[DPE-10876](https://warthogs.atlassian.net/browse/DPE-10876)] patch: Bump opensearch-charms-single-kernel to v0.0.13 ([PR \#851](https://github.com/canonical/opensearch-operator/pull/851))
* fix: Fix tutorial test ([PR \#854](https://github.com/canonical/opensearch-operator/pull/854))
* patch: Bump opensearch-charms-single-kernel to v0.0.14 ([PR \#855](https://github.com/canonical/opensearch-operator/pull/855))

## Charmed OpenSearch Dashboards

Dashboards moved onto the shared single-kernel library, absorbed its Kubernetes charm, and had its documentation migrated into the Charmed OpenSearch documentation set.

### Other improvements

* Documentation content migrated and published to RTD ([PR \#225](https://github.com/canonical/opensearch-dashboards-operator/pull/225))
* docs: Update the Dashboards docs to fit into OpenSearch docs better ([PR \#234](https://github.com/canonical/opensearch-dashboards-operator/pull/234))
* docs: Fix spell check errors in READMEs ([PR \#237](https://github.com/canonical/opensearch-dashboards-operator/pull/237))
* docs: update README.md ([PR \#239](https://github.com/canonical/opensearch-dashboards-operator/pull/239))
* [[DPE-9414](https://warthogs.atlassian.net/browse/DPE-9414)] docs: Build submodule automation ([PR \#241](https://github.com/canonical/opensearch-dashboards-operator/pull/241))
* patch: fix spread installation ([PR \#246](https://github.com/canonical/opensearch-dashboards-operator/pull/246))
* docs: Test pr automation ([PR \#250](https://github.com/canonical/opensearch-dashboards-operator/pull/250))
* docs: Fix dashboards docs update workflow ([PR \#252](https://github.com/canonical/opensearch-dashboards-operator/pull/252))
* [[DPE-9763](https://warthogs.atlassian.net/browse/DPE-9763)] patch: Migrate to single kernel ([PR \#253](https://github.com/canonical/opensearch-dashboards-operator/pull/253))
* patch: Bump opensearch-dashboards-charms-single-kernel to v0.0.6 ([PR \#266](https://github.com/canonical/opensearch-dashboards-operator/pull/266))
* Update rust in charmcraft.yaml ([PR \#268](https://github.com/canonical/opensearch-dashboards-operator/pull/268))
* docs: Documentation content revamp ([PR \#273](https://github.com/canonical/opensearch-dashboards-operator/pull/273))
* [[DPE-10681](https://warthogs.atlassian.net/browse/DPE-10681)] patch: Merge dashboards k8s in dashboards-operator ([PR \#275](https://github.com/canonical/opensearch-dashboards-operator/pull/275))
* [[DPE-10681](https://warthogs.atlassian.net/browse/DPE-10681)] patch: Fix release ([PR \#278](https://github.com/canonical/opensearch-dashboards-operator/pull/278))
* docs: Fix a link ([PR \#276](https://github.com/canonical/opensearch-dashboards-operator/pull/276))
* patch: Bump opensearch-dashboards-charms-single-kernel to v0.0.10 ([PR \#281](https://github.com/canonical/opensearch-dashboards-operator/pull/281))
* docs: docs revamp minor updates migration ([PR \#282](https://github.com/canonical/opensearch-dashboards-operator/pull/282))
* patch: Bump opensearch-dashboards-charms-single-kernel to v0.0.11 ([PR \#283](https://github.com/canonical/opensearch-dashboards-operator/pull/283))

## Compatibility

| Charm | Revision | Hardware architecture | OpenSearch version | Minimum Juju version | Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Charmed OpenSearch | TODO | AMD64 | TODO | 3.5+ | Snap: TODO |
| Charmed OpenSearch Dashboards | TODO | AMD64 | TODO | 3.5+ | Snap: TODO |
