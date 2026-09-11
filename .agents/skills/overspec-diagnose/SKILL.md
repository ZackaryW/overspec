---
name: overspec-diagnose
description: Explain missing, unexpected, stale, or overridden Overspec guidance by tracing source precedence, trait lifetimes, settings, and runtime inputs. Use for read-only troubleshooting before a repair.
---

# Diagnose Overspec guidance

Start with the named policy, observed output, and owning project. Inspect current
CLI help and preserve explicit --project/--home and OpenSpec --store choices.
Use these read-only inputs proportionally:

- `overspec trait resolve --explain --json`: effective origins, retained eligibility,
  suppression, assertion decisions, and compiled setting key/enabled decisions.
- `overspec sync --dry-run --json`: candidate output, errors, and the exact diff.
- `overspec trait show <name> --details --json`: saved documentation from the last
  successful sync. Details are not a live-runtime evaluation.

Separate four causes:

1. **Source selection:** package default is lowest priority, acquired repository
   contributions follow, and workspace declarations win. Same-name definitions
   replace whole declarations. Profile mode off still selects default. Management
   commands appear only when enabled; avoid toggling mode just to inspect it.
2. **Retained eligibility:** compile-time assertions/bodies change at init/update.
   Normal traits evaluate at sync. A newly available tool does not change a frozen
   result until update; an off publication setting does not erase matched history.
3. **Publication setting:** an eligible compiled trait's setting key is checked at
   sync using project variables. False suppresses its body, missing enables it,
   and nonboolean values fail. Inspect higher-precedence overrides. Explain exposes
   this gate separately from assertion matching.
4. **Runtime inputs:** execute only actual runtime commands with --attach and
   --trait, plus --context-file/--change-root when applicable. They load current
   definitions and variables without --resolution. Removed or moved names require
   resyncing the emitted selection; body/condition/variable edits do not.

Read [controls](../overspec-bootstrap/references/controls.md) for variable layers
and state recovery. Missing or corrupt state is evidence to report, not permission
to delete it. An old --resolution runtime command needs config regeneration;
--resolution remains valid only for saved detail lookup. Remote discovery reads
already acquired sources and does not authorize retrieval.

Return the cause, supporting output/source, and smallest repair. Do not initialize,
update, sync, edit settings, fetch, or change lifecycle state during a diagnosis-only
request. If repair is already requested, apply the relevant bootstrap/configure/sync
skill and verify its actual effect.
