"""
An extension for scikit-build to add C++-dependencies as easily as Python dependencies
via conan.
"""
from .setup_wrapper import setup
from .logging_utils import LogLevel

# Add __version__ variable from package information.
# https://packaging-guide.openastronomy.org/en/latest/minimal.html#my-package-init-py
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:  # Python < 3.8
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    pass  # package is not installed

__all__ = ["setup", "LogLevel"]
