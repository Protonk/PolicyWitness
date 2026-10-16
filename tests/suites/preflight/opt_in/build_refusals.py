"""Drive the unchanged build script through every refusal the manifest lists, with real toolchains and signatures.

One disposable checkout of the working tree serves every control. A control
arranges one fault beside the boundary the refusal guards: an environment the
script cannot build in, a held checkout lock, a stamp that is missing,
malformed or describes another toolchain, a redirected Cargo directory, a
cache path fresh mode cannot admit, a source that does not compile, or a file
a tool wrapper removes, moves, truncates, rewrites or replaces right before or
after one named cargo, meson, codesign or cp call. The wrapper runs the real
tool and records a receipt; forwarding compiler wrappers run the real
compilers and record every invocation; the script's own check makes the
refusal. Each control asserts the diagnostic and status, the banners that
must and must not follow, the tool calls that must not have happened and the
output left behind, so the refusal is placed before the operation it
protects. The state sequence the fresh knob defines (fresh build, unchanged
reuse, a permitted option change, refused incompatible reuse, explicit fresh
recovery) runs through the same script, with the stamp, the session, the
record and the caches observed independently of the provenance builder.
Mutated copies of the script with a guard removed or moved past that
operation must fail their control.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import shlex
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
import build_provenance as prov
WRAPPER = ROOT / 'tests/fixtures/build_refusals/tools.py'
FORWARD = ROOT / 'tests/fixtures/build_refusals/forward.py'
WRONG_WORKER = ROOT / 'tests/fixtures/build_refusals/wrong_worker.c'
WRAPPED = ('cargo', 'meson', 'ninja', 'codesign', 'cp')
VARIANTS = {'full': '1', 'partial': '0'}
IDENTITY_INPUT = 'runner/Package.swift'   # a digest input Meson never compiles
VALIDATOR_SOURCE = 'controller/tools/sb_api_validator/sb_api_validator.c'   # compiled, but not a digest input
RUST_BIN_SOURCE = 'controller/src/bin/sbpl-check.rs'
TREE_INPUTS = ('Info.plist', 'PolicyWitness.entitlements', 'runner/augments', 'runner/Services/PWRunner',
               'runner/Services/PWRunner/Info.plist', 'runner/Services/PWRunner/Entitlements.plist')
CARGO_BINS = ('policy-witness', 'sandbox-log-observer', 'sbpl-check')
STAMP = 'builddir/pw-toolchain.json'
SESSION = 'controller/target/pw-build-session.json'
RECORD = prov.RECORD_PATH


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def command(out, argv, *, cwd, env, timeout=900, pass_fds=()):
    """Keep raw output and a receipt, and reap the build's process group on timeout."""
    out.mkdir(parents=True, exist_ok=True)
    receipt = dict(argv=list(map(str, argv)), returncode=None, timed_out=False)
    started = time.monotonic()
    try:
        with (out / 'stdout').open('wb') as stdout, (out / 'stderr').open('wb') as stderr:
            process = subprocess.Popen(receipt['argv'], cwd=cwd, env=env, stdout=stdout,
                                       stderr=stderr, start_new_session=True, pass_fds=pass_fds)
            try:
                receipt['returncode'] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                receipt['timed_out'] = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
    finally:
        receipt['elapsed_seconds'] = time.monotonic() - started
        save(out / 'command.json', receipt)
    return receipt['returncode'], (out / 'stdout').read_text(errors='replace'), (out / 'stderr').read_text(errors='replace')


def lock_free(root):
    """Whether tests/.checkout.lock in a checkout can be taken now, observed with a separate open."""
    path = root / 'tests/.checkout.lock'
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


# ---- hooks for the tool wrapper ----------------------------------------------

def hook(label, tool, actions=(), *, when='after', respond=None, **match):
    entry = dict(label=label, tool=tool, when=when, match=match, actions=list(actions))
    if respond is not None:
        entry['respond'] = respond
    return entry


def delete(path):
    return dict(op='delete', path=str(path))


def move(path, to):
    return dict(op='move', path=str(path), to=str(to))


def copy(source, path):
    return {'op': 'copy', 'from': str(source), 'path': str(path)}


def append(path, text):
    return dict(op='append', path=str(path), text=text)


def write(path, text):
    return dict(op='write', path=str(path), text=text)


def truncate(path, keep):
    return dict(op='truncate', path=str(path), keep=keep)


def judge(path, target, **change):
    return dict(op='judge', path=str(path), target=target, **change)


def kill_parent():
    return dict(op='kill_parent')


class Build:
    def __init__(self, name, status, stdout, stderr, receipts, dist, before, root, forward_receipts=()):
        self.name, self.status, self.stdout, self.stderr = name, status, stdout, stderr
        self.receipts, self.dist, self.before = receipts, dist, before
        self.after = inventory(dist)
        self.app = dist / 'PolicyWitness.app'
        self.root = root
        self.forward = list(forward_receipts)
        self.session = self.load(root / SESSION)
        self.record = self.load(self.app / RECORD)
        self.stamp = (root / STAMP).read_bytes() if (root / STAMP).is_file() else None

    @staticmethod
    def load(path):
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    @property
    def output(self):
        return self.stdout + self.stderr

    def fired(self, label):
        return sum(label in r['fired'] for r in self.receipts)

    def calls(self, tool, first=None):
        """Receipts of a tool's working calls; the version probes the stamp checks make are not among them."""
        return [r for r in self.receipts if r['tool'] == tool and r['args'] != ['--version']
                and (first is None or (r['args'] and r['args'][0] == first))]

    def probes(self, tool):
        return [r for r in self.receipts if r['tool'] == tool and r['args'] == ['--version']]

    def signed(self):
        """The targets of codesign --force calls, in order."""
        return [r['args'][-1] for r in self.receipts if r['tool'] == 'codesign' and '--force' in r['args']]

    def judgments(self):
        return ((self.session or {}).get('cargo') or {}).get('judgments') or {}


class Checkout:
    """A disposable copy of the working tree with wrapped tools and no imported caches."""

    def __init__(self, work, identity, out):
        self.work, self.identity, self.out = work, identity, out
        self.root = work / 'checkout'
        self.root.mkdir()
        names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        for name in set(names.decode().split('\0')) - {''}:
            source, target = ROOT / name, self.root / name
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        self.script = (self.root / 'build.sh').read_bytes()
        self.tools = {name: shutil.which(name) for name in WRAPPED}
        assert all(self.tools.values()), self.tools
        self.bin = self.wrappers(work / 'bin', WRAPPED)
        self.bin_without_meson = self.wrappers(work / 'bin-without-meson', ('cargo', 'codesign', 'cp'))
        self.base_env = {k: v for k, v in os.environ.items()
                         if k not in ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD', 'DIST_DIR', 'CARGO_TARGET_DIR', 'CARGO_BUILD_TARGET',
                                      'CARGO_BUILD_BUILD_DIR', 'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_RUSTFLAGS', 'RUSTC',
                                      'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CC', 'BASH_ENV', 'ENV', 'PW_VERSION', 'PW_BUILD_NUMBER',
                                      'DEVELOPER_DIR', 'SDKROOT', 'PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_ROOT', 'PW_CHECKOUT_LOCK_NONCE')}
        # Canaries: an unrelated environment value and every wrapped tool's stderr; no record may carry them.
        self.canary = 'PW_CANARY_' + os.urandom(8).hex()
        self.base_env['PW_UNRELATED_CANARY'] = self.canary
        self.builddir = self.root / 'builddir'
        self.target = self.root / 'controller/target/release'
        self.minimum = plistlib.loads((self.root / 'Info.plist').read_bytes())['LSMinimumSystemVersion']
        self.ninja_minimum = re.search(r'^NINJA_MINIMUM="([^"]+)"$', self.script.decode(), re.M).group(1)
        self.host_triple = re.search(r'^host: (\S+)$', subprocess.check_output(['rustc', '-vV'], text=True), re.M).group(1)
        self.augment = sorted(p.name for p in (ROOT / 'runner/augments').glob('*.sb'))[0]
        self.aside = work / 'aside'
        self.aside.mkdir()
        self.config = work / 'config.json'
        self.forward_config = work / 'forward.json'
        self.forward_dir = work / 'forward'
        self.forward_dir.mkdir()
        self.prefix = ''
        self.records = []
        self.wrong_worker = None

    @staticmethod
    def wrappers(directory, names):
        directory.mkdir()
        for name in names:
            target = directory / name
            shutil.copy2(WRAPPER, target)
            target.chmod(0o755)
        return directory

    def forwarding(self, name, real, **config):
        """A forwarding compiler wrapper on its own path, configured by name."""
        path = self.forward_dir / name
        if not path.exists():
            shutil.copy2(FORWARD, path)
            path.chmod(0o755)
        table = json.loads(self.forward_config.read_text()) if self.forward_config.exists() else {}
        table[name] = dict(real=real, receipt=str(self.forward_dir / (name + '.receipts.jsonl')), **config)
        save(self.forward_config, table)
        return path

    def forward_receipts(self, name):
        path = self.forward_dir / (name + '.receipts.jsonl')
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def path(self, bin_dir, homebrew=True):
        system = '/usr/bin:/bin:/usr/sbin:/sbin'
        if homebrew:
            return f"{bin_dir}{os.pathsep}{self.base_env['PATH']}"
        # Only the wrappers, Cargo's directory and the system: no meson or ninja anywhere.
        return os.pathsep.join([str(bin_dir), str(Path(self.tools['cargo']).parent), system])

    def dist(self, variant, name):
        return self.work / f'dist-{self.prefix}{variant}-{name}'

    def app(self, variant, name):
        """Where this build's app bundle will be: the paths the hooks must name."""
        return self.dist(variant, name) / 'PolicyWitness.app'

    def build(self, name, variant, *, hooks=(), env=None, bin_dir=None, homebrew=True, previous=True, fresh='0',
              pass_fds=(), claim=None, stderr_canary=True, holder_alive=False):
        case = self.out / f'{self.prefix}{variant}-{name}'
        case.mkdir(parents=True)
        dist = self.dist(variant, name)
        dist.mkdir()
        if previous:
            # Earlier distribution output: a refusal before assembly must leave it,
            # and one after assembly removes the app, ZIP and guide together.
            app = dist / 'PolicyWitness.app'
            app.mkdir()
            (app / 'previous-build').write_text('previous app\n')
            (dist / 'PolicyWitness.zip').write_bytes(b'previous zip\n')
            (dist / 'PolicyWitness.md').write_text('previous guide\n')
        before = inventory(dist)
        receipt = case / 'tools.jsonl'
        config = dict(tools=self.tools, receipt=str(receipt), hooks=list(hooks), stderr_canary=self.canary if stderr_canary else '')
        save(self.config, config)
        save(case / 'fixture.json', dict(config, variant=variant, env=env or {}, fresh=fresh))
        environment = dict(self.base_env, PATH=self.path(bin_dir or self.bin, homebrew),
                           PW_BUILD_REFUSAL_CONFIG=str(self.config), PW_FORWARD_CONFIG=str(self.forward_config),
                           IDENTITY=self.identity, BUILD_XPC=VARIANTS[variant], PW_INSPECTION='1', PW_FRESH_BUILD=fresh,
                           DIST_DIR=str(dist), PW_VERSION='0.0.0', PW_BUILD_NUMBER='0', CARGO_NET_OFFLINE='true')
        environment.update(env or {})  # a control's settings win over these defaults
        if claim:
            environment.update(claim)
        forward_before = {name: len(self.forward_receipts(name)) for name in os.listdir(self.forward_dir) if not name.endswith('.jsonl')}
        status, stdout, stderr = command(case / 'build', ['bash', self.root / 'build.sh'], cwd=self.root, env=environment, pass_fds=pass_fds)
        receipts = [json.loads(line) for line in receipt.read_text().splitlines()] if receipt.exists() else []
        forwarded = [dict(r, wrapper=name) for name, count in forward_before.items() for r in self.forward_receipts(name)[count:]]
        build = Build(name, status, stdout, stderr, receipts, dist, before, self.root, forwarded)
        self.last = build
        save(case / 'result.json', dict(status=status, fired=[f for r in receipts for f in r['fired']],
                                        signed=build.signed(), tools=[r['tool'] for r in receipts],
                                        before=before, after=build.after, lock_free=lock_free(self.root),
                                        forwarded=forwarded, stamp=build.stamp.decode() if build.stamp else None))
        for path in (self.root / SESSION, self.root / STAMP):
            if path.is_file():
                shutil.copy2(path, case / path.name)
        if build.record is not None:
            shutil.copy2(build.app / RECORD, case / 'provenance.json')
        assert (self.root / 'build.sh').read_bytes() == self.script, 'a control changed the build script'
        if not holder_alive:
            assert lock_free(self.root), 'the build left the checkout lock held after it finished'
        for text in (json.dumps(build.session or {}), json.dumps(build.record or {}), (build.stamp or b'').decode()):
            assert self.canary not in text, 'a canary reached an embedded or local record'
            assert self.base_env['PATH'] not in text, 'PATH reached a record'
            assert (os.environ.get('HOME', '/nonexistent') + '/') not in text, 'a home-prefixed path reached a record'
        return build

    # ---- source mutations a control owns and restores ----

    def keep_aside(self, relative):
        """Move a checkout path out of the tree; the caller restores it."""
        source, parked = self.root / relative, self.aside / relative.replace('/', '__')
        shutil.move(str(source), str(parked))
        return parked

    def restore_aside(self, relative):
        """Put a parked path back; nothing to do when the hook that parks it never fired."""
        source, parked = self.root / relative, self.aside / relative.replace('/', '__')
        if not parked.exists():
            assert source.exists(), relative
            return
        if source.exists():
            shutil.rmtree(source) if source.is_dir() else source.unlink()
        shutil.move(str(parked), str(source))

    def restore_file(self, relative):
        shutil.copy2(ROOT / relative, self.root / relative)

    def parked(self, relative):
        return self.aside / relative.replace('/', '__')

    def meson(self, *args):
        return subprocess.run([self.tools['meson'], *args], capture_output=True, text=True, timeout=300)

    def compile_wrong_worker(self):
        """A worker stand-in that reports a foreign identity and passes every other output check."""
        if self.wrong_worker is None:
            self.wrong_worker = self.work / 'wrong-worker'
            subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', f'-mmacosx-version-min={self.minimum}', str(WRONG_WORKER),
                            '-o', str(self.wrong_worker)], check=True, capture_output=True, timeout=120)
            assert 'abi_identity=' + '0' * 64 in subprocess.check_output([str(self.wrong_worker), '--version'], text=True)
        return self.wrong_worker


