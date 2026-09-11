"""Read-only static/runtime resolution and retained detail lookup."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from overspec.core import storage
from overspec.core.projection import config_target, project_yaml
from overspec.core.resolution import (
    contributions,
    explain,
    resolve_runtime,
    show_details,
)

from .common import (
    HomeOption,
    JsonOption,
    ProjectOption,
    VarsOption,
    emit_json,
    guard,
    json_file,
    scope,
    target,
)
from .explanations import explanation_tree

app = typer.Typer(
    help="Resolve guidance or inspect saved trait details.",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.callback()(scope)
ResolutionOption = Annotated[
    str | None,
    typer.Option(
        "--resolution",
        help="Current saved resolution ID; superseded IDs fail without loading history.",
        rich_help_panel="Saved resolution",
    ),
]


@app.command("resolve")
@guard
def resolve(
    ctx: typer.Context,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
    vars_file: VarsOption = None,
    explain_output: Annotated[
        bool,
        typer.Option(
            "--explain",
            help="Explain static matches, suppression, and source origins.",
            rich_help_panel="Output",
        ),
    ] = False,
    attach: Annotated[
        str | None,
        typer.Option(
            help="Exact attachment point for runtime resolution.",
            rich_help_panel="Runtime",
        ),
    ] = None,
    traits: Annotated[
        list[str] | None,
        typer.Option(
            "--trait",
            help="Runtime trait ID; repeat for every requested trait.",
            rich_help_panel="Runtime",
        ),
    ] = None,
    context_file: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            help="JSON context for this runtime invocation only.",
            rich_help_panel="Runtime",
        ),
    ] = None,
    change_root: Annotated[
        Path | None,
        typer.Option(
            help="Explicit OpenSpec-resolved change root for live runtime variables.",
            rich_help_panel="Runtime",
        ),
    ] = None,
):
    """Resolve static guidance or evaluate a current runtime trait group."""
    project_target = target(ctx, home, project)
    if attach or traits or context_file or change_root:
        if explain_output or vars_file or not attach or not traits:
            raise typer.BadParameter(
                "Runtime resolve requires --attach and --trait; use --context-file for inputs."
            )
        result = resolve_runtime(
            project_target,
            attach,
            traits,
            json_file(context_file),
            change=change_root,
        )
    else:
        if explain_output and not storage.has_compilation(project_target.root):
            json_file(vars_file)  # Validate supplied input without evaluating traits.
            plan = project_target.source_inputs()
            effective, overridden, _, _ = project_target.inventory(inputs=plan)
            decisions = [
                {
                    "name": t.name,
                    "phase": t.phase,
                    "attach": t.attach,
                    "origin": t.origin,
                    "provenance": t.provenance,
                    "has_details": bool(t.details),
                    "decision": None,
                    "status": "deferred"
                    if t.phase == "runtime-trait"
                    else "unevaluated",
                    "reason": "Run init to retain compilation before resolving guidance.",
                }
                for t in effective
            ]
            decisions.extend(
                {
                    "name": t.name,
                    "phase": t.phase,
                    "attach": t.attach,
                    "origin": t.origin,
                    "provenance": t.provenance,
                    "status": "overridden",
                }
                for t in overridden
            )
            decisions.extend(
                {
                    "name": item["source_id"],
                    "phase": "source",
                    "attach": "-",
                    "origin": "saucepan:" + item["source_id"],
                    "status": "excluded",
                    **item,
                }
                for item in plan.excluded
            )
            show_explanations(ctx, json_output, decisions)
            return
        bundle = project_target.prepare(values=json_file(vars_file))
        result = contributions(bundle)
        project_yaml(
            config_target(project_target.root).read_text(encoding="utf-8"), result
        )
        if explain_output:
            decisions = explain(bundle)
            show_explanations(ctx, json_output, decisions)
            return
    if not emit_json(ctx, json_output, result) and result:
        # Guidance is a literal protocol payload: no markup interpretation or wrapping.
        typer.echo(
            "\n\n".join(
                item["body"].rstrip("\n") + f"\n<!-- over:{item['name']} -->"
                for item in result
            )
        )


@app.command("show")
@guard
def show(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Trait name in the saved resolution.")],
    details: Annotated[
        bool,
        typer.Option(
            "--details",
            help="Read the retained explanation without evaluating the trait.",
        ),
    ] = False,
    resolution: ResolutionOption = None,
    home: HomeOption = None,
    project: ProjectOption = None,
    json_output: JsonOption = False,
):
    """Read last-synced literal details; an explicit ID must match current state."""
    if not details:
        raise typer.BadParameter("Use --details to read the saved explanation.")
    result = show_details(target(ctx, home, project).root, name, resolution)
    if not emit_json(ctx, json_output, result):
        typer.echo(
            f"{result['name']} ({result['phase']}, {result['attach']})\nSource: {result['origin']}\n\n{result['details'] or result['message']}"
        )


def show_explanations(ctx, json_output, decisions):
    if emit_json(ctx, json_output, decisions):
        return
    table = Table(title="Trait resolution", expand=True)
    for column in (
        "Trait",
        "Phase",
        "Status",
        "Attachment",
        "Source",
    ):
        table.add_column(column, overflow="fold")
    for item in decisions:
        table.add_row(
            *(
                Text(str(item[key]))
                for key in ("name", "phase", "status", "attach", "origin")
            ),
        )
    console = Console(highlight=False)
    console.print(table)
    for item in decisions:
        if item.get("reason"):
            console.print(Text(item["reason"]))
        if (item.get("provenance") or {}).get("source_id"):
            provenance = item["provenance"]
            console.print(
                Text(
                    f"{item['name']}: revision {provenance['revision']}, "
                    f"snapshot {provenance['snapshot']}, layout {provenance['layout']}"
                )
            )
        elif (item.get("provenance") or {}).get("package"):
            provenance = item["provenance"]
            console.print(
                Text(
                    f"{item['name']}: package {provenance['package']} {provenance['version']}"
                )
            )
        if item.get("decision"):
            console.print(explanation_tree(item))
