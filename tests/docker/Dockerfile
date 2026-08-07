# Parameterized test image for skbuild-conan.
#
# The point of this image is *not* to be a good production image. It is to
# provide a compiler whose default `compiler.cppstd` we do not control, so that
# `conan profile detect` behaves the way it does on a user's machine rather
# than the way it does on `ubuntu-latest`.
ARG BASE_IMAGE=gcc:13
FROM ${BASE_IMAGE}

# The base images span Debian- and RHEL-family distributions, so detect the
# package manager instead of maintaining one Dockerfile per family.
#
# We need: a C++ toolchain, Python *with development headers* (the examples
# build a native module), and git because CPM may fetch pybind11 over git.
# cmake and ninja deliberately come from pip below, matching what the examples
# declare in their `pyproject.toml`.
#
# The RPM branch deliberately omits `curl`: RHEL-family images ship
# `curl-minimal`, and pulling in full `curl` is a package conflict rather than
# an upgrade. Nothing here needs the curl *binary* anyway — CMake's
# `file(DOWNLOAD)`, which FetchContent and CPM use, links its own libcurl.
RUN set -eux; \
    if command -v apt-get >/dev/null 2>&1; then \
        export DEBIAN_FRONTEND=noninteractive; \
        apt-get update; \
        apt-get install -y --no-install-recommends \
            build-essential make git curl ca-certificates \
            python3 python3-dev python3-venv; \
        rm -rf /var/lib/apt/lists/*; \
    elif command -v dnf >/dev/null 2>&1; then \
        dnf -y install gcc-c++ make git ca-certificates python3 python3-devel; \
        dnf clean all; \
    elif command -v yum >/dev/null 2>&1; then \
        yum -y install gcc-c++ make git ca-certificates python3 python3-devel; \
        yum clean all; \
    else \
        echo "unsupported base image: no apt-get, dnf or yum found" >&2; \
        exit 1; \
    fi

# A virtualenv keeps us clear of PEP 668 ("externally managed environment"),
# which newer Debian/Ubuntu images enforce on a plain `pip install`.
RUN python3 -m venv /venv
ENV PATH="/venv/bin:${PATH}"

# Baked into the image so that a run does not re-download the build toolchain
# every time. Pinned only as loosely as the examples themselves pin.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
        "conan>=2.0.0" \
        "scikit-build>=0.17.3" \
        "cmake>=3.23" \
        ninja \
        pytest

# run.sh mounts a per-image volume here, so repeated runs reuse the conan
# package cache instead of rebuilding boost/CGAL from scratch.
ENV CONAN_HOME=/conan

WORKDIR /work