# ---- assertions ---------------------------------------------------------------

def check(build, status, message, *, present=(), absent=(), where='stderr'):
    text = {'stderr': build.stderr, 'stdout': build.stdout, 'output': build.output}[where]
    assert build.status == status, (build.name, build.status, build.stderr[-4000:])
    assert message in text, (build.name, message, text[-4000:])
    for banner in present:
        assert banner in build.stdout, (build.name, 'missing banner', banner, build.stdout[-2000:])
    for banner in absent:
        assert banner not in build.stdout, (build.name, 'unexpected banner', banner)


def preserved(build):
    assert build.after == build.before, (build.name, 'the refusal changed previous distribution output')


def removed_previous(build):
    """Assembly started: the previous app, ZIP and guide are gone together."""
    assert not (build.app / 'previous-build').exists(), build.name
    assert not (build.dist / 'PolicyWitness.zip').exists(), build.name
    assert not (build.dist / 'PolicyWitness.md').exists(), build.name


def no_calls(build, *tools):
    for tool in tools:
        assert not build.calls(tool), (build.name, f'{tool} was invoked', build.calls(tool))


def no_compiles(build):
    """Neither Cargo nor Meson compiled anything: the admission refused before any build tool."""
    assert not build.calls('cargo', 'build'), (build.name, 'cargo build ran')
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')


def fired_once(build, label):
    assert build.fired(label) == 1, (build.name, label, build.receipts)


def no_evidence(build):
    for banner in ('Writing evidence manifest', 'Codesigning app bundle', 'Verifying signature', "Checking every executable's signer",
                   'Codesigning observer tool', 'Staging checked user guide', 'Creating zip'):
        assert banner not in build.stdout, (build.name, banner)
    assert not (build.app / 'Contents/Resources/Evidence').exists(), build.name
    assert not (build.dist / 'PolicyWitness.zip').exists(), build.name
    assert not (build.dist / 'PolicyWitness.md').exists(), build.name


def passing(co, build, variant):
    """A build that packaged: its evidence, record, stamp, session and lock state agree."""
    assert build.status == 0, (build.name, build.status, build.stderr[-4000:])
    assert 'DONE:' in build.stdout
    assert (build.dist / 'PolicyWitness.zip').stat().st_size > 0
    assert (build.app / 'Contents/XPCServices/PWRunner.xpc').exists() == (variant == 'full')
    assert any(r['tool'] == 'codesign' and '--verify' in r['args'] and r['status'] == 0 for r in build.receipts), build.receipts
    manifest = json.loads((build.app / artifact.MANIFEST).read_text())
    assert build.record is not None and build.record['schema_version'] == prov.SCHEMA_VERSION
    assert prov.record_problems(build.app, manifest) == [], prov.record_problems(build.app, manifest)
    assert any(e['rel_path'] == RECORD for e in manifest['entries']), 'the manifest must list the record'
    if variant == 'full':
        report = artifact.inspect(build.app)
        assert report['ok'], report['errors']
    assert build.stamp is not None and json.loads(build.stamp)['schema_version'] == prov.STAMP_SCHEMA_VERSION
    assert build.session['knobs']['PW_FRESH_BUILD'] in ('0', '1')
    assert set(build.judgments()) == set(CARGO_BINS), build.judgments()
    outputs = {o['rel_path']: o for o in build.record['outputs']}
    assert outputs['Contents/MacOS/policy-witness']['sha256'] is None, 'the controller hash cannot live inside the sealed record'
    for name in ('sandbox-log-observer', 'sbpl-check'):
        relative = 'Contents/MacOS/' + name
        assert outputs[relative]['sha256'] == artifact.digest(build.app / relative)
        assert outputs[relative]['cargo']['fresh'] == build.judgments()[name]['fresh']
        assert outputs[relative]['signature']['timestamp'] is True and outputs[relative]['signature']['leaf'] == co.identity
    assert build.record['toolchain']['sdk']['version'] == build.session['sdk_check']['selected']
    assert build.record['configuration']['build_directories']['cargo_release']['state'] in ('created', 'reused')
    return build


BEFORE_TOOLCHAIN = ('Checking the native toolchain', 'Configuring native build', 'Compiling native executables', 'Assembling app bundle')
BEFORE_ASSEMBLY = ('Assembling app bundle', 'Checking host/worker identity again', 'Codesigning embedded MacOS tools')
BEFORE_SIGNING = ('Codesigning embedded MacOS tools', 'Codesigning embedded XPC services', 'Writing evidence manifest')
BEFORE_CARGO = ('Admitting the Cargo output', 'Replacing the build caches', 'Building Rust controller + tools')


# ---- controls: one per refusal; the function name is the manifest's citation ----

def control_none(co, variant):
    """The valid neighbour: the same checkout, wrappers and variant package a signed app with its record."""
    build = co.build('none', variant)
    passing(co, build, variant)
    assert not any(f for r in build.receipts for f in r['fired']), build.receipts
    assert co.canary not in (build.app / RECORD).read_text()
    assert co.canary not in (build.app / artifact.MANIFEST).read_text()
    return build


def control_missing_tree_input(co, variant):
    """Each tracked input the build copies, absent before the first check: named before any banner, lock or tool."""
    build = None
    for relative in TREE_INPUTS:
        parked = co.keep_aside(relative)
        try:
            build = co.build(f'missing_tree_input-{relative.replace("/", "_")}', variant)
        finally:
            shutil.move(str(parked), str(co.root / relative))
        check(build, 2, f'missing tracked build input: {relative}', absent=('Verifying the checkout lock', 'Checking limits documentation'))
        assert not build.receipts, build.receipts
        preserved(build)
    return build


def control_checkout_busy(co, variant):
    """A held checkout lock refuses before any banner, tool or mutation; the holder and the lock file are untouched."""
    lock = co.root / 'tests/.checkout.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inode = os.fstat(fd).st_ino
        os.ftruncate(fd, 0)
        os.write(fd, b'{"pid": 0, "started_at_unix_ms": 0, "nonce": "control"}\n')
        build = co.build('checkout_busy', variant, holder_alive=True)
        check(build, 2, 'checkout busy: another execution or mutating operation holds tests/.checkout.lock',
              absent=('Verifying the checkout lock', 'Checking limits documentation'))
        assert not build.receipts, build.receipts
        preserved(build)
        assert lock.stat().st_ino == inode, 'the lock file was unlinked or replaced'
        assert lock.read_bytes() == b'{"pid": 0, "started_at_unix_ms": 0, "nonce": "control"}\n', 'the refused build rewrote the owner record'
        # The holder still holds: a separate open cannot take the lock, and the refused build left no claim behind.
        assert not lock_free(co.root)
        fresh_build = co.build('checkout_busy-fresh', variant, fresh='1', holder_alive=True)
        check(fresh_build, 2, 'checkout busy', absent=('Replacing the build caches',))
        assert (co.builddir / 'build.ninja').exists(), 'a busy lock in fresh mode removed a cache'
        preserved(fresh_build)
    finally:
        os.close(fd)
    assert lock_free(co.root)
    return build


