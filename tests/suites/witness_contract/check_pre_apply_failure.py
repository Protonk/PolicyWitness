"""Observe a pre-apply reporting gap and a populated real-worker positive control.

Every assertion group runs, including the positive control after a failed
attribution assertion. Signal-shape failures cannot hide the baseline regression.
The final case still fails normally if any group fails; there is no xfail mode.
"""
import errno
import json
from pathlib import Path
import re
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from blackbox import validate_step
from run_capture import RunCapture
from consumer import recover_evidence, validate_evidence_shape

OVERRIDES = {'worker_pre_ready_hang_ms': 10000, 'worker_timeout_ms': 200}
FORBIDDEN_OUTCOMES = {'ok', 'sandbox_apply_failed', 'bad_policy', 'runner_sandbox_denied'}


def library_claims(value, path='runner'):
    """Reject reported compile/apply results, including future structured records.

    Operation-tagged records and explicit apply/compile return fields are checked
    separately from prose. Ordinary step rc values are not library-failure claims.
    Extend these checks if the step-1 record contract uses different field names.
    """
    claims = []
    if isinstance(value, dict):
        operation = value.get('operation')
        library_operation = operation in (
            'sandbox_apply', 'sandbox_compile_string', 'apply', 'compile',
            'application', 'compilation', 5, 8)
        for key, item in value.items():
            if item is not None and (
                key in ('apply_rc', 'apply_errno', 'compile_rc', 'compile_errno')
                or (library_operation and key in (
                    'rc', 'errno', 'return_value', 'return_code', 'native_result'))
            ):
                claims.append(f'{path}.{key}={item!r}')
            claims.extend(library_claims(item, f'{path}.{key}'))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            claims.extend(library_claims(item, f'{path}[{i}]'))
    elif isinstance(value, str) and re.search(
        r'\b(?:sandbox_apply|sandbox_compile_string|compilation|application|compile|apply)'
        r'\b\s*(?:\([^)]*\))?\s*(?:returned\b|failed\b|(?:rc|errno|return[_ ](?:code|value))\s*[:=])',
        value, re.IGNORECASE,
    ):
        claims.append(f'{path}={value!r}')
    return claims


def no_cause_claim(envelope):
    data = envelope['data']
    runner = data['runner_result']
    assert runner['normalized_outcome'] != 'runner_sandbox_denied', runner
    assert data['sandbox_log_capture'] is None, 'log capture must be disabled'
    diagnostics = data.get('runner_sandbox_diagnostics')
    if diagnostics is not None:
        assert isinstance(diagnostics, dict), diagnostics
        assert diagnostics.get('first_deny') is None, diagnostics
        for key in ('cause', 'termination_cause'):
            assert diagnostics.get(key) in (None, 'unknown', 'undetermined'), diagnostics
        for key in ('sandbox_caused_termination', 'policy_caused_termination'):
            assert diagnostics.get(key) is not True, diagnostics
        prose = json.dumps(diagnostics).lower()
        assert not any(claim in prose for claim in (
            'sandbox killed', 'killed by sandbox', 'sandbox caused', 'kernel sandbox terminated'
        )), diagnostics


