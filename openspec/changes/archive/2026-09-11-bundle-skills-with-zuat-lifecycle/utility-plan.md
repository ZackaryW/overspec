# Utility plan

Caller: openspec-update-change, revising the original openspec-propose plan; mode: plan. Scope: this change's proposal and three delta specs, including companion schema requirements added to bundled-default-profile. Native design instructions supply enabled utility-plan guidance. The user selected explicit user-level managed skills and accepted schema installation at project init. No prototype is needed: current installed public APIs and the existing packaging/publication implementation establish the approach; behavior remains to be verified during apply.

## Ponytail assessment

This is an actual package and lifecycle feature, not a trait-only edit. It requires implementation, but no new trait assertions or actions. No new general snapshot, registry, rollback, agent router, or transaction utility is warranted.

| Responsibility | Existing fit | Accepted work |
| --- | --- | --- |
| Single authored release assets | hatch_build.py already force-includes the authored profile into wheel/sdist | Extend the bounded build collector for skill directories/support files and schema/templates; do not import runtime application code in the build hook |
| Installed and editable resource access | core/bundled.py and importlib.resources already establish package identity; zuu.case5.ConfinedPath.inspect checks editable paths | Add a focused skill catalog/materialization utility using those contracts; avoid forcing skills through trait document parsing |
| Native inspection and ownership | Pinned zuat.pub.AssetInput and Zuat.inspect_asset expose classifications and evidence | Call public APIs directly from the skill lifecycle owner; do not recreate ownership checks or adapter protocols |
| Installation, update, removal | Zuat.install(ZuatRequest), update_asset, uninstall with explicit asset_refs | Application orchestration selects exact packaged identities and native contexts |
| History and restoration | Zuat.history, revert(ZuatRequest), and restore_all(operation_id, AssetSelector, force=...) retain content and ownership | Use after-state-checked revert for successful single-target transitions and exact selectors for partial snapshot recovery; bind registry to native home and retain IDs/outcomes |
| CLI rendering | Existing Typer and Rich conventions | New skill command group with JSON output; no project resolution prerequisite |
| Project schema publication | zuu.case5.ConfinedPath and core/storage.py provide confined inspection, atomic writes, and a validated single current state | Add the schema-specific file plan and baseline section; preserve other state sections, preflight local conflicts, and wire normal init/update without a new generic file manager |

Inspected pinned dependency: zuat ae26293ace7e2794893daedf3205949741584206, including installed public service/model signatures. Zuat's managed plugin bundle API has weaker restoration guarantees and is excluded. The local ZuAT source_asset_lifecycle example demonstrates the intended public call sequence but is not treated as test evidence for Overspec.

Repository memory: 7cb744f2#1 and current hatch_build.py corroborate one authored source mapped at build time. 3d9e7850#2 cautions against invented utility work. No copied ZuAT internals or wrapper that merely renames a public call is needed.

## Narrow utility contract

Owner: proposed `core/skill_assets.py`.

- `skill_catalog() -> tuple[SkillAsset, ...]`: deterministic validated inventory with names, relative origins, installed version, and payload identities. Reads imported package resources or its verified editable source; does not inspect native installations or mutate them. Missing/incomplete/ambiguous resources produce actionable package diagnostics.
- `materialize_skills(names) -> ContextManager[tuple[SkillSource, ...]]`: validates exact catalog selection and yields complete filesystem source directories for ZuAT. Reuses directly addressable resources where possible; temporary extraction is confined and lives through all dependent calls. No persistent copy, implicit remote retrieval, or durable path-based identity.

Use standard importlib.resources context management and existing ZuU confinement where they fit. Keep build-time collection separate from installed lifecycle dependencies. Application orchestration and CLI wiring are not additional generic utilities. Existing one-assertion/action-per-file structure remains unchanged.

Additional schema responsibility: proposed `core/schema_assets.py` supplies `schema_payload()` with the imported package's schema/template bytes and relative origins, and `plan_schema_install(project_root, payload, baseline)` returns desired writes/removals, no-ops, and conflicts without writing. Its inputs are the verified package payload and validated current baseline; its output is bounded to openspec/schemas/overspec. Missing/invalid package files or redirected targets fail; differing unmanaged or locally edited managed files are conflicts. Init/update own publication order and baseline persistence using existing storage primitives. No new assertion/action, generic transaction utility, or schema history engine is needed.

The existing storage validator accepts only the current exact state shape, so adding schema evidence requires explicit validator/constructor/publisher updates and preservation checks, not merely writing an extra JSON field. An absent baseline conveys no prior schema ownership. ZuAT skill snapshots do not support generic OpenSpec schema installation and must not be repurposed to pretend these are native skills.

## Focused verification

During apply, first extend the existing release fixture and observe failure because skill assets are absent; implement packaging and observe direct/sdist byte parity. Then verify installed resource access from outside the checkout, including support files and missing-resource diagnostics. These checks establish the utility contract.

Extend that same release verification for schema/template parity. Verify the small schema plan with absent/identical/changed/edited inputs; then verify normal init installs before native OpenSpec discovery, update preserves user edits, schema selection remains unchanged, and state writers preserve the baseline. Include native OpenSpec schema resolution from a clean consuming project. Source/target races or later publication failures must report partial outcomes. No tests are executed merely to populate this planning record.

Application verification then exercises real ZuAT public calls in temporary registry/native homes: install A, inspect, update B, reopen, restore A, and compare body/support bytes and ownership. Add only distinct cases for unowned/local edits, scoped selection, and partial recovery/failed targets. Pure selection cases may use unit tests; mock call assertions alone cannot establish rollback. Native agent prerequisites must be reported explicitly; never use the real user home for tests.

This plan originally recorded pending RED/implementation/GREEN. The observed implementation and verification status is now maintained in utility-evidence.md; planning alone establishes no completion evidence.
