import sys
import typing
import os
import skbuild
import platform
from .conan_helper import ConanHelper
from .logging_utils import Logger, LogLevel
from .exceptions import (
    SkbuildConanError,
    ConanVersionError,
    ConanProfileError,
    ConanDependencyError,
    ConanNetworkError,
    ValidationError,
)


def validate_setup_args(
    conanfile: str,
    conan_recipes: typing.Optional[typing.List[str]],
    conan_requirements: typing.Optional[typing.List[str]],
) -> None:
    """
    Validate setup arguments before running expensive operations.

    Args:
        conanfile: Path to conanfile
        conan_recipes: List of local recipe paths
        conan_requirements: List of requirement strings

    Raises:
        ValidationError: If validation fails
    """
    errors = []

    # Check conan_requirements format
    if conan_requirements:
        for req in conan_requirements:
            # Conan 2.x requirements must include a version: package/version
            # Optionally with version ranges: package/[>=1.0]
            # Optionally with user/channel: package/version@user/channel
            if not req or '/' not in req:
                errors.append(
                    f"Invalid requirement format: '{req}'. "
                    f"Expected format: 'package/version', 'package/[>=version]', "
                    f"or 'package/version@user/channel'. "
                    f"See https://docs.conan.io/2/reference/conanfile/methods/requirements.html"
                )

    # Check paths exist
    if conanfile != '.' and not os.path.exists(conanfile):
        errors.append(f"Conanfile path does not exist: {conanfile}")

    if conan_recipes:
        for recipe in conan_recipes:
            if not os.path.exists(recipe):
                errors.append(f"Recipe path does not exist: {recipe}")
            else:
                conanfile_path = os.path.join(recipe, 'conanfile.py')
                if not os.path.exists(conanfile_path):
                    errors.append(
                        f"Recipe path missing conanfile.py: {recipe}"
                    )

    # Check mutually exclusive options
    if conan_requirements and conanfile != '.':
        errors.append(
            "Cannot specify both conan_requirements and conanfile. "
            "Use conan_requirements for simple cases or conanfile for complex setups."
        )

    if errors:
        error_msg = "\n  - " + "\n  - ".join(errors)
        raise ValidationError(error_msg)


def _detect_verbosity_from_args() -> typing.Optional[LogLevel]:
    """
    Detect if --verbose or --quiet flags are present in command line args.

    This allows skbuild-conan to honor pip install --verbose or setup.py --verbose
    without requiring users to set SKBUILD_CONAN_LOG_LEVEL.

    Returns:
        LogLevel if detected from args, None otherwise (will use env var or default)
    """
    # Check for pip/setup.py verbosity flags
    # pip uses --verbose/-v (can be repeated: -vv, -vvv)
    # setup.py also uses --verbose
    verbose_count = 0
    quiet = False

    for arg in sys.argv[1:]:
        if arg in ('--verbose', '-v'):
            verbose_count += 1
        elif arg.startswith('-v'):
            # Count multiple v's: -vv, -vvv
            verbose_count += arg.count('v')
        elif arg in ('--quiet', '-q'):
            quiet = True

    # Map verbosity to log levels
    if quiet:
        return LogLevel.QUIET
    elif verbose_count >= 2:
        return LogLevel.DEBUG  # -vv or more -> debug
    elif verbose_count == 1:
        return LogLevel.VERBOSE  # -v -> verbose

    return None  # No flags detected, will use env var or default


