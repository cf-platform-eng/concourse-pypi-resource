#!/usr/bin/env python

# Copyright (c) 2015-Present Pivotal Software, Inc. All Rights Reserved.
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
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

def read_readme():
    with open(os.path.join(here, 'README.md')) as f:
        return f.read()

setup(
    name = "pypi-resource",
    version = '0.1.0',
    description = 'Concourse CI resource for PyPI packages.',
    long_description = read_readme(),
    url = 'https://github.com/cf-platform-eng/pypi-resource',
    author = 'Pivotal Cloud Foundry Platform Engineering',
    license = 'Apache 2.0',
    classifiers = [
    ],
    keywords = [
    ],
    packages = [ 'pypi_resource' ],
    install_requires = [
        'requests',
        'twine',
    ],
    include_package_data = True,
)
