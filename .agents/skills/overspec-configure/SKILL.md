---
name: overspec-configure
description: Configure Overspec policy switches, scoped variables, and optional profile selection. Use when enabling or disabling guidance or choosing where a setting should persist.
---

# Configure Overspec

Inspect the effective trait declaration first: its lifetime and setting or
assertion determine when a control applies. Read
[controls](../overspec-bootstrap/references/controls.md) for scope and precedence.
Use the user's selected project/home; do not put authored traits in ~/.overspec.

## Policy switches

For a compiled policy with `setting = "tdd"`, put a real boolean under `[vars]`:

```toml
[vars]
tdd = false
```

Use `openspec/.over/.vars.toml` for a shared committed project choice and
`.current.toml` for a temporary/local override. Preserve existing keys and
comments with TOML-aware edits. If the user has not specified persistence, use
project .vars.toml for a project policy and state that choice. Check higher-priority
layers before claiming the edit wins. Unset means enabled; strings/numbers are
invalid for a referenced compiled setting. Removing a temporary override reveals
the next layer; it does not necessarily enable the policy.

Run overspec-sync for a requested compiled-policy change. A switch-only edit does
not need update. It cannot make a failed compile-time assertion eligible.
Change-root files and invocation JSON do not control shared compiled publication.

For runtime controls, get changeRoot from `openspec status --change <name> --json`
with the user's selected --store, then use that change's .vars.toml or .current.toml
when the request is change-specific. Project layers provide defaults. Invoke the
runtime command with --change-root to verify the effective result; sync is not
needed for runtime variable edits. BDD selection remains `bdd = ["behave"]` with
optional `bdd-behave = false`; it is explicit selection, not framework detection.

## Profile selection

Inspect `overspec profile --help` and current user settings before changing mode.
Default works while mode is off; local default declarations extend/override it.
`profile activate` toggles mode, so do not run it when the requested mode already
holds. Once enabled, `profile use <name>` saves a selection; OVERSPEC_PROFILE can
override it. Re-check help after activation. Existing source precedence remains
package, acquired repositories, workspace. Acquire external repositories only
when the user requests it, using the configured Saucepan scope; configuration
alone is not permission to fetch. Preview affected guidance through overspec-sync.
