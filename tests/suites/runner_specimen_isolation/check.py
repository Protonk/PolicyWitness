"""Keep two ordinary CLI specimens live, then finish B while A remains held."""
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures' / 'exec'))
from control import ExitObserver, TreeControl, process_snapshot

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def envelope_errors(envelope, witness):
    """Compare PW's claims to the request and independently observed identities."""
    errors = []

    def equal(field, actual, expected):
        if type(actual) is not type(expected) or actual != expected:
            errors.append(f"{witness['label']}: {field}: expected {expected!r}, got {actual!r}")

    spec = witness['specimen']
    worker_pid = witness['processes']['worker']['pid']
    equal('kind', envelope.get('kind'), 'run')
    equal('result.ok', (envelope.get('result') or {}).get('ok'), True)
    data = envelope.get('data') or {}
    equal('runner_kind', (data.get('runner_provenance') or {}).get('runner_kind'), 'standard')
    runner = data.get('runner_result') or {}
    equal('specimen_id', runner.get('specimen_id'), spec['specimen_id'])
    equal('normalized_outcome', runner.get('normalized_outcome'), 'ok')
    equal('test_overrides', runner.get('test_overrides'), None)
    equal('worker pid', runner.get('pid'), worker_pid)
    sub = runner.get('runner_subprocess') or {}
    equal('runner_subprocess.pid', sub.get('pid'), worker_pid)
    equal('runner_subprocess.exit_code', sub.get('exit_code'), 0)
    equal('runner_subprocess.term_signal', sub.get('term_signal'), None)
    equal('runner_subprocess.partial_steps', sub.get('partial_steps'), False)
    steps = runner.get('steps') or []
    equal('step IDs', [step.get('step_id') for step in steps],
          [step['step_id'] for step in spec['probe_plan']])
    if len(steps) != len(spec['probe_plan']):
        return errors
    for index, (step, planned) in enumerate(zip(steps, spec['probe_plan'])):
        field = f"step {planned['step_id']}"
        sb, attempt = step.get('sandbox_check') or {}, step.get('attempt') or {}
        allowed = index == 0 or index - 1 == witness['allowed_index']
        equal(f'{field} prediction pid', sb.get('pid'), worker_pid)
        equal(f'{field} operation', sb.get('operation'), planned['sandbox_check']['operation'])
        equal(f'{field} filter value', sb.get('filter_value'), planned['sandbox_check']['filter']['value'])
        equal(f'{field} prediction', sb.get('outcome'), 'allow' if allowed else 'deny')
        equal(f'{field} requested_path', attempt.get('requested_path'), planned['attempt']['target'])
        equal(f'{field} attempt outcome', attempt.get('outcome'), 'ok' if allowed else 'open_failed')
        if 'drift' not in step:
            errors.append(f"{witness['label']}: {field}: missing drift")
        equal(f'{field} drift', step.get('drift'), False)
        if allowed:
            equal(f'{field} attempt rc', attempt.get('rc'), 0)
            equal(f'{field} syscall_errno', attempt.get('syscall_errno'), None)
        elif type(attempt.get('rc')) is not int or attempt['rc'] == 0 or attempt.get('syscall_errno') not in (1, 13):
            errors.append(f"{witness['label']}: {field}: denied attempt lacks failure/permission errno: {attempt!r}")
        if index == 0:
            equal(f'{field} child_pid', attempt.get('child_pid'), witness['processes']['helper']['pid'])
            equal(f'{field} child_exit_code', attempt.get('child_exit_code'), 0)
            equal(f'{field} child_term_signal', attempt.get('child_term_signal'), 0)
            equal(f'{field} stdout', attempt.get('stdout'), 'exec_fixture: hello from helper\n')
            equal(f'{field} stderr marker', attempt.get('stderr'), witness['marker'] + '\n')
        elif allowed:
            equal(f'{field} observed_path', attempt.get('observed_path'), planned['attempt']['target'])
    return errors


def inspect_chain(helper, control):
    leader = process_snapshot(helper, control.pids['P'])
    worker = process_snapshot(helper, leader['ppid'])
    host = process_snapshot(helper, worker['ppid'])
    assert leader['path'] == helper, leader
    assert Path(worker['path']).name == 'pw-probe-runner', worker
    assert Path(host['path']).name == 'PWRunner', host
    assert len({leader['pid'], worker['pid'], host['pid']}) == 3
    return {'helper': leader, 'worker': worker, 'host': host}


