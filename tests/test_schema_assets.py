import json

import pytest
from typer.testing import CliRunner

from overspec.cli import app
from overspec.core import schema_assets, storage


def test_schema_install_refresh_conflicts_and_state_preservation(project, monkeypatch):
    original = schema_assets.schema_payload()
    result = schema_assets.install_schema(project.root)
    assert result['changed'] and result['status'] == 'installed'
    target = project.root / 'openspec/schemas/overspec/templates/tasks.md'
    before = target.read_bytes(), target.stat().st_mtime_ns
    assert not schema_assets.install_schema(project.root)['changed']
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    baseline = storage.read_state(project.root)['schema']
    project.initialize()
    project.sync()
    assert storage.read_state(project.root)['schema'] == baseline
    updated = {**original, 'templates/tasks.md': original['templates/tasks.md'] + b'\nUpgrade\n'}
    monkeypatch.setattr(schema_assets, 'schema_payload', lambda: updated)
    assert schema_assets.install_schema(project.root)['changed']
    assert target.read_bytes() == updated['templates/tasks.md']
    target.write_text('local customization')
    with pytest.raises(ValueError, match='conflict'):
        schema_assets.install_schema(project.root)
    assert target.read_text() == 'local customization'


def test_schema_unmanaged_and_race(project):
    directory = project.root / 'openspec/schemas/overspec'
    directory.mkdir(parents=True)
    (directory / 'schema.yaml').write_text('custom')
    with pytest.raises(ValueError, match='conflict'):
        schema_assets.install_schema(project.root)
    assert not project.state.exists()


def test_schema_removes_only_baseline_files_and_reports_partial_failure(project, monkeypatch):
    original = schema_assets.schema_payload()
    augmented = {**original, 'obsolete.md': b'old'}
    monkeypatch.setattr(schema_assets, 'schema_payload', lambda: augmented)
    schema_assets.install_schema(project.root)
    target = project.root / 'openspec/schemas/overspec'
    (target / 'local.md').write_bytes(b'keep')
    monkeypatch.setattr(schema_assets, 'schema_payload', lambda: original)
    schema_assets.install_schema(project.root)
    assert not (target / 'obsolete.md').exists()
    assert (target / 'local.md').read_bytes() == b'keep'
    before = project.state.read_bytes()
    updated = {**original, 'new.md': b'new'}
    monkeypatch.setattr(schema_assets, 'schema_payload', lambda: updated)
    def fail(*args, **kwargs):
        raise OSError('receipt failed')
    monkeypatch.setattr(storage, 'save_state', fail)
    with pytest.raises(ValueError, match='completed paths.*new.md'):
        schema_assets.install_schema(project.root)
    assert project.state.read_bytes() == before
    assert (target / 'new.md').read_bytes() == b'new'


def test_schema_detects_races_and_directory_collisions_before_writes(project, monkeypatch):
    original = schema_assets.schema_payload()
    directory = project.root / 'openspec/schemas/overspec/templates/tasks.md'
    directory.mkdir(parents=True)
    with pytest.raises((ValueError, OSError)):
        schema_assets.install_schema(project.root)
    assert not (directory.parents[1] / 'schema.yaml').exists()


def test_init_installs_schema_before_discovery_and_preserves_selection(project, monkeypatch):
    from overspec.core import discovery
    config = project.root / 'openspec/config.yaml'
    before = config.read_bytes()
    def discover(root, *, store=None):
        assert (root / 'openspec/schemas/overspec/schema.yaml').is_file()
        assert store == 'external'
        return []
    monkeypatch.setattr(discovery, 'discover_changes', discover)
    args = ['--project', str(project.root), '--home', str(project.home)]
    result = CliRunner().invoke(app, [*args, 'init', '--store', 'external', '--json'])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)['schema']['status'] == 'installed'
    assert config.read_bytes() == before
    assert not project.home.exists()
    assert CliRunner().invoke(app, [*args, 'init']).exit_code != 0
