## Context

See proposal.md for motivation. Trait composition, grouped assertions, snapshots, config synchronization, and the Typer CLI are implemented. Before the profile-toggle revision, management commands were unconditional and selection used invocation/project/user name precedence. The implemented revision replaces that model with default-only operation and an opt-in profile feature. The implementation report records the revised contract and verification. Preserve the core boundaries between actions, assertions, and trait_system and the authored default-profile sources.

The companion OpenSpec reads native context, artifact rules, and apply/archive guidance. It does not interpret trait assertions or execute commands embedded in those fields. Zuu's inspected public `case12.GitHubSubpath` supports public GitHub directory synchronization and records resolved commits. Its cache-marker hit does not verify target contents, so overspec must validate profile contents independently.

## Goals / Non-Goals

**Goals:** Separate discovery, phase evaluation, and destination rendering; strip profile names from resolved identity; retain reproducible compilation and runtime bundles; provide explicit reviewable sync.

**Non-Goals:** Recreate workflow runs, automatically execute OpenSpec operations, install agent hooks, interpret arbitrary scripts in bodies, preserve manual edits inside owned fields, or provide private/enterprise/non-GitHub remotes through a utility that does not support them.

## Decisions

### 1. Resolve default automatically; enable named profiles explicitly

Treat `openspec/.over/` as the project source root. Immediate `profile-*` directories with nonempty suffixes are profiles. The user home defaults to `~/.overspec`, overridable by `OVERSPEC_HOME` and an explicit `--home`; this changes userspace only, never the project root. Do not implicitly read or migrate `~/.over`, which may belong to another application.

Separate the feature toggle from the selected profile name. Persist `[profiles] enabled = false` by default in `<user-home>/config.toml`; absence also means off. `overspec profile activate` takes no profile name and toggles that boolean, reporting the resulting on/off state. Each invocation is an intentional toggle. Preserve an optional `[profiles] selected` value across toggles. `profile use NAME`, available only while enabled, writes that user-level selection. It is a selection operation, not an activation alias. Keep `[vars]` in project and user settings as before. There is no project-level feature toggle or profile selector.

When off, resolve only `default`: project `openspec/.over/profile-default` takes precedence over the user home's authored or previously retrieved default. Ignore `OVERSPEC_PROFILE`, saved selected names, and old project `profile` values. Other profile directories do not force activation or a selection error and are not loaded or validated as trait sources. If no default source exists, allow loose local traits alone. Off mode disables named-profile management, not the underlying default trait composition feature.

When on, choose exactly one name in this order: nonblank `OVERSPEC_PROFILE`, user `[profiles] selected`, then implicit `default`. An explicitly supplied empty/invalid environment value or invalid saved selection is an error; missing explicit selections never fall back. Environment selection affects only the invocation and does not rewrite user settings or enable the feature. If the implicit default is absent, local-only operation remains valid. A project `profile-<name>` still shadows a same-name user source completely; loose local declarations then override same-name traits. Activation does not pin a source or disable local overrides. Do not merge every discovered profile.

The toggle and named selection affect subsequent resolution, never automatically compile, sync, fetch, or delete anything. Disabling ignores the remembered selection and environment override until reenabled. Use the chosen `--home`/`OVERSPEC_HOME` for both toggle state and default sources. Atomically update user settings through the existing confined-path and TOML-preservation boundaries. No command writes shell startup files or changes its parent process environment.

Remove invocation `--profile`, project `profile` selection, and the previous `profile use ... --user` distinction. No compatibility aliases or migration layer are required for the superseded profile interface. Existing flat assertion parsing and retained runtime-bundle semantics are separate contracts and remain as specified.

Discover regular files matching basename `trait*.toml` recursively inside the selected profile and outside every profile subtree in the project source root. This is the intended interpretation of the user's `.over/**/trait**.toml`: zero or more subdirectories and any basename suffix after trait. Exclude `.state/`, reject redirected traversal, and deduplicate physical source paths. Sort normalized relative paths case-sensitively; preserve declaration order within each phase array. Do not inject loose user-level traits into every project.

