## Context

See proposal.md for motivation and scope. Current inventory is assembled by
`Project.inventory`, `profiles.select_profile`/`trait_files`, and the two-layer
`trait_system.sources.compose`. User-level standalone traits are not currently
loaded. The remote implementation in `core/remotes.py` retrieves one GitHub
subdirectory through zuu case12 and maintains its own revisions. This proposal
adds a separate discovery boundary; it does not silently replace that backend.

Current Saucepan exposes Python `Saucepan.view`, `verify`, `history`, and `path`
over an independent executable. `AppView.entries` is a map of touched artifacts,
not a list of currently selected repositories. Artifacts carry source identity,
snapshot, revision, folder and content manifest. `history` exposes current source
selection, and `path` returns the public usable content path. `verify` requires a
caller token; merely passing `app="overspec"` is insufficient for verification.
Observed in the sibling checkout through CodeGraph and the public documentation:

- [Central source store](https://github.com/ZackaryW/saucepan/blob/main/docs/central-source-store.md)
- [Python SDK](https://github.com/ZackaryW/saucepan/tree/main/sdk/python)

Memory `f832923` establishes current-only project state and explicit partial sync
failure. `07ada6d` records the need to check complete merged requirements. The
older version-1 compatibility note in `49d9e91` is superseded by current specs.

## Goals / Non-Goals

**Goals:** A reusable acquisition adapter, deterministic layered discovery,
explainable overrides, and no hidden acquisition during composition.

**Non-Goals:** Installing or initializing Saucepan, new acquisition commands,
changing the profile-mode command surface, replacing profile pull/update,
materializing user profile copies, migrating legacy remote storage, importing
variable files or skills from acquired repositories, changing predicate semantics,
or undertaking the deferred utilities-governance refactor.

## Decisions

### 1. Explicit connection with automatic discovery inside the scope

Proposed user configuration in the existing chosen home `config.toml`:

```toml
[sources.saucepan]
marker = ".saucepanhash"
order = []
```

Presence of the table enables the connection independently of profile activation.
The marker is the token returned by registering the `overspec` app, stored at the
given path relative to the chosen user home, or at an explicit absolute path.
The marker path must be a regular nonredirected file. Do not copy its contents
into diagnostics, project state, or Git. Require the returned view app to be
`overspec`. An optional `binary` path can select an installed executable; otherwise
use the SDK default. Reject unknown configuration fields, invalid order entries,
or an incomplete connection. No table means no Saucepan dependency is needed at
runtime. Once configured, errors are not treated as an empty inventory.

Use the current Python SDK behind a small injectable adapter. Add it as an optional
installation extra, locked to a verified current-API release or immutable source
revision. Keep SDK imports lazy for unconfigured installations. Reuse zuu case5
for confined reads and case2 for consumed-file observations. The SDK already
handles process execution; do not duplicate that machinery with new utilities.

### 2. One eligible current root per source

Read and verify one view; group its entries by source identity. For each source,
read public source state and select the artifact with `folder=None` and the
current snapshot ID, only if that artifact is in the view. Resolve its path using
the public API and validate its content against the artifact manifest before use.
No directory crawling under `~/.saucepan` is allowed. A historical artifact or
folder-only acquisition is reported as excluded with whole-current-root acquisition
guidance. Do not ascend from an artifact folder to recover a repository root.

This choice avoids arbitrary history merging. It deliberately does not support
pin selection yet: a pin is eligible only when it is also the source's current
whole-root artifact. If another app advances shared current content, Overspec
must not import that unseen snapshot; it reports the source excluded until the
current root is acquired within its own scope. Include this limitation in help.
Remote Git and local directory repositories can use the same discovery layouts.

`view`/`verify` and `history` are distinct observations. Recheck both the scoped
view and the selected source states before publishing; a view verification alone
does not establish that the shared current pointer stayed unchanged.

### 3. Independent category selection and deferred profile parsing

For each eligible root, inspect the existence/type of `over-traits` and
`over-profiles` independently. Select the corresponding fallback only on absence.
Reuse recursive trait scanning inside the selected standalone root; exclude
profile subtrees, `.state`, and `.git`. Within the selected profile container,
enumerate only immediate `profile-*` directories. Enumerate candidate names and
origins without reading every profile's trait files; parse only the winning
selected profile. An empty top-level category wins over a populated fallback.
Invalid selected paths fail without trying another layout.

The actual project and user authored sources keep their existing locations;
the two-layout rule applies to acquired repository roots. User standalone traits
are newly scanned recursively below the chosen home, excluding profile and
internal-state subtrees. The existing repository's `openspec/.over/profile-default`
therefore works as an external default without relocating authored files.

### 4. Explicit priority and complete replacement

The optional `order` list contains canonical Saucepan source IDs from low to high
priority. Unlisted sources come first, sorted lexicographically by source ID.
Absent IDs remain inactive settings entries; they do not select out-of-scope
content. Reject duplicates. This includes every eligible acquired source while
avoiding changing precedence when a repository is merely refreshed.

For profile candidates, ordered external sources are below existing user sources
and then project sources. Same-name external profiles replace as whole directories.
The existing authored-user/legacy-remote collision diagnostic remains unchanged
inside the preexisting user tier. Do not let that old backend consume or modify
Saucepan-owned content. Profile listing includes external origins and winners.

Composition uses named layers: selected profile, each external standalone source,
user standalone, project standalone. Reject duplicate names inside each layer;
replace whole declarations across layers, preserving initial insertion positions
before stable phase ordering. Parse declaration shape in contributing layers,
then validate cross-trait references on the final effective inventory. Retain
overridden records for explanation. Profile-independent names stay unchanged.

Explicit priority and discovery-first scope are proposed defaults in this plan;
the user was offered alternatives during preparation. They are not described as
separately confirmed decisions. No implementation proceeds merely because these
planning artifacts exist.

### 5. Separate compatibility from acquisition provenance

Inventory should return effective declarations, layered origins, selected profile
identity, base variables, and captured external evidence. Use stable source-ID plus
repository-relative origins for compatibility; an absolute cache path containing a
new snapshot ID must not force recompilation when only ordinary/runtime content
changed. Include effective compile-time declarations, the selected profile identity,
and used project inputs in the compilation signature. Keep snapshot/revision data
in explanation and saved provenance, outside unrelated compatibility inputs.

Record no connection tokens in resolution snapshots. Existing runtime/details
reads consume saved declarations and provenance without calling Saucepan. Preserve
the current-state schema/lifetimes unless an actual representation change requires
a deliberate version change; no compatibility reader is added here.

Capture selected roots, category absence/presence, files, source current pointers,
view identity, priority and connection configuration. Recheck before compilation or
config publication, and retain existing rechecks before state publication. No-op
sync preserves bytes/mtime. A failure after config replacement still reports the
existing partial outcome; this is not a cross-process transaction with Saucepan.

## Risks / Trade-offs

- Shared current source selection can move outside Overspec -> intersect current
  roots with the app view, report excluded sources, and recheck before publication.
- Default source-ID order is stable but not meaningful to humans -> expose origins
  and configurable order; never imply acquisition recency is a priority contract.
- Global standalone traits apply to every connected project -> show effective
  layers and retain project-local complete overrides and trait assertions.
- Reading a changing external store adds work -> capture one view per inventory,
  reuse it within preparation, and make only required consistency rechecks. Do not
  claim measured performance improvements or persist another generation cache.
- SDK installation does not install the executable or credential store -> document
  the explicit prerequisite and fail clearly for connected homes.
- Two retrieval systems coexist temporarily -> label this as discovery-first and
  keep subsequent pull/update redesign separate and explicit.

## Migration Plan

Existing homes without a Saucepan connection continue unchanged. In an isolated
test store, register `overspec`, acquire whole repositories, configure the test
connection, and validate discovery before documenting production setup. Never
initialize, register, change filters, or acquire against the user's real store
during automated tests. Existing user/profile directories are neither copied nor
deleted. Projects need explicit update when effective compilation changes, then
sync to capture new declarations. Removing the connection restores existing
inventory behavior; existing saved commands remain usable until replaced.

Implement each behavioral slice with observed failing tests, minimal implementation,
then green/refactoring. Keep one action/assertion per file and existing base
contracts; this work adds no predicate types. Validate specs, examples, SDK/public
CLI integration, current-state/no-op behavior, and the full existing suite before
requesting an archive outcome. Implementation commits follow the established zmem
workflow and exclude this active change's artifacts.
