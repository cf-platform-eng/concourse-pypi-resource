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
from unittest.mock import patch
from pypi_resource import *
from distutils.version import LooseVersion
import io
import json
import os

def read_file(file):
    with open(file) as f:
        return f.read()

here = os.path.dirname(os.path.realpath(__file__))
canned_pypi_info = json.loads(read_file(os.path.join(here, 'pypi-package-info.json')))

def make_stream(json_obj):
    stream = io.StringIO()
    json.dump(json_obj, stream)
    stream.seek(0)
    return stream

def make_input(version):
    return {
        'source': {
            'name': 'tile-generator',
            'username': 'username',
            'password': 'password',
            'test': False,
        },
        'version': version,
    }

def make_input_stream(version):
    return make_stream(make_input(version))

class TestPypi(unittest.TestCase):
    def test_pypi_url(self):
        input = {'source': { 'test': True } }
        self.assertEqual(pypi.get_pypi_url(input), 'https://testpypi.python.org/pypi')
        input = {'source': { 'test': False } }
        self.assertEqual(pypi.get_pypi_url(input), 'https://pypi.python.org/pypi')

    def test_pypi_url(self):
        input = {'source': { 'test': True } }
        self.assertEqual(pypi.get_pypi_repository(input), 'pypitest')
        input = {'source': { 'test': False } }
        self.assertEqual(pypi.get_pypi_repository(input), 'pypi')

    @patch('pypi_resource.pypi.get_pypi_package_info')
    def test_get_versions_from_pypi(self, mock_info):
        mock_info.return_value = canned_pypi_info
        input = make_input('0.9.2')
        result = pypi.get_versions_from_pypi(input)
        self.assertEqual(list(result), ['0.9.1', '0.9.2'])

    @patch('pypi_resource.pypi.get_pypi_package_info')
    def test_get_version_url(self, mock_info):
        mock_info.return_value = canned_pypi_info
        version = '0.9.1'
        input = make_input(version)
        result = pypi.get_pypi_version_url(input, version)
        self.assertEqual(result, 'https://testpypi.python.org/packages/d6/7f/adacf6e8b1078f0338d71782911ea2f8822d89d2cb816688b5363e34bc09/tile_generator-0.9.1.tar.gz')

class TestCheck(unittest.TestCase):
    def test_truncate_before(self):
        self.assertEqual(check.truncate_before([1, 2, 3], 1), [1, 2, 3])
        self.assertEqual(check.truncate_before([1, 2, 3], 2), [2, 3])
        self.assertEqual(check.truncate_before([1, 2, 3], 3), [3])
        self.assertEqual(check.truncate_before([1, 2, 3], 4), [3])

    @patch('pypi_resource.pypi.get_pypi_package_info')
    def test_newest_version(self, mock_info):
        mock_info.return_value = canned_pypi_info
        version = {'version': {'version': '0.9.2'}}
        instream = make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(result, [version['version']])

    @patch('pypi_resource.pypi.get_pypi_package_info')
    def test_has_newer_version(self, mock_info):
        mock_info.return_value = canned_pypi_info
        version = {'version': {'version': '0.9.1'}}
        instream = make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(result, [{'version': '0.9.1'}, {'version': '0.9.2'}])

class TestIn(unittest.TestCase):
    def test_parse_filename_from_url(self):
        url = 'https://testpypi.python.org/packages/d6/7f/adacf6e8b1078f0338d71782911ea2f8822d89d2cb816688b5363e34bc09/tile_generator-0.9.1.tar.gz'
        filename = 'tile_generator-0.9.1.tar.gz'
        self.assertEqual(in_.parse_filename_from_url(url), filename)

    def test_local_download_path(self):
        url = 'https://testpypi.python.org/packages/d6/7f/adacf6e8b1078f0338d71782911ea2f8822d89d2cb816688b5363e34bc09/tile_generator-0.9.1.tar.gz'
        filename = 'tile_generator-0.9.1.tar.gz'
        destdir = 'output'
        expected = os.path.join(destdir, filename)
        self.assertEqual(in_.local_download_path(url, destdir), expected)

class TestCommon(unittest.TestCase):
    def test_is_release(self):
        self.assertTrue(common.is_release(LooseVersion('0.9.1')))
        self.assertFalse(common.is_release(LooseVersion('1.1.2.dev21')))
        self.assertFalse(common.is_release(LooseVersion('1.1.2-dev.21')))

if __name__ == '__main__':
	unittest.main()
