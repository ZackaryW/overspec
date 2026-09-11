"""Native YAML projection with ownership and scalar-header provenance."""

from copy import deepcopy
from io import StringIO
from collections.abc import Mapping
import re

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import LiteralScalarString
from ruamel.yaml.error import YAMLError
from zuu.case13 import deep_get

from .storage import digest
from zuu.case5 import ConfinedPath, TargetState


def config_target(root):
    for name in ("config.yaml", "config.yml"):
        plan = ConfinedPath("openspec/" + name).inspect(
            root, allowed=(TargetState.FILE, TargetState.ABSENT)
        )
        if plan.state == TargetState.FILE:
            return plan.target
    raise ValueError("Missing openspec/config.yaml or config.yml")


def parse_yaml(text):
    try:
        document = YAML().load(text)
    except YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ValueError("Configuration root must be a mapping")
    if "operations" in document:
        operations = document["operations"]
        if not isinstance(operations, Mapping):
            raise ValueError("operations must be a mapping")
        for operation in ("apply", "archive"):
            if operation in operations and not isinstance(
                operations[operation], Mapping
            ):
                raise ValueError(f"operations.{operation} must be a mapping")
    return document


def destinations(document):
    rules = document.get("rules")
    if isinstance(rules, Mapping):
        for key, value in rules.items():
            yield "rules." + str(key), value
    for operation in ("apply", "archive"):
        yield (
            f"operations.{operation}.guidance",
            deep_get(document, ["operations", operation, "guidance"], default=None),
        )


def markers(document, text):
    lines = text.splitlines()
    result = {}
    for attach, items in destinations(document):
        if isinstance(items, CommentedSeq):
            for index in range(len(items)):
                line = lines[items.lc.item(index)[0]]
                found = re.search(r"[|>][-+0-9]*\s+#\s*over:([a-z0-9,-]+)\s*$", line)
                result[f"{attach}:{index}"] = found.group(1) if found else None
    return result


def owned_fingerprint(text):
    doc = parse_yaml(text)

    # Type-tag scalars so true, 1, and "1" cannot share a receipt fingerprint.
    def token(value):
        if isinstance(value, Mapping):
            return sorted([(repr(k), token(v)) for k, v in value.items()])
        if isinstance(value, list):
            return [token(v) for v in value]
        return [
            type(value).__name__ if not isinstance(value, str) else "str",
            str(value),
        ]

    owned = {
        "context": doc.get("context"),
        "rules": doc.get("rules"),
        **{k: v for k, v in destinations(doc) if k.startswith("operations.")},
    }
    return digest({"owned": token(owned), "markers": markers(doc, text)})


def project_yaml(original, contributions):
    before = parse_yaml(original)
    doc = deepcopy(before)
    doc.pop("context", None)
    doc.pop("rules", None)
    if "operations" in doc:
        # Independently copy each modified ancestor: shared aliases may point at unowned data.
        doc["operations"] = deepcopy(doc["operations"])
        for operation in ("apply", "archive"):
            if operation in doc["operations"]:
                doc["operations"][operation] = deepcopy(doc["operations"][operation])
                doc["operations"][operation].pop("guidance", None)
    expected = {}
    contexts = []
    for item in contributions:
        attach, body, name = item["attach"], item["body"], item["name"]
        if attach == "context":
            contexts.append(body.rstrip("\n") + f"\n<!-- over:{name} -->")
            continue
        if attach.startswith("rules."):
            parent = doc.setdefault("rules", CommentedMap())
            key = attach[6:]
        else:
            parent = doc.setdefault("operations", CommentedMap()).setdefault(
                attach.split(".")[1], CommentedMap()
            )
            key = "guidance"
        items = parent.setdefault(key, CommentedSeq())
        expected[f"{attach}:{len(items)}"] = name
        items.append(LiteralScalarString(body))
    if contexts:
        context = "\n\n".join(contexts) + "\n"
        if len(context.encode("utf-8")) > 50 * 1024:
            raise ValueError("Rendered context exceeds 50 KiB")
        doc["context"] = LiteralScalarString(context)
    if "operations" in doc:
        for operation in ("apply", "archive"):
            if operation in doc["operations"] and not doc["operations"][operation]:
                del doc["operations"][operation]
        if not doc["operations"]:
            del doc["operations"]
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    stream = StringIO()
    yaml.dump(doc, stream)
    text = stream.getvalue()
    parsed = parse_yaml(text)
    lines = text.splitlines(keepends=True)
    # ruamel currently loses comments on sequence block-scalar headers. Use its
    # parsed source positions to attach comments to exact generated nodes.
    for attach, items in destinations(parsed):
        if isinstance(items, CommentedSeq):
            for index in range(len(items)):
                line = items.lc.item(index)[0]
                lines[line] = (
                    lines[line].rstrip("\r\n")
                    + f" # over:{expected[f'{attach}:{index}']}\n"
                )
    text = "".join(lines)
    candidate = parse_yaml(text)
    if before == candidate and markers(before, original) == markers(candidate, text):
        return original, False
    return text, True
