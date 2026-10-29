"""Measured reply-size workloads at the admitted maxima, plus refused over-cap plans.

Attempt targets and independent query filter values have separate admission
limits. These cases exercise long ASCII/escaped paths, observed paths,
maximal independent query paths, exec output and the worst admitted JSON
escaping (control characters in every query path and child stream), and
require 32,768-byte query values and filter/attempt labels to be refused
before any process work. They measure reply sizes against the synthesized
maximal reply recorded in docs/limits.json, from which the receiver budget is
derived; the corpus is evidence that real replies stay inside that bound.
"""
import errno
import copy
import json
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
from run_capture import RunCapture

SESSION = None

def documented_limit(ident):
    manifest = json.loads((Path(__file__).resolve().parents[3] / 'docs/limits.json').read_text())
    return next(row['value'] for row in manifest['limits'] if row['id'] == ident)


STEPS = 256
TARGET_BYTES = 511
QUERY_FILTER_BYTES = 511   # query_filter_value in docs/LIMITS.md; equal to the target limit
OVER_CAP_QUERY_BYTES = 32768
EXEC_STEPS = STEPS  # The worker raises its soft descriptor limit to fit every exec step.
IDS = [f's{i:03d}' for i in range(STEPS)]


def targets_under(root, *, escaped=False, control=False):
    # escaped: quote, backslash and tab (short JSON escapes, about 1.5x).
    # control: U+0001, which every JSON encoder escapes as six bytes (6x).
    component = ('\x01' * 200) if control else ('a"\\\t' * 50) if escaped else ('a' * 200)
    parent = root / component / (('\x01' if control else 'b') * 200)
    parent.mkdir(parents=True)
    leaf_len = TARGET_BYTES - len(str(parent).encode()) - 1
    assert leaf_len > 8, leaf_len
    targets = [parent / (f'{i:03d}-' + ('\x01' if control else 'c') * (leaf_len - 4)) for i in range(STEPS)]
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
    return dict(schema_version=5, specimen_id=secrets.token_hex(12),
                policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)' +
                            ('(deny file-read-data)' if denied else '')),
                probe_plan=steps)


def request_steps(request):
    return request.get('probe_plan', [step for phase in request.get('phases', []) for step in phase['actions'] if 'attempt' in step])


def check_reply(runner, request, *, denied=False, exec_args=None, large_filter=False, exec_output=None):
    assert runner['normalized_outcome'] == 'ok', runner['normalized_outcome']
    assert runner.get('admission_failure') is None, runner.get('admission_failure')
    assert [step['step_id'] for step in runner['steps']] == [step['step_id'] for step in request_steps(request)]
    errors = consumer.validate(runner)
    assert not errors, errors
    if 'phases' in request:
        assert len(runner['phases']) == 8
        for phase, planned in zip(runner['phases'], request['phases']):
            ordinary = [action for action in planned['actions'] if 'attempt' in action]
            assert phase['arrival_observed'] and phase['completion_observed']
            assert len(phase['validator_subprocess']['records']) == len(ordinary)
        assert all(step['comparison']['order'] == 'query_first' for step in runner['steps'])
    for step, planned in zip(runner['steps'], request_steps(request)):
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
            if planned['attempt']['action'] == 'read_fresh':
                read = attempt['fresh_read']
                independent = Path(target).read_bytes()
                metadata = Path(target).stat()
                assert read['open_rc'] >= 0 and read['stat_rc'] == 0 and read['close_rc'] == 0, read
                assert read['read_rc'] == min(64, len(independent))
                assert bytes.fromhex(read['content_hex']) == independent[:64]
                assert (read['identity']['device'], read['identity']['inode']) == (metadata.st_dev, metadata.st_ino)
            elif planned['attempt']['action'] == 'write_fresh':
                write = attempt['fresh_write']
                independent = Path(target).read_bytes()
                metadata = Path(target).stat()
                assert write['open_rc'] >= 0 and write['truncate_rc'] == 0 and write['write_rc'] == 1 and write['close_rc'] == 0
                assert write['truncated_stat']['size'] == 0 and write['written_stat']['size'] == 1
                assert independent == b'x'
                assert (write['written_stat']['identity']['device'], write['written_stat']['identity']['inode']) == (metadata.st_dev, metadata.st_ino)
            elif planned['attempt']['kind'] != 'exec':
                # Independent native observation: these are existing canonical files.
                assert attempt['observed_path'] == str(Path(target).resolve()), attempt
            else:
                assert attempt['child_exit_code'] == 0
                stdout, stderr = exec_output or ('A' * 1023, exec_args[-1] + '\n')
                assert attempt['stdout'] == stdout
                assert attempt['stderr'] == stderr
    if request.get('extensions'):
        declaration, = runner['extensions']
        assert declaration['issuance_status'] == 'issued' and declaration['delivery_status'] == 'delivered'
        consume, release = runner['extension_events']
        assert consume['status'] == release['status'] == 'returned'
        assert consume['native_result'] != -1 and release['native_result'] == 0
        assert consume['handle_ref'] == release['handle_ref']


