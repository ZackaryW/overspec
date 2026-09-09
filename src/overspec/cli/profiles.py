"""Profile discovery, activation, and explicit remote retrieval."""

import os
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from overspec.core import storage
from overspec.core.profiles import (
    profile_directories,
    profile_settings,
    selected_name,
    toggle_profiles,
    use_profile,
    user_profiles,
)
from overspec.core.remotes import pull_profile, update_profile

from .common import (
    HomeOption,
    JsonOption,
    ProjectOption,
    emit_json,
    guard,
    scope,
    target,
)
from .profile_mode import ProfileGroup

app = typer.Typer(
    cls=ProfileGroup,
    help="Browse, select, and retrieve reusable profiles.",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.callback()(scope)


@app.command("list")
@guard
def list_profiles(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    """List available profiles, their scope, and the active selection."""
    project_target = target(ctx, home, project)
    local = profile_directories(project_target.over)
    users = user_profiles(project_target.home)
    saved = profile_settings(project_target.home).get("selected")
    effective, _ = selected_name(project_target.home)
    result = []
    for name, path in sorted({**users, **local}.items()):
        item = {
            "name": name,
            "path": str(path),
            "level": "project" if name in local else "user",
            "active": name == effective,
            "selected": name == saved,
            "environment": os.environ.get("OVERSPEC_PROFILE"),
        }
        metadata = f".state/remotes/{name}/current.json"
        if (
            name not in local
            and project_target.home.exists()
            and storage.read_bytes(project_target.home, metadata)
        ):
            item.update(storage.read_json(project_target.home, metadata))
        result.append(item)
    if emit_json(ctx, json_output, result):
        return
    console = Console(highlight=False)
    if not result:
        console.print(
            "No profiles found. Add a profile directory or use overspec profile pull."
        )
        return
    table = Table(title="Profiles", expand=True)
    for column in ("Profile", "Scope", "Active", "Saved", "Location", "Revision"):
        table.add_column(column, overflow="fold")
    for item in result:
        table.add_row(
            Text(item["name"]),
            item["level"],
            "Yes" if item["active"] else "",
            "Yes" if item["selected"] else "",
            Text(item["path"]),
            Text(item.get("commit", "")),
        )
    console.print(table)
    if "OVERSPEC_PROFILE" in os.environ:
        console.print(
            "Environment selection: " + os.environ["OVERSPEC_PROFILE"], markup=False
        )


@app.command("activate")
@guard
def activate(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    """Toggle optional profile management on or off for this user home."""
    enabled = toggle_profiles(target(ctx, home, project).home)
    if not emit_json(ctx, json_output, {"enabled": enabled}):
        Console(highlight=False).print("Profile mode: " + ("on" if enabled else "off"))


@app.command("use")
@guard
def select(
    ctx: typer.Context,
    name: Annotated[
        str, typer.Argument(help="Profile name to save as the user selection.")
    ],
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    """Save the user's profile choice; OVERSPEC_PROFILE takes precedence."""
    project_target = target(ctx, home, project)
    use_profile(project_target.root, project_target.home, name)
    result = {"profile": name, "environment": os.environ.get("OVERSPEC_PROFILE")}
    if not emit_json(ctx, json_output, result):
        console = Console(highlight=False)
        console.print(f"Saved user profile: {name}", markup=False)
        if result["environment"] is not None:
            console.print(
                f"Environment selection: {result['environment']}", markup=False
            )


def show_revision(ctx, json_output, name, result):
    if not emit_json(ctx, json_output, result):
        console = Console(highlight=False)
        console.print(
            f"Profile {name}: {result['commit']}", markup=False, soft_wrap=True
        )
        console.print(f"Revision: {result['revision']}", markup=False, soft_wrap=True)


@app.command("pull")
@guard
def pull(
    ctx: typer.Context,
    name: Annotated[
        str, typer.Argument(help="Name to register in the user profile home.")
    ],
    owner: Annotated[
        str,
        typer.Option(help="GitHub owner or organization.", rich_help_panel="Source"),
    ],
    repo: Annotated[
        str, typer.Option(help="GitHub repository name.", rich_help_panel="Source")
    ],
    path: Annotated[
        str,
        typer.Option(
            help="Profile subdirectory inside the repository.", rich_help_panel="Source"
        ),
    ],
    branch: Annotated[
        str | None,
        typer.Option(
            help="Branch to track; omit for the default branch.",
            rich_help_panel="Revision",
        ),
    ] = None,
    commit: Annotated[
        str | None,
        typer.Option(
            help="Full commit SHA; mutually exclusive with --branch.",
            rich_help_panel="Revision",
        ),
    ] = None,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    """Retrieve a public GitHub profile without activating it."""
    if branch is not None and commit is not None:
        raise typer.BadParameter("Choose either --branch or --commit, not both.")
    project_target = target(ctx, home, project)
    source = {"kind": "github", "owner": owner, "repository": repo, "path": path}
    source.update(
        {
            key: value
            for key, value in (("branch", branch), ("commit", commit))
            if value is not None
        }
    )
    show_revision(
        ctx, json_output, name, pull_profile(project_target.home, name, source)
    )


@app.command("update")
@guard
def refresh(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Registered remote profile to refresh.")],
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    """Refresh a registered remote profile, preserving the last usable revision."""
    show_revision(
        ctx, json_output, name, update_profile(target(ctx, home, project).home, name)
    )
