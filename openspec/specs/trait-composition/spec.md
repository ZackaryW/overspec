# trait-composition Specification

## Purpose

Resolve reusable profiles and local traits into attributable OpenSpec guidance at initialization, synchronization, and runtime without duplicating OpenSpec's workflow authority.

## Requirements

### Requirement: Profile and local trait discovery

Overspec SHALL recognize immediate `profile-<nonempty-name>` directories under the project's `openspec/.over/` and configured user home as profile sources. With profile mode off, it SHALL resolve only default sources; with mode on, named-profile discovery and selection SHALL be available. Trait discovery SHALL include regular TOML files whose basenames begin with `trait`, at any depth under the effective profile or the project's `.over/`. The local scan SHALL exclude every profile subtree, including inactive profiles, and internal generated-state directories. Discovery SHALL not require a source-list manifest, follow redirected directories outside its roots, or load one file twice. Paths SHALL be ordered deterministically by normalized relative path, then declarations by file order within each trait type.

#### Scenario: Nested local sources
- **WHEN** the project contains `.over/trait.toml`, `.over/team/python/traits.toml`, and `.over/team/trait-testing.toml`
- **THEN** all three contribute local traits, while an adjacent `notes.toml` does not

#### Scenario: Inactive profile is not a local source
- **WHEN** profiles `profile-default` and `profile-strict` exist but default is selected
- **THEN** only default's profile traits and non-profile local traits participate

#### Scenario: Default profile spans separate trait documents
- **WHEN** the selected default profile contains traits.toml, trait-tdd.toml, and trait-zuu.toml
- **THEN** all three documents contribute through the same profile, tdd participates unconditionally, and zuu participates only when both its project-file and dependency assertions match, without a skill lookup

### Requirement: Default composition and optional profile mode

The default user home SHALL be `~/.overspec`. An explicit `--home` SHALL override
`OVERSPEC_HOME`, which SHALL override that default. User profiles, activation, and
remote state SHALL use the chosen user home. Overspec SHALL NOT implicitly read,
write, or migrate `~/.over`; project sources and resolution state SHALL remain
under `openspec/.over/`.

Profile mode SHALL be off when no enabled state has been persisted in the chosen user home. In off mode, composition SHALL use default automatically, with project `profile-default` overriding the user default as a complete source and loose local traits applying afterward. It SHALL ignore named-profile environment and saved-user selections. Unrelated named profiles SHALL neither contribute nor force a selection error, and their source contents SHALL not be loaded or validated. With no default source, local-only operation SHALL remain available. Profile mode SHALL control access to named selection and management, not whether ordinary composition works.

`overspec profile activate` SHALL accept no profile name and SHALL toggle the persisted user-level mode, reporting its resulting state. It SHALL preserve any saved selection and unrelated user settings. Toggling SHALL not implicitly compile, synchronize configuration, fetch profiles, or delete sources or saved resolutions. Turning mode off SHALL restore default resolution even while a named environment selection remains set; turning it back on SHALL make that selection applicable again.

#### Scenario: User home avoids another application's files
- **WHEN** both ~/.overspec and ~/.over exist without a user-home override
- **THEN** overspec uses profiles and activation from ~/.overspec and leaves ~/.over untouched

#### Scenario: Ordinary project needs no activation
- **WHEN** mode is off and both user and project default profiles exist
- **THEN** composition uses the project default and loose local overrides without enabling profile management

#### Scenario: Dormant selection does not change default behavior
- **WHEN** mode is off, a saved or environment selection names strict, and a non-default profile contains malformed trait data
- **THEN** composition uses only default plus local traits and does not validate or activate that unrelated profile

#### Scenario: No default but other profiles exist
- **WHEN** mode is off and only named non-default profiles and loose local traits exist
- **THEN** composition uses the loose local traits without demanding profile selection

#### Scenario: Toggle on and off
- **WHEN** the user runs profile activate twice starting with mode off
- **THEN** the first call enables mode, the second disables it, both report the resulting state, and the saved selection, sources, compiled state, and generated config remain intact

#### Scenario: Profiles disappear only from output identity
- **WHEN** a selected profile resolves successfully
- **THEN** its source directory remains intact and its name does not prefix resolved trait names

