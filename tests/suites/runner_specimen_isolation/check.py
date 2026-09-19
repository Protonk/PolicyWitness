"""Keep two ordinary CLI specimens live, then finish B while A remains held."""
import copy
from collections import Counter
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
from blackbox import validate_run_shape, validate_step


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def envelope_errors(envelope, witness):
    """Compare PW's claims to the request and independently observed identities."""
    spec = witness['specimen']
    expected_steps = []
    for index, planned in enumerate(spec['probe_plan']):
        allowed = index == 0 or index - 1 == witness['allowed_index']
        expected = {'step_id': planned['step_id'], 'index': index,
                    'sandbox_outcome': 'allow' if allowed else 'deny',
                    'attempt_ok': allowed, 'drift': False if allowed else None}
        if index == 0:
            expected['comparison'] = {'operation_relation': 'matched', 'observation': 'succeeded'}
        if allowed:
            expected['errno'] = None
        expected_steps.append(expected)
    common_errors, matched = validate_run_shape(envelope, expected_steps)
    errors = [f"{witness['label']}: {error}" for error in common_errors]

    def equal(field, actual, expected):
        if type(actual) is not type(expected) or actual != expected:
            errors.append(f"{witness['label']}: {field}: expected {expected!r}, got {actual!r}")

    # Shape errors are already recorded. Only enter the independent identity
    # checks when their containing objects exist; matched steps still receive
    # both shared and specimen-specific checks after an ordering error.
    if not isinstance(envelope, dict) or not isinstance(envelope.get('data'), dict):
        return errors
    data = envelope['data']
    runner = data.get('runner_result')
    if not isinstance(runner, dict):
        return errors
    provenance = data.get('runner_provenance')
    equal('runner_kind', provenance.get('runner_kind') if isinstance(provenance, dict) else None, 'standard')
    worker_pid = witness['processes']['worker']['pid']
    equal('specimen_id', runner.get('specimen_id'), spec['specimen_id'])
    equal('test_overrides', runner.get('test_overrides'), None)
    equal('worker pid', runner.get('pid'), worker_pid)
    sub = runner.get('runner_subprocess')
    if not isinstance(sub, dict):
        sub = {}
    equal('runner_subprocess.pid', sub.get('pid'), worker_pid)
    equal('runner_subprocess.exit_code', sub.get('exit_code'), 0)
    equal('runner_subprocess.term_signal', sub.get('term_signal'), None)
    equal('runner_subprocess.partial_steps', sub.get('partial_steps'), False)
    for step, expected in matched:
        errors.extend(f"{witness['label']}: {error}" for error in validate_step(step, expected))
        index = expected['index']
        planned = spec['probe_plan'][index]
        allowed = expected['attempt_ok']
        field = f"step {planned['step_id']}"
        sb, attempt = step.get('sandbox_check'), step.get('attempt')
        if isinstance(sb, dict):
            equal(f'{field} prediction pid', sb.get('pid'), worker_pid)
            equal(f'{field} operation', sb.get('operation'), planned['sandbox_check']['operation'])
            equal(f'{field} filter value', sb.get('filter_value'), planned['sandbox_check']['filter']['value'])
        if not isinstance(attempt, dict):
            continue  # The shared validator already reported the missing channel.
        equal(f'{field} requested_path', attempt.get('requested_path'), planned['attempt']['target'])
        equal(f'{field} attempt outcome', attempt.get('outcome'), 'ok' if allowed else 'open_failed')
        if not allowed and attempt.get('syscall_errno') not in (1, 13):
            errors.append(f"{witness['label']}: {field}: expected permission syscall_errno (EPERM/EACCES)")
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

    counts = {'accepted': 0, 'rejected': 0}

    def check(name, broken, witness, required=(), *, same_diagnostics_as=None):
        save(controls / f'{name}.json', broken)
        errors = envelope_errors(broken, witness)
        diagnostic = '\n'.join(errors)
        (controls / f'{name}.log').write_text(diagnostic + '\n')
        if required:
            assert errors and all(f"{witness['label']}:" in line for line in errors), (name, errors)
            assert all(fragment in diagnostic for fragment in required), (name, required, errors)
            counts['rejected'] += 1
        else:
            assert not errors, (name, errors)
            counts['accepted'] += 1
        if same_diagnostics_as is not None:
            prefix = f"{witness['label']}: expected step IDs in order "
            order = [error for error in errors if error.startswith(prefix)]
            remaining = Counter(errors) - Counter(order)
            reference = Counter(same_diagnostics_as)
            assert len(order) == 1 and remaining == reference, (
                name, 'reordering changed step diagnostics',
                {'order_errors': len(order),
                 'missing': list((reference - remaining).elements()),
                 'unexpected': list((remaining - reference).elements())})
        return errors

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
                required = ['filter value:', 'expected sandbox_check'] if part == 'prediction' else ['requested_path:', 'attempt outcome:']
            name = f"{witness['label']}_{part}"
            check(name, broken, witness, required)

    for witness, envelope in zip(witnesses, envelopes):
        # Expectations are a fixed test-side table, never inferred from the
        # checker's return value. Each case changes one field of one step.
        for index, planned in enumerate(witness['specimen']['probe_plan']):
            allowed = index in (0, witness['allowed_index'] + 1)
            if allowed:
                cases = [('syscall_errno', 'delete', 'missing attempt.syscall_errno'),
                         ('syscall_errno', 'true', 'invalid attempt.syscall_errno'),
                         ('syscall_errno', 'false', 'invalid attempt.syscall_errno')]
            else:
                # The bounded audit's complete 24-case measurement, including
                # the two legitimate omissions of optional diagnostic text.
                cases = [(key, 'delete', f'missing attempt.{key}') for key in
                         ('rc', 'exit_code', 'errno', 'syscall_errno', 'requested_path',
                          'normalized_path', 'observed_path')]
                cases += [('outcome', 'delete', 'attempt outcome:'), ('error', 'delete', None),
                          ('errno', 'null', 'attempt.errno mismatch'),
                          ('exit_code', 'null', 'invalid attempt.exit_code'),
                          ('rc', 'null', 'invalid attempt.rc'),
                          ('syscall_errno', 'null', 'expected permission syscall_errno'),
                          ('outcome', 'null', 'attempt outcome:'),
                          ('requested_path', 'null', 'requested_path:'), ('error', 'null', None)]
                cases += [(key, value, f'invalid attempt.{key}') for key in
                          ('errno', 'exit_code', 'rc', 'syscall_errno') for value in ('true', 'false')]
            for key, mutation, diagnostic in cases:
                changed = copy.deepcopy(envelope)
                attempt = changed['data']['runner_result']['steps'][index]['attempt']
                if mutation == 'delete':
                    attempt.pop(key, None)
                else:
                    attempt[key] = {'null': None, 'true': True, 'false': False}[mutation]
                check(f"{witness['label']}_step{index}_{key}_{mutation}", changed, witness,
                      [planned['step_id'], diagnostic] if diagnostic else ())

            changed = copy.deepcopy(envelope)
            # Both values have legal types; agreement is independently required.
            changed['data']['runner_result']['steps'][index]['attempt']['errno'] = 1 if allowed else 2
            check(f"{witness['label']}_step{index}_errno_mismatch", changed, witness,
                  [planned['step_id'], 'attempt.errno mismatch'])
            if not allowed:
                changed = copy.deepcopy(envelope)
                attempt = changed['data']['runner_result']['steps'][index]['attempt']
                attempt['rc'] = attempt['exit_code'] + 1
                check(f"{witness['label']}_step{index}_rc_mismatch", changed, witness,
                      [planned['step_id'], 'attempt.rc mismatch'])
                for error in (1, 13):
                    changed = copy.deepcopy(envelope)
                    changed['data']['runner_result']['steps'][index]['attempt'].update(
                        errno=error, syscall_errno=error)
                    check(f"{witness['label']}_step{index}_permission_{error}", changed, witness)

        # Baseline acceptance and the named attempt failure are independent
        # expectations. Their paired reorders must preserve all step errors,
        # including multiplicity, while allowing diagnostic order to change.
        valid_diagnostics = check(f"{witness['label']}_attribution_valid_ordered", envelope, witness)
        changed = copy.deepcopy(envelope)
        changed['data']['runner_result']['steps'].reverse()
        check(f"{witness['label']}_reordered_valid", changed, witness,
              ['expected step IDs in order'], same_diagnostics_as=valid_diagnostics)
        changed = copy.deepcopy(envelope)
        steps = changed['data']['runner_result']['steps']
        steps[0]['attempt'].update(rc=1, exit_code=1, errno=13, syscall_errno=13)
        step_id = witness['specimen']['probe_plan'][0]['step_id']
        attempt_errors = [f"{step_id}: expected attempt_ok=True", f"{step_id}: expected errno=None"]
        ordered_diagnostics = check(f"{witness['label']}_attribution_bad_attempt", changed, witness,
                                    attempt_errors)
        steps.reverse()  # Move the faulty exec step away from its request position.
        check(f"{witness['label']}_reordered_and_bad_attempt", changed, witness,
              ['expected step IDs in order', *attempt_errors], same_diagnostics_as=ordered_diagnostics)
        changed = copy.deepcopy(envelope)
        steps = changed['data']['runner_result']['steps']
        steps[0]['sandbox_check'] = None
        del steps[2]['attempt']['errno']
        check(f"{witness['label']}_malformed_prediction_and_missing_alias", changed, witness,
              [f"missing sandbox_check for {witness['specimen']['probe_plan'][0]['step_id']}",
               f"{witness['specimen']['probe_plan'][2]['step_id']}: missing attempt.errno"])
    print(f"{counts['rejected']} corruptions rejected with attribution diagnostics; "
          f"{counts['accepted']} valid evidence variants accepted", flush=True)


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
