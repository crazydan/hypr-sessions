# type: ignore
# ruff: noqa

"""
Tests for the commons module - comprehensive test suite.
"""

import logging
import os
import subprocess
from unittest.mock import MagicMock, mock_open, patch

from hypr.sessions.commons import (
    APPS_TOML,
    STATE,
    best_key,
    hypr,
    hyprjson,
    launch,
    launch_applications,
    launch_applications_with_logging,
    match_window,
    place_windows,
    pwa_key_for,
    read_toml,
    setup_logging,
    wait_for_windows,
)


def test_constants_exist():
    """Test that required constants are defined."""
    assert STATE is not None
    assert APPS_TOML is not None
    assert isinstance(STATE, str)
    assert isinstance(APPS_TOML, str)


def test_setup_logging_no_verbosity():
    """Test setup_logging with no verbosity."""
    logger = setup_logging(0)
    assert logger.level == logging.WARNING


def test_setup_logging_with_verbosity():
    """Test setup_logging with different verbosity levels."""
    # Test verbose level 1
    logger1 = setup_logging(1)
    assert logger1.level == logging.INFO

    # Test verbose level 2
    logger2 = setup_logging(2)
    assert logger2.level == 15  # VERBOSE level

    # Test verbose level 3
    logger3 = setup_logging(3)
    assert logger3.level == logging.DEBUG


def test_hyprjson_success():
    """Test successful hyprjson call."""
    with patch("subprocess.check_output") as mock_check_output:
        mock_check_output.return_value = '{"test": "data"}'

        result = hyprjson(["clients"])

        assert result == {"test": "data"}
        mock_check_output.assert_called_once_with(["hyprctl", "-j", "clients"], text=True)


def test_hyprjson_failure():
    """Test hyprjson with subprocess failure."""
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "hyprctl")):
        try:
            hyprjson(["invalid"])
            raise AssertionError("Should have raised exception")
        except subprocess.CalledProcessError:
            pass  # Expected


def test_hypr_success():
    """Test successful hypr call."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        result = hypr("dispatch", "workspace", "1")

        assert result == 0
        mock_run.assert_called_once_with(["hyprctl", "dispatch", "workspace", "1"], check=False)


def test_hypr_failure():
    """Test hypr with command failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1

        result = hypr("invalid", "command")

        assert result == 1


def test_read_toml_success():
    """Test successful TOML file reading."""
    with patch("builtins.open", mock_open(read_data="[test]\nkey = 'value'")), patch("tomllib.load") as mock_load:
        mock_load.return_value = {"test": {"key": "value"}}

        result = read_toml("/path/to/file.toml")

        assert result == {"test": {"key": "value"}}


def test_read_toml_file_not_found():
    """Test read_toml with missing file."""
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        result = read_toml("/path/to/missing.toml")

        assert result == {}


def test_pwa_key_for_found():
    """Test pwa_key_for with matching PWA."""
    pwa_map = {"github": {"match_title": "GitHub"}}

    result = pwa_key_for("GitHub - Repository", pwa_map)

    assert result == "github"


def test_pwa_key_for_not_found():
    """Test pwa_key_for with no matching PWA."""
    pwa_map = {"github": {"match_title": "GitHub"}}

    result = pwa_key_for("Different Title", pwa_map)

    assert result is None


def test_best_key_with_pwa():
    """Test best_key with PWA entry."""
    entry = {"pwa": "github"}

    result = best_key(entry)

    assert result == "github"


def test_best_key_with_class():
    """Test best_key with class entry."""
    entry = {"class": "firefox"}

    result = best_key(entry)

    assert result == "firefox"


def test_best_key_empty():
    """Test best_key with empty entry."""
    entry = {}

    result = best_key(entry)

    assert result is None


def test_launch_success():
    """Test successful application launch."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        entry = {"exec": "firefox", "class": "firefox"}
        launch("firefox", entry)

        mock_popen.assert_called_once()


def test_match_window_success():
    """Test successful window matching."""
    entry = {"class": "firefox", "workspace": {"id": 1}}
    now = [{"class": "firefox", "workspace": {"id": 1}, "address": "0x123"}]
    unmatched = {"0x123"}

    result = match_window(entry, now, unmatched)

    assert result is not None
    assert "0x123" not in unmatched


def test_match_window_no_match():
    """Test window matching with no matches."""
    entry = {"class": "firefox", "workspace": {"id": 1}}
    now = [{"class": "chrome", "workspace": {"id": 1}, "address": "0x123"}]
    unmatched = {"0x123"}

    result = match_window(entry, now, unmatched)

    assert result is None
    assert "0x123" in unmatched


def test_wait_for_windows():
    """Test waiting for windows."""
    desired = [{"class": "firefox"}]

    with patch("time.time", return_value=1000.0), patch("hypr.sessions.commons.hyprjson") as mock_hyprjson:
        mock_hyprjson.return_value = [{"class": "firefox", "address": "0x123"}]

        result = wait_for_windows(desired, 1001.0)

        assert len(result) == 1


def test_launch_applications_success():
    """Test successful application launching."""
    desired = [{"class": "firefox"}]
    appmap = {"firefox": {"exec": "firefox"}}

    with patch("hypr.sessions.commons.launch") as mock_launch:
        result = launch_applications(desired, appmap)

        assert result == 0
        mock_launch.assert_called()


def test_launch_applications_with_logging_main():
    """Test successful application launching with logging."""
    desired = [{"class": "firefox"}]
    appmap = {"firefox": {"exec": "firefox"}}

    with patch("hypr.sessions.commons.launch_applications") as mock_launch_apps:
        mock_launch_apps.return_value = 0
        mock_logger = MagicMock()

        result = launch_applications_with_logging(desired, appmap, mock_logger)

        assert result == 0
        mock_launch_apps.assert_called_once()


def test_place_windows_success():
    """Test successful window placement."""
    desired = [{"class": "firefox", "workspace": {"id": 1}}]
    now = [{"class": "firefox", "workspace": {"id": 2}, "address": "0x123"}]

    with patch("hypr.sessions.commons.hypr") as mock_hypr:
        mock_hypr.return_value = 0

        result = place_windows(desired, now)

        assert result == 0
        mock_hypr.assert_called()


def test_constants_point_to_files():
    """Test that constants point to valid file paths."""
    # Just check that they're strings with reasonable extensions
    assert STATE.endswith(".json")
    assert APPS_TOML.endswith(".toml")

    # Check that they're absolute paths
    assert os.path.isabs(STATE)
    assert os.path.isabs(APPS_TOML)


def test_setup_logging_creates_handlers():
    """Test that setup_logging creates proper handlers."""
    logger = setup_logging(1, "test.logger")

    # Verify logger was configured
    assert logger.name == "test.logger"
    assert logger.level == logging.INFO
