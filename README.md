# PyPI Package Resource
A [Concourse CI](http://concourse.ci) resource for Python [PyPI](https://pypi.python.org/pypi) packages.

Docker image publicly available on Docker Hub: https://hub.docker.com/r/cfplatformeng/concourse-pypi-resource/.

## Source Configuration
* `name`: *Required* The name of the package.
* `username`: *Required for `out`* The username for PyPI server authentication.
* `password`: *Required for `out`* The password for PyPI server authentication.
* `test`: *Optional, default `false`* Set to `true` to use the [PyPI test server](https://testpypi.python.org/pypi).

### Example
``` yaml
resource_types:
- name: pypi
  type: docker-image
  source:
    repository: cfplatformeng/concourse-pypi-resource

resources:
- name: my-pypi-package
  type: pypi
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
- put: my-pypi-package
  params:
    glob: my_package-*.tar.gz
```

## Development
To run the unit tests, go to the root of the repository and run:

``` sh
PYTHONPATH=.:$PYTHONPATH python test/unittests.py
```

To build the docker image for the resource:
``` sh
python setup.py sdist
docker build -t <username>/concourse-pypi-resource .
```
