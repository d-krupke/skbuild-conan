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
        assert "known issues" in captured.err.lower() or "upgrading" in captured.err.lower()


# ---------------------------------------------------------------------------
# cmake_args
# ---------------------------------------------------------------------------


class TestConanHelperCmakeArgs:
    """Tests for cmake_args generation."""

    def test_returns_correct_paths(self, tmp_path):
        """Test that cmake_args returns toolchain and prefix path (flat layout)."""
        helper = _make_helper(tmp_path)

        # Create the expected toolchain file (flat layout, no cmake_layout)
        release_dir = tmp_path / "conan_out" / "release"
        release_dir.mkdir(parents=True)
        (release_dir / "conan_toolchain.cmake").touch()

        args = helper.cmake_args()
        assert len(args) == 2
        assert args[0].startswith("-DCMAKE_TOOLCHAIN_FILE=")
        assert "conan_toolchain.cmake" in args[0]
        # PREFIX_PATH should point to the generator folder itself
        assert args[1] == f"-DCMAKE_PREFIX_PATH={release_dir}"

    def test_finds_toolchain_with_cmake_layout(self, tmp_path):
        """Test that cmake_args finds toolchain under build/{BuildType}/generators/ (cmake_layout)."""
        helper = _make_helper(tmp_path)

        # cmake_layout places generators in build/{BuildType}/generators/
        generators_dir = tmp_path / "conan_out" / "release" / "build" / "Release" / "generators"
        generators_dir.mkdir(parents=True)
        (generators_dir / "conan_toolchain.cmake").touch()

        args = helper.cmake_args()
        assert len(args) == 2
        assert args[0].startswith("-DCMAKE_TOOLCHAIN_FILE=")
        assert "conan_toolchain.cmake" in args[0]
        # PREFIX_PATH should point to the generators directory, not the top-level folder
        assert args[1] == f"-DCMAKE_PREFIX_PATH={generators_dir}"

    def test_finds_toolchain_with_cmake_layout_debug(self, tmp_path):
        """Test cmake_layout with Debug build type."""
        helper = _make_helper(tmp_path, build_type="Debug")

        generators_dir = tmp_path / "conan_out" / "debug" / "build" / "Debug" / "generators"
        generators_dir.mkdir(parents=True)
        (generators_dir / "conan_toolchain.cmake").touch()

        args = helper.cmake_args()
        assert len(args) == 2
        assert "conan_toolchain.cmake" in args[0]
        assert args[1] == f"-DCMAKE_PREFIX_PATH={generators_dir}"

    def test_prefers_flat_layout_over_cmake_layout(self, tmp_path):
        """Test that flat layout is preferred when both paths exist."""
        helper = _make_helper(tmp_path)

        # Create toolchain in both locations
        release_dir = tmp_path / "conan_out" / "release"
        release_dir.mkdir(parents=True)
        (release_dir / "conan_toolchain.cmake").touch()

        generators_dir = release_dir / "build" / "Release" / "generators"
        generators_dir.mkdir(parents=True)
        (generators_dir / "conan_toolchain.cmake").touch()

        args = helper.cmake_args()
        # Should find the flat-layout one first
        assert args[1] == f"-DCMAKE_PREFIX_PATH={release_dir}"

    def test_raises_when_toolchain_missing(self, tmp_path):
        """Test that RuntimeError is raised when toolchain file is missing."""
        helper = _make_helper(tmp_path)

        with pytest.raises(RuntimeError, match="conan_toolchain.cmake not found"):
            helper.cmake_args()


# ---------------------------------------------------------------------------
# conan_env / CONAN_HOME
# ---------------------------------------------------------------------------


