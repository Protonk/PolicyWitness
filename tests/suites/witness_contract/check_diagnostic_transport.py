"""Transport controls use independent inputs; they establish no native cause."""
import errno
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture

ROOT = Path(__file__).resolve().parents[3]
INPUTS = json.loads((ROOT / 'tests/fixtures/diagnostic_transport/cases.json').read_text())


def run(pw, output, request):
    with RunCapture(pw, output, request, cli_args=['--no-log-capture']) as capture:
        rc = capture.wait(timeout=30)
        envelope = capture.load_json()
    runner = envelope['data']['runner_result']
    assert runner['schema_version'] == 6, runner
    assert runner.get('test_overrides') == request['_test_overrides'], runner
    return rc, runner


def specimen(source, target, overrides):
    return {'schema_version': 1, 'specimen_id': 'unfamiliar-transport',
            'policy': {'format': 'sbpl', 'sbpl_source': source},
            'probe_plan': [{'step_id': 's', 'sandbox_check': {'operation': 'file-write-data',
                'filter': {'kind': 'path', 'value': str(target)}},
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}],
            '_test_overrides': overrides}


def check_worker(pw, output, fixture, mode):
    oracle = INPUTS['worker'][int('beta' in mode)]
    with tempfile.TemporaryDirectory(prefix='pw-transport-', dir='/private/tmp') as temp:
        target = Path(temp) / 'untouched'
        before = b'independent no-effect witness'
        target.write_bytes(before)
        source = mode if mode != 'close_transport_beta' else mode + '\n' + 'x' * 200000
        request = specimen(source, target, {'worker_executable_path': str(fixture.resolve())})
        rc, runner = run(pw, output, request)
        after = target.read_bytes()
        (output / 'before.bin').write_bytes(before)
        (output / 'after.bin').write_bytes(after)
        (output / 'oracle.json').write_text(json.dumps(oracle, ensure_ascii=False, indent=2)+'\n')
    assert rc == 1 and runner['normalized_outcome'] == 'runner_failed', runner
    process = runner['runner_subprocess']
    assert process['pid'] > 0 and runner['pid'] == process['pid'], process
    assert process['reaped'] is True and process['exit_code'] == 23, process
    assert process.get('term_signal') is None and process.get('termination_request') is None, process
    assert process['wait_errors'] == [], process
    assert runner['sandboxed_after_apply'] is False and runner.get('validator_subprocess') is None, runner
    assert after == before, 'transport fixture must not perform the requested attempt'
    step = runner['steps'][0]
    assert step['sandbox_check']['pid'] == process['pid'], step
    for channel in ('sandbox_check', 'attempt'):
        assert step[channel]['result_source'] == 'synthetic' and step[channel]['native_rc'] is None, step
    assert step['drift'] is None and step['deny_signal'] is None, step
    evidence = process.get('worker_evidence')
    if mode == 'transport_incompatible':
        assert evidence is None, evidence
        assert 'native return unavailable' in runner['error'], runner
        return
    assert evidence['abi_version'] == 6, evidence
    progress = dict(evidence['progress']); progress.pop('raw')
    assert progress == oracle['progress'], progress
    if mode in ('transport_absent', 'transport_unpublished', 'transport_malformed'):
        state = {'transport_absent': 'absent', 'transport_unpublished': 'incomplete', 'transport_malformed': 'invalid'}[mode]
        assert evidence['failure_state'] == state and evidence.get('failure') is None, evidence
        assert 'sandbox_apply' not in runner['error'] and 'sandbox_compile_string' not in runner['error'], runner
    else:
        assert evidence['failure_state'] == 'published', evidence
        assert evidence['failure'] == oracle['failure'], (mode, evidence['failure'], oracle['failure'])
        assert str(oracle['failure']['code']) in runner['error'], runner
        if 'beta' in mode: assert 'sandbox_apply' in runner['error'], runner  # operation 8, independently of code
        else: assert 'sandbox_apply' not in runner['error'] and 'sandbox_compile_string' not in runner['error'], runner
    diagnostic = evidence['diagnostic']
    if mode == 'transport_beta_truncated':
        assert diagnostic == {'state': 2, 'status': 'truncated', 'length': 4095, 'text': 'T'*4095}, diagnostic
    elif mode == 'transport_bad_text':
        assert diagnostic == {'state': 1, 'status': 'invalid'}, diagnostic
        assert evidence['failure'] == oracle['failure'], evidence
    else:
        assert diagnostic == {'state': 1, 'status': 'complete', 'length': len(oracle['text'].encode()), 'text': oracle['text']}, diagnostic
    if mode == 'close_transport_beta':
        transfer = process['policy_transfer_error']
        assert transfer['errno'] == errno.EPIPE and transfer['bytes_written'] < transfer['bytes_expected'] == len(source.encode()), transfer
        assert process['poll_stop_reason'] == 'policy_write_error' and not process['done_observed'], process
        assert 'host write(policy_pipe)' in runner['error'], runner
    else:
        assert process['done_observed'] is True and process.get('policy_transfer_error') is None, process


