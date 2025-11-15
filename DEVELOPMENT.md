# Development Guide

This guide covers the development workflow, testing strategy, and contribution guidelines for skbuild-conan.

## Table of Contents

- [Development Setup](#development-setup)
- [CI/CD Testing Strategy](#cicd-testing-strategy)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Code Quality](#code-quality)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

---

## Development Setup

### Prerequisites

- Python 3.9+ (for development; package supports 3.9+)
- Git
- A C++ compiler (gcc/clang on Linux/Mac, MSVC on Windows)
- CMake 3.23+

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/d-krupke/skbuild-conan.git
cd skbuild-conan

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install --upgrade pip
pip install -e .  # Install package in editable mode
pip install pytest flake8 black pre-commit

# Install pre-commit hooks
pre-commit install

# Verify installation
python -c "from skbuild_conan import setup, LogLevel; print('✓ Import successful')"
```

### Development Dependencies

The project uses several tools for code quality:

- **pytest**: Testing framework
- **flake8**: Linting (with flake8-bugbear for additional checks)
- **black**: Code formatting
- **pre-commit**: Git hook framework
- **pyupgrade**: Syntax modernization

---

## CI/CD Testing Strategy

### Current Strategy Overview

The project uses GitHub Actions for CI/CD with a **multi-tiered testing approach**:

#### Tier 1: Fast Tests (On every push to main)
**File:** `.github/workflows/pytest.yml`

- **Purpose:** Quick validation of core functionality
- **Runtime:** ~5-10 minutes
- **Matrix:** Python 3.9 and 3.13 on Ubuntu
- **Tests:** Simple example (fmt library)
- **Trigger:** Push to `main` branch

**Strengths:**
- Fast feedback loop
- Tests basic functionality
- Validates multiple Python versions

**Weaknesses:**
- Only tests Linux
- Only one simple example
- No unit tests for core library

#### Tier 2: Platform-Specific Tests (Manual)
**Files:** `pytest_windows.yml`, `pytest_cgal_windows.yml`

- **Purpose:** Validate Windows compatibility
- **Runtime:** ~10-15 minutes
- **Tests:** Windows-specific issues (MSVC, paths, etc.)
- **Trigger:** Manual (`workflow_dispatch`)

#### Tier 3: Expensive Tests (Manual)
**Files:** `pytest_cgal.yml`, `pytest_cgal_custom_recipe.yml`

- **Purpose:** Test complex scenarios with large dependencies
- **Runtime:** ~30-60 minutes (CGAL compilation)
- **Tests:** CGAL example with custom recipes
- **Trigger:** Manual (`workflow_dispatch`)

### Testing Strategy Assessment

#### ✅ What's Working Well

1. **Good separation** between fast and expensive tests
2. **Multi-version testing** (Python 3.9 and 3.13)
3. **Real-world validation** via example projects
4. **Pre-commit hooks** ensure code quality before commit

#### ⚠️ Critical Gaps

1. **No unit tests** for core library (`src/skbuild_conan/`)
   - No tests for `logging_utils.py`
   - No tests for `exceptions.py`
   - No tests for `conan_helper.py` logic
   - No tests for `setup_wrapper.py` validation

2. **Limited platform coverage** in automatic tests
   - No macOS testing
   - Windows tests are manual only

3. **No integration tests** for new v1.4.0 features
   - Logging levels not tested
   - Error handling not tested
   - Retry logic not tested
   - Input validation not tested

4. **No performance testing**
   - Cache behavior not validated
   - Network retry timing not verified

5. **No regression testing**
   - Breaking changes can slip through

### Recommended Improvements

See [Testing Strategy](#testing-strategy) section below for detailed recommendations.

---

## Development Workflow

### Branch Strategy

```
main (protected)
  ├─ feature/feature-name     # New features
  ├─ fix/bug-description      # Bug fixes
  └─ docs/documentation-update # Documentation
```

### Workflow Steps

1. **Create a feature branch**
   ```bash
   git checkout -b feature/structured-logging
   ```

2. **Make changes**
   - Write code following the [Code Quality](#code-quality) guidelines
   - Add tests for new functionality
   - Update documentation

3. **Run pre-commit checks**
   ```bash
   # Automatically runs on git commit, or manually:
   pre-commit run --all-files
   ```

4. **Test locally**
   ```bash
   # Quick test with simple example
   cd examples/simple_skbuild_conan_example
   pip install -e .
   pytest tests/

   # Test with different log levels
   SKBUILD_CONAN_LOG_LEVEL=verbose pip install -e .
   SKBUILD_CONAN_LOG_LEVEL=debug pip install -e .
   ```

5. **Run syntax checks**
   ```bash
   python -m py_compile src/skbuild_conan/*.py
   flake8 src/skbuild_conan/
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: Add structured logging system"

   # Commit message format:
   # - feat: New feature
   # - fix: Bug fix
   # - docs: Documentation
   # - refactor: Code refactoring
   # - test: Test additions/changes
   # - chore: Maintenance
   ```

7. **Push and create PR**
   ```bash
   git push -u origin feature/structured-logging
   # Create pull request on GitHub
   ```

8. **Address review comments**
   - Make changes based on feedback
   - Push updates to the same branch

9. **Merge**
   - Once approved, merge to main
   - Delete feature branch

---

## Testing Strategy

### Current Testing: Integration Tests Only

**Location:** `examples/*/tests/`

Current tests only validate that:
- Examples can be built
- Basic functionality works in built packages

**Gap:** No tests for the skbuild-conan library itself!

### Recommended: Add Unit Tests

Create a `tests/` directory at project root:

```
skbuild-conan/
├── src/skbuild_conan/
├── tests/                    # ← NEW
│   ├── unit/
│   │   ├── test_logging.py
│   │   ├── test_exceptions.py
│   │   ├── test_validation.py
│   │   └── test_conan_helper.py
│   └── integration/
│       └── test_examples.py
└── examples/
```

#### Unit Test Examples

**tests/unit/test_logging.py:**
```python
"""Tests for logging_utils module."""
import os
import pytest
from skbuild_conan.logging_utils import Logger, LogLevel


def test_log_level_from_env(monkeypatch):
    """Test that log level is read from environment."""
    monkeypatch.setenv('SKBUILD_CONAN_LOG_LEVEL', 'debug')
    logger = Logger()
    assert logger.log_level == LogLevel.DEBUG


def test_log_level_priority():
    """Test that explicit log level takes precedence."""
    os.environ['SKBUILD_CONAN_LOG_LEVEL'] = 'quiet'
    logger = Logger(LogLevel.VERBOSE)
    assert logger.log_level == LogLevel.VERBOSE


def test_debug_with_exc_info(capsys):
    """Test that debug logs exceptions when exc_info=True."""
    logger = Logger(LogLevel.DEBUG)
    try:
        raise ValueError("test error")
    except ValueError:
        logger.debug("Error occurred", exc_info=True)

    captured = capsys.readouterr()
    assert "test error" in captured.out
    assert "Traceback" in captured.out
```

**tests/unit/test_validation.py:**
```python
"""Tests for input validation."""
import pytest
from skbuild_conan.setup_wrapper import validate_setup_args
from skbuild_conan.exceptions import ValidationError


def test_validate_missing_slash_in_requirement():
    """Test that requirements without '/' are rejected."""
    with pytest.raises(ValidationError, match="Invalid requirement format"):
        validate_setup_args(
            conanfile=".",
            conan_recipes=None,
            conan_requirements=["invalid_requirement"]
        )


def test_validate_nonexistent_recipe_path(tmp_path):
    """Test that non-existent recipe paths are rejected."""
    fake_path = str(tmp_path / "nonexistent")
    with pytest.raises(ValidationError, match="Recipe path does not exist"):
        validate_setup_args(
            conanfile=".",
            conan_recipes=[fake_path],
            conan_requirements=None
        )


def test_validate_mutually_exclusive_options():
    """Test that conanfile and requirements are mutually exclusive."""
    with pytest.raises(ValidationError, match="Cannot specify both"):
        validate_setup_args(
            conanfile="custom_path",
            conan_recipes=None,
            conan_requirements=["fmt/10.0.0"]
        )
```

**tests/unit/test_exceptions.py:**
```python
"""Tests for custom exceptions."""
from skbuild_conan.exceptions import (
    ConanVersionError,
    ValidationError,
    SkbuildConanError
)


def test_conan_version_error_includes_remediation():
    """Test that ConanVersionError includes installation instructions."""
    error = ConanVersionError("1.59.0", "2.x")
    detailed = error.detailed_message()

    assert "1.59.0" in detailed
    assert "Install Conan 2.x" in detailed
    assert "pip install 'conan>=2.0.0'" in detailed


def test_validation_error_inheritance():
    """Test that custom exceptions inherit from base."""
    error = ValidationError("test")
    assert isinstance(error, SkbuildConanError)
    assert isinstance(error, Exception)
```

### Integration Tests

Keep existing example-based tests but add:

**tests/integration/test_verbosity.py:**
```python
"""Integration tests for verbosity detection."""
import subprocess
import sys


def test_verbose_flag_detection():
    """Test that --verbose flag increases verbosity."""
    # This would test that pip install --verbose actually works
    # Requires mocking or a test package
    pass


def test_quiet_flag_detection():
    """Test that --quiet flag suppresses output."""
    pass
```

### Mock-Based Tests

For testing without requiring actual conan installation:

**tests/unit/test_conan_helper.py:**
```python
"""Tests for ConanHelper with mocked conan."""
from unittest.mock import Mock, patch, MagicMock
import pytest
from skbuild_conan.conan_helper import ConanHelper
from skbuild_conan.exceptions import ConanNetworkError


@patch('skbuild_conan.conan_helper.ConanAPI')
@patch('skbuild_conan.conan_helper.ConanCli')
def test_network_error_retry(mock_cli_class, mock_api_class):
    """Test that network errors trigger retry logic."""
    mock_cli = Mock()
    mock_cli_class.return_value = mock_cli

    # Simulate network error on first call, success on second
    mock_cli.run.side_effect = [
        Exception("ConnectionError: Network unreachable"),
        None  # Success
    ]

    helper = ConanHelper()
    # This should retry and succeed
    # Implementation would need to be testable
```

### Test Organization

```bash
# Run all tests
pytest tests/

# Run only unit tests (fast)
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=skbuild_conan --cov-report=html tests/

# Run specific test file
pytest tests/unit/test_logging.py

# Run specific test
pytest tests/unit/test_logging.py::test_log_level_from_env

# Run with verbose output
pytest -v tests/

# Run with stdout (see print statements)
pytest -s tests/
```

### CI/CD Integration

Update `.github/workflows/pytest.yml` to include unit tests:

```yaml
- name: Run unit tests
  run: |
    pytest tests/unit/ -v --cov=skbuild_conan --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

---

## Code Quality

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. These run automatically on `git commit`:

- **black**: Code formatting (line length 88)
- **flake8**: Linting (max line length 127)
- **pyupgrade**: Modernize syntax to Python 3.7+
- **trailing-whitespace**: Remove trailing spaces
- **end-of-file-fixer**: Ensure files end with newline

### Manual Formatting

```bash
# Format code with black
black src/skbuild_conan/

# Check linting
flake8 src/skbuild_conan/

# Run all pre-commit checks
pre-commit run --all-files
```

### Code Style Guidelines

1. **Follow PEP 8** with black's formatting
2. **Maximum line length:** 88 characters (black default)
3. **Imports:** Group stdlib, third-party, local with blank lines
4. **Docstrings:** Use Google style
5. **Type hints:** Use typing module for Python 3.9 compatibility
6. **Error messages:** Be specific and actionable

### Example Good Code

```python
"""
Module docstring explaining purpose.
"""
import os
import sys
from typing import Optional, List

from .logging_utils import Logger
from .exceptions import ValidationError


def validate_requirements(
    requirements: Optional[List[str]] = None
) -> None:
    """
    Validate conan requirement strings.

    Args:
        requirements: List of requirement strings to validate

    Raises:
        ValidationError: If any requirement is invalid

    Example:
        >>> validate_requirements(["fmt/10.0.0"])
        >>> validate_requirements(["invalid"])  # Raises ValidationError
    """
    if not requirements:
        return

    errors = []
    for req in requirements:
        if '/' not in req:
            errors.append(f"Invalid format: {req}")

    if errors:
        raise ValidationError("\n".join(errors))
```

---

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.4.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

### Release Checklist

1. **Ensure all tests pass**
   ```bash
   # Run local tests
   pytest tests/

   # Test examples
   cd examples/simple_skbuild_conan_example
   pip install -e .
   pytest tests/
   ```

2. **Update version in `pyproject.toml`**
   ```toml
   version = "v1.4.1"
   ```

3. **Update CHANGELOG in `README.md`**
   ```markdown
   ## Changelog

   - _1.4.1_ Bug fix for retry logic edge case
   - _1.4.0_ Major transparency and usability improvements
   ```

4. **Commit version bump**
   ```bash
   git add pyproject.toml README.md
   git commit -m "chore: Bump version to v1.4.1"
   git push origin main
   ```

5. **Create GitHub Release**
   - Go to GitHub → Releases → "Draft a new release"
   - Tag: `v1.4.1`
   - Title: `v1.4.1 - Bug Fixes`
   - Description: Copy relevant section from CHANGELOG
   - Publish release

6. **Automatic PyPI Upload**
   - GitHub Action (`.github/workflows/release.yml`) will:
     - Build source distribution and wheel
     - Upload to PyPI using trusted publishing

7. **Verify Release**
   ```bash
   # Wait a few minutes for PyPI to update
   pip install --upgrade skbuild-conan
   python -c "import skbuild_conan; print(skbuild_conan.__version__)"
   ```

### Pre-release Testing (Optional)

For major releases, test on TestPyPI first:

```bash
# Build distributions
python -m build

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ skbuild-conan
```

---

## Troubleshooting

### Common Development Issues

#### Import Errors After Changes

```bash
# Reinstall in editable mode
pip install -e . --force-reinstall
```

#### Pre-commit Hook Failures

```bash
# Skip hooks temporarily (not recommended)
git commit --no-verify

# Fix issues manually
black src/
flake8 src/

# Update hook versions
pre-commit autoupdate
```

#### Test Failures in Examples

```bash
# Clean build artifacts
cd examples/simple_skbuild_conan_example
rm -rf _skbuild/ build/ dist/ *.egg-info
pip uninstall -y simple_skbuild_conan_example

# Rebuild
pip install -e . --verbose
```

#### Conan Cache Issues During Development

```bash
# Clear conan cache
rm -rf ~/.conan2/

# Or just the test profile
rm ~/.conan2/profiles/skbuild_conan_py
```

### Getting Help

1. **Check existing issues:** https://github.com/d-krupke/skbuild-conan/issues
2. **Review documentation:** README.md, this file
3. **Check CI logs:** GitHub Actions tab
4. **Ask maintainers:** Open a GitHub discussion

---

## Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch** from `main`
3. **Make your changes** following this guide
4. **Add tests** for new functionality
5. **Ensure all tests pass** locally
6. **Submit a pull request** with clear description

### Good First Issues

Look for issues labeled `good first issue` on GitHub. These are typically:
- Documentation improvements
- Adding tests for existing features
- Small bug fixes
- Code quality improvements

### Pull Request Guidelines

- **One feature per PR** - easier to review
- **Write clear commit messages** - explain the "why"
- **Add tests** - for new functionality
- **Update documentation** - if behavior changes
- **Keep it focused** - don't mix refactoring with features

---

## Future Improvements

### Testing
- [ ] Add comprehensive unit test suite
- [ ] Add macOS to CI matrix
- [ ] Add Windows to automatic CI (not just manual)
- [ ] Add coverage reporting with codecov
- [ ] Add performance benchmarks

### Development Tools
- [ ] Add tox for testing multiple Python versions locally
- [ ] Add mypy for type checking
- [ ] Add sphinx for documentation generation
- [ ] Add changelog automation

### CI/CD
- [ ] Add automatic dependency updates (Dependabot)
- [ ] Add security scanning (Snyk/CodeQL)
- [ ] Add automatic labeling for PRs
- [ ] Add issue templates

---

## Questions?

If you have questions about development, feel free to:
- Open a GitHub Discussion
- Open an issue with the `question` label
- Check the main README.md for usage questions

Thank you for contributing to skbuild-conan! 🎉
