# Verification: compose-traits-into-openspec-config

Historical verification record. Its commit-scope discussion was superseded on
2026-09-10: exclude only the active change's artifacts from incremental commits,
not `.over`, config, tests, canonical specs, or already archived records.

Verified on 2026-09-09 against the current working tree.

The change is already archived at
`openspec/changes/archive/2026-09-09-compose-traits-into-openspec-config/`.
There are no active changes. Its schema is `spec-driven`. The CLI's active-change
`status` and `instructions apply` commands cannot address it, so proposal, design,
tasks, delta specifications, and implementation evidence were read from the archive.
The later zmem traits were also reviewed against the user's accepted instructions.

## Summary

| Dimension | Result |
| --- | --- |
| Completeness | 39/39 tasks checked; implementation evidence for all 27 requirements |
| Correctness | 81 specified scenarios reviewed against implementation and related tests; 142 tests pass |
| Coherence | Core boundaries and declared design followed; one README warning |
| Critical findings | None found |
| Warnings | One reproducibly failing documentation command |

Scenario review maps to related tests and source handling; it is not a claim that
each specification scenario has its own dedicated test or that testing proves
all possible behavior. Historical red-first execution is documented in the archived
implementation report; this verification reran green checks, not historical reds.

## Warning

**README documents validation of an active change that no longer exists.**
`README.md:356` instructs readers to run
`openspec validate compose-traits-into-openspec-config --strict`.
Running that command reports `Unknown item` now that the change is archived.
Replace the development check with `openspec validate --all --strict` and, for
archived task completion, `openspec validate --archived --strict`.
The latter checks archived task completion; it does not replace canonical spec
validation. Documentation was left unchanged during this verification.

## Requirement coverage

Paths below are relative to the repository root. Each row has implementation and
behavioral evidence; no required implementation was found missing.

### Trait composition: 14 requirements, 47 scenarios

| Requirement | Implementation evidence | Test evidence |
| --- | --- | --- |
| Profile and local trait discovery | `src/overspec/core/profiles.py:18`, `src/overspec/core/project.py:29` | `tests/test_profiles.py`, physical-file deduplication regressions |
| Default composition and optional profile mode | `core/profiles.py`: selected_name, select_profile, toggle_profiles; `core/project.py`: Project | `test_profile_activation.py`, `test_profiles.py` |
| Enabled user/environment selection | `core/profiles.py`: selected_name, resolve_profile, use_profile | `test_profile_activation.py`, `test_profile_lifecycle.py`, `test_profile_commands.py` |
| Remote profile retrieval through zuu | `core/remotes.py`: source_api, pull_profile, update_profile, remote_profile | `test_remotes.py`: injectable public GitHub client, offline default, failed publication and cache validation |
| Declarations and attachments | `core/trait_system/sources.py`: parse_trait, parse_document, attachment | `test_composition.py`, `test_projection.py` |
| Compact bodies and optional details | `core/trait_system/sources.py`: details validation; default-profile sources | `test_composition.py`, `test_integration.py`, `test_sync.py` |
| Profile-independent identity and local overrides | `core/trait_system/sources.py`: compose | `test_composition.py`, `test_profiles.py` |
| Three evaluation lifetimes | `core/project.py`: initialize, compatibility, prepare; `core/resolution.py`: resolve_runtime | `test_compilation.py`, `test_grouped_lifecycle.py`, `test_profile_lifecycle.py` |
| Assertions and output suppression | Separate handlers, registry, `trait_system/evaluator.py` | `test_assertions.py`, `test_contracts.py`, `test_evaluator.py`, suppression regression |
| Recursive numbered assertion groups | `trait_system/conditions.py`, immutable model nodes, evaluate_condition, CLI explanation tree | `test_condition_groups.py`, `test_grouped_cli.py`, `test_grouped_lifecycle.py` |
| Project file and Python dependency assertions | `assertions/files_exist.py`, `assertions/python_dependency.py` | `test_assertions.py`, default-profile eligibility integration |
| Dynamic bodies retain identity | `trait_system/rendering.py`; saved runtime variable overlay | `test_evaluator.py`, `test_resolution.py`, `test_projection.py` |
| Read-only resolution and explanations | `cli/traits.py`: resolve; `core/resolution.py`: explain | `test_cli.py`, `test_compilation.py`, oversized-context explain regression |
| Resolution-bound detail lookup | `core/resolution.py`: show_details; `core/storage.py`: load_bundle | `test_sync.py`, `test_resolution.py`, `test_profile_lifecycle.py` |

Shortened `core/`, `cli/`, `assertions/`, and `trait_system/` paths above are beneath
`src/overspec/` or `src/overspec/core/` as appropriate; test filenames are under `tests/`.

### OpenSpec config sync: 13 requirements, 34 scenarios

