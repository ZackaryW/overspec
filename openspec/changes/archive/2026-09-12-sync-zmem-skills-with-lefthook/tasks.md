## 1. Upstream prerequisite

- [x] 1.1 Complete Saucepan's add-unscoped-acquisition first and select a compatible executable/SDK revision; verify identity-free folder acquisition in an isolated store, declare the maintenance dependencies in scripts/pyproject.toml and scripts/uv.lock without changing Overspec application dependencies or the root lockfile, and verify the scripts environment does not install Overspec.

## 2. Script and hook

- [x] 2.1 RED: add a focused integration test under scripts/tests/ using a controlled local Git source and real Saucepan; verify initial copy, support-file changes/removals, no-op behavior, provenance, and preservation of unrelated skills, with failures attributable to the missing sync behavior.
- [x] 2.2 GREEN: implement scripts/sync_zmem_skills.py and any local helpers entirely under scripts/ using the accepted reuse plan; verify the command runs with Overspec uninstalled and no application imports, verify the integration case passes and invalid/incomplete input leaves all three destination trees unchanged. Add an observed failure-injection regression before implementing recovery and verify failed publication reports retained recovery paths.
- [x] 2.3 Add Lefthook configuration and maintainer setup documentation, including an initialized Saucepan store, executable selection, the independent scripts environment, and hook installation; invoke uv run --project scripts scripts/sync_zmem_skills.py from Lefthook and verify the hook stops after changed content, succeeds after an unchanged refresh, and reports missing prerequisites without fallback or auto-staging.

## 3. Refresh and distribution verification

- [x] 3.1 Refresh the three skills from zmem main, review their complete trees and provenance, and verify only the allowlisted skill directories and provenance are synchronized.
- [x] 3.2 Run existing direct-wheel/source-distribution parity and isolated installed-resource tests against the refreshed snapshot with acquisition unavailable during build/use; record observed outcomes and confirm complete support files remain bundled.

Utility planning is complete in [utility-plan.md](utility-plan.md). [utility-evidence.md](utility-evidence.md) records planning-only status; no implementation or RED/GREEN is claimed during propose.
