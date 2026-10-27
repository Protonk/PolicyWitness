#!/usr/bin/env python3
"""Bounded, standalone runtime observations. No application code is modified."""
import argparse
import collections
import contextlib
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import select
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FIXTURES = ('file_read_deny', 'mach_deny', 'sysctl_read', 'exec_spawn',
            'path_diagnostics_strict')
CHILD_ENV = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
             'HOME': pwd.getpwuid(os.getuid()).pw_dir, 'LANG': 'C', 'LC_ALL': 'C'}
INTERRUPTED = None
RUN_DIRECTORY = None


def clock():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) / 1e9


def clocks():
    return {'monotonic_raw_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW),
            'uptime_raw_ns': time.clock_gettime_ns(time.CLOCK_UPTIME_RAW)}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def atomic(path, value):
    data = encode(value)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
    temporary.replace(path)
    return data


def digest(path, deadline=math.inf):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            if clock() >= deadline:
                raise TimeoutError('checksum deadline')
            block = stream.read(1024 * 1024)
            if not block:
                return h.hexdigest()
            h.update(block)


def interrupt(signum, frame):
    global INTERRUPTED
    if INTERRUPTED is None:
        INTERRUPTED = {'signal': signum, 'at': utc(), 'monotonic_raw': clock()}


def probe(argv, deadline, timeout=2):
    remaining = min(timeout, deadline - clock())
    result = {'argv': argv, 'state': 'timed_out'}
    if remaining <= 0:
        result['error'] = 'probe set deadline exhausted before launch'
        return result
    started = clock()
    try:
        output = subprocess.run(argv, cwd=ROOT, env=CHILD_ENV, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=remaining, check=False)
        result.update(state='ok' if output.returncode == 0 else 'failed',
                      exit_code=output.returncode,
                      stdout=output.stdout.decode('utf-8', 'replace'),
                      stderr=output.stderr.decode('utf-8', 'replace'))
    except subprocess.TimeoutExpired as exc:
        result.update(stdout=(exc.stdout or b'').decode('utf-8', 'replace'),
                      stderr=(exc.stderr or b'').decode('utf-8', 'replace'))
    except OSError as exc:
        result.update(state='failed', error=str(exc))
    result['elapsed_s'] = clock() - started
    return result


def conditions(deadline, delay=0):
    # comm, rather than full process arguments, avoids recording unrelated secrets.
    commands = {
        'os': ['/usr/bin/sw_vers'], 'architecture': ['/usr/bin/uname', '-m'],
        'hardware': ['/usr/sbin/sysctl', 'hw.model', 'hw.ncpu', 'hw.memsize'],
        'power': ['/usr/bin/pmset', '-g', 'batt'],
        'thermal': ['/usr/bin/pmset', '-g', 'therm'],
        'git_head': ['/usr/bin/git', 'rev-parse', 'HEAD'],
        'git_status': ['/usr/bin/git', 'status', '--porcelain'],
        'process_names': ['/bin/ps', '-axo', 'pid=,comm='],
    }
    if delay:
        commands = {'delayed_control': [sys.executable, '-B', '-S', '-c',
                                       f'import time; time.sleep({delay!r})'], **commands}
    result = {'observed_at': utc(), 'probes': {}}
    for key, argv in commands.items():
        result['probes'][key] = probe(argv, deadline)
    thermal = result['probes']['thermal']
    if thermal['state'] == 'ok' and 'Error:' in thermal.get('stdout', ''):
        thermal['state'] = 'failed'
        thermal['error'] = 'pmset returned zero but reported unavailable thermal/power observations'
    processes = result['probes']['process_names']
    names = processes.get('stdout', '')
    result['background_servers'] = {
        'codex_daemon_matches': [line.strip() for line in names.splitlines()
                                 if 'app-server-daemon' in line],
        'other_app_server_matches': [line.strip() for line in names.splitlines()
                                     if 'app-server' in line and 'app-server-daemon' not in line],
        'inspection_state': processes['state'],
        'custom_server_identity': 'not supplied; broad app-server name match only',
    }
    # Retain all executable names so an unknown custom server can be identified later.
    return result


