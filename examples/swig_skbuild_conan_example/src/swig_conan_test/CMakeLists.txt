set(target swig_conan_test)

find_package(
  Python3
  COMPONENTS Development
  REQUIRED)
find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

find_package(PythonLibs)
include_directories(${PYTHON_INCLUDE_PATH})

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

set(SWIG_SOURCES swig_conan_test.i)
set(CMAKE_SWIG_FLAGS -DTest)

set_property(SOURCE ${target}.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE ${target}.i PROPERTY SWIG_MODULE_NAME swig_conan_test)

swig_add_library(
  ${target}
  LANGUAGE python
  SOURCES ${SWIG_SOURCES})
set_property(TARGET ${target} PROPERTY SWIG_INCLUDE_DIRECTORIES
                                       ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(${target} ${PYTHON_LIBRARIES} mylib)

install(TARGETS ${target} DESTINATION python)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/swig_conan_test.py"
        DESTINATION python)
