import os
from setuptools import setup

setup(
    name = os.environ.get('TEST_PACKAGE_NAME', 'test_package1'),
    version = os.environ.get('TEST_PACKAGE_VERSION', '0.0.1'),
    description = 'Repository IO Test-Package.',
    platforms = ['linux'],
    license = 'Apache 2.0',
    packages = ['test_package1',],
    install_requires = [],
    include_package_data = True,
)
