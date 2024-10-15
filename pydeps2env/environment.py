from __future__ import annotations

from dataclasses import dataclass, field, InitVar
from packaging.requirements import Requirement
from pathlib import Path
from collections import defaultdict
import configparser
import sys
import yaml
from io import StringIO, BytesIO
from warnings import warn

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib


def get_mapping():
    """Downloads the mapping conda->pypi names from Parselmouth and returns the reverse mapping."""
    import json
    import urllib.request as request
    from importlib import resources

    from urllib.error import ContentTooShortError, URLError
    try:
        fn, response = request.urlretrieve(
        "https://raw.githubusercontent.com/prefix-dev/parselmouth/refs/heads/main/files/compressed_mapping.json")
    except (ContentTooShortError, URLError):
        fn = resources.files("pydeps2env") / "compressed_mapping.json"

    with open(fn, 'r') as f:
        data = json.load(f)

    pypi_2_conda = {v: k for k, v in data.items() if v is not None and v != k}
    return pypi_2_conda


"""This mapping holds name mappings from pypi to conda packages."""
pypi_to_conda_mapping = get_mapping()


def split_extras(filename: str) -> tuple[str, set]:
    """Split extras requirements indicated in []."""
    if "[" in filename:
        filename, extras = filename.split("[", 1)
        extras = set(extras.split("]", 1)[0].split(","))
    else:
        extras = set()
    return filename, extras


def add_requirement(
    req: Requirement | str,
    requirements: dict[str, Requirement],
    mode: str = "combine",
):
    """Add a requirement to existing requirement specification (in place)."""

    if not isinstance(req, Requirement):
        req = Requirement(req)

    # A pip requirement can contain dashes in their name, we need to replace them to underscores.
    # https://docs.conda.io/projects/conda-build/en/latest/concepts/package-naming-conv.html#term-Package-name
    if req.name in pypi_to_conda_mapping.keys():
        old_name = req.name
        req.name = pypi_to_conda_mapping[req.name]
        assert req.name != old_name
        requirements.pop(old_name, None)

    if req.extras:  # expand extras
        for r in req.extras:
            add_requirement(r, requirements)
        req.extras = {}

    if req.name not in requirements:
        requirements[req.name] = req
    elif mode == "combine":
        requirements[req.name].specifier &= req.specifier
        if req.url:
            if requirements[req.name].url and requirements[req.name].url != req.url:
                warn(
                    f"Replacing url for package {req.name}: {requirements[req.name].url} -> req.url",
                    UserWarning,
                    stacklevel=1,
                )
                requirements[req.name].url = req.url
    elif mode == "replace":
        requirements[req.name] = req
    else:
        raise ValueError(f"Unknown `mode` for add_requirement: {mode}")


def extract_url_user_auth(url) -> tuple[str, str, str]:
    """Extract basic url, user and authentication from url scheme.

    Returns
    -------
    tuple
        Tuple consisting of the url with authentication stripped
        and username and password if supplied.
    """
    import urllib.parse

    split_results = urllib.parse.urlsplit(url=url)
    components = [*split_results]
    components[1] = components[1].split("@")[-1]  # remove user:auth info
    return (
        urllib.parse.urlunsplit(components),
        split_results.username,
        split_results.password,
    )


