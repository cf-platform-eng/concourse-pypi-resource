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

import unittest
from unittest.mock import Mock
import json
import os
import subprocess

from pypi_resource import *

THISDIR = os.path.dirname(os.path.realpath(__file__))
REPODIR = os.path.join(THISDIR, '..')

class TestPut(unittest.TestCase):

    def test_out(self):
        subprocess.check_call(['python', 'setup.py', 'sdist'], cwd=REPODIR)
        out.out(
            os.path.join(REPODIR, 'dist'),
            {
                'source': {
                    'test': True,
                },
                'params': {
                    'glob': '*.tar.gz',
                }
            }
        )

if __name__ == '__main__':
    unittest.main()
