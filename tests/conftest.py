"""
Pytest configuration and shared fixtures.

This file contains pytest configuration and fixtures that are
available to all test modules.
"""
import pytest
import os


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """
    Clean environment variables before each test.

    This ensures that tests don't interfere with each other via
    environment variables.
    """
    # Remove skbuild-conan env vars if they exist
    monkeypatch.delenv('SKBUILD_CONAN_LOG_LEVEL', raising=False)


@pytest.fixture
def isolated_env(monkeypatch):
    """
    Provide a completely isolated environment for tests.

    This fixture clears all environment variables and provides
    a clean slate. Use this for tests that need complete isolation.
    """
    original_env = dict(os.environ)
    os.environ.clear()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