def app_identity(pw, version, deadline):
    value = {'version': version, 'executable': str(pw), 'files': {str(pw): digest(pw, deadline)}}
    app = pw.parents[2]
    manifest = app / 'Contents/Resources/Evidence/manifest.json'
    if manifest.is_file():
        value['files'][str(manifest)] = digest(manifest, deadline)
        inventory = json.loads(manifest.read_text())
        for entry in inventory['entries']:
            path = app / entry['rel_path']
            actual = digest(path, deadline)
            if actual != entry['sha256']:
                raise ValueError(f'app manifest mismatch: {path}')
            value['files'][str(path)] = actual
    return value


def cells():
    # Keep no-capture cells contiguous to exercise ordinary consecutive use.
    return [(specimen, capture) for capture in (True, False) for specimen in FIXTURES] + [(None, False)]


def make_entries(run_dir, pw, config, rounds):
    entries = []

    def add(specimen, capture, warmup, round_number, pair=None):
        seq = len(entries) + 1
        request = run_dir / 'specimens' / f'{specimen}.json' if specimen else None
        argv = [str(pw), 'run', str(request)] if request else [str(pw), '--version']
        if request and not capture:
            argv.append('--no-log-capture')
        entries.append({'sequence': seq, 'cell': f'{specimen}/{"capture" if capture else "no-capture"}'
                        if specimen else 'version', 'specimen': specimen, 'capture': capture,
                        'specimen_sha256': digest(request) if request else None,
                        'argv': argv, 'warmup': warmup, 'round': round_number, 'pair': pair,
                        'directory': f'invocations/{seq:05d}'})

    if config == 'overlap':
        for pair in range(1, 11):
            for _ in range(2):
                add('sysctl_read', False, False, pair, pair)
    else:
        if config == 'pilot':
            for round_number in range(1, 4):
                for specimen in FIXTURES:
                    add(specimen, True, True, round_number)
        for round_number in range(1, rounds + 1):
            for specimen, capture in cells():
                add(specimen, capture, False, round_number)
    return entries


def launch(entry, run_dir, nominal, work_deadline, event_queue):
    directory = run_dir / entry['directory']
    directory.mkdir(parents=True)
    atomic(directory / 'argv.json', entry['argv'])
    out = (directory / 'stdout.json').open('xb')
    err = (directory / 'stderr.txt').open('xb')
    before = clocks()
    start = before['monotonic_raw_ns'] / 1e9
    effective = min(nominal, max(0, work_deadline - start))
    status = {'sequence': entry['sequence'], 'state': 'running', 'started_at': utc(),
              'clocks_start': before, 'effective_deadline_s': effective,
              'deadline_source': 'nominal' if nominal <= work_deadline - start else 'ceiling',
              'signals': [], 'exit_status': None, 'term_signal': None,
              'wait_method': 'kqueue_proc_exit', 'descendant_cleanup':
              'Only controller managed; XPC service tree retains its own budgets.'}
    job = {'entry': entry, 'directory': directory, 'status': status, 'out': out, 'err': err,
           'deadline': start + effective, 'term_at': None, 'kill_at': None, 'process': None}
    try:
        process = subprocess.Popen(entry['argv'], stdin=subprocess.DEVNULL, stdout=out,
                                   stderr=err, close_fds=True, start_new_session=True,
                                   cwd=ROOT, env=CHILD_ENV)
        job['process'] = process
        status['pid'] = process.pid
        try:
            event_queue.control([select.kevent(process.pid, filter=select.KQ_FILTER_PROC,
                                               flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                               fflags=select.KQ_NOTE_EXIT)], 0, 0)
        except OSError as exc:
            # Fast exit can precede registration. wait4 remains authoritative.
            status['event_registration_error'] = str(exc)
            status['wait_method'] = 'wait4_nonblocking_fallback'
    except OSError as exc:
        status.update(state='spawn_failed', error=str(exc))
        finish(job, None, None)
    return job


