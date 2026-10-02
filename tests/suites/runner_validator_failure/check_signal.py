"""Real SIGKILL after one flushed verdict; attempts and partial evidence survive."""
import json
from pathlib import Path
import secrets
import sys

from check import install_fixture, assert_transcript
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'witness_contract'))
from check_ordering import RunCapture, envelope, ordering, specimen, step, save

pw, out_arg = sys.argv[1:]
out = Path(out_arg).resolve()
validator = install_fixture(out / 'validator', 'signal_after_one')
paths = [out / ('file-' + secrets.token_hex(8)) for _ in range(3)]
seeds = [secrets.token_bytes(64) for _ in paths]
for path, seed in zip(paths, seeds): path.write_bytes(seed)
spec = specimen([step(p, 'open_write', str(i)) for i, p in enumerate(paths)],
                overrides={'validator_executable_path': str(validator)})
with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture']) as run:
    rc = run.wait(timeout=20)
    after = [p.read_bytes() for p in paths]
    save(out / 'effects.json', [dict(before_hex=b.hex(), after_hex=a.hex()) for b, a in zip(seeds, after)])
    assert all(a and a != b for b, a in zip(seeds, after)), 'all writes must independently change bytes'
    runner = envelope(run, rc, spec, 'validator_unavailable')
ordering(runner)
status = runner['validator_subprocess']
assert status['term_signal'] == 9 and status.get('exit_code') is None and status['reaped'] is True, status
assert 'signal' in runner['error'] and '9' in runner['error'], runner['error']
received = json.loads(validator.with_suffix('.received.json').read_text())
assert received == dict(target_pid=runner['pid'], probes=[dict(
    step_id=str(i), operation='file-write-data', filter_type='PATH', filter_value=str(p))
    for i, p in enumerate(paths)]), received
assert_transcript(validator.with_suffix('.emitted.ndjson').read_text(), received['probes'], 'signal_after_one')
assert [s['comparison']['order'] for s in runner['steps']] == ['query_first', 'unestablished', 'unestablished']
for i, row in enumerate(runner['steps']):
    assert row['attempt']['outcome'] == 'ok', row
    assert row['comparison']['observation'] == 'succeeded', row
    if i == 0:
        assert row['sandbox_check']['outcome'] == 'allow' and row['sandbox_check']['native_rc'] == 0, row
    else:
        assert row['sandbox_check']['missing_reason'] == 'validator_no_verdict', row
print('one ordered record retained after SIGKILL; three independent writes complete after release')
