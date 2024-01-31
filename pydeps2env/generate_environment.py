from __future__ import annotations

from pathlib import Path


def create_environment_file(
    filename: str,
    output_file: str,
    channels: list[str],
    extras: list[str],
    pip: list[str],
    include_build_system: bool = False,
):
    try:
        from pydeps2env.environment import Environment
    except ModuleNotFoundError:  # try local file if not installed
        from environment import Environment

    env = Environment(filename, pip_packages=pip, extras=extras, channels=channels)

    _include = include_build_system == "include"
    env.export(output_file, include_build_system=_include)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "setup", type=str, default="pyproject.toml", help="dependency file"
    )
    parser.add_argument("env", type=str, default="environment.yml", help="output file")
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

    if not Path(args.setup).is_file():
        raise FileNotFoundError(f"Could not find file {args.setup}")

    create_environment_file(
        filename=args.setup,
        output_file=args.env,
        channels=args.channels,
        extras=args.extras,
        pip=args.pip,
        include_build_system=args.build_system,
    )


if __name__ == "__main__":
    main()
