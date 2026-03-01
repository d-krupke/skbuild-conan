%module swig_conan_test

#if SWIG_VERSION == 0x040400

%{
/* Put header files here or function declarations like below */
extern void swig_conan_test();
%}

extern void swig_conan_test();

#else

%{
/* Put header files here or function declarations like below */
extern void swig_conan_test2();
%}

extern void swig_conan_test2();

#endif



// %{
// #include "swig_conan_test.h"
// %}

// Make SWIG look into this header:
// %include "swig_conan_test.h"
