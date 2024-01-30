from dataclasses import dataclass, field
from packaging.requirements import Requirement
from pathlib import Path
from collections import defaultdict
import tomli as tomllib
import yaml
import warnings


def add_requirement(
    req: Requirement | str,
    requirements: dict[str, Requirement],
    mode: str = "combine",
):
    """Add a requirement to existing requirement specification (in place)."""

    if not isinstance(req, Requirement):
        req = Requirement(req)

    if req.name not in requirements:
        requirements[req.name] = req
    elif mode == "combine":
        requirements[req.name].specifier &= req.specifier
    elif mode == "replace":
        requirements[req.name] = req
    else:
        raise ValueError(f"Unknown `mode` for add_requirement: {mode}")


def combine_requirements(
    req1: dict[str, Requirement], req2: dict[str, Requirement]
) -> dict[str, Requirement]:
    """Combine multiple requirement listings."""
    req1 = req1.copy()
    for r in req2.values():
        add_requirement(r, req1, mode="combine")

    return req1


@dataclass
class Environment:
    filename: str | Path
    channels: list[str] = field(default_factory=lambda: ["conda-forge"])
    pip_packages: set[str] = field(default_factory=set)  # install via pip
    requirements: dict[str, Requirement] = field(default_factory=dict, init=False)
    build_system: dict[str, Requirement] = field(default_factory=dict, init=False)

    def __post_init__(self):
        if Path(self.filename).suffix == ".toml":
            self.load_pyproject()

    def load_pyproject(self):
        with open(self.filename, "rb") as fh:
            cp = defaultdict(dict, tomllib.load(fh))

        if python := cp["project"].get("requires-python"):
            add_requirement("python" + python, self.requirements)

        for dep in cp.get("project").get("dependencies"):
            add_requirement(dep, self.requirements)

        for dep in cp.get("build-system").get("requires"):
            add_requirement(dep, self.build_system)

    def _get_dependencies(self, include_build_system: bool = True):
        """Get the default conda environment entries."""

        reqs = self.requirements.copy()
        if include_build_system:
            reqs = combine_requirements(reqs, self.build_system)

        _python = reqs.pop("python", None)

        deps = [str(r) for r in reqs.values() if r.name not in self.pip_packages]
        deps.sort(key=str.lower)
        if _python:
            deps = [str(_python)] + deps

        pip = [str(r) for r in reqs.values() if r.name in self.pip_packages]
        pip.sort(key=str.lower)

        return deps, pip

    def export(
        self,
        outfile: str | Path = "environment.yaml",
        include_build_system: bool = True,
    ):
        deps, pip = self._get_dependencies(include_build_system=include_build_system)

        conda_env = {"channels": self.channels, "dependencies": deps.copy()}
        if pip:
            conda_env["dependencies"] += ["pip", {"pip": pip}]

        if outfile is None:
            return conda_env

        p = Path(outfile)
        if p.suffix in [".txt"]:
            deps += pip
            deps.sort(key=str.lower)
            with open(p, "w") as outfile:
                outfile.writelines("\n".join(deps))
        else:
            if p.suffix not in [".yaml", ".yml"]:
                warnings.warn(
                    f"Unknown environment format `{p.suffix}`, generating conda yaml output."
                )
            with open(p, "w") as outfile:
                yaml.dump(conda_env, outfile, default_flow_style=False)
