"""Corrupt fixture evidence after its suite has reported a completed case."""
import json
from pathlib import Path
import sys

mode, report_arg, events_arg = sys.argv[1:]
report_path, events_path = Path(report_arg), Path(events_arg)
if mode == 'malformed_report':
    report_path.write_text('{invalid')
elif mode == 'report_list':
    report_path.write_text('[]')
elif mode == 'missing_report':
    report_path.unlink()
elif mode in ('wrong_identity', 'invalid_status', 'status_mismatch'):
    report = json.loads(report_path.read_text())
    if mode == 'wrong_identity':
        report['suite'] = 'someone_else'
    else:
        report['status'] = 'unknown' if mode == 'invalid_status' else 'skip'
    report_path.write_text(json.dumps(report))
elif mode == 'malformed_event':
    with events_path.open('a') as stream:
        stream.write('invalid-event\n')
elif mode == 'no_events':
    events_path.write_text('')
elif mode == 'unreadable_events':
    events_path.unlink()
    events_path.mkdir()
elif mode == 'remove_prior':
    (report_path.parents[2] / 'pass/fixture_case/report.json').unlink()
elif mode in ('stale_events', 'no_end', 'end_before_start'):
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    if mode == 'stale_events':
        for event in events:
            event['run_id'] = 'a_different_run'
    elif mode == 'no_end':
        events = [event for event in events if event['step'] != 'test_end']
    else:
        events.reverse()
    events_path.write_text(''.join(json.dumps(event) + '\n' for event in events))
else:
    raise SystemExit(f'unknown fixture alteration: {mode}')
