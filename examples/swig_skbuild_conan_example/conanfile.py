from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout


class SwigConanTestConan(ConanFile):
    name = "swig_conan_test"
    version = "0.0.1"

    # Optional metadata
    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of SwigConanTest here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"

    options = {"shared": [True, False], "fPIC": [True, False], "test": [True, False]}

    default_options = {"shared": False, "fPIC": True, "test": False}

    # Sources are located in the same place as this recipe, copy them to the recipe
    exports_sources = "CMakeLists.txt", "src/*", "include/*"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    # def requirements(self):
    #     self.requires("swig/4.1.0")

    # def system_requirements(self):
    #     # Python.h required by swig for python wrapper generation and build
    #     Apt(self).install(["libpython-dev"], update=True)
    #     Yum(self).install(["python3-devel"])
    #     Dnf(self).install(["python3-devel"])

    def build_requirements(self):
        self.tool_requires("cmake/[~3.25.0]")
        # self.tool_requires("ninja/[~1.11.0]")
        # self.tool_requires("ccache/[~4.6]")
        # self.tool_requires("swig/4.1.0")
        self.tool_requires("swig/4.1.0")
        if self.options.test:
            self.tool_requires("gtest/1.12.1")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        cmake = CMakeDeps(self)
        cmake.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build(cli_args=["-v"])
        # TODO: add some tests
        if self.options.test:
            cmake.test()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        # Add cpack to generate deb and rpm packages
        # TODO: study https://docs.conan.io/en/latest/reference/generators/deploy.html
        # TODO: study cpack

        # self.run("cpack")

    def imports(self):
        self.copy("swig_conan_test.py", dst="src/swig_conan_test/", src="python/")
        # self.copy("*.dylib*", dst=dest, src="lib")

    def package_info(self):
        self.cpp_info.libs = ["mylib"]

    def package_id(self):
        del self.info.options.test
