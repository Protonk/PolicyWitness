#!/usr/bin/env python3
"""Bounded schedule of late-publication cases against the shipped worker.

Fixture units run LatePublicationProbe through the runner's internal driver.
CLI units run `policy-witness run` with `_test_overrides.worker_timeout_ms`
(and the post-apply hang where the case needs it) against an owned FIFO or
file; a harness thread releases the FIFO at a fixed delay after the
controller's spawn. Each unit keeps argv, stdout, stderr, status and clocks,
then checks that no process running the worker executable remains and removes
its owned FIFO. No application binary, setting or signature is changed.
"""
import argparse
import ctypes
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import random
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
CHILD_ENV = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
             'HOME': pwd.getpwuid(os.getuid()).pw_dir, 'LANG': 'C', 'LC_ALL': 'C'}
APP = ROOT / 'dist/PolicyWitness.app'
WORKER = APP / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
FIXTURE = ROOT / '.tmp/late-publication-build/out/Products/Debug/LatePublicationProbe'
SENTINEL_MS = 400
HOLD_MS = 50
# Fixture cases: target and the fixture options that produce them.
FIXTURE_CASES = {
    'timely': ['--target', 'fifo', '--unblock-after-release-ms', '100'],
    'late-done': ['--target', 'file', '--hang-ms', '800'],
    'late-slot': ['--target', 'fifo', '--unblock-after-grace-entry-ms', '400'],
    'grace-exhausted': ['--target', 'fifo'],
}
# CLI cases: target, post-apply hang, FIFO release delay after controller spawn.
CLI_CASES = {
    'cli-timely': ('fifo', None, 150),
    'cli-late-done': ('file', 800, None),
    'cli-late-slot': ('fifo', None, 950),
    'cli-grace-exhausted': ('fifo', None, None),
}
FIXTURE_REPEATS = 3
STOP = None


