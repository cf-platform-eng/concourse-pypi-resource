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

import os
import sys
from contextlib import redirect_stdout
from typing import List, Tuple
from urllib.parse import urlsplit, urlunsplit

from pip._internal.commands import DownloadCommand as PipDownloadCommand
from pip._vendor.packaging.version import Version
from pip._internal.req import RequirementSet

from . import common, out


class ListVersionsCommand(PipDownloadCommand):

    def __init__(self, *args, **kw):
        super(ListVersionsCommand, self).__init__(*args, **kw)

    def run(self, options, args):
        options.ignore_installed = True
        options.editables = []

        if options.python_version:
            python_versions = [options.python_version]
        else:
            python_versions = None

        with self._build_session(options) as session:
            finder = self._build_package_finder(
                options=options,
                session=session,
                platform=options.platform,
                python_versions=python_versions,
                abi=options.abi,
                implementation=options.implementation,
            )

            requirement_set = RequirementSet(
                require_hashes=options.require_hashes,
            )
            self.populate_requirement_set(
                requirement_set,
                args,
                options,
                finder,
                session,
                self.name,
                None
            )

            candidates = []
            for req in requirement_set.requirements.values():
                # extract from finder.find_requirement
                all_candidates = finder.find_all_candidates(req.name)      
                candidates.extend(all_candidates)

        self.candidates = candidates


def _input_to_download_args(resconfig, destdir=None) -> List[str]:
    package_name = resconfig['source']['name']
    package_version = resconfig['version']['version']

    args = ['--no-deps', ]

    # abi
    # implementation
    # platform
    if resconfig['source']['pre_release']:
        args.append('--pre')

    if resconfig['source']['packaging'] == 'source':
        args.extend(['--no-binary', ':all:'])
    elif resconfig['source']['packaging'] == 'binary':
        args.extend(['--only-binary', ':all:'])

    if resconfig['source']['python_version']:
        args.extend(['--python-version', resconfig['source']['python_version']])

    if destdir:
        args.extend(['--dest', destdir])

    if 'index_url' in resconfig['source']['repository']:
        url, hostname = get_pypi_url(resconfig, kind='index')
        args.extend(['--index-url', url,
                     '--trusted-host', hostname])

    args.append(package_name + ('=={}'.format(package_version) if package_version else ''))
    return args


def get_pypi_repository(resconfig) -> str:
    if 'name' in resconfig['source']['repository']:
        return resconfig['source']['repository']['name']
    elif resconfig['source']['test']:
        return 'pypitest'
    return 'pypi'


def get_pypi_url(input, mode='in', kind='repository') -> Tuple[str, str]:
    repocfg = input['source']['repository']

    key = '%s_url' % (kind,)
    if key in repocfg:
        url = repocfg[key]
    elif input['source']['test']:
        url = 'https://testpypi.python.org/pypi'
    else:
        url = 'https://pypi.python.org/pypi'
    
    url_parts = urlsplit(url)

    if mode == 'out' or repocfg.get('authenticate', None) == 'always':
        host_login = '%s:%s@%s' % (
            repocfg.get('username', ''),
            repocfg.get('password', ''),
            url_parts[1]
        )
        host_login = host_login.lstrip(':@')
    else:
        host_login = url_parts[1]

    url = urlunsplit((
        url_parts[0],
        host_login,
        url_parts[2],
        url_parts[3],
        url_parts[4]
    ))

    hostname = url_parts[1].split(':')[0]
    return url, hostname


def get_versions_from_pip(resconfig) -> List[Version]:
    args = _input_to_download_args(resconfig)

    with redirect_stdout(sys.stderr):
        cmd = ListVersionsCommand()
        rc = cmd.main(args)
        if rc == 0:
            candidates = cmd.candidates
        else:
            common.msg("List Versions returned {}", rc)
            candidates = []

    # https://www.python.org/dev/peps/pep-0440
    if not resconfig['source']['pre_release']:
        candidates = filter(lambda x: not (x.version.is_prerelease or x.version.is_devrelease), candidates)
    if not resconfig['source']['release']:
        candidates = filter(lambda x: (x.version.is_prerelease or x.version.is_devrelease), candidates)

    if resconfig['source'].get('filename_match', None):
        matchstr = resconfig['source']['filename_match']
        candidates = filter(lambda x: matchstr in x.location.filename, candidates)

    versions = {x.version for x in candidates}
    versions = list(sorted(versions))
    return versions


def pip_download(resconfig, destdir) -> str:
    args = _input_to_download_args(resconfig, destdir=destdir)

    with redirect_stdout(sys.stderr):
        cmd = PipDownloadCommand()
        result = cmd.main(args)
        
    if result == 0:
        destfiles = os.listdir(destdir)
        assert len(destfiles) == 1
        version = resconfig['version']['version']
        if not version:
            version = out.get_package_version(destfiles[0])
            common.msg("downloaded a latest version which identified as {}", version)
            
        return str(version)
    
    else:
        return None
