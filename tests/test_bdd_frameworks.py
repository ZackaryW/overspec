"""Framework selection through synchronized runtime guidance."""

import pytest
from conftest import declaration, source

from overspec.core.resolution import resolve_runtime
from overspec.core.trait_system.sources import parse_document


FRAMEWORKS = ("behave", "cucumber", "flutter")


def framework_source(project, frameworks=FRAMEWORKS):
    source(project, "".join(
        declaration(
            "bdd-" + name, "runtime-trait", body=name,
            **{"assert": {"1": {"assertion": [
                {"type": "~runtime-context-match", "kv": f"bdd-{name}=false"},
                {"type": "bdd-framework", "name": name},
            ]}}},
        ) for name in frameworks
    ))
    project.initialize()
    return project.sync()["resolution"]


def resolve(project, identity, context=None, frameworks=FRAMEWORKS):
    return [row["body"] for row in resolve_runtime(
        project.root, identity, "context", ["bdd-" + f for f in frameworks], context
    )]


@pytest.mark.parametrize("context,expected", [
    ({}, []),
    ({"bdd": []}, []),
    ({"bdd": ["behave", "cucumber", "behave"]}, ["behave", "cucumber"]),
    ({"bdd": list(FRAMEWORKS), "bdd-behave": False}, ["cucumber", "flutter"]),
    ({"bdd": ["behave"], "bdd-behave": "false"}, ["behave"]),
])
def test_selection_and_off_controls(project, context, expected):
    identity = framework_source(project)
    assert resolve(project, identity, context) == expected


@pytest.mark.parametrize("value", [None, False, "behave", ["unknown"], [1]])
def test_invalid_selection_is_not_automatic_detection(project, value):
    identity = framework_source(project)
    with pytest.raises(ValueError, match="bdd"):
        resolve(project, identity, {"bdd": value})


def test_explicit_selection_and_off_avoid_unused_manifests(project):
    identity = framework_source(project)
    (project.root / "pyproject.toml").write_text("invalid TOML")
    assert resolve(project, identity, {"bdd": ["cucumber"]}) == ["cucumber"]
    assert resolve(project, identity, {"bdd": []}) == []
    assert resolve(project, identity, {f"bdd-{f}": False for f in FRAMEWORKS}) == []


def test_current_selection_is_reread(project):
    identity = framework_source(project)
    current = source(project, '[vars]\nbdd=["behave"]\n', ".current.toml")
    assert resolve(project, identity) == ["behave"]
    current.write_text('[vars]\nbdd=[]\n')
    assert resolve(project, identity) == []


@pytest.mark.parametrize("name", ["unknown", "", 1])
def test_unknown_framework_rejected(project, name):
    text = declaration("bdd", "runtime-trait", **{
        "assert": {"1": {"assertion": [{"type": "bdd-framework", "name": name}]}}
    })
    with pytest.raises(ValueError, match="framework"):
        parse_document(text, "test")


def test_static_framework_assertion_rejected(project):
    source(project, declaration("bdd", **{
        "assert": {"1": {"assertion": [{"type": "bdd-framework", "name": "behave"}]}}
    }))
    with pytest.raises(ValueError, match="runtime"):
        project.inventory()


def test_selected_change_override(project):
    identity = framework_source(project)
    source(project, '[vars]\nbdd=["behave"]\n', '.vars.toml')
    change = project.root / 'openspec/changes/one'
    change.mkdir(parents=True)
    (change / '.openspec.yaml').write_text('schema: spec-driven\n')
    (change / '.current.toml').write_text('[vars]\nbdd=["flutter"]\n')
    rows = resolve_runtime(project.root, identity, 'context',
                           ['bdd-' + f for f in FRAMEWORKS], change=change)
    assert [r['body'] for r in rows] == ['flutter']
    assert resolve(project, identity) == ['behave']


