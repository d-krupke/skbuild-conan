# skbuild-conan: A conan extension for scikit-build

![PyPI](https://img.shields.io/pypi/v/skbuild-conan)
![License](https://img.shields.io/github/license/d-krupke/skbuild-conan)

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

**This project is currently just a nice interface to hacks we accumulated. We try to make it
as universal and robust as possible as we rely on this for multiple projects, but we are
working fast-paced and will quickly abandon this tool once there is something better.**

We (TU Braunschweig, Algorithms Group) are not affiliated with scikit-build or conan.

## Installation

You can simply add `"skbuild_conan",`
to `requires=[...]` in `pyproject.toml`.
E.g. The `pyproject.toml` could look like this

```toml
[build-system]
requires = [
    "conan>=2.0.0",
    "setuptools",
    "scikit-build>=0.17.3",
    "skbuild-conan",
    "cmake>=3.23",
    "ninja",
]
build-backend = "setuptools.build_meta"
```

If you want to use for example `setup.py build`, you need to
install `skbuild_conan` to your environment. You can do so
by ` pip install skbuild_conan`.

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
- `conan_profile`: The name of the conan profile to use. By default, it is
  `skbuild_conan_py`. This profile is created automatically and should work for
  most cases. If you need to change it, you can do so by editing
  `~/.conan2/profiles/skbuild_conan_py`.
- `conan_env`: Environment variables that are used for the conan calls. By
  default it will override `CC` and `CXX` with empty strings. This is necessary
  to work around problems with anaconda, but it should not cause any problems
  with other setups. You could define `CONAN_HOME` to `./conan/cache` to use
  a local cache and not install anything to the user space.

An example usage could be as follows

```python
from skbuild_conan import setup
from setuptools import find_packages

setup(  # https://scikit-build.readthedocs.io/en/latest/usage.html#setup-options
    name="simple_skbuild_conan_example",
    version="0.1.1",
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

## Examples

If you do not have any C++-dependencies, you can just use [scikit-build](https://github.com/scikit-build/scikit-build) which also provides a [set of examples](https://github.com/scikit-build/scikit-build-sample-projects/tree/master/projects).

### Simple Example with fmt

The example in [./examples/simple_skbuild_conan_example](./examples/simple_skbuild_conan_example) provides a minimal example of how to use fmt in Python using PyBind11 and skbuild_conan.
fmt is a nice library for formatting strings and is used by many other libraries.
Python, of course, comes with extensive inbuilt string formatting, thus, this example is not very useful.
However, it is a good starting point to understand how to use skbuild_conan with a simple external library.

### Complex Example with CGAL: Using CGAL in Python

Sometimes, your dependencies are significantly more complex.
For example, you may want to do some geometry processing and use CGAL.
CGAL is a very complex library with many dependencies, but also the most powerful library for geometric operations and often the only choice for many problems.
CGAL has a conan recipe, but it took a while until it received updates for conan2, such that we wrote our own recipe.
In the meantime, the official recipe was updated, but for the sake of the example, we will use our own recipe.
In case you are faced with the problem of an outdated conan recipe (or none at all), you can use the same trick.

See [./examples/cgal_skbuild_conan_example](./examples/cgal_skbuild_conan_example) for an example of how to use CGAL via a custom conan recipe in Python using PyBind11 and skbuild_conan.

Note that there is also the [cgalpy](https://bitbucket.org/taucgl/cgal-python-bindings/) project by my friends at TAU (which I visited for a few months in 2022/2023), which is a nearly complete and efficient wrapper of CGAL.
It may need some more documentation, but Efi put a lot of thought into efficiency and configurability.

## Common problems

> Feel free to copy these comments. Attribution is appreciated but not necessary.

### ABI problems: Undefined symbole `...__cxx1112basic_stringIcSt11char_...`

This problem should be automatically fixed. Please open an issue if you still encounter it.

See [https://docs.conan.io/1/howtos/manage_gcc_abi.html](https://docs.conan.io/1/howtos/manage_gcc_abi.html) for more details.

### glibcxx problems:

If you get an error such as

```
ImportError: /home/krupke/anaconda3/envs/mo310/bin/../lib/libstdc++.so.6: version `GLIBCXX_3.4.30' not found (required by /home/krupke/anaconda3/envs/mo310/lib/python3.10/site-packages/samplns/cds/_cds_bindings.cpython-310-x86_64-linux-gnu.so)
```

you are probably using conda (good!) but need to update glibcxx. Install the latest version by

```sh
conda install -c conda-forge libstdcxx-ng
```

In some cases, this still is not enough, especially if you are using a very up to date rolling-release distribution, such as Arch Linux, or if you installed `libstdcxx-ng` some time ago.
This could lead to the system having a slightly newer version of glibcxx than conda.
First try to upgrade `libstdcxx-ng` with

```sh
conda upgrade -c conda-forge --all
```

If this does not help, you can try to install g++ (caveat: Linux only, Mac OS needs clang) into your conda environment and use it to compile the package.

```sh
conda install -c conda-forge gxx_linux-64  # This should enforce a modern g++ version.
conda install -c conda-forge cxx-compiler  # This should make sure that the compiler is used.
```

Note that just the second command first may install an outdated g++ version (at least I observed that it installed gcc11 instead of gcc13, messing up my whole environment as this is too old).
When compiling from source, you probably should delete the `_skbuild`-folder and do a proper uninstall of the previous installation first.

### conan problems

If you encounter problems with conan, you can try to delete the conan profile and let it be recreated.

```sh
rm ~/.conan2/profiles/skbuild_conan_py
```

Maybe you can also just take a look at the file and see if conan detected your compiler correctly.
A proper profile on Linux should for example look like this (different for other systems):

```
[settings]
arch=x86_64
build_type=Release
compiler=gcc
compiler.cppstd=gnu17
compiler.libcxx=libstdc++11
compiler.version=13
os=Linux
```

If the problem persists, you can try to delete the conan cache.

```sh
rm -rf ~/.conan2
```

If you still encounter problems, please open an issue.

## Contribution

We are happy about any contribution and also about reported issues.
Sometimes it can take some time before we are able to take care
of something, as we need to prioritize quite often.

## Changelog

- _1.2.0_ Workaround for Windows and MSVC found by Ramin Kosfeld (TU Braunschweig).
- _1.1.1_ Fixing problem if the conan default profile has been renamed via environment variable.
- _1.1.0_ conan is now called directly. This is kind of hacky, but circumvents problems with conan not being in the path if only installed for build.
- _1.0.0_ Custom conan profile and workaround for anaconda problem.
- _0.2.0_ Improved logging.
- _0.1.4_ Fixing problem with paths that contain spaces. Switching back to manual versioning.
- _0.1.3_ Fixing bug if no settings are given.
- _0.1.2_ Moved workaround into setup to make it more explicit.
- _0.1.1_ First tested and apparently working version.