Profile layers are resolved away, not deleted from disk. Local declarations replace same-name profile declarations completely; duplicate names within either layer are errors across all types. A replacement keeps the inherited file/declaration ordering key, even if its phase changes. Additional local declarations follow inherited entries. This is deterministic without using body text or profile prefixes as identity.

This repository is itself a reusable default-profile source and consumes that same profile. Keep all repository-authored traits under `openspec/.over/profile-default/`, including the existing `traits.toml` and separate `trait-tdd.toml` and `trait-zuu.toml`. Do not create repository guidance as loose local traits outside the profile. Local trait discovery remains a supported consumer feature and is exercised through temporary fixtures. A remote consumer can retrieve the `openspec/.over/profile-default` subdirectory without requiring the rest of this repository.

### 2. Pull remote profiles through the existing zuu boundary

Expose retrieval and refresh only when profile mode is on. An off-mode default may consume an already retrieved default revision offline; it cannot trigger downloads or expose management commands. Resolving default must not validate unrelated named-profile sources or remote entries.

Add explicit profile pull/update operations accepting a local profile name and structured GitHub owner, repository, directory, and optional branch or full commit. Persist source metadata and a pointer to a validated installed revision in userspace; source association is immutable for each managed download target. Use `GitHubSubpath.sync` only on overspec-owned download directories, never a manually authored profile or the project source tree.

Keep downloaded material under `<user-home>/.state/remotes/`. A registered remote name participates in the same user-level profile catalog as `profile-<name>`; a collision with a manually authored user profile is an error. Validate candidate traits after every retrieval, including zuu cache hits, and publish a validated immutable revision through an atomic pointer. A failed download or invalid candidate leaves the last usable pointer and activation intact. Resolve and sync never fetch implicitly.

Record both the remote source and resolved commit in diagnostics. Zuu's commit marker alone is not a content-integrity guarantee: hash validated local content for the published revision. Initial support is public GitHub subdirectories because that is the truthful public API available; generic URLs would overstate capability.

### 3. Use trait declarations with recursive condition groups

Accept `[[compiletime-trait]]`, `[[trait]]`, and `[[runtime-trait]]`. Require `name`, `attach`, and nonblank `body`. Optional literal-prose `details` supplements the body; omitted or whitespace-only details normalize to absence and non-string values fail. Optional `assert` contains a recursive condition group; `actions` retains its existing shape. Retain the legacy flat `assert` array and `assert_or_grouping` for existing sources and saved resolutions. No required source version or source manifest is introduced. Reject unknown fields. Restrict names to `[a-z][a-z0-9-]*` so comma-separated markers and command arguments are unambiguous.

Each condition group has optional boolean `or` (false/default means AND), and either a nonempty `assertion` array of registered leaves or one or more numbered child groups. Do not mix leaves and numbered groups in the same group. Child names are canonical positive decimal integers (`1`, `2`, `10`), need not be contiguous, and evaluate numerically. Reject zero, leading zeros, other names, non-table children, empty groups, malformed leaves, and a legacy grouping flag alongside a group table. Omitted assertions and legacy empty arrays remain unconditional. A leaf's leading `~` negates its result; group negation is not added.

For example, `[trait.assert]` with `or = true`, followed by `[trait.assert.1]` and `[trait.assert.2]`, each holding two `[[trait.assert.N.assertion]]` leaves, expresses `(A AND B) OR (C AND D)`. A numbered group can itself contain numbered groups, each with its own operator. Direct `[[trait.assert.assertion]]` leaves are also supported. Always place root fields including body, details, and actions before nested tables; TOML binds tables to the latest declaration of their owning trait type.

Represent conditions as immutable group/leaf nodes in shared models; parse recursively through the existing assertion registry and evaluate generically in trait_system. Validate every nested reference and phase constraint before short-circuit evaluation. Evaluation traces retain group paths, operators, results, negation, and skipped nodes; keep the flat evaluated-assertion trace for older consumers. CLI explanations show the tree, with a fallback for old retained traces. Save original grouped declaration structure in version-1 bundles; the compatible reader accepts both shapes. Source changes to compiled conditions still require explicit update. Use zuu at existing source, path, and persistence boundaries; Boolean expression interpretation is overspec's domain responsibility, not deep mapping traversal.