def setup(
    conanfile: str = ".",
    conan_recipes: typing.Optional[typing.List[str]] = None,
    conan_requirements: typing.Optional[typing.List[str]] = None,
    conan_output_folder=".conan",
    conan_profile_settings: typing.Optional[typing.Dict] = None,
    wrapped_setup: typing.Callable = skbuild.setup,
    cmake_args: typing.Optional[typing.List[str]] = None,
    conan_profile: str = "skbuild_conan_py",
    conan_env: typing.Optional[typing.Dict[str, str]] = None,
    conan_log_level: typing.Optional[LogLevel] = None,
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
    :param conan_log_level: The logging level for conan operations. If None, reads
        from environment variable SKBUILD_CONAN_LOG_LEVEL (quiet/normal/verbose/debug).
        Defaults to NORMAL. Use LogLevel.QUIET for minimal output, LogLevel.DEBUG for
        full transparency.
    :param kwargs: The arguments for the underlying `setup`. Please check the
        documentation of `skbuild` and `setuptools` for this.
    :return: The returned values of the wrapped setup.
    """

    # Auto-detect verbosity from command-line args if not explicitly set
    if conan_log_level is None:
        detected_level = _detect_verbosity_from_args()
        if detected_level is not None:
            conan_log_level = detected_level

    logger = Logger(conan_log_level)

    # Validate arguments early to catch errors before expensive operations
    try:
        validate_setup_args(conanfile, conan_recipes, conan_requirements)
    except ValidationError as e:
        logger.error(e.detailed_message())
        sys.exit(1)

    build_type = parse_args()

    # Default conan_env to override CC/CXX (workaround for anaconda)
    if conan_env is None:
        conan_env = {"CC": "", "CXX": ""}

    # Workaround for mismatching ABI with GCC on Linux
    conan_profile_settings = conan_profile_settings if conan_profile_settings else {}
    cmake_args = cmake_args if cmake_args else []
    if platform.system() == "Linux" and "compiler.libcxx" not in conan_profile_settings:
        logger.verbose('Using ABI workaround: setting "compiler.libcxx=libstdc++11"')
        conan_profile_settings = conan_profile_settings.copy()
        conan_profile_settings["compiler.libcxx"] = "libstdc++11"
    # Workaround for Windows and MSVC
    if platform.system() == "Windows":
        # Setting the policy to NEW means:
        # CMAKE_MSVC_RUNTIME_LIBRARY is used to initialize the MSVC_RUNTIME_LIBRARY property on all targets.
        # If CMAKE_MSVC_RUNTIME_LIBRARY is not set, CMake defaults to choosing a runtime library value consistent with the current build type.
        logger.verbose("Using MSVC workaround: enforcing policy CMP0091 to NEW")
        cmake_args += ["-DCMAKE_POLICY_DEFAULT_CMP0091=NEW"]
    try:
        conan_helper = ConanHelper(
            output_folder=conan_output_folder,
            local_recipes=conan_recipes,
            settings=conan_profile_settings,
            profile=conan_profile,
            env=conan_env,
            build_type=build_type,
            log_level=conan_log_level,
        )
        conan_helper.install(path=conanfile, requirements=conan_requirements)
        cmake_args += conan_helper.cmake_args()

        # Generate dependency report for transparency
        report = conan_helper.generate_dependency_report(requirements=conan_requirements)
        if logger.log_level >= LogLevel.VERBOSE:
            logger.info("\n" + report)

    except ConanVersionError as e:
        logger.error(e.detailed_message())
        sys.exit(1)
    except ConanProfileError as e:
        logger.error(e.detailed_message())
        sys.exit(1)
    except ConanDependencyError as e:
        logger.error(e.detailed_message())
        sys.exit(1)
    except ConanNetworkError as e:
        logger.error(e.detailed_message())
        logger.warning("Network errors are often transient. Try running again.")
        sys.exit(1)
    except SkbuildConanError as e:
        # Other skbuild-conan errors
        logger.error(e.detailed_message())
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\nBuild interrupted by user")
        sys.exit(130)
    except Exception as e:
        # Unexpected error - show full context
        logger.error(f"\nUnexpected error during setup: {e}")
        logger.error("\nThis is likely a bug. Please report it at:")
        logger.error("https://github.com/d-krupke/skbuild-conan/issues")
        logger.debug(f"\nFull error details:", exc_info=True)
        raise

    logger.success("Conan dependencies setup completed successfully")
    logger.verbose(f"CMake arguments: {cmake_args}")
    logger.info("See https://github.com/d-krupke/skbuild-conan for documentation")
    return wrapped_setup(cmake_args=cmake_args, **kwargs)


def parse_args() -> str:
    """
    This function parses the command-line arguments ``sys.argv`` and returns
    build_type as a string. Release or Debug.

    This is consistent with the interface of the underlying scikit-build, which
    will also read this argument and change its behavior accordingly.
    """

    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--build-type",
        default="Release",
        choices=["Release", "Debug"],
        help="specify the CMake build type (e.g. Debug or Release)",
    )

    args, _ = parser.parse_known_args()
    return args.build_type
