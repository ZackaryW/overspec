# Utility status

Caller: openspec-propose. Native tasks delegation was evaluated with planning-only intent using the accepted utility-plan.md.

Current status: utility implementation and maturation **complete**; application integration **complete**. The initial planning assessment below is historical; observed implementation evidence follows it.

Planning evidence: existing Hatchling hook and distribution fixtures inspected; imported package resource pattern inspected; pinned ZuAT public API signatures inspected; ZuU confinement contract inspected; prior single-authored-package decision corroborated through zmem. These establish a reuse plan, not implementation verification.

During apply, append actual commands, intended RED reasons, GREEN outcomes, and remaining integration limitations here. Do not infer completion from artifact existence.

Schema scope revision at planning time: user approved folding schema/template packaging and project installation into this change. Current init/update, state shape validation, and the authored schema were inspected. The revised plan included schema-specific payload/planning work and integration ordering, with implementation then pending.

## Package utility milestone

RED: distribution checks observed absent skill/schema wheel assets and acceptance of a missing template (2 failed, 4 passed). New catalog check observed missing public module. GREEN: `uv run pytest tests/test_distribution.py -q --tb=short` (6 passed); `uv run pytest tests/test_installed_package.py::test_installed_resources_are_unchanged tests/test_skill_assets.py -q --tb=short` (3 passed). Installed isolated Python verified skill support files outside the checkout. Schema publication and skill lifecycle remain pending.

## Schema publication milestone

RED: missing schema module; then a directory collision case proved the initial implementation could publish schema.yaml before encountering a later directory target. Added complete target preflight. GREEN: schema/setup/current-state checks (22 passed); installed package/schema checks (8 passed), including native `openspec schema validate overspec` in a consumer project. Partial state-receipt failure preserves previous state and reports completed schema paths. Skills remain pending.

## Managed skills and final integration

RED: the lifecycle module and CLI group were initially absent. Real ZuAT calls then exposed snapshot restoration's force semantics; public after-state-checked revert supplies ordinary successful-operation undo, with filtered restore_all retained for partial recovery. A later focused exception test observed an unstructured native error; another observed loss of an earlier successful removal when the next target raised. Error boundaries now retain per-target outcomes. Invalid packaged YAML similarly moved from an unhandled parser exception to an actionable package error after observed RED.

GREEN: real ZuAT/Kimi operations in isolated registry/native homes verified install, source update, current no-op, reopen, exact body/support restoration, original unowned ownership, protected later edits, historical removal, mismatched-home rejection, and partial target outcomes. CLI tests exercised explicit selection, JSON errors, and operation outside a project. The installed-wheel smoke exercised install/update/restore and native OpenSpec schema validation, change creation, design instructions, and template loading in a clean consumer project. Zip resource extraction remained available through its context and was cleaned up afterward. Schema target races and state-receipt failures preserved local bytes/old state and reported partial publication.

Final verification:
- `uv run pytest -q --tb=short`: **310 passed, 1 skipped** in 74.38 seconds, before the final batch-removal exception regression.
- After observing/fixing that regression, `uv run pytest tests/test_managed_skills.py tests/test_skill_cli.py tests/test_installed_package.py -q --tb=short`: **10 passed** in 24.21 seconds.
- Scoped Ruff checks pass for new modules and changed tests. The wider check still reports five preexisting storage.py style diagnostics (four TRY004 and one SIM102), corroborated against the pre-change source; no error-handling contract was changed merely to silence them.
- `uv lock --check` passes; existing distribution tests build wheels directly and from sdist with exact payload comparisons.
- `openspec validate --all --strict`: **11 passed**; `openspec validate --archived --strict`: **2 passed**.
- Edited bootstrap/configure/diagnose skill validators pass; CLI skill/restore help and `git diff --check` pass.

Limitations: native lifecycle behavior was exercised through the real pinned ZuAT Kimi adapter in temporary homes, not every supported native agent installation. Other agents retain ZuAT prerequisite/provider diagnostics. Multi-target work is sequential and recoverable per target, not atomic. Project schema recovery uses ordinary project files/current baseline, not ZuAT skill history. No real user skill installation or project schema selection was changed during verification.

Implementation milestones: `1b60dd4` packages the assets; `66c61cb` installs the project schema; `41e45c2` completes skill lifecycle, failure handling, and documentation. Commit messages passed zmem validation and were inspected after creation. Active change artifacts stay outside incremental commits until the user selects final disposition.
