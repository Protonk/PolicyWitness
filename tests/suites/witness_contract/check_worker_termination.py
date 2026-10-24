"""Independent failed attempts, unrelated self-signal and worker disposal."""
import errno
import json
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
import consumer

def main():
    pw, directory = sys.argv[1:]
    out = Path(directory)
    observations = []
    with tempfile.TemporaryDirectory(prefix='pw-termination-', dir='/private/tmp') as work:
        target = Path(work) / secrets.token_hex(12)
        seed = secrets.token_bytes(64)
        target.write_bytes(seed)
        ids = [secrets.token_hex(8), secrets.token_hex(8)]
        base = {
            'schema_version': 5, 'specimen_id': secrets.token_hex(12),
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'
                       '(deny file-write-data (literal (param "BLOCKED")))',
                       'params': {'BLOCKED': str(target)}},
            # Query operation intentionally differs from the attempted operation.
            'probe_plan': [{'step_id': step_id,
                           'sandbox_check': {'operation': 'file-read-data',
                                             'filter': {'kind': 'path', 'value': str(target)}},
                           'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}
                          for step_id in ids],
        }
        overrides = {'worker_post_apply_kill_signal': 9, 'worker_post_apply_hang_ms': 1500}
        for name, signaled, phased in [
                ('signal', True, False), ('success', False, False),
                ('phases_signal', True, True), ('phases_success', False, True)]:
            specimen = dict(base)
            if phased:
                specimen['phases'] = [
                    {'phase_id': f'phase{i}', 'actions': [entry]}
                    for i, entry in enumerate(specimen.pop('probe_plan'))]
            if signaled:
                specimen['_test_overrides'] = overrides
            args = ['--timeout-ms', '20000']
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
            if phased:
                assert [s['phase_id'] for s in runner['steps']] == ['phase0', 'phase1']
                assert [p['phase_id'] for p in runner['phases']] == ['phase0', 'phase1']
                for phase, identity in zip(runner['phases'], ids):
                    assert phase['arrival_observed'] and phase['completion_observed']
                    assert phase['action_ids'] == [identity]
                    assert phase['validator_subprocess']['expected_step_ids'] == [identity]
                    assert all(phase['ordering'][k] for k in (
                        'collection_closed_before_proceed', 'proceed_set', 'proceed_observed'))
                assert all(s['comparison']['order'] == 'query_first' for s in runner['steps'])
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
            assert not consumer.validate(envelope), consumer.validate(envelope)
            rows = consumer.steps(envelope)
            # Permission failures by errno against a different query operation.
            failed = consumer.select(rows, observation='permission_failure', observation_basis='permission_errno',
                                     operation_relation='different', target_relation='same_submitted')
            assert [s['step_id'] for s in failed] == ids, rows
            observations.append({'run': name, 'outcome': expected, 'diagnostics': diag})
            (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
            print(f'{name}: disposition and independent failed attempts verified', flush=True)


if __name__ == '__main__':
    main()
