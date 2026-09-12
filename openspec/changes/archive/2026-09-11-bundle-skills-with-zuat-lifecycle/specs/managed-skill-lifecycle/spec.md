## Purpose

Manage explicit user-level installation of packaged skills with observable ownership, recoverable content changes, and narrowly scoped restoration.

## ADDED Requirements

### Requirement: Explicit user-level skill commands

Overspec SHALL expose skill list, status, install, update, history, restore, and remove commands. Lifecycle commands SHALL require explicit agent selection and support individual named skills or explicit all-skills selection; restore SHALL additionally require an operation ID. Native targets SHALL be user-scoped and independent of the working project and trait profile mode. The selected Overspec home SHALL determine a dedicated registry; an explicit agent-home option SHALL independently select the native home. Package installation, imports, trait discovery, and existing project init/update/sync SHALL not install or modify native skills.

#### Scenario: Explicit first install
- **WHEN** a user selects an agent and all packaged skills for installation from a directory without OpenSpec
- **THEN** supported skills install into the selected native user home with recoverable operation identifiers and no workspace skill copies

#### Scenario: Project operations stay passive
- **WHEN** existing project initialization or synchronization runs
- **THEN** no native skill is installed, updated, removed, or restored

### Requirement: Ownership-aware reconciliation

Status SHALL distinguish absent, current, outdated, conflicting, unowned, unsupported, and indeterminate targets using source and ownership evidence. Install SHALL address absent targets and report existing targets without silently replacing them. Update SHALL replace outdated owned targets and preserve current targets as no-ops. Conflict or unowned replacement SHALL require an explicit force request supported by the provider; force SHALL not bypass invalid identities, invalid receipts, or provider boundaries. Remove SHALL target only explicitly selected, verified managed skills. An operation SHALL never broadly adopt or remove unrelated agent skills.

#### Scenario: Existing unrelated OpenSpec installation
- **WHEN** an openspec-* skill already exists without ownership by this integration
- **THEN** install reports the collision without mutation and update requires explicit force before any supported replacement

#### Scenario: Local edits after installation
- **WHEN** an installed managed skill has user edits and update runs without force
- **THEN** the command reports a conflict and preserves the user's bytes

#### Scenario: Current catalog is unchanged
- **WHEN** installed owned bytes already match the supplied package content
- **THEN** update reports unchanged without creating a content-change event

### Requirement: Recoverable operations with exact scope

History SHALL expose skill operation identifiers and affected native identities sufficient to select a prior operation. Restore SHALL recover supported pre-operation content and ownership from retained history after reopening, including content explicitly replaced during a forced update. Restoration SHALL not require the previous Python package version or source checkout. It SHALL restrict targets to selected agent/user-home skill identities recorded by this integration, including historical skills no longer in the current catalog, and shall reject unknown or unrelated operations. Later local edits SHALL require explicit force before overwrite. Restoration SHALL append a new transition rather than reset Git history.

#### Scenario: Undo update after restart
- **WHEN** a skill is updated from A to B, the process restarts, and its operation is restored
- **THEN** A's exact body and support bytes and prior ownership return, with B's operation retained in history

#### Scenario: Restore explicitly replaced foreign content
- **WHEN** a supported forced update replaced unowned content and the user restores that operation
- **THEN** its original bytes and original ownership state return rather than being relabeled as package-owned

#### Scenario: Recovery after a skill leaves the package
- **WHEN** the current catalog no longer contains a skill affected by a retained operation
- **THEN** explicitly selected restoration can use the recorded identity and snapshot without finding that skill in the current package

#### Scenario: Unrelated history and later edits
- **WHEN** a caller selects an unrelated operation or restoration would overwrite later unapproved edits
- **THEN** restoration fails with a scope or conflict diagnostic and preserves those targets

### Requirement: Observable partial outcomes

Human output SHALL identify targets, classifications, changes, operation IDs, and recovery guidance. JSON SHALL expose those results without terminal styling. Unsupported agents or scopes, unavailable providers, partial failures, and indeterminate recovery SHALL return non-success without claiming an atomic multi-skill or multi-agent transaction. Retained recovery evidence SHALL survive failures. Inspection and history SHALL not mutate native skills; restoring or retrying SHALL always be an explicit action.

#### Scenario: One selected target fails
- **WHEN** one skill succeeds and another fails during a selected operation
- **THEN** results distinguish both outcomes, retain available recovery identifiers, and return non-success without claiming all targets rolled back
