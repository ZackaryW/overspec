"""Explicit user-level skill management with readable and structured outcomes."""

from pathlib import Path, PurePosixPath
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from zuu.case11 import Choice, CliSelector

from .common import HomeOption, JsonOption, emit_json, scope

app = typer.Typer(
    help="Install packaged skills and recover native changes.", no_args_is_help=True
)
app.callback()(scope)
AgentOption = Annotated[
    list[str] | None,
    typer.Option(
        "--agent",
        help="Native agent; repeat for several, or omit for an interactive checklist.",
        rich_help_panel="Selection",
    ),
]
NameOption = Annotated[
    list[str] | None,
    typer.Option(
        "--name",
        help="Exact skill name; repeat, choose --all, or omit for a checklist.",
        rich_help_panel="Selection",
    ),
]
AllOption = Annotated[
    bool,
    typer.Option(
        "--all",
        help="All catalog skills, or all matching recorded skills for history/recovery.",
        rich_help_panel="Selection",
    ),
]
AgentHomeOption = Annotated[
    Path | None,
    typer.Option(
        "--agent-home",
        help="Native user home; distinct from the Overspec --home.",
        rich_help_panel="Scope",
    ),
]
ForceOption = Annotated[
    bool,
    typer.Option(
        "--force",
        help="Explicitly replace conflicts where restore/remove supports it.",
        rich_help_panel="Conflicts",
    ),
]


def execute(
    ctx,
    operation,
    home,
    agent_home,
    agents,
    names,
    all_skills,
    force,
    json_output,
    operation_id=None,
):
    from overspec.core import skill_assets
    from overspec.core.skills import AGENTS, Skills

    try:
        manager = Skills(home or (ctx.obj or {}).get("home"), agent_home)
        if names and all_skills:
            raise ValueError("Select --name values or --all, exclusively")
        if operation != "list" and not (json_output or (ctx.obj or {}).get("json")):
            if not agents:
                selection = CliSelector(
                    "Select agents (--agent)", (Choice(a, a) for a in AGENTS)
                ).select(required=True)
                if selection.cancelled:
                    typer.echo("Selection cancelled.")
                    raise typer.Exit(130)
                agents = selection.values
            if not names and not all_skills:
                if operation in {"history", "restore", "remove"}:
                    history = manager.run("history", agents=agents, all_skills=True)[
                        "history"
                    ]
                    candidates = sorted(
                        {
                            PurePosixPath(item["locator"]).name
                            for event in history
                            if operation != "restore"
                            or event["operation_id"] == operation_id
                            for item in (*event["before"], *event["after"])
                        }
                    )
                else:
                    candidates = [s.name for s in skill_assets.skill_catalog()]
                if not candidates:
                    raise ValueError("No skills available for this selection")
                selection = CliSelector(
                    "Select skills (--name or --all)",
                    (Choice(n, n) for n in candidates),
                ).select(required=True)
                if selection.cancelled:
                    typer.echo("Selection cancelled.")
                    raise typer.Exit(130)
                names = selection.values
        result = manager.run(
            operation,
            agents=agents or (),
            names=names or (),
            all_skills=all_skills,
            force=force,
            operation_id=operation_id,
        )
    except typer.Exit:
        raise
    except (ValueError, OSError, RuntimeError) as exc:
        result = {"ok": False, "operation": operation, "diagnostics": [str(exc)]}
    if not emit_json(ctx, json_output, result):
        console = Console(highlight=False)
        table = Table(title="Skills: " + operation)
        for heading in ("Agent", "Skill", "Status", "Operation / origin"):
            table.add_column(heading, overflow="fold")
        for item in result.get("skills", []):
            table.add_row("", item["name"], item["version"], item["origin"])
        for item in result.get("results", []):
            status = item.get("status", item.get("classification", "failed"))
            table.add_row(
                item["agent"], item["name"], status, item.get("operation_id") or ""
            )
            for diagnostic in item.get("diagnostics", []):
                console.print(diagnostic, markup=False)
        for item in result.get("history", []):
            targets = item["after"] or item["before"]
            table.add_row(
                ",".join(sorted({a["agent"] for a in targets})),
                ",".join(sorted({a["locator"] for a in targets})),
                item["kind"] + ": " + item["outcome"],
                item["operation_id"],
            )
        console.print(table)
        for diagnostic in result.get("diagnostics", []):
            console.print(diagnostic, markup=False)
        if result.get("registry"):
            console.print("Registry: " + result["registry"], markup=False)
            console.print("Native home: " + result["agent_home"], markup=False)
        if not result["ok"]:
            console.print(
                "Incomplete. Inspect diagnostics and history before an explicit retry or restore."
            )
    if not result["ok"]:
        raise typer.Exit(1)


@app.command("list")
def catalog(
    ctx: typer.Context, home: HomeOption = None, json_output: JsonOption = False
):
    """List the complete packaged skill catalog without native installation."""
    execute(ctx, "list", home, None, (), (), False, False, json_output)


def lifecycle_command(operation):
    if operation != "remove":

        def reconcile(
            ctx: typer.Context,
            home: HomeOption = None,
            agent_home: AgentHomeOption = None,
            agents: AgentOption = None,
            names: NameOption = None,
            all_skills: AllOption = False,
            json_output: JsonOption = False,
        ):
            execute(
                ctx,
                operation,
                home,
                agent_home,
                agents,
                names,
                all_skills,
                False,
                json_output,
            )

        return reconcile

    def command(
        ctx: typer.Context,
        home: HomeOption = None,
        agent_home: AgentHomeOption = None,
        agents: AgentOption = None,
        names: NameOption = None,
        all_skills: AllOption = False,
        force: ForceOption = False,
        json_output: JsonOption = False,
    ):
        execute(
            ctx,
            operation,
            home,
            agent_home,
            agents,
            names,
            all_skills,
            force,
            json_output,
        )

    return command


for name, description in {
    "status": "Inspect selected native skills against packaged content.",
    "install": "Install selected skills, replacing differing existing content with recovery history.",
    "update": "Refresh existing skills, replacing differing content with recovery history.",
    "history": "Read recorded operations for exactly selected skills.",
    "remove": "Remove selected managed skills while retaining recovery history.",
}.items():
    app.command(name, help=description)(lifecycle_command(name))


@app.command("restore")
def restore(
    ctx: typer.Context,
    operation_id: str,
    home: HomeOption = None,
    agent_home: AgentHomeOption = None,
    agents: AgentOption = None,
    names: NameOption = None,
    all_skills: AllOption = False,
    force: ForceOption = False,
    json_output: JsonOption = False,
):
    """Restore selected skill before-state using a recorded operation ID."""
    execute(
        ctx,
        "restore",
        home,
        agent_home,
        agents,
        names,
        all_skills,
        force,
        json_output,
        operation_id,
    )
