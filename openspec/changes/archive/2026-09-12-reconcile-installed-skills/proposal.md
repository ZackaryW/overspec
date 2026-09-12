## Why

Users expect installing the packaged skill catalog to bring selected skills to the packaged version. The current absent-only install and force-gated update require extra commands for an ordinary refresh; the user explicitly wants differing skills overwritten.

## What Changes

- **BREAKING**: install reconciles selected existing skills as well as installing missing skills; update replaces differing existing skills automatically, including supported unowned and locally edited targets.
- Identical managed content remains a no-op; replacements retain ZuAT recovery history and original ownership evidence.
- Remove the install/update force switch. Explicit force remains available for restoration and removal; invalid identities and provider boundaries still fail.
- Use ZuU case11 checklists to select omitted agents and skills in an interactive terminal. Explicit selections and JSON/noninteractive errors remain available for scripts. Cancellation performs no native mutation.
- Update command help and packaged workflow documentation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `managed-skill-lifecycle`: make explicit installation/update selection sufficient to reconcile differing content, preserving scoped recovery.

## Impact

Existing skill lifecycle orchestration, Typer help/options, README, and bootstrap/configure guidance. Reuse pinned ZuAT update_asset and existing test fixtures; no dependency, schema, trait, assertion, action, or general utility changes. The already tested forced replacement and restoration API makes a separate prototype unnecessary.