def common_evidence(envelope, rc, specimen, failure):
    assert not validate_evidence_shape(envelope), validate_evidence_shape(envelope)
    answers = recover_evidence(envelope)
    ids = [s['step_id'] for s in specimen['probe_plan']]
    assert answers['failure_groups']['missing_result'] == (ids if failure else [])
    assert answers['failure_groups']['unattributed_failure'] == ([] if failure else ids[1:])
    assert answers['comparison_groups']['unavailable'] == (ids if failure else [])
    assert answers['comparison_groups']['agreement'] == ([] if failure else ids[:1])
    assert answers['comparison_groups']['directional_consistency'] == ([] if failure else ids[1:])
    if failure:
        for answer in answers['steps']:
            assert answer['prediction_missing_reason'] == 'validator_not_invoked', answer
            assert answer['attempt_missing_reason'] == 'slot_incomplete', answer
            assert {'prediction:validator_not_invoked', 'attempt:slot_incomplete'} <= set(answer['comparison']['limitations'])
            assert answer['attempt']['native_rc'] is None and answer['attempt']['errno'] is None
            assert answer['query']['native_rc'] is None and answer['query']['errno'] is None
    assert rc == (1 if failure else 0), f'CLI exit: {rc}'
    assert envelope['kind'] == 'run', envelope
    assert envelope['result']['ok'] is (not failure), envelope['result']
    runner = envelope['data']['runner_result']
    assert envelope['result']['normalized_outcome'] == runner['normalized_outcome'], envelope['result']
    assert type(runner['rc']) is int and runner['rc'] == (1 if failure else 0), runner
    assert runner['specimen_id'] == specimen['specimen_id'], runner
    assert runner.get('test_overrides') == specimen.get('_test_overrides'), runner
    worker = runner['runner_subprocess']
    assert type(worker['pid']) is int and worker['pid'] > 0, worker
    assert runner['pid'] == worker['pid'], runner
    assert runner['schema_version'] == 7, runner
    steps = runner['steps']
    assert [s['step_id'] for s in steps] == [s['step_id'] for s in specimen['probe_plan']], steps
    if failure:
        assert runner.get('sandboxed_after_apply') is not True, runner
        assert runner.get('validator_subprocess') is None, runner
        assert worker['partial_steps'] is True, worker
        assert worker.get('term_signal') == 9 and worker.get('exit_code') is None, worker
        assert 'pw-probe-runner' in runner['error'], runner['error']
        for step, submitted in zip(steps, specimen['probe_plan']):
            prediction, attempt = step['sandbox_check'], step['attempt']
            assert isinstance(prediction['outcome'], str) and prediction['outcome'], prediction
            assert prediction['outcome'] not in ('allow', 'deny'), prediction
            # This compatibility spelling means no completed result. It does
            # not prove the worker never started the operation (step 1A).
            assert attempt['outcome'] == 'not_run_worker_died', attempt
            assert attempt['errno'] is None and attempt['syscall_errno'] is None, attempt
            assert step['drift'] is None, step
            assert attempt['requested_path'] == submitted['attempt']['target'], attempt
    else:
        assert runner['normalized_outcome'] == 'ok', runner
        assert runner['sandboxed_after_apply'] is True, runner
        assert worker['exit_code'] == 0 and worker.get('term_signal') is None, worker
        assert worker['partial_steps'] is False, worker
        validator = runner['validator_subprocess']
        assert type(validator['pid']) is int and validator['pid'] > 0, validator
        assert validator['pid'] != worker['pid'], validator
        assert validator['exit_code'] == 0 and validator.get('term_signal') is None, validator
        failures = []
        for i, (step, submitted) in enumerate(zip(steps, specimen['probe_plan'])):
            expectation = {'step_id': submitted['step_id'],
                           'sandbox_outcome': 'allow' if i == 0 else 'deny',
                           'attempt_ok': i == 0, 'drift': False if i == 0 else None}
            failures.extend(validate_step(step, expectation))
            prediction, attempt = step['sandbox_check'], step['attempt']
            target = submitted['attempt']['target']
            assert prediction['pid'] == worker['pid'], prediction
            assert prediction['operation'] == 'file-write-data', prediction
            assert prediction['filter_value'] == target, prediction
            assert type(prediction['rc']) is int and prediction['rc'] == i, prediction
            assert step['drift'] is (False if i == 0 else None), step
            assert attempt['requested_path'] == target, attempt
            if i == 0:
                assert attempt['outcome'] == 'ok' and attempt['observed_path'] == target, attempt
                assert attempt['errno'] is None, attempt
            else:
                assert attempt['outcome'] == 'open_failed' and attempt['rc'] == 1, attempt
                assert type(attempt['errno']) is int and attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
                assert 'open(' in attempt['error'], attempt
        assert not failures, '\n'.join(failures)


def lifecycle_observations(envelope, failure):
    worker = envelope['data']['runner_result']['runner_subprocess']
    assert worker['ready_byte_received'] is (not failure), worker
    assert worker['done_observed'] is (not failure), worker
    assert worker['poll_stop_reason'] == ('sentinel_deadline' if failure else 'done'), worker
    assert worker['exit_requested'] is True, worker
    assert worker['reaped'] is True, worker
    assert worker['wait_errors'] == [], worker
    request = worker.get('termination_request')
    if failure:
        assert request['signal'] == 9 and request['rc'] == 0, request
        assert request.get('errno') is None, request
    else:
        assert request is None, worker


