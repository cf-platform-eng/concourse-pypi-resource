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

from pypi_resource import check, in_, pipio

def read_file(file):
    with open(file) as f:
        return f.read()

here = os.path.dirname(os.path.realpath(__file__))

canned_versions = list(map(pipio.Version, ["0.9.3rc1", "0.9.1", "0.9.2"]))

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

def make_input(version, **kwargs):
    resconfig = {
        'source': {
            'name': 'tile-generator',
            'test': False,
        },
        'version': version,
    }
    resconfig['source'].update(kwargs)
    return resconfig

def make_input_stream(version, **kwargs):
    return make_stream(make_input(version, **kwargs))

class TestPypi(unittest.TestCase):
    def setUp(self):
        newout = io.StringIO()
        sys.stdout = newout


    def tearDown(self):
        self.assertEqual(sys.stdout.getvalue(), '', '%s sent text to stdout and this is not allowed' % self._testMethodName)


    def test_pypi_url(self):
        input = {'source': { 'repository_url': 'http://example.org/pypi' } }
        self.assertEqual(pipio.get_pypi_url(input), 'http://example.org/pypi')
        input = {'source': { 'test': True } }
        self.assertEqual(pipio.get_pypi_url(input), 'https://testpypi.python.org/pypi')
        input = {'source': { 'test': False } }
        self.assertEqual(pipio.get_pypi_url(input), 'https://pypi.python.org/pypi')

        input = {'source': { 'test': False, 'authenticate': 'always', 'username': 'u', 'password': 'p' } }
        self.assertEqual(pipio.get_pypi_url(input, 'in'), 'https://u:p@pypi.python.org/pypi')        
        input = {'source': { 'test': False, 'username': 'u', 'password': 'p' } }
        self.assertEqual(pipio.get_pypi_url(input, 'in'), 'https://pypi.python.org/pypi')        
        input = {'source': { 'test': False, 'username': 'u', 'password': 'p' } }
        self.assertEqual(pipio.get_pypi_url(input, 'out'), 'https://u:p@pypi.python.org/pypi')        

        input = make_input_nexus3('')
        self.assertEqual(pipio.get_pypi_url(input, 'out'), 'http://admin:admin123@localhost:8081/repository/pypi-private/')           


    def test_pypi_repo(self):
        input = {'source': { 'repository': "example_repo" } }
        self.assertEqual(pipio.get_pypi_repository(input), 'example_repo')
        input = {'source': { 'test': True } }
        self.assertEqual(pipio.get_pypi_repository(input), 'pypitest')
        input = {'source': { 'test': False } }
        self.assertEqual(pipio.get_pypi_repository(input), 'pypi')


class TestCheck(unittest.TestCase):
    def test_truncate_before(self):
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 1), [1, 2, 3])
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 2), [2, 3])
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 3), [3])
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 4), [3])

    @patch('pypi_resource.pipio.get_versions_from_pip')
    def test_newest_version(self, mock_info):
        mock_info.return_value = canned_versions
        version = {'version': '0.9.2'}
        instream = make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(result, [version])

    @patch('pypi_resource.pipio.get_versions_from_pip')
    def test_has_newer_version(self, mock_info):
        mock_info.return_value = canned_versions
        version = {'version': '0.9.1'}
        instream = make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(result, [{'version': '0.9.1'}, {'version': '0.9.2'}])
        
    @patch('pypi_resource.pipio.get_versions_from_pip')
    def test_has_newer_prerelease(self, mock_info):
        mock_info.return_value = canned_versions
        version = {'version': '0.9.2'}
        instream = make_input_stream(version, pre_releases=True)
        result = check.check(instream)
        self.assertEqual(result, [{'version': '0.9.2'}, {'version': '0.9.3rc1'}])

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

if __name__ == '__main__':
	unittest.main()
