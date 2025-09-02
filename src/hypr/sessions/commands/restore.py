import json
import os
import time

import typer
from rich.console import Console

from hypr.sessions.commons import (
    APPS_TOML,
    STATE,
    ClientEntry,
    WindowKind,
    launch_applications_with_logging,
    place_windows,
    read_toml,
    setup_logging,
    wait_for_windows,
)

console = Console()


def _show_dry_run_preview(desired: list[ClientEntry], app_map: dict, input: str) -> None:
    """Show what would be restored in dry run mode."""
    console.print(f"🔍 [bold yellow]DRY RUN[/bold yellow] - Would restore [green]{len(desired)}[/green] windows")
    console.print(f"   Session file: [cyan]{input}[/cyan]")
    console.print("\n[bold]Applications that would be launched:[/bold]")
    missing_mappings = []

    for entry in desired:
        app_key = entry.class_name or "unknown"
        title = entry.title
        workspace = entry.workspace
        floating = "floating" if entry.floating else "tiled"

        # Check for command mapping
        cmd = _get_command_for_entry(entry, app_map)

        # Color-code by window kind
        kind_colors = {
            WindowKind.PWA: "magenta",
            WindowKind.BROWSER: "green",
            WindowKind.TERMINAL: "red",
            WindowKind.APPLICATION: "white",
        }
        kind_color = kind_colors.get(entry.kind, "white")

        if cmd:
            console.print(
                f"  • [{kind_color}]{app_key}[/{kind_color}] - '{title}' "
                f"(workspace [blue]{workspace}[/blue], [yellow]{floating}[/yellow])"
            )
            console.print(f"    [dim]Command: hyprctl dispatch exec -- {cmd}[/dim]")
        else:
            console.print(
                f"  • [red]{app_key}[/red] - '{title}' "
                f"(workspace [blue]{workspace}[/blue], [yellow]{floating}[/yellow])"
            )
            console.print("    [red]❌ No command mapping found[/red]")
            missing_mappings.append(app_key)

    if missing_mappings:
        console.print(f"\n[bold red]Missing mappings in {APPS_TOML}:[/bold red]")
        for missing in missing_mappings:
            console.print(f"  • {missing}")
        console.print("\n[dim]Add these to your session-apps.toml file to enable launching.[/dim]")

    console.print(f"\n[bold]Session would be restored from:[/bold] [cyan]{input}[/cyan]")


def _get_command_for_entry(entry: ClientEntry, app_map: dict) -> str:
    """Get command for a window entry based on its type and mapping."""
    # For PWA applications, check pwa mapping first
    if entry.kind == WindowKind.PWA and entry.pwa_key:
        cmd = app_map.get("pwa", {}).get(entry.pwa_key, "")
        if cmd:
            return cmd

    # For regular applications, try apps mapping
    if entry.kind in (WindowKind.APPLICATION, WindowKind.TERMINAL):
        cmd = app_map.get("apps", {}).get(entry.class_name, "")
        if cmd:
            return cmd

    # Try fallback mapping with various keys
    for alt in (entry.class_name, entry.app_id):
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

    console.print(f"🔄 Restoring session from: [cyan]{input}[/cyan]")
    console.print(f"📋 Using apps configuration from: [cyan]{apps_toml}[/cyan]")

    if not os.path.exists(input):
        console.print(
            "❌ No saved session found. Run [cyan]hypr-sessions save[/cyan] first or specify a valid input file."
        )
        raise typer.Exit(getattr(os, "EX_SOFTWARE", 1))

    try:
        with open(input) as f:
            snapshot = json.load(f)

        client_data = snapshot.get("clients", [])
        if not client_data:
            console.print("❌ Saved session is empty.")
            raise typer.Exit(getattr(os, "EX_SOFTWARE", 1))

        # Convert dict data to ClientEntry objects
        desired = [ClientEntry.from_dict(client) for client in client_data]
        logger.verbose(f"Loaded {len(desired)} client entries from session file")

        appmap = read_toml(apps_toml)

        if dry_run:
            _show_dry_run_preview(desired, appmap, input)
        else:
            # 1) launch apps: one process per saved window
            launched = launch_applications_with_logging(desired, appmap, logger)
            console.print(f"🚀 Launched [green]{launched}[/green]/[blue]{len(desired)}[/blue] applications")

            # 2) wait for windows to appear (up to 30s)
            deadline = time.time() + 30
            console.print("⏳ Waiting for windows to appear...")

            now = wait_for_windows(desired, deadline)

            # 3) match and place windows
            placed = place_windows(desired, now)

            console.print(f"✅ Restore complete. Placed [green]{placed}[/green]/[blue]{len(desired)}[/blue] windows.")
        raise typer.Exit(getattr(os, "EX_OK", 0))

    except Exception as e:
        console.print(f"❌ Error restoring session: [red]{e}[/red]")
        raise typer.Exit(getattr(os, "EX_SOFTWARE", 1)) from e
