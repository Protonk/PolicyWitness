"""Gate-3 witnesses. Observe effects before consulting the production envelope."""
import errno
import json
from pathlib import Path
import secrets
import select
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/validator'))
from run_capture import RunCapture
import consumer
from gate import Gate, install_bridge
from control import TreeControl, process_snapshot, ExitObserver


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def step(path, action, name):
    operation = {'unlink': 'file-write-unlink', 'create': 'file-write-create',
                 'open_read': 'file-read-data', 'open_write': 'file-write-data'}[action]
    return dict(step_id=name, sandbox_check=dict(operation=operation, filter=dict(kind='path', value=str(path))),
                attempt=dict(kind='file', action=action, target=str(path)))


def specimen(plan, policy='(version 1)(allow default)', overrides=None):
    result = dict(schema_version=1, specimen_id=secrets.token_hex(12),
                  policy=dict(format='sbpl', sbpl_source=policy), probe_plan=plan)
    if overrides: result['_test_overrides'] = overrides
    return result


def ordering(runner, disposition='reaped'):
    assert runner['runner_subprocess']['ordering'] == dict(
        collection_closed_before_proceed=True, proceed_set=True, proceed_observed=True,
        validator_disposition=disposition, protocol_violations=[], worker_lifetime_established=True), runner['runner_subprocess']['ordering']


def envelope(run, rc, spec, outcome='ok'):
    value = run.load_json()
    assert rc == (0 if outcome == 'ok' else 1), value
    runner = value['data']['runner_result']
    assert runner['normalized_outcome'] == outcome, runner
    assert runner.get('test_overrides') == spec.get('_test_overrides'), runner
    assert runner['runner_subprocess']['exit_code'] == 0, runner
    errors = consumer.validate(value)
    assert not errors, errors
    assert [s['step_id'] for s in runner['steps']] == [s['step_id'] for s in spec['probe_plan']]
    return runner


def limited(row):
    # The record carries only the vocabulary; what the interval cannot
    # establish is said by `order`. The consumer's shape allowlist already
    # rejected any key outside the current contract.
    limits = row['comparison']['limitations']
    assert set(limits) <= consumer.LIMITATIONS, row


def native_rows(runner, records):
    for row, record in zip(runner['steps'], records):
        q = row['sandbox_check']
        for key in ('step_id', 'operation', 'filter_value'):
            assert (row['step_id'] if key == 'step_id' else q[key]) == record[key], (row, record)
        assert (q['native_rc'], q['errno'], q['outcome']) == (record['rc'], record['errno'], record['outcome']), (row, record)
        if record['outcome'] in ('allow', 'deny'):
            assert row['comparison']['order'] == 'query_first', row
        limited(row)


def held_effects(pw, out, bridge, helper):
    """Used unchanged by baseline and barrier-bypass candidates.

    Preserve observations and finish/clean up the run before rejecting early
    effects. A malformed envelope or transport failure is never mutation credit.
    """
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    observed = {'held_samples': []}
    with tempfile.TemporaryDirectory(prefix='pw-held-', dir='/private/tmp') as work_arg:
        work = Path(work_arg)
        target = work / secrets.token_hex(8); seed = secrets.token_bytes(64); target.write_bytes(seed)
        tree, gate, exits = TreeControl(work / 'tree'), Gate(work / 'gate'), ExitObserver()
        validator = install_bridge(bridge, out / 'bridge', gate.path)
        plan = [step(target, 'unlink', 'unlink'), dict(step_id='exec',
                sandbox_check=dict(operation='process-exec*', filter=dict(kind='path', value=str(helper))),
                attempt=dict(kind='exec', action='spawn', target=str(helper), args=['--tree', tree.path]))]
        spec = specimen(plan, overrides={'validator_executable_path': str(validator)})
        run = RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture'])
        try:
            run.start(); ready = gate.accept()
            worker = process_snapshot(helper, ready['target_pid'])
            validator_info = process_snapshot(helper, gate.pid)
            host = process_snapshot(helper, worker['ppid'])
            assert validator_info['ppid'] == host['pid'], (validator_info, host)
            for pid in (worker['pid'], host['pid']): exits.watch(pid)
            observed.update(worker=worker, validator=validator_info, host=host)
            records = []
            for _ in plan: records.append(gate.query()); gate.emit()
            deadline = time.monotonic() + 0.5
            while True:
                held = gate.ping()
                assert not held['closed'] and held['next'] == 2, held
                present = target.exists()
                observed['held_samples'].append(dict(present=present,
                    bytes_match=present and target.read_bytes() == seed,
                    exec_connected=bool(select.select([tree.listener], [], [], 0)[0])))
                if time.monotonic() >= deadline: break
                time.sleep(0.02)
            gate.finish()
            pids = tree.accept(); tree.assert_running()
            observed['helper'] = process_snapshot(helper, pids['P'])
            observed['grandchild'] = process_snapshot(helper, pids['C'])
            assert observed['helper']['ppid'] == worker['pid'], observed
            assert observed['grandchild']['ppid'] == pids['P'], observed
            observed['absent_after_release'] = not target.exists()
            tree.release(); tree.assert_stopped()
            rc = run.wait(timeout=15)
            exits.assert_stopped(timeout=3)
            observed['exit_events'] = sorted(exits.exited)
            save(out / 'effects.json', observed)
            gate.save(out / 'gate-events.json')
            # These named assertions are the only accepted mutation failures.
            assert all(s['present'] and s['bytes_match'] for s in observed['held_samples']), 'early unlink while collection held'
            assert not any(s['exec_connected'] for s in observed['held_samples']), 'early exec connection while collection held'
            assert observed['absent_after_release'], observed
            runner = envelope(run, rc, spec)
            ordering(runner); native_rows(runner, records)
            assert runner['pid'] == worker['pid'], runner
            assert all(s['attempt']['outcome'] == 'ok' for s in runner['steps']), runner
            assert runner['steps'][1]['attempt']['child_pid'] == pids['P'], runner
            assert runner['steps'][0]['comparison']['observation'] == 'succeeded', runner
            assert runner['steps'][1]['comparison']['observation_basis'] == 'spawned_child', runner
        finally:
            save(out / 'effects.json', observed); gate.save(out / 'gate-events.json')
            try: gate.close()
            finally:
                try: tree.close()
                finally: run.close(); exits.close()
    print('held collection prevents unlink and exec; released effects and ancestry independently observed')


