# trait-composition Specification

## Purpose

Resolve reusable profiles and local traits into attributable OpenSpec guidance at initialization, synchronization, and runtime without duplicating OpenSpec's workflow authority.

## Requirements

### Requirement: Profile and local trait discovery

Overspec SHALL discover the packaged default, acquired repository sources defined by saucepan-source-discovery, and immediate `profile-<nonempty-name>` directories under the project's `openspec/.over/`. It SHALL NOT discover trait documents or profiles directly from the user home or legacy remote storage. With profile mode off it SHALL load only default profile declarations; with mode on it SHALL load only the selected name's declarations across all contributing sources. Repository and project standalone traits SHALL participate in either mode. Trait discovery SHALL include regular TOML files whose basenames begin with `trait`, at any depth within a selected profile or standalone root. Standalone scans SHALL exclude every profile subtree, including inactive profiles, and internal generated-state directories. Discovery SHALL not require a repository-specific source-list manifest, follow redirected directories outside its roots, or load one physical file twice within one source. Paths SHALL be ordered deterministically by normalized relative path, then declarations by file order within each trait type. External repositories SHALL retain independent top-level-first category selection and stable source priority.

#### Scenario: Nested local sources
- **WHEN** the project contains `.over/trait.toml`, `.over/team/python/traits.toml`, and `.over/team/trait-testing.toml`
- **THEN** all three contribute local traits, while an adjacent `notes.toml` does not

#### Scenario: Inactive profile is not a local source
- **WHEN** profiles profile-default and profile-strict exist but default is selected
- **THEN** only default's declarations across sources and non-profile standalone traits participate

#### Scenario: Default profile spans separate trait documents
- **WHEN** selected default contains traits.toml, trait-tdd.toml, and trait-zuu.toml
- **THEN** all three documents contribute, tdd guidance participates unless explicitly disabled by its project boolean setting at sync, and zuu guidance participates only when enabled and both its project-file and dependency assertions match, without a skill lookup

#### Scenario: Obsolete user content is not a source
- **WHEN** the selected user home contains authored profile or standalone documents or `.state/remotes` content
- **THEN** those documents do not contribute, cause duplicate errors, or get migrated or deleted automatically

### Requirement: Default composition and optional profile mode

The default user home SHALL be `~/.overspec`. Explicit `--home` SHALL override `OVERSPEC_HOME`, which SHALL override that default. Activation, saved selection, Saucepan connection/priority, and existing configured variable settings SHALL use the chosen user home. Acquired content SHALL remain in Saucepan-managed storage accessed through its public API; bundled content SHALL remain in the installed package. Overspec SHALL NOT implicitly read, write, or migrate `~/.over`; project sources and resolution state SHALL remain under `openspec/.over/`.

Profile mode SHALL be off when no enabled state has been persisted. In off mode, composition SHALL select default automatically and apply packaged default, each eligible acquired repository, and the workspace in ascending priority. Within each repository or workspace, selected-profile declarations SHALL precede its standalone declarations. Same-name profile contributors SHALL extend rather than replace whole profiles. Saved and environment named selections SHALL be ignored in off mode. Unrelated named profiles SHALL neither contribute nor force selection errors and their declarations SHALL not be loaded or validated. Packaged default SHALL remain available when no other default contributor exists. Profile mode SHALL control named selection and management, not ordinary composition.

`overspec profile activate` SHALL accept no profile name and SHALL toggle persisted user-level mode, reporting its resulting state. It SHALL preserve saved selection and unrelated settings. Toggling SHALL not implicitly compile, synchronize, acquire content, or delete sources or saved resolutions. Turning mode off SHALL restore default resolution even while a named environment selection remains set; turning it back on SHALL make that selection applicable again.

#### Scenario: User home avoids another application's files
- **WHEN** both ~/.overspec and ~/.over exist without a user-home override
- **THEN** overspec uses settings from ~/.overspec and leaves ~/.over untouched

#### Scenario: Ordinary project needs no activation
- **WHEN** mode is off and packaged, repository, and project default contributors exist
- **THEN** they compose by source priority with workspace overrides, without enabling profile management

