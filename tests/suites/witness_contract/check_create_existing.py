"""Creating an existing file opens it for write without replacing its contents.

An allowed create must succeed without truncation or exclusive-create failure.
A denied write must fail even though a read-only open would preserve the bytes.
Filesystem observations are independent of the runner's reported outcomes.
"""
import errno
import json
from pathlib import Path
import secrets
import stat
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from blackbox import validate_run_shape, validate_step
from run_capture import RunCapture


def snapshot_files(paths, out, phase):
    contents, identities = [], []
    for i, path in enumerate(paths):
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode), f'{phase}: target is not a regular file: {path}'
        data = path.read_bytes()
        (out / f'file{i}.{phase}').write_bytes(data)
        contents.append(data)
        identities.append({'path': str(path), 'device': info.st_dev, 'inode': info.st_ino})
    (out / f'identities.{phase}.json').write_text(json.dumps(identities, indent=2) + '\n')
    return contents, identities


def check_files(before, after, identities_before, identities_after):
    assert after == before, 'create changed existing file contents'
    assert identities_after == identities_before, 'create replaced an existing file'


def check_envelope(envelope, rc, specimen, expected):
    assert rc == 0, f'expected successful CLI exit, got {rc}'
    failures, pairs = validate_run_shape(
        envelope, expected, policy_format='sbpl',
        require_sandboxed_after_apply=True, require_policy_sha256=True)
    runner = envelope['data']['runner_result']
    assert type(runner['rc']) is int and runner['rc'] == 0, runner
    assert runner['specimen_id'] == specimen['specimen_id'], runner
    assert runner.get('test_overrides') is None, runner
    worker = runner['runner_subprocess']
    validator = runner['validator_subprocess']
    assert type(worker['pid']) is int and worker['pid'] > 0, worker
    assert runner['pid'] == worker['pid'], runner
    assert worker['exit_code'] == 0 and worker.get('term_signal') is None, worker
    assert worker['partial_steps'] is False, worker
    assert type(validator['pid']) is int and validator['pid'] > 0, validator
    assert validator['pid'] != worker['pid'], validator
    assert validator['exit_code'] == 0 and validator.get('term_signal') is None, validator

    planned = {step['step_id']: step for step in specimen['probe_plan']}
    for step, expectation in pairs:
        failures.extend(validate_step(step, expectation))
        prediction, attempt = step['sandbox_check'], step['attempt']
        target = planned[step['step_id']]['attempt']['target']
        assert prediction['pid'] == worker['pid'], prediction
        assert prediction['scope'] == 'post_sandbox', prediction
        assert prediction['operation'] == 'file-write-data', prediction
        assert prediction['filter_kind'] == 'path' and prediction['filter_type_id'] == 1, prediction
        assert prediction['filter_value'] == target and prediction['effective_filter_value'] == target, prediction
        assert type(prediction['rc']) is int, prediction
        assert prediction['rc'] == (0 if expectation['attempt_ok'] else 1), prediction
        assert prediction['errno'] == 0 and prediction['error'] is None, prediction
        assert step['drift'] is False, step
        assert attempt['requested_path'] == target, attempt
        if expectation['attempt_ok']:
            assert attempt['outcome'] == 'ok' and attempt['observed_path'] == target, attempt
            assert attempt.get('error') is None, attempt
        else:
            assert attempt['outcome'] == 'open_failed' and attempt['rc'] == 1, attempt
            assert type(attempt['errno']) is int and attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
            assert attempt['observed_path'] is None, attempt
            assert 'open(' in attempt['error'], attempt
    assert not failures, '\n'.join(failures)


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    with tempfile.TemporaryDirectory(prefix='pw-create-existing-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(12) for _ in range(2)]
        seeds = [bytes([i]) + secrets.token_bytes(64) for i in range(2)]
        for path, seed in zip(paths, seeds):
            path.write_bytes(seed)
            path.chmod(0o600)
        before, identities_before = snapshot_files(paths, out, 'before')
        assert before == seeds, 'could not seed existing files'
        step_ids = [secrets.token_hex(12) for _ in paths]
        specimen = {
            'schema_version': 1, 'specimen_id': secrets.token_hex(12),
            'policy': {
                'format': 'sbpl',
                'sbpl_source': '(version 1)(allow default)'
                               '(deny file-write-data (literal (param "BLOCKED")))',
                'params': {'BLOCKED': str(paths[1])},
            },
            'probe_plan': [{
                'step_id': step_id,
                'sandbox_check': {'operation': 'file-write-data',
                                  'filter': {'kind': 'path', 'value': str(path)}},
                'attempt': {'kind': 'file', 'action': 'create', 'target': str(path)},
            } for step_id, path in zip(step_ids, paths)],
        }
        expected = [
            {'step_id': step_ids[0], 'sandbox_outcome': 'allow',
             'attempt_ok': True, 'errno': None, 'drift': False},
            {'step_id': step_ids[1], 'sandbox_outcome': 'deny',
             'attempt_ok': False, 'drift': False},
        ]
        (out / 'expectations.json').write_text(json.dumps(expected, indent=2) + '\n')
        with RunCapture(pw, out, specimen,
                        cli_args=['--no-log-capture', '--timeout-ms', '15000']) as run:
            rc = run.wait(timeout=20)
            # Read the files and their identities before decoding claimed effects.
            after, identities_after = snapshot_files(paths, out, 'after')
            check_files(before, after, identities_before, identities_after)
            print('both existing files retain every seed byte and their identities', flush=True)
            check_envelope(run.load_json(), rc, specimen, expected)
        print('existing-file create succeeds when allowed and fails when writes are denied; drift=false')


if __name__ == '__main__':
    main()
