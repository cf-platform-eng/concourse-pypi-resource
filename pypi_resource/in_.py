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

import json
import os
import sys

from . import common, pipio


def in_(destdir, instream):
    resconfig = json.load(instream)
    common.merge_defaults(resconfig)

    version = pipio.pip_download(resconfig, destdir)
    with open(os.path.join(destdir, 'version'), 'w') as file:
        file.write(version)
    
    semver = common.py_version_to_semver(version)
    if semver:
        with open(os.path.join(destdir, 'semver'), 'w') as file:
            file.write(semver)

    return str(version)


def main():
    destdir = sys.argv[1]
    common.msg('Output directory: {}', destdir)
    version = in_(destdir, sys.stdin)
    print(json.dumps({'version': {'version': version}}))


if __name__ == '__main__':
    main()
