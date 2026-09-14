"""Capture a public CLI run without deciding whether its evidence passes.

Prepare every specimen before calling start() to overlap runs. wait() observes
the CLI only: it never releases a fixture or signals a process. close() owns
cleanup of this CLI, after the caller's independent lifecycle observations.
Workers, XPC hosts, and fixture trees remain the caller's responsibility.
"""
import json
from pathlib import Path
import subprocess
import time


class HarnessTimeout(TimeoutError):
    """The test's CLI wait expired, independently of any PW deadline."""


class RunCapture:
    def __init__(self, pw, out, specimen, *, cli_args=()):
        self.out = Path(out).resolve()
        self.request_path = self.out / 'specimen.json'
        self.stdout_path = self.out / 'run.json'
        self.stderr_path = self.out / 'pw.stderr'
        self.metadata_path = self.out / 'capture.json'
        self.argv = [str(pw), 'run', str(self.request_path), *map(str, cli_args)]
        self._process = None
        self._started = None
        self._metadata = {
            'argv': self.argv, 'state': 'prepared', 'pid': None,
            'started_at_unix_ns': None, 'elapsed_seconds': None,
            'returncode': None, 'exit_code': None, 'term_signal': None,
            'harness_timeout_seconds': None, 'cleanup_kill_requested': False,
            'launch_error': None, 'json_error': None, 'cleanup_error': None,
        }
        self.out.mkdir(parents=True, exist_ok=True)
        # A reused directory must not replace another run's evidence.
        for path in (self.request_path, self.stdout_path, self.stderr_path, self.metadata_path):
            if path.exists():
                raise FileExistsError(f'capture artifact already exists: {path}')
        with self.request_path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(specimen, indent=2) + '\n')
        self.stdout_path.touch(exist_ok=False)
        self.stderr_path.touch(exist_ok=False)
        self._record()

    def _record(self):
        self.metadata_path.write_text(json.dumps(self._metadata, indent=2) + '\n', encoding='utf-8')

    def start(self):
        if self._metadata['state'] != 'prepared':
            raise RuntimeError(f'capture already started: {self.out}')
        self._started = time.monotonic()
        self._metadata['started_at_unix_ns'] = time.time_ns()
        try:
            # The child writes directly to binary files, including on failure.
            # Parent file handles close immediately after spawn; no pipes fill.
            with self.stdout_path.open('wb') as stdout, self.stderr_path.open('wb') as stderr:
                self._process = subprocess.Popen(self.argv, stdout=stdout, stderr=stderr)
        except OSError as exc:
            self._metadata.update(state='launch_failed', launch_error=str(exc),
                                  elapsed_seconds=time.monotonic() - self._started)
            self._record()
            raise
        self._metadata.update(state='running', pid=self._process.pid)
        self._record()
        return self

    def poll(self):
        if self._process is None:
            raise RuntimeError(f'capture has no CLI process: {self.out}')
        rc = self._process.poll()
        if rc is not None and self._metadata['state'] != 'exited':
            self._metadata.update(state='exited', returncode=rc,
                                  exit_code=rc if rc >= 0 else None,
                                  term_signal=-rc if rc < 0 else None,
                                  elapsed_seconds=time.monotonic() - self._started)
            self._record()
        return rc

    def wait(self, *, timeout):
        if self._process is None:
            raise RuntimeError(f'capture has no CLI process: {self.out}')
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            self._metadata['harness_timeout_seconds'] = timeout
            self._record()
            raise HarnessTimeout(f'test harness CLI wait exceeded {timeout}s; '
                                 f'see {self.metadata_path}, {self.stdout_path}, and {self.stderr_path}') from exc
        return self.poll()

    @property
    def elapsed_seconds(self):
        """Elapsed time through the first observation of CLI exit."""
        return self._metadata['elapsed_seconds']

    def load_json(self):
        """Decode only when requested, including after a nonzero CLI exit."""
        if self.poll() is None:
            raise RuntimeError(f'CLI still running; raw output at {self.stdout_path}')
        try:
            return json.loads(self.stdout_path.read_text(encoding='utf-8'))
        except ValueError as exc:
            self._metadata['json_error'] = str(exc)
            self._record()
            raise ValueError(f'invalid JSON at {self.stdout_path}; stderr at {self.stderr_path}: {exc}') from exc

    def close(self):
        if self._process is None:
            return
        try:
            if self.poll() is None:
                self._metadata['cleanup_kill_requested'] = True
                self._record()
                self._process.kill()
                self._process.wait(timeout=5)
            self.poll()
        except (OSError, subprocess.TimeoutExpired) as exc:
            self._metadata['cleanup_error'] = str(exc)
            self._record()
            raise

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.close()
        except (OSError, subprocess.TimeoutExpired):
            # Preserve the test's original assertion; cleanup_error is durable.
            if exc is None:
                raise
        return False