class TestConanEnv:
    """Tests for the environment overrides passed as `conan_env`.

    `ConanAPI()` reads `CONAN_HOME` and loads the configuration in its
    constructor, so the override has to be active while it is built. It used to
    be constructed before the override was applied, which made
    `conan_env={"CONAN_HOME": ...}` a no-op.
    """

    def test_conan_api_sees_the_env_override(self, tmp_path, monkeypatch):
        """The env override must be active while ConanAPI is constructed."""
        monkeypatch.delenv("CONAN_HOME", raising=False)
        home = tmp_path / "cache"
        helper = _make_helper(tmp_path, env={"CONAN_HOME": str(home)})

        seen = {}

        def fake_api():
            seen["CONAN_HOME"] = os.environ.get("CONAN_HOME")
            return MagicMock()

        with patch("skbuild_conan.conan_helper.ConanAPI", side_effect=fake_api), \
             patch("skbuild_conan.conan_helper.ConanCli"):
            helper._conan_cli(["--version"])

        assert seen["CONAN_HOME"] == str(home)

    def test_relative_conan_home_is_made_absolute(self, tmp_path):
        """Conan rejects a relative CONAN_HOME, so resolve it against cwd.

        The README and the CGAL example both document
        `conan_env={"CONAN_HOME": "./conan/cache"}`, which conan would refuse
        with "please specify an absolute or path starting with ~/".
        """
        helper = _make_helper(tmp_path, env={"CONAN_HOME": "./conan/cache"})

        assert os.path.isabs(helper.env["CONAN_HOME"])
        assert helper.env["CONAN_HOME"] == os.path.abspath("./conan/cache")

    def test_absolute_conan_home_is_untouched(self, tmp_path):
        """An already absolute path must be passed through unchanged."""
        home = str(tmp_path / "cache")
        helper = _make_helper(tmp_path, env={"CONAN_HOME": home})

        assert helper.env["CONAN_HOME"] == home

    def test_tilde_conan_home_is_expanded(self, tmp_path):
        """`~/...` is expanded rather than treated as a relative path."""
        helper = _make_helper(tmp_path, env={"CONAN_HOME": "~/my_conan_home"})

        assert helper.env["CONAN_HOME"] == os.path.expanduser("~/my_conan_home")

    def test_other_env_vars_are_untouched(self, tmp_path):
        """Only CONAN_HOME gets path treatment; everything else passes through."""
        helper = _make_helper(tmp_path, env={"CC": "", "CXX": "./not/a/path"})

        assert helper.env == {"CC": "", "CXX": "./not/a/path"}

    def test_caller_env_dict_not_mutated(self, tmp_path):
        """The caller's dict must not be rewritten under them."""
        user_env = {"CONAN_HOME": "./conan/cache"}
        _make_helper(tmp_path, env=user_env)

        assert user_env == {"CONAN_HOME": "./conan/cache"}


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

    def test_creates_even_when_name_version_is_cached(self, tmp_path):
        """A local recipe is exported on every run, never skipped by name/version.

        The cache can hold a package with the same `name/version` that came from
        a remote -- the bundled CGAL recipe is `cgal/6.0.1`, the very reference
        ConanCenter serves. Skipping on that match silently swapped the local
        recipe for the remote package. `conan create --build=missing` is cheap
        when nothing changed, so it always runs and conan decides.
        """
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()
        (recipe_dir / "conanfile.py").touch()

        helper = _make_helper(tmp_path)

        with patch.object(
            helper, "_conan_to_json", return_value={"name": "mypkg", "version": "1.0"}
        ), patch.object(helper, "_conan_cli") as mock_cli:
            helper.install_from_paths([str(recipe_dir)])

        cmd = mock_cli.call_args[0][0]
        assert cmd[0] == "create"
        assert "--build=missing" in cmd

    def test_does_not_query_the_cache_listing(self, tmp_path):
        """`conan list` is no longer consulted; it only enabled the bad skip."""
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()
        (recipe_dir / "conanfile.py").touch()

        helper = _make_helper(tmp_path)

        with patch.object(
            helper, "_conan_to_json", return_value={"name": "mypkg", "version": "1.0"}
        ) as mock_json, patch.object(helper, "_conan_cli"):
            helper.install_from_paths([str(recipe_dir)])

        called = [call[0][0] for call in mock_json.call_args_list]
        assert all("list" not in args for args in called)

    def test_create_uses_profile_settings(self, tmp_path):
        """Local recipes must be built with the same settings as the dependencies.

        Otherwise the recipe is built with the profile defaults and conan's
        binary compatibility fallback resolves that mismatched binary for the
        later `install` -- e.g. a `gnu20` build answering a `cppstd=20` request.
        """
        recipe_dir = tmp_path / "recipe"
        recipe_dir.mkdir()
        (recipe_dir / "conanfile.py").touch()

        helper = _make_helper(tmp_path, settings={"compiler.cppstd": "20"})

        with patch.object(
            helper, "_conan_to_json", return_value={"name": "mypkg", "version": "1.0"}
        ), patch.object(helper, "_conan_cli") as mock_cli:
            helper.install_from_paths([str(recipe_dir)])

        cmd = mock_cli.call_args[0][0]
        assert cmd[0] == "create"
        assert "compiler.cppstd=20" in cmd
        assert cmd[cmd.index("compiler.cppstd=20") - 1] == "-s"
        # build_type must still be forwarded
        assert "build_type=Release" in cmd


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

    def test_install_settings_are_sorted(self, tmp_path):
        """Settings are emitted in a stable order, independent of dict order."""
        settings = {"compiler.libcxx": "libstdc++11", "compiler.cppstd": "20"}
        helper = _make_helper(tmp_path, settings=settings)

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli") as mock_cli:
            helper.install(requirements=["fmt/10.0.0"])

        cmd = mock_cli.call_args[0][0]
        # cppstd sorts before libcxx, even though it was inserted second
        assert cmd.index("compiler.cppstd=20") < cmd.index("compiler.libcxx=libstdc++11")

    def test_build_type_in_settings_is_dropped(self, tmp_path, capsys):
        """build_type belongs to --build-type, not to the profile settings.

        Conan uses the last `-s` given for a key and `build_type` is always
        appended last, so a value here was silently overridden. Drop it rather
        than emit a command line that sets build_type twice.
        """
        helper = _make_helper(
            tmp_path,
            settings={"build_type": "Debug", "compiler.cppstd": "20"},
            log_level=LogLevel.NORMAL,
        )

        assert "build_type" not in helper.settings
        assert "build_type" in capsys.readouterr().err.lower()

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli") as mock_cli:
            helper.install(requirements=["fmt/10.0.0"])

        cmd = mock_cli.call_args[0][0]
        assert cmd.count("build_type=Release") == 1
        assert "build_type=Debug" not in cmd

    def test_install_forwards_profile_settings(self, tmp_path):
        """Test that settings such as compiler.cppstd reach the install command."""
        helper = _make_helper(tmp_path, settings={"compiler.cppstd": "20"})

        with patch.object(helper, "create_profile"), \
             patch.object(helper, "_conan_cli") as mock_cli:
            helper.install(requirements=["fmt/10.0.0"])

        cmd = mock_cli.call_args[0][0]
        assert "compiler.cppstd=20" in cmd
        assert cmd[cmd.index("compiler.cppstd=20") - 1] == "-s"

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
