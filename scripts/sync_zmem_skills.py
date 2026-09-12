"""Refresh authored zmem skills through unscoped Saucepan acquisition.

Independent maintenance only: no Overspec imports, configuration, or environment.
Exit 0 means unchanged, 2 means changed/review required, and 1 means failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from saucepan_sdk import Saucepan
from zuu.case2 import FileSystemSnapshot
from zuu.case5 import ConfinedPath, TargetState

SOURCE = "https://github.com/ZackaryW/zmem.git"
NAMES = ("zmem-author-commits", "zmem-query-memory", "zmem-design-extensions")
PROVENANCE = ".agents/zmem-skills.json"


@dataclass(frozen=True)
class SyncResult:
    revision: str
    changed: tuple[str, ...]


def _contents(snapshot):
    return tuple((entry.relative_path, entry.kind, entry.content) for entry in snapshot.entries)


def _snapshot(plan):
    return None if plan.state is TargetState.ABSENT else FileSystemSnapshot.capture([plan.target])


def _remove(path):
    # Only private staged or explicitly confined publication paths reach here.
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def sync_zmem_skills(repo_root: Path, client: Saucepan, *, origin=SOURCE) -> SyncResult:
    acquired = client.acquire({"source": {"provider": "git", "origin": origin,
                                          "reference": "main"}, "folder": "skills"})
    if (acquired.get("fallback") is not False or acquired.get("update_checked") is not True
            or acquired.get("content_verified") is not True):
        raise ValueError("Saucepan must return freshly checked, verified content without fallback")
    revision = acquired["artifact"]["revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", revision):
        raise ValueError("Saucepan did not return an immutable Git revision")
    source = Path(acquired["directory"])
    snapshots = {}
    for name in NAMES:
        source_plan = ConfinedPath(name).inspect(source, allowed=[TargetState.DIRECTORY])
        ConfinedPath(f"{name}/SKILL.md").inspect(source, allowed=[TargetState.FILE])
        snapshots[name] = FileSystemSnapshot.capture([source_plan.target])
        source_plan.revalidate()
    provenance = {
        "source": origin, "revision": revision, "skills": list(NAMES),
        "files": {f"{name}/{entry.relative_path}": hashlib.sha256(entry.content).hexdigest()
                  for name, snapshot in snapshots.items() for entry in snapshot.files},
    }
    provenance_bytes = (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()
    root = Path(os.path.abspath(repo_root))
    plans = {f".agents/skills/{name}": ConfinedPath(f".agents/skills/{name}").inspect(
        root, allowed=[TargetState.ABSENT, TargetState.DIRECTORY]) for name in NAMES}
    plans[PROVENANCE] = ConfinedPath(PROVENANCE).inspect(
        root, allowed=[TargetState.ABSENT, TargetState.FILE])
    before = {relative: _snapshot(plan) for relative, plan in plans.items()}
    changed = []
    for name in NAMES:
        relative = f".agents/skills/{name}"
        if before[relative] is None or _contents(before[relative]) != _contents(snapshots[name]):
            changed.append(relative)
    if before[PROVENANCE] is None or before[PROVENANCE].files[0].content != provenance_bytes:
        changed.append(PROVENANCE)
    if not changed:
        return SyncResult(revision, ())

    # Validate every payload and destination before creating any publication paths.
    for plan in plans.values():
        plan.revalidate()
    for parent in (".agents", ".agents/skills"):
        plan = ConfinedPath(parent).inspect(root, allowed=[TargetState.ABSENT, TargetState.DIRECTORY])
        plan.revalidate()
        plan.target.mkdir(exist_ok=True)
    plans = {relative: ConfinedPath(relative).inspect(root, allowed=plan.allowed)
             for relative, plan in plans.items()}
    stage = Path(tempfile.mkdtemp(prefix=".zmem-sync-", dir=root / ".agents"))
    published = []
    backups = {}
    try:
        for relative in changed:
            incoming = stage / "incoming" / relative
            if relative == PROVENANCE:
                incoming.parent.mkdir(parents=True, exist_ok=True)
                incoming.write_bytes(provenance_bytes)
            else:
                snapshot = snapshots[Path(relative).name]
                for entry in snapshot.directories:
                    (incoming / entry.relative_path).mkdir(parents=True, exist_ok=True)
                for entry in snapshot.files:
                    (incoming / entry.relative_path).write_bytes(entry.content)
        for relative, plan in plans.items():
            plan.revalidate()
            current = _snapshot(plan)
            if (None if current is None else _contents(current)) != (
                    None if before[relative] is None else _contents(before[relative])):
                raise ValueError(f"Destination changed during refresh: {relative}")
        for relative in changed:
            plan = plans[relative]
            plan.revalidate()
            if plan.state is not TargetState.ABSENT:
                backup = stage / "backup" / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(plan.target, backup)
                backups[relative] = backup
            os.replace(stage / "incoming" / relative, plan.target)
            published.append(relative)
    except Exception as error:
        recovery_errors = []
        for relative in reversed(changed):
            if relative not in backups and relative not in published:
                continue
            try:
                target = ConfinedPath(relative).inspect(root, allowed=plans[relative].allowed)
                target.revalidate()
                if target.state is not TargetState.ABSENT:
                    # Keep the attempted replacement for inspection as well as the original.
                    displaced = stage / "displaced" / relative
                    displaced.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(target.target, displaced)
                if relative in backups:
                    os.replace(backups[relative], target.target)
            except Exception as recovery_error:
                recovery_errors.append(f"{relative}: {recovery_error}")
        recovery = ("recovery incomplete: " + "; ".join(recovery_errors)
                    if recovery_errors else "previous destinations restored")
        raise RuntimeError(f"Skill publication failed ({error}); affected: {', '.join(changed)}; "
                           f"{recovery}; recovery files retained at {stage}") from error
    else:
        _remove(stage)
    return SyncResult(revision, tuple(changed))


def main(argv=None, *, client=None, origin=SOURCE):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="Destination repository (defaults to this script's repository)")
    parser.add_argument("--binary", type=Path, default=os.environ.get("SAUCEPAN_BINARY"),
                        help="Saucepan executable; also accepts SAUCEPAN_BINARY")
    args = parser.parse_args(argv)
    try:
        result = sync_zmem_skills(args.root, client or Saucepan(binary=args.binary), origin=origin)
    except Exception as error:
        print(f"zmem skill refresh failed: {error}\nUse a Saucepan executable with unscoped acquisition "
              "and run its init command once before refreshing.", file=sys.stderr)
        return 1
    if result.changed:
        print(f"Updated zmem skills at {result.revision}. Review and stage before retrying the commit:")
        print("\n".join(f"  {path}" for path in result.changed))
        return 2
    print(f"zmem skills unchanged at {result.revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
