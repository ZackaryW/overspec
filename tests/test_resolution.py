import pytest

from conftest import declaration, source
from overspec.core import storage


def test_runtime_resolution_uses_retained_bundle_and_context(project):
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
    identity = storage.publish(project.root, "resolutions", bundle)
    assert identity == storage.publish(project.root, "resolutions", project.prepare())
    output = contributions(bundle, identity)
    assert len(output) == 2
    assert output[1]["body"].count("overspec trait resolve") == 1
    assert "--trait r --trait s" in output[1]["body"]
    assert output[1]["name"] == "r,s"
    assert "private long details" not in str(explain(bundle))
    source(project, declaration("replacement"))
    result = resolve_runtime(
        project.root,
        identity,
        "operations.archive.guidance",
        ["r", "s"],
        {"flag": True, "change": "a"},
    )
    assert [item["body"] for item in result] == ["Stop a", "Review"]
    assert (
        resolve_runtime(
            project.root, identity, "operations.archive.guidance", ["r"], {}
        )
        == []
    )
    assert (
        resolve_runtime(
            project.root,
            identity,
            "operations.archive.guidance",
            ["r"],
            {"flag": True, "change": "b"},
        )[0]["body"]
        == "Stop b"
    )
    with pytest.raises(ValueError):
        resolve_runtime(project.root, identity, "context", ["r"], {})
    with pytest.raises(ValueError):
        resolve_runtime(
            project.root, identity, "operations.archive.guidance", ["unknown"], {}
        )
    path = project.state / "resolutions" / (identity + ".json")
    path.write_text("{}")
    with pytest.raises(ValueError, match="Corrupt"):
        resolve_runtime(
            project.root, identity, "operations.archive.guidance", ["r"], {}
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
    identity = storage.publish(project.root, "resolutions", project.prepare())
    assert [
        x["name"] for x in resolve_runtime(project.root, identity, "context", ["b"], {})
    ] == ["b"]
    assert resolve_runtime(project.root, identity, "context", ["a"], {}) == []