def file_bytes(witness, phase, allowed_effect=False):
    after = []
    for index, (path, seed) in enumerate(zip(witness['paths'], witness['seeds'])):
        data = path.read_bytes()
        (witness['out'] / f'file{index}.{phase}.bin').write_bytes(data)
        if allowed_effect and index == witness['allowed_index']:
            assert data and data != seed, f"{witness['label']}: allowed file {index} did not change with nonempty data"
        else:
            assert data == seed, f"{witness['label']}: file {index} changed while held or denied ({phase})"
        after.append(data)
    return after


def exercise_checker(witnesses, envelopes, out):
    controls = out / 'checker_controls'
    controls.mkdir()
    count = 0
    for owner, other in ((0, 1), (1, 0)):
        witness = witnesses[owner]
        for part in ('envelope', 'step0', 'step1', 'step2', 'prediction', 'attempt'):
            broken = copy.deepcopy(envelopes[owner])
            foreign = copy.deepcopy(envelopes[other])
            if part == 'envelope':
                broken = foreign
                required = ['specimen_id:', 'worker pid:', 'stderr marker:']
            elif part.startswith('step'):
                index = int(part[-1])
                broken['data']['runner_result']['steps'][index] = foreign['data']['runner_result']['steps'][index]
                required = ['stderr marker:'] if index == 0 else ['requested_path:', 'filter value:']
            else:
                # Keep this run's top-level identity and step IDs intact. For
                # predictions, even repair the PID so path/decision checks
                # must catch the foreign evidence themselves.
                key = 'sandbox_check' if part == 'prediction' else 'attempt'
                broken['data']['runner_result']['steps'][1][key] = foreign['data']['runner_result']['steps'][1][key]
                if part == 'prediction':
                    broken['data']['runner_result']['steps'][1][key]['pid'] = witness['processes']['worker']['pid']
                required = ['filter value:', 'prediction:'] if part == 'prediction' else ['requested_path:', 'attempt outcome:']
            name = f"{witness['label']}_{part}"
            save(controls / f'{name}.json', broken)
            errors = envelope_errors(broken, witness)
            diagnostic = '\n'.join(errors)
            (controls / f'{name}.log').write_text(diagnostic + '\n')
            assert errors and all(f"{witness['label']}:" in line for line in errors), (name, errors)
            assert all(fragment in diagnostic for fragment in required), (name, required, errors)
            count += 1
    print(f'{count} cross-run corruptions rejected with attribution diagnostics', flush=True)


