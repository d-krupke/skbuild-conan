from skbuild_conan import setup
from setuptools import find_packages

setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    name="simple_skbuild_conan_example",
    version="0.1.0",
    packages=find_packages("src"),  # Include all packages in `./src`.
    package_dir={"": "src"},  # The root for our python package is in `./src`.
    python_requires=">=3.7",  # lowest python version supported.
    install_requires=[""],  # Python Dependencies
    conan_requirements=["fmt/[>=10.0.0]"],  # C++ Dependencies
    cmake_minimum_required_version="3.23",
)
