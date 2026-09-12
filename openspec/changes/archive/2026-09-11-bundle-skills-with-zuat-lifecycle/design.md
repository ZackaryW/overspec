## Context

See proposal.md for motivation. Overspec currently bundles only the authored default traits through a Hatchling force-include hook. The existing release fixture explicitly excludes skills. `core/bundled.py` distinguishes imported installed resources from a verified editable checkout. No Overspec source currently calls ZuAT, although its public API is pinned and installed.

The user selected explicit user-level managed skills and subsequently included packaging/installing the companion schema in this change. ZuAT provides independent source-aware skills with content/ownership restoration; its plugin bundle path explicitly lacks an equivalent cross-agent rollback guarantee. The integration will use independent skills. The authored schema already exists at openspec/schemas/overspec, but current init only sets up variables and compilation. The [utility plan](utility-plan.md) records inspected APIs and the proportional verification boundary.

## Goals / Non-Goals

**Goals:** Ship complete authored skill and schema payloads, install the companion schema during project initialization, offer deliberate user-level skill lifecycle commands outside any OpenSpec project, and expose recoverable skill operations with exact target scope.

**Non-Goals:** Native plugins, hooks, project-level agent skill installation, remote skill acquisition, predecessor state migration, ZPP aliases, automatic dependency skill installation, package-manager hooks, or changes to trait composition/lifetimes. ZuAT rollback concerns agent skill content and ownership, not Python package versions, schema files, traits, project config, or OpenSpec change records. Installing a schema does not select it on the user's behalf.

## Decisions

### 1. A separate package resource tree

Map `.agents/skills/<name>/...` to `overspec/_bundled/skills/<name>/...` in wheels; retain the authored path in sdists so rebuilding uses the same hook. Include immediate directories containing SKILL.md and their regular support files, preserving license metadata and links. Exclude metadata/cache/state directories and standalone control files such as `.openspec-target`. Fail closed on redirected or unreadable included payloads. Native frontmatter/identity validation uses ZuAT before installation; do not write a second full native skill parser.

Extend the existing packaging test rather than maintain a duplicate release suite. This deliberately revises the bundled-default-profile packaging exclusion while keeping skills outside its trait resource tree. Avoid checked-in generated copies and build-time imports of Overspec/ZuAT runtime code.

### 2. Package assets and native state have separate identities

Resource origin is package/version/relative skill path; native identity is agent, user scope, and skill name. Importlib resources can be materialized within a context for the duration of a ZuAT call. Temporary paths are not stored as Overspec ownership or revision identifiers. Editable lookup is anchored to the imported distribution, never cwd.

Use `<selected overspec home>/zuat` as a dedicated ZuAT registry. Existing --home / OVERSPEC_HOME selects that Overspec home, defaulting to ~/.overspec. `--agent-home` independently selects the native user home, defaulting to the actual user home; pass both paths explicitly to ZuAT. Do not store journal content in project `.over/.state.json`. The dedicated registry is for this integration only; exact recorded native references remain the selection authority. No parallel Overspec snapshot database is introduced.

Bind that registry to its native home in the sibling `zuat-home.json`. ZuAT records relative native locators, so recovery must verify this immutable context before interpreting them. Refuse a nonempty registry without a binding rather than infer a destination. This file contains context metadata only; ZuAT remains the sole history and snapshot owner.

### 3. Deliberate Typer commands

Add `overspec skill list`, `status`, `install`, `update`, `history`, `restore`, and `remove`. List shows the packaged catalog without native mutation. Native operations require repeatable `--agent`; target selection is repeatable `--name` or explicit `--all`, mutually exclusive. `restore OPERATION_ID` also takes selected agents/names; --all there means only supported skill targets recorded in that operation, never all assets in the agent home. History/removal/restoration may select recorded historical identities absent from the current package. No invocation installs into all agents by default.

Offer --json consistently, explicit --force only on supported conflict-changing skill operations, and report package/native scopes in human output. Project init/update gain schema publication independently of skill management; sync stays limited to trait guidance. Skill commands work without openspec/config.yaml and without profile activation. Document example flows in README and the existing Overspec bootstrap/configure/diagnose skills rather than copying their full procedures into traits.

### 4. Reuse the pinned public lifecycle

Construct `AssetInput(agent, 'skill', scope='user', source=...)` for each selected package skill. Inspect first. Install absent targets with `Zuat.install(ZuatRequest(...))`; reject existing collisions with actionable update guidance. Update calls `update_asset` for owned outdated content, recognizes current no-ops, and permits supported conflicting/unowned replacement only with explicit force. Keep indeterminate/provider-owned content blocked under ZuAT's own contract.

