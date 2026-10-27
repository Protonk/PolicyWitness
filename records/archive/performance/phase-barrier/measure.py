#!/usr/bin/env python3
"""Bounded schedule of phase-barrier fixture runs against the shipped worker.

Each unit runs the PhaseBarrierProbe fixture once in a fresh work directory and
retains its argv, stdout, stderr, exit status, harness clocks and the fixture's
JSON record. After each unit the worker generation the fixture identified is
checked for absence. No application binary, setting or signature is changed.
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
import time

ROOT = Path(__file__).resolve().parents[3]
CHILD_ENV = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
             'HOME': pwd.getpwuid(os.getuid()).pw_dir, 'LANG': 'C', 'LC_ALL': 'C'}
WORKER = ROOT / 'dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
FIXTURE = ROOT / '.tmp/phase-barrier-build/out/Products/Debug/PhaseBarrierProbe'
# Condition: (hold ms, worker proceed allowance ms or None, sampling mode).
CONDITIONS = {
    'hold0-boundary': (0, None, 'boundary'),
    'hold200-boundary': (200, None, 'boundary'),
    'hold800-boundary': (800, None, 'boundary'),
    'hold200-dense': (200, None, 'dense'),
    'hold800-dense': (800, None, 'dense'),
    'hold200-none': (200, None, 'none'),
    'hold800-none': (800, None, 'none'),
    'deadline250-hold400-boundary': (400, 250, 'boundary'),
}
# Rounds per plan; each round runs its conditions in a recorded shuffled order.
PLANS = {
    'pilot': {'rounds': 1, 'per_round': list(CONDITIONS)},
    'measure': {'rounds': 5, 'per_round': list(CONDITIONS),
                'only_first_rounds': {'hold200-dense': 3, 'hold800-dense': 3, 'hold200-none': 3,
                                      'hold800-none': 3, 'deadline250-hold400-boundary': 3}},
}
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
        probe(['/usr/sbin/sysctl', 'hw.model', 'hw.ncpu', 'hw.perflevel0.logicalcpu',
               'hw.perflevel1.logicalcpu', 'hw.memsize', 'kern.boottime', 'vm.loadavg']),
        probe(['/usr/bin/pmset', '-g', 'batt']),
        probe(['/usr/bin/pmset', '-g', 'therm']),
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
    """Live processes whose executable is `path`, with PID, parent and creation time."""
    count = LIBC.proc_listallpids(PIDS, ctypes.sizeof(PIDS))
    found = []
    buffer = ctypes.create_string_buffer(4096)
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


def schedule(plan, seed):
    spec = PLANS[plan]
    rng = random.Random(seed)
    units = []
    for round_index in range(spec['rounds']):
        names = [n for n in spec['per_round']
                 if round_index < spec.get('only_first_rounds', {}).get(n, spec['rounds'])]
        rng.shuffle(names)
        units.extend({'round': round_index, 'condition': n} for n in names)
    return units


def run_unit(fixture, worker, run_dir, sequence, unit, deadline_s):
    hold, proceed, sampling = CONDITIONS[unit['condition']]
    unit_dir = run_dir / 'units' / f'{sequence:03d}-{unit["condition"]}'
    work = unit_dir / 'work'
    work.mkdir(parents=True)
    record_path = unit_dir / 'fixture.json'
    argv = [str(fixture), '--worker', str(worker), '--work-dir', str(work), '--out', str(record_path),
            '--condition', unit['condition'], '--hold-ms', str(hold), '--sampling', sampling]
    if proceed is not None:
        argv += ['--proceed-wait-ms', str(proceed)]
    status = {'sequence': sequence, **unit, 'argv': argv, 'state': 'started'}
    with open(unit_dir / 'stdout.txt', 'xb') as out, open(unit_dir / 'stderr.txt', 'xb') as err:
        status['start'] = now()
        process = subprocess.Popen(argv, env=CHILD_ENV, stdin=subprocess.DEVNULL, stdout=out, stderr=err, cwd=ROOT)
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
    # The worker generation the fixture identified must be gone.
    identity = None
    try:
        identity = json.loads(record_path.read_text())['hook']['worker_identity_entry']
    except (OSError, ValueError, KeyError) as error:
        status['identity_error'] = repr(error)
    survivors = processes_with_path(worker)
    status['worker_identity'] = identity
    status['worker_processes_after_unit'] = survivors
    status['identified_worker_survived'] = bool(identity) and any(
        s['pid'] == identity['pid'] and s['start_wall_us'] == identity['start_wall_us'] for s in survivors)
    write_json(unit_dir / 'status.json', status)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, choices=sorted(PLANS))
    parser.add_argument('--label', required=True)
    parser.add_argument('--fixture', type=Path, default=FIXTURE)
    parser.add_argument('--worker', type=Path, default=WORKER)
    parser.add_argument('--out', type=Path, default=ROOT / 'records/performance/runs')
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--gap-s', type=float, default=1.0)
    parser.add_argument('--unit-deadline-s', type=float, default=20.0)
    parser.add_argument('--ceiling-s', type=float, default=300.0)
    args = parser.parse_args()
    entry = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    fixture, worker = args.fixture.resolve(), args.worker.resolve()
    if not fixture.is_file() or not worker.is_file():
        print(f'refused: missing fixture {fixture} or worker {worker}', file=sys.stderr)
        return 2
    lock = os.open(ROOT / 'tests/.checkout.lock', os.O_RDWR)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('refused: tests/.checkout.lock is held', file=sys.stderr)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_dir = args.out / f'{stamp}-phasebarrier-{args.label}'
    run_dir.mkdir(parents=True, exist_ok=False)
    print(run_dir, flush=True)
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    units = schedule(args.plan, args.seed)
    app = ROOT / 'dist/PolicyWitness.app'
    run = {'format': 1, 'argv': [sys.executable, *sys.argv], 'python': sys.version,
           'harness_sha256': sha256(__file__), 'plan': args.plan, 'seed': args.seed,
           'settings': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
           'conditions_table': CONDITIONS, 'schedule': units, 'child_env': CHILD_ENV,
           'identity': {'fixture_sha256': sha256(fixture), 'worker_sha256': sha256(worker),
                        'fixture_source_sha256': {p.name: sha256(p) for p in
                                                  sorted((Path(__file__).parent).rglob('*'))
                                                  if p.is_file() and p.suffix in ('.swift', '.py')},
                        'probes': [probe([str(app / 'Contents/MacOS/policy-witness'), '--version']),
                                   probe(['/usr/bin/codesign', '-dvvv', str(worker)]),
                                   probe(['/usr/bin/git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
                                   probe(['/usr/bin/git', '-C', str(ROOT), 'status', '--porcelain'])]},
           'worker_processes_before': processes_with_path(worker),
           'started': now(), 'conditions_start': conditions()}
    statuses, stop_reason = [], 'completed'
    for sequence, unit in enumerate(units):
        if STOP is not None:
            stop_reason = 'interrupted'
            break
        elapsed = (time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) - entry) / 1e9
        if elapsed + args.unit_deadline_s + args.gap_s > args.ceiling_s:
            stop_reason = 'ceiling'
            break
        time.sleep(args.gap_s)
        statuses.append(run_unit(fixture, worker, run_dir, sequence, unit, args.unit_deadline_s))
    run.update({'stop_reason': stop_reason, 'interrupt': STOP, 'units_run': len(statuses),
                'never_started': [u for u in units[len(statuses):]], 'ended': now(),
                'worker_processes_after': processes_with_path(worker), 'conditions_end': conditions()})
    write_json(run_dir / 'run.json', run)
    sums = [f'{sha256(p)}  {p.relative_to(run_dir)}\n' for p in sorted(run_dir.rglob('*')) if p.is_file()]
    (run_dir / 'SHA256SUMS').write_text(''.join(sums))
    os.close(lock)
    failed = sum(s['state'] != 'exited' or s.get('exit') != 0 for s in statuses)
    print(f'{stop_reason}: {len(statuses)} of {len(units)} units, {failed} not clean', flush=True)
    return 0 if stop_reason == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
