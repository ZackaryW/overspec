---
name: overspec-bootstrap
description: Orient or initialize an Overspec companion project, explain scoped variables and profile controls, and set up current files for existing or newly created OpenSpec changes. Use when establishing or repairing the project's Overspec workflow.
---

# Bootstrap Overspec

Use the installed CLI to establish the requested project state. OpenSpec owns
changes and artifacts; Overspec composes guidance into its configuration.

## Inspect and choose the next action

1. Confirm the implementation project root and inspect `overspec --help`,
   `overspec init --help`, `overspec profile --help`, and `openspec list --json`.
   In this checkout use `uv run overspec`. Preserve an explicitly selected
   OpenSpec store on list/status/instructions calls; do not infer one from folders.
2. Inspect `openspec/config.yaml`, `.over` sources, and the compilation pointer at
   the compilation section in `openspec/.over/.state.json`. Read
   [references/controls.md](references/controls.md) for file scope, precedence,
   lifetimes, and troubleshooting. Explain that `.vars.toml` is optional shared
   data and `.current.toml` is local state before setting them up.
3. With no compilation, run `overspec init --project <root>` within the requested
   setup scope. With existing compilation, use `overspec init --setup-only` for
   missing current files or new changes. Init discovers active changes; append
   `--store <id>` for a selected store. For exact targets, instead pass repeatable
   `--change-root <path>` values obtained from OpenSpec status. Store and exact
   roots are mutually exclusive. Always keep `--project` bound to the owning
   implementation project, even when changes live in an external store.
4. Inspect setup's per-target and Git-ignore results. A partial failure is not
   success; correct the reported issue and retry, preserving existing files.
   Do not create persistent files unless needed. Do not activate profiles merely
   to use default: mode is off by default and local default overrides still work.
5. Run `overspec trait resolve --explain` and `overspec sync --dry-run`. If relevant
   compiled inputs changed, use explicit `overspec update` within the requested
   scope before retrying. Setup-only never replaces update. Apply `overspec sync`
   when synchronization is requested, inspect the result, and verify a repeated
   sync is unchanged. Runtime calls and details lookup never initialize files.

## Work within the existing workflows

After OpenSpec creates a later change, get its exact `changeRoot` from
`openspec status --change <name> --json`, retaining `--store <id>` when selected.
Run `overspec init --setup-only --project <root> --change-root <changeRoot>`.
Execute emitted runtime commands with that same root; never guess an active
change or bake its variables into shared config. OpenSpec shows these commands
as guidance; it does not automatically execute them.

For trait edits, use `create-overspec-trait`. For each meaningful source
implementation milestone and final post-archive commit work, use
`zmem-author-commits`. Verify referenced skills are available; report a missing
skill without inventing installation or copying its workflow here. Follow
existing commit authorization; a trait reference alone is not authorization.
Incremental implementation commits include all nonignored work except the active
change's own `changeRoot` artifacts. Include `.over`, project config, tests,
skills, canonical specs, and already archived records; do not exclude `openspec/`
as a whole. Keep ignored generated state and `.current.toml` local.

## Before archive handling

Unless the user has already answered for this same archive operation, ask
explicitly whether to **discard**, **archive normally**, **dissolve
into zmem**, or **only form specs**. Describe the concrete affected change and
effects using the reference. Keep the question pending until answered; elapsed
time, an earlier implementation approval, and a value in either vars file are
not an answer. Preserve an existing answer for the same operation without asking
again. Do not archive or remove records while waiting. If dissolution is selected
but zmem or its authoring skill is unavailable, report the limitation and preserve
the records until the user chooses how to proceed.

Follow the selected outcome, then handle final commits with zmem-author-commits.
Retained specs/archive records and authored `.vars.toml` belong in the final
commit when their containing records are retained. `.current.toml` stays local
under every outcome. This skill does not add a new archive CLI or duplicate the
OpenSpec or zmem procedures.
