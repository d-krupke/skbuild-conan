#!/usr/bin/env bash
# Runs *inside* the test container. Not meant to be called directly; see run.sh.
#
# The repository is mounted read-only at /src. We copy it to /work first so the
# build artefacts (_skbuild/, .conan/, *.egg-info) land in the container and
# never touch the host checkout, and so that nothing ends up owned by root on
# the host.
set -euo pipefail

EXPECTED_CPPSTD="${EXPECTED_CPPSTD:-17}"
EXAMPLES="${EXAMPLES:-simple_skbuild_conan_example cmake_layout_example}"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31mFAIL: %s\033[0m\n' "$*" >&2; exit 1; }

log "Environment"
# Which compiler we actually got is the whole point of this image, so say so.
(c++ --version 2>/dev/null || g++ --version 2>/dev/null || true) | head -1
python3 --version
pip show conan 2>/dev/null | awk '/^Version:/ {print "conan " $2}'

log "Detected conan profile"
# --force so a reused cache volume cannot hide what this image would detect on
# a clean machine. This is what documents each image's default cppstd; do not
# trust a hand-maintained table for it.
conan profile detect --force >/dev/null 2>&1 || true
conan profile show 2>/dev/null | grep -E '^(compiler|arch|os|build_type)' | sed 's/^/  /' || true

DETECTED_CPPSTD="$(conan profile show 2>/dev/null \
    | grep -m1 '^compiler.cppstd=' | cut -d= -f2 || true)"
echo "  -> detected compiler.cppstd: ${DETECTED_CPPSTD:-<unset>}"

log "Copying repository to /work"
cp -a /src/. /work/
# A checkout that was built on the host would otherwise leak its artefacts in.
rm -rf /work/_skbuild /work/examples/*/_skbuild /work/examples/*/.conan
rm -rf /work/examples/*/conan

log "Installing skbuild-conan"
pip install --no-cache-dir -e /work

log "Unit tests"
cd /work && python -m pytest tests/unit -q

# ConanCenter's prebuilt `b2` (boost's build tool) is linked against GLIBC_2.34,
# so boost -- and therefore CGAL -- cannot be built on an older image at all:
#
#   b2: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.34' not found
#
# That is a property of the published binary, not of skbuild-conan, and it hits
# exactly the old images we keep for the #16 reproduction (gcc10 and debian11
# are both glibc 2.31). Skip the CGAL example there, loudly, rather than
# reporting a failure that no change to this project could fix.
MIN_GLIBC_FOR_BOOST=2.34
GLIBC_VERSION="$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')"

skipped=""
overall_rc=0
for example in $EXAMPLES; do
    example_dir="/work/examples/${example}"
    [ -d "$example_dir" ] || fail "no such example: $example"

    case "$example" in
        *cgal*)
            if [ -n "$GLIBC_VERSION" ] && [ "$(printf '%s\n%s\n' \
                    "$MIN_GLIBC_FOR_BOOST" "$GLIBC_VERSION" | sort -V | head -1)" \
                    != "$MIN_GLIBC_FOR_BOOST" ]; then
                printf '\n\033[1;33m==> SKIP %s: glibc %s < %s, boost cannot build here\033[0m\n' \
                    "$example" "$GLIBC_VERSION" "$MIN_GLIBC_FOR_BOOST"
                skipped="${skipped} ${example}"
                continue
            fi
            ;;
    esac

    log "Building example: ${example}"
    build_log="/tmp/build_${example}.log"
    if ! pip install --no-build-isolation --verbose "$example_dir" >"$build_log" 2>&1; then
        tail -40 "$build_log"
        printf '\033[1;31mFAIL: %s did not build\033[0m\n' "$example" >&2
        overall_rc=1
        continue
    fi

    # Building is not enough. If the cppstd pin were ever dropped, the build
    # would still succeed on a modern compiler and this script would report a
    # false pass. Assert the standard the toolchain actually applied.
    if grep -q "Conan toolchain: C++ Standard ${EXPECTED_CPPSTD}" "$build_log"; then
        echo "  ok: toolchain applied C++ standard ${EXPECTED_CPPSTD}"
    else
        echo "  actual toolchain line(s):"
        grep "Conan toolchain: C++ Standard" "$build_log" | sed 's/^/    /' \
            || echo "    (none found)"
        printf '\033[1;31mFAIL: %s did not build against C++%s\033[0m\n' \
            "$example" "$EXPECTED_CPPSTD" >&2
        overall_rc=1
        continue
    fi

    # Conan warns via variable_watch when a CMakeLists overrides the standard
    # the toolchain set. That warning means dependencies and bindings disagree.
    if grep -q "has been modified" "$build_log"; then
        grep "has been modified" "$build_log" | sed 's/^/    /'
        printf '\033[1;31mFAIL: %s overrides CMAKE_CXX_STANDARD\033[0m\n' "$example" >&2
        overall_rc=1
        continue
    fi

    if [ -d "${example_dir}/tests" ]; then
        log "Testing example: ${example}"
        # Run from / so the import resolves to the installed module rather than
        # the source tree next to it.
        (cd / && python -m pytest "${example_dir}/tests" -q) || overall_rc=1
    fi
done

echo
# Report what was not covered, so a green run is not mistaken for full coverage.
if [ -n "$skipped" ]; then
    echo "SKIPPED_EXAMPLES=${skipped# }"
fi
echo "DETECTED_CPPSTD=${DETECTED_CPPSTD:-unset}"
exit "$overall_rc"
