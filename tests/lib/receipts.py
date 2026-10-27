"""Per-control evidence for the drift and offline preflight cases.

Schema 2 files contain case/mode, ok, complete and controls. Unittest controls
retain their test source, explicitly registered input trees, subtest outcomes,
assertion failures and direct commands. Commands retain argv, selected test
environment, input snapshots, output and monotonic time even when they fail.
Input snapshots store lexical paths, modes, symlink targets and content hashes;
blobs live beside the receipt. They observe the registered inputs, not all reads.
Nothing patches subprocess or filesystem APIs. Child processes of a recorded
command are outside the counting boundary.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import time
import unittest

SCHEMA_VERSION = 2
# Only the test's execution settings, never the caller's entire environment.
ENVIRONMENT = ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD', 'IDENTITY', 'DIST_DIR', 'SDKROOT', 'DEVELOPER_DIR',
               'PYTHONPATH', 'PYTHONHOME', 'MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES', 'MAKEFILES')


class Receipts:
    """Written at control start and after each observation; complete means execution reached its end."""
    def __init__(self, path, case, mode):
        self.path = Path(path)
        self.case, self.mode = case, mode
        self.controls = []
        self.write(ok=False, complete=False)

    def add(self, **control):
        control.setdefault('mode', self.mode)
        self.controls.append(control)
        self.write(ok=False, complete=False)
        return control

    def extend(self, controls):
        for control in controls:
            self.add(**control)

    def finish(self, ok, *, complete=True):
        self.write(ok=ok, complete=complete)

    def write(self, ok=False, complete=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(dict(schema_version=SCHEMA_VERSION, case=self.case, mode=self.mode, ok=ok,
                                             complete=complete, controls=self.controls), indent=2) + '\n')


class Control:
    """One test's recorder. Callers register roots/files and invoke run explicitly.

    paths=None selects the whole disposable input tree, including new paths, except .git metadata.
    Live checkouts and native copies use explicit paths, so build products and retained output are never scanned.
    Input versions share content-addressed blobs within this receipt file; every snapshot is a complete path map.
    """
    def __init__(self, file, record):
        self.file, self.record = file, record
        self.roots = []
        self.previous = {}
        self.base = file.path.parent / (file.path.stem + '-evidence') if file else None

    def flush(self):
        if self.file:
            self.file.write()

    def blob(self, data):
        digest = hashlib.sha256(data).hexdigest()
        path = self.base / 'blobs' / digest
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return str(path.relative_to(self.file.path.parent))

    def capture(self, root, paths=None, label='inputs'):
        if not self.file:
            return None
        started = time.perf_counter()
        root = Path(root).absolute()
        if paths is None:
            paths = []
            for where, directories, files in os.walk(root, followlinks=False):
                directories[:] = sorted(name for name in directories if name != '.git')
                paths.extend((Path(where) / name).relative_to(root).as_posix() for name in directories + sorted(files))
        entries = {}
        size = 0
        for name in sorted(set(paths)):
            name = str(name)
            path = root / name
            try:
                metadata = path.lstat()
                entry = dict(mode=stat.S_IMODE(metadata.st_mode))
                if stat.S_ISLNK(metadata.st_mode):
                    entry.update(kind='symlink', target=os.readlink(path))
                elif stat.S_ISDIR(metadata.st_mode):
                    entry.update(kind='directory')
                elif stat.S_ISREG(metadata.st_mode):
                    data = path.read_bytes()
                    size += len(data)
                    entry.update(kind='file', bytes=len(data), blob=self.blob(data))
                else:
                    entry.update(kind='special')
            except FileNotFoundError:
                entry = dict(kind='missing')
            except OSError as error:
                entry = dict(kind='unreadable', error=str(error))
            entries[name] = entry
        key = str(root)
        before = self.previous.get(key, {})
        changed = [name for name in sorted(set(before) | set(entries)) if before.get(name) != entries.get(name)]
        self.previous[key] = entries
        snapshot = dict(root=key, label=label, entries=entries, changed=changed, bytes=size,
                        elapsed_seconds=time.perf_counter() - started)
        number = len(self.record['inputs'])
        path = self.base / self.record['id'] / f'inputs-{number:03}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot, indent=2) + '\n')
        reference = str(path.relative_to(self.file.path.parent))
        self.record['inputs'].append(reference)
        self.flush()
        return reference

    def track(self, root, paths=None):
        paths = tuple(paths) if paths is not None else None
        item = (Path(root).absolute(), paths)
        if item not in self.roots:
            self.roots.append(item)
            self.capture(*item, label='initial')
            return True
        return False

    def capture_tracked(self, label):
        return [self.capture(root, paths, label) for root, paths in self.roots if root.exists()]

    def run(self, argv, *, subtest=None, **kwargs):
        """subprocess.run with durable before/after evidence. Preserve the caller's return/raise behavior."""
        inputs = self.capture_tracked('before command')
        entry = dict(argv=[str(a) for a in argv], cwd=str(kwargs.get('cwd', Path.cwd())), subtest=subtest,
                     inputs=inputs, environment={k: v for k, v in (kwargs.get('env') or {}).items() if k in ENVIRONMENT},
                     status='running', returncode=None, elapsed_seconds=None, stdout=None, stderr=None)
        self.record['launches'].append(entry)
        self.flush()
        # These controls capture output; an otherwise inherited stream is also captured and replayed for the log.
        replay = not kwargs.get('capture_output') and 'stdout' not in kwargs and 'stderr' not in kwargs
        if replay:
            kwargs['capture_output'] = True
        started = time.perf_counter()
        result = None
        try:
            result = subprocess.run(argv, **kwargs)
            entry.update(status='completed', returncode=result.returncode)
            return result
        except BaseException as error:
            result = error
            entry.update(status='timeout' if isinstance(error, subprocess.TimeoutExpired) else 'error',
                         error=f'{type(error).__name__}: {error}', returncode=getattr(error, 'returncode', None))
            raise
        finally:
            entry['elapsed_seconds'] = time.perf_counter() - started
            for stream in ('stdout', 'stderr'):
                data = getattr(result, stream, None)
                if data is not None and self.file:
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    path = self.base / self.record['id'] / f'launch-{len(self.record["launches"]):03}.{stream}'
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                    entry[stream] = str(path.relative_to(self.file.path.parent))
                if replay and data:
                    import sys
                    print(data.decode('utf-8', errors='replace') if isinstance(data, bytes) else data,
                          end='', file=getattr(sys, stream))
            self.flush()


