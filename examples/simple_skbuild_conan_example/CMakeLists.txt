# Here we define how to compile the C++-part. It does not differ from a normal
# CMakeLists for scitkit-build. All the magic for conan is internally added via
# command line arguments.

# ======================================
# Boilerplate C++ stuff you see in most cmakes
# --------------------------------------
cmake_minimum_required(VERSION 3.23)
option(CXX "enable C++ compilation" ON)
if(CXX)
  enable_language(CXX)
endif()
project(simple_skbuild_conan_example CXX)
# Using C++-17 (most features with good support at 2022)
set(CMAKE_CXX_STANDARD 17)
# The code needs to be compiled as PIC to build the shared lib for python.
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
# Workaround for some Macs (if I remember correctly)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
# Define CMAKE_INSTALL_xxx: LIBDIR, INCLUDEDIR
include(GNUInstallDirs)
# ========================================

# ==================================
# C++-dependencies
# ----------------------------------
find_package(fmt REQUIRED)
# ==================================

# ====================================================
# Download PyBind11 I usually prefer to use CPM for this, but to keep it simple,
# we are going to use FetchContent.
# ----------------------------------------------------
include(FetchContent)
FetchContent_Declare(
  pybind11
  URL https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.tar.gz
  URL_HASH
    SHA256=e08cb87f4773da97fa7b5f035de8763abc656d87d5773e62f6da0587d1f0ec20)
FetchContent_MakeAvailable(pybind11)
# =====================================================

# ====================================================
# PyBind11 Bindings
# ----------------------------------------------------
# the name of the module must equal the one in the .cpp-file!
pybind11_add_module(_bindings src/simple_skbuild_conan_example/_bindings.cpp)
# link to the library
target_link_libraries(_bindings PRIVATE fmt::fmt)

# just more extensive warnings to spot bugs
target_compile_options(
  _bindings PRIVATE "$<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall>")
target_compile_definitions(_bindings PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)
# move the binary `_bindings` to its destination in the Python module
install(TARGETS _bindings DESTINATION ./src/simple_skbuild_conan_example/)
# ========================================================
