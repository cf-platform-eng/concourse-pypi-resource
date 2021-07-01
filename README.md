# PyPI Package Resource
A [Concourse CI](http://concourse.ci) resource for Python [PyPI](https://pypi.org) packages.

It can be used to check/download existing packages and to manages your own builds as well. Internally it uses [Pip 10.0.1](https://pip.pypa.io/en/stable/reference/pip_download/#options) for *check* and *in* (downloads) and [twine](https://twine.readthedocs.io/en/latest/) for *out*put.

Docker image publicly available on Docker Hub: https://hub.docker.com/r/cfplatformeng/concourse-pypi-resource.

## Resource Configuration

|Parameter                   |default|status   |description
|----------------------------|-------|---------|-----------
|__PACKAGE SELECTION__
|`name`                      |-       |required | name of the package
|`name_must_match  `         |`true`  |optional | require the project name and the packge name to match (see [PEP-423](https://www.python.org/dev/peps/pep-0423/#use-a-single-name))
|`pre_release`               |`false` |optional | check dev and pre-release versions (see [PEP-440](https://www.python.org/dev/peps/pep-0440))
|`release`                   |`true`  |optional | check release versions
|`filename_match`            |-/-     |optional | only include packages containing this string (e.g. `py2.py3`, `.whl`)
|`packaging`                 |`any`   |optional | only include `source` or `binary` (or `any`) packages
|`platform`                  |-/-     |optional | only include releases compatible with this platform (implicit default will be the os used for Concourse's workers)
|`python_abi`                |-/-     |optional | TODO
|`python_implementation`     |-/-     |optional | TODO
|`python_version`            |-/-     |optional | only include packages compatible with this Python interpreter version number (see [pip's `--python-version`]((https://pip.pypa.io/en/stable/reference/pip_download/#options)))
|__REPOSITORY__
|`repository.test`           |`false` |optional | set to `true` as shortcut to use the [PyPI test server](https://test.pypi.org/) for `index_url` and `repository_url`
|`repository.index_url`      |[PyPI](https://pypi.org/simple)|optional         | url to a pip compatible index for check and download
|`repository.repository_url` |[PyPI](https://upload.pypi.org/legacy)|optional         | url to a twine compatible repository for upload
|`repository.username`       |-/-     |req. for uploads | username for PyPI server authentication
|`repository.password`       |-/-     |req. for uploads | password for PyPI server authentication
|`repository.authenticate`   |out     |optional         | set to `in` to authenticate to a private repo for check and download only, `always` to authenticate to a private repository for upload, check and download.

### Deprecated parameters (since version 0.2.0)
* `python_version`: gets mapped to `filename_match` if it's not a version number. `python_version` is now only used for the actual interpreter version to have a transparent mapping to pip.
* ~~`repository`~~: (special index-server name if it is specified in `~/.pypirc`). This is no longer available to the current implementation of check and in. Also there's no way to inject a `.pypirc` file into this Concourse resource type.
* `repository`, `test`, `username` and `password`: get mapped to `repository.<key>`. This allows to configure private repositories through a single yaml-map parameter value, thus removing redundancy from the pipeline.


## Examples
``` yaml
resource_types:
- name: pypi
  type: docker-image
  source:
    repository: cfplatformeng/concourse-pypi-resource

resources:
- name: my-public-package
  type: pypi
  source:
    name: my_package
    packaging: any
    repository:
      username: user
      password: pass

- name: my-private-package
  type: pypi
  source:
    name: my_package
    pre_release: true
    # In a live pipeline you would probably set the while repository configuration
    # through a single yaml parameter:
    # repository: ((my-private-repository))
    repository:
      authenticate: always
      index_url: http://nexus.local:8081/repository/pypi-private/simple
      repository_url: http://nexus.local:8081/repository/pypi-private/
      username: admin
      password: admin123
```

## `get`: Download the latest version
* `version.version`: *Optional*, defaults to latest version
* `count_retries`: *Optional* Number of maximum retry before the task fails. By default 20 times.
* `delay_between_retries`: *Optional* Time to wait in sec between two iterations of retry. By default 3s.

### Additional files populated
 * `version`: [Python version number](https://www.python.org/dev/peps/pep-0440/) of the downloaded package
 * `semver`: [Semver](https://semver.org/)-formatted version number that can be processed with a Concourse SemVer Resource.

### Example
```yaml
plan:
- get: my-public-package
- get: my-private-package
  version: {version: '4.2'}
```

## `put`: Upload a new version
* `glob`: *Required* A [glob](https://docs.python.org/2/library/glob.html) expression matching the package file to upload.

### Note
You can modify `count_retries` and `delay_between_retries` in `get_params` to give enough time to PyPi to make available your package.

### Example
```yaml
plan:
- put: my-pypi-package
  params:
    glob: 'task-out-folder/my_package-*.tar.gz'
  get_params:
    count_retries: 10
    delay_between_retries: 30
```

## Development
To run the unit tests, go to the root of the repository and run:

``` sh
# install pipenv
pip3 install --user pipenv
# setup and run unittests
make test
```

To build the docker image for the resource:
``` sh
# package
make dist
# optionally upload
make push
```

Run local test runs like this:
```sh
# check
docker run -i concourse-pypi-resource:latest-rc check < test/input/check-nexus.json | jq
# in
docker run --rm -i --volume destdir concourse-pypi-resource:latest-rc in destdir < test/input/in-nexus.json | jq
```

### Private repository integration tests (using Sonatype Nexus 3)
* Spin-up a docker instance of [Nexus 3](https://hub.docker.com/r/sonatype/nexus3):
  ```sh
  docker run -d -p 8081:8081 --name nexus sonatype/nexus3
  ```
* Create pypi hosted repositories called `pypi-private` and `pypi-release` (enable redeploy).
* Disable user anonymous access.

```sh
# ensure test-packages are built
make test
pipenv run python -m pytest "test/nexus-integration.py"
```

Test using Concourse CI. Check that the provided params match your repository.
```sh
fly -t test sp -p demo -c test/ci/pipeline.yml -l test/ci/params.yml
```

### Public Integration Tests
```sh
# provide login data to be able to upload concourse-pypi-resource
export TWINE_USERNAME=<...>
export TWINE_PASSWORD=<...>
python -m pytest -v test/pypi-integration.py 

# or skip the upload
python -m pytest -v -k 'not test_upload' test/pypi-integration.py 

```
