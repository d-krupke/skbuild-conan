#include "swig_conan_test.h"
#include <iostream>

void swig_conan_test() {
#ifdef NDEBUG
  std::cout << "swig_conan_test/0.0.1: Hello World Release!\n";
#else
  std::cout << "swig_conan_test/0.0.1: Hello World Debug!\n";
#endif
}

void swig_conan_test2() { std::cout << "swig_conan_test2\n"; }