def control_lock_claim_invalid(co, variant):
    """A claim the environment makes without a real hold is refused at verification; a competing real holder is unchanged."""
    builds = []
    stale = {'PW_CHECKOUT_LOCK_FD': '3', 'PW_CHECKOUT_LOCK_ROOT': str(co.root), 'PW_CHECKOUT_LOCK_NONCE': 'f' * 32}
    build = co.build('lock_claim_invalid-closed', variant, claim=stale)
    check(build, 2, 'checkout lock claim is not verified', present=('Verifying the checkout lock',),
          absent=('Checking limits documentation', 'Building Rust'))
    assert 'is not open in this process' in build.stderr, build.stderr[-1000:]
    assert not build.receipts and lock_free(co.root)
    preserved(build)
    builds.append(build)
    # A separately opened descriptor on the real lock's inode, with the owner nonce copied, while the real holder lives.
    lock = co.root / 'tests/.checkout.lock'
    holder = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(holder, 0)
        os.write(holder, b'{"pid": 0, "started_at_unix_ms": 0, "nonce": "' + b'a' * 32 + b'"}\n')
        separate = os.open(lock, os.O_RDWR)
        try:
            os.set_inheritable(separate, True)
            claim = {'PW_CHECKOUT_LOCK_FD': str(separate), 'PW_CHECKOUT_LOCK_ROOT': str(co.root), 'PW_CHECKOUT_LOCK_NONCE': 'a' * 32}
            build = co.build('lock_claim_invalid-separate', variant, claim=claim, pass_fds=(separate,), holder_alive=True)
        finally:
            os.close(separate)
        check(build, 2, 'does not hold the lock', present=('Verifying the checkout lock',), absent=('Checking limits documentation',))
        assert not build.receipts
        preserved(build)
        assert not lock_free(co.root), 'the refused claim released the real holder'
        assert json.loads(lock.read_text())['nonce'] == 'a' * 32, 'the refused claim rewrote the owner record'
        # Another checkout's claim and another file are refused the same way.
        other = {'PW_CHECKOUT_LOCK_FD': str(separate), 'PW_CHECKOUT_LOCK_ROOT': '/private/tmp', 'PW_CHECKOUT_LOCK_NONCE': 'a' * 32}
        build = co.build('lock_claim_invalid-checkout', variant, claim=other, holder_alive=True)
        check(build, 2, 'another checkout', present=('Verifying the checkout lock',))
    finally:
        os.close(holder)
    builds.append(build)
    return builds[0]


def control_sdk_unavailable(co, variant):
    """Only SDK selection sees a disposable developer directory, inside a restrictive sandbox.

    The shell wrapper still invokes the real xcrun. It supplies the fixture's
    unconfigured developer directory, not an exit status. All other build tools use the real
    selected developer directory, including the /usr/bin Python/git shims.
    """
    fixture = co.work / 'developer-without-sdk'
    if not fixture.exists():
        fake_developer_dir(fixture)
    build = co.build('sdk_unavailable', variant, env=dict(BASH_ENV=str(fixture / 'sdk-only.bash')))
    check(build, 2, 'xcrun could not select the macOS SDK',
          present=('Checking host/worker identity', 'Selecting the macOS SDK'),
          absent=('Checking the native build directory', 'Checking the signing identity', 'Building Rust'))
    assert not build.receipts, build.receipts
    calls = (fixture / 'calls').read_text().splitlines()
    assert calls[-1] == '--sdk macosx --show-sdk-path', calls
    assert int((fixture / 'invocation.status').read_text()) != 0
    assert 'invalid DEVELOPER_DIR path' in (fixture / 'invocation.stderr').read_text()
    assert 'requesting installation' not in build.output, build.output[-2000:]
    shutil.copytree(fixture, co.out / f'{co.prefix}{variant}-sdk_unavailable' / 'sdk-fixture')
    preserved(build)
    return build


def fake_developer_dir(fixture):
    """An unconfigured developer directory, independent of Xcode/CLT layout.

    No /usr/bin tool shim runs with the fake DEVELOPER_DIR. The isolated SDK
    command may execute only xcrun, cannot make Mach service lookups or write
    outside its own fixture. Its real configuration error drives the refusal;
    no SDK response or exit status is fabricated.
    """
    fake = fixture / 'unconfigured-developer'
    fake.mkdir(parents=True)
    profile = fixture / 'sdk.sb'
    # JSON string quoting is also valid for these SBPL path literals.
    profile.write_text('(version 1)(allow default)(deny mach-lookup)(deny process-exec)'
        '(allow process-exec (literal "/usr/bin/xcrun"))'
        '(deny file-write*)(allow file-write* (subpath ' + json.dumps(str(fixture.resolve())) + '))\n')
    prefix = ['/usr/bin/sandbox-exec', '-f', str(profile)]
    env = dict(os.environ, DEVELOPER_DIR=str(fake))
    # Verify containment before the SDK query. A general subprocess cannot run;
    # the allowed SDK process must report the real developer-directory error.
    denied = command(fixture / 'containment', prefix + ['/usr/bin/true'], cwd=fixture, env=env)
    assert denied[0] != 0 and 'Operation not permitted' in denied[2], denied
    refused = command(fixture / 'sdk-probe', prefix + ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'],
                      cwd=fixture, env=env)
    assert refused[0] != 0 and 'invalid DEVELOPER_DIR path' in refused[2], refused
    (fixture / 'sdk-only.bash').write_text(
        '/usr/bin/xcrun() {\n'
        '  [[ "$*" == "--sdk macosx --show-sdk-path" ]] || return 125\n'
        '  printf "%s\\n" "$*" >> ' + shlex.quote(str(fixture / 'calls')) + '\n'
        '  local sdk_status=0\n'
        '  DEVELOPER_DIR=' + shlex.quote(str(fake)) + ' command ' + shlex.join(prefix) +
        ' /usr/bin/xcrun "$@" > ' + shlex.quote(str(fixture / 'invocation.stdout')) +
        ' 2> ' + shlex.quote(str(fixture / 'invocation.stderr')) + ' || sdk_status=$?\n'
        '  cat ' + shlex.quote(str(fixture / 'invocation.stdout')) + '\n'
        '  cat ' + shlex.quote(str(fixture / 'invocation.stderr')) + ' >&2\n'
        '  printf "%s\\n" "$sdk_status" > ' + shlex.quote(str(fixture / 'invocation.status')) + '\n'
        '  return "$sdk_status"\n}\n')


def control_sdk_version_unreadable(co, variant):
    """xcrun selects the SDK but reports no numeric version for it: the selection refuses before the build directory."""
    fixture = co.work / 'developer-without-version'
    if not fixture.exists():
        fixture.mkdir()
        (fixture / 'version-garbage.bash').write_text(
            '/usr/bin/xcrun() {\n'
            '  if [[ "${*: -1}" == "--show-sdk-version" ]]; then\n'
            '    printf "%s\\n" "$*" >> ' + shlex.quote(str(fixture / 'calls')) + '\n'
            '    echo "latest"\n    return 0\n  fi\n'
            '  command /usr/bin/xcrun "$@"\n}\n')
    build = co.build('sdk_version_unreadable', variant, env=dict(BASH_ENV=str(fixture / 'version-garbage.bash')))
    check(build, 2, "xcrun did not report a numeric macOS SDK version (got 'latest')",
          present=('Selecting the macOS SDK',), absent=('Checking the native build directory', 'Building Rust'))
    assert not build.receipts, build.receipts
    preserved(build)
    return build


def control_builddir_stamp_missing(co, variant):
    """A configured directory without its stamp is not adopted: refused before the identity and Cargo; fresh mode recovers."""
    stamp = co.root / STAMP
    assert stamp.is_file() and (co.builddir / 'build.ninja').is_file(), 'the valid neighbour leaves a stamped directory'
    kept = stamp.read_bytes()
    stamp.unlink()
    ninja_before = (co.builddir / 'build.ninja').stat().st_mtime_ns
    build = co.build('builddir_stamp_missing', variant)
    check(build, 2, 'has no pw-toolchain.json', present=('Checking the native build directory',),
          absent=('Checking the signing identity', *BEFORE_CARGO))
    assert 'PW_FRESH_BUILD=1' in build.stderr
    assert not stamp.exists(), 'validation never writes a stamp'
    assert (co.builddir / 'build.ninja').stat().st_mtime_ns == ninja_before, 'the refusal reconfigured the directory'
    no_compiles(build)
    preserved(build)
    # A stamp beside an unconfigured directory is an unknown state as well.
    ninja = co.keep_aside('builddir/build.ninja')
    stamp.write_bytes(kept)
    try:
        unconfigured = co.build('builddir_stamp_missing-unconfigured', variant)
    finally:
        shutil.move(str(ninja), str(co.builddir / 'build.ninja'))
    check(unconfigured, 2, 'no configuration', absent=('Checking the signing identity', *BEFORE_CARGO))
    preserved(unconfigured)
    # Explicit fresh recovery replaces the directory and publishes a new stamp; Cargo rebuilds every target.
    stamp.unlink()
    recovered = co.build('builddir_stamp_missing-recovery', variant, fresh='1')
    passing(co, recovered, variant)
    assert 'Replacing the build caches' in recovered.stdout
    assert recovered.session['fresh']['replacement']['builddir']['removed'] is True
    assert all(j['fresh'] is False for j in recovered.judgments().values()), recovered.judgments()
    assert recovered.calls('meson', 'setup') and not recovered.calls('meson', 'configure')
    return build


