# Implementation evidence

The initial 29 implementation tasks are complete. The repository now consumes its default
profile through the installed overspec console command. The first real sync added
the retained tooling context and bundled archive instruction while reproducing the
existing compact TDD/zuu apply bodies. The second sync reported unchanged with the
same resolution identifier. Saved TDD details were retrieved successfully.

## Initial implementation verification

| Check | Observed result |
| --- | --- |
| `uv run pytest -q` | 77 passed, including companion-OpenSpec and installed-console integration |
| `uv lock --check` | Passed; 15 packages resolved |
| `uv build` | Built source distribution and wheel |
| `uvx ruff check src tests --select F` | All checks passed |
| `openspec validate compose-traits-into-openspec-config --strict` | Valid |
| Wheel inspection | Core, concrete handlers, and CLI included; 25 Python modules |
| Repository sync | First write succeeded; repeat unchanged; detail lookup succeeded |

Tests ran on Windows with Python 3.12. Companion OpenSpec reports 1.12.0; the local
reference checkout HEAD is `e062b9572be933564ba3899d059377dfa1393e32`.
The lock pins zuu 202609.8.0 to `be05a93f6726e54568e11181d805eccd7dcaf4af`.
Other tested versions: ruamel.yaml 0.19.1, packaging 26.3, tomlkit 0.15.1, pytest 9.1.1.

## Coverage by task group

| Tasks | Implementation | Behavioral evidence |
| --- | --- | --- |
| 1.1–1.4 | `core/profiles.py`, `trait_system/sources.py` | Default/arbitrary/nested discovery, inactive/state exclusion, redirected roots, physical-file deduplication across layers, activation precedence, full overrides, all source types and optional details |
| 2.1–2.3 | `core/remotes.py`, profile CLI | Real zuu public-client ZIP integration, default/branch/full-commit selectors, immutable source association, cached-content validation, failed download/copy recovery, previous revision preservation, offline selection, collisions |
| 3.1–3.5 | Base classes, individual handlers, registry, evaluator, rendering | Custom registered handler through generic dispatch, unknown/duplicate registry errors, regular-file AND, requirement parsing, negation, suppression history, forward/later-phase references, runtime scope and typed predicates, scalar interpolation and variable layers |
| 3.6–3.7 | `core/project.py`, `core/storage.py` | Frozen compilation, relevant source/input/details compatibility, fresh ordinary evaluation, suppression without compilation mutation, publication failure and source-race checks, read-only preparation/explanations |
| 4.1–4.5 | `core/resolution.py`, retained state | Stable content IDs, distinct attachment groups, unique bundled names, context isolation, requested output filtering, integrity/root binding, static-only bundles, saved/historical details, stale-receipt rejection, no implicit details output |
| 5.1–5.6 | `core/projection.py`, sync and CLI | YAML/YML precedence, invalid/duplicate-key rejection, shared-alias preservation, literal dotted artifact IDs, marker repair, whole-field replacement, empty inventory cleanup, preview/no-op, context limit, source/config races, receipt failure and retry |
| 6.1–6.4 | `tests/test_integration.py`, CLI tests, README | Real proposal/apply/archive instruction JSON and execution of embedded command, unchanged change artifacts, default-profile eligibility transitions, compact-body reproduction and separate details, console packaging, full checks |

All source handlers were reviewed directly for the requested structure: one concrete
assertion/action per file, separate abstract bases, explicit registration, and no
type-specific predicate/action switch chain in the evaluator.

## Observed TDD cycles

Tests were added and run before their implementation groups. Initial reds exposed
missing public modules, registry entries, methods, and console behavior. The
corresponding focused suites reached green before subsequent groups were started:

- Discovery: 3 failures → 3 passing; activation added 2 failures → 5 passing.
- Base contracts: 1 failure → 1 passing; concrete predicates/actions: 14 failures
  → 14 passing; source parsing/composition: 8 failures → 8 passing.
- Evaluation/rendering: 7 failures → 7 passing. Compilation: missing lifecycle
  implementation → 4 passing after implementation and correction of the test TOML
  serializer. The serializer problem was a fixture defect, not behavioral red evidence.
