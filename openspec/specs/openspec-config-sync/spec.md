# openspec-config-sync Specification

## Purpose

Maintain native OpenSpec guidance from composed traits through explicit, reviewable synchronization that replaces owned fields and preserves unrelated configuration data.

## Requirements

### Requirement: Discoverable terminal commands and stable script output

Overspec SHALL provide a successful no-argument command overview, descriptive
command help, and grouped options. Human-readable output SHALL distinguish sync
status, candidate YAML, and diff, and SHALL present profile scope/activation and
trait explanations clearly. Long preview lines SHALL remain complete, wrapping
for terminal display where needed. The CLI SHALL preserve the non-profile command
surface, common options at root/group/command levels, and repeated runtime trait
arguments. JSON output SHALL contain only the structured result without styling;
resolved guidance SHALL retain literal text and provenance without formatting
decoration. Usage and expected operational failures SHALL return nonzero without
an application traceback.

#### Scenario: Discover available commands
- **WHEN** the user runs overspec without a command or requests command help
- **THEN** the CLI shows the appropriate command overview or grouped options and exits successfully

### Requirement: Profile commands appear only when profile mode is enabled

The profile group SHALL expose only `activate` while mode is off. Named selection and listing SHALL be absent from help and completion and unavailable for direct dispatch. While mode is on, it SHALL additionally expose `use NAME` and `list`; activate SHALL remain available. Legacy profile `pull` and `update` SHALL be absent and unavailable in both modes without compatibility aliases. The ordinary top-level `overspec update` compilation command SHALL remain available. `activate` SHALL accept no name and report resulting mode in terminal and structured output. The surface SHALL reflect the chosen user home's current state on every invocation, including repeated invocations in one process. `--home` at every supported common-option position SHALL control the same toggle and command availability.

Named-management core operations SHALL also reject use while mode is off. Ordinary init, update, sync, static trait resolution, live runtime resolution, and saved detail lookup SHALL remain available. Removed flags or aliases SHALL not bypass the off-state boundary. Listing in enabled mode SHALL include default from the installed package and show each profile's ordered contributors, active/saved selection, and source kind/location rather than implying one winning directory. Package contributors SHALL identify the distribution and version; repository contributors SHALL identify source and revision; workspace contributors SHALL identify their paths. Contributor reporting SHALL not require parsing inactive profile documents.

#### Scenario: Default command surface remains small
- **WHEN** mode is off and help or completion is requested
- **THEN** activate is the only available profile subcommand

#### Scenario: Disabled command cannot be invoked directly
- **WHEN** mode is off and a caller invokes profile use or list
- **THEN** the command is unavailable and no activation, selection, network, or config mutation occurs

#### Scenario: Activation expands the next invocation
- **WHEN** mode is toggled on, help is requested, then mode is toggled off and help requested again
- **THEN** use and list appear only in the middle invocation, including within one process

#### Scenario: Explicit home selects the feature state
- **WHEN** two homes have different mode states and a supported --home position selects one
- **THEN** availability and resulting reads and writes use that home

#### Scenario: Read profiles and preview changes
- **WHEN** profiles are listed with mode enabled or sync is previewed in either mode
- **THEN** profiles report ordered contributors and selection, default is present without acquisitions, and preview separates summary, complete candidate, and diff

#### Scenario: Script consumes output
- **WHEN** --json is supplied or runtime trait resolution is run
- **THEN** JSON remains parseable without decorations and runtime guidance remains literal with the same IDs and markers

#### Scenario: Removed acquisition interface
- **WHEN** profile pull or profile update is requested in either mode
- **THEN** dispatch fails without network or filesystem mutation, while top-level update remains usable

### Requirement: Explicit project target

Overspec SHALL support an explicit project root and otherwise use the current working directory as the project root. It SHALL target that root's existing `openspec/config.yaml`, falling back to `config.yml` only when the YAML path is absent. Missing configuration or invalid YAML SHALL fail without creating a replacement project or selecting a global store. The configuration root SHALL be a mapping. Existing `operations`, `operations.apply`, and `operations.archive` containers, when present, SHALL be mappings.

#### Scenario: YAML alternative
- **WHEN** a project has only `openspec/config.yml`
- **THEN** preview and sync address that file and do not create `config.yaml`