#### Scenario: Dormant selection does not change default behavior
- **WHEN** mode is off, a saved or environment selection names strict, and strict has malformed declarations
- **THEN** composition uses default and applicable standalone traits without validating or activating strict

#### Scenario: No default but other profiles exist
- **WHEN** only named non-default profiles and loose local traits exist outside the package
- **THEN** packaged default and applicable standalone traits compose without demanding profile selection

#### Scenario: Toggle on and off
- **WHEN** the user runs profile activate twice starting with mode off
- **THEN** the first enables mode and the second disables it, both report state, and saved selection, sources, compilation, and config remain intact

#### Scenario: Profiles disappear only from output identity
- **WHEN** a selected profile resolves successfully
- **THEN** source directories remain intact and the profile name does not prefix resolved trait names

### Requirement: Enabled profile selection through user settings and environment

While mode is on, Overspec SHALL select one profile name using `OVERSPEC_PROFILE`, then saved user selection, then implicit default. Explicit empty, invalid, or missing selections SHALL fail without falling back. Packaged default SHALL make default selectable without external or workspace content. Other names SHALL be available when at least one repository or workspace provides a matching directory, including an empty directory. `profile use NAME` SHALL save a selection only while mode is enabled and report when environment selection overrides it. Environment selection SHALL not persist itself or turn mode on. All matching contributors SHALL compose by source priority; activation SHALL not pin sources or suppress workspace overrides. Packaged default SHALL NOT implicitly contribute to a different selected profile.

The interface SHALL have no project-level persisted selection, invocation `--profile` option, activation-name argument, or compatibility aliases for removed interfaces. Old project profile selectors SHALL not affect resolution. User-home selection through --home and OVERSPEC_HOME SHALL remain available in both modes.

#### Scenario: Environment overrides the saved user choice
- **WHEN** mode is on, saved selection is strict, and OVERSPEC_PROFILE is team
- **THEN** team is effective for the invocation and saved selection remains strict

#### Scenario: Local source overrides the selected user source
- **WHEN** mode is on and strict exists in two acquired repositories and the workspace
- **THEN** all strict contributors compose in source order and workspace declarations replace only matching names

#### Scenario: Invalid enabled selection
- **WHEN** mode is on and an explicit selected profile is absent or OVERSPEC_PROFILE is empty
- **THEN** resolution fails with a selection diagnostic rather than silently using default

#### Scenario: Disabling retains a named choice
- **WHEN** the user selects strict, disables profile mode, and reenables it without an environment override
- **THEN** off-mode composition uses default and reenabled composition uses strict

#### Scenario: Obsolete project setting cannot select a profile
- **WHEN** project config contains an old profile selector
- **THEN** it has no effect on default or enabled user/environment selection

### Requirement: Trait declarations and attachments

Overspec SHALL accept the sketch's `[[compiletime-trait]]`, `[[trait]]`, and `[[runtime-trait]]` declarations without requiring a version field absent from that sketch. Each declaration SHALL contain a stable name, a nonblank body, and one required `attach` string. Supported attachments SHALL be `context`, `rules.<artifact-id>`, `operations.apply.guidance`, and `operations.archive.guidance`. The suffix after `rules.` SHALL be interpreted as one literal artifact ID. Names SHALL be nonempty lowercase alphanumeric/hyphen identifiers starting with a letter, suitable for unambiguous markers and CLI arguments. Unknown declaration fields, malformed assertions/actions, and unsupported attachments SHALL fail validation.

#### Scenario: Same lifetime with different destinations
- **WHEN** two compile-time traits attach to context and proposal rules respectively
- **THEN** their bodies route to those destinations independently of their shared evaluation lifetime

#### Scenario: Custom artifact ID
- **WHEN** a trait attaches to `rules.review.notes`
- **THEN** its body targets the literal artifact ID `review.notes`

### Requirement: Compact bodies and optional details

Each trait SHALL express one responsibility in a small, self-contained body. A declaration MAY include an optional string `details` for longer explanations, examples, or configuration notes. Essential instructions SHALL remain in the body; reading details SHALL not be a prerequisite for following it. Details SHALL be literal prose, without interpolation or execution. Omitted or whitespace-only details SHALL mean no elaboration is available; non-string values SHALL fail validation. Brevity SHALL be an authoring convention, not an arbitrary parser length limit.

