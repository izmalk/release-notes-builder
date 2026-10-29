---
myst:
  html_meta:
    description: Release notes for LXD 6.10.1, including bugfixes.
---

<!-- Release-notes review notes (not published). Remove before publishing.
     Product: LXD (canonical/lxd), LTS track 6, release 6.10.1 (first point
     release of the 6.10 LTS). Regenerated on 2026-10-29 at the user's request
     (they explicitly chose to regenerate the already-published 6.10.1 notes
     rather than draft the next release; the revision guard was surfaced and
     overridden). Published document being updated:
     doc/reference/release-notes/6/release-notes-6.10.1.md in canonical/lxd
     (GitHub release lxd-6.10.1, published 2026-10-28).

     Range: lxd-6.10.0...lxd-6.10.1 on the stable-6 branch (compare API:
     37 commits, not truncated). Deduplicated to 11 distinct PRs (26 duplicate
     entries removed: LXD backport PRs contain the cherry-picked main commits,
     so each change appears once as the original commit message and once as
     the squash merge bearing the PR number; entries cite the stable-6 backport
     PR, consistent with the published notes' links).

     Raw builder categories: all 37 entries landed in "Other improvements"
     (LXD repos carry no DA186 labels; PR titles are Go-style prefixes like
     "lxd/auth/oidc:", not conventional commits). Auto-sort was enabled by the
     user; effective moves (recorded per move):
       PR #19303 "snap/lvm: Store metadata archives and backups under SNAP_COMMON" — Other improvements -> Bug fixes (snap bug fix; also listed by published notes)
       PR #19308 "Network: OVN BGP regression and other fixes" — Other improvements -> Bug fixes (fixes regressions #19290, #19292)
       PR #19332 "snap: Cherry-pick LXCFS suspension enablement fix" — Other improvements -> Bug fixes (snap bug fix; also listed by published notes)
       PR #19340 "lxd/instance/drivers/qmp: remove limit on QMP response size" — Other improvements -> Bug fixes (also listed by published notes)
       PR #19358 "lxd/auth/oidc: Use ID token claims in callback" — Other improvements -> Bug fixes (fixes AD FS OIDC login; also listed by published notes)
       PR #19286 "auth: Allow all authenticated callers to view builtin image registries" — Other improvements -> Bug fixes (FLAGGED, judgement call: corrects the 6.10.0 image-registry authorization; treats restricted callers' inability to view built-in registries as a user-visible defect)
       PR #19259 "Specify stable-6 as source branch for lxd-ui" — Other improvements -> Snap packaging changes (packaging change, not a bug fix)

     Entries reviewed but deliberately NOT surfaced in visible sections,
     following LXD's own curation convention (the section list is curated and
     the "Change log" compare link is the completeness mechanism); each is
     present in the lxd-6.10.0...lxd-6.10.1 compare:
       PR #19257 "shared/version: Set IsLTSVersion to true" (release plumbing)
       PR #19261 "github: Fix branch target rule for stable-6" (CI-only,
         infrastructure fix — auto-sort rule: never moved to Bug fixes)
       PR #19360 "doc/reference/release-notes: Add release notes for 6.10.1"
         (documentation; no docs exclusion was requested — this is structural
         curation, not filtering)
       PR #19373 "Release LXD 6.10.1" (release commit)

     UI updates section (included at the user's request): drafted from
     canonical/lxd-ui changes 0.23...0.23.1 (the UI version shipping in the
     6.10.1 snap: snapcraft.yaml at lxd-6.10.1 builds lxd-ui from the stable-6
     branch, which is the 0.23.1 tag). Nuance to verify: the 6.10.0 snap built
     the UI from an unpinned main-HEAD snapshot whose build date (2026-10-19,
     release day) already contained part of the 0.23.1 change set, so some of
     these updates may already have been present in the 6.10.0 snap; the LXD
     team's own 6.10.1 Discourse announcement does present them as 6.10.1 UI
     updates. Underlying lxd-ui PRs: #2268, #2348/#2353, #2365, #2367, #2371,
     #2374, #2375 (docs), #2376, #2377, #2382, #2383, #2384 (test/CI), #2385,
     #2386, #2397, #2401, #2422/#2469 style dependency updates; compare link:
     https://github.com/canonical/lxd-ui/compare/0.23...0.23.1

     Compatibility facts: minimum Go version unchanged at 1.27.1 (go.mod at
     both lxd-6.10.0 and lxd-6.10.1); the 6.10.0 known issues (CDI GPU
     passthrough failure on Ubuntu Core 26; Ceph userspace tooling
     incompatibility) were not addressed in this range and so plausibly
     persist, but the published 6.10.1 notes carry no known-issues section.

     TODO for the release owner:
     - Verify that the two bug fixes NEW to this regenerated list (PR #19286
       image-registry authorization and PR #19308 OVN BGP regression fixes)
       are intended for the public 6.10.1 list; the published notes list only
       four bug fixes (PRs #19303, #19332, #19340, #19358).
     - Confirm the UI updates section framing against the Discourse
       announcement (https://discourse.ubuntu.com/t/lxd-6-10-1-lts-has-been-released/90024),
       including whether changes already present in the 6.10.0 snap build
       should be re-announced here.
     - Decide whether to carry over the 6.10.0 known issues (CDI GPU
       passthrough on Ubuntu Core 26, Ceph userspace tooling incompatibility)
       as they remain unfixed in this range.
     - To publish in canonical/lxd, replace
       doc/reference/release-notes/6/release-notes-6.10.1.md with this
       document (removing this comment block first) and confirm the 6/ toctree
       entry is unchanged.
-->

(ref-release-notes-6.10.1)=
# LXD 6.10.1 release notes

This is a {ref}`LTS release <ref-releases-lts>` and is recommended for production use.

```{admonition} Release notes content
:class: note
These release notes cover updates in the [core LXD repository](https://github.com/canonical/lxd) and the [LXD snap package](https://snapcraft.io/lxd).
For a tour of [LXD UI](https://github.com/canonical/lxd-ui) updates, please see the release announcement in [our Discourse forum](https://discourse.ubuntu.com/t/lxd-6-10-1-lts-has-been-released/90024).
```

This is a maintenance release for the 6 LTS series.
It includes several bug fixes backported from the main development branch.
The snap now also builds the bundled [LXD UI](https://github.com/canonical/lxd-ui) from its own stable branch instead of an unpinned development snapshot, shipping LXD UI version 0.23.1.

(ref-release-notes-6.10.1-ui)=
## UI updates

The snap ships LXD UI 0.23.1, which includes the following updates.

### Image handling fixes in the UI

Images now show the correct architecture names (for example, `arm64` instead of `aarch64`), are listed in a consistent order, and instance creation works from image aliases after merging VM and instance images.

### Image registries in the image selector

The image selector now surfaces image registries, complementing the image registries feature introduced in LXD 6.10.0.

### Ceph replicator configuration in the UI

Support was added for configuring replicators on Ceph storage pools from the UI.

### Instance copy improvements in the UI

Copied instances now show their setup status during the copy, and they are linked from the operations page.

### Load balancer fixes in the UI

Load balancer pool statuses now reflect the health of their targets, and notifications no longer display wildcard IP addresses.

### Other UI fixes

The OIDC sign-in flow and its icons were fixed, the show/hide password button in settings no longer submits the form, the spacing of placement group rows was corrected, and the UI icons were migrated to a maintained icon set.

View the [complete list of UI changes in LXD UI 0.23.1](https://github.com/canonical/lxd-ui/compare/0.23...0.23.1).

(ref-release-notes-6.10.1-bugfixes)=
## Bug fixes

The following bug fixes are included in this release.

- [{spellexception}`auth: Allow all authenticated callers to view builtin image registries`](https://github.com/canonical/lxd/pull/19286)
- [{spellexception}`snap/lvm: Store metadata archives and backups under SNAP_COMMON`](https://github.com/canonical/lxd/pull/19303)
- [{spellexception}`Network: OVN BGP regression and other fixes`](https://github.com/canonical/lxd/pull/19308)
- [{spellexception}`snap: Cherry-pick LXCFS suspension enablement fix`](https://github.com/canonical/lxd/pull/19332)
- [{spellexception}`lxd/instance/drivers/qmp: remove limit on QMP response size`](https://github.com/canonical/lxd/pull/19340)
- [{spellexception}`lxd/auth/oidc: Use ID token claims in callback`](https://github.com/canonical/lxd/pull/19358)

(ref-release-notes-6.10.1-snap)=
## Snap packaging changes

The snap packaging includes the following change in this release.

- The LXD snap now builds the bundled LXD UI from the pinned `stable-6` branch of the LXD UI repository instead of the default development branch, so LTS snaps ship a stable, pinned UI version ([PR #19259](https://github.com/canonical/lxd/pull/19259)).

(ref-release-notes-6.10.1-changelog)=
## Change log

View the [complete list of all changes in this release](https://github.com/canonical/lxd/compare/lxd-6.10.0...lxd-6.10.1).

(ref-release-notes-6.10.1-downloads)=
## Downloads

The source tarballs and binary clients can be found on our [download page](https://github.com/canonical/lxd/releases/tag/lxd-6.10.1).

Binary packages are also available for:

- **Linux:** `snap install lxd --channel=6/stable`
- **macOS client:** `brew install lxc`
- **Windows client:** `choco install lxc`
