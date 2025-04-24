from __future__ import annotations

from pathlib import Path

import yaml

try:
    from pydeps2env.environment import Environment, split_extras
except ModuleNotFoundError:  # try local file if not installed
    from environment import Environment, split_extras


def create_environment_file(
    sources: list[str],
    output: str = "environment.yml",
    *,
    channels: list[str] = None,
    extras: list[str] = None,
    pip: set[str] = None,
    editable: set[str] = None,
    additional_requirements: list[str] = None,
    remove: set[str] = None,
    include_build_system: str = "omit",
    name: str = None,
):
    """Create an environment file from multiple source files and additional requirements.

    Parameters
    ----------
    sources
        The list of source files to combine.
    output
        The output filename to generate
    channels
        Conda channels to include.
    extras
        Extras specification to apply to all sources.
    pip
        List of dependencies to install via pip.
    editable
        List of names of packages to install in pip editable mode
    additional_requirements
        Additional requirements to include in the environment.
    remove
        Remove selected requirements from the environment.
    include_build_system
        Include build system requirements by using `include`.
    name
        Name of the environment.

    """
    if remove is None:
        remove = set()
    if additional_requirements is None:
        additional_requirements = []
    if pip is None:
        pip = []
    pip = set(pip)
    if editable is None:
        editable = {}

    env = create_environment(
        sources=sources,
        additional_requirements=additional_requirements,
        channels=channels,
        extras=extras,
        pip=pip,
        editable=editable,
    )

    _include = include_build_system == "include"
    env.export(output, include_build_system=_include, remove=remove, name=name)


def create_from_definition(env_def: str):
    """Create an environment from parameters stored in a definition YAML file.

    Parameters
    ----------
    env_def
        The definition file.

    """
    with open(env_def, "r") as f:
        config = yaml.load(f.read(), yaml.SafeLoader)
    create_environment_file(**config)


def create_environment(
    sources: list[str],
    *,
    channels: list[str] = None,
    extras: list[str] = None,
    pip: set[str] = None,
    additional_requirements: list[str] = None,
    editable: set[str] = None,
):
    """Create an environment instance from multiple source files and additional requirements.

    Parameters
    ----------
    sources
        The list of source files to combine.
    channels
        Conda channels to include.
    extras
        Extras specification to apply to all sources.
    pip
        List of dependencies to install via pip.
    additional_requirements
        Additional requirements to include in the environment.
    editable
        List of names of packages to install in pip editable mode

    Returns
    -------
    Environment
        The environment specification.
    """
    if channels is None:
        channels = ["conda-forge"]
    if extras is None:
        extras = []
    if pip is None:
        pip = []
    if additional_requirements is None:
        additional_requirements = []
    if editable is None:
        editable = {}

    env = Environment(
        sources[0],
        pip_packages=pip,
        extras=extras,
        channels=channels,
        editable=editable,
    )
    for source in sources[1:]:
        env.combine(
            Environment(source, pip_packages=pip, extras=extras, channels=channels)
        )

    env.add_requirements(additional_requirements)

    return env


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sources",
        type=str,
        nargs="*",
        default="pyproject.toml",
        help="dependency files and sources",
    )
    parser.add_argument(
        "-o", "--output", type=str, default="environment.yml", help="output file"
    )
    parser.add_argument(
        "-c", "--channels", type=str, nargs="*", default=["conda-forge"]
    )
    parser.add_argument("-e", "--extras", type=str, nargs="*", default=[])
    parser.add_argument(
        "-b",
        "--build_system",
        "--setup_requires",
        type=str,
        choices=["omit", "include"],
    )
    parser.add_argument("-p", "--pip", type=str, nargs="*", default=[])
    parser.add_argument("-r", "--remove", type=str, nargs="*", default=[])
    parser.add_argument(
        "-a", "--additional_requirements", type=str, nargs="*", default=[]
    )
    args = parser.parse_args()

    for file in args.sources:
        filename, _ = split_extras(file)
        if not Path(filename).is_file():
            raise FileNotFoundError(f"Could not find file {filename}")

    create_environment_file(
        sources=args.sources,
        output=args.output,
        channels=args.channels,
        extras=args.extras,
        pip=args.pip,
        remove=args.remove,
        additional_requirements=args.additional_requirements,
        include_build_system=args.build_system,
    )


if __name__ == "__main__":
    main()
