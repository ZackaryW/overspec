# maintained-external-skills Specification

## Purpose

Keep the repository's three packaged zmem skills synchronized with an identifiable upstream revision while keeping release builds and installed packages independent of source acquisition.

## Requirements

### Requirement: Fixed upstream skill refresh
The maintenance command SHALL acquire zmem main through Saucepan without an app, marker, token, or registration and synchronize exactly zmem-author-commits, zmem-query-memory, and zmem-design-extensions into .agents/skills. It SHALL preserve recursive regular support files, names, licenses, and relative links. It SHALL remove obsolete files within those owned skill directories and preserve all unrelated skills.

#### Scenario: Complete upstream update
- **WHEN** the acquired revision changes a skill and adds or removes a support file
- **THEN** the corresponding local skill matches the acquired tree, obsolete files are removed, and unrelated skill directories remain unchanged

### Requirement: Validated publication and provenance
The command SHALL validate all three skill trees, required SKILL.md files, and destination confinement before modifying the authored catalog. Missing, redirected, or nonregular payloads SHALL fail before publication. It SHALL record source URL, resolved revision, selected skills, and their file hashes outside the packaged skill trees. Identical content and provenance SHALL be a no-op. Failure during publication SHALL report affected paths and retain recovery information rather than claim a successful refresh.

#### Scenario: Incomplete upstream payload
- **WHEN** acquisition succeeds but one required skill is missing
- **THEN** the command fails and leaves all local skills and the provenance record unchanged

#### Scenario: Repeat the same revision
- **WHEN** source bytes and recorded provenance already match
- **THEN** the command reports unchanged without rewriting local files

### Requirement: Lefthook review behavior
An installed pre-commit hook SHALL run the refresh automatically. If refresh changes files, it SHALL stop the commit and report the paths to review and stage. It SHALL NOT stage unrelated work or create commits. If refresh is unchanged, it SHALL permit the commit. A missing executable, missing initialized store, unsupported unscoped API, or failed refresh SHALL produce a clear nonzero diagnostic without a scoped or direct-Git fallback.

#### Scenario: Upstream skills change before commit
- **WHEN** the hook refreshes different upstream skill content
- **THEN** it leaves the synchronized files for review, stops the current commit, and succeeds on a subsequent unchanged refresh

### Requirement: Acquisition stays outside distribution use
Builds and installed catalog operations SHALL consume the repository snapshot or bundled resources without fetching zmem, invoking Saucepan, or requiring Lefthook. Direct and source-distribution wheels SHALL include the synchronized skills and complete relative support trees.

#### Scenario: Build and use without upstream access
- **WHEN** a synchronized source distribution is built and its wheel is used with upstream access unavailable
- **THEN** the three skills and their support files remain available from package resources without acquisition

### Requirement: Independent maintenance scripts
All skill-refresh implementation and its helpers SHALL reside under scripts/, with independently declared dependencies and focused tests. The command SHALL run without installing or importing Overspec, reading its application configuration, or using its root project environment. Lefthook SHALL invoke the independent script directly. The target repository SHALL be treated as a filesystem destination.

#### Scenario: Run without the application
- **WHEN** the scripts project runs in an isolated environment where Overspec is not installed, against a repository containing only the required target structure
- **THEN** skill synchronization succeeds through its own dependencies without importing Overspec or resolving its application environment
