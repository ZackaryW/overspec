import pytest

from conftest import declaration, source


def test_runtime_resolution_uses_live_definitions_and_context(project):
    from overspec.core.resolution import resolve_runtime, contributions, explain

    source(
        project,
        declaration("a", body="static", details="private long details")
        + declaration(
            "r",
            "runtime-trait",
            body="Stop ${change}",
            attach="operations.archive.guidance",
            **{"assert": [{"type": "runtime-context-match", "kv": "flag=true"}]},
        )
        + declaration(
            "s", "runtime-trait", body="Review", attach="operations.archive.guidance"
        ),
    )
    project.initialize()
    bundle = project.prepare()
    identity = project.sync()["resolution"]
    assert identity == project.sync()["resolution"]
    output = contributions(bundle)
    assert len(output) == 2
    assert output[1]["body"].count("overspec trait resolve") == 1
    assert "--trait r --trait s" in output[1]["body"]
    assert "--resolution" not in output[1]["body"]
    assert output[1]["name"] == "r,s"
    assert "private long details" not in str(explain(bundle))
    result = resolve_runtime(
        project,
        "operations.archive.guidance",
        ["r", "s"],
        {"flag": True, "change": "a"},
    )
    assert [item["body"] for item in result] == ["Stop a", "Review"]
    assert (
        resolve_runtime(
            project, "operations.archive.guidance", ["r"], {}
        )
        == []
    )
    assert (
        resolve_runtime(
            project,
            "operations.archive.guidance",
            ["r"],
            {"flag": True, "change": "b"},
        )[0]["body"]
        == "Stop b"
    )
    with pytest.raises(ValueError):
        resolve_runtime(project, "context", ["r"], {})
    with pytest.raises(ValueError):
        resolve_runtime(
            project, "operations.archive.guidance", ["unknown"], {}
        )
    source(project, declaration("replacement"))
    with pytest.raises(ValueError, match="Unknown"):
        resolve_runtime(project, "operations.archive.guidance", ["r"], {})
    source(project, declaration("r", "runtime-trait", attach="operations.archive.guidance"))
    path = project.state
    path.write_text("{}")
    with pytest.raises(ValueError, match="Corrupt"):
        resolve_runtime(
            project, "operations.archive.guidance", ["r"], {}
        )


def test_runtime_dependencies_evaluate_group_but_only_requested_emit(project):
    from overspec.core.resolution import resolve_runtime

    source(
        project,
        declaration("a", "runtime-trait")
        + declaration(
            "b",
            "runtime-trait",
            **{
                "assert": [{"type": "loaded-trait", "trait": "a"}],
                "actions": [{"type": "remove-trait", "trait": "a"}],
            },
        ),
    )
    project.initialize()
    identity = project.sync()["resolution"]
    assert [
        x["name"] for x in resolve_runtime(project, "context", ["b"], {})
    ] == ["b"]
    assert resolve_runtime(project, "context", ["a"], {}) == []


def test_runtime_cli_reads_live_definitions_without_sync_and_preserves_lifetimes(project):
    import json
    from test_setup_cli import invoke

    runtime = source(project, declaration("r", "runtime-trait", body="old ${x}"))
    variables = source(project, '[vars]\nx="first"', "config.toml")
    command = ("trait", "resolve", "--attach", "context", "--trait", "r", "--json")
    result = invoke(project, *command)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)[0]["body"] == "old first"
    assert not project.state.exists()

    earlier = source(
        project,
        declaration("c", "compiletime-trait", body="compiled ${x}")
        + declaration("n", body="normal ${x}"),
        "trait-earlier.toml",
    )
    project.initialize()
    project.sync()
    before = project.state.read_bytes(), (project.root / "openspec/config.yaml").read_bytes()
    runtime.write_text(declaration("r", "runtime-trait", body="new ${x}", **{
        "assert": [{"type": "runtime-context-match", "kv": "x=second"}]
    }))
    variables.write_text('[vars]\nx="second"')
    # Missing substitutions would fail if either earlier phase were reevaluated.
    earlier.write_text(declaration("c", "compiletime-trait", body="${missing}")
                       + declaration("n", body="${missing}"))
    result = invoke(project, *command)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)[0]["body"] == "new second"
    variables.write_text('[vars]\nx="third"')
    assert json.loads(invoke(project, *command).stdout) == []
    assert before == (project.state.read_bytes(), (project.root / "openspec/config.yaml").read_bytes())
    assert invoke(project, *command, "--resolution", "0" * 64).exit_code != 0

    # A former normal trait's retained match must not bypass its runtime condition.
    earlier.write_text(declaration("c", "compiletime-trait", body="${missing}")
                       + declaration("n", "runtime-trait", **{
                           "assert": [{"type": "runtime-context-match", "kv": "enabled=true"}]
                       }))
    assert json.loads(invoke(project, "trait", "resolve", "--attach", "context", "--trait", "n", "--json").stdout) == []
