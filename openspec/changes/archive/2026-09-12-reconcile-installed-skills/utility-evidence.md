# Utility evidence

Native design/tasks stages applied overspec-utilities plan/mature modes. No new utility work was applicable: existing public ZuAT reconciliation, snapshots, ownership, and restore cover replacement; existing ZuU case11 covers CLI selection. Application integration is complete.

## Observed RED

- `uv run pytest tests/test_managed_skills.py tests/test_skill_cli.py -q --tb=short`: 5 failed, 4 passed. Failures established repeated-install rejection, unowned replacement refusal for both commands, and the obsolete force option.
- The interactive selector tests initially failed for a test import issue, corrected before counting RED. The next run observed both interactive calls rejected for missing selections rather than invoking ZuU.
- After selector wiring, cancellation exposed the generic RuntimeError handler catching Typer Exit and converting cancellation into exit 1. The handler now preserves explicit exits. A test variable shadowing the operation name was also corrected; that failure was not implementation RED.

## GREEN and scope

- `uv run pytest tests/test_managed_skills.py tests/test_skill_cli.py tests/test_installed_package.py -q --tb=short`: **15 passed** in 33.12 seconds.
- Real pinned ZuAT/Kimi operations in temporary homes verify install/update replacement of unowned and locally edited content, exact restoration and ownership, repeated current no-ops without new lifecycle history, and native-home checks.
- Actual ZuU selector, renderer, and state transitions run with controlled keyboard actions at the terminal session boundary. Confirmed agent/skill choices drive real native skill installation and historical removal after the catalog is cleared; cancellation writes no native files. JSON bypasses prompts even with terminal streams; noninteractive missing selections fail explicitly. Physical native keyboard input was not manually exercised.
- Installed-wheel lifecycle/schema smoke remains green. No unrelated trait/schema implementation changed; no new dependency or generic utility was introduced.
- Scoped Ruff, edited bootstrap/configure skill validators, CLI help, git diff whitespace, lock consistency, and strict OpenSpec change validation pass. Full unrelated regression was not rerun for this scoped follow-up.

Implementation uses zmem-author-commits; active change artifacts remain outside the implementation commit until final disposition.
