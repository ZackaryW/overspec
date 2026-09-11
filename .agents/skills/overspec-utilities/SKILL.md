---
name: overspec-utilities
description: Plan reusable utility responsibilities and mature accepted utility slices through observed RED and GREEN when delegated by native OpenSpec stages. Application wiring remains for apply-change.
---

# Overspec Utilities

Accept the owning native instruction JSON, the caller (`ff-change`, `propose`,
or explicit apply), its resolved project and changeRoot, and mode (`plan` or
`mature`). Read current context and rules first, including applicable
Overspec runtime commands with the exact changeRoot. Respect source-of-truth
and allowedEditRoots from native status. Do not infer a store from cwd.

Invoke a mode only when its resolved policy is enabled: `utility-plan` for plan,
`utility-mature` for mature. A stage may load this skill to understand a pending
reference; loading it does not bypass a disabled policy. If no policy body is
returned, record disabled and leave required work pending. Unanswered material
decisions block their dependent work; wait for explicit answers.

## Plan

Start by asking whether this accepted change needs any implementation at all.
For a trait migration, assess whether existing assertions, actions, grouped
conditions, variables, and attachments already express the requested guidance.
If they do, conclude **no new assertions, actions, or utilities needed**. Record
that assessment and return; utility maturation and RED/GREEN are not applicable.
Validate the authored traits and resolved guidance proportionally. Do not invent
new detectors, source changes, test suites, or disposable demonstrations merely
to exercise the procedure. An actual missing capability is a separate scope
decision, not automatic permission to expand a trait update.

Read accepted proposal/specs, relevant implementation, tests, dependencies, and
repository memory. Use the project's established discovery tools. Perform a
Ponytail assessment: derive necessary responsibilities, inspect existing project
or dependency APIs, and explain concrete fit or mismatch before planning custom
mechanics. When zuu guidance applies, inspect the installed public cases and
their contracts rather than assuming capabilities from names.

For each necessary utility record ownership, its public signature, inputs,
outputs, side effects, errors, and the smallest meaningful verification. Separate
pure case matrices from tests that must cross the real integration boundary.
Keep application decisions in their owner; avoid wrappers that merely rename a
dependency and avoid new general frameworks for a single application rule.

Write `utility-plan.md` inside the exact changeRoot and link it from design.md.
Use an existing accepted plan if still valid; revise it when accepted behavior
changes. If no utility responsibility exists, record not applicable with evidence
and leave application work visible. Do not create artificial utilities or tests.

## Mature

`propose` is planning-only: record utility implementation pending and return
without changing project code or running a fabricated RED/GREEN cycle. During
`ff-change`, follow only the accepted utility plan; application wiring remains
pending for apply. An explicit apply invocation may complete those remaining tasks.

Require a current accepted plan. If planning is disabled or absent, use a supplied
valid plan only; otherwise record the missing plan and leave utility work pending.
Do not silently perform planning under the maturation switch. A missing referenced
skill is a prerequisite failure, not permission to copy or invent its procedure.

For each planned utility slice:

1. Write the smallest meaningful failing test before changing its implementation.
   Run it. Inspect the failure and establish the intended missing behavior;
   dependency, fixture, syntax, or environment failures do not establish RED.
2. Implement that slice using the accepted reuse decisions. Run its tests and
   observe GREEN. Correct implementation rather than weakening the contract.
3. Refactor under passing tests, then run affected checks. Record exact commands,
   outcomes, and the scope they establish in `utility-evidence.md` in changeRoot.
4. Mark only verified utility tasks complete. Keep application wiring and broader
   integration tasks pending. Follow applicable commit guidance with existing
   authorization; preserve active change artifacts outside milestone commits.

On resume, read existing tasks, plan, and evidence even if artifact status says
done. Reuse evidence only when it still covers the current implementation and
accepted behavior; rerun checks when changes or unresolved concerns justify it.
Do not infer execution from test-file existence or generate empty milestone commits.

Return utility scope as verified, disabled, not applicable, or pending with the
specific reason. State remaining application work. Never label utility GREEN as
whole-feature completion.

## Inputs and records

Native artifact instructions carry `context`, `rules`, `instruction`, dependencies,
and resolved output paths. Direct policy guidance in the stage rules enables its referenced mode without a
runtime call. When the input instead supplies a runtime command, execute it and
use its returned names/bodies. Do not call the runtime resolver for a compiled
policy. Absence of applicable direct or resolved guidance disables the mode.
Obtain changeRoot and edit scope from current native status. Do not treat synthetic
test inputs as proof that native caller integration works.

A plan is accepted when it reflects the behavior and scope already authorized by
the user and has no unresolved material choices; a new approval ceremony is not
required. Before reuse, compare its contracts with current specs, implementation,
and dependency APIs. Explain and settle material mismatches before dependent work.

Record verified commands in `utility-evidence.md` and link them from tasks.md.
Record disabled/pending/not-applicable outcomes in the same file without claiming
tests ran; retain required unchecked tasks. This record is evidence for the agent,
not another CLI state machine. If artifact writes themselves are outside the
authorized scope, return the status in conversation instead.
