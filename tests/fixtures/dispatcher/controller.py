#!/usr/bin/python3
"""Runnable stub controller: records its own identity, independent of PW config."""
import json
import os
from pathlib import Path
import sys

binary = Path(__file__).resolve()
with Path(os.environ['CONTROL_CONTROLLER_RECEIPTS']).open('a') as stream:
    stream.write(json.dumps({'binary': str(binary), 'argv': sys.argv[1:],
                             'marker': binary.with_name('controller-marker.txt').read_text()}) + '\n')