def now():
    return {'mono_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW), 'wall_ns': time.time_ns()}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with open(path, 'x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def probe(argv, timeout=10):
    try:
        out = subprocess.run(argv, env=CHILD_ENV, stdin=subprocess.DEVNULL, capture_output=True,
                             timeout=timeout, cwd=ROOT)
        return {'argv': argv, 'exit': out.returncode, 'stdout': out.stdout.decode(errors='replace')[:20000],
                'stderr': out.stderr.decode(errors='replace')[-4000:]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'argv': argv, 'error': repr(error)}


def conditions():
    return {'at': now(), 'probes': [
        probe(['/usr/bin/sw_vers']),
        probe(['/usr/sbin/sysctl', 'hw.model', 'hw.ncpu', 'hw.memsize', 'vm.loadavg']),
        probe(['/usr/bin/pmset', '-g', 'batt']),
        probe(['/bin/ps', '-axo', 'pid,ppid,%cpu,comm', '-r']),
    ]}


class BsdInfo(ctypes.Structure):
    _fields_ = [('pbi_flags', ctypes.c_uint32), ('pbi_status', ctypes.c_uint32),
                ('pbi_xstatus', ctypes.c_uint32), ('pbi_pid', ctypes.c_uint32),
                ('pbi_ppid', ctypes.c_uint32), ('pbi_uid', ctypes.c_uint32), ('pbi_gid', ctypes.c_uint32),
                ('pbi_ruid', ctypes.c_uint32), ('pbi_rgid', ctypes.c_uint32), ('pbi_svuid', ctypes.c_uint32),
                ('pbi_svgid', ctypes.c_uint32), ('rfu_1', ctypes.c_uint32), ('pbi_comm', ctypes.c_char * 16),
                ('pbi_name', ctypes.c_char * 32), ('pbi_nfiles', ctypes.c_uint32), ('pbi_pgid', ctypes.c_uint32),
                ('pbi_pjobc', ctypes.c_uint32), ('e_tdev', ctypes.c_uint32), ('e_tpgid', ctypes.c_uint32),
                ('pbi_nice', ctypes.c_int32), ('pbi_start_tvsec', ctypes.c_uint64),
                ('pbi_start_tvusec', ctypes.c_uint64)]


LIBC = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
PIDS = (ctypes.c_int * 16384)()


def processes_with_path(path):
    count = LIBC.proc_listallpids(PIDS, ctypes.sizeof(PIDS))
    found, buffer = [], ctypes.create_string_buffer(4096)
    for pid in PIDS[:max(count, 0)]:
        if LIBC.proc_pidpath(pid, buffer, 4096) <= 0 or os.fsdecode(buffer.value) != str(path):
            continue
        info = BsdInfo()
        if LIBC.proc_pidinfo(pid, 3, ctypes.c_uint64(0), ctypes.byref(info), ctypes.sizeof(info)) == ctypes.sizeof(info):
            found.append({'pid': pid, 'ppid': info.pbi_ppid,
                          'start_wall_us': info.pbi_start_tvsec * 1_000_000 + info.pbi_start_tvusec})
    return found


def interrupt(signum, frame):
    global STOP
    STOP = {'signal': signum, 'at': now()}


def supervise(argv, unit_dir, deadline_s, status):
    with open(unit_dir / 'stdout.txt', 'xb') as out, open(unit_dir / 'stderr.txt', 'xb') as err:
        status['start'] = now()
        process = subprocess.Popen(argv, env=CHILD_ENV, stdin=subprocess.DEVNULL, stdout=out, stderr=err, cwd=ROOT)
        status['pid'] = process.pid
        try:
            status['exit'] = process.wait(timeout=deadline_s)
            status['state'] = 'exited'
        except subprocess.TimeoutExpired:
            process.send_signal(signal.SIGTERM)
            status['sigterm'] = now()
            try:
                status['exit'] = process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                status['sigkill'] = now()
                status['exit'] = process.wait(timeout=5)
            status['state'] = 'deadline'
        status['end'] = now()


def fifo_release(path, due_mono_ns, record):
    """Open the FIFO's write end without blocking at the due time, write one byte, close."""
    while True:
        remaining = due_mono_ns - time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
        if remaining <= 0:
            break
        time.sleep(min(remaining / 1e9, 0.05))
    record['open_start_ns'] = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
    except OSError as error:
        record.update({'open_errno': error.errno, 'open_end_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)})
        return
    record['open_end_ns'] = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    record['write_rc'] = os.write(fd, b'x')
    os.close(fd)
    record['close_end_ns'] = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)


def run_fixture_unit(fixture, unit_dir, case, deadline_s):
    work = unit_dir / 'work'
    work.mkdir()
    argv = [str(fixture), '--worker', str(WORKER), '--work-dir', str(work), '--out', str(unit_dir / 'fixture.json'),
            '--label', case, '--sentinel-ms', str(SENTINEL_MS), '--hold-ms', str(HOLD_MS), *FIXTURE_CASES[case]]
    status = {'kind': 'fixture', 'case': case, 'argv': argv, 'state': 'started'}
    supervise(argv, unit_dir, deadline_s, status)
    return status


def run_cli_unit(unit_dir, case, deadline_s):
    target_kind, hang, release_ms = CLI_CASES[case]
    work = unit_dir / 'work'
    work.mkdir()
    target = work / ('attempt.fifo' if target_kind == 'fifo' else 'attempt.file')
    if target_kind == 'fifo':
        os.mkfifo(target, 0o600)
    else:
        target.write_bytes(b'late-publication')
    overrides = {'worker_timeout_ms': SENTINEL_MS}
    if hang:
        overrides['worker_post_apply_hang_ms'] = hang
    request = {'schema_version': 5, 'specimen_id': case,
               'policy': {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default) (deny mach-lookup)'},
               'probe_plan': [{'step_id': 'r1',
                               'sandbox_check': {'operation': 'file-read-data',
                                                 'filter': {'kind': 'path', 'value': str(target)}},
                               'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(target)}}],
               '_test_overrides': overrides}
    write_json(unit_dir / 'request.json', request)
    argv = [str(APP / 'Contents/MacOS/policy-witness'), 'run', str(unit_dir / 'request.json')]
    status = {'kind': 'cli', 'case': case, 'argv': argv, 'state': 'started', 'target': str(target),
              'fifo_release_after_spawn_ms': release_ms}
    release = {}
    thread = None
    if release_ms is not None:
        due = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) + release_ms * 1_000_000
        release['due_ns'] = due
        thread = threading.Thread(target=fifo_release, args=(target, due, release), daemon=True)
        thread.start()
    supervise(argv, unit_dir, deadline_s, status)
    if thread is not None:
        thread.join(timeout=5)
    status['fifo_release'] = release or None
    status['target_existed_after_run'] = target.exists()
    target.unlink(missing_ok=True)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--fixture', type=Path, default=FIXTURE)
    parser.add_argument('--out', type=Path, default=ROOT / 'records/performance/runs')
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--gap-s', type=float, default=1.0)
    parser.add_argument('--unit-deadline-s', type=float, default=15.0)
    parser.add_argument('--ceiling-s', type=float, default=240.0)
    parser.add_argument('--fixture-repeats', type=int, default=FIXTURE_REPEATS)
    parser.add_argument('--no-cli', action='store_true')
    args = parser.parse_args()
    entry = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    fixture = args.fixture.resolve()
    if not fixture.is_file() or not WORKER.is_file():
        print(f'refused: missing fixture {fixture} or worker {WORKER}', file=sys.stderr)
        return 2
    if processes_with_path(WORKER):
        print('refused: a process is already running the worker executable', file=sys.stderr)
        return 2
    lock = os.open(ROOT / 'tests/.checkout.lock', os.O_RDWR)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('refused: tests/.checkout.lock is held', file=sys.stderr)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_dir = args.out / f'{stamp}-latepub-{args.label}'
    run_dir.mkdir(parents=True, exist_ok=False)
    print(run_dir, flush=True)
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    units = [case for case in FIXTURE_CASES for _ in range(args.fixture_repeats)]
    if not args.no_cli:
        units += list(CLI_CASES)
    random.Random(args.seed).shuffle(units)
    run = {'format': 1, 'argv': [sys.executable, *sys.argv], 'python': sys.version,
           'harness_sha256': sha256(__file__), 'seed': args.seed, 'schedule': units,
           'settings': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
           'sentinel_ms': SENTINEL_MS, 'hold_ms': HOLD_MS, 'fixture_cases': FIXTURE_CASES,
           'cli_cases': CLI_CASES, 'child_env': CHILD_ENV,
           'identity': {'fixture_sha256': sha256(fixture), 'worker_sha256': sha256(WORKER),
                        'source_sha256': {p.name: sha256(p) for p in sorted(Path(__file__).parent.rglob('*'))
                                          if p.is_file() and p.suffix in ('.swift', '.py')},
                        'probes': [probe([str(APP / 'Contents/MacOS/policy-witness'), '--version']),
                                   probe(['/usr/bin/git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
                                   probe(['/usr/bin/git', '-C', str(ROOT), 'status', '--porcelain'])]},
           'started': now(), 'conditions_start': conditions()}
    statuses, stop_reason = [], 'completed'
    for sequence, case in enumerate(units):
        if STOP is not None:
            stop_reason = 'interrupted'
            break
        if (time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) - entry) / 1e9 + args.unit_deadline_s + args.gap_s \
                > args.ceiling_s:
            stop_reason = 'ceiling'
            break
        time.sleep(args.gap_s)
        unit_dir = run_dir / 'units' / f'{sequence:03d}-{case}'
        unit_dir.mkdir(parents=True)
        if case in FIXTURE_CASES:
            status = run_fixture_unit(fixture, unit_dir, case, args.unit_deadline_s)
        else:
            status = run_cli_unit(unit_dir, case, args.unit_deadline_s)
        status['sequence'] = sequence
        status['worker_processes_after_unit'] = processes_with_path(WORKER)
        write_json(unit_dir / 'status.json', status)
        statuses.append(status)
        if status['worker_processes_after_unit']:
            stop_reason = 'worker_survived_unit'
            break
    run.update({'stop_reason': stop_reason, 'interrupt': STOP, 'units_run': len(statuses),
                'never_started': units[len(statuses):], 'ended': now(),
                'worker_processes_after': processes_with_path(WORKER), 'conditions_end': conditions()})
    write_json(run_dir / 'run.json', run)
    sums = [f'{sha256(p)}  {p.relative_to(run_dir)}\n' for p in sorted(run_dir.rglob('*')) if p.is_file()]
    (run_dir / 'SHA256SUMS').write_text(''.join(sums))
    os.close(lock)
    unclean = sum(s['state'] != 'exited' for s in statuses)
    print(f'{stop_reason}: {len(statuses)} of {len(units)} units, {unclean} past deadline', flush=True)
    return 0 if stop_reason == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