def check_validator(pw, output, bad_tail):
    output.mkdir(parents=True)
    executable = output / 'validator.py'
    shutil.copy2(ROOT / 'tests/fixtures/validator/validator.py', executable)
    executable.chmod(0o755)
    responses = [{'probe_index': i, 'outcome': 'future_transport_'+str(i), 'rc': 0, 'errno': 0,
                  'fields': {'error': 'controlled diagnostic '+str(i), 'diagnostic': record},
                  'omit': ['rc', 'errno']} for i, record in enumerate(INPUTS['diagnostics'])]
    responses.append({'probe_index': 2, 'outcome': 'allow', 'rc': 0, 'errno': 0})
    transcript = {'probe_count': 3, 'responses': responses, 'tail': 'invalid_utf8' if bad_tail else 'eof'}
    executable.with_suffix('.case.json').write_text(json.dumps(transcript, ensure_ascii=False, indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='pw-transport-validator-', dir='/private/tmp') as temp:
        target = Path(temp) / 'effect'
        target.write_bytes(b'before')
        (output/'before.bin').write_bytes(b'before')
        request = specimen('(version 1)(allow default)', target, {'validator_executable_path': str(executable.resolve())})
        request['probe_plan'] = [dict(request['probe_plan'][0], step_id='s'+str(i)) for i in range(3)]
        rc, runner = run(pw, output, request)
        after = target.read_bytes()
        (output/'after.bin').write_bytes(after)
    assert after != b'before', 'actual worker effects were lost'
    assert rc == int(bad_tail), runner
    assert runner['normalized_outcome'] == ('validator_decode_failure' if bad_tail else 'ok'), runner
    assert runner['sandboxed_after_apply'] is True and runner['runner_subprocess']['exit_code'] == 0, runner
    process = runner['validator_subprocess']
    assert process['pid'] > 0 and process['pid'] != runner['runner_subprocess']['pid'], process
    assert process['reaped'] is True and process['exit_code'] == 0 and process['stdout_collection_stop'] == 'eof', process
    assert process.get('io_error') is None and process['association_issues'] == [], process
    incoming = json.loads(executable.with_suffix('.received.json').read_text())
    assert incoming['target_pid'] == runner['runner_subprocess']['pid'], incoming
    assert [p['step_id'] for p in incoming['probes']] == ['s0', 's1', 's2'], incoming
    emitted = executable.with_suffix('.emitted.ndjson').read_bytes()
    original = [json.loads(line) for line in emitted.splitlines()[:3]]
    assert process['stdout_bytes_received'] == len(emitted), process
    records = process['records']
    assert len(records) == 3, records
    for i in range(2):
        assert json.loads(records[i]['raw_line']) == original[i], records[i]
        assert json.loads(records[i]['raw_line'])['diagnostic'] == INPUTS['diagnostics'][i], records[i]
        assert records[i]['outcome'] == 'future_transport_'+str(i), records[i]
        step = runner['steps'][i]
        assert step['sandbox_check']['result_source'] == 'validator', step
        assert step['sandbox_check']['native_rc'] is None and step['sandbox_check']['rc'] == -1, step
        assert step['sandbox_check']['error'] == 'controlled diagnostic '+str(i) and step['drift'] is None, step
        assert step['attempt']['result_source'] == 'worker' and step['attempt']['rc'] == 0, step
    assert records[2]['outcome'] == 'allow' and records[2]['rc'] == 0, records[2]
    assert runner['steps'][2]['sandbox_check']['native_rc'] == 0 and runner['steps'][2]['drift'] is False, runner
    if bad_tail:
        assert process['decode_fault']['kind'] == 'utf8' and process['decode_fault']['context_b64'] == '/w==', process
        assert process['decode_fault']['byte_offset'] == len(emitted)-2, process
    else: assert process.get('decode_fault') is None, process


def main():
    pw, directory, fixture_path = sys.argv[1:]
    output, fixture = Path(directory), Path(fixture_path)
    failures = []
    modes = ['transport_alpha', 'transport_beta', 'transport_beta_truncated', 'transport_bad_text',
             'transport_absent', 'transport_unpublished', 'transport_malformed', 'transport_incompatible', 'close_transport_beta']
    checks = [(mode, lambda mode=mode: check_worker(pw, output/mode, fixture, mode)) for mode in modes]
    checks += [('validator_'+str(bad), lambda bad=bad: check_validator(pw, output/('validator_'+str(bad)), bad)) for bad in (False, True)]
    for name, check in checks:
        try:
            check()
            print('PASS', name, flush=True)
        except AssertionError as error:
            failures.append(name+': '+str(error))
            print('FAIL', name, str(error), flush=True)
    (output/'checks.json').write_text(json.dumps({'checks': len(checks), 'failures': failures}, indent=2)+'\n')
    assert not failures, '\n'.join(failures)


if __name__ == '__main__': main()
