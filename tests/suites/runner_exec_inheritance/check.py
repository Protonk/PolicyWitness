"""Observe exec inheritance through the CLI and a deliberately contaminated worker."""
import fcntl
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures' / 'exec'))
from inspection import ENV_KEY, parse_report, assert_clean


def run_cli(pw, helper, out):
    nonce = secrets.token_hex(16)
    canary_fd = 200
    plan = [{
        'step_id': f'inspect_{i}',
        'sandbox_check': {'operation': 'process-exec*',
                          'filter': {'kind': 'path', 'value': helper}},
        'attempt': {'kind': 'exec', 'action': 'spawn', 'target': helper,
                    'args': ['--inspect', f'{nonce}-{i}', '--read-fd', str(canary_fd)]},
    } for i in range(3)]
    specimen = {'schema_version': 1, 'specimen_id': 'exec_inheritance',
                'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
                'probe_plan': plan}
    request = out / 'specimen.json'
    request.write_text(json.dumps(specimen, indent=2) + '\n')
    with (out / 'run.json').open('wb') as stdout, (out / 'pw.stderr').open('wb') as stderr:
        run = subprocess.run([pw, 'run', str(request), '--no-log-capture', '--timeout-ms', '15000'],
                             stdout=stdout, stderr=stderr, timeout=20)
    assert run.returncode == 0, f'CLI exited {run.returncode}'
    envelope = json.loads((out / 'run.json').read_text())
    runner = envelope['data']['runner_result']
    assert envelope['result']['ok'] is True and runner['normalized_outcome'] == 'ok', runner
    assert runner.get('test_overrides') is None, runner
    assert [s['step_id'] for s in runner['steps']] == [s['step_id'] for s in plan], runner
    observations = []
    for i, step in enumerate(runner['steps']):
        attempt = step['attempt']
        assert attempt['outcome'] == 'ok' and attempt['rc'] == 0, attempt
        assert attempt['child_exit_code'] == 0 and attempt['child_term_signal'] == 0, attempt
        assert step['sandbox_check']['outcome'] == 'allow' and step['drift'] is None, step
        assert attempt['stderr'] == f'inspect:{nonce}-{i}\n', attempt
        report = parse_report(attempt['stdout'], f'{nonce}-{i}', canary_fd)
        assert report['pid'] == attempt['child_pid'], (report, attempt)
        observations.append(report)
    (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    for report in observations:
        assert_clean(report)
    assert len({r['pid'] for r in observations}) == 3, 'exec steps must be separate invocations'
    print('CLI: three exec children report empty environments, isolated descriptors, and stdin EOF')


def run_worker(worker, helper, harness, out):
    nonce = secrets.token_hex(16)
    with tempfile.TemporaryFile() as resource:
        canary = secrets.token_bytes(32)
        resource.write(canary)
        resource.flush()
        high_fd = fcntl.fcntl(resource.fileno(), fcntl.F_DUPFD, 200)
        try:
            with (out / 'harness.jsonl').open('wb') as stdout, (out / 'harness.stderr').open('wb') as stderr:
                run = subprocess.run([harness, worker, 'exec_inheritance', helper, nonce, str(high_fd)],
                                     env={ENV_KEY: nonce}, pass_fds=(high_fd,),
                                     stdout=stdout, stderr=stderr, timeout=20)
        finally:
            os.close(high_fd)
    assert run.returncode == 0, f'worker harness exited {run.returncode}'
    launch_raw, result_raw = (out / 'harness.jsonl').read_text().splitlines()
    launch = parse_report(launch_raw, nonce, high_fd)
    result = json.loads(result_raw)
    assert launch['pid'] == result['worker_pid'], 'launch inspection must precede exec in the same PID'
    assert launch['env_count'] == 1 and launch['env_value'] == nonce, launch
    assert high_fd in [fd for fd, _ in launch['fds']], launch
    assert launch['canary_rc'] == 32 and launch['canary_errno'] == 0, launch
    assert launch['canary_hex'] == canary.hex(), 'worker was not supplied the test-owned resource'
    assert launch['stdin_skipped'] is True, 'launch observer must preserve the policy pipe'
    assert result['ready_byte_received'] and result['applied'] and result['done'], result
    assert result['apply_rc'] == 0 and result['exit_code'] == 0, result
    assert result['term_signal'] is None and result['sent_sigkill'] is False, result
    assert [s['step_id'] for s in result['slots']] == [f'inspect_{i}' for i in range(3)], result
    observations = []
    for i, slot in enumerate(result['slots']):
        assert slot['completed'] == 1 and slot['rc'] == 0, slot
        assert slot['child_exit_code'] == 0 and slot['child_term_signal'] == 0, slot
        assert slot['stderr'] == f'inspect:{nonce}-{i}\n', slot
        report = parse_report(slot['stdout'], f'{nonce}-{i}', high_fd)
        assert report['pid'] == slot['child_pid'], (report, slot)
        observations.append(report)
    (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    for report in observations:
        assert_clean(report)
    print('worker: launch-state contamination verified; all three exec children received a clean state')
    return observations


if __name__ == '__main__':
    mode, out_arg, *args = sys.argv[1:]
    out = Path(out_arg)
    if mode == 'cli':
        run_cli(*args, out)
    elif mode == 'worker':
        run_worker(*args, out)
    else:
        raise SystemExit(f'unknown mode: {mode}')