- Retained runtime resolution/YAML projection: 10 failures → 10 passing.
- Synchronization/detail lookup: 6 failures → 6 passing.
- Remote lifecycle: 3 failures → 3 passing. Installed CLI tests failed against the
  original greeting entry point, then both passed with the command implementation.

Review then added focused regression tests before fixing each discovered defect:

1. Explain mode accepted oversized context; it now validates the same candidate as
   normal static resolution.
2. Compilation could publish a pointer after a source changed during generation
   publication; the pointer now has a final compatibility recheck.
3. Project activation could traverse a redirected `.over` root; it now uses the
   confined project-root inspection before activation.
4. Remote validation could validate text different from the captured publication
   bytes; parsing now uses the captured byte content.
5. One physical file could be loaded in both profile and local layers; discovery
   now deduplicates across both layers.
6. An interrupted remote revision copy could prevent retry; revisions are now
   staged and published as complete directories before pointer activation.

Each regression failed with the original behavior and passed after its fix. Final
formatting was followed by the complete passing suite. No expectations were weakened
to produce green. Integration checks that passed when first added were treated as
additional verification, not claimed as red-first implementation cycles.

## Zuu integration decisions

- **case2** captures source bytes and filesystem evidence, remote material, and
  pre-publication input observations. Empty inventories are handled explicitly
  because its capture contract requires at least one root. Content identities omit
  timestamps; rechecks can still compare captured filesystem evidence.
- **case5** confines source traversal, activation targets, dependency probes, state
  access, and publication targets, with revalidation before replacement.
- **case8** performs whole-key user/project/invocation variable layering. Overspec
  validates scalar values and controls the lifetime of those inputs.
- **case12** performs public GitHub subpath synchronization through its real public
  interface. Tests inject a client producing ZIP archives, not a substitute for
  GitHubSubpath itself. Overspec validates actual cached content and publishes
  separate immutable profile revisions because a zuu commit-marker hit alone does
  not verify download contents.
- **case13** reads `project.dependencies` through explicit keys and traverses native
  operation-guidance destinations without splitting literal artifact IDs.

Contract mismatches were kept explicit:

- case1's persisted match lifecycle can write baselines, so it is not used for
  read-only preparation or implicitly refreshing compile-time state. SHA-256 over
  canonical JSON supplies immutable generation identities instead.
- case7's modified-output protection does not fit deliberate whole-owned-field
  replacement. Config publication uses confined plans plus atomic replacement.
- case14 provides no round-trip writer. ruamel.yaml preserves unowned YAML data and
  comments; its tested version loses block-scalar sequence header comments on dump,
  so overspec inserts its required markers at exact scalar source positions obtained
  by reparsing the generated YAML. Tests cover repair and no-op behavior.
- tomlkit preserves activation configuration and variables. Packaging parses Python
  requirement names. These are format/domain contracts, not alternate zuu mechanics.
- Interactive selection was not introduced, so case11 is not needed.

## Practical limits

Live GitHub HTTP access was not exercised; retrieval was verified through zuu's
injectable public client using controlled archives and failures. Other operating
systems were not run in this session. Remote support is public GitHub directories,
as planned. Runtime guidance requires an agent to execute the embedded command and
apply its output. State remains root-bound and retained without garbage collection.
Publication is designed for a single writer and explicitly reports receipt failure
after a config commit; it does not claim a multi-file transaction.

No sibling repository was modified. No commit or archive operation was performed.

## Typer/Rich UX follow-up

The added task 6.5 is complete, bringing the change to 30 completed tasks. The CLI
now uses Typer 0.27.2 and Rich 15.0.0, with separate lifecycle, profile, and trait
command modules and shared typed options. It provides grouped help, successful
no-argument discovery, profile/explanation tables, explicit empty states, and sync
summary/candidate/diff sections. Existing command spelling and common-option
positions remain supported. JSON and runtime guidance remain undecorated; literal
details are not interpreted as Rich markup.

