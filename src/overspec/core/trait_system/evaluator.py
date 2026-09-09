"""Ordered phase execution through assertion and action contracts."""

from copy import deepcopy

from .models import PHASES, ConditionGroup, EvaluationContext, Suppress
from .rendering import render


def validate_references(traits):
    inventory = {t.name: t for t in traits}
    for trait in traits:
        for leaf in trait.condition.leaves():
            if leaf.handler.runtime_only and trait.phase != "runtime-trait":
                raise ValueError(
                    f"{trait.origin}: {leaf.path}: runtime predicate in earlier phase {trait.name}"
                )
        for handler, is_action, path in [
            (leaf.handler, False, leaf.path) for leaf in trait.condition.leaves()
        ] + [(a, True, f"actions.{i}") for i, a in enumerate(trait.actions, 1)]:
            location = f"{trait.origin}: {path}"
            for name in handler.references():
                if name not in inventory:
                    raise ValueError(f"{location}: Unknown referenced trait {name}")
                target = inventory[name]
                if PHASES.index(target.phase) > PHASES.index(trait.phase):
                    raise ValueError(
                        f"{location}: {trait.name} references later phase {name}"
                    )
                if trait.phase == "runtime-trait":
                    if is_action and target.phase != "runtime-trait":
                        raise ValueError(
                            f"{location}: Runtime suppression cannot target an earlier phase"
                        )
                    if (
                        target.phase == "runtime-trait"
                        and target.attach != trait.attach
                    ):
                        raise ValueError(
                            f"{location}: Runtime reference crosses attachment group"
                        )


def evaluate_condition(node, context, decisions, *, skipped=False):
    trace = {"path": node.path, "matched": None, "skipped": skipped}
    if not isinstance(node, ConditionGroup):
        trace["negated"] = node.negated
        if not skipped:
            try:
                result = node.handler.evaluate(context)
            except (ValueError, OSError) as exc:
                raise ValueError(f"{node.path}: {exc}") from exc
            trace["matched"] = not result.matched if node.negated else result.matched
            trace["reason"] = result.reason
            decisions.append(
                {key: trace[key] for key in ("matched", "negated", "reason")}
            )
        return trace
    trace.update(operator="OR" if node.any_child else "AND", children=[])
    # An omitted assertion or legacy empty list is unconditional, even with OR.
    success = not node.children or not node.any_child
    stop = skipped
    for child in node.children:
        child_trace = evaluate_condition(child, context, decisions, skipped=stop)
        trace["children"].append(child_trace)
        if not stop:
            success = child_trace["matched"]
            stop = success if node.any_child else not success
    if not skipped:
        trace["matched"] = success
    return trace


def evaluate(traits, project, *, prior=None, values=None, runtime=None):
    state = (
        deepcopy(prior)
        if prior is not None
        else {"matched": [], "suppressed": [], "bodies": {}, "decisions": {}}
    )
    matched = set(state["matched"])
    suppressed = set(state["suppressed"])
    for trait in traits:
        context = EvaluationContext(project, frozenset(matched), runtime or {})
        decisions = []
        try:
            condition = evaluate_condition(trait.condition, context, decisions)
            success = condition["matched"]
            state["decisions"][trait.name] = {
                "matched": success,
                "assertions": decisions,
                "condition": condition,
            }
            if not success:
                continue
            matched.add(trait.name)
            state["bodies"][trait.name] = render(trait.body, values or {})
            for action in trait.actions:
                effect = action.evaluate(context)
                if not isinstance(effect, Suppress):
                    raise TypeError(f"Unsupported action effect: {effect}")
                suppressed.add(effect.name)
        except (ValueError, OSError) as exc:
            raise ValueError(f"{trait.origin} ({trait.name}): {exc}") from exc
    state["matched"] = sorted(matched)
    state["suppressed"] = sorted(suppressed)
    return state
