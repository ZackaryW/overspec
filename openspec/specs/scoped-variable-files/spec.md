# scoped-variable-files Specification

## Purpose

Provide persistent project/change defaults and local temporary variable state with explicit precedence, repeatable initialization, and isolated runtime evaluation.

## Requirements

### Requirement: Persistent and temporary variable documents

Overspec SHALL read optional `.vars.toml` and `.current.toml` from the project's
`openspec/.over/` and from an explicitly selected OpenSpec change root. Documents
SHALL contain only an optional `[vars]` table with literal keys and scalar or
scalar-list values. Scalars SHALL be strings, booleans, integers, or finite floats.
Missing files and empty documents SHALL contribute an empty layer. Malformed TOML,
unknown top-level keys, dates/times, nested mappings/lists, and invalid values SHALL
fail with source/key diagnostics. `.vars.toml` SHALL be persistent, optional, and
eligible for Git tracking; `.current.toml` SHALL be local temporary state.

#### Scenario: Optional files are absent
- **WHEN** neither variable file exists in an applicable scope
- **THEN** resolution uses the remaining layers without creating files

#### Scenario: Typed values and literal keys
- **WHEN** a vars table contains a boolean, a string list, and a quoted dotted key
- **THEN** their types and literal keys are preserved rather than stringified or traversed as paths

#### Scenario: Invalid document
- **WHEN** a file contains malformed TOML, a date, or a nested vars table
- **THEN** resolution fails with the file and relevant key identified

### Requirement: Project variable precedence and lifetimes

Static evaluation SHALL use explicit invocation variables over project current
variables, project persistent variables, project config variables, and user config
variables, in that order. A higher layer SHALL replace the entire same-name value,
including lists. Existing JSON null inputs SHALL remain supported. Change-level
files SHALL NOT influence shared init/update/sync evaluation. Compile-time values
SHALL remain frozen until update, with changed effective inputs used by compiled
bodies requiring update. Unrelated variable edits SHALL not invalidate compilation.
Ordinary evaluation SHALL read current project layers at sync.

#### Scenario: Explicit project override
- **WHEN** all project layers define language and an invocation supplies its own language
- **THEN** the invocation value wins; without it project current wins over persistent and configured defaults

#### Scenario: Whole-list override
- **WHEN** a lower layer contains two list entries and a higher layer contains one
- **THEN** the effective list has only the higher layer's entry

#### Scenario: Compiled key changes
- **WHEN** a project variable used by a compiled body changes after init
- **THEN** sync requires update, while an unrelated variable change alone does not

#### Scenario: Shared sync ignores change files
- **WHEN** two active changes have conflicting variables
- **THEN** shared sync uses only project layers and neither change alters the other's inputs

### Requirement: Fresh selected-change runtime layers

For newly synchronized resolutions, effective runtime variables SHALL use explicit
context JSON over selected-change current variables, selected-change persistent
variables, project current variables, project persistent variables, and retained
configured defaults, in that order. All file layers SHALL be read afresh per
invocation and shared by runtime assertions and body rendering. Missing or removed
file layers SHALL not revive their previously captured values. Live profile
selection and user/project config edits SHALL not replace retained defaults.

#### Scenario: Change specificity beats project defaults
- **WHEN** project current specifies strict=false and selected-change persistent specifies strict=true
- **THEN** strict=true reaches both runtime matching and body rendering

#### Scenario: Explicit context overrides a change
- **WHEN** selected-change current specifies strict=true but context JSON specifies strict=false
- **THEN** both matching and rendering use strict=false

#### Scenario: Removing a temporary override
- **WHEN** a current file is removed between runtime invocations
- **THEN** the next invocation uses the next remaining layer without reusing the deleted override

#### Scenario: No cross-invocation leakage
- **WHEN** a later invocation selects another change or supplies no explicit context
- **THEN** it uses only that invocation's applicable layers and never reuses the earlier context or change selection

### Requirement: Explicit OpenSpec change scope

Runtime resolution SHALL accept one `--change-root PATH` identifying an existing
nonredirected change directory with OpenSpec metadata. Callers SHALL obtain its path
from OpenSpec's selected planning root rather than constructing a project-local
path. Explicit external store roots SHALL be supported without changing the owning
Overspec project's identity. With no selected change, only project/default layers
SHALL apply. A missing or invalid explicit root SHALL fail rather than falling back.

#### Scenario: Two active changes
- **WHEN** the same saved runtime command is called with two different change roots
- **THEN** each reads only its selected change files and the shared project layers

#### Scenario: External planning store
- **WHEN** OpenSpec returns an explicitly selected store's change root outside the implementation repository
- **THEN** its change files layer over the owning project's files without selecting a different Overspec profile or bundle root

