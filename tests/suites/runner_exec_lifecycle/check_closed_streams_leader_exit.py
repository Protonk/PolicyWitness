"""Observe a same-group descendant after leader exit and captured-stream EOF.

The descendant's lifetime after ordinary completion carries no verdict. This
checker classifies it from OS exit events registered before completion is
triggered: the original generation alive with an acknowledged ping, or that
generation's observed exit before cleanup. A classification those events cannot
settle fails the observation; a missing ping or PID is never read as an exit.
The reply's account of the product's own calls and the later file effect are
judged separately and written to account.json for the case to publish.
Process and effect observations precede JSON interpretation. Staging is
removed only after independent helper/worker exit and CLI cleanup.
"""
import json
import os
from pathlib import Path
import secrets
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures/exec'))
from control import TreeControl, ExitObserver, process_snapshot
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
import build_context
from run_capture import RunCapture
from exec_observation import assert_observation

ALIVE = 'alive_acknowledged'
EXITED = 'exited_before_cleanup'
# Only the sample taken after this checker releases the fixture can report this.
RELEASED = 'exited_after_fixture_release'
SAMPLE_WINDOW_SECONDS = 2.0


class Unresolved(Exception):
    """The registered events do not settle which history occurred."""


class InvalidObservation(Exception):
    """The sample does not describe the registered generation."""


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def identity(snapshot):
    # Reparenting after the leader exits may change ppid, but not this identity.
    return {key: snapshot[key] for key in ('pid', 'start_sec', 'start_usec', 'path')}


class ExitStamps:
    """Stamp registered processes' OS exit events on one queue and one clock.

    A stamp is when this process observed the event, not when the process
    exited; events returned by one wake share a stamp. The event carries no
    status for a process that is not this one's child.
    """
    def __init__(self):
        self.queue = select.kqueue()
        self.registered = {}
        self.observed = {}

    def watch(self, pid):
        assert pid > 0 and pid not in self.registered, f'invalid or duplicate stamped PID: {pid}'
        self.queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                           flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                           fflags=select.KQ_NOTE_EXIT)], 0, 0)
        self.registered[pid] = time.monotonic_ns()

    def collect(self, timeout=0):
        events = self.queue.control(None, max(1, len(self.registered)), timeout)
        stamp = time.monotonic_ns()
        for event in events:
            assert not event.flags & select.KQ_EV_ERROR, f'exit observation failed: {event}'
            if event.fflags & select.KQ_NOTE_EXIT:
                self.observed.setdefault(event.ident, stamp)

    def wait_for(self, pid, timeout):
        deadline = time.monotonic() + timeout
        self.collect()
        while pid not in self.observed:
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            self.collect(min(left, 0.25))
        return self.observed[pid]

    def close(self):
        self.queue.close()


def sample_descendant(control, stamps, helper, registered, group, timing):
    """Read the registered events, then ping and inspect only a descendant with no exit event."""
    pid = registered['pid']
    sample = dict(descendant=dict(identity=identity(registered), group=group),
                  exit_watch_registered_ns=stamps.registered.get(pid), **timing,
                  sample_started_ns=time.monotonic_ns(), ping=None, snapshot=None)
    stamps.collect()
    if pid not in stamps.observed:
        ping = dict(sent_ns=time.monotonic_ns(), acknowledged=False, error=None)
        try:
            control.ping('C')
            ping['acknowledged'] = True
        except (AssertionError, OSError) as error:
            ping['error'] = repr(error)
        ping['ended_ns'] = time.monotonic_ns()
        try:
            current = process_snapshot(helper, pid)
            snapshot = dict(identity=identity(current), group=os.getpgid(pid))
        except (AssertionError, OSError, ValueError, subprocess.TimeoutExpired) as error:
            snapshot = dict(error=repr(error))
        sample.update(ping=ping, snapshot=snapshot)
        # An unacknowledged ping is not an exit. Give the registered event a bounded time to arrive.
        if ping['acknowledged']:
            stamps.collect()
        else:
            stamps.wait_for(pid, SAMPLE_WINDOW_SECONDS)
    sample.update(exit_observed_ns=stamps.observed.get(pid), sample_ended_ns=time.monotonic_ns())
    return sample


