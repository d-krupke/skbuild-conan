import sys
import typing
import skbuild
import platform
from .conan_helper import ConanHelper


def setup(
    conanfile: str = ".",
    conan_recipes: typing.Optional[typing.List[str]] = None,
    conan_requirements: typing.Optional[typing.List[str]] = None,
    conan_output_folder=".conan",
    conan_profile_settings: typing.Optional[typing.Dict] = None,
    wrapped_setup: typing.Callable = skbuild.setup,
    cmake_args: typing.Optional[typing.List[str]] = None,
    conan_profile: str = "skbuild_conan_py",
    conan_env: typing.Dict[str, str] = {"CC": "", "CXX": ""},
    **kwargs,
):
    """
    An extended setup that takes care of conan dependencies.

    :param conanfile: Path to the folder with the conanfile.[py|txt]. By default the root
        is assumed. The conanfile can be used to define the dependencies.
        Alternatively, you can also use `conan_requirements` to define
        the conan dependencies without a conanfile. This option is
        exclusive. If you define `conan_requirements`, this option is
        ignored.
    :param conan_recipes: List of paths to further conan recipes. The conan package index
        is far from perfect, so often you need to build your own recipes. You don't
        always want to upload those, so this argument gives you the option to integrate
        local recipes. Just the path to the folder containing the `conanfile.py`.
    :param conan_requirements: Instead of providing a conanfile, you can simply state
        the dependencies here. E.g. `["fmt/[>=10.0.0]"]` to add fmt in version >=10.0.0.
    :param conan_profile_settings: Overwrite conan profile settings. Sometimes necessary
        because of ABI-problems, etc.
    :param wrapped_setup: The setup-method that is going to be wrapped. This would allow
        you to extend already extended setup functions. By default, it is the `setup`
        of `skbuild`, which extends the `setup` of `setuptools`.
    :param conan_output_folder: The folder where conan will write the generated files.
        No real reason to change it unless the default creates conflicts with some other
        tool.
    :param cmake_args: This is actually an argument of `skbuild` but we will extend it.
        It hands cmake custom arguments. We use it to tell cmake about the conan modules.
    :param conan_profile: The name of the conan profile to use. By default, it is
        `skbuild_conan_py`. This profile is created automatically and should work for
        most cases. If you need to change it, you can do so by editing
        `~/.conan2/profiles/skbuild_conan_py`.
    :param conan_env: Environment variables that are used for the conan calls. By
        default it will override `CC` and `CXX` with empty strings. This is necessary
        to work around problems with anaconda, but it should not cause any problems
        with other setups. You could define `CONAN_HOME` to `./conan/cache` to use
        a local cache and not install anything to the user space.
    :param kwargs: The arguments for the underlying `setup`. Please check the
        documentation of `skbuild` and `setuptools` for this.
    :return: The returned values of the wrapped setup.
    """

    # Workaround for mismatching ABI with GCC on Linux
    conan_profile_settings = conan_profile_settings if conan_profile_settings else {}
    cmake_args = cmake_args if cmake_args else []
    if platform.system( )== "Linux" and "compiler.libcxx" not in conan_profile_settings:
        print(
            '[skbuild-conan] Using workaround and setting "compiler.libcxx=libstdc++11"'
        )
        conan_profile_settings = conan_profile_settings.copy()
        conan_profile_settings["compiler.libcxx"] = "libstdc++11"
    # Workaround for Windows and MSVC
    if platform.system() == "Windows":
        # Setting the policy to NEW means:
        # CMAKE_MSVC_RUNTIME_LIBRARY is used to initialize the MSVC_RUNTIME_LIBRARY property on all targets.
        # If CMAKE_MSVC_RUNTIME_LIBRARY is not set, CMake defaults to choosing a runtime library value consistent with the current build type.
        print("[skbuild-conan] Using workaround for Windows and MSVC by enforcing policy CMP0091 to NEW")
        cmake_args += ["-DCMAKE_POLICY_DEFAULT_CMP0091=NEW"]
    try:
        conan_helper = ConanHelper(
            output_folder=conan_output_folder,
            local_recipes=conan_recipes,
            settings=conan_profile_settings,
            profile=conan_profile,
            env=conan_env,
        )
        conan_helper.install(path=conanfile, requirements=conan_requirements)
        cmake_args += conan_helper.cmake_args()
        
    except Exception as e:
        # Setup could not be completed. Give debugging information in red and abort.
        print(f"\033[91m[skbuild-conan] {e}\033[0m")
        print(
            "\033[91m[skbuild-conan] skbuild_conan failed to install dependencies.\033[0m"
        )
        print("There are several reasons why this could happen:")
        print(
            "1. A mistake by the developer of the package you are trying to install."
            + " Maybe a wrongly defined dependency?"
        )
        print("2. An unexpected conflict with an already existing conan configuration.")
        print("3. A rare downtime of the conan package index.")
        print(
            "4. A bug in skbuild_conan. Please report it at https://github.com/d-krupke/skbuild-conan/issues"
        )
        print(
            "5. Your system does not have a C++-compiler installed. Please install one."
        )
        print(
            "6. You conan profile is not configured correctly. "
            + f"Please check `~/.conan2/profiles/{conan_profile}`. "
            + "You can also try to just delete `./conan2/` to reset conan completely."
        )
        raise e
    print(
        "[skbuild-conan] Setup of conan dependencies finished. cmake args:", cmake_args
    )
    print(
        "[skbuild-conan] See https://github.com/d-krupke/skbuild-conan if you encounter problems."
    )
    return wrapped_setup(cmake_args=cmake_args, **kwargs)