| Requirement | Implementation evidence | Test evidence |
| --- | --- | --- |
| Discoverable commands and stable script output | Typer command modules, shared options/output, literal guidance emission | `test_cli.py`, `test_grouped_cli.py` |
| Profile commands gated by mode | `cli/profile_mode.py`: InvocationGroup and ProfileGroup; core require_profiles | `test_profile_commands.py`, `test_profile_activation.py` |
| Explicit project target | `core/project.py`: Project; `core/projection.py`: config_target, parse_yaml | `test_sync.py`, `test_projection.py`, CLI scope tests |
| Read-only preview | `core/project.py`: sync(dry_run=True) | `test_sync.py`, preview/long-output CLI tests |
| Replace only owned guidance | `core/projection.py`: project_yaml | `test_projection.py`: unowned aliases, operation siblings, dotted IDs |
| Body-only projection | `core/resolution.py`: contributions, resolve_runtime | `test_integration.py`, `test_sync.py`, runtime-details regression |
| Remove stale contributions | `core/projection.py`: replacement and pruning | `test_projection.py`, `test_compilation.py`, default eligibility transitions |
| Validated repeatable writes | `core/project.py`: evidence and sync; `core/storage.py`: atomic_write | `test_sync.py`, `test_profile_lifecycle.py`, publication regressions |
| Short source markers | `core/projection.py`: markers, project_yaml | `test_projection.py`, `test_sync.py`, dynamic-body resolution tests |
| Bundled runtime commands | `core/resolution.py`: contributions; immutable root-bound storage | `test_resolution.py`, `test_grouped_lifecycle.py`, distinct-destination and copied-root regressions |
| Successful-sync receipt | `core/project.py`: sync receipt; owned_fingerprint; show_details | `test_sync.py`: details-only changes, stale receipt, failure/retry |
| Runtime invocation context | `core/resolution.py`: resolve_runtime; typed runtime assertion handlers | `test_assertions.py`, `test_resolution.py`, `test_evaluator.py` |
| Native OpenSpec consumption | Project projection and embedded command protocol | `test_integration.py`: real proposal/apply/archive commands in both mode states |

Canonical requirement content matches the archived delta specifications. The only
text differences are the canonical specification titles and the conversion of
`ADDED Requirements` to `Requirements`.

## Design and recent authoring review

- Separate Assertion and Action abstract bases, seven concrete assertion modules,
  and one concrete action module follow the requested structure. Generic parsing
  and evaluation dispatch through explicit registries; no arbitrary source imports.
- Public zuu cases 2, 5, 8, 12, and 13 handle source observations, confined paths,
  variable layering, remote retrieval, and explicit-key lookups. The archived
  implementation report records contract mismatches for specialized YAML and
  persistence behavior.
- Profile mode defaults off, preserves default composition, and controls actual
  command dispatch and completion. Retained runtime/detail reads bypass current
  profile selection as designed.
- Static bodies, retained details, deferred runtime groups, and OpenSpec lifecycle
  authority remain separate. Guidance is advisory; sync does not execute a skill
  or enforce a commit/archive hook.
- `openspec/.over/profile-default/trait-zmem-commits.toml:3` attaches milestone
  guidance to context; line 27 attaches post-archive guidance to
  `operations.archive.guidance`. Both are ordinary traits gated on zmem availability,
  with short bodies and separate details. The workflow stays in the referenced
  `zmem-author-commits` skill. OpenSpec artifacts are excluded from the requested
  implementation commits.
- `tests/test_zmem_reference_trait.py:7` verifies both references appear at their
  destinations with zmem available and disappear after syncing without it, without
  relying on codegraph. This tests emitted guidance, not an agent's future execution
  of that guidance.
- The zmem references and `create-overspec-trait` skill were added after archival;
  they are reviewed here as later authoring work, not presented as original
  archived requirements or retroactively inserted into the historical plan.

## Observed checks

| Check | Result |
| --- | --- |
| `uv run pytest -q --tb=short` | 142 passed in 16.59 seconds; no skips |
| `openspec validate --all --strict --json` | Both canonical specifications valid; informational length notes only |
| `openspec validate --archived --strict --json` | Archived change valid; no incomplete tasks |
| `uv lock --check` | Passed, 21 packages resolved |
| `uv build` | Built source distribution and wheel |
| `uvx ruff check src tests --select F` | Passed |
| `uv run overspec sync --dry-run --json` | No pending config change |

Current saved resolution:
`a4ec33b6165fd33aab6a91741510868e489e13c7f7f03880e493bc9a2c5a12af`.

No critical issues were found. One documentation warning remains. This is a
post-archive verification; no archive operation or implementation change was made.

## Post-archive follow-up

The README warning was subsequently resolved by replacing the obsolete active-change
validation command with canonical and archived validation commands. Both replacement
commands passed. The existing archive remains intact; no duplicate archive was made.
