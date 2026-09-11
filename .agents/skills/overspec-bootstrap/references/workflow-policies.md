# Workflow policies and lifetimes

Project-wide policies compile at init/update and use a small boolean setting gate
at sync. Operation attachments describe where guidance is delivered, not when its
conditions must run.

| Guidance | Attachment | Control |
| --- | --- | --- |
| Utility assessment | rules.design | utility-plan |
| Conditional utility maturation | rules.tasks | utility-mature |
| Integration-test policies | operations.apply.guidance | integration-test-policies |
| Exploration/proposal consultation | context / rules.proposal | decision-choice |
| Exploration/proposal prototype choice | context / rules.proposal | prototype-choice |
| Task/apply evidence | rules.tasks / operations.apply.guidance | evidence-first |
| TDD and eligible Zuu reuse | context | tdd / zuu |

These declarations use `compiletime-trait` with `setting = "control-key"`.
Put controls under [vars] in project openspec/.over/.vars.toml (shared) or
.current.toml (local). Existing project/user config defaults also participate.
Missing means enabled; a referenced setting must be a real boolean. Change-root
files do not affect these shared policies. Edit a switch and sync; update is only
needed when compiled declarations/body inputs change or eligibility needs refresh.
Zuu's file/dependency assertions remain compiled, so enabling its setting cannot
make an ineligible project match.

```toml
[vars]
utility-mature = false
```

BDD framework selection and the temporary-change archive flag remain runtime.
They can vary by selected change: project defaults, selected change .vars/.current,
and invocation JSON participate through the existing precedence.

```toml
[vars]
bdd = ["behave", "cucumber"]
bdd-behave = false
```

Missing/empty bdd selects none; individual false disables a selected framework.
No manifest detector or new framework assertion is introduced. Runtime commands
load current definitions and values without a saved resolution ID.

The project-local overspec schema delegates utility assessment from design and
conditional maturation from tasks to overspec-utilities. Direct compiled guidance
is a policy input; only actual runtime commands need execution. The skill must
be available in the target environment; sync does not install skills or schemas.
No native OpenSpec source changes are needed. Artifact existence does not prove
utility work ran. If existing APIs suffice, record no new utilities needed and
skip utility RED/GREEN; real application behavior changes still need focused TDD.

Use overspec-create-trait to author policies, overspec-configure to change controls,
overspec-sync to publish guidance, and overspec-diagnose to explain an outcome.
