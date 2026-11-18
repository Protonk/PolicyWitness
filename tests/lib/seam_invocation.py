"""Submit a request with selected test-seam controls and retain what was requested.

A caller gives the ordinary request without the selected controls, the controls
as their own mapping and the remaining `run` arguments. The request is
delivered as given and the controls travel beside it: as one flag each after
`policy-witness test-input run` (the record's route is `experimental_cli`), or
as the one JSON object after `pw-runner-client run --experimental-controls`
(`experimental_client`). The executable decides which.

The mapping may be empty, and the request may carry its own `_test_overrides`
block: what the product does with either is the caller's experiment. A key
outside SELECTED_CONTROLS is refused before anything is written, and so is a
value with a NUL for the controller, whose command line cannot carry one; the
client's controls object can.

Each invocation owns `seam-invocations/<scenario>/` under the case's artifacts.
`invocation.json` is written before launch and completed when the exit is
observed; beside it are the ordinary request bytes, the controls, the delivered
bytes and the process's raw stdout and stderr. A scenario is recorded once in a
case.

The record holds what was requested and what the process wrote. It does not
establish that a control took effect: the reply's `test_overrides` echo and
the case's own observations are the caller's to read, and expectations,
independent effects and cleanup stay with the caller.

Shell cases use the command form, started as the other file helpers are:

    seam_invocation.py --scenario NAME --request FILE --controls JSON
        --delivered FILE --stdout FILE --stderr FILE -- EXECUTABLE [RUN_ARG...]

It exits with the submission's exit status, 128 plus the signal number after a
signal, or 70 when the adapter itself refuses or fails.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from run_capture import RunCapture

SELECTED_CONTROLS = (
    'worker_timeout_ms', 'worker_pre_ready_hang_ms', 'worker_post_apply_hang_ms',
    'worker_post_apply_kill_signal', 'worker_kill_before_publish_slot',
    'validator_executable_path', 'validator_io_timeout_ms', 'validator_total_timeout_ms')
ROUTES = {'cli': 'experimental_cli', 'client': 'experimental_client'}
CLIENT_CONTROLS = '--experimental-controls'
SCHEMA = 'pw-seam-invocation-1'
DIRECTORY = 'seam-invocations'
ENTRIES = {'policy-witness': 'cli', 'pw-runner-client': 'client'}
LIMITS = ('requested controls and raw process output only; this record does not establish '
          'that any control took effect')
ADAPTER_FAILURE = 70
_SCENARIO = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}')
_identities = {}


def encode(document):
    """The bytes RunCapture writes for a request."""
    return (json.dumps(document, indent=2) + '\n').encode()


def control_flags(controls):
    """The `test-input run` arguments for a mapping: one flag and one value per control, in the mapping's order."""
    return [item for key, value in controls.items() for item in ('--' + key.replace('_', '-'), str(value))]


def case_artifacts():
    artifacts = os.environ.get('PW_TEST_ARTIFACTS')
    if not artifacts:
        raise RuntimeError('PW_TEST_ARTIFACTS is unset: a seam invocation is recorded under its case artifacts; '
                           'start the case through tests/run.sh')
    return Path(artifacts).resolve()


def scenario_for(directory):
    """A directory's path below the case artifacts, joined with dots.

    For a shared helper whose artifact directory already identifies the
    invocation within the case."""
    relative = Path(directory).resolve().relative_to(case_artifacts())
    if not relative.parts:
        raise ValueError(f'{directory} is the case artifacts directory itself')
    return '.'.join(relative.parts)


def app_identity(executable):
    """The app holding the executable and the build its controller reports."""
    macos = Path(executable).parent
    bundled = macos.name == 'MacOS' and macos.parent.name == 'Contents'
    controller = macos / 'policy-witness'
    key = str(controller)
    if key not in _identities:
        record = dict(app_path=str(macos.parents[1]) if bundled else None, controller=key,
                      version_argv=[key, '--version'], version_exit_status=None,
                      build=None, build_contract=None, error=None)
        try:
            probe = subprocess.run(record['version_argv'], capture_output=True, timeout=30)
            record['version_exit_status'] = probe.returncode
            build = json.loads(probe.stdout)['build']
            record.update(build=build, build_contract=build['contract'])
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        _identities[key] = record
    return dict(_identities[key])


def _blob(path):
    data = Path(path).read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


