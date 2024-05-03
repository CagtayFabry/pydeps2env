"""pydeps2env: helps to generate conda environment files from python package dependencies."""

from .environment import Environment
from .generate_environment import (
    create_environment,
    create_environment_file,
    create_from_definition,
)

__all__ = [
    "Environment",
    "create_environment",
    "create_environment_file",
    "create_from_definition",
]

try:
    from ._version import __version__
except ModuleNotFoundError:
    __version__ = ""
