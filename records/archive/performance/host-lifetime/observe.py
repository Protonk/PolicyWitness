#!/usr/bin/env python3
"""Bounded external observation of PolicyWitness process lifetimes.

Launches ordinary `policy-witness run` invocations and, independently of the
application, records every process whose executable is one of the selected
app's binaries: PID, kernel creation time, p_uniqueid and the parent's
p_puniqueid (PROC_PIDUNIQIDENTIFIERINFO), discovery time, kqueue exit and fork
notifications. No application code, setting, schema or signature is changed.
"""
import argparse
import atexit
import ctypes
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import resource
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CHILD_ENV = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
             'HOME': pwd.getpwuid(os.getuid()).pw_dir, 'LANG': 'C', 'LC_ALL': 'C'}
NOTE_EXITSTATUS = 0x04000000
STOP = None


def now():
    """One reading of each clock; wall time is CLOCK_REALTIME, as kernel start times are."""
    return {'mono_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW), 'wall_ns': time.time_ns()}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    with open(path, 'xb') as stream:
        stream.write(data)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


class BsdInfo(ctypes.Structure):
    _fields_ = [('pbi_flags', ctypes.c_uint32), ('pbi_status', ctypes.c_uint32),
                ('pbi_xstatus', ctypes.c_uint32), ('pbi_pid', ctypes.c_uint32),
                ('pbi_ppid', ctypes.c_uint32), ('pbi_uid', ctypes.c_uint32),
                ('pbi_gid', ctypes.c_uint32), ('pbi_ruid', ctypes.c_uint32),
                ('pbi_rgid', ctypes.c_uint32), ('pbi_svuid', ctypes.c_uint32),
                ('pbi_svgid', ctypes.c_uint32), ('rfu_1', ctypes.c_uint32),
                ('pbi_comm', ctypes.c_char * 16), ('pbi_name', ctypes.c_char * 32),
                ('pbi_nfiles', ctypes.c_uint32), ('pbi_pgid', ctypes.c_uint32),
                ('pbi_pjobc', ctypes.c_uint32), ('e_tdev', ctypes.c_uint32),
                ('e_tpgid', ctypes.c_uint32), ('pbi_nice', ctypes.c_int32),
                ('pbi_start_tvsec', ctypes.c_uint64), ('pbi_start_tvusec', ctypes.c_uint64)]


class UniqInfo(ctypes.Structure):
    _fields_ = [('p_uuid', ctypes.c_uint8 * 16), ('p_uniqueid', ctypes.c_uint64),
                ('p_puniqueid', ctypes.c_uint64), ('p_idversion', ctypes.c_int32),
                ('p_reserve2', ctypes.c_uint32), ('p_reserve3', ctypes.c_uint64),
                ('p_reserve4', ctypes.c_uint64)]


assert ctypes.sizeof(BsdInfo) == 136 and ctypes.sizeof(UniqInfo) == 56
LIBC = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
LIBC.mach_continuous_time.restype = ctypes.c_uint64
PROC_PIDTBSDINFO, PROC_PIDUNIQIDENTIFIERINFO = 3, 17
try:
    RESPONSIBLE = LIBC.responsibility_get_pid_responsible_for_pid
    RESPONSIBLE.restype, RESPONSIBLE.argtypes = ctypes.c_int, [ctypes.c_int]
except AttributeError:
    RESPONSIBLE = None
PIDS = (ctypes.c_int * 16384)()


def list_pids():
    count = LIBC.proc_listallpids(PIDS, ctypes.sizeof(PIDS))
    if count <= 0:
        raise OSError(ctypes.get_errno(), 'proc_listallpids')
    return set(PIDS[:count])


def pidinfo(pid, flavor, structure):
    value = structure()
    ctypes.set_errno(0)
    count = LIBC.proc_pidinfo(pid, flavor, ctypes.c_uint64(0), ctypes.byref(value), ctypes.sizeof(value))
    if count == ctypes.sizeof(value):
        return value, None
    return None, ctypes.get_errno()


def pidpath(pid):
    buffer = ctypes.create_string_buffer(4096)
    count = LIBC.proc_pidpath(pid, buffer, 4096)
    return os.fsdecode(buffer.value) if count > 0 else None


def start_us(info):
    return info.pbi_start_tvsec * 1_000_000 + info.pbi_start_tvusec


def start_us_key(record):
    return record['kernel_start_wall_us']


class Observer:
    """Single-threaded poll/kqueue loop. Records generations, never infers absence from errors."""

    def __init__(self, roles, poll_ms, recheck_ms, enabled=True):
        self.enabled = enabled
        self.roles = roles
        self.comms = {Path(p).name[:15].encode(): role for p, role in roles.items()}
        self.poll_s = poll_ms / 1000
        self.recheck_ns = recheck_ms * 1_000_000
        self.kq = select.kqueue()
        self.events = []
        self.processes = {}      # key "pid:start_us" -> record
        self.live = {}           # pid -> key, for registered generations
        self.unregistered = {}   # pid -> key, watched by polling because registration failed
        self.pending = {}        # pid -> first-seen mono_ns, unmatched new pids awaiting recheck
        self.controllers = {}    # pid -> unit status dict
        self.proxies = {}        # pid -> xpcproxy awaiting exec into a selected executable
        self.polls = 0
        self.max_gap_ns = 0
        self.gaps_over_5ms = 0
        self.last_poll_ns = None
        self.list_errors = 0
        self.previous = list_pids() if enabled else set()
        self.baseline = []
        for pid in sorted(self.previous):
            record = self.inspect(pid, now(), baseline=True)
            if record is not None:
                self.baseline.append(record['key'])

    def event(self, kind, at, **fields):
        self.events.append({'kind': kind, 'mono_ns': at['mono_ns'], 'wall_ns': at['wall_ns'], **fields})

    def inspect(self, pid, at, baseline=False):
        info, err = pidinfo(pid, PROC_PIDTBSDINFO, BsdInfo)
        if info is None:
            return None
        comm = bytes(info.pbi_comm)[:15].rstrip(b'\0')
        role = self.comms.get(comm)
        if role is None:
            if comm == b'xpcproxy' and not baseline and pid not in self.proxies:
                self.watch_proxy(pid, info, at)
            return None
        path = pidpath(pid)
        uniq, uniq_err = pidinfo(pid, PROC_PIDUNIQIDENTIFIERINFO, UniqInfo)
        after, _ = pidinfo(pid, PROC_PIDTBSDINFO, BsdInfo)
        if after is None or start_us(after) != start_us(info):
            self.event('identity_changed_during_inspection', at, pid=pid)
            return None
        resolved = os.path.realpath(path) if path else None
        role = self.roles.get(resolved, 'foreign:' + role)
        key = f'{pid}:{start_us(info)}'
        if key in self.processes:
            return self.processes[key]
        responsible = RESPONSIBLE(pid) if RESPONSIBLE is not None else None
        record = {'key': key, 'role': role, 'pid': pid, 'ppid': info.pbi_ppid,
                  'uid': info.pbi_uid, 'path': path,
                  'kernel_start_wall_us': start_us(info),
                  'uniqueid': uniq.p_uniqueid if uniq else None,
                  'parent_uniqueid': uniq.p_puniqueid if uniq else None,
                  'uniqinfo_errno': uniq_err, 'responsible_pid': responsible,
                  'first_seen': at, 'baseline': baseline,
                  'registration': None, 'exit': None, 'fork_notifications': []}
        self.processes[key] = record
        self.event('discovered', at, key=key, role=role)
        proxy = self.proxies.pop(pid, None)
        if proxy is not None and proxy['start_us'] == start_us(info):
            # Found by the poll before its NOTE_EXEC was read; the exec time is not observed.
            record['xpcproxy'] = {'first_seen': proxy['first_seen'], 'exec_observed': None,
                                  'basis': 'found_by_poll'}
        if pid in self.controllers:
            # Already registered by spawn() with NOTE_EXITSTATUS; wait() maps its exit here.
            record['registration'] = 'controller_kqueue'
            self.live[pid] = key
            return record
        fflags = select.KQ_NOTE_EXIT | select.KQ_NOTE_EXEC | (select.KQ_NOTE_FORK if role == 'host' else 0)
        try:
            self.kq.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                                           flags=select.KQ_EV_ADD, fflags=fflags)], 0, 0)
            check, _ = pidinfo(pid, PROC_PIDTBSDINFO, BsdInfo)
            if check is not None and start_us(check) == start_us(info):
                record['registration'] = 'kqueue'
                self.live[pid] = key
                # An exec finished before registration raises no NOTE_EXEC; reread the image once.
                path_now = pidpath(pid)
                if path_now is not None and path_now != path:
                    role_now = self.roles.get(os.path.realpath(path_now), 'foreign_or_gone')
                    record['exec_notifications'] = [{'at': now(), 'basis': 'path_changed_before_registration',
                                                     'path_after': path_now, 'role_before': record['role'],
                                                     'role_after': role_now}]
                    record['role'], record['path'] = role_now, path_now
            else:
                record['registration'] = 'kqueue_generation_unconfirmed'
                record['exit'] = {'basis': 'absent_after_registration', 'at': now()}
        except ProcessLookupError:
            record['registration'] = 'esrch'
            record['exit'] = {'basis': 'gone_at_registration', 'at': now()}
        except OSError as error:
            record['registration'] = f'error:{error.errno}'
            self.unregistered[pid] = key
        return record

    def watch_proxy(self, pid, info, at):
        """launchd starts a service as xpcproxy, which then execs the service executable."""
        try:
            self.kq.control([select.kevent(pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD,
                                           fflags=select.KQ_NOTE_EXEC | select.KQ_NOTE_EXIT)], 0, 0)
        except OSError:
            return
        # An exec completed before registration produces no event; the pending recheck covers it.
        self.proxies[pid] = {'start_us': start_us(info), 'first_seen': at}

    def poll(self):
        if not self.enabled:
            return
        at = now()
        if self.last_poll_ns is not None:
            gap = at['mono_ns'] - self.last_poll_ns
            self.max_gap_ns = max(self.max_gap_ns, gap)
            self.gaps_over_5ms += gap > 5_000_000
        self.last_poll_ns = at['mono_ns']
        self.polls += 1
        try:
            current = list_pids()
        except OSError:
            self.list_errors += 1
            return
        # A pid first seen before its exec would show its parent's name; recheck briefly.
        for pid, first in list(self.pending.items()):
            if pid in current and self.inspect(pid, at) is None and at['mono_ns'] - first < self.recheck_ns:
                continue
            del self.pending[pid]
        for pid in current - self.previous:
            if self.inspect(pid, at) is None:
                self.pending[pid] = at['mono_ns']
        for pid, key in list(self.unregistered.items()):
            info, err = pidinfo(pid, PROC_PIDTBSDINFO, BsdInfo)
            if info is None or f'{pid}:{start_us(info)}' != key:
                self.processes[key]['exit'] = {'basis': 'absent_at_poll', 'at': at, 'errno': err}
                del self.unregistered[pid]
        self.previous = current

    def wait(self, timeout_s):
        try:
            got = self.kq.control(None, 64, timeout_s)
        except InterruptedError:
            got = []
        at = now()
        for ev in got:
            pid = ev.ident
            if pid in self.controllers and ev.fflags & select.KQ_NOTE_EXIT:
                self.controllers[pid].setdefault('note_exit', at)
            proxy = self.proxies.pop(pid, None)
            exec_consumed = False
            if proxy is not None and ev.fflags & select.KQ_NOTE_EXEC:
                exec_consumed = True
                record = self.inspect(pid, at)
                if record is not None and start_us_key(record) == proxy['start_us']:
                    record['xpcproxy'] = {'first_seen': proxy['first_seen'], 'exec_observed': at,
                                          'basis': 'kqueue_note_exec'}
                else:
                    self.event('xpcproxy_exec_unidentified', at, pid=pid, fflags=ev.fflags)
            key = self.live.get(pid)
            if key is None:
                continue
            record = self.processes[key]
            if ev.fflags & select.KQ_NOTE_FORK:
                record['fork_notifications'].append(at)
            if ev.fflags & select.KQ_NOTE_EXEC and not exec_consumed:
                # posix_spawn children are briefly visible under the parent's image before exec.
                path_after = pidpath(pid)
                role_after = self.roles.get(os.path.realpath(path_after) if path_after else None,
                                            'foreign_or_gone')
                record.setdefault('exec_notifications', []).append(
                    {'at': at, 'path_after': path_after, 'role_before': record['role'],
                     'role_after': role_after})
                record['role'], record['path'] = role_after, path_after
            if ev.fflags & select.KQ_NOTE_EXIT:
                record['exit'] = {'basis': 'kqueue_note_exit', 'at': at}
                del self.live[pid]
        for pid, status in self.controllers.items():
            if 'reaped' in status:
                continue
            try:
                waited, wstatus, usage = os.wait4(pid, os.WNOHANG)
            except ChildProcessError:
                continue
            if waited == pid:
                status['reaped'] = now()
                status['wait_status'] = wstatus
                status['exit_code'] = os.waitstatus_to_exitcode(wstatus)
                status['rusage'] = {'utime_s': usage.ru_utime, 'stime_s': usage.ru_stime,
                                    'maxrss': usage.ru_maxrss}
                key = self.live.pop(pid, None)
                if key is not None and self.processes[key]['exit'] is None:
                    self.processes[key]['exit'] = {'basis': 'wait4_reaped', 'at': status['reaped']}

    def step(self):
        self.poll()
        self.wait(self.poll_s)

    def alive_owned(self):
        return [self.processes[k] for k in list(self.live.values()) + list(self.unregistered.values())
                if not self.processes[k]['baseline'] and not self.processes[k]['role'].startswith('foreign')]


