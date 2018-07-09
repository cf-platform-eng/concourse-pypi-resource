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

from pypi_resource import check, common, pipio


here = os.path.dirname(os.path.realpath(__file__))
canned_versions = list(map(pipio.Version, ["0.9.3rc1", "0.9.1", "0.9.2"]))


def make_stream(json_obj):
    stream = io.StringIO()
    json.dump(json_obj, stream)
    stream.seek(0)
    return stream


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


class TestConfiguration(unittest.TestCase):
    def test_repository_name_deprecated(self):
        resconfig = {'source': {'repository': 'foo'}}
        with self.assertRaises(ValueError):
            common.merge_defaults(resconfig)

    def test_repository_props_migrated(self):
        expected = {'source': {'repository': {'authenticate': 'out', 'username': 'u', 'password': 'p', 'repository_url': 'url'}}}
        resconfig = {'source': {'username': 'u', 'password': 'p', 'repository_url': 'url'}}
        result = common.merge_defaults(resconfig)

        self.assertDictEqual(expected['source']['repository'], result['source']['repository'])


class TestPypi(unittest.TestCase):
    def setUp(self):
        newout = io.StringIO()
        sys.stdout = newout

    def tearDown(self):
        self.assertEqual(sys.stdout.getvalue(), '',
                         '%s sent text to stdout and this is not allowed' % self._testMethodName)

    def test_pypi_url(self):
        input = {'source': {'repository_url': 'http://example.org/pypi'}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input), ('http://example.org/pypi', 'example.org'))

        input = {'source': {'repository': {'repository_url': 'http://example.org/pypi'}}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input), ('http://example.org/pypi', 'example.org'))

        input = {'source': {'repository': {'authenticate': 'always', 'username': 'u', 'password': 'p'}}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input, 'in'), ('https://u:p@pypi.python.org/pypi', 'pypi.python.org'))

        input = {'source': {'repository': {'username': 'u', 'password': 'p'}}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input, 'in'), ('https://pypi.python.org/pypi', 'pypi.python.org'))
        self.assertEqual(pipio.get_pypi_url(input, 'out'), ('https://u:p@pypi.python.org/pypi', 'pypi.python.org'))

        input = {'source': {'repository': {
                            'username': 'admin', 'password': 'admin123', 'authenticate': 'always', 
                            'repository_url': 'http://localhost:8081/repository/pypi-private/'
        }}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input, 'out'), ('http://admin:admin123@localhost:8081/repository/pypi-private/', 'localhost'))

    def test_pypi_test_url(self):
        input = {'source': {'test': True}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input), ('https://testpypi.python.org/pypi', 'testpypi.python.org'))

        input = {'source': {'test': False}}
        input = common.merge_defaults(input)
        self.assertEqual(pipio.get_pypi_url(input), ('https://pypi.python.org/pypi', 'pypi.python.org'))


class TestCheck(unittest.TestCase):
    def test_truncate_before(self):
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 1), [1, 2, 3])
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 2), [2, 3])
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 3), [3])
        self.assertEqual(check.truncate_smaller_versions([1, 2, 3], 4), [3])

    @patch('pypi_resource.pipio.pip_get_versions')
    def test_newest_version(self, mock_info):
        mock_info.return_value = canned_versions
        version = {'version': '0.9.2'}
        instream = make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(result, [version])

    @patch('pypi_resource.pipio.pip_get_versions')
    def test_has_newer_version(self, mock_info):
        mock_info.return_value = canned_versions
        version = {'version': '0.9.1'}
        instream = make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(result, [{'version': '0.9.1'}, {'version': '0.9.2'}])

    @patch('pypi_resource.pipio.pip_get_versions')
    def test_has_newer_prerelease(self, mock_info):
        mock_info.return_value = canned_versions
        version = {'version': '0.9.2'}
        instream = make_input_stream(version, pre_release=True)
        result = check.check(instream)
        self.assertEqual(result, [{'version': '0.9.2'}, {'version': '0.9.3rc1'}])


class TestOther(unittest.TestCase):
    def test_py_version_to_semver(self):
        tests = [
            ('1.2.3rc7dev11', '1.2.3-rc.7+dev000011'),
            ('1.2.3rc7', '1.2.3-rc.7'),
            ('1.2.3alpha', '1.2.3-alpha.0'),
            ('1.2.3beta', '1.2.3-beta.0'),
            ('1.2.3', '1.2.3'),
            ('1.2.3-1', '1.2.3'),
            ('1.2', '1.2.0'),
            ('1', '1.0.0'),
        ]
        for pyver, expected in tests:
            result = common.py_version_to_semver(pyver)
            self.assertEqual(result, expected, "%s did not convert to %s" % (pyver, expected))


if __name__ == '__main__':
    unittest.main()