Parse attachment prefixes explicitly. `context` is a string destination; `rules.` consumes the entire remaining artifact ID literally; apply/archive guidance are string-list destinations. One trait has one attachment. Join static context fragments with blank lines and append one body per list entry, in compiled-then-ordinary-then-runtime phase order.

### 4. Freeze compile-time results, resolve ordinary traits at sync

Init and update discover sources, resolve profiles/local overrides, evaluate compile-time traits, render their bodies, and publish a compiled snapshot under project `.over/.state/`. They do not themselves rewrite OpenSpec configuration; sync is the explicit config-writing step. Init refuses to overwrite an existing valid compilation and directs the user to update.

The snapshot records compilation format, selected profile identity, effective compile-time definitions/order, relevant explicit variables, matched names, suppression decisions, rendered bodies, optional details, and origin evidence. Compile-time details are frozen with the definition, so edits to them require update. Its compatibility fingerprint excludes unrelated ordinary/runtime definitions. Sync checks compatibility but does not rerun executable probes. Changing tool availability alone has no effect until update; changing a compile-time definition, its relevant explicit inputs, or profile selection requires update. Ordinary/runtime-only edits are handled at the next sync. Missing or incompatible snapshots produce actionable init/update guidance.

Sync evaluates ordinary traits against retained compile-time matched history and current sync inputs. Ordinary suppression can hide a compiled body for that sync without changing the stored compilation. Runtime definitions remain deferred and are stored with the current resolved earlier-phase history in an immutable resolution bundle.

Resolve the toggle, applicable environment selection, and user selection once per invocation and carry that observation through preparation. Recheck inputs that determine effective selection before publishing compilation or config. A detected selection change aborts publication. Compatibility follows the effective source/name and compile-time inputs: toggling while still resolving the same default source need not invalidate compilation, but changing the effective profile does require update. Retained runtime commands and detail lookup use their saved bundle regardless of current profile mode; disabling management must not prevent executing already synchronized guidance.

### 5. Define matched history independently of emitted output

Use a single ordered evaluation pass per phase, with AND by default, optional OR at every group, and recursive short-circuit evaluation. Omitted assertions and legacy empty arrays match; explicitly empty group tables are invalid. `which` checks executable availability without launching the executable. `require-trait` and `loaded-trait` both test previously matched names; a leading `~` negates the predicate. Validate name references against the effective inventory before evaluation. References to later phases are errors; forward references in the same phase are false until matched, not an implicit recursive resolver.

A matched `remove-trait` action adds a suppression name without erasing matched history, source definitions, or identity. Suppression can precede the target's evaluation. It affects only emitted output. Runtime references to other runtime traits and runtime removal stay within the same attachment group; references to earlier matched phases use the retained bundle. Compile-time actions cannot target later phases. Ordinary actions can suppress compiled or ordinary output but cannot preempt runtime evaluation.

Consequently require-zmem can require require-codegraph and suppress its separate body. The sketch's only-zmem OR condition matches when either referenced trait has not matched. Its current prose still mentions both tools; preserve that author content rather than silently changing its condition or body.

### 6. Generate one runtime command per resolution and attachment

Build a content-addressed resolution bundle under `openspec/.over/.state/resolutions/<digest>.json`. Include the root binding, contract version, effective definitions of all three types (including optional details), retained static results, earlier-phase matched/suppressed history, necessary explicit variables, and origin mapping. Retain unmatched and suppressed effective declarations for inspection, while excluding overridden declarations. Publish a bundle even for static-only or empty inventories so detail lookup has the same stable source as runtime resolution. The bundle is immutable and verified before use. Equivalent effective inputs reuse the same digest; do not include timestamps. Retain bundles referenced by existing config; garbage collection is outside this change.

For each attachment with runtime traits, emit one instruction at the group's first runtime position. Bundle unique names in declaration order, for example:

```text
From this project's root, run:
overspec trait resolve --resolution <digest> --attach operations.archive.guidance --trait do-not-archive-openspec-change --trait archive-review
Supply --context-file <path> when current invocation context is available, and apply the returned guidance to this operation.
```

