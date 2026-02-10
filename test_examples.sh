#!/usr/bin/env bash
# Build and test all examples using the local skbuild-conan.
#
# Usage:
#   ./test_examples.sh                  # test all examples
#   ./test_examples.sh simple_skbuild_conan_example  # test a specific example
#
# This installs the local skbuild-conan in editable mode, then builds the
# examples with --no-build-isolation so they pick up the local version
# instead of fetching from PyPI.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing local skbuild-conan in editable mode..."
pip install -e "$SCRIPT_DIR"

if [ $# -gt 0 ]; then
    examples=("$@")
else
    examples=(simple_skbuild_conan_example cgal_skbuild_conan_example cgal_skbuild_conanio_example)
fi

for example in "${examples[@]}"; do
    example_dir="$SCRIPT_DIR/examples/$example"
    if [ ! -d "$example_dir" ]; then
        echo "ERROR: Example directory not found: $example_dir" >&2
        exit 1
    fi
    echo ""
    echo "==> Building example: $example"
    pip install --no-build-isolation --verbose "$example_dir"
done

echo ""
echo "==> All examples built successfully."
