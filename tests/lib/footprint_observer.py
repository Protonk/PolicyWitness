"""Bounded test-only persistent native sampling; no footprint-manifest inputs."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess

METRICS = ('user_ns', 'system_ns', 'resident_bytes', 'phys_footprint_bytes')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generation(sample):
    g = sample['generation_before']
    return {k: g[k] for k in ('pid', 'start_sec', 'start_usec')}


def require_sample(sample, expected=None):
    assert sample['status'] == 'ok', sample
    assert sample['generation_before'] == sample['generation_after'], sample
    g = generation(sample)
    assert type(g['pid']) is int and g['pid'] > 0
    assert type(sample['pid']) is int and sample['pid'] == g['pid'], sample
    assert type(g['start_sec']) is int and g['start_sec'] > 0
    assert type(g['start_usec']) is int and 0 <= g['start_usec'] < 1_000_000
    if expected is not None:
        assert g == {k: expected[k] for k in g}, (g, expected)
    assert isinstance(sample['path'], str) and sample['path'].startswith('/'), sample
    assert type(sample['begin_ns']) is int and type(sample['end_ns']) is int
    assert 0 <= sample['begin_ns'] <= sample['end_ns'], sample
    previous = sample['begin_ns']
    for name in ('generation_before', 'rusage', 'path', 'generation_after'):
        call = sample['calls'][name]
        assert previous <= call['begin_ns'] <= call['end_ns'] <= sample['end_ns'], sample
        assert type(call['errno']) is int and call['errno'] == 0, sample
        assert call['rc'] == 0 if name == 'rusage' else call['rc'] > 0, sample
        previous = call['end_ns']
    for key in METRICS:
        assert type(sample[key]) is int and sample[key] >= 0, (key, sample)
    assert sample['raw_cpu_unit'] == 'mach_absolute_time_ticks', sample
    for key in ('timebase_numer', 'timebase_denom'):
        assert type(sample[key]) is int and sample[key] > 0, sample
    for kind in ('user', 'system'):
        raw = sample[kind + '_ticks']
        assert type(raw) is int and raw >= 0, sample
        assert sample[kind + '_ns'] == raw * sample['timebase_numer'] // sample['timebase_denom'], sample
    return sample


def validate_batch(batch, pids=None):
    assert batch['version'] == 1 and batch['clock'] == 'mach_continuous_time_ns', batch
    assert batch['cpu_unit'] == 'ns' and batch['memory_unit'] == 'bytes', batch
    assert type(batch['begin_ns']) is int and batch['begin_ns'] <= batch['end_ns'], batch
    assert 1 <= len(batch['samples']) <= 64
    if pids is not None:
        assert [s['pid'] for s in batch['samples']] == list(pids), batch
    previous = batch['begin_ns']
    for sample in batch['samples']:
        assert previous <= sample['begin_ns'] <= sample['end_ns'] <= batch['end_ns'], batch
        previous = sample['end_ns']
        if sample['status'] == 'ok':
            require_sample(sample)
        else:
            assert sample['status'] in ('error', 'generation_changed'), sample
            assert all(sample[key] is None for key in METRICS), sample
            assert sample['user_ticks'] is None and sample['system_ticks'] is None, sample
    return batch


class JsonProcess:
    def __init__(self, argv):
        self.process = subprocess.Popen(list(map(str, argv)), stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.pending = b''

    def read(self):
        # Read bytes directly: TextIO buffering can conceal a ready second line.
        while b'\n' not in self.pending:
            assert select.select([self.process.stdout], [], [], 5)[0], 'observer acknowledgement deadline'
            chunk = os.read(self.process.stdout.fileno(), 65536)
            assert chunk, f'observer exited: {self.process.poll()}'
            self.pending += chunk
            assert len(self.pending) <= 2_000_000, 'oversized observer receipt'
        line, self.pending = self.pending.split(b'\n', 1)
        return json.loads(line)

    def command(self, command):
        self.process.stdin.write((command + '\n').encode('ascii'))
        self.process.stdin.flush()
        return self.read()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(b'quit\n')
            self.process.stdin.flush()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                raise AssertionError('observer child required forced cleanup')
        assert self.process.returncode == 0, self.process.stderr.read().decode(errors='replace')
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()


class ControlChild(JsonProcess):
    def __init__(self, binary, mode):
        assert mode in ('busy', 'sleep', 'allocation')
        super().__init__([binary, '--child', mode])
        self.ack = self.read()
        assert self.ack == {'ack': 'ready', 'pid': self.process.pid, 'mode': mode}, self.ack
        self.pid = self.process.pid

    def touch(self, allocation_bytes):
        assert type(allocation_bytes) is int and 0 < allocation_bytes <= 256 * 1024 * 1024
        receipt = self.command(f'touch {allocation_bytes}')
        assert receipt == {'ack': 'touched', 'bytes': allocation_bytes}, receipt
        return receipt

    def cpu(self):
        receipt = self.command('cpu')
        assert receipt['ack'] == 'cpu' and receipt['source'] == 'getrusage_RUSAGE_SELF_timeval'
        assert receipt['rc'] == 0 and receipt['errno'] == 0, receipt
        assert receipt['begin_ns'] <= receipt['end_ns'], receipt
        for kind in ('user', 'system'):
            assert type(receipt[kind + '_sec']) is int and receipt[kind + '_sec'] >= 0
            assert type(receipt[kind + '_usec']) is int and 0 <= receipt[kind + '_usec'] < 1_000_000
        return receipt

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class FootprintObserver(JsonProcess):
    def __init__(self, binary, artifact_dir=None):
        self.binary = Path(binary).resolve()
        self.artifact_dir = Path(artifact_dir) if artifact_dir else None
        self.sequence = 0
        self.provenance = {'binary': str(self.binary), 'binary_sha256': sha256(self.binary),
                           'source_sha256': sha256(Path(__file__).parents[1] / 'fixtures/footprint/observer.c'),
                           'wrapper_sha256': sha256(__file__), 'observer_pid': None,
                           'clock': 'mach_continuous_time_ns',
                           'cpu_fields': 'rusage_info_v0.ri_user_time/ri_system_time',
                           'raw_cpu_unit': 'mach_absolute_time_ticks',
                           'cpu_conversion': 'floor(raw_ticks * timebase_numer / timebase_denom)',
                           'memory_fields': 'rusage_info_v0.ri_resident_size/ri_phys_footprint'}
        super().__init__([self.binary])
        self.provenance['observer_pid'] = self.process.pid
        if self.artifact_dir:
            self.artifact_dir.mkdir(parents=True, exist_ok=True)
            (self.artifact_dir / 'provenance.json').write_text(json.dumps(self.provenance, indent=2) + '\n')

    def _retain(self, receipt):
        if self.artifact_dir:
            self.sequence += 1
            (self.artifact_dir / f'{self.sequence:06d}.json').write_text(json.dumps(receipt, indent=2) + '\n')
        return receipt

    def clock(self):
        value = self.command('clock')
        assert value['clock'] == 'mach_continuous_time_ns'
        assert value['begin_ns'] <= value['continuous_ns'] <= value['end_ns']
        assert 0 <= value['uptime_ns'] <= value['continuous_ns']
        return self._retain(value)

    def sample(self, pids):
        pids = list(pids)
        assert 1 <= len(pids) <= 64 and len(set(pids)) == len(pids)
        assert all(type(pid) is int and 0 < pid <= 2**31 - 1 for pid in pids)
        result = self.command('sample ' + ' '.join(map(str, pids)))
        self._retain(result)
        return validate_batch(result, pids)

    def inspect(self, pid, expected=None):
        value = self.sample([pid])['samples'][0]
        return require_sample(value, expected) if expected is not None else value

    def spawn_control(self, mode='sleep', allocation_bytes=None):
        child = ControlChild(self.binary, mode)
        if allocation_bytes is not None:
            child.touch(allocation_bytes)
        return child

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class GenerationExitObserver:
    """EVFILT_PROC events bound to live generations; timestamps bracket collection."""
    def __init__(self, observer):
        self.observer = observer
        self.queue = select.kqueue()
        self.registered = {}
        self.events = {}
        self.registrations = []

    def watch(self, pid, expected=None):
        assert pid not in self.registered
        before = require_sample(self.observer.inspect(pid), expected)
        identity = generation(before)
        begin = self.observer.clock()
        self.queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                           flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                           fflags=select.KQ_NOTE_EXIT)], 0, 0)
        end = self.observer.clock()
        after = require_sample(self.observer.inspect(pid), identity)
        self.registered[pid] = identity
        receipt = {'generation': identity, 'before': before, 'after': after,
                   'begin_ns': begin['begin_ns'], 'end_ns': end['end_ns'],
                   'source': 'EVFILT_PROC NOTE_EXIT registration'}
        self.registrations.append(receipt)
        return receipt

    def read_exit_events(self, timeout=0):
        assert 0 <= timeout <= 5
        begin = self.observer.clock()
        events = self.queue.control(None, max(1, len(self.registered)), timeout)
        end = self.observer.clock()
        for event in events:
            assert not event.flags & select.KQ_EV_ERROR, event
            assert event.ident in self.registered, event
            if event.fflags & select.KQ_NOTE_EXIT:
                self.events[event.ident] = {'generation': self.registered[event.ident],
                    'source': 'EVFILT_PROC NOTE_EXIT', 'event': 'exit',
                    'collection_begin_ns': begin['begin_ns'],
                    'collection_end_ns': end['end_ns'],
                    'actual_exit_time_ns': None}
        return list(self.events.values())

    def close(self):
        self.queue.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