The repeated `--trait` form avoids ambiguous argument splitting. The executable command is present once per group, not repeated per trait. The digest identifies a resolution, not a profile; trait arguments remain short names. Distinct destinations need distinct groups so proposal/context and archive scope cannot be mixed accidentally. Group markers list unique names with commas, using `over:first,second`.

The runtime command loads only the named retained bundle from the owning project's root, validates attachment/IDs, evaluates same-group dependencies in recorded order, and returns requested matched unsuppressed bodies with trailing name markers. Missing/corrupt bundles require resync, never fallback to the currently active profile. Profile activation after sync cannot redirect an old command.

Use `--context-file` for an explicit JSON object. No file means an empty object; do not carry invocation values between calls. Parse `kv` at its first equals sign, recognize JSON scalar literals such as true, and otherwise treat its value as a string. Match uses typed equality. Includes uses exact scalar membership or overlap with a referenced list such as `$activeChanges`; it does not search substrings. The caller supplies activeChanges, rather than overspec guessing that every open change is active. Missing keys or incompatible target types are false. A needed variable reference that is missing or malformed is an error. This allows the sketch's boolean-or-list alternatives.

Runtime resolution is read-only and offline. Returned guidance is advisory. OpenSpec exposes the embedded command to the agent; it does not execute it, and an agent failing to run it does not establish an enforced prohibition.

### 7. Render dynamic bodies and short provenance

Support scalar `${key}` interpolation, with `$$` escaping a literal dollar. Use project variables over user variables over no defaults, then explicit invocation variables at the relevant phase. Runtime invocation context overlays retained variables for rendering, while runtime-context assertions inspect only the invocation object. Missing used values or non-scalar substitutions fail. Never interpolate names/attachments or execute body content. Reserved marker syntax in source bodies/substitutions is rejected to prevent ambiguous generated attribution.

Static context fragments end with `<!-- over:<name> -->`. Static YAML list scalars have `# over:<name>` on their header line. Runtime group instructions use the same forms with comma-joined member names. Runtime output itself uses individual trailing HTML markers. Source/profile paths and body digests remain in diagnostics/bundles, not displayed identity. A changed body retains its name and is replaced at its declared evaluation time.

### 8. Preserve field ownership and publish state before config references

Own exactly `context`, the whole `rules` mapping, and apply/archive `guidance`. Replace them from the prepared resolution, removing empty destinations. Preserve every other value, including unknown operations and operation siblings. Prune containers only when nothing preserved remains. Reject duplicate YAML keys and non-mapping parent containers. Detach shared YAML aliases before editing owned nodes to avoid changing unowned values.

Use an explicitly declared round-trip YAML dependency, proposed `ruamel.yaml`, for comments and formatting. Native value equality is insufficient for no-op detection because YAML provenance comments are semantically invisible: compare owned markers as well as parsed values. If both are current, preserve config bytes and mtime. A details-only change can publish new resolution state without rewriting static-only config; if runtime groups reference the changed bundle digest, their command references also change. Enforce the 50 KiB UTF-8 context limit after marker and command insertion.

Dry-run computes candidate bundles and YAML in memory and writes nothing. Real sync validates all inputs, publishes needed immutable bundles, prepares a temporary sibling YAML file, rechecks source inventory/contents, activation, compiled snapshot and target bytes, then atomically replaces config. A failed config write may leave an unreferenced valid bundle but must not leave config pointing at absent state. After replacement or verification of an unchanged config candidate, atomically publish `.over/.state/last-sync.json` with the resolution ID, root binding, and fingerprint of owned values plus required markers. Report the ID on success. Default detail lookup verifies this receipt against current owned config; unowned edits do not invalidate it. A receipt publication failure reports non-success and explicitly states that config may already have changed; retry completes publication. An older valid receipt continues to identify its own saved resolution, never new unpublished details. Reuse identical bundles and receipts. No multi-file atomicity is claimed. Compilation/profile publication use immutable generations and atomic pointers so failures preserve the last usable generation.

### 9. Keep CLI operations bounded

