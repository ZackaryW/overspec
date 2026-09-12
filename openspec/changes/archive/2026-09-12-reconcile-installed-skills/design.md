## Context

See proposal.md. The lifecycle already inspects selected sources and calls pinned ZuAT APIs. Install currently rejects existing content and update forwards a user force flag. The accepted [utility plan](utility-plan.md) identifies no new utility responsibility.

## Goals / Non-Goals

**Goals:** Explicit selected install/update reconciles differing content automatically, with current no-ops and recoverable prior content/ownership.

**Non-Goals:** Changing restore/remove force semantics, project schema publication, broad native selection, new dependencies, compatibility aliases, or bypassing native identity/provider validation.

## Decisions

- Keep absent installation through Zuat.install; route existing installation and updates through update_asset(force=True). Its current no-op and recovery handling avoid duplicate comparison/snapshot logic. Update keeps its existing-target scope.
- Expose force only for restore/remove. Keeping an ineffective update force switch would obscure the new unconditional reconciliation contract; no alias is retained.
- Reuse the native target selection and immutable home binding. No application process installs into a real user home during verification.

- Use existing ZuU case11 CliSelector/Choice directly in the CLI owner for missing selections. Pass required=True; treat cancellation as exit 130. JSON mode never prompts. Catalog operations select package names; history/remove/restore select recorded names, restricted to the supplied operation ID for restore. All selection finishes before native mutation; no new generic picker utility or dependency is needed.

## Risks / Trade-offs

- Selected locally edited or unowned content will be replaced by design. Make this visible in help/docs and retain operation IDs plus original ownership for restoration.
- ZuAT can still refuse malformed identities or unsupported/provider-owned targets. Preserve diagnostics and partial outcomes; automatic replacement is not permission to bypass those contracts.

## Migration Plan

Use install for initial setup or refresh; update remains usable for existing targets. Remove --force from install/update invocations. Existing restore/remove commands and retained history remain usable.
