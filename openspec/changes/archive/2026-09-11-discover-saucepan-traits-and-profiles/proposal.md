## Why

Reusable traits and profiles should be discoverable from repositories acquired for
Overspec, without individually copying profiles or teaching Overspec each source
provider. Saucepan already supplies a scoped artifact catalog and resolved content
paths; Overspec needs a deterministic composition contract above that boundary.

## What Changes

- Connect a user home to Saucepan's `overspec` app scope and discover every eligible
  acquired repository root through its public API, without fetching during loading.
- Discover standalone traits from `over-traits/` first, falling back to
  `openspec/.over/` only when the top-level directory is absent. Discover profiles
  independently from `over-profiles/`, otherwise `openspec/.over/profile-*`.
  Empty top-level directories intentionally contribute nothing; invalid paths or
  content produce errors rather than fallback.
- Make external standalone traits participate in both profile modes and expose
  discovered named profiles to the existing selection mechanism. Only the selected
  profile contributes declarations.
- **BREAKING**: Extend composition into ordered source layers: same-name traits
  across layers replace complete earlier declarations. Preserve duplicate errors
  within one source layer and retain winner/overridden provenance.
- Proposed priority: selected profile, ordered external standalone sources,
  user-authored standalone traits, then project-local traits. Profile sources use
  ordered external candidates below user and project profiles. Record explicit
  source priority with a deterministic fallback for unlisted sources.
- Preserve frozen compilation, current-only saved resolutions, live variable scope,
  offline reads, and publication rechecks when external inventories change.

## Capabilities

### New Capabilities

- `saucepan-source-discovery`: Scoped repository roots, independent top-level-first
  discovery, stable source ordering, provenance, and read-only integration failures.

### Modified Capabilities

- `trait-composition`: External and user standalone layers, external profile
  candidates, complete same-name replacement, and preserved profile mode semantics.

## Impact

Project inventory/evidence, profile discovery/listing/selection, trait composition,
tests, README, bootstrap and trait-authoring references. Add an adapter to the
current Saucepan Python SDK and its independently installed executable. Retain zuu
for confinement, observations and other applicable existing contracts.

This is a discovery-first proposal. It does not install Saucepan, acquire sources
implicitly, mirror acquired repositories into `~/.overspec/profile-*`, redesign
existing profile pull/update commands, or remove the existing remote backend.
Those acquisition/layout changes require a subsequent contract. Existing local
profiles remain ordinary user/project directories. No implementation or archive
operation is part of preparing these artifacts.
