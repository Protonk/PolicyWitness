"""Each file attempt action has one exact effect, observed outside PolicyWitness.

Every row runs one single-step specimen through the public CLI. The target is
snapshotted before the run and again after, and the effect expectation is
applied to those snapshots before the envelope is decoded. Denied twins of the
mutating actions must leave the target identical.
"""
import errno
import json
import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_capture import RunCapture  # noqa: E402
import effects  # noqa: E402

OPERATION = {
    'open_read': 'file-read-data',
    'access': 'file-read-data',
    'open_write': 'file-write-data',
    'create': 'file-write-create',
    'unlink': 'file-write-unlink',
}

# name, action, seeded target, denied operation (None = allow default),
# effect expectation, expected attempt outcome
ROWS = [
    ('open_write_allowed', 'open_write', True, None, 'truncated', 'ok'),
    ('open_write_denied', 'open_write', True, 'file-write-data', 'unchanged', 'open_failed'),
    ('create_absent_allowed', 'create', False, None, 'created', 'ok'),
    ('create_absent_denied', 'create', False, 'file-write-create', 'absent', 'open_failed'),
    ('create_existing_allowed', 'create', True, None, 'unchanged', 'ok'),
    ('unlink_allowed', 'unlink', True, None, 'absent', 'ok'),
    ('unlink_denied', 'unlink', True, 'file-write-unlink', 'unchanged', 'unlink_failed'),
    ('open_read_allowed', 'open_read', True, None, 'unchanged', 'ok'),
    ('access_allowed', 'access', True, None, 'unchanged', 'ok'),
]

EXPECTATIONS = {
    'truncated': lambda before, after: effects.expect_truncated_to_one_byte(before, after),
    'created': lambda before, after: effects.expect_created_empty(before, after),
    'absent': lambda before, after: effects.expect_absent(after),
    'unchanged': lambda before, after: effects.expect_unchanged(before, after),
}


def policy_for(denied_operation, target):
    if denied_operation is None:
        return '(version 1) (allow default)'
    return f'(version 1) (allow default) (deny {denied_operation} (literal "{target}"))'


def specimen_for(name, action, target, denied_operation):
    return {
        'schema_version': 1,
        'specimen_id': f'run_effects_{name}',
        'policy': {'format': 'sbpl', 'sbpl_source': policy_for(denied_operation, target)},
        'probe_plan': [{
            'step_id': secrets.token_hex(8),
            'sandbox_check': {'operation': OPERATION[action],
                              'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': action, 'target': str(target)},
        }],
    }


def expected_prediction(before, denied_operation, expectation):
    if not before['exists']:
        # PW does not query sandbox_check for a path that does not resolve
        # when the query is planned; the attempt still runs.
        return 'unavailable'
    if expectation == 'absent' and denied_operation is None:
        # The worker starts its attempts as soon as it publishes `applied`, and
        # the host spawns the validator only after observing that, so an
        # allowed unlink usually removes the target before the query runs.
        # PW then reports deny with order/state limitations. This suite pins
        # the effect and records the prediction rather than asserting it.
        return 'raced'
    return 'allow' if denied_operation is None else 'deny'


def check_step(step, target, prediction_expectation, expected_outcome):
    prediction, attempt = step['sandbox_check'], step['attempt']
    if prediction_expectation == 'unavailable':
        assert prediction['outcome'] == 'prediction_unavailable', prediction
        assert prediction['missing_reason'] == 'query_not_requested', prediction
    elif prediction_expectation == 'raced':
        assert prediction['result_source'] == 'validator', prediction
        assert prediction['outcome'] in ('allow', 'deny'), prediction
    else:
        assert prediction['result_source'] == 'validator', prediction
        assert prediction['outcome'] == prediction_expectation, prediction
    assert attempt['requested_path'] == str(target), attempt
    assert attempt['outcome'] == expected_outcome, attempt
    if expected_outcome == 'ok':
        assert attempt['rc'] == 0 and attempt.get('error') is None, attempt
    else:
        assert attempt['rc'] != 0, attempt
        assert attempt['errno'] in (errno.EPERM, errno.EACCES), attempt


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    results = []
    for name, action, seeded, denied_operation, expectation, expected_outcome in ROWS:
        work = out / name
        work.mkdir()
        target = work / secrets.token_hex(8)
        if seeded:
            target.write_bytes(secrets.token_bytes(64))
            os.chmod(target, 0o640)
        before = effects.snapshot(target)
        effects.record(before, work, 'before')
        spec = specimen_for(name, action, target, denied_operation)
        with RunCapture(pw, work / 'run', spec, cli_args=['--no-log-capture']) as run:
            rc = run.wait(timeout=30)
        # Observe the filesystem before consulting PW's report.
        after = effects.snapshot(target)
        effects.record(after, work, 'after')
        EXPECTATIONS[expectation](before, after)

        assert rc == 0, f'{name}: PW exit={rc}; see {run.stdout_path}'
        envelope = run.load_json()
        assert envelope['kind'] == 'run' and envelope['result']['ok'] is True, name
        runner = envelope['data']['runner_result']
        assert runner['normalized_outcome'] == 'ok', (name, runner['normalized_outcome'])
        assert runner.get('test_overrides') is None, name
        assert len(runner['steps']) == 1, name
        step = runner['steps'][0]
        assert step['step_id'] == spec['probe_plan'][0]['step_id'], name
        prediction_expectation = expected_prediction(before, denied_operation, expectation)
        check_step(step, target, prediction_expectation, expected_outcome)
        results.append({'row': name, 'action': action, 'seeded': seeded,
                        'denied_operation': denied_operation, 'effect': expectation,
                        'prediction_expectation': prediction_expectation,
                        'prediction': step['sandbox_check']['outcome'],
                        'drift': step.get('drift'),
                        'comparison_limitations': (step.get('comparison') or {}).get('limitations'),
                        'attempt_outcome': attempt_summary(step)})
        print(f'{name}: external effect "{expectation}" observed; attempt reported {expected_outcome}; '
              f'prediction {step["sandbox_check"]["outcome"]} ({prediction_expectation})', flush=True)
    (out / 'rows.json').write_text(json.dumps(results, indent=2) + '\n')


def attempt_summary(step):
    attempt = step['attempt']
    return {key: attempt.get(key) for key in ('outcome', 'rc', 'errno', 'observed_path')}


if __name__ == '__main__':
    main()
