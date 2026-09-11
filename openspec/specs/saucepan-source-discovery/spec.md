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

Every discovered external profile SHALL contribute under its profile name. Same-name profiles across repositories SHALL remain ordered contributors rather than selecting one whole directory. Only selected-name declarations SHALL be parsed; other profile contents SHALL not be evaluated or parsed merely because a repository was discovered. Workspace contributors SHALL follow acquired repositories, and packaged default SHALL precede them when default is selected. User-home authored profiles and legacy remote copies SHALL not enter this catalog.

Standalone traits SHALL contribute independently of profile mode. For each repository in stable source order, its selected-profile layer SHALL apply first and its standalone layer second, before moving to the next repository. Workspace selected-profile and standalone layers SHALL apply last in that order. Duplicate names within one profile contributor or one standalone layer SHALL remain errors; collisions across layers SHALL replace complete declarations before reference validation and evaluation. Missing or empty profile contributors SHALL not erase lower names. Categories SHALL retain independent top-level-first lookup, including empty top-level directories suppressing fallback.

#### Scenario: Default without local profile files
- **WHEN** mode is off and a scoped repository provides profile-default
- **THEN** its declarations extend and override packaged default without creating user or workspace profile copies

#### Scenario: Local profile overrides external default
- **WHEN** workspace profile-default exists alongside external default contributors
- **THEN** workspace same-name declarations win and nonconflicting external and packaged names survive

#### Scenario: Inactive malformed profile
- **WHEN** a discovered non-default profile has malformed traits and mode is off
- **THEN** its declarations are not loaded and default composition remains available

#### Scenario: Same source duplicate
- **WHEN** two files within one repository's standalone layer declare the same name
- **THEN** loading fails with both origins instead of choosing a file accidentally

#### Scenario: Higher repository profile overrides lower standalone
- **WHEN** A precedes B and A's standalone layer and B's selected profile declare the same name
- **THEN** B wins regardless of whether A's standalone layout is top-level or fallback

#### Scenario: Standalone overrides its own profile
- **WHEN** a repository declares beta in its selected profile and its standalone layer
- **THEN** its standalone beta wins within that source, subject to any higher source override

#### Scenario: Multiple default extensions
- **WHEN** two repositories extend default with overlapping and disjoint names
- **THEN** all disjoint names survive, overlapping names use stable source priority, and changing view serialization order does not change the result

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

Connecting a user home SHALL remain independent of profile mode. With no connection configured, packaged default and workspace composition SHALL remain available without Saucepan. Once connected, unavailable dependencies, invalid scope credentials, unsupported formats, malformed selected source data, or missing consumed artifacts SHALL be explicit failures rather than an empty successful inventory or a silent fallback to packaged content. An authenticated empty view SHALL be a valid inventory with no repository contributions.

Discovery SHALL not initialize/register Saucepan, acquire or refresh sources, mirror files, install skills, change app filters, or persist selection. Source/view/config changes detected between preparation and publication SHALL reject inconsistent compilation or synchronization, including changes to the set or order of selected-profile contributors. No-op synchronization SHALL retain existing byte/mtime guarantees. Existing config-first/state-second partial failure diagnostics SHALL remain truthful.

#### Scenario: Connected versus unconfigured home
- **WHEN** an unconfigured user home is used without Saucepan
- **THEN** packaged default and workspace operations remain available; an explicitly configured unavailable connection instead produces an actionable error

#### Scenario: Scoped view changes during sync
- **WHEN** acquired entries, filters, current source selection, or priority change after preparation and before publication
- **THEN** publication is rejected with retry guidance and does not claim a consistent new result

#### Scenario: Preview is not acquisition
- **WHEN** explanation or sync preview discovers package and external content
- **THEN** it reads sources without changing app registration, source storage, profile directories, variable files, or project state

#### Scenario: Contributor changes during publication
- **WHEN** a repository adds or removes a selected-profile contributor after preparation
- **THEN** publication rejects stale source evidence even if a former whole-profile winner still exists
