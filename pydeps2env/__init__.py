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

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pydeps2env")
except PackageNotFoundError:
    # package is not installed
    pass
finally:
    del version, PackageNotFoundError
