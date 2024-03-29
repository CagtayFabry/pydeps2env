from __future__ import annotations

from pathlib import Path

try:
    from pydeps2env.environment import Environment, split_extras
except ModuleNotFoundError:  # try local file if not installed
    from environment import Environment, split_extras


def create_environment_file(
    filename: list[str],
    output_file: str,
    channels: list[str],
    extras: list[str],
    pip: set[str],
    include_build_system: bool = False,
):
    pip = set(pip)
    env = Environment(filename[0], pip_packages=pip, extras=extras, channels=channels)
    for f in filename[1:]:
        env.combine(Environment(f, pip_packages=pip, extras=extras, channels=channels))

    _include = include_build_system == "include"
    env.export(output_file, include_build_system=_include)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "setup", type=str, nargs="*", default="pyproject.toml", help="dependency file"
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
    args = parser.parse_args()

    for file in args.setup:
        filename, _ = split_extras(file)
        if not Path(filename).is_file():
            raise FileNotFoundError(f"Could not find file {filename}")

    create_environment_file(
        filename=args.setup,
        output_file=args.output,
        channels=args.channels,
        extras=args.extras,
        pip=args.pip,
        include_build_system=args.build_system,
    )


if __name__ == "__main__":
    main()
