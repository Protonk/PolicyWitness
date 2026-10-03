"""Independent CLI assertions for admission, framing, structure and association."""
import base64
import copy
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture


def specimen():
    return {'schema_version': 4, 'specimen_id': 'failure-boundaries',
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


def echoes(value, needle):
    """True when any decoded string leaf or key contains the needle. Containment,
    not equality: prose fields embed values (paths in spawn and dlopen diagnostics,
    IDs in duplicate-step messages), so a whole-field comparison would miss them."""
    return any(needle in text for text in string_values(value))


def string_values(value):
    """Decoded string leaves and dictionary keys, independent of JSON escaping."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from string_values(child)


def set_field(request, field, value):
    obj = request
    parts = field.split('.')
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def admission(pw, out):
    # Every production capacity check uses the same record, not just this checker.
    # Query strings and filter/attempt labels are host-only (never shared memory);
    # the orchestrator refuses them with the same record.
    caps = {'policy.sbpl_source': 262143, 'probe_plan': 256, 'policy.params': 1024,
            'step_id': 63, 'target': 511, 'key': 127, 'value': 383, 'args_count': 15, 'args_bytes': 127,
            'sandbox_check.operation': 127, 'sandbox_check.filter.value': 511,
            'sandbox_check.filter.kind': 127, 'attempt.kind': 127, 'attempt.action': 127,
            'specimen_id': 255, 'run_kind': 63, 'policy.format': 63,
            '_test_overrides.worker_executable_path': 1023,
            '_test_overrides.validator_executable_path': 1023}
    # At-limit strings that pass admission but cannot run: the format is not sbpl
    # and the seam paths do not exist. Each fails later, in its own way.
    later = {'policy.format': 'bad_request', 'sandbox_check.filter.kind': 'bad_request',
             'attempt.kind': 'bad_request', 'attempt.action': 'bad_request',
             '_test_overrides.worker_executable_path': 'worker_spawn_failed',
             '_test_overrides.validator_executable_path': 'validator_spawn_failed'}
    top_level = ('specimen_id', 'run_kind', 'policy.format') + tuple(f for f in caps if f.startswith('_test_overrides.'))
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
            # At-limit runs must still complete: an unrecognized operation name is a
            # per-step unsupported_operation verdict and a nonexistent query path is a
            # per-step prediction_unavailable, never a run-level failure.
            elif field == 'sandbox_check.operation': step['sandbox_check']['operation'] = text
            elif field == 'sandbox_check.filter.kind': step['sandbox_check']['filter']['kind'] = text
            elif field in ('attempt.kind', 'attempt.action'): step['attempt'][field.split('.')[1]] = text
            elif field == 'sandbox_check.filter.value' or field.startswith('_test_overrides.'):
                remaining = actual - 1
                tail = ('é' * (remaining // 2) + 'x' * (remaining % 2)) if variant.startswith('unicode') else 'x' * remaining
                if field.startswith('_test_overrides.'):
                    request['_test_overrides'] = {field.split('.')[1]: '/' + tail}
                    assert len(request['_test_overrides'][field.split('.')[1]].encode()) == actual
                else:
                    step['sandbox_check']['filter']['value'] = '/' + tail
                    assert len(step['sandbox_check']['filter']['value'].encode()) == actual
            elif field == 'specimen_id': request['specimen_id'] = text
            elif field == 'run_kind': request['run_kind'] = text
            elif field == 'policy.format': request['policy']['format'] = text
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
                # Nothing ran and nothing is echoed: a refusal reply carries no steps,
                # and the record never repeats the refused string itself.
                assert runner['steps'] == [], runner
                assert not echoes(runner, text), 'refusal echoed the refused string'
                if field in ('target', 'args_count', 'args_bytes',
                             'sandbox_check.operation', 'sandbox_check.filter.value',
                             'sandbox_check.filter.kind', 'attempt.kind', 'attempt.action'):
                    assert failure['step_id'] == step['step_id'] and failure['step_index'] == 0, failure
                if field == 'step_id':
                    assert failure.get('step_id') is None and failure['step_index'] == 0, failure
                if field.startswith(('sandbox_check.', 'attempt.')):
                    assert failure.get('parameter_key') is None and failure.get('index') is None, failure
                if field == 'args_bytes': assert failure['index'] == 0, failure
                if field == 'key': assert failure.get('parameter_key') is None, failure
                if field == 'value': assert failure['parameter_key'] == next(iter(request['policy']['params'])), failure
                if field in top_level:
                    assert failure.get('step_id') is None and failure.get('step_index') is None, failure
                if field == 'specimen_id': assert runner['specimen_id'] == '<admission_refused>', runner
                if field == 'run_kind': assert runner.get('run_kind') is None, runner
                if field == 'policy.format': assert runner['policy_format'] == 'unknown', runner
                if field.startswith('_test_overrides.'):
                    assert (runner.get('test_overrides') or {}).get(field.split('.')[1]) is None, runner
            elif field in later:
                assert runner.get('admission_failure') is None, runner
                assert rc == 1 and runner['normalized_outcome'] == later[field], runner
                if later[field] == 'bad_request':
                    code = {'policy.format': 'unsupported_policy_format', 'sandbox_check.filter.kind': 'unknown_filter_kind',
                            'attempt.kind': 'unsupported_attempt', 'attempt.action': 'unsupported_attempt'}[field]
                    assert runner['request_failure']['code'] == code, runner
                    assert runner['steps'] == [] and runner.get('runner_subprocess') is None and runner.get('validator_subprocess') is None, runner
                if field.startswith('_test_overrides.'):
                    assert runner['test_overrides'][field.split('.')[1]] == request['_test_overrides'][field.split('.')[1]], runner
            else:
                assert runner.get('admission_failure') is None, runner
                assert runner['normalized_outcome'] == 'ok' and rc == 0, runner
                assert runner['runner_subprocess']['reaped'] is True, runner
                if field == 'specimen_id': assert runner['specimen_id'] == text, runner
                if field == 'run_kind': assert runner['run_kind'] == text, runner
            print('PASS admission', field, variant, actual, maximum, unit, flush=True)
    # Capacity precedes meaning: an oversized ID must be refused before an
    # empty operation or duplicate ID, and never appear in the reply.
    huge = 'x' * 4096
    empty = specimen(); empty['probe_plan'][0]['step_id'] = huge; empty['probe_plan'][0]['sandbox_check']['operation'] = ''
    duplicate = specimen(); duplicate['probe_plan'] = [copy.deepcopy(duplicate['probe_plan'][0]) for _ in range(2)]
    for step in duplicate['probe_plan']: step['step_id'] = huge
    for name, request in [('empty_operation', empty), ('duplicate_step_id', duplicate)]:
        rc, runner = run(pw, out / f'precedence-{name}', request)
        assert rc == 1 and runner['normalized_outcome'] == 'bad_request', runner
        failure = runner['admission_failure']
        assert (failure['field'], failure['actual'], failure['maximum']) == ('step_id', 4096, 63), failure
        assert failure.get('step_id') is None and failure['step_index'] == 0, failure
        assert not echoes(runner, huge), 'validation diagnostic echoed an unbounded string'
        print('PASS admission precedence', name, flush=True)

    # A refusal must sanitize every echoed field, not only the first violation.
    fields = ['specimen_id', 'run_kind', 'policy.format',
              '_test_overrides.worker_executable_path', '_test_overrides.validator_executable_path']
    with tempfile.TemporaryDirectory(prefix='pw-admission-', dir='/private/tmp') as temp:
        target = Path(temp) / 'write-target'
        target.write_bytes(b'before')
        for i, (first, second) in enumerate(itertools.combinations(fields, 2)):
            request = specimen()
            request['probe_plan'][0]['attempt'].update(action='open_write', target=str(target))
            rejected = 'é' * 32768
            for field in [first, second]: set_field(request, field, rejected)
            rc, runner = run(pw, out / f'combined-{i}', request)
            assert rc == 1 and runner['normalized_outcome'] == 'bad_request', runner
            assert runner['admission_failure']['field'] == first, runner
            assert not echoes(runner, rejected), 'secondary oversized field escaped refusal projection'
            assert len(json.dumps(runner).encode()) < 4096, 'refusal size grew with rejected inputs'
            assert runner['steps'] == [] and runner.get('runner_subprocess') is None, runner
            assert target.read_bytes() == b'before', 'attempt ran despite refusal'
        # Native C strings must not silently change meaning at the first NUL.
        native = ['step_id', 'target', 'args', 'key', 'value', 'policy.sbpl_source',
                  'sandbox_check.operation', 'sandbox_check.filter.value'] + fields[3:]
        # The two helper overrides are the controller's observation inputs as
        # well: a NUL in either is refused by the host and recorded by the
        # dossier without reading the path.
        for i, field in enumerate(native):
            request = specimen()
            good = request['probe_plan'][0]
            good['attempt'].update(action='open_write', target=str(target))
            bad = copy.deepcopy(good); bad['step_id'] = 'bad'
            request['probe_plan'].append(bad)
            text = 'prefix\0suffix'
            if field == 'step_id': bad['step_id'] = text
            elif field == 'target': bad['attempt']['target'] = text
            elif field == 'args': bad['attempt'] = dict(kind='exec', action='spawn', target='/usr/bin/true', args=[text])
            elif field in ('key', 'value'): request['policy']['params'] = {text: 'v'} if field == 'key' else {'K': text}
            elif field.startswith('sandbox_check.'): set_field(bad, field, text)
            else: set_field(request, field, text)
            rc, runner = run(pw, out / f'nul-{i}', request)
            assert rc == 1 and runner['normalized_outcome'] == 'bad_request', runner
            failure = runner['admission_failure']
            assert (failure['field'], failure['unit'], failure['actual'], failure['maximum']) == (field, 'nul_bytes', 1, 0), failure
            assert not echoes(runner, text), runner
            assert runner['steps'] == [] and runner.get('runner_subprocess') is None, runner
            assert target.read_bytes() == b'before', 'earlier write ran before invalid native argument was rejected'
        print('PASS combined refusals and native NUL admission', flush=True)


def validator(pw, out, mode):
    modes = {'validator_frames': ['invalid_utf8', 'incomplete_allow', 'incomplete_deny', 'diagnostic'],
             'validator_association': ['duplicate', 'unexpected', 'wrong_operation', 'wrong_filter_type', 'wrong_filter_value', 'missing_filter_value'], 'validator_overlong_request': ['real_overlong'], 'validator_removed_target': ['real_removed'],
             'validator_control_characters': ['real_control']}[mode]
    for case in modes:
        case_out = out / case
        case_out.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix='pw-validator-boundary-', dir='/private/tmp') as temp:
            # Control characters are legal in file names and in step IDs. Foundation
            # sends them to the validator as \uXXXX escapes and the validator must
            # echo them escaped; one raw byte would cost every later prediction.
            names = ['first\x01', 'mid\x08dle', 'la\x1bst\x1f'] if case == 'real_control' else ['first', 'middle', 'last']
            paths = [Path(temp) / name for name in names]
            for path in paths: path.write_bytes(b'before')
            request = specimen()
            request['probe_plan'] = [{'step_id': name, 'sandbox_check': {'operation': 'file-write-data',
                'filter': {'kind': 'path', 'value': str(path)}},
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(path)}}
                for name, path in zip(names, paths)]
            if case == 'real_overlong':
                request['probe_plan'][1]['sandbox_check']['operation'] = 'x' * 65536
                probes = [{'step_id': s['step_id'], 'operation': s['sandbox_check']['operation'],
                           'filter_type': 'PATH', 'filter_value': s['attempt']['target']} for s in request['probe_plan']]
                # Foundation sortedKeys encoding escapes '/' and uses compact ASCII
                # JSON for these ASCII-only probes. Retained to show the middle line
                # would exceed the validator line cap had admission let it through.
                lines = [json.dumps(p, sort_keys=True, separators=(',', ':')).replace('/', '\\/').encode() + b'\n' for p in probes]
                (case_out / 'serialized-probes.ndjson').write_bytes(b''.join(lines))
                assert len(lines[0]) < 65536 < len(lines[1]) and len(lines[2]) < 65536
            elif case == 'real_removed':
                request['probe_plan'][2]['attempt']['action'] = 'unlink'
            elif case == 'real_control':
                pass  # the real validator and an unmodified plan; the names carry the control characters
            else:
                fixture = Path(__file__).resolve().parents[2] / 'fixtures' / 'validator'
                executable = case_out / 'validator.py'
                shutil.copyfile(fixture / 'validator.py', executable); executable.chmod(0o755)
                shutil.copyfile(fixture / f'{case}.json', executable.with_suffix('.case.json'))
                request['_test_overrides'] = {'validator_executable_path': str(executable.resolve())}
            rc, runner = run(pw, case_out, request)
            assert runner.get('test_overrides') == request.get('_test_overrides'), runner
            if case == 'real_control':
                assert rc == 0 and runner['normalized_outcome'] == 'ok', runner
                assert all(path.read_bytes() != b'before' for path in paths), 'completed file effects absent'
                process = runner['validator_subprocess']
                assert process['reaped'] is True and process['exit_code'] == 0, process
                assert process['association_issues'] == [] and process.get('decode_fault') is None, process
                assert [v['step_id'] for v in process['records']] == names, process
                for record, path in zip(process['records'], paths):
                    line = record['raw_line']
                    assert all(ord(ch) >= 0x20 for ch in line), 'validator echoed a raw control byte'
                    assert json.loads(line)['filter_value'] == str(path), line
                steps = runner['steps']
                assert [s['step_id'] for s in steps] == names, steps
                assert all(s['sandbox_check']['outcome'] == 'allow' and s['sandbox_check']['result_source'] == 'validator'
                           and s['sandbox_check']['filter_value'] == str(path) for s, path in zip(steps, paths)), steps
                assert all(s['attempt']['result_source'] == 'worker' and s['attempt']['rc'] == 0 for s in steps), steps
                print('PASS validator', case, 'control characters round-tripped in', len(steps), 'steps', flush=True)
                continue
            if case == 'real_overlong':
                # Query admission closes the CLI route to the validator's line cap:
                # the overlong operation is refused before any process work, and the
                # unchanged file contents prove no attempt ran. The exact cap and its
                # drain/recovery stay owned by the native runner_abi_layout boundary.
                assert rc == 1 and runner['normalized_outcome'] == 'bad_request', runner
                failure = runner['admission_failure']
                assert failure['origin'] == 'runner_host' and failure['field'] == 'sandbox_check.operation', failure
                assert (failure['actual'], failure['maximum'], failure['unit']) == (65536, 127, 'utf8_bytes'), failure
                assert failure['step_id'] == 'middle', failure
                assert all(path.read_bytes() == b'before' for path in paths), 'attempt ran despite refusal'
                assert runner.get('runner_subprocess') is None and runner.get('validator_subprocess') is None, runner
                assert runner['steps'] == [], runner  # a refusal echoes nothing
                # The largest admitted probe, every byte escaped to six, stays far inside
                # the 65,534-byte line; step_id 63, operation 127 and filter value 511 are
                # the admission limits and IOKIT_REGISTRY_ENTRY_CLASS the longest type name.
                worst = {'step_id': '\x01' * 63, 'operation': '\x01' * 127,
                         'filter_type': 'IOKIT_REGISTRY_ENTRY_CLASS', 'filter_value': '\x01' * 511}
                worst_line = json.dumps(worst, sort_keys=True, separators=(',', ':')).encode() + b'\n'
                (case_out / 'largest-admitted-probe.ndjson').write_bytes(worst_line)
                assert b'\\u0001' in worst_line and len(worst_line) < 8192, len(worst_line)
                print('PASS validator', case, 'refused at admission; largest admitted probe line is',
                      len(worst_line), 'bytes', flush=True)
                continue
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
                assert steps[2]['sandbox_check']['native_rc'] is None, steps[2]
                assert steps[2]['comparison']['order'] == 'unestablished', steps[2]
            else:
                assert rc == 1 and runner['normalized_outcome'] != 'ok', runner
                missing = 0 if case == 'duplicate' else 2
                for i, step in enumerate(steps):
                    if i == missing or (case == 'duplicate' and i == 2):
                        assert step['sandbox_check']['native_rc'] is None, step
                        assert step['sandbox_check']['result_source'] == 'synthetic', step
                        assert step['comparison']['order'] == 'unestablished', step
                    else:
                        assert step['sandbox_check']['outcome'] == 'allow', step
                        assert step['comparison']['observation'] == 'succeeded' and step['comparison']['order'] == 'query_first', step
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
            assert prediction['native_rc'] is None, step
            assert step['comparison']['order'] == 'unestablished', step
            assert step['comparison']['limitations'] == ['query_plan:path_unresolved_at_planning'], step
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
    assert result.returncode == 1, result
    assert envelope['result']['normalized_outcome'] == 'policy_too_large', envelope
    assert envelope['result']['ok'] is False and envelope['result']['exit_code'] == 1, envelope
    data = envelope['data']
    # A refused input performs no import walk and no native call: both groups
    # are explicit nulls and the source hash is withheld.
    for group in ('compile', 'import_inventory', 'policy_sha256'):
        assert group in data and data[group] is None, (group, data)
    for retired in ('compiled', 'compile_error', 'imports', 'imports_truncated', 'imports_cycle',
                    'policy_closure_sha256', 'params_referenced', 'params_supplied', 'params_missing',
                    'params_unused', 'params_scan_complete', 'param_scan'):
        assert retired not in data, (retired, data)
    assert data['params_present'] is False and data['params_count'] == 0, data
    print('PASS helper-owned 4 MiB admission refusal with null compile and inventory groups; startup prose tested separately in Rust')


if __name__ == '__main__':
    mode, directory, pw = sys.argv[1:]
    out = Path(directory).resolve()
    if mode == 'admission': admission(pw, out)
    elif mode == 'fallback_helper': fallback_helper(pw, out)
    else:
        validator(pw, out, mode)
        if mode == 'validator_removed_target': query_planning(pw, out)
