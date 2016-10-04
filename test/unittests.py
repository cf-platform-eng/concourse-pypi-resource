import unittest
from unittest.mock import patch
from pypi_resource import check
import io
import json
import os

def read_file(file):
    with open(file) as f:
        return f.read()

here = os.path.dirname(os.path.realpath(__file__))
canned_pypi_info = json.loads(read_file(os.path.join(here, 'pypi-package-info.json')))

class TestCheck(unittest.TestCase):
    def make_stream(self, json_obj):
        stream = io.StringIO()
        json.dump(json_obj, stream)
        stream.seek(0)
        return stream

    def make_input(self, version):
        return {
            'source': {
                'name': 'tile-generator',
                'username': 'username',
                'password': 'password',
                'test': False,
            },
            'version': {
                'version': version,
            }
        }

    def make_input_stream(self, version):
        return self.make_stream(self.make_input(version))

    def test_pypi_url(self):
        input = {'source': { 'test': True } }
        self.assertEqual(check.get_pypi_url(input), 'https://testpypi.python.org/pypi')
        input = {'source': { 'test': False } }
        self.assertEqual(check.get_pypi_url(input), 'https://pypi.python.org/pypi')

    @patch('pypi_resource.check.get_pypi_package_info')
    def test_get_versions_from_pypi(self, mock_info):
        mock_info.return_value = canned_pypi_info
        input = self.make_input('0.9.2')
        result = check.get_versions_from_pypi(input)
        self.assertEqual(list(result), ['0.9.1', '0.9.2'])

    def test_truncate_before(self):
        self.assertEqual(check.truncate_before([1, 2, 3], 1), [1, 2, 3])
        self.assertEqual(check.truncate_before([1, 2, 3], 2), [2, 3])
        self.assertEqual(check.truncate_before([1, 2, 3], 3), [3])
        self.assertEqual(check.truncate_before([1, 2, 3], 4), [])

    @patch('pypi_resource.check.get_pypi_package_info')
    def test_newest_version(self, mock_info):
        mock_info.return_value = canned_pypi_info
        version = '0.9.2'
        instream = self.make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(json.loads(result), [version])

    @patch('pypi_resource.check.get_pypi_package_info')
    def test_has_newer_version(self, mock_info):
        mock_info.return_value = canned_pypi_info
        version = '0.9.1'
        instream = self.make_input_stream(version)
        result = check.check(instream)
        self.assertEqual(json.loads(result), ['0.9.1', '0.9.2'])

if __name__ == '__main__':
	unittest.main()
