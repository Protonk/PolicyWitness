"""Real operation evidence and controlled transport are separate observations."""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture

pw, output, fixture = sys.argv[1:]
out = Path(output)
with tempfile.TemporaryDirectory(prefix='pw-evidence-', dir='/private/tmp') as temp:
    target = Path(temp) / 'effect'
    for mode, source, override in [
        ('success', '(version 1)(allow default)', None),
        ('compile', '(version 1)(not-a-real-sandbox-operation)', None),
        *[(mode, mode, {'worker_executable_path': str(Path(fixture).resolve())})
          for mode in ('diagnostic_rich', 'diagnostic_missing', 'diagnostic_truncated')],
        ('unfamiliar', 'unfamiliar', {'worker_executable_path': str(Path(fixture).resolve())}),
    ]:
        target.write_bytes(b'original independent witness')
        before = target.read_bytes()
        request = {'schema_version': 1, 'specimen_id': 'worker-evidence-' + mode,
                   'policy': {'format': 'sbpl', 'sbpl_source': source},
                   'probe_plan': [{'step_id': 'write',
                       'sandbox_check': {'operation': 'file-write-data',
                                         'filter': {'kind': 'path', 'value': str(target)}},
                       'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}]}
        if override:
            request['_test_overrides'] = override
        with RunCapture(pw, out / mode, request, cli_args=['--no-log-capture']) as capture:
            rc = capture.wait(timeout=30)
            envelope = capture.load_json()
        after = target.read_bytes()
        (out / mode / 'before.bin').write_bytes(before)
        (out / mode / 'after.bin').write_bytes(after)
        runner = envelope['data']['runner_result']
        process = runner['runner_subprocess']
        evidence = process['worker_evidence']
        assert evidence['abi_version'] == 6, evidence
        assert runner.get('test_overrides') == override, runner
        assert process['reaped'] and process['exit_code'] == 0, process
        step = runner['steps'][0]
        assert step['deny_signal'] is None, step
        assert rc == (0 if mode == 'success' else 1), envelope
        assert runner['normalized_outcome'] == ('ok' if mode == 'success' else 'runner_failed'), runner
        if mode == 'success':
            assert evidence['failure_state'] == 'absent' and evidence.get('failure') is None, evidence
            assert runner['sandboxed_after_apply'] is True, runner
            assert evidence['progress']['operation'] == 10, evidence
            assert step['sandbox_check']['outcome'] == 'allow', step
            assert step['sandbox_check']['result_source'] == 'validator', step
            assert step['attempt']['result_source'] == 'worker', step
            assert step['attempt']['rc'] == 0 and after != before, (step, after)
            assert step['attempt']['native_rc'] is None, 'PW status must not become a raw syscall return'
        else:
            assert runner['sandboxed_after_apply'] is False, runner
            assert after == before, (mode, after)
            assert step['sandbox_check']['native_rc'] is None, step
            assert step['sandbox_check']['missing_reason'] == 'validator_not_invoked', step
            assert step['attempt']['native_rc'] is None and step['drift'] is None, step
            f = evidence['failure']
            if mode == 'compile' or mode.startswith('diagnostic_'):
                assert f['operation'] == 5 and f['native_kind'] == 2 and f['native_result'] == 0, f
                assert 'errno' not in f, f
                assert 'sandbox_compile_string' in runner['error'], runner
                diagnostic = evidence['diagnostic']
                expected = 'absent' if mode == 'diagnostic_missing' else 'truncated' if mode == 'diagnostic_truncated' else 'complete'
                assert diagnostic['status'] == expected, diagnostic
                if mode == 'compile':
                    assert diagnostic['text'] and 'not-a-real-sandbox-operation' in diagnostic['text'], diagnostic
                    assert diagnostic['text'] in runner['error'], runner
                if mode == 'diagnostic_truncated':
                    assert diagnostic['length'] == 4095 and diagnostic['text'] == 'x' * 4095, diagnostic
                if mode == 'diagnostic_rich':
                    assert diagnostic['text'] == 'controlled compiler diagnostic', diagnostic
            else:
                assert f == {'operation': 239, 'code': 4000000001, 'native_kind': 77,
                             'native_result': -123, 'errno': 0, 'index': 17, 'detail': 7654321}, f
                assert evidence['progress']['operation'] == 239, evidence
                assert not any(x in runner['error'] for x in ('sandbox_apply', 'sandbox_compile_string')), runner
        print('PASS', mode, flush=True)
