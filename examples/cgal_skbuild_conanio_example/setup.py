from setuptools import find_packages

from skbuild_conan import setup

setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    name="cgal_skbuild_conanio_example",
    version="0.1.0",
    packages=find_packages("src"),  # Include all packages in `./src`.
    package_dir={"": "src"},  # The root for our python package is in `./src`.
    python_requires=">=3.7",  # lowest python version supported.
    install_requires=[],  # Python Dependencies
    conan_requirements=["fmt/[>=10.0.0]", "cgal/[>=6.0]"],  # C++ Dependencies
    # CGAL 6 requires C++17. Do not rely on the compiler's default standard,
    # which can be as low as C++14 on some platforms (notably Windows/MSVC).
    # See https://github.com/d-krupke/skbuild-conan#setting-the-c-standard
    conan_profile_settings={"compiler.cppstd": "17"},
    cmake_minimum_required_version="3.23",
)
