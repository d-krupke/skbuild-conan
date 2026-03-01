set(target mylib)

set(SOURCES swig_conan_test.cpp)

add_library(${target} ${SOURCES})
target_include_directories(${target} PUBLIC ../../include)

set_target_properties(${target} PROPERTIES PUBLIC_HEADER
                                           "../../include/swig_conan_test.h")
install(TARGETS ${target})