def signal_contract(envelope):
    steps = envelope['data']['runner_result']['steps']
    assert len(steps) == 2, steps
    failures = [f"{s.get('step_id')}: {s.get('deny_signal', '<absent>')!r}"
                for s in steps if 'deny_signal' not in s or s['deny_signal'] is not None]
    assert not failures, 'every step must contain deny_signal:null: ' + '; '.join(failures)


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    results, observations = [], {}

    def check(name, fn):
        try:
            fn()
        except (AssertionError, KeyError, TypeError, ValueError) as exc:
            result = {'group': name, 'passed': False, 'error': f'{type(exc).__name__}: {exc}'}
        else:
            result = {'group': name, 'passed': True}
        results.append(result)
        print(f"{'PASS' if result['passed'] else 'FAIL'} {name}: {result.get('error', 'verified')}", flush=True)
        (out / 'assertions.json').write_text(json.dumps(results, indent=2) + '\n')

    with tempfile.TemporaryDirectory(prefix='pw-pre-apply-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(12) for _ in range(2)]
        seeds = [secrets.token_bytes(64) for _ in paths]
        specimen = {
            'schema_version': 1, 'specimen_id': secrets.token_hex(12),
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'
                       '(deny file-write-data (literal (param "BLOCKED")))',
                       'params': {'BLOCKED': str(paths[1])}},
            'probe_plan': [{
                'step_id': secrets.token_hex(12),
                'sandbox_check': {'operation': 'file-write-data',
                                  'filter': {'kind': 'path', 'value': str(path)}},
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(path)},
            } for path in paths],
        }
        for failure, name in ((True, 'pre_apply'), (False, 'positive_control')):
            request = dict(specimen)
            if failure:
                # 10s exceeds readiness (1s), sentinel (200ms) and exit grace
                # (1s) by a wide margin. The seam is after compilation, before
                # readiness/application; it is not a compiler-failure seam.
                request['_test_overrides'] = OVERRIDES
            capture = RunCapture(pw, out / name, request,
                                 cli_args=['--no-log-capture', '--timeout-ms', '20000'])
            # Both runs use the same files, seeds, policy and plan. Seed them
            # before entering RunCapture (which starts the CLI on entry).
            for i, (path, seed) in enumerate(zip(paths, seeds)):
                path.write_bytes(seed)
                path.chmod(0o600)
                before = path.read_bytes()
                (capture.out / f'file{i}.before').write_bytes(before)
                assert before == seed, f'could not seed file {i}'
            with capture as run:
                rc = run.wait(timeout=25)
                after = [path.read_bytes() for path in paths]
                for i, contents in enumerate(after):
                    (run.out / f'file{i}.after').write_bytes(contents)
                envelope = run.load_json()

            def effects():
                if failure:
                    assert after == seeds, 'pre-apply run changed file bytes'
                else:
                    assert after[0] and after[0] != seeds[0], 'allowed control write must change nonempty bytes'
                    assert after[1] == seeds[1], 'denied control write changed seed bytes'

            check(f'{name}.file_effects', effects)
            check(f'{name}.evidence', lambda: common_evidence(envelope, rc, request, failure))
            check(f'{name}.lifecycle_observations', lambda: lifecycle_observations(envelope, failure))
            check(f'{name}.no_policy_cause', lambda: no_cause_claim(envelope))
            if failure:
                def outcome():
                    for location, summary in (('runner', envelope['data']['runner_result']),
                                              ('controller', envelope['result'])):
                        actual = summary['normalized_outcome']
                        assert actual not in FORBIDDEN_OUTCOMES, f'unsupported {location} pre-apply outcome: {actual}'

                def no_library_result():
                    claims = library_claims(envelope['data']['runner_result'])
                    claims.extend(library_claims(envelope['result'], 'controller_summary'))
                    assert not claims, 'unobserved library result: ' + '; '.join(claims)

                check('pre_apply.outcome_attribution', outcome)
                check('pre_apply.library_result_attribution', no_library_result)
            check(f'{name}.signal_contract', lambda: signal_contract(envelope))
            runner = envelope['data']['runner_result']
            observations[name] = {'schema_version': runner.get('schema_version'),
                                  'validator_subprocess': runner.get('validator_subprocess'),
                                  'predictions': [s.get('sandbox_check') for s in runner.get('steps', [])]}
            (out / 'prediction_observations.json').write_text(json.dumps(observations, indent=2) + '\n')

    assert all(result['passed'] for result in results), 'contract failures retained in assertions.json'


if __name__ == '__main__':
    main()
