# current-project-state Specification

## Purpose

Keep only the owning project's current compilation and synchronized resolution in
one bounded local state document without accumulating historical generations.

## Requirements

### Requirement: Single current state document
Overspec SHALL store generated compilation, current resolution, and sync metadata
in one ignored openspec/.over/.state.json file. Repeated updates and syncs SHALL
replace current sections without adding generation files. Init/update SHALL preserve
the last synced resolution; sync SHALL preserve frozen compilation. Equivalent
operations SHALL preserve state bytes and modification time.

#### Scenario: Many different syncs
- **WHEN** traits change and sync is repeated
- **THEN** only the current resolution remains in the same single state file

#### Scenario: Compilation refresh
- **WHEN** update refreshes compile-time results
- **THEN** the last synced resolution remains usable until sync replaces it

### Requirement: Validated state publication
The state SHALL validate its format, owning root, section shapes, content hashes,
and sync-to-resolution linkage. Missing, corrupt, redirected, or root-mismatched
state SHALL produce actionable errors. Atomic state replacement SHALL preserve
previous bytes on failure and reject intervening observed input changes. Read-only
resolution, details, and preview SHALL create no state or migration files.

#### Scenario: Concurrent state edit
- **WHEN** state changes between preparation and publication
- **THEN** publication fails instead of overwriting the intervening state

#### Scenario: Invalid current state
- **WHEN** a current file has a wrong root, invalid shape/version, or altered hash
- **THEN** reads fail with recovery guidance and do not consult old generation files

### Requirement: Explicit legacy regeneration
Legacy .state/ generations SHALL NOT serve as fallback storage. Existing legacy
compilation SHALL make normal init refuse before setup writes. Explicit update
then sync SHALL regenerate the single-file state. Documentation SHALL explain
that obsolete generated directories can be removed after successful regeneration.

#### Scenario: Legacy project
- **WHEN** a project has only legacy generated state
- **THEN** reads require update and sync and neither migrate nor load history implicitly
