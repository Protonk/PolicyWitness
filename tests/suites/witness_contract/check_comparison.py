"""Controlled input verdicts, real worker observations and independent OS witnesses.

The transcript is not a native sandbox_check result. Expected distinctions below
come from the submitted scopes and independent file/permission controls.
"""
import errno
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
from blackbox import validate_run_shape, validate_step


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    with tempfile.TemporaryDirectory(prefix='pw-comparison-', dir='/private/tmp') as work:
        root = Path(work)
        a, b, locked, absent = (root / name for name in ('A', 'B', 'locked', 'absent'))
        for p in (a, b, locked):
            p.write_bytes(b'independent witness\n')
        locked.chmod(0)
        try:
            with locked.open('rb'):
                raise AssertionError('permission control unexpectedly opened locked file')
        except OSError as exc:
            assert exc.errno == errno.EACCES
            (out / 'direct-permission.json').write_text(json.dumps({'errno': exc.errno}) + '\n')
        expected = []
        steps = []
        predictions = {}

        def add(name, prediction='allow', query=a, target=a, operation='file-read-data',
                action='open_read', kind='file', observation='succeeded', conclusion='agreement',
                drift=False, operation_relation='matched', target_relation='same_submitted', attempt_ok=True):
            predictions[name] = prediction
            steps.append({'step_id': name, 'sandbox_check': {'operation': operation,
                'filter': {'kind': 'path', 'value': str(query)}},
                'attempt': {'kind': kind, 'action': action, 'target': str(target)}})
            expected.append({'step_id': name, 'attempt_ok': attempt_ok, 'drift': drift,
                'comparison': {'observation': observation, 'conclusion': conclusion,
                    'operation_relation': operation_relation, 'target_relation': target_relation}})

        add('agreement')
        add('disagreement', prediction='deny', conclusion='disagreement', drift=True)
        add('allow_permission', query=locked, target=locked, observation='permission_failure',
            conclusion='unavailable', drift=None, attempt_ok=False)
        add('deny_permission', prediction='deny', query=locked, target=locked, observation='permission_failure',
            conclusion='directional_consistency', drift=None, attempt_ok=False)
        add('different_target', prediction='deny', target=b, conclusion='unavailable', drift=None,
            target_relation='different_submitted')
        add('different_operation', prediction='deny', operation='file-write-data', conclusion='unavailable',
            drift=None, operation_relation='different')
        add('absent', query=absent, target=absent, observation='other_failure', conclusion='unavailable',
            drift=None, attempt_ok=False)
        add('missing_query_success', query=absent, target=b, conclusion='unavailable', drift=None,
            target_relation='different_submitted')
        add('compound_create', operation='file-write-data', action='create', conclusion='unavailable',
            drift=None, operation_relation='unresolved')
        add('unsupported', kind='future', action='future', observation='unavailable', conclusion='unavailable',
            drift=None, operation_relation='unresolved', target_relation='unresolved', attempt_ok=False)
        validator = out / 'comparison-validator.py'
        validator.write_text('#!/usr/bin/python3\nimport json, sys\npredictions = ' + repr(predictions) + '''
for line in sys.stdin:
    p = json.loads(line)
    outcome = predictions[p['step_id']]
    print(json.dumps(dict(kind='sb_api_validator_verdict', schema_version=1,
        step_id=p['step_id'], operation=p['operation'], filter_type=p['filter_type'],
        filter_type_id=1, filter_value=p.get('filter_value'), outcome=outcome,
        rc=0 if outcome == 'allow' else 1, errno=0)), flush=True)
''')
        validator.chmod(0o755)
        spec = {'schema_version': 1, 'specimen_id': 'comparison-evidence',
                'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
                'probe_plan': steps, '_test_overrides': {'validator_executable_path': str(validator)}}
        (out / 'comparison-expectations.json').write_text(json.dumps(expected, indent=2) + '\n')
        before = {str(p): p.read_bytes() for p in (a, b)}
        try:
            with RunCapture(pw, out / 'comparison', spec, cli_args=['--no-log-capture']) as run:
                assert run.wait(timeout=30) == 0
                envelope = run.load_json()
            runner = envelope['data']['runner_result']
            assert runner['schema_version'] == 7
            assert runner['test_overrides']['validator_executable_path'] == str(validator)
            assert runner['runner_subprocess']['exit_code'] == 0
            assert runner['validator_subprocess']['exit_code'] == 0
            errors, matched = validate_run_shape(envelope, expected, require_sandboxed_after_apply=True)
            for step, exp in matched:
                errors.extend(validate_step(step, exp))
                comparison = step['comparison']
                assert comparison['scope'] == 'submitted_operation_and_target'
                for limit in ('query_attempt_order_unestablished', 'state_stability_unestablished',
                              'runtime_target_identity_unestablished'):
                    assert limit in comparison['limitations'], step
                assert step['attempt']['requested_kind'] == next(s for s in steps if s['step_id'] == step['step_id'])['attempt']['kind']
                if exp['comparison']['observation'] in ('permission_failure', 'other_failure'):
                    assert 'sandbox_attribution_unestablished' in comparison['limitations'], step
                if step['step_id'] in ('absent', 'missing_query_success'):
                    assert 'prediction:query_not_requested' in comparison['limitations'], step
                    assert 'query_plan:path_unresolved_at_planning' in comparison['limitations'], step
                    assert comparison['prediction'] == 'unavailable'
                if comparison['observation'] == 'succeeded':
                    assert step['attempt']['observed_path'] == step['attempt']['requested_path'], step
                if step['step_id'] == 'unsupported':
                    assert 'attempt:attempt_not_supported' in comparison['limitations'], step
            assert not errors, errors
            for path, content in before.items():
                assert Path(path).read_bytes() == content
            (out / 'file-witness.json').write_text(json.dumps({'unchanged': list(before), 'absent_exists': absent.exists()}, indent=2) + '\n')
            assert not absent.exists()
            (out / 'comparison-checks.json').write_text(json.dumps({'checks': len(expected), 'failures': []}) + '\n')
        finally:
            locked.chmod(0o600)
    print('ten controlled comparisons preserve real observations, submitted scope and independent limits')


if __name__ == '__main__':
    main()
