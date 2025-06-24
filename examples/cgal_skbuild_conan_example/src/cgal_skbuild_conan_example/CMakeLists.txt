# Created by the script cgal_create_cmake_script This is the CMake script for
# compiling a CGAL application.
cpmaddpackage("gh:pybind/pybind11@2.13.6") # pybind11, essential
find_package(CGAL REQUIRED)
find_package(fmt REQUIRED)

pybind11_add_module(_cgal_bindings ./_cgal_bindings.cpp)

if(TARGET CGAL::CGAL)
    set(CGAL_TARGET CGAL::CGAL)
elseif(TARGET cgal::cgal)
    set(CGAL_TARGET cgal::cgal)
else()
    message(FATAL_ERROR "Could not find CGAL target (CGAL::CGAL or cgal::cgal)")
endif()

target_link_libraries(_cgal_bindings PUBLIC fmt::fmt  ${CGAL_TARGET})

# enable compilation warnings
target_compile_options(
  _cgal_bindings PRIVATE "$<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall>")
target_compile_definitions(_cgal_bindings
                           PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)

# move the compiled module to this folder. You can check with `python setup.py
# build` how the package will look like and if the module is moved to the right
# location.
install(TARGETS _cgal_bindings DESTINATION ./src/cgal_skbuild_conan_example)
