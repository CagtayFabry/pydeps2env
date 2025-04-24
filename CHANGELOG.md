# pydeps2env

## v1.4.1

### fixed

- fixed pip markers in conda packages and add test case [#80]
- fixed url not set for existing requirements [#80]

## v1.4.0

### added

- added `additional_requirements` option to github action [#77]

### fixed

- fixed conda package name conversion if package is listed to be pip-installed [#77]

## v1.3.0

### added

- support renaming of pip/conda packages based on repository mapping [#57]

### fixed

- remove extras definitions from build system requirements [#57]

## v1.2.0

### added
- add support for GitLab instances with token authentication [#45]
