#!/usr/bin/env python3
"""Bounded, shuffled schedule for the pre-touch investigation.

Fixture units run pretouch_harness, which prepares the region, varies which
pages are touched before the experimental child applies its policy, and
records the child's post-apply stores through independent observations. Shipped
units run the test harness copies (touch/notouch, deny-default policy version
1/2/3) against the shipped pw-probe-runner. After the schedule the unified log
is read once for kernel sandbox reports naming either executable. Each unit
keeps argv, stdout, stderr, status and clocks, and checks that no process
running either executable remains. No application binary, setting or signature
is changed.
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
APP = ROOT / 'dist/PolicyWitness.app'
WORKER = APP / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
BUILD = ROOT / '.tmp/pretouch-build'
POLICIES = {
    'allow1': '(version 1)\n(allow default)\n',
    'deny1': '(version 1)\n(deny default)\n',
    'deny2': '(version 2)\n(deny default)\n',
    'deny3': '(version 3)\n(deny default)\n',
    'noapply': '(version 1)\n(allow default)\n',   # compiled but never applied
}
TOUCHES = ('none', 'host', 'child', 'both', 'prod')
SINGLE = {'probe_page': 100, 'probe_pages': 1, 'second_map_page': 200}
MANY = {'probe_page': 10, 'probe_pages': 200, 'second_map_page': 215}
MANY_CONDITIONS = [('deny1', 'none'), ('deny2', 'none'), ('deny3', 'none'), ('allow1', 'none'),
                   ('noapply', 'none'), ('deny2', 'host'), ('deny2', 'both')]
VARIANTS = ('touch_v1', 'touch_v2', 'touch_v3', 'notouch_v1', 'notouch_v2', 'notouch_v3')
SHIPPED = ([(v, 'bare_deny_default') for v in VARIANTS] * 2
           + [('touch_v1', 'max_slots_deny_default'), ('notouch_v1', 'max_slots_deny_default'),
              ('touch_v1', 'happy_default_allow'), ('notouch_v1', 'happy_default_allow')])
SINGLE_REPEATS = 3
MANY_REPEATS = 2
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
        probe(['/usr/bin/uname', '-a']),
        probe(['/usr/sbin/sysctl', 'hw.model', 'hw.ncpu', 'hw.memsize', 'hw.pagesize', 'vm.loadavg',
               'kern.osversion', 'machdep.cpu.brand_string']),
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


def processes_with_path(paths):
    wanted = {str(p) for p in paths}
    count = LIBC.proc_listallpids(PIDS, ctypes.sizeof(PIDS))
    found, buffer = [], ctypes.create_string_buffer(4096)
    for pid in PIDS[:max(count, 0)]:
        if LIBC.proc_pidpath(pid, buffer, 4096) <= 0 or os.fsdecode(buffer.value) not in wanted:
            continue
        info = BsdInfo()
        if LIBC.proc_pidinfo(pid, 3, ctypes.c_uint64(0), ctypes.byref(info), ctypes.sizeof(info)) == ctypes.sizeof(info):
            found.append({'pid': pid, 'ppid': info.pbi_ppid, 'path': os.fsdecode(buffer.value),
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


def run_fixture_unit(unit_dir, unit, deadline_s):
    policy, touch, geometry = unit['policy'], unit['touch'], unit['geometry']
    policy_path = unit_dir / 'policy.sbpl'
    policy_path.write_text(POLICIES[policy])
    argv = [str(BUILD / 'pretouch_harness'), '--child', str(BUILD / 'pretouch_child'),
            '--policy-file', str(policy_path), '--policy-name', policy, '--touch', touch,
            '--apply', '0' if policy == 'noapply' else '1',
            '--probe-page', str(geometry['probe_page']), '--probe-pages', str(geometry['probe_pages']),
            '--second-map-page', str(geometry['second_map_page']), '--out', str(unit_dir / 'result.json')]
    status = {'kind': 'fixture', 'case': unit['case'], 'policy': policy, 'touch': touch, 'geometry': geometry,
              'argv': argv, 'state': 'started'}
    supervise(argv, unit_dir, deadline_s, status)
    return status


def run_shipped_unit(unit_dir, unit, deadline_s):
    argv = [str(BUILD / f"harness_{unit['variant']}"), str(WORKER), unit['scenario']]
    status = {'kind': 'shipped', 'case': unit['case'], 'variant': unit['variant'], 'scenario': unit['scenario'],
              'argv': argv, 'state': 'started'}
    supervise(argv, unit_dir, deadline_s, status)
    return status


def schedule(args):
    units = []
    for policy in POLICIES:
        for touch in TOUCHES:
            for _ in range(args.single_repeats):
                units.append({'kind': 'fixture', 'case': f'{policy}-{touch}-p1', 'policy': policy, 'touch': touch,
                              'geometry': SINGLE})
    for policy, touch in MANY_CONDITIONS:
        for _ in range(args.many_repeats):
            units.append({'kind': 'fixture', 'case': f"{policy}-{touch}-p{MANY['probe_pages']}", 'policy': policy,
                          'touch': touch, 'geometry': MANY})
    if not args.no_shipped:
        for variant, scenario in SHIPPED:
            units.append({'kind': 'shipped', 'case': f'shipped-{variant}-{scenario}', 'variant': variant,
                          'scenario': scenario})
    random.Random(args.seed).shuffle(units)
    return units


def read_deny_log(run_dir, start_wall_ns, end_wall_ns):
    fmt = '%Y-%m-%d %H:%M:%S'
    start = datetime.datetime.fromtimestamp(start_wall_ns / 1e9 - 5).strftime(fmt)
    end = datetime.datetime.fromtimestamp(end_wall_ns / 1e9 + 5).strftime(fmt)
    argv = ['/usr/bin/log', 'show', '--start', start, '--end', end, '--style', 'ndjson', '--predicate',
            '(process == "kernel") AND (eventMessage CONTAINS "pretouch_child" OR eventMessage CONTAINS "pw-probe-runner")']
    record = {'argv': argv, 'start': start, 'end': end, 'at': now()}
    try:
        with open(run_dir / 'deny-log.ndjson', 'xb') as out:
            done = subprocess.run(argv, env=CHILD_ENV, stdin=subprocess.DEVNULL, stdout=out,
                                  stderr=subprocess.PIPE, timeout=300, cwd=ROOT)
        record.update({'exit': done.returncode, 'stderr': done.stderr.decode(errors='replace')[-4000:]})
    except (OSError, subprocess.TimeoutExpired) as error:
        record['error'] = repr(error)
    record['ended'] = now()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'records/performance/runs')
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--gap-s', type=float, default=0.2)
    parser.add_argument('--unit-deadline-s', type=float, default=30.0)
    parser.add_argument('--ceiling-s', type=float, default=600.0)
    parser.add_argument('--single-repeats', type=int, default=SINGLE_REPEATS)
    parser.add_argument('--many-repeats', type=int, default=MANY_REPEATS)
    parser.add_argument('--no-shipped', action='store_true')
    parser.add_argument('--no-log', action='store_true')
    args = parser.parse_args()
    entry = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    binaries = [BUILD / 'pretouch_child', BUILD / 'pretouch_harness'] + [BUILD / f'harness_{v}' for v in VARIANTS]
    missing = [str(p) for p in binaries + [WORKER, BUILD / 'build.json'] if not p.is_file()]
    if missing:
        print(f'refused: missing {missing}; run records/performance/pretouch/build.sh', file=sys.stderr)
        return 2
    watched = [WORKER, BUILD / 'pretouch_child']
    if processes_with_path(watched):
        print('refused: a process is already running the worker or the fixture child', file=sys.stderr)
        return 2
    lock = os.open(ROOT / 'tests/.checkout.lock', os.O_RDWR)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('refused: tests/.checkout.lock is held', file=sys.stderr)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_dir = args.out / f'{stamp}-pretouch-{args.label}'
    run_dir.mkdir(parents=True, exist_ok=False)
    print(run_dir, flush=True)
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    units = schedule(args)
    build = json.loads((BUILD / 'build.json').read_text())
    run = {'format': 1, 'argv': [sys.executable, *sys.argv], 'python': sys.version,
           'harness_sha256': sha256(__file__), 'seed': args.seed,
           'schedule': [u['case'] for u in units], 'units': units,
           'settings': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
           'policies': POLICIES, 'single': SINGLE, 'many': MANY, 'child_env': CHILD_ENV,
           'build': build,
           'identity': {'binary_sha256': {p.name: sha256(p) for p in binaries}, 'worker_sha256': sha256(WORKER),
                        'source_sha256': {p.name: sha256(p) for p in sorted(Path(__file__).parent.iterdir())
                                          if p.is_file() and p.suffix in ('.c', '.h', '.py', '.sh')},
                        'probes': [probe([str(APP / 'Contents/MacOS/policy-witness'), '--version']),
                                   probe([str(WORKER), '--version']),
                                   probe(['/usr/bin/git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
                                   probe(['/usr/bin/git', '-C', str(ROOT), 'status', '--porcelain']),
                                   probe(['/usr/bin/codesign', '-dv', str(BUILD / 'pretouch_child')]),
                                   probe(['/usr/bin/codesign', '-dv', str(WORKER)])]},
           'started': now(), 'conditions_start': conditions()}
    statuses, stop_reason = [], 'completed'
    for sequence, unit in enumerate(units):
        if STOP is not None:
            stop_reason = 'interrupted'
            break
        if (time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) - entry) / 1e9 + args.unit_deadline_s + args.gap_s \
                > args.ceiling_s:
            stop_reason = 'ceiling'
            break
        time.sleep(args.gap_s)
        unit_dir = run_dir / 'units' / f"{sequence:03d}-{unit['case']}"
        unit_dir.mkdir(parents=True)
        if unit['kind'] == 'fixture':
            status = run_fixture_unit(unit_dir, unit, args.unit_deadline_s)
        else:
            status = run_shipped_unit(unit_dir, unit, args.unit_deadline_s)
        status['sequence'] = sequence
        status['processes_after_unit'] = processes_with_path(watched)
        write_json(unit_dir / 'status.json', status)
        statuses.append(status)
        if status['processes_after_unit']:
            stop_reason = 'child_survived_unit'
            break
    run.update({'stop_reason': stop_reason, 'interrupt': STOP, 'units_run': len(statuses),
                'never_started': [u['case'] for u in units[len(statuses):]], 'ended': now(),
                'processes_after': processes_with_path(watched), 'conditions_end': conditions()})
    if not args.no_log and statuses:
        run['deny_log'] = read_deny_log(run_dir, statuses[0]['start']['wall_ns'], statuses[-1]['end']['wall_ns'])
    write_json(run_dir / 'run.json', run)
    sums = [f'{sha256(p)}  {p.relative_to(run_dir)}\n' for p in sorted(run_dir.rglob('*')) if p.is_file()]
    (run_dir / 'SHA256SUMS').write_text(''.join(sums))
    os.close(lock)
    unclean = sum(s['state'] != 'exited' for s in statuses)
    print(f'{stop_reason}: {len(statuses)} of {len(units)} units, {unclean} past deadline', flush=True)
    return 0 if stop_reason == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
