import pytest

from overspec.core.trait_system.models import EvaluationContext


def predicate(kind, payload, root, matched=(), runtime=None):
    from overspec.core.trait_system.registry import builtins

    handler, negated = builtins().assertion({"type": kind, **payload})
    result = handler.evaluate(
        EvaluationContext(root, frozenset(matched), runtime or {})
    )
    assert result.reason
    return not result.matched if negated else result.matched


def test_which_probes_without_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda name: "/bin/tool" if name == "tool" else None
    )
    assert predicate("which", {"app": "tool"}, tmp_path)
    assert predicate("~which", {"app": "missing"}, tmp_path)


@pytest.mark.parametrize("kind", ["loaded-trait", "require-trait"])
def test_matched_history_predicates(kind, tmp_path):
    assert predicate(kind, {"trait": "known"}, tmp_path, ["known"])
    assert predicate("~" + kind, {"trait": "absent"}, tmp_path, ["known"])


def test_files_require_all_regular_files(tmp_path):
    data = {"paths": [".python-version", "uv.lock"]}
    assert not predicate("files-exist", data, tmp_path)
    (tmp_path / ".python-version").touch()
    assert not predicate("files-exist", data, tmp_path)
    (tmp_path / "uv.lock").mkdir()
    assert not predicate("files-exist", data, tmp_path)
    (tmp_path / "uv.lock").rmdir()
    (tmp_path / "uv.lock").touch()
    assert predicate("files-exist", data, tmp_path)
    with pytest.raises(ValueError):
        predicate("files-exist", {"paths": ["../outside"]}, tmp_path)


@pytest.mark.parametrize(
    "requirement,expected",
    [
        ("zuu>=1", True),
        ("ZUU[extra]", True),
        ("zuu @ https://example.org/pkg.whl", True),
        ('zuu; python_version < "0"', True),
        ("zuu-helper", False),
        ("some_pkg", False),
    ],
)
def test_python_dependency_names(tmp_path, requirement, expected):
    import json

    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = [" + json.dumps(requirement) + "]"
    )
    assert predicate("python-dependency", {"name": "zuu"}, tmp_path) is expected


def test_python_dependency_missing_and_invalid(tmp_path):
    assert not predicate("python-dependency", {"name": "zuu"}, tmp_path)
    path = tmp_path / "pyproject.toml"
    for text in (
        '[tool.uv.sources]\nzuu = "local"',
        '[project.optional-dependencies]\ndev = ["zuu"]',
        "[project]",
    ):
        path.write_text(text)
        assert not predicate("python-dependency", {"name": "zuu"}, tmp_path)
    for text in (
        "not toml",
        "project = []",
        '[project]\ndependencies = "zuu"',
        '[project]\ndependencies = ["zuu", "bad ???"]',
    ):
        path.write_text(text)
        with pytest.raises(ValueError):
            predicate("python-dependency", {"name": "zuu"}, tmp_path)


def test_runtime_typed_match(tmp_path):
    for value, expected in ((True, True), (1, False), ("true", False), (False, False)):
        assert (
            predicate(
                "runtime-context-match",
                {"kv": "flag=true"},
                tmp_path,
                runtime={"flag": value},
            )
            is expected
        )
    assert not predicate("runtime-context-match", {"kv": "flag=true"}, tmp_path)


def test_runtime_includes_exact_membership(tmp_path):
    payload = {"k": "flag", "includes": "$activeChanges"}
    assert predicate(
        "runtime-context-includes",
        payload,
        tmp_path,
        runtime={"flag": ["one"], "activeChanges": ["one", "two"]},
    )
    assert not predicate(
        "runtime-context-includes",
        payload,
        tmp_path,
        runtime={"flag": ["one"], "activeChanges": ["on"]},
    )
    assert not predicate(
        "runtime-context-includes", payload, tmp_path, runtime={"flag": True}
    )
    with pytest.raises(ValueError, match="activeChanges"):
        predicate(
            "runtime-context-includes", payload, tmp_path, runtime={"flag": ["one"]}
        )
    assert not predicate(
        "runtime-context-includes",
        {"k": "flag", "includes": True},
        tmp_path,
        runtime={"flag": [1]},
    )


def test_remove_action_returns_typed_effect(tmp_path):
    from overspec.core.trait_system.registry import builtins
    from overspec.core.trait_system.models import Suppress

    action = builtins().action({"type": "remove-trait", "trait": "old"})
    assert action.references() == ("old",)
    assert action.evaluate(EvaluationContext(tmp_path)) == Suppress("old")
