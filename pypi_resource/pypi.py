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
from .retry import retry_wrapper

from distutils.version import LooseVersion
from typing import List
from urllib.parse import urlsplit, urlunsplit

import re
import requests
import subprocess
import sys


PIP_SEARCH_PATTERN = re.compile(r'\(from versions:([^\)]*)\)')


def get_pypi_url(input, mode='in', kind='repository'):
    key = '%s_url' % (kind,)

    if key in input['source']:
        url = input['source'][key]
    elif input['source']['test']:
        url = 'https://testpypi.python.org/pypi'
    else:
        url = 'https://pypi.python.org/pypi'
    
    url_parts = urlsplit(url)

    if mode == 'out' or input['source'].get('authenticate', None) == 'always':
        hostname = '%s:%s@%s' % (
            input['source'].get('username', ''),
            input['source'].get('password', ''),
            url_parts[1]
        )
    else:
        hostname = url_parts[1]

    url = urlunsplit((
        url_parts[0],
        hostname.lstrip(':@'),
        url_parts[2],
        url_parts[3],
        url_parts[4]
    ))

    return url


def _pip_search_to_versions(lines: List[str]) -> List[LooseVersion]:
    versions = []

    match = PIP_SEARCH_PATTERN.search(lines)
    if match:
        for ver_text in match.group(1).split(','):
            version = LooseVersion(ver_text.strip())
            versions.append(version)

    else:
        print("no versions found: '%s'" % (lines,), file=sys.stderr)

    return versions      


def _get_versions_from_pip(input):
    package_name = input['source']['name']

    pip_cmd = [
        'pip', 'install', '--no-deps', '--pre',
        '--disable-pip-version-check', '--no-color', '--ignore-installed',
    ]
    if 'repository_url' in input['source']:
        pip_cmd.append('--index')
        pip_cmd.append(get_pypi_url(input, kind='index'))
    pip_cmd.append('%s==' % (package_name,))

    proc = subprocess.run(pip_cmd, check=False, encoding='utf-8',
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)

    return _pip_search_to_versions(proc.stderr)


def download_with_pip(input):
    package_name = input['source']['name']
    package_version = input['version']['version']

    pip_cmd = [
        'pip', 'install', '--no-deps', '--pre',
        '--disable-pip-version-check', '--no-color', '--ignore-installed',
        '--dest', destdir,
    ]
    if 'index_url' in input['source']:
        pip_cmd.append('--index')
        pip_cmd.append(get_pypi_url(input, kind='index'))
    pip_cmd.append('%s==%s' % (package_name, package_version))

    proc = subprocess.run(pip_cmd, check=False, encoding='utf-8',
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)

    return proc.returncode == 0


def get_pypi_package_info(input):
    package_name = input['source']['name']
    url = get_pypi_url(input).rstrip('/') + '/' + package_name + '/json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def _get_versions_from_pypi(input):
    pypi_info = get_pypi_package_info(input)
    versions = pypi_info['releases'].keys()
    versions = [version for version in versions if common.is_release(version)]
    versions = sorted(versions, key=LooseVersion)
    return versions


def get_pypi_repository(input):
    if 'repository' in input['source']:
        return input['source']['repository']
    elif input['source']['test']:
        return 'pypitest'
    return 'pypi'


def get_package_versions(input):
    url = get_pypi_url(input, kind='index')
    print(url)
    if url.endswith('simple'):
        versions = _get_versions_from_pip(input)

    else:
        versions = _get_versions_from_pypi(input)

    return versions


@retry_wrapper(5, 1)
def get_pypi_version_url(input, version):
    pypi_info = get_pypi_package_info(input)
    files = pypi_info['releases'][version]
    if 'python_version' not in input['source']:
        return files[0]['url']
    for file in files:
        if file['python_version'] == input['source']['python_version']:
            return file['url']
    raise LookupError("No %s download found" % input['source']['python_version'])

