import pytest
from pydeps2env import Environment

_inputs = [
    "./test/pyproject.toml[test]",
    "./test/setup.cfg[test]",
    "./test/requirements.txt",
    "./test/environment.yaml",
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
