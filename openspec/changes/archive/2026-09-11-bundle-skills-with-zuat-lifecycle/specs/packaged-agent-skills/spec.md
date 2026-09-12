## Purpose

Deliver the maintained agent skills and their support files with Overspec so installed tools can supply complete workflows without a separate checkout.

## ADDED Requirements

### Requirement: Single authored skill catalog

The distribution SHALL include immediate skill directories from `.agents/skills` that contain `SKILL.md`, preserving each skill's recursive regular support files and relative paths. Both openspec-* and overspec-* skills SHALL participate without renaming. The authored tree SHALL remain the only maintained copy. Wheels built directly and from the source distribution SHALL contain identical skill paths and bytes in a resource tree separate from bundled traits. Reports, caches, repository metadata, generated state, and files outside selected skill directories SHALL be excluded. Missing or unreadable required skill files, redirected paths, and nonregular payloads SHALL fail packaging rather than yield partial assets.

#### Scenario: References survive release packaging
- **WHEN** a skill contains SKILL.md, references, and agents/openai.yaml
- **THEN** direct and source-distribution wheels preserve all those regular payload files at the same skill-relative paths

#### Scenario: Unrelated repository files
- **WHEN** the source tree also contains .agents/reports, .openspec-target, caches, and generated project state
- **THEN** those files are absent from the skill resource tree

### Requirement: Installed catalog access and provenance

Catalog access SHALL use the imported distribution's resources, identify package version and skill-relative origins, and work outside the source checkout. Editable development SHALL use its verified authored skill tree rather than the caller's working directory. A missing or incomplete installed catalog SHALL report a package error without silently fetching a substitute. Source materialization needed for an operation SHALL last through that operation without modifying package resources. Listing the catalog SHALL not install skills or require an OpenSpec project.

#### Scenario: Installed package without checkout
- **WHEN** the wheel is installed and catalog listing runs from an unrelated empty directory
- **THEN** it lists the packaged skills and their package provenance without reading the checkout or installing native assets

#### Scenario: Temporary resource extraction
- **WHEN** installed resources require extraction to obtain filesystem paths
- **THEN** all selected skills and support files remain available until the dependent operation completes and extraction paths do not become durable skill identities

### Requirement: External references remain external

Packaging SHALL preserve skill names, licenses, and relative support links. It SHALL not vendor skills from the user's home or claim installation of referenced skills absent from the catalog. Operational documentation SHALL identify external prerequisites and preserve native OpenSpec skill names.

#### Scenario: Referenced commit skill is absent
- **WHEN** packaged guidance references zmem-author-commits but it is not part of the authored catalog
- **THEN** installing the catalog does not copy a user's version or report that prerequisite as installed
