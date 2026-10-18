"""Characterize a same-group survivor after leader exit and captured-stream EOF.

This pins a current observation limit, not desired process-tree containment.
The helper and kernel observations establish the survivor before PW JSON is read.
Staging is removed only after independent helper/worker exit and CLI cleanup.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures/exec'))
from control import TreeControl, ExitObserver, process_snapshot
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
from contract import REQUEST_SCHEMA
from run_capture import RunCapture


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def identity(snapshot):
    # Reparenting after the leader exits may change ppid, but not this identity.
    return {key: snapshot[key] for key in ('pid', 'start_sec', 'start_usec', 'path')}


def observe_survivor(control, helper, initial, group):
    exited = control.exits()
    assert control.pids['P'] in exited, 'leader exit event missing'
    assert control.pids['C'] not in exited, 'descendant already exited'
    control.ping('C')
    current = process_snapshot(helper, control.pids['C'])
    assert identity(current) == identity(initial), (initial, current)
    current_group = os.getpgid(current['pid'])
    assert current_group == group, (current_group, group)
    assert current['pid'] not in control.exits(), 'descendant exited during observation'
    return dict(process=current, process_group=current_group,
                ping_acknowledged=True, exit_event_observed=False)


def cleanup(control, worker_observer, run, launched, root, out, primary):
    """Attempt owned cleanup, but retain staging unless every relevant exit is known."""
    record = dict(staging=str(root), cleanup_retained=True, staging_removed=False,
                  primary_error=None if primary is None else repr(primary),
                  helper_pids={} if control is None else dict(control.pids),
                  helper_exit_events=[], worker_exit_events=[],
                  helper_cleanup_signals=[], cli_closed=False, errors=[])

    def attempt(label, action):
        try:
            return action()
        except BaseException as error:
            record['errors'].append(dict(stage=label, error=repr(error)))
            return None

    helper_exits_known = not launched
    if control is not None:
        attempt('release_helpers', control.release)
        watched = set(control.observer.pids)
        if watched:
            # The shared close() can signal without observing the resulting exit.
            # Keep its observer open until this case records those exit events.
            attempt('observe_helper_release', lambda: control.observer.assert_stopped(timeout=2))
            exited = attempt('read_helper_exit_events', control.exits)
            if exited is not None:
                for pid in sorted(watched - exited):
                    def terminate(pid=pid):
                        os.kill(pid, signal.SIGKILL)
                        record['helper_cleanup_signals'].append(dict(pid=pid, signal=signal.SIGKILL))
                    attempt('terminate_owned_helper', terminate)
                attempt('observe_helper_cleanup', lambda: control.observer.assert_stopped(timeout=3))
                exited = attempt('final_helper_exit_events', control.exits)
            if exited is not None:
                record['helper_exit_events'] = sorted(exited)
                helper_exits_known = set(control.pids) == {'P', 'C'} and exited == watched
        # An incomplete rendezvous may leave an unobserved peer. Never infer its
        # absence from a closed socket, leader exit or a termination request.
        for role, peer in control.peers.items():
            attempt('close_peer_' + role, peer.close)
        attempt('close_listener', control.listener.close)
        attempt('close_helper_observer', control.observer.close)

    worker_exit_known = not launched
    if worker_observer is not None:
        if worker_observer.pids:
            attempt('observe_worker_exit', lambda: worker_observer.assert_stopped(timeout=5))
            exited = attempt('read_worker_exit_events', worker_observer.exits)
            if exited is not None:
                record['worker_exit_events'] = sorted(exited)
                worker_exit_known = exited == worker_observer.pids
        attempt('close_worker_observer', worker_observer.close)

    if run is not None:
        try:
            run.close()
            record['cli_closed'] = True
        except BaseException as error:
            record['errors'].append(dict(stage='close_cli', error=repr(error)))
    else:
        record['cli_closed'] = not launched

    record['helper_exits_known'] = helper_exits_known
    record['worker_exit_known'] = worker_exit_known
    safe_to_remove = helper_exits_known and worker_exit_known and record['cli_closed']
    # Publish the cleanup account before removing anything. If writing fails,
    # leave staging intact and preserve the original exception below.
    attempt('write_cleanup_before_removal', lambda: write_json(out / 'cleanup.json', record))
    if safe_to_remove and not any(e['stage'] == 'write_cleanup_before_removal' for e in record['errors']):
        try:
            shutil.rmtree(root)
            record['staging_removed'] = True
            record['cleanup_retained'] = False
        except BaseException as error:
            record['errors'].append(dict(stage='remove_staging', error=repr(error)))
    attempt('write_cleanup_final', lambda: write_json(out / 'cleanup.json', record))
    if record['cleanup_retained']:
        record['errors'].append(dict(stage='cleanup_unconfirmed', error='staging retained at ' + str(root)))
        attempt('write_retained_cleanup', lambda: write_json(out / 'cleanup.json', record))
    if record['errors']:
        message = 'cleanup observations: ' + json.dumps(record['errors'])
        if primary is not None:
            print(message, file=sys.stderr)
        else:
            raise AssertionError(message)


def main():
    pw, directory, helper = sys.argv[1:]
    out = Path(directory).resolve()
    out.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='pw-exec-same-group-', dir='/private/tmp'))
    control, worker_observer, run = None, None, None
    launched = False
    primary = None
    observations = dict(staging=str(root), stage='prepared', helper_pids={},
                        stream_closures_acknowledged=[], survivor_after_cli=None)
    try:
        # Persist ownership before any launch. Interruption before finally leaves
        # a conservative retained record, rather than an unrecorded temp path.
        write_json(out / 'cleanup.json', dict(staging=str(root), cleanup_retained=True,
                   staging_removed=False, state='execution_not_finished'))
        write_json(out / 'observations.json', observations)
        control = TreeControl(root / 'control')
        worker_observer = ExitObserver()
        seed = secrets.token_bytes(64)
        target = root / 'after'
        target.write_bytes(seed)
        (out / 'before.bin').write_bytes(seed)
        request = dict(schema_version=REQUEST_SCHEMA, specimen_id='closed_streams_leader_exit',
            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'), probe_plan=[
                dict(step_id='exec', sandbox_check=dict(operation='process-exec*',
                    filter=dict(kind='path', value=helper)),
                    attempt=dict(kind='exec', action='spawn', target=helper, args=['--tree', control.path])),
                dict(step_id='after', sandbox_check=dict(operation='file-write-data',
                    filter=dict(kind='path', value=str(target))),
                    attempt=dict(kind='file', action='open_write', target=str(target)))])
        run = RunCapture(pw, out, request, cli_args=['--no-log-capture', '--timeout-ms', '30000'])
        # start() can launch the CLI and then fail while recording metadata.
        # Treat every attempted launch as potentially active until observed.
        launched = True
        run.start()
        observations['stage'] = 'cli_started'
        write_json(out / 'observations.json', observations)
        pids = dict(control.accept())
        groups = {role: os.getpgid(pid) for role, pid in pids.items()}
        assert groups['P'] == groups['C'] == pids['P'], groups
        control.assert_running()
        processes = {role: process_snapshot(helper, pid) for role, pid in pids.items()}
        assert all(Path(value['path']).resolve() == Path(helper).resolve() for value in processes.values()), processes
        assert processes['C']['ppid'] == pids['P'], processes
        worker = process_snapshot(helper, processes['P']['ppid'])
        assert Path(worker['path']).name == 'pw-probe-runner', worker
        worker_observer.watch(worker['pid'])
        assert identity(process_snapshot(helper, worker['pid'])) == identity(worker), worker
        observations.update(stage='peers_observed', helper_pids=pids, initial_groups=groups,
                            initial_processes=processes, worker=worker)
        write_json(out / 'observations.json', observations)

        for role in ('P', 'C'):
            control.close_streams(role)
            observations['stream_closures_acknowledged'].append(role)
            write_json(out / 'observations.json', observations)
        control.exit_leader()
        observations.update(stage='leader_exit_observed', exit_events_before_cli=sorted(control.exits()))
        write_json(out / 'observations.json', observations)
        rc = run.wait(timeout=25)
        survivor = observe_survivor(control, helper, processes['C'], groups['P'])
        after = target.read_bytes()
        (out / 'after.bin').write_bytes(after)
        observations.update(stage='survivor_observed_after_cli', survivor_after_cli=survivor,
                            cli_returncode=rc, elapsed_seconds=run.elapsed_seconds,
                            later_file_hex=after.hex(), exit_events_after_cli=sorted(control.exits()))
        write_json(out / 'observations.json', observations)
        assert after == b'x' and after != seed, after

        # Only now read PW's claims and compare them with the independent facts.
        envelope = run.load_json()
        errors = consumer.validate(envelope)
        assert not errors, errors
        runner = envelope['data']['runner_result']
        assert rc == 0 and runner['normalized_outcome'] == 'ok', runner
        sub = runner['runner_subprocess']
        assert sub['pid'] == worker['pid'] and sub['reaped'] is True, sub
        assert sub['exit_code'] == 0 and sub.get('term_signal') is None, sub
        assert sub['done_observed'] is True and sub['partial_steps'] is False, sub
        middle, last = runner['steps']
        attempt = middle['attempt']
        assert attempt['result_source'] == 'worker' and attempt['outcome'] == 'ok' and attempt['rc'] == 0, attempt
        assert attempt['lifecycle']['summary'] == 'completed', attempt
        assert attempt['child_pid'] == pids['P'] and attempt['child_exit_code'] == 0, attempt
        assert attempt['child_term_signal'] == 0 and not attempt.get('error'), attempt
        assert attempt['stdout'] == 'exec_fixture: hello from helper\n', attempt
        assert middle['comparison']['observation_basis'] == 'spawned_child', middle
        assert last['attempt']['outcome'] == 'ok' and last['attempt']['result_source'] == 'worker', last
        assert last['attempt']['rc'] == 0 and last['attempt']['lifecycle']['summary'] == 'completed', last

        # Cleanup is an explicit later intervention, never part of the survivor
        # observation. The same liveness check must reject the exited child.
        control.release()
        control.assert_stopped(timeout=3)
        observations['exit_events_after_release'] = sorted(control.exits())
        try:
            observe_survivor(control, helper, processes['C'], groups['P'])
        except AssertionError as error:
            assert str(error) == 'descendant already exited', error
            observations['released_child_negative_control'] = str(error)
        else:
            raise AssertionError('survivor observer accepted the released, exited child')
        observations['stage'] = 'characterization_complete'
        write_json(out / 'observations.json', observations)
        print('Current limit observed: clean exec publication and later file effect while a same-group descendant remained responsive; fixture release then produced its exit event.')
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            cleanup(control, worker_observer, run, launched, root, out, primary)
        except BaseException as error:
            if primary is None:
                raise
            print('Additional cleanup failure; original exception preserved: ' + repr(error), file=sys.stderr)


if __name__ == '__main__':
    main()
