import pytest

from overspec.core.trait_system.sources import parse_document


def traits(text):
    return parse_document(text, "test")


def test_suppression_keeps_matched_history_and_negation(tmp_path):
    from overspec.core.trait_system.evaluator import evaluate, validate_references

    source = traits("""
[[trait]]
name="a"
attach="context"
body="A"
[[trait]]
name="b"
attach="context"
body="B"
assert=[{type="require-trait",trait="a"}]
actions=[{type="remove-trait",trait="a"}]
[[trait]]
name="c"
attach="context"
body="C"
assert_or_grouping=true
assert=[{type="~loaded-trait",trait="a"},{type="~loaded-trait",trait="b"}]
""")
    validate_references(source)
    result = evaluate(source, tmp_path)
    assert result["matched"] == ["a", "b"]
    assert result["suppressed"] == ["a"]
    assert result["bodies"] == {"a": "A", "b": "B"}
    assert result["decisions"]["c"]["matched"] is False


def test_forward_suppression_and_unmatched_actions(tmp_path):
    from overspec.core.trait_system.evaluator import evaluate

    source = traits("""
[[trait]]
name="a"
attach="context"
body="A"
assert=[{type="~loaded-trait",trait="b"}]
actions=[{type="remove-trait",trait="b"}]
[[trait]]
name="b"
attach="context"
body="B"
[[trait]]
name="c"
attach="context"
body="C"
assert=[{type="~loaded-trait",trait="b"}]
actions=[{type="remove-trait",trait="a"}]
""")
    result = evaluate(source, tmp_path)
    assert result["matched"] == ["a", "b"] and result["suppressed"] == ["b"]


@pytest.mark.parametrize(
    "target_phase,target_attach,action",
    [
        ("runtime-trait", "context", False),
        ("runtime-trait", "context", True),
        ("trait", "context", False),
    ],
)
def test_unknown_later_phase_and_runtime_scope_rejected(
    target_phase, target_attach, action
):
    from overspec.core.trait_system.evaluator import validate_references

    field = "actions" if action else "assert"
    kind = "remove-trait" if action else "require-trait"
    source = traits(
        f'[[compiletime-trait]]\nname="a"\nattach="context"\nbody="a"\n{field}=[{{type="{kind}",trait="b"}}]\n[[{target_phase}]]\nname="b"\nattach="{target_attach}"\nbody="b"'
    )
    with pytest.raises(ValueError, match="phase"):
        validate_references(source)
    with pytest.raises(ValueError, match="Unknown"):
        validate_references(source[:1])


def test_runtime_or_short_circuit_and_isolation(tmp_path):
    from overspec.core.trait_system.evaluator import evaluate, validate_references

    source = traits("""
[[runtime-trait]]
name="archive"
attach="operations.archive.guidance"
body="Stop"
assert_or_grouping=true
assert=[{type="runtime-context-match",kv="flag=true"},{type="runtime-context-includes",k="flag",includes="$activeChanges"}]
""")
    validate_references(source)
    assert evaluate(source, tmp_path, runtime={"flag": True})["matched"] == ["archive"]
    assert evaluate(source, tmp_path, runtime={"flag": ["a"], "activeChanges": ["a"]})[
        "matched"
    ] == ["archive"]
    assert evaluate(source, tmp_path)["matched"] == []


def test_rendering_and_variable_layers():
    from overspec.core.trait_system.rendering import render, variables

    values = variables({"x": "user", "y": 1}, {"x": "project"}, {"x": "invocation"})
    assert (
        render("${x}: ${y}, $$, $(echo ignored)", values)
        == "invocation: 1, $, $(echo ignored)"
    )
    for body, inputs in [
        ("${missing}", {}),
        ("${x}", {"x": []}),
        ("${x}", {"x": "<!-- over:fake -->"}),
    ]:
        with pytest.raises(ValueError):
            render(body, inputs)
