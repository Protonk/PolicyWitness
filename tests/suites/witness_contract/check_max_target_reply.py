"""Measured reply-size workloads, including an admitted plan exceeding the cap.

The target admission limit does not bound independent query filters. These
cases exercise long ASCII/escaped paths, observed paths, independent queries,
and exec output; they do not claim a maximum possible serialized reply size.
"""
import errno
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from consumer import validate_current_build_evidence
from run_capture import RunCapture

STEPS = 256
TARGET_BYTES = 511
EXEC_STEPS = STEPS  # The worker raises its soft descriptor limit to fit every exec step.
IDS = [f's{i:03d}' for i in range(STEPS)]


def targets_under(root, *, escaped=False):
    component = ('a"\\\t' * 50) if escaped else ('a' * 200)
    parent = root / component / ('b' * 200)
    parent.mkdir(parents=True)
    leaf_len = TARGET_BYTES - len(str(parent).encode()) - 1
    assert leaf_len > 8, leaf_len
    targets = [parent / (f'{i:03d}-' + 'c' * (leaf_len - 4)) for i in range(STEPS)]
    for target in targets:
        assert len(str(target).encode()) == TARGET_BYTES
        target.write_bytes(b'x')
    return list(map(str, targets))


def specimen(targets, queries, *, denied=False, exec_args=None, large_filter=False):
    steps = []
    for index, (sid, target, query) in enumerate(zip(IDS, targets, queries)):
        attempt = dict(kind='file', action='open_read', target=target)
        if exec_args is not None and index < EXEC_STEPS:
            attempt = dict(kind='exec', action='spawn', target=target, args=exec_args)
        steps.append(dict(step_id=sid, sandbox_check=dict(
            operation='sysctl-read' if large_filter else 'file-read-data',
            filter=dict(kind='sysctl_name' if large_filter else 'path', value=query)), attempt=attempt))
    return dict(schema_version=1, specimen_id=secrets.token_hex(12),
                policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)' +
                            ('(deny file-read-data)' if denied else '')),
                probe_plan=steps)


def check_reply(runner, request, *, denied=False, exec_args=None, large_filter=False):
    assert runner['normalized_outcome'] == 'ok', runner['normalized_outcome']
    assert runner['schema_version'] >= 9
    assert runner.get('admission_failure') is None, runner.get('admission_failure')
    assert [step['step_id'] for step in runner['steps']] == IDS
    errors = validate_current_build_evidence(dict(data=dict(runner_result=runner)))
    assert not errors, errors
    for step, planned in zip(runner['steps'], request['probe_plan']):
        check, attempt = step['sandbox_check'], step['attempt']
        target = planned['attempt']['target']
        query = planned['sandbox_check']['filter']['value']
        assert check['filter_value'] == query and 'effective_filter_value' not in check
        if not large_filter:
            assert check['path_diagnostics']['input'] == query
        assert attempt['requested_path'] == target
        if denied:
            assert check['outcome'] == 'deny'
            assert attempt['outcome'] == 'open_failed' and attempt['errno'] in (errno.EPERM, errno.EACCES)
        else:
            assert check['outcome'] == ('prediction_unavailable' if large_filter else 'allow')
            assert attempt['outcome'] == 'ok' and attempt['rc'] == 0, attempt
            if planned['attempt']['kind'] != 'exec':
                # Independent native observation: these are existing canonical files.
                assert attempt['observed_path'] == str(Path(target).resolve()), attempt
            else:
                assert attempt['child_exit_code'] == 0
                assert attempt['stdout'] == 'A' * 1023
                assert attempt['stderr'] == exec_args[-1] + '\n'


