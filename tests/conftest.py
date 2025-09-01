"""
Test configuration and shared fixtures for pytest.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        session_data = {
            "windows": [{"class": "firefox", "title": "Test Browser"}, {"class": "code", "title": "VS Code"}],
            "workspaces": [{"id": 1, "name": "workspace1"}, {"id": 2, "name": "workspace2"}],
        }
        json.dump(session_data, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_apps_file():
    """Create a temporary apps TOML file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        apps_content = """
[firefox]
exec = "firefox"
match_class = "firefox"

[code]
exec = "code"
match_class = "code"
"""
        f.write(apps_content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_console():
    """Mock Rich console for testing output."""
    return MagicMock(spec=Console)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_hyprctl():
    """Mock hyprctl command responses."""

    def _mock_hyprctl(args, *_args, **_kwargs):
        if "clients" in args:
            return MagicMock(
                returncode=0,
                stdout='[{"class": "firefox", "title": "Test Browser"}, {"class": "code", "title": "VS Code"}]',
            )
        if "workspaces" in args:
            return MagicMock(returncode=0, stdout='[{"id": 1, "name": "workspace1"}, {"id": 2, "name": "workspace2"}]')
        return MagicMock(returncode=0, stdout="")

    with patch("subprocess.run", side_effect=_mock_hyprctl) as mock:
        yield mock


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "windows": [
            {"class": "firefox", "title": "Test Browser"},
            {"class": "code", "title": "VS Code"},
            {"class": "unknown-app", "title": "Unknown Application"},
        ],
        "workspaces": [{"id": 1, "name": "workspace1"}, {"id": 2, "name": "workspace2"}],
    }


@pytest.fixture
def sample_apps_data():
    """Sample apps configuration for testing."""
    return {"firefox": {"exec": "firefox", "match_class": "firefox"}, "code": {"exec": "code", "match_class": "code"}}
