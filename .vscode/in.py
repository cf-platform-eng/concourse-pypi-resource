import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pypi_resource.check import main

with open(sys.argv[2], 'r') as f:
    sys.stdin = f
    main()
