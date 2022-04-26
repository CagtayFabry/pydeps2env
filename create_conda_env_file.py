"""Read a 'setup.cfg' file and create a conda environment file."""

import argparse
import configparser

parser = argparse.ArgumentParser()
parser.add_argument("setup", type=str, default="setup.cfg")
parser.add_argument("env", type=str, default="environment.yml")
parser.add_argument("--channels", type=str, nargs="*", default=["defaults"])
parser.add_argument("--extras", type=str, nargs="*", default=[])
parser.add_argument("--setup_requires", type=str, default="omit")
args = parser.parse_args()

cp = configparser.ConfigParser(
    converters={"list": lambda x: [i.strip() for i in x.split("\n") if i.strip()]}
)
cp.read(args.setup)

env = dict(channels=args.channels)
env["dependencies"] = ["python" + cp.get("options", "python_requires")]
if args.setup_requires == "include":
    env["dependencies"] = env["dependencies"] + cp.getlist("options", "setup_requires")
env["dependencies"] = env["dependencies"] + cp.getlist("options", "install_requires")
for e in args.extras:
    env["dependencies"] = env["dependencies"] + cp.getlist("options.extras_require", e)

# cleanup
env["dependencies"] = [dep.replace(" ", "") for dep in env["dependencies"]]

output = "channels:"
output += "\n  - ".join([""] + env["channels"])
output += "\ndependencies:"
output += "\n  - ".join([""] + env["dependencies"])

with open(args.env, "w") as f:
    f.write(output)