def interval(pw, out):
    with tempfile.TemporaryDirectory(prefix='pw-interval-', dir='/private/tmp') as work:
        target = Path(work) / 'target'
        for name, actions, exists in (('absent', ['create', 'unlink'], False),
                                      ('removed', ['unlink', 'open_read'], True),
                                      ('recreated', ['unlink', 'create', 'open_read'], True)):
            if exists: target.write_bytes(secrets.token_bytes(64))
            spec = specimen([step(target, a, str(i)) for i, a in enumerate(actions)])
            with RunCapture(pw, out / name, spec, cli_args=['--no-log-capture']) as run:
                rc = run.wait(timeout=20)
                after = dict(exists=target.exists(), bytes_hex=target.read_bytes().hex() if target.exists() else None)
                save(run.out / 'effect.json', after)
                assert after['exists'] is (name == 'recreated'), after
                runner = envelope(run, rc, spec)
            ordering(runner, 'not_needed' if name == 'absent' else 'reaped')
            for i, row in enumerate(runner['steps']):
                q, a, c = row['sandbox_check'], row['attempt'], row['comparison']
                assert a['requested_action'] == actions[i] and a['requested_path'] == str(target), row
                if name == 'absent':
                    assert q['outcome'] == 'prediction_unavailable' and q['missing_reason'] == 'query_not_requested', row
                    assert c['order'] == 'unestablished', row
                    assert c['limitations'] == ['query_plan:path_unresolved_at_planning'], row
                    assert a['outcome'] == 'ok' and c['observation'] == 'succeeded', row
                else:
                    assert q['outcome'] == 'allow' and c['order'] == 'query_first', row
                    limited(row)
                    if name == 'removed' and i == 1:
                        assert a['outcome'] == 'open_failed' and a['errno'] == errno.ENOENT, row
                        assert c['observation'] == 'other_failure' and c['limitations'] == [], row
                    elif actions[i] == 'create':
                        # A create has no single query operation: the record says so.
                        assert a['outcome'] == 'ok' and c['observation'] == 'succeeded', row
                        assert c['operation_relation'] == 'unresolved', row
                    else:
                        assert a['outcome'] == 'ok' and c['observation'] == 'succeeded', row
                        assert c['operation_relation'] == 'matched' and c['target_relation'] == 'same_submitted', row
            if exists:
                # The earlier mutation remains raw evidence even after re-resolution.
                assert runner['steps'][0]['attempt']['requested_action'] == 'unlink'
                assert runner['steps'][0]['attempt']['outcome'] == 'ok'
    print('absent/create/unlink, existing/unlink/read and unlink/recreate/read retain planning and identity limits')


