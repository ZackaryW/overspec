## MODIFIED Requirements

### Requirement: Profile and local trait discovery

Overspec SHALL recognize immediate `profile-<nonempty-name>` directories under the project's `openspec/.over/` and configured user home as profile sources, and external profile candidates defined by saucepan-source-discovery. With profile mode off, it SHALL resolve only default profile declarations; with mode on, named-profile discovery and selection SHALL be available. External standalone traits SHALL participate in either mode. Trait discovery SHALL include regular TOML files whose basenames begin with `trait`, at any depth under the effective profile, the project's `.over/`, or the user home's standalone layer. Standalone scans SHALL exclude every profile subtree, including inactive profiles, and internal generated-state directories. Discovery SHALL not require a repository-specific source-list manifest, follow redirected directories outside its roots, or load one physical file twice within a layer. Paths SHALL be ordered deterministically by normalized relative path, then declarations by file order within each trait type. External repository discovery SHALL use its independent top-level-first category selection and source priority.

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
legacy remote state SHALL use the chosen user home. The Saucepan connection and
source priority SHALL also belong to that home; acquired content SHALL remain
in Saucepan-managed storage accessed through its public API. Overspec SHALL NOT implicitly read,
write, or migrate `~/.over`; project sources and resolution state SHALL remain
under `openspec/.over/`.

Profile mode SHALL be off when no enabled state has been persisted in the chosen user home. In off mode, composition SHALL use default automatically, with project `profile-default` overriding the user default, which overrides external default candidates, each as a complete profile source. External, user, and project standalone traits SHALL then apply in their defined layer order. It SHALL ignore named-profile environment and saved-user selections. Unrelated named profiles SHALL neither contribute nor force a selection error, and their source contents SHALL not be loaded or validated. With no default source, standalone-only operation SHALL remain available, including local-only operation when there are no external sources. Profile mode SHALL control access to named selection and management, not whether ordinary composition works.

`overspec profile activate` SHALL accept no profile name and SHALL toggle the persisted user-level mode, reporting its resulting state. It SHALL preserve any saved selection and unrelated user settings. Toggling SHALL not implicitly compile, synchronize configuration, fetch profiles, or delete sources or saved resolutions. Turning mode off SHALL restore default resolution even while a named environment selection remains set; turning it back on SHALL make that selection applicable again.

#### Scenario: User home avoids another application's files
- **WHEN** both ~/.overspec and ~/.over exist without a user-home override
- **THEN** overspec uses profiles and activation from ~/.overspec and leaves ~/.over untouched

#### Scenario: Ordinary project needs no activation
- **WHEN** mode is off and both user and project default profiles exist
- **THEN** composition uses the project default and loose local overrides without enabling profile management

#### Scenario: Dormant selection does not change default behavior
- **WHEN** mode is off, a saved or environment selection names strict, and a non-default profile contains malformed trait data
- **THEN** composition uses only default plus applicable standalone traits and does not validate or activate that unrelated profile

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

While mode is on, Overspec SHALL select one profile using `OVERSPEC_PROFILE`, then the saved user-level selection, then implicit default. An explicitly provided empty, invalid, or missing selection SHALL fail without falling back. An absent implicit default SHALL allow standalone-only composition, including local-only composition when there are no external sources. `profile use NAME` SHALL save a user-level selection only while mode is enabled and SHALL report when an environment selection overrides it. Environment selection SHALL not persist itself or turn mode on. External profiles SHALL participate in the named catalog using saucepan-source-discovery priority. A user profile SHALL override a same-name external profile, and a project profile SHALL continue to shadow both completely; activation SHALL not pin profile sources or suppress local overrides.

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

### Requirement: Profile-independent identity and local overrides

Overspec SHALL resolve identities across all three trait types by name. It SHALL apply complete declarations from lowest to highest priority: the effective selected profile, external standalone source layers in their configured order, the user-authored standalone layer, then the project-local standalone layer. A later layer's same-name trait SHALL replace the entire earlier declaration before reference validation and evaluation; no assertions, actions, body, details, phase, or attachment SHALL be inherited implicitly. Duplicates within the selected profile, within one external repository's standalone layer, or within either authored standalone layer SHALL fail with both origins. Surviving names SHALL be unique regardless of type or attachment. Overrides SHALL retain the inherited name's insertion position before the stable phase ordering; additional names SHALL follow earlier-layer names within their phase. Diagnostics SHALL retain file/profile origins and external source/revision provenance for winners and overridden declarations even though emitted identity is name-only.

#### Scenario: Override a profile trait locally
- **WHEN** a profile and a local file both declare `require-codegraph`
- **THEN** the local declaration wins completely and only one trait with that name remains

#### Scenario: Collision across trait types
- **WHEN** two local files reuse one name across a trait and a runtime trait
- **THEN** resolution fails rather than treating the names as separate namespaces

#### Scenario: Complete override removes inherited elaboration
- **WHEN** a local override omits details that existed in its profile declaration
- **THEN** the effective local declaration has no details rather than inheriting the profile's explanation
