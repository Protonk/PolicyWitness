#!/usr/bin/env python3
"""Prepare or run the bounded log-observer pilot; preparation makes no log query."""
import argparse
import collections
import contextlib
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.append(str(HERE.parent / 'harness'))
import measure as common

PW = ROOT / 'dist/PolicyWitness.app/Contents/MacOS/policy-witness'
OBSERVER = PW.with_name('sandbox-log-observer')
FIXTURE = ROOT / 'tests/fixtures/pw_runner/specimen_mach_deny.json'
CONFIG = HERE / 'pilot-config.json'
OLD_RUN = ROOT / 'records/performance/runs/20261023T212050Z-short-b841'
SOURCES = [ROOT / p for p in (
    'controller/src/bin/sandbox-log-observer.rs', 'controller/src/log_show.rs',
    'controller/src/log_capture.rs', 'controller/src/sandbox_log.rs',
    'controller/src/run_flow.rs', 'controller/src/runner_client.rs')]
NAME = 'pw-probe-runner'
CEILING = 180
RESERVE = 10
ACTIVE_RUN = None


def stamp(seconds):
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S+0000')


def predicate(pid):
    # NAME is a fixed literal with no regex metacharacters; mirror the source.
    pattern = rf'(?s).*Sandbox:[ \t]+{NAME}\({pid}\)([ \t]+.*)?'
    return 'eventMessage MATCHES[c] ' + json.dumps(pattern)


