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
    from pydeps2env import Environment

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
    parser.add_argument("--channels", type=str, nargs="*", default=["defaults"])
    parser.add_argument("--extras", type=str, nargs="*", default=[])
    parser.add_argument("--setup_requires", type=str, default="omit")
    parser.add_argument("--pip", type=str, nargs="*", default=[])
    args = parser.parse_args()

    if not Path(args.setup).is_file():
        raise FileNotFoundError(f"Could not find file {args.setup}")

    create_environment_file(
        filename=args.setup,
        output_file=args.env,
        channels=args.channels,
        extras=args.extras,
        pip=args.pip,
        include_build_system=args.setup_requires,
    )


if __name__ == "__main__":
    main()
