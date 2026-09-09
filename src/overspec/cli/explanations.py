"""Human-readable condition trees, including retained legacy decisions."""

from rich.text import Text
from rich.tree import Tree


def condition_tree(node):
    status = "skipped" if node["skipped"] else str(node["matched"]).lower()
    if "operator" in node:
        label = f"{node['path']}: {node['operator']} -> {status}"
    else:
        negation = "not " if node["negated"] else ""
        label = f"{node['path']}: {negation}{node.get('reason', '')} -> {status}"
    tree = Tree(Text(label))
    for child in node.get("children", []):
        tree.add(condition_tree(child))
    return tree


def explanation_tree(item):
    tree = Tree(Text(f"Conditions: {item['name']}"))
    decision = item.get("decision") or {}
    if "condition" in decision:
        tree.add(condition_tree(decision["condition"]))
    else:
        for assertion in decision.get("assertions", []):
            negation = "not " if assertion["negated"] else ""
            tree.add(Text(f"{negation}{assertion['reason']} -> {assertion['matched']}"))
    return tree
