## Why

Installed Overspec supplies its default traits but omits the skills and companion OpenSpec schema needed to reproduce this repository's workflow without a checkout. Shipping both assets completes project setup, while the already pinned ZuAT dependency gives explicit user-level skill updates recoverable content history.

## What Changes

- Include valid skill directories from `.agents/skills`, including native `openspec-*`, companion `overspec-*`, and their supporting files, in wheels and source distributions from a single authored tree.
- Bundle `openspec/schemas/overspec/schema.yaml` and its templates separately; normal project init installs them into `openspec/schemas/overspec`, and update refreshes unchanged managed files while preserving local edits. Keep an installation baseline in the single project state document.
- Add explicit user-level `overspec skill` commands for catalog listing, inspection, installation, update, history, restoration, and removal, with agent selection and structured output.
- Use ZuAT's public independent-skill lifecycle and recoverable snapshots; expose operation IDs and partial outcomes rather than promise a cross-agent transaction.
- Preserve unowned and locally modified skills unless the caller explicitly requests the supported override. Limit operations and restoration to selected Overspec skill identities.
- Keep project init/update/sync, trait profile activation, and Python package installation free of implicit native skill mutations. Schema installation does not change the project's selected schema or an active change's schema; setup-only and sync do not publish schema files.
- Retain external skill references without copying external user skills or reintroducing ZPP compatibility aliases, hooks, or its workflow engine.

## Capabilities

### New Capabilities

- `packaged-agent-skills`: Distribution inventory, support files, provenance, and installed/editable resource access.
- `managed-skill-lifecycle`: Explicit user-scope ZuAT-backed skill operations, ownership, recovery, and CLI results.

### Modified Capabilities

- `bundled-default-profile`: Deliver the companion schema and templates alongside the packaged default, define project installation/refresh behavior, and keep schema and skill assets outside the default trait resource tree.

## Impact

Extends `hatch_build.py`, installed resource access, project init/update and state handling, the Typer command tree, focused distribution/lifecycle tests, README, and Overspec operational skill guidance. Reuses the pinned `zuat.pub` API and existing ZuU path contracts; no dependency upgrade is currently required. Adds a dedicated ZuAT registry below the selected Overspec user home; native agent home remains a separate scope. No implementation, native agent files, or installed schema files are changed by this proposal.