#### Scenario: Small trait needs no elaboration
- **WHEN** a valid short trait omits details
- **THEN** it remains valid and its body is sufficient to follow its instruction

#### Scenario: Detailed process stays separate
- **WHEN** tdd supplies a compact red-green-refactor body and a longer details string
- **THEN** both are retained, but the longer process is available only through explicit detail lookup

#### Scenario: Invalid details type
- **WHEN** a declaration supplies a table or list as details
- **THEN** source validation fails with the declaration's origin

### Requirement: Profile-independent identity and local overrides

Overspec SHALL resolve identities across all three trait types by name. Complete declarations SHALL apply from lowest to highest source priority: packaged default when selected, acquired repositories in configured order, then the workspace. Within each repository or workspace, its selected-profile declarations SHALL apply before its standalone declarations. A higher source's profile declaration SHALL therefore override a lower source's standalone declaration. A later layer's same-name declaration SHALL replace the entire earlier declaration before reference validation and evaluation; assertions, actions, body, details, phase, and attachment SHALL NOT be inherited implicitly. Nonconflicting lower declarations SHALL survive even when higher contributors contain an empty profile directory.

Duplicates within one profile contributor or one standalone layer SHALL fail with both origins; the profile-to-standalone boundary within the same source SHALL allow complete overrides. Surviving names SHALL be unique regardless of type or attachment. Overrides SHALL retain the inherited name's insertion position before stable phase ordering; additional names SHALL follow earlier-layer names within their phase. Diagnostics SHALL retain origins and package or repository provenance for winners and overridden declarations even though emitted identity is name-only. Malformed declarations and within-layer duplicates in a selected lower contributor SHALL remain errors even when a higher layer could override the affected name.

#### Scenario: Override a profile trait locally
- **WHEN** the workspace profile and a loose workspace file both declare require-codegraph
- **THEN** the standalone declaration wins completely and only one name remains

#### Scenario: Collision across trait types
- **WHEN** two files within one standalone layer reuse one name across a trait and runtime trait
- **THEN** resolution fails instead of treating the types as separate namespaces

#### Scenario: Complete override removes inherited elaboration
- **WHEN** a higher declaration omits details present in a lower declaration
- **THEN** the effective declaration has no details

#### Scenario: Source rank precedes layout rank
- **WHEN** lower repository A declares beta standalone and higher repository B declares beta in the selected profile
- **THEN** B's profile declaration wins, and A's other names survive

#### Scenario: Local profile retains lower unmatched names
- **WHEN** packaged default contains alpha and beta and workspace profile-default contains only a replacement beta
- **THEN** alpha survives, workspace beta wins, and the profile directory does not erase the package layer

#### Scenario: Selected malformed contributor remains visible
- **WHEN** a lower selected-profile document is malformed and a higher contributor declares the same name
- **THEN** source loading fails with the lower origin before publication instead of using whole-profile shadowing to hide the error

### Requirement: Three evaluation lifetimes

Overspec SHALL evaluate and retain compile-time assertion results and rendered bodies only during init or update. Sync SHALL reuse that retained compilation, evaluate ordinary traits immediately, and retain runtime definitions without evaluating runtime assertions. The runtime resolution command SHALL load current effective runtime declarations and evaluate them using current invocation variables, without a sync resolution ID. Runtime SHALL NOT evaluate compile-time or normal traits; their retained results provide earlier-phase history. Runtime-only invocation SHALL work without init or sync when no retained state exists. Missing or incompatible compiled state SHALL require init/update instead of silently compiling during sync. Source or activation changes affecting compile-time definitions SHALL require update; runtime-only and ordinary-only edits SHALL be usable by the next sync without rerunning unchanged compile-time traits.

#### Scenario: Tool availability changes after init
- **WHEN** zmem becomes available after init and sync runs without update
- **THEN** compile-time selection remains unchanged until update reevaluates it

