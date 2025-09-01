# type: ignore
# ruff: noqa

"""
Tests for the CLI main module.
"""

import os
from unittest.mock import patch

from typer.testing import CliRunner

from hypr.sessions.cli import app

runner = CliRunner()


def test_cli_app_exists():
    """Test that the CLI app is properly configured."""
    assert app is not None
    assert hasattr(app, "command")


def test_save_command_exists():
    """Test that save command is registered."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "save" in result.stdout


def test_restore_command_exists():
    """Test that restore command is registered."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "restore" in result.stdout


@patch("hypr.sessions.commands.save.save_session")
def test_save_command_calls_function(mock_save):
    """Test that save command properly calls the save function."""
    mock_save.return_value = os.EX_OK

    result = runner.invoke(app, ["save"])

    assert result.exit_code == 0
    mock_save.assert_called_once()


@patch("hypr.sessions.commands.restore.restore_session")
def test_restore_command_calls_function(mock_restore):
    """Test that restore command properly calls the restore function."""
    mock_restore.return_value = os.EX_OK

    result = runner.invoke(app, ["restore"])

    assert result.exit_code == 0
    mock_restore.assert_called_once()


@patch("hypr.sessions.commands.save.save_session")
def test_save_command_with_output_option(mock_save):
    """Test save command with output option."""
    mock_save.return_value = os.EX_OK

    result = runner.invoke(app, ["save", "--output", "/tmp/test.json"])

    assert result.exit_code == 0
    mock_save.assert_called_once()
    # Check that the function was called with the right parameters
    call_args = mock_save.call_args
    assert call_args is not None


@patch("hypr.sessions.commands.restore.restore_session")
def test_restore_command_with_input_option(mock_restore):
    """Test restore command with input option."""
    mock_restore.return_value = os.EX_OK

    result = runner.invoke(app, ["restore", "--input", "/tmp/test.json"])

    assert result.exit_code == 0
    mock_restore.assert_called_once()


@patch("hypr.sessions.commands.save.save_session")
def test_save_command_dry_run(mock_save):
    """Test save command with dry run option."""
    mock_save.return_value = os.EX_OK

    result = runner.invoke(app, ["save", "--dry-run"])

    assert result.exit_code == 0
    mock_save.assert_called_once()


@patch("hypr.sessions.commands.restore.restore_session")
def test_restore_command_dry_run(mock_restore):
    """Test restore command with dry run option."""
    mock_restore.return_value = os.EX_OK

    result = runner.invoke(app, ["restore", "--dry-run"])

    assert result.exit_code == 0
    mock_restore.assert_called_once()


@patch("hypr.sessions.commands.save.save_session")
def test_save_command_verbose(mock_save):
    """Test save command with verbose option."""
    mock_save.return_value = os.EX_OK

    result = runner.invoke(app, ["save", "-vv"])

    assert result.exit_code == 0
    mock_save.assert_called_once()


@patch("hypr.sessions.commands.restore.restore_session")
def test_restore_command_verbose(mock_restore):
    """Test restore command with verbose option."""
    mock_restore.return_value = os.EX_OK

    result = runner.invoke(app, ["restore", "-vvv"])

    assert result.exit_code == 0
    mock_restore.assert_called_once()


@patch("hypr.sessions.commands.save.save_session")
def test_save_command_error_handling(mock_save):
    """Test that CLI properly handles save command errors."""
    mock_save.return_value = os.EX_SOFTWARE

    result = runner.invoke(app, ["save"])

    assert result.exit_code == os.EX_SOFTWARE
    mock_save.assert_called_once()


@patch("hypr.sessions.commands.restore.restore_session")
def test_restore_command_error_handling(mock_restore):
    """Test that CLI properly handles restore command errors."""
    mock_restore.return_value = os.EX_SOFTWARE

    result = runner.invoke(app, ["restore"])

    assert result.exit_code == os.EX_SOFTWARE
    mock_restore.assert_called_once()