class TestCase(unittest.TestCase):
    """Explicit evidence hooks used by the existing unittest cases; assertions remain ordinary unittest assertions."""
    @property
    def evidence(self):
        if not hasattr(self, '_evidence'):
            self._evidence = Control(None, dict(inputs=[], launches=[]))
        return self._evidence

    def track_inputs(self, root, paths=None):
        # Registered after fixture cleanup, so this observation runs before cleanup removes the inputs.
        if self.evidence.track(root, paths):
            self.addCleanup(self.evidence.capture_tracked, 'before cleanup')

    def run_command(self, argv, **kwargs):
        subtest = str(self._subtest) if self._subtest else None
        return self.evidence.run(argv, subtest=subtest, **kwargs)

    @contextmanager
    def subTest(self, *args, **params):
        with super().subTest(*args, **params):
            self.evidence.capture_tracked('subtest inputs')
            try:
                yield
            finally:
                self.evidence.capture_tracked('subtest outputs')


def launch(argv, launches, step, **kwargs):
    """Standalone scenario wrapper; record attempted launches even when subprocess.run raises."""
    entry = dict(step=step, argv=[str(a) for a in argv], returncode=None, elapsed_seconds=None)
    launches.append(entry)
    start = time.perf_counter()
    try:
        result = subprocess.run(argv, **kwargs)
        entry['returncode'] = result.returncode
        return result
    except BaseException as error:
        entry['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        entry['elapsed_seconds'] = time.perf_counter() - start


class TimedResult(unittest.TextTestResult):
    """Finalize exactly one receipt at stopTest, including failures reported only through addSubTest."""
    def __init__(self, *args, receipts=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.receipts = receipts
        self._active_test = None
        self._next_id = 0

    def begin_control(self, test):
        self._active_test = test
        self._started = time.perf_counter()
        self._record = dict(id=f'{self._next_id:03}', test=test.id(), mode=self.receipts.mode if self.receipts else 'unittest',
                            status='running', expected={'status': 'pass'}, actual={'status': 'running', 'errors': []},
                            elapsed_seconds=None, subtests=[], failed_subtests=[], inputs=[], launches=[])
        if self.receipts:
            self._record = self.receipts.add(**self._record)
        self._next_id += 1
        test._evidence = Control(self.receipts, self._record)
        source = Path(inspect.getfile(type(test)))
        if source.is_file():
            test._evidence.capture(source.parent, [source.name], 'test source')

    def startTest(self, test):
        self.begin_control(test)
        super().startTest(test)

    def outcome(self, status, error=None):
        if self._record['status'] not in ('fail', 'error') or status == 'error':
            self._record['status'] = status
        if error:
            self._record['actual']['errors'].append(error)
        self._record['actual']['status'] = self._record['status']
        if self.receipts:
            self.receipts.write()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcome('pass')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcome('fail', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        # unittest reports setUpClass/tearDownClass/module errors without startTest or stopTest.
        standalone = self._active_test is None
        if standalone:
            self.begin_control(test)
        self.outcome('error', self._exc_info_to_string(err, test))
        if standalone:
            self.end_control(test)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        standalone = self._active_test is None
        if standalone:
            self.begin_control(test)
        if test is not self._active_test:
            self._record['subtests'].append(dict(test=str(test), status='skip', reason=reason))
        else:
            self.outcome('skip', reason)
        if standalone:
            self.end_control(test)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        status = 'pass' if err is None else ('fail' if issubclass(err[0], test.failureException) else 'error')
        self._record['subtests'].append(dict(test=str(subtest), status=status))
        if err:
            self._record['failed_subtests'].append(str(subtest))
            self.outcome(status, self._exc_info_to_string(err, test))
        elif self.receipts:
            self.receipts.write()

    def end_control(self, test):
        self._record['elapsed_seconds'] = time.perf_counter() - self._started
        if self.receipts:
            self.receipts.write()
        print(f'test: {test.id()} {self._record["status"]} {self._record["elapsed_seconds"]:.3f} s')
        self._active_test = None

    def stopTest(self, test):
        self.end_control(test)
        super().stopTest(test)


def timed_main(module, case, name, mode='unittest'):
    """Run the module with one receipt per test; an interrupted suite remains incomplete."""
    artifacts = os.environ.get('PW_TEST_ARTIFACTS')
    file = Receipts(Path(artifacts) / f'{name}-receipts.json', case, mode) if artifacts else None
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=lambda *a, **kw: TimedResult(*a, receipts=file, **kw))
    try:
        result = runner.run(suite)
    except BaseException:
        if file:
            file.finish(False, complete=False)
        raise
    if file:
        file.finish(result.wasSuccessful())
    return 0 if result.wasSuccessful() else 1
