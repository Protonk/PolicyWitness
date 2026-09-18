"""Interrupted transfer, competing host failure and completed effects reach the CLI."""
import errno
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture

pw, output, fixture = sys.argv[1:]
out = Path(output)
modes = [
    ('close_report', 'close_report\n' + 'x' * 200000, {'worker_executable_path': str(Path(fixture).resolve())}),
    ('close_absent', 'close_absent\n' + 'x' * 200000, {'worker_executable_path': str(Path(fixture).resolve())}),
    ('mapping', '(version 1)(allow default)', {'worker_executable_path': str(Path(fixture).resolve()) + '.map-failure'}),
    ('after_probes', '(version 1)(allow default)', {'worker_post_apply_kill_signal': 9, 'worker_post_apply_hang_ms': 1500}),
]
with tempfile.TemporaryDirectory(prefix='pw-sparse-', dir='/private/tmp') as temp:
    target = Path(temp) / 'effect'
    for mode, policy, overrides in modes:
        target.write_bytes(b'independent pre-run bytes')
        before = target.read_bytes()
        request = {'schema_version': 1, 'specimen_id': 'sparse-' + mode,
                   'policy': {'format': 'sbpl', 'sbpl_source': policy},
                   'probe_plan': [{'step_id': 'write',
                       'sandbox_check': {'operation': 'file-write-data', 'filter': {'kind': 'path', 'value': str(target)}},
                       'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}]}
        if overrides:
            request['_test_overrides'] = overrides
        with RunCapture(pw, out / mode, request, cli_args=['--no-log-capture']) as capture:
            rc = capture.wait(timeout=30)
            envelope = capture.load_json()
        after = target.read_bytes()
        (out / mode / 'before.bin').write_bytes(before)
        (out / mode / 'after.bin').write_bytes(after)
        runner = envelope['data']['runner_result']
        assert rc == 1 and runner['normalized_outcome'] == 'runner_failed', runner
        assert runner.get('test_overrides') == overrides, runner
        process = runner['runner_subprocess']
        evidence = process['worker_evidence']
        assert process['reaped'] is True, process
        assert process.get('termination_request') is None, process
        step = runner['steps'][0]
        assert step['deny_signal'] is None, step
        if mode == 'after_probes':
            assert process['term_signal'] == 9 and process['done_observed'] is False, process
            assert runner['sandboxed_after_apply'] is True, runner
            assert step['attempt']['result_source'] == 'worker' and step['attempt']['rc'] == 0, step
            assert step['sandbox_check']['outcome'] == 'allow', step
            assert after != before, (step, after)
            assert evidence['failure_state'] == 'absent', evidence
        else:
            assert after == before and runner['sandboxed_after_apply'] is False, runner
            assert step['attempt']['native_rc'] is None and step['sandbox_check']['native_rc'] is None, step
            assert step['drift'] is None, step
            assert 'sandbox_apply' not in runner['error'], runner
            if mode == 'mapping':
                assert process['exit_code'] == 3, process
                assert evidence.get('failure') is None and evidence.get('progress') is None, evidence
            else:
                transfer = process['policy_transfer_error']
                assert transfer['errno'] == errno.EPIPE, transfer
                assert transfer['bytes_expected'] == len(policy.encode()), transfer
                assert 0 <= transfer['bytes_written'] < transfer['bytes_expected'], transfer
                assert process['poll_stop_reason'] == 'policy_write_error', process
                if mode == 'close_report':
                    assert evidence['failure']['code'] == 987654 and process['exit_code'] == 23, evidence
                else:
                    assert evidence.get('failure') is None and process['exit_code'] == 23, evidence
        print('PASS', mode, flush=True)
