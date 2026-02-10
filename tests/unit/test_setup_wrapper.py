"""
Unit tests for setup_wrapper module.

These tests validate verbosity detection, argument parsing, and the
main setup() function with mocked ConanHelper and skbuild.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from skbuild_conan.setup_wrapper import (
    _detect_verbosity_from_args,
    parse_args,
    setup as conan_setup,
)
from skbuild_conan.logging_utils import LogLevel
from skbuild_conan.exceptions import (
    ConanVersionError,
    ConanNetworkError,
    ConanDependencyError,
)


# ---------------------------------------------------------------------------
# _detect_verbosity_from_args
# ---------------------------------------------------------------------------


class TestDetectVerbosity:
    """Tests for command-line verbosity detection."""

    def test_no_flags_returns_none(self, monkeypatch):
        """Test that no verbosity flags returns None."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "install"])
        assert _detect_verbosity_from_args() is None

    def test_verbose_flag(self, monkeypatch):
        """Test that --verbose maps to VERBOSE."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "--verbose"])
        assert _detect_verbosity_from_args() == LogLevel.VERBOSE

    def test_short_verbose_flag(self, monkeypatch):
        """Test that -v maps to VERBOSE."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "-v"])
        assert _detect_verbosity_from_args() == LogLevel.VERBOSE

    def test_double_verbose_flag(self, monkeypatch):
        """Test that -vv maps to DEBUG."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "-vv"])
        assert _detect_verbosity_from_args() == LogLevel.DEBUG

    def test_triple_verbose_flag(self, monkeypatch):
        """Test that -vvv also maps to DEBUG."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "-vvv"])
        assert _detect_verbosity_from_args() == LogLevel.DEBUG

    def test_quiet_flag(self, monkeypatch):
        """Test that --quiet maps to QUIET."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "--quiet"])
        assert _detect_verbosity_from_args() == LogLevel.QUIET

    def test_short_quiet_flag(self, monkeypatch):
        """Test that -q maps to QUIET."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "-q"])
        assert _detect_verbosity_from_args() == LogLevel.QUIET


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    """Tests for build type argument parsing."""

    def test_default_is_release(self, monkeypatch):
        """Test that the default build type is Release."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])
        assert parse_args() == "Release"

    def test_debug_build_type(self, monkeypatch):
        """Test that --build-type Debug is parsed."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "--build-type", "Debug"])
        assert parse_args() == "Debug"

    def test_release_build_type(self, monkeypatch):
        """Test that --build-type Release is parsed."""
        monkeypatch.setattr(sys, "argv", ["setup.py", "--build-type", "Release"])
        assert parse_args() == "Release"


# ---------------------------------------------------------------------------
# setup() integration (with mocked internals)
# ---------------------------------------------------------------------------


