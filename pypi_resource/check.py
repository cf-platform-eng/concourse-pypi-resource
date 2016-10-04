#!/usr/bin/env python

from distutils.version import LooseVersion
import json
import sys

import requests

def get_pypi_url(input):
    if input['source']['test']:
        return 'https://testpypi.python.org/pypi'
    return 'https://pypi.python.org/pypi'

def get_pypi_package_info(input):
    package_name = input['source']['name']
    url = get_pypi_url(input) + '/' + package_name + '/json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_versions_from_pypi(input):
    pypi_info = get_pypi_package_info(input)
    versions = pypi_info['releases'].keys()
    versions = sorted(versions, key=LooseVersion)
    return versions

def truncate_before(lst, value):
    for index, val in enumerate(lst):
        if val == value:
            return lst[index:]
    return []

def check(instream):
    input = {
        'source': {
            'test': False
        }
    }
    input.update(json.load(instream))
    version = input['version']['version']
    print('Starting version: {}'.format(version), file=sys.stderr)
    versions = get_versions_from_pypi(input)
    return json.dumps(truncate_before(versions, version))

def main():
    print('check', file=sys.stderr)
    print(check(sys.stdin))

if __name__ == '__main__':
    main()
