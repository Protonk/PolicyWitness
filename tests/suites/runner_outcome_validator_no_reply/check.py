"""Deadline through the public CLI; independent file effects precede JSON assertions."""
import json
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer
import contract
from run_capture import RunCapture


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    validator = out / 'validator.py'
    shutil.copyfile(ROOT / 'tests/fixtures/validator/validator.py', validator)
    validator.chmod(0o755)
    shutil.copyfile(ROOT / 'tests/fixtures/validator/deadline.json', validator.with_suffix('.case.json'))
    with tempfile.TemporaryDirectory(prefix='pw-vdeadline-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(8) for _ in range(2)]
        seeds = [secrets.token_bytes(64) for _ in paths]
        for i, (path, seed) in enumerate(zip(paths, seeds)):
            path.write_bytes(seed)
            (out / f'before-{i}.bin').write_bytes(seed)
        plan = [dict(step_id=f'write-{i}', sandbox_check=dict(operation='file-write-data',
                    filter=dict(kind='path', value=str(path))),
                    attempt=dict(kind='file', action='open_write', target=str(path)))
                for i, path in enumerate(paths)]
        spec = dict(schema_version=1, specimen_id='validator-io-deadline',
                    policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'), probe_plan=plan,
                    _test_overrides=dict(validator_executable_path=str(validator), validator_io_timeout_ms=500))
        started = time.monotonic()
        with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture', '--timeout-ms', '15000']) as run:
            rc = run.wait(timeout=20)
            after = [p.read_bytes() for p in paths]
            for i, data in enumerate(after):
                (out / f'after-{i}.bin').write_bytes(data)
                assert len(data) == 1 and data != seeds[i], 'released write did not produce its independent effect'
            envelope = run.load_json()
        elapsed_ms = round((time.monotonic() - started) * 1000)
    runner = envelope['data']['runner_result']
    assert rc == 1 and envelope['result']['ok'] is False, envelope['result']
    assert runner['schema_version'] == contract.RESPONSE_SCHEMA and runner['normalized_outcome'] == 'validator_no_reply', runner
    assert '500 ms I/O deadline' in runner['error'], runner['error']
    assert runner['test_overrides'] == spec['_test_overrides'], runner
    worker, v = runner['runner_subprocess'], runner['validator_subprocess']
    assert worker['exit_code'] == 0 and worker['done_observed'] and not worker['partial_steps'], worker
    assert worker['worker_evidence']['failure_state'] == 'absent', worker
    assert v['stdout_collection_stop'] == 'deadline' and v['reaped'] is True, v
    assert v['termination_request']['signal'] == 9 and v['termination_request']['rc'] == 0, v
    assert len(v['records']) == 1 and v['records'][0]['step_id'] == 'write-0', v
    ordering = worker['ordering']
    assert all(ordering[k] is True for k in ('collection_closed_before_proceed', 'proceed_set',
                                           'proceed_observed', 'worker_lifetime_established')), ordering
    assert ordering['validator_disposition'] == 'reaped' and not ordering['protocol_violations'], ordering
    first, second = runner['steps']
    assert first['comparison']['order'] == 'query_first' and first['comparison']['observation'] == 'succeeded', first
    assert second['comparison']['order'] == 'unestablished' and second['comparison']['observation'] == 'succeeded', second
    assert second['sandbox_check']['missing_reason'] == 'validator_no_verdict', second
    assert all(s['attempt']['outcome'] == 'ok' for s in runner['steps']), runner['steps']
    errors = consumer.validate(envelope)
    assert not errors, errors
    (out / 'timing.json').write_text(json.dumps(dict(cli_elapsed_ms=elapsed_ms, validator_io_timeout_ms=500,
        worker_proceed_observed=True, worker_proceed_failure=False), indent=2) + '\n')
    print(f'validator deadline released both writes; one query_first record retained; CLI elapsed {elapsed_ms} ms')


if __name__ == '__main__':
    main()
