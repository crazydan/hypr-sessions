import json
import os
import time

import typer
from rich.console import Console

from hypr.sessions.commons import (
    APPS_TOML,
    STATE,
    launch_applications_with_logging,
    place_windows,
    read_toml,
    setup_logging,
    wait_for_windows,
)

console = Console()


def _show_dry_run_preview(desired: list, app_map: dict, input: str) -> None:
    """Show what would be restored in dry run mode."""
    console.print(f"🔍 [bold yellow]DRY RUN[/bold yellow] - Would restore {len(desired)} windows")
    console.print("\n[bold]Applications that would be launched:[/bold]")
    missing_mappings = []

    for entry in desired:
        app_key = entry.get("class") or entry.get("app_id") or "unknown"
        title = entry.get("title", "")
        workspace = entry.get("workspace", "unknown")
        floating = "floating" if entry.get("floating") else "tiled"

        # Check for command mapping
        key = entry.get("class") or entry.get("app_id") or entry.get("app_key") or "unknown"
        application_type = entry.get("kind", "")

        cmd = _get_command_for_entry(entry, app_map, application_type)

        if cmd:
            console.print(f"  • {app_key} - '{title}' (workspace {workspace}, {floating})")
            console.print(f"    [dim]Command: hyprctl dispatch exec -- {cmd}[/dim]")
        else:
            console.print(f"  • [red]{app_key}[/red] - '{title}' (workspace {workspace}, {floating})")
            console.print("    [red]❌ No command mapping found[/red]")
            missing_mappings.append(key)

    if missing_mappings:
        console.print(f"\n[bold red]Missing mappings in {APPS_TOML}:[/bold red]")
        for missing in missing_mappings:
            console.print(f"  • {missing}")
        console.print("\n[dim]Add these to your session-apps.toml file to enable launching.[/dim]")

    console.print(f"\n[bold]Session would be restored from:[/bold] [cyan]{input}[/cyan]")


def _get_command_for_entry(entry: dict, app_map: dict, application_type: str) -> str:
    """Get command for a window entry based on its type and mapping."""
    # For application type, try apps mapping first
    if application_type == "application":
        cmd = app_map.get("apps", {}).get(entry.get("class"), "")
        if cmd:
            return cmd

    # Try fallback mapping with various keys
    for alt in (entry.get("class"), entry.get("app_id"), entry.get("app_key")):
        if alt and alt in app_map:
            return app_map[alt]

    return ""


def restore_session(
    input: str = typer.Option(STATE, "-i", "--input", help="Input file path for the session state", show_default=True),
    apps_toml: str = typer.Option(
        APPS_TOML, "-a", "--apps-toml", help="Path to apps TOML configuration file", show_default=True
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be restored without actually restoring"),
    verbose: int = typer.Option(
        0, "-v", "--verbose", count=True, help="Increase verbosity (use -vvv for maximum verbosity)"
    ),
) -> None:
    """Restore a previously saved Hyprland session."""

    # Configure logging based on verbosity level
    logger = setup_logging(verbose, __name__)

    logger.info(f"Restoring session from: {input}")
    logger.info(f"Using apps configuration from: {apps_toml}")

    if not os.path.exists(input):
        console.print(
            "❌ No saved session found. Run [cyan]hypr-sessions save[/cyan] first or specify a valid input file."
        )
        raise typer.Exit(getattr(os, "EX_SOFTWARE", 1))

    try:
        with open(input) as f:
            snapshot = json.load(f)

        desired = snapshot.get("clients", [])
        if not desired:
            console.print("❌ Saved session is empty.")
            raise typer.Exit(getattr(os, "EX_SOFTWARE", 1))

        appmap = read_toml(apps_toml)

        if dry_run:
            _show_dry_run_preview(desired, appmap, input)
        else:
            # 1) launch apps: one process per saved window
            launched = launch_applications_with_logging(desired, appmap, logger)
            console.print(f"🚀 Launched {launched}/{len(desired)} applications")

            # 2) wait for windows to appear (up to 30s)
            deadline = time.time() + 30
            console.print("⏳ Waiting for windows to appear...")

            now = wait_for_windows(desired, deadline)

            # 3) match and place windows
            placed = place_windows(desired, now)

            console.print(f"✅ Restore complete. Placed {placed}/{len(desired)} windows.")
        raise typer.Exit(getattr(os, "EX_OK", 0))

    except Exception as e:
        console.print(f"❌ Error restoring session: [red]{e}[/red]")
        raise typer.Exit(getattr(os, "EX_SOFTWARE", 1)) from e
