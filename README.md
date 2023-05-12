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
from skbuild_conan import setup
from setuptools import find_packages

setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    name="simple_skbuild_conan_example",
    version="0.1.0",
    packages=find_packages("src"),  # Include all packages in `./src`.
    package_dir={"": "src"},  # The root for our python package is in `./src`.
    python_requires=">=3.7",  # lowest python version supported.
    install_requires=[],  # Python Dependencies
    conan_requirements=["fmt/[>=10.0.0]"],  # C++ Dependencies
    cmake_minimum_required_version="3.23",
)
```

See [./examples/simple_skbuild_conan_example](./examples/simple_skbuild_conan_example)
for a full example.

## Contribution

We are happy about any contribution and also about reported issues.
Sometimes it can take some time before we are able to take care
of something, as we need to prioritize quite often.

## Changelog

* *0.1.3* Fixing bug if no settings are given.
* *0.1.2* Moved workaround into setup to make it more explicit.
* *0.1.1* First tested and apparently working version.