def control_builddir_stamp_invalid(co, variant):
    """A malformed, unsupported or foreign stamp beside a configured directory is refused and never rewritten."""
    stamp = co.root / STAMP
    kept = stamp.read_bytes()
    record = json.loads(kept)
    build = None
    try:
        for label, text, needle in (('malformed', '{not json', 'malformed'),
                                    ('unsupported', json.dumps(dict(record, schema_version=99)), 'unsupported schema'),
                                    ('elsewhere', json.dumps(dict(record, source_dir='/private/tmp/elsewhere')), 'not this checkout'),
                                    ('other-compiler', json.dumps(dict(record, fields=dict(record['fields'], **{'compilers.c.command': ['/usr/bin/other-cc']}))),
                                     'does not describe this directory')):
            stamp.write_text(text)
            build = co.build(f'builddir_stamp_invalid-{label}', variant)
            check(build, 2, needle, present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
            assert stamp.read_text() == text, 'the refusal rewrote the stamp'
            no_compiles(build)
            preserved(build)
    finally:
        stamp.write_bytes(kept)
    return build


def control_builddir_toolchain_changed(co, variant):
    """A forwarding Rust compiler wrapper configured as A: unchanged reuse passes, the same wrapper relabelled B refuses
    reuse by name, and fresh mode recovers under B. The wrapper forwards every compilation to the real compiler and
    records each invocation, distinguishing compilations from version and capability probes."""
    real = subprocess.check_output(['rustup', 'which', 'rustc'], text=True).strip() if shutil.which('rustup') else shutil.which('rustc')
    wrapper = co.forwarding('rustc-forward', real, mode='direct', label='A', stderr_canary=co.canary)
    env = dict(RUSTC=str(wrapper))
    first = co.build('toolchain_changed-fresh-A', variant, env=env, fresh='1')
    passing(co, first, variant)
    assert first.record['toolchain']['rustc']['identity'].endswith('[forward A]'), first.record['toolchain']['rustc']
    assert first.record['toolchain']['rustc']['source'] == 'RUSTC'
    assert any(r['kind'] == 'compile' for r in first.forward), 'the wrapper received no compilation'
    assert any(r['kind'] == 'version' for r in first.forward), 'the wrapper received no version probe'
    stamped = json.loads(first.stamp)['fields']
    assert stamped['rustc.identity'].endswith('[forward A]') and stamped['rustc.command'] == str(wrapper)
    # Effective flags per output come from Cargo's fingerprint and agree with the compilations the wrapper received.
    compiled = [r for r in first.forward if r['kind'] == 'compile' and '--crate-name' in r['args']]
    for output in first.record['outputs']:
        cargo = output.get('cargo')
        if not cargo or cargo.get('status') != 'reported':
            continue
        assert cargo['fingerprint']['status'] == 'observed', cargo
        name = output['rel_path'].rsplit('/', 1)[1].replace('-', '_')
        invocations = [r for r in compiled if r['args'][r['args'].index('--crate-name') + 1] == name]
        assert invocations, (name, [r['args'][:3] for r in compiled][:5])
        flags = cargo['effective_rustflags']
        assert all(flag in invocations[-1]['args'] for flag in flags), (flags, invocations[-1]['args'])
    reused = co.build('toolchain_changed-reuse-A', variant, env=env)
    passing(co, reused, variant)
    assert reused.stamp == first.stamp, 'unchanged reuse rewrote the stamp'
    assert all(j['fresh'] for j in reused.judgments().values()), reused.judgments()
    co.forwarding('rustc-forward', real, mode='direct', label='B', stderr_canary=co.canary)
    refused = co.build('toolchain_changed-reuse-B', variant, env=env)
    check(refused, 1, 'rustc.identity', present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
    assert 'a changed toolchain cannot reuse this directory' in refused.stderr
    assert '[forward A]' in refused.stderr and '[forward B]' in refused.stderr, refused.stderr[-1500:]
    assert refused.stamp == first.stamp and not refused.calls('cargo', 'build')
    preserved(refused)
    recovered = co.build('toolchain_changed-fresh-B', variant, env=env, fresh='1')
    passing(co, recovered, variant)
    assert json.loads(recovered.stamp)['fields']['rustc.identity'].endswith('[forward B]')
    assert any(r['kind'] == 'compile' for r in recovered.forward)
    # Back to the ordinary compiler: the binding changed again, so reuse is refused until fresh mode.
    plain = co.build('toolchain_changed-reuse-plain', variant)
    check(plain, 1, 'rustc.command', absent=BEFORE_CARGO)
    restored = co.build('toolchain_changed-fresh-plain', variant, fresh='1')
    passing(co, restored, variant)
    return refused


def control_provenance_probe_failed(co, variant):
    """A required observation that fails or hangs refuses before Cargo; its stderr never reaches a record."""
    real = subprocess.check_output(['rustup', 'which', 'rustc'], text=True).strip() if shutil.which('rustup') else shutil.which('rustc')
    wrapper = co.forwarding('rustc-probe', real, mode='direct', label='P', stderr_canary=co.canary)
    env = dict(RUSTC=str(wrapper))
    primed = co.build('probe_failed-fresh', variant, env=env, fresh='1')
    passing(co, primed, variant)
    co.forwarding('rustc-probe', real, mode='direct', label='P', fail_version=True, stderr_canary=co.canary)
    failed = co.build('probe_failed-nonzero', variant, env=env)
    check(failed, 2, 'required toolchain observation failed: rustc.command (nonzero_exit)',
          present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
    no_compiles(failed)
    preserved(failed)
    assert co.canary not in (co.root / SESSION).read_text()
    co.forwarding('rustc-probe', real, mode='direct', label='P', hang_version=True, stderr_canary=co.canary)
    started = time.monotonic()
    hung = co.build('probe_failed-hang', variant, env=env)
    check(hung, 2, 'required toolchain observation failed: rustc.command (timeout)', absent=BEFORE_CARGO)
    assert time.monotonic() - started < prov.PROBE_TIMEOUT + 60, 'a hung probe was not bounded'
    preserved(hung)
    restored = co.build('probe_failed-fresh-plain', variant, fresh='1')
    passing(co, restored, variant)
    return failed


def control_cargo_build_dir_redirected(co, variant):
    """Cargo intermediate state redirected outside the pinned directory refuses before any mutation, in both modes."""
    elsewhere = co.work / 'redirected-build-dir'
    elsewhere.mkdir(exist_ok=True)
    (elsewhere / 'sentinel').write_text('external\n')
    env = dict(CARGO_BUILD_BUILD_DIR=str(elsewhere))
    build = co.build('cargo_build_dir_redirected', variant, env=env)
    check(build, 1, 'outside the admitted', present=('Admitting the Cargo output and intermediate directories',),
          absent=('Replacing the build caches', 'Building Rust'))
    assert 'nothing was removed' in build.stderr
    assert (elsewhere / 'sentinel').read_text() == 'external\n' and sorted(p.name for p in elsewhere.iterdir()) == ['sentinel']
    assert not build.calls('cargo', 'build') and build.calls('cargo', 'metadata')
    preserved(build)
    fresh_build = co.build('cargo_build_dir_redirected-fresh', variant, env=env, fresh='1')
    check(fresh_build, 1, 'outside the admitted', absent=('Replacing the build caches', 'Building Rust'))
    assert (co.builddir / 'build.ninja').exists() and co.target.is_dir(), 'a refused admission removed a cache in fresh mode'
    assert (elsewhere / 'sentinel').read_text() == 'external\n'
    preserved(fresh_build)
    return build


def control_cargo_build_dir_unknown(co, variant):
    """Cargo cannot report the intermediate directory: nothing is admitted or built."""
    build = co.build('cargo_build_dir_unknown', variant,
                     hooks=[hook('garbage-metadata', 'cargo', first='metadata', respond=dict(stdout='not json\n', status=0))])
    check(build, 2, 'cannot be admitted', present=('Admitting the Cargo output',), absent=('Replacing the build caches', 'Building Rust'))
    fired_once(build, 'garbage-metadata')
    assert not build.calls('cargo', 'build')
    preserved(build)
    failed = co.build('cargo_build_dir_unknown-nonzero', variant,
                      hooks=[hook('failed-metadata', 'cargo', first='metadata', respond=dict(stdout='', status=101))])
    check(failed, 2, 'did not report the intermediate directory (nonzero_exit)', absent=('Building Rust',))
    preserved(failed)
    return build


def control_fresh_removal_unsafe(co, variant):
    """A cache path fresh mode cannot admit (a symlink to an external directory) refuses before anything is removed."""
    elsewhere = co.work / 'external-release'
    elsewhere.mkdir(exist_ok=True)
    (elsewhere / 'sentinel').write_text('external\n')
    parked = co.keep_aside('controller/target/release')
    co.target.symlink_to(elsewhere)
    try:
        build = co.build('fresh_removal_unsafe', variant, fresh='1')
    finally:
        co.target.unlink()
        shutil.move(str(parked), str(co.target))
    check(build, 2, 'is a symlink; fresh mode removes only real directories', present=('Replacing the build caches',), absent=('Building Rust',))
    assert (elsewhere / 'sentinel').read_text() == 'external\n'
    assert (co.builddir / 'build.ninja').exists(), 'the refused admission removed the admitted sibling'
    assert 'fresh' not in build.session, 'a refused admission must not record a replacement'
    assert build.record is None
    preserved(build)
    return build


def control_fresh_removal_failed(co, variant):
    """A removal that fails stops the build naming the path, records the failure, and the next fresh build recovers."""
    locked = co.builddir / 'control-immutable'
    locked.write_text('x\n')
    subprocess.run(['/usr/bin/chflags', 'uchg', str(locked)], check=True)
    try:
        build = co.build('fresh_removal_failed', variant, fresh='1')
    finally:
        subprocess.run(['/usr/bin/chflags', 'nouchg', str(locked)], check=False)
    check(build, 1, 'fresh mode could not remove', present=('Replacing the build caches',), absent=('Building Rust',))
    assert build.session['fresh']['failed'] == 'builddir'
    assert build.record is None and not build.calls('cargo', 'build')
    preserved(build)
    locked.unlink()
    recovered = co.build('fresh_removal_failed-recovery', variant, fresh='1')
    passing(co, recovered, variant)
    return build


def control_missing_cargo_output(co, variant):
    """Each shipped Cargo output removed right after Cargo reports it: refused before Meson, naming the path."""
    build = None
    for binary in CARGO_BINS:
        label = f'remove-{binary}'
        build = co.build(f'missing_cargo_output-{binary}', variant, hooks=[hook(label, 'cargo', [delete(co.target / binary)], first='build')])
        check(build, 2, f'expected an executable Cargo output at {co.target / binary}',
              present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
        fired_once(build, label)
        assert len(build.calls('cargo', 'build')) == 1, build.receipts
        no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
        preserved(build)
    # A present but non-executable output is refused by the same check: Cargo's path report and a parsable Mach-O do
    # not establish the permission bit, and the build never repairs it with a later chmod.
    path = co.target / 'sbpl-check'
    try:
        build = co.build('missing_cargo_output-nonexecutable', variant,
                         hooks=[hook('strip-x', 'cargo', [dict(op='chmod', path=str(path), mode='644')], first='build')])
    finally:
        if path.exists():
            path.chmod(0o755)
    check(build, 2, f'expected an executable Cargo output at {path}', present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
    fired_once(build, 'strip-x')
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    return build


def control_cargo_artifact_elsewhere(co, variant):
    """Cargo itself places the outputs under the host triple when the environment selects one."""
    moved = co.root / 'controller/target' / co.host_triple / 'release/policy-witness'
    build = co.build('cargo_artifact_elsewhere', variant, env=dict(CARGO_BUILD_TARGET=co.host_triple))
    check(build, 2, f'cargo built policy-witness at {moved}, not at {co.target / "policy-witness"}; '
                    'a target triple or a Cargo setting moved it',
          present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
    assert moved.exists(), moved
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    return build


def control_cargo_failed(co, variant):
    """A Rust source that does not compile: Cargo's status and diagnostic stop the build before Meson."""
    source = co.root / RUST_BIN_SOURCE
    original = source.read_bytes()
    source.write_bytes(original + b'\nfn pw_control_broken( {\n')
    try:
        build = co.build('cargo_failed', variant)
    finally:
        source.write_bytes(original)
    check(build, 101, 'error: could not compile `controller`',
          present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
    assert 'unclosed delimiter' in build.stderr, build.stderr[-2000:]
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    return build


def control_cargo_target_reused(co, variant):
    """In fresh mode, a reused or missing Cargo judgment after replacement refuses before Meson."""
    messages = co.root / 'controller/target/pw-build-messages.jsonl'
    build = co.build('cargo_target_reused', variant, fresh='1',
                     hooks=[hook('report-reused', 'cargo', [judge(messages, 'sbpl-check', set=dict(fresh=True))], first='build')])
    check(build, 1, 'fresh mode requires Cargo to report rebuilding every shipped target, but sbpl-check (reused)',
          present=('Replacing the build caches', 'Building Rust controller + tools'), absent=BEFORE_TOOLCHAIN)
    fired_once(build, 'report-reused')
    assert build.session['fresh']['replacement']['cargo_release']['removed'] is True
    assert build.judgments()['sbpl-check']['fresh'] is True and build.judgments()['policy-witness']['fresh'] is False
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    # A report with no entry for a shipped target stops at the artifact-path check that precedes the judgment,
    # before Meson; the judgment's own missing-report refusal is reached only by constructed inputs (unit controls).
    missing = co.build('cargo_target_reused-missing', variant, fresh='1',
                       hooks=[hook('drop-report', 'cargo', [judge(messages, 'sbpl-check', drop=True)], first='build')])
    check(missing, 1, 'Cargo reported no executable for sbpl-check', absent=BEFORE_TOOLCHAIN)
    fired_once(missing, 'drop-report')
    no_calls(missing, 'meson', 'ninja', 'codesign', 'cp')
    preserved(missing)
    return build


def control_meson_ninja_missing(co, variant):
    """A PATH with Cargo and the system tools but neither meson nor ninja."""
    build = co.build('meson_ninja_missing', variant, bin_dir=co.bin_without_meson, homebrew=False)
    check(build, 2, 'meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md',
          present=('Building Rust controller + tools', 'Checking the native toolchain'),
          absent=('Configuring native build', 'Compiling native executables', 'Assembling app bundle'))
    assert len(build.calls('cargo', 'build')) == 1, build.receipts
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    return build


def control_ninja_old(co, variant):
    """A ninja that reports a version below the minimum the script states."""
    build = co.build('ninja_old', variant, hooks=[hook('old-ninja', 'ninja', args=['--version'], respond=dict(stdout='1.0.0\n', status=0))])
    check(build, 2, f'ninja 1.0.0 is older than the {co.ninja_minimum} minimum; see docs/SIGNING.md',
          present=('Checking the native toolchain',),
          absent=('Configuring native build', 'Compiling native executables', 'Assembling app bundle'))
    # The stamp check observes ninja's version when the directory is configured; the toolchain step's probe refuses.
    probes = build.probes('ninja')
    assert 1 <= len(probes) <= 2 and build.fired('old-ninja') == len(probes), build.receipts
    assert not build.calls('ninja'), build.receipts
    no_calls(build, 'meson', 'codesign', 'cp')
    preserved(build)
    return build


def control_meson_policy(co, variant):
    """A configured directory departing from the fixed policy: the buildtype label, reached only through the levels it is
    derived from, and one ordinary option of the same assertion family. The regeneration the compile triggers refuses by name."""
    if not (co.builddir / 'build.ninja').exists():
        # Earlier fresh-mode controls can leave no configured directory; a valid build configures and stamps one.
        passing(co, co.build('meson_policy-prime', variant), variant)
    build = None
    for label, poison, restore, message in (
            ('buildtype', ('-Dbuildtype=custom', '-Doptimization=plain', '-Ddebug=false'), ('-Dbuildtype=plain',),
             'Assert failed: fixed native policy: buildtype must be plain (got custom)'),
            ('b_lto', ('-Db_lto=true',), ('-Db_lto=false',), 'Assert failed: fixed native policy: b_lto must be false (got true)')):
        poisoned = co.meson('configure', str(co.builddir), *poison)
        assert poisoned.returncode == 0, poisoned.stdout + poisoned.stderr
        try:
            build = co.build(f'meson_policy-{label}', variant)
        finally:
            restored = co.meson('configure', str(co.builddir), *restore)
            assert restored.returncode == 0, restored.stdout + restored.stderr
        check(build, 1, message, where='output',
              present=('Configuring native build (meson configure, existing directory)', 'Compiling native executables'),
              absent=('Checking the configured native source lists', 'Assembling app bundle'))
        no_calls(build, 'codesign', 'cp')
        preserved(build)
    return build


def control_meson_failed(co, variant):
    """A C source that does not compile: the compiler's diagnostic and Ninja's status stop the build."""
    source = co.root / VALIDATOR_SOURCE
    original = source.read_bytes()
    source.write_bytes(b'#error pw_control\n' + original)
    try:
        build = co.build('meson_failed', variant)
    finally:
        source.write_bytes(original)
    check(build, 1, 'error: pw_control', where='output',
          present=('Compiling native executables',),
          absent=('Checking the configured native source lists', 'Assembling app bundle'))
    no_calls(build, 'codesign', 'cp')
    preserved(build)
    return build


def control_native_sources_unreadable(co, variant):
    """A build directory Meson can no longer introspect after it compiled."""
    intro = co.builddir / 'meson-info/intro-buildoptions.json'
    parked = co.aside / 'intro-buildoptions.json'
    try:
        build = co.build('native_sources_unreadable', variant, hooks=[hook('remove-intro', 'meson', [move(intro, parked)], first='compile')])
    finally:
        if parked.exists():
            shutil.move(str(parked), str(intro))
    check(build, 2, 'native sources: meson introspection failed',
          present=('Compiling native executables', 'Checking the configured native source lists'),
          absent=('Assembling app bundle',))
    fired_once(build, 'remove-intro')
    no_calls(build, 'codesign', 'cp')
    preserved(build)
    return build


def control_missing_native_output(co, variant):
    """A Meson output that vanishes after the compile and the source check."""
    output = co.builddir / 'sb_api_validator'
    build = co.build('missing_native_output', variant, hooks=[hook('remove-validator', 'meson', [delete(output)], first='compile')])
    check(build, 2, f'expected Meson output at {output}',
          present=('Checking the configured native source lists',), absent=BEFORE_ASSEMBLY)
    fired_once(build, 'remove-validator')
    no_calls(build, 'codesign', 'cp')
    preserved(build)
    return build


def control_stale_identity_presign(co, variant):
    """An identity input edited after compile and before signing, without regeneration."""
    source = co.root / IDENTITY_INPUT
    original = source.read_bytes()
    try:
        build = co.build('stale_identity_presign', variant,
                         hooks=[hook('edit-identity-input', 'meson', [append(source, '\n// pw_control\n')], first='compile')])
    finally:
        source.write_bytes(original)
    check(build, 1, 'generate_worker_identity.py',
          present=('Assembling app bundle', 'Checking host/worker identity again, before signing'),
          absent=('Codesigning embedded MacOS tools',))
    assert 'stale' in build.stderr, build.stderr[-2000:]
    fired_once(build, 'edit-identity-input')
    removed_previous(build)
    no_calls(build, 'codesign')
    return build


def control_worker_identity_mismatch(co, variant):
    """The built worker replaced after compile by one reporting another identity: the source recheck passes, the binary refuses."""
    stub = co.compile_wrong_worker()
    worker = co.builddir / 'pw-probe-runner'
    try:
        build = co.build('worker_identity_mismatch', variant, hooks=[hook('replace-worker', 'meson', [copy(stub, worker)], first='compile')])
    finally:
        if worker.exists():
            worker.unlink()  # a stand-in newer than its sources would otherwise survive the next compile
    check(build, 1, 'reports identity ' + '0' * 64 + ', not the generated',
          present=('Assembling app bundle', 'Checking host/worker identity again, before signing'),
          absent=('Codesigning embedded MacOS tools',))
    assert 'stale' not in build.stderr, 'the source recheck must pass; only the binary disagrees'
    fired_once(build, 'replace-worker')
    assert build.session['worker_identity']['reported'] == '0' * 64
    removed_previous(build)
    no_calls(build, 'codesign')
    return build


def control_sign_target_not_macho(co, variant):
    """A signing-list target missing or rewritten after the observer is signed: the next sign_macho refuses before codesign."""
    app = co.app(variant, 'sign_target_not_macho-missing')
    build = None
    for label, name, actions in (('missing', 'sign_target_not_macho-missing', [delete(app / 'Contents/MacOS/sbpl-check')]),
                                 ('rewritten', 'sign_target_not_macho-rewritten', None)):
        app = co.app(variant, name)
        target = app / 'Contents/MacOS/sbpl-check'
        actions = actions if actions is not None else [write(target, 'not an executable\n')]
        build = co.build(name, variant, hooks=[hook('damage-target', 'codesign', actions,
                                                      last=str(app / 'Contents/MacOS/sandbox-log-observer'), contains='--force')])
        check(build, 2, f'{target} is missing or not a Mach-O; the signing list names only executables',
              present=('Codesigning embedded MacOS tools',), absent=('Codesigning embedded XPC services', 'Writing evidence manifest'))
        fired_once(build, 'damage-target')
        expected = ([str(app / 'Contents/MacOS/pw-runner-client')] if variant == 'full' else []) + [str(app / 'Contents/MacOS/sandbox-log-observer')]
        assert build.signed() == expected, (build.signed(), expected)
        assert str(target) not in build.signed(), 'codesign ran on the damaged target'
        no_evidence(build)
    return build


def control_codesign_failed(co, variant):
    """A Mach-O truncated as codesign reaches it: codesign's own status and diagnostic stop the build."""
    app = co.app(variant, 'codesign_failed')
    target = app / 'Contents/MacOS/sbpl-check'
    build = co.build('codesign_failed', variant,
                     hooks=[hook('truncate-target', 'codesign', [truncate(target, 4096)], when='before', last=str(target), contains='--force')])
    check(build, 1, str(target), present=('Codesigning embedded MacOS tools',),
          absent=('Codesigning embedded XPC services', 'Writing evidence manifest'))
    fired_once(build, 'truncate-target')
    failed = [r for r in build.calls('codesign') if r['args'][-1] == str(target)]
    assert len(failed) == 1 and failed[0]['status'] == 1, failed
    assert build.signed()[-1] == str(target), build.signed()
    no_evidence(build)
    return build


def control_evidence_failed(co, variant):
    """The app's Contents gone after the last signature before evidence generation."""
    app = co.app(variant, 'evidence_failed')
    last = app / ('Contents/XPCServices/PWRunner.xpc' if variant == 'full' else 'Contents/MacOS/sbpl-check')
    build = co.build('evidence_failed', variant,
                     hooks=[hook('remove-contents', 'codesign', [delete(app / 'Contents')], last=str(last), contains='--force')])
    check(build, 2, f'missing app bundle Contents: {app / "Contents"}',
          present=('Writing evidence manifest and provenance record',),
          absent=('Codesigning app bundle', 'Verifying signature', 'Creating zip'))
    fired_once(build, 'remove-contents')
    assert str(app) not in build.signed(), build.signed()
    assert not (build.dist / 'PolicyWitness.zip').exists()
    assert not (build.dist / 'PolicyWitness.md').exists()
    return build


def control_provenance_required_unknown(co, variant):
    """The build session gone before evidence generation: no record can be written and nothing is sealed."""
    app = co.app(variant, 'provenance_required_unknown')
    last = app / ('Contents/XPCServices/PWRunner.xpc' if variant == 'full' else 'Contents/MacOS/sbpl-check')
    build = co.build('provenance_required_unknown', variant,
                     hooks=[hook('remove-session', 'codesign', [delete(co.root / SESSION)], last=str(last), contains='--force')])
    check(build, 2, 'ERROR: provenance: build session is not readable',
          present=('Writing evidence manifest and provenance record',),
          absent=('Codesigning app bundle', 'Verifying signature', 'Creating zip'))
    fired_once(build, 'remove-session')
    assert str(app) not in build.signed(), build.signed()
    assert not (app / RECORD).exists() and not (app / artifact.MANIFEST).exists(), 'a refused record left evidence behind'
    assert not (build.dist / 'PolicyWitness.zip').exists()
    return build


def control_verify_failed(co, variant):
    """A sealed resource changed after the outer seal: strict verification fails and nothing is packaged."""
    app = co.app(variant, 'verify_failed')
    resource = app / 'Contents/Resources/Augments' / co.augment
    build = co.build('verify_failed', variant,
                     hooks=[hook('tamper-resource', 'codesign', [append(resource, '\n; tampered\n')], last=str(app), contains='--force')])
    check(build, 1, 'a sealed resource is missing or invalid',
          present=('Codesigning app bundle', 'Verifying signature + entitlements'),
          absent=("Checking every executable's signer", 'Codesigning observer tool', 'Staging checked user guide', 'Creating zip'))
    fired_once(build, 'tamper-resource')
    assert str(co.target / 'sandbox-log-observer') not in build.signed(), build.signed()
    assert not (build.dist / 'PolicyWitness.zip').exists()
    assert not (build.dist / 'PolicyWitness.md').exists()
    # An embedded evidence edit after the seal fails verification: no record is rewritten after sealing.
    edited = co.app(variant, 'verify_failed-record-edit')
    sealed = co.build('verify_failed-record-edit', variant,
                      hooks=[hook('edit-record', 'codesign', [append(edited / RECORD, '\n')], last=str(edited), contains='--force')])
    check(sealed, 1, 'a sealed resource is missing or invalid', absent=("Checking every executable's signer", 'Creating zip'))
    fired_once(sealed, 'edit-record')
    assert not (sealed.dist / 'PolicyWitness.zip').exists()
    return build


def control_fresh_sequence(co, variant):
    """The state sequence through the actual entrypoint, with a forwarding C compiler wrapper selected as A at setup:
    fresh build, unchanged reuse, a permitted option change (enabling the XPC pieces extends the stamp with the Swift
    compiler), reuse again, refused incompatible reuse when the wrapper is relabelled B, explicit fresh recovery under B;
    then interrupted setup and stamp publication on each side of their boundaries, a compile failure retried under the
    validated configuration, and the two caches surviving independently."""
    real = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '-f', 'clang'], text=True).strip()
    wrapper = co.forwarding('cc-forward', real, mode='direct', label='A', stderr_canary=co.canary)
    env = dict(CC=str(wrapper))
    sentinels = {co.builddir / 'control-sentinel': 'native cache', co.target / 'control-sentinel': 'cargo cache'}
    for path, text in sentinels.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    first = co.build('sequence-1-fresh', 'partial', env=env, fresh='1')
    passing(co, first, 'partial')
    assert all(not p.exists() for p in sentinels), 'fresh mode left a cache sentinel'
    assert first.calls('meson', 'setup') and not first.calls('meson', 'configure')
    assert all(j['fresh'] is False for j in first.judgments().values())
    stamp1 = json.loads(first.stamp)
    assert stamp1['scope'] == {'xpc': False} and stamp1['fields']['compilers.c.command'] == [str(wrapper)]
    assert stamp1['fields']['compilers.c.identity'].endswith('[forward A]')
    assert any(r['kind'] == 'compile' and r['wrapper'] == 'cc-forward' for r in first.forward), 'the C wrapper compiled nothing'
    assert first.record['toolchain']['compilers']['swift']['status'] == 'not applicable'
    assert first.record['configuration']['build_directories']['builddir'] == dict(state='created', replaced_by_fresh_mode=True, stamp='published')
    reused = co.build('sequence-2-reuse', 'partial', env=env)
    passing(co, reused, 'partial')
    assert reused.stamp == first.stamp and reused.calls('meson', 'configure') and not reused.calls('meson', 'setup')
    assert all(j['fresh'] is True for j in reused.judgments().values())
    assert reused.record['configuration']['build_directories']['builddir']['state'] == 'reused'
    assert reused.record['configuration']['build_directories']['builddir']['stamp'] == 'validated'
    changed = co.build('sequence-3-enable-xpc', 'full', env=env)
    passing(co, changed, 'full')
    stamp3 = json.loads(changed.stamp)
    assert stamp3['scope'] == {'xpc': True} and stamp3['fields']['compilers.swift.command'] == ['swiftc']
    assert {k: v for k, v in stamp3['fields'].items() if not k.startswith('compilers.swift.')} == stamp1['fields'], 'extension changed another field'
    assert stamp3['published_at'] == stamp1['published_at'] and stamp3['extended_at']
    assert changed.record['configuration']['build_directories']['builddir']['stamp'] == 'extended'
    assert changed.record['toolchain']['compilers']['swift']['observed']['status'] == 'ok'
    again = co.build('sequence-4-reuse-full', 'full', env=env)
    passing(co, again, 'full')
    assert again.stamp == changed.stamp
    inspection = co.build('sequence-5-inspection-off', 'full', env=env | {'PW_INSPECTION': '0'})
    passing(co, inspection, 'full')
    assert inspection.stamp == changed.stamp, 'an inspection change is permitted and leaves the stamp intact'
    assert inspection.record['configuration']['knobs']['PW_INSPECTION'] == '0'
    back = co.build('sequence-6-partial-again', 'partial', env=env)
    passing(co, back, 'partial')
    assert back.stamp == changed.stamp, 'disabling the XPC pieces leaves the Swift binding in the stamp'
    co.forwarding('cc-forward', real, mode='direct', label='B', stderr_canary=co.canary)
    refused = co.build('sequence-7-refused', 'full', env=env)
    check(refused, 1, 'compilers.c.identity', present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
    assert refused.stamp == changed.stamp and not refused.calls('meson')
    preserved(refused)
    recovered = co.build('sequence-8-fresh-B', 'full', env=env, fresh='1')
    passing(co, recovered, 'full')
    assert json.loads(recovered.stamp)['fields']['compilers.c.identity'].endswith('[forward B]')
    assert json.loads(recovered.stamp)['scope'] == {'xpc': True}
    # Interruptions: after setup before publication, the configured directory has no stamp and is not adopted.
    killed = co.build('sequence-9-killed-after-setup', 'partial', env=env, fresh='1',
                      hooks=[hook('kill-after-setup', 'meson', [kill_parent()], first='setup')])
    assert killed.status != 0 and (co.builddir / 'build.ninja').exists() and not (co.root / STAMP).exists(), killed.status
    assert lock_free(co.root), 'the killed build left the lock held'
    unstamped = co.build('sequence-10-unstamped', 'partial', env=env)
    check(unstamped, 2, 'has no pw-toolchain.json', absent=BEFORE_CARGO)
    preserved(unstamped)
    republished = co.build('sequence-11-fresh-again', 'partial', env=env, fresh='1')
    passing(co, republished, 'partial')
    # After publication before compile: the next incremental build validates the matching stamp and compiles.
    # The wrapper kills the script's shell and then runs the compile itself: that descendant inherited the lock
    # descriptor, so the hold outlives the killed parent and ends only when the compile exits.
    interrupted = co.build('sequence-12-killed-before-compile', 'partial', env=env, fresh='1', holder_alive=True,
                           hooks=[hook('kill-before-compile', 'meson', [kill_parent()], when='before', first='compile')])
    assert interrupted.status != 0 and (co.root / STAMP).exists()
    held_after_kill = not lock_free(co.root)
    deadline = time.monotonic() + 600
    while not lock_free(co.root) and time.monotonic() < deadline:
        time.sleep(0.2)
    assert lock_free(co.root), 'the orphaned compile never released the lock'
    save(co.out / f'{co.prefix}partial-sequence-12-killed-before-compile' / 'lock-lifetime.json',
         dict(held_by_descendant_after_parent_killed=held_after_kill, released_after_descendant_exit=True))
    retried = co.build('sequence-13-retry', 'partial', env=env)
    passing(co, retried, 'partial')
    assert retried.stamp == interrupted.stamp and retried.calls('meson', 'configure')
    # A compile failure is retried under the validated configuration; the stamp is neither rewritten nor adopted anew.
    source = co.root / VALIDATOR_SOURCE
    original = source.read_bytes()
    source.write_bytes(b'#error pw_control\n' + original)
    try:
        failed = co.build('sequence-14-compile-failure', 'partial', env=env)
    finally:
        source.write_bytes(original)
    check(failed, 1, 'error: pw_control', where='output')
    assert failed.stamp == retried.stamp
    recompiled = co.build('sequence-15-retry-after-failure', 'partial', env=env)
    passing(co, recompiled, 'partial')
    assert recompiled.stamp == retried.stamp
    # The caches survive independently: removing one leaves the other's reuse judgment intact.
    shutil.rmtree(co.target)
    cargo_only = co.build('sequence-16-cargo-cache-removed', 'partial', env=env)
    passing(co, cargo_only, 'partial')
    assert all(j['fresh'] is False for j in cargo_only.judgments().values()) and cargo_only.calls('meson', 'configure')
    assert cargo_only.record['configuration']['build_directories']['cargo_release']['state'] == 'created'
    shutil.rmtree(co.builddir)
    meson_only = co.build('sequence-17-meson-cache-removed', 'partial', env=env)
    passing(co, meson_only, 'partial')
    assert all(j['fresh'] is True for j in meson_only.judgments().values()) and meson_only.calls('meson', 'setup')
    assert meson_only.record['configuration']['build_directories']['builddir']['state'] == 'created'
    # CC matters at setup only: without it the configured directory keeps the compiler it was set up with, which the
    # record names, and the stamp is byte-for-byte intact under the same options. A fresh build without CC configures
    # the ordinary compiler again.
    plain = co.build('sequence-18-plain-reuse', 'partial')
    passing(co, plain, 'partial')
    assert plain.record['toolchain']['compilers']['c']['configured']['command'] == [str(wrapper)], plain.record['toolchain']['compilers']['c']
    assert plain.stamp == meson_only.stamp
    restored = co.build('sequence-19-plain-fresh', variant, fresh='1')
    passing(co, restored, variant)
    assert json.loads(restored.stamp)['fields']['compilers.c.command'] == ['cc']
    return refused


def control_replaced_cached_output_is_recorded_not_detected(co, variant):
    """A cached Cargo output replaced before capture, with distinguishable bytes that keep the checked metadata, is reported
    reusable by Cargo and described by the record's hash. This establishes the limit of the evidence, not a refusal.
    A change after capture is a different boundary: the inspector refuses it."""
    previous = co.build('replaced_output-baseline', variant)
    passing(co, previous, variant)
    observer_bytes = (co.target / 'sandbox-log-observer').read_bytes()
    original_hash = artifact.digest(previous.app / 'Contents/MacOS/sbpl-check')
    replacement = co.work / 'replacement-sbpl-check'
    replacement.write_bytes(observer_bytes)
    replacement.chmod(0o755)
    build = co.build('replaced_output', variant, hooks=[hook('replace-cached', 'cargo', [copy(replacement, co.target / 'sbpl-check')], first='build')])
    try:
        passing(co, build, variant)
        fired_once(build, 'replace-cached')
        judgment = build.judgments()['sbpl-check']
        assert judgment['fresh'] is True, 'Cargo judged the untouched unit current; the replacement happened after its report'
        output = next(o for o in build.record['outputs'] if o['rel_path'] == 'Contents/MacOS/sbpl-check')
        shipped = artifact.digest(build.app / 'Contents/MacOS/sbpl-check')
        assert output['sha256'] == shipped and shipped != original_hash
        assert output['cargo']['fresh'] is True and 'does not authenticate their compilation history' in output['cargo']['note']
        assert any('replaced before capture' in limit for limit in build.record['limits'])
        # After capture and sealing, a helper swapped for the previous build's, validly signed by the same identity, passes
        # every signature check on a copy and is refused by the manifest and the record; the shipped app is untouched.
        copied = co.work / f'replaced-after-capture-{variant}.app'
        subprocess.run(['/usr/bin/ditto', str(build.app), str(copied)], check=True)
        (copied / 'Contents/MacOS/sbpl-check').write_bytes(previous.app.joinpath('Contents/MacOS/sbpl-check').read_bytes())
        report = artifact.inspect(copied)
        save(co.out / f'{co.prefix}{variant}-replaced_output' / 'replaced-after-capture.json', report)
        codes = {e['code'] for e in report['errors']}
        assert all(s['returncode'] == 0 for s in report['signatures']), report['signatures']
        assert not report['ok'] and {'provenance_hash', 'manifest_hash'} <= codes and 'signer' not in codes, codes
    finally:
        (co.target / 'sbpl-check').unlink(missing_ok=True)  # Cargo relinks the real output when it is missing
    return build


def control_release_entrypoints_enforce_fresh_mode(co, variant):
    """make notarize and make release, through their recursive Make calls, run the build with PW_FRESH_BUILD=1 and refuse a
    conflicting caller value before building; the controlled build step stops the chain before any submission."""
    with tempfile.TemporaryDirectory(prefix='pw-make-fresh-', dir='/private/tmp') as temporary:
        repo = Path(temporary) / 'repo'
        repo.mkdir()
        for name in ('Makefile', 'tests/lib/release_preflight.py', 'tests/fixtures/docs/prose_baseline.json', 'tests/fixtures/docs/build_baseline.json'):
            target = repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        marker = repo / 'build-invocation.json'
        script = repo / 'build.sh'
        script.write_text('#!/usr/bin/env bash\nprintf \'{"PW_FRESH_BUILD": "%s", "IDENTITY": "%s"}\' "${PW_FRESH_BUILD-unset}" "${IDENTITY:-}" > build-invocation.json\nexit 97\n')
        script.chmod(0o755)
        (repo / 'dist').mkdir()
        git = ['git', '-C', str(repo), '-c', 'user.name=Control', '-c', 'user.email=control@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'tag.gpgsign=false']
        subprocess.run([*git, 'init', '-q'], check=True)
        subprocess.run([*git, 'add', '.'], check=True)
        subprocess.run([*git, 'commit', '-qm', 'control'], check=True)
        subprocess.run([*git, 'tag', '-a', 'v0.0.1', '-m', 'control'], check=True)
        remote = Path(temporary) / 'origin.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(remote)], check=True)
        subprocess.run([*git, 'remote', 'add', 'origin', str(remote)], check=True)
        base = {k: v for k, v in co.base_env.items() if k not in ('MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES', 'MAKELEVEL', 'PW_FRESH_BUILD', 'IDENTITY')}
        results = []

        def run(label, args, env=None):
            marker.unlink(missing_ok=True)
            result = subprocess.run(['make', *args], cwd=repo, env=dict(base, **(env or {})), capture_output=True, text=True, timeout=120)
            invoked = json.loads(marker.read_text()) if marker.exists() else None
            results.append(dict(label=label, args=args, env=env, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, build=invoked))
            return result, invoked

        settings = ['NOTARY_KEYCHAIN_PROFILE=control-profile', 'IDENTITY=Developer ID Application: Control (TEAMID00AA)']
        for target in ('notarize', 'release'):
            result, invoked = run(f'{target}-default', [target, *settings])
            assert result.returncode == 2 and invoked == {'PW_FRESH_BUILD': '1', 'IDENTITY': 'Developer ID Application: Control (TEAMID00AA)'}, (result.stdout, result.stderr, invoked)
            assert 'Error 97' in result.stderr or 'Error 2' in result.stderr, result.stderr
            assert not (repo / 'dist/evidence').exists(), 'the chain continued past the controlled build'
            result, invoked = run(f'{target}-env-conflict', [target, *settings], env={'PW_FRESH_BUILD': '0'})
            assert result.returncode == 2 and invoked is None and "PW_FRESH_BUILD='0' conflicts" in result.stdout + result.stderr, (result.stdout, result.stderr)
            result, invoked = run(f'{target}-cli-conflict', [target, *settings, 'PW_FRESH_BUILD=0'])
            assert result.returncode == 2 and invoked is None and 'conflicts' in result.stdout + result.stderr, (result.stdout, result.stderr)
            result, invoked = run(f'{target}-explicit-one', [target, *settings, 'PW_FRESH_BUILD=1'])
            assert invoked == {'PW_FRESH_BUILD': '1', 'IDENTITY': 'Developer ID Application: Control (TEAMID00AA)'}, invoked
        result, invoked = run('build-unset', ['build', settings[1]])
        assert invoked == {'PW_FRESH_BUILD': 'unset', 'IDENTITY': 'Developer ID Application: Control (TEAMID00AA)'}, invoked
        save(co.out / f'{co.prefix}{variant}-release_entrypoints.json', results)
    return None


# The manifest's refusals in script order, with the variants each applies to.
CONTROLS = [
    ('missing_tree_input', ('full', 'partial'), control_missing_tree_input),
    ('checkout_busy', ('full', 'partial'), control_checkout_busy),
    ('lock_claim_invalid', ('full', 'partial'), control_lock_claim_invalid),
    ('sdk_unavailable', ('full', 'partial'), control_sdk_unavailable),
    ('sdk_version_unreadable', ('full', 'partial'), control_sdk_version_unreadable),
    ('builddir_stamp_missing', ('full', 'partial'), control_builddir_stamp_missing),
    ('builddir_stamp_invalid', ('full', 'partial'), control_builddir_stamp_invalid),
    ('cargo_build_dir_redirected', ('full', 'partial'), control_cargo_build_dir_redirected),
    ('cargo_build_dir_unknown', ('full', 'partial'), control_cargo_build_dir_unknown),
    ('fresh_removal_unsafe', ('full', 'partial'), control_fresh_removal_unsafe),
    ('fresh_removal_failed', ('full', 'partial'), control_fresh_removal_failed),
    ('missing_cargo_output', ('full', 'partial'), control_missing_cargo_output),
    ('cargo_artifact_elsewhere', ('full', 'partial'), control_cargo_artifact_elsewhere),
    ('cargo_failed', ('full', 'partial'), control_cargo_failed),
    ('cargo_target_reused', ('full', 'partial'), control_cargo_target_reused),
    ('meson_ninja_missing', ('full', 'partial'), control_meson_ninja_missing),
    ('ninja_old', ('full', 'partial'), control_ninja_old),
    ('meson_policy', ('full', 'partial'), control_meson_policy),
    ('meson_failed', ('full', 'partial'), control_meson_failed),
    ('native_sources_unreadable', ('full', 'partial'), control_native_sources_unreadable),
    ('missing_native_output', ('full', 'partial'), control_missing_native_output),
    ('stale_identity_presign', ('full', 'partial'), control_stale_identity_presign),
    ('worker_identity_mismatch', ('full', 'partial'), control_worker_identity_mismatch),
    ('sign_target_not_macho', ('full', 'partial'), control_sign_target_not_macho),
    ('codesign_failed', ('full', 'partial'), control_codesign_failed),
    ('evidence_failed', ('full', 'partial'), control_evidence_failed),
    ('provenance_required_unknown', ('full', 'partial'), control_provenance_required_unknown),
    ('verify_failed', ('full', 'partial'), control_verify_failed),
]
# Controls that drive sequences across variants or establish a limit rather than one refusal; run once each.
SEQUENCES = [
    ('builddir_toolchain_changed', control_builddir_toolchain_changed),
    ('provenance_probe_failed', control_provenance_probe_failed),
    ('fresh_sequence', control_fresh_sequence),
    ('replaced_cached_output', control_replaced_cached_output_is_recorded_not_detected),
    ('release_entrypoints', control_release_entrypoints_enforce_fresh_mode),
]


# ---- mutations: a guard removed or moved past its operation must fail its control ----

def _move_block(text, block, anchor):
    assert text.count(block) == 1 and text.count(anchor) == 1, (block[:60], anchor[:60])
    return text.replace(block, '', 1).replace(anchor, anchor + block, 1)


def _remove_block(text, block):
    assert text.count(block) == 1, block[:60]
    return text.replace(block, '', 1)


CARGO_OUTPUT_LOOP = ('for rust_bin in "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}"; do\n'
                     '  if [[ ! -x "${rust_bin}" ]]; then\n'
                     '    echo "ERROR: expected an executable Cargo output at ${rust_bin}" 1>&2\n'
                     '    exit 2\n'
                     '  fi\n'
                     '  check_minimum_macos "${rust_bin}"\n'
                     'done\n')
NINJA_GUARD = ('if ! /usr/bin/python3 -c \'import sys; v, m = (tuple(int(p) for p in a.split(".")) for a in sys.argv[1:3]); sys.exit(0 if v >= m else 1)\' \\\n'
               '    "${NINJA_VERSION}" "${NINJA_MINIMUM}"; then\n'
               '  echo "ERROR: ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md" 1>&2\n'
               '  exit 2\n'
               'fi\n')
NATIVE_OUTPUT_LOOP = ('for native_bin in "${NATIVE_OUTPUTS[@]}"; do\n'
                      '  if [[ ! -x "${native_bin}" ]]; then\n'
                      '    echo "ERROR: expected Meson output at ${native_bin}" 1>&2\n'
                      '    exit 2\n'
                      '  fi\n'
                      '  check_minimum_macos "${native_bin}"\n'
                      'done\n')
ASSEMBLY_ANCHOR = 'mkdir -p "${APP_BUNDLE}/Contents/MacOS" "${APP_BUNDLE}/Contents/Resources"\n'
TREE_INPUT_LOOP = ('for tree_input in Info.plist PolicyWitness.entitlements runner/augments runner/Services/PWRunner runner/Services/PWRunner/Info.plist runner/Services/PWRunner/Entitlements.plist; do\n'
                   '  if [[ ! -e "${ROOT_DIR}/${tree_input}" ]]; then\n'
                   '    echo "ERROR: missing tracked build input: ${tree_input}" 1>&2\n'
                   '    exit 2\n'
                   '  fi\n'
                   'done\n')
LIMITS_ANCHOR = 'echo "==> Checking limits documentation"\n'
MACHO_GUARD = ('  if ! /usr/bin/file -b "${target}" 2>/dev/null | /usr/bin/grep -q "Mach-O"; then\n'
               '    echo "ERROR: ${target} is missing or not a Mach-O; the signing list names only executables" 1>&2\n'
               '    exit 2\n'
               '  fi\n')
SIGN_ANCHOR = '  codesign --force --options runtime --timestamp -s "${IDENTITY}" "${target}"\n'
STAMP_CHECK = ('  /usr/bin/python3 -B "${ROOT_DIR}/tests/lib/build_provenance.py" stamp-check --session "${BUILD_SESSION}" \\\n'
               '    --builddir "${MESON_BUILD_DIR}" --root "${ROOT_DIR}" --xpc "${BUILD_XPC}"\n')
WORKER_IDENTITY = ('/usr/bin/python3 -B "${ROOT_DIR}/tests/lib/build_provenance.py" worker-identity --session "${BUILD_SESSION}" \\\n'
                   '  --worker "${PW_PROBE_RUNNER_BIN}" --expected "${GENERATED_WORKER_IDENTITY}"\n')
REQUIRE_REBUILT = '--require-rebuilt "${PW_FRESH_BUILD}"'

MUTATIONS = [
    ('missing_cargo_output', 'guard removed', lambda t: _remove_block(t, CARGO_OUTPUT_LOOP)),
    ('ninja_old', 'guard removed', lambda t: _remove_block(t, NINJA_GUARD)),
    ('missing_native_output', 'guard moved past assembly', lambda t: _move_block(t, NATIVE_OUTPUT_LOOP, ASSEMBLY_ANCHOR)),
    ('missing_tree_input', 'admission moved after the first check', lambda t: _move_block(t, TREE_INPUT_LOOP, LIMITS_ANCHOR)),
    ('sign_target_not_macho', 'check moved after codesign', lambda t: _move_block(t, MACHO_GUARD, SIGN_ANCHOR)),
    ('builddir_stamp_missing', 'stamp validation removed', lambda t: _remove_block(t, STAMP_CHECK)),
    ('worker_identity_mismatch', 'worker identity check removed', lambda t: _remove_block(t, WORKER_IDENTITY)),
    ('cargo_target_reused', 'rebuild requirement dropped', lambda t: t.replace(REQUIRE_REBUILT, '--require-rebuilt "0"', 1)),
]


SELF_CHECK_RE = re.compile(r'^/usr/bin/python3 -B "\$\{ROOT_DIR\}/docs/generate_[a-z_]+\.py" --check\n', re.M)
SELF_CHECK_MARKERS = ('is stale', 'missing symbol', 'disagrees with the script', 'generate_worker_identity.py')


def _without_self_checks(text):
    """The script's generator checks removed: limits, contract, architecture, build document and both identity checks.

    Their banners stay. Each of those checks compares a document or a digest with
    the script, so a mutated script fails one of them before any guard runs."""
    text, count = SELF_CHECK_RE.subn('', text)
    assert count == 6, count
    return text


def _control_failure(function, co, variant):
    try:
        function(co, variant)
    except AssertionError as exc:
        return str(exc)[:600]
    return None


def _restore(co, script, original, prefix):
    """The original script, and a fresh build with it: the valid neighbour every stage and repeat starts from."""
    script.write_bytes(original)
    co.script = original
    co.prefix = prefix
    build = co.build('restore', 'full', fresh='1')
    passing(co, build, 'full')


def demonstrate_bypass(co):
    """A guard removed or moved past its operation must fail its control, in two stages.

    With the script's self-checks present, the control fails: usually because
    the build's documentation and identity checks refuse a script that disagrees
    with the manifest or the digest before the guard is reached, which the
    first stage records from the build's stderr; a guard displaced ahead of
    those checks fails its control by the displacement itself. With the
    self-checks removed the build runs to the displaced guard, and the second
    stage shows the control failing there with no self-check involved. A fresh
    build with the original script precedes the second stage and the repeat,
    since a mutated run can leave the stamp missing or outputs torn down; the
    original script then passes the same control again."""
    results = []
    functions = {refusal: function for refusal, _, function in CONTROLS}
    script = co.root / 'build.sh'
    original = co.script
    for refusal, label, mutate in MUTATIONS:
        mutated = mutate(original.decode())
        assert mutated.encode() != original
        stages = {}
        try:
            for stage, text in (('self_checks', mutated), ('guard', _without_self_checks(mutated))):
                if stage == 'guard':
                    _restore(co, script, original, f'restore-before-guard-{refusal}-')
                script.write_bytes(text.encode())
                co.script = text.encode()
                co.prefix = f'mutated-{stage}-{refusal}-'
                co.last = None
                failure = _control_failure(functions[refusal], co, 'full')
                assert failure is not None, f'{refusal}: the control passed with the {label} ({stage} stage)'
                assert co.last is not None, f'{refusal}: the control raised before building ({stage} stage): {failure}'
                stages[stage] = dict(control=failure, build=co.last.name, status=co.last.status, stderr=co.last.stderr[-800:],
                                     self_check_refused=any(marker in co.last.stderr for marker in SELF_CHECK_MARKERS))
        finally:
            script.write_bytes(original)
            co.script = original
            (co.builddir / 'pw-probe-runner').unlink(missing_ok=True)
        assert not stages['guard']['self_check_refused'], stages['guard']
        _restore(co, script, original, f'restore-before-repeat-{refusal}-')
        co.prefix = f'repeat-{refusal}-'
        functions[refusal](co, 'full')
        co.prefix = ''
        results.append(dict(refusal=refusal, mutation=label, self_checks=stages['self_checks'], guard=stages['guard']))
        print(f"mutation {refusal}: {label}; with the self-checks "
              f"{'refusing the script' if stages['self_checks']['self_check_refused'] else 'passed by the displaced guard'}, "
              f"then failed at the guard: {stages['guard']['control'][:140]}", flush=True)
    return results


def test_build_refusals(out, identity):
    assert identity.startswith('Developer ID Application: '), 'a Developer ID Application identity is required'
    manifest = json.loads((ROOT / 'docs/build.json').read_text())
    variants = {r['id']: tuple(r['variants']) for r in manifest['refusals']}
    for refusal, applicable, _ in CONTROLS:
        assert variants[refusal] == applicable, (refusal, variants[refusal], applicable)
    records = []
    with tempfile.TemporaryDirectory(prefix='pw-build-refusals-', dir='/private/tmp') as temporary:
        co = Checkout(Path(temporary), identity, out)
        for variant in VARIANTS:
            for refusal, applicable, function in (('none', ('full', 'partial'), control_none), *CONTROLS):
                if variant not in applicable:
                    continue
                started = time.monotonic()
                build = function(co, variant)
                records.append(dict(refusal=refusal, variant=variant, status=build.status,
                                    fired=[f for r in build.receipts for f in r['fired']],
                                    elapsed_seconds=round(time.monotonic() - started, 1)))
                save(out / 'controls.json', records)
                print(f'{variant}/{refusal}: status {build.status}; protected operations checked', flush=True)
        for name, function in SEQUENCES:
            started = time.monotonic()
            build = function(co, 'full')
            records.append(dict(refusal=name, variant='sequence', status=None if build is None else build.status,
                                elapsed_seconds=round(time.monotonic() - started, 1)))
            save(out / 'controls.json', records)
            print(f'sequence/{name}: completed', flush=True)
        mutations = demonstrate_bypass(co)
        save(out / 'mutations.json', mutations)
    expected = sum(len(applicable) for _, applicable, _ in CONTROLS) + len(VARIANTS) + len(SEQUENCES)
    assert len(records) == expected, (len(records), expected)
    print(f'{expected} build refusal controls and {len(mutations)} bypass demonstrations passed')


def run_selected(out, identity, names):
    """Development entry: the valid neighbour, then only the named controls, sequences or the mutation phase
    (`mutations`), in the full variant."""
    functions = {refusal: function for refusal, _, function in CONTROLS}
    functions.update(dict(SEQUENCES))
    functions['mutations'] = lambda co, variant: save(out / 'mutations.json', demonstrate_bypass(co))
    unknown = [name for name in names if name not in functions]
    assert not unknown, f'unknown controls: {unknown}'
    with tempfile.TemporaryDirectory(prefix='pw-build-refusals-', dir='/private/tmp') as temporary:
        co = Checkout(Path(temporary), identity, out)
        control_none(co, 'full')
        for name in names:
            functions[name](co, 'full')
            print(f'selected/{name}: completed', flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[3] == '--only':
        run_selected(Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[4].split(','))
    else:
        test_build_refusals(Path(sys.argv[1]).resolve(), sys.argv[2])