def classify_lifetime(sample):
    """Name the history a sample's registered events establish, or refuse.

    This is a pure reading of the sample, so constructed samples replay it.
    """
    def stamp(name, required=True):
        value = sample.get(name)
        if value is None and not required:
            return None
        if type(value) is not int or value < 0:
            raise InvalidObservation(f'{name} is not a clock reading: {value!r}')
        return value

    subject = sample.get('descendant')
    if not isinstance(subject, dict) or not isinstance(subject.get('identity'), dict) or type(subject.get('group')) is not int:
        raise InvalidObservation('sample names no registered generation and group')
    registered = stamp('exit_watch_registered_ns')
    triggered = stamp('completion_triggered_ns')
    completed = stamp('cli_completed_ns')
    released = stamp('fixture_released_ns', required=False)
    exited = stamp('exit_observed_ns', required=False)
    if registered >= triggered:
        raise InvalidObservation('the exit watch was not registered before completion was triggered')
    ping = sample.get('ping')
    acknowledged = isinstance(ping, dict) and ping.get('acknowledged') is True
    if exited is not None:
        if exited < registered:
            raise InvalidObservation('exit event precedes its registration')
        after_release = released is not None and exited >= released
        return dict(history=RELEASED if after_release else EXITED, exit_observed_ns=exited,
                    exit_minus_cli_completion_ns=exited - completed,
                    exit_observed='before_cli_completion' if exited < completed else 'at_or_after_cli_completion',
                    ping_acknowledged_before_exit=acknowledged and ping['ended_ns'] <= exited,
                    termination_cause='not identified: the exit event carries no status for a process that is not this checker\'s child')
    if released is not None:
        raise Unresolved('no registered exit event after the fixture release')
    if not acknowledged:
        raise Unresolved('no registered exit event and no acknowledged ping; a missing ping is not an observed exit')
    snapshot = sample.get('snapshot')
    if not isinstance(snapshot, dict) or 'error' in snapshot:
        raise Unresolved('acknowledged ping without a readable snapshot of the registered generation')
    if snapshot.get('identity') != subject['identity']:
        raise InvalidObservation('changed identity: the process at the registered PID is not the registered generation')
    if snapshot.get('group') != subject['group']:
        raise InvalidObservation('changed process group: the descendant left the group it was registered in')
    return dict(history=ALIVE, ping_acknowledged_ns=ping['ended_ns'],
                ping_minus_cli_completion_ns=ping['ended_ns'] - completed,
                exit_observed_ns=None, exit_observed='not_observed_through_sample')


