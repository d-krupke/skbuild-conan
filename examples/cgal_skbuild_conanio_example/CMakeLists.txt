# This is the root file for CMake, which is used to define the native part of
# the project. It is completely independent of the Python-part and can actually
# be used just to build a C++-library.
cmake_minimum_required(VERSION 3.23)
option(CXX "enable C++ compilation" ON)

if(CXX)
  enable_language(CXX)
endif()
project(cgal_skbuild_conan_example CXX) # Feel free to add more project
                                        # information
set(CMAKE_CXX_STANDARD 17) # Using C++-17 (most features with good support at
                           # 2022)
set(CMAKE_POSITION_INDEPENDENT_CODE ON) # The code needs to be compiled as PIC
                                        # to build the shared lib for python.
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# CPM Dependencies ~~~~~~~~~~~~~~~~ CPM allows us to include some simple
# dependencies without much fuss. Great default, for everything more
# complicated, uses conan. Why not always use conan? CPM works without any
# interaction (conan needs to be called externally). CPM also has no problems
# with install PyBind11 (which conan has at the time). If the dependency has
# complicated dependencies on its own or is slow to compile, better use conan.
# Check out https://github.com/cpm-cmake/CPM.cmake
include(./cmake/CPM.cmake) # Package manager for simple requirements.

# cpmaddpackage("gh:fmtlib/fmt#9.1.0") # fmt for nice strings

# Define the rest of the project ~~~~~~~~~~~~~~~
add_subdirectory(src)
