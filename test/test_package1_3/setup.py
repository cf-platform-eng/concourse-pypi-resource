from setuptools import setup


setup(
    name = "test_package1",
    version = '1.0.1',
    description = 'Repository IO Test-Package.',
    platforms = ['linux'],
    license = 'Apache 2.0',
    packages = ['test_package1',],
    install_requires = [
    ],
    include_package_data = True,
)