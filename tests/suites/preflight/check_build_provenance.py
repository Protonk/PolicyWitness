"""Offline controls over the build's provenance helpers: parsing, state decisions and lock ownership.

These exercise tests/lib/build_provenance.py, tests/lib/checkout_lock.py and
tests/lib/signer_check.py directly, with constructed inputs and disposable
directories. Observed probes use real tools where one is needed (clang for a
Mach-O); every other expectation is independent of the helper under test.
The build-driving controls in the opt-in preflight cases establish the same
refusals through the unchanged script.
"""
import copy
import errno
from contextlib import contextmanager, ExitStack, redirect_stderr, redirect_stdout
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
import build_provenance as prov
import cargo_config
import checkout_lock
import output_target
import signer_check
import fixture_bundle

PYTHON = sys.executable


@contextmanager
def environment(env):
    """os.environ replaced for the block, so an in-process helper reads the claim a control set up."""
    saved = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def run_main(argv, env=None):
    """build_provenance.main under a controlled environment, with its streams captured."""
    out, err = io.StringIO(), io.StringIO()
    saved = dict(os.environ)
    try:
        if env is not None:
            os.environ.clear()
            os.environ.update(env)
        with redirect_stdout(out), redirect_stderr(err):
            status = prov.main(argv)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return status, out.getvalue(), err.getvalue()


def fake_observation(**overrides):
    """A toolchain observation shaped like observe_toolchain's, with every required field present."""
    def ok(**fields):
        return dict(status='ok', **fields)
    base = dict(
        developer_dir=ok(value='/Applications/Xcode.app/Contents/Developer', source='xcode-select'),
        sdk=dict(path=ok(line='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk'),
                 version=ok(line='27.0'), build=ok(line='26A425')),
        xcode=dict(status='ok', version='27.0', build='27A266a'),
        compilers={'c': dict(configured=dict(command=['cc'], id='clang', version='21.0.0', full_version='Apple clang version 21.0.0 (clang-2100.3.34.2)'),
                             observed=ok(command=['cc'], identity='Apple clang version 21.0.0 (clang-2100.3.34.2)'))},
        rustc=ok(command='/opt/homebrew/opt/rustup/bin/rustc', exact_command='/opt/homebrew/opt/rustup/bin/rustc', source='PATH',
                 identity='rustc 1.99.0 (b940084d7 2026-09-28)', release='1.99.0', commit_hash='b940084d7', host='aarch64-apple-darwin',
                 llvm_version='23.1.1', wrappers={}, selection_environment={}, configuration_files=[], unresolved_configuration=[]),
        cargo=ok(command='/opt/homebrew/opt/rustup/bin/cargo', version='cargo 1.99.0'),
        meson=ok(command='/opt/homebrew/bin/meson', version='1.12.1'),
        ninja=ok(command='/opt/homebrew/bin/ninja', version='1.13.2'),
        xpc=False)
    for key, value in overrides.items():
        base[key] = value
    return base


def write_compilers(builddir, swift=False):
    host = {'c': dict(id='clang', exelist=['cc'], version='21.0.0', full_version='Apple clang version 21.0.0 (clang-2100.3.34.2)')}
    if swift:
        host['swift'] = dict(id='llvm', exelist=['swiftc'], version='6.4', full_version=None)
    (builddir / 'meson-info').mkdir(parents=True, exist_ok=True)
    (builddir / 'meson-info/intro-compilers.json').write_text(json.dumps(dict(host=host)))
    (builddir / 'meson-info/intro-buildoptions.json').write_text(json.dumps([dict(name='xpc', value=swift), dict(name='inspection', value=True)]))
    write_configured_output(builddir, swift)


def write_configured_output(builddir, swift=False, cpu_family='aarch64', arch='arm64', link_arch='arm64', swift_target='arm64-apple-macosx26.0'):
    """Meson's introspection of the machines and the targets' effective arguments, shaped as Meson 1.12 writes them."""
    machine = lambda family: dict(system='darwin', cpu_family=family, cpu=family, endian='little')
    (builddir / 'meson-info/intro-machines.json').write_text(json.dumps(dict(host=machine(cpu_family), build=machine('aarch64'),
                                                                              target=machine(cpu_family))))
    c = lambda name: dict(name=name, type='executable', target_sources=[
        dict(language='c', compiler=['cc'], parameters=['-I.', '-O2', '-arch', arch, '-mmacosx-version-min=26.0']),
        dict(language=None, compiler=None, parameters=['-Wl,-headerpad_max_install_names', '-arch', link_arch, '-mmacosx-version-min=26.0'])])
    targets = [c('sb_api_validator'), c('pw-probe-runner'), c('pw-extension-issuer')]
    if swift:
        targets.append(dict(name='PWCWorkerShim', type='static library', target_sources=[
            dict(language='c', compiler=['cc'], parameters=['-arch', arch, '-mmacosx-version-min=26.0']),
            dict(language=None, compiler=None, parameters=['csr'])]))
        targets.append(dict(name='PWRunner', type='executable', target_sources=[
            dict(language='swift', compiler=['swiftc'], parameters=['-module-name', 'PWRunner', '-target', swift_target])]))
    (builddir / 'meson-info/intro-targets.json').write_text(json.dumps(targets))


NAMES = ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')
LIB = str(ROOT / 'tests/lib')
CLAIM = dict(fd=checkout_lock.ENV_FD, root=checkout_lock.ENV_ROOT, nonce=checkout_lock.ENV_NONCE, channel=checkout_lock.ENV_CHANNEL)


def clean_env():
    """This process's environment without the claim the dispatcher passed for the real checkout."""
    return {k: v for k, v in os.environ.items() if not k.startswith(('PW_CHECKOUT_LOCK_', 'PW_ENV_WITNESS_'))}


def witnessed(env):
    return dict(env, **{'PW_ENV_WITNESS_' + name: 's' + env[name] if name in env else 'u' for name in NAMES},
                PYTHONCOERCECLOCALE='0')


def own(test, root):
    """An in-process owner of a disposable checkout's lock for the test's duration: its scope and a claimed environment."""
    stack = ExitStack()
    test.addCleanup(stack.close)
    scope = stack.enter_context(checkout_lock.owned(root, env=clean_env()))
    return scope, scope.child_env(witnessed({k: v for k, v in clean_env().items() if k not in NAMES}))


def lock_free(root):
    """Whether the lock can be taken now, observed with a separate open from outside every owner."""
    path = Path(root) / checkout_lock.LOCK
    if not path.exists():
        return True
    fd = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False
    finally:
        os.close(fd)


def wait_for(condition, timeout=20, message='condition'):
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise AssertionError(f'timed out waiting for {message}')
        time.sleep(0.05)


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


# A protected child's wrapper: it runs a grandchild that waits for a release file, passing the claim's descriptors on
# ('pass') or relying on Python's default, which closes them ('drop').
WRAPPER = textwrap.dedent('''
    import json, os, subprocess, sys
    sys.path.insert(0, sys.argv[1])
    import checkout_lock
    mode, release, report = sys.argv[2], sys.argv[3], sys.argv[4]
    waiter = ('import os, sys, time\\n'
              'deadline = time.monotonic() + 60\\n'
              'while not os.path.exists(sys.argv[1]) and time.monotonic() < deadline:\\n'
              '    time.sleep(0.05)\\n')
    fds = checkout_lock.inherited_fds() if mode == 'pass' else ()
    child = subprocess.Popen([sys.executable, '-B', '-c', waiter, release], pass_fds=fds)
    with open(report, 'w') as stream:
        json.dump(dict(wrapper=os.getpid(), grandchild=child.pid, passed=list(fds)), stream)
    child.wait()
''')

FAKE_OWNER = textwrap.dedent('''
    import json, os, socket, subprocess, sys, time
    sys.path.insert(0, sys.argv[1])
    import checkout_lock
    root, mode, client, result, release = sys.argv[2:7]
    fd, record = checkout_lock.acquire(root)
    server, end = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
    checkout_lock.bind_channel(fd, end)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('PW_CHECKOUT_LOCK_', 'PW_ENV_WITNESS_'))}
    for name in ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE'):
        env.pop(name, None)
        env['PW_ENV_WITNESS_' + name] = 'u'
    env.update(PW_CHECKOUT_LOCK_ROOT=root, PW_CHECKOUT_LOCK_NONCE=record['nonce'], PW_CHECKOUT_LOCK_CHANNEL=str(end.fileno()))
    subprocess.Popen([sys.executable, '-B', client, sys.argv[1], root, result, release], env=env, pass_fds=(end.fileno(),))
    end.close()
    message, fds, _, _ = socket.recv_fds(server, 65536, 4)
    print('received', flush=True)
    if mode == 'exit':
        os._exit(0)   # the lock, the channel and the reply socket close without an answer
    time.sleep(60)    # the control kills this owner while the client waits
''')

ADMISSION_CLIENT = textwrap.dedent('''
    import fcntl, json, os, sys, time
    sys.path.insert(0, sys.argv[1])
    import build_provenance, checkout_lock
    root, result, release = sys.argv[2:5]
    out = {}
    try:
        checkout_lock.admit(root, timeout=20)
        out['admission'] = 'admitted'
    except checkout_lock.Refusal as exc:
        out['admission'] = 'refused: ' + str(exc)
    # A session helper under the same claim is refused as well and writes nothing.
    out['session_start'] = build_provenance.main(['session-start', '--root', root, '--describe', 'x', '--commit', 'x',
                                                  '--version', '0', '--build-number', '0'])
    lock = os.open(os.path.join(root, 'tests/.checkout.lock'), os.O_RDWR)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        out['free_from_client'] = True
    except BlockingIOError:
        out['free_from_client'] = False
    finally:
        os.close(lock)
    with open(result + '.part', 'w') as stream:
        json.dump(out, stream)
    os.rename(result + '.part', result)
    deadline = time.monotonic() + 30
    while not os.path.exists(release) and time.monotonic() < deadline:
        time.sleep(0.05)
''')


