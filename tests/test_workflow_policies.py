"""Default-policy controls through actual saved-resolution output."""

import pytest
from conftest import source

from overspec.core.project import Project
from overspec.core.resolution import resolve_runtime

POLICIES = {
    "utility-plan": {"utility-plan": "rules.design"},
    "utility-mature": {"utility-mature": "rules.tasks"},
    "integration-test-policies": {
        "integration-test-policies": "operations.apply.guidance"
    },
    "decision-choice": {
        "decision-explore": "operations.explore.guidance",
        "decision-propose": "operations.propose.guidance",
    },
    "prototype-choice": {
        "prototype-explore": "operations.explore.guidance",
        "prototype-propose": "operations.propose.guidance",
    },
    "evidence-first": {
        "evidence-tasks": "rules.tasks",
        "evidence-apply": "operations.apply.guidance",
    },
    **{
        f"bdd-{f}": {f"bdd-{f}": "operations.apply.guidance"}
        for f in ("behave", "cucumber", "flutter")
    },
    "tdd": {"tdd": "context"},
    "zuu": {"zuu": "context"},
}


@pytest.fixture
def consumer(tmp_path, monkeypatch):
    monkeypatch.delenv("OVERSPEC_PROFILE", raising=False)
    root = tmp_path / "consumer"
    (root / "openspec").mkdir(parents=True)
    (root / "openspec/config.yaml").write_text("schema: spec-driven\n")
    (root / ".python-version").write_text("3.12")
    (root / "uv.lock").write_text("")
    (root / "pyproject.toml").write_text('[project]\ndependencies=["zuu"]\n')
    project = Project(root, tmp_path / "home")
    project.initialize()
    return project, project.sync()["resolution"]


@pytest.mark.parametrize("policy", list(POLICIES))
def test_each_control_and_attachment(consumer, policy):
    project, identity = consumer
    for name, attach in POLICIES[policy].items():
        for value, enabled in ((True, True), (False, False), ("false", True)):
            rows = resolve_runtime(
                project.root,
                identity,
                attach,
                [name],
                {"bdd": ["behave", "cucumber", "flutter"], policy: value},
            )
            assert bool(rows) is enabled
        rows = resolve_runtime(
            project.root,
            identity,
            attach,
            [name],
            {"bdd": ["behave", "cucumber", "flutter"]},
        )
        assert len(rows) == 1 and len(rows[0]["body"]) < 700


def test_change_and_removed_current_controls(consumer):
    project, identity = consumer
    source(project, "[vars]\nutility-plan=true\n", ".vars.toml")
    change = project.root / "openspec/changes/selected"
    change.mkdir(parents=True)
    (change / ".openspec.yaml").write_text("schema: spec-driven\n")
    current = change / ".current.toml"
    current.write_text("[vars]\nutility-plan=false\n")

    def rows(change=None):
        return resolve_runtime(
            project.root, identity, "rules.design", ["utility-plan"], change=change
        )

    assert rows() and not rows(change)
    current.write_text("[vars]\n")
    assert rows(change)


def test_zuu_keeps_project_evidence_and_off_short_circuit(consumer):
    project, identity = consumer
    (project.root / "pyproject.toml").write_text("invalid TOML")
    assert not resolve_runtime(
        project.root, identity, "context", ["zuu"], {"zuu": False}
    )
    (project.root / "pyproject.toml").write_text("[project]\ndependencies=[]\n")
    assert not resolve_runtime(project.root, identity, "context", ["zuu"])


def test_each_trait_keeps_literal_details(consumer):
    project, _identity = consumer
    traits = {t.name: t for t in project.inventory()[0]}
    for members in POLICIES.values():
        for name in members:
            assert traits[name].phase == "runtime-trait"
            assert traits[name].details
            assert (
                traits[name].details
                not in (project.root / "openspec/config.yaml").read_text()
            )