#### Scenario: Invalid operation container
- **WHEN** the existing configuration contains a scalar `operations.apply` value
- **THEN** synchronization fails without changing the file

### Requirement: Read-only preview

Overspec SHALL offer a preview containing the exact target path, complete candidate YAML, whether a write would occur, and a diff against the current file. Preview SHALL use the same composition and candidate construction as synchronization and SHALL not modify project or user state. Diagnostics SHALL state that manual edits in owned fields are replaced by sync.

#### Scenario: Review manual guidance replacement
- **WHEN** existing context contains a manual edit absent from selected traits
- **THEN** preview shows its replacement and leaves the file unchanged

### Requirement: Replace only owned guidance fields

Synchronization SHALL replace `context`, the entire `rules` mapping, `operations.apply.guidance`, and `operations.archive.guidance` with the resolved contributions. It SHALL preserve the semantic values of every other field, including unknown keys, other operations, and sibling properties within apply and archive. The previous owned values SHALL not become composition inputs. No custom managed-context field SHALL be required for OpenSpec to consume the generated guidance.

#### Scenario: Preserve unowned operation properties
- **WHEN** the existing configuration contains `schema`, `references`, a custom top-level field, an apply property other than `guidance`, and an unknown operation
- **THEN** synchronization preserves all those values while replacing only the owned guidance fields

### Requirement: Body-only guidance projection

Synchronization SHALL project rendered static bodies and bundled runtime command instructions, never trait details. Normal runtime resolution SHALL return matched unsuppressed bodies without details. Longer elaborations SHALL remain available through explicit resolution-bound lookup. Source markers SHALL retain their existing short name-only form, without an additional per-trait lookup command in configuration.

#### Scenario: Detailed TDD guidance
- **WHEN** the default tdd trait supplies both body and details
- **THEN** apply guidance contains exactly its compact body and source marker, while the full process remains in the saved resolution

### Requirement: Remove stale contributions

Synchronization SHALL remove owned fields with no remaining static contributions or runtime groups. It SHALL prune empty operation containers only when they contain no preserved properties. A successfully resolved empty inventory with a compatible compilation SHALL remove all owned guidance while retaining other configuration data. Missing or invalid selected profiles and compiled state SHALL be errors, not empty inventories.

#### Scenario: Remove the last archive trait
- **WHEN** the selected traits no longer contribute archive guidance
- **THEN** old archive guidance disappears and any unrelated archive properties remain

#### Scenario: Clear all generated guidance
- **WHEN** the discovered inventory is empty and a successful init/update has established its compatible empty compilation
- **THEN** synchronization removes context, rules, and apply/archive guidance and preserves schema and all other unowned fields

### Requirement: Validated and repeatable writes

Overspec SHALL validate all resolved sources and the complete candidate before replacing the target. A candidate with unchanged parsed configuration data AND unchanged required source markers SHALL result in no configuration write, preserving the existing bytes and modification time. Resolution state MAY still be published when its retained details changed. Changed candidates SHALL be written by atomic file replacement. Detectable changes to the captured source or target bytes before committing SHALL abort synchronization. Validation, detected staleness, and failures before replacement SHALL leave the target unchanged and return a non-success result.

#### Scenario: Repeat synchronization
- **WHEN** synchronization runs twice with equivalent sources and target data
- **THEN** the second run reports unchanged and preserves the file's bytes and modification time

#### Scenario: Target changes during preparation
- **WHEN** the target file's bytes change after they were read and before the pre-replacement recheck
- **THEN** synchronization aborts and preserves the intervening edit

#### Scenario: Effective profile changes during preparation
- **WHEN** a relevant mode, user selection, environment selection, or source-selection input changes after preparation but before publication
- **THEN** synchronization detects the changed effective selection and aborts without committing the prepared config

#### Scenario: Mode changes without changing effective default
- **WHEN** toggling mode still resolves the same default source and the same compile-time definitions and inputs
- **THEN** existing compilation remains usable, while a toggle or selection that changes the effective profile requires explicit update before sync

#### Scenario: Invalid source cannot partially update output
- **WHEN** one selected trait document fails validation
- **THEN** no portion of its or other traits' guidance is written

### Requirement: Short source markers