### Requirement: Enabled profile selection through user settings and environment

While mode is on, Overspec SHALL select one profile using `OVERSPEC_PROFILE`, then the saved user-level selection, then implicit default. An explicitly provided empty, invalid, or missing selection SHALL fail without falling back. An absent implicit default SHALL allow local-only composition. `profile use NAME` SHALL save a user-level selection only while mode is enabled and SHALL report when an environment selection overrides it. Environment selection SHALL not persist itself or turn mode on. A project profile SHALL continue to shadow a same-name user profile completely; activation SHALL not pin profile sources or suppress local overrides.

The revised profile interface SHALL have no project-level persisted selection, no invocation `--profile` option, no activation-name argument, and no compatibility aliases for the replaced interface. Old project profile selectors SHALL not affect resolution. User-home selection through --home and OVERSPEC_HOME SHALL remain available in both modes.

#### Scenario: Environment overrides the saved user choice
- **WHEN** mode is on, the user selected strict, and OVERSPEC_PROFILE is team
- **THEN** team is effective for the invocation while the saved user selection remains strict

#### Scenario: Local source overrides the selected user source
- **WHEN** mode is on and the selected name has both project and user sources
- **THEN** the project source is used and local trait overrides still apply

#### Scenario: Invalid enabled selection
- **WHEN** mode is on and an explicit selected profile is absent or OVERSPEC_PROFILE is empty
- **THEN** resolution fails with a selection diagnostic rather than silently using default

#### Scenario: Disabling retains a named choice
- **WHEN** a user selects strict, disables profile mode, and later reenables it without an environment override
- **THEN** off-mode composition uses default and reenabled composition uses strict

#### Scenario: Obsolete project setting cannot select a profile
- **WHEN** project config contains an old profile selector
- **THEN** it has no effect on either off-mode default resolution or enabled user/environment selection

### Requirement: Remote profile retrieval through zuu

While profile mode is enabled, Overspec SHALL support explicit user-level profile retrieval and refresh from public GitHub directory sources through zuu's public subpath synchronization API. It SHALL support the default branch, a named branch, or a full commit selector, record source identity and resolved commit, and validate retrieved trait documents before making them usable. Retrieval SHALL not change the feature toggle or selected name. Remote source targets SHALL be owned generated directories separate from locally authored profiles. Ordinary sync and runtime resolution SHALL use retained local content without network retrieval, including a previously retrieved default while mode is off. Unsupported source kinds and failed downloads or validation SHALL report errors while preserving the last usable profile and mode/selection settings.

#### Scenario: Refresh a remote profile
- **WHEN** profile mode is on and the user explicitly refreshes a branch-backed profile
- **THEN** overspec uses zuu to retrieve its resolved revision and publishes it only after trait validation succeeds

#### Scenario: Offline synchronization
- **WHEN** a previously retrieved profile is available locally and the network is unavailable
- **THEN** sync can use that profile without attempting remote access

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

Overspec SHALL resolve identities across all three trait types by name. A local trait with the same name as a profile trait SHALL replace the complete profile declaration before evaluation. Duplicates within the selected profile or within the local layer SHALL fail with both origins. Surviving names SHALL be unique regardless of their type or attachment. Local overrides SHALL retain the inherited declaration's ordering position within its effective phase; additional local traits SHALL follow profile traits. Diagnostics SHALL retain file/profile origins even though emitted identity is name-only.

#### Scenario: Override a profile trait locally
- **WHEN** a profile and a local file both declare `require-codegraph`
- **THEN** the local declaration wins completely and only one trait with that name remains

#### Scenario: Collision across trait types
- **WHEN** two local files reuse one name across a trait and a runtime trait
- **THEN** resolution fails rather than treating the names as separate namespaces

#### Scenario: Complete override removes inherited elaboration
- **WHEN** a local override omits details that existed in its profile declaration
- **THEN** the effective local declaration has no details rather than inheriting the profile's explanation

### Requirement: Three evaluation lifetimes

