#!/usr/bin/env bash
# Build and test the examples across a set of Linux containers.
#
# Why: the bug class in #16 is a compiler whose *default* C++ standard is older
# than a dependency requires. That cannot be reproduced on `ubuntu-latest`,
# which ships a GCC defaulting to gnu17 — a regression that dropped the cppstd
# pin would pass every check we currently run. GCC <= 10 defaults to gnu14 and
# reproduces it exactly.
#
# Usage:
#   ./tests/docker/run.sh                      # default image set
#   ./tests/docker/run.sh gcc10 ubuntu2204     # only these images
#   ./tests/docker/run.sh --list               # show known images
#   ./tests/docker/run.sh --all                # every known image
#   ./tests/docker/run.sh --with-cgal gcc10    # include the slow CGAL example
#   ./tests/docker/run.sh --no-cache           # ignore the conan cache volumes
#
# Reusing containers/caches is the default: each image gets a named docker
# volume for CONAN_HOME, so boost/CGAL are built once and reused afterwards.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# label:base image
# The comments are a hint only — each run prints the *detected* cppstd, which
# is the authoritative value.
IMAGES=(
    "gcc10:gcc:10"            # GCC 10 -> defaults to gnu14; the #16 reproduction
    "gcc13:gcc:13"            # GCC 13 -> defaults to gnu17
    "ubuntu2204:ubuntu:22.04" # GCC 11, the first GCC defaulting to gnu17
    "almalinux9:almalinux:9"  # RHEL family, different glibc/python packaging
)
# Included by --all only: slower or more exotic.
EXTRA_IMAGES=(
    "gcc14:gcc:14"
    "debian11:debian:11"      # older glibc/libstdc++
    "ubuntu2404:ubuntu:24.04"
)

FAST_EXAMPLES="simple_skbuild_conan_example cmake_layout_example"
CGAL_EXAMPLE="cgal_skbuild_conanio_example"

EXPECTED_CPPSTD=17
WITH_CGAL=0
USE_CACHE=1
SELECTED=()

die() { printf '\033[1;31m%s\033[0m\n' "$*" >&2; exit 1; }

list_images() {
    echo "Default images:"
    for entry in "${IMAGES[@]}"; do printf '  %-12s %s\n' "${entry%%:*}" "${entry#*:}"; done
    echo "Additional images (--all):"
    for entry in "${EXTRA_IMAGES[@]}"; do printf '  %-12s %s\n' "${entry%%:*}" "${entry#*:}"; done
}

while [ $# -gt 0 ]; do
    case "$1" in
        --list) list_images; exit 0 ;;
        --all) IMAGES+=("${EXTRA_IMAGES[@]}") ;;
        --with-cgal) WITH_CGAL=1 ;;
        --no-cache) USE_CACHE=0 ;;
        # Print the header comment block, stopping at the first line that is
        # not a comment. Avoids a hard-coded line range drifting out of date,
        # and avoids GNU-only sed syntax (BSD/macOS sed has no `\?`).
        -h|--help)
            awk 'NR == 1 { next } /^#/ { sub(/^#[ ]?/, ""); print; next } { exit }' \
                "${BASH_SOURCE[0]}"
            exit 0 ;;
        -*) die "unknown option: $1" ;;
        *) SELECTED+=("$1") ;;
    esac
    shift
done

command -v docker >/dev/null 2>&1 || die "docker not found in PATH"
docker info >/dev/null 2>&1 || die "cannot talk to the docker daemon (is it running?)"

# Narrow to the requested labels, if any.
if [ "${#SELECTED[@]}" -gt 0 ]; then
    filtered=()
    for want in "${SELECTED[@]}"; do
        found=0
        for entry in "${IMAGES[@]}" "${EXTRA_IMAGES[@]}"; do
            if [ "${entry%%:*}" = "$want" ]; then filtered+=("$entry"); found=1; break; fi
        done
        [ "$found" = 1 ] || die "unknown image label: ${want} (see --list)"
    done
    IMAGES=("${filtered[@]}")
fi

EXAMPLES="$FAST_EXAMPLES"
[ "$WITH_CGAL" = 1 ] && EXAMPLES="$EXAMPLES $CGAL_EXAMPLE"

results=()
overall_rc=0

for entry in "${IMAGES[@]}"; do
    label="${entry%%:*}"
    base="${entry#*:}"
    tag="skbuild-conan-test:${label}"

    printf '\n\033[1;35m########## %s (%s) ##########\033[0m\n' "$label" "$base"

    if ! docker build -q -t "$tag" \
            --build-arg "BASE_IMAGE=${base}" \
            -f "${SCRIPT_DIR}/Dockerfile" "${SCRIPT_DIR}" >/dev/null; then
        printf '\033[1;31mimage build failed: %s\033[0m\n' "$label" >&2
        results+=("${label}|image build failed|-")
        overall_rc=1
        continue
    fi

    docker_args=(
        --rm
        -v "${REPO_ROOT}:/src:ro"
        -v "${SCRIPT_DIR}/in_container.sh:/in_container.sh:ro"
        -e "EXPECTED_CPPSTD=${EXPECTED_CPPSTD}"
        -e "EXAMPLES=${EXAMPLES}"
    )
    if [ "$USE_CACHE" = 1 ]; then
        # Per image: a cache from a different compiler is useless at best.
        docker_args+=(-v "skbuild-conan-cache-${label}:/conan")
    fi

    # Explicit template: portable across GNU and BSD mktemp, and gives the
    # stray file a recognisable name if a run is interrupted before cleanup.
    out_log="$(mktemp "${TMPDIR:-/tmp}/skbuild-conan-${label}.XXXXXX")"
    if docker run "${docker_args[@]}" "$tag" bash /in_container.sh 2>&1 | tee "$out_log"; then
        rc=0
    else
        rc=1
    fi
    cppstd="$(grep -m1 '^DETECTED_CPPSTD=' "$out_log" | cut -d= -f2 || true)"
    rm -f "$out_log"

    if [ "$rc" = 0 ]; then
        results+=("${label}|PASS|${cppstd:-unknown}")
    else
        results+=("${label}|FAIL|${cppstd:-unknown}")
        overall_rc=1
    fi
done

printf '\n\033[1m%-14s %-6s %s\033[0m\n' "IMAGE" "RESULT" "DETECTED cppstd"
for row in "${results[@]}"; do
    IFS='|' read -r label result cppstd <<<"$row"
    if [ "$result" = "PASS" ]; then colour='\033[0;32m'; else colour='\033[0;31m'; fi
    printf "%-14s ${colour}%-6s\033[0m %s\n" "$label" "$result" "$cppstd"
done

exit "$overall_rc"
