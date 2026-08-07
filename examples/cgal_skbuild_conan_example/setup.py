from skbuild_conan import setup
from setuptools import find_packages

setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    name="cgal_skbuild_conan_example",
    version="0.1.0",
    packages=find_packages("src"),  # Include all packages in `./src`.
    package_dir={"": "src"},  # The root for our python package is in `./src`.
    python_requires=">=3.7",  # lowest python version supported.
    install_requires=[],  # Python Dependencies
    conan_recipes=["./conans/cgal_custom"],  # Conan Recipes
    conan_requirements=["fmt/[>=10.0.0]", "cgal/[>=6.0]"],  # C++ Dependencies
    # CGAL 6 requires C++17. Do not rely on the compiler's default standard,
    # which can be as low as C++14 on some platforms (notably Windows/MSVC).
    # This setting also applies to the local recipe in `conan_recipes`.
    # See https://github.com/d-krupke/skbuild-conan#setting-the-c-standard
    conan_profile_settings={"compiler.cppstd": "17"},
    cmake_minimum_required_version="3.23",
    # Use a project-local conan cache instead of the user-wide `~/.conan2`, so
    # this example never touches your normal cache. The path is relative to the
    # directory you build from. Note that nothing is shared with your other
    # projects, so the first build downloads and compiles everything (gmp, mpfr,
    # boost, CGAL) from scratch. Drop this line to use the shared cache.
    conan_env={"CONAN_HOME": "./conan/cache"},
)
