"""Native exec admission controls: policies and helper effects supply the oracle.

There is no validator override. Query acceptance is tested separately from
operation correspondence; interpreter and fork queries are negative controls.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
from consumer import recover_evidence, validate_evidence_shape


def main():
    pw, out_arg, helper_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    evidence = {}
    consumer_evidence = {}
    with tempfile.TemporaryDirectory(prefix='pw-exec-scope-', dir='/private/tmp') as work:
        helper = Path(work) / 'helper'
        other = Path(work) / 'other'
        script = Path(work) / 'script'
        for target in (helper, other):
            shutil.copyfile(helper_arg, target)
            target.chmod(0o755)
        script.write_text('#!/bin/sh\nprintf "native_exec_script\\n"\n')
        script.chmod(0o755)
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (helper, other, script)}
        for code in (0, 37):
            result = subprocess.run([str(helper), '--exit', str(code)], capture_output=True, timeout=5)
            assert result.returncode == code
            assert result.stdout == b'exec_fixture: hello from helper\n'
            (out / f'direct-{code}.json').write_text(json.dumps({
                'returncode': result.returncode, 'stdout': result.stdout.decode(),
                'stderr': result.stderr.decode()}, indent=2) + '\n')
        literal = json.dumps(str(helper))
        policies = {
            'allow': '(allow default)',
            'deny_exec': f'(allow default)(deny process-exec* (literal {literal}))',
            'deny_fork': '(allow default)(deny process-fork)',
            'deny_read': f'(allow default)(deny file-read-data (literal {literal}))',
            'minimum': '(deny default)(allow process-exec*)(allow process-fork)(allow file-read*)',
            'without_fork': '(deny default)(allow process-exec*)(allow file-read*)',
            'without_read': '(deny default)(allow process-exec*)(allow process-fork)',
            'bare_policy': f'(allow default)(deny process-exec (literal {literal}))',
            'interpreter_policy': f'(allow default)(deny process-exec-interpreter (literal {literal}))',
            'interpreter_all': '(allow default)(deny process-exec-interpreter)',
            'deny_metadata': f'(allow default)(deny file-read-metadata (literal {literal}))',
            'deny_script_exec': f'(allow default)(deny process-exec* (literal {json.dumps(str(script))}))',
        }
        for name, policy in policies.items():
            queries = [('exec', 'process-exec*', 'path', str(helper)),
                       ('bare', 'process-exec', 'path', str(helper)),
                       ('interpreter', 'process-exec-interpreter', 'path', str(helper)),
                       ('fork', 'process-fork', 'none', None),
                       ('read', 'file-read-data', 'path', str(helper)),
                       ('different_target', 'process-exec*', 'path', str(other))]
            steps = []
            for step_id, operation, kind, value in queries:
                query_filter = {'kind': kind}
                if value is not None:
                    query_filter['value'] = value
                steps.append({'step_id': step_id,
                              'sandbox_check': {'operation': operation, 'filter': query_filter},
                              'attempt': {'kind': 'exec', 'action': 'spawn', 'target': str(helper)}})
            if name == 'allow':
                steps.append({'step_id': 'child_37',
                              'sandbox_check': {'operation': 'process-exec*',
                                                'filter': {'kind': 'path', 'value': str(helper)}},
                              'attempt': {'kind': 'exec', 'action': 'spawn', 'target': str(helper),
                                          'args': ['--exit', '37']}})
            if name in ('allow', 'interpreter_all', 'deny_script_exec'):
                for label, query_operation in [('script', 'process-exec*'),
                                                ('script_interpreter', 'process-exec-interpreter')]:
                    steps.append({'step_id': label,
                                  'sandbox_check': {'operation': query_operation,
                                                    'filter': {'kind': 'path', 'value': str(script)}},
                                  'attempt': {'kind': 'exec', 'action': 'spawn', 'target': str(script)}})
            if name == 'deny_exec':
                steps.append({'step_id': 'denied_query_allowed_attempt',
                              'sandbox_check': {'operation': 'process-exec*',
                                                'filter': {'kind': 'path', 'value': str(helper)}},
                              'attempt': {'kind': 'exec', 'action': 'spawn', 'target': str(other)}})
            spec = {'schema_version': 1, 'specimen_id': 'native-exec-' + name,
                    'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)' + policy},
                    'probe_plan': steps}
            with RunCapture(pw, out / name, spec, cli_args=['--no-log-capture']) as run:
                rc = run.wait(timeout=30)
                envelope = run.load_json()
            runner = envelope['data']['runner_result']
            assert type(runner.get('schema_version')) is int and runner['schema_version'] == 7, runner
            assert not validate_evidence_shape(envelope), validate_evidence_shape(envelope)
            answers = recover_evidence(envelope)
            consumer_evidence[name] = answers
            (out / name / 'consumer-answers.json').write_text(json.dumps(answers, indent=2) + '\n')
            assert rc == 0 and envelope['result']['ok'] is True, (name, envelope)
            assert runner['normalized_outcome'] == 'ok'
            assert runner.get('test_overrides') is None
            assert runner['runner_subprocess']['exit_code'] == 0
            assert runner['validator_subprocess']['exit_code'] == 0
            assert [s['step_id'] for s in runner['steps']] == [s['step_id'] for s in steps]
            evidence[name] = {s['step_id']: s for s in runner['steps']}
            for step in runner['steps']:
                query, attempt = step['sandbox_check'], step['attempt']
                rows.append({'policy': name, 'step': step['step_id'], 'cli_rc': rc,
                             'query': query['outcome'], 'query_errno': query['errno'],
                             'attempt': attempt['outcome'], 'errno': attempt['errno'],
                             'child_pid': attempt.get('child_pid'), 'exit': attempt.get('child_exit_code'),
                             'stdout': attempt.get('stdout'), 'comparison': step['comparison']})
        (out / 'observations.json').write_text(json.dumps(rows, indent=2) + '\n')
        after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (helper, other, script)}
        (out / 'target-hashes.json').write_text(json.dumps({'before': before, 'after': after}, indent=2) + '\n')
        assert after == before

        # Columns are target exec, interpreter, fork and read predictions, then
        # whether this binary can spawn. Each policy changes a separate gate.
        # In particular a successful binary does not need interpreter admission.
        expected_native = {
            'allow': ('allow', 'allow', 'allow', 'allow', True),
            'deny_exec': ('deny', 'deny', 'allow', 'allow', False),
            'deny_fork': ('allow', 'allow', 'deny', 'allow', False),
            'deny_read': ('allow', 'allow', 'allow', 'deny', True),
            'minimum': ('allow', 'allow', 'allow', 'allow', True),
            'without_fork': ('allow', 'allow', 'deny', 'allow', False),
            'without_read': ('allow', 'allow', 'allow', 'deny', False),
            'bare_policy': ('deny', 'deny', 'allow', 'allow', False),
            'interpreter_policy': ('allow', 'deny', 'allow', 'allow', True),
            'interpreter_all': ('allow', 'deny', 'allow', 'allow', True),
            'deny_metadata': ('allow', 'allow', 'allow', 'allow', True),
            'deny_script_exec': ('allow', 'allow', 'allow', 'allow', True),
        }
        for name, (execute, interpreter, fork, read, spawned) in expected_native.items():
            records = evidence[name]
            for step_id, expected_prediction in [('exec', execute), ('interpreter', interpreter),
                                                  ('fork', fork), ('read', read),
                                                  ('bare', 'unsupported_operation'),
                                                  ('different_target', 'allow')]:
                step = records[step_id]
                query, attempt = step['sandbox_check'], step['attempt']
                assert query['result_source'] == 'validator'
                assert query['pid'] == runner_pid(out / name)
                assert query['outcome'] == expected_prediction, (name, step_id, query)
                assert query['rc'] == {'allow': 0, 'deny': 1, 'unsupported_operation': -1}[expected_prediction]
                assert query['errno'] == (22 if step_id == 'bare' else 0)
                assert attempt['result_source'] == 'worker'
                assert attempt['requested_kind'] == 'exec' and attempt['requested_action'] == 'spawn'
                assert attempt['requested_path'] == str(helper)
                if spawned:
                    assert attempt['child_pid'] > 0 and attempt['child_exit_code'] == 0, (name, attempt)
                    assert attempt['outcome'] == 'ok' and attempt['rc'] == 0
                    assert attempt['stdout'] == 'exec_fixture: hello from helper\n'
                else:
                    assert attempt['child_pid'] == 0 and attempt['child_exit_code'] == -1, (name, attempt)
                    assert attempt['outcome'] == 'exec_failed' and attempt['rc'] == -1
                    assert attempt['errno'] in (1, 13)
                    assert attempt['syscall_errno'] == attempt['errno']
                    assert 'posix_spawn:' in attempt['error']
            assert records['bare']['comparison']['prediction'] == 'unavailable'
            assert records['bare']['drift'] is None
            for key in ('interpreter', 'fork', 'read'):
                assert records[key]['comparison']['operation_relation'] == 'different'
                assert records[key]['comparison']['conclusion'] == 'unavailable'
                assert records[key]['drift'] is None
            assert records['different_target']['comparison']['target_relation'] == 'different_submitted'
            assert records['different_target']['drift'] is None

        # Scenario-authored expectations protect useful agreement, limited
        # consistency and unavailable comparisons independently of errno rules.
        comparisons = [
            ('allow', 'exec', 'allow', 'succeeded', 'agreement', False),
            ('minimum', 'exec', 'allow', 'succeeded', 'agreement', False),
            ('interpreter_all', 'exec', 'allow', 'succeeded', 'agreement', False),
            ('allow', 'child_37', 'allow', 'succeeded', 'agreement', False),
            ('allow', 'script', 'allow', 'succeeded', 'agreement', False),
            ('deny_exec', 'exec', 'deny', 'permission_failure', 'directional_consistency', None),
            ('bare_policy', 'exec', 'deny', 'permission_failure', 'directional_consistency', None),
            ('deny_fork', 'exec', 'allow', 'permission_failure', 'unavailable', None),
            ('without_read', 'exec', 'allow', 'permission_failure', 'unavailable', None),
            ('interpreter_all', 'script', 'allow', 'permission_failure', 'unavailable', None),
            ('deny_script_exec', 'script', 'deny', 'permission_failure', 'directional_consistency', None),
        ]
        for name, step_id, prediction, observation, conclusion, drift in comparisons:
            answers = consumer_evidence[name]
            step = next(s for s in answers['steps'] if s['step_id'] == step_id)
            assert step_id in answers['comparison_groups'][conclusion]
            assert (step_id in answers['failure_groups']['unattributed_failure']) == (observation == 'permission_failure' or step_id == 'child_37')
            comparison = step['comparison']
            assert comparison['prediction'] == prediction
            assert comparison['observation'] == observation
            assert comparison['conclusion'] == conclusion, (name, step_id, comparison)
            assert comparison['operation_relation'] == 'matched'
            assert comparison['target_relation'] == 'same_submitted'
            assert step['drift'] is drift
            for limit in ('query_attempt_order_unestablished', 'state_stability_unestablished',
                          'runtime_target_identity_unestablished', 'exec_query_not_full_spawn_prediction'):
                assert limit in comparison['limitations'], (name, step_id, comparison)
            assert 'broad_query_operation' not in comparison['limitations']
            if observation == 'permission_failure':
                assert 'sandbox_attribution_unestablished' in comparison['limitations']

        child = evidence['allow']['child_37']
        recovered_child = next(s for s in consumer_evidence['allow']['steps'] if s['step_id'] == 'child_37')
        assert recovered_child['failed_after_spawn'] is True
        assert recovered_child['attempt'] == child['attempt']
        assert recovered_child['comparison']['observation_basis'] == 'spawned_child'
        assert {'exec_result_failed_after_spawn', 'sandbox_attribution_unestablished'} <= set(recovered_child['comparison']['limitations'])
        assert child['attempt']['child_exit_code'] == 37 and child['attempt']['child_pid'] > 0
        assert child['attempt']['outcome'] == 'exec_failed' and child['attempt']['rc'] == 37
        assert child['attempt']['stdout'] == 'exec_fixture: hello from helper\n'
        assert child['comparison']['observation_basis'] == 'spawned_child'
        assert 'exec_result_failed_after_spawn' in child['comparison']['limitations']
        assert 'sandbox_attribution_unestablished' in child['comparison']['limitations']
        assert evidence['allow']['script']['attempt']['stdout'] == 'native_exec_script\n'
        denied_script = evidence['interpreter_all']['script']
        assert denied_script['attempt']['child_pid'] == 0
        assert denied_script['attempt']['errno'] in (1, 13)
        assert evidence['interpreter_all']['script_interpreter']['sandbox_check']['outcome'] == 'deny'
        blocked_script = evidence['deny_script_exec']['script']
        assert blocked_script['attempt']['child_pid'] == 0
        assert blocked_script['attempt']['errno'] in (1, 13)
        swapped = evidence['deny_exec']['denied_query_allowed_attempt']
        recovered_swap = next(s for s in consumer_evidence['deny_exec']['steps'] if s['step_id'] == 'denied_query_allowed_attempt')
        assert recovered_swap['comparison']['target_relation'] == 'different_submitted'
        assert recovered_swap['comparison']['conclusion'] == 'unavailable'
        assert swapped['sandbox_check']['outcome'] == 'deny'
        assert swapped['attempt']['child_pid'] > 0 and swapped['attempt']['child_exit_code'] == 0
        assert swapped['attempt']['stdout'] == 'exec_fixture: hello from helper\n'
        assert swapped['comparison']['operation_relation'] == 'matched'
        assert swapped['comparison']['target_relation'] == 'different_submitted'
        assert swapped['comparison']['conclusion'] == 'unavailable' and swapped['drift'] is None
        (out / 'checks.json').write_text(json.dumps({'policies': len(policies), 'native_steps': len(rows),
            'comparison_scenarios': len(comparisons), 'failures': []}, indent=2) + '\n')
    print('native exec admission, independent spawn prerequisites and child outcomes verified')


def runner_pid(out):
    envelope = json.loads((out / 'run.json').read_text())
    return envelope['data']['runner_result']['runner_subprocess']['pid']


if __name__ == '__main__':
    main()
