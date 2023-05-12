# skbuild-conan: A conan extension for scikit-build

[PyBind11](https://github.com/pybind/pybind11) and
[scitkit-build](https://github.com/scikit-build/scikit-build)
enable us to easily write native C++-modules for Python.
However, you get problems if your C++-code has dependencies.
This extension tries to make defining C++-dependencies as easy
as defining the Python-dependencies. This way you can easily
add any C++-library that has a conan recipe to your Python-project.

This project originates from [our](https://www.ibr.cs.tu-bs.de/alg/) need to use complex C++-libraries
in Python projects and missing any nice option to include C++-dependencies.
For a few projects, we wrote individual code to fetch the dependencies
or just added instructions on how to install them (which of course
can scare pure Python users).

**This project is currently just nice interface to hacks we accumulated. We try to make it as universal and robust as possible as we rely on this for multiple projects, but we are working fast-paced and will quickly abandon this tool once there is something better.**

We (TU Braunschweig, Algorithms Group) are not affiliated with scikit-build or conan.


## Installation

TBD

## Usage

The usage is very similar to scitkit-build (and setuptools).
We just added a few additional arguments to `setup()`.

See [how to use scikit-build](https://scikit-build.readthedocs.io/en/latest/usage.html#example-of-setup-py-cmakelists-txt-and-pyproject-toml) first, as this is just a small extension to it.

