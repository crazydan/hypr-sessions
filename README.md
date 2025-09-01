# hypr-sessions

> 🚧 **Work in Progress** - This project is under active development

A session manager for Hyprland that allows you to save and restore your window layouts, perfect for maintaining productivity workflows on Linux (specifically Omarchy).

## ✨ Features

- 🪟 **Save window layouts** - Capture current Hyprland workspace configuration
- 🔄 **Restore sessions** - Recreate your exact window arrangement
- 🌐 **PWA support** - Special handling for Progressive Web Apps (Chrome/Chromium)
- 📱 **Terminal detection** - Preserves current working directories for terminal apps
- ⚙️ **Configurable** - Customizable app mappings via TOML configuration
- 🎯 **Workspace-aware** - Maintains window positioning across multiple workspaces

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/crazydan/hypr-sessions.git
cd hypr-sessions

# Install with uv (recommended)
uv sync --all-groups

# Or install with pip
pip install -e .
```

### Basic Usage

```bash
# Save current session
hypr-sessions save

# Restore last saved session
hypr-sessions restore

# Save to custom file
hypr-sessions save --output ~/my-session.json

# Use custom app configuration
hypr-sessions save --apps-toml ~/.config/hypr/my-apps.toml

# Verbose output for debugging
hypr-sessions save -vv
```

## 📁 Configuration

### App Mappings (`~/.config/hypr/session-apps.toml`)

Configure how applications should be launched when restoring sessions:

```toml
[apps]
"firefox" = "firefox"
"Alacritty" = "alacritty"
"code" = "code"
"spotify" = "spotify"

[pwa]
"WhatsApp" = "google-chrome --app=https://web.whatsapp.com"
"Discord" = "google-chrome --app=https://discord.com/app"
"Notion" = "google-chrome --app=https://notion.so"
```

### Session Format

Sessions are saved as JSON files containing:
- Window class, title, and application ID
- Workspace assignments and floating status
- Window position and size
- Current working directory (for terminals)
- PWA detection and launch commands

## 🛠️ Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Hyprland window manager
- Linux environment (tested on Omarchy)

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/crazydan/hypr-sessions.git
cd hypr-sessions

# Install all dependencies including dev tools
uv sync --all-groups

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Project Structure

```
hypr-sessions/
├── src/hypr/sessions/          # Main package
│   ├── cli.py                  # CLI interface
│   ├── commons.py              # Shared utilities
│   └── commands/               # Save/restore commands
├── tests/                      # Test suite
├── .vscode/                    # VS Code configuration
├── pyproject.toml              # Project configuration
└── session-apps.toml           # Example app mappings
```

### Code Quality

This project uses modern Python tooling:

- **Formatting**: [Ruff](https://docs.astral.sh/ruff/) (replaces Black + isort)
- **Linting**: [Ruff](https://docs.astral.sh/ruff/) + [MyPy](http://mypy-lang.org/)
- **Testing**: [pytest](https://pytest.org/) with coverage
- **Pre-commit**: Automated code quality checks
- **Security**: [Bandit](https://bandit.readthedocs.io/) + [Safety](https://pyup.io/safety/)

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_commons.py

# Run with coverage
uv run pytest --cov=src

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## 🐛 Debugging

VS Code debugging is configured for easy development:

1. Set breakpoints in your code
2. Use F5 to start debugging
3. Choose "Save Command" or "Restore Command" configuration

Or debug manually:
```bash
# Debug save command
uv run python -m debugpy --listen 5678 --wait-for-client -m hypr.sessions save -vv

# Debug restore command
uv run python -m debugpy --listen 5678 --wait-for-client -m hypr.sessions restore -vv
```

## 📋 Roadmap

- [x] Basic save/restore functionality
- [x] PWA detection and handling
- [x] Terminal working directory preservation
- [x] Configurable app mappings
- [x] Verbose logging and diagnostics
- [ ] Automatic session detection
- [ ] Session templates
- [ ] Integration with system startup
- [ ] Multi-monitor layout support
- [ ] Session versioning and history

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Run pre-commit checks (`uv run pre-commit run --all-files`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow [Conventional Commits](https://conventionalcommits.org/)
- Maintain test coverage above 90%
- Use type hints for all new code
- Add docstrings for public functions
- Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hyprland](https://hyprland.org/) - The amazing tiling window manager
- [Omarchy](https://omarchy.org/) - The Linux distribution this was tested on
- The Python community for excellent tooling

## 🆘 Support

- 📖 Check the [documentation](docs/) (coming soon)
- 🐛 Report bugs via [GitHub Issues](https://github.com/crazydan/hypr-sessions/issues)
- 💬 Join discussions in [GitHub Discussions](https://github.com/crazydan/hypr-sessions/discussions)
- 📧 Contact: [your-email@example.com](mailto:your-email@example.com)

---

**Note**: This project is specifically designed for Hyprland on Linux. While it may work on other setups, Omarchy Linux is the primary testing environment.
