## Context

See proposal.md and [utility-plan.md](utility-plan.md). The custom Hatch build hook already embeds complete immediate skill trees in both wheel and source distribution. Installed readers use importlib.resources. Saucepan is currently an optional application SDK dependency, which this independent maintenance project will not rely on; its present acquire implementation requires an app even when caller options are omitted. The user selected an upstream unscoped feature first, not an Overspec app or direct Git workaround.

## Goals / Non-Goals

**Goals:** A small maintenance hook with traceable upstream content, stable no-op behavior, and a clean boundary between refresh and packaging.

**Non-Goals:** New runtime commands, user-level skill installation, changes to trait discovery, updates to native agent homes, broad plugin management, or a custom acquisition/cache framework.

## Decisions

- Block downstream implementation on Saucepan's `add-unscoped-acquisition`. Use `Saucepan(...).acquire(recipe)` without app/marker/token and consume its returned directory and revision. Recipe: Git origin `https://github.com/ZackaryW/zmem.git`, reference `main`, folder `skills`. Check update/verification status; never accept stale fallback as a fresh refresh.
- Add `scripts/sync_zmem_skills.py` and a pre-commit Lefthook job. Declare and lock Saucepan SDK, ZuU, and test dependencies independently in `scripts/pyproject.toml` and `scripts/uv.lock`. Lefthook invokes `uv run --project scripts scripts/sync_zmem_skills.py`; it does not invoke `overspec` or resolve the root project environment. Document executable/store initialization plus `lefthook install`; builds do not run the hook. Provide an explicit binary option for maintainers and controlled tests. Do not auto-download executables or change an app registration.
- Keep all maintenance implementation, helpers, and focused tests under `scripts/` (tests under `scripts/tests/`). Import no `overspec.*` module, root build hook, or application configuration. Obtain the destination repository from an explicit root argument, defaulting to the script's parent repository; the repository is a data destination, not an installed dependency.
- Own exactly three named directories, including obsolete files inside them. Acquire once so all three come from one revision. Validate and stage complete payloads before replacing local content. Use ZuU path confinement and snapshots; retain backups until publication finishes. On failure restore what can be restored and clearly report any remaining recovery paths. Do not claim a cross-directory filesystem transaction.
- Record URL, revision, selected names and file SHA-256 values in `.agents/zmem-skills.json`, outside the skill catalog. Avoid volatile timestamps and cache paths. A new source revision may update provenance even when skill bytes are unchanged; identical revision and payload is a no-op.
- Hook mode refreshes automatically, reports changed paths, and exits nonzero when review/staging is required. It does not auto-stage. This keeps upstream edits reviewable and avoids capturing unrelated staged/unstaged work. A manual refresh command uses the same script. Network/prerequisite failures are explicit, not silently ignored.
- Retain the existing build path unchanged. The three trees and provenance are committed maintenance inputs. Existing vendored untracked copies are compared against the acquired revision during apply rather than treated as proof of upstream freshness.
- Prototype is not needed because the folder layout and existing package tests establish the copy/build boundary. Use focused RED/GREEN during apply, with an actual isolated Saucepan store and local Git fixture for deterministic integration.

## Risks / Trade-offs

- Main can advance between commits → log the resolved immutable revision and preserve reviewable Git diffs; do not fetch during build.
- A network-backed pre-commit job can fail offline → report failure and document the maintainer prerequisite; no silent cache success.
- Three directory replacements cannot be one atomic filesystem operation → stage first, retain recovery copies, and report partial recovery explicitly.
- Saucepan capability is not available yet → dependency remains visible in tasks; do not claim this hook is runnable before the upstream change is delivered.

## Migration Plan

Complete Saucepan's proposal first, then pin the compatible SDK in the scripts project and identify the required executable revision independently of Overspec. The SDK already forwards omitted identity, so its existing revision works with the new executable; the executable must contain the unscoped implementation. Verify the script in an isolated environment with Overspec unavailable, then implement the hook, refresh the three skills, review/stage their content and provenance, then verify wheel and source-distribution parity plus installed resource use. Git restores the prior vendored snapshot and hook configuration if rollback is needed.