Overspec SHALL evaluate and retain compile-time assertion results and rendered bodies only during init or update. Sync SHALL reuse that retained compilation, evaluate ordinary traits immediately, and retain runtime definitions without evaluating runtime assertions. The runtime resolution command SHALL evaluate runtime traits using invocation context. Missing or incompatible compiled state SHALL require init/update instead of silently compiling during sync. Source or activation changes affecting compile-time definitions SHALL require update; runtime-only and ordinary-only edits SHALL be usable by the next sync without rerunning unchanged compile-time traits.

#### Scenario: Tool availability changes after init
- **WHEN** zmem becomes available after init and sync runs without update
- **THEN** compile-time selection remains unchanged until update reevaluates it

#### Scenario: Ordinary trait changes
- **WHEN** an ordinary trait changes while the compile-time inputs remain unchanged
- **THEN** the next sync reevaluates and renders it without refreshing the compilation

#### Scenario: Deferred runtime body
- **WHEN** sync encounters a runtime trait
- **THEN** it retains the definition for a runtime command and does not emit its unconditional body

#### Scenario: Details follow their declaration lifetime
- **WHEN** compile-time details change after init
- **THEN** sync requires update to capture the changed definition, while ordinary or runtime details changes are captured at the next sync without reevaluating unchanged compile-time traits

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

The default zuu trait SHALL use exactly two assertions with default AND grouping: `files-exist` for both `.python-version` and `uv.lock`, and `python-dependency` for `zuu`. As an ordinary trait, it SHALL reevaluate these conditions at sync.

#### Scenario: Eligible Python uv project
- **WHEN** both project files exist and project.dependencies declares zuu
- **THEN** both assertions match and the zuu guidance is emitted

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
- **THEN** the next sync omits the zuu trait and removes its old owned guidance

### Requirement: Dynamic bodies retain stable identity

Overspec SHALL support scalar variable interpolation using `${key}` in bodies at the trait's evaluation time. Values SHALL come from explicit phase input, with runtime values supplied by the runtime invocation. Missing referenced values or non-scalar substitutions SHALL report errors rather than emit incomplete text. Interpolation SHALL not execute shell commands or source code. Literal `$$` SHALL represent a dollar sign. Body changes SHALL retain the same trait identity. Names and attachments SHALL not be dynamically interpolated.

#### Scenario: Runtime value changes
- **WHEN** the same runtime trait is resolved twice with different supplied scalar values
- **THEN** its rendered text changes while its trait name remains constant and persistent configuration is unchanged

### Requirement: Read-only resolution and explanations

Read-only resolution SHALL report retained, unmatched, overridden, and suppressed traits with their origins, phase, attachment, and assertion decisions, without writing state, fetching profiles, or changing OpenSpec lifecycle state. The emitted context including markers and runtime instructions SHALL fit OpenSpec's 50 KiB UTF-8 limit; exceeding it SHALL fail candidate preparation.

#### Scenario: Explain suppression
- **WHEN** an explanation is requested for the combined tooling example
- **THEN** it distinguishes require-codegraph matching from its body being suppressed by require-zmem

### Requirement: Resolution-bound detail lookup

`overspec trait show NAME --details` SHALL retrieve literal details by profile-independent name from the most recent successfully synchronized resolution for the owning project. An explicit `--resolution ID` SHALL select a retained historical resolution. Lookup SHALL support all three trait types, including unmatched or suppressed effective declarations, without evaluating assertions, rendering bodies, executing actions, fetching profiles, or writing state. It SHALL report the name, phase, attachment, and source origin with the explanation; absent details SHALL produce a successful explicit no-details result. Unknown names and absent, corrupt, or root-mismatched state SHALL produce actionable errors rather than falling back to live sources. Normal resolution/explanation output SHALL not dump details implicitly.

#### Scenario: Source changes after sync
- **WHEN** a source's details or profile activation changes after successful sync
- **THEN** default detail lookup still returns the saved explanation from that sync, and explicit historical lookup returns its selected retained version

#### Scenario: Runtime details do not evaluate conditions
- **WHEN** details are requested for a deferred runtime trait without invocation context
- **THEN** lookup returns the literal explanation without evaluating its conditions or substituting variable-looking examples

#### Scenario: No saved resolution
- **WHEN** detail lookup has neither a usable successful-sync receipt nor an explicit valid resolution
- **THEN** it fails with sync guidance rather than presenting current source text as synchronized details
