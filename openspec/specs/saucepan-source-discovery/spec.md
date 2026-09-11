# saucepan-source-discovery Specification

## Purpose

Discover reusable traits and named profiles from repositories visible to Saucepan's
Overspec scope while preserving predictable precedence, provenance, and offline use.

## Requirements

### Requirement: Scoped acquired repository inventory

A connected Overspec user home SHALL discover repository content exclusively from
the authenticated Saucepan app view whose app identity is `overspec`. It SHALL
honor that view's filters and touched entries rather than scanning Saucepan's
storage directories or another app's catalog. Every eligible repository root in
the view SHALL be considered without a repository-specific source manifest.
Discovery SHALL use public artifact paths and source metadata, not infer a root
by ascending from an acquired subdirectory.

For each source identity, automatic discovery SHALL select only a whole-root
artifact for the source's current snapshot that is itself visible in the app view.
Historical artifacts and folder-only artifacts SHALL not contribute duplicate or
partial repositories. An in-scope source lacking an eligible current root SHALL
be reported as excluded with guidance to acquire its whole current root under
the Overspec scope. Global current content invisible to that scope SHALL not be
imported implicitly. Missing eligible content or invalid scope/proof SHALL fail
before publishing changed project guidance.

#### Scenario: Another application's repository
- **WHEN** a repository is cached solely for another Saucepan app
- **THEN** Overspec does not discover its traits or profiles

#### Scenario: Current and historical artifacts
- **WHEN** a scoped source has visible whole-root artifacts for current and older snapshots
- **THEN** only the current snapshot contributes and the source is scanned once

#### Scenario: Folder acquisition or invisible current root
- **WHEN** the scoped source has only a folder artifact or no visible artifact for its current root
- **THEN** the source contributes nothing, its exclusion is explained, and discovery neither escapes the folder nor borrows another app's artifact

### Requirement: Independent top-level-first locations

For each eligible repository, standalone trait discovery SHALL select `over-traits/`
when it exists, otherwise `openspec/.over/`. Profile discovery SHALL independently
select `over-profiles/` when it exists, otherwise `openspec/.over/`. Only an absent
top-level directory SHALL enable its fallback. An existing empty directory SHALL
contribute no content in its category; a non-directory, redirected path, unreadable
directory, or malformed selected declaration SHALL fail instead of using fallback.
If neither location exists, that category SHALL contribute nothing.

Standalone discovery SHALL recursively include regular `trait*.toml` files within
its selected root, excluding profile subtrees and generated-state directories.
Profile discovery SHALL enumerate immediate `profile-<nonempty-name>` directories
within its selected root. Only the effective selected profile's declarations SHALL
be loaded, using recursive `trait*.toml` discovery. Paths SHALL remain confined to
their inspected source root and no physical file SHALL be scanned twice within
one discovery layer. Unselected fallback locations SHALL not be inspected for
declarations or merged into the selected category.

#### Scenario: Both layouts exist
- **WHEN** a repository has over-traits and over-profiles as well as openspec/.over
- **THEN** both categories use their top-level directories and ignore their fallback content

#### Scenario: Independent fallback
- **WHEN** over-traits exists but over-profiles is absent
- **THEN** standalone traits come from over-traits and profiles come from openspec/.over/profile-*

#### Scenario: Intentional empty top-level category
- **WHEN** over-traits is empty and fallback trait files exist
- **THEN** no standalone traits are loaded from that repository

#### Scenario: Invalid top-level path
- **WHEN** over-profiles is a file or redirected directory
- **THEN** discovery reports the invalid path rather than loading fallback profiles

#### Scenario: Fallback profile isolation
- **WHEN** fallback openspec/.over contains loose traits and multiple profiles
- **THEN** loose traits form the standalone layer and inactive profiles never leak into it

### Requirement: Stable external source priority

The chosen Overspec user home SHALL support an optional ordered list of Saucepan
source identities. All eligible unlisted sources SHALL be processed first in
ascending canonical source-identity order, followed by listed sources in their
configured order; later sources SHALL have higher priority. Listing SHALL not be
required to include a source. Priority SHALL not depend on filesystem enumeration,
view map order, modification times, artifact hashes, or cache refresh times.
Malformed or duplicate priority entries SHALL fail with a settings diagnostic.
Well-formed identities absent from the current view SHALL remain configured but
inactive and SHALL be reported without importing them outside scope.

#### Scenario: Cross-repository name collision
- **WHEN** two eligible repositories define the same standalone trait name
- **THEN** the later source replaces the earlier declaration completely and both origins remain explainable

#### Scenario: Equivalent inventory order changes
- **WHEN** Saucepan returns the same entries in a different serialization order
- **THEN** effective traits and profile winners remain unchanged

