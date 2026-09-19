"""Independent CLI assertions for admission, framing, structure and association."""
import base64
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture


def specimen():
    return {'schema_version': 1, 'specimen_id': 'failure-boundaries',
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
            'probe_plan': [{'step_id': 's', 'sandbox_check': {'operation': 'file-read-data',
                'filter': {'kind': 'path', 'value': '/etc/hosts'}},
                'attempt': {'kind': 'file', 'action': 'open_read', 'target': '/etc/hosts'}}]}


def run(pw, out, request):
    with RunCapture(pw, out, request, cli_args=['--no-log-capture']) as capture:
        rc = capture.wait(timeout=40)
        envelope = capture.load_json()
    assert envelope['data']['runner_result'] is not None, envelope
    return rc, envelope['data']['runner_result']


def admission(pw, out):
    # Every production capacity check uses the same record, not just this checker.
    caps = {'policy.sbpl_source': 262143, 'probe_plan': 256, 'policy.params': 1024,
            'step_id': 63, 'target': 511, 'key': 127, 'value': 383, 'args_count': 15, 'args_bytes': 127}
    for field, maximum in caps.items():
        is_count = field in ('probe_plan', 'policy.params', 'args_count')
        variants = ['exact', 'over'] if is_count else ['exact', 'over', 'unicode_exact', 'unicode_over']
        for variant in variants:
            actual = maximum + int(variant.endswith('over'))
            unit = 'items' if is_count else 'utf8_bytes'
            text = ('é' * (actual // 2) + 'x' * (actual % 2)) if variant.startswith('unicode') else 'x' * actual
            request = specimen()
            step = request['probe_plan'][0]
            if field == 'policy.sbpl_source':
                prefix = '(version 1)(allow default);'
                remaining = actual - len(prefix)
                text = ('é' * (remaining // 2) + 'x' * (remaining % 2)) if variant.startswith('unicode') else 'x' * remaining
                request['policy']['sbpl_source'] = prefix + text
            elif field == 'probe_plan':
                request['probe_plan'] = [dict(copy.deepcopy(step), step_id=f's{i}') for i in range(actual)]
            elif field == 'policy.params':
                request['policy']['params'] = {f'K{i}': 'v' for i in range(actual)}
            elif field == 'step_id': step['step_id'] = text
            elif field == 'target': step['attempt']['target'] = text
            elif field == 'key': request['policy']['params'] = {text: 'v'}
            elif field == 'value': request['policy']['params'] = {'K': text}
            else:
                step['attempt'] = {'kind': 'exec', 'action': 'spawn', 'target': '/usr/bin/true',
                                   'args': ['x'] * actual if field == 'args_count' else [text]}
            rc, runner = run(pw, out / f'{field}-{variant}', request)
            if actual > maximum:
                assert rc == 1 and runner['normalized_outcome'] == 'bad_request', runner
                failure = runner['admission_failure']
                assert failure['origin'] == 'runner_host', failure
                assert failure['field'] == ('args' if field.startswith('args_') else field), failure
                assert (failure['actual'], failure['maximum'], failure['unit']) == (actual, maximum, unit), failure
                assert runner.get('runner_subprocess') is None and runner.get('validator_subprocess') is None, runner
                assert runner['schema_version'] == 7, runner
                assert all('pid' in s['sandbox_check'] and s['sandbox_check']['pid'] is None for s in runner['steps']), runner
                assert all(s['attempt']['result_source'] == 'synthetic' and s['drift'] is None for s in runner['steps']), runner
                if field in ('step_id', 'target', 'args_count', 'args_bytes'):
                    assert failure['step_id'] == step['step_id'], failure
                if field == 'args_bytes': assert failure['index'] == 0, failure
                if field in ('key', 'value'): assert failure['parameter_key'] == next(iter(request['policy']['params'])), failure
            else:
                assert runner.get('admission_failure') is None, runner
                assert runner['normalized_outcome'] == 'ok' and rc == 0, runner
                assert runner['runner_subprocess']['reaped'] is True, runner
            print('PASS admission', field, variant, actual, maximum, unit, flush=True)


def validator(pw, out, mode):
    modes = {'validator_frames': ['invalid_utf8', 'incomplete_allow', 'incomplete_deny', 'diagnostic'],
             'validator_association': ['duplicate', 'unexpected', 'wrong_operation', 'wrong_filter_type', 'wrong_filter_value', 'missing_filter_value'], 'validator_overlong_request': ['real_overlong'], 'validator_removed_target': ['real_removed']}[mode]
    for case in modes:
        case_out = out / case
        case_out.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix='pw-validator-boundary-', dir='/private/tmp') as temp:
            paths = [Path(temp) / name for name in ['first', 'middle', 'last']]
            for path in paths: path.write_bytes(b'before')
            request = specimen()
            request['probe_plan'] = [{'step_id': name, 'sandbox_check': {'operation': 'file-write-data',
                'filter': {'kind': 'path', 'value': str(path)}},
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(path)}}
                for name, path in zip(['first', 'middle', 'last'], paths)]
            if case == 'real_overlong':
                request['probe_plan'][1]['sandbox_check']['operation'] = 'x' * 65536
                probes = [{'step_id': s['step_id'], 'operation': s['sandbox_check']['operation'],
                           'filter_type': 'PATH', 'filter_value': s['attempt']['target']} for s in request['probe_plan']]
                # Foundation sortedKeys encoding escapes '/' and uses compact ASCII
                # JSON for these ASCII-only probes. Compare total to host measurement.
                lines = [json.dumps(p, sort_keys=True, separators=(',', ':')).replace('/', '\\/').encode() + b'\n' for p in probes]
                (case_out / 'serialized-probes.ndjson').write_bytes(b''.join(lines))
                assert len(lines[0]) < 65536 < len(lines[1]) and len(lines[2]) < 65536
            elif case == 'real_removed':
                request['probe_plan'][2]['attempt']['action'] = 'unlink'
            else:
                fixture = Path(__file__).resolve().parents[2] / 'fixtures' / 'validator'
                executable = case_out / 'validator.py'
                shutil.copyfile(fixture / 'validator.py', executable); executable.chmod(0o755)
                shutil.copyfile(fixture / f'{case}.json', executable.with_suffix('.case.json'))
                request['_test_overrides'] = {'validator_executable_path': str(executable.resolve())}
            rc, runner = run(pw, case_out, request)
            assert runner.get('test_overrides') == request.get('_test_overrides'), runner
            if case == 'real_removed':
                assert not paths[2].exists(), 'unlink effect absent'
                assert all(path.read_bytes() != b'before' for path in paths[:2])
            else:
                assert all(path.read_bytes() != b'before' for path in paths), 'completed file effects absent'
            process = runner['validator_subprocess']
            assert process['reaped'] is True and process['exit_code'] == 0, process
            assert process.get('term_signal') is None and process.get('termination_request') is None, process
            assert process['wait_errors'] == [] and process['stdout_bytes_received'] > 0, process
            assert runner['runner_subprocess']['exit_code'] == 0, runner
            steps = runner['steps']
            assert [s['step_id'] for s in steps] == ['first', 'middle', 'last'], steps
            assert all(s['attempt']['result_source'] == 'worker' and s['attempt']['rc'] == 0 for s in steps), steps
            if case == 'real_removed':
                assert rc == 0 and runner['normalized_outcome'] == 'ok', runner
                assert process['expected_step_ids'] == ['first', 'middle', 'last'], process
                assert process['association_issues'] == [], process
                assert steps[2]['sandbox_check']['result_source'] == 'validator', steps[2]
                assert steps[2]['sandbox_check']['outcome'] == process['records'][2]['outcome'], steps[2]
            elif case == 'diagnostic':
                assert rc == 0 and runner['normalized_outcome'] == 'ok', runner
                assert process['records'][-1]['outcome'] == 'future_937', process
                assert '97319' in process['records'][-1]['raw_line'], process
                assert steps[2]['sandbox_check']['rc'] == -1 and steps[2]['sandbox_check']['result_source'] == 'validator', steps[2]
                assert steps[2]['sandbox_check']['native_rc'] is None and steps[2]['drift'] is None, steps[2]
            else:
                assert rc == 1 and runner['normalized_outcome'] != 'ok', runner
                missing = 1 if case == 'real_overlong' else 0 if case == 'duplicate' else 2
                for i, step in enumerate(steps):
                    if i == missing or (case == 'duplicate' and i == 2):
                        assert step['sandbox_check']['native_rc'] is None and step['drift'] is None, step
                        assert step['sandbox_check']['result_source'] == 'synthetic', step
                    else:
                        assert step['sandbox_check']['outcome'] == 'allow' and step['drift'] is False, step
                if case in ('invalid_utf8', 'incomplete_allow', 'incomplete_deny'):
                    assert runner['normalized_outcome'] == 'validator_decode_failure', runner
                    fault = process['decode_fault']
                    assert fault['origin'] == 'runner_host' and fault['kind'] == ('utf8' if case == 'invalid_utf8' else 'structure'), fault
                    emitted = (case_out / 'validator.emitted.ndjson').read_bytes()
                    tail = emitted.splitlines()[-1]
                    assert process['stdout_bytes_received'] == len(emitted), process
                    assert fault['frame_bytes'] == len(tail), fault
                    assert base64.b64decode(fault['context_b64']) == tail[:256], fault
                    assert fault['context_truncated'] == (len(tail) > 256), fault
                    assert len(process['records']) == 2, process
                elif case == 'real_overlong':
                    assert runner['normalized_outcome'] == 'validator_unavailable', runner
                    assert process['probe_bytes_written'] == process['probe_bytes_expected'] == sum(map(len, lines)), process
                    records = process['records']
                    assert [v.get('step_id') for v in records] == ['first', None, 'last'], records
                    assert records[1]['outcome'] == 'parse_error' and '64 KiB' in records[1]['error'], records
                    assert {v['kind'] for v in process['association_issues']} == {'missing_id', 'unassociated'}, process
                else:
                    assert runner['normalized_outcome'] == 'validator_unavailable', runner
                    kinds = {v['kind'] for v in process['association_issues']}
                    assert ('duplicate_id' if case == 'duplicate' else 'unexpected_id' if case == 'unexpected' else 'query_mismatch') in kinds, process
                    assert len(process['records']) == 3, process
                    if case not in ('duplicate', 'unexpected'):
                        emitted = [json.loads(line) for line in (case_out / 'validator.emitted.ndjson').read_bytes().splitlines()]
                        assert json.loads(process['records'][-1]['raw_line']) == emitted[-1]
                        assert process['association_issues'] == [{'origin': 'runner_host', 'kind': 'query_mismatch', 'step_id': 'last', 'count': 1}], process
            print('PASS validator', case, 'retained records', len(process['records']), flush=True)


def query_planning(pw, out):
    # Mixed and all-excluded plans prove that host decisions survive creation
    # even when no validator process exists to remember submitted IDs.
    for mixed in (False, True):
        with tempfile.TemporaryDirectory(prefix='pw-query-plan-', dir='/private/tmp') as temp:
            target = Path(temp) / 'created'
            request = specimen()
            create = {'step_id': 'created', 'sandbox_check': {'operation': 'file-write-create',
                'filter': {'kind': 'path', 'value': str(target)}},
                'attempt': {'kind': 'file', 'action': 'create', 'target': str(target)}}
            request['probe_plan'] = ([request['probe_plan'][0]] if mixed else []) + [create]
            rc, runner = run(pw, out / ('mixed-create' if mixed else 'all-excluded-create'), request)
            assert rc == 0 and runner['normalized_outcome'] == 'ok', runner
            assert target.exists(), 'create effect absent'
            step = runner['steps'][-1]
            assert step['attempt']['result_source'] == 'worker' and step['attempt']['rc'] == 0, step
            prediction = step['sandbox_check']
            assert prediction['outcome'] == 'prediction_unavailable', prediction
            assert prediction['missing_reason'] == 'query_not_requested', prediction
            assert prediction['native_rc'] is None and step['drift'] is None, step
            assert 'when the query was planned' in prediction['error'], prediction
            if mixed: assert runner['validator_subprocess']['expected_step_ids'] == ['s'], runner
            else: assert runner.get('validator_subprocess') is None, runner
            print('PASS frozen query decision after create', mixed, flush=True)


def fallback_helper(pw, out):
    request = specimen()
    request['policy']['sbpl_source'] = 'x' * (4 * 1024 * 1024 + 1)
    path = out / 'helper-request.json'
    path.write_text(json.dumps(request))
    helper = Path(pw).parent / 'sbpl-check'
    result = subprocess.run([str(helper), '--request', str(path)], capture_output=True, timeout=20)
    (out / 'helper.stdout').write_bytes(result.stdout)
    (out / 'helper.stderr').write_bytes(result.stderr)
    envelope = json.loads(result.stdout)
    assert result.returncode != 0, result
    assert envelope['result']['normalized_outcome'] == 'policy_too_large', envelope
    assert envelope['data']['compiled'] is False, envelope
    print('PASS helper-owned 4 MiB admission refusal; startup prose tested separately in Rust')


if __name__ == '__main__':
    mode, directory, pw = sys.argv[1:]
    out = Path(directory).resolve()
    if mode == 'admission': admission(pw, out)
    elif mode == 'fallback_helper': fallback_helper(pw, out)
    else:
        validator(pw, out, mode)
        if mode == 'validator_removed_target': query_planning(pw, out)