def main():
    pw, out_arg, helper_arg = sys.argv[1:]
    out, helper = Path(out_arg).resolve(), str(Path(helper_arg).resolve())
    step_ids = [secrets.token_hex(8) for _ in range(3)]
    with tempfile.TemporaryDirectory(prefix='pw-overlap-', dir='/private/tmp') as work, ExitStack() as resources:
        b_exits = ExitObserver()
        resources.callback(b_exits.close)
        controls, runs, witnesses, envelopes = [], [], [], []
        events = []
        started = time.monotonic()

        def event(name):
            events.append({'event': name, 'elapsed_seconds': time.monotonic() - started})
            save(out / 'timeline.json', events)

        try:
            for index, label in enumerate(('A', 'B')):
                directory = Path(work) / label
                directory.mkdir()
                artifacts = out / label
                artifacts.mkdir()
                control = TreeControl(directory / 'gate')
                controls.append(control)
                paths = [directory / secrets.token_hex(8) for _ in range(2)]
                seeds = [secrets.token_bytes(64) for _ in paths]
                for path, seed in zip(paths, seeds):
                    path.write_bytes(seed)
                marker = secrets.token_hex(16)
                spec = {
                    'schema_version': 1, 'specimen_id': secrets.token_hex(16),
                    'runner': {'mode': 'standard'},
                    'policy': {'format': 'sbpl', 'sbpl_source':
                               '(version 1)(allow default)(deny file-write-data (literal (param "TARGET")))',
                               'params': {'TARGET': str(paths[1 - index])}},
                    'probe_plan': [{
                        'step_id': step_ids[0],
                        'sandbox_check': {'operation': 'process-exec*', 'filter': {'kind': 'path', 'value': helper}},
                        'attempt': {'kind': 'exec', 'action': 'spawn', 'target': helper,
                                    'args': ['--stderr', marker, '--tree', control.path]},
                    }] + [{
                        'step_id': step_ids[i + 1],
                        'sandbox_check': {'operation': 'file-write-data', 'filter': {'kind': 'path', 'value': str(path)}},
                        'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(path)},
                    } for i, path in enumerate(paths)],
                }
                witness = {'label': label, 'specimen': spec, 'marker': marker, 'allowed_index': index,
                           'paths': paths, 'seeds': seeds, 'out': artifacts}
                witnesses.append(witness)
                run = RunCapture(pw, artifacts, spec,
                                 cli_args=['--no-log-capture', '--timeout-ms', '30000'])
                runs.append(run)
                resources.callback(run.close)
                file_bytes(witness, 'before')
            # Prepare everything before either exec deadline starts. The two
            # launches overlap by socket rendezvous, never by guessed sleeps.
            for run in runs:
                run.start()
            for witness, control in zip(witnesses, controls):
                control.accept(timeout=5)
                control.assert_running()
                witness['processes'] = inspect_chain(helper, control)
                save(witness['out'] / 'processes.json', witness['processes'])
                groups = {role: os.getpgid(pid) for role, pid in control.pids.items()}
                assert groups['P'] == groups['C'] == control.pids['P'], groups
                save(witness['out'] / 'tree.json', {'pids': control.pids, 'groups': groups})
            all_pids = [info['pid'] for witness in witnesses for info in witness['processes'].values()]
            assert len(set(all_pids)) == 6, f'runs share an OS-observed helper, worker, or host: {all_pids}'
            for role in ('worker', 'host'):
                b_exits.watch(witnesses[1]['processes'][role]['pid'])
            for witness, control in zip(witnesses, controls):
                control.assert_running()
                file_bytes(witness, 'held')
            event('both_runs_held')

            controls[1].release()
            event('B_released')
            assert runs[1].wait(timeout=5) == 0, 'B: CLI failed; see B/run.json and B/pw.stderr'
            controls[1].assert_stopped()
            b_after = file_bytes(witnesses[1], 'after', allowed_effect=True)
            event('B_completed')
            # A reply precedes the XPC host's scheduled exit. Wait for the
            # actual process exits so delayed teardown is exercised while A
            # is still held, rather than racing both runs to completion.
            b_exits.assert_stopped()
            save(witnesses[1]['out'] / 'exited.json', {'worker_and_host': sorted(b_exits.exited),
                                                    'helper_tree': sorted(controls[1].exited)})
            event('B_processes_exited')
            controls[0].assert_running()
            assert runs[0].poll() is None, 'A: CLI completed before its gate was released'
            again = inspect_chain(helper, controls[0])
            assert again == witnesses[0]['processes'], 'A: process identity changed while B completed'
            save(witnesses[0]['out'] / 'processes_after_B.json', again)
            file_bytes(witnesses[0], 'after_B')
            event('A_still_held_after_B')

            controls[0].release()
            event('A_released')
            assert runs[0].wait(timeout=5) == 0, 'A: CLI failed; see A/run.json and A/pw.stderr'
            controls[0].assert_stopped()
            file_bytes(witnesses[0], 'after', allowed_effect=True)
            assert file_bytes(witnesses[1], 'after_A', allowed_effect=True) == b_after, 'A changed B files'
            event('A_completed')
            # Consult PW's reports only after recording the independent effects.
            for witness, run in zip(witnesses, runs):
                envelope = run.load_json()
                errors = envelope_errors(envelope, witness)
                (witness['out'] / 'envelope_checks.log').write_text('\n'.join(errors) + '\n')
                assert not errors, '\n'.join(errors)
                envelopes.append(envelope)
            print('B completed while A remained held; distinct OS identities, file effects, and envelopes agree', flush=True)
            exercise_checker(witnesses, envelopes, out)
        finally:
            for control in controls:
                control.close()


if __name__ == '__main__':
    main()
