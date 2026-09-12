## MODIFIED Requirements

### Requirement: Explicit user-level skill commands

Overspec SHALL expose skill list, status, install, update, history, restore, and remove commands. Lifecycle commands SHALL require agent and skill selection through explicit options or confirmed interactive checklists, supporting individual named skills or explicit all-skills selection; restore SHALL additionally require an operation ID. Native targets SHALL be user-scoped and independent of the working project and trait profile mode. The selected Overspec home SHALL determine a dedicated registry; an explicit agent-home option SHALL independently select the native home. Package installation, imports, trait discovery, and existing project init/update/sync SHALL not install or modify native skills.

#### Scenario: Explicit first install
- **WHEN** a user selects an agent and all packaged skills for installation from a directory without OpenSpec
- **THEN** supported skills install into the selected native user home with recoverable operation identifiers and no workspace skill copies

#### Scenario: Project operations stay passive
- **WHEN** existing project initialization or synchronization runs
- **THEN** no native skill is installed, updated, removed, or restored

#### Scenario: Interactive selection
- **WHEN** a lifecycle command omits agent or skill selections in an interactive terminal
- **THEN** required checklists collect the omitted selections before native mutation, using packaged names for catalog operations and recorded names for history/removal/restoration; restore choices are limited to its supplied operation ID

#### Scenario: Cancellation or noninteractive input
- **WHEN** the user cancels a selection, or JSON/noninteractive execution lacks required selections
- **THEN** cancellation exits without native mutation and JSON/noninteractive execution reports missing explicit selections without opening a prompt

### Requirement: Ownership-aware reconciliation

Status SHALL distinguish absent, current, outdated, conflicting, unowned, unsupported, and indeterminate targets using source and ownership evidence. Install SHALL install absent selected targets and reconcile existing selected targets to the packaged content. Install and update SHALL automatically replace differing supported existing content, including unowned and locally edited skills, and preserve current managed targets as no-ops. The explicit agent and skill selection SHALL authorize this reconciliation without a separate force switch. Neither command SHALL expose a force option. Replacement SHALL retain recoverable content and ownership evidence and SHALL not bypass invalid identities, invalid receipts, or provider boundaries. Update SHALL retain its existing-target scope. Remove SHALL target only explicitly selected, verified managed skills. An operation SHALL never broadly adopt or remove unrelated agent skills.

#### Scenario: Existing unrelated OpenSpec installation
- **WHEN** an openspec-* skill already exists without ownership by this integration
- **THEN** install or update replaces supported differing content and retains its original bytes and ownership for restoration

#### Scenario: Local edits after installation
- **WHEN** an installed managed skill has user edits and install or update runs
- **THEN** the command replaces differing content with the package version and records the prior edited content for restoration

#### Scenario: Current catalog is unchanged
- **WHEN** installed owned bytes already match the supplied package content
- **THEN** install or update reports unchanged without creating a content-change event

### Requirement: Recoverable operations with exact scope

History SHALL expose skill operation identifiers and affected native identities sufficient to select a prior operation. Restore SHALL recover supported pre-operation content and ownership from retained history after reopening, including content replaced automatically during a selected install or update. Restoration SHALL not require the previous Python package version or source checkout. It SHALL restrict targets to selected agent/user-home skill identities recorded by this integration, including historical skills no longer in the current catalog, and shall reject unknown or unrelated operations. Later local edits SHALL require explicit force before overwrite. Restoration SHALL append a new transition rather than reset Git history.

#### Scenario: Undo update after restart
- **WHEN** a skill is updated from A to B, the process restarts, and its operation is restored
- **THEN** A's exact body and support bytes and prior ownership return, with B's operation retained in history

#### Scenario: Restore explicitly replaced foreign content
- **WHEN** a supported install or update replaced unowned content and the user restores that operation
- **THEN** its original bytes and original ownership state return rather than being relabeled as package-owned

#### Scenario: Recovery after a skill leaves the package
- **WHEN** the current catalog no longer contains a skill affected by a retained operation
- **THEN** explicitly selected restoration can use the recorded identity and snapshot without finding that skill in the current package

#### Scenario: Unrelated history and later edits
- **WHEN** a caller selects an unrelated operation or restoration would overwrite later unapproved edits
- **THEN** restoration fails with a scope or conflict diagnostic and preserves those targets
