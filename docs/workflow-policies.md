# Configurable native workflow policies

The bundled default contributes these runtime policies. Guidance is resolved by
the agent from native instruction inputs; the CLI does not execute skills or tests.

| Policy control | Native attachment | Responsibility |
| --- | --- | --- |
| `utility-plan` | `rules.design` | Ponytail reuse assessment and accepted utility contracts |
| `utility-mature` | `rules.tasks` | Utility-only RED → implementation → GREEN during ff-change |
| `integration-test-policies` | `operations.apply.guidance` | Meaningful public-boundary integration evidence |
| `decision-choice` | `operations.explore/propose.guidance` | Grounded material choices and explicit answers |
| `prototype-choice` | `operations.explore/propose.guidance` | Prototype choice or evidence-backed not-needed finding |
| `evidence-first` | `rules.tasks`, `operations.apply.guidance` | Full-scope completion claims and observed checks |
| `bdd-behave`, `bdd-cucumber`, `bdd-flutter` | `operations.apply.guidance` | Independent framework-specific practices |
| `tdd` | `context` | RED/GREEN available before apply too |
| `zuu` | `context` | Public API reuse, when Python/uv files and dependency qualify |

Paired operations use separate trait names (`decision-explore`/`decision-propose`,
`prototype-explore`/`prototype-propose`); one shared control disables both.

## Off controls

Put only the overrides you want under `[vars]` in committed optional
`openspec/.over/.vars.toml` or ignored `.current.toml`. For one change, put either
file directly inside its exact OpenSpec `changeRoot` and pass that root to runtime
resolution. Missing switches inherit the enabled default. Only boolean `false`
disables; the string `"false"` does not. Higher-scope `true` can re-enable a policy.

```toml
[vars]
utility-plan = false
utility-mature = false
integration-test-policies = false
decision-choice = false
prototype-choice = false
evidence-first = false
tdd = false
zuu = false
bdd-behave = false
bdd-cucumber = false
bdd-flutter = false
```

These settings withdraw policy guidance, not independent explicit user instructions.
Runtime file changes apply to saved definitions without resync. No persistent
preferences are created by default. Existing zmem/archive-choice policies retain
their established behavior.

## BDD activation

When `bdd` is absent, the enabled framework traits detect:

- Behave: `behave.ini`, `.behaverc`, `[tool.behave]`, or a normalized Behave
  requirement in `project.dependencies`, any `project.optional-dependencies`, or
  standardized `dependency-groups`. Group includes support normalized names and
  reject cycles, missing groups, and ambiguous normalized names.
- Cucumber: `cucumber.js`, `.cjs`, `.mjs`, `.json`, `.yaml`, or `.yml`, or
  `@cucumber/cucumber` in package.json dependencies, devDependencies, or
  optionalDependencies. Configuration files are not executed.
- Flutter: a Flutter SDK dependency in pubspec.yaml plus its SDK integration_test
  dependency (dependencies or dev_dependencies), or Dart sources under
  `integration_test/`. Language markers alone do not activate a framework.

```toml
[vars]
bdd = ["behave", "cucumber"] # explicit selection replaces detection
bdd-behave = false           # individual off wins
# bdd = []                  # select none
```

Duplicates contribute once. Invalid values or unknown names fail when the assertion
is evaluated. Explicit selection bypasses detection manifests. Missing evidence is
a nonmatch; malformed consumed manifests and redirected evidence are errors.
Detection is read-only and project-confined. Selection never installs a runner.

## Explicit native setup

The `overspec` native schema is opt-in. Default traits alone do not install it or
its referenced skills. To set up the full utility sequence:

1. Use a companion OpenSpec build supporting
   `openspec instructions explore --json` and `openspec instructions propose --json`.
   Each must return its matching `operation`; an unknown-artifact/error result means
   the prerequisite is missing. Version 1.12.0 alone is not sufficient: use a build
   containing the `add-consultation-operation-inputs` change (verified sibling commit
   `3fc57de`). Regenerate native
   explore/propose/ff skills with that build's `openspec update --force`.
2. Explicitly install the `overspec-utilities` skill from `.agents/skills/` in this
   repository into the target agent environment. Confirm it is discoverable.
   Report a missing skill; do not copy its procedure into a trait as a substitute.
3. Copy this repository's `openspec/schemas/overspec/` directory into the selected
   planning root's `openspec/schemas/overspec/`. It derives from native spec-driven
   and retains proposal/specs/design/tasks. Run `openspec schema validate overspec
   --json` there. Select `schema: overspec` in that root's config explicitly.
   Existing changes keep their recorded schema; use `--schema overspec` deliberately
   or update the selected change metadata as part of an authorized schema change.
4. Preview and run Overspec sync. Read native design/tasks instructions for an
   actual change to verify rules, dependencies, and delegation. Do not claim full
   setup from a sync command alone.

`ff-change` consults propose guidance, creates the native artifacts, performs the
enabled accepted utility plan, and reaches observed utility GREEN. Application
wiring stays pending for apply. Propose remains planning-only, including delegated
stages. On ff resume, existing tasks.md does not establish utility completion.

Disabled maturation leaves utility implementation pending. Disabled planning with
no valid supplied plan leaves maturation pending too. No necessary utilities is
an evidence-backed not-applicable result. Unanswered material choices remain
pending. These are agent procedure contracts, not a new workflow engine.

## Verification

`tests/test_native_workflow.py` uses the real companion in isolated project/store
roots. Set `OVERSPEC_TEST_OPENSPEC_CLI` to its `bin/openspec.js` when the sibling
checkout is unavailable. A skipped prerequisite test is not integration success.
Installed-wheel tests verify default trait bytes and resolution without Saucepan;
the wheel does not install agent skills or schemas. Procedure execution requires
recorded actual RED/GREEN evidence in addition to validating the native inputs.
