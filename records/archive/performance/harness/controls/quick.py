#!/opt/homebrew/opt/python@3.14/bin/python3.14
"""Immediate stand-in exit for cleanup controls; never runtime evidence."""
import json
import sys

if sys.argv[1:] == ['--version']:
    print(json.dumps({'kind': 'version', 'build': {'number': '841', 'commit': 'stand-in'}}))
else:
    print(json.dumps({'kind': 'control', 'result': {'ok': True}, 'data': {}}))