def classifier_controls():
    """Constructed samples: both promised histories complete; each unsettled or foreign sample refuses."""
    generation = dict(pid=4242, start_sec=1700000000, start_usec=17, path='/constructed/helper')
    def sample(**changes):
        value = dict(descendant=dict(identity=dict(generation), group=4241), exit_watch_registered_ns=100,
                     completion_triggered_ns=200, cli_completed_ns=300, fixture_released_ns=None,
                     ping=dict(sent_ns=310, ended_ns=320, acknowledged=True, error=None),
                     snapshot=dict(identity=dict(generation), group=4241), exit_observed_ns=None)
        value.update(changes)
        return value
    no_ping = dict(sent_ns=310, ended_ns=1310, acknowledged=False, error='constructed: no live response')
    cases = [
        ('alive_with_acknowledged_ping', sample(), ALIVE),
        ('exit_before_cli_completion', sample(exit_observed_ns=250, ping=None, snapshot=None), EXITED),
        ('exit_after_cli_completion', sample(exit_observed_ns=305, ping=None, snapshot=None), EXITED),
        ('acknowledged_ping_then_exit_in_window', sample(exit_observed_ns=330), EXITED),
        ('unacknowledged_ping_then_exit_event', sample(exit_observed_ns=900, ping=no_ping, snapshot=dict(error='constructed')), EXITED),
        ('exit_after_fixture_release', sample(fixture_released_ns=400, exit_observed_ns=410, ping=None, snapshot=None), RELEASED),
        ('missing_exit_evidence_and_ping', sample(ping=no_ping, snapshot=dict(error='constructed: no such process')), Unresolved),
        ('missing_pid_without_exit_event', sample(snapshot=dict(error='constructed: no such process')), Unresolved),
        ('no_exit_event_after_release', sample(fixture_released_ns=400), Unresolved),
        ('changed_identity', sample(snapshot=dict(identity=dict(generation, start_usec=18), group=4241)), InvalidObservation),
        ('changed_group', sample(snapshot=dict(identity=dict(generation), group=4242)), InvalidObservation),
        ('watch_registered_after_trigger', sample(exit_watch_registered_ns=201, exit_observed_ns=250), InvalidObservation),
        ('watch_never_registered', sample(exit_watch_registered_ns=None), InvalidObservation),
        ('exit_before_registration', sample(exit_observed_ns=50), InvalidObservation),
    ]
    results = []
    for name, value, expected in cases:
        try:
            actual, detail = classify_lifetime(value)['history'], None
        except (Unresolved, InvalidObservation) as refusal:
            actual, detail = type(refusal), str(refusal)
        assert actual == expected, f'lifetime classifier control {name}: expected {expected!r}, got {actual!r} ({detail})'
        results.append(dict(control=name, sample=value, refusal=detail,
                            result=actual if isinstance(actual, str) else actual.__name__))
    return results


def observation_disagreement(attempt, pid):
    """The shared exec-observation assertions as one reported disagreement; they only read the reply."""
    try:
        assert_observation(attempt, pid, stop='leader_exit_and_eof', leader_observed=True,
                           stdout_eof=True, stderr_eof=True, cleanup_requested=False, exit_code=0)
    except (AssertionError, KeyError, TypeError) as error:
        return repr(error)[:600]
    return None


def reply_account(envelope, rc, worker_pid, leader_pid):
    """Each fact the reply must report about the product's own calls, beside its independent expectation."""
    def member(value, key):
        return value.get(key) if isinstance(value, dict) else None
    runner = member(member(envelope, 'data'), 'runner_result')
    sub = member(runner, 'runner_subprocess')
    steps = member(runner, 'steps')
    middle, last = steps if isinstance(steps, list) and len(steps) == 2 else (None, None)
    attempt, later = member(middle, 'attempt'), member(last, 'attempt')
    rows = [
        ('cli exit status', rc, 0),
        ('envelope validation errors', consumer.validate(envelope, build_context.candidate_contract()), []),
        ('normalized_outcome', member(runner, 'normalized_outcome'), 'finished'),
        ('step count', len(steps) if isinstance(steps, list) else None, 2),
        ('runner_subprocess.pid', member(sub, 'pid'), worker_pid),
        ('runner_subprocess.reaped', member(sub, 'reaped'), True),
        ('runner_subprocess.exit_code', member(sub, 'exit_code'), 0),
        ('runner_subprocess.term_signal', member(sub, 'term_signal'), None),
        ('runner_subprocess.done_observed', member(sub, 'done_observed'), True),
        ('runner_subprocess.partial_steps', member(sub, 'partial_steps'), False),
        ('exec result_source', member(attempt, 'result_source'), 'worker'),
        ('exec outcome', member(attempt, 'outcome'), 'ok'),
        ('exec rc', member(attempt, 'rc'), 0),
        ('exec lifecycle summary', member(member(attempt, 'lifecycle'), 'summary'), 'completed'),
        ('exec child_pid', member(attempt, 'child_pid'), leader_pid),
        ('exec child_exit_code', member(attempt, 'child_exit_code'), 0),
        ('exec child_term_signal', member(attempt, 'child_term_signal'), 0),
        ('exec error', member(attempt, 'error') or None, None),
        ('exec_observation: leader_exit_and_eof stop, both streams at EOF, no cleanup request, leader exit status zero',
         observation_disagreement(attempt, leader_pid), None),
        ('exec stdout', member(attempt, 'stdout'), 'exec_fixture: hello from helper\n'),
        ('exec comparison observation_basis', member(member(middle, 'comparison'), 'observation_basis'), 'spawned_child'),
        ('later step exec_observation', member(later, 'exec_observation'), None),
        ('later step outcome', member(later, 'outcome'), 'ok'),
        ('later step result_source', member(later, 'result_source'), 'worker'),
        ('later step rc', member(later, 'rc'), 0),
        ('later step lifecycle summary', member(member(later, 'lifecycle'), 'summary'), 'completed'),
    ]
    disagreements = [dict(claim=claim, reported=reported, expected=expected)
                     for claim, reported, expected in rows if reported != expected]
    reported = dict(cli_returncode=rc, normalized_outcome=member(runner, 'normalized_outcome'),
                    runner_subprocess=sub, exec_observation=member(attempt, 'exec_observation'),
                    exec_child_pid=member(attempt, 'child_pid'), later_step_outcome=member(later, 'outcome'),
                    claims_compared=len(rows), disagreements=disagreements)
    return reported, disagreements