#### Scenario: Explicit priority and filtered source
- **WHEN** a listed source is filtered out while unlisted sources remain eligible
- **THEN** all eligible sources still contribute in stable order and the filtered source's priority record does not bypass the filter

### Requirement: External profile catalog and standalone layers

Every discovered external profile SHALL be available as a candidate under its
profile name. Same-name profiles across external repositories SHALL use source
priority to select one whole profile, without merging profile directories.
Existing user-level profiles SHALL override external candidates, and project
profiles SHALL override both. Unselected profile contents SHALL not be evaluated
or parsed merely because a repository was discovered.

Standalone traits SHALL contribute independently of profile mode. Trait layers
SHALL be applied from lowest to highest priority: effective selected profile,
external standalone sources in source order, user-authored standalone traits,
then project-local standalone traits. Duplicate names within one selected profile,
one repository's standalone layer, or one authored layer SHALL remain errors;
cross-layer collisions SHALL replace the complete declaration before references
are validated and evaluation begins.

#### Scenario: Default without local profile files
- **WHEN** mode is off and only a scoped external repository provides profile-default
- **THEN** its default profile and applicable standalone layers contribute without creating a user or project profile copy

#### Scenario: Local profile overrides external default
- **WHEN** a project profile-default exists alongside external default candidates
- **THEN** the project profile replaces them as the selected profile while external standalone traits still participate

#### Scenario: Inactive malformed profile
- **WHEN** a discovered non-default profile has malformed traits and mode is off
- **THEN** its declarations are not loaded and ordinary default composition remains available

#### Scenario: Same source duplicate
- **WHEN** two files within one external standalone layer declare the same trait name
- **THEN** loading fails with both origins rather than choosing a file accidentally

### Requirement: Source provenance and project lifetimes

Explanations SHALL identify source identity, snapshot/revision, repository-relative
path, selected discovery location, and overwrite winners and losers. Emitted trait
names SHALL remain profile-independent and source-independent. Existing compilation
and runtime lifetimes SHALL apply to external declarations: changed effective
compile-time declarations or profile selection SHALL require update; changes only
to ordinary/runtime declarations SHALL become available at the next sync without
refreshing unchanged compilation. Unrelated acquired content SHALL not by itself
invalidate compilation.

Saved runtime commands and literal detail lookup SHALL use the current synchronized
resolution without requiring a live Saucepan connection, rereading external sources,
or acquiring content. Superseded resolution IDs SHALL continue to fail. External
repository variable files SHALL not become variable layers of the consuming project.

#### Scenario: External runtime refresh
- **WHEN** a source refresh changes only runtime declarations
- **THEN** existing commands use saved declarations until sync, and sync adopts the new declarations without requiring an unrelated compilation refresh

#### Scenario: External compile-time refresh
- **WHEN** a source refresh changes an effective compile-time declaration
- **THEN** sync requires update instead of silently recompiling

#### Scenario: Saved details when Saucepan is unavailable
- **WHEN** Saucepan is unavailable after successful synchronization
- **THEN** current resolution runtime evaluation and literal details remain usable with their existing variable-file rules

### Requirement: Read-only connection and consistent publication

Connecting a user home SHALL be independent of the profile-mode toggle. With no
connection configured, existing local and legacy remote behavior SHALL remain
available without requiring Saucepan. Once connected, unavailable dependencies,
invalid scope credentials, unsupported response formats, malformed source data,
or missing consumed artifacts SHALL be explicit failures rather than an empty
successful inventory. An authenticated empty view SHALL be a valid empty inventory.

Discovery SHALL not initialize/register Saucepan, acquire or refresh sources,
mirror files, install skills, change app filters, or persist selection while
loading. Source/view/config changes detected between preparation and publication
SHALL reject inconsistent compilation or sync publication. No-op sync SHALL retain
the existing byte/mtime guarantees. Existing config-first/state-second partial
failure diagnostics SHALL remain truthful.

#### Scenario: Connected versus unconfigured home
- **WHEN** an unconfigured user home is used on a machine without Saucepan
- **THEN** local-only operations remain available; configuring an unavailable Saucepan connection instead produces an actionable error

#### Scenario: Scoped view changes during sync
- **WHEN** acquired entries, filters, current source selection, or source priority change after preparation and before publication
- **THEN** the relevant publication is rejected with retry guidance and does not claim to have committed a consistent new result

#### Scenario: Preview is not acquisition
- **WHEN** trait explanation or sync preview discovers external content
- **THEN** it reads the scoped catalog and consumed files without changing sources, app registration, profile directories, variable files, or project state