def check_refused(runner, *, field='sandbox_check.filter.value', maximum=QUERY_FILTER_BYTES, step_index=0):
    # Host-owned admission record; nothing ran and nothing is echoed. A refusal
    # that echoed 256 x 32 KiB filters would outgrow the reply cap by itself.
    assert runner['normalized_outcome'] == 'bad_request', runner['normalized_outcome']
    failure = runner['admission_failure']
    assert failure['origin'] == 'runner_host', failure
    assert failure['field'] == field, failure
    assert (failure['actual'], failure['maximum'], failure['unit']) == (OVER_CAP_QUERY_BYTES, maximum, 'utf8_bytes'), failure
    assert failure['step_id'] == IDS[step_index], failure
    assert runner.get('runner_subprocess') is None and (runner.get('phases') or [{}])[0].get('validator_subprocess') is None, runner
    assert runner['steps'] == [], runner
    errors = consumer.validate(runner)
    assert not errors, errors


def host_handoff(directory):
    """Start size-limit workloads after the preceding host has retired.

    Large replies take time to decode, so the next request can race the previous
    host's exit without receiving an already_ran reply. Contention is exercised
    separately; this test needs a reply from the host that checks its limits.
    Failed launchctl/process observations never establish retirement.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures/byoxpc'))
    from neighbor_lab import executable_path, generation, generation_state, process_identity, save, wait_for
    receipt = {}
    try:
        result = subprocess.run(['/bin/launchctl', 'print', SESSION['target']],
                                capture_output=True, text=True, timeout=10)
        receipt['launchd'] = dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        assert result.returncode == 0, receipt
        match = re.search(r'^\s*pid = (\d+)\s*$', result.stdout, re.M)
        if match is None:
            receipt['outcome'] = 'launchd_reports_no_pid'
            return
        pid = int(match[1])
        identity = process_identity(pid)
        receipt['identity'] = identity
        if not identity['observed']:
            assert identity['absent'], ('unknown host observation', receipt)
            receipt['outcome'] = 'esrch_before_identity'
            return
        key = generation(identity)
        path = executable_path(pid)
        receipt['executable_path'] = path
        state = generation_state(key)
        if state != 'gone':
            assert state == 'alive', ('unknown host observation', receipt)
            assert path == str(Path(SESSION['bundle_path']) / 'Contents/MacOS/PWRunner'), receipt

            def retired():
                state = generation_state(key)
                assert state != 'unknown', ('unknown host observation', receipt)
                return state == 'gone'

            wait_for(retired, 'size-limit host handoff', timeout=10)
        receipt['outcome'] = 'generation_gone'
    finally:
        save(directory / 'host-handoff.json', receipt)


def run_case(pw, out, name, request, *, refused=False, measure_margin=False, **expectations):
    if SESSION:
        request['runner'] = dict(mode='byoxpc', service=SESSION['service_name'])
        (out / name).mkdir(parents=True, exist_ok=True)
        host_handoff(out / name)
    run = RunCapture(pw, out / name, request,
                     cli_args=['--timeout-ms', '120000'])
    with run:
        rc = run.wait(timeout=150)
        envelope = run.load_json()
    data, result = envelope['data'], envelope['result']
    client = data['runner_client']
    # Both the admitted workloads and the refusals must survive the receiver cap.
    assert client['stdout_parse_error'] is None, client['stdout_parse_error']
    # The budget is derived from the synthesized maximal reply; both come from the
    # manifest here, and the relation is asserted independently of either number.
    maximum, budget = documented_limit('runner_reply_maximum'), documented_limit('controller_output')
    assert client['capture_limit_bytes'] == budget, client['capture_limit_bytes']
    assert 3 * maximum <= budget < 3 * maximum + 4 * 1024 * 1024 and budget % (4 * 1024 * 1024) == 0, (maximum, budget)
    assert client['stdout_truncated'] is False and client['stdout_capture_error'] is None
    assert client['stdout_bytes_received'] == client['stdout_bytes_retained'] <= client['capture_limit_bytes']
    observation = dict(case=name, steps=len(request_steps(request)), target_bytes=TARGET_BYTES,
                       extension_events=len(data['runner_result'].get('extension_events') or []),
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
        # Every admitted workload stays under the synthesized maximum, which is
        # the bound the budget is derived from; the measured ratio is evidence.
        assert client['stdout_bytes_received'] <= maximum, (client['stdout_bytes_received'], maximum)
        observation.update(synthesized_maximum_bytes=maximum,
                           fraction_of_maximum=round(client['stdout_bytes_received'] / maximum, 4))
        if measure_margin:
            # Live capture must be present in the maximal-metadata workload; the
            # conservative receipt allowance (base64 with every slash escaped plus
            # metadata) is recorded beside it. The capture size is the manifest's.
            capture_bytes = documented_limit('compiled_profile')
            profile_allowance = 2 * 4 * ((capture_bytes + 2) // 3) + 4096
            capture = data['runner_result']['compiled_profile']
            assert capture['status'] == 'captured' and capture['bytecode_length'] > 0, capture
            assert client['stdout_bytes_received'] + profile_allowance <= maximum, 'reply plus a maximal receipt exceeds the synthesized maximum'
            observation.update(profile_allowance_bytes=profile_allowance,
                               budget_over_reply=round(client['capture_limit_bytes'] / client['stdout_bytes_received'], 3))
    print(f"{name}: {client['stdout_bytes_received']} reply bytes; refused at admission={refused}", flush=True)
    return observation


def main():
    global SESSION
    pw, directory = sys.argv[1:3]
    if len(sys.argv) == 4:
        SESSION = json.loads(Path(sys.argv[3]).read_text())
    out = Path(directory)
    observations = []
    with tempfile.TemporaryDirectory(prefix='pw-max-', dir='/private/tmp') as work:
        root = Path(work)
        plain = targets_under(root / 'plain')
        escaped = targets_under(root / 'escaped', escaped=True)
        observations.append(run_case(pw, out, 'denied_ascii', specimen(plain, plain, denied=True),
                                     denied=True))
        observations.append(run_case(pw, out, 'allowed_escaped', specimen(escaped, escaped)))
        # Maximal admitted independent queries: every 511-byte escaped path is an
        # existing file, so predictions resolve, while the attempts read the plain set.
        assert all(len(query.encode()) == QUERY_FILTER_BYTES for query in escaped)
        observations.append(run_case(pw, out, 'independent_query', specimen(plain, escaped)))
        phased = specimen(plain, escaped)
        actions = phased.pop('probe_plan')
        phased['phases'] = [dict(phase_id='p' + str(i), actions=actions[i * 32:(i + 1) * 32]) for i in range(8)]
        observations.append(run_case(pw, out, 'eight_phase_maximum', phased))
        assert all(Path(target).read_bytes() == b'x' for target in plain + escaped)

        # Fresh descriptor/content evidence at the aggregate action maximum,
        # with and without two native lifecycle actions sharing those 256 slots.
        payload = bytes(range(65))
        for target in plain:
            Path(target).write_bytes(payload)
        fresh = copy.deepcopy(phased)
        for action in request_steps(fresh):
            action['attempt']['action'] = 'read_fresh'
        observations.append(run_case(pw, out, 'fresh_read_maximum', fresh))
        mixed = copy.deepcopy(fresh)
        mixed['extensions'] = [dict(token_ref='token', target=plain[0])]
        mixed['phases'][0]['actions'][0] = dict(step_id='consume', extension=dict(
            operation='consume', token_ref='token', handle_ref='handle'))
        mixed['phases'][-1]['actions'][-1] = dict(step_id='release', extension=dict(
            operation='release', handle_ref='handle'))
        observations.append(run_case(pw, out, 'extension_action_maximum', mixed))
        assert all(Path(target).read_bytes() == payload for target in plain)

        writes = copy.deepcopy(phased)
        for action in request_steps(writes):
            action['attempt']['action'] = 'write_fresh'
            action['sandbox_check']['operation'] = 'file-write-data'
        observations.append(run_case(pw, out, 'fresh_write_maximum', writes))
        write_mixed = copy.deepcopy(writes)
        write_mixed['extensions'] = [dict(token_ref='token', target=str(Path(plain[0]).parent), authority='read_write')]
        write_mixed['phases'][0]['actions'][0] = dict(step_id='consume', extension=dict(
            operation='consume', token_ref='token', handle_ref='handle'))
        write_mixed['phases'][-1]['actions'][-1] = dict(step_id='release', extension=dict(
            operation='release', handle_ref='handle'))
        observations.append(run_case(pw, out, 'write_extension_action_maximum', write_mixed))
        assert all(Path(target).read_bytes() == b'x' for target in plain)

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
        # Worst admitted escaping: 511-byte independent query paths and 1,023-byte
        # child streams made of U+0001, six bytes each once serialized, on every
        # step. Predictions must round-trip through the validator, and the
        # complete reply must fit the receiver with the documented margin.
        control = targets_under(root / 'control', control=True)
        assert all(len(query.encode()) == QUERY_FILTER_BYTES for query in control)
        # Use a maximal escaped exec target as well as independent query paths.
        stream_helper = Path(control[0])
        subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
                        '-std=c11', str(repo / 'tests/fixtures/exec/streams.c'), '-o', str(stream_helper)], check=True)
        # Check the equipment independently before relying on PW's observations.
        for byte in [0, 1, 34, 92, 255]:
            direct = subprocess.run([str(stream_helper), '1023', '17', str(byte)], capture_output=True, timeout=5, check=True)
            assert direct.stdout == bytes([byte]) * 1023 and direct.stderr == bytes([byte]) * 17
        stream_args = ['1023', '1023', '1']
        request = specimen([str(stream_helper)] * STEPS, control, exec_args=stream_args)
        request['specimen_id'] = '\x01' * 255
        request['run_kind'] = '\x01' * 63
        request['policy'].update(capture_compiled_profile=True, capture_nonce=secrets.token_hex(16))
        for index, step in enumerate(request['probe_plan']):
            step['step_id'] = '\x01' * 59 + f'{index:04d}'
        observation = run_case(pw, out, 'control_character_exec', request, measure_margin=True,
                               exec_args=stream_args, exec_output=('\x01' * 1023, '\x01' * 1023))
        observation['exec_steps'] = EXEC_STEPS
        observations.append(observation)
        # Oversized fields must remain refused even with a larger receiver budget.
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
