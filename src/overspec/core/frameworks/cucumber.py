"""Cucumber runner evidence, without importing executable configuration."""

from zuu.case13 import deep_get


def detect(evidence):
    if any(evidence.file("cucumber." + suffix)
           for suffix in ("js", "cjs", "mjs", "json", "yaml", "yml")):
        return True
    document = evidence.document("package.json", "json")
    if document is None:
        return False
    found = False
    for group in ("dependencies", "devDependencies", "optionalDependencies"):
        dependencies = deep_get(document, [group], default={})
        if not isinstance(dependencies, dict) or any(
            not isinstance(v, str) for v in dependencies.values()
        ):
            raise ValueError(f"package.json: {group} must map names to version strings")
        found |= "@cucumber/cucumber" in dependencies
    return found