def judgment(disagreements, agreement):
    if not disagreements:
        return dict(result='favorable', detail=agreement)
    return dict(result='unfavorable', detail=json.dumps(disagreements, sort_keys=True, default=repr)[:1500])


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
    write_json(out / 'classifier-controls.json', classifier_controls())
    root = Path(tempfile.mkdtemp(prefix='pw-exec-same-group-', dir='/private/tmp'))
    control, worker_observer, run, stamps = None, None, None, None
    launched = False
    primary = None
    observations = dict(staging=str(root), stage='prepared', helper_pids={},
                        clock='time.monotonic_ns in this checker; each exit stamp is when its event was observed',
                        stream_closures_acknowledged=[], interventions_before_sampling=[],
                        sample_after_cli=None, lifetime=None)
    try:
        # Persist ownership before any launch. Interruption before finally leaves
        # a conservative retained record, rather than an unrecorded temp path.
        write_json(out / 'cleanup.json', dict(staging=str(root), cleanup_retained=True,
                   staging_removed=False, state='execution_not_finished'))
        write_json(out / 'observations.json', observations)
        control = TreeControl(root / 'control')
        worker_observer = ExitObserver()
        stamps = ExitStamps()
        seed = secrets.token_bytes(64)
        target = root / 'after'
        target.write_bytes(seed)
        (out / 'before.bin').write_bytes(seed)
        request = dict(contract=build_context.candidate_contract(), specimen_id='closed_streams_leader_exit',
            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'), probe_plan=[
                dict(step_id='exec', sandbox_check=dict(operation='process-exec*',
                    filter=dict(kind='path', value=helper)),
                    attempt=dict(kind='exec', action='spawn', target=helper, args=['--tree', control.path])),
                dict(step_id='after', sandbox_check=dict(operation='file-write-data',
                    filter=dict(kind='path', value=str(target))),
                    attempt=dict(kind='file', action='open_write', target=str(target)))])
        run = RunCapture(pw, out, request, cli_args=['--timeout-ms', '30000'])
        # start() can launch the CLI and then fail while recording metadata.
        # Treat every attempted launch as potentially active until observed.
        launched = True
        run.start()
        stamps.watch(run.pid)
        observations['stage'] = 'cli_started'
        write_json(out / 'observations.json', observations)
        pids = dict(control.accept())
        # Both helper exit watches exist before any stream closes or the leader is asked to exit.
        for role in ('P', 'C'):
            stamps.watch(pids[role])
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
                            initial_processes=processes, worker=worker, cli_pid=run.pid,
                            exit_watches_registered_ns={str(pid): stamp for pid, stamp in stamps.registered.items()})
        write_json(out / 'observations.json', observations)

        for role in ('P', 'C'):
            control.close_streams(role)
            observations['stream_closures_acknowledged'].append(role)
            write_json(out / 'observations.json', observations)
        # With both streams closed, the leader's exit is what completes the exec attempt.
        triggered = time.monotonic_ns()
        control.peers['P'].sendall(b'x')
        leader_exit = stamps.wait_for(pids['P'], 2)
        assert leader_exit is not None, 'leader exit event missing'
        observations.update(stage='leader_exit_observed', completion_triggered_ns=triggered,
                            leader_exit_observed_ns=leader_exit)
        write_json(out / 'observations.json', observations)
        completed = stamps.wait_for(run.pid, 25)
        assert completed is not None, 'CLI exit event missing 25 seconds after the leader exited'
        rc = run.wait(timeout=5)
        timing = dict(completion_triggered_ns=triggered, cli_completed_ns=completed, fixture_released_ns=None)
        sample = sample_descendant(control, stamps, helper, processes['C'], groups['P'], timing)
        after = target.read_bytes()
        (out / 'after.bin').write_bytes(after)
        observations.update(stage='descendant_sampled_after_cli', sample_after_cli=sample,
                            cli_returncode=rc, cli_completed_ns=completed, elapsed_seconds=run.elapsed_seconds,
                            later_file_hex=after.hex(),
                            exit_events_observed_ns={str(pid): stamp for pid, stamp in stamps.observed.items()})
        write_json(out / 'observations.json', observations)
        # Unresolved and InvalidObservation propagate: the promised classification is then incomplete.
        lifetime = classify_lifetime(sample)
        observations.update(stage='lifetime_classified', lifetime=lifetime)
        write_json(out / 'observations.json', observations)

        # Only now read PW's claims and compare them with the independent facts.
        envelope = run.load_json()
        reported, disagreements = reply_account(envelope, rc, worker['pid'], pids['P'])
        effect = [] if after == b'x' and after != seed else [dict(claim='later step target bytes', reported=after.hex(), expected=b'x'.hex())]

        # Release is a later intervention, never part of the lifetime sample. It
        # must leave exit events for both helpers whichever history was observed.
        released = time.monotonic_ns()
        control.release()
        control.assert_stopped(timeout=3)
        observations['exit_events_after_release'] = sorted(control.exits())
        if lifetime['history'] == ALIVE:
            # The same sampler and classifier must now report the released generation's exit.
            again = sample_descendant(control, stamps, helper, processes['C'], groups['P'],
                                      dict(timing, fixture_released_ns=released))
            sensitivity = dict(sample=again, classification=classify_lifetime(again))
            assert sensitivity['classification']['history'] == RELEASED, sensitivity
        else:
            sensitivity = dict(not_applicable='the descendant had exited before the fixture release')
        observations.update(stage='observation_complete', fixture_released_ns=released,
                            released_descendant_sample=sensitivity)
        write_json(out / 'observations.json', observations)
        write_json(out / 'account.json', dict(
            descendant_lifetime=dict(lifetime, verdict=None, descendant_pid=pids['C'], process_group=groups['P'],
                                     stream_closures_acknowledged=observations['stream_closures_acknowledged'],
                                     interventions_before_sampling=observations['interventions_before_sampling'],
                                     cli_completed_ns=completed, completion_triggered_ns=triggered),
            exec_reply=reported,
            later_file_effect=dict(seed_bytes=len(seed), after_hex=after.hex(), changed_from_seed=after != seed),
            judgments=dict(
                truthful_exec_account=judgment(disagreements, f"{reported['claims_compared']} reported facts agree with the independent observations; the exec attempt reports leader_exit_and_eof with no cleanup request"),
                later_step_effect=judgment(effect, 'the later step replaced its target seed with the one byte it writes'))))
        print(f"Descendant lifetime after ordinary completion observed without a verdict: {lifetime['history']} "
              f"(exit event {lifetime['exit_observed']}). Reply account disagreements: {len(disagreements)}; "
              f"later file effect disagreements: {len(effect)}.")
    except BaseException as error:
        primary = error
        raise
    finally:
        if stamps is not None:
            stamps.close()
        try:
            cleanup(control, worker_observer, run, launched, root, out, primary)
        except BaseException as error:
            if primary is None:
                raise
            print('Additional cleanup failure; original exception preserved: ' + repr(error), file=sys.stderr)


if __name__ == '__main__':
    main()
