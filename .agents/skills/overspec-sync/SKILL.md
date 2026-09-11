---
name: overspec-sync
description: Preview and synchronize Overspec guidance into OpenSpec config, choosing init or update only when the compilation lifecycle requires it. Use when publishing trait or policy-setting changes.
---

# Sync Overspec guidance

Bind commands to the owning project with `--project <root>` and preserve any
explicit `--home`. In the Overspec checkout use `uv run overspec`. OpenSpec stores
select change artifacts; they do not redirect the owning project's config.

1. Inspect current CLI help, `openspec/config.yaml`, and the requested source or
   setting edits. Use `overspec trait resolve --explain --json` to inspect origins,
   eligibility, suppression, and setting decisions.
2. Preview with `overspec sync --dry-run --json`. It writes nothing. A missing
   compilation needs first setup via overspec-bootstrap; incompatible compiled
   declarations or body variables need `overspec update` before retrying. A
   setting-only toggle needs sync, not update. Do not refresh frozen checks just
   because the environment changed.
3. Read the candidate/diff. Sync owns context, artifact rules, and supported
   operation guidance, so edit the trait sources rather than the generated body.
   When synchronization is requested, run `overspec sync --json` and verify a
   repeated sync reports changed=false.
4. Check the expected direct guidance and markers. Compile-time traits may have
   `setting = "key"`: false omits their retained body at sync. Normal traits are
   evaluated at sync. Only runtime traits emit commands; exercise relevant ones
   using their attachment/names and the caller's exact change/context.

Report what changed and what remained disabled or unmatched. A successful sync
is not evidence that an OpenSpec implementation is complete. Publishing config
does not authorize fetching sources, activating profiles, or archiving changes.
Use overspec-diagnose for source, variable, or state errors that need explanation.
