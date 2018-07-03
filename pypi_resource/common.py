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

def msg(msg):
    print(msg, file=sys.stderr)

def merge_defaults(input):
    source = input['source']

    if not 'test' in source:
        source['test'] = False

    if not 'authenticate' in source:
        source['authenticate'] = 'out'
    
    assert source['authenticate'] in ['out', 'always']

def is_release(version):
    return re.match('^\d+(\.\d+)*$', str(version))
