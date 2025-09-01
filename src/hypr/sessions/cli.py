import sys

import typer
from rich.console import Console

from hypr.sessions.commands import restore_session, save_session

console = Console()
app = typer.Typer(
    name="hypr-sessions",
    help="Hyprland session manager - save and restore window layouts",
    rich_markup_mode="rich",
)

# Register commands
app.command("save")(save_session)
app.command("restore")(restore_session)


def main() -> int:
    """Main entry point for the CLI application."""
    return app()


if __name__ == "__main__":
    sys.exit(main())