#### Scenario: Ordinary trait changes
- **WHEN** an ordinary trait changes while the compile-time inputs remain unchanged
- **THEN** the next sync reevaluates and renders it without refreshing the compilation

#### Scenario: Deferred runtime body
- **WHEN** sync encounters a runtime trait
- **THEN** it emits a deferred command selecting the attachment and unique names, not a snapshot ID or unconditional body

#### Scenario: Details follow their declaration lifetime
- **WHEN** compile-time details change after init
- **THEN** sync requires update to capture the changed definition, while ordinary or runtime details changes are captured at the next sync without reevaluating unchanged compile-time traits

#### Scenario: Runtime edits need no sync
- **WHEN** a runtime body or condition changes after sync
- **THEN** the next runtime invocation uses that edit without re-evaluating compile-time or normal traits

### Requirement: Assertions and output suppression

Overspec SHALL support `which`, `require-trait`, `loaded-trait`, leading-`~` predicate negation, and runtime context match/includes assertions from the sketch. Assertion groups SHALL use AND by default and OR when their `or = true`; legacy flat lists SHALL continue to use `assert_or_grouping`. Omitted assertions or an empty legacy list SHALL match unconditionally. Evaluation SHALL be a deterministic single pass per phase. Trait-state assertions SHALL read the set of previously matched traits, including prior phases, not the set of currently emitted bodies. References to unknown names or later evaluation phases SHALL be rejected. A reference to a known but not-yet-matched trait in the same phase SHALL be false before negation.

A matched trait's `remove-trait` action SHALL suppress the target body's emission, including when that body would occur later, without deleting source data or removing the target from matched-history state. An unmatched trait SHALL take no actions. Runtime suppression SHALL be limited to runtime traits in the same attachment group; earlier phases SHALL not require runtime context.

#### Scenario: Combined tooling replaces a generic body
- **WHEN** require-codegraph matches and require-zmem subsequently matches its dependency and executable assertions
- **THEN** require-zmem can suppress require-codegraph's body while require-codegraph remains a matched dependency

#### Scenario: OR grouping with negation
- **WHEN** a trait has OR grouping over two negated loaded-trait assertions
- **THEN** it matches if either named trait has not matched, and fails only when both have matched

### Requirement: Recursive numbered assertion groups

Overspec SHALL accept an `assert` table under each trait declaration, with optional boolean `or` defaulting to false. Each group SHALL contain either a nonempty `assertion` array of registered assertion payloads or one or more numbered child group tables, recursively. Numbered keys SHALL be canonical positive decimal integers, need not be contiguous, and SHALL evaluate in numeric order; leaves SHALL evaluate in array order. AND SHALL stop at the first false child and OR at the first true child at every depth. A leading `~` SHALL negate only its leaf result. Omitted assertions remain unconditional.

Overspec SHALL reject empty groups, mixed numbered children and assertion arrays, nonboolean operators, malformed or unknown fields/handlers, noncanonical child keys, and a legacy grouping flag on a table-shaped assert. Validation SHALL inspect all nested leaves for unknown references, phase constraints, and runtime attachment constraints even when evaluation would skip them. Errors SHALL identify source and condition path. The default profile SHALL use grouped tables while retaining its existing conditions, bodies, details, and actions. Flat lists and their legacy grouping flag SHALL remain readable, including in saved resolutions.

#### Scenario: Alternatives of conjunctions
- **WHEN** an OR root contains two AND groups with leaves A/B and C/D
- **THEN** it matches exactly when `(A AND B) OR (C AND D)` is true

#### Scenario: Nested alternatives and numeric ordering
- **WHEN** a group contains keys 10, 2, and 1 in source order and another nested OR group
- **THEN** child evaluation follows 1, 2, 10, each group applies its own operator, and skipped branches execute no assertions

#### Scenario: Invalid skipped reference
- **WHEN** a short-circuited branch contains an unknown or later-phase reference
- **THEN** validation fails before trait evaluation despite that branch being unnecessary to the result

#### Scenario: Invalid condition shape
- **WHEN** a group is empty, mixes assertion leaves with numbered children, or uses a noncanonical child number or nonboolean or field
- **THEN** parsing fails with its source and condition path rather than enabling the trait

