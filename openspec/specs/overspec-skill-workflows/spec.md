# overspec-skill-workflows Specification

## Purpose

Provide discoverable, task-focused skills that guide users through Overspec authoring, configuration, synchronization, and diagnosis with the correct lifetimes.

## Requirements

### Requirement: Consistent Overspec skill names

Overspec-owned skills under .agents/skills SHALL use the overspec- prefix. Trait authoring SHALL be named overspec-create-trait without a legacy alias; native openspec-* workflow skills SHALL keep their existing names. Active references SHALL point to available skills.

#### Scenario: Find trait authoring
- **WHEN** an agent needs to author a trait
- **THEN** overspec-create-trait explains lifetime selection, setting gates, body/details, scope, and proportional validation

### Requirement: Focused operational skills

The repository SHALL provide overspec-sync, overspec-configure, and overspec-diagnose alongside bootstrap and utilities. They SHALL use real current CLI contracts, preserve selected project/home/store scopes, distinguish live runtime evaluation from compiled setting publication, and explain the next valid action. Diagnosis SHALL be read-only unless repair is requested. Skill use SHALL not implicitly activate profile management, fetch remote sources, or select an archive disposition.

#### Scenario: Toggle a project policy
- **WHEN** overspec-configure handles disabling a compiled policy
- **THEN** it writes a typed project setting in the requested scope and uses sync without unnecessary update

#### Scenario: Diagnose missing guidance
- **WHEN** overspec-diagnose inspects a missing policy
- **THEN** it distinguishes source precedence, retained eligibility, setting suppression, and runtime invocation inputs without mutating state

#### Scenario: Synchronize guidance
- **WHEN** overspec-sync applies a requested sync
- **THEN** it reviews a preview, uses update only for compiled changes, applies the output, and verifies no-op repetition
