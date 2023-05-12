# skbuild-conan: A conan extension for scikit-build

[PyBind11](https://github.com/pybind/pybind11) and
[scitkit-build](https://github.com/scikit-build/scikit-build)
enable us to easily write native C++-modules for Python.
However, you get problems if your C++-code has dependencies.
This extension tries to make defining C++-dependencies as easy
as defining the Python-dependencies. This way you can easily
add any C++-library that has a conan recipe to your Python-project.

This project originates from [our](https://www.ibr.cs.tu-bs.de/alg/) need to use complex
C++-libraries
in Python projects and missing any nice option to include C++-dependencies.
For a few projects, we wrote individual code to fetch the dependencies
or just added instructions on how to install them (which of course
can scare pure Python users).

**This project is currently just nice interface to hacks we accumulated. We try to make it
as universal and robust as possible as we rely on this for multiple projects, but we are
working fast-paced and will quickly abandon this tool once there is something better.**

We (TU Braunschweig, Algorithms Group) are not affiliated with scikit-build or conan.

## Installation

You can simply add `"skbuild_conan@git+https://github.com/d-krupke/skbuild-conan.git",`
to `requires=[...]` in `pyproject.toml`.
E.g. The `pyproject.toml` could look like this

```toml
[build-system]
requires = [
    "conan>=2.0.0",
    "setuptools",
    "scikit-build>=0.17.3",
    "skbuild_conan@git+https://github.com/d-krupke/skbuild-conan.git",
    "cmake>=3.23",
    "ninja",
]
build-backend = "setuptools.build_meta"
```

If you want to use for example `setup.py build`, you need to
install `skbuild_conan` to your environment. You can do so
by ` pip install skbuild_conan@git+https://github.com/d-krupke/skbuild-conan.git`.
We will also add this tool to PyPI soon.

## Usage

The usage is very similar to scitkit-build (and setuptools).
We just added a few additional arguments to `setup()`.

See [how to use scikit-build](https://scikit-build.readthedocs.io/en/latest/usage.html#example-of-setup-py-cmakelists-txt-and-pyproject-toml)
first, as this is just a small extension to it.

The added options are

- `conanfile`: Path to the folder with the conanfile.[py|txt]. By default the root
  is assumed. The conanfile can be used to define the dependencies.
  Alternatively, you can also use `conan_requirements` to define
  the conan dependencies without a conanfile. This option is
  exclusive. If you define `conan_requirements`, this option is
  ignored.
- `conan_recipes`: List of paths to further conan recipes. The conan package index
  is far from perfect, so often you need to build your own recipes. You don't
  always want to upload those, so this argument gives you the option to integrate
  local recipes. Just the path to the folder containing the `conanfile.py`.
- `conan_requirements`: Instead of providing a conanfile, you can simply state
  the dependencies here. E.g. `["fmt/[>=10.0.0]"]` to add fmt in version >=10.0.0.
- `conan_profile_settings`: Overwrite conan profile settings. Sometimes necessary
  because of ABI-problems, etc.
- `wrapped_setup`: The setup-method that is going to be wrapped. This would allow
  you to extend already extended setup functions. By default, it is the `setup`
  of `skbuild`, which extends the `setup` of `setuptools`.
- `conan_output_folder`: The folder where conan will write the generated files.
  No real reason to change it unless the default creates conflicts with some other
  tool.
- `cmake_args`: This is actually an argument of `skbuild` but we will extend it.
  It hands cmake custom arguments. We use it to tell cmake about the conan modules.

An example usage could be as follows

```python
"""
This file instructs scitkit-build how to build the module. This is very close
to the classical setuptools, but wraps some things for us to build the native
modules easier and more reliable.

For a proper installation with `pip install .`, you additionally need a
`pyproject.toml` to specify the dependencies to load this `setup.py`.

You can use `python3 setup.py install` to build and install the package
locally, with verbose output. To build this package in place, which may be
useful for debugging, use `python3 setup.py develop`. This will build
the native modules and move them into your source folder.

The setup options are documented here:
https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
"""
from setuptools import find_packages
from skbuild_conan import setup


def readme():
    # Simply return the README.md as string
    with open("README.md") as file:
        return file.read()


setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    # ~~~~~~~~~ BASIC INFORMATION ~~~~~~~~~~~
    name="cetsp-bnb2",
    version="0.1.0",  # TODO: Use better approach for managing version number.
    # ~~~~~~~~~~~~ CRITICAL PYTHON SETUP ~~~~~~~~~~~~~~~~~~~
    # This project structures defines the python packages in a subfolder.
    # Thus, we have to collect this subfolder and define it as root.
    packages=find_packages("pysrc"),  # Include all packages in `./python`.
    package_dir={"": "pysrc"},  # The root for our python package is in `./python`.
    python_requires=">=3.7",  # lowest python version supported.
    install_requires=[
        # requirements necessary for basic usage (subset of requirements.txt)
        "chardet>=4.0.0",
        "networkx>=2.5.1",
        "requests>=2.25.1",
    ],
    # ~~~~~~~~~~~ CRITICAL CMAKE SETUP ~~~~~~~~~~~~~~~~~~~~~
    # Especially LTS systems often have very old CMake version (or none at all).
    # Defining this will automatically install locally a working version.
    cmake_minimum_required_version="3.17",
    #
    # By default, the `install` target is built (automatically provided).
    # To compile a specific target, use the following line.
    # Alternatively, you can use `if(NOT SKBUILD) ... endif()` in CMake, to
    # remove unneeded parts for packaging (like tests).
    # cmake_install_target = "install"
    #
    # In the cmake you defined by install(...) where to move the built target.
    # This is critical als only targets with install will be used by skbuild.
    # This should be relative paths to the project root, as you don't know
    # where the package will be packaged. You can change the root for the
    # install-paths with the following line. Note that you can also access
    # the installation root (including this modification) in cmake via
    # `CMAKE_INSTALL_PREFIX`. If your package misses some binaries, you
    # probably messed something up here or in the `install(...)` path.
    # cmake_install_dir = ".",
    # |-----------------------------------------------------------------------|
    # | If you are packing foreign code/bindings, look out if they do install |
    # | targets in global paths, like /usr/libs/. This could be a problem.    |
    # |-----------------------------------------------------------------------|
    #
    # Some CMake-projects allow you to configure it using parameters. You
    # can specify them for this Python-package using the following line.
    # cmake_args=[]
    # There are further options, but you should be fine with these above.
    # ~~~~~~~~ Conan ~~~~~~~~~~~~~
    conan_recipes=["./cmake/conan/gurobi_public/", "./cmake/conan/cgal_custom"],
)
```

## Contribution

We are happy about any contribution and also about reported issues.
Sometimes it can take some time before we are able to take care
of something, as we need to prioritize quite often.
