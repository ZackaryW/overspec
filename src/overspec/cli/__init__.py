"""Typer application entry point for overspec."""

import typer

from .common import scope
from .profile_mode import InvocationGroup
from .profiles import app as profiles
from .project import initialize, sync, update
from .skills import app as skills
from .traits import app as traits

app = typer.Typer(
    name="overspec",
    cls=InvocationGroup,
    help="Compose reusable traits into native OpenSpec guidance.",
    epilog="Start with: overspec init, then overspec sync --dry-run.",
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.callback()(scope)
app.command("init", rich_help_panel="Project workflow")(initialize)
app.command("update", rich_help_panel="Project workflow")(update)
app.command("sync", rich_help_panel="Project workflow")(sync)
app.add_typer(profiles, name="profile", rich_help_panel="Profiles and traits")
app.add_typer(traits, name="trait", rich_help_panel="Profiles and traits")
app.add_typer(skills, name="skill", rich_help_panel="Agent setup")


def main(argv=None):
    """Keep the console and embedded callers on the same exit-code contract."""
    try:
        app(args=argv, prog_name="overspec")
        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0 if exc.code is None else 1