Overspec SHALL identify each emitted static contribution using only its resolved trait `name`. Each context fragment SHALL end with `<!-- over:<name> -->` on its own line. Each emitted static rule or operation-guidance list item SHALL carry a YAML comment `# over:<name>` on that item's scalar header line. A bundled runtime command SHALL use the corresponding marker form with its unique names joined by commas in command order, such as `over:first,second`. Markers SHALL NOT contain a profile prefix or body digest. Profile and file provenance SHALL remain available in resolution diagnostics. Markers SHALL describe output provenance, not grant ownership beyond the already managed fields.

#### Scenario: Resolved profiles disappear from output identity
- **WHEN** the resolved trait `require-codegraph` originated in `profile-default`
- **THEN** its marker is `over:require-codegraph` and contains no profile name

#### Scenario: Repair a missing list marker
- **WHEN** an existing guidance body's value is correct but its required YAML marker is absent or names another trait
- **THEN** preview reports a change and sync restores the correct marker

#### Scenario: Changed body retains its identity
- **WHEN** a trait's rendered body changes while its resolved name remains unchanged
- **THEN** synchronization replaces the old contribution and retains the same short marker without appending a duplicate old body


### Requirement: Retain successful synchronization for detail lookup

Every successful sync SHALL retain only the current root-bound content-identified resolution in .state.json, including static-only or empty inventories, and report its identifier. After configuration commit or verification of an unchanged candidate, it SHALL atomically publish the current resolution and latest-success receipt together in the state file linking the resolution to a fingerprint of the owned values and required source markers. Default detail lookup SHALL verify that receipt against the current owned configuration; a mismatch SHALL require resync or the explicit current resolution ID. Unowned configuration edits SHALL not invalidate the receipt. Preview SHALL publish neither bundle nor receipt.

Receipt publication failure SHALL return non-success and explain that configuration may already have been committed; it SHALL not claim a multi-file transaction. Any usable default lookup SHALL still validate the receipt and return the version it identifies. An explicit ID SHALL match the current stored resolution and validate its hash independently of the current configuration; superseded IDs SHALL fail. Identical state SHALL be reused.

#### Scenario: Static-only details change
- **WHEN** an ordinary trait's details change in a project with no runtime groups and its rendered bodies remain unchanged
- **THEN** sync publishes the new resolution and receipt while preserving configuration bytes and modification time

#### Scenario: Configuration changed outside sync
- **WHEN** owned guidance or its required markers no longer match the saved receipt
- **THEN** default lookup reports stale synchronization instead of associating that guidance with possibly incorrect details

#### Scenario: Receipt publication fails after replacement
- **WHEN** configuration replacement succeeds but publishing the latest-success receipt fails
- **THEN** sync reports the partial outcome, preserves the previous state document, and a retry can complete publication

### Requirement: Runtime command evaluates invocation context

The runtime command SHALL evaluate requested runtime traits and their same-group runtime dependencies using the current effective source definitions, returning only matched unsuppressed bodies for that attachment with name-only provenance. It SHALL accept a JSON context file, treat runtime context match as exact typed equality, and treat includes as exact membership rather than substring matching. The sketch's `kv = "do-not-archive=true"` SHALL compare against boolean true. Runtime assertions and body interpolation SHALL share effective variables from current configured defaults, project/change variable files, and explicit invocation JSON according to scoped-variable-files precedence. An includes operand `$activeChanges` SHALL refer to a list supplied by those effective inputs and match when the target list overlaps it. Absent effective keys, equality type mismatches, and non-list membership targets SHALL make the predicate false, allowing the sketch's boolean-or-list alternatives. Malformed context input or missing/invalid referenced variables needed for an otherwise applicable membership evaluation SHALL report an error. Missing explicit context SHALL contribute an empty layer, not inherit from another invocation; other applicable file/default layers SHALL still participate. Runtime declarations SHALL be loaded afresh through existing discovery. Earlier-phase results SHALL be read from retained state without reevaluating those phases; no saved resolution ID is an input. Retained matches SHALL NOT make a name that is now runtime appear matched before its current condition succeeds. Missing state SHALL contribute empty earlier-phase history; corrupt existing state SHALL fail explicitly.

The command SHALL be read-only, perform no remote retrieval, and leave config and compilation unchanged. It SHALL emit no applicable guidance when no requested trait matches. It SHALL not invoke itself recursively or advance, block, or archive an OpenSpec change. Instruction text accompanying the command SHALL direct the agent to run it from the owning project root, supply the selected --change-root and explicit context when applicable, and apply the returned guidance to the current operation.

