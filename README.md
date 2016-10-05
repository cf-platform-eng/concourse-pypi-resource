# PyPI Package Resource
A [Concourse CI](http://concourse.ci) resource for Python [PyPI](https://pypi.python.org/pypi) packages.

## Source Configuration
* `name`: *Required* The name of the package.
* `username`: *Required for `out`* The username for PyPI server authentication.
* `password`: *Required for `out`* The password for PyPI server authentication.
* `test`: *Optional, default `false`* Set to `true` to use the [PyPI test server](https://testpypi.python.org/pypi).

### Example
``` yaml
resources:
- name: my-pypi-package
  type: pypi-package
  source:
    name: my_package
    username: user
    password: pass
    test: false
```

## `get`: Download the latest version
No parameters.

### Example
``` yaml
plan:
- get: my-pypi-package
```

## `put`: Upload a new version
* `glob`: *Required* A [glob](https://docs.python.org/2/library/glob.html) expression matching the package file to upload.

### Example
``` yaml
plan:
- put: my-pacakge
  params:
    glob: my_package-*.tar.gz
```

## Development
To run the unit tests, go to the root of the repository and run:

``` sh
PYTHONPATH=.:$PYTHONPATH python test/unittests.py
```
