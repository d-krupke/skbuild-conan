# Simple Example

This simple example shows how to use skbuild-conan to
easily create bindings to C++-code that uses some further
library (fmt in this case).

You can build and install it with

```bash
pip install .
```

Run the tests to make sure everything works by

```bash
pytest -s tests
```

The only two files that differ to a normal scikit-build project
are
1. `pyproject.toml` that defines `skbuild-conan` as requirement
2. `setup.py` that defines the C++ dependency via `conan_requirements=["fmt/[>=10.0.0]"],`

You can find examples for pure scikit-build examples [here](https://github.com/scikit-build/scikit-build-sample-projects/tree/master/projects). 