#### Scenario: Runtime archive flag
- **WHEN** the do-not-archive trait resolves with a context containing boolean `do-not-archive: true`
- **THEN** the command returns its body, without writing that transient body into shared configuration or changing archive state

#### Scenario: Runtime includes current change
- **WHEN** `do-not-archive` contains a list that overlaps the supplied `activeChanges` list
- **THEN** the includes predicate matches by exact list membership

#### Scenario: No context leakage
- **WHEN** a second runtime invocation supplies no context after an earlier invocation supplied an archive flag
- **THEN** the second invocation does not reuse that explicit flag; any matching value must come independently from its applicable layers

#### Scenario: Persistent runtime match
- **WHEN** a current resolution has no explicit context but selected-change vars supply boolean do-not-archive=true
- **THEN** the predicate matches using that typed value and resolution changes no lifecycle artifacts

#### Scenario: Variable files cannot supply approval
- **WHEN** runtime variables contain a lifecycle preference or returned guidance suggests an outcome
- **THEN** the command remains advisory and does not select, approve, or perform an archive/discard/dissolution/spec-only operation

### Requirement: OpenSpec consumption through native fields

The generated configuration SHALL expose static guidance and runtime-command instructions through the companion OpenSpec instruction commands without a ZPP hook or custom-field consumer. Synchronization SHALL not change OpenSpec artifacts, schema definitions, or change lifecycle state. OpenSpec supplies command instructions as guidance; overspec SHALL NOT claim OpenSpec automatically executes them.

#### Scenario: Read synchronized guidance through OpenSpec
- **WHEN** context, proposal rules, and apply/archive guidance are synchronized in a project using the supported companion OpenSpec CLI
- **THEN** its proposal, apply, and archive instruction outputs expose the corresponding static inputs and runtime commands, and the project's artifact contents and change lifecycle state remain unchanged by synchronization

### Requirement: Live runtime resolution commands

For each nonempty runtime group identified by exact attachment, synchronization SHALL emit exactly one instruction to run `overspec trait resolve --attach <attachment>` with all unique trait names in deterministic order. It SHALL NOT emit a resolution ID, one command per trait, or unconditional runtime bodies. Different attachments SHALL remain separate groups. The group SHALL occupy the first runtime trait's position in that destination's output order. Repeated sync SHALL replace stale names without accumulating commands.

The command SHALL load current effective definitions using the current source/profile selection and existing source precedence. Unknown, removed, duplicate, or moved requested names SHALL fail explicitly rather than use saved definitions. Instructions SHALL direct the caller to run from the owning project root, append --change-root from OpenSpec for the selected change, and supply invocation context when available. Shared config SHALL not embed a selected change's path or values.

Sync SHALL still save the current resolution and receipt together for saved detail inspection. Saved detail lookup SHALL remain bound to current stored literal details without loading live variable files. Runtime SHALL NOT accept --resolution; existing generated commands require sync to remove that option, with no compatibility alias.

#### Scenario: Two runtime traits at the same point
- **WHEN** two runtime traits attach to archive guidance
- **THEN** one command carries each name once without a resolution ID or unconditional body

#### Scenario: Distinct attachment groups
- **WHEN** runtime traits attach to context and archive guidance
- **THEN** each destination contains its own single command with only its names

#### Scenario: Active profile changes after sync
- **WHEN** a profile change replaces a requested runtime trait
- **THEN** the next invocation uses the current effective definition; a missing requested name fails rather than using the old profile

#### Scenario: Grouped source migration needs no sync
- **WHEN** a runtime condition changes from a flat list to nested groups
- **THEN** the next invocation evaluates the current groups without a replacement snapshot

#### Scenario: Change selection remains invocation-specific
- **WHEN** shared config serves several active changes
- **THEN** commands contain no selected change's path or values and request the caller's current scope

#### Scenario: Saved details remain independent
- **WHEN** live sources or variables are invalid during saved detail lookup
- **THEN** lookup still returns saved literal details while runtime lookup reports applicable live input errors

#### Scenario: Removed runtime option
- **WHEN** a caller supplies --resolution to trait resolve
- **THEN** the CLI rejects the option rather than resolving saved runtime definitions