class LockTests(unittest.TestCase):
    def test_unrelated_socket_cannot_handoff_a_copied_nonce_and_unheld_descriptor(self):
        # The impostor is a separate process. It knows the public record and
        # opens the right inode, but never owned its locked open description.
        impostor = self.script('impostor.py', textwrap.dedent('''
            import json, os, socket, sys, threading
            sys.path.insert(0, sys.argv[1])
            import checkout_lock
            root = sys.argv[2]
            fd = os.open(root + '/tests/.checkout.lock', os.O_RDONLY)
            record = checkout_lock.read_owner(fd)
            server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
            def answer():
                _, fds, _, _ = socket.recv_fds(server, 65536, 1)
                with socket.socket(fileno=fds[0]) as reply:
                    info = os.fstat(fd)
                    message = dict(v=1, status='ok', nonce=record['nonce'], device=info.st_dev, inode=info.st_ino)
                    socket.send_fds(reply, [json.dumps(message).encode()], [fd])
            threading.Thread(target=answer, daemon=True).start()
            env = dict(PW_CHECKOUT_LOCK_ROOT=root, PW_CHECKOUT_LOCK_NONCE=record['nonce'], PW_CHECKOUT_LOCK_CHANNEL=str(client.fileno()))
            try:
                admission = checkout_lock.admit(root, env, timeout=1)
                admission.close()
                print('ADMITTED')
            except checkout_lock.Refusal as exc:
                print('REFUSED: ' + str(exc))
        '''))
        with checkout_lock.owned(self.root, env=clean_env()):
            result = subprocess.run([PYTHON, '-B', str(impostor), LIB, str(self.root)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('REFUSED: the channel was not created by the acquisition owner', result.stdout)
            self.assertFalse(lock_free(self.root))

    def test_admission_send_is_bounded_when_the_channel_queue_is_full(self):
        fd, record = checkout_lock.acquire(self.root)
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
        checkout_lock.bind_channel(fd, client)
        try:
            while True:
                try:
                    client.send(b'x' * 1024, socket.MSG_DONTWAIT)
                except OSError as exc:
                    self.assertIn(exc.errno, (errno.EAGAIN, errno.ENOBUFS))
                    break
            env = {CLAIM['root']: str(self.root), CLAIM['nonce']: record['nonce'], CLAIM['channel']: str(client.fileno())}
            started = time.monotonic()
            with self.assertRaises(checkout_lock.Refusal):
                checkout_lock.admit(self.root, env, timeout=0.1)
            self.assertLess(time.monotonic() - started, 2)
            self.assertFalse(lock_free(self.root))
        finally:
            server.close()
            client.close()
            os.close(fd)

    def test_nested_scope_cannot_admit_after_acquisition_owner_exits(self):
        ready, proceed, result = (self.work / name for name in ('nested-ready', 'nested-proceed', 'nested-result'))
        nested = self.script('nested.py', textwrap.dedent('''
            import os, pathlib, sys, time
            sys.path.insert(0, sys.argv[1])
            import checkout_lock
            root, ready, proceed, result = map(pathlib.Path, sys.argv[2:])
            with checkout_lock.owned(root) as scope:
                ready.write_text(str(os.getpid()))
                deadline = time.monotonic() + 20
                while not proceed.exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                try:
                    checkout_lock.admit(root, scope.child_env(), timeout=1).close()
                    result.write_text('admitted')
                except checkout_lock.Refusal:
                    result.write_text('refused')
        '''))
        owner = subprocess.Popen([*self.launcher, PYTHON, '-B', str(nested), LIB, str(self.root), str(ready), str(proceed), str(result)],
                                 env=clean_env(), start_new_session=True)
        try:
            wait_for(ready.exists)
            owner.kill()
            owner.wait(timeout=5)
            self.assertFalse(lock_free(self.root), 'the nested scope must still hold the old acquisition')
            proceed.touch()
            wait_for(result.exists)
            self.assertEqual(result.read_text(), 'refused')
            wait_for(lambda: lock_free(self.root))
        finally:
            proceed.touch()
            if owner.poll() is None:
                owner.kill()
                owner.wait()

    def test_another_socket_from_the_owner_process_is_not_the_acquisition_channel(self):
        with checkout_lock.owned(self.root, env=clean_env()) as scope:
            server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
            try:
                env = dict(scope.child_env(), **{CLAIM['channel']: str(client.fileno())})
                with self.assertRaisesRegex(checkout_lock.Refusal, 'does not belong to this acquisition'):
                    checkout_lock.admit(self.root, env, timeout=.1)
            finally:
                server.close()
                client.close()

    def test_cancellation_bounds_a_command_and_descendant_that_ignore_signals(self):
        # Shorten only the grace periods, so a broken supervisor fails promptly.
        launcher = ('import sys; sys.path.insert(0, sys.argv.pop(1)); import checkout_lock; '
                    'checkout_lock.GROUP_GRACE=.2; checkout_lock.KILL_GRACE=2; sys.exit(checkout_lock.main())')
        stubborn = self.script('stubborn.py', textwrap.dedent('''
            import json, os, signal, subprocess, sys, time
            sys.path.insert(0, sys.argv[1])
            import checkout_lock
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], pass_fds=checkout_lock.inherited_fds())
            with open(sys.argv[2], 'w') as stream:
                json.dump([os.getpid(), child.pid], stream)
            time.sleep(30)
        '''))
        for signum in (signal.SIGINT, signal.SIGTERM):
            report = self.work / f'stubborn-{signum}.json'
            owner = subprocess.Popen([PYTHON, '-B', '-c', launcher, LIB, '--root', str(self.root), '--',
                                      PYTHON, '-B', str(stubborn), LIB, str(report)], env=witnessed(clean_env()), start_new_session=True)
            pids = []
            try:
                wait_for(report.exists)
                wait_for(lambda: report.read_text().endswith(']'))
                pids = json.loads(report.read_text())
                self.assertFalse(lock_free(self.root))
                os.kill(owner.pid, signum)
                self.assertEqual(owner.wait(timeout=5), 128 + signum)
                wait_for(lambda: all(not alive(pid) for pid in pids), timeout=5)
                self.assertTrue(lock_free(self.root))
            finally:
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if owner.poll() is None:
                    owner.kill()
                    owner.wait()

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-lock-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        self.root = self.work / 'checkout'
        (self.root / 'tests').mkdir(parents=True)
        self.lock = self.root / checkout_lock.LOCK
        self.launcher = ['/bin/bash', str(ROOT / 'tests/lib/checkout_lock.sh'), '--root', str(self.root), '--']

    def script(self, name, text):
        path = self.work / name
        path.write_text(text)
        return path

    def admit(self, claim, pass_fds=(), root=None):
        """checkout_lock.admit in a child given only this claim; its status and report. After a refusal the child also
        reports whether it could take the lock through a separate open, which it cannot while anything holds it."""
        script = textwrap.dedent(f'''
            import fcntl, os, sys
            sys.path.insert(0, {LIB!r})
            import checkout_lock
            try:
                admission = checkout_lock.admit({str(root or self.root)!r}, timeout=10)
                print('admitted', admission.nonce)
            except checkout_lock.Refusal as exc:
                lock = os.open({str(self.lock)!r}, os.O_RDWR)
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    free = 'free'
                except BlockingIOError:
                    free = 'held'
                finally:
                    os.close(lock)
                print('refused', free, exc)
                raise SystemExit(2)
        ''')
        env = dict(clean_env(), **claim)
        result = subprocess.run([PYTHON, '-B', '-c', script], pass_fds=pass_fds, env=env, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout.strip() + result.stderr.strip()

    def test_claims_are_admitted_only_by_a_live_owners_handoff(self):
        other = self.work / 'other-worktree'
        (other / 'tests').mkdir(parents=True)
        with checkout_lock.owned(other, env=clean_env()):
            pass  # the other worktree has a lock file of its own, never held below
        with checkout_lock.owned(self.root, env=clean_env()) as scope:
            inode, record = self.lock.stat().st_ino, self.lock.read_bytes()
            claim = {k: v for k, v in scope.child_env({}).items()}
            status, text = self.admit(claim, scope.pass_fds())
            self.assertEqual(status, 0, text)
            self.assertIn('admitted ' + scope.nonce, text)
            separate = os.open(self.lock, os.O_RDWR)
            os.set_inheritable(separate, True)
            try:
                cases = {
                    'stale claim (never passed)': (claim, (), None, 'is not open in this process'),
                    'closed descriptors': (dict(claim, **{CLAIM['channel']: '250', CLAIM['fd']: '251'}), (), None, 'is not open in this process'),
                    'another open on the lock inode': (dict(claim, **{CLAIM['channel']: str(separate), CLAIM['fd']: str(separate)}), (separate,), None,
                                                       'is not an owner channel'),
                    'wrong nonce over the real channel': (dict(claim, **{CLAIM['nonce']: 'f' * 32}), scope.pass_fds(), None, 'another acquisition'),
                    'another worktree': (dict(claim, **{CLAIM['root']: str(other)}), scope.pass_fds(), None, 'another checkout'),
                    'another worktree asked of this owner': (dict(claim, **{CLAIM['root']: str(other)}), scope.pass_fds(), other, 'does not belong to this acquisition'),
                    'malformed claim without a channel': ({CLAIM['fd']: str(scope.fd), CLAIM['root']: str(self.root), CLAIM['nonce']: scope.nonce},
                                                          (scope.fd,), None, 'not set'),
                }
                for label, (case, fds, root, needle) in cases.items():
                    with self.subTest(claim=label):
                        status, text = self.admit(case, fds, root)
                        self.assertEqual(status, 2, text)
                        self.assertIn(needle, text)
                        self.assertIn('refused held', text, 'the real owner still holds the lock')
            finally:
                os.close(separate)
            self.assertFalse(lock_free(self.root), 'refused claims left the real hold in place')
            self.assertEqual((self.lock.stat().st_ino, self.lock.read_bytes()), (inode, record), 'refused claims left the lock file')
            with self.assertRaises(checkout_lock.Refusal) as busy:
                checkout_lock.acquire(self.root)
            self.assertIn('checkout busy', str(busy.exception))
            result = subprocess.run([*self.launcher, '/usr/bin/true'], env=clean_env(), capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertIn('checkout busy', result.stderr)
        self.assertTrue(lock_free(self.root))
        self.assertTrue(lock_free(other), 'the other worktree was never held')
        # An unheld descriptor on the lock inode while the lock is free is no claim, and admission takes no hold:
        # the child's own separate open can take the lock while it runs.
        unheld = os.open(self.lock, os.O_RDWR)
        os.set_inheritable(unheld, True)
        try:
            record = json.loads(self.lock.read_text())
            status, text = self.admit({CLAIM['fd']: str(unheld), CLAIM['channel']: str(unheld), CLAIM['root']: str(self.root),
                                       CLAIM['nonce']: record['nonce']}, (unheld,))
        finally:
            os.close(unheld)
        self.assertEqual(status, 2, text)
        self.assertIn('refused free', text, 'the refused claim created a hold')
        self.assertTrue(lock_free(self.root))
        # Nesting: a launched command's nested launcher is admitted by its owner and serves its own command.
        nested = (f'{PYTHON} -B {LIB}/checkout_lock.py --verify --root {self.root} && '
                  f'{PYTHON} -B {LIB}/checkout_lock.py --root {self.root} -- /bin/sh -c '
                  f'"{PYTHON} -B {LIB}/checkout_lock.py --verify --root {self.root} && echo nested"')
        result = subprocess.run([*self.launcher, '/bin/sh', '-c', nested], env=clean_env(), capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr.count('ok: admitted by the owner'), 2, result.stderr)
        self.assertIn('nested', result.stdout)
        self.assertTrue(lock_free(self.root))

    def test_owner_exit_during_admission_creates_no_hold(self):
        owner, client = self.script('fake_owner.py', FAKE_OWNER), self.script('client.py', ADMISSION_CLIENT)
        for mode in ('exit', 'killed'):
            with self.subTest(owner=mode):
                result, release = self.work / f'{mode}.json', self.work / f'{mode}.release'
                process = subprocess.Popen([PYTHON, '-B', str(owner), LIB, str(self.root), mode, str(client), str(result), str(release)],
                                           env=clean_env(), stdout=subprocess.PIPE, text=True)
                try:
                    self.assertEqual(process.stdout.readline().strip(), 'received', 'the owner never received the request')
                    if mode == 'killed':
                        process.kill()
                    process.wait(timeout=10)
                    wait_for(result.exists, message='the client result')
                    out = json.loads(result.read_text())
                    self.assertTrue(out['admission'].startswith('refused: the owner of this claim is gone'), out)
                    self.assertEqual(out['session_start'], 2, out)
                    self.assertTrue(out['free_from_client'], 'the client holds the lock under the old acquisition')
                    self.assertTrue(lock_free(self.root), 'a hold outlived the owner without a protected child')
                    self.assertFalse((self.root / 'controller/target/pw-build-session.json').exists())
                finally:
                    release.touch()
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    process.stdout.close()

    def lifetime(self, mode):
        """Kill the owner and the wrapper while a grandchild runs; what an outside observer sees."""
        report, release = self.work / f'{mode}-pids.json', self.work / f'{mode}.release'
        wrapper = self.script('wrapper.py', WRAPPER)
        owner = subprocess.Popen([*self.launcher, PYTHON, '-B', str(wrapper), LIB, mode, str(release), str(report)],
                                 env=clean_env(), start_new_session=True)
        observed = {}
        try:
            wait_for(report.exists, message='the wrapper')
            wait_for(lambda: report.read_text().endswith('}'), message='the wrapper report')
            pids = json.loads(report.read_text())
            observed['held_while_running'] = not lock_free(self.root)
            os.kill(owner.pid, signal.SIGKILL)
            owner.wait(timeout=10)
            os.kill(pids['wrapper'], signal.SIGKILL)
            wait_for(lambda: not alive(pids['wrapper']), message='the wrapper exit')
            observed['grandchild_alive_after_kills'] = alive(pids['grandchild'])
            observed['held_after_kill'] = not lock_free(self.root)
            competing = subprocess.run([*self.launcher, '/usr/bin/true'], env=clean_env(), capture_output=True, text=True, timeout=30)
            observed['competitor_refused'] = competing.returncode == 2 and 'checkout busy' in competing.stderr
            release.touch()
            wait_for(lambda: not alive(pids['grandchild']), message='the grandchild exit')
            observed['released_after_last_exit'] = lock_free(self.root)
            after = subprocess.run([*self.launcher, '/usr/bin/true'], env=clean_env(), capture_output=True, text=True, timeout=30)
            observed['competitor_after'] = after.returncode
        finally:
            release.touch()
            if owner.poll() is None:
                owner.kill()
                owner.wait()
        return observed

    @staticmethod
    def check_lifetime(observed):
        assert observed['held_while_running'], observed
        assert observed['grandchild_alive_after_kills'], observed
        assert observed['held_after_kill'], ('the killed owner and wrapper released a hold the grandchild needs', observed)
        assert observed['competitor_refused'], observed
        assert observed['released_after_last_exit'] and observed['competitor_after'] == 0, observed

    def test_protected_children_keep_the_hold_after_the_owner_dies(self):
        passing = self.lifetime('pass')
        self.check_lifetime(passing)
        # A wrapper that drops the passed descriptor (Python's default) must fail the same control.
        dropping = self.lifetime('drop')
        with self.assertRaises(AssertionError):
            self.check_lifetime(dropping)
        self.assertFalse(dropping['held_after_kill'], dropping)
        # Orderly cancellation: SIGINT and SIGTERM reach the command's process group, the launcher returns its status
        # after it exits, and the lock is free; SIGKILL leaves the command holding the lock until it exits.
        trap = ('trap "echo int > $0; exit 130" INT; trap "echo term > $0; exit 143" TERM; echo ready > $0.ready; '
                'while :; do sleep 0.05; done')
        for signum, word, code in ((signal.SIGINT, 'int', 130), (signal.SIGTERM, 'term', 143)):
            with self.subTest(signal=word):
                marker = self.work / f'{word}.marker'
                process = subprocess.Popen([*self.launcher, '/bin/bash', '-c', trap, str(marker)], env=clean_env(), start_new_session=True)
                wait_for(Path(str(marker) + '.ready').exists, message='the trapping command')
                os.kill(process.pid, signum)
                self.assertEqual(process.wait(timeout=20), code)
                self.assertEqual(marker.read_text().strip(), word, 'the signal was not forwarded to the command')
                self.assertTrue(lock_free(self.root))
        marker = self.work / 'kill.marker'
        process = subprocess.Popen([*self.launcher, '/bin/bash', '-c', trap, str(marker)], env=clean_env(), start_new_session=True)
        wait_for(Path(str(marker) + '.ready').exists, message='the trapping command')
        os.kill(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
        self.assertFalse(lock_free(self.root), 'a killed launcher released the lock its command holds')
        children = subprocess.run(['/usr/bin/pgrep', '-f', str(marker)], capture_output=True, text=True).stdout.split()
        for pid in children:
            try:
                os.killpg(int(pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        wait_for(lambda: lock_free(self.root), message='release after the orphaned command exits')

    def test_witness_preserves_bytes_and_nested_front_end_records_its_own(self):
        caller = {k: v for k, v in clean_env().items() if k not in NAMES}
        caller.update(CPATH='', LIBRARY_PATH=os.fsdecode(bytes(range(1, 256))) + '\n', MANPATH='spaced dir/man\n')
        report = ('import json, os, sys; sys.path.insert(0, sys.argv[1]); import checkout_lock; '
                  'print(json.dumps(checkout_lock.verify_environment(), sort_keys=True))')
        command = shlex.join([PYTHON, '-B', '-c', report, LIB])
        nested = command + '; CPATH=/inner/include ' + shlex.join(self.launcher) + ' ' + command
        result = subprocess.run([*self.launcher, '/bin/bash', '-c', nested], env=caller, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        outer, inner = map(json.loads, result.stdout.splitlines())
        expected = {n: dict(state='set', value=caller[n]) if n in caller else dict(state='unset') for n in NAMES}
        self.assertEqual(outer, expected)
        self.assertEqual(inner, dict(expected, CPATH=dict(state='set', value='/inner/include')))
        # Python-only ownership leaves the supplied environment alone, including stale claims being dropped.
        with checkout_lock.owned(self.root, env=clean_env()) as scope:
            self.assertEqual(scope.child_env({'CPATH': '/unchanged'})['CPATH'], '/unchanged')

    def test_witness_refusals_precede_lock_writes(self):
        caller = {k: v for k, v in clean_env().items() if k not in NAMES}
        cli = [PYTHON, '-B', f'{LIB}/checkout_lock.py', '--root', str(self.root), '--', '/usr/bin/true']
        for name in NAMES:
            for fault in ('missing', 'changed', 'malformed'):
                env = witnessed(caller)
                key = 'PW_ENV_WITNESS_' + name
                if fault == 'missing':
                    env.pop(key)
                else:
                    env[key] = 's' if fault == 'changed' else 'invalid'
                with self.subTest(name=name, fault=fault):
                    result = subprocess.run(cli, env=env, capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn('environment witness', result.stderr)
                    self.assertIn(name, result.stderr)
                    self.assertFalse(self.lock.exists(), 'a refused witness wrote the lock')

    def test_direct_python_children_inherit_the_callers_environment(self):
        # Compare NUL-delimited raw bytes; no decoding or line splitting can hide changes.
        script = self.script('environment.sh', '\n'.join([
            'source "$1/python_start.sh"',
            'if [[ "$3" == direct ]]; then set -- "$1" "$2" "$PW_PYTHON" "$4"; fi',
            '/usr/bin/env -0 "_=$3" > "$2"',
            '"$3" -B -c \'import subprocess,sys; open(sys.argv[1], "wb").write(subprocess.check_output(["/usr/bin/env", "-0"]))\' "$4"',
            ':'
        ]))
        for interpreter in ('direct', '/usr/bin/python3'):
            before, after = self.work / 'before', self.work / 'after'
            # Python adds __CF_USER_TEXT_ENCODING when it is missing, so the caller supplies one.
            env = dict(PATH='/usr/bin:/bin', LIBRARY_PATH='spaced dir/lib\n', MANPATH='/caller/man',
                       __CF_USER_TEXT_ENCODING=os.environ.get('__CF_USER_TEXT_ENCODING', f'0x{os.getuid():X}:0x0:0x0'))
            result = subprocess.run(['/usr/bin/env', '-i', *[f'{k}={v}' for k, v in env.items()], '/bin/bash', str(script),
                                     LIB, str(before), interpreter, str(after)], capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            a, b = set(before.read_bytes().split(b'\0')), set(after.read_bytes().split(b'\0'))
            if interpreter == 'direct':
                self.assertEqual(a, b, (a - b, b - a))
            else:
                self.assertNotEqual(a, b, 'the shim negative control did not change the environment')

    def test_forwarder_preserves_the_environment_and_a_shim_control_does_not(self):
        wrapper = self.work / 'forward'
        shutil.copy2(ROOT / 'tests/fixtures/build_refusals/forward.py', wrapper)
        wrapper.chmod(0o755)
        interpreter = self.work / 'directory with spaces/python'
        interpreter.parent.mkdir()
        interpreter.symlink_to(PYTHON)
        receipt = self.work / 'forward.jsonl'
        config = self.work / 'forward-config.json'
        config.write_text(json.dumps({'forward': dict(real='/usr/bin/true', mode='direct',
                                                     receipt=str(receipt), record_env=list(NAMES))}))
        env = {k: v for k, v in clean_env().items() if k not in NAMES}
        env.update(PW_PYTHON=str(interpreter), PYTHONCOERCECLOCALE='0', PW_FORWARD_CONFIG=str(config))
        for command in ([str(wrapper)], ['/usr/bin/python3', str(wrapper)]):
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        direct, shim = [json.loads(line)['environment'] for line in receipt.read_text().splitlines()]
        self.assertEqual(direct, {name: None for name in NAMES})
        self.assertNotEqual(shim, direct)
        self.assertIsNotNone(shim['CPATH'])

    def test_entrypoints_refuse_a_stand_in_developer_directory_without_a_shim(self):
        developer = self.work / 'empty developer'
        developer.mkdir()
        profile = self.script('resolver.sb', '(version 1)(allow default)(deny mach-lookup)(deny process-exec)'
                              '(allow process-exec (literal "/bin/bash") (literal "/usr/bin/dirname") (literal "/usr/bin/xcode-select"))')
        for entry in ('tests/lib/checkout_lock.sh', 'tests/run.sh'):
            result = subprocess.run(['/usr/bin/sandbox-exec', '-f', str(profile), '/bin/bash', str(ROOT / entry), '--help'],
                                    env=dict(clean_env(), DEVELOPER_DIR=str(developer), PW_PYTHON='/usr/bin/false'),
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('DEVELOPER_DIR=' + str(developer), result.stderr)
            self.assertIn('direct Python unavailable', result.stderr)
            self.assertNotIn('requesting installation', result.stdout + result.stderr)


class ProbeTests(unittest.TestCase):
    def test_cleanup_has_one_deadline_even_when_the_group_cannot_be_reaped(self):
        from unittest import mock
        # Model an unobservable/unreaped group. Each observation consumes its
        # whole allowance; resetting that allowance would exceed the contract.
        def remains(process, pgid, timeout):
            time.sleep(timeout)
            return False
        with mock.patch.object(prov, 'CLEANUP_TIMEOUT', .2), mock.patch.object(prov, 'TERM_GRACE', .05), \
                mock.patch.object(prov, 'group_gone', side_effect=remains), mock.patch.object(prov.os, 'killpg'):
            started = time.monotonic()
            self.assertEqual(prov.terminate_group(mock.Mock(pid=123)), 'failed')
            self.assertLess(time.monotonic() - started, .32)

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-probe-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def timed(self, argv, **kwargs):
        started = time.monotonic()
        found = prov.probe(argv, **kwargs)
        return found, time.monotonic() - started

    def gone(self, pid_file):
        """Whether the pid a fixture recorded has exited, observed from outside the probe."""
        pid = int(pid_file.read_text().split()[0])
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            state = subprocess.run(['/bin/ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
            if not state or state.startswith('Z'):
                return True
            time.sleep(0.05)
        return False

    def test_probes_are_bounded_and_failures_carry_no_output(self):
        canary = 'CANARY_' + os.urandom(6).hex()
        planted = self.work / 'canary'
        planted.write_text(canary + '\n')
        failed = prov.probe(['/bin/sh', '-c', f'cat {planted} >&2; cat {planted}; exit 3'])
        self.assertEqual((failed['status'], failed['kind'], failed['returncode']), ('failed', 'nonzero_exit', 3))
        self.assertNotIn(canary, json.dumps(failed))
        empty = prov.probe(['/bin/sh', '-c', 'printf "  \\n"'])
        self.assertEqual(empty['kind'], 'empty_output')
        missing = prov.probe(['/nonexistent/tool-' + os.urandom(4).hex()])
        self.assertEqual(missing['kind'], 'launch_failed')
        good = prov.probe(['/bin/sh', '-c', 'echo tool 1.2.3; echo more'])
        self.assertEqual((good['status'], good['line']), ('ok', 'tool 1.2.3'))
        self.assertEqual(prov.version_line(prov.probe(['/bin/sh', '-c', 'echo nodigits']))['kind'], 'malformed_output')
        # Overflow on either stream fails the observation while the tool runs, even when it would exit zero; an endless
        # writer is stopped once past its cap, and the counts show how much was read.
        overflow, elapsed = self.timed(['/usr/bin/yes'], limit=65536)
        self.assertEqual((overflow['kind'], overflow['stream'], overflow['cleanup']), ('output_overflow', 'stdout', 'complete'))
        self.assertGreater(overflow['stdout_bytes'], 65536)
        self.assertLess(overflow['stdout_bytes'], 65536 + 65536 * 2)
        self.assertLess(elapsed, 5)
        flood = prov.probe(['/bin/sh', '-c', f'i=0; while [ $i -lt 200 ]; do cat {planted} >&2; i=$((i+1)); done; echo tool 1.0'],
                           stderr_limit=64)
        self.assertEqual((flood['status'], flood['kind'], flood['stream']), ('failed', 'output_overflow', 'stderr'))
        self.assertNotIn(canary, json.dumps(flood))
        # The review's counterexample: 8192 stderr bytes against a 64-byte cap with a zero exit.
        review = prov.probe(['/bin/sh', '-c', 'head -c 8192 /dev/zero >&2; echo tool 1.0'], stderr_limit=64)
        self.assertEqual((review['kind'], review['stream']), ('output_overflow', 'stderr'))
        # Both streams active at once, each under its cap: no deadlock, and stdout is complete.
        both = prov.probe([PYTHON, '-c', 'import sys\nfor i in range(15):\n    sys.stdout.write("o" * 4000); sys.stdout.flush()\n'
                                         '    sys.stderr.write("e" * 4000); sys.stderr.flush()\n'], limit=65536, stderr_limit=65536)
        self.assertEqual((both['status'], len(both['text']), both['stderr_bytes']), ('ok', 60000, 60000))
        exact = prov.probe(['/bin/sh', '-c', 'head -c 65536 /dev/zero | tr "\\\\0" a'], limit=65536)
        self.assertEqual((exact['status'], len(exact['text'])), ('ok', 65536))
        over = prov.probe(['/bin/sh', '-c', 'head -c 65537 /dev/zero | tr "\\\\0" a'], limit=65536)
        self.assertEqual(over['kind'], 'output_overflow')
        # A deadline covers the whole run; a tool ignoring SIGTERM is killed, and an orphan keeping a pipe open after its
        # leader exited cannot extend the run or survive it.
        hung, elapsed = self.timed(['/bin/sh', '-c', 'sleep 30'], timeout=1)
        self.assertEqual((hung['kind'], hung['cleanup']), ('timeout', 'complete'))
        self.assertLess(elapsed, 1 + prov.TERM_GRACE + prov.CLEANUP_TIMEOUT + 2)
        stubborn_pid = self.work / 'stubborn.pid'
        stubborn, elapsed = self.timed(['/bin/sh', '-c', f'trap "" TERM; echo $$ > {stubborn_pid}; while :; do sleep 0.1; done'], timeout=1)
        self.assertEqual((stubborn['kind'], stubborn['cleanup']), ('timeout', 'complete'))
        self.assertLess(elapsed, 1 + prov.TERM_GRACE + prov.CLEANUP_TIMEOUT + 2)
        self.assertTrue(self.gone(stubborn_pid), 'the tool that ignored SIGTERM survived the probe')
        orphan_pid = self.work / 'orphan.pid'
        orphan, elapsed = self.timed(['/bin/sh', '-c', f'(trap "" TERM; while :; do sleep 0.1; done) & echo $! > {orphan_pid}; echo tool 1.0; exit 0'],
                                     timeout=1)
        self.assertEqual((orphan['status'], orphan['kind'], orphan['cleanup']), ('failed', 'timeout', 'complete'))
        self.assertLess(elapsed, 1 + prov.TERM_GRACE + prov.CLEANUP_TIMEOUT + 2)
        self.assertTrue(self.gone(orphan_pid), 'the orphaned pipe writer survived the probe')
        with self.assertRaises(prov.Refusal) as required:
            prov.required(failed, 'compilers.c.identity')
        self.assertEqual(required.exception.status, 2)
        self.assertIn('nonzero_exit', str(required.exception))

    def test_comparison_inputs_are_complete_within_their_bounds(self):
        # Two identities that agree on the first LINE_LIMIT characters and differ after them: neither is an observation,
        # and two failed observations never compare equal.
        a, b = 'tool ' + 'x' * 250 + 'A', 'tool ' + 'x' * 250 + 'B'
        self.assertEqual(a[:prov.LINE_LIMIT], b[:prov.LINE_LIMIT], 'the identities agree within the former truncation boundary')
        seen = [prov.version_line(prov.probe(['/bin/echo', identity])) for identity in (a, b)]
        self.assertEqual([s['kind'] for s in seen], ['oversized_output', 'oversized_output'])
        stamped = dict(observation=seen[0])
        self.assertEqual(prov.compare_fields({'rustc.identity': None}, {'rustc.identity': None}, ['rustc.identity'])[3], 'unavailable')
        self.assertIsNotNone(stamped)
        # A configured command longer than the bound is unknown, not a prefix; Cargo's oversized flag list is not recorded.
        builddir = self.work / 'builddir'
        (builddir / 'meson-info').mkdir(parents=True)
        (builddir / 'meson-info/intro-compilers.json').write_text(json.dumps(dict(host={'c': dict(
            id='clang', exelist=['cc'] + ['-flag'] * prov.COMMAND_LIMIT, version='21.0.0', full_version='x')})))
        self.assertTrue(prov.read_compilers(builddir)['c']['oversized'])
        self.assertEqual(prov.compiler_observation(None, builddir, os.environ)['kind'], 'oversized_output')
        long_line = prov.probe(['/bin/echo', 'cc version ' + '9' * 300])
        self.assertEqual(prov.version_line(long_line)['kind'], 'oversized_output')


class StampFixture(unittest.TestCase):
    """A disposable checkout with an owned session and a substituted toolchain observation."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-stamp-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        (self.root / 'controller').mkdir()
        self.builddir = self.root / 'builddir'
        self.session = self.root / 'controller/target/pw-build-session.json'
        self.scope, self.env = own(self, self.root)
        status, _, err = run_main(['session-start', '--root', str(self.root), '--knob', 'BUILD_XPC=0',
                                   '--describe', 'v0.0.0-control', '--commit', 'c' * 40, '--version', '0.0.0', '--build-number', '1'], self.env)
        self.assertEqual(status, 0, err)
        self.observation = fake_observation()
        self.original = prov.observe_toolchain
        prov.observe_toolchain = lambda *a, **k: copy.deepcopy(self.observation)
        self.addCleanup(setattr, prov, 'observe_toolchain', self.original)

    def configure(self, swift=False):
        self.builddir.mkdir(exist_ok=True)
        (self.builddir / 'build.ninja').write_text('# control\n')
        write_compilers(self.builddir, swift)

    def check(self, xpc='0'):
        return run_main(['stamp-check', '--root', str(self.root), '--xpc', xpc], self.env)

    def publish(self):
        return run_main(['stamp-publish', '--root', str(self.root)], self.env)

    def extend(self, xpc):
        return run_main(['stamp-extend', '--root', str(self.root), '--xpc', xpc], self.env)



class StampTests(StampFixture):
    def test_stamp_states_are_decided_without_adopting_unknowns(self):
        stamp = self.builddir / prov.STAMP_NAME
        status, out, _ = self.check()
        self.assertEqual(status, 0, 'an unconfigured directory needs no stamp')
        self.assertIn('not configured', out)
        self.configure()
        status, _, err = self.check()
        self.assertEqual(status, 2)
        self.assertIn('has no pw-toolchain.json', err)
        self.assertIn('PW_FRESH_BUILD=1', err)
        self.assertFalse(stamp.exists(), 'a missing stamp is never written by validation')
        status, _, err = self.publish()
        self.assertEqual(status, 0, err)
        published = stamp.read_bytes()
        record = json.loads(published)
        self.assertEqual(record['scope'], {'xpc': False})
        self.assertEqual(record['fields']['compilers.c.identity'], 'Apple clang version 21.0.0 (clang-2100.3.34.2)')
        status, _, err = self.publish()
        self.assertEqual(status, 2, 'publishing over an existing stamp is refused')
        self.assertIn('already holds', err)
        status, _, _ = self.check()
        self.assertEqual(status, 0)
        self.assertEqual(stamp.read_bytes(), published, 'unchanged reuse leaves the stamp intact')
        # A changed observation refuses as changed; a failed one refuses as unavailable; neither rewrites the stamp.
        self.observation['compilers']['c']['observed']['identity'] = 'Apple clang version 21.0.0 (clang-2100.1.1.101)'
        status, _, err = self.check()
        self.assertEqual(status, 1)
        self.assertIn('compilers.c.identity', err)
        self.assertIn('a changed toolchain cannot reuse this directory', err)
        self.observation = fake_observation(rustc=dict(status='failed', kind='nonzero_exit'))
        status, _, err = self.check()
        self.assertEqual(status, 2)
        self.assertIn('required toolchain observation failed: rustc.command', err)
        self.observation = fake_observation()
        self.assertEqual(stamp.read_bytes(), published)
        # A stamp that does not describe the directory, belongs elsewhere, is malformed or unsupported is not adopted.
        write_compilers(self.builddir)
        (self.builddir / 'meson-info/intro-compilers.json').write_text(json.dumps(dict(host={'c': dict(id='clang', exelist=['/usr/bin/clang'], version='21.0.0', full_version='x')})))
        status, _, err = self.check()
        self.assertEqual(status, 2)
        self.assertIn('does not describe this directory', err)
        write_compilers(self.builddir)
        for label, text in (('malformed', '{not json'), ('unsupported', json.dumps(dict(schema_version=99))),
                            ('elsewhere', json.dumps(dict(record, source_dir='/private/tmp/elsewhere'))),
                            ('fieldless', json.dumps(dict(schema_version=1, scope={}, source_dir=str(self.root))))):
            with self.subTest(stamp=label):
                stamp.write_text(text)
                status, _, err = self.check()
                self.assertEqual(status, 2, err)
                self.assertNotEqual(stamp.read_text(), published.decode(), 'validation never rewrites a stamp')
        stamp.write_bytes(published)
        shutil.rmtree(self.builddir)
        self.builddir.mkdir()
        stamp.write_bytes(published)
        status, _, err = self.check()
        self.assertEqual(status, 2, 'a stamp without a configuration is an unknown state')
        self.assertIn('no configuration', err)
        # Extension: a reused directory that discovers Swift extends the stamp without touching other fields.
        self.configure(swift=True)
        stamp.write_bytes(published)
        self.observation = fake_observation(compilers={
            'c': fake_observation()['compilers']['c'],
            'swift': dict(configured=dict(command=['swiftc'], id='llvm', version='6.4', full_version=None),
                          observed=dict(status='ok', command=['swiftc'], identity='swift-driver version: 1.168.6 Apple Swift version 6.4'))})
        status, out, err = self.extend('0')
        self.assertEqual(status, 0, err)
        self.assertIn('intact', out)
        self.assertEqual(stamp.read_bytes(), published)
        status, out, err = self.extend('1')
        self.assertEqual(status, 0, err)
        self.assertIn('extended', out)
        extended = json.loads(stamp.read_text())
        self.assertEqual(extended['scope'], {'xpc': True})
        self.assertEqual(extended['fields']['compilers.swift.command'], ['swiftc'])
        self.assertEqual({k: v for k, v in extended['fields'].items() if not k.startswith('compilers.swift.') and k != 'output.swift_target'},
                         record['fields'])
        self.assertEqual(extended['fields']['output.swift_target'], ['arm64-apple-macosx26.0'])
        self.assertEqual(extended['published_at'], record['published_at'])
        # A validated reuse with Swift applicable compares the Swift fields too; a changed one refuses.
        self.assertEqual(self.check('1')[0], 0)
        self.observation['compilers']['swift']['observed']['identity'] = 'swift-driver version: 1.148.6 Apple Swift version 6.3.3'
        status, _, err = self.check('1')
        self.assertEqual(status, 1)
        self.assertIn('compilers.swift.identity', err)
        # An extension that would also change another field refuses instead of rewriting it.
        stamp.write_bytes(published)
        self.observation = fake_observation(compilers=self.observation['compilers'])
        self.observation['sdk']['build']['line'] = '26A999'
        status, _, err = self.extend('1')
        self.assertEqual(status, 1)
        self.assertIn('cannot be extended', err)
        self.assertEqual(stamp.read_bytes(), published)
        session = json.loads(self.session.read_text())
        self.assertIn('toolchain', session)


class OutputTargetStampTests(StampFixture):
    def test_stamps_carry_the_output_target_and_refuse_another(self):
        stamp = self.builddir / prov.STAMP_NAME
        self.configure()
        self.assertEqual(self.publish()[0], 0)
        published = stamp.read_bytes()
        self.assertEqual({k: v for k, v in json.loads(published)['fields'].items() if k.startswith('output.')},
                         {'output.system': 'darwin', 'output.cpu_family': 'aarch64', 'output.c_arch': ['arm64'],
                          'output.link_arch': ['arm64'], 'output.cargo_triple': 'aarch64-apple-darwin'},
                         "the stamp records Meson's host machine and the targets' effective arguments")
        # A stamp from before the output target contract is never relabelled as arm64-compatible: it refuses until fresh mode.
        old = json.loads(published)
        old['schema_version'] = 1
        old['fields'] = {k: v for k, v in old['fields'].items() if not k.startswith('output.')}
        stamp.write_text(json.dumps(old))
        status, _, err = self.check()
        self.assertEqual(status, 2, err)
        self.assertIn('unsupported schema', err)
        self.assertIn('PW_FRESH_BUILD=1', err)
        self.assertEqual(json.loads(stamp.read_text()), old, 'validation never rewrites a stamp')
        missing = json.loads(published)
        missing['fields'].pop('output.link_arch')
        stamp.write_text(json.dumps(missing))
        status, _, err = self.check()
        self.assertEqual(status, 2, err)
        self.assertIn('lacks its output target fields', err)
        # A stamp naming another target refuses reuse as such, before any toolchain is probed.
        probed = []
        prov.observe_toolchain = lambda *a, **k: probed.append(True) or copy.deepcopy(self.observation)
        for name, value in (('output.cpu_family', 'x86_64'), ('output.system', 'ios'), ('output.c_arch', ['x86_64']),
                            ('output.link_arch', ['arm64', 'x86_64']), ('output.cargo_triple', 'x86_64-apple-darwin')):
            with self.subTest(field=name):
                changed = json.loads(published)
                changed['fields'][name] = value
                stamp.write_text(json.dumps(changed))
                status, _, err = self.check()
                self.assertEqual(status, 1, err)
                self.assertIn(f'is configured for output {name}', err)
                self.assertIn('a directory configured for another target cannot be reused', err)
                self.assertEqual(probed, [], 'the target is compared before any toolchain probe')
        # A stamp naming the target beside a directory configured for another does not describe the directory.
        stamp.write_bytes(published)
        write_configured_output(self.builddir, arch='x86_64')
        status, _, err = self.check()
        self.assertEqual(status, 2, err)
        self.assertIn("records output.c_arch = ['arm64'] but the directory is configured with ['x86_64']", err)
        self.assertIn('does not describe this directory', err)
        write_configured_output(self.builddir, cpu_family='x86_64')
        status, _, err = self.check()
        self.assertEqual(status, 2, err)
        self.assertIn('output.cpu_family', err)
        # After compiling, a configuration that moved away from the stamped target refuses; the stamp is never rewritten.
        write_configured_output(self.builddir, link_arch='x86_64')
        status, _, err = self.extend('0')
        self.assertEqual(status, 2, err)
        self.assertIn('no longer describes the output target', err)
        self.assertEqual(stamp.read_bytes(), published)
        write_configured_output(self.builddir)
        self.assertEqual(self.check()[0], 0)
        self.assertEqual(stamp.read_bytes(), published)
        # Swift's target joins a newly applicable compiler's fields and is then compared like the others.
        self.configure(swift=True)
        self.observation = fake_observation(compilers={
            'c': fake_observation()['compilers']['c'],
            'swift': dict(configured=dict(command=['swiftc'], id='llvm', version='6.4', full_version=None),
                          observed=dict(status='ok', command=['swiftc'], identity='swift-driver version: 1.168.6 Apple Swift version 6.4'))})
        status, _, err = self.extend('1')
        self.assertEqual(status, 0, err)
        extended = stamp.read_bytes()
        self.assertEqual(json.loads(extended)['fields']['output.swift_target'], ['arm64-apple-macosx26.0'])
        self.assertEqual(self.check('1')[0], 0)
        changed = json.loads(extended)
        changed['fields']['output.swift_target'] = ['x86_64-apple-macosx26.0']
        stamp.write_text(json.dumps(changed))
        status, _, err = self.check('1')
        self.assertEqual(status, 1, err)
        self.assertIn('is configured for output output.swift_target', err)
        stamp.write_bytes(extended)
        write_configured_output(self.builddir, swift=True, swift_target='arm64-apple-ios17.0-macabi')
        status, _, err = self.extend('1')
        self.assertEqual(status, 2, err)
        self.assertIn('output.swift_target', err)
        # A partial build reconfigures the directory without the XPC pieces, so its introspection lists no Swift target;
        # a full build reusing it is not refused for that before its compile regenerates the target.
        stamp.write_bytes(extended)
        write_configured_output(self.builddir, swift=False)
        (self.builddir / 'meson-info/intro-buildoptions.json').write_text(json.dumps([dict(name='xpc', value=False),
                                                                                      dict(name='inspection', value=True)]))
        status, _, err = self.check('1')
        self.assertEqual(status, 0, err)
        self.assertEqual(stamp.read_bytes(), extended)


class FailedObservationTests(StampFixture):
    def test_failed_required_observations_refuse_compatibility_and_publication(self):
        stamp = self.builddir / prov.STAMP_NAME
        self.configure()
        for kind in ('output_overflow', 'oversized_output', 'timeout'):
            with self.subTest(publication=kind):
                self.observation = fake_observation(rustc=dict(status='failed', kind=kind, stream='stderr', stdout_bytes=0, stderr_bytes=70000))
                status, _, err = self.publish()
                self.assertEqual(status, 2, err)
                self.assertIn('required toolchain observation failed: rustc.command', err)
                self.assertFalse(stamp.exists(), 'a stamp recorded an unobserved field')
        self.observation = fake_observation()
        self.assertEqual(self.publish()[0], 0)
        published = stamp.read_bytes()
        failed_c = dict(configured=fake_observation()['compilers']['c']['configured'], observed=dict(status='failed', kind='output_overflow', stream='stdout'))
        self.observation = fake_observation(compilers={'c': failed_c})
        status, _, err = self.check()
        self.assertEqual(status, 2, err)
        self.assertIn('compilers.c.identity (output_overflow)', err)
        self.assertEqual(stamp.read_bytes(), published)
        # A configured command beyond the bound is an unobserved field, never a prefix compared with the stamp.
        (self.builddir / 'meson-info/intro-compilers.json').write_text(json.dumps(dict(host={'c': dict(
            id='clang', exelist=['cc'] + ['-flag'] * prov.COMMAND_LIMIT, version='21.0.0', full_version='x')})))
        self.observation = fake_observation()
        status, _, err = self.check()
        self.assertEqual(status, 2, err)
        self.assertIn('compilers.c.command (oversized_output)', err)
        # The record refuses a failed required observation as well.
        session = json.loads(self.session.read_text())
        session['toolchain'] = fake_observation(rustc=dict(status='failed', kind='output_overflow', stream='stderr'))
        with self.assertRaises(prov.Refusal) as refused:
            prov.collect(session, self.root / 'absent.app', self.root, 'Developer ID Application: Control (TEAMID00AA)',
                         manifest_entries=[], signature=None)
        self.assertIn('rustc (output_overflow)', str(refused.exception))


class FreshRemovalTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-fresh-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        self.root = self.work / 'checkout'
        self.root.mkdir()
        (self.root / 'controller/target/release/deps').mkdir(parents=True)
        (self.root / 'controller/target/debug').mkdir()
        (self.root / prov.TRIPLE_RELEASE / 'deps').mkdir(parents=True)
        (self.root / 'builddir/meson-info').mkdir(parents=True)
        (self.root / 'builddir-clt').mkdir()
        self.sentinels = {self.root / 'controller/target/debug/keep': 'debug', self.root / 'controller/target/CACHEDIR.TAG': 'tag',
                          self.root / prov.TRIPLE_DIR / 'debug/keep': 'triple debug',
                          self.root / 'controller/target/x86_64-apple-darwin/release/keep': 'another triple',
                          self.root / 'builddir-clt/keep': 'alternate', self.work / 'outside/keep': 'outside',
                          self.root / 'dist/PolicyWitness.zip': 'previous'}
        for path, text in self.sentinels.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.session = self.root / 'controller/target/pw-build-session.json'
        self.scope, self.env = own(self, self.root)
        self.assertEqual(run_main(['session-start', '--root', str(self.root), '--describe', 'x', '--commit', 'x',
                                   '--version', '0', '--build-number', '0'], self.env)[0], 0)

    def remove(self):
        return run_main(['fresh-remove', '--root', str(self.root)], self.env)

    def intact(self):
        for path, text in self.sentinels.items():
            self.assertEqual(path.read_text(), text, f'{path} was touched')

    def test_fresh_removal_admits_only_owned_real_directories(self):
        (self.root / 'builddir/meson-info/keep').write_text('cache')
        (self.root / 'controller/target/release/deps/keep').write_text('cache')
        (self.root / 'controller/target/release/deps/link').symlink_to(self.work / 'outside/keep')
        (self.root / prov.TRIPLE_RELEASE / 'deps/keep').write_text('shipped cache')
        status, out, err = self.remove()
        self.assertEqual(status, 0, err)
        self.assertFalse((self.root / 'builddir').exists())
        self.assertFalse((self.root / 'controller/target/release').exists())
        self.assertFalse((self.root / prov.TRIPLE_RELEASE).exists())
        self.assertTrue((self.root / prov.TRIPLE_DIR).is_dir(), "only the triple's release area is replaced")
        self.intact()  # a symlink inside a removed directory is unlinked, never followed; other profiles and triples stay
        session = json.loads(self.session.read_text())
        self.assertEqual({k: v['removed'] for k, v in session['fresh']['replacement'].items()},
                         {'builddir': True, 'cargo_release': True, 'cargo_target_release': True})
        self.assertEqual(session['fresh']['replacement']['cargo_target_release']['path'], 'controller/target/aarch64-apple-darwin/release')
        status, _, _ = self.remove()
        self.assertEqual(status, 0, 'absent directories are not an error')
        self.assertEqual({k: v['existed'] for k, v in json.loads(self.session.read_text())['fresh']['replacement'].items()},
                         {'builddir': False, 'cargo_release': False, 'cargo_target_release': False})
        # The triple's release area is admitted like the others: a symlink there refuses before anything is removed.
        (self.root / 'builddir').mkdir()
        (self.work / 'elsewhere/triple').mkdir(parents=True)
        (self.work / 'elsewhere/triple/keep').write_text('external')
        (self.root / prov.TRIPLE_RELEASE).symlink_to(self.work / 'elsewhere/triple')
        status, _, err = self.remove()
        self.assertEqual(status, 2, err)
        self.assertIn('aarch64-apple-darwin/release is a symlink', err)
        self.assertTrue((self.root / 'builddir').is_dir(), 'a refused admission removes nothing')
        self.assertEqual((self.work / 'elsewhere/triple/keep').read_text(), 'external')
        (self.root / prov.TRIPLE_RELEASE).unlink()
        (self.root / 'builddir').rmdir()
        # A symlinked component redirecting outside the checkout refuses at admission, before anything is removed.
        (self.root / 'builddir').mkdir()
        (self.root / 'builddir/keep').write_text('rebuilt')
        (self.work / 'elsewhere/release').mkdir(parents=True)
        (self.work / 'elsewhere/release/keep').write_text('external')
        (self.root / 'controller/target/release').symlink_to(self.work / 'elsewhere/release')
        status, _, err = self.remove()
        self.assertEqual(status, 2, err)
        self.assertIn('is a symlink; the build admits only real directories', err)
        self.assertEqual((self.work / 'elsewhere/release/keep').read_text(), 'external')
        self.assertEqual((self.root / 'builddir/keep').read_text(), 'rebuilt', 'a refused admission removes nothing, not even the admitted sibling')
        (self.root / 'controller/target/release').unlink()
        (self.root / 'controller/target/release').write_text('a file, not a directory')
        status, _, err = self.remove()
        self.assertEqual(status, 2)
        self.assertIn('is not a directory', err)
        (self.root / 'controller/target/release').unlink()
        # A removal that fails stops the build with the path; the session records the failure.
        (self.root / 'controller/target/release').mkdir()
        locked = self.root / 'builddir/immutable'
        locked.write_text('x')
        subprocess.run(['/usr/bin/chflags', 'uchg', str(locked)], check=True)
        try:
            status, _, err = self.remove()
        finally:
            subprocess.run(['/usr/bin/chflags', 'nouchg', str(locked)], check=False)
        self.assertEqual(status, 1, err)
        self.assertIn('could not remove', err)
        self.assertEqual(json.loads(self.session.read_text())['fresh'].get('failed'), 'builddir')
        self.assertTrue((self.root / 'controller/target/release').exists(), 'a failed removal stops before the next root')
        self.intact()


class OwnershipAndAdmissionTests(unittest.TestCase):
    """Helpers refuse before any write without a live owner's handoff, a valid session or admitted paths."""

    def test_refused_start_does_not_create_a_missing_target_directory(self):
        with checkout_lock.owned(self.root, env=clean_env()) as scope:
            status, _, err = self.start(scope.child_env(clean_env()))
            self.assertEqual(status, 2, err)
            self.assertIn('environment witness missing for SDKROOT', err)
            self.assertFalse((self.root / 'controller/target').exists())
        with checkout_lock.owned(self.root, env=clean_env()) as scope:
            (self.root / 'builddir').symlink_to(self.outside / 'builddir')
            status, _, err = self.start(scope.child_env(witnessed({k: v for k, v in clean_env().items() if k not in NAMES})))
            self.assertEqual(status, 2, err)
            self.assertIn('is a symlink', err)
            self.assertFalse((self.root / 'controller/target').exists())

    def test_session_witness_refusals_preserve_the_session_and_missing_target(self):
        with checkout_lock.owned(self.root, env=clean_env()) as scope:
            base = witnessed({k: v for k, v in clean_env().items() if k not in NAMES})
            for existing in (False, True):
                if existing:
                    self.session.parent.mkdir()
                    self.session.write_bytes(b'previous session\n')
                for name in NAMES:
                    for fault in ('missing', 'changed'):
                        env = dict(base)
                        if fault == 'missing':
                            env.pop('PW_ENV_WITNESS_' + name)
                        else:
                            env['PW_ENV_WITNESS_' + name] = 's'
                        status, _, err = self.start(scope.child_env(env))
                        self.assertEqual(status, 2, (name, fault, err))
                        self.assertIn(name, err)
                        if existing:
                            self.assertEqual(self.session.read_bytes(), b'previous session\n')
                        else:
                            self.assertFalse(self.session.parent.exists())
            self.session.unlink()
            env = dict(base, PW_ENV_WITNESS_SDKROOT='srequested sdk\n')
            args = ['session-start', '--root', str(self.root), '--describe', 'x', '--commit', 'x', '--version', '0',
                    '--build-number', '0', '--sdk-request-state', 'set', '--sdk-request-value=requested sdk\n']
            status, _, err = run_main(args, scope.child_env(env))
            self.assertEqual(status, 0, err)
            self.assertEqual(json.loads(self.session.read_text())['requests']['SDKROOT'],
                             dict(state='set', value='requested sdk\n'))

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-admit-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        self.root = self.work / 'checkout'
        (self.root / 'controller').mkdir(parents=True)
        self.outside = self.work / 'outside'
        self.outside.mkdir()
        (self.outside / 'pw-build-session.json').write_text('outside session\n')
        (self.outside / 'release').mkdir()
        (self.outside / 'release/keep').write_text('outside release\n')
        (self.outside / 'builddir').mkdir()
        (self.outside / 'builddir/keep').write_text('outside builddir\n')
        (self.outside / 'triple/release').mkdir(parents=True)
        (self.outside / 'triple/release/keep').write_text('outside triple release\n')
        self.session = self.root / 'controller/target/pw-build-session.json'

    def outside_inventory(self):
        return {str(p.relative_to(self.outside)): (p.is_symlink(), p.read_bytes() if p.is_file() and not p.is_symlink() else None)
                for p in sorted(self.outside.rglob('*'))}

    def start(self, env):
        return run_main(['session-start', '--root', str(self.root), '--describe', 'x', '--commit', 'x', '--version', '0',
                         '--build-number', '0'], env)

    def test_helpers_refuse_without_ownership(self):
        bare = witnessed({k: v for k, v in clean_env().items() if k not in NAMES})
        (self.root / 'builddir').mkdir()
        (self.root / 'builddir/build.ninja').write_text('# control\n')
        write_compilers(self.root / 'builddir')
        (self.root / 'controller/target/release').mkdir(parents=True)
        (self.root / 'controller/target/release/keep').write_text('cache')
        # No claim at all: session writes, fresh removal and stamp publication refuse before writing.
        for argv in (['session-start', '--root', str(self.root), '--describe', 'x', '--commit', 'x', '--version', '0', '--build-number', '0'],
                     ['fresh-remove', '--root', str(self.root)], ['stamp-publish', '--root', str(self.root)]):
            with self.subTest(helper=argv[0], claim='none'):
                status, _, err = run_main(argv, bare)
                self.assertEqual(status, 2, err)
                self.assertIn('build helpers mutate only under an owned build', err)
        self.assertFalse(self.session.exists())
        self.assertTrue((self.root / 'controller/target/release/keep').exists() and (self.root / 'builddir/build.ninja').exists())
        self.assertFalse((self.root / 'builddir' / prov.STAMP_NAME).exists())
        scope, env = own(self, self.root)
        original = prov.observe_toolchain
        prov.observe_toolchain = lambda *a, **k: fake_observation()
        self.addCleanup(setattr, prov, 'observe_toolchain', original)
        # A session without a nonce, with another acquisition's nonce or with a malformed one is stale.
        self.assertEqual(self.start(env)[0], 0)
        valid = json.loads(self.session.read_text())
        self.assertEqual(valid['lock_nonce'], scope.nonce)
        for label, nonce in (('missing', None), ('another hold', 'e' * 32), ('malformed', 'not-a-nonce')):
            for argv in (['fresh-remove', '--root', str(self.root)], ['stamp-publish', '--root', str(self.root)]):
                with self.subTest(session=label, helper=argv[0]):
                    session = dict(valid)
                    if nonce is None:
                        session.pop('lock_nonce')
                    else:
                        session['lock_nonce'] = nonce
                    self.session.write_text(json.dumps(session))
                    status, _, err = run_main(argv, env)
                    self.assertEqual(status, 2, err)
                    self.assertIn('the session is stale', err)
                    self.assertTrue((self.root / 'controller/target/release/keep').exists(), 'a stale session removed a cache')
                    self.assertFalse((self.root / 'builddir' / prov.STAMP_NAME).exists(), 'a stale session published a stamp')
        # The valid owned neighbours succeed.
        self.assertEqual(self.start(env)[0], 0)
        status, _, err = run_main(['stamp-publish', '--root', str(self.root)], env)
        self.assertEqual(status, 0, err)
        status, _, err = run_main(['fresh-remove', '--root', str(self.root)], env)
        self.assertEqual(status, 0, err)
        self.assertFalse((self.root / 'controller/target/release').exists())
        # A claim whose owner is gone admits nothing new.
        claimed = dict(env)
        scope.server.close()
        status, _, err = self.start(claimed)
        self.assertEqual(status, 2, err)
        self.assertIn('the owner of this claim is gone', err)

    def test_cache_paths_are_admitted_before_any_write(self):
        scope, env = own(self, self.root)
        before = self.outside_inventory()
        components = {
            'controller/target': self.outside,
            'controller/target/release': self.outside / 'release',
            prov.TRIPLE_DIR: self.outside / 'triple',
            prov.TRIPLE_RELEASE: self.outside / 'triple/release',
            'builddir': self.outside / 'builddir',
            'controller/target/pw-build-session.json': self.outside / 'pw-build-session.json',
        }
        for relative, target in components.items():
            with self.subTest(symlink=relative):
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target)
                try:
                    status, _, err = self.start(env)
                finally:
                    path.unlink()
                self.assertEqual(status, 2, err)
                self.assertIn('(nothing was written or removed)', err)
                self.assertEqual(self.outside_inventory(), before, 'admission let a write through the symlink')
                self.assertFalse(self.session.exists())
        # A component that is not a directory, a session destination that is a directory or hard-linked, and another
        # user's directory are refused the same way.
        (self.root / 'builddir').write_text('a file')
        status, _, err = self.start(env)
        self.assertEqual(status, 2)
        self.assertIn('builddir is not a directory', err)
        (self.root / 'builddir').unlink()
        self.session.mkdir()
        status, _, err = self.start(env)
        self.assertEqual(status, 2)
        self.assertIn('the destination is unsafe', err)
        self.session.rmdir()
        os.link(self.outside / 'pw-build-session.json', self.session)
        status, _, err = self.start(env)
        self.assertEqual(status, 2)
        self.assertIn('with one link', err)
        self.session.unlink()
        from unittest import mock
        with mock.patch.object(prov.os, 'getuid', return_value=os.getuid() + 1):
            status, _, err = self.start(env)
        self.assertEqual(status, 2)
        self.assertIn('is owned by uid', err)
        self.assertFalse(self.session.exists())
        # An owned missing path is created only beneath the admitted controller/.
        shutil.rmtree(self.root / 'controller/target')
        status, out, err = self.start(env)
        self.assertEqual(status, 0, err)
        self.assertEqual(json.loads(self.session.read_text())['admission']['created'], ['controller/target'])
        self.assertEqual(self.outside_inventory(), before)
        # A path replaced between admission and use: the write is refused, never made through the replacement.
        with environment(env), prov.build_scope(self.root) as state:
            (self.root / 'controller/target').rename(self.work / 'moved-target')
            (self.root / 'controller/target').symlink_to(self.outside)
            with self.assertRaises(prov.Refusal) as replaced:
                state.save()
            self.assertIn('was replaced after admission', str(replaced.exception))
        (self.root / 'controller/target').unlink()
        (self.work / 'moved-target').rename(self.root / 'controller/target')
        self.assertEqual(self.outside_inventory(), before)
        (self.root / 'builddir').mkdir()
        (self.root / 'builddir/keep').write_text('cache')
        with environment(env), prov.build_scope(self.root) as state:
            (self.root / 'builddir').rename(self.work / 'moved-builddir')
            (self.root / 'builddir').symlink_to(self.outside / 'builddir')
            with self.assertRaises(prov.Refusal) as replaced:
                prov.fresh_remove_admitted(state)
            self.assertIn('was replaced after admission', str(replaced.exception))
        self.assertEqual(self.outside_inventory(), before, 'a removal followed a replaced path')
        self.assertEqual((self.work / 'moved-builddir/keep').read_text(), 'cache', 'the moved directory was removed through its old descriptor')


class CargoJudgmentTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-cargo-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.target = self.root / 'controller/target'
        self.release = self.target / prov.TRIPLE / 'release'
        (self.release / 'deps').mkdir(parents=True)
        self.session = self.target / 'pw-build-session.json'
        (self.root / 'controller').mkdir(exist_ok=True)
        self.scope, self.env = own(self, self.root)
        self.assertEqual(run_main(['session-start', '--root', str(self.root), '--describe', 'x', '--commit', 'x',
                                   '--version', '0', '--build-number', '0'], self.env)[0], 0)

    def unit(self, name, meta, payload, fresh=False, rustflags=('-C', 'opt-level=1'), link=True, fingerprint=True):
        executable = self.release / name
        if executable.exists():
            executable.unlink()  # a rewrite through the old inode would also rewrite its hard-linked deps file
        executable.write_bytes(payload)
        deps = self.release / 'deps' / f"{name.replace('-', '_')}-{meta}"
        if link:
            os.link(executable, deps)
        else:
            deps.write_bytes(payload)
        if fingerprint is not None:
            directory = self.release / '.fingerprint' / f'controller-{meta}'
            directory.mkdir(parents=True, exist_ok=True)
            data = dict(rustc=111, features='[]', target=222, profile=333, path=444, deps=[], local=[], rustflags=list(rustflags), config=555, compile_kind=0)
            if fingerprint == 'malformed':
                (directory / f'bin-{name}.json').write_text('{oops')
            elif fingerprint == 'unsupported':
                (directory / f'bin-{name}.json').write_text(json.dumps(dict(data, rustflags='-C opt-level=1')))
            elif fingerprint:
                (directory / f'bin-{name}.json').write_text(json.dumps(data))
        return dict(reason='compiler-artifact', package_id=f'path+file://{self.root}/controller#0.1.0',
                    manifest_path=str(self.root / 'controller/Cargo.toml'), target=dict(kind=['bin'], name=name),
                    profile=dict(opt_level='3', debuginfo=0, debug_assertions=False, overflow_checks=False, test=False),
                    features=[], filenames=[str(executable)], executable=str(executable), fresh=fresh)

    def judge(self, messages, require='0', bins=('policy-witness', 'sandbox-log-observer', 'sbpl-check')):
        path = self.target / 'pw-build-messages.jsonl'
        path.write_text(''.join(json.dumps(m) + '\n' for m in messages))
        argv = ['cargo-judge', '--root', str(self.root),
                '--require-rebuilt', require, '--rustflags-source', 'script']
        for name in bins:
            argv += ['--bin', name]
        status, out, err = run_main(argv, dict(self.env, RUSTFLAGS='-C opt-level=1'))
        judgments = json.loads(self.session.read_text()).get('cargo', {}).get('judgments', {})
        return status, out, err, judgments

    def test_cargo_judgments_bind_fingerprints_without_guessing(self):
        messages = [self.unit('policy-witness', 'a' * 16, b'controller bytes'),
                    self.unit('sandbox-log-observer', 'b' * 16, b'observer bytes', fresh=True, link=False),
                    self.unit('sbpl-check', 'c' * 16, b'check bytes', fingerprint=None)]
        # A stale sibling for another target with the same bytes is never attributed to this unit.
        stale = self.release / 'deps' / ('policy_witness-' + 'd' * 16)
        stale.write_bytes(b'stale sibling bytes')
        status, out, err, judgments = self.judge(messages)
        self.assertEqual(status, 0, err)
        bound = judgments['policy-witness']
        self.assertEqual((bound['fresh'], bound['fingerprint']['status'], bound['fingerprint']['binding']['how']), (False, 'observed', 'hard link'))
        self.assertEqual(bound['effective_rustflags'], ['-C', 'opt-level=1'])
        self.assertEqual((bound['rustflags_source']['kind'], bound['rustflags_source']['agrees']), ('RUSTFLAGS (script default)', True))
        self.assertEqual(bound['fingerprint']['binding']['metadata_hash'], 'a' * 16)
        self.assertEqual(judgments['sandbox-log-observer']['fingerprint']['binding']['how'], 'identical bytes')
        self.assertIs(judgments['sandbox-log-observer']['fresh'], True)
        self.assertEqual(judgments['sbpl-check']['fingerprint']['status'], 'unavailable')
        self.assertNotIn(str(self.root), json.dumps(judgments).replace(prov.redact(str(self.root)), ''), 'exact paths are kept apart from published ones')
        # Fresh mode refuses a reused target, naming it.
        status, _, err, _ = self.judge(messages, require='1')
        self.assertEqual(status, 1)
        self.assertIn('sandbox-log-observer (reused)', err)
        # Ambiguous, malformed, unsupported and oversized fingerprints are explicit limitations, never guesses.
        (self.release / 'deps' / ('sandbox_log_observer-' + 'e' * 16)).write_bytes(b'observer bytes')
        malformed = self.unit('policy-witness', 'f' * 16, b'controller bytes 2', fingerprint='malformed')
        unsupported = self.unit('sbpl-check', '0' * 16, b'check bytes 2', fingerprint='unsupported')
        status, _, err, judgments = self.judge([malformed, messages[1], unsupported])
        self.assertEqual(status, 0, err)
        self.assertEqual(judgments['sandbox-log-observer']['fingerprint']['status'], 'ambiguous')
        self.assertEqual(judgments['policy-witness']['fingerprint']['status'], 'malformed')
        self.assertEqual(judgments['sbpl-check']['fingerprint']['status'], 'unsupported')
        self.assertIsNone(judgments['sbpl-check']['effective_rustflags'])
        self.assertIsNone(judgments['sbpl-check']['rustflags_source']['agrees'])
        many = self.unit('sbpl-check', '1' * 16, b'check bytes 3', rustflags=['-C', 'x'] * (prov.FLAG_LIMIT // 2 + 1))
        status, _, err, judgments = self.judge([messages[0], messages[1], many])
        self.assertEqual(status, 0, err)
        self.assertEqual((judgments['sbpl-check']['fingerprint']['status'], judgments['sbpl-check']['effective_rustflags']), ('oversized', None))
        (self.target / 'pw-build-messages.jsonl').write_text('{not json\n')
        status, _, err = run_main(['cargo-judge', '--root', str(self.root), '--bin', 'policy-witness',
                                   '--require-rebuilt', '0', '--rustflags-source', 'none'], self.env)
        self.assertEqual(status, 2)
        self.assertIn('malformed', err)

    def test_fresh_judgments_are_literal_booleans_bound_to_the_admitted_executable(self):
        valid = {name: self.unit(name, meta * 16, name.encode()) for name, meta in
                 (('policy-witness', 'a'), ('sandbox-log-observer', 'b'), ('sbpl-check', 'c'))}

        def without(message, key):
            return {k: v for k, v in message.items() if k != key}
        faults = {
            'missing': lambda m: without(m, 'fresh'),
            'null': lambda m: dict(m, fresh=None),
            'numeric zero': lambda m: dict(m, fresh=0),
            'numeric one': lambda m: dict(m, fresh=1),
            'string false': lambda m: dict(m, fresh='false'),
            'string true': lambda m: dict(m, fresh='true'),
            'another executable': lambda m: dict(m, executable=str(self.release / 'elsewhere')),
            "the host release area's executable": lambda m: dict(m, executable=str(self.target / 'release' / m['target']['name'])),
            'no profile': lambda m: without(m, 'profile'),
            'empty profile': lambda m: dict(m, profile={}),
            'test profile': lambda m: dict(m, profile=dict(m['profile'], test=True)),
            'profile flag string': lambda m: dict(m, profile=dict(m['profile'], debug_assertions='false')),
            'not a binary': lambda m: dict(m, target=dict(m['target'], kind=['lib'])),
        }
        for require in ('0', '1'):
            status, _, err, judgments = self.judge(list(valid.values()), require=require)
            self.assertEqual(status, 0, err)
            self.assertEqual({k: j['fresh'] for k, j in judgments.items()}, dict.fromkeys(valid, False))
            for label, fault in faults.items():
                with self.subTest(fault=label, fresh_mode=require):
                    messages = [fault(m) if name == 'sbpl-check' else m for name, m in valid.items()]
                    status, _, err, judgments = self.judge(messages, require=require)
                    self.assertEqual(status, 2, err)
                    self.assertIn("establishes no literal boolean fresh judgment", err)
                    self.assertIn('sbpl-check (', err)
                    self.assertEqual(judgments['sbpl-check']['status'], 'unknown')
            # A missing message and contradictory duplicates are unknown, never a default.
            for label, messages in (('absent', [valid['policy-witness'], valid['sandbox-log-observer']]),
                                    ('contradictory', [*valid.values(), dict(valid['sbpl-check'], fresh=True)]),
                                    ('duplicated', [*valid.values(), valid['sbpl-check']])):
                with self.subTest(fault=label, fresh_mode=require):
                    status, _, err, _ = self.judge(messages, require=require)
                    self.assertEqual(status, 2, err)
                    self.assertIn('sbpl-check (', err)

    def test_requested_flags_are_attributed_by_precedence(self):
        resolve = cargo_config.requested_flags
        host = 'aarch64-apple-darwin'
        both = resolve({}, {'CARGO_ENCODED_RUSTFLAGS': '-C\x1fx', 'RUSTFLAGS': '-C x'}, host)
        self.assertEqual((both['source'], both['tokens'], both['overrides']), ('CARGO_ENCODED_RUSTFLAGS', ['-C', 'x'], ['RUSTFLAGS']))
        # Equal tokens do not name a source: Cargo takes the encoded variable, and agreement is judged against it alone.
        attribution = prov.flag_attribution(['-C', 'y'], resolve({}, {'CARGO_ENCODED_RUSTFLAGS': '-C\x1fx', 'RUSTFLAGS': '-C y'}, host), 'caller')
        self.assertEqual((attribution['kind'], attribution['agrees']), ('CARGO_ENCODED_RUSTFLAGS', False))
        empty = resolve({}, {'CARGO_ENCODED_RUSTFLAGS': ''}, host)
        self.assertEqual((empty['source'], empty['tokens']), ('CARGO_ENCODED_RUSTFLAGS', []))
        config = cargo_config.wrap(dict(build=dict(rustflags=['-C', 'b']), target={host: dict(rustflags='-C t'), 'cfg(unix)': dict(rustflags=['-C', 'u'])}), '/x/.cargo/config.toml')
        rules = resolve(config, {}, host)
        self.assertEqual((rules['source'], rules['resolved'], rules['tokens'], rules['overrides']), ('target rules', False, None, ['build.rustflags']))
        # The rules that apply are the output triple's: a compiler reporting another host contributes nothing of its own.
        crossed = cargo_config.wrap(dict(target={'x86_64-apple-darwin': dict(rustflags='-C host'), prov.TRIPLE: dict(rustflags='-C output')}),
                                    '/x/.cargo/config.toml')
        self.assertEqual(resolve(crossed, {}, prov.TRIPLE)['tokens'], ['-C', 'output'])
        self.assertEqual(resolve(crossed, {}, 'x86_64-apple-darwin')['tokens'], ['-C', 'host'], 'the triple decides, not the host')
        environment_rule = resolve({}, {'CARGO_TARGET_AARCH64_APPLE_DARWIN_RUSTFLAGS': '-C e', 'CARGO_TARGET_X86_64_APPLE_DARWIN_RUSTFLAGS': '-C h'},
                                   prov.TRIPLE)
        self.assertEqual((environment_rule['source'], environment_rule['rules']), ('target rules', ['CARGO_TARGET_AARCH64_APPLE_DARWIN_RUSTFLAGS']))
        self.assertIsNone(prov.flag_attribution(['-C', 't'], rules, 'none')['agrees'], 'cfg() rules are not evaluated, so agreement is unknown')
        only_triple = cargo_config.wrap(dict(build=dict(rustflags=['-C', 'b']), target={host: dict(rustflags='-C t'), 'x86_64-unknown-linux-gnu': dict(rustflags='-C o')}), '/x/.cargo/config.toml')
        triple = resolve(only_triple, {}, host)
        self.assertEqual((triple['source'], triple['resolved'], triple['tokens']), ('target rules', True, ['-C', 't']))
        build = resolve(cargo_config.wrap(dict(build=dict(rustflags='-C b')), '/x/.cargo/config.toml'), {}, host)
        self.assertEqual((build['source'], build['tokens']), ('build.rustflags', ['-C', 'b']))
        mixed = resolve(cargo_config.wrap(dict(build=dict(rustflags='-C b')), '/x/.cargo/config.toml'), {'CARGO_BUILD_RUSTFLAGS': '-C e'}, host)
        self.assertEqual((mixed['source'], mixed['resolved'], mixed['tokens']), ('build.rustflags', False, None))
        self.assertEqual(resolve({}, {}, host)['source'], 'none')


class CargoConfigurationTests(unittest.TestCase):
    """The resolver's reading of constructed configuration graphs; real Cargo is the oracle in the opt-in refusal controls."""

    def test_failed_launcher_observations_never_fall_back_to_standalone_cargo(self):
        from unittest import mock
        with mock.patch.object(cargo_config.shutil, 'which', side_effect=lambda name, **kwargs: '/tools/' + name):
            for kind in ('timeout', 'output_overflow', 'launch_failed'):
                with self.subTest(kind=kind):
                    probe = lambda *args, **kwargs: dict(status='failed', kind=kind)
                    for env in ({}, dict(RUSTUP_TOOLCHAIN='stable')):
                        with self.assertRaises(cargo_config.Unresolved):
                            cargo_config.launcher(self.work, env, probe)
        with mock.patch.object(cargo_config.shutil, 'which', side_effect=lambda name, **kwargs: '/tools/cargo' if name == 'cargo' else None):
            with self.assertRaises(cargo_config.Unresolved):
                cargo_config.launcher(self.work, {}, lambda *a, **k: None)

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-cargo-config-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        self.home = self.work / 'cargo-home'
        self.home.mkdir()
        self.cwd = self.work / 'a/b/c'
        self.cwd.mkdir(parents=True)
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        for name in ('rustc', 'other-rustc'):
            (self.bin / name).write_text('#!/bin/sh\n')
            (self.bin / name).chmod(0o755)
        self.env = dict(HOME=str(self.work), CARGO_HOME=str(self.home), PATH=str(self.bin))

    def write(self, path, text):
        path = self.work / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text))
        return path

    def selected(self, env=None, cwd=None):
        merged, _ = cargo_config.load(cwd or self.cwd, env or self.env)
        return cargo_config.selection(merged, env or self.env, cwd or self.cwd, (env or self.env)['PATH'])

    def unresolved(self, needle, env=None):
        with self.assertRaises(cargo_config.Unresolved) as refused:
            self.selected(env)
        self.assertIn(needle, str(refused.exception))

    def test_toml_forms_discovery_and_precedence(self):
        for label, text in (('inline', 'build = { rustc = "/inline/rustc" }\n'), ('dotted', 'build.rustc = "/inline/rustc"\n'),
                            ('table', '[build]\nrustc = "/inline/rustc"\n')):
            with self.subTest(form=label):
                path = self.write('a/b/c/.cargo/config.toml', text)
                self.assertEqual(self.selected()['rustc']['command'], '/inline/rustc')
                path.unlink()
        # Discovery starts at the invocation directory: an ancestor's file applies, a deeper one wins, Cargo home is lowest.
        self.write('a/.cargo/config.toml', '[build]\nrustc = "/ancestor/rustc"\nrustc-wrapper = "/ancestor/wrap"\n')
        self.write('cargo-home/config.toml', '[build]\nrustc = "/home/rustc"\nrustc-workspace-wrapper = "/home/ws"\n')
        chosen = self.selected()
        self.assertEqual((chosen['rustc']['command'], chosen['wrapper']['command'], chosen['workspace_wrapper']['command']),
                         ('/ancestor/rustc', '/ancestor/wrap', '/home/ws'))
        self.assertEqual(self.selected(cwd=self.work)['rustc']['command'], '/home/rustc', 'a sibling invocation directory reads only Cargo home')
        self.write('a/b/.cargo/config.toml', '[build]\nrustc = "/deeper/rustc"\n')
        self.assertEqual(self.selected()['rustc']['command'], '/deeper/rustc')
        # Where both names exist Cargo reads `config`; Cargo home inside the walk is read once, at its walk position.
        self.write('a/b/.cargo/config', '[build]\nrustc = "/extensionless/rustc"\n')
        self.assertEqual(self.selected()['rustc']['command'], '/extensionless/rustc')
        files = cargo_config.discover(self.cwd, dict(self.env, CARGO_HOME=str(self.work / 'a/.cargo')))
        self.assertEqual([str(p.relative_to(self.work)) for p in files], ['a/b/.cargo/config', 'a/.cargo/config.toml'])
        # The environment overrides files: RUSTC over CARGO_BUILD_RUSTC over build.rustc, each lower source recorded as overridden.
        env = dict(self.env, CARGO_BUILD_RUSTC='/env/build-rustc')
        self.assertEqual((self.selected(env)['rustc']['source'], self.selected(env)['rustc']['overrides']), ('CARGO_BUILD_RUSTC', ['build.rustc']))
        env = dict(env, RUSTC='relative/rustc')
        rustc = self.selected(env)['rustc']
        self.assertEqual((rustc['source'], rustc['command'], rustc['overrides']),
                         ('RUSTC', str(self.cwd / 'relative/rustc'), ['CARGO_BUILD_RUSTC', 'build.rustc']))
        # An empty wrapper at a higher level disables the one a file configures.
        env = dict(self.env, RUSTC_WRAPPER='')
        wrapper = self.selected(env)['wrapper']
        self.assertEqual((wrapper['source'], wrapper['command'], wrapper.get('disabled')), ('RUSTC_WRAPPER', None, True))

    def test_program_paths_resolve_as_cargo_resolves_them(self):
        self.write('a/b/c/.cargo/config.toml', '[build]\nrustc = "tools/rustc"\nrustc-wrapper = "other-rustc"\n')
        chosen = self.selected()
        self.assertEqual(chosen['rustc']['command'], str(self.cwd / 'tools/rustc'), 'a config-relative path resolves from the parent of .cargo')
        self.assertEqual(chosen['wrapper']['command'], str(self.bin / 'other-rustc'), 'a bare name is searched on the child PATH')
        self.write('a/b/c/.cargo/config.toml', '[build]\nrustc-wrapper = "absent-tool"\n')
        self.unresolved('not on the PATH Cargo gives the compiler')
        self.write('a/b/c/.cargo/config.toml', '[build]\nrustc = ["/an", "array"]\n')
        self.unresolved('not a string program path')
        # The default compiler is found on the child PATH; with none, the selection is unknown, never assumed.
        self.write('a/b/c/.cargo/config.toml', '')
        self.unresolved('not a program path', dict(self.env, RUSTC=''))
        self.assertEqual(self.selected()['rustc']['command'], str(self.bin / 'rustc'))
        self.unresolved('not on the PATH', dict(self.env, PATH=str(self.work)))

    def test_includes_follow_cargo_order_and_refuse_what_cannot_be_read(self):
        self.write('a/b/c/.cargo/config.toml', 'include = ["one.toml", { path = "two.toml" }, { path = "absent.toml", optional = true }]\n'
                                              '[build]\nrustc-wrapper = "/own/wrap"\n')
        self.write('a/b/c/.cargo/one.toml', 'include = ["nested/three.toml"]\n[build]\nrustc = "/one/rustc"\nrustc-wrapper = "/one/wrap"\n')
        self.write('a/b/c/.cargo/two.toml', '[build]\nrustc = "/two/rustc"\n')
        self.write('a/b/c/.cargo/nested/three.toml', '[build]\nrustc-workspace-wrapper = "relative/ws"\n')
        merged, graph = cargo_config.load(self.cwd, self.env)
        chosen = cargo_config.selection(merged, self.env, self.cwd, self.env['PATH'])
        self.assertEqual(chosen['rustc']['command'], '/two/rustc', 'a later include wins over an earlier one')
        self.assertEqual(chosen['wrapper']['command'], '/own/wrap', 'the including file wins over its includes')
        self.assertEqual(chosen['workspace_wrapper']['command'], str(self.cwd / '.cargo/relative/ws'),
                         "an included file's relative path resolves from the parent of its own directory")
        self.assertEqual([Path(n['path']).name for n in graph], ['config.toml', 'one.toml', 'three.toml', 'two.toml'])
        self.assertEqual(graph[0]['includes'][2], dict(path=str(self.cwd / '.cargo/absent.toml'), optional=True, loaded=False))
        for label, text, needle in (
                ('required missing', 'include = ["gone.toml"]\n', 'required include'),
                ('not toml', 'include = ["settings.conf"]\n', 'does not end in .toml'),
                ('malformed entry', 'include = [{ file = "x.toml" }]\n', 'neither a path'),
                ('malformed file', 'build = { rustc = \n', 'not valid TOML'),
                ('cycle', 'include = ["loop.toml"]\n', 'include cycle'),
                ('type conflict', 'include = ["typed.toml"]\n[build]\nrustflags = "-C x"\n', 'is a array in one file and a str in another')):
            with self.subTest(include=label):
                self.write('a/b/c/.cargo/loop.toml', 'include = ["config.toml"]\n')
                self.write('a/b/c/.cargo/typed.toml', '[build]\nrustflags = ["-C", "y"]\n')
                self.write('a/b/c/.cargo/config.toml', text)
                self.unresolved(needle)
        chain = 'a/b/c/.cargo/config.toml'
        for depth in range(cargo_config.INCLUDE_DEPTH + 2):
            self.write(chain, f'include = ["d{depth}.toml"]\n')
            chain = f'a/b/c/.cargo/d{depth}.toml'
        self.write(chain, '')
        self.unresolved('nest deeper than')
        self.write('a/b/c/.cargo/config.toml', 'include = [' + ', '.join(f'"w{i}.toml"' for i in range(cargo_config.FILE_COUNT)) + ']\n')
        for i in range(cargo_config.FILE_COUNT):
            self.write(f'a/b/c/.cargo/w{i}.toml', '')
        self.unresolved('configuration files')
        self.write('a/b/c/.cargo/config.toml', '# ' + 'x' * cargo_config.FILE_BYTES + '\n')
        self.unresolved('larger than')
        self.write('a/b/c/.cargo/config.toml', 'include = [' + ', '.join(f'"big{i}.toml"' for i in range(5)) + ']\n')
        for i in range(5):
            self.write(f'a/b/c/.cargo/big{i}.toml', '# ' + 'x' * (cargo_config.FILE_BYTES - 100) + '\n')
        self.unresolved('in all')

    def test_env_entries_apply_as_cargo_applies_them(self):
        self.write('a/.cargo/config.toml', '[env]\nFORCED = { value = "lower", force = true }\nMERGED = { value = "lower", force = true }\n')
        self.write('a/b/c/.cargo/config.toml', textwrap.dedent('''\
            [env]
            PLAIN = "config"
            FORCED = { value = "higher", force = true }
            UNFORCED = { value = "config", force = false }
            MERGED = { value = "higher" }
            RELATIVE = { value = "vendor/lib", relative = true }
            '''))
        merged, _ = cargo_config.load(self.cwd, self.env)
        for inherited in (False, True):
            with self.subTest(inherited=inherited):
                base = dict(self.env, PLAIN='caller', FORCED='caller', UNFORCED='caller', MERGED='caller') if inherited else dict(self.env)
                child, entries = cargo_config.child_environment(merged, base, self.cwd)
                self.assertEqual(child['PLAIN'], 'caller' if inherited else 'config')
                self.assertEqual(child['UNFORCED'], 'caller' if inherited else 'config')
                self.assertEqual(child['FORCED'], 'higher')
                self.assertEqual(child['MERGED'], 'higher', 'tables merge field by field: the lower file\'s force stays')
                self.assertTrue(entries['MERGED']['force'] and entries['MERGED']['applied'])
                self.assertEqual(child['RELATIVE'], str(self.cwd / 'vendor/lib'))
                self.assertEqual(entries['PLAIN']['applied'], not inherited)
        for label, text, needle in (('mixed forms', '[env]\nFORCED = "a string"\n', 'is a table in one file and a str in another'),
                                    ('not a boolean', '[env]\nX = { value = "v", force = "yes" }\n', 'not a boolean'),
                                    ('no value', '[env]\nX = { force = true }\n', 'neither a string'),
                                    ('not a string', '[env]\nX = { value = 3 }\n', 'does not hold a string')):
            with self.subTest(env=label):
                self.write('a/b/c/.cargo/config.toml', text)
                with self.assertRaises(cargo_config.Unresolved) as refused:
                    merged, _ = cargo_config.load(self.cwd, self.env)
                    cargo_config.child_environment(merged, dict(self.env), self.cwd)
                self.assertIn(needle, str(refused.exception))
        # A forced PATH selects the compiler Cargo starts; forced inputs that differ from the build's are conflicts.
        alternate = self.work / 'alternate'
        alternate.mkdir()
        (alternate / 'rustc').write_text('#!/bin/sh\n')
        (alternate / 'rustc').chmod(0o755)
        canary = 'PW_CANARY_' + os.urandom(6).hex()
        self.write('a/b/c/.cargo/config.toml', f'[env]\nPATH = {{ value = "{alternate}", force = true }}\n'
                                              'MACOSX_DEPLOYMENT_TARGET = { value = "26.1", force = true }\n'
                                              f'UNRELATED = "{canary}"\n')
        merged, graph = cargo_config.load(self.cwd, self.env)
        base = dict(self.env, MACOSX_DEPLOYMENT_TARGET='26.0', SDKROOT='/sdk')
        child, entries = cargo_config.child_environment(merged, base, self.cwd)
        programs = cargo_config.selection(merged, base, self.cwd, child['PATH'])
        self.assertEqual(programs['rustc']['command'], str(alternate / 'rustc'))
        resolution = dict(graph=graph, launcher=dict(kind='cargo'), env_entries=entries, programs=programs, child=child, merged=merged)
        self.assertEqual(cargo_config.conflicts(resolution, base), [('MACOSX_DEPLOYMENT_TARGET', '26.1', '26.0')])
        published = json.dumps(cargo_config.summary(resolution, str(self.work)))
        self.assertNotIn(canary, published, 'an unrelated [env] value reached the summary')
        self.assertNotIn(str(alternate), published.replace(str(alternate / 'rustc'), ''), 'the replaced PATH value reached the summary')
        self.assertIn('"path_replaced_by_env": true', published)
        self.write('a/b/c/.cargo/config.toml', '[env]\nMACOSX_DEPLOYMENT_TARGET = { value = "26.0", force = true }\n')
        merged, graph = cargo_config.load(self.cwd, self.env)
        child, entries = cargo_config.child_environment(merged, base, self.cwd)
        self.assertEqual(cargo_config.conflicts(dict(child=child), base), [], 'a forced value equal to the build\'s is the valid neighbour')


class OutputTripleSelectionTests(unittest.TestCase):
    def test_the_command_line_target_overrides_lower_defaults(self):
        file = '/x/.cargo/config.toml'
        named = cargo_config.wrap(dict(build=dict(target='x86_64-apple-darwin')), file)
        selected = cargo_config.target_selection(named, {'CARGO_BUILD_TARGET': 'x86_64-apple-darwin'}, prov.TRIPLE)
        self.assertEqual(selected, dict(source='--target', triple=prov.TRIPLE, overrides=['CARGO_BUILD_TARGET', 'build.target']),
                         'lower-precedence defaults are recorded as overridden, never applied and never refused')
        listed = cargo_config.wrap(dict(build=dict(target=['x86_64-apple-darwin', prov.TRIPLE])), file)
        self.assertEqual(cargo_config.target_selection(listed, {}, prov.TRIPLE)['overrides'], ['build.target'])
        self.assertEqual(cargo_config.target_selection({}, {}, prov.TRIPLE)['overrides'], [])
        for value in (7, [7], dict(name='x86_64-apple-darwin')):
            with self.subTest(value=value), self.assertRaises(cargo_config.Unresolved):
                cargo_config.target_selection(cargo_config.wrap(dict(build=dict(target=value)), file), {}, prov.TRIPLE)
        summary = cargo_config.summary(dict(graph=[], launcher=dict(kind='cargo'), env_entries={}, programs={}, child={},
                                            target=selected), '/Users/nobody')
        self.assertEqual(summary['target'], selected)
        self.assertNotIn('target', cargo_config.summary(dict(graph=[], launcher=dict(kind='cargo'), env_entries={}, programs={}, child={}),
                                                        '/Users/nobody'))


class SdkTests(unittest.TestCase):
    OTOOL = textwrap.dedent('''\
        Load command 8
              cmd LC_UUID
          cmdsize 24
             uuid 2E4F9C8A-1111-2222-3333-444444444444
        Load command 9
              cmd LC_BUILD_VERSION
          cmdsize 32
         platform 1
            minos 26.0
              sdk {sdk}
           ntools 1
             tool 3
          version 27037.1
        Load command 10
              cmd LC_MAIN
        ''')

    def test_sdk_versions_normalize_and_unknowns_never_agree(self):
        self.assertEqual(prov.normalize_version('27.0'), (27,))
        self.assertEqual(prov.normalize_version('27'), (27,))
        self.assertEqual(prov.normalize_version('26.5'), (26, 5))
        self.assertNotEqual(prov.normalize_version('26.5'), prov.normalize_version('26.50'))
        self.assertEqual(prov.normalize_version('26.5.0'), prov.normalize_version('26.5'))
        for text in ('n/a', '', None, '27.0a', 'latest'):
            self.assertIsNone(prov.normalize_version(text), text)
        parsed = prov.parse_build_version(self.OTOOL.format(sdk='27.0'))
        self.assertEqual((parsed['uuid'], parsed['platform'], parsed['minos'], parsed['sdk']), ('2E4F9C8A-1111-2222-3333-444444444444', '1', '26.0', '27.0'))
        self.assertEqual(parsed['tools'], [dict(tool='3', version='27037.1')])
        self.assertEqual(parsed['problems'], [])
        self.assertIn('sdk is missing', prov.parse_build_version(self.OTOOL.format(sdk='n/a'))['problems'][0])
        self.assertTrue(prov.parse_build_version(self.OTOOL.format(sdk='27.0') + self.OTOOL.format(sdk='27.0'))['problems'])
        self.assertTrue(prov.parse_build_version('Load command 0\n      cmd LC_MAIN\n')['problems'])
        self.assertIn('LC_UUID', prov.parse_build_version(self.OTOOL.format(sdk='27.0').replace('LC_UUID', 'LC_OTHER'))['problems'][0])
        # Over a real Mach-O: equivalent numeric forms agree with the selected SDK; another version or a malformed selection refuses.
        directory = tempfile.TemporaryDirectory(prefix='pw-sdk-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        work = Path(directory.name)
        source = work / 'probe.c'
        source.write_text('int main(void) { return 0; }\n')
        binary = work / 'probe'
        subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', str(source), '-o', str(binary)], check=True, capture_output=True)
        sdk = subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version'], check=True, capture_output=True, text=True).stdout.strip()
        (work / 'controller').mkdir()
        _, env = own(self, work)
        self.assertEqual(run_main(['session-start', '--root', str(work), '--describe', 'x', '--commit', 'x',
                                   '--version', '0', '--build-number', '0'], env)[0], 0)
        metadata = prov.output_metadata(binary)
        self.assertEqual(metadata['status'], 'ok')
        self.assertEqual(prov.normalize_version(metadata['sdk']), prov.normalize_version(sdk))
        equivalent = sdk + '.0' if '.' in sdk else sdk + '.0'
        self.assertEqual(run_main(['sdk-check', '--root', str(work), '--sdk-version', equivalent, str(binary)], env)[0], 0)
        status, _, err = run_main(['sdk-check', '--root', str(work), '--sdk-version', '1.2', str(binary)], env)
        self.assertEqual(status, 1)
        self.assertIn('built against SDK', err)
        status, _, err = run_main(['sdk-check', '--root', str(work), '--sdk-version', 'n/a', str(binary)], env)
        self.assertEqual(status, 1)
        self.assertIn('not a numeric version', err)
        status, _, err = run_main(['sdk-check', '--root', str(work), '--sdk-version', sdk, str(source)], env)
        self.assertEqual(status, 1, 'a file without load commands never agrees')


# ---- the output target: real Mach-O fixtures and an independent reading of their bytes ----------------------------

CPU_ARM64, CPU_X86_64 = 0x0100000c, 0x01000007
LC_BUILD_VERSION = 0x32


def oracle_name(cputype, cpusubtype):
    """The architecture a CPU type and subtype name, read here from the header, not from lipo."""
    if cputype == CPU_ARM64:
        return {0: 'arm64', 2: 'arm64e'}.get(cpusubtype & 0x00ffffff, f'arm64 subtype {cpusubtype}')
    if cputype == CPU_X86_64:
        return 'x86_64'
    return f'cputype {cputype:#x}'


def oracle(path):
    """The container, architectures, file type and platform a file's bytes carry, by walking its header and load
    commands directly: the fixtures' independent description, never the helper under test."""
    data = Path(path).read_bytes()
    if data[:4] == b'\xcf\xfa\xed\xfe' and len(data) >= 32:
        cputype, cpusubtype, filetype, ncmds = struct.unpack_from('<IIII', data, 4)
        platform, offset = None, 32
        for _ in range(ncmds):
            if offset + 8 > len(data):
                platform = None
                break
            command, size = struct.unpack_from('<II', data, offset)
            if command == LC_BUILD_VERSION:
                platform = str(struct.unpack_from('<I', data, offset + 8)[0])
            offset += size
        return dict(container='thin', architectures=[oracle_name(cputype, cpusubtype)], filetype=filetype, platform=platform)
    if data[:4] == b'\xca\xfe\xba\xbe':
        slices = struct.unpack_from('>I', data, 4)[0]
        names = [oracle_name(*struct.unpack_from('>II', data, 8 + 20 * index)) for index in range(slices)]
        return dict(container='fat', architectures=names, slices=slices)
    return dict(container=None)


def target_fixtures(work):
    """Real Mach-O fixtures linked with the selected macOS SDK, and malformed files, by name.

    The platform mismatch is an arm64 Mac Catalyst executable (platform 6), which
    the macOS SDK links; a dSYM companion of an x86_64 executable is debug data
    and is not runnable code."""
    source = work / 'main.c'
    source.write_text('int main(void) { return 0; }\n')

    def clang(*args):
        subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', *map(str, args)], check=True, capture_output=True, timeout=120)

    found = {}
    for name, flags in (('thin-arm64', ['-arch', 'arm64']), ('thin-x86_64', ['-arch', 'x86_64']), ('thin-arm64e', ['-arch', 'arm64e']),
                        ('universal', ['-arch', 'arm64', '-arch', 'x86_64'])):
        found[name] = work / name
        clang(*flags, '-mmacosx-version-min=26.0', source, '-o', found[name])
    found['one-slice-fat'] = work / 'one-slice-fat'
    subprocess.run(['/usr/bin/lipo', '-create', found['thin-arm64'], '-output', found['one-slice-fat']], check=True, capture_output=True)
    found['catalyst-arm64'] = work / 'catalyst-arm64'
    clang('-target', 'arm64-apple-ios17.0-macabi', source, '-o', found['catalyst-arm64'])
    found['truncated'] = work / 'truncated'
    found['truncated'].write_bytes(found['thin-arm64'].read_bytes()[:100])
    found['short-header'] = work / 'short-header'
    found['short-header'].write_bytes(found['thin-arm64'].read_bytes()[:6])
    found['text'] = work / 'text'
    found['text'].write_text('#!/bin/sh\nexit 0\n')
    found['empty'] = work / 'empty'
    found['empty'].write_bytes(b'')
    found['class-file'] = work / 'class-file'   # the fat magic with a Java class file's version words, not a container
    found['class-file'].write_bytes(b'\xca\xfe\xba\xbe\x00\x00\x00\x41' + b'\0' * 64)
    found['missing'] = work / 'missing'
    objects = work / 'debug.o'
    clang('-arch', 'x86_64', '-g', '-c', source, '-o', objects)
    found['debug-x86_64'] = work / 'debug-x86_64'
    clang('-arch', 'x86_64', '-mmacosx-version-min=26.0', objects, '-o', found['debug-x86_64'])
    subprocess.run(['/usr/bin/xcrun', 'dsymutil', found['debug-x86_64'], '-o', work / 'debug-x86_64.dSYM'], check=True, capture_output=True)
    found['dsym-x86_64'] = work / 'debug-x86_64.dSYM/Contents/Resources/DWARF/debug-x86_64'
    clang('-arch', 'arm64', '-arch', 'x86_64', '-g', source, '-o', work / 'debug-universal')
    subprocess.run(['/usr/bin/xcrun', 'dsymutil', work / 'debug-universal', '-o', work / 'debug-universal.dSYM'],
                   check=True, capture_output=True)
    found['dsym-universal'] = work / 'debug-universal.dSYM/Contents/Resources/DWARF/debug-universal'
    for name, inputs, flags in (
            ('dsym-one-slice', [found['dsym-x86_64']], []),
            ('dsym-fat64', [found['dsym-universal']], ['-fat64']),
            ('mixed-debug-code', [found['dsym-x86_64'], found['thin-arm64']], [])):
        found[name] = work / name
        subprocess.run(['/usr/bin/lipo', '-create', *inputs, *flags, '-output', found[name]], check=True, capture_output=True)
    return found


class OutputTargetTests(unittest.TestCase):
    """The output check against real fixtures whose bytes this class reads itself first."""

    # What the fixtures' bytes must be before the helper is consulted, and the one decision each must produce.
    EXPECTED = {
        'thin-arm64': (dict(container='thin', architectures=['arm64'], platform='1'), []),
        'thin-x86_64': (dict(container='thin', architectures=['x86_64'], platform='1'), ['architecture x86_64, not exactly arm64']),
        'thin-arm64e': (dict(container='thin', architectures=['arm64e'], platform='1'), ['architecture arm64e, not exactly arm64']),
        'universal': (dict(container='fat', architectures=['arm64', 'x86_64']), ['not a thin Mach-O', 'not exactly arm64']),
        'one-slice-fat': (dict(container='fat', architectures=['arm64']), ['a fat container with 1 slice(s) (arm64), not a thin Mach-O']),
        'catalyst-arm64': (dict(container='thin', architectures=['arm64'], platform='6'), ['platform 6 (Mac Catalyst), not macOS (1)']),
    }
    MALFORMED = {'truncated': 'no readable LC_BUILD_VERSION platform', 'short-header': 'the Mach-O header is truncated',
                 'text': 'not a Mach-O file', 'empty': 'not a Mach-O file', 'class-file': 'not a Mach-O file',
                 'missing': 'unreadable (FileNotFoundError)'}

    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='pw-output-target-', dir='/private/tmp')
        cls.work = Path(cls.directory.name).resolve()
        cls.fixtures = target_fixtures(cls.work)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def observe(self, path, module=output_target):
        return module.observe(path, probe=prov.probe, read_metadata=prov.output_metadata)

    def test_fixtures_are_what_their_bytes_say(self):
        for name, (expected, _) in self.EXPECTED.items():
            with self.subTest(fixture=name):
                found = oracle(self.fixtures[name])
                self.assertEqual(found['container'], expected['container'])
                self.assertEqual(sorted(found['architectures']), sorted(expected['architectures']))
                if 'platform' in expected:
                    self.assertEqual((found['filetype'], found['platform']), (2, expected['platform']))
        self.assertEqual(oracle(self.fixtures['dsym-x86_64'])['filetype'], output_target.MH_DSYM)
        self.assertEqual(oracle(self.fixtures['dsym-x86_64'])['architectures'], ['x86_64'])
        self.assertEqual(oracle(self.fixtures['truncated'])['platform'], None, 'the truncated copy keeps its header but loses its load commands')
        self.assertFalse(self.fixtures['missing'].exists())

    def test_observations_are_kept_apart_from_the_decision(self):
        for name, (expected, reasons) in self.EXPECTED.items():
            with self.subTest(fixture=name):
                found = self.observe(self.fixtures[name])
                self.assertEqual(found['problems'], [])
                self.assertEqual(found['container'], expected['container'])
                self.assertEqual(sorted(found['architectures']), sorted(expected['architectures']))
                self.assertEqual(found['platform'], expected.get('platform'))
                if expected['container'] == 'fat':
                    self.assertEqual(found['slices'], len(expected['architectures']))
                problems = output_target.target_problems(found)
                self.assertEqual(len(problems), len(reasons), problems)
                for reason, problem in zip(reasons, problems):
                    self.assertIn(reason, problem)
                self.assertEqual(output_target.describe(found).startswith(str(self.fixtures[name]) + ': '), True)
        for name, reason in self.MALFORMED.items():
            with self.subTest(fixture=name):
                found = self.observe(self.fixtures[name])
                self.assertEqual(output_target.target_problems(found), [reason])
                self.assertIsNone(found['architectures'] if name != 'truncated' else found['platform'])

    def test_failed_and_inconsistent_tool_reports_refuse(self):
        thin = self.fixtures['thin-arm64']
        reports = {'nonzero': dict(status='failed', kind='nonzero_exit'), 'timeout': dict(status='failed', kind='timeout'),
                   'empty': dict(status='ok', text='\n'), 'two names for a thin file': dict(status='ok', text='arm64 x86_64\n'),
                   'unknown name': dict(status='ok', text='arm65\n'), 'oversized': dict(status='ok', text='a' * 40 + '\n'),
                   'substring': dict(status='ok', text='xarm64\n')}
        for label, report in reports.items():
            with self.subTest(report=label):
                found = output_target.observe(thin, probe=lambda argv, **_: report, read_metadata=prov.output_metadata)
                self.assertIsNone(found['architectures'])
                self.assertTrue(output_target.target_problems(found))
        found = output_target.observe(thin, probe=prov.probe, read_metadata=lambda path: dict(status='failed', platform=None))
        self.assertEqual(output_target.target_problems(found), ['no readable LC_BUILD_VERSION platform'])
        calls = []
        output_target.observe(thin, probe=lambda argv, **bounds: calls.append((argv, bounds)) or prov.probe(argv, **bounds),
                              read_metadata=prov.output_metadata)
        self.assertEqual(calls[0][0], ['/usr/bin/lipo', '-archs', str(thin)], 'architecture names come from lipo -archs on the file')
        self.assertEqual(calls[0][1], dict(limit=4096, stderr_limit=4096))

    def test_runnable_code_is_found_by_header_and_dsym_data_is_not_code(self):
        app = self.work / 'scan.app'
        (app / 'Contents/MacOS').mkdir(parents=True)
        (app / 'Contents/Resources').mkdir(parents=True)
        shutil.copy2(self.fixtures['thin-arm64'], app / 'Contents/MacOS/main')
        shutil.copy2(self.fixtures['universal'], app / 'Contents/Resources/renamed.txt')
        shutil.copy2(self.fixtures['truncated'], app / 'Contents/Resources/torn')
        shutil.copytree(self.work / 'debug-x86_64.dSYM', app / 'Contents/MacOS/main.dSYM')
        shutil.copytree(self.work / 'debug-universal.dSYM', app / 'Contents/Resources/universal.dSYM')
        for name in ('dsym-one-slice', 'dsym-fat64'):
            shutil.copy2(self.fixtures[name], app / 'Contents/Resources' / name)
        (app / 'Contents/Info.plist').write_text('<plist/>')
        (app / 'Contents/MacOS/link').symlink_to(self.fixtures['thin-x86_64'])
        found = [str(path.relative_to(app)) for path in output_target.runnable_code(app)]
        self.assertEqual(found, ['Contents/MacOS/main', 'Contents/Resources/renamed.txt', 'Contents/Resources/torn'])
        # A dSYM companion's own metadata names another architecture; it is excluded as debug data, not passed.
        dsym = self.observe(app / 'Contents/MacOS/main.dSYM/Contents/Resources/DWARF/debug-x86_64')
        self.assertEqual((dsym['filetype'], dsym['architectures']), (output_target.MH_DSYM, ['x86_64']))
        # The fat dSYM fixtures contain only debug slices, independently read from their tables and thin headers.
        for name in ('dsym-universal', 'dsym-one-slice', 'dsym-fat64'):
            data = self.fixtures[name].read_bytes()
            layout = '>IIIII' if data[:4] == b'\xca\xfe\xba\xbe' else '>IIQQII'
            count = struct.unpack_from('>I', data, 4)[0]
            self.assertEqual(count, 1 if name == 'dsym-one-slice' else 2)
            for index in range(count):
                offset = struct.unpack_from(layout, data, 8 + index * struct.calcsize(layout))[2]
                self.assertEqual(struct.unpack_from('<I', data, offset + 12)[0], 0xa)
        # A fat file with one debug slice and one runnable slice is still code, even under a dSYM path.
        mixed = app / 'Contents/MacOS/main.dSYM/mixed'
        shutil.copy2(self.fixtures['mixed-debug-code'], mixed)
        self.assertIn(mixed, output_target.runnable_code(app))
        self.assertTrue(output_target.target_problems(self.observe(mixed)))
        # A Mach-O moved under a dSYM directory is still code: exclusion is by file type, not by path.
        shutil.copy2(self.fixtures['thin-x86_64'], app / 'Contents/MacOS/main.dSYM/Contents/Resources/DWARF/hidden')
        self.assertIn('Contents/MacOS/main.dSYM/Contents/Resources/DWARF/hidden',
                      [str(path.relative_to(app)) for path in output_target.runnable_code(app)])
        (app / 'Contents/Resources/locked').mkdir()
        (app / 'Contents/Resources/locked').chmod(0)
        self.addCleanup((app / 'Contents/Resources/locked').chmod, 0o755)
        with self.assertRaises(OSError):
            output_target.runnable_code(app)

    def test_malformed_fat_debug_slices_are_not_exempted(self):
        app = self.work / 'malformed-dsym.app'
        app.mkdir()
        original = self.fixtures['dsym-universal'].read_bytes()
        _, _, first, size, _ = struct.unpack_from('>IIIII', original, 8)
        mutations = {
            'short-table': original[:20],
            'short-slice': original[:first + 20],
        }
        for name, position, value in (
                ('slice-in-table', 16, 8), ('outside-file', 16, len(original)),
                ('short-header', 20, 20), ('oversized-slice', 20, len(original)),
                ('invalid-alignment', 24, 64), ('overlapping-slices', 36, first),
                ('wrong-cpu', 8, 0), ('unknown-slice', first, 0), ('code-slice', first + 12, 2)):
            changed = bytearray(original)
            struct.pack_into('>I' if position < first else '<I', changed, position, value)
            mutations[name] = changed
        for name, data in mutations.items():
            path = app / name
            path.write_bytes(data)
        self.assertEqual(set(output_target.runnable_code(app)), set(app.iterdir()),
                         'malformed debug claims remain in the code inventory and are refused as fat containers')
        for path in app.iterdir():
            self.assertTrue(output_target.target_problems(self.observe(path)), path)

    def test_the_build_gate_records_each_stage_and_refuses_any_departure(self):
        root = self.work / 'gate'
        (root / 'controller').mkdir(parents=True)
        _, env = own(self, root)
        self.assertEqual(run_main(['session-start', '--root', str(root), '--describe', 'x', '--commit', 'x', '--version', '0',
                                   '--build-number', '0', '--knob', 'BUILD_XPC=1'], env)[0], 0)
        session = root / 'controller/target/pw-build-session.json'
        self.assertEqual(json.loads(session.read_text())['output_target'], output_target.DECLARED)
        status, out, err = run_main(['output-check', '--root', str(root), '--stage', 'cargo', str(self.fixtures['thin-arm64'])], env)
        self.assertEqual(status, 0, err)
        self.assertIn('1 outputs are thin arm64 Mach-O for macOS (cargo)', out)
        for name in ('thin-x86_64', 'universal', 'one-slice-fat', 'thin-arm64e', 'catalyst-arm64', 'truncated', 'text', 'missing'):
            with self.subTest(output=name):
                status, _, err = run_main(['output-check', '--root', str(root), '--stage', 'native',
                                           str(self.fixtures['thin-arm64']), str(self.fixtures[name])], env)
                self.assertEqual(status, 1, err)
                self.assertIn('outputs are not thin arm64 Mach-O executables for macOS', err)
                self.assertIn(f"{self.fixtures[name]}: ", err)
                self.assertNotIn(f"{self.fixtures['thin-arm64']}: ", err, 'only the departing output is named')
                recorded = json.loads(session.read_text())['output_check']['native']
                self.assertEqual(len(recorded['problems']), 1)
                self.assertEqual(recorded['outputs'][str(self.fixtures['thin-arm64'])]['problems'], [])
        # A bundle is scanned by header: an unlisted renamed universal file refuses; a dSYM companion is not code.
        app = self.work / 'gate.app'
        for relative in prov.FULL_OUTPUTS:
            path = app / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.fixtures['thin-arm64'], path)
        shutil.copytree(self.work / 'debug-x86_64.dSYM', app / 'Contents/MacOS/main.dSYM')
        shutil.copytree(self.work / 'debug-universal.dSYM', app / 'Contents/MacOS/universal.dSYM')
        status, out, err = run_main(['output-check', '--root', str(root), '--stage', 'assembled', '--app', str(app)], env)
        self.assertEqual(status, 0, err)
        self.assertIn(f'{len(prov.FULL_OUTPUTS)} outputs', out)
        shutil.copy2(self.fixtures['universal'], app / 'Contents/MacOS/main.dSYM/notes.txt')
        status, _, err = run_main(['output-check', '--root', str(root), '--stage', 'packaging', '--app', str(app)], env)
        self.assertEqual(status, 1, err)
        self.assertIn('notes.txt: a fat container with 2 slice(s)', err)
        status, _, err = run_main(['output-check', '--root', str(root), '--stage', 'assembled', '--app', str(self.work / 'absent.app')], env)
        self.assertEqual(status, 1, err)
        self.assertIn('the bundle cannot be scanned', err)
        empty = self.work / 'empty.app'
        empty.mkdir()
        status, _, err = run_main(['output-check', '--root', str(root), '--stage', 'assembled', '--app', str(empty)], env)
        self.assertEqual(status, 1, err)
        self.assertIn('policy-witness: unreadable (FileNotFoundError)', err)
        self.assertEqual(set(json.loads(session.read_text())['output_check']), {'cargo', 'native', 'assembled', 'packaging'})
        status, _, err = run_main(['output-check', '--root', str(root), '--stage', 'cargo', str(self.fixtures['thin-arm64'])], clean_env())
        self.assertEqual(status, 2, 'the gate writes the session only under an owned build')
        self.assertIn('build helpers mutate only under an owned build', err)

    def test_app_gates_check_required_paths_without_macho_headers_in_both_variants(self):
        root = self.work / 'required-gate'
        (root / 'controller').mkdir(parents=True)
        _, env = own(self, root)
        for xpc, expected in (('0', prov.PARTIAL_OUTPUTS), ('1', prov.FULL_OUTPUTS)):
            self.assertEqual(run_main(['session-start', '--root', str(root), '--describe', 'x', '--commit', 'x', '--version', '0',
                                       '--build-number', '0', '--knob', f'BUILD_XPC={xpc}'], env)[0], 0)
            app = root / f'variant-{xpc}.app'
            for relative in expected:
                path = app / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.fixtures['thin-arm64'], path)
            for stage in ('assembled', 'packaging'):
                args = ['output-check', '--root', str(root), '--stage', stage, '--app', str(app)]
                self.assertEqual(run_main(args, env)[0], 0, 'the variant has exactly its own required inventory')
                for relative in expected:
                    path = app / relative
                    for label, data in (('text', b'#!/bin/sh\nexit 0\n'), ('empty', b''), ('short-magic', b'\xcf\xfa'), ('missing', None)):
                        with self.subTest(xpc=xpc, stage=stage, path=relative, fault=label):
                            if data is None:
                                path.unlink()
                            else:
                                path.write_bytes(data)
                            status, _, err = run_main(args, env)
                            self.assertEqual(status, 1, err)
                            reason = 'unreadable (FileNotFoundError)' if data is None else 'not a Mach-O file'
                            self.assertIn(f'{path}: {reason}', err)
                            recorded = json.loads((root / 'controller/target/pw-build-session.json').read_text())['output_check'][stage]
                            self.assertEqual(len(recorded['outputs']), len(expected))
                            self.assertEqual(recorded['problems'], [f'{path}: {reason}'])
                    shutil.copy2(self.fixtures['thin-arm64'], path)

    def test_weakened_predicates_fail_these_controls(self):
        """Each weakening, applied to a copy of the helper, accepts a fixture the decision above refuses."""
        import importlib.util
        source = (ROOT / 'tests/lib/output_target.py').read_text()
        weakenings = {
            'container requirement removed': (
                "    if observation['container'] != CONTAINER:\n        found.append(", "    if False:\n        found.append(", 'one-slice-fat'),
            'the predicate reduced to arm64 membership': (
                "    if observation['architectures'] != [ARCHITECTURE]:", "    if ARCHITECTURE not in observation['architectures']:", 'universal'),
            'names matched as a substring': (
                "    if observation['architectures'] != [ARCHITECTURE]:", "    if ARCHITECTURE not in names:", 'thin-arm64e'),
            'platform requirement removed': (
                "    if observation['container'] == CONTAINER and observation['platform'] != PLATFORM:", "    if False:", 'catalyst-arm64'),
        }
        for label, (old, new, fixture) in weakenings.items():
            with self.subTest(weakening=label):
                self.assertEqual(source.count(old), 1, old)
                mutated = source.replace(old, new, 1)
                if label == 'the predicate reduced to arm64 membership':
                    # Membership alone is masked by the container rule for every fat file; the reduction drops both.
                    mutated = mutated.replace("    if observation['container'] != CONTAINER:\n        found.append(",
                                              "    if False:\n        found.append(", 1)
                path = self.work / f"weakened-{label.replace(' ', '-')}.py"
                path.write_text(mutated)
                spec = importlib.util.spec_from_file_location(path.stem.replace('-', '_'), path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(output_target.target_problems(self.observe(self.fixtures[fixture])) != [], True)
                self.assertEqual(module.target_problems(self.observe(self.fixtures[fixture], module)), [],
                                 f'{label}: the weakened helper must accept {fixture}, which this control refuses')


class SignatureDisplayTests(unittest.TestCase):
    IDENTITY = 'Developer ID Application: Control (TEAMID00AA)'
    VALID = textwrap.dedent('''\
        Identifier=sbpl-check
        Format=Mach-O thin (arm64)
        CodeDirectory v=20500 size=1654 flags=0x10000(runtime) hashes=46+2 location=embedded
        Signature size=9042
        Authority=Developer ID Application: Control (TEAMID00AA)
        Authority=Developer ID Certification Authority
        Authority=Apple Root CA
        Timestamp=Oct 15, 2026 at 1:16:12 PM
        TeamIdentifier=TEAMID00AA
        ''')

    def test_signature_displays_establish_class_team_and_timestamp(self):
        valid = signer_check.parse_display(self.VALID)
        self.assertEqual(signer_check.signature_problems(valid, self.IDENTITY), [])
        self.assertTrue(valid['timestamp'] and valid['readable'] and valid['runtime'])
        signed_time = signer_check.parse_display(self.VALID.replace('Timestamp=', 'Signed Time='))
        problems = signer_check.signature_problems(signed_time, self.IDENTITY)
        self.assertEqual(len(problems), 1)
        self.assertIn('no secure timestamp', problems[0])
        self.assertIn('Signed Time', problems[0])
        team = signer_check.parse_display(self.VALID.replace('TeamIdentifier=TEAMID00AA', 'TeamIdentifier=OTHERTEAM1'))
        self.assertTrue(any('team identifier is OTHERTEAM1' in p for p in signer_check.signature_problems(team, self.IDENTITY)))
        chain = signer_check.parse_display(self.VALID.replace('Authority=Developer ID Certification Authority\n', 'Authority=Apple Development CA\n'))
        self.assertTrue(any('certificate chain' in p for p in signer_check.signature_problems(chain, self.IDENTITY)))
        development = signer_check.parse_display(self.VALID.replace('Developer ID Application: Control (TEAMID00AA)', 'Apple Development: Control (TEAMID00AA)'))
        self.assertTrue(any('signed by Apple Development' in p for p in signer_check.signature_problems(development, self.IDENTITY)))
        adhoc = signer_check.parse_display('Identifier=x\nFormat=Mach-O thin (arm64)\nCodeDirectory v=20400 size=1 flags=0x2(adhoc) hashes=1+1 location=embedded\nSignature=adhoc\nTeamIdentifier=not set\n')
        self.assertEqual(signer_check.signature_problems(adhoc, self.IDENTITY), ['signed by ad hoc, not ' + self.IDENTITY])
        self.assertIsNone(adhoc['team'], "codesign's `TeamIdentifier=not set` names no team")
        runtime = signer_check.parse_display(self.VALID.replace('flags=0x10000(runtime)', 'flags=0x0(none)'))
        self.assertTrue(any('hardened runtime' in p for p in signer_check.signature_problems(runtime, self.IDENTITY)))
        ambiguous = signer_check.parse_display(self.VALID + self.VALID)
        self.assertFalse(ambiguous['readable'])
        self.assertTrue(any('ambiguous' in p for p in signer_check.signature_problems(ambiguous, self.IDENTITY)))
        unsigned = dict(leaf=None, authorities=[], adhoc=False, runtime=False, team=None, timestamp=False, signed_time=False, readable=True)
        self.assertEqual(signer_check.signature_problems(unsigned, self.IDENTITY), ['signed by nobody, not ' + self.IDENTITY])
        teamless = signer_check.parse_display(self.VALID.replace('Control (TEAMID00AA)', 'Control'))
        self.assertTrue(any('names no team' in p for p in signer_check.signature_problems(teamless, 'Developer ID Application: Control')))
        self.assertIn('timestamp=secure', signer_check.observation('x', valid))


class RecordTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-record-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        host = self.work / 'host'
        subprocess.run(['bash', str(ROOT / 'tests/fixtures/dispatcher/build.sh'), str(host)], check=True, capture_output=True)
        self.host = host

    def app(self, name):
        app = self.work / f'{name}.app'
        fixture_bundle.bundle(app, self.host)
        return app

    def problems(self, app):
        manifest = json.loads((app / 'Contents/Resources/Evidence/manifest.json').read_text())
        return [(code, path) for code, path, _ in prov.record_problems(app, manifest)]

    def rewrite(self, app, mutate):
        path = app / prov.RECORD_PATH
        record = json.loads(path.read_text())
        mutate(record)
        path.write_text(json.dumps(record))

    def test_records_are_bounded_redacted_and_complete(self):
        home = os.environ.get('HOME', '/Users/nobody')
        self.assertEqual(prov.redact(home + '/x/y', home), prov.HOME_MARKER + '/x/y')
        self.assertEqual(prov.redact(home, home), prov.HOME_MARKER)
        self.assertEqual(prov.redact('/opt/x', home), '/opt/x')
        self.assertEqual(prov.redact([home + '/a', '/b'], home), [prov.HOME_MARKER + '/a', '/b'])
        self.assertEqual(prov.redact('path+file://' + home + '/x/controller#0.1.0', home), 'path+file://' + prov.HOME_MARKER + '/x/controller#0.1.0')
        self.assertEqual(prov.forbidden_content('text ' + home + '/x', dict(HOME=home, PATH='/p')), 'a home-prefixed path')
        self.assertEqual(prov.forbidden_content('path=/usr/bin:/bin', dict(HOME=home, PATH='/usr/bin:/bin')), 'the PATH value')
        self.assertIsNone(prov.forbidden_content(prov.HOME_MARKER + '/x', dict(HOME=home, PATH='/p')))
        valid, other = self.app('valid'), self.app('other')
        self.assertEqual(self.problems(valid), [])
        # A record for another bundle with the same inventory but other bytes is refused by hash and load-command metadata.
        with (other / 'Contents/MacOS/pw-runner-client').open('ab') as stream:
            stream.write(b'\0other bytes')
        fixture_bundle.record(other)
        shutil.copy2(other / prov.RECORD_PATH, valid / prov.RECORD_PATH)
        self.assertTrue(any(code in ('provenance_hash', 'provenance_metadata') for code, _ in self.problems(valid)))
        fixture_bundle.record(valid)
        self.assertEqual(self.problems(valid), [])
        cases = {
            'missing entry': (lambda r: r['outputs'].pop(), 'provenance_output'),
            'duplicate entry': (lambda r: r['outputs'].append(dict(r['outputs'][1])), 'provenance_output'),
            'invalid path': (lambda r: r['outputs'][1].__setitem__('rel_path', '../escape'), 'provenance_output'),
            'absolute path': (lambda r: r['outputs'][1].__setitem__('rel_path', '/Contents/MacOS/x'), 'provenance_output'),
            'unshipped executable': (lambda r: r['outputs'].append(dict(r['outputs'][1], rel_path='Contents/MacOS/extra')), 'provenance_output'),
            'controller hash inside the seal': (lambda r: r['outputs'][0].__setitem__('sha256', 'a' * 64), 'provenance_hash'),
            'wrong hash': (lambda r: r['outputs'][1].__setitem__('sha256', 'b' * 64), 'provenance_hash'),
            'wrong uuid': (lambda r: r['outputs'][1].__setitem__('uuid', 'FFFFFFFF-0000-0000-0000-000000000000'), 'provenance_metadata'),
            'wrong sdk': (lambda r: r['outputs'][1].__setitem__('sdk', '1.0'), 'provenance_metadata'),
            'missing section': (lambda r: r.pop('toolchain'), 'provenance'),
            'other schema': (lambda r: r.__setitem__('schema_version', 3), 'provenance'),
            'an earlier build\'s schema': (lambda r: r.__setitem__('schema_version', 1), 'provenance'),
            'wrong architectures': (lambda r: r['outputs'][1].__setitem__('architectures', ['x86_64']), 'provenance_metadata'),
            'wrong container': (lambda r: r['outputs'][1].__setitem__('container', 'fat'), 'provenance_metadata'),
        }
        for name, (mutate, code) in cases.items():
            with self.subTest(case=name):
                self.rewrite(valid, mutate)
                found = self.problems(valid)
                self.assertTrue(any(c == code for c, _ in found), (name, found))
                fixture_bundle.record(valid)
        (valid / prov.RECORD_PATH).write_text('[]')
        self.assertEqual(self.problems(valid), [('provenance', prov.RECORD_PATH)])
        # A manifest that disagrees with the record about a helper hash is named too.
        fixture_bundle.record(valid)
        manifest = json.loads((valid / 'Contents/Resources/Evidence/manifest.json').read_text())
        manifest['entries'][0]['sha256'] = 'c' * 64
        self.assertTrue(any(c == 'provenance_hash' for c, _ in [(c, p) for c, p, _ in prov.record_problems(valid, manifest)]))

    def partial(self, record):
        """The partial build's record for the same stand-ins: Cargo's outputs only, no Swift compiler."""
        out = copy.deepcopy(record)
        out['configuration']['knobs']['BUILD_XPC'] = '0'
        out['toolchain']['compilers']['swift'] = dict(status='not applicable', reason='partial build: the XPC pieces were not compiled')
        out['outputs'] = [o for o in out['outputs'] if o['rel_path'] in prov.PARTIAL_OUTPUTS]
        out['signing']['nested'] = [n for n in out['signing']['nested'] if n['rel_path'] in prov.PARTIAL_OUTPUTS]
        return out

    def test_records_are_validated_by_shape_in_every_reader(self):
        valid = self.app('shape')
        self.assertEqual(self.problems(valid), [])
        record = json.loads((valid / prov.RECORD_PATH).read_text())
        # Valid neighbours: the partial build's record, and each optional observation the field policy lets stay unknown.
        self.assertEqual(prov.record_shape_problems(self.partial(record)), [])
        neighbours = {
            'xcode unknown': lambda r: r['toolchain'].__setitem__('xcode', dict(status='unknown', reason='nonzero_exit', returncode=1)),
            'meson options unknown': lambda r: r['configuration'].__setitem__('meson_options', dict(status='unknown')),
            'stamp projection unavailable': lambda r: r['configuration']['toolchain_stamp'].__setitem__('projection', dict(status='unavailable', reason='x')),
            'fingerprint ambiguous': lambda r: r['outputs'][0]['cargo'].__setitem__('fingerprint', dict(status='ambiguous', binding=None, limitation='x')),
            'wrapper without a hash': lambda r: r['toolchain']['rustc'].__setitem__('wrappers', dict(wrapper=dict(source='RUSTC_WRAPPER', command='/w'))),
            'explicitly empty SDK request': lambda r: r['configuration']['requests'].__setitem__('SDKROOT', dict(state='set', value='')),
        }
        for label, mutate in neighbours.items():
            with self.subTest(neighbour=label):
                changed = copy.deepcopy(record)
                mutate(changed)
                self.assertEqual(prov.record_shape_problems(changed), [], label)
        # Every required section and representative nested fields: missing, null and the wrong type; each is a problem.
        def drop(*keys):
            def mutate(r):
                node = r
                for key in keys[:-1]:
                    node = node[key]
                node.pop(keys[-1])
            return mutate

        def put(value, *keys):
            def mutate(r):
                node = r
                for key in keys[:-1]:
                    node = node[key]
                node[keys[-1]] = value
            return mutate
        faults = {}
        for section in ('generated_at', 'source', 'toolchain', 'configuration', 'outputs', 'signing', 'limits'):
            faults[f'{section} missing'] = drop(section)
            faults[f'{section} null'] = put(None, section)
            faults[f'{section} wrong type'] = put(7, section)
        faults.update({
            'dirty is a string': put('no', 'source', 'dirty'),
            'an input hash missing': drop('source', 'input_hashes', 'meson.build'),
            'worker identity not hex': put('z' * 64, 'source', 'worker_identity'),
            'SDK version null': put(None, 'toolchain', 'sdk', 'version'),
            'C compiler observation failed': put(dict(status='failed', kind='timeout'), 'toolchain', 'compilers', 'c', 'observed'),
            'Swift compiler missing in a full build': put(dict(status='not applicable', reason='partial build: the XPC pieces were not compiled'),
                                                          'toolchain', 'compilers', 'swift'),
            'rustc selection missing': drop('toolchain', 'rustc', 'selection'),
            'rustc source unknown': put('guess', 'toolchain', 'rustc', 'source'),
            'xcode status unknown kind': put(dict(status='maybe'), 'toolchain', 'xcode'),
            'knob is an integer': put(1, 'configuration', 'knobs', 'BUILD_XPC'),
            'deployment target null': put(None, 'configuration', 'deployment_target'),
            'deployment target disagrees with the outputs': put('1.0', 'configuration', 'deployment_target'),
            'sdkroot disagrees with the SDK': put('/other/SDK', 'configuration', 'sdkroot'),
            'request state unknown': put(dict(state='maybe'), 'configuration', 'requests', 'SDKROOT'),
            'request missing': drop('configuration', 'requests', 'CPATH'),
            'set SDK request without value': put(dict(state='set'), 'configuration', 'requests', 'SDKROOT'),
            'private request leaks its value': put(dict(state='set', value='/private/includes'), 'configuration', 'requests', 'CPATH'),
            'SDK source contradicts request': put('SDKROOT named by the caller', 'toolchain', 'sdk', 'source'),
            'empty stamp projection': put({}, 'configuration', 'toolchain_stamp', 'projection'),
            'wrong replacement type': put('garbage', 'configuration', 'build_directories', 'fresh_mode', 'replacement'),
            'absent replacement observation': put(None, 'configuration', 'build_directories', 'fresh_mode', 'replacement'),
            'fresh mode knob disagrees': put('0', 'configuration', 'knobs', 'PW_FRESH_BUILD'),
            'fresh mode reused a target': lambda r: r['outputs'][0]['cargo'].__setitem__('fresh', True),
            'Meson xpc is a string': put(dict(status='ok', values=dict(xpc='not-a-boolean')), 'configuration', 'meson_options'),
            'empty Cargo profile': lambda r: r['outputs'][0]['cargo'].__setitem__('profile', {}),
            'an output field null': lambda r: r['outputs'][1].__setitem__('uuid', None),
            'an output tools list of strings': lambda r: r['outputs'][1].__setitem__('tools', ['ld']),
            'a Cargo judgment null': lambda r: next(o for o in r['outputs'] if 'cargo' in o)['cargo'].__setitem__('fresh', None),
            'a signature timestamp string': lambda r: r['outputs'][1]['signature'].__setitem__('timestamp', 'true'),
            'signing nested disagrees': lambda r: r['signing']['nested'][0].__setitem__('timestamp', True),
            'an unknown top-level field': put('x', 'extra'),
            'a partial knob with full outputs': put('0', 'configuration', 'knobs', 'BUILD_XPC'),
            'a string beyond its bound': put('x' * (prov.LINE_LIMIT + 1), 'toolchain', 'rustc', 'identity'),
            'output target missing': drop('configuration', 'output_target'),
            'output target of another architecture': put('x86_64', 'configuration', 'output_target', 'architecture'),
            'output target of another triple': put('x86_64-apple-darwin', 'configuration', 'output_target', 'cargo_triple'),
            'Meson machines missing': drop('configuration', 'meson_machines'),
            'Meson host of another architecture': put(dict(system='darwin', cpu_family='x86_64'), 'configuration', 'meson_machines', 'host'),
            'Cargo target selection missing': drop('toolchain', 'rustc', 'selection', 'target'),
            'Cargo target of another triple': put('x86_64-apple-darwin', 'toolchain', 'rustc', 'selection', 'target', 'triple'),
            "the triple's release area missing": drop('configuration', 'build_directories', 'cargo_target_release'),
            'an output architecture missing': lambda r: r['outputs'][1].pop('architectures'),
            'an output of another architecture': lambda r: r['outputs'][1].__setitem__('architectures', ['x86_64']),
            'a universal output': lambda r: r['outputs'][1].update(architectures=['arm64', 'x86_64'], container='fat'),
            'an output of another platform': lambda r: r['outputs'][1].__setitem__('platform', '6'),
        })
        for label, mutate in faults.items():
            with self.subTest(fault=label):
                changed = copy.deepcopy(record)
                mutate(changed)
                self.assertTrue(prov.record_shape_problems(changed), label)
                (valid / prov.RECORD_PATH).write_text(json.dumps(changed))
                self.assertIn('provenance', {code for code, _ in self.problems(valid)}, label)
        # Only a linker tool's version changes: the shape holds and the load commands disagree.
        changed = copy.deepcopy(record)
        changed['outputs'][1]['tools'] = [dict(t, version=t['version'] + '.1') for t in changed['outputs'][1]['tools']] or [dict(tool='3', version='1')]
        self.assertEqual(prov.record_shape_problems(changed), [])
        (valid / prov.RECORD_PATH).write_text(json.dumps(changed))
        self.assertEqual({code for code, _ in self.problems(valid)}, {'provenance_metadata'})
        # A signature claim that differs from codesign's display of the bytes: the inspector names it.
        fixture_bundle.record(valid)
        observed = {o['rel_path']: dict(o['signature']) for o in record['outputs'] if 'signature' in o}
        manifest = json.loads((valid / 'Contents/Resources/Evidence/manifest.json').read_text())
        self.assertEqual(prov.record_problems(valid, manifest, signatures=observed), [])
        observed[record['outputs'][1]['rel_path']]['adhoc'] = False
        self.assertEqual({c for c, _, _ in prov.record_problems(valid, manifest, signatures=observed)}, {'provenance_signature'})

    def test_the_archive_reader_validates_the_record_and_binds_its_outputs(self):
        valid = self.app('archive')
        record = self.partial(json.loads((valid / prov.RECORD_PATH).read_text()))

        def archive(record, members=None, name='release.zip'):
            import zipfile
            path = self.work / name
            members = dict(members if members is not None else {rel: (valid / rel).read_bytes() for rel in prov.PARTIAL_OUTPUTS})
            with zipfile.ZipFile(path, 'w') as zipped:
                for relative, data in members.items():
                    zipped.writestr('PolicyWitness.app/' + relative, data)
                zipped.writestr('PolicyWitness.app/' + prov.RECORD_PATH, json.dumps(record))
            return path
        data, controller = prov.read_zip_record(archive(record))
        self.assertEqual(json.loads(data), record)
        self.assertEqual(controller, hashlib.sha256((valid / prov.CONTROLLER).read_bytes()).hexdigest())
        oversized = dict(record, padding='x' * prov.RECORD_LIMIT)
        with self.assertRaisesRegex(ValueError, 'beyond .* bytes'):
            prov.read_zip_record(archive(oversized, name='oversized.zip'))
        (valid / prov.RECORD_PATH).write_text(json.dumps(oversized))
        manifest = json.loads((valid / 'Contents/Resources/Evidence/manifest.json').read_text())
        self.assertIn('exceeds', prov.record_problems(valid, manifest)[0][2])
        broken = copy.deepcopy(record)
        broken['configuration']['deployment_target'] = None
        with self.assertRaises(ValueError) as refused:
            prov.read_zip_record(archive(broken, name='null.zip'))
        self.assertIn('invalid provenance record', str(refused.exception))
        for label in ('load commands', 'signature facts'):
            changed = copy.deepcopy(record)
            output = changed['outputs'][1]
            if label == 'load commands':
                output['tools'] = [dict(tool='3', version='999.0')]
            else:
                output['signature']['adhoc'] = False
            self.assertEqual(prov.record_shape_problems(changed), [])
            with self.assertRaisesRegex(ValueError, label):
                prov.read_zip_record(archive(changed, name=label + '.zip'))
        members = {rel: (valid / rel).read_bytes() for rel in prov.PARTIAL_OUTPUTS}
        members['Contents/MacOS/sbpl-check'] += b'\0other bytes'
        with self.assertRaises(ValueError) as refused:
            prov.read_zip_record(archive(record, members, 'swapped.zip'))
        self.assertIn('differs from its provenance record', str(refused.exception))
        members.pop('Contents/MacOS/sbpl-check')
        with self.assertRaises(ValueError) as refused:
            prov.read_zip_record(archive(record, members, 'missing.zip'))
        self.assertIn('lacks Contents/MacOS/sbpl-check', str(refused.exception))
        # A one-slice fat container of the same arm64 slice: its load commands and the record's hash agree, so only the
        # container read from the member's own bytes separates it from the thin file the record claims.
        fat = self.work / 'one-slice-fat'
        subprocess.run(['/usr/bin/lipo', '-create', str(valid / 'Contents/MacOS/sbpl-check'), '-output', str(fat)], check=True, capture_output=True)
        self.assertEqual(oracle(fat)['container'], 'fat')
        self.assertEqual({k: prov.output_metadata(fat)[k] for k in ('uuid', 'platform', 'minos', 'sdk', 'tools')},
                         {k: prov.output_metadata(valid / 'Contents/MacOS/sbpl-check')[k] for k in ('uuid', 'platform', 'minos', 'sdk', 'tools')})
        members = {rel: (valid / rel).read_bytes() for rel in prov.PARTIAL_OUTPUTS}
        members['Contents/MacOS/sbpl-check'] = fat.read_bytes()
        rehashed = copy.deepcopy(record)
        next(o for o in rehashed['outputs'] if o['rel_path'] == 'Contents/MacOS/sbpl-check')['sha256'] = hashlib.sha256(fat.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'architectures or container'):
            prov.read_zip_record(archive(rehashed, members, 'one-slice-fat.zip'))
        # An earlier build's record is read only on request, as its own version describes it; nothing is supplied to it.
        historical = copy.deepcopy(record)
        historical['schema_version'] = 1
        for output in historical['outputs']:
            output.pop('architectures')
            output.pop('container')
        for name in ('output_target', 'meson_machines'):
            historical['configuration'].pop(name)
        historical['configuration']['build_directories'].pop('cargo_target_release')
        historical['configuration']['build_directories']['fresh_mode']['replacement'].pop('cargo_target_release')
        historical['toolchain']['rustc']['selection'].pop('target')
        self.assertEqual(prov.record_shape_problems(historical), [], 'a version 1 record is valid as version 1')
        with self.assertRaisesRegex(ValueError, 'unsupported provenance record'):
            prov.read_zip_record(archive(historical, name='historical.zip'))
        data, _ = prov.read_zip_record(archive(historical, name='historical.zip'), historical=True)
        self.assertEqual(json.loads(data), historical, 'the historical record is returned byte for byte, never completed')
        mixed = copy.deepcopy(record)
        mixed['schema_version'] = 1
        self.assertTrue(prov.record_shape_problems(mixed), 'version 1 is closed: it carries no output target fields')
        missing = copy.deepcopy(record)
        missing['outputs'][0].pop('architectures')
        with self.assertRaisesRegex(ValueError, 'invalid provenance record'):
            prov.read_zip_record(archive(missing, name='incomplete.zip'), historical=True)

    def test_the_producer_validates_before_sealing(self):
        app = self.app('producer')
        record = json.loads((app / prov.RECORD_PATH).read_text())
        root = self.work / 'producer-root'
        for relative in prov.SOURCE_INPUTS:
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(relative)
        (root / 'builddir').mkdir()
        rustc = dict(record['toolchain']['rustc'], exact_command='/fixture/rustc')
        rustc.pop('selection_note')
        toolchain = fake_observation(rustc=rustc, compilers={'c': fake_observation()['compilers']['c'],
                                                             'swift': dict(configured=dict(command=['swiftc'], id='llvm', version='6.4', full_version=None),
                                                                           observed=dict(status='ok', command=['swiftc'], identity='swift 6.4'))})
        toolchain['sdk']['version']['line'] = record['toolchain']['sdk']['version']
        toolchain['sdk']['path']['line'] = '/fixture/SDK'
        judgment = next(o for o in record['outputs'] if 'cargo' in o)['cargo']
        session = dict(knobs=dict(BUILD_XPC='1', PW_INSPECTION='1', PW_FRESH_BUILD='0'), toolchain=toolchain,
                       worker_identity=dict(status='ok', reported='0' * 64), stamp=dict(commit='0' * 40, describe='fixture', dirty=False,
                                                                                      version='0.0.0', build_number='0'),
                       requests={name: dict(state='unset') for name in ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')},
                       environment={}, cargo=dict(judgments={name: dict(judgment) for name in prov.CARGO_TARGETS.values()},
                                                  selection=record['toolchain']['rustc']['selection'],
                                                  requested_rustflags=dict(source='none', tokens=[]), flag_environment={},
                                                  admission=dict(target_directory='/t', build_directory='/t')),
                       builddir=dict(configured_before=False, stamp_state='published'), cargo_release=dict(existed_before=False),
                       cargo_target_release=dict(existed_before=False),
                       meson_machines=dict(host=dict(system='darwin', cpu_family='aarch64'), build=dict(system='darwin', cpu_family='aarch64')))
        manifest = json.loads((app / 'Contents/Resources/Evidence/manifest.json').read_text())

        def produce(session):
            return prov.collect(session, app, root, 'fixture: linker-signed stand-ins', manifest_entries=manifest['entries'],
                                signature=lambda path: dict(fixture_bundle.LINKER_SIGNED))
        produced = produce(session)
        self.assertEqual(prov.record_shape_problems(produced), [])
        self.assertEqual({(o['container'], tuple(o['architectures'])) for o in produced['outputs']}, {('thin', ('arm64',))})
        self.assertEqual(produced['configuration']['output_target'],
                         dict(output_target.DECLARED, note=produced['configuration']['output_target']['note']))
        for label, mutate, needle in (
                ('no effective deployment target (the null the accepted app carried)', lambda s: s['cargo']['selection']['child_environment'].__setitem__('MACOSX_DEPLOYMENT_TARGET', None),
                 'no effective deployment target'),
                ('requests absent', lambda s: s.pop('requests'), 'no caller requests'),
                ('an effective deployment target the outputs do not carry', lambda s: s['cargo']['selection']['child_environment'].__setitem__('MACOSX_DEPLOYMENT_TARGET', '1.0'),
                 'fails its own validation'),
                ('an xcode observation of another shape', lambda s: s['toolchain'].__setitem__('xcode', dict(status='maybe')), 'fails its own validation'),
                ('a judgment that is not a boolean', lambda s: s['cargo']['judgments']['sbpl-check'].__setitem__('fresh', 'false'), 'fails its own validation'),
                ('no Meson machines', lambda s: s.pop('meson_machines'), 'no Meson host and build machines'),
                ('a Meson host of another architecture', lambda s: s['meson_machines'].__setitem__('host', dict(system='darwin', cpu_family='x86_64')),
                 'fails its own validation')):
            with self.subTest(producer=label):
                changed = copy.deepcopy(session)
                mutate(changed)
                with self.assertRaises(prov.Refusal) as refused:
                    produce(changed)
                self.assertIn(needle, str(refused.exception))
        # An output outside the target is refused from its bytes, whatever the session says.
        helper = app / 'Contents/MacOS/sbpl-check'
        source = self.work / 'x86_64.c'
        source.write_text('int main(void) { return 0; }\n')
        subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-arch', 'x86_64', str(source), '-o', str(helper)],
                       check=True, capture_output=True)
        for entry in manifest['entries']:
            if entry['rel_path'] == 'Contents/MacOS/sbpl-check':
                entry['sha256'] = prov.sha256_file(helper)
        with self.assertRaises(prov.Refusal) as refused:
            produce(session)
        self.assertIn('Contents/MacOS/sbpl-check: outside the output target (architecture x86_64, not exactly arm64)', str(refused.exception))

    def test_helper_subcommands_are_the_ones_the_script_invokes(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('generate_build', ROOT / 'docs/generate_build.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        model = generator.parse_script((ROOT / 'build.sh').read_text())
        invoked = {i['command'].split()[1] for i in model['invocations'] if i['command'].startswith('tests/lib/build_provenance.py')}
        self.assertEqual(invoked, set(prov.SUBCOMMANDS) - {'inspect'})
        self.assertIn('inspect', prov.SUBCOMMANDS)

    def test_opt_in_mutation_anchors_match_current_sources(self):
        # Loading and applying mutations in memory needs no build or signing.
        # Execution remains opt-in; stale anchors fail the default battery.
        import importlib.util
        spec = importlib.util.spec_from_file_location('build_refusals', ROOT / 'tests/suites/preflight/opt_in/build_refusals.py')
        controls = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controls)
        for refusal, label, mutate, *where in controls.MUTATIONS:
            with self.subTest(refusal=refusal, mutation=label):
                source = (ROOT / (where[0] if where else 'build.sh')).read_text()
                self.assertNotEqual(source, mutate(source))
        script = (ROOT / 'build.sh').read_text()
        self.assertEqual(script.count(controls.REQUIRE_REBUILT), 1)
        self.assertNotEqual(controls._without_self_checks(script), script)

    def test_unknown_wrapper_hashes_never_establish_stamp_compatibility(self):
        for missing in (None, {'wrapper': dict(command='/wrapper', sha256=None)}):
            fields = {'rustc.wrappers': missing}
            difference = prov.compare_fields(fields, fields, ['rustc.wrappers'])
            self.assertEqual(difference[-1], 'unavailable')
        fields = {'rustc.wrappers': {'wrapper': dict(command='/wrapper', sha256='a' * 64)}}
        self.assertIsNone(prov.compare_fields(fields, fields, ['rustc.wrappers']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
