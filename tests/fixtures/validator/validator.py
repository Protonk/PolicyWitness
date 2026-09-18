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
        verdict.update(response.get('fields', {}))
        for key in response.get('omit', []): verdict.pop(key, None)
        lines.append(json.dumps(verdict, sort_keys=True))
    tail = case['tail']
    if tail == 'malformed':
        lines.append('invalid-verdict:' + probes[-1]['step_id'])
    elif tail in ('incomplete_allow', 'incomplete_deny', 'diagnostic', 'duplicate', 'unexpected'):
        index = 0 if tail == 'duplicate' else -1
        verdict = dict(probes[index], kind='sb_api_validator_verdict', schema_version=1,
                       outcome='allow', rc=0, errno=0)
        if tail == 'incomplete_allow': verdict.pop('rc')
        if tail == 'incomplete_deny': verdict.update(outcome='deny', rc=None)
        if tail == 'diagnostic':
            verdict.pop('rc'); verdict.pop('errno')
            for key in ('operation', 'filter_type', 'filter_value'): verdict.pop(key, None)
            verdict.update(outcome='future_937', error='unfamiliar diagnostic', future_code=97319)
        if tail == 'unexpected': verdict['step_id'] = 'never-requested'
        lines.append(json.dumps(verdict, sort_keys=True))
    else:
        assert tail in ('eof', 'invalid_utf8'), 'unknown transcript tail'
    output = ('\n'.join(lines) + '\n').encode()
    if tail == 'invalid_utf8': output += b'\xff\n'
    here.with_suffix('.emitted.ndjson').write_bytes(output)
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()



if __name__ == '__main__':
    main()
