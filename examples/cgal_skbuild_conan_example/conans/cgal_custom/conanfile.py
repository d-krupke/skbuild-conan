"""
This is a conan recipe for CGAL. It is a header only library, but has
dependencies on other libraries. This recipe is based on the conan recipe
for CGAL in the conan-center-index, but has been modified for conan2, as
the original recipe was written for conan1.

Note that CGAL requires a license for commercial use. See the CGAL website
for more information.
"""

import os
from conan import ConanFile
from conan.tools import files
from conan.tools import scm
from conan.tools.cmake import CMake, CMakeToolchain

required_conan_version = ">=2.0.0"


class CgalConan(ConanFile):
    name = "cgal"
    license = "GPL-3.0-or-later", "LGPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CGAL/cgal"
    description = (
        "C++ library that provides easy access to efficient and reliable algorithms"
        " in computational geometry."
    )
    topics = ("cgal", "geometry", "algorithms")
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"
    exports_sources = "CMakeLists.txt"
    short_paths = True
    version = "6.0.1"

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            # self._cmake.definitions["CGAL_HEADER_ONLY"] = "TRUE"
            self._cmake.configure(
                variables={"CGAL_HEADER_ONLY": "TRUE"}
            )  # , build_folder=self._build_subfolder)
        return self._cmake

    def _patch_sources(self):
        if scm.Version(self.version) < "5.3":
            files.replace_in_file(
                self,
                os.path.join(self._source_subfolder, "CMakeLists.txt"),
                "CMAKE_SOURCE_DIR",
                "CMAKE_CURRENT_SOURCE_DIR",
            )
        else:
            files.replace_in_file(
                self,
                os.path.join(self._source_subfolder, "CMakeLists.txt"),
                "if(NOT PROJECT_NAME)",
                "if(TRUE)",
            )

    def requirements(self):
        self.requires("boost/1.83.0")
        self.requires("eigen/3.4.0")
        self.requires("mpfr/4.2.1")
        self.requires("gmp/6.3.0")

    def package_id(self):
        self.info.clear()

    def source(self):
        files.get(
            self,
            **self.conan_data["sources"][self.version],
            destination=self._source_subfolder,
            strip_root=True
        )

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        files.copy(self, "LICENSE*", self.recipe_folder, self.export_sources_folder)
        cmake = self._configure_cmake()
        cmake.install()
        files.rmdir(self, os.path.join(self.package_folder, "share"))
        files.rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        files.rmdir(self, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "CGAL"
        self.cpp_info.names["cmake_find_package_multi"] = "CGAL"
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
        self.cpp_info.defines.append("CGAL_HEADER_ONLY=1")
