<!--
REVIEW NOTES (for the release owner — remove before publishing)

Scope: Charmed Apache Spark in the widest sense, per the component overview
(https://canonical.com/data/spark/docs/3.5/explanation/component-overview/):
spark8t, Charmed Apache Spark Rock (OCI images), spark-client snap,
Spark Integration Hub (+ its rock), Spark History Server, Charmed Apache Kyuubi,
and the Spark K8s Bundle / Terraform module. External charms consumed by the
product (s3-integrator, azure-storage-integrator, postgresql-k8s,
zookeeper-k8s, self-signed-certificates, data-integrator, traefik-k8s,
grafana-agent-k8s, prometheus-pushgateway-k8s, cos-configuration-k8s,
prometheus-scrape-config-k8s) are maintained by other teams and are NOT
covered here.

Baseline: the last published stable releases — revision 5 (track 3.4),
revision 6 (track 3.5) and revision 7 (track 4.0), all dated July 29th, 2026
(docs/reference/releases on the respective track branches of
canonical/spark-k8s-bundle). From-refs per repo were taken from the revisions
documented in those releases' compatibility tables (verified as ancestors of
the track branches):

  spark-k8s-toolkit-py        v1.4.0 (tag)                     -> main
  charmed-spark-rock          8e1b8640 (3.5) c9a58d10 (4.0) df066837 (3.4)  -> */edge
                              (last PRA-322 artifact-update commits included in rev5/6/7)
  spark-client-snap           rev153 (3.5) rev152 (4.0) rev156 (3.4)        -> */edge
  spark-integration-hub-k8s-operator  rev134                        -> 3/edge
  spark-integration-hub-rock  aa40d850                          -> 3/edge
  spark-history-server-k8s-operator  rev122 (3/edge) rev119 (4/edge)       -> */edge
  kyuubi-k8s-operator         rev183 (3.5) rev180 (3.4) rev181 (4.0)       -> */edge
  spark-k8s-bundle            6212f5a3 (3.5) f00612d4 (3.4) bf400cb6 (4.0) -> track/*
                              (the rev5/6/7 release-notes commits themselves)

To-refs: branch HEADs as of Aug 31, 2026.

TODOs for the release owner:
1. Release designation: the per-track "revision" numbers for this release are
   TBD (previous: 3.4 -> rev5, 3.5 -> rev6, 4.0 -> rev7). Update the title and
   Charmhub channel links once the release is cut.
2. Compatibility: charm/snap revisions listed are the latest *edge* revisions
   (verified from release-workflow logs and the Snap Store API on Aug 31,
   2026). Re-verify at release time; promote to stable numbers as appropriate.
3. Compatibility: exact ghcr image IDs for the Rock and Integration Hub images
   were not re-resolved after the digest bumps — links point at the packages;
   pin specific image IDs at release time.
4. Juju versions (min 3.6.13+ / recommended 3.6.25) are carried over from the
   rev5/6/7 notes; no change was detected in the repos.
5. Upgrade-instructions link: the docs only have a Kyuubi upgrade page; a
   product-wide upgrade page is missing (left as Kyuubi's).

Flagged entries:
- The S3-region docs fix (PRA-165) appears in the Integration Hub, History
  Server and bundle repos (same logical change, different PRs) — kept in each
  component, as each repo shipped it.
- "Update dependency cryptography to v50 [SECURITY]" (Kyuubi) and
  "org.postgresql:postgresql to v42.7.13 [SECURITY]" (Rock) were moved to the
  Security category based on the explicit [SECURITY] tag in the PR title.
- The Kyuubi LDAP entry (PRA-340, "feat:" prefix) was moved to Features.
- The Integration Hub "fix: mount S3 truststore secret..." entry was moved to
  Bug fixes based on the "fix:" prefix.
- False Jira IDs produced by the builder (CVE-2025, CVE-2026, SHA-256, UTF-8,
  SCTE-35, SAY-5 — the latter is a GitHub username) were stripped; only
  PRA-*/DPE-*/KF-* links were kept.
