---
myst:
  html_meta:
    description: "Charmed Apache Kafka revision 777 release notes - Apache Kafka 4.3.0, OpenTelemetry tracing, monorepo consolidation, Kafka UI high availability and identity integration."
---
<!--
REVIEW NOTES — delete this whole comment before publishing.

Source of truth for scope, track and from-refs:
  https://canonical.com/data/kafka/docs/4/reference/release-notes/revision-248/
  (raw: canonical/kafka-operator, docs/reference/release-notes/revision-248.md)
That page documents the PREVIOUS release; this document covers the next one.

Track: 4 (single track). Rendered from templates/kafka.md.j2.

Components and commit ranges (from-ref = the revision documented on the
revision-248 page; to-ref = HEAD of `main` in each repo):
  Charmed Apache Kafka          canonical/kafka-operator          rev248..main  45 commits
  Charmed Apache Kafka Connect  canonical/kafka-connect-operator  rev33..main   11 commits
  Charmed Karapace              canonical/karapace-operator       rev21..main    4 commits
  Charmed Kafka UI              canonical/kafka-ui-operator        rev6..main    5 commits
All four components were confirmed in scope by the release owner.

TODOs — act on each before publishing:

1. Replace the revision number in the title, the anchor, the frontmatter
   description and the Charmed Apache Kafka row of the Compatibility table.
   `777` is a placeholder supplied for this run; `kafka-operator`'s `rev*`
   tags stop at `rev248` on track 4 (newer tags are version-style, e.g.
   `v4/1.46.0`), so the real charm revision could not be derived.
2. Fill in every `TODO` in the Compatibility table. Confirmed facts and the
   reason each value is still open:
   - Charmed Apache Kafka snap: `charmed-kafka` has no `4/stable` channel
     yet — only `4/edge` (revision 77, version 4.3.0). Publish to stable and
     record the stable revision here.
   - Charmed Apache Kafka distribution: bump from `4.1.1-ubuntu4` once the
     4.3.0 release artefact is published on Launchpad.
   - Charmed Karapace snap: only `4/edge` exists (revision 12, version
     4.1.2). Record the stable revision once promoted.
   - Charmed Kafka UI snap: the Snap Store API returned no data for
     `charmed-kafka-ui`; look up its revision manually.
   - Charm revisions: latest tags are `rev26` (karapace), `rev9` (kafka-ui),
     `rev38` (kafka-connect). Confirm which of these ship in this release
     rather than assuming the newest tag.
   - Update the "Apache Kafka release notes" line with the upstream versions
     this release actually ships (4.3.0 is in `4/edge` today).
