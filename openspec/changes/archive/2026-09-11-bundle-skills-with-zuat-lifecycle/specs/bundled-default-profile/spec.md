## MODIFIED Requirements

### Requirement: Single authored default in distributions

The Python distribution SHALL bundle the regular recursive `trait*.toml` documents from this project's `openspec/.over/profile-default` as read-only package content. That directory SHALL remain the single authored source. Building directly from the checkout and building a wheel from its source distribution SHALL yield the same relative trait paths and bytes. Adding a nested eligible trait SHALL not require a second maintained copy or a per-file packaging list. Other profiles, loose repository traits, OpenSpec config/specs/changes, skills, `.vars.toml`, `.current.toml`, generated state, and unrelated files SHALL NOT be included in the bundled default trait resource tree. Skills SHALL be separately packaged under the packaged-agent-skills contract; their presence SHALL not change trait discovery or implicitly install referenced skills. A missing authored default, unreadable or redirected eligible sources, or syntactically invalid trait TOML SHALL fail the build instead of silently producing an incomplete default.

#### Scenario: Direct and source-distribution builds
- **WHEN** a release is built directly and again from its source distribution
- **THEN** both wheels contain the same default trait documents as the authored profile, including nested documents

#### Scenario: Local state is not package guidance
- **WHEN** the checkout contains current variables, state, archived changes, another profile, and unrelated files inside default
- **THEN** none of those files appears in the bundled default resource tree

## ADDED Requirements

### Requirement: Bundled companion schema and templates

The distribution SHALL additionally package the authored `openspec/schemas/overspec` schema and its referenced templates as separate read-only resources. Direct and source-distribution wheels SHALL preserve identical relative paths and bytes. Missing required files, invalid schema YAML, missing referenced templates, unreadable payloads, and redirected sources SHALL fail packaging. Installed access SHALL work without the source checkout or remote acquisition, and SHALL not use the caller's working directory as the package source.

#### Scenario: Complete release workflow assets
- **WHEN** a wheel is built directly and rebuilt from its source distribution
- **THEN** both contain the same overspec schema and all referenced templates outside the trait and skill resource trees

### Requirement: Project schema installation and refresh

Normal project init SHALL install the packaged schema and templates into the owning project's `openspec/schemas/overspec` before change discovery that might require that schema. Existing-compilation refusal SHALL occur before installation writes. Project update SHALL refresh the installed schema using its recorded baseline while retaining its compilation-refresh responsibility. Setup-only, sync, trait resolution, and user-level skill operations SHALL not install or refresh project schema files. Schema installation SHALL preserve config.yaml's existing schema selection, other schema directories, and active change metadata. A selected external planning store SHALL not redirect schema writes away from the explicit owning project.

#### Scenario: First initialization with a missing schema
- **WHEN** a project with existing OpenSpec configuration but no local overspec schema runs normal init
- **THEN** it receives the packaged schema and templates before any schema-dependent change discovery, without cloning this repository

#### Scenario: Preserve selected workflows
- **WHEN** the project's selected schema is another name or an active change has its own schema
- **THEN** installing overspec makes it available without changing those selections and reports how to select it explicitly

#### Scenario: Existing compilation and variable-only setup
- **WHEN** normal init encounters existing compilation or setup-only is requested
- **THEN** normal init refuses before schema writes and setup-only retains its variable/ignore setup scope

### Requirement: Protect local schema edits

Schema publication SHALL validate and preflight all affected targets before writing. A missing tree SHALL be installable; an existing tree identical to the packaged payload MAY establish a reported baseline without rewriting its files. Without a baseline, differing existing content SHALL cause a conflict rather than implicit adoption. With a baseline, update SHALL change or remove only previously managed files whose bytes still match that baseline, install nonconflicting new files, and preserve unrelated additions. Modified or missing previously managed files and collisions SHALL report a conflict before publication. Repeated equivalent updates SHALL preserve schema file bytes and modification times.

#### Scenario: Package schema upgrade
- **WHEN** packaged templates change and installed managed files still match their baseline
- **THEN** update installs the new payload and records its current baseline without touching unrelated files

#### Scenario: Locally customized template
- **WHEN** a managed template was edited or a differing schema exists without a baseline
- **THEN** init/update reports the conflicting paths and preserves the tree instead of overwriting the customization

### Requirement: Current schema installation evidence

The project SHALL retain only the current schema installation baseline in the same ignored `.over/.state.json` document as compilation and synchronization state. Baseline evidence SHALL bind the owning root, schema identity, and managed relative paths/content fingerprints. Other state publications SHALL preserve that evidence; schema publication SHALL preserve retained compilation and sync sections until their respective operations update them. Invalid or mismatched evidence SHALL fail explicitly. Detectable source/target races SHALL abort publication. Schema or receipt failures SHALL report affected paths and a non-success partial outcome without claiming a transaction across schema files, variable setup, and compilation. Skill restoration SHALL not be presented as schema restoration; schema customizations remain ordinary project files suitable for version control.

#### Scenario: Sync preserves the schema baseline
- **WHEN** trait synchronization replaces the current resolution
- **THEN** schema installation evidence remains in the same state file without creating per-generation manifests

#### Scenario: Failure after schema publication
- **WHEN** schema files were published but later baseline, setup, or compilation work fails
- **THEN** the command identifies the completed and failed work, retains usable evidence, and gives explicit repair guidance rather than reporting full initialization success
