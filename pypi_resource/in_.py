#!/usr/bin/env python

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
import glob
import json
import os
import sys

from . import common, pipio
from .retry import retry_wrapper


RETRIES = 20
DELAY = 3


def select_artefact_for_response(package_info, version: pipio.Version, artefact_index: int=0):
    """
    From the package_info returned by pip_get_version select a specific version/artefact and
    provide metadata for the response to Concourse.
    """
    item = package_info[version]
    artefacts = item['artefacts']

    metadata = item['metadata'].copy()

    # this artefact has been chosen to represent this version
    if artefact_index > len(artefacts):
        raise KeyError('no artefact{} found for version {}'.format(artefact_index, version))
    metadata.update(item['artefacts'][artefact_index])

    # list all artefacts that match the search pattern
    for i, artefact in enumerate(artefacts):
        metadata['artefact{:d}'.format(i)] = artefact['filename']

    return {
        'version': {'version': str(version)},
        'metadata': metadata,
    }


def download_version(resconfig, destdir):
    # fetch all matching versions/artifacts
    package_info = pipio.pip_get_versions(resconfig)
    if not package_info:
        raise ValueError("No matching packages found.")

    version = resconfig['version']['version']
    if not version:
        version = max(package_info.keys())
    artefacts = package_info[version]['artefacts']

    # select requested version
    if len(artefacts) > 1:
        common.msg("selecting first out of {} artefacts matching the selection criteria", len(artefacts))
    response = select_artefact_for_response(package_info, version)
    url = artefacts[0]['url']

    pipio.pip_download_link(resconfig, url, destdir)
    return response


def in_(destdir, instream):
    resconfig = json.load(instream)
    common.merge_defaults(resconfig)

    retries = resconfig.get('params', {}).get('count_retries', RETRIES)
    delay = resconfig.get('params', {}).get('delay_between_retries', DELAY)
    download = retry_wrapper(retries, delay)(download_version)
    response = download(resconfig, destdir)

    # fetch metadata from download
    wheel = glob.glob(os.path.join(destdir, '*.whl'))
    package_info_path = wheel[0] if wheel else destdir
    pkg_info = common.get_package_info(package_info_path)
    response['metadata'].update(pkg_info['metadata'])

    # provide other output files
    version = pkg_info['version']
    with open(os.path.join(destdir, 'version'), 'w') as file:
        file.write(str(version))
    semver = common.py_version_to_semver(str(version))
    if semver:
        with open(os.path.join(destdir, 'semver'), 'w') as file:
            file.write(semver)

    response['metadata'] = common.metadata_dict_to_kvlist(response['metadata'])
    return response


def main():
    destdir = sys.argv[1]
    common.msg('Output directory: {}', destdir)

    response = in_(destdir, sys.stdin)
    print(json.dumps(response))


if __name__ == '__main__':
    main()
