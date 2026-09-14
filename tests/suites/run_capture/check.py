"""Public capture API controls backed by independent bytes and OS observations."""
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import sys
import tempfile
import time

TESTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TESTS / 'lib'))
from run_capture import HarnessTimeout, RunCapture
sys.path.insert(0, str(TESTS / 'fixtures/exec'))
from control import ExitObserver

CLI = TESTS / 'fixtures/capture/cli.py'


class Gate:
    """A single CLI peer, observed through the kernel and the existing fixture."""
    def __init__(self, path):
        self.path = str(path)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(1)
        self.listener.settimeout(5)
        self.peer = None
        self.observer = ExitObserver()

    def accept(self):
        self.peer, _ = self.listener.accept()
        self.peer.settimeout(2)
        assert self.peer.recv(1) == b'r', 'fixture did not acknowledge flushed output'
        self.pid = self.peer.getsockopt(0, 2)  # macOS LOCAL_PEERPID, not a JSON claim.
        self.observer.watch(self.pid)
        self.ping()
        return self.pid

    def ping(self):
        self.peer.sendall(b'p')
        assert self.peer.recv(1) == b'a', 'fixture is not responsive'
        assert not self.observer.exits(), 'responsive fixture already has an exit event'

    def release(self):
        self.peer.sendall(b'q')

    def assert_reaped(self):
        self.observer.assert_stopped()
        try:
            os.waitpid(self.pid, os.WNOHANG)
        except ChildProcessError:
            return
        raise AssertionError('capture left its CLI running or unreaped')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.peer is not None:
            self.peer.close()
        self.listener.close()
        self.observer.close()


def specimen(stdout, stderr, *, exit_code=0, gate=None):
    result = {'stdout_hex': stdout.hex(), 'stderr_hex': stderr.hex(), 'exit_code': exit_code}
    if gate:
        result['gate'] = gate.path
    return result


def metadata(out):
    return json.loads((out / 'capture.json').read_text())


def exact_bytes(out, stdout, stderr):
    assert (out / 'run.json').read_bytes() == stdout, f'{out}: stdout changed'
    assert (out / 'pw.stderr').read_bytes() == stderr, f'{out}: stderr changed'


