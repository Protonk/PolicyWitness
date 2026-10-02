"""Real denied attempts, unrelated self-signal, and capture on failure/success.

Captured kernel events are optional: deterministic Rust controls cover their
association independently of live availability. Required tool access and valid
collection/cleanup facts remain mandatory. Documented budget exhaustion is
unavailable evidence, never positive correlation coverage.
"""
import errno
import json
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
import consumer
from log_capture_contract import check_live_capture

# The target is a real path under /private/tmp, so the host's after-orchestration
# forms equal the submitted target and are admitted beside it, by name.
PATH_SOURCES = {'submitted_attempt.target', 'attempt.requested_path',
                'runner_host.after_orchestration.realpath_resolved',
                'runner_host.after_orchestration.parent_realpath_resolved'}


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
            args = ['--timeout-ms', '20000']
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
            assert 'log_last' not in data, data.keys()
            runner = data['runner_result']
            expected = 'runner_failed' if signaled else 'ok'
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
                assert step['sandbox_check']['operation'] == 'file-read-data', step
                assert step['sandbox_check']['outcome'] == 'allow', step
                attempt = step['attempt']
                assert attempt['outcome'] == 'open_failed', attempt
                assert attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
                assert attempt['requested_path'] == str(target), attempt
            diag = data['runner_sandbox_diagnostics']
            assert diag['process_disposition'] == ('signaled' if signaled else 'clean_exit'), diag
            # The self-signal was not a host cleanup: the record projects no cause.
            assert diag['termination_cause'] == ('unknown' if signaled else None), diag
            capture = data['sandbox_log_capture']
            assert not consumer.validate(envelope), consumer.validate(envelope)
            rows = consumer.steps(envelope)
            # Permission failures by errno against a different query operation.
            failed = consumer.select(rows, observation='permission_failure', observation_basis='permission_errno',
                                     operation_relation='different', target_relation='same_submitted')
            assert [s['step_id'] for s in failed] == ids, rows
            recovered = consumer.denials(envelope)
            (run.out / 'consumer-denials.json').write_text(json.dumps(recovered, indent=2) + '\n')
            assert recovered['correlation_status'] == diag['correlation_status']
            assert recovered['diagnostics']['termination_cause'] == ('unknown' if signaled else None)
            live_result = {'outcome': 'disabled'}
            if not capture_enabled:
                assert recovered['capture_status'] == 'not_reported'
                assert recovered['association_reporting'] == 'not_reported'
                assert recovered['candidates'] is None
                assert capture is None, capture
                assert diag['correlation_status'] == 'not_attempted', diag
                assert diag['permission_failures_without_record'] is None, diag
            else:
                live_result = check_live_capture(envelope)
                assert isinstance(capture, dict), 'observer must be invoked for both failure and success'
                assert recovered['capture_status'] == capture['capture_status']
                window = capture['window']
                assert recovered['window'] == window
                client = data['runner_client']
                assert window['kind'] == 'runner_client_span' and 'last' not in window, window
                assert window['started_at_unix_ms'] == client['started_at_unix_ms'], (window, client)
                assert window['ended_at_unix_ms'] == client['ended_at_unix_ms'], (window, client)
                assert window['start'] < window['end'], window
                observer = capture.get('observer')
                if observer is not None:
                    assert observer['data']['pid'] == worker['pid'], observer
                    assert observer['data']['process_name'] == 'pw-probe-runner', observer
                    assert observer['data']['last'] is None, observer
                    assert (observer['data']['start'], observer['data']['end']) == (window['start'], window['end']), observer
                events = capture.get('deny_events')
                if capture['capture_status'] == 'captured' and events is not None:
                    matches = [i for i, event in enumerate(events) if event.get('pid') == worker['pid']]
                    assert diag['correlation_status'] == ('pid_match' if matches else 'no_match'), diag
                    # Both denied writes are permission failures by the runner's own account;
                    # the ones no captured event names stay listed beside the status.
                    assert diag['permission_failures_without_record'] == ([] if matches else ids), diag
                    associations = capture['step_denies']
                    assert recovered['events'] == events
                    assert recovered['association_reporting'] == 'reported'
                    assert len(recovered['candidates']) == len(associations)
                    for candidate in recovered['candidates']:
                        assert candidate['event'] == events[candidate['event_index']]
                        assert candidate['candidate_step_ids'] == ids
                        assert candidate['association'] == 'ambiguous'
                        assert len(candidate['matching_evidence']) == 2
                        for match in candidate['matching_evidence']:
                            assert match['operation'] == 'file-write-data'
                            assert match['operation_source'] == 'submitted_attempt'
                            assert match['requested_kind'] == 'file' and match['requested_action'] == 'open_write'
                            assert match['path'] == str(target)
                            assert set(match['path_sources']) == PATH_SOURCES, match
                    assert isinstance(associations, list), capture
                    assert len({a['event_index'] for a in associations}) == len(associations), associations
                    for association in associations:
                        event = events[association['event_index']]
                        assert event['pid'] == worker['pid'], event
                        assert event['operation'] == 'file-write-data', event
                        assert event['path'] == str(target), event
                        assert association['candidate_step_ids'] == ids, association
                        assert association['association'] == 'ambiguous', association
                        evidence = association['matching_evidence']
                        assert [item['step_id'] for item in evidence] == ids, evidence
                        for item in evidence:
                            assert item['operation'] == event['operation'], item
                            assert item['operation_source'] == 'submitted_attempt', item
                            assert (item['requested_kind'], item['requested_action']) == ('file', 'open_write'), item
                            assert item['path'] == str(target), item
                            assert set(item['path_sources']) == PATH_SOURCES, item
                        assert 'deny_events' not in association, association
                else:
                    assert diag['correlation_status'] == 'unavailable', diag
                    assert diag['permission_failures_without_record'] is None, diag
            observations.append({'run': name, 'outcome': expected, 'diagnostics': diag, 'live_result': live_result})
            (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
            print(f'{name}: disposition and independent denied attempts verified; capture={recovered["capture_status"]}', flush=True)


if __name__ == '__main__':
    main()
