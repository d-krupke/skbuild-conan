# Example of using CGAL (original recipe) in Python using PyBind11 and skbuild_conan

This example shows how to implement CGAL-based algorithms in Python using PyBind11 and skbuild_conan.
It uses the original CGAL conan recipe, which is available on conan-center.
There is an other example that uses a custom recipe because the original recipe had some delay in being updated for conan2.

You can build the package with:

```bash
pip install .
```

> If you just want to use CGAL in Python, you should use [cgalpy](https://bitbucket.org/taucgl/cgal-python-bindings/src/master/) instead of this example.
> cgalpy is not only pretty complete, but also more efficient. This example is for the case where you want to do
> most of the work in C++ and just call it from Python.