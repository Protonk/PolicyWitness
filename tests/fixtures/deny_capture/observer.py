"""Deterministic observer transport fixture, not a kernel/log-delivery oracle.

Events have fixed timestamps independent of the requested bounds. Python's
datetime parses the controller's actual argv, independently of its formatter.
The real tool's timestamp acceptance is covered by the live witness case.
"""
import argparse
import json
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--pid', type=int, required=True)
parser.add_argument('--process-name', required=True)
parser.add_argument('--start', required=True)
parser.add_argument('--end', required=True)
parser.add_argument('--format', choices=['json'], required=True)
args = parser.parse_args()


def milliseconds(value):
    return int(datetime.strptime(value, '%Y-%m-%d %H:%M:%S%z').timestamp()) * 1000


# Literal timestamps span both pads of 1999..22001ms, exact query bounds,
# and one millisecond outside each. Short/equal scans select a fixed subset.
events = [(-1001, '/before'), (-1000, '/lower-bound'), (0, '/start-pad'),
          (1500, '/start-slack'), (2100, '/early'), (2800, '/short-tail'),
          (4999, '/short-pad'), (5000, '/short-bound'), (21900, '/late'),
          (22800, '/end-slack'), (24000, '/end-pad'), (25000, '/upper-bound'),
          (25001, '/after')]
selected = [{'pid': args.pid, 'process': args.process_name,
             'operation': 'file-read-data', 'path': path,
             'raw_line': f'fixture event at {at} ms: {path}'}
            for at, path in events
            if milliseconds(args.start) <= at <= milliseconds(args.end)]
print(json.dumps({'data': {'start': args.start, 'end': args.end, 'last': None,
                          'observed_deny': bool(selected), 'deny_events': selected,
                          'log_rc': 0, 'log_error': None}}))
