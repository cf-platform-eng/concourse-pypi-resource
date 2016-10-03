#!/usr/bin/env python

import sys

def main():
    print('in', file=sys.stderr)
    sys.exit(0)

if __name__ == '__main__':
    main()
