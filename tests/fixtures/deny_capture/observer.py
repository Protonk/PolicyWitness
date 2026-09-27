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


# Include events in the widened portions, and on either side of the bounds.
events = [(999, '/before'), (1500, '/start-slack'), (2100, '/early'),
          (2800, '/short-tail'), (21900, '/late'), (22800, '/end-slack'),
          (23001, '/after')]
selected = [{'pid': args.pid, 'process': args.process_name,
             'operation': 'file-read-data', 'path': path,
             'raw_line': f'fixture event at {at} ms: {path}'}
            for at, path in events
            if milliseconds(args.start) <= at < milliseconds(args.end)]
print(json.dumps({'data': {'start': args.start, 'end': args.end, 'last': None,
                          'observed_deny': bool(selected), 'deny_events': selected,
                          'log_rc': 0, 'log_error': None}}))
