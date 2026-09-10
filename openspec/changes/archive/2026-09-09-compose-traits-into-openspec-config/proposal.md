## Why

Project guidance such as zuat's OpenSpec configuration should be reusable and conditional without requiring a separate ZPP workflow system. Overspec will resolve profiles and traits at their declared evaluation times, then supply guidance through native OpenSpec configuration fields.

## What Changes

- Use `default` automatically with project-local overrides while profile mode is off, requiring no activation for ordinary trait composition. Combine the effective profile with recursively discovered local `openspec/.over/**/trait*.toml` files outside profile directories. Profile identity is removed from output names, not from source storage.
- **BREAKING**: Make `overspec profile activate` a user-level feature toggle. Only when enabled, expose profile management commands and select a profile through `OVERSPEC_PROFILE`, then the persisted user selection, then `default`. Remove project-level profile selection, invocation `--profile`, and the proposed activation alias; backward compatibility with that profile interface is not required.
- In enabled profile mode, discover named `profile-*` sources and support explicit retrieval through zuu's public GitHub-subpath utility. Disabling mode restores default resolution without deleting authored or retrieved sources.
- Maintain this repository's reusable default profile under `openspec/.over/profile-default/`, including an unconditional TDD trait and a zuu-reuse trait gated on Python/uv project files and a declared zuu dependency. The repository consumes that same source; its initial apply guidance is seeded from those traits until sync is available.
- Support `[[compiletime-trait]]` evaluated at init/update, `[[trait]]` evaluated at sync, and `[[runtime-trait]]` evaluated when an embedded resolution command runs.
- Require `name`, `attach`, and `body`; support the sketch's assertions, assertion grouping, and output-suppression actions. Attachments target context, artifact rules, or apply/archive guidance.
- Prefer recursive numbered `assert` tables with per-group `or` and `[[...assertion]]` leaves for readable grouped conditions. Preserve flat assertion compatibility, leading-`~` negation, short-circuit behavior, and saved resolutions; migrate the default profile without changing its conditions.
- Keep each trait body small and self-contained, with optional prose `details` for elaboration. Sync and normal runtime output emit bodies only; a read-only detail lookup retrieves the explanation from the same retained resolution, including for static traits.
- Use short name-only provenance markers: `<!-- over:<name> -->` for context fragments and `# over:<name>` on YAML list items. Dynamic body changes retain their trait identity.
- Emit one command per runtime resolution/attachment group, bundling its unique trait IDs into `overspec trait resolve ...`, rather than duplicating commands or embedding unconditional runtime bodies.
- Replace context, rules, and apply/archive guidance on sync; preserve other configuration fields. Include preview, marker-aware no-op detection, stale-output removal, and validated atomic config replacement.

## Capabilities

### New Capabilities

- `trait-composition`: Profile discovery, activation and retrieval; local trait discovery; three evaluation lifetimes; assertions, attachments, small bodies with optional details, dynamic bodies, and profile-independent identity.
- `openspec-config-sync`: Body-only native configuration projection, short provenance markers, retained detail lookup, bundled runtime-resolution commands, and explicit repeatable synchronization.

### Modified Capabilities

None. These remain new capabilities in the existing change.

## Impact

- Implement the currently scaffolded core and CLI packages, including the placeholder assertion module, profile management, compiled state, and runtime resolution bundles. Preserve `core/assertions/`, `core/actions/`, and `core/trait_system/`: assertions and actions each have an abstract base class and one concrete implementation per file, with orchestration in trait_system.
- Use the existing zuu dependency through public APIs. The inspected `zuu.case12.GitHubSubpath` supports public GitHub directory sources with branch/default-branch or full-commit selection; broader remote providers are not promised by this change.
- Prefer relevant public zuu utilities throughout implementation and record specific contract mismatches for custom mechanics. Follow the default profile's observed red, minimal implementation, verified green, and refactor cycle for implementation behavior changes.
- Add TOML parsing, YAML round-trip support, behavioral tests, companion-OpenSpec integration checks, and examples.
- Provide a Typer/Rich CLI with grouped help, a profile command surface that expands only after activation, profile/explanation tables, readable sync previews, and literal guidance and JSON output.
- Keep OpenSpec authoritative for schemas, artifacts, and lifecycle state. Runtime commands supply advisory guidance and do not enforce an archive prohibition themselves.
- Do not change sibling repositories, install agent hooks, recreate ZPP workflow runs, or migrate legacy ZPP documents. Zuat's configuration remains the output reference.
