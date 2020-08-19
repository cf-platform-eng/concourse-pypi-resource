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

import requests
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from typing import Dict, List, Tuple
from urllib.parse import urlsplit, urlunsplit

from pip._internal.commands.download import DownloadCommand as PipDownloadCommand
from pip._internal.network.download import Downloader
from pip._internal.network.session import PipSession
from pip._internal.operations.prepare import unpack_url
from pip._internal.models.candidate import InstallationCandidate
from pip._internal.models.link import Link
from pip._internal.models.target_python import TargetPython
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.utils.temp_dir import global_tempdir_manager
from pip._vendor.packaging.version import Version, InvalidVersion # for other files

from . import common

TIMEOUT = 15
RETRIES = 5


class ListVersionsCommand(PipDownloadCommand):

    def __init__(self, *args, **kw):
        super(ListVersionsCommand, self).__init__(*args, **kw)

    def run(self, options, args):
        options.timeout = TIMEOUT
        options.retries = RETRIES
        options.ignore_installed = True
        options.editables = []

        with self._build_session(options) as session:
            finder = self._build_package_finder(
                options=options,
                session=session,
                target_python = TargetPython(
                    platform=options.platform,
                    py_version_info=options.python_version,
                    abi=options.abi,
                    implementation=options.implementation,
                ),
            )

            requirement_set = self.get_requirements(
                args,
                options,
                finder,
                session,
            )

            candidates = []
            for req in requirement_set:
                # extract from finder.find_requirement
                all_candidates = finder.find_all_candidates(req.name)
                candidates.extend(all_candidates)

        self.candidates = candidates
        return SUCCESS


def _input_to_download_args(resconfig, destdir=None) -> List[str]:
    """ Build pip download args from a resource configuration. """

    package_name = resconfig['source']['name']
    package_version = resconfig['version']['version']

    args = ['--no-deps', ]

    # TODO:
    # abi
    # implementation
    if resconfig['source']['pre_release']:
        args.append('--pre')

    if resconfig['source'].get('platform'):
        args.extend(['--platform', resconfig['source']['platform']])

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


def get_pypi_url(input, mode='in', kind='repository') -> Tuple[str, str]:
    """ Get a PyPi URL including authorization details. """
    repocfg = input['source']['repository']

    key = '%s_url' % (kind,)
    if key in repocfg:
        url = repocfg[key]    
    url_parts = urlsplit(url)

    authenticate = repocfg.get('authenticate', None)
    if authenticate == 'always' or authenticate == mode:
        host_login = '%s:%s@%s' % (
            repocfg.get('username', ''),
            repocfg.get('password', ''),
            url_parts[1]
        )
        host_login = host_login.lstrip(':@')
        url = urlunsplit((url_parts[0], host_login, url_parts[2], url_parts[3], url_parts[4]))

    hostname = url_parts[1].split(':')[0]
    return url, hostname


def _candidate_to_package_info_artefact(candidate: InstallationCandidate) -> Dict[str, str]:
    """ Provide artifact metadata """
    loc = candidate.link
    artefact = {
        'filename': loc.filename,
        'hash': '{}:{}'.format(loc.hash_name, loc.hash),
        'url': loc.url,
    }
    return artefact


def _pip_query_pypi_json(resconfig):
    package_name = resconfig['source']['name']
    index_url, unused_hostname = get_pypi_url(resconfig)
    url = '{}/{}/json'.format(index_url, package_name)

    response = requests.get(url)
    if response.ok:
        candidates = []
        data = response.json()
        for version, release_artefacts in data['releases'].items():
            for release in release_artefacts:
                candidates.append(InstallationCandidate(package_name, version, Link(release['url'])))
        return candidates

    return None


def _pip_query_candidates(resconfig) -> List[InstallationCandidate]:
    args = _input_to_download_args(resconfig)

    with redirect_stdout(sys.stderr):
        cmd = ListVersionsCommand('list versions', 'list versions')
        rc = cmd.main(args)
        # pip 10.0.1 returns 0 even on connection problems, which get output to stderr
        # but cannot be clearly distinguished from a successful 'not found'.
        if rc == 0:
            candidates = cmd.candidates
        else:
            common.msg("List Versions returned {}", rc)
            candidates = []

    return candidates


def pip_get_versions(resconfig) -> Dict[str, dict]:
    # JSON protocol query as used in version 0.2.0 could still be used here,
    # but does not include mechanisms of filtering (platform, abi, python_version,
    # packaging) that pip includes.
    # candidates = _pip_query_pypi_json(resconfig)
    candidates = _pip_query_candidates(resconfig)

    if resconfig['source'].get('filename_match', None):
        matchstr = resconfig['source']['filename_match']
        candidates = filter(lambda x: matchstr in x.link.filename, candidates)

    if not resconfig['source']['pre_release']:
        candidates = filter(lambda x: not (x.version.is_prerelease or x.version.is_devrelease), candidates)

    if not resconfig['source']['release']:
        candidates = filter(lambda x: (x.version.is_prerelease or x.version.is_devrelease), candidates)

    versions = dict()
    for candidate in candidates:
        version = versions.get(candidate.version, dict())
        if not version:
            version = {
                'artefacts': [],
                'metadata': {
                    'package_key': candidate.name,
                },
            }
            versions[candidate.version] = version
        version['artefacts'].append(_candidate_to_package_info_artefact(candidate))

    return versions


def pip_download_link(resconfig, url: str, destdir: str):
    with redirect_stdout(sys.stderr):

        netloc = urlsplit(resconfig['source']['repository']['index_url'])[1]
        hostname = netloc.split(':')[0]
        with PipSession(retries=RETRIES, trusted_hosts=[hostname, ]) as session:
            session.timeout = TIMEOUT
            session.auth.prompting = False
            session.auth.passwords[netloc] = (resconfig['source']['repository'].get('username', None),
                                              resconfig['source']['repository'].get('password', None))
            # pip internals hardcode global tempdir manager.
            # need to copy to destdir before tempdir gets blown away.
            with global_tempdir_manager():
                file = unpack_url(
                    Link(url),
                    destdir,
                    Downloader(session, "pretty"),
                )
                shutil.copy(file.path, destdir)
