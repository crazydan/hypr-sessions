# Test Suite Documentation

This directory contains comprehensive unit tests for the hypr-sessions CLI application.

## Test Structure

```
tests/
├── __init__.py               # Test package initialization
├── conftest.py              # Shared test fixtures and configuration
├── test_cli.py             # Tests for CLI command interface
├── test_commons.py         # Tests for common utility functions
├── test_integration.py     # Integration tests for CLI workflows
└── commands/
    ├── __init__.py         # Commands test package
    ├── test_save.py        # Tests for save command (original)
    ├── test_save_new.py    # Updated tests for save command
    ├── test_restore.py     # Tests for restore command (original)
    └── test_restore_new.py # Updated tests for restore command
```

## Test Coverage

### Core Modules

#### `test_commons.py`
Tests for shared utility functions in `src/hypr/sessions/commons.py`:
- Constants validation (STATE, APPS_TOML paths)
- Logging setup with different verbosity levels
- Hyprland command execution (hypr, hyprjson)
- TOML file reading and error handling
- PWA key resolution
- Window matching and placement
- Application launching with logging

#### `test_cli.py`
Tests for the main CLI interface in `src/hypr/sessions/cli.py`:
- Command registration and help text
- Command-line option parsing
- Error handling and exit codes
- Integration with save/restore commands

### Command Modules

#### `test_save.py` / `test_save_new.py`
Tests for the save command functionality:
- Session data collection from Hyprland
- JSON file output with proper formatting
- Dry-run mode preview
- Custom output file handling
- Verbose logging levels
- Error handling (hyprctl failures, file write errors)
- Edge cases (empty sessions, TOML read errors)

#### `test_restore.py` / `test_restore_new.py`
Tests for the restore command functionality:
- Session data reading and validation
- Application launching and window placement
- Dry-run mode preview
- Custom input file handling
- Verbose logging levels
- Error handling (missing files, invalid JSON, TOML errors)
- Edge cases (empty sessions, unmapped applications)

### Integration Tests

#### `test_integration.py`
End-to-end CLI workflow tests:
- Complete save/restore workflows
- Command-line interface integration
- File I/O operations
- Error scenarios and recovery
- Multi-command workflows

## Test Configuration

### pytest Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Test Dependencies
- `pytest>=8.0.0` - Testing framework
- `pytest-cov>=5.0.0` - Coverage reporting
- `pytest-mock>=3.14.0` - Enhanced mocking capabilities

### Shared Fixtures (`conftest.py`)
- `temp_session_file` - Temporary JSON session files
- `temp_apps_file` - Temporary TOML app configuration files
- `mock_console` - Rich console mocking
- `mock_subprocess` - Subprocess execution mocking
- `mock_hyprctl` - Hyprland command mocking
- `sample_session_data` - Test session data structures
- `sample_apps_data` - Test app configuration data

## Running Tests

### Run All Tests
```bash
cd /home/daniel/Projects/hypr-sessions
python -m pytest tests/ -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test Files
```bash
python -m pytest tests/test_commons.py -v
python -m pytest tests/commands/test_save_new.py -v
```

### Run Integration Tests Only
```bash
python -m pytest tests/test_integration.py -v
```

## Test Patterns and Best Practices

### Mocking Strategy
- **External Commands**: Mock `subprocess.run`, `hyprjson`, and `hypr` calls
- **File Operations**: Use `mock_open` for file I/O operations
- **System Dependencies**: Mock `os.path.exists`, `os.makedirs`
- **Logging**: Mock logger instances to verify log calls

### Error Testing
- Test both success and failure scenarios
- Verify proper exit codes with `typer.Exit` exceptions
- Test edge cases like empty files, missing dependencies
- Validate error messages and user feedback

### CLI Testing
- Use `typer.testing.CliRunner` for command-line interface testing
- Test command options, arguments, and help text
- Verify output formatting and error handling
- Test complete workflows from CLI perspective

## Known Issues and Limitations

1. **Typer Exit Handling**: Functions use `typer.Exit()` rather than return codes
2. **Mock Complexity**: Some tests require extensive mocking due to Hyprland dependencies
3. **Platform Dependencies**: Tests assume Linux/Hyprland environment availability
4. **File Path Assumptions**: Some tests use hardcoded paths that may need adjustment

## Future Improvements

1. **Parameterized Tests**: Add more parameterized test cases for different scenarios
2. **Property-Based Testing**: Consider using hypothesis for property-based testing
3. **Performance Tests**: Add tests for performance with large session files
4. **Real Integration**: Add optional tests that work with actual Hyprland instances
5. **Test Data**: Expand test data sets to cover more edge cases

## Contributing to Tests

When adding new functionality:
1. Add corresponding unit tests in the appropriate test file
2. Update integration tests if CLI interface changes
3. Add new fixtures to `conftest.py` if needed
4. Update this documentation with any new test patterns
5. Ensure all tests pass and maintain high coverage
