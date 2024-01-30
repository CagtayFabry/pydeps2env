"""pydeps2env: helps to generate conda environment files from python package dependencies."""

from .environment import Environment

__all__ = ["Environment"]

try:
    from ._version import __version__
except ModuleNotFoundError:
    __version__ = ""

