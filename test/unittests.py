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
import io
import json
import os
import sys

from unittest.mock import patch
from pypi_resource import *
from distutils.version import LooseVersion

from pypi_resource import check, common, in_, pypi

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

def make_input_nexus3(version):
    # https://help.sonatype.com/repomanager3/pypi-repositories#PyPIRepositories-HostingPyPIRepositories
    return {
        'source': {
            'name': 'somedemo',
            'username': 'admin',
            'password': 'admin123',
            'authenticate': 'always',
            'index_url': 'http://localhost:8081/repository/pypi-private/simple',
            'repository_url': 'http://localhost:8081/repository/pypi-private/',
        },
        'version': version,
    }

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
    def setUp(self):
        newout = io.StringIO()
        sys.stdout = newout

    def tearDown(self):
        self.assertEqual(sys.stdout.getvalue(), '', '%s sent text to stdout and this is not allowed' % self._testMethodName)

    def test_pip_search_parser(self):
        expected_text = ['1.3.0', '1.4.1', '1.5.0', '1.5.1', '1.6.0', '1.6.1', '1.6.2', '1.7.0', '1.7.1', '1.7.2', '1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.9.2', '1.9.3', '1.10.0.post2', '1.10.1', '1.10.2', '1.10.4', '1.11.0b3', '1.11.0rc1', '1.11.0rc2', '1.11.0', '1.11.1rc1', '1.11.1', '1.11.2rc1', '1.11.2', '1.11.3', '1.12.0b1', '1.12.0rc1', '1.12.0rc2', '1.12.0', '1.12.1rc1', '1.12.1', '1.13.0rc1', '1.13.0rc2', '1.13.0', '1.13.1', '1.13.3', '1.14.0rc1', '1.14.0', '1.14.1', '1.14.2', '1.14.3', '1.14.4', '1.14.5', '1.15.0rc1']
        expected_vers = sorted([LooseVersion(x) for x in expected_text])

        lines = read_file(os.path.join(here, 'pip-search.lst'))
        self.assertGreater(len(lines), 0)

        versions = sorted(pypi._pip_search_to_versions(lines))
        self.assertListEqual(expected_vers, versions)

    def test_pypi_url(self):
        input = {'source': { 'repository_url': 'http://example.org/pypi' } }
        self.assertEqual(pypi.get_pypi_url(input), 'http://example.org/pypi')
        input = {'source': { 'test': True } }
        self.assertEqual(pypi.get_pypi_url(input), 'https://testpypi.python.org/pypi')
        input = {'source': { 'test': False } }
        self.assertEqual(pypi.get_pypi_url(input), 'https://pypi.python.org/pypi')

        input = {'source': { 'test': False, 'authenticate': 'always', 'username': 'u', 'password': 'p' } }
        self.assertEqual(pypi.get_pypi_url(input, 'in'), 'https://u:p@pypi.python.org/pypi')        
        input = {'source': { 'test': False, 'username': 'u', 'password': 'p' } }
        self.assertEqual(pypi.get_pypi_url(input, 'in'), 'https://pypi.python.org/pypi')        
        input = {'source': { 'test': False, 'username': 'u', 'password': 'p' } }
        self.assertEqual(pypi.get_pypi_url(input, 'out'), 'https://u:p@pypi.python.org/pypi')        

        input = make_input_nexus3('')
        self.assertEqual(pypi.get_pypi_url(input, 'out'), 'http://admin:admin123@localhost:8081/repository/pypi-private/')           

    def test_pypi_repo(self):
        input = {'source': { 'repository': "example_repo" } }
        self.assertEqual(pypi.get_pypi_repository(input), 'example_repo')
        input = {'source': { 'test': True } }
        self.assertEqual(pypi.get_pypi_repository(input), 'pypitest')
        input = {'source': { 'test': False } }
        self.assertEqual(pypi.get_pypi_repository(input), 'pypi')

    @patch('pypi_resource.pypi.get_pypi_package_info')
    def test_get_versions_from_pypi(self, mock_info):
        mock_info.return_value = canned_pypi_info
        input = make_input('0.9.2')
        result = pypi._get_versions_from_pypi(input)
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

# class TestIn(unittest.TestCase):
#     def test_parse_filename_from_url(self):
#         url = 'https://testpypi.python.org/packages/d6/7f/adacf6e8b1078f0338d71782911ea2f8822d89d2cb816688b5363e34bc09/tile_generator-0.9.1.tar.gz'
#         filename = 'tile_generator-0.9.1.tar.gz'
#         self.assertEqual(in_.parse_filename_from_url(url), filename)

#     def test_local_download_path(self):
#         url = 'https://testpypi.python.org/packages/d6/7f/adacf6e8b1078f0338d71782911ea2f8822d89d2cb816688b5363e34bc09/tile_generator-0.9.1.tar.gz'
#         filename = 'tile_generator-0.9.1.tar.gz'
#         destdir = 'output'
#         expected = os.path.join(destdir, filename)
#         self.assertEqual(in_.local_download_path(url, destdir), expected)

class TestCommon(unittest.TestCase):
    def test_is_release(self):
        self.assertTrue(common.is_release(LooseVersion('0.9.1')))
        self.assertFalse(common.is_release(LooseVersion('1.1.2.dev21')))
        self.assertFalse(common.is_release(LooseVersion('1.1.2-dev.21')))

if __name__ == '__main__':
	unittest.main()
