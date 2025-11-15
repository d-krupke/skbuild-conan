import json
import subprocess
import sys
import os
import typing
import io
import time
from contextlib import redirect_stdout
from functools import wraps

from conan.cli.cli import Cli as ConanCli
from conan.api.conan_api import ConanAPI
import conan

from .logging_utils import Logger, LogLevel
from .exceptions import (
    ConanVersionError,
    ConanProfileError,
    ConanDependencyError,
    ConanNetworkError,
    ConanRecipeError,
    ConanOutputError,
)


def retry_on_network_error(max_attempts: int = 3, backoff_base: float = 2.0):
    """
    Decorator to retry network operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_base: Base for exponential backoff (seconds)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except ConanNetworkError as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_base ** attempt
                        self.logger.warning(
                            f"Network error (attempt {attempt+1}/{max_attempts}). "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        self.logger.error(
                            f"Network error after {max_attempts} attempts. Giving up."
                        )
            # This should never happen (last_exception should always be set if we reach here)
            # but we check to be safe
            if last_exception is not None:
                raise last_exception
            else:
                # Shouldn't happen, but just in case
                return func(self, *args, **kwargs)
        return wrapper
    return decorator


class EnvContextManager:
    """
    Context for temporary replacing environment variables.
    """

    def __init__(self, env: typing.Optional[typing.Dict[str, str]]):
        self.env = env
        self.old_env = {}

    def __enter__(self):
        if not self.env:
            return
        for key, val in self.env.items():
            self.old_env[key] = os.environ.get(key)
            os.environ[key] = val

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.env:
            return
        for key, val in self.old_env.items():
            if val is None:
                del os.environ[key]
            else:
                os.environ[key] = val


class ConanHelper:
    """
    The ConanHelper is used for installing conan dependencies automatically
    for scikit-build based packages.
    This is kind of a workaround, not a production ready tool.

    Dominik Krupke, TU Braunschweig, 2023
    """

    def __init__(
        self,
        output_folder=".conan",
        local_recipes=None,
        settings=None,
        profile: str = "default",
        env: typing.Optional[typing.Dict] = None,
        build_type: str = "Release",
        log_level: typing.Optional[LogLevel] = None,
    ):
        self.local_recipes = local_recipes if local_recipes else []
        self.settings = settings if settings else {}
        self.profile = profile
        self.env = env
        self.build_type = build_type
        self.logger = Logger(log_level)
        self.generator_folder = os.path.join(
            os.path.abspath(output_folder), self.build_type.lower()
        )
        env = env if env else {}
        self._default_profile_name = env.get(
            "CONAN_DEFAULT_PROFILE", os.environ.get("CONAN_DEFAULT_PROFILE", "default")
        )
        if env:
            self.logger.verbose(f"Temporarily overriding environment variables: {env}")
        self._check_conan_version()
        self._check_version_compatibility()

    @retry_on_network_error(max_attempts=3, backoff_base=2.0)
    def _conan_cli(self, cmd: typing.List[str]) -> str:
        printable_cmd = " ".join(cmd)
        self.logger.command(f"conan {printable_cmd}")

        f = io.StringIO()
        conan_api = ConanAPI()
        conan_cli = ConanCli(conan_api)
        with redirect_stdout(f):
            with EnvContextManager(self.env):
                try:
                    conan_cli.run(cmd)
                except BaseException as e:
                    out = f.getvalue()
                    self.logger.conan_output(out)
                    # Check if it's a network error
                    if "ConnectionError" in str(e) or "URLError" in str(e):
                        raise ConanNetworkError(str(e)) from e
                    # Re-raise as-is for now (will be caught by caller)
                    raise
        out = f.getvalue()
        self.logger.conan_output(out)
        return out

    def conan_version(self):
        return conan.__version__


    def _check_conan_version(self):
        self.logger.verbose("Checking Conan version...")
        version = self.conan_version()
        if version[0] != "2":
            raise ConanVersionError(version, "2.x")

        # Parse version for more detailed checks
        try:
            version_parts = version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2].split('-')[0]) if len(version_parts) > 2 else 0

            # Warn about old Conan 2.x versions
            if major == 2 and minor == 0 and patch < 14:
                self.logger.warning(
                    f"Conan {version} may have known issues. "
                    f"Consider upgrading to Conan 2.0.14 or later."
                )
        except (ValueError, IndexError):
            # If we can't parse the version, just log it
            self.logger.debug(f"Could not parse Conan version: {version}")

    def _check_version_compatibility(self):
        """Check compatibility of all components."""
        self.logger.verbose("Checking version compatibility...")
        issues = []

        # Check Python version
        py_version = sys.version_info
        if py_version < (3, 9):
            issues.append(
                f"Python {py_version.major}.{py_version.minor} is below recommended version. "
                f"Minimum recommended version is 3.9 (though 3.7+ may work)."
            )

        # Check scikit-build version if we can
        try:
            import skbuild
            if hasattr(skbuild, '__version__'):
                skbuild_version = skbuild.__version__
                # Parse version and check if it's below 0.17.0
                try:
                    # Simple version comparison for major.minor
                    version_parts = skbuild_version.split('.')
                    major = int(version_parts[0])
                    minor = int(version_parts[1]) if len(version_parts) > 1 else 0

                    if major == 0 and minor < 17:
                        self.logger.warning(
                            f"scikit-build {skbuild_version} may be too old. "
                            f"Recommended version is 0.17.3+"
                        )
                except (ValueError, IndexError):
                    # If we can't parse, just skip the check
                    self.logger.debug(f"Could not parse scikit-build version: {skbuild_version}")
        except Exception as e:
            self.logger.debug(f"Could not check scikit-build version: {e}")

        if issues:
            # These are warnings, not errors
            for issue in issues:
                self.logger.warning(issue)

    def _conan_to_json(self, args: typing.List[str]):
        """
        Runs conan with the args and parses the output as json.
        """
        try:
            output = self._conan_cli(args)
            return json.loads(output)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse conan output as JSON: {e}")
            self.logger.debug(f"Conan output was: {output}")
            raise ConanOutputError(
                f"Conan did not return valid JSON. This is likely a bug. "
                f"Output: {output[:200]}..."
            ) from e

    def install_from_paths(self, paths: typing.List[str]):
        """
        Installs all the conanfiles to local cache. Will automatically skip if the package
        is already available. Currently only works on name and version, not user or
        similar.
        """
        for path in paths:
            self.logger.info(f"Installing local recipe from {path}...")
            if not os.path.exists(path):
                raise ConanRecipeError(path, "Path does not exist")

            conanfile_path = os.path.join(path, "conanfile.py")
            if not os.path.exists(conanfile_path):
                raise ConanRecipeError(path, "Missing conanfile.py")

            try:
                package_info = self._conan_to_json(["inspect", "-f", "json", path])
                conan_list = self._conan_to_json(
                    ["list", "-c", "-f", "json", package_info["name"]]
                )
                package_id = f"{package_info['name']}/{package_info['version']}"
                if package_id in conan_list["Local Cache"].keys():
                    self.logger.info(f"{package_id} already available. Skipping.")
                    continue

                self.logger.verbose(f"Building and caching {package_id}...")
                cmd = [
                    "create",
                    path,
                    "-pr",
                    self.profile,
                    "-s",
                    f"build_type={self.build_type}",
                    "--build=missing",
                ]
                self._conan_cli(cmd)
                self.logger.success(f"Successfully installed {package_id}")
            except Exception as e:
                if not isinstance(e, (ConanRecipeError, ConanNetworkError, ConanOutputError)):
                    raise ConanRecipeError(path, str(e)) from e
                raise

    def create_profile(self):
        """
        Creates a default profile if it does not exist.
        """
        self.logger.verbose("Setting up Conan profile...")
        # check if profile exists or create a default one automatically.
        try:
            profile_list = self._conan_to_json(["profile", "list", "-f", "json"])
            if self._default_profile_name not in profile_list:
                self.logger.info(f"Creating default profile '{self._default_profile_name}'...")
                self._conan_cli(["profile", "detect"])
                if self.profile == self._default_profile_name:
                    return  # default profile is already created
            if self.profile in profile_list:
                self.logger.verbose(f"Profile '{self.profile}' already exists.")
                return  # Profile already exists

            self.logger.info(f"Creating profile '{self.profile}'...")
            cmd = ["profile", "detect", "--name", self.profile]
            self._conan_cli(cmd)
            self.logger.success(f"Profile '{self.profile}' created successfully")
        except Exception as e:
            if not isinstance(e, (ConanProfileError, ConanNetworkError, ConanOutputError)):
                raise ConanProfileError(self.profile, str(e)) from e
            raise

    def install(
        self, path: str = ".", requirements: typing.Optional[typing.List[str]] = None
    ):
        """
        Running conan to get C++ dependencies
        """
        # Phase 1: Profile setup
        self.logger.enter_phase("Setting up Conan Profile")
        try:
            self.create_profile()
            self.logger.exit_phase(success=True)
        except Exception:
            self.logger.exit_phase(success=False)
            raise

        # Phase 2: Local recipes
        if self.local_recipes:
            self.logger.enter_phase("Installing Local Recipes")
            try:
                self.install_from_paths(self.local_recipes)
                self.logger.exit_phase(success=True)
            except Exception:
                self.logger.exit_phase(success=False)
                raise

        # Phase 3: Dependency resolution and installation
        self.logger.enter_phase("Resolving and Installing Dependencies")
        try:
            if requirements:
                self.logger.info(f"Installing requirements: {', '.join(requirements)}")
            else:
                self.logger.info(f"Installing from conanfile at: {path}")

            cmd = ["install"]
            if requirements:
                # requirements passed from Python directly
                for req in requirements:
                    cmd += ["--requires", req]
            else:
                # requirements from conanfile
                cmd += [path]
            for key, val in self.settings.items():
                cmd += ["-s", f"{key}={val}"]
            cmd += ["--build=missing"]
            # redirecting the output to a subfolder. The `cmake_args` makes sure
            # that CMake still finds it.
            cmd += [f"--output-folder={self.generator_folder}"]
            # Making sure the right generators are used.
            cmd += ["-g", "CMakeDeps", "-g", "CMakeToolchain"]
            # profile
            cmd += ["-pr", self.profile]
            # build type
            cmd += ["-s", f"build_type={self.build_type}"]

            self._conan_cli(cmd)
            self.logger.exit_phase(success=True)
        except Exception as e:
            self.logger.exit_phase(success=False)
            if not isinstance(e, (ConanDependencyError, ConanNetworkError, ConanOutputError)):
                raise ConanDependencyError(str(e)) from e
            raise

    def generate_dependency_report(self, requirements: typing.Optional[typing.List[str]] = None) -> str:
        """
        Generate a dependency resolution report for transparency.

        Returns:
            A formatted report string showing what was installed and why.
        """
        from datetime import datetime

        lines = []
        lines.append("=" * 60)
        lines.append("Dependency Resolution Report")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Build configuration
        lines.append("Build Configuration:")
        lines.append(f"  Profile: {self.profile}")
        lines.append(f"  Build Type: {self.build_type}")
        lines.append(f"  Output Folder: {self.generator_folder}")
        if self.settings:
            lines.append(f"  Custom Settings:")
            for key, val in self.settings.items():
                lines.append(f"    {key}={val}")
        lines.append("")

        # Dependencies
        if requirements:
            lines.append("Requested Dependencies:")
            for req in requirements:
                lines.append(f"  - {req}")
        else:
            lines.append("Dependencies loaded from conanfile")
        lines.append("")

        # Local recipes
        if self.local_recipes:
            lines.append("Local Recipes:")
            for recipe in self.local_recipes:
                lines.append(f"  - {recipe}")
            lines.append("")

        # Try to get installed package info
        try:
            graph_info_path = os.path.join(self.generator_folder, "graph_info.json")
            if os.path.exists(graph_info_path):
                with open(graph_info_path, 'r') as f:
                    graph_info = json.load(f)
                lines.append("Resolved Packages:")
                # Parse graph_info to show packages (structure varies by conan version)
                if "graph" in graph_info:
                    lines.append("  (See graph_info.json for detailed dependency graph)")
            else:
                lines.append("Resolved Packages:")
                lines.append("  (Detailed graph information not available)")
        except Exception as e:
            self.logger.debug(f"Could not read graph info: {e}")
            lines.append("Resolved Packages:")
            lines.append("  (Could not read dependency graph)")

        lines.append("")
        lines.append("=" * 60)

        report = "\n".join(lines)

        # Write report to file
        report_path = os.path.join(self.generator_folder, "dependency-report.txt")
        try:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w') as f:
                f.write(report)
            self.logger.verbose(f"Dependency report written to: {report_path}")
        except Exception as e:
            self.logger.debug(f"Could not write dependency report: {e}")

        return report

    def cmake_args(self):
        """
        Has to be appended to `cmake_args` in `setup(...)`.
        """
        toolchain_path = os.path.abspath(
            f"{self.generator_folder}/conan_toolchain.cmake"
        )
        if not os.path.exists(toolchain_path):
            raise RuntimeError(
                "conan_toolchain.cmake not found. Make sure you"
                " specified 'CMakeDeps' and 'CMakeToolchain' as"
                " generators."
            )
        return [
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_path}",
            f"-DCMAKE_PREFIX_PATH={self.generator_folder}",
        ]