def finish(job, raw_status, usage):
    status, directory = job['status'], job['directory']
    after = clocks()
    before = status['clocks_start']
    wall = after['monotonic_raw_ns'] - before['monotonic_raw_ns']
    uptime = after['uptime_raw_ns'] - before['uptime_raw_ns']
    gap = wall - uptime
    status.update(ended_at=utc(), clocks_end=after, wall_ms=wall / 1e6, uptime_ms=uptime / 1e6,
                  system_sleep_ms=max(0, gap) // 1_000_000 if gap > -1_000_000 else None,
                  sleep_clock_error=None if gap > -1_000_000 else 'uptime exceeded continuous clock',
                  sleep_detected=gap >= 1_000_000, rusage=None)
    if raw_status is not None:
        rc = os.waitstatus_to_exitcode(raw_status)
        job['process'].returncode = rc
        status.update(wait_status=raw_status, exit_status=rc if rc >= 0 else None,
                      term_signal=-rc if rc < 0 else None)
    if usage is not None:
        status['rusage'] = {name: getattr(usage, name) for name in
                            ('ru_utime', 'ru_stime', 'ru_maxrss', 'ru_minflt', 'ru_majflt',
                             'ru_inblock', 'ru_oublock', 'ru_nvcsw', 'ru_nivcsw')}
    if status['state'] == 'running':
        status['state'] = 'completed'
    job['out'].close()
    job['err'].close()
    status['stdout_bytes'] = (directory / 'stdout.json').stat().st_size
    status['stderr_bytes'] = (directory / 'stderr.txt').stat().st_size
    atomic(directory / 'status.json', status)


def signal_job(job, signum):
    observation = {'signal': signum, 'monotonic_raw': clock(), 'at': utc()}
    try:
        os.kill(job['process'].pid, signum)
        observation['result'] = 'sent'
    except OSError as exc:
        observation.update(result='failed', errno=exc.errno, error=str(exc))
    job['status']['signals'].append(observation)


def run_group(entries, directory, nominal, work_deadline):
    with contextlib.closing(select.kqueue()) as events:
        jobs = [launch(entry, directory, nominal, work_deadline, events) for entry in entries]
        active = [job for job in jobs if job['process'] is not None]
        while active:
            for job in list(active):
                pid, status, usage = os.wait4(job['process'].pid, os.WNOHANG)
                if pid:
                    finish(job, status, usage)
                    active.remove(job)
                    continue
                now = clock()
                if job['term_at'] is None and (INTERRUPTED or now >= job['deadline']):
                    job['status']['state'] = 'interrupted' if INTERRUPTED else 'harness_timeout'
                    job['status']['interrupt'] = INTERRUPTED
                    signal_job(job, signal.SIGTERM)
                    job['term_at'] = now
                if job['term_at'] is not None and job['kill_at'] is None and now >= job['term_at'] + 2:
                    signal_job(job, signal.SIGKILL)
                    job['kill_at'] = now
                if job['kill_at'] is not None and now >= job['kill_at'] + 1:
                    job['status']['unreaped_after_sigkill'] = True
                    # Retain terminal evidence and let the OS finish disposal; never block forever.
                    finish(job, None, None)
                    active.remove(job)
            if active:
                fallback = any('event_registration_error' in j['status'] for j in active)
                try:
                    events.control(None, len(active), 0.001 if fallback else 0.05)
                except InterruptedError:
                    pass
                except OSError as exc:
                    for job in active:
                        job['status']['event_registration_error'] = str(exc)
                        job['status']['wait_method'] = 'wait4_nonblocking_fallback'
                    time.sleep(.001)
    return [job['status'] for job in jobs]


