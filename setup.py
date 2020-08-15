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

from setuptools import setup
from distutils.version import LooseVersion
import os

here = os.path.abspath(os.path.dirname(__file__))


def read_readme():
    with open(os.path.join(here, 'README.md')) as f:
        return f.read()


def read_version():
    with open(os.path.join(here, '.version')) as f:
        version = f.read()
    return str(LooseVersion(version))


setup(
    name = "concourse-pypi-resource",
    version = read_version(),
    description = 'Concourse CI resource for PyPI packages.',
    long_description = read_readme(),
    long_description_content_type = 'text/markdown',
    platforms = ['linux'],
    url = 'https://github.com/cf-platform-eng/pypi-resource',
    author = 'Pivotal Cloud Foundry Platform Engineering',
    license = 'Apache 2.0',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Build Tools',
    ],
    keywords = [
        'concourse',
    ],
    packages = ['pypi_resource', 'test'],
    install_requires = [
        'pkginfo',
        'twine',
        'pip',
    ],
    setup_requires = [],
    tests_require = ['pytest'],
    test_suite = 'test',
    include_package_data = True,
    entry_points = {
        'console_scripts': [
            'check = pypi_resource.check:main',
            'in = pypi_resource.in_:main',
            'out = pypi_resource.out:main',
        ]
    }
)
