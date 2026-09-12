# configurable-workflow-traits Specification

## Purpose

Provide small reusable workflow policies through existing trait declarations and scoped variable controls without expanding runtime machinery.

## Requirements

### Requirement: Compact configurable guidance

The default profile SHALL provide compact utility, integration-test, consultation, prototype, evidence, and independently selected BDD policies with separate literal details. Each migrated policy SHALL have an explicit off control: project-wide policies use a compiled setting gate; change-scoped BDD traits retain their runtime typed-false control. Paired stage declarations SHALL share the relevant policy control.

#### Scenario: Disable a policy
- **WHEN** an effective policy control is boolean false
- **THEN** its guidance is absent at that policy's publication/evaluation time without disabling independent policies

### Requirement: Existing activation contracts

BDD guidance SHALL use the existing runtime-context-includes assertion to select behave, cucumber, or flutter from the bdd list. Empty or absent selection SHALL emit no framework guidance. Individual false controls SHALL take precedence. This migration SHALL retain existing assertion semantics rather than add manifest detectors or framework-specific validation.

#### Scenario: Independently selected frameworks
- **WHEN** bdd contains behave and cucumber and bdd-behave=false
- **THEN** only Cucumber guidance is emitted from those framework traits

### Requirement: Native attachment reuse

Policies SHALL use existing context, artifact rules, and apply/archive guidance destinations. Exploration consultation SHALL be described as exploration-only guidance in shared context; proposal consultation SHALL use proposal rules. Decisions SHALL wait for explicit answers, preserving settled choices. Prototype guidance SHALL allow an evidence-backed not-needed determination.

#### Scenario: No new operation endpoint
- **WHEN** consultation traits are synchronized
- **THEN** their guidance uses supported context/proposal fields without a new native command or attachment
