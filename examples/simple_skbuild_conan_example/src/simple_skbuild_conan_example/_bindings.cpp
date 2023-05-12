#include <pybind11/pybind11.h>
#include <fmt/core.h>
#include <string>

std::string add(int i, int j) {
    return fmt::format("{}+{}={}", i, j, i+j);
}

PYBIND11_MODULE(_bindings, m) {
    m.doc() = "Simple example"; // optional module docstring
    m.def("add", &add, "A function that adds two numbers");
}