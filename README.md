# PyPI Package Resource
A [Concourse CI](http://concourse.ci) resource for Python [PyPI](https://pypi.python.org/pypi) packages.

Docker image publicly available on Docker Hub: https://hub.docker.com/r/cfplatformeng/concourse-pypi-resource/.

## Source Configuration

  * `name`: *Required* The name of the package.
  * `python_version`: *Optional* Package type, if multiple files have been uploaded for a package (e.g. source tarballs and wheels), download the file for the specified version instead of the file that was first uploaded.

__Authentication__

  * `username`: *Required for `out`, optional for `in`*
    The username for PyPI server authentication.
  * `password`: *Required for `out`, optional for `in`*
     The password for PyPI server authentication.
  * `authenticate`: *Optional, default `out`*
     Set to `always` to authenticate for read operations too.

__Repository__

  * `test`: *Optional, default `false`* Set to `true` to use the [PyPI test server](https://testpypi.python.org/pypi).
  * `repository_url`: *Optional* Set to a another pypi server such as pypicloud.
  * `repository`: *Optional* Set to a special index-server name if it is specified in `~/.pypirc`.


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
    python_version: source

- name: my-private-package
  type: pypi
  source:
    name: my_package
    username: admin
    password: admin123
    authenticate: always
    index_url: http://localhost:8081/repository/pypi-private/simple
    repository_url: http://localhost:8081/repository/pypi-private/
    python_version: source

```

## `get`: Download the latest version
No parameters.
__TODO__
 * `version`: *Optional, defaults to `latest`*

### Additional files populated
 * `version`: the latest version

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
pipenv --three install --dev
pipenv run python -m pytest -v test/unittests.py
```

To build the docker image for the resource:
``` sh
python setup.py sdist
docker build -t <username>/concourse-pypi-resource .
```

### Nexus Integration Tests
* Spin-up a docker instance of Nexus 3:
  ```sh
  docker run -d -p 8081:8081 --name nexus sonatype/nexus3
  ```
* Create a pypi hosted repo `pypi-private`.
* Disable user anonymous access.

```sh
python setup.py sdist
pipenv run python -m pytest test/nexus-integration.py
```

### Public Integration Tests
```sh
# provide login data to be able to upload concourse-pypi-reousource
export TWINE_USERNAME=<...>
export TWINE_PASSWORD=<...>
python -m pytest -v test/pypi-integration.py 

# or skip the upload
python -m pytest -v -k 'not test_upload' test/pypi-integration.py 

```