def main():
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    completed = []

    def passed(name):
        completed.append(name)
        print(f'{name}: ok', flush=True)

    # Expected bytes and exit statuses come from the control, not capture data.
    for name, rc in (('success', 0), ('nonzero', 7), ('pw_deadline', 1)):
        out = root / name
        envelope = {'marker': secrets.token_hex(12), 'result': {'ok': rc == 0}}
        if name == 'pw_deadline':
            envelope['data'] = {'runner_result': {'normalized_outcome': 'runner_timeout'}}
        stdout = (' \n' + json.dumps(envelope, indent=3) + '\n\n').encode()
        stderr = b'diagnostic\r\n\x00\xff' + secrets.token_bytes(32)
        spec = specimen(stdout, stderr, exit_code=rc)
        args = ['--timeout-ms', '10', '--literal', 'space ; $() " argument']
        with RunCapture(CLI, out, spec, cli_args=args) as run:
            assert run.wait(timeout=5) == rc
            exact_bytes(out, stdout, stderr)
            assert run.load_json() == envelope
            assert run.elapsed_seconds >= 0
        recorded = metadata(out)
        assert recorded['state'] == 'exited'
        assert recorded['returncode'] == recorded['exit_code'] == rc
        assert recorded['term_signal'] is None and recorded['harness_timeout_seconds'] is None
        assert recorded['cleanup_kill_requested'] is False
        receipt = json.loads((out / 'fixture.received.json').read_text())
        expected_argv = ['run', str(out / 'specimen.json'), *args]
        assert receipt == {'argv': expected_argv, 'specimen': spec}
        assert recorded['argv'] == [str(CLI), *expected_argv]
        assert json.loads((out / 'specimen.json').read_text()) == spec
        passed(name)

    for name, stdout in (('malformed_json', b'{"truncated":'), ('invalid_utf8', b'\xff')):
        out = root / name
        stderr = b'diagnostic before malformed output\n'
        with RunCapture(CLI, out, specimen(stdout, stderr)) as run:
            assert run.wait(timeout=5) == 0
            try:
                run.load_json()
            except ValueError as exc:
                assert str(out / 'run.json') in str(exc) and str(out / 'pw.stderr') in str(exc)
            else:
                raise AssertionError('invalid output was accepted as JSON')
        exact_bytes(out, stdout, stderr)
        assert metadata(out)['json_error']
        assert metadata(out)['returncode'] == 0
        passed(name)

    # The fixture is live before any timeout or signal. Socket acknowledgements
    # and EVFILT_PROC distinguish observations from capture's own metadata.
    with tempfile.TemporaryDirectory(prefix='pw-capture-', dir='/private/tmp') as work:
        for name in ('signal', 'harness_timeout', 'assertion_cleanup', 'unwaited_cleanup'):
            out = root / name
            stdout, stderr = b'partial:' + secrets.token_bytes(32), b'flushed before gate\n'
            with Gate(Path(work) / name) as gate:
                original_error = AssertionError('deliberate assertion while CLI is live')
                try:
                    with RunCapture(CLI, out, specimen(stdout, stderr, gate=gate)) as run:
                        pid = gate.accept()
                        assert metadata(out)['pid'] == pid
                        exact_bytes(out, stdout, stderr)
                        try:
                            run.load_json()
                        except RuntimeError as exc:
                            assert 'still running' in str(exc)
                        else:
                            raise AssertionError('accepted an unfinished capture')
                        if name == 'signal':
                            os.kill(pid, signal.SIGTERM)
                            assert run.wait(timeout=5) == -signal.SIGTERM
                        elif name == 'harness_timeout':
                            started = time.monotonic()
                            try:
                                run.wait(timeout=0.1)
                            except HarnessTimeout as exc:
                                assert 'test harness' in str(exc) and str(out / 'capture.json') in str(exc)
                            else:
                                raise AssertionError('held CLI did not trigger the harness deadline')
                            waited = time.monotonic() - started
                            assert 0.09 <= waited < 2
                            # Timing out must not manufacture a cleanup observation.
                            gate.ping()
                            assert metadata(out)['harness_timeout_seconds'] == 0.1
                            assert metadata(out)['cleanup_kill_requested'] is False
                        elif name == 'assertion_cleanup':
                            raise original_error
                        # unwaited_cleanup leaves a live process at context exit.
                except AssertionError as exc:
                    if name != 'assertion_cleanup' or exc is not original_error:
                        raise
                else:
                    assert name != 'assertion_cleanup', 'capture swallowed the original assertion'
                gate.assert_reaped()
                run.close()  # Repeated cleanup must preserve the first result.
            exact_bytes(out, stdout, stderr)
            recorded = metadata(out)
            expected_signal = signal.SIGTERM if name == 'signal' else signal.SIGKILL
            assert recorded['returncode'] == -expected_signal and recorded['term_signal'] == expected_signal
            assert recorded['exit_code'] is None
            assert recorded['cleanup_kill_requested'] is (name != 'signal')
            assert recorded['harness_timeout_seconds'] == (0.1 if name == 'harness_timeout' else None)
            if name == 'harness_timeout':
                assert recorded['elapsed_seconds'] >= waited, 'capture lost time spent at its deadline'
            assert recorded['cleanup_error'] is None
            passed(name)

        with Gate(Path(work) / 'A') as ga, Gate(Path(work) / 'B') as gb:
            a_out, b_out = root / 'overlap_A', root / 'overlap_B'
            a_bytes, b_bytes = json.dumps({'marker': secrets.token_hex(16)}).encode(), json.dumps({'marker': secrets.token_hex(16)}).encode()
            with RunCapture(CLI, a_out, specimen(a_bytes, b'A stderr', gate=ga)) as a, \
                 RunCapture(CLI, b_out, specimen(b_bytes, b'B stderr', gate=gb)) as b:
                assert ga.accept() != gb.accept()
                ga.ping()
                gb.ping()
                gb.release()
                assert b.wait(timeout=5) == 0
                b.close()
                gb.assert_reaped()
                ga.ping()
                assert a.poll() is None, 'finishing B also finished A'
                exact_bytes(a_out, a_bytes, b'A stderr')
                exact_bytes(b_out, b_bytes, b'B stderr')
                ga.release()
                assert a.wait(timeout=5) == 0
                ga.assert_reaped()
                assert a.load_json() == json.loads(a_bytes)
                assert b.load_json() == json.loads(b_bytes)
            assert not metadata(a_out)['cleanup_kill_requested'] and not metadata(b_out)['cleanup_kill_requested']
            passed('overlapping_captures')

    out = root / 'success'
    before = {path.name: path.read_bytes() for path in out.iterdir()}
    try:
        RunCapture(CLI, out, specimen(b'replacement', b'replacement'))
    except FileExistsError as exc:
        assert str(out) in str(exc)
    else:
        raise AssertionError('capture replaced an existing run')
    assert {path.name: path.read_bytes() for path in out.iterdir()} == before
    passed('reject_artifact_reuse')

    out = root / 'launch_failure'
    try:
        with RunCapture(root / 'missing-cli', out, specimen(b'', b'')):
            raise AssertionError('missing executable launched')
    except FileNotFoundError:
        pass
    recorded = metadata(out)
    assert recorded['state'] == 'launch_failed' and recorded['launch_error']
    assert recorded['pid'] is None and recorded['returncode'] is None
    exact_bytes(out, b'', b'')
    passed('launch_failure')
    (root / 'controls.json').write_text(json.dumps(completed, indent=2) + '\n')
    print(f'{len(completed)} capture controls passed')


if __name__ == '__main__':
    main()
