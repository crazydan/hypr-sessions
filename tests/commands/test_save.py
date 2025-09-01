# type: ignore
# ruff: noqa

"""
Tests for the save command.
"""

from unittest.mock import MagicMock, patch

import typer

from hypr.sessions.commands.save import save_session


class TestSaveSession:
    """Test class for save_session function."""

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("hypr.sessions.commands.save.read_toml")
    @patch("hypr.sessions.commands.save._save_to_file")
    def test_save_session_success(self, mock_save_to_file, mock_read_toml, mock_hyprjson, mock_setup_logging):
        """Test successful session save."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.return_value = {"pwa": {}}
        mock_hyprjson.side_effect = [
            [{"class": "firefox", "title": "Test Browser"}],  # clients
            [{"id": 1, "name": "workspace1"}],  # workspaces
        ]

        # Mock the _process_clients function
        with patch("hypr.sessions.commands.save._process_clients") as mock_process:
            mock_process.return_value = [{"class": "firefox", "title": "Test Browser"}]

            try:
                save_session()
                assert False, "Should have raised typer.Exit"
            except typer.Exit as e:
                assert e.exit_code == 0

        mock_setup_logging.assert_called_once_with(0, "hypr.sessions.commands.save")
        mock_save_to_file.assert_called_once()

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("hypr.sessions.commands.save.read_toml")
    @patch("rich.console.Console.print")
    def test_save_session_dry_run(self, mock_print, mock_read_toml, mock_hyprjson, mock_setup_logging):
        """Test session save in dry run mode."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.return_value = {"pwa": {}}
        mock_hyprjson.side_effect = [[{"class": "firefox", "title": "Test Browser"}], [{"id": 1, "name": "workspace1"}]]

        with patch("hypr.sessions.commands.save._process_clients") as mock_process:
            mock_process.return_value = [{"class": "firefox", "title": "Test Browser"}]

            try:
                save_session(dry_run=True)
                assert False, "Should have raised typer.Exit"
            except typer.Exit as e:
                assert e.exit_code == 0

        # Should print dry run information
        mock_print.assert_called()
        # Check for dry run text in any of the print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("DRY RUN" in call for call in print_calls)

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    def test_save_session_hyprctl_failure(self, mock_hyprjson, mock_setup_logging):
        """Test session save when hyprjson fails."""
        import subprocess

        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_hyprjson.side_effect = subprocess.CalledProcessError(1, "hyprctl")

        try:
            save_session()
            assert False, "Should have raised typer.Exit"
        except typer.Exit as e:
            assert e.exit_code == 1

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("hypr.sessions.commands.save.read_toml")
    def test_save_session_with_output_file(self, mock_read_toml, mock_hyprjson, mock_setup_logging):
        """Test session save with custom output file."""
        custom_output = "/tmp/custom_session.json"
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.return_value = {"pwa": {}}
        mock_hyprjson.side_effect = [[{"class": "firefox", "title": "Test"}], [{"id": 1, "name": "workspace1"}]]

        with (
            patch("hypr.sessions.commands.save._process_clients") as mock_process,
            patch("hypr.sessions.commands.save._save_to_file") as mock_save_to_file,
        ):
            mock_process.return_value = [{"class": "firefox", "title": "Test"}]

            try:
                save_session(output=custom_output)
                assert False, "Should have raised typer.Exit"
            except typer.Exit as e:
                assert e.exit_code == 0

            # Check that save_to_file was called with the custom output
            mock_save_to_file.assert_called_once()
            call_args = mock_save_to_file.call_args[0]
            assert call_args[1] == custom_output  # Second argument should be the output path

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("hypr.sessions.commands.save.read_toml")
    def test_save_session_verbose_logging(self, mock_read_toml, mock_hyprjson, mock_setup_logging):
        """Test session save with verbose logging."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.return_value = {"pwa": {}}
        mock_hyprjson.side_effect = [[{"class": "firefox", "title": "Test"}], [{"id": 1, "name": "workspace1"}]]

        with (
            patch("hypr.sessions.commands.save._process_clients") as mock_process,
            patch("hypr.sessions.commands.save._save_to_file"),
        ):
            mock_process.return_value = [{"class": "firefox", "title": "Test"}]

            try:
                save_session(verbose=2)
                assert False, "Should have raised typer.Exit"
            except typer.Exit as e:
                assert e.exit_code == 0

        mock_setup_logging.assert_called_once_with(2, "hypr.sessions.commands.save")

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("hypr.sessions.commands.save.read_toml")
    def test_save_session_empty_clients(self, mock_read_toml, mock_hyprjson, mock_setup_logging):
        """Test session save with no clients."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.return_value = {"pwa": {}}
        mock_hyprjson.side_effect = [
            [],  # No clients
            [{"id": 1, "name": "workspace1"}],
        ]

        with (
            patch("hypr.sessions.commands.save._process_clients") as mock_process,
            patch("hypr.sessions.commands.save._save_to_file"),
        ):
            mock_process.return_value = []

            try:
                save_session()
                assert False, "Should have raised typer.Exit"
            except typer.Exit as e:
                assert e.exit_code == 0

        # Should still save successfully with empty clients
        mock_process.assert_called_once()

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.read_toml")
    def test_save_session_toml_read_error(self, mock_read_toml, mock_setup_logging):
        """Test session save when TOML read fails."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.side_effect = Exception("TOML read error")

        try:
            save_session()
            assert False, "Should have raised typer.Exit"
        except typer.Exit as e:
            assert e.exit_code == 1

    @patch("hypr.sessions.commands.save.setup_logging")
    @patch("hypr.sessions.commands.save.hyprjson")
    @patch("hypr.sessions.commands.save.read_toml")
    @patch("hypr.sessions.commands.save._save_to_file")
    def test_save_session_file_write_error(self, mock_save_to_file, mock_read_toml, mock_hyprjson, mock_setup_logging):
        """Test session save when file write fails."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_read_toml.return_value = {"pwa": {}}
        mock_hyprjson.side_effect = [[{"class": "firefox", "title": "Test"}], [{"id": 1, "name": "workspace1"}]]
        mock_save_to_file.side_effect = OSError("Permission denied")

        with patch("hypr.sessions.commands.save._process_clients") as mock_process:
            mock_process.return_value = [{"class": "firefox", "title": "Test"}]

            try:
                save_session()
                assert False, "Should have raised typer.Exit"
            except typer.Exit as e:
                assert e.exit_code == 1
