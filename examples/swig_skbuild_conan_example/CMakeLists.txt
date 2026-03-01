cmake_minimum_required(VERSION 3.15)
project(swig_conan_test CXX)

cmake_policy(SET CMP0078 NEW)

add_subdirectory(src/mylib)
add_subdirectory(src/swig_conan_test)
