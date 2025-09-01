import contextlib
import json
import os
import pathlib
import re
import time

import typer
import verboselogs  # type: ignore
from rich.console import Console

from hypr.sessions.commons import APPS_TOML, STATE, hyprjson, pwa_key_for, read_toml, setup_logging

console = Console()


def _get_terminal_cwd(client: dict, logger) -> str | None:
    """Get the current working directory for terminal applications."""
    pid = client.get("pid")
    term_classes = {"Alacritty", "foot"}
    if pid and (client.get("class") in term_classes):
        with contextlib.suppress(Exception):
            cwd = os.path.realpath(f"/proc/{pid}/cwd")
            logger.verbose(f"Detected terminal with cwd: {cwd}")
            return cwd
    return None


def _create_client_entry(client: dict, pwa_map: dict, logger) -> dict:
    """Create a client entry from Hyprland client data."""
    app_class = client.get("class") or client.get("initialClass")
    title = client.get("title")
    workspace_id = (client.get("workspace") or {}).get("id")
    is_floating = client.get("floating", False)

    logger.verbose(f"Processing window: {app_class} - '{title}'")

    cwd = _get_terminal_cwd(client, logger)

    entry = {
        "class": app_class,
        "app_id": client.get("app_id"),
        "title": title,
        "workspace": workspace_id,
        "floating": is_floating,
        "at": client.get("at"),
        "size": client.get("size"),
        "monitor": client.get("monitor"),
        "pid": client.get("pid"),
        "cwd": cwd,
    }

    # Detect Chromium/Chrome PWA by class pattern or title match
    if app_class and re.match(r"^(chromium|google-chrome|chrome-.*__-Default)$", app_class):
        key = pwa_key_for(title, pwa_map)
        if key:
            entry["kind"] = "pwa"
            entry["pwa_key"] = key
            logger.verbose(f"  → PWA: {key} (workspace {workspace_id}, {'floating' if is_floating else 'tiled'})")
        else:
            entry["kind"] = "browser"
            logger.verbose(f"  → Browser window (workspace {workspace_id}, {'floating' if is_floating else 'tiled'})")
    elif cwd:
        # Terminal application with working directory
        entry["kind"] = "terminal"
        logger.verbose(
            f"  → Terminal app with cwd: {cwd} (workspace {workspace_id}, {'floating' if is_floating else 'tiled'})"
        )
    else:
        # Regular application
        entry["kind"] = "application"
        logger.verbose(f"  → Application window (workspace {workspace_id}, {'floating' if is_floating else 'tiled'})")

    return entry


def _categorize_window(entry: dict) -> str:
    """Categorize a window entry by type."""
    if entry.get("kind") == "pwa":
        return "pwa"
    if entry.get("kind") == "browser":
        return "browser"
    if entry.get("cwd"):
        return "terminal"
    return "application"


def _should_check_mapping(app_class: str) -> bool:
    """Check if an app class should be checked for mappings."""
    if not app_class:
        return False
    system_classes = {"", "hyprland", "Hyprland", "hyprpaper", "waybar", "rofi", "dunst"}
    return app_class not in system_classes


def _log_window_summary(window_types: dict, total_saved: int, logger) -> None:
    """Log a summary of window types in verbose mode."""
    if not logger.isEnabledFor(verboselogs.VERBOSE):
        return

    logger.verbose("\n📊 Window type summary:")
    if window_types["pwa"] > 0:
        logger.verbose(f"  • PWAs: {window_types['pwa']}")
    if window_types["browser"] > 0:
        logger.verbose(f"  • Browser windows: {window_types['browser']}")
    if window_types["terminal"] > 0:
        logger.verbose(f"  • Terminal apps: {window_types['terminal']}")
    if window_types["application"] > 0:
        logger.verbose(f"  • Applications: {window_types['application']}")
    if window_types["skipped"] > 0:
        logger.verbose(f"  • Skipped (unmapped): {window_types['skipped']}")
    logger.verbose(f"  • Total saved: {total_saved}")


