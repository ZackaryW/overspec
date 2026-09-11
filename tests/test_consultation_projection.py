import pytest
from conftest import declaration, source

from overspec.core.projection import owned_fingerprint, parse_yaml, project_yaml
from overspec.core.resolution import resolve_runtime


@pytest.mark.parametrize("operation", ["explore", "propose"])
def test_consultation_projection_ownership(operation):
    original = f"""schema: spec-driven
custom: &shared
  guidance: [manual]
  keep: true
operations:
  {operation}: *shared
  unrelated: {{guidance: [retained]}}
"""
    items = [
        {
            "name": "consult",
            "attach": f"operations.{operation}.guidance",
            "body": "Ask once\n",
        }
    ]
    candidate, changed = project_yaml(original, items)
    assert changed
    parsed = parse_yaml(candidate)
    assert parsed["custom"]["guidance"] == ["manual"]
    assert parsed["operations"][operation] == {"keep": True, "guidance": ["Ask once\n"]}
    assert parsed["operations"]["unrelated"]["guidance"] == ["retained"]
    assert "# over:consult" in candidate
    assert owned_fingerprint(candidate) != owned_fingerprint(original)
    assert project_yaml(candidate, items) == (candidate, False)
    damaged = candidate.replace("# over:consult", "# over:wrong")
    assert owned_fingerprint(damaged) != owned_fingerprint(candidate)
    assert project_yaml(damaged, items)[0] == candidate
    cleared = parse_yaml(project_yaml(candidate, [])[0])
    assert cleared["operations"][operation] == {"keep": True}
    only, _ = project_yaml("schema: spec-driven\n", items)
    assert "operations" not in parse_yaml(project_yaml(only, [])[0])


@pytest.mark.parametrize("operation", ["explore", "propose"])
def test_consultation_saved_group_and_noop(project, operation):
    attach = f"operations.{operation}.guidance"
    source(
        project,
        declaration("one", "runtime-trait", attach=attach)
        + declaration("two", "runtime-trait", attach=attach),
    )
    project.initialize()
    result = project.sync()
    config = project.root / "openspec/config.yaml"
    before = config.read_bytes(), config.stat().st_mtime_ns
    assert config.read_text().count("overspec trait resolve") == 1
    rows = resolve_runtime(project.root, result["resolution"], attach, ["one", "two"])
    assert [row["name"] for row in rows] == ["one", "two"]
    project.sync()
    assert (config.read_bytes(), config.stat().st_mtime_ns) == before


@pytest.mark.parametrize("operation", ["explore", "propose"])
def test_invalid_operation_parent(operation):
    with pytest.raises(ValueError, match=operation):
        project_yaml(f"operations: {{{operation}: false}}", [])
