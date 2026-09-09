from itertools import product

import pytest
from conftest import declaration

from overspec.core.trait_system.evaluator import evaluate, validate_references
from overspec.core.trait_system.sources import parse_document, parse_trait


def leaf(key, *, negate=False):
    return {
        "type": "~runtime-context-match" if negate else "runtime-context-match",
        "kv": f"{key}=true",
    }


def group(*leaves, any_=False):
    return {"or": any_, "assertion": list(leaves)}


def parsed(condition, *, phase="runtime-trait", **extra):
    return parse_trait(
        {
            "name": "sample",
            "attach": "context",
            "body": "Sample",
            "assert": condition,
            **extra,
        },
        phase,
        "trait-groups.toml",
    )


def test_numbered_tables_bind_to_latest_owning_declaration():
    traits = parse_document(
        """
[[trait]]
name = "first"
attach = "context"
body = "First"
[trait.assert.10]
[[trait.assert.10.assertion]]
type = "which"
app = "ten"
[trait.assert.2]
[[trait.assert.2.assertion]]
type = "which"
app = "two"
[[trait]]
name = "second"
attach = "context"
body = "Second"
[trait.assert]
or = true
[[trait.assert.assertion]]
type = "~which"
app = "other"
[[compiletime-trait]]
name = "compiled"
attach = "context"
body = "Compiled"
[compiletime-trait.assert.1]
[[compiletime-trait.assert.1.assertion]]
type = "which"
app = "compiler"
""",
        "traits.toml",
    )
    assert [t.name for t in traits] == ["first", "second", "compiled"]
    assert [h.app for h, _ in traits[0].predicates] == ["two", "ten"]
    assert traits[1].predicates[0][1] is True
    assert traits[2].predicates[0][0].app == "compiler"
    assert (
        traits[0].record()["declaration"]["assert"]["10"]["assertion"][0]["app"]
        == "ten"
    )


@pytest.mark.parametrize(
    "condition,path",
    [
        ({}, "assert"),
        ({"or": True}, "assert"),
        ({"or": "true", "assertion": [leaf("a")]}, "assert"),
        ({"or": 1, "assertion": [leaf("a")]}, "assert"),
        ({"assertion": []}, "assert"),
        ({"assertion": {}}, "assert"),
        ({"1": group(leaf("a")), "assertion": [leaf("b")]}, "assert"),
        ({"0": group(leaf("a"))}, "assert.0"),
        ({"01": group(leaf("a"))}, "assert.01"),
        ({"-1": group(leaf("a"))}, "assert.-1"),
        ({"one": group(leaf("a"))}, "assert.one"),
        ({"1": []}, "assert.1"),
        ({"1": {}}, "assert.1"),
        ({"1": {"assetion": [leaf("a")]}}, "assert.1.assetion"),
        ({"1": {"assertion": [{"type": "unknown"}]}}, "assert.1.assertion.1"),
        ({"1": {"assertion": [{"type": "which"}]}}, "assert.1.assertion.1"),
    ],
)
def test_invalid_groups_report_source_and_condition_path(condition, path):
    with pytest.raises(ValueError) as failure:
        parsed(condition)
    assert "trait-groups.toml" in str(failure.value)
    assert path in str(failure.value)


@pytest.mark.parametrize("flag", [False, True])
def test_group_table_rejects_legacy_operator_even_when_false(flag):
    with pytest.raises(ValueError, match="assert_or_grouping"):
        parsed(group(leaf("a")), assert_or_grouping=flag)


def test_group_records_round_trip_without_flattening():
    condition = {
        "or": True,
        "1": group(leaf("a"), leaf("b", negate=True)),
        "2": {"1": group(leaf("c"))},
    }
    original = parsed(condition)
    reread = parse_document(
        declaration("sample", "runtime-trait", body="Sample", **{"assert": condition}),
        "roundtrip",
    )[0]
    assert original.record()["declaration"] == reread.record()["declaration"]
    assert len(reread.predicates) == 3


@pytest.mark.parametrize("outer_or", [False, True])
def test_nested_truth_tables_and_leaf_negation(tmp_path, outer_or):
    condition = {
        "or": outer_or,
        "1": group(leaf("a"), leaf("b"), any_=not outer_or),
        "2": {"1": group(leaf("c"), leaf("d", negate=True), any_=not outer_or)},
    }
    trait = parsed(condition)
    for a, b, c, d in product([False, True], repeat=4):
        expected = (
            ((a and b) or (c and not d)) if outer_or else ((a or b) and (c or not d))
        )
        state = evaluate([trait], tmp_path, runtime={"a": a, "b": b, "c": c, "d": d})
        assert ("sample" in state["matched"]) == expected, (a, b, c, d, outer_or)


def test_numeric_order_short_circuit_and_skipped_trace(tmp_path, monkeypatch):
    from overspec.core.assertions.which import WhichAssertion
    from overspec.core.trait_system.models import MatchResult

    calls = []

    def probe(self, context):
        calls.append(self.app)
        return MatchResult(self.app != "false", self.app)

    monkeypatch.setattr(WhichAssertion, "evaluate", probe)

    def executable(app):
        return {"type": "which", "app": app}

    trait = parsed(
        {
            "or": True,
            "10": group(executable("never")),
            "2": group(executable("true")),
            "1": group(executable("false"), executable("also-never")),
        },
        phase="trait",
    )
    result = evaluate([trait], tmp_path)
    assert calls == ["false", "true"]
    decision = result["decisions"]["sample"]
    root = decision["condition"]
    assert root["operator"] == "OR" and root["matched"] is True
    assert [c["path"] for c in root["children"]] == [
        "assert.1",
        "assert.2",
        "assert.10",
    ]
    skipped = root["children"][0]["children"][1]
    assert skipped["skipped"] and skipped["matched"] is None
    assert root["children"][2]["skipped"]
    assert len(decision["assertions"]) == 2


@pytest.mark.parametrize(
    "target_phase,target_attach,owner_phase,kind,error",
    [
        (None, "context", "trait", "loaded-trait", "Unknown"),
        ("runtime-trait", "context", "trait", "loaded-trait", "later phase"),
        (
            "runtime-trait",
            "operations.archive.guidance",
            "runtime-trait",
            "loaded-trait",
            "attachment",
        ),
        (None, "context", "trait", "runtime-context-match", "runtime predicate"),
    ],
)
def test_nested_references_validate_even_in_skipped_branches(
    target_phase, target_attach, owner_phase, kind, error
):
    predicate = (
        leaf("flag")
        if kind == "runtime-context-match"
        else {"type": kind, "trait": "target"}
    )
    owner = parsed(
        {
            "or": True,
            "1": group({"type": "which", "app": "python"}),
            "2": {"1": group(predicate)},
        },
        phase=owner_phase,
    )
    traits = [owner]
    if target_phase:
        traits += parse_document(
            declaration("target", target_phase, attach=target_attach), "target.toml"
        )
    with pytest.raises(ValueError, match=error) as failure:
        validate_references(traits)
    assert "trait-groups.toml" in str(failure.value)
    assert "assert.2.1.assertion.1" in str(failure.value)


@pytest.mark.parametrize("operator", [False, True])
def test_legacy_empty_lists_remain_unconditional(tmp_path, operator):
    trait = parsed([], phase="trait", assert_or_grouping=operator)
    assert evaluate([trait], tmp_path)["matched"] == ["sample"]
