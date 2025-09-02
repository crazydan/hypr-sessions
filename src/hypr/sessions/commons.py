import json
import logging
import os
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from email.quoprimime import quote
from enum import StrEnum
from typing import Final

import verboselogs  # type: ignore
from rich.console import Console

# Common constants
APPS_TOML: Final[str] = os.path.expanduser("~/.config/hypr/session-apps.toml")
STATE: Final[str] = os.path.expanduser("~/.local/state/hypr/session.json")

# Constants for validation
POSITION_SIZE: Final[int] = 2  # [x, y] or [width, height]

console = Console()


class WindowKind(StrEnum):
    """Enumeration of supported window types."""

    PWA = "pwa"
    BROWSER = "browser"
    TERMINAL = "terminal"
    APPLICATION = "application"


@dataclass
class ClientEntry:
    """Data class representing a saved client/window entry with validation."""

    # Mandatory fields
    kind: WindowKind
    class_name: str  # Using class_name to avoid Python keyword conflict
    title: str
    workspace: int
    floating: bool
    at: list[int]  # [x, y] position
    size: list[int]  # [width, height]
    monitor: int

    # Optional fields
    app_id: str | None = None
    pid: int | None = None
    cwd: str | None = None
    pwa_key: str | None = None

    def __post_init__(self):
        """Validate the client entry after initialization."""
        # Validate position and size arrays
        if len(self.at) != POSITION_SIZE:
            raise ValueError(f"Position 'at' must be [x, y], got: {self.at}")
        if len(self.size) != POSITION_SIZE:
            raise ValueError(f"Size must be [width, height], got: {self.size}")

        # Validate PWA entries have pwa_key
        if self.kind == WindowKind.PWA and not self.pwa_key:
            raise ValueError("PWA entries must have a pwa_key")

        # Validate workspace is positive
        if self.workspace <= 0:
            raise ValueError(f"Workspace must be positive, got: {self.workspace}")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization, filtering out null values."""
        result = {
            "class": self.class_name,
            "title": self.title,
            "workspace": self.workspace,
            "floating": self.floating,
            "at": self.at,
            "size": self.size,
            "monitor": self.monitor,
            "kind": self.kind.value,
        }

        # Only add optional fields if they have values
        if self.app_id is not None:
            result["app_id"] = self.app_id
        if self.pid is not None:
            result["pid"] = self.pid
        if self.cwd is not None:
            result["cwd"] = self.cwd
        if self.pwa_key is not None:
            result["pwa_key"] = self.pwa_key

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ClientEntry":
        """Create a ClientEntry from a dictionary (e.g., from JSON)."""
        return cls(
            kind=WindowKind(data["kind"]),
            class_name=data["class"],
            title=data["title"],
            workspace=data["workspace"],
            floating=data["floating"],
            at=data["at"],
            size=data["size"],
            monitor=data["monitor"],
            app_id=data.get("app_id"),
            pid=data.get("pid"),
            cwd=data.get("cwd"),
            pwa_key=data.get("pwa_key"),
        )


def setup_logging(verbose: int, logger_name: str = __name__) -> verboselogs.VerboseLogger:
    """Configure logging based on verbosity level."""
    logger = verboselogs.VerboseLogger(logger_name)

    if verbose == 0:
        logger.setLevel(logging.WARNING)
    elif verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose >= 2:  # noqa: PLR2004
        logger.setLevel(verboselogs.VERBOSE)
    else:  # 3 or more
        logger.setLevel(logging.DEBUG)

    # Add console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def hyprjson(cmd):
    out = subprocess.check_output(["hyprctl", "-j", *cmd], text=True)
    return json.loads(out)


def hypr(*args):
    try:
        subprocess.run(["hyprctl", "dispatch", *args], check=False)
    except FileNotFoundError:
        print("hyprctl not found", file=sys.stderr)


def read_toml(path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        # ultra-basic fallback: supports [section] then key="value"
        data, sec = {}, None
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    ln = line.strip()
                    if not ln or ln.startswith("#"):
                        continue
                    if ln.startswith("[") and ln.endswith("]"):
                        sec = ln.strip("[]")
                        data.setdefault(sec, {})
                    elif "=" in ln and sec:
                        k, v = ln.split("=", 1)
                        data[sec][k.strip().strip('"')] = v.strip().strip('"')
        return data


def pwa_key_for(title, pwa_map):
    if not title:
        return None
    t = title.lower()
    # longest-key-first to disambiguate
    for key in sorted(pwa_map.keys(), key=len, reverse=True):
        if key.lower() in t:
            return key
    return None


def launch(cmd: str, entry: ClientEntry) -> None:
    """Launch a command with template substitution."""
    if "{cwd}" in cmd:
        cmd = cmd.replace("{cwd}", quote(entry.cwd or os.path.expanduser("~")))
    if "{url}" in cmd:
        cmd = cmd.replace("{url}", quote(""))  # URL not stored in ClientEntry yet

    # use Hyprland exec so env is correct
    subprocess.Popen(["hyprctl", "dispatch", "exec", "--", cmd])


def best_key(entry: ClientEntry) -> str:
    """Get the best key for identifying a window entry."""
    return entry.app_id or entry.class_name or "unknown"


def match_window(entry: ClientEntry, now: list, unmatched: set) -> tuple | None:
    """Match a saved window entry to current windows."""
    key = best_key(entry)
    title = (entry.title or "").lower()
    best = None
    best_score = -1
    for idx, c in enumerate(now):
        if idx not in unmatched:
            continue
        ck = c.get("app_id") or c.get("class") or c.get("initialClass")
        if ck != key:
            continue
        score = 1
        ct = (c.get("title") or "").lower()
        if title and ct and (title in ct or ct in title):
            score += 2
        if c.get("floating") == entry.floating:
            score += 1
        if score > best_score:
            best_score = score
            best = (idx, c)
    if best is None:
        # fallback: first any window of same class
        for idx, c in enumerate(now):
            if idx in unmatched:
                ck = c.get("app_id") or c.get("class") or c.get("initialClass")
                if ck == key:
                    return idx, c
        return None
    return best


def wait_for_windows(desired: list[ClientEntry], deadline: float) -> list:
    """Wait for windows to appear after launching."""

    def current_clients():
        try:
            return hyprjson("clients")
        except Exception:
            return []

    now = []
    while time.time() < deadline:
        now = current_clients()
        # simple readiness: have we got at least as many windows of each app_key?
        want_counts: dict[str, int] = {}
        got_counts: dict[str, int] = {}
        for e in desired:
            want_counts[best_key(e)] = want_counts.get(best_key(e), 0) + 1
        for c in now:
            k = c.get("app_id") or c.get("class") or c.get("initialClass")
            got_counts[k] = got_counts.get(k, 0) + 1
        ok = all(got_counts.get(k, 0) >= want_counts[k] for k in want_counts)
        if ok:
            break
        time.sleep(1)
    return now


def launch_applications(desired: list, appmap: dict) -> int:
    """Launch applications for the session."""
    launched = 0
    for entry in desired:
        key = best_key(entry)
        cmd = appmap.get(key)
        if not cmd:
            # try a couple of guesses
            for alt in (entry.get("class"), entry.get("app_id"), entry.get("app_key")):
                if alt and alt in appmap:
                    cmd = appmap[alt]
                    break
        if not cmd:
            console.print(
                f"⚠️ No launcher for [yellow]{key}[/yellow] (class={entry.get('class')} app_id={entry.get('app_id')})"
            )
            continue
        launch(cmd, entry)
        launched += 1
    return launched


def launch_applications_with_logging(desired: list[ClientEntry], appmap: dict, logger) -> int:
    """Launch applications with verbose logging."""
    launched = 0
    for entry in desired:
        key = entry.class_name or "unknown"

        # Get command based on window type
        cmd = None
        if entry.kind == WindowKind.PWA and entry.pwa_key:
            cmd = appmap.get("pwa", {}).get(entry.pwa_key)
        elif entry.kind in (WindowKind.APPLICATION, WindowKind.TERMINAL):
            cmd = appmap.get("apps", {}).get(entry.class_name)

        # Fallback to direct mapping
        if not cmd:
            for alt in (entry.class_name, entry.app_id):
                if alt and alt in appmap:
                    cmd = appmap[alt]
                    break

        if not cmd:
            console.print(f"⚠️ No launcher for [yellow]{key}[/yellow] (class={entry.class_name} app_id={entry.app_id})")
            continue

        # Log the command that will be launched
        logger.info(f"Launching application: {key}")
        logger.verbose(f"Command to execute: hyprctl dispatch exec -- {cmd}")

        # Launch the application
        launch(cmd, entry)
        launched += 1
    return launched


def place_windows(desired: list[ClientEntry], now: list) -> int:
    """Place and configure windows according to saved session."""
    unmatched = {i for i, _ in enumerate(now)}
    placed = 0

    for e in desired:
        m = match_window(e, now, unmatched)
        if not m:
            console.print(f"⚠️ Couldn't find a window for [yellow]{best_key(e)}[/yellow] / '{e.title}'")
            continue
        idx, c = m
        unmatched.discard(idx)
        addr = c.get("address")
        ws = e.workspace
        # focus to target subsequent commands
        hypr("focuswindow", f"address:{addr}")
        if ws is not None:
            hypr("movetoworkspacesilent", str(ws))
        # ensure correct floating state
        want_float = bool(e.floating)
        cur_float = bool(c.get("floating"))
        if want_float != cur_float:
            hypr("togglefloating")
        # restore geometry for floating windows
        if want_float and e.at and e.size:
            x, y = e.at
            w, h = e.size
            hypr("resizewindowpixel", "exact", str(w), str(h))
            hypr("movewindowpixel", "exact", str(x), str(y))
        placed += 1
    return placed