def window(start_ms, end_ms):
    if type(start_ms) is not int or type(end_ms) is not int or end_ms < start_ms:
        raise ValueError('missing, invalid or reversed client wall-clock span')
    return {'started_at_unix_ms': start_ms, 'ended_at_unix_ms': end_ms,
            'pad_seconds': 2, 'start': stamp(start_ms // 1000 - 2),
            'end': stamp((end_ms + 999) // 1000 + 2)}


def direct_argv(query):
    return ['/usr/bin/log', 'show', '--style', 'syslog', '--info', '--debug',
            '--start', query['start'], '--end', query['end'], '--predicate', query['predicate']]


def observer_argv(query):
    return [str(OBSERVER), '--pid', str(query['pid']), '--process-name', NAME,
            '--start', query['start'], '--end', query['end'], '--predicate', query['predicate'],
            '--format', 'json']


def prepare():
    """Pin current artifacts, source and a historical query without querying the store."""
    version_probe = common.probe([str(PW), '--version'], common.clock() + 5, 5)
    if version_probe['state'] != 'ok':
        raise ValueError(f'version unavailable: {version_probe}')
    version = json.loads(version_probe['stdout'])
    identity = common.app_identity(PW, version, common.clock() + 10)
    old = json.loads((HERE.parent / 'harness/configurations.json').read_text())['short']
    if identity['files'] != old['expected_files']:
        raise ValueError('current application differs from build-841 comparison artifacts')
    source_diff = common.probe(['/usr/bin/git', 'diff', version['build']['commit'], '--',
                                'controller', 'runner'], common.clock() + 5, 5)
    if source_diff['state'] != 'ok' or source_diff['stdout']:
        raise ValueError('source differs from the current application build; reassess before preparation')
    relative = 'invocations/00002/stdout.json'
    hashes = dict(line.split('  ', 1)[::-1] for line in (OLD_RUN / 'SHA256SUMS').read_text().splitlines())
    if common.digest(OLD_RUN / 'manifest.json') != hashes['manifest.json']:
        raise ValueError('historical manifest checksum mismatch')
    previous_manifest = json.loads((OLD_RUN / 'manifest.json').read_text())
    event_counts = collections.defaultdict(collections.Counter)
    for entry in previous_manifest['entries']:
        if not entry['capture']:
            continue
        name = entry['directory'] + '/stdout.json'
        payload = (OLD_RUN / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != hashes[name]:
            raise ValueError(f'historical envelope checksum mismatch: {name}')
        prior = json.loads(payload)['data']['sandbox_log_capture']['observer']['data']
        event_counts[entry['specimen']][len(prior['deny_events'])] += 1
    if common.digest(OLD_RUN / relative) != hashes[relative]:
        raise ValueError('historical anchor checksum mismatch')
    envelope = json.loads((OLD_RUN / relative).read_text())
    capture = envelope['data']['sandbox_log_capture']
    original = capture['observer']['data']
    if not original['deny_events']:
        raise ValueError('historical anchor has no parsed denial; reconsider anchor explicitly')
    query = {key: original[key] for key in ('pid', 'predicate', 'start', 'end')}
    if query['predicate'] != predicate(query['pid']):
        raise ValueError('constructed predicate disagrees with recorded production predicate')
    if {k: capture['window'][k] for k in ('start', 'end')} != {
            k: window(capture['window']['started_at_unix_ms'], capture['window']['ended_at_unix_ms'])[k]
            for k in ('start', 'end')}:
        raise ValueError('window reconstruction disagrees with production window')
    dependencies = [*SOURCES, FIXTURE, HERE / 'pilot.py', HERE / 'summarize.py',
                    HERE.parent / 'harness/measure.py', ROOT / 'tests/lib/python.sh',
                    ROOT / 'tests/lib/python_start.sh']
    config = {'format_version': 1, 'prepared_at': common.utc(), 'identity': identity,
              'system_log_sha256': common.digest(Path('/usr/bin/log')),
              'sources_match_build': source_diff, 'version_probe': version_probe,
              'dependencies': {str(p.relative_to(ROOT)): common.digest(p) for p in dependencies},
              'historical_anchor': {'raw_directory': str(OLD_RUN.relative_to(ROOT)),
                                    'file': relative, 'sha256': hashes[relative],
                                    'capture_status': capture['capture_status'],
                                    'original_observed_lines': original['observed_lines'],
                                    'original_deny_events': len(original['deny_events']),
                                    'query': query, 'window': capture['window']},
              'historical_selection': {'specimen': 'mach_deny', 'reason': 'existing fixture with 127/132 prior captures retaining a parsed denial',
                                       'verified_capture_envelopes': sum(sum(v.values()) for v in event_counts.values()),
                                       'deny_event_count_frequencies_by_specimen': event_counts},
              'ceiling_s': CEILING, 'cleanup_reserve_s': RESERVE,
              'child_environment': common.CHILD_ENV}
    common.atomic(CONFIG, config)
    print(json.dumps({'prepared': str(CONFIG.relative_to(ROOT)), 'build': version['build'],
                      'app_files_verified': len(identity['files']), 'live_queries': 0}))


def cost_conditions(anchor):
    q = anchor['query']
    start = int(dt.datetime.strptime(q['start'], '%Y-%m-%d %H:%M:%S%z').timestamp())
    end = int(dt.datetime.strptime(q['end'], '%Y-%m-%d %H:%M:%S%z').timestamp())
    return [
        ('original', dict(q)),
        ('wide_60s', dict(q, start=stamp(end - 60))),
        ('earlier_same_width', dict(q, start=stamp(start - 60), end=stamp(end - 60))),
        ('literal_prefilter', dict(q, predicate='eventMessage CONTAINS[c] "Sandbox:" AND (' + q['predicate'] + ')')),
        ('no_match', dict(q, predicate='FALSEPREDICATE')),
        ('all_pw_workers', dict(q, predicate='eventMessage MATCHES[c] ' + json.dumps(
            rf'(?s).*Sandbox:[ \t]+{NAME}\([0-9]+\)([ \t]+.*)?'))),
    ]


def schedule(config):
    entries = []
    # Reversal balances method and condition order; neither pass is called cold.
    conditions = cost_conditions(config['historical_anchor'])
    for block in (1, 2):
        for label, query in conditions if block == 1 else reversed(conditions):
            for method in ('observer', 'direct') if block == 1 else ('direct', 'observer'):
                entries.append({'kind': 'cost', 'block': block, 'condition': label,
                                'method': method, 'query': query})
    cohorts = [('repeated', [0, 2, 10]), ('first_0', [0]), ('first_2', [2]), ('first_10', [10])]
    for block in (1, 2):
        for cohort, delays in cohorts if block == 1 else reversed(cohorts):
            event = f'b{block}-{cohort}'
            entries.append({'kind': 'specimen', 'event': event, 'block': block, 'cohort': cohort})
            for ordinal, delay in enumerate(delays, 1):
                entries.append({'kind': 'availability', 'event': event, 'block': block,
                                'cohort': cohort, 'method': 'direct', 'ordinal': ordinal,
                                'nominal_delay_s': delay})
    for seq, entry in enumerate(entries, 1):
        entry.update(sequence=seq, directory=f'invocations/{seq:03d}')
    return entries


def send_group(pid, sig):
    try:
        os.killpg(pid, sig)
        return {'signal': sig, 'result': 'sent'}
    except OSError as exc:
        return {'signal': sig, 'result': 'failed', 'errno': exc.errno}


def capture(directory, argv, timeout, limits, metadata):
    """Bounded pipes; retain leader until the final group signal, then wait4."""
    directory.mkdir(parents=True)
    common.atomic(directory / 'request.json', {'argv': argv, 'environment': common.CHILD_ENV,
                                              'cwd': str(ROOT), 'metadata': metadata,
                                              'timeout_s': timeout, 'stream_limits': limits})
    status = {'state': 'running', 'started_at': common.utc(), 'wall_start_ns': time.time_ns(),
              'clocks_start': common.clocks(), 'signals': [], 'exit_code': None,
              'streams': {}, 'cleanup': 'not_started',
              'timing_endpoint': 'wall_ms includes pipe handling, wait4 and group-absence probing; process_wall_ms ends at wait4'}
    begin = common.clock()
    deadline = begin + timeout
    proc = None
    cutoff = None
    try:
        with contextlib.ExitStack() as stack:
            output = {name: stack.enter_context((directory / (name + '.bin')).open('xb'))
                      for name in ('stdout', 'stderr')}
            status.update(popen_enter_monotonic_raw=common.clock(), popen_enter_wall_ns=time.time_ns())
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, cwd=ROOT, env=common.CHILD_ENV,
                                    start_new_session=True, close_fds=True)
            status.update(pid=proc.pid, spawn_return_monotonic_raw=common.clock())
            events = stack.enter_context(contextlib.closing(select.kqueue()))
            pipes = {}
            for name in ('stdout', 'stderr'):
                pipe = stack.enter_context(getattr(proc, name))
                os.set_blocking(pipe.fileno(), False)
                pipes[pipe.fileno()] = (name, pipe)
                status['streams'][name] = {'read': 0, 'retained': 0, 'eof': False, 'limit': limits[name]}
                events.control([select.kevent(pipe.fileno(), filter=select.KQ_FILTER_READ,
                                              flags=select.KQ_EV_ADD)], 0, 0)
            try:
                events.control([select.kevent(proc.pid, filter=select.KQ_FILTER_PROC,
                                              flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                              fflags=select.KQ_NOTE_EXIT)], 0, 0)
            except OSError as exc:
                status['exit_event_error'] = str(exc)
            exited = False
            while True:
                if not exited:
                    observed = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if observed is not None:
                        exited = True
                        status['exit_observed_monotonic_raw'] = common.clock()
                for fd, (name, pipe) in list(pipes.items()):
                    info = status['streams'][name]
                    try:
                        chunk = os.read(fd, min(8192, info['limit'] - info['retained'] + 1))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        info['eof'] = True
                        events.control([select.kevent(fd, filter=select.KQ_FILTER_READ,
                                                      flags=select.KQ_EV_DELETE)], 0, 0)
                        del pipes[fd]
                        continue
                    info['read'] += len(chunk)
                    kept = chunk[:info['limit'] - info['retained']]
                    output[name].write(kept)
                    info['retained'] += len(kept)
                    if len(kept) != len(chunk):
                        cutoff = 'output_overflow'
                if cutoff or (exited and not pipes):
                    break
                if common.INTERRUPTED or common.clock() >= deadline:
                    cutoff = 'interrupted' if common.INTERRUPTED else 'deadline'
                    break
                events.control(None, 3, min(0.005 if 'exit_event_error' in status else 0.05,
                                            max(0, deadline - common.clock())))
    except ChildProcessError as exc:
        cutoff = 'ownership_lost'
        status.update(error=repr(exc), cleanup='ownership_lost')
    except Exception as exc:
        cutoff = 'spawn_error' if proc is None else 'harness_error'
        status['error'] = repr(exc)
    finally:
        if proc is not None and status['cleanup'] != 'ownership_lost':
            # No poll/wait has reaped the leader. Its PID still pins our group.
            status['signals'].append(send_group(proc.pid, signal.SIGKILL))
            cleanup_deadline = common.clock() + 1
            while True:
                try:
                    pid, raw, usage = os.wait4(proc.pid, os.WNOHANG)
                except ChildProcessError as exc:
                    status['cleanup'] = 'ownership_lost'
                    status['cleanup_error'] = repr(exc)
                    break
                if pid:
                    proc.returncode = os.waitstatus_to_exitcode(raw)
                    status.update(exit_code=proc.returncode, wait4_monotonic_raw=common.clock(),
                                  cpu_user_s=usage.ru_utime, cpu_system_s=usage.ru_stime)
                    break
                if common.clock() >= cleanup_deadline:
                    break
                time.sleep(.001)
            # Probe only after release: never signal a possibly reused group.
            while proc.returncode is not None:
                probe = send_group(proc.pid, 0)
                status['group_probe'] = probe
                if probe.get('errno') == errno.ESRCH:
                    status['cleanup'] = 'group_absent'
                    break
                if common.clock() >= cleanup_deadline:
                    break
                time.sleep(.001)
            if status['cleanup'] == 'not_started':
                status['cleanup'] = 'unconfirmed'
        status.update(ended_at=common.utc(), wall_end_ns=time.time_ns(), clocks_end=common.clocks(),
                      cutoff=cutoff, state=cutoff or 'completed')
        a, b = status['clocks_start'], status['clocks_end']
        status['wall_ms'] = (b['monotonic_raw_ns'] - a['monotonic_raw_ns']) / 1e6
        status['process_wall_ms'] = ((status['wait4_monotonic_raw'] - status['popen_enter_monotonic_raw']) * 1000
                                    if 'wait4_monotonic_raw' in status else None)
        gap = b['monotonic_raw_ns'] - a['monotonic_raw_ns'] - b['uptime_raw_ns'] + a['uptime_raw_ns']
        status['sleep_gap_ns'] = gap
        status['sleep_detected'] = gap >= 1_000_000
        status['clock_fault'] = gap < -1_000_000
        common.atomic(directory / 'status.json', status)
    return status


def event_query(envelope):
    data = envelope['data']
    if envelope.get('kind') != 'run' or envelope.get('schema_version') != 7:
        raise ValueError('unsupported execution envelope')
    runner = data['runner_result']
    if runner.get('schema_version') != 23:
        raise ValueError('unsupported runner reply')
    pid = runner['runner_subprocess']['pid']
    if type(pid) is not int or pid <= 0:
        raise ValueError('no authoritative worker PID')
    if data.get('sandbox_log_capture') is not None:
        raise ValueError('unexpected automatic collection')
    span = data['runner_client']
    w = window(span['started_at_unix_ms'], span['ended_at_unix_ms'])
    return dict(w, pid=pid, predicate=predicate(pid))


def verify_config(config):
    for name, expected in config['dependencies'].items():
        if common.digest(ROOT / name) != expected:
            raise ValueError(f'dependency changed since preparation: {name}')
    for name, expected in config['identity']['files'].items():
        if common.digest(Path(name)) != expected:
            raise ValueError(f'app changed since preparation: {name}')
    if common.digest(Path('/usr/bin/log')) != config['system_log_sha256']:
        raise ValueError('system log executable changed since preparation')


def run(args):
    global ACTIVE_RUN
    config = json.loads(CONFIG.read_text())
    verify_config(config)
    if not args.note.strip():
        raise ValueError('record current execution conditions with --note')
    run_id = args.run_id or f'{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%S%fZ}-log-pilot-b841'
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError('run-id must be one path component')
    directory = ROOT / 'records/performance/runs' / run_id
    if directory.exists():
        raise ValueError('output exists; runs are never overwritten')
    with (ROOT / 'tests/.checkout.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_config(config)
        os.umask(0o077)
        directory.mkdir(mode=0o700)
        ACTIVE_RUN = directory
        start = common.clock()
        end = start + CEILING
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, common.interrupt)
        entries = schedule(config)
        manifest = {'format_version': 1, 'run_id': run_id, 'config': config, 'entries': entries,
                    'note': args.note, 'execution_context': 'interactive',
                    'harness_argv': [sys.executable, *sys.argv], 'python': sys.version}
        common.atomic(directory / 'manifest.json', manifest)
        for path in (HERE / 'pilot.py', HERE / 'summarize.py', HERE.parent / 'harness/measure.py', FIXTURE):
            shutil.copyfile(path, directory / path.name)
        assertion_record = {'argv': ['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())], 'launched': False}
        assertion = None
        states, events = {}, {}
        run_info = {'run_id': run_id, 'start_monotonic_raw': start, 'started_at': common.utc(),
                    'hard_finish_monotonic_raw': end, 'stop_reason': 'manifest_exhausted', 'error': None}
        try:
            assertion = subprocess.Popen(assertion_record['argv'], env=common.CHILD_ENV,
                                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, start_new_session=True)
            assertion_record.update(launched=True, pid=assertion.pid)
            common.atomic(directory / 'conditions-start.json', common.conditions(common.clock() + 5))
            for entry in entries:
                if common.INTERRUPTED or common.clock() >= end - RESERVE - 2:
                    run_info['stop_reason'] = 'interrupt' if common.INTERRUPTED else 'ceiling'
                    break
                target = directory / entry['directory']
                metadata = dict(entry)
                if entry['kind'] == 'specimen':
                    argv = [str(PW), 'run', str(directory / FIXTURE.name), '--no-log-capture', '--timeout-ms', '5000']
                    timeout, limit = 15, 32 * 1024 * 1024
                else:
                    if entry['kind'] == 'availability':
                        event = events.get(entry['event'])
                        if not event or 'query' not in event:
                            target.mkdir(parents=True)
                            common.atomic(target / 'status.json', {'state': 'not_queried', 'reason': 'event_identity_unavailable'})
                            states[entry['sequence']] = 'not_queried'
                            continue
                        due = event['origin_monotonic_raw'] + entry['nominal_delay_s']
                        while common.clock() < due and not common.INTERRUPTED and common.clock() < end - RESERVE - 2:
                            time.sleep(min(.05, due - common.clock()))
                        if common.INTERRUPTED or common.clock() >= end - RESERVE - 2:
                            run_info['stop_reason'] = 'interrupt' if common.INTERRUPTED else 'ceiling'
                            break
                        metadata.update(query=event['query'], origin_monotonic_raw=event['origin_monotonic_raw'],
                                        target_monotonic_raw=due)
                    query = metadata['query']
                    argv = observer_argv(query) if entry['method'] == 'observer' else direct_argv(query)
                    timeout, limit = (12, 32 * 1024 * 1024) if entry['method'] == 'observer' else (9, 1024 * 1024)
                effective = min(timeout, end - RESERVE - 1 - common.clock())
                metadata['timeout_source'] = 'nominal' if effective == timeout else 'ceiling'
                status = capture(target, argv, effective, {'stdout': limit, 'stderr': 128 * 1024}, metadata)
                states[entry['sequence']] = status['state']
                if entry['kind'] == 'specimen':
                    event = {'execution': entry['directory'], 'origin_monotonic_raw': status.get('wait4_monotonic_raw')}
                    try:
                        if status['state'] != 'completed' or event['origin_monotonic_raw'] is None:
                            raise ValueError('execution did not complete')
                        envelope = json.loads((target / 'stdout.bin').read_bytes())
                        event.update(query=event_query(envelope), execution_result=envelope['result'])
                    except (KeyError, ValueError, TypeError) as exc:
                        event['error'] = repr(exc)
                    events[entry['event']] = event
                    common.atomic(target / 'event.json', event)
                if status['cleanup'] not in ('group_absent', 'not_started'):
                    run_info['stop_reason'] = 'cleanup_unconfirmed'
                    break
        except Exception as exc:
            run_info.update(stop_reason='harness_error', error=repr(exc))
        finally:
            if common.INTERRUPTED:
                run_info['stop_reason'] = 'interrupt'
            for entry in entries:
                if entry['sequence'] not in states:
                    target = directory / entry['directory']
                    if (target / 'status.json').exists():
                        states[entry['sequence']] = json.loads((target / 'status.json').read_text())['state']
                    else:
                        target.mkdir(parents=True, exist_ok=True)
                        state = 'unresolved' if (target / 'request.json').exists() else 'never_started'
                        common.atomic(target / 'status.json', {'state': state, 'reason': run_info['stop_reason']})
                        states[entry['sequence']] = state
            run_info.update(counts=dict(collections.Counter(states.values())), planned=len(entries),
                            loop_ended_at=common.utc(), interrupt=common.INTERRUPTED)
            result = common.finalize(directory, run_info, assertion, assertion_record, end, RESERVE, 0)
        print(json.dumps({'raw_output': str(directory.relative_to(ROOT)), 'exit_status': result,
                          'stop_reason': run_info['stop_reason']}))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'describe', 'run'))
    parser.add_argument('--run-id')
    parser.add_argument('--note', default='')
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise ValueError('launch from repository root')
    if args.action == 'prepare':
        prepare()
        return 0
    if args.action == 'describe':
        print(json.dumps(schedule(json.loads(CONFIG.read_text())), indent=2))
        return 0
    return run(args)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f'REFUSED: {exc}' if ACTIVE_RUN is None else f'INCOMPLETE: {ACTIVE_RUN}: {exc}', file=sys.stderr)
        sys.exit(2 if ACTIVE_RUN is None else 3)