Use Typer for typed command declarations and Rich for terminal presentation.
Keep the application entry point small, with lifecycle, profile, and trait command
modules and shared option/output helpers under `cli/`. No-argument invocation
shows an overview successfully. Group help by workflow and management commands,
and group options by project, inputs, output, and runtime scope. Render profile
and explanation tables plus separate sync summary, candidate YAML, and diff
sections. Long terminal lines wrap; redirected candidate/diff text is complete.
Keep JSON undecorated, and emit resolved guidance literally without Rich markup
interpretation or wrapping. Preserve common option positions, repeated runtime
IDs, and non-profile command behavior. Replace the profile surface as specified
below without compatibility aliases. Commands remain noninteractive unless
explicitly extended in a future change; adopting Typer adds no confirmation gates.

Always-available command surface:

```text
overspec init [--project PATH]
overspec update [--project PATH]
overspec profile activate
overspec sync [--project PATH] [--dry-run]
overspec trait resolve [--project PATH] [--explain]
overspec trait resolve --resolution ID --attach POINT --trait NAME ... [--context-file PATH]
overspec trait show NAME --details [--resolution ID] [--project PATH]
```

Only while profile mode is on, add:

```text
overspec profile list
overspec profile use NAME
overspec profile pull NAME --owner OWNER --repo REPO --path SUBDIR [--branch BRANCH | --commit SHA]
overspec profile update NAME
```

The off-mode profile group exposes only `activate`. Exclude inactive management commands from help, shell completion, and dispatch; they must not merely be hidden yet executable. Expose no `activate NAME` alias. Build the command surface for each invocation after resolving the effective user home and toggle, rather than freezing it at import time. Common home options must select the same state at root, group, or command position. Ensure toggling between repeated in-process CLI invocations refreshes the available commands. Shared core entry points for named management also enforce enabled state so direct calls cannot bypass the feature gate. Default source resolution and retained runtime lookup remain available without that gate.

Global `--home` selects userspace. `--vars-file` supplies scalar rendering inputs to init, update, sync, or static resolve; retained compile-time inputs remain frozen until update. Static resolve performs sync preparation read-only. Profile use saves a user-level selected name and reports any effective environment override. Profile list distinguishes the saved choice, effective environment selection, and resolved local/user source. Profile pull installs but never changes the toggle or selected name and never recompiles a project.

Keep source parsing, phase evaluation, profile lifecycle, snapshots, and projection in distinct core modules. CLI handlers delegate and translate results to concise output/nonzero failures. The root entry point delegates to CLI. Avoid imports from zuu private modules or an OpenSpec reimplementation.

### 10. Base classes and one implementation per file

Use separate abstract base classes for assertions and actions. Each concrete TOML assertion type has exactly one implementation module under `core/assertions/`; each concrete action type has exactly one implementation module under `core/actions/`. A module can contain its implementation's payload model and private helpers, but must not accumulate unrelated concrete handlers. Preserve and fill the existing `assertions/which.py` rather than moving its behavior into a central evaluator.

```text
src/overspec/core/
  assertions/
    __init__.py
    base.py                       # Assertion abstract base class
    which.py                      # WhichAssertion
    files_exist.py                # FilesExistAssertion
    python_dependency.py          # PythonDependencyAssertion
    require_trait.py              # RequireTraitAssertion
    loaded_trait.py               # LoadedTraitAssertion
    runtime_context_match.py      # RuntimeContextMatchAssertion
    runtime_context_includes.py   # RuntimeContextIncludesAssertion
  actions/
    __init__.py
    base.py                       # Action abstract base class
    remove_trait.py               # RemoveTraitAction
  trait_system/
    __init__.py
    models.py                     # Shared context, results, and effects
    registry.py                   # Explicit built-in type registration
    evaluator.py                  # Grouping, ordering, and phase execution
```

`Assertion` defines the shared contract for validating its payload and evaluating against a supplied read-only context, returning a typed match result with explanation data. `Action` defines payload validation and evaluation into a typed effect; `RemoveTraitAction` returns a suppression effect. Concrete handlers own their type-specific payload rules and behavior. They do not read global activation, mutate compilation/configuration, or select evaluation phases. The evaluator applies action effects to its in-memory resolution state.