Use exact verified asset references for removal and public history from this dedicated registry. The pinned Zuat.history implementation ignores its request argument: filter returned records explicitly by recorded identities before displaying or selecting them. Restoration validates the recorded identities and native-home binding first. For a successful single-target install/update/uninstall, call public `revert`: its after-state check permits undoing the expected transition without force while protecting later local edits. Reject a partial selection of a multi-target inversion. For partial/pending recovery, use `restore_all` with exact agent/kind/user-scope/name filters; replacing differing existing content may require explicit force under its snapshot contract. Reject a different native home rather than restoring into the wrong destination. Recovery must work after reopening and without previous package sources, preserving the original snapshot's ownership, including unowned prior content. Do not call broad adopt_all, uninstall_all, or unfiltered restore helpers.

Orchestrate selected targets sequentially, recording independent outcomes and IDs. No implicit compensating batch rollback or retries. Preserve ZuAT's partial/pending evidence and report the explicit next recovery operation. An opaque operation ID is not a Git commit hash.

### 5. Install the companion schema as project content

Extend the same build hook to map the authored `openspec/schemas/overspec` tree to `overspec/_bundled/schemas/overspec` in wheels and retain its authored location in sdists. Validate YAML and referenced template completeness without importing the runtime application. If build-time YAML parsing requires ruamel-yaml, declare it explicitly in build-system requirements, reusing the project's existing YAML dependency. Include schema/template byte parity in the existing distribution fixture.

Normal init first checks its existing-compilation refusal and validates the project/package/state and schema targets. It then installs the schema before invoking OpenSpec change discovery, which may already need the schema named by config.yaml or change metadata. Continue variable setup and compilation only after successful schema publication. Update reconciles the schema and then refreshes compilation. Keep setup-only and sync free of schema writes. --store continues to scope change discovery only; schema installation targets the explicit implementation project's OpenSpec directory, not an external store. Report that a separate planning store needs its own schema availability.

Treat the schema tree as ordinary version-controllable project files, not a fake ZuAT skill. Reuse ZuU ConfinedPath and existing atomic publication helpers. Add a hashed current schema baseline section to project .state.json with schema identity, managed relative paths, and content hashes; do not create a second history directory or per-version manifests. Validate that section and preserve it through all compilation/sync writes. Existing state with no schema baseline proves no prior schema ownership; do not invent one from its package version.

An absent schema is installable. An existing tree with exactly the packaged payload can establish a baseline with an explicit adopted-identical result and no payload rewrite. A differing unmanaged tree is a conflict. Once managed, preflight every old/new target: unchanged old managed files can be updated or retired; new files must not collide; locally edited/deleted managed files cause a conflict; unrelated additions remain. Compare both captured input bytes and confined path evidence before writes. There is no new force-schema option in this scope: resolve conflicts by deliberately reconciling/backing up local files, then retry.

Schema publication and state/setup/compilation do not form an atomic cross-file transaction. Report paths and partial outcomes, preserve usable old state on state-write failure, and avoid claiming ownership of an unverified new tree. Retry can recognize an exact current package tree; other partial trees require reported reconciliation. Git remains the user's way to retain/restore local schema edits; the skill restore command never rolls back schema files.

Preserve config.yaml's schema field and active change metadata. Installing overspec makes it available; bootstrap explains setting `schema: overspec` or selecting it through OpenSpec when desired. Other existing workflows remain selected until explicitly changed.

### 6. Proportional TDD during apply

Follow utility-plan.md. Propose produces planning only; implementation and observed RED/GREEN remain pending. Reuse current distribution/installed-package fixtures, then exercise real ZuAT operations in temporary homes. Validate observable bytes, ownership, history, isolation, and exit/JSON results rather than only delegation calls. Keep agent-unavailable failures distinct from intended RED.

## Risks / Trade-offs

- Existing openspec-* names can collide with separately installed OpenSpec skills: status exposes unowned/conflict classifications, install preserves them, and replacement requires explicit force.
- Native providers differ and may be unavailable: expose unsupported/unavailable/partial outcomes; do not promise plugin rollback or silently fall back to copying.
- A package upgrade can remove a skill: installation never silently prunes it; historical selection supports explicit removal/restoration without current source bytes.
- Recovery depends on the retained registry: document its location and operation IDs; removing it is outside skill removal and loses recovery evidence.
- External skills are not in this catalog: preserve references and document prerequisites; never copy this machine's user skills into releases.
- Local schema customizations may block refresh: compare against current installation evidence and report exact conflicts; never overwrite them as a side effect of compilation refresh.
- Schema installation can precede a later setup/compilation failure: report the partial outcome; do not claim ZuAT covers project schema recovery.

## Migration Plan

Publish the wheel/sdist with separate skill and schema assets, then users explicitly run `overspec skill install --agent codex --all`. In a project, normal init installs the schema and establishes compilation; existing initialized projects use update to reconcile schema and compilation. Skill package upgrades use skill status followed by skill update. Record returned operation IDs; restore a selected operation to undo supported skill mutations. Do not migrate existing ZPP or external OpenSpec ownership. Schema selection and project config sync retain their independent responsibilities.
