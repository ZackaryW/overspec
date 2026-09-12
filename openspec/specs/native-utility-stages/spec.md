# native-utility-stages Specification

## Purpose

Make utility assessment proportionate to accepted change scope through existing native stage configuration and a referenced procedure.

## Requirements

### Requirement: Assess before planning implementation

Utility planning SHALL first assess whether the accepted change needs new assertions, actions, or utilities. Existing models, handlers, and dependency APIs SHALL be considered before proposing source work. If guidance can be expressed using existing capabilities, the assessment SHALL conclude no implementation is needed.

#### Scenario: Trait-only migration
- **WHEN** existing assertions, actions, conditions, variables, and attachments express the requested traits
- **THEN** the assessment records no new assertions, actions, or utilities and RED/GREEN is not applicable

### Requirement: Conditional utility maturation

Native design/tasks configuration MAY reference overspec-utilities using existing instruction delegation. Only an accepted plan with actual missing utility behavior SHALL trigger utility RED, implementation, and GREEN. A no-work assessment SHALL finish without fabricated source changes, tests, or demonstrations. Propose SHALL remain planning-only; application wiring SHALL remain for apply.

#### Scenario: No utility work
- **WHEN** the accepted assessment concludes no utilities are needed
- **THEN** the procedure returns that assessment and validates the trait artifacts proportionately

#### Scenario: Future accepted utility need
- **WHEN** a separately accepted utility contract has missing implementation behavior
- **THEN** utility maturation observes an intended failing test before implementation and passing verification afterward
