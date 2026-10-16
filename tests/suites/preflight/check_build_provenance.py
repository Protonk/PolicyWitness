"""Offline controls over the build's provenance helpers: parsing, state decisions and lock ownership.

These exercise tests/lib/build_provenance.py, tests/lib/checkout_lock.py and
tests/lib/signer_check.py directly, with constructed inputs and disposable
directories. Observed probes use real tools where one is needed (clang for a
Mach-O); every other expectation is independent of the helper under test.
The build-driving controls in the opt-in preflight cases establish the same
refusals through the unchanged script.
"""
import copy
from contextlib import contextmanager, ExitStack, redirect_stderr, redirect_stdout
import fcntl
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
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
import checkout_lock
import signer_check
import fixture_bundle

PYTHON = '/usr/bin/python3'


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


UNSET_REQUESTS = checkout_lock.Requests({name: None for name in checkout_lock.REQUEST_NAMES})
LIB = str(ROOT / 'tests/lib')
CLAIM = dict(fd=checkout_lock.ENV_FD, root=checkout_lock.ENV_ROOT, nonce=checkout_lock.ENV_NONCE, channel=checkout_lock.ENV_CHANNEL)


def clean_env():
    """This process's environment without the claim the dispatcher passed for the real checkout."""
    return {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}


def own(test, root, requests=UNSET_REQUESTS):
    """An in-process owner of a disposable checkout's lock for the test's duration: its scope and a claimed environment."""
    stack = ExitStack()
    test.addCleanup(stack.close)
    scope = stack.enter_context(checkout_lock.owned(root, requests=requests, env=clean_env()))
    return scope, scope.child_env(clean_env())


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
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
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
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-lock-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        self.root = self.work / 'checkout'
        (self.root / 'tests').mkdir(parents=True)
        self.lock = self.root / checkout_lock.LOCK
        self.launcher = [PYTHON, '-B', str(ROOT / 'tests/lib/checkout_lock.py'), '--root', str(self.root), '--']
        self.front_end = ['/bin/bash', str(ROOT / 'tests/lib/checkout_lock.sh'), '--root', str(self.root), '--']

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
        with checkout_lock.owned(self.root, requests=UNSET_REQUESTS, env=clean_env()) as scope:
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
                    'another worktree asked of this owner': (dict(claim, **{CLAIM['root']: str(other)}), scope.pass_fds(), other, 'another checkout'),
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

    def test_requests_are_captured_before_python_and_handed_to_nested_owners(self):
        caller = {k: v for k, v in clean_env().items() if k not in checkout_lock.REQUEST_NAMES}
        caller.update(CPATH='', LIBRARY_PATH='spaced dir/lib\n', MANPATH='/caller/man')  # SDKROOT and LC_CTYPE unset
        expected = {name: caller.get(name) for name in checkout_lock.REQUEST_NAMES}
        report = (f'for n in SDKROOT CPATH LIBRARY_PATH MANPATH LC_CTYPE; do '
                  f'if [[ -n "${{!n+set}}" ]]; then printf "%s set %s\\n" "$n" "$(printf %s "${{!n}}" | xxd -p | tr -d "\\n")"; '
                  f'else printf "%s unset\\n" "$n"; fi; done; '
                  f'{PYTHON} -B {LIB}/checkout_lock.py --verify --root {self.root} --build-requests; '
                  f'CPATH=/inner/include /bin/bash {LIB}/checkout_lock.sh --root {self.root} -- '
                  f'{PYTHON} -B {LIB}/checkout_lock.py --verify --root {self.root} --build-requests')
        result = subprocess.run([*self.front_end, '/bin/bash', '-c', report], env=caller, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = result.stdout.splitlines()
        seen = {}
        for line in lines[:5]:
            name, state, *value = line.split(' ')
            seen[name] = bytes.fromhex(value[0]).decode() if state == 'set' else None
        self.assertEqual(seen, expected, 'the command did not see the caller\'s values restored')
        handed = [line.split(' ') for line in lines[5:10]]
        decoded = {words[1]: (bytes.fromhex(words[3]).decode() if words[2] == 'set' else None) for words in handed}
        self.assertEqual(decoded, expected, 'the owner did not hand over the requests the front end recorded')
        self.assertEqual(lines[10:15], lines[5:10], 'a nested launcher must hand over its owner\'s requests, not its own environment')
        # Without the front end the owner holds no requests and a build is refused; ownership alone needs none.
        bare = subprocess.run([*self.launcher, PYTHON, '-B', f'{LIB}/checkout_lock.py', '--verify', '--root', str(self.root), '--build-requests'],
                              env=caller, capture_output=True, text=True, timeout=30)
        self.assertEqual(bare.returncode, 2)
        self.assertIn('holds no preserved build requests', bare.stderr)
        plain = subprocess.run([*self.launcher, PYTHON, '-B', f'{LIB}/checkout_lock.py', '--verify', '--root', str(self.root)],
                               env=caller, capture_output=True, text=True, timeout=30)
        self.assertEqual(plain.returncode, 0, plain.stderr)
        # Malformed or incomplete request options refuse before the lock is taken.
        for options in (['--request', 'BOGUS=1'], ['--request', 'SDKROOT=/x', '--request', 'SDKROOT=/y'], ['--request', 'SDKROOT=/x']):
            with self.subTest(options=options):
                refused = subprocess.run([PYTHON, '-B', f'{LIB}/checkout_lock.py', '--root', str(self.root), *options, '--', '/usr/bin/true'],
                                         env=caller, capture_output=True, text=True, timeout=30)
                self.assertEqual(refused.returncode, 2)
                self.assertIn('request', refused.stderr)
        self.assertTrue(lock_free(self.root))
        # A Python caller of the owned scope supplies its snapshot explicitly; a nested scope cannot supply its own.
        snapshot = checkout_lock.Requests(dict(expected))
        with checkout_lock.owned(self.root, requests=snapshot, env=clean_env()) as scope:
            self.assertEqual(scope.child_env({'SDKROOT': '/shim'}).get('SDKROOT'), None)
            with self.assertRaises(checkout_lock.Refusal):
                with checkout_lock.owned(self.root, requests=snapshot, env=scope.child_env(clean_env())):
                    pass


class ProbeTests(unittest.TestCase):
    def test_probes_are_bounded_and_failures_carry_no_output(self):
        canary = 'CANARY_' + os.urandom(6).hex()
        directory = tempfile.TemporaryDirectory(prefix='pw-probe-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        planted = Path(directory.name) / 'canary'
        planted.write_text(canary + '\n')
        failed = prov.probe(['/bin/sh', '-c', f'cat {planted} >&2; cat {planted}; exit 3'])
        self.assertEqual((failed['status'], failed['kind'], failed['returncode']), ('failed', 'nonzero_exit', 3))
        self.assertNotIn(canary, json.dumps(failed))
        empty = prov.probe(['/bin/sh', '-c', 'printf "  \\n"'])
        self.assertEqual(empty['kind'], 'empty_output')
        overflow = prov.probe(['/bin/sh', '-c', 'yes | head -c 70000'], limit=65536)
        self.assertEqual(overflow['kind'], 'output_overflow')
        started = time.monotonic()
        hung = prov.probe(['/bin/sh', '-c', 'sleep 30'], timeout=1)
        self.assertEqual(hung['kind'], 'timeout')
        self.assertLess(time.monotonic() - started, 5)
        missing = prov.probe(['/nonexistent/tool-' + os.urandom(4).hex()])
        self.assertEqual(missing['kind'], 'launch_failed')
        good = prov.probe(['/bin/sh', '-c', 'echo tool 1.2.3; echo more'])
        self.assertEqual((good['status'], good['line']), ('ok', 'tool 1.2.3'))
        self.assertEqual(prov.version_line(prov.probe(['/bin/sh', '-c', 'echo nodigits']))['kind'], 'malformed_output')
        self.assertLessEqual(len(prov.bounded_line('x' * 1000)), prov.LINE_LIMIT)
        with self.assertRaises(prov.Refusal) as required:
            prov.required(failed, 'compilers.c.identity')
        self.assertEqual(required.exception.status, 2)
        self.assertIn('nonzero_exit', str(required.exception))


class StampTests(unittest.TestCase):
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
        self.assertEqual({k: v for k, v in extended['fields'].items() if not k.startswith('compilers.swift.')}, record['fields'])
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


class FreshRemovalTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-fresh-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name).resolve()
        self.root = self.work / 'checkout'
        self.root.mkdir()
        (self.root / 'controller/target/release/deps').mkdir(parents=True)
        (self.root / 'controller/target/debug').mkdir()
        (self.root / 'builddir/meson-info').mkdir(parents=True)
        (self.root / 'builddir-clt').mkdir()
        self.sentinels = {self.root / 'controller/target/debug/keep': 'debug', self.root / 'controller/target/CACHEDIR.TAG': 'tag',
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
        status, out, err = self.remove()
        self.assertEqual(status, 0, err)
        self.assertFalse((self.root / 'builddir').exists())
        self.assertFalse((self.root / 'controller/target/release').exists())
        self.intact()  # a symlink inside a removed directory is unlinked, never followed
        session = json.loads(self.session.read_text())
        self.assertEqual({k: v['removed'] for k, v in session['fresh']['replacement'].items()}, {'builddir': True, 'cargo_release': True})
        status, _, _ = self.remove()
        self.assertEqual(status, 0, 'absent directories are not an error')
        self.assertEqual({k: v['existed'] for k, v in json.loads(self.session.read_text())['fresh']['replacement'].items()},
                         {'builddir': False, 'cargo_release': False})
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
        self.session = self.root / 'controller/target/pw-build-session.json'

    def outside_inventory(self):
        return {str(p.relative_to(self.outside)): (p.is_symlink(), p.read_bytes() if p.is_file() and not p.is_symlink() else None)
                for p in sorted(self.outside.rglob('*'))}

    def start(self, env):
        return run_main(['session-start', '--root', str(self.root), '--describe', 'x', '--commit', 'x', '--version', '0',
                         '--build-number', '0'], env)

    def test_helpers_refuse_without_ownership(self):
        bare = clean_env()
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
        self.release = self.target / 'release'
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
                    profile=dict(opt_level='3', debuginfo=0), features=[], filenames=[str(executable)], executable=str(executable), fresh=fresh)

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
        self.assertEqual(bound['rustflags_source']['kind'], 'RUSTFLAGS (script default)')
        self.assertEqual(bound['fingerprint']['binding']['metadata_hash'], 'a' * 16)
        self.assertEqual(judgments['sandbox-log-observer']['fingerprint']['binding']['how'], 'identical bytes')
        self.assertTrue(judgments['sandbox-log-observer']['fresh'])
        self.assertEqual(judgments['sbpl-check']['fingerprint']['status'], 'unavailable')
        self.assertNotIn(str(self.root), json.dumps(judgments).replace(prov.redact(str(self.root)), ''), 'exact paths are kept apart from published ones')
        # Fresh mode refuses a reused target and a missing judgment, naming them.
        status, _, err, _ = self.judge(messages, require='1')
        self.assertEqual(status, 1)
        self.assertIn('sandbox-log-observer (reused)', err)
        status, _, err, _ = self.judge(messages[:2], require='1')
        self.assertEqual(status, 1)
        self.assertIn('sbpl-check (no judgment)', err)
        # Ambiguous, malformed and unsupported fingerprints are explicit limitations, never guesses.
        (self.release / 'deps' / ('sandbox_log_observer-' + 'e' * 16)).write_bytes(b'observer bytes')
        malformed = self.unit('policy-witness', 'f' * 16, b'controller bytes 2', fingerprint='malformed')
        unsupported = self.unit('sbpl-check', '0' * 16, b'check bytes 2', fingerprint='unsupported')
        status, _, err, judgments = self.judge([malformed, messages[1], unsupported])
        self.assertEqual(status, 0, err)
        self.assertEqual(judgments['sandbox-log-observer']['fingerprint']['status'], 'ambiguous')
        self.assertEqual(judgments['policy-witness']['fingerprint']['status'], 'malformed')
        self.assertEqual(judgments['sbpl-check']['fingerprint']['status'], 'unsupported')
        self.assertIsNone(judgments['sbpl-check']['effective_rustflags'])
        self.assertEqual(judgments['sbpl-check']['rustflags_source']['kind'], 'unknown')
        self.assertEqual(prov.flag_source(['-C', 'x'], {'CARGO_ENCODED_RUSTFLAGS': '-C\x1fx'}, 'RUSTFLAGS')['kind'], 'CARGO_ENCODED_RUSTFLAGS')
        self.assertEqual(prov.flag_source(['-C', 'y'], {'RUSTFLAGS': '-C x'}, 'RUSTFLAGS')['kind'], 'cargo configuration or target rules')
        (self.target / 'pw-build-messages.jsonl').write_text('{not json\n')
        status, _, err, _ = self.judge([]) if False else run_main(['cargo-judge', '--root', str(self.root), '--bin', 'policy-witness',
            '--require-rebuilt', '0', '--rustflags-source', 'none'], self.env)[:3] + (None,)
        self.assertEqual(status, 2)
        self.assertIn('malformed', err)


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
            'other schema': (lambda r: r.__setitem__('schema_version', 2), 'provenance'),
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

    def test_helper_subcommands_are_the_ones_the_script_invokes(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('generate_build', ROOT / 'docs/generate_build.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        model = generator.parse_script((ROOT / 'build.sh').read_text())
        invoked = {i['command'].split()[1] for i in model['invocations'] if i['command'].startswith('tests/lib/build_provenance.py')}
        self.assertEqual(invoked, set(prov.SUBCOMMANDS) - {'inspect'})
        self.assertIn('inspect', prov.SUBCOMMANDS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