def guess_suffix_from_url(url) -> str:
    """Try to extract filename suffix from url."""

    return "." + url.split(".")[-1].split("/")[0]


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
    extras: set[str] | list[str] = field(default_factory=set)
    pip_packages: set[str] = field(
        default_factory=set
    )  # names of packages to install via pip
    extra_requirements: InitVar[list[str]] = None
    requirements: dict[str, Requirement] = field(default_factory=dict, init=False)
    build_system: dict[str, Requirement] = field(default_factory=dict, init=False)

    def __post_init__(self, extra_requirements):
        # cleanup duplicates etc.
        self.extras = set(self.extras)
        self.channels = list(dict.fromkeys(self.channels))
        self.pip_packages = set(self.pip_packages)

        if self.filename:
            self._read_source()

        if extra_requirements:
            self.add_requirements(extra_requirements)

        # packages with url specification must be pip installed
        self.pip_packages |= {req.name for req in self.requirements.values() if req.url}

    def add_requirements(self, requirements: list[str]):
        """Add a list of additional requirements to the environment."""

        for req in requirements:
            add_requirement(req, self.requirements)

    def add_build_system(self, requirements: list[str]):
        """Manually add a list of additional requirements to the build system specification."""

        for req in requirements:
            add_requirement(req, self.build_system)

    def _read_source(self):
        """Read and parse source definition and add requirements."""

        # parse and remove extra specs from filename
        if isinstance(self.filename, str):
            self.filename, extras = split_extras(self.filename)
            self.extras |= set(extras)

        # get file contents from web url or local file
        if isinstance(self.filename, str) and self.filename.startswith("http"):
            import urllib.request

            url = self.filename
            _token = None

            # site specific url parsing
            if "/github.com/" in url:
                url = url.replace("/github.com/", "/raw.githubusercontent.com/")
                url = url.replace("/blob/", "/")
            elif "git.bam.de" in url or "gitlab.com" in url:
                url, _, _token = extract_url_user_auth(url)

            req = urllib.request.Request(url)
            if _token:
                req.add_header("PRIVATE-TOKEN", _token)

            # store suffix for later parsing
            self._suffix = guess_suffix_from_url(url)

            with urllib.request.urlopen(req) as f:
                _contents: bytes = f.read()  # read raw content into bytes
        else:  # local file
            # store suffix for later parsing
            self._suffix = Path(self.filename).suffix

            with open(self.filename, "rb") as f:
                _contents: bytes = f.read()

        if self._suffix == ".toml":
            self.load_pyproject(_contents)
        elif self._suffix == ".cfg":
            self.load_config(_contents)
        elif self._suffix in [".yaml", ".yml"]:
            self.load_yaml(_contents)
        elif self._suffix in [".txt"]:
            self.load_txt(_contents)
        else:
            raise ValueError(f"Unsupported input {self.filename}")

    def load_pyproject(self, contents: bytes):
        """Load contents from a toml file (assume pyproject.toml layout)."""

        tomldict = tomllib.load(BytesIO(contents))
        cp = defaultdict(dict, tomldict)

        if python := cp["project"].get("requires-python"):
            self.add_requirements(["python" + python])

        self.add_requirements(cp.get("project").get("dependencies"))
        self.add_build_system(cp.get("build-system").get("requires"))
        for e in self.extras:
            self.add_requirements(cp.get("project").get("optional-dependencies").get(e))

    def load_config(self, contents: bytes):
        """Load contents from a cfg file (assume setup.cfg layout)."""
        cp = configparser.ConfigParser(
            converters={
                "list": lambda x: [i.strip() for i in x.split("\n") if i.strip()]
            }
        )

        cp.read_string(contents.decode("UTF-8"))

        if python := cp.get("options", "python_requires"):
            self.add_requirements(["python" + python])

        self.add_requirements(cp.getlist("options", "install_requires"))
        self.add_build_system(cp.getlist("options", "setup_requires"))
        for e in self.extras:
            self.add_requirements(cp.getlist("options.extras_require", e))

    def load_yaml(self, contents: bytes):
        """Load a conda-style environment.yaml file."""
        env = yaml.load(contents.decode(), yaml.SafeLoader)

        self.channels += env.get("channels", [])
        self.channels = list(dict.fromkeys(self.channels))

        for dep in env.get("dependencies"):
            if isinstance(dep, str):
                add_requirement(dep, self.requirements)
            elif isinstance(dep, dict) and "pip" in dep:
                add_requirement("pip", self.requirements)
                for pip_dep in dep["pip"]:
                    req = Requirement(pip_dep)
                    self.pip_packages |= {req.name}
                    add_requirement(req, self.requirements)

    def load_txt(self, contents: bytes):
        """Load simple list of requirements from txt file."""
        deps = StringIO(contents.decode()).readlines()

        self.add_requirements([dep.strip() for dep in deps])

    def _get_dependencies(
        self,
        include_build_system: bool = True,
        remove: list[str] = None,
    ) -> tuple[list[str], list[str]]:
        """Get the default conda environment entries."""

        if remove is None:
            remove = []

        reqs = self.requirements.copy()
        if include_build_system:
            reqs = combine_requirements(reqs, self.build_system)

        _python = reqs.pop("python", None)

        _pip_packages = self.pip_packages
        # _pip_packages |= {r.name for r in reqs.values() if r.url}

        deps = [
            str(r)
            for r in reqs.values()
            if not r.url  # install via pip
            and r.name not in _pip_packages
            and r.name not in remove
        ]
        deps.sort(key=str.lower)
        if _python:
            deps = [str(_python)] + deps

        pip = [
            r
            for r in reqs.values()
            if (r.name in _pip_packages or r.url) and r.name not in remove
        ]
        # string formatting
        pip = [str(r) if not r.url else f"{r.name}@ {r.url}" for r in pip]
        pip.sort(key=str.lower)

        return deps, pip

    def export(
        self,
        outfile: str | Path = "environment.yaml",
        include_build_system: bool = True,
        remove: list[str] = None,
        name: str = None,
    ):
        """Export the environment to a yaml or txt file."""
        if remove is None:
            remove = []

        deps, pip = self._get_dependencies(
            include_build_system=include_build_system, remove=remove
        )

        conda_env = {
            "name": name,
            "channels": self.channels,
            "dependencies": deps.copy(),
        }
        if pip:
            if "pip" not in self.requirements:
                conda_env["dependencies"] += ["pip"]
            conda_env["dependencies"] += [{"pip": pip}]

        conda_env = {k: v for k, v in conda_env.items() if v}

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
                warn(
                    f"Unknown environment format `{p.suffix}`, generating conda yaml output."
                )
            with open(p, "w") as outfile:
                yaml.dump(conda_env, outfile, default_flow_style=False, sort_keys=False)

    def combine(self, other: Environment):
        """Merge other Environment requirements into this Environment."""
        self.requirements = combine_requirements(self.requirements, other.requirements)
        self.build_system = combine_requirements(self.build_system, other.build_system)
        self.pip_packages = self.pip_packages | other.pip_packages