def mutation_interval(pw, out, bridge, between_queries):
    with tempfile.TemporaryDirectory(prefix='pw-change-', dir='/private/tmp') as work_arg:
        work = Path(work_arg); target = work / 'target'; target.write_bytes(secrets.token_bytes(64))
        gate = Gate(work / 'gate')
        validator = install_bridge(bridge, out / 'bridge', gate.path)
        spec = specimen([step(target, 'open_read', str(i)) for i in range(2 if between_queries else 1)],
                        overrides={'validator_executable_path': str(validator)})
        observations = []
        try:
            with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture']) as run:
                # __enter__ starts CLI; the acknowledged query precedes mutation.
                gate_ready = gate.accept()
                records = [gate.query()]; gate.emit()
                assert records[0]['outcome'] == 'allow', records
                observations.append(dict(event='first_query_returned', exists=target.exists(), target_pid=gate_ready['target_pid']))
                assert observations[-1]['exists']
                target.unlink()
                observations.append(dict(event='removed_while_collection_open', exists=target.exists(), gate=gate.ping()))
                assert not observations[-1]['exists'] and not observations[-1]['gate']['closed']
                if between_queries: records.append(gate.query()); gate.emit()
                gate.finish()
                rc = run.wait(timeout=15)
                save(out / 'external-state.json', observations)
                assert not target.exists()
                runner = envelope(run, rc, spec)
                ordering(runner); native_rows(runner, records)
                for row in runner['steps']:
                    assert row['attempt']['outcome'] == 'open_failed' and row['attempt']['errno'] == errno.ENOENT, row
                    assert row['comparison']['observation'] == 'other_failure', row
                    assert row['comparison']['limitations'] == [], row
        finally:
            save(out / 'external-state.json', observations); gate.save(out / 'gate-events.json'); gate.close()
    print('native query receipts and external mutation precede release; missing-target failures are other failures')


def ordinary(pw, out, maximum):
    count = 256 if maximum else 2
    with tempfile.TemporaryDirectory(prefix='pw-ordered-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(8) for _ in range(count)]
        seeds = [secrets.token_bytes(64) for _ in paths]
        for path, seed in zip(paths, seeds): path.write_bytes(seed)
        action = 'open_write' if maximum else 'open_read'
        if maximum:
            policy = '(version 1)(allow default)(deny file-write-data ' + ''.join(f'(literal "{p}")' for p in paths[1::2]) + ')'
        else:
            policy = f'(version 1)(deny default)(allow file-read-data (literal "{paths[0]}"))'
        spec = specimen([step(p, action, str(i)) for i, p in enumerate(paths)], policy)
        with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture']) as run:
            rc = run.wait(timeout=30)
            after = [p.read_bytes() for p in paths]
            save(out / 'effects.json', [dict(index=i, before_hex=b.hex(), after_hex=a.hex()) for i, (b, a) in enumerate(zip(seeds, after))])
            for i, (b, a) in enumerate(zip(seeds, after)):
                assert (bool(a) and a != b) if maximum and i % 2 == 0 else a == b, i
            runner = envelope(run, rc, spec)
        ordering(runner)
        for i, row in enumerate(runner['steps']):
            allowed = i % 2 == 0
            assert row['sandbox_check']['outcome'] == ('allow' if allowed else 'deny'), row
            assert row['comparison']['order'] == 'query_first', row
            assert row['attempt']['outcome'] == ('ok' if allowed else 'open_failed'), row
            assert row['comparison']['observation'] == ('succeeded' if allowed else 'permission_failure'), row
            assert row['comparison']['limitations'] == [], row
    print(f'{count} native predictions precede attempts, with independent file observations')


def spawn_failed(pw, out):
    target = out / 'target'; seed = secrets.token_bytes(64); target.write_bytes(seed)
    hostile = '/nonexistent/pw-validator-not-real'
    spec = specimen([step(target, 'open_write', 'write')], overrides={'validator_executable_path': hostile})
    with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture']) as run:
        rc = run.wait(timeout=20)
        after = target.read_bytes(); save(out / 'effects.json', dict(before_hex=seed.hex(), after_hex=after.hex()))
        assert after and after != seed
        runner = envelope(run, rc, spec, 'validator_spawn_failed')
    ordering(runner, 'not_spawned')
    assert runner.get('validator_subprocess') is None, runner
    failure = runner['validator_spawn_failure']
    assert failure['origin'] == 'runner_host' and failure['operation'] == 'posix_spawn', failure
    assert failure['executable_path'] == hostile and failure['return_code'] == errno.ENOENT, failure
    assert isinstance(failure['diagnostic'], str) and failure['diagnostic'], failure
    assert hostile in runner['error'] and failure['operation'] in runner['error'], runner['error']
    assert failure['diagnostic'] in runner['error'], runner['error']
    row = runner['steps'][0]
    assert row['comparison']['order'] == 'unestablished', row
    assert row['attempt']['outcome'] == 'ok' and row['comparison']['observation'] == 'succeeded', row
    print('real spawn failure closes collection and releases an independently observed write')


if __name__ == '__main__':
    case, pw, out_arg, *equipment = sys.argv[1:]
    out = Path(out_arg).resolve()
    if case == 'attempt_effects_wait_for_collection': held_effects(pw, out, *equipment)
    elif case == 'queries_use_a_pre_attempt_interval': interval(pw, out)
    elif case in ('query_interval_is_not_a_snapshot', 'external_mutation_between_query_and_attempt'):
        mutation_interval(pw, out, equipment[0], case == 'query_interval_is_not_a_snapshot')
    elif case in ('max_steps_ordered', 'deny_default_ordered'): ordinary(pw, out, case == 'max_steps_ordered')
    elif case == 'validator_spawn_failed_reports_degraded': spawn_failed(pw, out)
    else: raise AssertionError(case)
