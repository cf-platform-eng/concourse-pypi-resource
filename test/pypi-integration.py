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
import glob
import unittest
import io
import json
import os
import subprocess
import tempfile

from pypi_resource import common, in_, out, pipio

THISDIR = os.path.dirname(os.path.realpath(__file__))
REPODIR = os.path.join(THISDIR, '..')

class TestGet(unittest.TestCase):

    def test_get_pypi(self):
        resconfig = io.StringIO(
            json.dumps({
                'source': {
                    'name': 'numpy',
                    'test': False,
                },
                'version': {
                    'version': '1.19.1',
                },
            })
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            in_.in_(tmpdir, resconfig)
            files = os.listdir(tmpdir)
            self.assertIn('version', files)
            self.assertIn('semver', files)
            self.assertEqual(len(glob.glob(os.path.join(tmpdir, '*.whl'))), 1)

    def test_get_pypi_source(self):
        resconfig = io.StringIO(
            json.dumps({
                'source': {
                    'name': 'cf_platform_eng',
                    'test': True,
                },
                'version': {
                    'version': '0.0.45',
                },
            })
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            in_.in_(tmpdir, resconfig)
            files = os.listdir(tmpdir)
            self.assertIn('version', files)
            self.assertIn('semver', files)
            self.assertIn('setup.py', files)


class TestPut(unittest.TestCase):

    def test_upload_pypi(self):
        rc = subprocess.run(['python', 'setup.py', 'sdist'], check=True, cwd=REPODIR)
        print("sdist returned", rc)
        out.out(
            os.path.join(REPODIR, 'dist'),
            {
                'source': {'test': True, 'name': 'concourse-pypi-resource'},
                'params': {'glob': '*.tar.gz'}
            }
        )

    def test_fail_to_upload_if_input_name_different_from_package_name(self):
        rc = subprocess.run(['python', 'setup.py', 'sdist'], check=True, cwd=REPODIR)
        print("sdist returned", rc)
        with self.assertRaises(out.NamesValidationError) as context:
            out.out(
                os.path.join(REPODIR, 'dist'),
                {
                    'source': {'test': True, 'name': 'mismatching-name'},
                    'params': {'glob': '*.tar.gz'}
                }
            )

    def test_upload_when_different_names_allowed(self):
        rc = subprocess.run(['python', 'setup.py', 'sdist'], check=True, cwd=REPODIR)
        print("sdist returned", rc)
        with self.assertRaises(out.NamesValidationError) as context:
            out.out(
                os.path.join(REPODIR, 'dist'),
                {
                    'source': {'test': True, 'name': 'mismatching-name', 'name_must_match': False},
                    'params': {'glob': '*.tar.gz'}
                }
            )

    def test_fail_to_upload_if_package_version_not_pep440_compliant(self):
        rc = subprocess.run(['python', 'setup.py', 'sdist'], check=True, cwd=os.path.join(THISDIR, 'test_package1_4'))
        print("sdist returned", rc)
        with self.assertRaises(out.VersionValidationError):
            out.out(
                os.path.join(THISDIR, 'test_package1_4'),
                {
                    'source': {'test': True, 'name': 'test_package1'},
                    'params': {'glob': 'dist/*.tar.gz'}
                }
            )


class TestPip(unittest.TestCase):

    def test_search_public(self):
        resconfig = {
            'source': {
                'name': 'numpy',
                'test': False,
            },
            'version': None,
        }
        resconfig = common.merge_defaults(resconfig)
        versions = pipio.pip_get_versions(resconfig)
        self.assertGreater(len(versions), 5)


if __name__ == '__main__':
    unittest.main()
