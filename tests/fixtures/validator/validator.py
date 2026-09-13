#!/usr/bin/python3
"""Test validator: replay a checked-in transcript against actual incoming probes."""
import json
from pathlib import Path
import signal
import sys


def main():
    signal.alarm(10)
    here = Path(__file__).resolve()
    assert len(sys.argv) == 3 and sys.argv[1] == '--batch', 'expected --batch <worker PID>'
    target_pid = int(sys.argv[2])
    assert target_pid > 0, 'expected a live target PID'
    case = json.loads(here.with_suffix('.case.json').read_text())
    # Drain all input before emitting anything, so clean shortfall and decode
    # failure cannot accidentally become a probe-write/EPIPE failure.
    probes = [json.loads(line) for line in sys.stdin if line.strip()]
    here.with_suffix('.received.json').write_text(json.dumps({
        'target_pid': target_pid, 'probes': probes,
    }, indent=2) + '\n')
    assert len(probes) == case['probe_count'], 'unexpected probe count'
    assert len({p['step_id'] for p in probes}) == len(probes), 'duplicate step IDs'
    lines = []
    for response in case['responses']:
        probe = probes[response['probe_index']]
        verdict = dict(probe, kind='sb_api_validator_verdict', schema_version=1,
                       filter_type_id=1, outcome=response['outcome'], rc=response['rc'],
                       errno=response['errno'])
        lines.append(json.dumps(verdict, sort_keys=True))
    if case['tail'] == 'malformed':
        lines.append('invalid-verdict:' + probes[-1]['step_id'])
    else:
        assert case['tail'] == 'eof', 'unknown transcript tail'
    output = '\n'.join(lines) + '\n'
    here.with_suffix('.emitted.ndjson').write_text(output)
    sys.stdout.write(output)
    sys.stdout.flush()


if __name__ == '__main__':
    main()
