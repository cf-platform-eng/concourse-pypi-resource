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
import sys
from bisect import bisect_left
from typing import List

from . import common, pipio


def truncate_smaller_versions(lst: List, value: pipio.Version) -> List:
    if not lst:
        return []
    elif not value:
        return lst
    else:
        index = bisect_left(lst, value)
        return lst[index:] if index < len(lst) else [lst[-1]]


def check(instream):
    resconfig = json.load(instream)
    resconfig = common.merge_defaults(resconfig)

    versions = pipio.pip_get_versions(resconfig)

    if not resconfig['source']['pre_release']:
        versions = filter(lambda x: not (x.is_prerelease or x.is_devrelease), versions)
    if not resconfig['source']['release']:
        versions = filter(lambda x: (x.is_prerelease or x.is_devrelease), versions)

    versions = list(sorted(versions))
    common.msg("{}", versions)

    versions = truncate_smaller_versions(versions, resconfig['version']['version'])

    return [{'version': str(version)} for version in versions]


def main():
    print(json.dumps(check(sys.stdin)))


if __name__ == '__main__':
    main()
