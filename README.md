# pydeps2env

An easy way to create conda environment files from you python project dependencies.  
Creates a conda `environment.yml` file from python package dependencies listed in on or multiple different source formats like `pyproject.toml`, `setup.cfg`, `environment.yaml` or `requirements.txt` files.

The project contains
- GitHub action
- python package
- command line script

```mermaid
flowchart LR
    pyproject.toml --> pydeps2env
    setup.cfg --> pydeps2env
    environment.yaml --> pydeps2env
    requirements.txt --> pydeps2env
    pydeps2env --> E2[environment.yaml]
    pydeps2env --> R2[requirements.txt]
```

## basic usage (GitHub action)

By default, the action will parse a `pyproject.toml` file in your root directory into `environment.yml`. Here is an example
of a simple setup:

```yaml
steps:
  - uses: CagtayFabry/pydeps2env@v1.0.0
```

```toml
[project]
requires-python = ">=3.8,<3.10"
dependencies = [
    "numpy >=1.20",
    "pandas >=1.0",
    "IPython",
    "boltons",
]
[project.optional-dependencies]
test = ["pytest"]
pip_only = ["bidict"]
```

The default parameters will output this sorted `environment.yml` (note that the `python` dependency specification will always be the first item on the list):

```yaml
channels:
  - defaults
dependencies:
  - python>=3.8,<3.10
  - boltons
  - IPython
  - numpy>=1.20
  - pandas>=1.0
```

A full output with options `--build_system include --extras test pip_only --pip bidict`

```yaml
channels:
  - defaults
dependencies:
  - python>=3.8,<3.10
  - boltons
  - IPython
  - numpy>=1.20
  - pandas>=1.0
  - pytest
  - setuptools>=40.9.0
  - setuptools_scm
  - wheel
  - pip:
    - bidict
```

## basic usage (python)

Create an `Environment` using Python and export it to an `environment.yaml` file.

```python
from pydeps2env import Environment

env = Environment("./test/pyproject.toml[doc]")
env.export("my_environment.yaml")
```

## basic usage (command line)

Combine multiple source files into a single environment file (including build dependencies).
Install pandas using `pip`.

```bash
pydeps2env ./test/setup.cfg ./test/pyproject.toml[doc] ./test/environment.yaml ./test/requirements.txt -o output.yaml -c defaults --extras test -b include --pip pandas
```

## advanced usage (definition file)

Users can store complex configurations in a single yaml file and create the desired output using `create_from_definition`.
Example definition file:

```yaml
# the target file to create
output: test-configuration.yaml
# default name of the environment
name: test-env
# conda channels to include
channels:
- conda-forge
- defaults
# list of source files that define sub environments
# these will be loaded as Environment()
sources:
- ./test/environment.yaml
- ./test/local.yaml
- ./test/pyproject.toml[doc]
- ./test/requirements.txt
- https://github.com/CagtayFabry/pydeps2env/blob/custom_deps/pyproject.toml
# extras to apply to all sources and packages
extras:
- test
# dependencies that should be removed after collection
remove:
- pyyaml
additional_requirements:
- urllib3
# include build system dependencies
# list of dependencies that must be pip installed (excluding auto-sorted depedencies like urls)
pip:
- urllib3
include_build_system: include

```

## configuration options (GitHub action)

To customize the output the input options are available to the action:

### files

Specify the location of the dependencies files to parse. (defaults to 'pyproject.toml')
Multiple files can be listed. This will result in a combined environment file.

### output:

Specify the location and name of the conda environment file to generate. (defaults to `'environment.yml'`)

### channels:

List the conda channels to include in the environment file. (defaults to `'conda-forge'`)
Separate a list of multiple channels by spaces (e.g. `'conda-forge defaults'`).

### extras:

Specify one or more optional `[extras_require]` sections to add to all the environments (e.g. `'test'` to include package that
you would normally install with `pip install pkg[test]`).
Note that for individual packages, the [extra]` syntax is also possible.

### build_system:

If set to `'include'` the dependencies listed under `[build-system]` (or `[options:setup_requires]` in `setup.cfg`) will be added to the environment (default
is `'omit'` so no setup dependencies will be installed).

### pip
List of packages to install via `pip` instead of `conda`.
The dependencies will be listed under the `pip:` section in the environment file.
If a dependency is listed with its URN, it will always be installed via pip (e.g. `pydeps2env @ git+https://github.com/CagtayFabry/pydeps2env`)

## example

```yaml
steps:
  - uses: CagtayFabry/pydeps2env@v1.0.0
    with:
      files: ./test/pyproject.toml[doc] ./test/setup.cfg # comine both files, add [doc] only for pyproject.toml
      output: 'environment_test.yml'
      channels: 'conda-forge defaults'
      extras: 'test'
      build_system: 'include'
      pip: 'bidict'
```

```toml
[project]
requires-python = ">=3.8,<3.10"
dependencies = [
    "numpy >=1.20",
    "pandas >=1.0",
    "IPython",
    "boltons",
]
[project.optional-dependencies]
test = ["pytest"]
pip_only = ["bidict"]
```

```yaml
channels:
  - conda-forge
  - defaults
dependencies:
  - python>=3.8,<3.10
  - boltons
  - IPython
  - numpy>=1.20
  - pandas>=1.0
  - pytest
  - setuptools>=40.9.0
  - setuptools_scm
  - sphinx
  - wheel
  - pip:
    - bidict
```
