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

from . import common, pypi

import json
import os
import sys
from urllib.parse import urlparse

import requests

def download(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

def parse_filename_from_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    return os.path.basename(path)

def local_download_path(url, destdir):
    basename = parse_filename_from_url(url)
    return os.path.join(destdir, basename)

def in_(destdir, instream):
    input = json.load(instream)
    common.merge_defaults(input)
    version = input['version']['version']
    if common.is_release(version):
        url = pypi.get_pypi_version_url(input, version)
        dest = local_download_path(url, destdir)
        download(url, dest)
        version_dest = os.path.join(destdir, 'version')
        with open(version_dest, 'w+') as file:
            file.write(version)
    else:
        common.msg('Version {} is not a release; skipping download'.format(version))
    return version

def main():
    destdir = sys.argv[1]
    common.msg('Output directory: {}'.format(destdir))
    version = in_(destdir, sys.stdin)
    print(json.dumps({'version': {'version': version}}))
    sys.exit(0)

if __name__ == '__main__':
    main()