#### Scenario: Owning trait and lifetime
- **WHEN** a source contains multiple declarations and tables prefixed with trait, compiletime-trait, or runtime-trait
- **THEN** each table belongs to the most recent declaration of that type and is evaluated only at that type's declared lifetime

#### Scenario: Explain nested short-circuiting
- **WHEN** a grouped condition has evaluated and skipped branches
- **THEN** structured and terminal explanations show group operators, paths, results, leaf negation and reasons, and skipped branches without evaluating those branches

#### Scenario: Legacy source compatibility
- **WHEN** an existing source or saved resolution uses a flat assert array and assert_or_grouping
- **THEN** its matching, negation, order, unconditional empty-array behavior, and actions retain their previous semantics

### Requirement: Project file and Python dependency assertions

Overspec SHALL support `files-exist` with a nonempty list of project-root-relative paths. It SHALL match only when every path identifies an existing regular file within the project. A missing file or directory in place of a file SHALL be a non-match; invalid confined paths or inspection errors SHALL be reported rather than treated as absence.

Overspec SHALL support `python-dependency` with a package `name`. It SHALL read the project's `pyproject.toml` and inspect only `project.dependencies`. Missing pyproject.toml or an absent dependency list SHALL be a non-match; unreadable or malformed TOML, invalid dependency-list types, and malformed requirements SHALL report errors. Matching SHALL compare normalized declared requirement names, accepting versions, extras, direct references, and environment markers without evaluating whether a declared dependency is installed or its marker is active. Unrelated package names, optional/development-only dependencies, and entries only under `tool.uv.sources` SHALL not establish a match.

The default zuu trait SHALL use exactly two assertions with default AND grouping: `files-exist` for both `.python-version` and `uv.lock`, and `python-dependency` for `zuu`. As a compiletime-trait, it SHALL evaluate these conditions at init/update and retain eligibility until the next update. Its `zuu` setting SHALL control publication at sync through the compiled setting gate.

#### Scenario: Eligible Python uv project
- **WHEN** both project files exist and project.dependencies declares zuu
- **THEN** both assertions match at init/update and subsequent sync emits the zuu guidance unless its setting is false

#### Scenario: Missing uv project evidence
- **WHEN** either .python-version or uv.lock is absent
- **THEN** the first assertion fails and zuu guidance is omitted even if zuu is declared

#### Scenario: Dependency declaration distinguishes names
- **WHEN** project.dependencies contains `zuu>=1` or `zuu[extra]` instead of a bare `zuu` string
- **THEN** the dependency assertion matches by package name, while `zuu-helper` does not match

#### Scenario: Source override alone is not a dependency
- **WHEN** tool.uv.sources contains zuu but project.dependencies does not
- **THEN** the dependency assertion does not match

#### Scenario: Project eligibility changes
- **WHEN** project.dependencies removes zuu after an earlier successful sync
- **THEN** init/update reevaluates eligibility and subsequent sync removes its old owned guidance; sync alone retains compiled eligibility

### Requirement: Dynamic bodies retain stable identity

Overspec SHALL support scalar variable interpolation using `${key}` in bodies at the trait's evaluation time. Values SHALL follow the scoped-variable-files precedence at the trait's evaluation time. Project file layers SHALL participate in static evaluation; selected-change file layers SHALL participate only in runtime resolution. Compile-time values SHALL remain frozen until update. Runtime bodies SHALL use the same effective variable mapping as runtime assertions and the current effective declarations discovered at invocation. Runtime SHALL NOT accept a resolution ID or render bodies from a saved declaration snapshot. Missing referenced values or non-scalar substitutions SHALL report errors rather than emit incomplete text. Interpolation SHALL not execute shell commands or source code. Literal `$$` SHALL represent a dollar sign. Body changes SHALL retain the same trait identity. Names and attachments SHALL not be dynamically interpolated.

#### Scenario: Runtime value changes
- **WHEN** the same runtime trait is resolved twice with different supplied scalar values
- **THEN** its rendered text changes while its trait name remains constant and persistent configuration is unchanged