def spawn(observer, argv, unit_dir, label):
    unit_dir.mkdir()
    write_json(unit_dir / 'argv.json', argv)
    actions = [(os.POSIX_SPAWN_OPEN, 0, '/dev/null', os.O_RDONLY, 0),
               (os.POSIX_SPAWN_OPEN, 1, str(unit_dir / 'stdout.json'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644),
               (os.POSIX_SPAWN_OPEN, 2, str(unit_dir / 'stderr.txt'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)]
    before = now()
    pid = os.posix_spawn(argv[0], argv, CHILD_ENV, file_actions=actions)
    after = now()
    status = {'label': label, 'pid': pid, 'spawn_before': before, 'spawn_after': after,
              'unit_dir': unit_dir.name}
    observer.controllers[pid] = status
    try:
        observer.kq.control([select.kevent(pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD,
                                           fflags=select.KQ_NOTE_EXIT | NOTE_EXITSTATUS)], 0, 0)
        status['registration'] = 'kqueue'
    except OSError as error:
        status['registration'] = f'error:{error.errno}'
    info, _ = pidinfo(pid, PROC_PIDTBSDINFO, BsdInfo)
    uniq, _ = pidinfo(pid, PROC_PIDUNIQIDENTIFIERINFO, UniqInfo)
    status['kernel_start_wall_us'] = start_us(info) if info else None
    status['uniqueid'] = uniq.p_uniqueid if uniq else None
    observer.event('controller_spawned', after, pid=pid, label=label)
    return status


def supervise(observer, statuses, deadline_ns, kill_grace_ns=2_000_000_000):
    """Observe until every listed controller is reaped; enforce the unit deadline."""
    while any('reaped' not in s for s in statuses):
        observer.step()
        at = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
        for s in statuses:
            if 'reaped' in s:
                continue
            if (at >= deadline_ns or STOP is not None) and 'sigterm' not in s:
                os.kill(s['pid'], signal.SIGTERM)
                s['sigterm'] = now()
            elif 'sigterm' in s and 'sigkill' not in s and at >= s['sigterm']['mono_ns'] + kill_grace_ns:
                os.kill(s['pid'], signal.SIGKILL)
                s['sigkill'] = now()


def quiesce(observer, deadline_ns):
    """Observe until no owned role process remains alive, or the deadline passes."""
    while observer.alive_owned():
        if time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) >= deadline_ns:
            return False
        observer.step()
    return True


def observe_for(observer, seconds):
    end = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) + int(seconds * 1e9)
    while time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) < end:
        observer.step()


