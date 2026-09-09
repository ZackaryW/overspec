"""Project lifecycle commands and human-readable sync previews."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .common import (
    HomeOption,
    JsonOption,
    ProjectOption,
    VarsOption,
    emit_json,
    guard,
    json_file,
    target,
)


def compilation(ctx, home, project, vars_file, json_output, *, update):
    identity = target(ctx, home, project).initialize(
        update=update, values=json_file(vars_file)
    )
    if emit_json(ctx, json_output, {"compilation": identity}):
        return
    console = Console(highlight=False)
    console.print(
        Panel(
            Text("Compilation retained"),
            title="Updated" if update else "Initialized",
            border_style="green",
        )
    )
    console.print("Compilation: " + identity, markup=False, soft_wrap=True)
    console.print("Next: overspec sync --dry-run", style="cyan")


@guard
def initialize(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
    vars_file: VarsOption = None,
):
    """Evaluate compile-time traits and retain the first compilation."""
    compilation(ctx, home, project, vars_file, json_output, update=False)


@guard
def update(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
    vars_file: VarsOption = None,
):
    """Refresh compile-time traits after source, tool, or profile changes."""
    compilation(ctx, home, project, vars_file, json_output, update=True)


@guard
def sync(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
    vars_file: VarsOption = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview candidate YAML and changes without writing.",
            rich_help_panel="Output",
        ),
    ] = False,
):
    """Preview or synchronize trait guidance into OpenSpec configuration."""
    result = target(ctx, home, project).sync(
        dry_run=dry_run, values=json_file(vars_file)
    )
    if emit_json(ctx, json_output, result):
        return
    console = Console(highlight=False)
    status = (
        "Would change"
        if dry_run and result["changed"]
        else "Updated"
        if result["changed"]
        else "Unchanged"
    )
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column(overflow="fold")
    summary.add_row("Status", status)
    summary.add_row("Target", Text(result["path"]))
    summary.add_row("Resolution", Text(result["resolution"]))
    console.print(
        Panel(
            summary,
            title="Sync preview" if dry_run else "Sync",
            border_style="cyan" if dry_run else "green",
        )
    )
    console.print(result["ownership"], markup=False)
    if dry_run:
        console.rule("Candidate YAML")
        show_source(console, result["candidate"], "yaml")
        console.rule("Changes")
        if result["diff"]:
            show_source(console, result["diff"], "diff")
        else:
            console.print("No configuration changes.")


def show_source(console, text, language):
    if console.is_terminal:
        console.print(
            Syntax(text, language, word_wrap=True, background_color="default")
        )
    else:
        # Let the output stream apply its platform newline translation once.
        typer.echo(text.replace("\r\n", "\n"), nl=False)
