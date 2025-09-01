# type: ignore
# ruff: noqa

"""
Tests for the restore command.
"""

from unittest.mock import MagicMock, mock_open, patch

import typer

from hypr.sessions.commands.restore import restore_session


class TestRestoreSession:
    """Test class for restore_session function."""

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("hypr.sessions.commands.restore.read_toml")
    @patch("hypr.sessions.commands.restore.launch_applications_with_logging")
    @patch("hypr.sessions.commands.restore.wait_for_windows")
    @patch("hypr.sessions.commands.restore.place_windows")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_success(
        self,
        mock_file,
        mock_exists,
        mock_place_windows,
        mock_wait_for_windows,
        mock_launch_apps,
        mock_read_toml,
        mock_setup_logging,
    ):
        """Test successful session restore."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True
        mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}
        mock_launch_apps.return_value = 1
        mock_wait_for_windows.return_value = [{"class": "firefox", "address": "0x123"}]
        mock_place_windows.return_value = 1

        # Mock session data
        session_data = {"clients": [{"class": "firefox", "title": "Test Browser"}]}

        with patch("json.load", return_value=session_data):
            try:
                restore_session()
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 0

        mock_setup_logging.assert_called_once_with(0, "hypr.sessions.commands.restore")
        mock_launch_apps.assert_called_once()
        mock_place_windows.assert_called_once()

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("hypr.sessions.commands.restore.read_toml")
    @patch("hypr.sessions.commands.restore._show_dry_run_preview")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_dry_run(
        self, mock_file, mock_exists, mock_show_preview, mock_read_toml, mock_setup_logging
    ):
        """Test session restore in dry run mode."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True
        mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}

        session_data = {"clients": [{"class": "firefox", "title": "Test Browser"}]}

        with patch("json.load", return_value=session_data):
            try:
                restore_session(dry_run=True)
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 0

        # Should call dry run preview instead of actual restore
        mock_show_preview.assert_called_once()

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("os.path.exists")
    def test_restore_session_missing_file(self, mock_exists, mock_setup_logging):
        """Test session restore when input file doesn't exist."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = False

        try:
            restore_session()
            raise AssertionError("Should have raised typer.Exit")
        except typer.Exit as e:
            assert e.exit_code == 1

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_empty_session(self, mock_file, mock_exists, mock_setup_logging):
        """Test session restore with empty session data."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True

        # Empty session data
        session_data = {"clients": []}

        with patch("json.load", return_value=session_data):
            try:
                restore_session()
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 1

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("os.path.exists")
    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_restore_session_file_read_error(self, mock_file, mock_exists, mock_setup_logging):
        """Test session restore when file read fails."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True

        try:
            restore_session()
            raise AssertionError("Should have raised typer.Exit")
        except typer.Exit as e:
            assert e.exit_code == 1

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("hypr.sessions.commands.restore.read_toml")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_with_custom_input(self, mock_file, mock_exists, mock_read_toml, mock_setup_logging):
        """Test session restore with custom input file."""
        custom_input = "/tmp/custom_session.json"
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True
        mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}

        session_data = {"clients": [{"class": "firefox", "title": "Test Browser"}]}

        with (
            patch("json.load", return_value=session_data),
            patch("hypr.sessions.commands.restore.launch_applications_with_logging") as mock_launch,
            patch("hypr.sessions.commands.restore.wait_for_windows") as mock_wait,
            patch("hypr.sessions.commands.restore.place_windows") as mock_place,
        ):
            mock_launch.return_value = 1
            mock_wait.return_value = [{"class": "firefox", "address": "0x123"}]
            mock_place.return_value = 1

            try:
                restore_session(input=custom_input)
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 0

        # Should have opened the custom input file
        mock_file.assert_called_with(custom_input)

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("hypr.sessions.commands.restore.read_toml")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_verbose_logging(self, mock_file, mock_exists, mock_read_toml, mock_setup_logging):
        """Test session restore with verbose logging."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True
        mock_read_toml.return_value = {"firefox": {"exec": "firefox"}}

        session_data = {"clients": [{"class": "firefox", "title": "Test"}]}

        with (
            patch("json.load", return_value=session_data),
            patch("hypr.sessions.commands.restore.launch_applications_with_logging") as mock_launch,
            patch("hypr.sessions.commands.restore.wait_for_windows") as mock_wait,
            patch("hypr.sessions.commands.restore.place_windows") as mock_place,
        ):
            mock_launch.return_value = 1
            mock_wait.return_value = [{"class": "firefox", "address": "0x123"}]
            mock_place.return_value = 1

            try:
                restore_session(verbose=3)
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 0

        mock_setup_logging.assert_called_once_with(3, "hypr.sessions.commands.restore")

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_invalid_json(self, mock_file, mock_exists, mock_setup_logging):
        """Test session restore with invalid JSON."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True

        with patch("json.load", side_effect=ValueError("Invalid JSON")):
            try:
                restore_session()
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 1

    @patch("hypr.sessions.commands.restore.setup_logging")
    @patch("hypr.sessions.commands.restore.read_toml")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_restore_session_toml_read_error(self, mock_file, mock_exists, mock_read_toml, mock_setup_logging):
        """Test session restore when TOML read fails."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger
        mock_exists.return_value = True
        mock_read_toml.side_effect = FileNotFoundError("Apps file not found")

        session_data = {"clients": [{"class": "firefox", "title": "Test Browser"}]}

        with patch("json.load", return_value=session_data):
            try:
                restore_session()
                raise AssertionError("Should have raised typer.Exit")
            except typer.Exit as e:
                assert e.exit_code == 1
