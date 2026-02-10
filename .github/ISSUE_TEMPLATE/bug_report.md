---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce

1.
2.
3.

## Expected Behavior

<!-- What you expected to happen -->

## Actual Behavior

<!-- What actually happened -->

## Environment

- **OS:** <!-- e.g., Ubuntu 22.04, Windows 11, macOS 13 -->
- **Python Version:** <!-- e.g., 3.9.12 -->
- **skbuild-conan Version:** <!-- e.g., 1.4.0 -->
- **Conan Version:** <!-- Run: conan --version -->
- **CMake Version:** <!-- Run: cmake --version -->
- **Compiler:** <!-- e.g., gcc 11.3, MSVC 2022, clang 14 -->

## Logs

<!-- Run with debug logging and paste relevant output -->

```bash
# Command used
SKBUILD_CONAN_LOG_LEVEL=debug pip install <your-package> --verbose

# Output
<paste output here>
```

## Minimal Reproducible Example

<!-- If possible, provide a minimal setup.py or project that reproduces the issue -->

```python
# setup.py
from skbuild_conan import setup

setup(
    name="test_package",
    # ... your minimal setup
)
```

## Additional Context

<!-- Add any other context about the problem here -->
<!-- Screenshots, dependency tree, conanfile.txt, etc. -->

## Possible Solution

<!-- If you have ideas on how to fix this, describe them here -->

## Checklist

- [ ] I have searched existing issues to ensure this is not a duplicate
- [ ] I have provided a minimal reproducible example
- [ ] I have included debug logs
- [ ] I have included environment information
