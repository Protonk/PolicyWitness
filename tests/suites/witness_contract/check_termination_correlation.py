"""Real denied attempts, unrelated self-signal, and capture on failure/success.

Captured kernel events are optional: deterministic Rust controls cover their
association even on hosts where unified logs are blocked or contain no match.
"""
import errno
import json
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory)
    observations = []
    with tempfile.TemporaryDirectory(prefix='pw-correlation-', dir='/private/tmp') as work:
        target = Path(work) / secrets.token_hex(12)
        seed = secrets.token_bytes(64)
        target.write_bytes(seed)
        ids = [secrets.token_hex(8), secrets.token_hex(8)]
        base = {
            'schema_version': 1, 'specimen_id': secrets.token_hex(12),
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'
                       '(deny file-write-data (literal (param "BLOCKED")))',
                       'params': {'BLOCKED': str(target)}},
            # Query operation intentionally differs from the attempted operation.
            # Repeated attempts cannot be assigned uniquely to a captured event.
            'probe_plan': [{'step_id': step_id,
                           'sandbox_check': {'operation': 'file-read-data',
                                             'filter': {'kind': 'path', 'value': str(target)}},
                           'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}
                          for step_id in ids],
        }
        overrides = {'worker_post_apply_kill_signal': 9, 'worker_post_apply_hang_ms': 1500}
        for name, signaled, capture_enabled in [('signal_disabled', True, False),
                                               ('signal_capture', True, True),
                                               ('success_capture', False, True)]:
            specimen = dict(base)
            if signaled:
                specimen['_test_overrides'] = overrides
            args = ['--timeout-ms', '20000', '--log-last', '10s']
            if not capture_enabled:
                args.append('--no-log-capture')
            run = RunCapture(pw, out / name, specimen, cli_args=args)
            (run.out / 'file.before').write_bytes(target.read_bytes())
            with run:
                rc = run.wait(timeout=60)
                envelope = run.load_json()
            after = target.read_bytes()
            (run.out / 'file.after').write_bytes(after)
            assert after == seed, 'denied attempts changed file contents'
            assert rc == (1 if signaled else 0), rc
            data = envelope['data']
            runner = data['runner_result']
            expected = 'runner_failed' if signaled else 'ok'
            assert runner['schema_version'] == 5, runner
            assert runner['normalized_outcome'] == expected, runner
            assert envelope['result']['normalized_outcome'] == expected, envelope['result']
            assert envelope['result']['ok'] is (not signaled), envelope['result']
            assert runner.get('test_overrides') == (overrides if signaled else None), runner
            assert runner['sandboxed_after_apply'] is True, runner
            worker = runner['runner_subprocess']
            assert worker['reaped'] is True and worker.get('termination_request') is None, worker
            assert worker['partial_steps'] is False, worker
            assert worker['done_observed'] is (not signaled), worker
            if signaled:
                assert worker['term_signal'] == 9 and worker.get('exit_code') is None, worker
                assert worker['poll_stop_reason'] == 'child_reaped', worker
                assert 'signal 9' in runner['error'], runner
            else:
                assert worker['exit_code'] == 0 and worker.get('term_signal') is None, worker
            assert [s['step_id'] for s in runner['steps']] == ids, runner['steps']
            for step in runner['steps']:
                assert step['deny_signal'] is None, step
                assert step['sandbox_check']['operation'] == 'file-read-data', step
                assert step['sandbox_check']['outcome'] == 'allow', step
                attempt = step['attempt']
                assert attempt['outcome'] == 'open_failed', attempt
                assert attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
                assert attempt['requested_path'] == str(target), attempt
                assert step['drift'] is None, step  # permission failure is ambiguous against predicted allow
            diag = data['runner_sandbox_diagnostics']
            assert diag['worker_pid'] == worker['pid'], diag
            assert diag['process_disposition'] == ('signaled' if signaled else 'clean_exit'), diag
            assert diag['termination_cause'] == ('unknown' if signaled else None), diag
            capture = data['sandbox_log_capture']
            if not capture_enabled:
                assert capture is None, capture
                assert diag['capture_status'] == 'disabled' and diag['correlation_status'] == 'not_attempted', diag
                assert diag['first_deny'] is None, diag
            else:
                assert isinstance(capture, dict), 'observer must be invoked for both failure and success'
                assert diag['capture_status'] == capture['capture_status'], diag
                window = capture['window']
                assert window['kind'] == 'trailing' and window['last'] == '10s', window
                for key in ('event_timestamps_available', 'exact_run_membership', 'step_ordering', 'pid_reuse_protection'):
                    assert window[key] is False, window
                observer = capture.get('observer')
                if observer is not None:
                    assert observer['data']['pid'] == worker['pid'], observer
                    assert observer['data']['process_name'] == 'pw-probe-runner', observer
                events = capture.get('deny_events')
                if capture['capture_status'] == 'captured' and events is not None:
                    matches = [i for i, event in enumerate(events) if event.get('pid') == worker['pid']]
                    assert diag['correlation_status'] == ('pid_match' if matches else 'no_match'), diag
                    assert diag['first_deny'] == ({'event_index': matches[0]} if matches else None), diag
                    associations = capture['step_denies']
                    assert isinstance(associations, list), capture
                    assert len({a['event_index'] for a in associations}) == len(associations), associations
                    for association in associations:
                        event = events[association['event_index']]
                        assert event['pid'] == worker['pid'], event
                        assert event['operation'] == 'file-write-data', event
                        assert event['path'] == str(target), event
                        assert association['candidate_step_ids'] == ids, association
                        assert association['association'] == 'ambiguous', association
                        assert 'deny_events' not in association, association
                else:
                    assert diag['correlation_status'] == 'unavailable', diag
                    assert diag['first_deny'] is None, diag
            observations.append({'run': name, 'outcome': expected, 'diagnostics': diag})
            (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
            print(f'{name}: disposition and independent denied attempts verified; capture={diag["capture_status"]}', flush=True)


if __name__ == '__main__':
    main()
