# Contributing to Periflow

Thank you for your interest in contributing to Periflow! We welcome contributions from the community. This document provides guidelines and instructions for contributing.

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## How to Contribute

### Reporting Bugs

Before creating bug reports, check the [existing issues](https://github.com/yourusername/Periflow_PC_Client/issues) to avoid duplicates.

When filing a bug report, include:
- **Operating System and version** (e.g., Windows 10 Build 19042)
- **Python version** (if building from source)
- **Steps to reproduce** the issue
- **Expected behavior**
- **Actual behavior**
- **Screenshots or logs** if applicable
- **Any modifications** to the code

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub Issues. When suggesting an enhancement:
- Use a **clear, descriptive title**
- **Describe the current behavior** and **expected behavior**
- **Provide specific examples** demonstrating the enhancement
- **Explain why** this enhancement would be useful

### Pull Requests

Please follow these guidelines when submitting PRs:

1. **Fork** the repository and create a new branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Follow the coding style:**
   - Use Python 3.9+ type hints
   - Follow PEP 8 style guide
   - Use meaningful variable names
   - Add docstrings to functions/classes

3. **Write clear commit messages:**
   ```
   Brief description (50 chars)
   
   More detailed explanation of what and why, wrapped at 72 chars.
   Reference issues if applicable: Closes #123
   ```

4. **Test your changes:**
   ```bash
   python -m pytest tests/
   ```

5. **Update documentation** if your PR changes functionality:
   - Update README.md if needed
   - Add/update inline code comments
   - Update CHANGELOG.md

6. **Submit your PR** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots/demos if applicable

## Development Setup

### Prerequisites

- Python 3.9 or later
- pip or uv
- Git

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Periflow_PC_Client.git
   cd Periflow_PC_Client
   ```

2. **Create virtual environment:**
   ```bash
   # Using Python venv
   python -m venv venv
   venv\Scripts\activate
   
   # Or using uv
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies (optional):**
   ```bash
   pip install pytest pytest-cov black mypy
   ```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=periflow

# Run specific test file
python -m pytest tests/test_server.py
```

### Code Quality

Format and lint your code before submitting:

```bash
# Format with black
black periflow/ tests/

# Type checking with mypy
mypy periflow/
```

## Architecture Overview

```
Periflow PC Client
│
├── periflow/
│   ├── server.py          → TCP server, connection handling
│   ├── protocol.py        → Message encoding/decoding
│   ├── services/          → Video, Audio, Control workers
│   ├── ui.py              → Tkinter GUI
│   ├── config.py          → Settings management
│   ├── models.py          → Data structures
│   └── system.py          → Windows integration
│
├── tests/                 → Unit tests
└── build_assets/          → UI resources
```

### Module Responsibilities

- **server.py**: Accepts connections, dispatches messages to services
- **protocol.py**: Framed message format, handshake logic
- **services/**: Queue-based workers for video, audio, control
- **ui.py**: Tkinter interface, real-time logging, settings
- **config.py**: Persists settings to JSON
- **models.py**: AppSettings, ClientSession, presets
- **system.py**: Windows Firewall, admin checks, IP resolution

## Making Changes

### Adding a New Feature

1. Create a new branch:
   ```bash
   git checkout -b feature/descriptive-name
   ```

2. Implement your feature with tests:
   ```bash
   # Create/update tests first (TDD approach)
   vim tests/test_your_feature.py
   python -m pytest tests/test_your_feature.py
   
   # Implement feature
   ```

3. Update documentation:
   - README.md (if user-facing)
   - Docstrings (in code)
   - CHANGELOG.md

4. Commit with clear messages:
   ```bash
   git add .
   git commit -m "feat: add my new feature"
   ```

### Fixing a Bug

1. Create an issue (if not already reported)
2. Create a branch referencing the issue:
   ```bash
   git checkout -b fix/issue-123-description
   ```
3. Add a test that reproduces the bug
4. Fix the bug
5. Verify test passes
6. Commit with reference:
   ```bash
   git commit -m "fix: resolve issue #123 - description"
   ```

## Commit Message Convention

Follow conventional commits format:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only
- `style`: Changes that don't affect code meaning (formatting, semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process, dependencies, tools

**Examples:**
```
feat(server): add support for TCP audio transport
fix(protocol): handle incomplete handshake gracefully
docs: update README with troubleshooting section
```

## Review Process

1. Maintainers will review your PR
2. Changes may be requested
3. Once approved, your PR will be merged
4. Your contribution will be credited in CHANGELOG.md

## Questions?

Feel free to ask questions by:
- Opening a [GitHub Issue](https://github.com/yourusername/Periflow_PC_Client/issues)
- Starting a [GitHub Discussion](https://github.com/yourusername/Periflow_PC_Client/discussions)

## Recognition

Contributors are recognized in:
- CHANGELOG.md
- README.md acknowledgments section
- GitHub contributors page

## License

By contributing to Periflow, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Periflow! 🎉**
