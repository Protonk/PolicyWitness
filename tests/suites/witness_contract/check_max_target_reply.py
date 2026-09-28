"""Measured reply-size workloads at the admitted maxima, plus refused over-cap plans.

Attempt targets and independent query filter values have separate admission
limits. These cases exercise long ASCII/escaped paths, observed paths,
maximal independent query paths and exec output, and require 32,768-byte
query values and filter/attempt labels to be refused before any process work.
They measure reply sizes;
they do not claim a maximum possible serialized reply size.
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
QUERY_FILTER_BYTES = 511   # query_filter_value in docs/LIMITS.md; equal to the target limit
OVER_CAP_QUERY_BYTES = 32768
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


def check_refused(runner, *, field='sandbox_check.filter.value', maximum=QUERY_FILTER_BYTES, step_index=0):
    # Host-owned admission record; nothing ran and nothing is echoed. A refusal
    # that echoed 256 x 32 KiB filters would outgrow the reply cap by itself.
    assert runner['normalized_outcome'] == 'bad_request', runner['normalized_outcome']
    failure = runner['admission_failure']
    assert failure['origin'] == 'runner_host', failure
    assert failure['field'] == field, failure
    assert (failure['actual'], failure['maximum'], failure['unit']) == (OVER_CAP_QUERY_BYTES, maximum, 'utf8_bytes'), failure
    assert failure['step_id'] == IDS[step_index], failure
    assert runner.get('runner_subprocess') is None and runner.get('validator_subprocess') is None, runner
    assert runner['steps'] == [], runner
    errors = validate_current_build_evidence(dict(data=dict(runner_result=runner)))
    assert not errors, errors


def run_case(pw, out, name, request, *, refused=False, capture_logs=False, **expectations):
    run = RunCapture(pw, out / name, request,
                     cli_args=['--timeout-ms', '120000'] + ([] if capture_logs else ['--no-log-capture']))
    with run:
        rc = run.wait(timeout=150)
        envelope = run.load_json()
    data, result = envelope['data'], envelope['result']
    client = data['runner_client']
    # Both the admitted workloads and the refusals must survive the receiver cap.
    assert client['stdout_parse_error'] is None, client['stdout_parse_error']
    assert client['capture_limit_bytes'] == 8 * 1024 * 1024
    assert client['stdout_truncated'] is False and client['stdout_capture_error'] is None
    assert client['stdout_bytes_received'] == client['stdout_bytes_retained'] <= client['capture_limit_bytes']
    observation = dict(case=name, steps=STEPS, target_bytes=TARGET_BYTES,
                       runner_reply_bytes=client['stdout_bytes_received'],
                       capture_limit_bytes=client['capture_limit_bytes'],
                       envelope_bytes=run.stdout_path.stat().st_size)
    if refused:
        assert rc == 1 and result['normalized_outcome'] == 'bad_request', result
        check_refused(data['runner_result'], **expectations)
        assert client['stdout_bytes_received'] < 4096
        observation.update(refused_at_admission=True, query_bytes=OVER_CAP_QUERY_BYTES)
    else:
        assert rc == 0, result
        check_reply(data['runner_result'], request, **expectations)
        if capture_logs:
            capture = data['sandbox_log_capture']
            assert isinstance(capture, dict), 'known worker PID must request capture'
            assert capture['capture_status'] != 'capture_error'
            assert capture.get('stdout_truncated') is not True
            observation.update(observer_reply_bytes=capture.get('stdout_bytes_received'),
                               observer_capture_status=capture['capture_status'])
    print(f"{name}: {client['stdout_bytes_received']} reply bytes; refused at admission={refused}", flush=True)
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
        # Maximal admitted independent queries: every 511-byte escaped path is an
        # existing file, so predictions resolve, while the attempts read the plain set.
        assert all(len(query.encode()) == QUERY_FILTER_BYTES for query in escaped)
        observations.append(run_case(pw, out, 'independent_query', specimen(plain, escaped)))
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
        # Echoing 256 x 32 KiB filters would exceed the controller cap.
        queries = ['q' * OVER_CAP_QUERY_BYTES] * STEPS
        observations.append(run_case(pw, out, 'refused_over_cap_query', specimen(plain, queries, large_filter=True),
                                     refused=True))
        # Keep a valid write as the first step: a later invalid label must reject
        # the entire plan. Independent file contents prove no earlier attempt ran.
        for target in plain:
            Path(target).write_bytes(b'before')
        for field in ['sandbox_check.filter.kind', 'attempt.kind', 'attempt.action']:
            request = specimen(plain, plain)
            for index, step in enumerate(request['probe_plan']):
                step['attempt']['action'] = 'open_write'
                if index:
                    obj = step
                    parts = field.split('.')
                    for part in parts[:-1]:
                        obj = obj[part]
                    obj[parts[-1]] = 'x' * OVER_CAP_QUERY_BYTES
            observations.append(run_case(pw, out, 'refused_' + field.replace('.', '_'), request,
                                         refused=True, field=field, maximum=127, step_index=1))
            assert all(Path(target).read_bytes() == b'before' for target in plain), 'attempt ran despite refusal'
    (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')


if __name__ == '__main__':
    main()
