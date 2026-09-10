# overspec-bootstrap Specification

## Purpose

Give agents a concise, reusable entry point for understanding and initializing Overspec projects while preserving explicit scope and lifecycle decisions.

## Requirements

### Requirement: Discoverable bootstrap skill

The repository SHALL provide `.agents/skills/overspec-bootstrap/SKILL.md` describing
when to use it and explaining profiles, trait lifetimes, attachments, compact bodies,
optional details, variable scopes, and setup versus compilation versus sync.
Longer examples SHALL be placed in a linked reference. Instructions SHALL use
implemented public commands and distinguish unavailable functionality explicitly.

#### Scenario: Agent starts an unfamiliar project
- **WHEN** the bootstrap skill is invoked
- **THEN** it directs the agent to inspect current CLI capabilities, OpenSpec roots, profile mode, sources, and saved state before choosing setup actions

### Requirement: Setup through supported commands

The skill SHALL direct first-time setup through init, missing-file/new-change setup
through setup-only, incompatible compilation through explicit update, and guidance
changes through preview/sync within the user's scope. It SHALL preserve OpenSpec's
selected store and reported change roots, avoid enabling profile mode just to use
default, and explain variable precedence and the tracked/ignored file distinction.

#### Scenario: Existing default project
- **WHEN** compilation exists and only a new change's current file is missing
- **THEN** bootstrap selects setup-only for the resolved change root without toggling profiles or refreshing compilation

#### Scenario: Persistent configuration
- **WHEN** the user wants a shared default
- **THEN** bootstrap identifies the appropriate optional .vars.toml and explains that .current.toml overrides are local and ignored

### Requirement: Referenced skills remain authoritative

Bootstrap SHALL reference `create-overspec-trait` for trait authoring and
`zmem-author-commits` for commit memory, leaving their procedures in those skills.
It SHALL report missing dependencies without inventing installation or execution.

#### Scenario: Trait authoring requested during setup
- **WHEN** setup includes adding reusable guidance
- **THEN** bootstrap delegates to create-overspec-trait instead of reproducing the trait schema and validation procedure in its main workflow

### Requirement: Explicit final change outcome

Bootstrap SHALL distinguish incremental implementation commits, which exclude
only the active change's own changeRoot artifacts, from final outcome commits.
Incremental commits SHALL include other nonignored work, including .over trait
and config files, openspec/config.yaml, tests, skills, canonical specs, and
previously archived records. On an archive operation
it SHALL present discard, archive normally, dissolve into zmem, and only form specs
with concrete effects and await the user's answer. Files SHALL not supply consent.
An existing answer for that same operation SHALL not be requested again. Retained
canonical specs, archive records, and authored vars files SHALL be included as
appropriate to the chosen outcome; current files SHALL stay ignored. Unrelated
implementation, changes, and specs SHALL be preserved.

#### Scenario: Stored archive preference
- **WHEN** a variable file contains an archive outcome preference but the user has not selected an outcome for this operation
- **THEN** bootstrap still asks explicitly before changing lifecycle artifacts

#### Scenario: Normal archive selected
- **WHEN** the user chooses normal archive
- **THEN** bootstrap retains synchronized specs and archive records for the final commit instead of applying the incremental exclusion indefinitely

#### Scenario: Dissolve without zmem
- **WHEN** the user selects dissolution but zmem or its authoring skill is unavailable
- **THEN** bootstrap reports the limitation and preserves records until the user chooses how to proceed
