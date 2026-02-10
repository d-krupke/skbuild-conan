#include <fmt/core.h>
#include <pybind11/pybind11.h>
#include <string>

std::string add(int i, int j) { return fmt::format("{}+{}={}", i, j, i + j); }

PYBIND11_MODULE(_bindings, m) {
  m.doc() = "cmake_layout example";
  m.def("add", &add, "A function that adds two numbers");
}
