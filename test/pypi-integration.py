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
from .unittests import make_input_nexus3
import json
import os
import subprocess

from pypi_resource import out, pypi

THISDIR = os.path.dirname(os.path.realpath(__file__))
REPODIR = os.path.join(THISDIR, '..')

class TestPut(unittest.TestCase):

    def test_upload_pypi(self):
        rc = subprocess.run(['python', 'setup.py', 'sdist'], check=True, cwd=REPODIR)
        print("sdist returned", rc)
        out.out(
            os.path.join(REPODIR, 'dist'),
            {
                'source': { 'test': True },
                'params': { 'glob': '*.tar.gz' }
            }
        )     


class TestPip(unittest.TestCase):

    def test_search_public(self):
        input = {
            'source': {
                'name': 'numpy',
                'test': False,
            },
            'version': '',
        }
        versions = pypi.get_package_versions(input)
        self.assertGreater(len(versions), 5)


if __name__ == '__main__':
    unittest.main()
