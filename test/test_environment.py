import pytest
from pydeps2env import Environment, create_environment, create_from_definition

_inputs = [
    "./test/pyproject.toml[test]",
    "./test/setup.cfg[test]",
    "./test/requirements.txt",
    "./test/environment.yaml",
    "./test/local.yaml",
    "https://raw.githubusercontent.com/BAMWelDX/weldx/master/pyproject.toml[test]",
    "https://github.com/BAMWelDX/weldx/blob/master/pyproject.toml[test]",
    "https://raw.githubusercontent.com/BAMWelDX/weldx/v0.3.2/setup.cfg[test]",
    # "https://raw.githubusercontent.com/BAMWelDX/weldx/master/doc/rtd_environment.yml",
]


class TestEnvironment:
    """Test base Environment class."""

    # test_init ------------------------------------------------------------------------

    @pytest.mark.parametrize("filename", _inputs)
    def test_init(
        self,
        filename: str,
    ):
        """Test the `__init__` method of the Environment class."""

        env = Environment(filename)
        assert "python" in env.requirements
        if filename.startswith("./test/pyproject.toml"):
            assert "pydeps2env" in env.requirements
            assert "pydeps2env" in env.pip_packages

            conda, pip = env._get_dependencies()
            assert (
                "pydeps2env@ git+https://github.com/CagtayFabry/pydeps2env.git" in pip
            )


def test_multiple_sources():
    env = create_environment(
        _inputs,
        extras=["test"],
        pip=["urllib3", "pandas"],
        additional_requirements=["k3d"],
    )

    for req in ["python", "pydeps2env", "testproject", "urllib3", "pytest", "k3d"]:
        assert req in env.requirements

    for req in ["testproject", "pydeps2env", "requests", "pandas"]:
        assert req in env.pip_packages

    conda, pip = env._get_dependencies()
    assert "pydeps2env@ git+https://github.com/CagtayFabry/pydeps2env.git" in pip
    assert "testproject@ file:/..//test_package" in pip


def test_definition():
    create_from_definition("./test/definition.yaml")


def test_definition_offline():
    """Ensure we can map pypi to conda pkgs, even if we cannot download a current mapping."""
    from unittest.mock import patch

    def dummy():
        from urllib.error import URLError

        raise URLError

    with patch("urllib.request.urlretrieve", dummy):
        create_environment(
            _inputs,
            extras=["test"],
            pip=["setuptools-scm", "weldx-widgets"],
            additional_requirements=["k3d"],
        )


def test_extra_requirements_in_pip_req():
    """Ensure extras defined by pip requirements are also being handled."""
    env = create_environment(
        _inputs,
        pip=["setuptools-scm[toml]"],
    )
    assert "toml" in env.build_system.keys()
