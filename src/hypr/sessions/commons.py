import json
import logging
import os
import subprocess
import sys
import time
import tomllib
from email.quoprimime import quote
from typing import Final

import verboselogs  # type: ignore
from rich.console import Console

# Common constants
APPS_TOML: Final[str] = os.path.expanduser("~/.config/hypr/session-apps.toml")
STATE: Final[str] = os.path.expanduser("~/.local/state/hypr/session.json")

console = Console()


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


def launch(cmd, entry):
    if "{cwd}" in cmd:
        cmd = cmd.replace("{cwd}", quote(entry.get("cwd") or os.path.expanduser("~")))
    if "{url}" in cmd:
        cmd = cmd.replace("{url}", quote(entry.get("url", "")))

    # use Hyprland exec so env is correct
    subprocess.Popen(["hyprctl", "dispatch", "exec", "--", cmd])


def best_key(entry):
    return entry.get("app_id") or entry.get("class") or entry.get("app_key")


def match_window(entry: dict, now: list, unmatched: set) -> tuple | None:
    """Match a saved window entry to current windows."""
    key = best_key(entry)
    title = (entry.get("title") or "").lower()
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
        if c.get("floating") == entry.get("floating"):
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


def wait_for_windows(desired: list, deadline: float) -> list:
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


def launch_applications_with_logging(desired: list, appmap: dict, logger) -> int:
    """Launch applications with verbose logging."""
    launched = 0
    for entry in desired:
        key = entry.get("class") or entry.get("app_id") or entry.get("app_key") or "unknown"
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

        # Log the command that will be launched
        logger.info(f"Launching application: {key}")
        logger.verbose(f"Command to execute: hyprctl dispatch exec -- {cmd}")

        # Launch the application
        launch(cmd, entry)
        launched += 1
    return launched


def place_windows(desired: list, now: list) -> int:
    """Place and configure windows according to saved session."""
    unmatched = {i for i, _ in enumerate(now)}
    placed = 0

    for e in desired:
        m = match_window(e, now, unmatched)
        if not m:
            console.print(f"⚠️ Couldn't find a window for [yellow]{best_key(e)}[/yellow] / '{e.get('title')}'")
            continue
        idx, c = m
        unmatched.discard(idx)
        addr = c.get("address")
        ws = e.get("workspace")
        # focus to target subsequent commands
        hypr("focuswindow", f"address:{addr}")
        if ws is not None:
            hypr("movetoworkspacesilent", str(ws))
        # ensure correct floating state
        want_float = bool(e.get("floating"))
        cur_float = bool(c.get("floating"))
        if want_float != cur_float:
            hypr("togglefloating")
        # restore geometry for floating windows
        if want_float and e.get("at") and e.get("size"):
            x, y = e["at"]
            w, h = e["size"]
            hypr("resizewindowpixel", "exact", str(w), str(h))
            hypr("movewindowpixel", "exact", str(x), str(y))
        placed += 1
    return placed
