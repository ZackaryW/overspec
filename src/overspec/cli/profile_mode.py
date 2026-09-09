"""Resolve invocation home before dispatching the optional profile commands."""

import typer
from typer.core import TyperGroup

from overspec.core.profiles import profiles_enabled
from overspec.core.project import Project


def option_arities(command):
    result = {}
    for param in command.params:
        if param.param_type_name == "option":
            for name in param.opts + param.secondary_opts:
                result[name] = 0 if param.is_flag else param.nargs
    for child in getattr(command, "commands", {}).values():
        result.update(option_arities(child))
    return result


class InvocationGroup(TyperGroup):
    def parse_args(self, ctx, args):
        # A command-level --home must govern command availability before dispatch.
        # Only inspect declared options, consuming their values without executing
        # callbacks. Typer still performs all argument validation afterward.
        arities = option_arities(self)
        home = None
        index = 0
        while index < len(args):
            token = args[index]
            if token == "--":
                break
            option, separator, value = token.partition("=")
            count = arities.get(option, 0)
            if option == "--home":
                if separator:
                    home = value
                elif index + 1 < len(args):
                    home = args[index + 1]
            index += 1 + (count if not separator else 0)
        ctx.meta["profile_home"] = Project(home=home).home
        return super().parse_args(ctx, args)


class ProfileGroup(TyperGroup):
    def __init__(self, *args, **kwargs):
        # Typer's suggestions consult the full registration dictionary instead
        # of list_commands, which would disclose disabled commands.
        kwargs["suggest_commands"] = False
        super().__init__(*args, **kwargs)

    def enabled(self, ctx):
        home = ctx.meta.get("profile_home", Project().home)
        try:
            return profiles_enabled(home)
        except (ValueError, OSError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    def list_commands(self, ctx):
        return super().list_commands(ctx) if self.enabled(ctx) else ["activate"]

    def get_command(self, ctx, cmd_name):
        if cmd_name != "activate" and not self.enabled(ctx):
            return None
        return super().get_command(ctx, cmd_name)