def probe(argv, timeout=10):
    try:
        out = subprocess.run(argv, env=CHILD_ENV, stdin=subprocess.DEVNULL, capture_output=True,
                             timeout=timeout, cwd=ROOT)
        return {'argv': argv, 'exit': out.returncode,
                'stdout': out.stdout.decode(errors='replace')[:20000],
                'stderr': out.stderr.decode(errors='replace')[-4000:]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'argv': argv, 'error': repr(error)}


def conditions(app):
    return {'at': utc(), 'probes': [
        probe(['/usr/bin/sw_vers']),
        probe(['/usr/sbin/sysctl', 'hw.model', 'hw.ncpu', 'hw.memsize', 'kern.boottime', 'vm.loadavg']),
        probe(['/usr/bin/pmset', '-g', 'batt']),
        probe(['/bin/ps', '-axo', 'pid,ppid,%cpu,comm', '-r']),
    ]}


def identity(app):
    executables = sorted(p for p in app.rglob('*') if p.is_file() and os.access(p, os.X_OK))
    files = {str(p): sha256(p) for p in executables}
    for extra in ('Contents/Info.plist', 'Contents/XPCServices/PWRunner.xpc/Contents/Info.plist'):
        files[str(app / extra)] = sha256(app / extra)
    pw = app / 'Contents/MacOS/policy-witness'
    host = app / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner'
    return {'files': files, 'probes': [
        probe([str(pw), '--version']),
        probe(['/usr/bin/codesign', '-dvvv', str(host)]),
        probe(['/usr/bin/codesign', '-dvvv', str(app / 'Contents/MacOS/pw-runner-client')]),
        probe(['/usr/bin/plutil', '-convert', 'json', '-o', '-',
               str(app / 'Contents/XPCServices/PWRunner.xpc/Contents/Info.plist')]),
        probe(['/usr/bin/git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
        probe(['/usr/bin/git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=all']),
    ]}


def launchd_log(start_wall_ns, end_wall_ns, run_dir):
    """launchd's own account of the selected service's instances, retained raw."""
    def local(ns):
        return datetime.datetime.fromtimestamp(ns / 1e9).strftime('%Y-%m-%d %H:%M:%S')
    # launchd's domain/service prefix is the subsystem field, not part of eventMessage.
    predicate = ('(process == "launchd" AND (subsystem CONTAINS "PWRunner" OR subsystem CONTAINS '
                 '"pw-runner-clien" OR eventMessage CONTAINS "PWRunner")) '
                 'OR (process == "PWRunner" AND eventMessage CONTAINS "invalidated")')
    argv = ['/usr/bin/log', 'show', '--start', local(start_wall_ns - 1_000_000_000),
            '--end', local(end_wall_ns + 2_000_000_000), '--info', '--debug', '--style', 'ndjson',
            '--predicate', predicate]
    record = {'argv': argv, 'started': now()}
    try:
        with open(run_dir / 'launchd-log.ndjson', 'xb') as out:
            done = subprocess.run(argv, env=CHILD_ENV, stdin=subprocess.DEVNULL, stdout=out,
                                  stderr=subprocess.PIPE, timeout=120)
        record.update({'exit': done.returncode, 'stderr': done.stderr.decode(errors='replace')[-4000:]})
    except (OSError, subprocess.TimeoutExpired) as error:
        record['error'] = repr(error)
    record['ended'] = now()
    return record


class Timebase(ctypes.Structure):
    _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]


def clock_identity():
    """Unified-log machTimestamp values are compared with CLOCK_MONOTONIC_RAW through this timebase."""
    base = Timebase()
    LIBC.mach_timebase_info(ctypes.byref(base))
    return {'mach_timebase': [base.numer, base.denom], 'reading': now(),
            'uptime_raw_ns': time.clock_gettime_ns(time.CLOCK_UPTIME_RAW),
            'mach_continuous_time': LIBC.mach_continuous_time() if hasattr(LIBC, 'mach_continuous_time') else None}


def interrupt(signum, frame):
    global STOP
    STOP = {'signal': signum, 'at': now()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--series', required=True, choices=['separated', 'rapid', 'overlap'])
    parser.add_argument('--count', type=int, required=True, help='invocations, or pairs for overlap')
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--app', type=Path, default=ROOT / 'dist/PolicyWitness.app')
    parser.add_argument('--out', type=Path, default=ROOT / 'records/performance/runs')
    parser.add_argument('--label', required=True)
    parser.add_argument('--gap-s', type=float, default=1.0, help='quiet interval before separated units and pairs')
    parser.add_argument('--tail-s', type=float, default=1.0, help='observation after the last quiescence')
    parser.add_argument('--poll-ms', type=float, default=1.0)
    parser.add_argument('--recheck-ms', type=float, default=100.0)
    parser.add_argument('--unit-deadline-s', type=float, default=30.0)
    parser.add_argument('--quiesce-deadline-s', type=float, default=5.0)
    parser.add_argument('--ceiling-s', type=float, default=180.0)
    parser.add_argument('--no-launchd-log', action='store_true')
    parser.add_argument('--unobserved', action='store_true',
                        help='no process-table polling; controllers are still timed by kqueue and wait4')
    parser.add_argument('--busy-loop', action='store_true',
                        help='keep one spinning Python process alive for the series (idle-state control)')
    parser.add_argument('--pw-arg', action='append', default=[], help='extra argument after the request path')
    args = parser.parse_args()
    entry_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    ceiling_ns = entry_ns + int(args.ceiling_s * 1e9)

    app = Path(os.path.realpath(args.app))
    macos, xpc = app / 'Contents/MacOS', app / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS'
    roles = {str(macos / 'policy-witness'): 'controller', str(macos / 'pw-runner-client'): 'client',
             str(macos / 'sbpl-check'): 'sbpl_check', str(xpc / 'PWRunner'): 'host',
             str(xpc / 'pw-probe-runner'): 'worker', str(xpc / 'sb_api_validator'): 'validator',
             str(xpc / 'pw-extension-issuer'): 'issuer'}
    if not all(os.path.isfile(p) for p in roles):
        print('refused: selected app lacks an expected executable', file=sys.stderr)
        return 2

    lock_fd = os.open(ROOT / 'tests/.checkout.lock', os.O_RDWR)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('refused: tests/.checkout.lock is held', file=sys.stderr)
        return 2

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_dir = args.out / f'{stamp}-hostlife-{args.label}'
    run_dir.mkdir(parents=True, exist_ok=False)
    print(run_dir, flush=True)
    request = run_dir / 'request.json'
    request.write_bytes(args.request.read_bytes())
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)

    run = {'format': 1, 'argv': [sys.executable, *sys.argv], 'python': sys.version,
           'harness_sha256': sha256(__file__), 'series': args.series, 'count': args.count,
           'settings': {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
           'request_source': str(args.request), 'request_sha256': sha256(request),
           'child_env': CHILD_ENV, 'roles': roles, 'responsible_api': RESPONSIBLE is not None,
           'started_utc': utc(), 'start_clocks': now(), 'clock_identity_start': clock_identity(),
           'identity': identity(app), 'conditions_start': conditions(app)}
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    busy = None
    if args.busy_loop:
        busy = subprocess.Popen([sys.executable, '-B', '-S', '-c', 'while True: pass'], env=CHILD_ENV,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run['busy_loop'] = {'pid': busy.pid, 'started': now()}
        atexit.register(busy.kill)
        time.sleep(0.5)
    observer = Observer(roles, args.poll_ms, args.recheck_ms, enabled=not args.unobserved)
    argv = [str(macos / 'policy-witness'), 'run', str(request), *args.pw_arg]
    units, stop_reason = [], 'completed'

    def unit_deadline():
        return min(ceiling_ns, time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) + int(args.unit_deadline_s * 1e9))

    def guard():
        if STOP is not None:
            return 'interrupted'
        if time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) >= ceiling_ns:
            return 'ceiling'
        return None

    try:
        for index in range(args.count):
            stop = guard()
            if stop:
                stop_reason = stop
                break
            if args.series in ('separated', 'overlap'):
                quiet = quiesce(observer, min(ceiling_ns, time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                                              + int(args.quiesce_deadline_s * 1e9)))
                observer.event('quiesced' if quiet else 'quiesce_deadline', now(), before_unit=index)
                observe_for(observer, args.gap_s)
            if args.series == 'overlap':
                pair = [spawn(observer, argv, run_dir / f'unit-{index:03d}{side}', f'{index}{side}')
                        for side in 'ab']
                units.extend(pair)
                supervise(observer, pair, unit_deadline())
            else:
                status = spawn(observer, argv, run_dir / f'unit-{index:03d}', str(index))
                units.append(status)
                supervise(observer, [status], unit_deadline())
        quiet = quiesce(observer, min(ceiling_ns, time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                                      + int(args.quiesce_deadline_s * 1e9)))
        observer.event('quiesced' if quiet else 'quiesce_deadline', now(), before_unit=None)
        observe_for(observer, args.tail_s)
    except Exception as error:  # retain the partial record
        stop_reason = f'harness_error: {error!r}'
        for s in units:
            if 'reaped' not in s:
                try:
                    os.kill(s['pid'], signal.SIGKILL)
                    s['sigkill'] = now()
                except ProcessLookupError:
                    pass
        try:
            supervise(observer, units, time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) + 3_000_000_000)
        except Exception:
            pass

    usage_end = resource.getrusage(resource.RUSAGE_SELF)
    observed_end = now()
    if busy is not None:
        busy.kill()
        run['busy_loop'].update({'killed': now(), 'wait_status': busy.wait(timeout=5)})
    if not args.no_launchd_log:
        run['launchd_log'] = launchd_log(run['start_clocks']['wall_ns'], observed_end['wall_ns'], run_dir)
    run.update({'stop_reason': stop_reason, 'interrupt': STOP, 'ended_utc': utc(), 'end_clocks': observed_end,
                'clock_identity_end': clock_identity(),
                'units': units, 'baseline_processes': observer.baseline,
                'still_alive_at_end': [r['key'] for r in observer.alive_owned()],
                'observer': {'polls': observer.polls, 'max_poll_gap_ns': observer.max_gap_ns,
                             'poll_gaps_over_5ms': observer.gaps_over_5ms,
                             'list_errors': observer.list_errors,
                             'cpu_user_s': usage_end.ru_utime - usage_start.ru_utime,
                             'cpu_system_s': usage_end.ru_stime - usage_start.ru_stime},
                'conditions_end': conditions(app)})
    write_json(run_dir / 'processes.json', list(observer.processes.values()))
    write_json(run_dir / 'events.json', observer.events)
    write_json(run_dir / 'run.json', run)
    sums = []
    for path in sorted(p for p in run_dir.rglob('*') if p.is_file()):
        sums.append(f'{sha256(path)}  {path.relative_to(run_dir)}\n')
    (run_dir / 'SHA256SUMS').write_text(''.join(sums))
    os.close(lock_fd)
    print(f'{stop_reason}: {len(units)} controllers, {len(observer.processes)} processes', flush=True)
    return 0 if stop_reason == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