def _process_clients(clients: list, pwa_map: dict, app_map: dict, logger) -> tuple[list[dict], set[str]]:
    """Process all clients and return a list of client entries and missing app mappings."""
    saved = []
    missing_mappings = set()

    # Counters for verbose summary
    window_types = {"pwa": 0, "browser": 0, "terminal": 0, "application": 0, "skipped": 0}

    for client in clients:
        if not client.get("mapped", True):
            logger.verbose(f"Skipping unmapped window: {client.get('class', 'unknown')}")
            window_types["skipped"] += 1
            continue

        entry = _create_client_entry(client, pwa_map, logger)
        saved.append(entry)

        # Count window types for summary
        window_category = _categorize_window(entry)
        window_types[window_category] += 1

        # Check if the app class has a mapping in the TOML file
        app_class = client.get("class") or client.get("initialClass")
        if _should_check_mapping(app_class):
            application_type = entry.get("kind", "")
            match application_type:
                case "pwa":
                    if entry["pwa_key"] not in pwa_map:
                        missing_mappings.add(entry["pwa_key"])
                case "browser":
                    pass
                case "application" | "terminal":
                    if app_class not in app_map:
                        missing_mappings.add(app_class)
                case _:
                    logger.warning(f"Application {app_class} has unknown window kind: {application_type}")

    # Log summary in verbose mode
    _log_window_summary(window_types, len(saved), logger)

    return saved, missing_mappings


def _save_to_file(data: dict, output: str, logger) -> None:
    """Save session data to file."""
    logger.verbose(f"Creating directory: {os.path.dirname(output)}")
    pathlib.Path(os.path.dirname(output)).mkdir(parents=True, exist_ok=True)

    logger.verbose(f"Writing session data to file: {output}")
    with open(output, "w") as f:
        json.dump(data, f, indent=2)


def save_session(
    output: str = typer.Option(
        STATE, "-o", "--output", help="Output file path for the session state", show_default=True
    ),
    apps_toml: str = typer.Option(
        APPS_TOML, "-a", "--apps-toml", help="Path to apps TOML configuration file", show_default=True
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be saved without actually saving"),
    verbose: int = typer.Option(
        0, "-v", "--verbose", count=True, help="Increase verbosity (use -vvv for maximum verbosity)"
    ),
) -> None:
    """Save the current Hyprland session to file."""

    logger = setup_logging(verbose, __name__)
    logger.info(f"Saving session to: {output}")
    logger.info(f"Using apps configuration from: {apps_toml}")

    try:
        logger.verbose(f"Reading TOML configuration from: {apps_toml}")
        cfg = read_toml(apps_toml)
        pwa_map = cfg.get("pwa", {})
        logger.verbose(f"Loaded {len(pwa_map)} PWA mappings and {len(cfg.get('apps', {}))} app mappings")

        logger.verbose("Reading Hyprland client and workspace information...")
        clients = hyprjson(["clients"])
        workspaces = hyprjson(["workspaces"])

        logger.info(f"Found {len(clients)} clients and {len(workspaces)} workspaces")

        if logger.isEnabledFor(verboselogs.VERBOSE) and workspaces:
            logger.verbose("\n🖥️  Workspace details:")
            for ws in workspaces:
                logger.verbose(f"  • Workspace {ws.get('id')}: '{ws.get('name')}' on monitor {ws.get('monitor')}")

        saved, missing_mappings = _process_clients(clients, pwa_map, cfg.get("apps", {}), logger)

        # Display warnings for missing app mappings
        if missing_mappings:
            console.print(
                "\n[yellow]⚠️  Warning: The following applications don't have mappings in the apps.toml file:[/yellow]"
            )
            for app_class in sorted(missing_mappings):
                console.print(f"  • [cyan]{app_class}[/cyan]")
            console.print(
                "[dim]Consider adding these to your sessions-apps.toml file for better session restoration.[/dim]\n"
            )

        data = {
            "timestamp": int(time.time()),
            "clients": saved,
            "workspaces": [{"id": w.get("id"), "name": w.get("name"), "monitor": w.get("monitor")} for w in workspaces],
        }

        logger.info(f"Prepared session data with {len(saved)} windows")

        if dry_run:
            logger.info("Dry run mode: displaying session data preview")
            console.print(
                f"🔍 [bold yellow]DRY RUN[/bold yellow] - Would save {len(saved)} windows to [cyan]{output}[/cyan]"
            )
            console.print("\n[bold]Session data preview:[/bold]")
            console.print(json.dumps(data, indent=2))
        else:
            _save_to_file(data, output, logger)
            console.print(f"✅ Saved {len(saved)} windows -> [cyan]{output}[/cyan]")

        logger.info("Save operation completed successfully")
        raise typer.Exit(getattr(os, "EX_OK", 0))

    except Exception as e:
        console.print(f"❌ Error saving session: [red]{e}[/red]")
        raise typer.Exit(getattr(os, "EX_SOFTWARE", 1)) from e