def finalize(run_dir, run, assertion, assertion_record, hard_end, reserve, delay):
    start = clock()
    # A small final-write allowance is inside both the reserve and the total ceiling.
    end = min(hard_end, start + reserve) - 0.15
    run['cleanup'] = {'state': 'started', 'started_at': utc(), 'reserve_s': reserve}
    atomic(run_dir / 'run.json', run)
    steps = {}
    end_conditions = conditions(min(end, clock() + 5), delay) if clock() < end else None
    if end_conditions is not None:
        atomic(run_dir / 'conditions-end.json', end_conditions)
        timed_out = any(p['state'] == 'timed_out' for p in end_conditions['probes'].values())
        steps['conditions'] = 'incomplete' if timed_out else 'complete'
    else:
        steps['conditions'] = 'skipped'
    if assertion is not None and clock() < end:
        assertion_record['running_at_end'] = assertion.poll() is None
        if assertion.returncode is None:
            assertion.terminate()
            try:
                assertion.wait(timeout=max(0.001, min(0.3, end - clock())))
            except subprocess.TimeoutExpired:
                assertion.kill()
                try:
                    assertion.wait(timeout=max(0.001, min(0.2, end - clock())))
                except subprocess.TimeoutExpired:
                    assertion_record['release_unconfirmed'] = True
        assertion_record['exit_status'] = assertion.returncode
        steps['assertion'] = 'incomplete' if assertion.returncode is None else 'complete'
    elif assertion is None:
        steps['assertion'] = 'inapplicable'
    else:
        steps['assertion'] = 'skipped; caffeinate -w ends when harness exits'
    run['idle_sleep_assertion'] = assertion_record
    files = sorted(p for p in run_dir.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS', 'run.json'))
    hashed = 0
    checksum_path = run_dir / 'SHA256SUMS'
    with checksum_path.open('x') as stream:
        for path in files:
            try:
                value = digest(path, end)
            except TimeoutError:
                break
            stream.write(f'{value}  {path.relative_to(run_dir).as_posix()}\n')
            stream.flush()
            hashed += 1
        steps['checksums'] = 'complete' if hashed == len(files) else 'incomplete'
        complete = all(value in ('complete', 'inapplicable') for value in steps.values())
        code = (0 if run['stop_reason'] == 'manifest_exhausted' else 1) if complete else 3
        run.update(exit_status=code, finished_at=utc(), duration_s=clock() - run['start_monotonic_raw'])
        run['cleanup'].update(state='complete' if complete else 'incomplete', steps=steps,
                              elapsed_s=clock() - start, checksums_hashed=hashed + 1,
                              checksums_total=len(files) + 1,
                              checksum_order='run.json is finalized and hashed last')
        # Hash final bytes, not the provisional run.json. No file attests itself.
        data = atomic(run_dir / 'run.json', run)
        stream.write(f'{hashlib.sha256(data).hexdigest()}  run.json\n')
        stream.flush()
    return code


def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', choices=('pilot', 'short', 'standard', 'overlap', 'control'), default='pilot')
    parser.add_argument('--expect-build', required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'records/performance/runs')
    parser.add_argument('--run-id')
    parser.add_argument('--pw', type=Path, default=ROOT / 'dist/PolicyWitness.app/Contents/MacOS/policy-witness')
    parser.add_argument('--note', default='')
    parser.add_argument('--execution-context', choices=('interactive', 'operator'))
    parser.add_argument('--rounds', type=int)
    parser.add_argument('--ceiling-s', type=float)
    parser.add_argument('--nominal-s', type=float, default=300)
    parser.add_argument('--cleanup-reserve-s', type=float, default=10)
    parser.add_argument('--start-margin-s', type=float, default=5)
    parser.add_argument('--control', choices=('missing-request', 'delayed-cleanup'))
    return parser.parse_args()


def main():
    global RUN_DIRECTORY
    start = clock()
    started_at = utc()
    args = parse()
    if args.execution_context is None:
        args.execution_context = 'operator' if args.config in ('short', 'standard') else 'interactive'
    config_file = HERE / 'configurations.json'
    configurations = json.loads(config_file.read_text()) if config_file.exists() else {}
    config = configurations.get(args.config, {})
    ceiling = args.ceiling_s or {'pilot': 180, 'overlap': 180, 'control': 30, 'short': 600, 'standard': 1800}[args.config]
    rounds = args.rounds if args.rounds is not None else config.get('rounds', 5 if args.config == 'pilot' else 1)
    margin = max(args.start_margin_s, config.get('start_margin_s', 0))
    reserve = args.cleanup_reserve_s
    if not all(math.isfinite(v) and v > 0 for v in (ceiling, args.nominal_s, reserve, margin)) or rounds < 1:
        raise ValueError('bounds must be finite and positive')
    if reserve + margin >= ceiling:
        raise ValueError('ceiling must exceed cleanup reserve plus start margin')
    if args.config in ('short', 'standard') and not config:
        raise ValueError('operator configurations must first be sized from P2')
    if args.config == 'overlap' and args.execution_context != 'interactive':
        raise ValueError('overlap is interactive-only this cycle')
    if args.control and args.config != 'control':
        raise ValueError('controls require --config control')
    if Path.cwd().resolve() != ROOT:
        raise ValueError(f'launch from repository root: {ROOT}')
    pw = args.pw.resolve()
    fixtures = [ROOT / 'tests/fixtures/pw_runner' / f'specimen_{name}.json' for name in FIXTURES]
    if not all(path.is_file() for path in fixtures):
        raise ValueError('missing specimen fixture')
    run_id = args.run_id or f'{datetime.datetime.now(datetime.timezone.utc):%Y%m%dT%H%M%S%fZ}-{args.config}-b{args.expect_build}'
    if Path(run_id).name != run_id or run_id in ('.', '..'):
        raise ValueError('run-id must be one path component')
    run_dir = args.out.resolve() / run_id
    if not run_dir.is_relative_to(ROOT / 'records/performance/runs'):
        raise ValueError('raw evidence must stay under records/performance/runs')
    if run_dir.exists():
        raise ValueError(f'output already exists: {run_dir}')
    # Same persistent inode as builds/tests; never remove it or bypass a holder.
    with (ROOT / 'tests/.checkout.lock').open('a+') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        hard_end = start + ceiling
        version_probe = probe([str(pw), '--version'], min(hard_end - reserve, clock() + 5), 5)
        if version_probe['state'] != 'ok':
            raise ValueError(f'cannot read executable identity: {version_probe}')
        version = json.loads(version_probe['stdout'])
        if str(version.get('build', {}).get('number')) != args.expect_build:
            raise ValueError(f'build mismatch: expected {args.expect_build}, got {version.get("build")}')
        identity = app_identity(pw, version, hard_end - reserve)
        if config.get('expected_files') and identity['files'] != config['expected_files']:
            raise ValueError('app bytes differ from the configuration sizing pilot')
        run_dir.mkdir(parents=True, exist_ok=False)
        RUN_DIRECTORY = run_dir
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, interrupt)
        atomic(run_dir / 'owner.json', {'pid': os.getpid(), 'started_at': started_at,
                                       'clocks': clocks(), 'run_id': run_id, 'cwd': str(Path.cwd()),
                                       'execution_context': args.execution_context})
        (run_dir / 'specimens').mkdir()
        for name, source in zip(FIXTURES, fixtures):
            shutil.copyfile(source, run_dir / 'specimens' / f'{name}.json')
        (run_dir / 'harness').mkdir()
        for source in sorted(HERE.rglob('*.py')) + sorted(HERE.glob('*.json')):
            target = run_dir / 'harness' / source.relative_to(HERE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        entries = make_entries(run_dir, pw, args.config, rounds)
        if args.config == 'control':
            entries = entries[:3]
        manifest = {'format_version': 1, 'run_id': run_id, 'config': args.config, 'entries': entries,
                    'ceiling_s': ceiling, 'nominal_s': args.nominal_s, 'cleanup_reserve_s': reserve,
                    'start_margin_s': margin, 'rounds': rounds, 'identity': identity,
                    'child_environment': CHILD_ENV, 'note': args.note, 'control': args.control,
                    'execution_context': args.execution_context,
                    'warmup_definition': '3 rounds of the 5 capture cells; version preflight is unmeasured',
                    'harness_argv': [sys.executable, *sys.argv], 'python': sys.version}
        atomic(run_dir / 'manifest.json', manifest)
        print(json.dumps({'run_dir': str(run_dir), 'planned': len(entries)}), flush=True)
        assertion_record = {'argv': ['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())], 'launched': False}
        assertion = None
        try:
            assertion = subprocess.Popen(assertion_record['argv'], env=CHILD_ENV,
                                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, start_new_session=True)
            assertion_record.update(launched=True, pid=assertion.pid)
        except OSError as exc:
            assertion_record['error'] = str(exc)
        initial = conditions(min(hard_end - reserve, clock() + 5))
        initial.update(version_probe=version_probe, idle_sleep_assertion=dict(assertion_record))
        atomic(run_dir / 'conditions-start.json', initial)
        statuses = []
        stop = 'manifest_exhausted'
        fatal = None
        try:
            if args.control == 'missing-request':
                (run_dir / 'specimens' / f'{entries[0]["specimen"]}.json').unlink()
            width = 2 if args.config == 'overlap' else 1
            for index in range(0, len(entries), width):
                if INTERRUPTED or hard_end - clock() < reserve + margin:
                    stop = 'interrupt' if INTERRUPTED else 'ceiling'
                    break
                statuses.extend(run_group(entries[index:index + width], run_dir, args.nominal_s, hard_end - reserve))
                if any(s.get('unreaped_after_sigkill') for s in statuses[-width:]):
                    stop = 'unreaped_after_sigkill'
                    break
        except Exception as exc:
            stop, fatal = 'harness_error', repr(exc)
        if INTERRUPTED:
            stop = 'interrupt'
        completed = {s['sequence'] for s in statuses}
        for entry in entries:
            if entry['sequence'] not in completed:
                directory = run_dir / entry['directory']
                status_file = directory / 'status.json'
                if status_file.exists():
                    statuses.append(json.loads(status_file.read_text()))
                    continue
                # Do not relabel evidence from a partial launch as never started.
                began = (directory / 'stdout.json').exists()
                directory.mkdir(parents=True, exist_ok=True)
                status = {'sequence': entry['sequence'], 'state': 'unresolved' if began else 'never_started',
                          'reason': stop}
                atomic(directory / 'status.json', status)
                statuses.append(status)
        run = {'format_version': 1, 'run_id': run_id, 'started_at': started_at,
               'start_monotonic_raw': start, 'hard_finish_monotonic_raw': hard_end,
               'loop_ended_at': utc(), 'stop_reason': stop, 'error': fatal, 'interrupt': INTERRUPTED,
               'planned': len(entries), 'counts': dict(collections.Counter(s['state'] for s in statuses)),
               'execution_context': args.execution_context}
        result = finalize(run_dir, run, assertion, assertion_record, hard_end, reserve,
                          10 if args.control == 'delayed-cleanup' else 0)
        print(json.dumps({'run_dir': str(run_dir), 'exit_status': result, 'stop_reason': stop}), flush=True)
        return result


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, TimeoutError) as exc:
        if RUN_DIRECTORY is None:
            print(f'REFUSED: {exc}', file=sys.stderr)
            sys.exit(2)
        print(f'INCOMPLETE: {RUN_DIRECTORY}: {exc}', file=sys.stderr)
        sys.exit(3)
