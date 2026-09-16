"""Independent execution receipts and evidence: imports no test library."""
import json
import os
from pathlib import Path
import subprocess
import sys

suite = sys.argv[1]
out = Path(os.environ['PW_TEST_OUT_DIR'])
modes = json.loads(os.environ.get('CONTROL_SELECTION_MODES', '{}'))
result = 0
for leaf in os.environ['PW_TEST_CASES'].splitlines():
    key = f'{suite}/{leaf}'
    mode = modes.get(key, 'pass')
    if mode.startswith('mutate_'):
        app = Path(os.environ['PW_APP_DIR'])
        (app / 'Contents/MacOS/pw-runner-client').write_bytes(b'changed during case execution\n')
        (app / 'Contents/added-resource').write_text('new resource')
        (app / 'Contents/Resources/Evidence/symbols.json').unlink()
        (app / 'Contents').chmod(0o700)
        (app / 'Contents/new-link').symlink_to('added-resource')
        mode = mode.removeprefix('mutate_')
    with Path(os.environ['CONTROL_SELECTION_RECEIPTS']).open('a') as stream:
        stream.write(json.dumps({'id': key, 'argv': sys.argv[2:], 'cwd': os.getcwd(),
                                 'app': os.environ['PW_APP_DIR'], 'bin': os.environ['PW_BIN'],
                                 'rust_bin': os.environ['PW_BIN_PATH'],
                                 'quiet': os.environ.get('PW_TEST_QUIET')}) + '\n')
    if mode == 'silent':
        continue
    if mode == 'crash':
        raise SystemExit(19)
    if mode == 'run_controller':
        subprocess.run([os.environ['PW_BIN'], 'fixture-probe', *sys.argv[2:]], check=True)
    if mode == 'wrong':
        leaf = 'not_selected'
    path = out / 'suites' / suite / leaf
    path.mkdir(parents=True, exist_ok=True)
    status = 'skip' if mode.startswith('skip') else 'fail' if mode == 'fail' else 'pass'
    report = {'suite': suite, 'test_id': leaf, 'status': status, 'message': mode,
              'skip_reason': 'fixture_unavailable' if mode == 'skip_declared' else 'undeclared'}
    (path / 'report.json').write_text(json.dumps(report))
    events = [dict(kind='test_event', run_id=os.environ['PW_TEST_RUN_ID'], suite=suite,
                   test_id=leaf, step=step, status=value)
              for step, value in [('test_start', 'start'), ('test_end', status)]]
    if mode == 'duplicate':
        events.extend(events[:])
    with (out / 'events.jsonl').open('a') as stream:
        for event in events:
            stream.write(json.dumps(event) + '\n')
    if status == 'fail':
        result = 1
raise SystemExit(result)
