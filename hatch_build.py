"""Package the single authored default without importing runtime dependencies."""

import stat
import tomllib
from pathlib import Path
from ruamel.yaml import YAML

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

AUTHORED = Path("openspec/.over/profile-default")
SKILLS = Path('.agents/skills')
SCHEMA = Path('openspec/schemas/overspec')
EXCLUDED = {'.git', '__pycache__', '.state', '.pytest_cache', '.current.toml', '.state.json', '.DS_Store'}


def payload_files(root):
    if not stat.S_ISDIR(regular_path(root).st_mode):
        raise ValueError(f'Asset directory required: {root}')
    result = []
    for path in sorted(root.iterdir()):
        if path.name in EXCLUDED:
            continue
        info = regular_path(path)
        if stat.S_ISDIR(info.st_mode):
            result.extend(payload_files(path))
        elif stat.S_ISREG(info.st_mode):
            path.read_bytes()
            result.append(path)
        else:
            raise ValueError(f'Regular asset required: {path}')
    return result


def assets(root):
    for parent in (root / '.agents', root / SKILLS, root / 'openspec/schemas', root / SCHEMA):
        if not stat.S_ISDIR(regular_path(parent).st_mode):
            raise ValueError(f'Asset directory required: {parent}')
    skills = []
    for directory in sorted((root / SKILLS).iterdir()):
        if directory.name in EXCLUDED:
            continue
        info = regular_path(directory)
        if stat.S_ISDIR(info.st_mode) and (directory / 'SKILL.md').exists():
            skills.extend(payload_files(directory))
    if not skills:
        raise ValueError('Missing authored skills')
    schema_files = payload_files(root / SCHEMA)
    definition = YAML(typ='safe').load((root / SCHEMA / 'schema.yaml').read_text(encoding='utf-8'))
    if not isinstance(definition, dict) or definition.get('name') != 'overspec' or not definition.get('artifacts'):
        raise ValueError('Invalid overspec schema')
    for artifact in definition['artifacts']:
        template = artifact.get('template')
        if not isinstance(template, str) or not template or '\\' in template or Path(template).is_absolute() or '..' in Path(template).parts:
            raise ValueError(f'Invalid schema template: {template}')
        if root / SCHEMA / 'templates' / template not in schema_files:
            raise ValueError(f'Missing schema template: {template}')
    return [(p, SKILLS, 'skills') for p in skills] + [(p, SCHEMA, 'schemas/overspec') for p in schema_files]


def regular_path(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise ValueError(f"Redirected default profile path: {path}")
    return info


def documents(root):
    profile = root / AUTHORED
    for parent in (root / "openspec", root / "openspec/.over", profile):
        if not stat.S_ISDIR(regular_path(parent).st_mode):
            raise ValueError(f"Default profile directory required: {parent}")

    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.name in (".state", ".git", "__pycache__"):
                continue
            info = regular_path(path)
            if stat.S_ISDIR(info.st_mode):
                yield from visit(path)
            elif path.name.startswith("trait") and path.suffix == ".toml":
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError(f"Regular trait document required: {path}")
                tomllib.loads(path.read_text(encoding="utf-8"))
                yield path

    result = list(visit(profile))
    if not result:
        raise ValueError(f"Default profile has no trait documents: {profile}")
    return result


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        for path in documents(root):
            relative = path.relative_to(root / AUTHORED)
            destination = (
                Path("overspec/_bundled/profile-default") / relative
                if self.target_name == "wheel"
                else AUTHORED / relative
            )
            build_data["force_include"][str(path)] = destination.as_posix()
        for path, authored, packaged in assets(root):
            relative = path.relative_to(root / authored)
            destination = (Path('overspec/_bundled') / packaged / relative
                           if self.target_name == 'wheel' else authored / relative)
            build_data['force_include'][str(path)] = destination.as_posix()
