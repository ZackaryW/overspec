"""Preserving current-file setup and verified Git-ignore coverage."""

from pathlib import Path

from zuu.case3 import (
    GitIgnorePolicy,
    IgnoreMode,
    apply_gitignore,
    plan_gitignore,
    run_process,
    verify_gitignore,
)
from zuu.case5 import ConfinedPath, TargetState

from .change_scope import change_root
from .variables import load_variables
from .storage import STATE_PATH

CURRENT = b"# Local mutable variables; intentionally ignored by Git.\n[vars]\n"


def create_current(root, relative):
    plan = ConfinedPath(relative).inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    if plan.state == TargetState.FILE:
        load_variables(root, relative)
        return "preserved"
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    plan = ConfinedPath(relative).inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    plan.revalidate()
    try:
        with plan.target.open("xb") as stream:
            stream.write(CURRENT)
    except FileExistsError:
        load_variables(root, relative)
        return "preserved"
    return "created"


def worktree_for(path):
    ancestor = path
    while not ancestor.exists():
        ancestor = ancestor.parent
    result = run_process(["git", "rev-parse", "--show-toplevel"], ancestor)
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    if (
        any((p / ".git").exists() for p in (ancestor, *ancestor.parents))
        or "not a git repository" not in result.stderr.lower()
    ):
        raise ValueError(
            f"Git worktree discovery failed at {ancestor}: {result.stderr.strip()}"
        )
    return None


def git_flag(root, arguments):
    result = run_process(["git", *arguments], root)
    if result.returncode not in (0, 1):
        raise ValueError(f"Git inspection failed: {result.stderr.strip()}")
    return result.returncode == 0


def setup_variables(root, changes):
    root = Path(root)
    ConfinedPath(STATE_PATH).inspect(
        root, allowed=(TargetState.FILE, TargetState.ABSENT)
    )
    targets = [(root, "openspec/.over/.current.toml")]
    targets += [(change_root(path), ".current.toml") for path in changes]
    targets = list(dict.fromkeys(targets))
    # Validate all authored inputs before any Git or file mutation.
    for owner, relative in targets:
        load_variables(owner, relative)
        load_variables(owner, Path(relative).with_name(".vars.toml").as_posix())
    report = {"success": True, "targets": [], "worktrees": []}
    groups = {}
    for owner, relative in targets:
        path = owner / relative
        worktree = worktree_for(path.parent)
        item = {
            "path": str(path),
            "status": "pending",
            "ignore": "unavailable",
            "tracked": False,
            "vars_ignored": False,
        }
        report["targets"].append(item)
        groups.setdefault(worktree, []).append((owner, relative, item))
    for worktree, entries in groups.items():
        try:
            if worktree is not None:
                paths = [owner / relative for owner, relative, _ in entries]
                plan = plan_gitignore(
                    worktree,
                    paths,
                    policy=GitIgnorePolicy(
                        mode=IgnoreMode.PATTERN, pattern=".current.toml"
                    ),
                )
                changed = apply_gitignore(plan)
                verify_gitignore(plan)
                if any(owner == root for owner, _, _ in entries):
                    state_plan = plan_gitignore(worktree, [root / STATE_PATH])
                    changed = apply_gitignore(state_plan) or changed
                    verify_gitignore(state_plan)
                report["worktrees"].append(
                    {"path": str(worktree), "changed": changed, "ignore": "verified"}
                )
                for owner, relative, item in entries:
                    path = owner / relative
                    item["ignore"] = "verified"
                    item["tracked"] = git_flag(
                        worktree,
                        [
                            "ls-files",
                            "--error-unmatch",
                            "--",
                            path.relative_to(worktree).as_posix(),
                        ],
                    )
                    persistent = path.with_name(".vars.toml")
                    item["vars_ignored"] = persistent.exists() and git_flag(
                        worktree,
                        [
                            "check-ignore",
                            "--no-index",
                            "-q",
                            "--",
                            persistent.relative_to(worktree).as_posix(),
                        ],
                    )
        except (OSError, ValueError) as exc:
            report["success"] = False
            report["worktrees"].append(
                {"path": str(worktree), "ignore": "failed", "error": str(exc)}
            )
            for _, _, item in entries:
                item.update(status="failed", ignore="failed", error=str(exc))
            continue
        for owner, relative, item in entries:
            try:
                item["status"] = create_current(owner, relative)
            except (OSError, ValueError) as exc:
                item.update(status="failed", error=str(exc))
                report["success"] = False
    return report
