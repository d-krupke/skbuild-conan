import os

from conan import ConanFile
from conan.tools import build
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualBuildEnv", "VirtualRunEnv"

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.configure()
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def test(self):
        cmake = self._configure_cmake()
        cmake.test()

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("eigen/3.3.9")
        self.requires(self.tested_reference_str)
