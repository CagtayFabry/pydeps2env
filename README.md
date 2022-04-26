# pydeps2env

An easy way to manage create conda environemnt files from you python project dependencies.  
Creates a conda `environment.yml` file from python package dependencies listed in a `setup.cfg` file.

## basic usage

By default, the action will parse a `setup.cfg` file in your root directory into `environment.yml`. Here is an example
of a simple setup:

```yaml
steps:
  - uses: CagtayFabry/pydeps2env@v0.1.0
```

```cfg
[options]
python_requires = >=3.8,<3.10
setup_requires =
    setuptools >=38.3.0
    setuptools_scm
install_requires =
    numpy >=1.20
    pandas >=1.0

[options.extras_require]
test =
    pytest
```

The default parameters will output this `environment.yml`:

```yaml
channels:
  - defaults
dependencies:
  - python>=3.8
  - numpy>=1.20
  - pandas>=1.0
```

## configuration options

To customize the output the input options are available to the action:

### file

Specify the location of the 'setup.cfg' file to parse. (defaults to 'setup.cfg')

### output:

Specify the location and name of the conda environment file to generate. (defaults to 'environment.yml')

### channels:

List the conda channels to include in the environment file. (defaults to 'defaults')
Separate a list of multiple channels by spaces (e.g. 'conda-forge defaults').

### extras:

Specify one or more optional [extras_require] sections to add to the environment (e.g. 'test' to include package that
you would normally install with 'pip install pkg[test]')

### setup_requires:

if set to 'include' the dependencies listed under [options]:setup_requires will be added to the environment (default
is 'omit' so no setup dependencies will be installed)

## example

```yaml
steps:
  - uses: CagtayFabry/pydeps2env@main
    with:
      file: './test/setup.cfg'
      output: 'environment_test.yml'
      channels: 'conda-forge defaults'
      extras: 'test'
      setup_requires: 'include'
```

```cfg
[options]
python_requires = >=3.8,<3.10
setup_requires =
    setuptools >=38.3.0
    setuptools_scm
install_requires =
    numpy >=1.20
    pandas >=1.0

[options.extras_require]
test =
    pytest
```

```yaml
channels:
  - conda-forge
  - defaults
dependencies:
  - python>=3.8,<3.10
  - setuptools>=38.3.0
  - setuptools_scm
  - numpy>=1.20
  - pandas>=1.0
  - pytest
```
