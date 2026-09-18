"""CLI timeout contracts for empty, successful-write, and mixed-outcome plans.

A run deadline does not invalidate completed observations. File effects are
checked before decoding the envelope; its step evidence must survive separately
from the failed run status. The empty plan deliberately covers no validator.
"""
import errno
import json
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from blackbox import validate_step
from run_capture import RunCapture


def check_file_effects(before, after):
    assert len(after) == len(before), 'file observation count changed'
    if before:
        assert after[0] and after[0] != before[0], \
            'completed allowed write must leave changed, nonempty bytes'
        assert after[1:] == before[1:], 'denied write changed seed bytes'


def check_envelope(envelope, rc, specimen, expected):
    assert rc == 1, f'expected CLI failure exit 1, got {rc}'
    assert envelope['kind'] == 'run', envelope
    assert envelope['result']['ok'] is False, envelope['result']
    runner = envelope['data']['runner_result']
    assert runner['normalized_outcome'] == 'runner_timeout', runner
    assert type(runner['rc']) is int and runner['rc'] == 1, runner
    assert runner['specimen_id'] == specimen['specimen_id'], runner
    assert runner['sandboxed_after_apply'] is True, runner
    assert runner['test_overrides'] == specimen['_test_overrides'], runner
    error = runner['error']
    assert all(text in error for text in ('pw-probe-runner', 'sentinel deadline', 'host requested SIGKILL')), error

    worker = runner['runner_subprocess']
    assert type(worker['pid']) is int and worker['pid'] > 0, worker
    assert runner['pid'] == worker['pid'], runner
    assert worker['term_signal'] == 9 and worker.get('exit_code') is None, worker
    assert worker['partial_steps'] is False, worker

    steps = runner['steps']
    assert isinstance(steps, list), steps
    assert [step['step_id'] for step in steps] == [step['step_id'] for step in expected], steps
    validator = runner.get('validator_subprocess')
    if not expected:
        # Optional subprocess metadata is omitted or null when no child ran.
        assert validator is None, validator
        return
    assert type(validator['pid']) is int and validator['pid'] > 0, validator
    assert validator['pid'] != worker['pid'], validator
    assert validator['exit_code'] == 0 and validator.get('term_signal') is None, validator

    failures = []
    for step, expectation, request in zip(steps, expected, specimen['probe_plan']):
        failures.extend(validate_step(step, expectation))
        prediction, attempt = step['sandbox_check'], step['attempt']
        target = request['attempt']['target']
        assert prediction['pid'] == worker['pid'], prediction
        assert prediction['scope'] == 'post_sandbox', prediction
        assert prediction['operation'] == 'file-write-data', prediction
        assert prediction['filter_kind'] == 'path' and prediction['filter_type_id'] == 1, prediction
        assert prediction['filter_value'] == target, prediction
        assert prediction['effective_filter_value'] == target, prediction
        assert type(prediction['rc']) is int, prediction
        assert prediction['rc'] == (0 if expectation['attempt_ok'] else 1), prediction
        assert prediction['errno'] == 0 and prediction['error'] is None, prediction
        assert step['drift'] is False, step
        assert attempt['requested_path'] == target, attempt
        # Normalization is optional; the successful open's observed path is
        # independent worker evidence and must be present below.
        assert attempt['normalized_path'] in (None, target), attempt
        if expectation['attempt_ok']:
            assert attempt['outcome'] == 'ok' and attempt['observed_path'] == target, attempt
            assert attempt.get('error') is None, attempt
        else:
            assert attempt['outcome'] == 'open_failed' and attempt['rc'] == 1, attempt
            assert attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
            assert attempt['observed_path'] is None, attempt
            assert 'open(' in attempt['error'], attempt
    assert not failures, '\n'.join(failures)


def check_cli(variant, pw, out):
    count = {'empty': 0, 'write': 1, 'mixed': 2}[variant]
    with tempfile.TemporaryDirectory(prefix='pw-timeout-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(12) for _ in range(count)]
        seeds = [secrets.token_bytes(64) for _ in paths]
        plan, expected = [], []
        for i, (path, seed) in enumerate(zip(paths, seeds)):
            path.write_bytes(seed)
            path.chmod(0o600)
            before = path.read_bytes()
            (out / f'file{i}.before').write_bytes(before)
            assert before == seed, f'could not seed file {i}'
            step_id = secrets.token_hex(12)
            plan.append({
                'step_id': step_id,
                'sandbox_check': {'operation': 'file-write-data',
                                  'filter': {'kind': 'path', 'value': str(path)}},
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(path)},
            })
            expected.append({'step_id': step_id, 'sandbox_outcome': 'allow' if i == 0 else 'deny',
                             'attempt_ok': i == 0, 'drift': False})
        if expected:
            expected[0]['errno'] = None
        policy = {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'}
        if variant == 'mixed':
            policy['sbpl_source'] += '(deny file-write-data (literal (param "BLOCKED")))'
            policy['params'] = {'BLOCKED': str(paths[1])}
        specimen = {
            'schema_version': 1, 'specimen_id': secrets.token_hex(12),
            'policy': policy, 'probe_plan': plan,
            # The hang starts after every slot is durable, before done. Leave
            # ample room beyond the worker deadline and its 1-second reap grace
            # so this case selects the host-kill path, not clean exit in grace.
            '_test_overrides': {'worker_timeout_ms': 2000, 'worker_post_apply_hang_ms': 8000},
        }
        (out / 'expectations.json').write_text(json.dumps(expected, indent=2) + '\n')
        with RunCapture(pw, out, specimen,
                        cli_args=['--no-log-capture', '--timeout-ms', '20000']) as run:
            rc = run.wait(timeout=25)
            after = [path.read_bytes() for path in paths]
            for i, data in enumerate(after):
                (out / f'file{i}.after').write_bytes(data)
            check_file_effects(seeds, after)
            print(f'{variant}: independent file effects passed ({count} files)', flush=True)
            check_envelope(run.load_json(), rc, specimen, expected)
        print(f'{variant}: host timeout, honored overrides, and all {count} completed steps verified')


if __name__ == '__main__':
    variant, pw, out_arg = sys.argv[1:]
    check_cli(variant, pw, Path(out_arg).resolve())
