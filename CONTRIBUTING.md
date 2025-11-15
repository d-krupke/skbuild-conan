# Contributing to skbuild-conan

Thank you for your interest in contributing to skbuild-conan! 🎉

This guide will help you get started with contributing to the project. Whether you're fixing a bug, adding a feature, or improving documentation, we appreciate your help!

## Table of Contents

- [Quick Start](#quick-start)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing Your Changes](#testing-your-changes)
- [Submitting Your Contribution](#submitting-your-contribution)
- [Code Review Process](#code-review-process)
- [Community Guidelines](#community-guidelines)

---

## Quick Start

**First time contributing?** Here's the fastest way to get started:

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/skbuild-conan.git
cd skbuild-conan

# 3. Set up development environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
pip install pytest flake8 black pre-commit

# 4. Install pre-commit hooks
pre-commit install

# 5. Create a feature branch
git checkout -b fix/your-bugfix-name

# 6. Make your changes and test
# ... edit files ...
pytest tests/unit/ -v

# 7. Commit and push
git add .
git commit -m "fix: Your descriptive commit message"
git push origin fix/your-bugfix-name

# 8. Create a Pull Request on GitHub
```

**Need more details?** See the sections below or read [DEVELOPMENT.md](DEVELOPMENT.md) for comprehensive documentation.

---

## Ways to Contribute

### 🐛 Report Bugs

Found a bug? Please [open an issue](https://github.com/d-krupke/skbuild-conan/issues/new) with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs actual behavior
- Your environment (OS, Python version, Conan version)
- Relevant logs (use verbose mode: `SKBUILD_CONAN_LOG_LEVEL=debug pip install ...`)

### 💡 Suggest Features

Have an idea? [Open an issue](https://github.com/d-krupke/skbuild-conan/issues/new) labeled "enhancement" with:
- Clear description of the feature
- Use case and motivation
- Example of how it would work
- Whether you'd like to implement it yourself

### 📝 Improve Documentation

Documentation improvements are always welcome:
- Fix typos or clarify existing docs
- Add examples
- Improve error messages
- Write tutorials or guides

### 🧪 Add Tests

Help improve code coverage:
- Add unit tests for untested features
- Add integration tests for real-world scenarios
- Add platform-specific tests (Windows, macOS)

### 🔧 Fix Bugs or Add Features

Pick an issue labeled:
- `good first issue` - Great for newcomers
- `help wanted` - We'd appreciate help with these
- `bug` - Something that needs fixing

---

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- A C++ compiler (gcc/clang/MSVC)
- CMake 3.23+

### Setting Up Your Environment

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/skbuild-conan.git
   cd skbuild-conan
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode**

   ```bash
   pip install --upgrade pip
   pip install -e .
   ```

4. **Install development dependencies**

   ```bash
   pip install pytest flake8 black pre-commit
   ```

5. **Set up pre-commit hooks**

   This ensures code quality checks run before each commit:

   ```bash
   pre-commit install
   ```

6. **Verify installation**

   ```bash
   # Test imports
   python -c "from skbuild_conan import setup, LogLevel; print('✓ Success')"

   # Run tests
   pytest tests/unit/ -v
   ```

---

## Making Changes

### 1. Create a Branch

Use descriptive branch names:

```bash
git checkout -b feature/add-dry-run-mode
git checkout -b fix/retry-logic-bug
git checkout -b docs/improve-readme
```

### 2. Make Your Changes

**Write good code:**
- Follow PEP 8 style guide (black will handle most of this)
- Add type hints where appropriate
- Write clear, self-documenting code
- Add docstrings for public functions/classes

**Example of good code:**

```python
def validate_requirement(requirement: str) -> bool:
    """
    Validate a Conan requirement string format.

    Args:
        requirement: The requirement string to validate (e.g., "fmt/10.0.0")

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_requirement("fmt/10.0.0")
        True
        >>> validate_requirement("invalid")
        False
    """
    return '/' in requirement
```

### 3. Follow Code Style

The pre-commit hooks will enforce this automatically, but:

- **Format with black:** `black src/`
- **Lint with flake8:** `flake8 src/`
- **Max line length:** 88 characters (black default)
- **Imports:** Group stdlib, third-party, local

### 4. Write Tests

**For new features:**
- Add unit tests in `tests/unit/`
- Add integration tests if applicable
- Ensure tests pass: `pytest tests/ -v`

**Example test:**

```python
def test_new_feature():
    """Test that the new feature works as expected."""
    # Arrange
    input_data = "test"

    # Act
    result = your_function(input_data)

    # Assert
    assert result == expected_output
```

### 5. Update Documentation

If your change affects users:
- Update README.md with new features/options
- Update docstrings
- Add examples if helpful
- Update CHANGELOG section in README.md

---

## Testing Your Changes

### Run Tests Locally

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_logging.py -v

# Run with coverage
pytest tests/unit/ --cov=skbuild_conan --cov-report=html

# Run integration tests (examples)
cd examples/simple_skbuild_conan_example
pip install -e . --verbose
pytest tests/
```

### Test Different Log Levels

```bash
# Test normal output
pip install -e examples/simple_skbuild_conan_example

# Test verbose output
SKBUILD_CONAN_LOG_LEVEL=verbose pip install -e examples/simple_skbuild_conan_example

# Test debug output
SKBUILD_CONAN_LOG_LEVEL=debug pip install -e examples/simple_skbuild_conan_example

# Test quiet output
SKBUILD_CONAN_LOG_LEVEL=quiet pip install -e examples/simple_skbuild_conan_example
```

### Test on Multiple Python Versions (Optional)

If you have multiple Python versions installed:

```bash
# Python 3.9
python3.9 -m venv venv39
source venv39/bin/activate
pip install -e .
pytest tests/unit/

# Python 3.13
python3.13 -m venv venv313
source venv313/bin/activate
pip install -e .
pytest tests/unit/
```

---

## Submitting Your Contribution

### 1. Commit Your Changes

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
# Feature
git commit -m "feat: Add dry-run mode for previewing changes"

# Bug fix
git commit -m "fix: Correct retry logic for network errors"

# Documentation
git commit -m "docs: Improve logging documentation in README"

# Tests
git commit -m "test: Add tests for input validation"

# Refactoring
git commit -m "refactor: Simplify error handling logic"

# Chore (maintenance)
git commit -m "chore: Update pre-commit hook versions"
```

**Good commit message example:**

```
feat: Add automatic verbosity detection from pip --verbose flag

Detect --verbose/-v and --quiet/-q flags from pip/setup.py and
automatically set the appropriate log level without requiring
users to set SKBUILD_CONAN_LOG_LEVEL environment variable.

This improves usability by respecting standard pip conventions.

Closes #42
```

### 2. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 3. Create a Pull Request

1. Go to https://github.com/d-krupke/skbuild-conan
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:

   ```markdown
   ## Description
   Brief description of what this PR does and why.

   ## Changes
   - Added feature X
   - Fixed bug Y
   - Updated documentation Z

   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Tested with verbose logging
   - [ ] Tested on platform: [Ubuntu/Windows/macOS]

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Added tests for new functionality
   - [ ] Updated documentation
   - [ ] All tests pass locally
   ```

5. Submit the PR!

---

## Code Review Process

### What to Expect

1. **Automated Checks**
   - CI tests will run automatically
   - Pre-commit checks via GitHub Actions
   - Code linting and formatting checks

2. **Human Review**
   - A maintainer will review your code
   - They may request changes or ask questions
   - This is a collaborative process!

3. **Feedback**
   - Address any requested changes
   - Push new commits to the same branch
   - Respond to comments

### Making Changes After Review

```bash
# Make requested changes
# ... edit files ...

# Commit changes
git add .
git commit -m "fix: Address review feedback - improve error messages"

# Push updates
git push origin feature/your-feature-name
```

The PR will automatically update!

### Getting Your PR Merged

Once approved:
- A maintainer will merge your PR
- Your contribution will be in the next release!
- You'll be credited in the release notes

---

## Community Guidelines

### Be Respectful

- Be kind and courteous
- Respect different viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the project

### Be Clear

- Write clear code and commit messages
- Explain your reasoning in PRs
- Ask questions if something is unclear
- Provide context in issues

### Be Patient

- Reviews may take a few days
- Maintainers are volunteers with limited time
- Complex PRs take longer to review
- Feel free to politely ping after a week

---

## Getting Help

### I'm Stuck!

**First, try these resources:**
1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for detailed technical info
2. Check [existing issues](https://github.com/d-krupke/skbuild-conan/issues)
3. Read the [README.md](README.md) for usage documentation
4. Check the [CI/CD review](CI_CD_REVIEW.md) for testing info

**Still stuck?**
- Ask in the [GitHub Discussions](https://github.com/d-krupke/skbuild-conan/discussions)
- Comment on the related issue
- Mention `@d-krupke` in your PR if you need help

### Common Issues

**Pre-commit hooks failing?**
```bash
# Run manually to see what's wrong
pre-commit run --all-files

# Auto-fix most issues
black src/
```

**Tests failing locally?**
```bash
# Clean build artifacts
rm -rf _skbuild/ build/ dist/ *.egg-info

# Reinstall
pip install -e . --force-reinstall

# Run tests with verbose output
pytest tests/unit/ -vv
```

**Import errors?**
```bash
# Make sure you're in the virtual environment
which python  # Should show path to venv

# Reinstall in development mode
pip install -e .
```

---

## Recognition

### Contributors

All contributors are recognized in:
- GitHub contributors page
- Release notes
- Project documentation (when significant)

### Types of Contributions We Value

- Code contributions (features, bug fixes)
- Documentation improvements
- Bug reports and feature requests
- Helping other contributors
- Testing and QA
- Spreading the word about the project

---

## Advanced Topics

### For Maintainers

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Release process
- CI/CD configuration
- Testing strategy
- Project architecture

### For Major Contributors

If you're planning a major contribution:
1. Open an issue first to discuss the approach
2. Get feedback before investing lots of time
3. Consider breaking it into smaller PRs
4. Coordinate with maintainers

---

## Quick Reference

### Useful Commands

```bash
# Development
pip install -e .                    # Install in dev mode
pre-commit run --all-files          # Run all checks
black src/                          # Format code
flake8 src/                         # Lint code

# Testing
pytest tests/unit/ -v               # Run unit tests
pytest tests/unit/ --cov            # With coverage
pytest -k test_logging              # Run specific test
pytest -m "not slow"                # Skip slow tests

# Git
git checkout -b feature/name        # Create branch
git commit -m "type: message"       # Commit
git push origin branch-name         # Push changes
```

### File Structure

```
skbuild-conan/
├── src/skbuild_conan/           # Main package code
│   ├── __init__.py
│   ├── setup_wrapper.py         # Main setup logic
│   ├── conan_helper.py          # Conan integration
│   ├── logging_utils.py         # Logging system
│   └── exceptions.py            # Custom exceptions
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   └── conftest.py              # Test fixtures
├── examples/                    # Integration tests
├── CONTRIBUTING.md              # This file
├── DEVELOPMENT.md               # Detailed dev docs
└── README.md                    # User documentation
```

### Resources

- **Repository:** https://github.com/d-krupke/skbuild-conan
- **Issues:** https://github.com/d-krupke/skbuild-conan/issues
- **PyPI:** https://pypi.org/project/skbuild-conan
- **Documentation:** See README.md and DEVELOPMENT.md

---

## Thank You! 🙏

Your contributions make this project better for everyone. Whether you're fixing a typo or adding a major feature, we appreciate your effort and time.

**Happy coding!** 🚀

---

## Questions?

- **General questions:** Open a [GitHub Discussion](https://github.com/d-krupke/skbuild-conan/discussions)
- **Bug reports:** [Open an issue](https://github.com/d-krupke/skbuild-conan/issues/new)
- **Need help contributing:** Comment on the issue you're working on

We're here to help! Don't hesitate to ask questions.