def run_case(pw, out, name, request, *, overflow=False, capture_logs=False, **expectations):
    run = RunCapture(pw, out / name, request,
                     cli_args=['--timeout-ms', '120000'] + ([] if capture_logs else ['--no-log-capture']))
    with run:
        rc = run.wait(timeout=150)
        envelope = run.load_json()
    data, result = envelope['data'], envelope['result']
    client = data['runner_client']
    assert client['stdout_parse_error'] is None, client['stdout_parse_error']
    assert client['capture_limit_bytes'] == 8 * 1024 * 1024
    observation = dict(case=name, steps=STEPS, target_bytes=TARGET_BYTES,
                       runner_reply_bytes=client['stdout_bytes_received'],
                       capture_limit_bytes=client['capture_limit_bytes'],
                       envelope_bytes=run.stdout_path.stat().st_size)
    if overflow:
        assert rc == 1 and result['normalized_outcome'] == 'runner_output_not_json', result
        assert data['runner_result'] is None
        assert client['stdout_truncated'] is True and client['stdout_capture_error']
        assert client['stdout_bytes_received'] > client['capture_limit_bytes']
        assert client['stdout_bytes_retained'] == client['capture_limit_bytes']
        # Bypass only the controller receiver to prove this admitted read-only
        # specimen has a complete, valid runner reply. Keep both artifacts.
        raw_path = run.out / 'raw-client.json'
        with raw_path.open('wb') as stream, (run.out / 'raw-client.stderr').open('wb') as errors:
            raw = subprocess.run(client['argv'], stdout=stream, stderr=errors, timeout=150)
        assert raw.returncode == 0, raw.returncode
        assert raw_path.stat().st_size > client['capture_limit_bytes']
        check_reply(json.loads(raw_path.read_text()), request, **expectations)
        observation.update(expected_receiver_loss=True, raw_reply_bytes=raw_path.stat().st_size)
    else:
        assert rc == 0, result
        assert client['stdout_truncated'] is False and client['stdout_capture_error'] is None
        assert client['stdout_bytes_received'] == client['stdout_bytes_retained'] <= client['capture_limit_bytes']
        check_reply(data['runner_result'], request, **expectations)
        if capture_logs:
            capture = data['sandbox_log_capture']
            assert isinstance(capture, dict), 'known worker PID must request capture'
            assert capture['capture_status'] != 'capture_error'
            assert capture.get('stdout_truncated') is not True
            observation.update(observer_reply_bytes=capture.get('stdout_bytes_received'),
                               observer_capture_status=capture['capture_status'])
    print(f"{name}: {client['stdout_bytes_received']} reply bytes; expected overflow={overflow}", flush=True)
    return observation


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory)
    observations = []
    with tempfile.TemporaryDirectory(prefix='pw-max-', dir='/private/tmp') as work:
        root = Path(work)
        plain = targets_under(root / 'plain')
        escaped = targets_under(root / 'escaped', escaped=True)
        observations.append(run_case(pw, out, 'denied_ascii', specimen(plain, plain, denied=True),
                                     denied=True, capture_logs=True))
        observations.append(run_case(pw, out, 'allowed_escaped', specimen(escaped, escaped)))
        observations.append(run_case(pw, out, 'independent_query', specimen(plain, ['/etc/hosts'] * STEPS)))
        # The existing fixture has direct output/exit controls in exec_fixture.
        repo = Path(__file__).resolve().parents[3]
        helper = root / 'exec-fixture'
        subprocess.run(['bash', str(repo / 'tests/fixtures/exec/build.sh'), str(helper)], check=True)
        executable = Path(plain[0])
        shutil.copy2(helper, executable)
        exec_targets = [str(executable)] * STEPS
        args = ['--stdout-bytes', '1023', '--stderr', '"\\\t' * 40]
        observation = run_case(pw, out, 'exec_output', specimen(exec_targets, exec_targets, exec_args=args),
                               exec_args=args)
        observation['exec_steps'] = EXEC_STEPS
        observations.append(observation)
        queries = ['q' * 32768] * STEPS
        observations.append(run_case(pw, out, 'admitted_over_cap', specimen(plain, queries, large_filter=True),
                                     overflow=True, large_filter=True))
    (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')


if __name__ == '__main__':
    main()