class _Record:
    """The evidence directory of one invocation; no reading of its outcome."""

    def __init__(self, executable, scenario, ordinary, request, controls):
        if not isinstance(scenario, str) or not _SCENARIO.fullmatch(scenario):
            raise ValueError(f'invalid seam scenario identity: {scenario!r}')
        if not isinstance(request, dict):
            raise ValueError('the ordinary request must be a JSON object')
        if not isinstance(controls, dict):
            raise ValueError('seam controls must be a mapping')
        controls = dict(controls)
        unselected = sorted(set(controls) - set(SELECTED_CONTROLS))
        if unselected:
            raise ValueError(f'seam controls must be a mapping of selected controls; unselected: {unselected}')
        entry = ENTRIES.get(Path(executable).name)
        if entry is None:
            raise ValueError(f'neither the controller nor the runner client: {executable}')
        if entry == 'cli' and any('\0' in str(value) for value in controls.values()):
            raise ValueError('a command-line argument cannot carry a NUL; submit this control through the runner client')
        self.entry = entry
        self.controls = controls
        self.delivered = dict(request)
        self.directory = case_artifacts() / DIRECTORY / scenario
        identity = app_identity(executable)
        try:
            self.directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise FileExistsError(f'seam scenario already recorded in this case: {self.directory}') from None
        (self.directory / 'ordinary-request.json').write_bytes(ordinary)
        (self.directory / 'controls.json').write_bytes(encode(controls))
        self.value = dict(
            schema=SCHEMA, scenario=scenario, limits=LIMITS,
            case=dict(suite=os.environ.get('PW_TEST_SUITE'), test_id=os.environ.get('PW_TEST_ID'),
                      run_id=os.environ.get('PW_TEST_RUN_ID')),
            requested_route=ROUTES[entry], entry=entry,
            requested_controls=controls,
            app=identity, executable=str(executable), argv=None,
            ordinary_request=dict(file='ordinary-request.json', **_blob(self.directory / 'ordinary-request.json')),
            delivered_request=None, state='prepared', pid=None, launch_error=None,
            start_unix_ns=None, start_monotonic_ns=None, exit_observed_monotonic_ns=None,
            returncode=None, exit_code=None, term_signal=None, stdout=None, stderr=None, companion=None)
        self._write()

    def _write(self):
        (self.directory / 'invocation.json').write_text(json.dumps(self.value, indent=2) + '\n', encoding='utf-8')

    def intend(self, argv, delivered, *, channel, path=None, companion=None):
        (self.directory / 'delivered-request.json').write_bytes(delivered)
        self.value.update(
            argv=[str(item) for item in argv], state='intended', companion=companion,
            delivered_request=dict(file='delivered-request.json', channel=channel,
                                   path=None if path is None else str(path),
                                   **_blob(self.directory / 'delivered-request.json')))
        self._write()

    def launching(self):
        if self.value['state'] != 'intended':
            raise RuntimeError(f"seam invocation is {self.value['state']}, not ready to launch: {self.directory}")
        path = self.value['delivered_request']['path']
        if path is not None and _blob(path)['sha256'] != self.value['delivered_request']['sha256']:
            raise RuntimeError(f'delivered request changed after its intent was recorded: {path}')
        self.value.update(start_unix_ns=time.time_ns(), start_monotonic_ns=time.monotonic_ns())

    def launch_failed(self, error):
        self.value.update(state='launch_failed', launch_error=str(error))
        self._write()

    def launched(self, pid):
        self.value.update(state='launched', pid=pid)
        self._write()

    def exited(self, returncode, stdout, stderr):
        if self.value['state'] != 'launched':
            return
        self.value['exit_observed_monotonic_ns'] = time.monotonic_ns()
        for name, source in (('stdout', stdout), ('stderr', stderr)):
            target = self.directory / name
            if Path(source).resolve() != target:
                shutil.copyfile(source, target)
            self.value[name] = dict(file=name, source=str(source), **_blob(target))
        self.value.update(state='exited', returncode=returncode,
                          exit_code=returncode if returncode >= 0 else None,
                          term_signal=-returncode if returncode < 0 else None)
        self._write()


class SeamCapture(RunCapture):
    """RunCapture for a submission with selected controls.

    The capture directory, waits, decoding and cleanup are RunCapture's:
    `specimen.json` there is the delivered request. `seam` is the evidence
    directory."""

    def __init__(self, pw, out, request, *, controls, scenario, cli_args=()):
        if ENTRIES.get(Path(pw).name) == 'client':
            raise ValueError(f'a capture submits through the controller; use Submission for the client: {pw}')
        self._seam = _Record(pw, scenario, encode(request), request, controls)
        self.seam = self._seam.directory
        super().__init__(pw, out, self._seam.delivered, cli_args=cli_args)
        self.argv = [str(pw), 'test-input', 'run', str(self.request_path),
                     *control_flags(self._seam.controls), *map(str, cli_args)]
        self._metadata['argv'] = self.argv
        self._record()
        self._seam.intend(self.argv, self.request_path.read_bytes(), channel='path', path=self.request_path,
                          companion=dict(kind='run_capture', directory=str(self.out)))

    def start(self):
        if self._seam.value['state'] != 'intended':
            return super().start()
        self._seam.launching()
        try:
            super().start()
        except OSError as exc:
            self._seam.launch_failed(exc)
            raise
        self._seam.launched(self.pid)
        return self

    def poll(self):
        rc = super().poll()
        if rc is not None:
            self._seam.exited(rc, self.stdout_path, self.stderr_path)
        return rc


