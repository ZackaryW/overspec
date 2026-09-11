"""Profile mode, named selection, and ordered contributor discovery."""

import os
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from overspec.core.profiles import (
    profile_settings,
    require_profiles,
    selected_name,
    toggle_profiles,
    use_profile,
)
from overspec.core.source_plan import profile_catalog

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
    help="Browse and select reusable profiles.",
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
    """List profile contributors in ascending priority and the active selection."""
    project_target = target(ctx, home, project)
    require_profiles(project_target.home)
    catalog = profile_catalog(project_target.root, project_target.home)
    saved = profile_settings(project_target.home).get("selected")
    effective, _ = selected_name(project_target.home)
    result = [
        {
            "name": name,
            "contributors": contributors,
            "active": name == effective,
            "selected": name == saved,
            "environment": os.environ.get("OVERSPEC_PROFILE"),
        }
        for name, contributors in sorted(catalog.items())
    ]
    if emit_json(ctx, json_output, result):
        return
    table = Table(title="Profiles (contributors: low to high priority)", expand=True)
    for column in (
        "Profile",
        "Active",
        "Saved",
        "Source",
        "Location",
        "Version / revision",
    ):
        table.add_column(column, overflow="fold")
    for item in result:
        for contributor in item["contributors"]:
            table.add_row(
                Text(item["name"]),
                "Yes" if item["active"] else "",
                "Yes" if item["selected"] else "",
                contributor["kind"],
                Text(contributor["origin"]),
                Text(contributor.get("version", contributor.get("revision", ""))),
            )
    console = Console(highlight=False)
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
