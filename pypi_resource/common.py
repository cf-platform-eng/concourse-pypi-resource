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

import re
import sys
from distutils.version import LooseVersion

import pkginfo

from . import pipio


def msg(msg, *args, **kwargs):
    print(msg.format(*args, **kwargs), file=sys.stderr)


def is_deprecated_python_version(python_version: str) -> bool:
    if python_version:
        match = re.fullmatch(r'\d+(\.\d+){0,2}', python_version)
        return not match
    return False


def py_version_to_semver(version: pipio.Version) -> str:
    try:
        if isinstance(version, pipio.Version):
            v = version
        else:
            v = pipio.Version(str(version))
        
        result = '.'.join([str(x) for x in v.release])
        if len(v.release) < 3:
            result += '.' + '.'.join((3 - len(v.release)) * ['0', ])

        if v.pre:
            letter, pre = v.pre
            if letter == 'a':
                letter = 'alpha'
            elif letter == 'b':
                letter = 'beta'
            result += '-{}.{}'.format(letter, pre)

        if v.post:
            msg("Post-release counter {} in '{}' is not supported by semver and will be ignored", v.post, version)
        if v.dev:
            result += '+dev{:06d}'.format(v.dev)

    except pipio.InvalidVersion as ex:
        msg("Failed to convert Python version '{}' to semver format", version)
        result = None

    return result


def check_source(resconfig):
    keys = set(resconfig['source'].keys())
    deprecated_keys = {
        'username',
        'password',
        'repository_url',
        'test',
    }
    available_keys = {
        'name',
        'repository',
        'filename_match',
        'packaging',
        'pre_release',
        'release',
        'test',
    }
    
    delta = keys.difference(available_keys, deprecated_keys)
    if delta:
        raise KeyError("UNKNOWN keys within source: {}".format(delta))

    delta = keys.intersection(deprecated_keys)
    if delta:
        msg("DEPRECATED but still accepted keys within source: {}", delta)
    
    if isinstance(resconfig['source'].get('repository', None), dict):
        keys = set(resconfig['source']['repository'].keys())
        available_keys = {
            'authenticate',
            'username',
            'password',
            'index_url',
            'repository_url',
            'test',
        }
        delta = keys.difference(available_keys)
        if delta:
            raise KeyError("UNKNOWN keys within source.repository: {}".format(delta))


def merge_defaults(resconfig):
    check_source(resconfig)
    
    #
    # setup source
    #
    source = resconfig['source']
    source.setdefault('pre_release', False)
    source.setdefault('release', True)
    source.setdefault('packaging', 'any')
    assert source['packaging'] in ['any', 'source', 'binary']

    # Mapping of python_version for concourse_pypi_resource <= 0.2.0
    # Python_version is now expected to by the version of the python interpreter.
    python_version = source.get('python_version', None)
    if is_deprecated_python_version(python_version):
        msg('WARNING: The <python_version> property value format is deprecated: "{}". ' +
            'Only python version numbers will be accepted in the future.', python_version)
        source.pop('python_version')
        if python_version == 'source':
            msg('Value will be mapped to <prefer_source: True>.')
            source['prefer_source'] = True
        else:
            # python_version is a tag like "py2.py3" that can be matched within the urls filename
            msg('Value will be mapped to <filename_match>.')
            source['filename_match'] = python_version
    source.setdefault('python_version', None)

    #
    # setup source.repository
    #
    repository = source.setdefault('repository', dict())
    if not isinstance(repository, dict):
        raise ValueError('ERROR: source.repository must be a dictionary (using names is deprecated).')
    repository.setdefault('authenticate', 'out')
    assert repository['authenticate'] in ['out', 'always']

    # move deprecated values from source to source.repository
    for key in ['username', 'password', 'repository_url', 'test']:
        if key in source:
            repository[key] = source.pop(key)

    if repository.get('test', False):
        repository['repository_url'] = 'https://testpypi.python.org/pypi'
        repository['index_url'] = 'https://testpypi.python.org/pypi'

    #
    # setup version
    #
    if not resconfig.get('version', None):
        resconfig['version'] = dict()
    resconfig['version'].setdefault('version', None)
    if resconfig['version'].get('version', None):
        resconfig['version']['version'] = pipio.Version(resconfig['version']['version'])

    return resconfig


def get_package_version(pkgpath):
    metadata = pkginfo.get_metadata(pkgpath)
    return LooseVersion(metadata.version)
