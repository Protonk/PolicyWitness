"""Observe independent query/attempt routing through the real validator.

The crossed queries deliberately describe different targets from the attempts.
Their expected drift tests the harness; it is no claim about a compiler bug.

Keep this test as a contract guard even when the implementation prevents target
substitution by construction. A future refactor must still route queries and
attempts independently.
"""
import copy
import errno
import json
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from blackbox import validate_run_shape, validate_step
from run_capture import RunCapture


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    errors = []
    with tempfile.TemporaryDirectory(prefix='pw-query-targets-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(12) for _ in range(2)]
        seeds = [secrets.token_bytes(64) for _ in paths]
        step_ids = [secrets.token_hex(12) for _ in paths]
        base = {
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
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(path)},
            } for step_id, path in zip(step_ids, paths)],
        }

        # Literal expectations belong to this test, never to PW's response or
        # classifier. Only the query values change between these specimens.
        for name, query_indices, predictions, drifts in (
            ('matching', (0, 1), ('allow', 'deny'), (False, False)),
            ('swapped', (1, 0), ('deny', 'allow'), (True, None)),
        ):
            artifacts = out / name
            artifacts.mkdir()
            specimen = copy.deepcopy(base)
            for step, query_index in zip(specimen['probe_plan'], query_indices):
                step['sandbox_check']['filter']['value'] = str(paths[query_index])
            expected = [{'step_id': step_id, 'sandbox_outcome': prediction,
                         'attempt_ok': i == 0, 'drift': drift}
                        for i, (step_id, prediction, drift) in
                        enumerate(zip(step_ids, predictions, drifts))]
            expected[0]['errno'] = None
            (artifacts / 'expectations.json').write_text(json.dumps(expected, indent=2) + '\n')
            for i, (path, seed) in enumerate(zip(paths, seeds)):
                path.write_bytes(seed)
                path.chmod(0o600)
                before = path.read_bytes()
                (artifacts / f'file{i}.before').write_bytes(before)
                assert before == seed, f'{name}: could not restore file {i}'

            with RunCapture(pw, artifacts, specimen,
                            cli_args=['--no-log-capture', '--timeout-ms', '15000']) as run:
                rc = run.wait(timeout=20)
                # Establish actual effects before decoding any claimed effects.
                after = [path.read_bytes() for path in paths]
                for i, data in enumerate(after):
                    (artifacts / f'file{i}.after').write_bytes(data)
                assert after[0] and after[0] != seeds[0], \
                    f'{name}: allowed write did not leave changed, nonempty bytes'
                assert after[1] == seeds[1], f'{name}: denied write changed seed bytes'
                print(f'{name}: independent file effects passed', flush=True)
                assert rc == 0, f'{name}: PW exit {rc}; see {run.stdout_path} and {run.stderr_path}'
                envelope = run.load_json()

            failures, pairs = validate_run_shape(
                envelope, expected, policy_format='sbpl',
                require_sandboxed_after_apply=True, require_policy_sha256=True)
            runner = envelope['data']['runner_result']
            assert runner['rc'] == 0 and runner.get('test_overrides') is None, runner
            assert runner['specimen_id'] == specimen['specimen_id'], runner
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
                request = planned[step['step_id']]
                prediction, attempt = step['sandbox_check'], step['attempt']
                for key, value in (
                    ('pid', worker['pid']), ('scope', 'post_sandbox'),
                    ('operation', 'file-write-data'), ('filter_kind', 'path'),
                    ('rc', 0 if expectation['sandbox_outcome'] == 'allow' else 1),
                    ('errno', 0), ('filter_type_id', 1),
                    ('filter_value', request['sandbox_check']['filter']['value']),
                ):
                    if prediction.get(key) != value:
                        failures.append(f"{step['step_id']}: expected sandbox_check.{key}={value!r}, "
                                        f"got {prediction.get(key)!r}")
                target = request['attempt']['target']
                if attempt.get('requested_path') != target:
                    failures.append(f"{step['step_id']}: expected attempt.requested_path={target!r}")
                if expectation['attempt_ok']:
                    if attempt.get('outcome') != 'ok' or attempt.get('observed_path') != target:
                        failures.append(f"{step['step_id']}: expected successful write observed at {target!r}")
                elif (attempt.get('outcome') != 'open_failed'
                      or type(attempt.get('errno')) is not int
                      or attempt['errno'] not in (errno.EPERM, errno.EACCES)):
                    failures.append(f"{step['step_id']}: expected open_failed with permission errno")
            (artifacts / 'diagnostics.json').write_text(json.dumps(failures, indent=2) + '\n')
            errors.extend(f'{name}: {failure}' for failure in failures)
            if not failures:
                print(f'{name}: predictions, attempts, target attribution, and drift passed', flush=True)

    if errors:
        raise SystemExit('\n'.join(errors))
    print('real validator follows query targets; independently observed writes follow attempt targets')


if __name__ == '__main__':
    main()
