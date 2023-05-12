# Here we define how to compile the C++-part.

# ======================================
# Boilerplate C++ stuff
# --------------------------------------
cmake_minimum_required(VERSION 3.23)
option(CXX "enable C++ compilation" ON)
if(CXX)
  enable_language(CXX)
endif()
project(simple_skbuild_conan_example CXX)
set(CMAKE_CXX_STANDARD 17) # Using C++-17 (most features with good support at
                           # 2022)
set(CMAKE_POSITION_INDEPENDENT_CODE ON) # The code needs to be compiled as PIC
                                        # to build the shared lib for python.
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE) # Workaround for some Macs (I
                                            # believe)
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
  URL https://github.com/pybind/pybind11/archive/refs/tags/v2.9.2.tar.gz
  URL_HASH
    SHA256=6bd528c4dbe2276635dc787b6b1f2e5316cf6b49ee3e150264e455a0d68d19c1)
FetchContent_MakeAvailable(pybind11)
# =====================================================

# ====================================================
# PyBind11 Bindings
# ----------------------------------------------------
pybind11_add_module(_bindings src/simple_skbuild_conan_example/_bindings.cpp)
target_link_libraries(_bindings PRIVATE fmt::fmt)

target_compile_options(
  _bindings PRIVATE "$<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall>")
target_compile_definitions(_bindings PRIVATE DOCTEST_CONFIG_DISABLE
                                             PYBIND11_DETAILED_ERROR_MESSAGES)
install(TARGETS _bindings DESTINATION ./src/simple_skbuild_conan_example/)
# ========================================================
