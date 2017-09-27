# Copyright (c) 2016-Present Pivotal Software, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import common

from distutils.version import LooseVersion

import requests

def get_pypi_url(input):
    if input['source']['test']:
        return 'https://testpypi.python.org/pypi'
    return 'https://pypi.python.org/pypi'

def get_pypi_repository(input):
    if input['source']['test']:
        return 'pypitest'
    return 'pypi'

def get_pypi_package_info(input):
    package_name = input['source']['name']
    url = get_pypi_url(input) + '/' + package_name + '/json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_versions_from_pypi(input):
    pypi_info = get_pypi_package_info(input)
    versions = pypi_info['releases'].keys()
    versions = [version for version in versions if common.is_release(version)]
    versions = sorted(versions, key=LooseVersion)
    return versions

def get_pypi_version_url(input, version):
    pypi_info = get_pypi_package_info(input)
    return pypi_info['releases'][version][0]['url']
