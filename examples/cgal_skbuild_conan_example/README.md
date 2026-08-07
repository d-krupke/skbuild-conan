# Example of using CGAL (custom recipe) in Python using PyBind11 and skbuild_conan

This is a minimal example of how to use CGAL in Python using PyBind11 and skbuild_conan.
It provides CGAL via a custom conan recipe.

Just run `pip install .` to install the package.

This example also demonstrates `conan_env={"CONAN_HOME": "./conan/cache"}`, which
keeps everything conan builds inside `./conan/cache` instead of your user-wide
`~/.conan2`. That isolation has a price: nothing is shared with your other
projects, so the first build compiles gmp, mpfr, boost and CGAL from scratch and
takes a while. Remove that argument from `setup.py` to use the shared cache.

It just binds CGAL polygons with the EPEC-kernel, but does not do anything with it.

There may be issues with the target name `cgal::cgal`, which may have to be changed to `CGAL::CGAL` for some systems. This should not be an issue with the new CGAL conan recipe from the conan-center (which isn't used here!).
See the other CGAL example for more details.

> Use the original CGAL conan recipe from the conan-center instead of this custom recipe if possible.
> This example is just to show how to use a custom recipe, in case there is none or it is outdated.
