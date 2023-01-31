"""Read a 'setup.cfg' or 'pyproject.toml' file and create a conda environment file."""

import argparse
import configparser
from collections import defaultdict
from pathlib import Path

import tomli as tomllib

parser = argparse.ArgumentParser()
parser.add_argument("setup", type=str, default="setup.cfg", help="or pyproject.toml")
parser.add_argument("env", type=str, default="environment.yml")
parser.add_argument("--channels", type=str, nargs="*", default=["defaults"])
parser.add_argument("--extras", type=str, nargs="*", default=[])
parser.add_argument("--setup_requires", type=str, default="omit")
parser.add_argument("--pip", type=str, nargs="*", default=[])
args = parser.parse_args()

if not Path(args.setup).is_file():
    raise FileNotFoundError(f"Could not find file {args.setup}")


class MetadataType:
    SETUP_CFG = "setup.cfg"
    PYPROJECT_TOML = "pyproject.toml"


env = dict(channels=args.channels)


if MetadataType.SETUP_CFG in args.setup:
    cp = configparser.ConfigParser(
        converters={"list": lambda x: [i.strip() for i in x.split("\n") if i.strip()]}
    )
    cp.read(args.setup)

    env["dependencies"] = ["python" + cp.get("options", "python_requires")]
    if args.setup_requires == "include":
        env["dependencies"] = env["dependencies"] + cp.getlist(
            "options", "setup_requires"
        )
    env["dependencies"] = env["dependencies"] + cp.getlist(
        "options", "install_requires"
    )
    for e in args.extras:
        env["dependencies"] = env["dependencies"] + cp.getlist(
            "options.extras_require", e
        )

elif MetadataType.PYPROJECT_TOML in args.setup:
    with open(args.setup, "rb") as fh:
        cp = defaultdict(dict, tomllib.load(fh))

    env["dependencies"] = ["python" + cp["project"].get("requires-python")]

    if args.setup_requires == "include":
        env["dependencies"] = env["dependencies"] + cp.get("build-system").get(
            "requires"
        )

    env["dependencies"] = env["dependencies"] + cp.get("project").get("dependencies")

    for e in args.extras:
        extra_deps = cp.get("project").get("optional-dependencies").get(e)
        if not extra_deps:
            continue
        env["dependencies"] = env["dependencies"] + extra_deps
# cleanup
env["dependencies"] = [dep.replace(" ", "") for dep in env["dependencies"]]

# pip installs
pip = list(set(env["dependencies"]) & set(args.pip))
env["dependencies"] = list(set(env["dependencies"]) - set(pip))

# sort output
env["dependencies"] = sorted(env["dependencies"])
pip = sorted(pip)

output = "channels:"
output += "\n  - ".join([""] + env["channels"])
output += "\ndependencies:"
output += "\n  - ".join([""] + env["dependencies"])

if pip:
    output += "\n  - pip:"
    output += "\n    - ".join([""] + pip)

with open(args.env, "w") as f:
    f.write(output)
