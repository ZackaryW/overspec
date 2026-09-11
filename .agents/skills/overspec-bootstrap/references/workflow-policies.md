# Workflow traits using existing capabilities

This migration changes guidance and configuration only. No new assertion, action,
utility, native command, or test suite is required.

| Guidance | Existing attachment |
| --- | --- |
| Utility assessment | rules.design |
| Conditional utility maturation | rules.tasks |
| Integration-test policies and evidence | operations.apply.guidance |
| Exploration consultation | context, with an exploration-only body |
| Proposal consultation | rules.proposal |
| Task evidence | rules.tasks |
| Selected BDD frameworks | operations.apply.guidance |
| TDD and applicable zuu reuse | context |

Use boolean false under [vars] in optional committed .vars.toml or local ignored
.current.toml, at the project .over or exact selected change root. Controls are:
utility-plan, utility-mature, integration-test-policies, decision-choice,
prototype-choice, evidence-first, tdd, zuu, bdd-behave, bdd-cucumber, bdd-flutter.
Missing controls retain their normal applicability; string "false" is not boolean
false. Runtime overrides use existing precedence and require no resync.

```toml
[vars]
utility-mature = false
bdd = ["behave", "cucumber"]
bdd-behave = false
```

BDD selection uses the existing runtime-context-includes assertion. Missing or
empty bdd selects none. Individual false controls win. There is no new automatic
manifest detector or new invalid-selection validation. Framework guidance asks the
agent to inspect the project's actual fixtures, configuration, and runner.

The optional project-local overspec schema delegates assessment from design and
conditional utility maturation from tasks through existing native instructions.
Install its referenced overspec-utilities skill explicitly when selecting that
schema. Sync does not install skills or schemas. No new OpenSpec build is needed.
The source-generated native workflow skills remain unchanged. Existing artifact
status is file-based; it does not prove delegated work ran or add automatic resume
orchestration.

For this trait migration, utility assessment concludes: no new assertions, actions,
or utilities needed. RED/GREEN is not applicable. Parse declarations and inspect
inventory, supported attachments, controls, and resolved guidance. Do not create
code or a disposable exercise to manufacture work for the planning process.
