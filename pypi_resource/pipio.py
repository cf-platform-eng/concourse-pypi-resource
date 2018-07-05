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
import re
import warnings
from typing import List
from urllib.parse import urlsplit, urlunsplit

from pip._internal.basecommand import SUCCESS, Command
from pip._internal.commands import DownloadCommand as PipDownloadCommand
from pip._internal.commands import SearchCommand as PipSearchCommand
from pip._internal.download import PipXmlrpcTransport
from pip._internal.exceptions import CommandError
from pip._internal.operations.prepare import RequirementPreparer
from pip._internal.req import RequirementSet
from pip._internal.status_codes import NO_MATCHES_FOUND
from pip._internal.utils.misc import ensure_dir, normalize_path
from pip._internal.utils.temp_dir import TempDirectory
from pip._vendor.packaging.version import Version
from pip._vendor.six.moves import xmlrpc_client


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

        options.src_dir = os.path.abspath(options.src_dir)
        options.download_dir = normalize_path(options.download_dir)

        ensure_dir(options.download_dir)

        with self._build_session(options) as session:
            finder = self._build_package_finder(
                options=options,
                session=session,
                platform=options.platform,
                python_versions=python_versions,
                abi=options.abi,
                implementation=options.implementation,
            )            
            candidates = []
            for pkg in args:
                candidates.extend(finder.find_all_candidates(pkg))

        self.candidates = candidates


def _is_deprecated_python_version(python_version):
    if python_version:
        return not re.match(r'\d+(\.\d+){0,2}', python_version) is None
    return False


def _input_to_download_args(input, destdir=None):
    package_name = input['source']['name']
    package_version = input['version']['version']

    args = [ '--no-deps' ]

    # abi
    # implementation
    # platform
    if input['pre_releases']:
        args.append('--pre')

    python_version = input['source'].get('python_version', None)
    if _is_deprecated_python_version(python_version):
        if input['source'].get('python_version','') == 'source':
            args.extend( ['--no-binary', ':all:'] )
        else:
            warnings.warn('python_version format is deprecated. Only "source" or numeric python version allowed.', DeprecationWarning)
    elif python_version is not None:
        args.extend([ '--python-version', python_version ])

    if destdir:
        args.extend( [ '--dest', destdir ])

    if 'index_url' in input['source']:
        args.extend( ['--index-url', get_pypi_url(input, kind='index')] )

    args.append(package_name + ('==' + package_version if package_version else ''))
    return args


def get_pypi_repository(input):
    if 'repository' in input['source']:
        return input['source']['repository']
    elif input['source']['test']:
        return 'pypitest'
    return 'pypi'


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


def get_versions_from_pip(resconfig):
    args = _input_to_download_args(resconfig)

    cmd = ListVersionsCommand()
    if cmd.main(args) == 0:
        versions = [x.version for x in cmd.candidates]
        return versions
    else:
        return []


def pip_download(resconfig, destdir):
    args = _input_to_download_args(resconfig, destdir=destdir)

    cmd = PipDownloadCommand()
    result = cmd.main(args)
    return result == 0