#### Scenario: Moved change root
- **WHEN** an explicit change root no longer exists after an archive move
- **THEN** resolution fails and requires the caller to provide the correct root

### Requirement: Non-destructive current-file initialization

Normal init SHALL initialize missing project and active-change current files before
publishing a new compilation. `init --setup-only` SHALL perform the same variable
setup without compiling, syncing, fetching profiles, or changing profile mode and
SHALL work when compilation already exists. Normal init's existing-compilation
refusal SHALL occur before setup writes. Existing valid files SHALL retain their
contents and modification times, including under concurrent creation. Setup SHALL
never automatically create `.vars.toml` or alter existing variable values.

#### Scenario: First project setup
- **WHEN** init runs on an uncompiled project with active changes and missing current files
- **THEN** it creates project and active-change current files containing an empty vars table and leaves persistent files absent

#### Scenario: Repeated setup
- **WHEN** setup-only runs again after current values have been edited
- **THEN** it preserves those bytes and times and does not change compilation or generated config

#### Scenario: Concurrent creation
- **WHEN** another writer creates a current file after absence was observed
- **THEN** setup preserves that file rather than overwriting it

#### Scenario: Invalid existing current file
- **WHEN** setup encounters malformed current TOML or a redirected target
- **THEN** it reports the error without replacing that target

### Requirement: Setup follows OpenSpec discovery and explicit scope

Without explicit change roots, setup SHALL discover active changes through the
companion OpenSpec list/status outputs, preserving selected planning-root context.
`init --store ID` SHALL scope discovery to that store. Repeatable `--change-root`
SHALL instead set exact setup targets and SHALL be mutually exclusive with --store.
Project current state SHALL always be included. Discovery failures SHALL be errors,
not empty inventories. Setup SHALL not initialize archived changes by default.

#### Scenario: New change after project init
- **WHEN** bootstrap receives the new change's resolved root and runs setup-only with that root
- **THEN** the new current file is created without refreshing the existing compilation

#### Scenario: Archived changes are excluded
- **WHEN** OpenSpec lists active and archived records separately
- **THEN** default setup touches only active roots and project current state

#### Scenario: Discovery failure
- **WHEN** the companion CLI fails or returns invalid discovery JSON
- **THEN** setup reports failure before treating discovery as successful or publishing compilation

### Requirement: Git-ignore coverage preserves shared variables

In each containing Git worktree, setup SHALL establish and verify effective ignore
coverage for selected `.current.toml` paths using the basename pattern
`.current.toml` only when coverage is missing. Existing effective coverage SHALL
avoid duplicate additions and rewrites. A missing root .gitignore SHALL be created
when necessary. `.vars.toml` SHALL not receive an automatically added ignore rule.
Existing ignore content SHALL be preserved; stale plans or ineffective writes SHALL
fail without losing original ignore bytes. Setup SHALL not untrack files implicitly.

#### Scenario: Existing coverage
- **WHEN** Git already ignores every selected current path
- **THEN** setup leaves .gitignore bytes and modification time unchanged

#### Scenario: Missing ignore file
- **WHEN** a Git worktree has no .gitignore and a selected current path lacks coverage
- **THEN** setup creates .gitignore with effective current-file coverage while leaving vars files eligible for tracking

#### Scenario: Separate store worktree
- **WHEN** the project and selected change belong to different Git worktrees
- **THEN** setup establishes current-file coverage in both worktrees independently

#### Scenario: Tracked current or ignored persistent file
- **WHEN** a current file is already tracked or existing user rules ignore an authored vars file
- **THEN** setup reports the condition without staging removals or rewriting the user's exclusion policy

#### Scenario: Non-Git root
- **WHEN** a setup target is outside a Git worktree
- **THEN** current-file setup remains available and reports ignore coverage as unavailable without creating a Git repository

### Requirement: Read-only resolution and observable partial setup

Runtime resolve, static resolve, and sync preview SHALL never create variable files
or update ignore rules. Project file additions, removals, and content changes during
compilation/sync publication SHALL be rechecked and abort inconsistent publication.
Setup SHALL report created, preserved, and failed targets plus ignore status. A
partial setup failure SHALL return non-success and allow a retry without deleting
existing files or claiming a multi-root transaction.

#### Scenario: Preview with missing files
- **WHEN** a preview resolves a project with no variable files
- **THEN** neither current files nor ignore rules are created

#### Scenario: Variable source changes during sync
- **WHEN** a project variable file appears, disappears, or changes after preparation and before publication
- **THEN** publication aborts rather than committing guidance from inconsistent inputs

#### Scenario: Partial setup can be retried
- **WHEN** one target fails after another was created successfully
- **THEN** setup identifies both outcomes and a retry preserves the completed target
