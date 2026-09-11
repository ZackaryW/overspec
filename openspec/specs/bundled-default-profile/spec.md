# bundled-default-profile Specification

## Purpose

Make the installed Overspec distribution supply its own default trait profile directly, so projects can use maintained default guidance without separately acquiring the Overspec repository.

## Requirements

### Requirement: Single authored default in distributions

The Python distribution SHALL bundle the regular recursive `trait*.toml` documents from this project's `openspec/.over/profile-default` as read-only package content. That directory SHALL remain the single authored source. Building directly from the checkout and building a wheel from its source distribution SHALL yield the same relative trait paths and bytes. Adding a nested eligible trait SHALL not require a second maintained copy or a per-file packaging list. Other profiles, loose repository traits, OpenSpec config/specs/changes, skills, `.vars.toml`, `.current.toml`, generated state, and unrelated files SHALL NOT be included as bundled guidance. A missing authored default, unreadable or redirected eligible sources, or syntactically invalid trait TOML SHALL fail the build instead of silently producing an incomplete default.

#### Scenario: Direct and source-distribution builds
- **WHEN** a release is built directly and again from its source distribution
- **THEN** both wheels contain the same default trait documents as the authored profile, including nested documents

#### Scenario: Local state is not package guidance
- **WHEN** the checkout contains current variables, state, archived changes, another profile, and unrelated files inside default
- **THEN** none of those files appears in the bundled default resource tree

### Requirement: Default available without acquisition

A supported installation SHALL supply profile `default` directly from its own installed content. Default selection SHALL require neither a separate Overspec repository clone nor a Saucepan connection, source registration, download, user profile copy, or project profile directory. Loading SHALL not copy package traits into `~/.overspec` or the workspace, modify package resources, or enable profile mode. Existing init/update/sync and state/variable setup requirements SHALL continue to apply; supplying a profile SHALL not itself run an OpenSpec operation or install a referenced skill.

#### Scenario: Clean consuming project
- **WHEN** an installed package initializes and synchronizes a project containing only a standard OpenSpec structure, with an empty isolated user home and no Saucepan SDK
- **THEN** eligible packaged default guidance is produced without acquiring this repository or creating a profile-default copy; ordinary generated project state and current-variable files may be created by initialization

#### Scenario: Read-only discovery without a local over directory
- **WHEN** a consuming project's `openspec/.over` does not exist and a read-only trait explanation is requested
- **THEN** default discovery succeeds from package content without creating that directory or any user source copy

#### Scenario: Broken installed default
- **WHEN** required bundled content is absent, unreadable, or malformed
- **THEN** loading reports a package-content error before publishing guidance instead of silently returning an empty default or downloading a substitute

### Requirement: Selected profile controls bundled participation

Packaged default SHALL form the lowest source layer when the selected name is `default`, whether implicitly in off mode or explicitly in enabled mode. Other named profiles SHALL use their matching repository and workspace contributors without implicitly inheriting packaged default. An empty higher default profile SHALL add nothing and SHALL NOT erase lower declarations. Missing explicit named selections SHALL remain errors.

#### Scenario: Extension overrides one packaged trait
- **WHEN** packaged default contains `alpha` and `beta` and an acquired profile-default declares a new `beta` and `gamma`
- **THEN** effective default retains packaged `alpha`, uses the extension's complete `beta`, and includes `gamma`

#### Scenario: Named selection is separate
- **WHEN** enabled mode selects an available strict profile
- **THEN** strict contributors and applicable standalone traits are used without default profile declarations leaking into strict

### Requirement: Package provenance and retained lifetimes

Trait explanations and profile contributors SHALL identify the Overspec package, installed version, profile name, and resource-relative origin. Trait identity SHALL remain its short name. Installation directories and temporary extraction paths SHALL NOT determine precedence or compilation compatibility. Effective compile-time declaration or selected-name changes SHALL require update; package version changes, relocated installations, overridden lower declarations, and ordinary/runtime-only changes SHALL NOT alone invalidate otherwise compatible compilation. Source evidence SHALL still detect consumed package content changes during preparation/publication. Saved runtime resolution and details SHALL continue to use retained definitions without loading live package or repository sources.

#### Scenario: Package upgrade changes effective compiled guidance
- **WHEN** the installed package changes an effective compile-time declaration after initialization
- **THEN** sync requires update and does not silently refresh its compilation

#### Scenario: Package relocation or overridden change
- **WHEN** identical package content moves to a different installation path, or an upgrade changes only a fully overridden base declaration
- **THEN** unchanged effective compiled guidance remains compatible while explanations retain the appropriate package provenance

#### Scenario: Saved guidance survives live source changes
- **WHEN** package contents change or external discovery is unavailable after synchronization
- **THEN** the current saved runtime command and detail lookup still use their synchronized definitions until superseded
