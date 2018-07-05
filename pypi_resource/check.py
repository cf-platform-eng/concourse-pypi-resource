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

from bisect import bisect_left
import json
import sys


from . import common, pipio


def truncate_smaller_versions(lst, value):
    index = bisect_left(lst, value)
    return lst[index:] if index < len(lst) else [lst[-1]]


def check(instream):
    resconfig = json.load(instream)
    resconfig = common.merge_defaults(resconfig)

    versions = pipio.get_versions_from_pip(resconfig)
    if not resconfig['source']['pre_releases']:
        versions = filter(lambda x: not x.is_prerelease, versions)
    versions = list(sorted(versions))
    
    if resconfig.get('version', None):
        target_version = resconfig['version']['version']
        versions = truncate_smaller_versions(versions, target_version)

    versions = [{'version': str(version)} for version in versions]
    return versions


def main():
    print(json.dumps(check(sys.stdin)))

if __name__ == '__main__':
    main()
