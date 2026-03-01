from skbuild_conan import setup

setup(
    name="swig_skbuild_conan_example",
    version="0.0.1",
    description="a minimal example package (cpp version)",
    author="The scikit-build team",
    license="MIT",
    python_requires=">=3.8",
    conanfile="./conanfile.py",
    cmake_source_dir="./",
)
