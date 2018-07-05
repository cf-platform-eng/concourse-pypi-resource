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

from . import pipio


def merge_defaults(resconfig):
    source = resconfig['source']

    source.setdefault('test', False)
    source.setdefault('pre_releases', False)

    if resconfig['version'].get('version', None):
        resconfig['version']['version'] = pipio.Version(resconfig['version']['version'])

    source.setdefault('authenticate', 'out')
    assert source['authenticate'] in ['out', 'always']
    
    return resconfig
