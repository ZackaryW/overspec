"""Shared Typer options, invocation scope, and output boundaries."""

import json
from functools import wraps
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from overspec.core.project import Project

HomeOption = Annotated[
    Path | None,
    typer.Option(
        "--home",
        help="User profile home; defaults to OVERSPEC_HOME or ~/.overspec.",
        rich_help_panel="Project",
    ),
]
ProjectOption = Annotated[
    Path | None,
    typer.Option(
        "--project",
        help="Owning project root; defaults to the current directory.",
        rich_help_panel="Project",
    ),
]
JsonOption = Annotated[
    bool,
    typer.Option(
        "--json", help="Emit plain JSON for scripts.", rich_help_panel="Output"
    ),
]
VarsOption = Annotated[
    Path | None,
    typer.Option(
        "--vars-file",
        exists=True,
        dir_okay=False,
        help="JSON object containing scalar rendering variables.",
        rich_help_panel="Inputs",
    ),
]


def guard(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValueError, OSError) as exc:
            Console(stderr=True, highlight=False).print(
                Panel(Text(str(exc)), title="Error", border_style="red")
            )
            raise typer.Exit(1) from exc

    return wrapped


def scope(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    inherited = dict(ctx.obj or {})
    if home is not None:
        inherited["home"] = home
    if project is not None:
        inherited["project"] = project
    inherited["json"] = json_output or inherited.get("json", False)
    ctx.obj = inherited
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def target(ctx, home=None, project=None):
    options = ctx.obj or {}
    return Project(
        project if project is not None else options.get("project"),
        home if home is not None else options.get("home"),
    )


def emit_json(ctx, enabled, data):
    if enabled or (ctx.obj or {}).get("json", False):
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return True
    return False


def json_file(path):
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data
