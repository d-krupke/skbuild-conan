"""
An extension for scikit-build to add C++-dependencies as easily as Python dependencies
via conan.
"""
from .setup_wrapper import setup

# Add __version__ variable from package information.
# https://packaging-guide.openastronomy.org/en/latest/minimal.html#my-package-init-py
from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass  # package is not installed

__all = ["setup"]
