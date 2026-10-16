"""Offline controls over the build's provenance helpers: parsing, state decisions and lock ownership.

These exercise tests/lib/build_provenance.py, tests/lib/checkout_lock.py and
tests/lib/signer_check.py directly, with constructed inputs and disposable
directories. Observed probes use real tools where one is needed (clang for a
Mach-O); every other expectation is independent of the helper under test.
The build-driving controls in the opt-in preflight cases establish the same
refusals through the unchanged script.
"""
import copy
from contextlib import redirect_stderr, redirect_stdout
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


class LockTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-lock-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        (self.root / 'tests').mkdir()
        self.lock = self.root / checkout_lock.LOCK

    def probe_free(self):
        fd = os.open(self.lock, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False
        finally:
            os.close(fd)

    def verify_in_child(self, fd, claim):
        script = textwrap.dedent(f'''
            import sys
            sys.path.insert(0, {str(ROOT / "tests/lib")!r})
            import checkout_lock
            try:
                print("verified", checkout_lock.verify({str(self.root)!r}))
            except checkout_lock.Refusal as exc:
                print("refused", exc)
                raise SystemExit(2)
        ''')
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
        env.update(claim)
        result = subprocess.run([PYTHON, '-c', script], pass_fds=[fd] if fd is not None else (), env=env,
                                capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout.strip()

    def test_lock_claims_are_verified_through_the_descriptor(self):
        fd, record = checkout_lock.acquire(self.root)
        try:
            claim = {checkout_lock.ENV_FD: str(fd), checkout_lock.ENV_ROOT: str(self.root), checkout_lock.ENV_NONCE: record['nonce']}
            self.assertEqual(self.verify_in_child(fd, claim)[0], 0, 'the inherited descriptor shares the hold')
            self.assertEqual(self.verify_in_child(fd, dict(claim, **{checkout_lock.ENV_ROOT: '/private/tmp'}))[0], 2, 'another checkout')
            self.assertEqual(self.verify_in_child(fd, dict(claim, **{checkout_lock.ENV_NONCE: 'f' * 32}))[0], 2, 'a stale nonce')
            self.assertEqual(self.verify_in_child(None, claim)[0], 2, 'a closed descriptor')
            other = os.open(self.root / 'tests', os.O_RDONLY)
            try:
                os.set_inheritable(other, True)
                self.assertEqual(self.verify_in_child(other, dict(claim, **{checkout_lock.ENV_FD: str(other)}))[0], 2, 'another file')
            finally:
                os.close(other)
            # A separately opened descriptor on the lock inode, with the owner record copied, is not a hold.
            separate = os.open(self.lock, os.O_RDWR)
            try:
                os.set_inheritable(separate, True)
                status, text = self.verify_in_child(separate, dict(claim, **{checkout_lock.ENV_FD: str(separate)}))
                self.assertEqual(status, 2)
                self.assertIn('does not hold the lock', text)
            finally:
                os.close(separate)
            self.assertFalse(self.probe_free(), 'refused claims left the real hold in place')
            self.assertEqual(json.loads(self.lock.read_text())['nonce'], record['nonce'], 'refused claims left the owner record')
            with self.assertRaises(checkout_lock.Refusal) as busy:
                checkout_lock.acquire(self.root)
            self.assertIn('checkout busy', str(busy.exception))
            launcher = [PYTHON, '-B', str(ROOT / 'tests/lib/checkout_lock.py'), '--root', str(self.root), '--']
            env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
            result = subprocess.run([*launcher, '/usr/bin/true'], env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2)
            self.assertIn('checkout busy', result.stderr)
        finally:
            os.close(fd)
        self.assertTrue(self.probe_free())
        # The launcher's command verifies its own claim, and a nested launcher shares it without deadlock.
        nested = (f'{PYTHON} -B {ROOT / "tests/lib/checkout_lock.py"} --verify --root {self.root} && '
                  f'{PYTHON} -B {ROOT / "tests/lib/checkout_lock.py"} --root {self.root} -- /bin/sh -c "echo nested $PW_CHECKOUT_LOCK_FD"')
        result = subprocess.run([*launcher, '/bin/sh', '-c', nested], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('ok: inherited descriptor', result.stdout)
        self.assertIn('nested', result.stdout)
        self.assertTrue(self.probe_free())
        # The hold outlives a killed launcher command while a descendant that inherited the descriptor runs.
        holder = subprocess.Popen([*launcher, '/bin/sh', '-c', 'sleep 3 & wait'], env=env, start_new_session=True)
        deadline = time.monotonic() + 10
        while self.probe_free() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(self.probe_free(), 'the launched command did not take the lock')
        time.sleep(0.3)
        holder.kill()
        holder.wait(timeout=5)
        self.assertFalse(self.probe_free(), 'killing the shell released a hold its child still carries')
        deadline = time.monotonic() + 10
        while not self.probe_free() and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertTrue(self.probe_free(), 'the hold did not end when the last descendant exited')


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
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
        status, _, err = run_main(['session-start', '--session', str(self.session), '--root', str(self.root), '--knob', 'BUILD_XPC=0',
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
        return run_main(['stamp-check', '--session', str(self.session), '--builddir', str(self.builddir), '--root', str(self.root), '--xpc', xpc], self.env)

    def publish(self):
        return run_main(['stamp-publish', '--session', str(self.session), '--builddir', str(self.builddir), '--root', str(self.root)], self.env)

    def extend(self, xpc):
        return run_main(['stamp-extend', '--session', str(self.session), '--builddir', str(self.builddir), '--root', str(self.root), '--xpc', xpc], self.env)

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
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
        self.assertEqual(run_main(['session-start', '--session', str(self.session), '--root', str(self.root), '--describe', 'x', '--commit', 'x',
                                   '--version', '0', '--build-number', '0'], self.env)[0], 0)

    def remove(self):
        return run_main(['fresh-remove', '--session', str(self.session), '--root', str(self.root)], self.env)

    def intact(self):
        for path, text in self.sentinels.items():
            self.assertEqual(path.read_text(), text, f'{path} was touched')

    def test_fresh_removal_admits_only_owned_real_directories(self):
        (self.root / 'builddir/meson-info/keep').write_text('cache')
        (self.root / 'controller/target/release/deps/keep').write_text('cache')
        status, out, err = self.remove()
        self.assertEqual(status, 0, err)
        self.assertFalse((self.root / 'builddir').exists())
        self.assertFalse((self.root / 'controller/target/release').exists())
        self.intact()
        session = json.loads(self.session.read_text())
        self.assertEqual({k: v['removed'] for k, v in session['fresh']['replacement'].items()}, {'builddir': True, 'cargo_release': True})
        status, _, _ = self.remove()
        self.assertEqual(status, 0, 'absent directories are not an error')
        self.assertEqual({k: v['existed'] for k, v in json.loads(self.session.read_text())['fresh']['replacement'].items()},
                         {'builddir': False, 'cargo_release': False})
        # A symlinked parent redirecting outside the checkout refuses before anything is removed.
        (self.root / 'builddir').mkdir()
        (self.root / 'builddir/keep').write_text('rebuilt')
        shutil.rmtree(self.root / 'controller/target/debug')
        (self.work / 'elsewhere/release').mkdir(parents=True)
        (self.work / 'elsewhere/release/keep').write_text('external')
        shutil.rmtree(self.root / 'controller/target')
        (self.root / 'controller/target').symlink_to(self.work / 'elsewhere')
        session_elsewhere = self.work / 'elsewhere/pw-build-session.json'
        self.assertEqual(run_main(['session-start', '--session', str(session_elsewhere), '--root', str(self.root), '--describe', 'x',
                                   '--commit', 'x', '--version', '0', '--build-number', '0'], self.env)[0], 0)
        status, _, err = run_main(['fresh-remove', '--session', str(session_elsewhere), '--root', str(self.root)], self.env)
        self.assertEqual(status, 2)
        self.assertIn('is a symlink', err)
        self.assertEqual((self.work / 'elsewhere/release/keep').read_text(), 'external')
        self.assertEqual((self.root / 'builddir/keep').read_text(), 'rebuilt', 'a refused admission removes nothing, not even the admitted sibling')
        (self.root / 'controller/target').unlink()
        (self.root / 'controller/target').mkdir()
        (self.root / 'controller/target/release').symlink_to(self.work / 'elsewhere/release')
        status, _, err = run_main(['fresh-remove', '--session', str(session_elsewhere), '--root', str(self.root)], self.env)
        self.assertEqual(status, 2)
        self.assertEqual((self.work / 'elsewhere/release/keep').read_text(), 'external')
        (self.root / 'controller/target/release').unlink()
        (self.root / 'controller/target/release').write_text('a file, not a directory')
        status, _, err = run_main(['fresh-remove', '--session', str(session_elsewhere), '--root', str(self.root)], self.env)
        self.assertEqual(status, 2)
        self.assertIn('not a directory', err)
        (self.root / 'controller/target/release').unlink()
        # A removal that fails stops the build with the path; the session records the failure.
        (self.root / 'controller/target/release').mkdir()
        self.session.write_text(session_elsewhere.read_text())
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


class CargoJudgmentTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-cargo-', dir='/private/tmp')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.target = self.root / 'controller/target'
        self.release = self.target / 'release'
        (self.release / 'deps').mkdir(parents=True)
        self.session = self.target / 'pw-build-session.json'
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
        self.assertEqual(run_main(['session-start', '--session', str(self.session), '--root', str(self.root), '--describe', 'x', '--commit', 'x',
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
        argv = ['cargo-judge', '--session', str(self.session), '--messages', str(path), '--target-dir', str(self.target),
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
        status, _, err, _ = self.judge([]) if False else run_main(['cargo-judge', '--session', str(self.session), '--messages',
            str(self.target / 'pw-build-messages.jsonl'), '--target-dir', str(self.target), '--bin', 'policy-witness',
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
        session = work / 'session.json'
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
        self.assertEqual(run_main(['session-start', '--session', str(session), '--root', str(work), '--describe', 'x', '--commit', 'x',
                                   '--version', '0', '--build-number', '0'], env)[0], 0)
        metadata = prov.output_metadata(binary)
        self.assertEqual(metadata['status'], 'ok')
        self.assertEqual(prov.normalize_version(metadata['sdk']), prov.normalize_version(sdk))
        equivalent = sdk + '.0' if '.' in sdk else sdk + '.0'
        self.assertEqual(run_main(['sdk-check', '--session', str(session), '--sdk-version', equivalent, str(binary)], env)[0], 0)
        status, _, err = run_main(['sdk-check', '--session', str(session), '--sdk-version', '1.2', str(binary)], env)
        self.assertEqual(status, 1)
        self.assertIn('built against SDK', err)
        status, _, err = run_main(['sdk-check', '--session', str(session), '--sdk-version', 'n/a', str(binary)], env)
        self.assertEqual(status, 1)
        self.assertIn('not a numeric version', err)
        status, _, err = run_main(['sdk-check', '--session', str(session), '--sdk-version', sdk, str(source)], env)
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
