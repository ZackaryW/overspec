import pytest


def test_projection_preserves_unowned_aliases_and_literal_artifact_ids():
    from overspec.core.projection import project_yaml, parse_yaml

    original = """schema: spec-driven
custom: &shared
  guidance: [manual]
  keep: true
operations:
  apply: *shared
  archive:
    other: 1
  custom: {untouched: yes}
context: old
rules: {stale: [old]}
"""
    candidate, changed = project_yaml(
        original,
        [
            {"name": "ctx", "attach": "context", "body": "Context"},
            {"name": "rule", "attach": "rules.review.notes", "body": "Rule"},
            {"name": "tdd", "attach": "operations.apply.guidance", "body": "TDD\n"},
        ],
    )
    assert changed
    doc = parse_yaml(candidate)
    assert doc["custom"]["guidance"] == ["manual"]
    assert doc["operations"]["apply"] == {"guidance": ["TDD\n"], "keep": True}
    assert doc["operations"]["archive"] == {"other": 1}
    assert doc["rules"] == {"review.notes": ["Rule"]}
    assert doc["context"] == "Context\n<!-- over:ctx -->\n"
    assert "# over:tdd" in candidate and "# over:rule" in candidate
    repeated, changed = project_yaml(
        candidate,
        [
            {"name": "ctx", "attach": "context", "body": "Context"},
            {"name": "rule", "attach": "rules.review.notes", "body": "Rule"},
            {"name": "tdd", "attach": "operations.apply.guidance", "body": "TDD\n"},
        ],
    )
    assert not changed and repeated == candidate


def test_projection_repairs_markers_and_clears_owned_fields():
    from overspec.core.projection import project_yaml, parse_yaml

    body = [{"name": "x", "attach": "operations.apply.guidance", "body": "hello\n"}]
    initial, _ = project_yaml("schema: spec-driven\n", body)
    damaged = initial.replace("# over:x", "# over:wrong")
    repaired, changed = project_yaml(damaged, body)
    assert changed and "# over:x" in repaired
    empty, changed = project_yaml(repaired, [])
    assert changed and parse_yaml(empty) == {"schema": "spec-driven"}


@pytest.mark.parametrize(
    "text",
    [
        "schema: a\nschema: b\n",
        "[]",
        "operations: []",
        "operations: {apply: false}",
        "operations: {archive: null}",
    ],
)
def test_invalid_yaml_rejected(text):
    from overspec.core.projection import project_yaml

    with pytest.raises(ValueError):
        project_yaml(text, [])


def test_context_limit_includes_markers():
    from overspec.core.projection import project_yaml

    with pytest.raises(ValueError, match="50 KiB"):
        project_yaml(
            "schema: spec-driven",
            [{"name": "x", "attach": "context", "body": "x" * (50 * 1024)}],
        )