@pytest.mark.parametrize('framework,path,content', [
    ('behave', 'behave.ini', ''),
    ('behave', '.behaverc', ''),
    ('behave', 'pyproject.toml', '[tool.behave]\n'),
    ('behave', 'pyproject.toml', '[project]\ndependencies=["Behave>=1"]'),
    ('behave', 'pyproject.toml', '[project.optional-dependencies]\ntest=["behave"]'),
    ('behave', 'pyproject.toml', '[dependency-groups]\ndev=[{include-group="BDD_tests"}]\nbdd-tests=["behave"]'),
    *[('cucumber', name, '') for name in ('cucumber.js', 'cucumber.cjs', 'cucumber.mjs', 'cucumber.json', 'cucumber.yaml', 'cucumber.yml')],
    *[('cucumber', 'package.json', '{"' + group + '":{"@cucumber/cucumber":"*"}}')
      for group in ('dependencies', 'devDependencies', 'optionalDependencies')],
    ('flutter', 'pubspec.yaml', 'dependencies:\n  flutter:\n    sdk: flutter\ndev_dependencies:\n  integration_test:\n    sdk: flutter\n'),
    ('flutter', 'pubspec.yaml', 'dependencies:\n  flutter:\n    sdk: flutter\n  integration_test:\n    sdk: flutter\n'),
])
def test_detected_guidance(project, framework, path, content):
    identity = framework_source(project, (framework,))
    evidence = project.root / path
    evidence.write_text(content)
    before = evidence.read_bytes()
    assert resolve(project, identity, frameworks=(framework,)) == [framework]
    assert evidence.read_bytes() == before


@pytest.mark.parametrize('framework,path,content', [
    ('behave', 'pyproject.toml', '[project]\ndependencies=["pytest"]'),
    ('cucumber', 'package.json', '{"dependencies":{"typescript":"*"}}'),
    ('flutter', 'pubspec.yaml', 'name: example'),
    ('flutter', 'pubspec.yaml', 'dependencies:\n  flutter:\n    sdk: flutter\n'),
    ('flutter', 'pubspec.yaml', 'dependencies:\n  integration_test:\n    sdk: flutter\n'),
])
def test_language_or_unrelated_dependencies_do_not_activate(project, framework, path, content):
    identity = framework_source(project, (framework,))
    (project.root / path).write_text(content)
    assert resolve(project, identity, frameworks=(framework,)) == []


def test_flutter_nested_sources(project):
    identity = framework_source(project, ('flutter',))
    (project.root / 'pubspec.yaml').write_text('dependencies:\n  flutter:\n    sdk: flutter\n')
    directory = project.root / 'integration_test/nested'
    directory.mkdir(parents=True)
    (directory / 'README.md').write_text('not a test')
    assert resolve(project, identity, frameworks=('flutter',)) == []
    (directory / 'app_test.dart').write_text('// actual integration source')
    assert resolve(project, identity, frameworks=('flutter',)) == ['flutter']


@pytest.mark.parametrize('framework,path,content', [
    ('behave', 'pyproject.toml', 'broken TOML'),
    ('behave', 'pyproject.toml', 'project=[]'),
    ('behave', 'pyproject.toml', '[project]\ndependencies="behave"'),
    ('behave', 'pyproject.toml', '[project]\ndependencies=["???"]'),
    ('behave', 'pyproject.toml', '[project.optional-dependencies]\ntest="behave"'),
    ('behave', 'pyproject.toml', '[dependency-groups]\na=[{include-group="missing"}]'),
    ('behave', 'pyproject.toml', '[dependency-groups]\na=[{include-group="b"}]\nb=[{include-group="a"}]'),
    ('behave', 'pyproject.toml', '[dependency-groups]\na_b=[]\na-b=[]'),
    ('behave', 'pyproject.toml', '[dependency-groups]\na=[{unknown="b"}]'),
    ('cucumber', 'package.json', 'broken JSON'),
    ('cucumber', 'package.json', '[]'),
    ('cucumber', 'package.json', '{"devDependencies":[]}'),
    ('flutter', 'pubspec.yaml', 'dependencies: ['),
    ('flutter', 'pubspec.yaml', 'dependencies: []'),
])
def test_malformed_consumed_evidence_errors(project, framework, path, content):
    identity = framework_source(project, (framework,))
    (project.root / path).write_text(content)
    with pytest.raises(ValueError, match=path.replace('.', r'\.')):
        resolve(project, identity, frameworks=(framework,))


def test_evidence_directory_is_not_a_file(project):
    identity = framework_source(project, ('behave',))
    (project.root / 'behave.ini').mkdir()
    with pytest.raises(ValueError, match='behave.ini'):
        resolve(project, identity, frameworks=('behave',))


def test_redirected_evidence_is_rejected(project, tmp_path):
    identity = framework_source(project, ('behave',))
    outside = tmp_path / 'outside.ini'
    outside.write_text('')
    try:
        (project.root / 'behave.ini').symlink_to(outside)
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ValueError, match='behave.ini'):
        resolve(project, identity, frameworks=('behave',))