- Duplicate commits from repeated Renovate re-runs (rock PR #262 x3, PR #275
  x2, PR #276 x2) were collapsed to single entries.
- Backports of the same change across the 3.4/3.5/4.0 tracks (CODEOWNERS,
  SECURITY.md, Renovate migration, trivy rework, TIOBE workflow, dependency
  minimum age) are listed once per component with all track PR links.
- spark-integration-hub-k8s-operator 4/edge has no commits after rev126 (the
  4.0 release ships the hub from 3/stable per the rev7 compatibility table),
  so no separate 4.0 hub section exists.
- spark-k8s-bundle main has no commits since Jun 27, 2026; all changes are on
  the track branches.
-->

# Charmed Apache Spark (upcoming stable release — draft)

Aug 31st, 2026

We're happy to announce a draft of the next stable release notes for Charmed
Apache Spark, covering all components of the solution across the 3.4, 3.5 and
4.0 tracks. This release follows the previous stable releases — revision 5
(track 3.4), revision 6 (track 3.5) and revision 7 (track 4.0), published on
July 29th, 2026.

The highlight of this cycle is the new **LDAP authentication support for
Charmed Apache Kyuubi** ([PRA-340](https://warthogs.atlassian.net/browse/PRA-340)),
available on all tracks. The Spark Integration Hub also received a fix for
mounting the S3 truststore secret under `/etc/spark8t/conf` for non-root
workloads, and the `spark8t` Python library was bumped to **1.4.1**.

On the security side, the Charmed Apache Spark OCI images now ship the
PostgreSQL JDBC driver updated to 42.7.13 (security fix), and the Kyuubi charm
updated its `cryptography` dependency to v50. The cycle is otherwise dominated
by maintenance: migration and improvement of the Renovate configuration across
all repositories, a rework of the Trivy scanning workflows, addition of
`SECURITY.md` and `CODEOWNERS` files, a new TIOBE scan workflow, and general
updates of Python/charm dependencies, GitHub actions and base image digests.

Charmhub: [spark-integration-hub-k8s](https://charmhub.io/spark-integration-hub-k8s) | [spark-history-server-k8s](https://charmhub.io/spark-history-server-k8s) | [kyuubi-k8s](https://charmhub.io/kyuubi-k8s) | [spark-client snap](https://snapcraft.io/spark-client) | [Deploy guide](https://canonical.com/data/spark/docs/3.5/how-to/deploy/) | [Upgrade instructions (Kyuubi)](https://canonical.com/data/spark/docs/3.5/how-to/apache-kyuubi/upgrade/) | [System requirements](https://canonical.com/data/spark/docs/3.5/reference/requirements/)

## List of changes

### spark8t (Python library)

#### Other improvements

* [[PRA-353](https://warthogs.atlassian.net/browse/PRA-353)] Add dependency minimum age release ([PR #203](https://github.com/canonical/spark-k8s-toolkit-py/pull/203)) ([f978d39](https://github.com/canonical/spark-k8s-toolkit-py/commit/f978d397c3f6e76815c46f678806f4b260615c45))
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Prettify and improve renovate configuration ([PR #204](https://github.com/canonical/spark-k8s-toolkit-py/pull/204)) ([4193fd7](https://github.com/canonical/spark-k8s-toolkit-py/commit/4193fd7c50fdb445e68936376177ebbf8c03c47a))
* [[PRA-377](https://warthogs.atlassian.net/browse/PRA-377)] Add SECURITY.md ([PR #218](https://github.com/canonical/spark-k8s-toolkit-py/pull/218)) ([277138a](https://github.com/canonical/spark-k8s-toolkit-py/commit/277138a54f60661eb6f2019b6c29187a1c8e9070))
* [[PRA-379](https://warthogs.atlassian.net/browse/PRA-379)] Add tiobe_scan.yaml workflow ([PR #217](https://github.com/canonical/spark-k8s-toolkit-py/pull/217)) ([00580c1](https://github.com/canonical/spark-k8s-toolkit-py/commit/00580c103f2c101182032ea94ba20fa8fcec00a7))
* Bump lightkube to v1 ([PR #219](https://github.com/canonical/spark-k8s-toolkit-py/pull/219)) ([70382cd](https://github.com/canonical/spark-k8s-toolkit-py/commit/70382cd3f14b94550d091f15bed5e7cfb266a1bf))
* Bump version to 1.4.1 ([PR #220](https://github.com/canonical/spark-k8s-toolkit-py/pull/220)) ([947fcd1](https://github.com/canonical/spark-k8s-toolkit-py/commit/947fcd1f7cf3aa62bbdd087889ca597131abc3c9))
* Fix GH release job permission ([PR #221](https://github.com/canonical/spark-k8s-toolkit-py/pull/221)) ([e0533bd](https://github.com/canonical/spark-k8s-toolkit-py/commit/e0533bd49b1b66ec07882248ff9bef388c80f024))
* chore: adding CODEOWNERS file ([PR #202](https://github.com/canonical/spark-k8s-toolkit-py/pull/202)) ([7723576](https://github.com/canonical/spark-k8s-toolkit-py/commit/77235769ca67aa03d061f4997dfa04e057eb76ab))
* Update softprops/action-gh-release action to v3 ([PR #195](https://github.com/canonical/spark-k8s-toolkit-py/pull/195)) ([ee76082](https://github.com/canonical/spark-k8s-toolkit-py/commit/ee7608254fcc936476c32c981a601095a4cfe435))
* Update dependency pyOpenSSL to v26 [SECURITY] ([PR #186](https://github.com/canonical/spark-k8s-toolkit-py/pull/186)) ([a05ff8b](https://github.com/canonical/spark-k8s-toolkit-py/commit/a05ff8b6118bfe438d873e6d0b82039a2fde7f6b)) and to v26.4.0 ([PR #210](https://github.com/canonical/spark-k8s-toolkit-py/pull/210)) ([7705d4f](https://github.com/canonical/spark-k8s-toolkit-py/commit/7705d4f81bf85f2b4c16d1a9bacbb94b45bfa93a))
* Update dependency pytest to v9.0.3 [SECURITY] ([PR #193](https://github.com/canonical/spark-k8s-toolkit-py/pull/193)) ([77ec997](https://github.com/canonical/spark-k8s-toolkit-py/commit/77ec997aba1d860743b142090d677549c6ea3da7))
* General updates of Python dependencies and lock file maintenance ([PR #189](https://github.com/canonical/spark-k8s-toolkit-py/pull/189), [PR #194](https://github.com/canonical/spark-k8s-toolkit-py/pull/194), [PR #199](https://github.com/canonical/spark-k8s-toolkit-py/pull/199), [PR #206](https://github.com/canonical/spark-k8s-toolkit-py/pull/206), [PR #207](https://github.com/canonical/spark-k8s-toolkit-py/pull/207), [PR #209](https://github.com/canonical/spark-k8s-toolkit-py/pull/209), [PR #211](https://github.com/canonical/spark-k8s-toolkit-py/pull/211), [PR #212](https://github.com/canonical/spark-k8s-toolkit-py/pull/212), [PR #213](https://github.com/canonical/spark-k8s-toolkit-py/pull/213), [PR #214](https://github.com/canonical/spark-k8s-toolkit-py/pull/214), [PR #215](https://github.com/canonical/spark-k8s-toolkit-py/pull/215), [PR #216](https://github.com/canonical/spark-k8s-toolkit-py/pull/216), [PR #190](https://github.com/canonical/spark-k8s-toolkit-py/pull/190), [PR #196](https://github.com/canonical/spark-k8s-toolkit-py/pull/196))

### Charmed Apache Spark Rock (OCI images)

#### Security

* Update dependency org.postgresql:postgresql to v42.7.13 [SECURITY] (3.5/edge) ([PR #262](https://github.com/canonical/charmed-spark-rock/pull/262)) ([727424a](https://github.com/canonical/charmed-spark-rock/commit/727424a139552bfa56c67b78692cf3b9daa07ab8))

#### Other improvements

* [[PRA-331](https://warthogs.atlassian.net/browse/PRA-331)] Add .trivyignore ([PR #252](https://github.com/canonical/charmed-spark-rock/pull/252) 3.4/edge, [PR #253](https://github.com/canonical/charmed-spark-rock/pull/253) 3.5/edge, [PR #254](https://github.com/canonical/charmed-spark-rock/pull/254) 4.0/edge)
* [[PRA-355](https://warthogs.atlassian.net/browse/PRA-355)] Rework trivy workflow ([PR #258](https://github.com/canonical/charmed-spark-rock/pull/258) 3.4/edge, [PR #259](https://github.com/canonical/charmed-spark-rock/pull/259) 3.5/edge, [PR #260](https://github.com/canonical/charmed-spark-rock/pull/260) 4.0/edge); fix trivy.yaml permissions ([PR #263](https://github.com/canonical/charmed-spark-rock/pull/263) 3.4/edge)
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Migrate Renovate configuration to the release branches ([PR #267](https://github.com/canonical/charmed-spark-rock/pull/267) 3.4/edge, [PR #261](https://github.com/canonical/charmed-spark-rock/pull/261) 3.5/edge, [PR #265](https://github.com/canonical/charmed-spark-rock/pull/265) 4.0/edge); enable Renovate on 4.0/edge ([PR #264](https://github.com/canonical/charmed-spark-rock/pull/264))
* [[PRA-377](https://warthogs.atlassian.net/browse/PRA-377)] Add SECURITY.md ([PR #275](https://github.com/canonical/charmed-spark-rock/pull/275) 3.4/edge, [PR #276](https://github.com/canonical/charmed-spark-rock/pull/276) 3.5/edge, [PR #277](https://github.com/canonical/charmed-spark-rock/pull/277) 4.0/edge)
* chore: adding CODEOWNERS file ([PR #256](https://github.com/canonical/charmed-spark-rock/pull/256) 3.4/edge, [PR #255](https://github.com/canonical/charmed-spark-rock/pull/255) 3.5/edge, [PR #257](https://github.com/canonical/charmed-spark-rock/pull/257) 4.0/edge)
* Update GitHub actions ([PR #269](https://github.com/canonical/charmed-spark-rock/pull/269) 3.4/edge, [PR #272](https://github.com/canonical/charmed-spark-rock/pull/272) 3.5/edge, [PR #274](https://github.com/canonical/charmed-spark-rock/pull/274) 4.0/edge)
* Pin dependencies ([PR #268](https://github.com/canonical/charmed-spark-rock/pull/268) 3.4/edge, [PR #270](https://github.com/canonical/charmed-spark-rock/pull/270) 3.5/edge, [PR #273](https://github.com/canonical/charmed-spark-rock/pull/273) 4.0/edge)

### spark-client snap

#### Other improvements

* [[PRA-377](https://warthogs.atlassian.net/browse/PRA-377)] Add SECURITY.md ([PR #205](https://github.com/canonical/spark-client-snap/pull/205) 3.4/edge, [PR #204](https://github.com/canonical/spark-client-snap/pull/204) 3.5/edge, [PR #206](https://github.com/canonical/spark-client-snap/pull/206) 4.0/edge)
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Migrate and improve renovate config ([PR #191](https://github.com/canonical/spark-client-snap/pull/191) 3.4/edge, [PR #190](https://github.com/canonical/spark-client-snap/pull/190) 3.5/edge, [PR #192](https://github.com/canonical/spark-client-snap/pull/192) 4.0/edge)
* chore: adding CODEOWNERS file ([PR #187](https://github.com/canonical/spark-client-snap/pull/187) 3.4/edge, [PR #186](https://github.com/canonical/spark-client-snap/pull/186) 3.5/edge, [PR #188](https://github.com/canonical/spark-client-snap/pull/188) 4.0/edge)
* [[DPE-9830](https://warthogs.atlassian.net/browse/DPE-9830)] [[DPE-9769](https://warthogs.atlassian.net/browse/DPE-9769)] Update GitHub actions ([PR #180](https://github.com/canonical/spark-client-snap/pull/180), [PR #200](https://github.com/canonical/spark-client-snap/pull/200) 3.4/edge; [PR #183](https://github.com/canonical/spark-client-snap/pull/183), [PR #202](https://github.com/canonical/spark-client-snap/pull/202) 3.5/edge; [PR #185](https://github.com/canonical/spark-client-snap/pull/185), [PR #203](https://github.com/canonical/spark-client-snap/pull/203) 4.0/edge)
* Update canonical/data-platform-workflows action to v50.2.1 ([PR #194](https://github.com/canonical/spark-client-snap/pull/194) 3.4/edge, [PR #196](https://github.com/canonical/spark-client-snap/pull/196) 3.5/edge, [PR #197](https://github.com/canonical/spark-client-snap/pull/197) 4.0/edge)
* Update Charmed Apache Spark base image digest ([PR #177](https://github.com/canonical/spark-client-snap/pull/177), [PR #193](https://github.com/canonical/spark-client-snap/pull/193), [PR #198](https://github.com/canonical/spark-client-snap/pull/198) 3.4/edge; [PR #181](https://github.com/canonical/spark-client-snap/pull/181), [PR #195](https://github.com/canonical/spark-client-snap/pull/195), [PR #199](https://github.com/canonical/spark-client-snap/pull/199), [PR #201](https://github.com/canonical/spark-client-snap/pull/201) 3.5/edge)
* Remove actions read permissions ([PR #189](https://github.com/canonical/spark-client-snap/pull/189) 4.0/edge) ([236aae2](https://github.com/canonical/spark-client-snap/commit/236aae2a33d0a375f7647267c822bc0ac0301a85))

### Spark Integration Hub

#### Bug fixes

* fix: mount S3 truststore secret under /etc/spark8t/conf (non-root) ([PR #235](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/235)) ([fef6777](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/fef6777d14c93796a64cce6541c1d52d034f6919))

#### Other improvements

* [[PRA-165](https://warthogs.atlassian.net/browse/PRA-165)] Update docs showing correct behavior when S3 region is not configured ([PR #219](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/219)) ([69f36c9](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/69f36c95a9a253a1106a0e9e0949d99a3ed11415))
* Update hub image to version 60d965c ([PR #220](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/220)) ([4fccfd8](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/4fccfd86161adc48ea9f3e9f66e098928e400d64))
* Bump data_models to v1 and pydantic to v2 ([PR #227](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/227)) ([bc10fdf](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/bc10fdf090fa8df7b3a531ba95099997d02f885a))
* [[PRA-353](https://warthogs.atlassian.net/browse/PRA-353)] Add dependency minimum age release ([PR #226](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/226)) ([4dca40a](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/4dca40a07f159e4a2f7f2962be6f6b9e8ec305bf))
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Migrate and improve renovate config ([PR #228](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/228)) ([e1892df](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/e1892df81dbca8e2098c5aae695a0a446cecb757))
* Bump dp workflows to v50.0.0 ([PR #218](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/218)) ([a72433e](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/a72433eb7f4619e21116d9dd8715e9f78d7f1a06))
* chore: adding CODEOWNERS file ([PR #225](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/225)) ([4bb5a34](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/4bb5a34dd6096373890600ec00dbc7f4396fa97f))
* Update actions/checkout action to v7 ([PR #223](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/223)) ([1c7a432](https://github.com/canonical/spark-integration-hub-k8s-operator/commit/1c7a43267f7e61db1c3aa5b4a4d417d894b148b7))
* General updates of Python and charm dependencies, lock file maintenance and dependency pinning ([PR #221](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/221), [PR #222](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/222), [PR #224](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/224), [PR #230](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/230), [PR #231](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/231), [PR #232](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/232), [PR #233](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/233), [PR #234](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/234))

### Spark Integration Hub Rock

#### Other improvements

* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] [[PRA-355](https://warthogs.atlassian.net/browse/PRA-355)] Add trivy and renovate ([PR #36](https://github.com/canonical/spark-integration-hub-rock/pull/36)) ([bf30751](https://github.com/canonical/spark-integration-hub-rock/commit/bf307510787294bc8081b2eb16663dbe8d716e3a))
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Fix release workflow name ([PR #37](https://github.com/canonical/spark-integration-hub-rock/pull/37)) ([5b6ad33](https://github.com/canonical/spark-integration-hub-rock/commit/5b6ad3383c7893b852bbc63fe321fbcbfb5ea0a4))
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Improve renovate config ([PR #38](https://github.com/canonical/spark-integration-hub-rock/pull/38)) ([31517e2](https://github.com/canonical/spark-integration-hub-rock/commit/31517e289f5a8d428e48749933853ee916334e26))

### Spark History Server

#### Other improvements

* [[PRA-165](https://warthogs.atlassian.net/browse/PRA-165)] Update docs showing correct behavior when S3 region is not configured ([PR #187](https://github.com/canonical/spark-history-server-k8s-operator/pull/187) 3/edge) ([0183449](https://github.com/canonical/spark-history-server-k8s-operator/commit/01834494a474b64d7c8592c749c34ac1a2eb601e))
* [[PRA-63](https://warthogs.atlassian.net/browse/PRA-63)] Run integration tests using spread ([PR #199](https://github.com/canonical/spark-history-server-k8s-operator/pull/199) 4/edge) ([4aa8864](https://github.com/canonical/spark-history-server-k8s-operator/commit/4aa8864fcaa5a525de6c4a5a2516dea95e7ba5b0))
* Update Charmed Apache Spark image digest ([PR #188](https://github.com/canonical/spark-history-server-k8s-operator/pull/188) 3/edge) ([7908613](https://github.com/canonical/spark-history-server-k8s-operator/commit/790861392e3ba54f0cc4485c247ef0ccdbfb93f8))
* [[PRA-353](https://warthogs.atlassian.net/browse/PRA-353)] Add dependency minimum release age and update charmlibs ([PR #195](https://github.com/canonical/spark-history-server-k8s-operator/pull/195) 3/edge, [PR #198](https://github.com/canonical/spark-history-server-k8s-operator/pull/198) 4/edge)
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Migrate and improve renovate config ([PR #196](https://github.com/canonical/spark-history-server-k8s-operator/pull/196) 3/edge, [PR #200](https://github.com/canonical/spark-history-server-k8s-operator/pull/200) 4/edge)
* chore: adding CODEOWNERS file ([PR #194](https://github.com/canonical/spark-history-server-k8s-operator/pull/194) 3/edge, [PR #197](https://github.com/canonical/spark-history-server-k8s-operator/pull/197) 4/edge)
* Update GitHub actions (major) ([PR #192](https://github.com/canonical/spark-history-server-k8s-operator/pull/192) 3/edge) ([815a2a8](https://github.com/canonical/spark-history-server-k8s-operator/commit/815a2a838e7022321f420b146d3b34d58bc55094))
* Fix release permissions on track 4 ([PR #201](https://github.com/canonical/spark-history-server-k8s-operator/pull/201) 4/edge) ([81fc03c](https://github.com/canonical/spark-history-server-k8s-operator/commit/81fc03c61c9b48184902f961e67f094fb843c5fc))
* Update workflows ([PR #202](https://github.com/canonical/spark-history-server-k8s-operator/pull/202) 4/edge) ([d2aee5e](https://github.com/canonical/spark-history-server-k8s-operator/commit/d2aee5e04c613ea4e9a33a1e73bf8154699b22ee))
* Fix version release check (4) ([PR #205](https://github.com/canonical/spark-history-server-k8s-operator/pull/205) 4/edge) ([cec86cb](https://github.com/canonical/spark-history-server-k8s-operator/commit/cec86cb60c946f0563f03e334866072e44e4ff38))
* General updates of Python and charm dependencies, lock file maintenance and dependency pinning ([PR #191](https://github.com/canonical/spark-history-server-k8s-operator/pull/191), [PR #193](https://github.com/canonical/spark-history-server-k8s-operator/pull/193), [PR #206](https://github.com/canonical/spark-history-server-k8s-operator/pull/206), [PR #208](https://github.com/canonical/spark-history-server-k8s-operator/pull/208), [PR #209](https://github.com/canonical/spark-history-server-k8s-operator/pull/209), [PR #210](https://github.com/canonical/spark-history-server-k8s-operator/pull/210) 3/edge; [PR #207](https://github.com/canonical/spark-history-server-k8s-operator/pull/207), [PR #211](https://github.com/canonical/spark-history-server-k8s-operator/pull/211), [PR #212](https://github.com/canonical/spark-history-server-k8s-operator/pull/212), [PR #213](https://github.com/canonical/spark-history-server-k8s-operator/pull/213) 4/edge)

### Charmed Apache Kyuubi

#### Features

* [[PRA-340](https://warthogs.atlassian.net/browse/PRA-340)] feat: Support for LDAP authentication Kyuubi charm ([PR #281](https://github.com/canonical/kyuubi-k8s-operator/pull/281) 3.5/edge, [PR #310](https://github.com/canonical/kyuubi-k8s-operator/pull/310) 3.4/edge, [PR #312](https://github.com/canonical/kyuubi-k8s-operator/pull/312) 4.0/edge)

#### Security

* Update dependency cryptography to v50 [SECURITY] ([PR #289](https://github.com/canonical/kyuubi-k8s-operator/pull/289) 3.5/edge, [PR #288](https://github.com/canonical/kyuubi-k8s-operator/pull/288) 3.4/edge)

#### Other improvements

* [[PRA-353](https://warthogs.atlassian.net/browse/PRA-353)] Add dependency minimum release age and update charmlibs ([PR #282](https://github.com/canonical/kyuubi-k8s-operator/pull/282) 3.5/edge, [PR #283](https://github.com/canonical/kyuubi-k8s-operator/pull/283) 3.4/edge, [PR #284](https://github.com/canonical/kyuubi-k8s-operator/pull/284) 4.0/edge)
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Migrate and improve renovate config ([PR #285](https://github.com/canonical/kyuubi-k8s-operator/pull/285) 3.5/edge, [PR #287](https://github.com/canonical/kyuubi-k8s-operator/pull/287) 3.4/edge, [PR #286](https://github.com/canonical/kyuubi-k8s-operator/pull/286) 4.0/edge)
* [[PRA-377](https://warthogs.atlassian.net/browse/PRA-377)] Add SECURITY.md ([PR #317](https://github.com/canonical/kyuubi-k8s-operator/pull/317) 3.5/edge, [PR #316](https://github.com/canonical/kyuubi-k8s-operator/pull/316) 3.4/edge, [PR #318](https://github.com/canonical/kyuubi-k8s-operator/pull/318) 4.0/edge)
* chore: adding CODEOWNERS file ([PR #278](https://github.com/canonical/kyuubi-k8s-operator/pull/278) 3.5/edge, [PR #279](https://github.com/canonical/kyuubi-k8s-operator/pull/279) 3.4/edge, [PR #280](https://github.com/canonical/kyuubi-k8s-operator/pull/280) 4.0/edge)
* Update OCI resources ([PR #263](https://github.com/canonical/kyuubi-k8s-operator/pull/263) 3.5/edge, [PR #256](https://github.com/canonical/kyuubi-k8s-operator/pull/256) 3.4/edge, [PR #270](https://github.com/canonical/kyuubi-k8s-operator/pull/270) 4.0/edge)
* Update charmcraft.yaml build tools ([PR #264](https://github.com/canonical/kyuubi-k8s-operator/pull/264) 3.5/edge, [PR #257](https://github.com/canonical/kyuubi-k8s-operator/pull/257) 3.4/edge, [PR #271](https://github.com/canonical/kyuubi-k8s-operator/pull/271) 4.0/edge)
* Update GitHub actions ([PR #268](https://github.com/canonical/kyuubi-k8s-operator/pull/268) 3.5/edge, [PR #261](https://github.com/canonical/kyuubi-k8s-operator/pull/261) 3.4/edge, [PR #276](https://github.com/canonical/kyuubi-k8s-operator/pull/276), [PR #272](https://github.com/canonical/kyuubi-k8s-operator/pull/272) 4.0/edge)
* Update aws-actions/configure-aws-credentials action to v6.2.2 ([PR #266](https://github.com/canonical/kyuubi-k8s-operator/pull/266) 3.5/edge, [PR #259](https://github.com/canonical/kyuubi-k8s-operator/pull/259) 3.4/edge)
* Update dependency mypy to v2 ([PR #267](https://github.com/canonical/kyuubi-k8s-operator/pull/267) 3.5/edge, [PR #260](https://github.com/canonical/kyuubi-k8s-operator/pull/260) 3.4/edge, [PR #274](https://github.com/canonical/kyuubi-k8s-operator/pull/274) 4.0/edge)
* Update dependency pip to v26 ([PR #275](https://github.com/canonical/kyuubi-k8s-operator/pull/275) 4.0/edge) ([c4379df](https://github.com/canonical/kyuubi-k8s-operator/commit/c4379df77931a041863313c48db104bae86a37b))
* Update dependency lightkube to v1 ([PR #301](https://github.com/canonical/kyuubi-k8s-operator/pull/301) 3.5/edge, [PR #297](https://github.com/canonical/kyuubi-k8s-operator/pull/297) 3.4/edge, [PR #305](https://github.com/canonical/kyuubi-k8s-operator/pull/305) 4.0/edge)
* General updates of Python and charm dependencies, lock file maintenance and dependency pinning ([PR #265](https://github.com/canonical/kyuubi-k8s-operator/pull/265), [PR #269](https://github.com/canonical/kyuubi-k8s-operator/pull/269), [PR #292](https://github.com/canonical/kyuubi-k8s-operator/pull/292), [PR #298](https://github.com/canonical/kyuubi-k8s-operator/pull/298), [PR #299](https://github.com/canonical/kyuubi-k8s-operator/pull/299), [PR #306](https://github.com/canonical/kyuubi-k8s-operator/pull/306) 3.5/edge; [PR #258](https://github.com/canonical/kyuubi-k8s-operator/pull/258), [PR #262](https://github.com/canonical/kyuubi-k8s-operator/pull/262), [PR #294](https://github.com/canonical/kyuubi-k8s-operator/pull/294), [PR #295](https://github.com/canonical/kyuubi-k8s-operator/pull/295) 3.4/edge; [PR #273](https://github.com/canonical/kyuubi-k8s-operator/pull/273), [PR #277](https://github.com/canonical/kyuubi-k8s-operator/pull/277), [PR #293](https://github.com/canonical/kyuubi-k8s-operator/pull/293), [PR #302](https://github.com/canonical/kyuubi-k8s-operator/pull/302), [PR #303](https://github.com/canonical/kyuubi-k8s-operator/pull/303), [PR #307](https://github.com/canonical/kyuubi-k8s-operator/pull/307) 4.0/edge)

### Charmed Apache Spark Terraform Module (spark-k8s-bundle)

#### Other improvements

* [[PRA-353](https://warthogs.atlassian.net/browse/PRA-353)] Add dependency minimum release age ([PR #311](https://github.com/canonical/spark-k8s-bundle/pull/311) track/3.5, [PR #312](https://github.com/canonical/spark-k8s-bundle/pull/312) track/4.0)
* Fix the release section ([PR #315](https://github.com/canonical/spark-k8s-bundle/pull/315) track/3.5, [PR #313](https://github.com/canonical/spark-k8s-bundle/pull/313) track/3.4, [PR #314](https://github.com/canonical/spark-k8s-bundle/pull/314) track/4.0)
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Migrate and improve renovate config ([PR #316](https://github.com/canonical/spark-k8s-bundle/pull/316) track/3.5, [PR #317](https://github.com/canonical/spark-k8s-bundle/pull/317) track/3.4, [PR #318](https://github.com/canonical/spark-k8s-bundle/pull/318) track/4.0)
* [[PRA-354](https://warthogs.atlassian.net/browse/PRA-354)] Regroup python deps PRs in renovate config ([PR #346](https://github.com/canonical/spark-k8s-bundle/pull/346) track/3.5, [PR #349](https://github.com/canonical/spark-k8s-bundle/pull/349) track/3.4, [PR #350](https://github.com/canonical/spark-k8s-bundle/pull/350) track/4.0)
* [[PRA-379](https://warthogs.atlassian.net/browse/PRA-379)] Add tiobe_scan.yaml workflow ([PR #352](https://github.com/canonical/spark-k8s-bundle/pull/352) track/3.5, [PR #353](https://github.com/canonical/spark-k8s-bundle/pull/353) track/3.4, [PR #354](https://github.com/canonical/spark-k8s-bundle/pull/354) track/4.0)

## Compatibility

The following tables summarise the compatibility matrix of the solution.
Charm and snap revisions are the latest **edge** revisions as of Aug 31, 2026
(verified from the release workflow logs and the Snap Store API); they will be
promoted to the stable channels with this release. Minimum Juju version:
v3.6.13+; recommended Juju version: v3.6.25 (unchanged from the previous
release).

### Spark Integration Hub

| Hardware architecture | Channel | Artifact | Revision | Minimum Juju version | Recommended Juju version |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AMD64 | 3/edge | [Integration Hub Image](https://github.com/canonical/spark-integration-hub-rock/pkgs/container/spark-integration-hub) (updated to digest `60d965c`, see [PR #220](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/220)) | 149 | v3.6.13+ | v3.6.25 |
| ARM64 | 3/edge | [Integration Hub Image](https://github.com/canonical/spark-integration-hub-rock/pkgs/container/spark-integration-hub) (updated to digest `60d965c`, see [PR #220](https://github.com/canonical/spark-integration-hub-k8s-operator/pull/220)) | 150 | v3.6.13+ | v3.6.25 |

### Spark History Server

| Hardware architecture | Channel | Artifact | Revision | Minimum Juju version | Recommended Juju version |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AMD64 | 3/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1)) | 137 | v3.6.13+ | v3.6.25 |
| ARM64 | 3/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1)) | 138 | v3.6.13+ | v3.6.25 |
| AMD64 | 4/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2)) | 139 | v3.6.13+ | v3.6.25 |
| ARM64 | 4/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2)) | 140 | v3.6.13+ | v3.6.25 |

### Charmed Apache Kyuubi

| Hardware architecture | Channel | Artifact | Revision | Minimum Juju version | Recommended Juju version |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AMD64 | 3.4/edge | [Charmed Apache Kyuubi Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-kyuubi) (Apache Spark version: [3.4.4-ubuntu10](https://launchpad.net/spark-releases/+milestone/3.4.4-ubuntu10), Apache Kyuubi version: [1.10.3-ubuntu4](https://launchpad.net/kyuubi-releases/1.x/1.10.3-ubuntu4)) | 205 | v3.6.13+ | v3.6.25 |
| ARM64 | 3.4/edge | [Charmed Apache Kyuubi Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-kyuubi) (Apache Spark version: [3.4.4-ubuntu10](https://launchpad.net/spark-releases/+milestone/3.4.4-ubuntu10), Apache Kyuubi version: [1.10.3-ubuntu4](https://launchpad.net/kyuubi-releases/1.x/1.10.3-ubuntu4)) | 204 | v3.6.13+ | v3.6.25 |
| AMD64 | 3.5/edge | [Charmed Apache Kyuubi Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-kyuubi) (Apache Spark version: [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1), Apache Kyuubi version: [1.10.3-ubuntu4](https://launchpad.net/kyuubi-releases/1.x/1.10.3-ubuntu4)) | 210 | v3.6.13+ | v3.6.25 |
| ARM64 | 3.5/edge | [Charmed Apache Kyuubi Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-kyuubi) (Apache Spark version: [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1), Apache Kyuubi version: [1.10.3-ubuntu4](https://launchpad.net/kyuubi-releases/1.x/1.10.3-ubuntu4)) | 211 | v3.6.13+ | v3.6.25 |
| AMD64 | 4.0/edge | [Charmed Apache Kyuubi Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-kyuubi) (Apache Spark version: [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2), Apache Kyuubi version: [1.11.1-ubuntu1](https://launchpad.net/kyuubi-releases/1.x/1.11.1-ubuntu1)) | 212 | v3.6.13+ | v3.6.25 |
| ARM64 | 4.0/edge | [Charmed Apache Kyuubi Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-kyuubi) (Apache Spark version: [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2), Apache Kyuubi version: [1.11.1-ubuntu1](https://launchpad.net/kyuubi-releases/1.x/1.11.1-ubuntu1)) | 213 | v3.6.13+ | v3.6.25 |

### Apache Spark Client snap

| Hardware architecture | Channel | Apache Spark version | Revision |
| :--- | :--- | :--- | :--- |
| AMD64 | 3.4/edge | [3.4.4-ubuntu10](https://launchpad.net/spark-releases/+milestone/3.4.4-ubuntu10) | 199 |
| ARM64 | 3.4/edge | [3.4.4-ubuntu10](https://launchpad.net/spark-releases/+milestone/3.4.4-ubuntu10) | 202 |
| AMD64 | 3.5/edge | [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1) | 203 |
| ARM64 | 3.5/edge | [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1) | 200 |
| AMD64 | 4.0/edge | [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2) | 201 |
| ARM64 | 4.0/edge | [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2) | 204 |

### Charmed Apache Spark Rock (OCI images)

| Hardware architecture | Channel | Artifact |
| :--- | :--- | :--- |
| AMD64, ARM64 | 3.4-22.04/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [3.4.4-ubuntu10](https://launchpad.net/spark-releases/+milestone/3.4.4-ubuntu10)) |
| AMD64, ARM64 | 3.4-22.04/edge | [Charmed Apache Spark GPU Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-gpu) (Apache Spark version: [3.4.4-ubuntu10](https://launchpad.net/spark-releases/+milestone/3.4.4-ubuntu10), NVIDIA Spark RAPIDS version: 26.04.2) |
| AMD64, ARM64 | 3.5-22.04/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1)) |
| AMD64, ARM64 | 3.5-22.04/edge | [Charmed Apache Spark GPU Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-gpu) (Apache Spark version: [3.5.8-ubuntu1](https://launchpad.net/spark-releases/+milestone/3.5.8-ubuntu1), NVIDIA Spark RAPIDS version: 26.04.2) |
| AMD64, ARM64 | 4.0-22.04/edge | [Charmed Apache Spark Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark) (Apache Spark version: [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2)) |
| AMD64, ARM64 | 4.0-22.04/edge | [Charmed Apache Spark GPU Image](https://github.com/canonical/charmed-spark-rock/pkgs/container/charmed-spark-gpu) (Apache Spark version: [4.0.2-ubuntu2](https://launchpad.net/spark-releases/+milestone/4.0.2-ubuntu2), NVIDIA Spark RAPIDS version: 26.04.2) |

### spark8t (Python library)

| Component | Version |
| :--- | :--- |
| spark8t | [1.4.1](https://github.com/canonical/spark-k8s-toolkit-py/releases/tag/v1.4.1) |
