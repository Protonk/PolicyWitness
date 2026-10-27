#!/opt/homebrew/opt/python@3.14/bin/python3.14
"""A controller stand-in for harness deadlines, never runtime evidence."""
import json
import signal
import sys
import time

if sys.argv[1:] == ['--version']:
    print(json.dumps({'kind': 'version', 'build': {'number': '841', 'commit': 'stand-in'}}))
else:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print('stand-in ready; SIGTERM ignored for the two-signal control', flush=True)
    time.sleep(3600)
