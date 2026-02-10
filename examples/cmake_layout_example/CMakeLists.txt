cmake_minimum_required(VERSION 3.23)
option(CXX "enable C++ compilation" ON)
if(CXX)
  enable_language(CXX)
endif()
project(cmake_layout_example CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
include(GNUInstallDirs)

# C++ dependency from conan
find_package(fmt REQUIRED)

# Download pybind11
include(FetchContent)
FetchContent_Declare(
  pybind11
  URL https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.tar.gz
  URL_HASH
    SHA256=e08cb87f4773da97fa7b5f035de8763abc656d87d5773e62f6da0587d1f0ec20)
FetchContent_MakeAvailable(pybind11)

# PyBind11 bindings
pybind11_add_module(_bindings src/cmake_layout_example/_bindings.cpp)
target_link_libraries(_bindings PRIVATE fmt::fmt)
target_compile_options(
  _bindings PRIVATE "$<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall>")
target_compile_definitions(_bindings PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)
install(TARGETS _bindings DESTINATION ./src/cmake_layout_example/)
