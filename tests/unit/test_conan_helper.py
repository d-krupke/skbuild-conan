"""
Unit tests for conan_helper module.

These tests validate the ConanHelper class and related utilities
using mocks to avoid requiring a real conan installation.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from skbuild_conan.conan_helper import (
    ConanHelper,
    EnvContextManager,
    retry_on_network_error,
)
from skbuild_conan.exceptions import (
    ConanVersionError,
    ConanNetworkError,
    ConanOutputError,
    ConanRecipeError,
    ConanDependencyError,
)
from skbuild_conan.logging_utils import LogLevel


# ---------------------------------------------------------------------------
# EnvContextManager
# ---------------------------------------------------------------------------


class TestEnvContextManager:
    """Tests for the EnvContextManager context manager."""

    def test_sets_env_vars_on_enter(self, monkeypatch):
        """Test that environment variables are set when entering the context."""
        monkeypatch.delenv("TEST_VAR_ABC", raising=False)

        with EnvContextManager({"TEST_VAR_ABC": "hello"}):
            assert os.environ["TEST_VAR_ABC"] == "hello"

    def test_restores_env_vars_on_exit(self, monkeypatch):
        """Test that environment variables are restored after exiting."""
        monkeypatch.setenv("TEST_VAR_ABC", "original")

        with EnvContextManager({"TEST_VAR_ABC": "temporary"}):
            assert os.environ["TEST_VAR_ABC"] == "temporary"

        assert os.environ["TEST_VAR_ABC"] == "original"

    def test_removes_new_env_vars_on_exit(self, monkeypatch):
        """Test that newly set env vars are removed after exiting."""
        monkeypatch.delenv("TEST_VAR_NEW", raising=False)

        with EnvContextManager({"TEST_VAR_NEW": "temporary"}):
            assert os.environ["TEST_VAR_NEW"] == "temporary"

        assert "TEST_VAR_NEW" not in os.environ

    def test_noop_when_env_is_none(self):
        """Test that None env dict is a no-op."""
        original = dict(os.environ)
        with EnvContextManager(None):
            pass
        # Environment should be unchanged
        assert dict(os.environ) == original

    def test_noop_when_env_is_empty(self):
        """Test that empty env dict is a no-op."""
        original = dict(os.environ)
        with EnvContextManager({}):
            pass
        assert dict(os.environ) == original


# ---------------------------------------------------------------------------
# retry_on_network_error decorator
# ---------------------------------------------------------------------------


class TestRetryOnNetworkError:
    """Tests for the retry_on_network_error decorator."""

    def test_succeeds_on_first_try(self):
        """Test that no retry happens when the call succeeds."""

        class Fake:
            logger = MagicMock()
            call_count = 0

            @retry_on_network_error(max_attempts=3, backoff_base=0.01)
            def do_work(self):
                self.call_count += 1
                return "ok"

        obj = Fake()
        assert obj.do_work() == "ok"
        assert obj.call_count == 1

    def test_retries_on_network_error(self):
        """Test that the decorator retries on ConanNetworkError."""

        class Fake:
            logger = MagicMock()
            call_count = 0

            @retry_on_network_error(max_attempts=3, backoff_base=0.01)
            def do_work(self):
                self.call_count += 1
                if self.call_count < 3:
                    raise ConanNetworkError("connection lost")
                return "recovered"

        obj = Fake()
        assert obj.do_work() == "recovered"
        assert obj.call_count == 3

    def test_raises_after_all_attempts_exhausted(self):
        """Test that the last exception is raised when all attempts fail."""

        class Fake:
            logger = MagicMock()

            @retry_on_network_error(max_attempts=2, backoff_base=0.01)
            def do_work(self):
                raise ConanNetworkError("always fails")

        obj = Fake()
        with pytest.raises(ConanNetworkError, match="always fails"):
            obj.do_work()

    def test_does_not_retry_other_exceptions(self):
        """Test that non-network exceptions are not retried."""

        class Fake:
            logger = MagicMock()
            call_count = 0

            @retry_on_network_error(max_attempts=3, backoff_base=0.01)
            def do_work(self):
                self.call_count += 1
                raise ValueError("not a network error")

        obj = Fake()
        with pytest.raises(ValueError, match="not a network error"):
            obj.do_work()
        assert obj.call_count == 1


# ---------------------------------------------------------------------------
# Helper to create a ConanHelper with mocked conan internals
# ---------------------------------------------------------------------------


def _make_helper(tmp_path, conan_version="2.5.0", **kwargs):
    """Create a ConanHelper with conan internals mocked out."""
    defaults = dict(
        output_folder=str(tmp_path / "conan_out"),
        log_level=LogLevel.QUIET,
    )
    defaults.update(kwargs)

    with patch("skbuild_conan.conan_helper.conan") as mock_conan, \
         patch.object(ConanHelper, "_conan_cli", return_value="{}"):
        mock_conan.__version__ = conan_version
        helper = ConanHelper(**defaults)

    return helper


# ---------------------------------------------------------------------------
# ConanHelper version checks
# ---------------------------------------------------------------------------


class TestConanHelperVersionCheck:
    """Tests for Conan version validation."""

    def test_conan_2x_accepted(self, tmp_path):
        """Test that Conan 2.x is accepted without raising."""
        # If this doesn't raise, version check passed
        _make_helper(tmp_path, conan_version="2.5.0")

    def test_conan_1x_rejected(self, tmp_path):
        """Test that Conan 1.x raises ConanVersionError."""
        with patch("skbuild_conan.conan_helper.conan") as mock_conan, \
             patch.object(ConanHelper, "_conan_cli", return_value="{}"):
            mock_conan.__version__ = "1.59.0"
            with pytest.raises(ConanVersionError):
                ConanHelper(
                    output_folder=str(tmp_path / "out"),
                    log_level=LogLevel.QUIET,
                )

    def test_old_conan_2x_warns(self, tmp_path, capsys):
        """Test that old Conan 2.0.x versions produce a warning."""
        with patch("skbuild_conan.conan_helper.conan") as mock_conan, \
             patch.object(ConanHelper, "_conan_cli", return_value="{}"):
            mock_conan.__version__ = "2.0.5"
            ConanHelper(
                output_folder=str(tmp_path / "out"),
                log_level=LogLevel.NORMAL,
            )

        captured = capsys.readouterr()
        assert "known issues" in captured.out.lower() or "upgrading" in captured.out.lower()


# ---------------------------------------------------------------------------
# cmake_args
# ---------------------------------------------------------------------------


class TestConanHelperCmakeArgs:
    """Tests for cmake_args generation."""

    def test_returns_correct_paths(self, tmp_path):
        """Test that cmake_args returns toolchain and prefix path."""
        helper = _make_helper(tmp_path)

        # Create the expected toolchain file
        release_dir = tmp_path / "conan_out" / "release"
        release_dir.mkdir(parents=True)
        (release_dir / "conan_toolchain.cmake").touch()

        args = helper.cmake_args()
        assert len(args) == 2
        assert args[0].startswith("-DCMAKE_TOOLCHAIN_FILE=")
        assert args[1].startswith("-DCMAKE_PREFIX_PATH=")
        assert "conan_toolchain.cmake" in args[0]

    def test_raises_when_toolchain_missing(self, tmp_path):
        """Test that RuntimeError is raised when toolchain file is missing."""
        helper = _make_helper(tmp_path)

        with pytest.raises(RuntimeError, match="conan_toolchain.cmake not found"):
            helper.cmake_args()


# ---------------------------------------------------------------------------
# _conan_to_json
# ---------------------------------------------------------------------------


class TestConanToJson:
    """Tests for JSON parsing of conan output."""

    def test_valid_json_parsed(self, tmp_path):
        """Test that valid JSON output is parsed correctly."""
        helper = _make_helper(tmp_path)

        with patch.object(helper, "_conan_cli", return_value='{"name": "fmt"}'):
            result = helper._conan_to_json(["inspect", "-f", "json", "."])

        assert result == {"name": "fmt"}

    def test_invalid_json_raises_output_error(self, tmp_path):
        """Test that invalid JSON raises ConanOutputError."""
        helper = _make_helper(tmp_path)

        with patch.object(helper, "_conan_cli", return_value="not json at all"):
            with pytest.raises(ConanOutputError, match="did not return valid JSON"):
                helper._conan_to_json(["inspect", "-f", "json", "."])


# ---------------------------------------------------------------------------
# generate_dependency_report
# ---------------------------------------------------------------------------


class TestGenerateDependencyReport:
    """Tests for dependency report generation."""

    def test_report_contains_build_config(self, tmp_path):
        """Test that the report contains profile and build type."""
        helper = _make_helper(tmp_path, profile="myprofile")
        report = helper.generate_dependency_report()

        assert "myprofile" in report
        assert "Release" in report

    def test_report_lists_requirements(self, tmp_path):
        """Test that the report lists requested requirements."""
        helper = _make_helper(tmp_path)
        report = helper.generate_dependency_report(requirements=["fmt/10.0.0", "boost/1.82.0"])

        assert "fmt/10.0.0" in report
        assert "boost/1.82.0" in report

    def test_report_written_to_file(self, tmp_path):
        """Test that the report is written to dependency-report.txt."""
        helper = _make_helper(tmp_path)
        helper.generate_dependency_report()

        report_path = tmp_path / "conan_out" / "release" / "dependency-report.txt"
        assert report_path.exists()
        content = report_path.read_text()
        assert "Dependency Resolution Report" in content

    def test_report_lists_local_recipes(self, tmp_path):
        """Test that the report lists local recipes when present."""
        recipe_dir = tmp_path / "myrecipe"
        recipe_dir.mkdir()
        (recipe_dir / "conanfile.py").touch()

        helper = _make_helper(tmp_path, local_recipes=[str(recipe_dir)])
        report = helper.generate_dependency_report()

        assert "Local Recipes" in report
        assert str(recipe_dir) in report


# ---------------------------------------------------------------------------
# install_from_paths
# ---------------------------------------------------------------------------


class TestInstallFromPaths:
    """Tests for local recipe installation."""

    def test_nonexistent_path_raises(self, tmp_path):
        """Test that a non-existent recipe path raises ConanRecipeError."""
        helper = _make_helper(tmp_path)

        with pytest.raises(ConanRecipeError, match="does not exist"):
            helper.install_from_paths(["/nonexistent/path"])

    def test_missing_conanfile_raises(self, tmp_path):
        """Test that a recipe dir without conanfile.py raises ConanRecipeError."""
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()

        helper = _make_helper(tmp_path)
        with pytest.raises(ConanRecipeError, match="Missing conanfile.py"):
            helper.install_from_paths([str(recipe_dir)])

    def test_skips_already_installed(self, tmp_path):
        """Test that already-installed packages are skipped."""
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()
        (recipe_dir / "conanfile.py").touch()

        helper = _make_helper(tmp_path)

        inspect_result = json.dumps({"name": "mypkg", "version": "1.0"})
        list_result = json.dumps({"Local Cache": {"mypkg/1.0": {}}})

        with patch.object(helper, "_conan_to_json", side_effect=[
            json.loads(inspect_result),
            json.loads(list_result),
        ]):
            # Should not raise — package is already cached
            helper.install_from_paths([str(recipe_dir)])


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------


class TestInstall:
    """Tests for the main install method."""

    def test_install_with_requirements(self, tmp_path):
        """Test that requirements are passed as --requires flags."""
        helper = _make_helper(tmp_path)

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli") as mock_cli:
            helper.install(requirements=["fmt/10.0.0", "zlib/1.3"])

        # Find the install call (not profile-related)
        cmd = mock_cli.call_args[0][0]
        assert "install" in cmd
        assert "--requires" in cmd
        assert "fmt/10.0.0" in cmd
        assert "zlib/1.3" in cmd

    def test_install_with_conanfile(self, tmp_path):
        """Test that conanfile path is passed when no requirements."""
        helper = _make_helper(tmp_path)

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli") as mock_cli:
            helper.install(path="/my/project")

        cmd = mock_cli.call_args[0][0]
        assert "install" in cmd
        assert "/my/project" in cmd

    def test_install_wraps_unexpected_error(self, tmp_path):
        """Test that unexpected errors are wrapped in ConanDependencyError."""
        helper = _make_helper(tmp_path)

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli", side_effect=RuntimeError("boom")):
            with pytest.raises(ConanDependencyError):
                helper.install(requirements=["fmt/10.0.0"])

    def test_install_does_not_wrap_known_errors(self, tmp_path):
        """Test that known error types pass through unwrapped."""
        helper = _make_helper(tmp_path)

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli", side_effect=ConanNetworkError("timeout")):
            with pytest.raises(ConanNetworkError):
                helper.install(requirements=["fmt/10.0.0"])
