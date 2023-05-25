import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, rm
from conan.tools.google import bazel_layout, BazelDeps, BazelToolchain, Bazel

required_conan_version = ">=1.53.0"


class EmbagConan(ConanFile):
    name = "embag"
    version = "0.0.42"
    description = "Schema and dependency free ROS bag reader"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/embarktrucks/embag"
    topics = ("rosbag", "ros", "robotics")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    exports_sources = [
        "WORKSPACE",
        ".bazelproject",
        ".bazelversion",
        "lib/*",
        "LICENSE",
    ]

    @property
    def _min_cppstd(self):
        return 14

    def export_sources(self):
        copy(
            self,
            "CMakeLists.txt",
            src=self.recipe_folder,
            dst=os.path.join(self.export_sources_folder, "src"),
        )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        bazel_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.81.0", transitive_headers=True, transitive_libs=True)
        self.requires("lz4/1.9.4", transitive_headers=True, transitive_libs=True)
        self.requires("bzip2/1.0.8", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)

    def build_requirements(self):
        self.tool_requires("bazel/6.2.0")

    def generate(self):
        tc = BazelToolchain(self)
        tc.generate()
        deps = BazelDeps(self)
        deps.generate()

    def _patch_sources(self):
        pass

    def build(self):
        self._patch_sources()
        bazel = Bazel(self)
        bazel.configure()
        bazel.build(label="//lib:embag")

    def package(self):
        # license
        copy(
            self,
            pattern="LICENSE",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        # headers
        for pattern in ["*.h", "*.hpp"]:
            copy(
                self,
                pattern=pattern,
                dst=os.path.join(self.package_folder, "include", "embag"),
                src=os.path.join(self.build_folder, "lib"),
            )
        # library files
        copy(
            self,
            pattern="libembag*",
            dst=os.path.join(self.package_folder, "lib"),
            src=os.path.join(self.build_folder, "bazel-bin", "lib"),
        )
        rm(self, "*.params", self.package_folder)
        rm(self, "*.pdb", self.package_folder)

    def package_info(self):
        self.cpp_info.libs = ["embag"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
