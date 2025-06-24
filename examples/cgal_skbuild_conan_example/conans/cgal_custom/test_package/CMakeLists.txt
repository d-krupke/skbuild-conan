cmake_minimum_required(VERSION 3.23)
project(test_package LANGUAGES CXX)
enable_testing()
find_package(Eigen3 REQUIRED)
find_package(CGAL REQUIRED)
add_executable(cgal_test test_package.cpp)
target_link_libraries(cgal_test PUBLIC Eigen3::Eigen)
if(TARGET CGAL::CGAL)
    set(CGAL_TARGET CGAL::CGAL)
elseif(TARGET cgal::cgal)
    set(CGAL_TARGET cgal::cgal)
else()
    message(FATAL_ERROR "Could not find CGAL target (CGAL::CGAL or cgal::cgal)")
endif()

target_link_libraries(cgal_test PRIVATE ${CGAL_TARGET})
set_property(TARGET cgal_test PROPERTY CXX_STANDARD 14)
add_test(
  NAME run_cgal_test
  WORKING_DIRECTORY "${CMAKE_BINARY_DIR}"
  COMMAND cgal_test)
