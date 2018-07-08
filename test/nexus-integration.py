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

import os
import shutil
import tempfile
import unittest

from pypi_resource import common, pipio

THISDIR = os.path.dirname(os.path.realpath(__file__))
REPODIR = os.path.join(THISDIR, '..')


def make_input(version, **kwargs):
    """
    Provide a valid configuration template to connect to a local integration-test repository.

    .. note::

        Setting a local Nexus3:
        - docker run -d -p 8081:8081 --name nexus sonatype/nexus3
        - create pypi hosted repo pypi-private
        - disable anonymous access

    :see https://help.sonatype.com/repomanager3/pypi-repositories#PyPIRepositories-HostingPyPIRepositories
    """
    resconfig = {
        'source': {
            'name': 'somedemo',
            'username': 'admin',
            'password': 'admin123',
            'repository': {
                'authenticate': 'always',
                'index_url': 'http://localhost:8081/repository/pypi-private/simple',
                'repository_url': 'http://localhost:8081/repository/pypi-private/',
            },
            'pre_release': True,
        },
        'version': version,
    }
    resconfig['source'].update(kwargs)
    return resconfig


# class TestPut(unittest.TestCase):
# 
#     def test_nexus3(self):
#         rc = subprocess.run(['pipenv', 'run', 'python', 'setup.py', 'sdist'], check=True, cwd=REPODIR)
#         print("sdist returned", rc)
#         out.out(
#             os.path.join(REPODIR, 'dist'),
#             {
#                 'source': make_input(None)['source'],
#                 'params': {'glob': '*.tar.gz'}
#             }
#         )


class TestCheck(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCheck, cls).setUpClass()
        # upload the test-set
#         src = os.path.join(THISDIR, 'test_dist')
#         for fn in os.listdir(src):
#             out.out(src,
#                     {
#                         'source': make_input(None)['source'],
#                         'params': {'glob': fn}
#                     }
#             )         

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def get_versions(self, **kwargs):
        resconfig = make_input(None, **kwargs)
        resconfig = common.merge_defaults(resconfig)
        versions = pipio.pip_get_versions(resconfig)
        return versions
    
    def get_download(self, **kwargs):
        resconfig = make_input(None, **kwargs)
        resconfig = common.merge_defaults(resconfig)
        return pipio.pip_download(resconfig, self.temp_dir)

    def test_search_nexus3_filename_filter(self):
        versions = self.get_versions(
            name='test_package1',
            python_version='py2.py3',
            packaging='any',
        )
        self.assertListEqual(versions, [pipio.Version('1.0.1')])

    def test_search_prerelease(self):
        versions = self.get_versions(
            name='test_package1',
            pre_release=True,
        )
        self.assertListEqual(versions, [pipio.Version('1.0.0'), pipio.Version('1.0.1rc1'), pipio.Version('1.0.1')])

        versions = self.get_versions(
            name='test_package1',
            pre_release=False,
        )
        self.assertListEqual(versions, [pipio.Version('1.0.0'), pipio.Version('1.0.1')])                

    def test_download_latest(self):
        result = self.get_download(
            name='test_package1',
            packaging='source',
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'test_package1-1.0.1.tar.gz')))

    def test_search_nexus3_pyversion(self):
        versions = self.get_versions(
            name='test_package1',
            python_version='2',
            packaging='any',
        )
        self.assertListEqual(versions, [pipio.Version('1.0.0'), pipio.Version('1.0.1rc1'), pipio.Version('1.0.1')])

        versions = self.get_versions(
            name='test_package1',
            python_version='2',
            packaging='binary',
        )
        self.assertListEqual(versions, [pipio.Version('1.0.0'), pipio.Version('1.0.1')])

        versions = self.get_versions(
            name='test_package1',
            python_version='3',
            packaging='any',
        )
        self.assertListEqual(versions, [pipio.Version('1.0.0'), pipio.Version('1.0.1rc1'), pipio.Version('1.0.1')])

        versions = self.get_versions(
            name='test_package1',
            packaging='source',
        )
        self.assertListEqual(versions, [pipio.Version('1.0.0'), pipio.Version('1.0.1rc1'), pipio.Version('1.0.1')])        


if __name__ == '__main__':
    unittest.main()