`trait_system` owns shared data contracts, trait composition, phase rules, grouping, negation, short-circuiting, matched history, and effect application. Shared models must not import concrete handlers. Concrete handlers import their base and shared models; explicit registry construction imports the concrete handlers. Base classes do not import the registry or concrete subclasses. This keeps the dependency direction clear and avoids registration cycles.

Map TOML `type` identifiers to implementations through explicit assertion/action registries. Reject unknown identifiers and duplicate registrations. Dispatch uses the base-class contracts; do not implement assertion-specific or action-specific switch chains in the evaluator. Importing a trait source never loads arbitrary Python modules. Adding a new built-in type consists of its own implementation file and registry entry, without changing generic evaluation dispatch.

The `~` prefix and AND/OR grouping are composition operators handled by the evaluator, not extra concrete assertion files. `require-trait` and `loaded-trait` retain separate modules despite their currently shared matched-history semantics. Minimal package initializers may expose contracts but must not become collections of concrete behavior.

`FilesExistAssertion` accepts `paths` and checks that all entries are regular files beneath the supplied project root, using zuu.case5 inspection. Missing paths or non-file entries are non-matches; invalid paths and inspection errors remain errors. `PythonDependencyAssertion` accepts `name`, reads root-level `pyproject.toml` with tomllib, and obtains dependencies with the public `zuu.case13.deep_get(document, ["project", "dependencies"], default=[])`. Validate intermediate mappings and the final list rather than hiding type errors with a broad exception handler. Parse declared requirement strings with a standards-aware parser (proposed: an explicit packaging dependency), compare normalized package names, and do not use substring matching or installed-package discovery. Version constraints, extras, direct references, and markers do not change the declared package identity. Do not inspect optional dependencies, dependency groups, or tool.uv.sources as substitutes for project.dependencies. Register both types through the existing assertion registry and develop them through red-green behavioral tests.

Verify behavior through the shared contracts and generic evaluator, including a test-only registered implementation, duplicate/unknown-type errors, read-only assertions, and typed suppression effects. Review file placement directly; do not substitute file-count or source-text tests for those behavioral checks. This is an implementation architecture constraint, so it belongs here and in implementation tasks rather than adding a product capability spec.

### 11. Reuse zuu and observe the TDD cycle

The default profile's `tdd` and `zuu` traits are ordinary traits attached to `operations.apply.guidance`. Tdd is assertion-free. Zuu has exactly two AND-combined assertions: both `.python-version` and `uv.lock` must exist as project-root files, and `project.dependencies` in pyproject.toml must declare zuu. The dependency lookup uses zuu's public case13 deep_get API. These conditions are reevaluated at sync; normal profile replacement and explicit suppression semantics still apply. Their source bodies are self-contained, with no skill installation or extra file-read requirement. This repository satisfies the zuu conditions, so `openspec/config.yaml` initially contains exact seeded copies of both bodies before overspec sync exists. Once sync is implemented, verify it reproduces the eligible bodies and short markers from the same source rather than maintaining a second authored policy.

For every implementation behavior change, write and run the smallest meaningful test first, observe its intended failure, implement minimally, and rerun to observed green before refactoring. Continue with affected tests and broader required verification. Each implementation task is a sequence of these behavior-sized cycles, not permission to implement the whole task before testing. Preserve the observed red/green evidence in the implementation report. Documentation-only changes receive appropriate validation without manufacturing behavioral tests.

Use public zuu APIs extensively where their contracts match:

| Responsibility | Integration decision |
| --- | --- |
| Source observation | Use case2 filesystem snapshots; compute compatibility from relevant content so unrelated timestamps or ordinary-only edits do not invalidate compilation. |
| Rooted paths and exact-target rechecks | Use case5 confined path inspection/revalidation after selecting the trusted project or user root. |
| Explicit variable layering | Use case8 whole-key layering, with overspec retaining variable validation and phase ownership. |
| Remote profile retrieval | Use case12 as described above, with overspec-owned validation/publication. |
| Attachment traversal | Use case13 with explicit key sequences, preserving dotted artifact IDs as literal keys and verifying YAML metadata survives updates. |
| Persisted hash baselines | Use case1 where its write/callback lifecycle fits; do not use a matching operation that silently refreshes compile-time results or writes during read-only resolution. |
| Interactive profile selection, if introduced | Reuse case11 rather than a second selection framework; explicit selection and current noninteractive error behavior remain authoritative. |

