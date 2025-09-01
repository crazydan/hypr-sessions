# type: ignore
# ruff: noqa

"""
Integration tests for the hypr-sessions CLI application.
"""

import json
import os
import tempfile
from unittest.mock import patch

from typer.testing import CliRunner

from hypr.sessions.cli import app

runner = CliRunner()


class TestCLIIntegration:
    """Integration tests for the CLI application."""

    def test_help_command(self):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Hyprland session management" in result.stdout
        assert "save" in result.stdout
        assert "restore" in result.stdout

    def test_save_help(self):
        """Test save command help."""
        result = runner.invoke(app, ["save", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--verbose" in result.stdout

    def test_restore_help(self):
        """Test restore command help."""
        result = runner.invoke(app, ["restore", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--verbose" in result.stdout

    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_save_command_dry_run(self, mock_makedirs, mock_exists, mock_hyprjson):
        """Test save command in dry run mode."""
        mock_exists.return_value = True
        mock_hyprjson.side_effect = [
            [{"class": "firefox", "title": "Test"}],  # clients
            [{"id": 1, "name": "workspace1"}],  # workspaces
        ]

        result = runner.invoke(app, ["save", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout

    @patch("hypr.sessions.commands.restore.read_toml")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_restore_command_dry_run(self, mock_open, mock_exists, mock_read_toml):
        """Test restore command in dry run mode."""
        mock_exists.return_value = True
        mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}

        # Mock session data
        session_data = {"windows": [{"class": "firefox", "title": "Test"}], "workspaces": []}

        with patch("json.load", return_value=session_data):
            result = runner.invoke(app, ["restore", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout

    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_save_command_verbose(self, mock_makedirs, mock_exists, mock_hyprjson):
        """Test save command with verbose output."""
        mock_exists.return_value = True
        mock_hyprjson.side_effect = [[{"class": "firefox", "title": "Test"}], [{"id": 1, "name": "workspace1"}]]

        result = runner.invoke(app, ["save", "--verbose", "--dry-run"])

        assert result.exit_code == 0

    def test_save_with_custom_output(self):
        """Test save command with custom output file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            with (
                patch("hypr.sessions.commands.save.hyprjson") as mock_hyprjson,
                patch("os.path.exists", return_value=True),
                patch("os.makedirs"),
            ):
                mock_hyprjson.side_effect = [[{"class": "firefox", "title": "Test"}], [{"id": 1, "name": "workspace1"}]]

                result = runner.invoke(app, ["save", "--output", temp_path, "--dry-run"])

                assert result.exit_code == 0
                assert temp_path in result.stdout
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_restore_with_custom_input(self):
        """Test restore command with custom input file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            session_data = {"windows": [{"class": "firefox", "title": "Test"}], "workspaces": []}
            json.dump(session_data, temp_file)
            temp_path = temp_file.name

        try:
            with (
                patch("hypr.sessions.commands.restore.read_toml") as mock_read_toml,
                patch("os.path.exists", return_value=True),
            ):
                mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}

                result = runner.invoke(app, ["restore", "--input", temp_path, "--dry-run"])

                assert result.exit_code == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("hypr.sessions.commands.save.hyprjson")
    def test_save_command_hyprctl_failure(self, mock_hyprjson):
        """Test save command when hyprctl fails."""
        import subprocess

        mock_hyprjson.side_effect = subprocess.CalledProcessError(1, "hyprctl")

        result = runner.invoke(app, ["save", "--dry-run"])

        # Command should handle the error gracefully
        # The exact exit code depends on the error handling implementation
        assert "Error" in result.stdout or result.exit_code != 0

    def test_restore_command_missing_file(self):
        """Test restore command with missing session file."""
        with patch("os.path.exists", return_value=False):
            result = runner.invoke(app, ["restore"])

        # Should handle missing file gracefully
        assert "not found" in result.stdout or result.exit_code != 0

    def test_save_restore_workflow(self):
        """Test complete save and restore workflow."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # First save a session
            with (
                patch("hypr.sessions.commands.save.hyprjson") as mock_hyprjson,
                patch("os.path.exists", return_value=True),
                patch("os.makedirs"),
            ):
                mock_hyprjson.side_effect = [
                    [{"class": "firefox", "title": "Test Browser"}],
                    [{"id": 1, "name": "workspace1"}],
                ]

                save_result = runner.invoke(app, ["save", "--output", temp_path, "--dry-run"])
                assert save_result.exit_code == 0

            # Then restore the session
            with (
                patch("hypr.sessions.commands.restore.read_toml") as mock_read_toml,
                patch("os.path.exists", return_value=True),
                patch("builtins.open"),
            ):
                mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}
                session_data = {
                    "windows": [{"class": "firefox", "title": "Test Browser"}],
                    "workspaces": [{"id": 1, "name": "workspace1"}],
                }

                with patch("json.load", return_value=session_data):
                    restore_result = runner.invoke(app, ["restore", "--input", temp_path, "--dry-run"])
                    assert restore_result.exit_code == 0

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
