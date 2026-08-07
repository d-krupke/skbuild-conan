"""
An extension for scikit-build to add C++-dependencies as easily as Python dependencies
via conan.
"""

# Add __version__ variable from package information.
# https://packaging-guide.openastronomy.org/en/latest/minimal.html#my-package-init-py
import contextlib
from importlib.metadata import PackageNotFoundError, version

from .logging_utils import LogLevel
from .setup_wrapper import setup

with contextlib.suppress(PackageNotFoundError):  # package is not installed
    __version__ = version(__name__)

__all__ = ["LogLevel", "setup"]
