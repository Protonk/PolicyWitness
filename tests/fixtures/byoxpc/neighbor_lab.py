"""Process observation for BYOXPC coexistence controls.

Generations are PID plus kernel start time. Only ESRCH is absence; any other
failed query is an observation failure, never an exit.
"""
import ctypes
import json
from pathlib import Path
import threading
import time


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.new')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def wait_for(predicate, description, timeout=20):
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise AssertionError('experiment watchdog: ' + description)
        time.sleep(.01)


class BSDInfo(ctypes.Structure):
    # SDK sys/proc_info.h, struct proc_bsdinfo (136 bytes).
    _fields_ = [('words', ctypes.c_uint32 * 12), ('comm', ctypes.c_char * 16),
                ('name', ctypes.c_char * 32), ('tail', ctypes.c_uint32 * 6),
                ('start_sec', ctypes.c_uint64), ('start_usec', ctypes.c_uint64)]


LIBPROC = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
assert ctypes.sizeof(BSDInfo) == 136


def process_identity(pid):
    # PROC_PIDTBSDINFO. A returned start time distinguishes reuse of a PID. Only
    # ESRCH is absence; any other failed query is an observation failure.
    value = BSDInfo()
    ctypes.set_errno(0)
    count = LIBPROC.proc_pidinfo(int(pid), 3, 0, ctypes.byref(value), ctypes.sizeof(value))
    if count != ctypes.sizeof(value):
        error = ctypes.get_errno()
        return dict(pid=int(pid), observed=False, absent=error == 3, errno=error, returned_bytes=count)
    return dict(pid=int(pid), observed=True, start_sec=value.start_sec,
                start_usec=value.start_usec, ppid=value.words[4], status=value.words[1])


def generation(identity):
    """A process generation: PID plus kernel start time."""
    return f"{identity['pid']}@{identity['start_sec']}.{identity['start_usec']:06d}"


def generation_state(key):
    """'alive', 'gone' (ESRCH or the PID now names another start) or 'unknown'."""
    pid = int(key.split('@')[0])
    identity = process_identity(pid)
    if identity['observed']:
        return 'alive' if generation(identity) == key else 'gone'
    return 'gone' if identity['absent'] else 'unknown'


def executable_path(pid):
    buffer = ctypes.create_string_buffer(4096)
    length = LIBPROC.proc_pidpath(int(pid), buffer, 4096)
    return buffer.value[:length].decode('utf-8', 'replace') if length > 0 else None


class ProcessWatch:
    """Sample processes whose executable path is watched.

    A sweep lists all PIDs and reads each executable path. Generations seen
    alive are reported with first/last sweep times; a generation missing from a
    later complete sweep is reported as unseen after that sweep, not as exited.
    Short-lived processes can fall between sweeps; sweep timing is retained.
    """
    def __init__(self, watched):
        self.watched = {str(path): label for path, label in watched.items()}
        self.generations, self.sweeps = {}, []
        self.lock, self.stop_event = threading.Lock(), threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def sweep(self):
        started = time.monotonic_ns()
        count = LIBPROC.proc_listallpids(None, 0)
        buffer = (ctypes.c_int * (count + 64))()
        count = LIBPROC.proc_listallpids(buffer, ctypes.sizeof(buffer))
        seen = set()
        for pid in buffer[:count]:
            path = executable_path(pid) if pid > 0 else None
            if path not in self.watched:
                continue
            identity = process_identity(pid)
            if not identity['observed']:
                continue
            key = generation(identity)
            seen.add(key)
            with self.lock:
                record = self.generations.setdefault(key, dict(
                    generation=key, label=self.watched[path], path=path, pid=pid,
                    ppid=identity['ppid'], first_seen_ns=started, unseen_after_ns=None, reappeared=0))
                record['last_seen_ns'] = started
                if record['unseen_after_ns'] is not None:
                    record['unseen_after_ns'] = None
                    record['reappeared'] += 1
        finished = time.monotonic_ns()
        with self.lock:
            for key, record in self.generations.items():
                if key not in seen and record['unseen_after_ns'] is None:
                    record['unseen_after_ns'] = finished
            self.sweeps.append((started, finished))

    def run(self):
        while not self.stop_event.is_set():
            self.sweep()
            time.sleep(.001)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)

    def snapshot(self, label=None):
        with self.lock:
            return [dict(r) for r in self.generations.values() if label in (None, r['label'])]

    def summary(self):
        with self.lock:
            durations = [b - a for a, b in self.sweeps]
            gaps = [b[0] - a[1] for a, b in zip(self.sweeps, self.sweeps[1:])]
        return dict(sweeps=len(durations), max_sweep_ns=max(durations, default=None),
                    max_gap_ns=max(gaps, default=None),
                    median_sweep_ns=sorted(durations)[len(durations)//2] if durations else None)