3. Decide how to present Charmed Apache Kafka Connect: `kafka-connect-operator`
   is now ARCHIVED on GitHub (its last change is
   "docs: archive repository in favor of canonical/kafka-operator", and
   `kafka-operator` PR #509/#536 moved it into a monorepo). Its section below
   documents work done before the archive. Confirm whether Kafka Connect
   still ships as its own charm revision in this release, and if it now
   builds from the monorepo, fold its entries into the Charmed Apache Kafka
   section and drop its separate heading.
4. Write the introduction. The placeholder below lists the material changes
   found in range; rewrite it as the real product summary, and remove any
   item that does not belong in this release.
5. Confirm entry categorisation for these, which the builder placed by PR
   label and which look questionable:
   - "docs: Fix spread install in GH workflow" (#496) sits under Bug fixes
     because it carries the `bug` label, but it is a CI fix. Move it to
     Improvements unless it really fixed shipped behaviour.
   - "chore: bump to 4.2.0" (#493) sits under Features via the `enhancement`
     label. A workload version bump is arguably the headline change of this
     release — make sure the introduction reflects it.
   Two entries were recategorised during this pass, both on an unambiguous
   conventional-commit prefix: "feat: HA" (kafka-ui #33) moved to Features,
   and "fix: TLS setup failure if chain is missing" (kafka-connect #78) moved
   to Bug fixes. Several other `fix:`-prefixed entries were deliberately LEFT
   under Improvements because they fix tests, CI or release plumbing rather
   than shipped behaviour (#479, #500, #504, #578).
6. Verify these flagged entries and links:
   - "build: bump rust to latest stable" appears in all four components
     (#469, #52, #49, #14). These are genuinely separate changes, not a
     double-count — keep or consolidate as you prefer.
   - "build: remove tag dep" (#67) and "fbuild: remove tag dep" (#68) in
     Kafka Connect are near-duplicates; #68's title has a typo. Keep one if
     they are the same change.
   - "docs: archive repository in favor of canonical/kafka-operator" has no
     PR link — it was committed directly, so only a commit exists.
   - `KAFKA-20572` in #536's title was dropped rather than linked: it is an
     upstream Apache Kafka JIRA ID, not a Canonical one, so the builder's
     `warthogs.atlassian.net` link would have been wrong. Add a link to
     issues.apache.org if you want it referenced.
   - A stray leading `;` was removed from #577's title.
7. Verify all artefacts and links resolve before publishing.
8. Run the repo's docs checks against this page before publishing:
   `cd docs && make spelling` then `cd docs && make linkcheck` (the latter
   takes a few minutes). Fix typos in PR titles in place, wrap bare filenames
   in backticks so MyST doesn't linkify them, and only add genuinely
   uncheckable URLs to `linkcheck_ignore` in `docs/conf.py`.
-->

(reference-release-notes-revision-777)=
# Revision 777

<!-- TODO: Replace this paragraph with the real release summary; see review note 4. -->
This release updates Apache Kafka to 4.3.0 and consolidates the Charmed Apache Kafka components into a single repository. Charmed Apache Kafka gains OpenTelemetry-based tracing and a shared common library, Charmed Kafka UI gains high availability and Canonical Identity Platform integration, and Charmed Karapace and Charmed Apache Kafka Connect receive test and packaging improvements.

[Charmhub](https://charmhub.io/kafka) | [Deploy guide](how-to-deploy-index) | [Upgrade instructions](how-to-upgrade) | [System requirements](reference-requirements)

## Charmed Apache Kafka

The primary charm received the bulk of this release's changes, including the workload bump, tracing support and the move to a monorepo layout.

### Features

- [DPE-8588](https://warthogs.atlassian.net/browse/DPE-8588) - Automated tutorial testing [#487](https://github.com/canonical/kafka-operator/pull/487)
- [DPE-9776](https://warthogs.atlassian.net/browse/DPE-9776) - chore: bump to 4.2.0 [#493](https://github.com/canonical/kafka-operator/pull/493)
- [DPE-9950](https://warthogs.atlassian.net/browse/DPE-9950) - Update docs, libs to use Opentelemetry collector [#501](https://github.com/canonical/kafka-operator/pull/501)
- [DPE-10439](https://warthogs.atlassian.net/browse/DPE-10439) - feat: add common lib [#515](https://github.com/canonical/kafka-operator/pull/515)
- [DPE-9435](https://warthogs.atlassian.net/browse/DPE-9435) - Tracing [#490](https://github.com/canonical/kafka-operator/pull/490)

### Bug fixes

This release includes the following bug fix:

- docs: Fix spread install in GH workflow [#496](https://github.com/canonical/kafka-operator/pull/496)

### Improvements

- chore: Add a pull request template with a checklist [#417](https://github.com/canonical/kafka-operator/pull/417)
- docs: Add autogenerated metadata description [#462](https://github.com/canonical/kafka-operator/pull/462)
- ci: unpin temp. juju & lxd workarounds [#467](https://github.com/canonical/kafka-operator/pull/467)
- build: bump rust to latest stable [#469](https://github.com/canonical/kafka-operator/pull/469)
- docs: Fix 404 error page rendering [#471](https://github.com/canonical/kafka-operator/pull/471)
- docs: v.4 Tutorial fixes after testing [#454](https://github.com/canonical/kafka-operator/pull/454)
- [DPE-9430](https://warthogs.atlassian.net/browse/DPE-9430) - docs: Update cookie banner files (JS+CSS) [#475](https://github.com/canonical/kafka-operator/pull/475)
- [DPE-9434](https://warthogs.atlassian.net/browse/DPE-9434) - Add promote workflow [#477](https://github.com/canonical/kafka-operator/pull/477)
- fix: use full chain in test_certificate_transfer [#479](https://github.com/canonical/kafka-operator/pull/479)
- [DPE-9523](https://warthogs.atlassian.net/browse/DPE-9523) - docs: Update docs to deploy stable risk when possible [#483](https://github.com/canonical/kafka-operator/pull/483)
- [DPE-9434](https://warthogs.atlassian.net/browse/DPE-9434) - Add release trigger [#482](https://github.com/canonical/kafka-operator/pull/482)
- [DPE-9362](https://warthogs.atlassian.net/browse/DPE-9362) - docs: Kafka 4 release notes [#476](https://github.com/canonical/kafka-operator/pull/476)
- [DPE-9764](https://warthogs.atlassian.net/browse/DPE-9764) - Add Terraform guide [#488](https://github.com/canonical/kafka-operator/pull/488)
- docs: Fix tutorial test deployment - add pipx install [#497](https://github.com/canonical/kafka-operator/pull/497)
- docs: Fix tutorial test deployment - again - tox install [#498](https://github.com/canonical/kafka-operator/pull/498)
- deps: Update dependencies [#486](https://github.com/canonical/kafka-operator/pull/486)
- chore: Trigger release from edge [#494](https://github.com/canonical/kafka-operator/pull/494)
- ci: re-enable cached builds [#472](https://github.com/canonical/kafka-operator/pull/472)
- fix: action permissions [#500](https://github.com/canonical/kafka-operator/pull/500)
- docs: Homepage upgrade [#502](https://github.com/canonical/kafka-operator/pull/502)
- [DPE-9934](https://warthogs.atlassian.net/browse/DPE-9934) - cicd: update tics scan [#489](https://github.com/canonical/kafka-operator/pull/489)
- fix: release output name [#504](https://github.com/canonical/kafka-operator/pull/504)
- chore: Cleanup charm-revision parsing and envs [#505](https://github.com/canonical/kafka-operator/pull/505)
- chore: fix CI concurrency [#506](https://github.com/canonical/kafka-operator/pull/506)
- docs: Various fixes for commands syntax and typos [#484](https://github.com/canonical/kafka-operator/pull/484)
- docs: URL migration finalisation [#513](https://github.com/canonical/kafka-operator/pull/513)
- [DPE-10439](https://warthogs.atlassian.net/browse/DPE-10439), [DA-263](https://warthogs.atlassian.net/browse/DA-263) - refactor: monorepo [#509](https://github.com/canonical/kafka-operator/pull/509)
- ci: fix release workflow permissions [#518](https://github.com/canonical/kafka-operator/pull/518)
- docs: Upgrade Sphinx Stack [#522](https://github.com/canonical/kafka-operator/pull/522)
- docs: Experimental reference docs generation [#526](https://github.com/canonical/kafka-operator/pull/526)
- [DPE-9836](https://warthogs.atlassian.net/browse/DPE-9836) - chore: merge 4/monorepo feature branch [#536](https://github.com/canonical/kafka-operator/pull/536)
- docs: Update and review existing references [#538](https://github.com/canonical/kafka-operator/pull/538)
- [Prototype] docs: Experimental AIO [#540](https://github.com/canonical/kafka-operator/pull/540)
- [DPE-9594](https://warthogs.atlassian.net/browse/DPE-9594), [DPE-10984](https://warthogs.atlassian.net/browse/DPE-10984) - docs: update pre-refresh action command, order kraft+broker refreshes [#577](https://github.com/canonical/kafka-operator/pull/577)
- [MISC] Generate coverage XML report [#580](https://github.com/canonical/kafka-operator/pull/580)
- [DPE-10954](https://warthogs.atlassian.net/browse/DPE-10954) - fix: monorepo release [#578](https://github.com/canonical/kafka-operator/pull/578)
- [DPE-10696](https://warthogs.atlassian.net/browse/DPE-10696) - Update release flow [#583](https://github.com/canonical/kafka-operator/pull/583)
- docs: Refactor contacts page and add a contributor's guide [#581](https://github.com/canonical/kafka-operator/pull/581)
- docs: Experimental home page domains of concern [#579](https://github.com/canonical/kafka-operator/pull/579)

## Charmed Apache Kafka Connect

Kafka Connect received a TLS fix and packaging work before its repository was folded into the Charmed Apache Kafka monorepo.

### Bug fixes

This release includes the following bug fix:

- [DPE-10531](https://warthogs.atlassian.net/browse/DPE-10531) - fix: TLS setup failure if chain is missing [#78](https://github.com/canonical/kafka-connect-operator/pull/78)

### Improvements

- build: bump rust to latest stable [#52](https://github.com/canonical/kafka-connect-operator/pull/52)
- chore: Add icon [#53](https://github.com/canonical/kafka-connect-operator/pull/53)
- ci: unpin juju agent & use SH runners [#61](https://github.com/canonical/kafka-connect-operator/pull/61)
- build: add tag to release to 4, use 24.04 base [#49](https://github.com/canonical/kafka-connect-operator/pull/49)
- build: remove tag dep [#67](https://github.com/canonical/kafka-connect-operator/pull/67)
- build: remove tag dep [#68](https://github.com/canonical/kafka-connect-operator/pull/68)
- build: fix channel [#69](https://github.com/canonical/kafka-connect-operator/pull/69)
- [MISC] ci: fix permissions issue [#74](https://github.com/canonical/kafka-connect-operator/pull/74)
- [DPE-9994](https://warthogs.atlassian.net/browse/DPE-9994) - refactor: use jubilant, remove pytest-operator & libjuju dep [#70](https://github.com/canonical/kafka-connect-operator/pull/70)
- docs: archive repository in favor of canonical/kafka-operator

## Charmed Karapace

Karapace received test-framework and packaging improvements in this release.

### Improvements

- build: bump rust to latest stable [#49](https://github.com/canonical/karapace-operator/pull/49)
- chore: Add icons for listing [#51](https://github.com/canonical/karapace-operator/pull/51)
- ci: unpin juju agent & use SH [#57](https://github.com/canonical/karapace-operator/pull/57)
- [DPE-9994](https://warthogs.atlassian.net/browse/DPE-9994) - refactor: use jubilant [#58](https://github.com/canonical/karapace-operator/pull/58)

## Charmed Kafka UI

Kafka UI gained high availability and identity-platform integration.

### Features

- [DPE-10965](https://warthogs.atlassian.net/browse/DPE-10965) - feat: HA [#33](https://github.com/canonical/kafka-ui-operator/pull/33)
- [DPE-10355](https://warthogs.atlassian.net/browse/DPE-10355) - Add identity integration [#30](https://github.com/canonical/kafka-ui-operator/pull/30)

### Improvements

- build: bump rust to latest stable [#14](https://github.com/canonical/kafka-ui-operator/pull/14)
- chore: Add icon [#15](https://github.com/canonical/kafka-ui-operator/pull/15)
- ci: unpin juju agent [#22](https://github.com/canonical/kafka-ui-operator/pull/22)

## Compatibility

Principal charms support the latest LTS series `24.04` only.

| Charm | Revision | Hardware architecture | Juju version | Artefacts |
|---|---|---|---|---|
| Charmed Apache Kafka | TODO | AMD64 | Juju 3.6+ | Distribution: TODO <br> Snap: TODO |
| Charmed Apache Kafka Connect | TODO | AMD64 | Juju 3.6+ | Distribution: TODO <br> Snap: TODO |
| Charmed Karapace | TODO | AMD64 | Juju 3.6+ | Snap: TODO |
| Charmed Kafka UI | TODO | AMD64 | Juju 3.6+ | Snap: TODO |

Apache Kafka release notes: TODO.
