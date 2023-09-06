import json
import subprocess
import sys
import os
import typing


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
        self.env = env if env else {}
        if self.env:
            self._log(f"Temporary overriding environment variables: {env}")
        self._check_conan_version()

    def _log(self, msg: str):
        print(f"[skbuild-conan] {msg}")

    def _shell(self, cmd: typing.List[str]) -> str:
        printable_cmd = " ".join(cmd)
        # color the command blue
        printable_cmd = f"\033[94m{printable_cmd}\033[0m"
        self._log(printable_cmd)
        out = subprocess.check_output(cmd, env=self.env).decode()
        return out

    def conan_version(self):
        args = [sys.executable, "-m", "conans.conan", "-v"]
        version = self._shell(args).split(" ")[-1]
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
        args = [sys.executable, "-m", "conans.conan"] + args
        data = json.loads(self._shell(args))
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
                "-m",
                "conans.conan",
                "create",
                path,
                "-pr",
                self.profile,
                "-s",
                "build_type=Release",
                "--build=missing",
            ]
            self._shell([sys.executable] + cmd)

    def create_profile(self):
        """
        Creates a default profile if it does not exist.
        """
        self._log("Creating conan profile...")
        # check if profile exists or create a default one automatically.
        if self.profile in self._conan_to_json(["profile", "list", "-f", "json"]):
            self._log("Profile already exists.")
            return  # Profile already exists
        cmd = ["-m", "conans.conan", "profile", "detect", "--name", self.profile]
        self._shell([sys.executable] + cmd)

    def install(
        self, path: str = ".", requirements: typing.Optional[typing.List[str]] = None
    ):
        """
        Running conan to get C++ dependencies
        """
        self.create_profile()
        self.install_from_paths(self.local_recipes)
        self._log("Preparing conan dependencies for building package...")
        cmd = ["-m", "conans.conan", "install"]
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
        self._shell([sys.executable] + cmd)

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