#### Scenario: Runtime file override changes
- **WHEN** a selected change's current scalar value changes between invocations of the current resolution
- **THEN** the next body uses the changed value without changing trait identity or shared config

#### Scenario: List is not a body scalar
- **WHEN** a matched trait interpolates a list-valued variable
- **THEN** rendering fails with a scalar diagnostic even though that list can be used by membership assertions

### Requirement: Read-only resolution and explanations

Read-only resolution SHALL report retained, unmatched, overridden, and suppressed traits with their origins, phase, attachment, and assertion decisions, without writing state, fetching profiles, or changing OpenSpec lifecycle state. The emitted context including markers and runtime instructions SHALL fit OpenSpec's 50 KiB UTF-8 limit; exceeding it SHALL fail candidate preparation.

#### Scenario: Explain suppression
- **WHEN** an explanation is requested for the combined tooling example
- **THEN** it distinguishes require-codegraph matching from its body being suppressed by require-zmem

### Requirement: Resolution-bound detail lookup

`overspec trait show NAME --details` SHALL retrieve literal details by profile-independent name from the most recent successfully synchronized resolution for the owning project. An explicit `--resolution ID` SHALL guard the currently stored resolution; superseded IDs SHALL fail with current-state guidance. Lookup SHALL support all three trait types, including unmatched or suppressed effective declarations, without evaluating assertions, rendering bodies, executing actions, fetching profiles, or writing state. It SHALL report the name, phase, attachment, and source origin with the explanation; absent details SHALL produce a successful explicit no-details result. Unknown names and absent, corrupt, or root-mismatched state SHALL produce actionable errors rather than falling back to live sources. Normal resolution/explanation output SHALL not dump details implicitly.

#### Scenario: Source changes after sync
- **WHEN** a source's details or profile activation changes after successful sync
- **THEN** default detail lookup still returns the saved explanation from that sync, and an explicit matching current ID returns that same version; after resync replaces it, the old ID fails

#### Scenario: Runtime details do not evaluate conditions
- **WHEN** details are requested for a deferred runtime trait without invocation context
- **THEN** lookup returns the literal explanation without evaluating its conditions or substituting variable-looking examples

#### Scenario: No saved resolution
- **WHEN** detail lookup has neither a usable successful-sync receipt nor an explicit valid resolution
- **THEN** it fails with sync guidance rather than presenting current source text as synchronized details

### Requirement: Sync-time setting gate for compiled guidance

A compiletime-trait MAY declare setting as a nonblank literal variable key. Other lifetimes SHALL reject that field. Init/update SHALL evaluate eligibility, actions, and body independently of this publication gate. During sync/preview, an eligible unsuppressed compiled contribution SHALL consult only its referenced effective project setting using static variable precedence. Missing SHALL mean enabled; explicit false SHALL omit its body, and true SHALL permit normal publication. A present nonboolean value SHALL fail before modifying configuration. Selected-change or runtime context SHALL not participate.

The gate SHALL NOT reevaluate compile-time assertions/actions, erase matched history, undo compiled actions, or enable a compilation-ineligible trait. Toggling the value SHALL not require recompilation unless the same variable is used by a compiled body. Disabling and re-enabling SHALL reuse the retained body. Explain SHALL identify the setting key and enabled decision separately from assertion eligibility. Ungated traits and unrelated settings SHALL retain existing behavior.

#### Scenario: Toggle a compiled policy
- **WHEN** a compiled TDD policy's tdd setting changes false then true between syncs
- **THEN** its body disappears then returns without changing compilation or rerunning its assertions

#### Scenario: Failed assertion stays ineligible
- **WHEN** a compile-time assertion failed and the referenced setting becomes true
- **THEN** the guidance remains absent until an init/update makes the trait eligible

#### Scenario: Missing and invalid settings
- **WHEN** an eligible trait's setting is absent or has a present nonboolean value
- **THEN** absence enables publication, while the nonboolean value fails before a config write

#### Scenario: Limited publication check
- **WHEN** an unrelated variable changes or a gate hides a matched trait
- **THEN** no new assertions run and matched history remains intact for dependencies
