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
    remove: set[str] = None,
    additional_requirements: list[str] = None,
    include_build_system: str = "omit",
    name: str = None,
):
    if channels is None:
        channels = ["conda-forge"]
    if extras is None:
        extras = []
    if pip is None:
        pip = []
    if remove is None:
        remove = {}
    if additional_requirements is None:
        additional_requirements = []
    pip = set(pip)
    env = Environment(
        sources[0],
        pip_packages=pip,
        extras=extras,
        channels=channels,
        extra_requirements=additional_requirements,
    )
    for f in sources[1:]:
        env.combine(Environment(f, pip_packages=pip, extras=extras, channels=channels))

    _include = include_build_system == "include"
    env.export(output, include_build_system=_include, remove=remove, name=name)


def create_from_definition(env_def: str):
    with open(env_def, "r") as f:
        config = yaml.load(f.read(), yaml.SafeLoader)
    create_environment_file(**config)


def create_environment(
    sources: list[str],
    requirements: list[str] = None,
    channels: list[str] = None,
    extras: list[str] = None,
    pip: set[str] = None,
):
    if requirements is None:
        requirements = []
    if channels is None:
        channels = ["conda-forge"]
    if extras is None:
        extras = []
    if pip is None:
        pip = []

    env = Environment(sources[0], pip_packages=pip, extras=extras, channels=channels)
    for source in sources[1:]:
        env.combine(
            Environment(source, pip_packages=pip, extras=extras, channels=channels)
        )

    env.add_requirements(requirements)

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
    parser.add_argument("-c", "--channels", type=str, nargs="*", default=["defaults"])
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

    for file in args.setup:
        filename, _ = split_extras(file)
        if not Path(filename).is_file():
            raise FileNotFoundError(f"Could not find file {filename}")

    create_environment_file(
        filename=args.sources,
        output_file=args.output,
        channels=args.channels,
        extras=args.extras,
        pip=args.pip,
        remove=args.remove,
        additional_requirements=args.additional_requirements,
        include_build_system=args.build_system,
    )


if __name__ == "__main__":
    main()