class TestSetup:
    """Tests for the main setup() function with mocked dependencies."""

    def _mock_setup(self, monkeypatch, **setup_kwargs):
        """
        Call setup() with ConanHelper and skbuild.setup fully mocked.
        Returns (mock_wrapped_setup, mock_helper_instance).
        """
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_instance = mock_helper_cls.return_value
        mock_helper_instance.cmake_args.return_value = ["-DFROM_CONAN=1"]
        mock_helper_instance.generate_dependency_report.return_value = "report"

        mock_wrapped_setup = MagicMock(return_value=None)

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            conan_setup(
                wrapped_setup=mock_wrapped_setup,
                **setup_kwargs,
            )

        return mock_wrapped_setup, mock_helper_instance

    def test_forwards_cmake_args(self, monkeypatch):
        """Test that cmake_args from ConanHelper are forwarded to wrapped setup."""
        mock_setup, _ = self._mock_setup(
            monkeypatch,
            conan_requirements=["fmt/10.0.0"],
            name="testpkg",
        )

        mock_setup.assert_called_once()
        call_kwargs = mock_setup.call_args.kwargs
        assert "-DFROM_CONAN=1" in call_kwargs["cmake_args"]

    def test_passes_kwargs_through(self, monkeypatch):
        """Test that extra kwargs are passed to the wrapped setup."""
        mock_setup, _ = self._mock_setup(
            monkeypatch,
            conan_requirements=["fmt/10.0.0"],
            name="testpkg",
            version="1.0",
        )

        call_kwargs = mock_setup.call_args.kwargs
        assert call_kwargs["name"] == "testpkg"
        assert call_kwargs["version"] == "1.0"

    def test_calls_install_with_requirements(self, monkeypatch):
        """Test that ConanHelper.install is called with the right requirements."""
        _, mock_helper = self._mock_setup(
            monkeypatch,
            conan_requirements=["fmt/10.0.0"],
            name="testpkg",
        )

        mock_helper.install.assert_called_once_with(
            path=".", requirements=["fmt/10.0.0"]
        )

    def test_calls_install_with_conanfile(self, monkeypatch, tmp_path):
        """Test that ConanHelper.install is called with the right conanfile path."""
        conanfile_dir = str(tmp_path / "project")
        os.makedirs(conanfile_dir)

        _, mock_helper = self._mock_setup(
            monkeypatch,
            conanfile=conanfile_dir,
            name="testpkg",
        )

        mock_helper.install.assert_called_once_with(
            path=conanfile_dir, requirements=None
        )

    def test_version_error_exits(self, monkeypatch):
        """Test that ConanVersionError causes sys.exit(1)."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock(side_effect=ConanVersionError("1.0", "2.x"))

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            with pytest.raises(SystemExit) as exc_info:
                conan_setup(
                    conan_requirements=["fmt/10.0.0"],
                    name="testpkg",
                )

        assert exc_info.value.code == 1

    def test_network_error_exits(self, monkeypatch):
        """Test that ConanNetworkError causes sys.exit(1)."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_cls.return_value.install.side_effect = ConanNetworkError("timeout")

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            with pytest.raises(SystemExit) as exc_info:
                conan_setup(
                    conan_requirements=["fmt/10.0.0"],
                    name="testpkg",
                )

        assert exc_info.value.code == 1

    def test_keyboard_interrupt_exits_130(self, monkeypatch):
        """Test that KeyboardInterrupt causes sys.exit(130)."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_cls.return_value.install.side_effect = KeyboardInterrupt()

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            with pytest.raises(SystemExit) as exc_info:
                conan_setup(
                    conan_requirements=["fmt/10.0.0"],
                    name="testpkg",
                )

        assert exc_info.value.code == 130

    def test_dependency_error_exits(self, monkeypatch):
        """Test that ConanDependencyError causes sys.exit(1)."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_cls.return_value.install.side_effect = ConanDependencyError("missing")

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            with pytest.raises(SystemExit) as exc_info:
                conan_setup(
                    conan_requirements=["fmt/10.0.0"],
                    name="testpkg",
                )

        assert exc_info.value.code == 1

    def test_unexpected_error_reraises(self, monkeypatch):
        """Test that unexpected exceptions are re-raised."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_cls.return_value.install.side_effect = RuntimeError("unexpected")

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            with pytest.raises(RuntimeError, match="unexpected"):
                conan_setup(
                    conan_requirements=["fmt/10.0.0"],
                    name="testpkg",
                )

    def test_linux_abi_workaround(self, monkeypatch):
        """Test that Linux ABI workaround sets compiler.libcxx."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_instance = mock_helper_cls.return_value
        mock_helper_instance.cmake_args.return_value = []
        mock_helper_instance.generate_dependency_report.return_value = ""

        mock_wrapped = MagicMock()

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls), \
             patch("skbuild_conan.setup_wrapper.platform") as mock_platform:
            mock_platform.system.return_value = "Linux"
            conan_setup(
                conan_requirements=["fmt/10.0.0"],
                wrapped_setup=mock_wrapped,
                name="testpkg",
            )

        # The ConanHelper should have been created with libcxx setting
        call_kwargs = mock_helper_cls.call_args.kwargs
        assert call_kwargs["settings"]["compiler.libcxx"] == "libstdc++11"

    def test_windows_msvc_workaround(self, monkeypatch):
        """Test that Windows MSVC workaround adds cmake policy arg."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()
        mock_helper_instance = mock_helper_cls.return_value
        mock_helper_instance.cmake_args.return_value = []
        mock_helper_instance.generate_dependency_report.return_value = ""

        mock_wrapped = MagicMock()

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls), \
             patch("skbuild_conan.setup_wrapper.platform") as mock_platform:
            mock_platform.system.return_value = "Windows"
            conan_setup(
                conan_requirements=["fmt/10.0.0"],
                wrapped_setup=mock_wrapped,
                name="testpkg",
            )

        call_kwargs = mock_wrapped.call_args.kwargs
        assert "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW" in call_kwargs["cmake_args"]

    def test_validation_runs_before_conan(self, monkeypatch):
        """Test that invalid requirements are caught before ConanHelper is created."""
        monkeypatch.setattr(sys, "argv", ["setup.py"])

        mock_helper_cls = MagicMock()

        with patch("skbuild_conan.setup_wrapper.ConanHelper", mock_helper_cls):
            with pytest.raises(SystemExit) as exc_info:
                conan_setup(
                    conan_requirements=["invalid_no_slash"],
                    name="testpkg",
                )

        assert exc_info.value.code == 1
        # ConanHelper should never have been instantiated
        mock_helper_cls.assert_not_called()
