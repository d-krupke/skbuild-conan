import sys
import typing
import skbuild

from .conan_helper import ConanHelper


def setup(
    conanfile: str = ".",
    conan_recipes: typing.Optional[typing.List[str]] = None,
    conan_requirements: typing.Optional[typing.List[str]] = None,
    conan_output_folder=".conan",
    conan_profile_settings: typing.Optional[typing.Dict] = None,
    wrapped_setup: typing.Callable = skbuild.setup,
    cmake_args: typing.Optional[typing.List[str]] = None,
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
    :param kwargs: The arguments for the underlying `setup`. Please check the
        documentation of `skbuild` and `setuptools` for this.
    :return: The returned values of the wrapped setup.
    """

    # Workaround for mismatching ABI with GCC on Linux
    conan_profile_settings = conan_profile_settings if conan_profile_settings else {}
    if sys.platform == "linux" and "compiler.libcxx" not in conan_profile_settings:
        print(
            '[skbuild-conan] Using workaround and setting "compiler.libcxx=libstdc++11"'
        )
        conan_profile_settings = conan_profile_settings.copy()
        conan_profile_settings["compiler.libcxx"] = "libstdc++11"
    try:
        conan_helper = ConanHelper(
            output_folder=conan_output_folder,
            local_recipes=conan_recipes,
            settings=conan_profile_settings,
        )
        conan_helper.install(path=conanfile, requirements=conan_requirements)
        cmake_args = cmake_args if cmake_args else []
        cmake_args += conan_helper.cmake_args()
    except Exception as e:
        # Setup could not be completed. Give debugging information in red and abort.
        print(f"\033[91m[skbuild-conan] {e}\033[0m")
        print(
            "\033[91m[skbuild-conan] skbuild_conan failed to install dependencies.\033[0m"
        )
        print("There are several reasons why this could happen:")
        print(
            "1. A mistake by the developer of the package you are trying to install. Maybe a wrongly defined dependency?"
        )
        print("2. An unexpected conflict with an already existing conan configuration.")
        print("3. A rare downtime of the conan package index.")
        print(
            "4. A bug in skbuild_conan. Please report it at https://github.com/d-krupke/skbuild-conan/issues"
        )
        print(
            "5. Your system does not have a C++-compiler installed. Please install one."
        )
        raise e
    print("[skbuild-conan] Setup of conan dependencies finished. cmake args:", cmake_args)
    print(
        "[skbuild-conan] See https://github.com/d-krupke/skbuild-conan if you encounter problems."
    )
    return wrapped_setup(cmake_args=cmake_args, **kwargs)