class Submission:
    """One submission as a process the caller starts, polls and waits for.

    `run_args` is everything after the controls, in the caller's order,
    including the request path or `-`. The controls precede them: the
    controller's flags after `test-input run`, or the client's one controls
    object after `run`. The adapter writes the delivered request to
    `request_path`, or to the process's standard input when no path is given.
    `delivered` is the document the process receives; `ordinary_bytes` are the
    request's own bytes when it came from a file, and they are delivered
    unchanged."""

    def __init__(self, executable, scenario, request, controls, *, run_args=(), request_path=None,
                 encode=encode, ordinary_bytes=None):
        self.delivered_bytes = encode(request) if ordinary_bytes is None else ordinary_bytes
        self._seam = _Record(executable, scenario, self.delivered_bytes, request, controls)
        self.seam = self._seam.directory
        self.delivered = self._seam.delivered
        command = (['test-input', 'run', *control_flags(self._seam.controls)] if self._seam.entry == 'cli'
                   else ['run', CLIENT_CONTROLS, json.dumps(self._seam.controls)])
        self.argv = [str(executable), *command, *map(str, run_args)]
        self._stdin = request_path is None
        if request_path is not None:
            Path(request_path).write_bytes(self.delivered_bytes)
        self._seam.intend(self.argv, self.delivered_bytes, channel='stdin' if self._stdin else 'path', path=request_path)
        self._process = None

    def start(self, *, stdout=None, stderr=None, **popen):
        """Launch with stdout and stderr written to the named files (the evidence directory's by default)."""
        self._seam.launching()
        self._stdout = Path(stdout) if stdout is not None else self.seam / 'stdout'
        self._stderr = Path(stderr) if stderr is not None else self.seam / 'stderr'
        if self._stdin:
            popen['stdin'] = subprocess.PIPE
        try:
            with self._stdout.open('wb') as out, self._stderr.open('wb') as err:
                self._process = subprocess.Popen(self.argv, stdout=out, stderr=err, **popen)
        except OSError as exc:
            self._seam.launch_failed(exc)
            raise
        self._seam.launched(self._process.pid)
        if self._stdin:
            self._process.stdin.write(self.delivered_bytes)
            self._process.stdin.close()
        return self

    @property
    def pid(self):
        return self._process.pid

    def poll(self):
        rc = self._process.poll()
        if rc is not None:
            self._seam.exited(rc, self._stdout, self._stderr)
        return rc

    def wait(self, timeout=None):
        self._process.wait(timeout=timeout)
        return self.poll()

    def run(self, *, timeout=None, **popen):
        """Start, wait and return the completed process with its raw output, killing it at the timeout."""
        self.start(**popen)
        try:
            rc = self.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self.wait()
            raise
        return subprocess.CompletedProcess(self.argv, rc, self._stdout.read_bytes(), self._stderr.read_bytes())


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(ADAPTER_FAILURE, f'{self.prog}: error: {message}\n')


def main(argv=None):
    parser = _Parser(description='Submit one request with selected test-seam controls.', allow_abbrev=False)
    parser.add_argument('--scenario', required=True, help='identity of this invocation, unique within the case')
    parser.add_argument('--request', required=True, type=Path, help='the ordinary request, without the selected controls')
    parser.add_argument('--controls', required=True, help='JSON object of selected controls')
    parser.add_argument('--delivered', required=True, type=Path, help='where to write the delivered request')
    parser.add_argument('--stdout', required=True, type=Path)
    parser.add_argument('--stderr', required=True, type=Path)
    parser.add_argument('command', nargs=argparse.REMAINDER, metavar='-- EXECUTABLE [RUN_ARG...]',
                        help='the controller or runner client, then the arguments after the controls, '
                             'including the delivered request path')
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('missing EXECUTABLE')
    try:
        ordinary = args.request.read_bytes()
        submission = Submission(command[0], args.scenario, json.loads(ordinary), json.loads(args.controls),
                                run_args=command[1:], request_path=args.delivered, ordinary_bytes=ordinary)
        rc = submission.start(stdout=args.stdout, stderr=args.stderr).wait()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'seam_invocation: {type(exc).__name__}: {exc}', file=sys.stderr)
        return ADAPTER_FAILURE
    return rc if rc >= 0 else 128 - rc


if __name__ == '__main__':
    sys.exit(main())