Five UX tests first failed against argparse: no-argument success/help, help grouping,
profile table/empty state, a public Typer CliRunner entry point, and preview sections.
They passed after migration. An additional failing regression exposed cropped long
preview lines; terminal previews now wrap, and redirected previews retain complete
candidate and diff text. Windows output newline translation is applied once, avoiding
doubled CRLF lines. Installation and newline debugging failures were not counted as
new behavioral red evidence.

Final follow-up checks: **86 tests passed**, including installed-console and companion
OpenSpec integration; `uv lock --check` passed with 21 packages; `uv build` produced
the source distribution and wheel; Ruff's F checks and strict OpenSpec validation
passed. The rendered root/subcommand help, profile table, and repository dry-run
were also inspected. No completion script was installed and no interactive prompt
was added.

The migration uses Typer's public application, context, option, exception, and
testing interfaces. Reference: [Typer context documentation](https://typer.tiangolo.com/tutorial/commands/context/)
and [Typer testing documentation](https://typer.tiangolo.com/tutorial/testing/).

## User-home isolation follow-up

Task 6.6 changes the default user home to `~/.overspec`, bringing the change to 31
completed tasks. User profiles, activation, and remote storage use that home;
project-local sources and saved resolutions remain under `openspec/.over/`.
Explicit `--home` and `OVERSPEC_HOME` retain their precedence. No old user directory
is automatically inspected or migrated.

The new regression first failed because default discovery consumed another app's
`~/.over/config.toml`; the help assertion also failed against the old default.
Both passed after the change. The test verifies discovery from `~/.overspec`, user
activation writes, untouched foreign config, and unchanged project-local paths.
Final checks: **88 tests passed**, strict OpenSpec validation and lock validation
passed, and both distribution artifacts built successfully.

## Recursive assertion groups follow-up

Tasks 7.1–7.4 are complete, bringing this change to **35 completed tasks**.
Proposal, design, both capability specs, tasks, and README now describe numbered
recursive condition groups. Each group defaults to AND, accepts boolean `or`, and
contains either assertion leaves or numbered subgroups. Numbers sort numerically;
empty groups, mixed child kinds, invalid keys, and conflicting legacy operators
are rejected. Leading `~` remains leaf negation. Flat declarations and version-1
saved resolutions remain readable.

Observed TDD evidence:

- Parser tests first produced **13 failures / 7 passes**: valid grouped tables
  were rejected as non-lists, and nested errors lacked condition paths. Recursive
  parsing and immutable group/leaf nodes made the focused parser/composition/
  evaluator selection pass **35 tests**.
- Evaluation tests then produced **7 failures / 22 passes**: flattening lost nested
  truth-table semantics and short-circuit order, and reference errors lacked paths.
  Recursive evaluation and full-tree reference validation made the grouped,
  evaluator, and assertion selection pass **50 tests**. Truth tables cover both
  OR-of-AND and AND-of-OR, including negated leaves and deeper nesting.
- The terminal explanation test first failed because only flat reasons appeared.
  Rich condition trees now show operators, paths, results, and skipped branches;
  JSON retains the tree plus the compatible flat list of evaluated assertions.
  Old retained traces still display their reasons. The focused CLI/grouped
  selection passed **41 tests**.
- Additional lifecycle checks passed without further production changes: compiled
  decisions remain frozen until update, ordinary conditions refresh at sync,
  compiled source edits require update, retained runtime definitions stay isolated
  from live edits, and old flat bundles remain readable after grouped sync. These
  were integration verification, not additional claimed red cycles.

All existing conditional default-profile declarations now use numbered tables.
Migration compared every parsed body, details field, action, assertion payload,
and operator before/after; all were preserved. TDD remains assertion-free.
Four complete README trait examples parse successfully. Registry dispatch and
one-concrete-assertion/action-per-file boundaries remain intact. Zuu continues to
serve source observation, confined paths, variable layering, retrieval, and config
traversal; recursive Boolean evaluation is overspec domain behavior, not a
replacement for zuu's mapping utilities. No dependency was added.

Final verification: **120 tests passed**, including companion OpenSpec and
installed-console integration. `uv lock --check` passed with 21 packages;
`uv build` produced both distributions; strict OpenSpec validation passed.
Focused Ruff checks (`E4,E7,E9,F,I,C4`) passed. Parser schema failures intentionally
remain ValueError diagnostics; the broader inherited TRY004 exception-style rule
was not adopted. Tests were rerun after formatting/import refactoring. Versions
remain those recorded above.

The repository completed a real update, inspected dry-run, and sync. The YAML diff
changed only the runtime command's resolution reference to
`3dee644f9e3f0f6de1aa912f95fa8991e041e4b130be6ac8a955475062c0d9f7`.
A second sync reported unchanged and preserved config bytes and modification time.
The previous saved flat resolution and the new grouped resolution returned equal
runtime guidance for absent, boolean, and overlapping-list contexts. No sources,
profiles, or retained bundles were deleted; no commit or archive was performed.

## Optional profile feature implementation

The profile-toggle revision is implemented: **39/39 tasks complete**. This section
supersedes the earlier profile-activation and command-surface descriptions. Profile
mode defaults off; ordinary composition resolves default with project overrides
and ignores dormant user/environment selections and unrelated named sources.
With mode enabled, selection is OVERSPEC_PROFILE, saved user choice, then default.

`profile activate` takes no name and toggles `[profiles] enabled` in the chosen
user home's config.toml. It preserves `[profiles] selected`, variables, comments,
and other settings. Enabled-only `profile use NAME` saves the user choice and
reports any environment override. No project selector, invocation --profile,
--user selection flag, or compatibility alias remains. The repository's obsolete
project selector was removed; its authored default traits are unchanged.

Typer group subclasses filter help, completion, and dispatch for each invocation;
only activate is available while off. The invocation group observes declared
option arities to find the effective --home before subcommand dispatch, without
executing callbacks or replacing Typer validation. This supports common options
at root, group, and command positions and repeated in-process calls. Named core
management operations also check enabled state. Retained runtime and detail
commands remain available in both modes.

Observed verification:

- **7 failing state/selection tests** established the missing toggle, dormant
  selection bug, and missing management guards. All seven passed after the core
  changes, including boolean validation and unrelated-state preservation.
- CLI tests then failed on the ungated completion surface and missing toggle
  command. The focused state/CLI selection passed **12 tests** after implementation.
- A further red regression caught Typer suggesting disabled commands despite
  filtered command lookup. The generated nested group did not honor the instance
  suggestion setting, so the profile-group constructor explicitly disables that
  behavior. The focused profile/core/remote selection passed **31 tests**.
- Seven lifecycle checks verified effective-selection changes during compilation
  and sync, same-default toggle compatibility, explicit update requirements, and
  retained runtime/detail lookup after disabling. Existing publication rechecks
  already handled effective selection changes; these were integration verification,
  not additional claimed red cycles.
- Existing name-activation tests were revised to the accepted contract, and remote
  test fixtures explicitly enable mode. An additional test retrieves a default
  through zuu, disables mode, and consumes it offline despite unrelated corrupt
  remote metadata. No retrieval occurs during resolution.

Final checks: **141 tests passed**, including the companion OpenSpec integration
in both mode states. Strict OpenSpec validation, uv lock --check (21 packages),
uv build (source distribution and wheel), and focused Ruff E4/E7/E9/F/I checks pass.
No dependency was added. Zuu's existing source observation, confined paths,
remote retrieval, variable layering, and traversal integrations remain in use;
the new direct named-source lookup uses the public confined-path contract.

An installed-console smoke check in temporary user/project directories exercised
off/default -> on/user team -> environment default -> off/ignored environment,
including update and sync. The repository itself remains in off mode; its profile
help lists only activate. A real sync reused resolution
`3dee644f9e3f0f6de1aa912f95fa8991e041e4b130be6ac8a955475062c0d9f7`
and preserved config bytes and mtime. User-wide activation was not changed during
verification. No sibling repository, authored profile, or retained bundle was
deleted; no commit or archive was performed.