Inspect the current public API before adding equivalent mechanics. Record the concrete mismatch when custom code is needed. In particular, case7's ordinary modified-output protection does not directly match deliberate owned-guidance replacement, and case14 has no writer or round-trip comment support. Retain a suitable YAML renderer. Do not force a mismatched utility into the domain model or add wrappers that merely rename calls. Verify real public integration behavior with controlled dependencies, including zuu's injectable client for remote retrieval.

### 12. Keep bodies compact and details available on demand

A trait expresses one responsibility in a few self-contained sentences. Keep essential conditions and instructions in its body; place optional elaboration, examples, and configuration notes in literal `details`. There is no parser word limit and no requirement to add details to an already small trait. Local overrides replace details along with the rest of the declaration. Details are not interpolated, so examples containing `${key}` remain literal.

Sync emits only static bodies and runtime command instructions; normal runtime resolution returns bodies only. Do not append a details command to each config item or introduce a skill dependency. The default profile keeps the TDD cycle and zuu API selection principle in short bodies, with the full process and contract-review guidance in their respective details fields. The longer combined codegraph/zmem trait is split similarly; the other three already brief declarations need no details. Conditions, attachments, suppression, and identities stay intact.

`overspec trait show tdd --details` loads the validated latest-success receipt and returns that resolution's literal details with name, phase, attachment, and source origin. `--resolution ID` selects a historical bundle independently of current config. Both forms validate bundle integrity and root binding and never read live profiles, rerun predicates/actions, render bodies, or write state. Unknown names or missing/corrupt state are errors; an effective declaration without details returns an explicit no-details result successfully. Suppressed/unmatched effective traits remain inspectable without implying they emitted guidance. Normal explanations may report whether details exist, but do not dump them.

Compile-time details are retained at init/update; ordinary and runtime details are retained at sync. Consequently source edits and activation changes cannot silently rewrite the explanation for synchronized guidance. Documentation explains the lookup command and the need to sync first; the manually seeded bootstrap config has no fabricated resolution state.

## Risks / Trade-offs

- A compile-time tool becomes available after init -> intentionally retain the old decision until update and explain its evaluation time.
- User-level activation can conflict with an existing project compilation -> require an explicit update rather than silently mixing phases from different profiles.
- YAML comments can disappear under external rewriting -> marker-aware sync repairs them without treating old output as source.
- Runtime commands require retained project state -> report missing bundle clearly and regenerate through sync; do not silently resolve another profile.
- A rendered config copied to another project lacks its bound runtime bundle -> require that project's own init/sync instead of accepting mismatched state.
- Zuu retrieval owns entire target directories and trusts commit markers -> isolate downloads, validate actual content, and publish separate usable generations.
- Noncooperating writers can race after the final recheck -> document single-writer use; atomic replacement prevents partial config writes but is not a cross-process transaction.
- Manual guidance in owned fields is overwritten -> expose exact diffs and direct authors to retain desired text in traits.

## Migration Plan

Keep the existing default-profile trait declarations and grouped conditions. Ordinary setup needs only default sources, init, preview, and sync. Users wanting named profiles toggle mode on, retrieve sources if necessary, choose a user selection or set OVERSPEC_PROFILE, then update and sync when the effective profile changes. Profile update is the deliberate remote refresh; it is available only while mode is enabled.

Replace the obsolete project/user name-activation tests, including the interrupted activate-NAME/compatibility-alias draft, with the new toggle behavior through observed red-green tests. Remove this repository's obsolete project `profile` setting during implementation while preserving variables and authored sources. Do not translate old activation settings or preserve removed flags. Revalidate both mode states and recorded-runtime behavior, update README/help, and replace stale completion claims with verification of the revised contract. This planning update does not itself modify implementation, tests, configuration, or the historical implementation report.

Static generated configuration continues to work without overspec. Runtime groups require overspec and the matching retained resolution. Rollback restores matching config and state generations through existing backups/version control. Do not delete authored profiles when resolving or changing activation.
