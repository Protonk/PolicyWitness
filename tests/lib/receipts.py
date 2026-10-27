"""Receipts for test controls: what ran, over which inputs, with what result, and what it cost.

A receipt file is one JSON object: `schema_version` (2), `case` (the catalog case), `mode` (how the controls
ran), `ok`, `complete` (false while the controls are still running or after an exception, so a partial file
is never mistaken for a finished one) and `controls`, one object per control. A control names its `scenario`
or `test`, its `mode` (`in-process`, `entry-point`, `meson`, `build-script` or `unittest`), the owner `rules`
and `changed` inputs when it has them, its `expected` and `actual` records or status, the `stdout` and
`stderr` paths when output was captured, its monotonic `elapsed_seconds`, and `launches`: the direct child
processes it started, each with its argv, return code and elapsed time. A launch count is the controls'
own children, never an OS-wide count of what Meson, compilers or the build script started in turn.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time
import unittest

SCHEMA_VERSION = 2


class Receipts:
    """A receipt file that is written after every control, so a failure leaves a partial record."""

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

    def finish(self, ok):
        self.write(ok=ok, complete=True)

    def write(self, ok, complete):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(dict(schema_version=SCHEMA_VERSION, case=self.case, mode=self.mode, ok=ok,
                                             complete=complete, controls=self.controls), indent=2) + '\n')


def launch(argv, launches, step, **kwargs):
    """subprocess.run with the launch recorded: argv, return code and monotonic elapsed time."""
    start = time.perf_counter()
    result = subprocess.run(argv, **kwargs)
    launches.append(dict(step=step, argv=[str(a) for a in argv], returncode=result.returncode,
                         elapsed_seconds=time.perf_counter() - start))
    return result


class TimedResult(unittest.TextTestResult):
    """Records each test's status and elapsed time into a receipt as it finishes."""
    receipts = None

    def startTest(self, test):
        self._started = time.perf_counter()
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, 'pass')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, 'fail')

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, 'error')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, 'skip')

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._subtests = getattr(self, '_subtests', [])
            self._subtests.append(str(subtest.params if hasattr(subtest, 'params') else subtest))

    def _record(self, test, status):
        elapsed = time.perf_counter() - self._started
        print(f'test: {test.id().split(".")[-1]} {status} {elapsed:.3f} s')
        if self.receipts is not None:
            self.receipts.add(test=test.id().split('.')[-1], status=status, elapsed_seconds=elapsed,
                              failed_subtests=getattr(self, '_subtests', []))
        self._subtests = []


def timed_main(module, case, name, mode='unittest'):
    """Run a module's tests with per-test timings on stdout and a receipt under PW_TEST_ARTIFACTS when it is set."""
    artifacts = os.environ.get('PW_TEST_ARTIFACTS')
    receipts = Receipts(Path(artifacts) / f'{name}-receipts.json', case, mode) if artifacts else None
    TimedResult.receipts = receipts
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult)
    result = runner.run(suite)
    if receipts is not None:
        receipts.finish(result.wasSuccessful())
    return 0 if result.wasSuccessful() else 1
