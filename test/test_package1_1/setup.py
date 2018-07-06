from setuptools import setup


setup(
    name = "test_package1",
    version = '1.0.0',
    description = 'Repository IO Test-Package.',
    platforms = ['linux'],
    license = 'Apache 2.0',
    include_package_data = True,
    packages = ['test_package1',]
)