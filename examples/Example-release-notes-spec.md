# Example release notes

**Revision 552/553 in 14/stable channel**  
Feb 13, 2025

This release of Charmed PostgreSQL upgrades the PostgreSQL version to [14.15](https://www.postgresql.org/docs/release/14.15/) as well as adds [point-in-time-recovery](https://www.postgresql.org/docs/8.1/backup-online.html) (PITR) and [pgAudit](https://www.pgaudit.org/) plugin/extension.

[Charmhub](https://charmhub.io/postgresql) | [Deploy guide](https://canonical.com/data/docs/postgresql/iaas/h-deploy) | [Upgrade instructions](https://canonical.com/data/docs/postgresql/iaas/h-upgrade) | [System requirements](https://canonical.com/data/docs/postgresql/iaas/r-system-requirements)

## Features

* \[[DPE-5561](https://warthogs.atlassian.net/browse/DPE-5561)\] Added timeline management to point-in-time recovery (PITR) ([PR \#629](https://github.com/canonical/postgresql-operator/pull/629))  
* \[[DPE-5248](https://warthogs.atlassian.net/browse/DPE-5248)\] Added pgAudit plugin/extension ([PR \#612](https://github.com/canonical/postgresql-operator/pull/612))  
* Added fully-featured terraform module ([PR \#643](https://github.com/canonical/postgresql-operator/pull/643))  
* \[[DPE-5601](https://warthogs.atlassian.net/browse/DPE-5601)\] Added pgBackRest logrotate configuration ([PR \#645](https://github.com/canonical/postgresql-operator/pull/645))  
* Added \`tls\` and \`tls-ca\` fields to databag (\[[PR \#666](https://github.com/canonical/postgresql-operator/pull/666))


## Breaking changes

* Stopped tracking channel for held snaps ([PR \#638](https://github.com/canonical/postgresql-operator/pull/638))

## Bug fixes

* \[[DPE-6320](https://warthogs.atlassian.net/browse/DPE-6320)\] \[[DPE-6325](https://warthogs.atlassian.net/browse/DPE-6325)\] Juju secrets resetting fix on Juju 3.6 ([PR\#726](https://github.com/canonical/postgresql-operator/pull/726))  
* Fallback to trying to create bucket without LocationConstraint ([PR\#690](https://github.com/canonical/postgresql-operator/pull/690))  
* Added warning logs to Patroni reinitialisation ([PR \#660](https://github.com/canonical/postgresql-operator/pull/660))  
* \[[DPE-5512](https://warthogs.atlassian.net/browse/DPE-5512)\] Fixed some \`postgresql.conf\` parameters for hardening ([PR \#621](https://github.com/canonical/postgresql-operator/pull/621))  
* Fixed lib check ([PR \#627](https://github.com/canonical/postgresql-operator/pull/627))  
* Allow \`--restore-to-time=latest\` without a \`backup-id\` ([PR \#683](https://github.com/canonical/postgresql-operator/pull/683))  
* Clean-up duplicated Patroni config reloads ([PR \#682](https://github.com/canonical/postgresql-operator/pull/682))  
* \[[DPE-5714](https://warthogs.atlassian.net/browse/DPE-5714)\] Filter out degraded read only endpoints ([PR \#679](https://github.com/canonical/postgresql-operator/pull/679))  
* Remove clutter from singlestat panels in COS ([PR \#702](https://github.com/canonical/postgresql-operator/pull/702))  
* \[[DPE-5713](https://warthogs.atlassian.net/browse/DPE-5713)\] Catch wrong parameters exception on bucket create function call ([PR \#701](https://github.com/canonical/postgresql-operator/pull/701))  
* \[[DPE-6377](https://warthogs.atlassian.net/browse/DPE-6377)\] Split topology script ([PR \#729](https://github.com/canonical/postgresql-operator/pull/729))  
* \[[DPE-6171](https://warthogs.atlassian.net/browse/DPE-6171)\] Fix typos in COS alert rules ([PR \#724](https://github.com/canonical/postgresql-operator/pull/724))  
* \[[DPE-6056](https://warthogs.atlassian.net/browse/DPE-6056)\] Add plugins preload libs to regular startup parameters ([PR \#741](https://github.com/canonical/postgresql-operator/pull/741))

## Other improvements

* Upgraded PostgreSQL from v.14.12 → v.14.15 (\[[PR \#730](https://github.com/canonical/postgresql-operator/pull/730))  
* Observability stack (COS) improvements  
  * Polished built-in Grafana dashboard ([PR \#646](https://github.com/canonical/postgresql-operator/pull/646))  
  * \[[DPE-5658](https://warthogs.atlassian.net/browse/DPE-5658)\] Improved COS alert rule descriptions ([PR \#651](https://github.com/canonical/postgresql-operator/pull/651))  
* Several S3 stability improvements ([PR \#642](https://github.com/canonical/postgresql-operator/pull/642))  
* Removed patching of private ops class ([PR \#617](https://github.com/canonical/postgresql-operator/pull/617))  
* Switched charm libs from \`tempo\_k8s\` to \`tempo\_coordinator\_k8s\` and relay tracing traffic through \`grafana-agent\` ([PR \#640](https://github.com/canonical/postgresql-operator/pull/640))  
* Implemented more meaningful group naming for multi-group tests ([PR \#625](https://github.com/canonical/postgresql-operator/pull/625))  
* Ignoring alias error in case alias is already existing ([PR \#637](https://github.com/canonical/postgresql-operator/pull/637))  
* \[[DPE-5387](https://warthogs.atlassian.net/browse/DPE-5387)\] Grant privileges to non-public schemas ([PR \#647](https://github.com/canonical/postgresql-operator/pull/647))  
* Merged \`update\_tls\_flag\` into \`update\_endpoints\` ([PR \#669](https://github.com/canonical/postgresql-operator/pull/669))  
* \[[DPE-6042](https://warthogs.atlassian.net/browse/DPE-6042)\] Made tox commands resilient to white-space paths ([PR \#678](https://github.com/canonical/postgresql-operator/pull/678))  
* \[[DPE-5386](https://warthogs.atlassian.net/browse/DPE-5386)\] Added microceph (local backup) integration test \+ bump snap version ([PR \#633](https://github.com/canonical/postgresql-operator/pull/633))  
* \[[DPE-5533](https://warthogs.atlassian.net/browse/DPE-5533)\] Add \`max\_locks\_per\_transaction\` config option in ([PR\#718](https://github.com/canonical/postgresql-operator/pull/718))  
* \[[DPE-5181](https://warthogs.atlassian.net/browse/DPE-5181)\] Split PITR backup test in AWS and GCP ([PR \#605](https://github.com/canonical/postgresql-operator/pull/605))

## Compatibility

| Charm  revision | Hardware architecture | PostgreSQL version | Minimum  Juju version	 | Recommended  Juju version | Snap |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **552** | **ARM64** | **[v14.15](https://www.postgresql.org/docs/release/14.15/)** | **v.3.4.3+** | **v.3.6.1** | **[rev.142](https://github.com/canonical/charmed-postgresql-snap/releases/tag/rev143)** |
| **553**  | **AMD64** | **[v14.15](https://www.postgresql.org/docs/release/14.15/)** | **v.3.4.3+** | **v.3.6.1** | **[rev.143](https://github.com/canonical/charmed-postgresql-snap/releases/tag/rev143)** |

