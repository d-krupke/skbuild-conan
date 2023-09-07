import json
import subprocess
import sys
import os
import typing
import io
from contextlib import redirect_stdout

from conan.cli.cli import Cli as ConanCli
from conan.api.conan_api import ConanAPI

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
    ):
        self.generator_folder = os.path.abspath(output_folder)
        self.local_recipes = local_recipes if local_recipes else []
        self.settings = settings if settings else {}
        self.profile = profile
        self.env = env
        env = env if env else {}
        self._default_profile_name = env.get("CONAN_DEFAULT_PROFILE",
                                              os.environ.get("CONAN_DEFAULT_PROFILE", "default"))
        if env:
            self._log(f"Temporarily overriding environment variables: {env}")
        self._check_conan_version()


    def _log(self, msg: str):
        print(f"[skbuild-conan] {msg}")
    
    def _conan_cli(self, cmd: typing.List[str]) -> str:
        printable_cmd = " ".join(cmd)
        # color the command blue
        printable_cmd = f"\033[94mconan {printable_cmd}\033[0m"
        self._log(printable_cmd)

        f = io.StringIO()
        conan_api = ConanAPI()
        conan_cli = ConanCli(conan_api)
        with redirect_stdout(f):
            with EnvContextManager(self.env):
                try:
                    conan_cli.run(cmd)
                except BaseException as e:
                    error = conan_cli.exception_exit_error(e)
                    raise
        out = f.getvalue()
        self._log(out)
        return out

    def conan_version(self):
        args = ["-v"]
        version = self._conan_cli(args).split(" ")[-1]
        return version

    def _check_conan_version(self):
        self._log("Checking Conan version...")
        version = self.conan_version()
        if version[0] != "2":
            raise RuntimeError(f"Conan 2 required. Current version {version}.")

    def _conan_to_json(self, args: typing.List[str]):
        """
        Runs conan with the args and parses the output as json.
        """
        args = args
        data = json.loads(self._conan_cli(args))
        return data

    def install_from_paths(self, paths: typing.List[str]):
        """
        Installs all the conanfiles to local cache. Will automatically skip if the package
        is already available. Currently only works on name and version, not user or
        similar.
        """
        for path in paths:
            self._log(f"Installing {path}...")
            if not os.path.exists(path):
                raise RuntimeError(f"Conan recipe '{path}' does not exist.")
            package_info = self._conan_to_json(["inspect", "-f", "json", path])
            conan_list = self._conan_to_json(
                ["list", "-c", "-f", "json", package_info["name"]]
            )
            package_id = f"{package_info['name']}/{package_info['version']}"
            if package_id in conan_list["Local Cache"].keys():
                self._log(f"{package_id} already available. Not installing again.")
                continue
            cmd = [
                "create",
                path,
                "-pr",
                self.profile,
                "-s",
                "build_type=Release",
                "--build=missing",
            ]
            self._conan_cli(cmd)

    def create_profile(self):
        """
        Creates a default profile if it does not exist.
        """
        self._log("Creating conan profile...")
        # check if profile exists or create a default one automatically.
        profile_list = self._conan_to_json(["profile", "list", "-f", "json"])
        if self._default_profile_name not in profile_list:
            self._conan_cli(["profile", "detect"])
            if self.profile == self._default_profile_name:
                return  # default profile is already created
        if self.profile in profile_list:
            self._log("Profile already exists.")
            return  # Profile already exists
        cmd = ["profile", "detect", "--name", self.profile]
        self._conan_cli( cmd)

    def install(
        self, path: str = ".", requirements: typing.Optional[typing.List[str]] = None
    ):
        """
        Running conan to get C++ dependencies
        """
        self.create_profile()
        self.install_from_paths(self.local_recipes)
        self._log("Preparing conan dependencies for building package...")
        cmd = [ "install"]
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
        # Making sure  the right generators are used.
        cmd += ["-g", "CMakeDeps", "-g", "CMakeToolchain"]
        # profile
        cmd += ["-pr", self.profile]
        self._conan_cli( cmd)

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
