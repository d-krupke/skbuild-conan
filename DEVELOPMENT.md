# Development Guide

## Setup

```bash
git clone https://github.com/d-krupke/skbuild-conan.git
cd skbuild-conan
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
pip install pytest pre-commit
pre-commit install
```

## Project Structure

```
src/skbuild_conan/
  __init__.py          # Public API: setup(), LogLevel
  setup_wrapper.py     # Main setup() function, argument parsing, validation
  conan_helper.py      # ConanHelper class, conan CLI interaction
  logging_utils.py     # Logger, LogLevel enum
  exceptions.py        # Exception hierarchy

tests/unit/            # Unit tests (mocked, no conan needed)
tests/docker/          # Multi-compiler example builds in containers
examples/              # Integration test projects
.github/workflows/     # CI: unit tests, integration tests, release
```

## Testing

```bash
# Unit tests (fast, no conan needed)
pytest tests/unit/ -v

# Integration tests (requires conan + C++ compiler)
pip install examples/simple_skbuild_conan_example
pytest examples/simple_skbuild_conan_example/tests

# All examples against the local checkout
./test_examples.sh

# All examples across several Linux compilers (requires docker)
./tests/docker/run.sh
```

`tests/docker/` builds the examples in containers with different default C++
standards. `ubuntu-latest` ships a GCC defaulting to `gnu17`, so it cannot
reproduce the class of failure where a dependency needs a newer standard than
the compiler enables by default; `gcc:10` (default `gnu14`) can. See
[tests/docker/README.md](tests/docker/README.md).

## Code Quality

Pre-commit hooks run automatically on commit. The project uses
[ruff](https://docs.astral.sh/ruff/) for formatting and linting,
plus pyupgrade, clang-format, and cmake-format.

```bash
pre-commit run --all-files  # Run all checks manually
```

## Release Process

1. Update `version` in `pyproject.toml`
2. Update changelog in `README.md`
3. Push to `main`
4. Create a GitHub Release with the version tag (e.g., `v1.4.1`)
5. The `release.yml` workflow builds and publishes to PyPI automatically
