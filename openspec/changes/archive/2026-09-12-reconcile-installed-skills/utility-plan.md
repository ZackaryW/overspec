# Utility assessment

Caller: ff-change, native design stage; mode: plan. Scope: reconcile-installed-skills.

No new assertions, actions, or utilities are needed. Application behavior changes in the existing skill lifecycle owner and command signatures.

Ponytail assessment: existing Zuat.install handles absent targets; public Zuat.update_asset(asset, force=True) already supplies supported replacement, snapshots, ownership, and current no-ops. Existing restoration and registry/home checks remain valid (41e45c2#1 and #2). Reuse those calls directly; filesystem copying, a new comparison utility, and a second rollback layer are unnecessary. Existing ZuU confinement remains unchanged.

Verification: parameterize the existing real ZuAT lifecycle cases over install/update to establish reconciliation and no-op behavior, adapt conflict coverage to prove automatic replacement plus restoration of unowned and edited bytes, and exercise CLI install refresh plus removal of the force option. No generic utility maturation applies; application RED/GREEN remains for apply.

Interactive revision: inspected pinned zuu.case11 CliSelector(message, choices).select(explicit=(), required=True), Choice(label, value), and Selection(values, cancelled). It provides terminal detection, required choices, and cancellation. Reuse it in the CLI owner; no new generic utility is needed. Test actual selector/state/rendering with controlled terminal input, real ZuAT writes to temporary homes, cancellation, and JSON/noninteractive bypass.
