"""Drive the unchanged build script through every refusal the manifest lists, with real toolchains and signatures.

One disposable checkout of the working tree serves every control. A control
arranges one fault beside the boundary the refusal guards: a builder the
script cannot confirm as native, an environment the script cannot build in, a
held checkout lock, a stamp that is missing,
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
import stat
import subprocess
import sys
import tempfile
import textwrap
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
import build_provenance as prov
import cargo_config
import checkout_lock
import shim_probe
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

def hook(label, tool, actions=(), *, when='after', respond=None, append=None, **match):
    entry = dict(label=label, tool=tool, when=when, match=match, actions=list(actions))
    if respond is not None:
        entry['respond'] = respond
    if append is not None:
        entry['append'] = list(append)
    return entry


def delete(path):
    return dict(op='delete', path=str(path))


def move(path, to):
    return dict(op='move', path=str(path), to=str(to))


def copy(source, path):
    return {'op': 'copy', 'from': str(source), 'path': str(path)}


def replace(source, path):
    """A new file with the current time renamed over the path, never a write into the existing file."""
    return {'op': 'replace', 'from': str(source), 'path': str(path)}


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


def kill_self():
    return dict(op='kill_self')


def signal_owner(lock, name):
    """Signal the lock's outermost owner, named by the pid its owner record carries."""
    return dict(op='signal_owner', lock=str(lock), signal=name)


def spawn_holder(report, release):
    """A protected grandchild beyond the wrapper, holding the passed lock descriptors until release exists."""
    return dict(op='spawn_holder', path=str(report), release=str(release))


def probe_lock(lock, report):
    return dict(op='probe_lock', lock=str(lock), path=str(report))


def symlink(path, to):
    return dict(op='symlink', path=str(path), to=str(to))


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
                                      'DEVELOPER_DIR', 'SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE', 'PW_CHECKOUT_LOCK_FD',
                                      'PW_CHECKOUT_LOCK_ROOT', 'PW_CHECKOUT_LOCK_NONCE', 'PW_CHECKOUT_LOCK_CHANNEL')}
        self.base_env = {k: v for k, v in self.base_env.items() if not k.startswith(checkout_lock.WITNESS_PREFIX)}
        self.base_env.update(PW_PYTHON=sys.executable, PYTHONCOERCECLOCALE="0")
        # Canaries: an unrelated environment value and every wrapped tool's stderr; no record may carry them.
        self.canary = 'PW_CANARY_' + os.urandom(8).hex()
        self.base_env['PW_UNRELATED_CANARY'] = self.canary
        self.builddir = self.root / 'builddir'
        self.target = self.root / prov.TRIPLE_RELEASE   # the shipped Cargo outputs
        self.host_release = self.root / prov.RELEASE    # Cargo's build scripts and procedural macros
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
        # Prepared once and kept unchanged through every run that uses them, the mutation stages included.
        self.unreadable_arm64 = None
        self.contained_unreadable_arm64 = None

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
              pass_fds=(), claim=None, stderr_canary=True, holder_alive=False, argv=None):
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
        status, stdout, stderr = command(case / 'build', argv or ['bash', self.root / 'build.sh'], cwd=self.root, env=environment,
                                         pass_fds=pass_fds)
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

    def forbidden(self, name):
        """A real Mach-O outside the output target, linked with the selected SDK at the plist's minimum so the minimum and
        SDK checks would pass it: thin x86_64, thin arm64e, universal arm64/x86_64, a one-slice fat container of an arm64
        executable, or a truncated arm64 executable. Its container and architectures are observed here, independently."""
        path = self.work / f'forbidden-{name}'
        if not path.exists():
            source = self.work / 'forbidden.c'
            source.write_text('int main(void) { return 0; }\n')
            clang = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', f'-mmacosx-version-min={self.minimum}', str(source)]
            arm64 = self.work / 'forbidden-arm64'
            if not arm64.exists():
                subprocess.run([*clang, '-arch', 'arm64', '-o', str(arm64)], check=True, capture_output=True, timeout=120)
            if name in ('x86_64', 'arm64e'):
                subprocess.run([*clang, '-arch', name, '-o', str(path)], check=True, capture_output=True, timeout=120)
            elif name == 'universal':
                subprocess.run([*clang, '-arch', 'arm64', '-arch', 'x86_64', '-o', str(path)], check=True, capture_output=True, timeout=120)
            elif name == 'one-slice-fat':
                subprocess.run(['/usr/bin/lipo', '-create', str(arm64), '-output', str(path)], check=True, capture_output=True, timeout=60)
            elif name == 'truncated':
                path.write_bytes(arm64.read_bytes()[:100])
            else:
                raise ValueError(name)
            path.chmod(0o755)
        with path.open('rb') as stream:
            magic = stream.read(4).hex()
        listed = subprocess.run(['/usr/bin/lipo', '-archs', str(path)], capture_output=True, text=True, timeout=60)
        observed = dict(path=str(path), magic=magic, lipo_status=listed.returncode, architectures=listed.stdout.split())
        equipment = self.out / f'{self.prefix}forbidden-outputs.json'
        known = json.loads(equipment.read_text()) if equipment.exists() else {}
        known[name] = observed
        save(equipment, known)
        return path

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
    for name in ('cargo_release', 'cargo_target_release'):
        release = build.record['configuration']['build_directories'][name]
        assert release['state'] in ('created', 'reused') and not (release['replaced_by_fresh_mode'] and release['state'] == 'reused'), release
    # The output target: every shipped output, at every stage the build checked it, and in the record, from the bytes.
    for output in build.record['outputs']:
        assert (output['container'], output['architectures'], output['platform']) == ('thin', ['arm64'], '1'), output
        assert subprocess.check_output(['/usr/bin/lipo', '-archs', str(build.app / output['rel_path'])], text=True).split() == ['arm64']
    assert build.record['configuration']['output_target']['cargo_triple'] == prov.TRIPLE
    assert build.record['toolchain']['rustc']['selection']['target']['triple'] == prov.TRIPLE
    stages = build.session['output_check']
    assert set(stages) == set(prov.OUTPUT_STAGES) and not any(stage['problems'] for stage in stages.values()), stages
    assert {Path(path).name for path in stages['cargo']['outputs']} == set(CARGO_BINS)
    if variant == 'partial':
        # A partial bundle stays incomplete for the full inspector and still satisfies the output target.
        report = artifact.inspect(build.app)
        assert not [e for e in report['errors'] if e['code'] == 'output_target'], report['errors']
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


NATIVE_REFUSAL = 'this build runs only natively on Apple Silicon (hw.optional.arm64={arm64}, sysctl.proc_translated={translated})'
UNREADABLE_ARM64 = NATIVE_REFUSAL.format(arm64='<empty>', translated='0')


def cache_inventory(root):
    """The session, the stamp and the cache directories two levels deep, by kind, size, inode and modification time,
    observed without the build's helpers: a write, a replacement or a removal shows."""
    out = {}
    for relative in ('builddir', 'controller/target'):
        top = root / relative
        for path in [top, *(top.glob('*') if top.is_dir() else ()), *(top.glob('*/*') if top.is_dir() else ())]:
            try:
                info = path.lstat()
            except FileNotFoundError:
                out[str(path.relative_to(root))] = None
                continue
            out[str(path.relative_to(root))] = [stat.S_IFMT(info.st_mode), info.st_size, info.st_ino, info.st_mtime_ns]
    for relative in (SESSION, STAMP):
        path = root / relative
        out[relative + ':sha256'] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return out


def unreadable_arm64_profile(co):
    """A sandbox profile that only makes hw.optional.arm64 unreadable, checked once before use: inside it a shell's read
    exits zero and prints nothing while sysctl.proc_translated still reads 0."""
    if co.unreadable_arm64 is None:
        profile = co.work / 'unreadable-arm64.sb'
        profile.write_text('(version 1)(allow default)' + shim_probe.UNREADABLE_ARM64 + '\n')
        prefix = ['/usr/bin/sandbox-exec', '-f', str(profile)]
        observed = {}
        for name, expected in shim_probe.SYSCTL_EXPECTED['sysctl_inside'].items():
            result = subprocess.run(prefix + ['/bin/bash', '-c', shim_probe.SYSCTL_SHELL, 'sysctl-probe', name],
                                    capture_output=True, text=True, timeout=30)
            observed[name] = dict(status=result.returncode, stdout=result.stdout, stderr=result.stderr)
            assert (result.returncode, result.stdout) == (0, expected), ('the profile does not give the expected read', name, observed)
        save(co.out / 'unreadable-arm64-profile.json', dict(profile=profile.read_text(), observed=observed))
        co.unreadable_arm64 = prefix
    return co.unreadable_arm64


def contained_unreadable_arm64(co):
    """The shim-probe containment with the fixed unreadable-arm64 rule added by the helper, gated by the helper before use."""
    if co.contained_unreadable_arm64 is None:
        co.contained_unreadable_arm64 = shim_probe.prepare(co.work / 'unreadable-arm64-contained', extra_rules=[shim_probe.UNREADABLE_ARM64])
    return co.contained_unreadable_arm64


def refused_by_builder(build, caches, lock, record):
    """The native builder refusal and nothing after it: no usage, banner or other refusal, no wrapped tool call (version
    probes included), the previous distribution and the caches as they were, and the independent holder's lock as it was."""
    check(build, 2, UNREADABLE_ARM64)
    assert build.stdout == '', (build.name, build.stdout[-2000:])
    assert build.stderr.strip().splitlines() == ['ERROR: ' + UNREADABLE_ARM64], (build.name, build.stderr[-2000:])
    assert build.receipts == [], (build.name, build.receipts)
    preserved(build)
    assert cache_inventory(build.root) == caches, (build.name, 'the refusal changed the session or a cache')
    assert lock.stat().st_ino == record[0] and lock.read_bytes() == record[1], (build.name, 'the holder lock was replaced or rewritten')
    assert not lock_free(build.root), (build.name, 'the independent holder lost the lock')
    assert not shim_probe.installation_requests(build.output), (build.name, build.output[-2000:])


def control_unconfirmed_machine(co, variant):
    """With hw.optional.arm64 unreadable (the read exits zero and prints nothing) and sysctl.proc_translated reading 0,
    the unchanged script refuses before anything else runs, while an independent holder keeps the checkout lock: the
    refusal precedes the lock front end, which would report the busy lock. Under the same unreadable read, the builder
    refusal also wins over --help, an unknown argument, a bad knob, a missing tracked input and an invalid SDKROOT; the
    invalid SDK runs under the helper's validated containment with the same rule, so a displaced guard meets the SDK
    refusal there without reaching an installer. This exercises the empty-value path only: an arm64 value of 0 and a
    probe's nonzero exit rest on the guard's code, and no Intel Mac is involved."""
    plain = unreadable_arm64_profile(co)
    contained = contained_unreadable_arm64(co)
    script = str(co.root / 'build.sh')
    lock = co.root / 'tests/.checkout.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(fd, 0)
        os.write(fd, b'{"pid": 0, "started_at_unix_ms": 0, "nonce": "native-builder-control"}\n')
        record = (os.fstat(fd).st_ino, lock.read_bytes())
        caches = cache_inventory(co.root)
        # Valid knobs, arguments, tracked inputs and SDK selection: only the builder check and the held lock stand ahead.
        build = co.build('native_builder_required-lock', variant, argv=plain + ['/bin/bash', script], holder_alive=True)
        refused_by_builder(build, caches, lock, record)
        invalid = '/private/tmp/pw-no-such-sdk-' + os.urandom(4).hex()
        build = co.build('native_builder_required-invalid_sdk', variant, env=dict(SDKROOT=invalid),
                         argv=contained + ['/bin/bash', script], holder_alive=True)
        refused_by_builder(build, caches, lock, record)
        for label, args, env in (('help', ['--help'], {}), ('unknown_argument', ['--bogus'], {}),
                                 ('knob', [], dict(BUILD_XPC='2')), ('missing_tree_input', [], {})):
            parked = co.keep_aside('Info.plist') if label == 'missing_tree_input' else None
            try:
                build = co.build(f'native_builder_required-{label}', variant, env=env, argv=plain + ['/bin/bash', script, *args],
                                 holder_alive=True)
            finally:
                if parked is not None:
                    co.restore_aside('Info.plist')
            refused_by_builder(build, caches, lock, record)
    finally:
        os.close(fd)
    assert lock_free(co.root)
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


CLAIM_FD, CLAIM_ROOT, CLAIM_NONCE, CLAIM_CHANNEL = checkout_lock.ENV_FD, checkout_lock.ENV_ROOT, checkout_lock.ENV_NONCE, checkout_lock.ENV_CHANNEL


def unclaimed_env():
    """This process's environment without the claim the dispatcher passed for the real checkout."""
    return {k: v for k, v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}


def wait_for(condition, timeout=120, message='condition'):
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, f'timed out waiting for {message}'
        time.sleep(0.05)


def reread(co, build, variant):
    """An orphaned build keeps writing after its owner's death; read its output again once the lock is free."""
    case = co.out / f'{co.prefix}{variant}-{build.name}' / 'build'
    wait_for(lambda: lock_free(co.root), message=f'{build.name}: the orphaned build to exit')
    build.stdout = (case / 'stdout').read_text(errors='replace')
    build.stderr = (case / 'stderr').read_text(errors='replace')
    return build


def tree_snapshot(root):
    """Every path below root with its kind and, for files, its hash and modification time: creation, change and removal show."""
    out = {}
    for path in sorted(root.rglob('*')):
        info = path.lstat()
        relative = str(path.relative_to(root))
        if path.is_symlink():
            out[relative] = ['symlink', os.readlink(path)]
        elif path.is_dir():
            out[relative] = ['dir']
        else:
            out[relative] = ['file', hashlib.sha256(path.read_bytes()).hexdigest(), info.st_mtime_ns]
    return out


def control_lock_claim_invalid(co, variant):
    """A claim without a live owner's handoff is refused at verification, before any check, write or tool; a real owner's
    hold, record and inode are unchanged; and a build whose owner is killed admits no further helper."""
    lock = co.root / 'tests/.checkout.lock'
    session = co.root / SESSION
    kept = session.read_bytes() if session.exists() else None
    nonce = 'f' * 32
    builds = []

    def refused(build, needle):
        check(build, 2, 'checkout lock claim is not verified', present=('Verifying the checkout lock',),
              absent=('Checking limits documentation', 'Build stamp', 'Building Rust'))
        assert needle in build.stderr, (build.name, needle, build.stderr[-1500:])
        assert not build.receipts, build.receipts
        assert (session.read_bytes() if session.exists() else None) == kept, f'{build.name}: a refused claim wrote the session'
        preserved(build)
        builds.append(build)

    # A claim left over from an earlier owner names descriptors that are not open here.
    refused(co.build('lock_claim_invalid-stale', variant, claim={CLAIM_ROOT: str(co.root), CLAIM_NONCE: nonce, CLAIM_CHANNEL: '250',
                                                                 CLAIM_FD: '251'}), 'is not open in this process')
    # The pre-handoff form of a claim, a descriptor number without an owner channel, is malformed.
    refused(co.build('lock_claim_invalid-descriptor-only', variant, claim={CLAIM_FD: '3', CLAIM_ROOT: str(co.root), CLAIM_NONCE: nonce}),
            'not set')
    # The review's counterexample: an unheld descriptor on the lock inode while the lock is free, with the nonce of the
    # record a released owner left. Re-locking that descriptor would have taken the free lock and passed as a hold;
    # admission refuses it and takes no hold.
    released, record = checkout_lock.acquire(co.root)
    os.close(released)
    unheld = os.open(lock, os.O_RDWR)
    os.set_inheritable(unheld, True)
    try:
        build = co.build('lock_claim_invalid-unheld', variant, pass_fds=(unheld,),
                         claim={CLAIM_ROOT: str(co.root), CLAIM_NONCE: record['nonce'], CLAIM_CHANNEL: str(unheld), CLAIM_FD: str(unheld)})
    finally:
        os.close(unheld)
    refused(build, 'is not an owner channel')
    # While a real owner holds the lock: another open on its inode, a wrong nonce over the owner's real channel and another
    # worktree's claim over it.
    with checkout_lock.owned(co.root, env=unclaimed_env()) as scope:
        inode, record = lock.stat().st_ino, lock.read_bytes()
        claim = scope.child_env({})
        separate = os.open(lock, os.O_RDWR)
        os.set_inheritable(separate, True)
        try:
            build = co.build('lock_claim_invalid-separate', variant, holder_alive=True, pass_fds=(separate,),
                             claim=dict(claim, **{CLAIM_CHANNEL: str(separate), CLAIM_FD: str(separate)}))
        finally:
            os.close(separate)
        refused(build, 'is not an owner channel')
        refused(co.build('lock_claim_invalid-nonce', variant, holder_alive=True, pass_fds=scope.pass_fds(),
                         claim=dict(claim, **{CLAIM_NONCE: nonce})), 'another acquisition')
        refused(co.build('lock_claim_invalid-checkout', variant, holder_alive=True, pass_fds=scope.pass_fds(),
                         claim=dict(claim, **{CLAIM_ROOT: '/private/tmp'})), 'another checkout')
        assert not lock_free(co.root) and (lock.stat().st_ino, lock.read_bytes()) == (inode, record), 'a refused claim changed the real hold'
    assert lock_free(co.root)
    # The owner killed mid-build: the build's own processes keep the lock while they run, but the next helper's admission
    # is refused, so fresh mode removes nothing; the lock is free once the orphaned build exits.
    assert (co.builddir / 'build.ninja').exists() and co.target.is_dir()
    gone = co.build('lock_claim_invalid-owner-gone', variant, fresh='1', holder_alive=True,
                    hooks=[hook('kill-owner', 'cargo', [signal_owner(lock, 'SIGKILL')], first='metadata')])
    fired_once(gone, 'kill-owner')
    assert gone.status == -signal.SIGKILL, ('the owner was not the process killed', gone.status)
    reread(co, gone, variant)
    assert 'checkout lock claim is not verified: the owner of this claim is gone' in gone.stderr, gone.stderr[-1500:]
    assert 'Replacing the build caches' in gone.stdout and 'Building Rust' not in gone.stdout, gone.stdout[-1500:]
    assert (co.builddir / 'build.ninja').exists() and co.target.is_dir(), 'an unadmitted helper removed a cache'
    assert not gone.calls('cargo', 'build')
    preserved(gone)
    builds.append(gone)
    return builds[0]


def control_environment_witness_missing(co, variant):
    """Neither the CLI owner nor session-start writes with an absent witness."""
    session = co.root / SESSION
    kept = session.read_bytes() if session.exists() else None
    cli = ['/usr/bin/python3', '-B', str(co.root / 'tests/lib/checkout_lock.py'), '--root', str(co.root), '--',
           '/bin/bash', str(co.root / 'build.sh')]
    build = co.build('environment_witness_missing', variant, argv=cli)
    check(build, 2, 'environment witness missing for SDKROOT', absent=('Verifying the checkout lock',))
    assert not build.receipts and (session.read_bytes() if session.exists() else None) == kept
    preserved(build)
    python_only = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(co.root / 'tests/lib')!r})
        import checkout_lock
        with checkout_lock.owned({str(co.root)!r}) as scope:
            sys.exit(scope.supervise(['/bin/bash', {str(co.root / 'build.sh')!r}]))
    """)
    nested = co.build('environment_witness_missing-nested', variant, argv=[sys.executable, '-B', '-c', python_only])
    check(nested, 2, 'environment witness missing for SDKROOT', present=('Build stamp',), absent=('Supported macOS',))
    assert not nested.receipts and (session.read_bytes() if session.exists() else None) == kept
    preserved(nested)
    return build


def control_environment_witness_changed(co, variant):
    """A deliberate shim start changes CPATH; the owner refuses before taking the lock."""
    session = co.root / SESSION
    kept = session.read_bytes() if session.exists() else None
    # The owner compares SDKROOT first and the shim inserts one, so a witness of
    # the caller's own environment would be refused for SDKROOT. Witness what the
    # shim gives its Python under the same environment instead, except CPATH,
    # which the caller left unset: the refusal then names CPATH. A caller-set
    # SDKROOT would not isolate it, since the shim then inserts no CPATH here.
    names = ('SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')
    probe = 'import json, os; print(json.dumps({n: os.environ.get(n) for n in ' + repr(names) + '}))'
    observed = json.loads(subprocess.check_output(['/usr/bin/python3', '-B', '-c', probe],
                                                  env=co.base_env, text=True))
    assert observed['CPATH'] is not None, 'the shim negative control did not change CPATH'
    witnessed = {'PW_ENV_WITNESS_' + name: 'u' if value is None else 's' + value
                 for name, value in observed.items()}
    witnessed['PW_ENV_WITNESS_CPATH'] = 'u'
    cli = ['/usr/bin/python3', '-B', str(co.root / 'tests/lib/checkout_lock.py'), '--root', str(co.root), '--',
           '/bin/bash', str(co.root / 'build.sh')]
    build = co.build('environment_witness_changed', variant, argv=cli, env=witnessed)
    check(build, 2, 'environment witness differs for CPATH', absent=('Verifying the checkout lock',))
    assert not build.receipts and (session.read_bytes() if session.exists() else None) == kept
    preserved(build)
    return build


def control_cache_path_unsafe(co, variant):
    """A symlink at any component of builddir/, controller/target/, its release/, its output triple's directory or that
    directory's release/, or at the session destination, refuses at
    admission before the session or any cache is written and before any tool runs, in incremental and fresh mode, and
    nothing outside the checkout is created, changed or removed. A path replaced after one helper admitted it is refused
    by the next helper's admission. A missing controller/target/ is created beneath the admitted controller/."""
    outside = co.work / 'outside-caches'
    if outside.exists():
        shutil.rmtree(outside)
    for relative, text in (('target/pw-build-session.json', '{"outside": "session"}\n'), ('target/release/keep', 'outside release\n'),
                           ('target/debug/keep', 'outside debug\n'), ('triple/release/keep', 'outside triple release\n'),
                           ('builddir/build.ninja', '# outside\n'),
                           ('builddir/keep', 'outside builddir\n'), ('session.json', 'outside session file\n')):
        (outside / relative).parent.mkdir(parents=True, exist_ok=True)
        (outside / relative).write_text(text)
    expected = tree_snapshot(outside)
    components = (('controller/target', outside / 'target'), ('controller/target/release', outside / 'target/release'),
                  (prov.TRIPLE_DIR, outside / 'triple'), (prov.TRIPLE_RELEASE, outside / 'triple/release'),
                  ('builddir', outside / 'builddir'), (SESSION, outside / 'session.json'))
    build = None
    for relative, target in components:
        for fresh in ('0', '1'):
            name = f'cache_path_unsafe-{relative.replace("/", "_")}-{"fresh" if fresh == "1" else "incremental"}'
            path = co.root / relative
            parked = co.keep_aside(relative) if os.path.lexists(path) else None
            path.symlink_to(target)
            try:
                build = co.build(name, variant, fresh=fresh)
            finally:
                path.unlink()
                if parked is not None:
                    co.restore_aside(relative)
            # The outside tree first: with admission disabled, this is what the original defect overwrote.
            observed = tree_snapshot(outside)
            save(co.out / f'{co.prefix}{variant}-{name}' / 'outside.json', dict(expected=expected, observed=observed))
            assert observed == expected, (name, 'a write, change or removal went through the symlink',
                                          sorted(k for k in set(observed) | set(expected) if observed.get(k) != expected.get(k))[:5])
            check(build, 2, '(nothing was written or removed)', present=('Build stamp',),
                  absent=('Supported macOS', 'Checking the native build directory', 'Replacing the build caches', 'Building Rust'))
            assert ('is a symlink' if relative != SESSION else 'the destination is unsafe') in build.stderr, build.stderr[-1000:]
            assert not build.receipts, build.receipts
            preserved(build)
    # A path replaced between one helper's admission and the next helper: fresh mode's own admission refuses it.
    parked_release = co.work / 'parked-release'
    if parked_release.exists():
        shutil.rmtree(parked_release)
    replaced = co.build('cache_path_unsafe-replaced-after-admission', variant, fresh='1',
                        hooks=[hook('replace-release', 'cargo', [move(co.target, parked_release), symlink(co.target, outside / 'target/release')],
                                    first='metadata')])
    try:
        fired_once(replaced, 'replace-release')
        check(replaced, 2, f'{prov.TRIPLE_RELEASE} is a symlink', present=('Replacing the build caches',), absent=('Building Rust',))
        assert tree_snapshot(outside) == expected, 'fresh mode removed through a replaced path'
        assert (parked_release / 'policy-witness').exists(), 'the replaced directory was removed through its old name'
        preserved(replaced)
    finally:
        if co.target.is_symlink():
            co.target.unlink()
        if parked_release.exists():
            shutil.move(str(parked_release), str(co.target))
    # An owned missing path: controller/target/ is created beneath the admitted controller/ and the build packages.
    co.keep_aside('controller/target')
    try:
        created = co.build('cache_path_unsafe-missing-target', variant)
        passing(co, created, variant)
        assert created.session['admission']['created'] == ['controller/target'], created.session['admission']
    finally:
        shutil.rmtree(co.parked('controller/target'), ignore_errors=True)
    assert tree_snapshot(outside) == expected
    return build


def lifetime_kill(co, variant, name, bin_dir=None):
    """The owner, the build's shell and the meson wrapper killed in turn while a holder the wrapper started runs beyond it."""
    lock = co.root / 'tests/.checkout.lock'
    report, release = co.work / f'{name}-holder.json', co.work / f'{name}-holder.release'
    for path in (report, release):
        path.unlink(missing_ok=True)
    killed = co.build(name, variant, holder_alive=True, bin_dir=bin_dir,
                      hooks=[hook('kill-all', 'meson', [spawn_holder(report, release), signal_owner(lock, 'SIGKILL'), kill_parent(), kill_self()],
                                  when='before', first='compile')])
    wait_for(lambda: report.exists() and report.read_text().endswith('}'), message='the holder report')
    holder = json.loads(report.read_text())
    wait_for(lambda: not alive(holder['wrapper']), message='the wrapper to die')
    return killed, holder, release


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def battery(co, name):
    """A competing managed test execution in the disposable checkout: one offline case through the public dispatcher."""
    out = co.out / f'{co.prefix}battery-{name}'
    # The dispatcher running this control passes its own settings; a battery started here must not inherit them.
    env = {k: v for k, v in co.base_env.items() if not k.startswith('PW_TEST_') and k not in ('PW_APP_DIR', 'PW_BIN', 'PW_BIN_PATH')}
    env.update(PW_TEST_OUT_DIR=f'tests/out/runs/{name}', PYTHONDONTWRITEBYTECODE='1')
    status, stdout, stderr = command(out, ['bash', co.root / 'tests/run.sh', '--case', 'dispatcher/accounting_controls'],
                                     cwd=co.root, env=env, timeout=600)
    return status, stdout + stderr


def control_lock_lifetime(co, variant):
    """How long the hold lasts, observed from outside every owner: a protected holder beyond a killed owner, shell and wrapper
    keeps the lock, so a competing build, battery and standalone Cargo command refuse until it exits and succeed after; a
    wrapper that drops the passed descriptor fails the same control; SIGINT and SIGTERM reach the build's process group
    and the lock is free once it has stopped; the real Cargo, Meson and Ninja pass the descriptor to the compilers; a nested
    build and a nested owned command succeed under one acquisition; the lock is held through packaging; and an independent
    worktree is never excluded."""
    lock = co.root / 'tests/.checkout.lock'
    observations = {}
    front_end = ['/bin/bash', str(co.root / 'tests/lib/checkout_lock.sh'), '--root', str(co.root), '--']
    other = co.work / 'other-worktree'
    if not other.exists():
        (other / 'tests/lib').mkdir(parents=True)
        for name in ('checkout_lock.py', 'checkout_lock.sh', 'python_start.sh', 'sdk_guard.sh'):
            shutil.copy2(co.root / 'tests/lib' / name, other / 'tests/lib' / name)
    other_front_end = ['/bin/bash', str(other / 'tests/lib/checkout_lock.sh'), '--root', str(other), '--']
    killed, holder, release = lifetime_kill(co, variant, 'lifetime-killed')
    try:
        assert killed.status == -signal.SIGKILL, ('the owner was not the process killed', killed.status)
        observations['held_after_kill'] = not lock_free(co.root)
        assert observations['held_after_kill'], 'the killed owner, shell and wrapper released the hold the holder needs'
        busy = co.build('lifetime-competing-build', variant, holder_alive=True)
        check(busy, 2, 'checkout busy', absent=('Verifying the checkout lock',))
        assert not busy.receipts
        status, text = battery(co, 'lifetime-competing')
        observations['battery_refused'] = status == 2 and 'checkout busy' in text
        assert observations['battery_refused'], (status, text[-1000:])
        cargo = subprocess.run([*front_end, 'cargo', '--version'], env=co.base_env, capture_output=True, text=True, timeout=60)
        observations['standalone_cargo_refused'] = cargo.returncode == 2 and 'checkout busy' in cargo.stderr
        assert observations['standalone_cargo_refused'], (cargo.returncode, cargo.stderr)
        independent = subprocess.run([*other_front_end, '/usr/bin/true'], env=co.base_env, capture_output=True, text=True, timeout=60)
        observations['independent_worktree'] = independent.returncode
        assert independent.returncode == 0, independent.stderr
        assert alive(holder['holder'])
    finally:
        release.touch()
    wait_for(lambda: not alive(holder['holder']), message='the holder exit')
    observations['released_after_last_exit'] = lock_free(co.root)
    assert observations['released_after_last_exit']
    status, text = battery(co, 'lifetime-after')
    observations['battery_after'] = status
    assert status == 0, text[-2000:]
    cargo = subprocess.run([*front_end, 'cargo', '--version'], env=co.base_env, capture_output=True, text=True, timeout=60)
    observations['standalone_cargo_after'] = cargo.returncode
    assert cargo.returncode == 0, (cargo.returncode, cargo.stderr)
    # The same control with a wrapper that drops the descriptor (Python's default) observes a free lock while the holder runs.
    dropping = co.work / 'bin-dropping'
    if not dropping.exists():
        dropping.mkdir()
        text = WRAPPER.read_text()
        for old in ('pass_fds=lock_fds(), start_new_session=True', 'subprocess.run(executed, pass_fds=lock_fds())'):
            assert text.count(old) == 1, old
        text = text.replace('pass_fds=lock_fds(), start_new_session=True', 'start_new_session=True')
        text = text.replace('subprocess.run(executed, pass_fds=lock_fds())', 'subprocess.run(executed)')
        for name in WRAPPED:
            (dropping / name).write_text(text)
            (dropping / name).chmod(0o755)
    dropped, dropped_holder, dropped_release = lifetime_kill(co, variant, 'lifetime-dropped', bin_dir=dropping)
    try:
        observations['dropped_held_after_kill'] = not lock_free(co.root)
        assert not observations['dropped_held_after_kill'], 'a wrapper dropping the descriptor still passed the lifetime control'
        assert alive(dropped_holder['holder'])
    finally:
        dropped_release.touch()
    wait_for(lambda: not alive(dropped_holder['holder']), message='the dropped holder exit')
    # Orderly cancellation at the owner: the signal reaches the build's process group, the owner returns its status after
    # the group has stopped, nothing is assembled and the lock is free.
    for name, code in (('SIGTERM', 128 + signal.SIGTERM), ('SIGINT', 128 + signal.SIGINT)):
        cancelled = co.build(f'lifetime-{name}', variant, hooks=[hook(f'signal-{name}', 'cargo', [signal_owner(lock, name)], when='before', first='build')])
        observations[f'{name}_status'] = cancelled.status
        assert cancelled.status == code, (name, cancelled.status, cancelled.stderr[-1000:])
        assert 'Assembling app bundle' not in cancelled.stdout
        assert lock_free(co.root), f'{name}: the lock outlived the cancelled build'
        preserved(cancelled)
    # The real Cargo and Meson/Ninja pass the descriptor to the compilers they run, a nested build and a nested owned command
    # succeed under the outer acquisition, the lock stays held through packaging, and a held independent worktree excludes
    # nothing here.
    real_cc = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '-f', 'clang'], text=True).strip()
    real_rustc = subprocess.check_output(['rustup', 'which', 'rustc'], text=True).strip() if shutil.which('rustup') else shutil.which('rustc')
    cc = co.forwarding('cc-lifetime', real_cc, mode='direct')
    rustc = co.forwarding('rustc-lifetime', real_rustc, mode='direct')
    probe_report = co.work / 'packaging-probe'
    probe_report.unlink(missing_ok=True)
    other_release = co.work / 'other.release'
    other_release.unlink(missing_ok=True)
    other_holder = subprocess.Popen([*other_front_end, '/bin/sh', '-c', f'while [ ! -e {shlex.quote(str(other_release))} ]; do sleep 0.05; done'],
                                    env=co.base_env)
    try:
        wait_for(lambda: not lock_free(other), message='the other worktree hold')
        script = (f'/bin/bash {shlex.quote(str(co.root / "build.sh"))} && /bin/bash {shlex.quote(str(co.root / "tests/lib/checkout_lock.sh"))} '
                  f'--root {shlex.quote(str(co.root))} -- /usr/bin/python3 -B {shlex.quote(str(co.root / "tests/lib/checkout_lock.py"))} '
                  f'--verify --root {shlex.quote(str(co.root))} && echo nested-owned-command-admitted')
        nested = co.build('lifetime-nested', variant, fresh='1', env=dict(CC=str(cc), RUSTC=str(rustc)),
                          argv=[*front_end, '/bin/bash', '-c', script],
                          hooks=[hook('probe-packaging', 'codesign', [probe_lock(lock, probe_report)], last=str(co.target / 'sandbox-log-observer'))])
    finally:
        other_release.touch()
        other_holder.wait(timeout=60)
    passing(co, nested, variant)
    assert 'nested-owned-command-admitted' in nested.stdout
    observations['held_through_packaging'] = probe_report.read_text().split()
    assert observations['held_through_packaging'] == ['held'], observations['held_through_packaging']
    assert nested.session['lock_nonce'] == json.loads(lock.read_text())['nonce'], 'the nested build did not use the outer acquisition'
    inode = lock.stat().st_ino
    compiled = [r for r in nested.forward if r['kind'] == 'compile']
    for wrapper in ('cc-lifetime', 'rustc-lifetime'):
        receipts = [r for r in compiled if r['wrapper'] == wrapper]
        assert receipts, f'{wrapper} compiled nothing'
        missing = [r['args'][:4] for r in receipts if not (r.get('lock') or {}).get('open') or r['lock'].get('inode') != inode]
        assert not missing, (wrapper, 'a compiler ran without the lock descriptor', missing[:3])
    observations['compilers_holding'] = {w: len([r for r in compiled if r['wrapper'] == w]) for w in ('cc-lifetime', 'rustc-lifetime')}
    # A standalone Cargo command holding the lock excludes a build until it exits.
    cargo_release = co.work / 'cargo.release'
    cargo_release.unlink(missing_ok=True)
    standalone = subprocess.Popen([*front_end, '/bin/sh', '-c', f'cargo --version >/dev/null && while [ ! -e {shlex.quote(str(cargo_release))} ]; do sleep 0.05; done'],
                                  env=co.base_env)
    try:
        wait_for(lambda: not lock_free(co.root), message='the standalone Cargo hold')
        excluded = co.build('lifetime-excluded-by-cargo', variant, holder_alive=True)
        check(excluded, 2, 'checkout busy')
        preserved(excluded)
    finally:
        cargo_release.touch()
        standalone.wait(timeout=60)
    assert standalone.returncode == 0, standalone.returncode
    assert lock_free(co.root)
    restored = co.build('lifetime-restore', variant, fresh='1')
    passing(co, restored, variant)
    save(co.out / f'{co.prefix}{variant}-lock-lifetime.json', observations)
    return restored


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
    assert not shim_probe.installation_requests(build.output), build.output[-2000:]
    shutil.copytree(fixture, co.out / f'{co.prefix}{variant}-sdk_unavailable' / 'sdk-fixture')
    preserved(build)
    return build


def fake_developer_dir(fixture):
    """An unconfigured developer directory, independent of Xcode/CLT layout.

    No /usr/bin tool shim runs with the fake DEVELOPER_DIR. The isolated SDK
    command may execute only xcrun and the helper's dscl check, cannot make Mach service lookups or write
    outside its own fixture. Its real configuration error drives the refusal;
    no SDK response or exit status is fabricated.
    """
    fake = fixture / 'unconfigured-developer'
    fake.mkdir(parents=True)
    prefix = shim_probe.prepare(fixture, exec_allowlist=['/usr/bin/xcrun'])
    env = dict(os.environ, DEVELOPER_DIR=str(fake))
    # prepare established successful execution. This separate refusal checks
    # the exec allowance; the SDK process then reports its real configuration error.
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


def control_shim_install_detector(co, variant):
    """Only this opt-in control deliberately makes a contained shim request installation."""
    fixture = co.out / 'shim-install-detector'
    fixture.mkdir()
    records = []
    for name, request in (('missing', str(fixture / 'missing.sdk')), ('empty', '')):
        case = fixture / name
        record = shim_probe.run(case, ['/usr/bin/python3', '-V'],
                                env=dict(shim_probe.base_environment(case), SDKROOT=request))
        records.append(record)
        assert record['complete'], record
        if name == 'missing':
            assert record['status'] != 0 and record['install_requests'], record
            assert 'no install could be requested' in record['stderr'], record
        else:
            assert record['status'] == 0 and not record['install_requests'], record
    # Unified-log delivery can lag the child. Keep the last raw query and bound
    # the wait; missing evidence fails this control, never the helper's gate.
    denials = []
    for attempt in range(10):
        time.sleep(1)
        status, stdout, stderr = command(fixture / f'log-{attempt}',
            ['/usr/bin/log', 'show', '--last', '1m', '--style', 'ndjson', '--predicate',
             f'eventMessage CONTAINS "{shim_probe.SERVICE}"'], cwd=fixture, env=co.base_env, timeout=60)
        assert status == 0, stderr
        events = [json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
        denials = shim_probe.install_denials(events, records)
        if denials:
            break
    save(fixture / 'denials.json', denials)
    assert any(d['pid'] == records[0]['pid'] for d in denials), 'missing PID-attributed installation-service denial'
    assert not any(d['pid'] == records[1]['pid'] for d in denials), denials
    return None


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
    # A version query that answers correctly and exits zero but floods stderr past the cap is a failed observation.
    co.forwarding('rustc-probe', real, mode='direct', label='P', flood_stderr=prov.PROBE_LIMIT + 1, stderr_canary=co.canary)
    flooded = co.build('probe_failed-stderr-overflow', variant, env=env)
    check(flooded, 2, 'required toolchain observation failed: rustc.command (output_overflow)',
          present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
    assert co.canary not in (co.root / SESSION).read_text()
    no_compiles(flooded)
    preserved(flooded)
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
    """Cargo's report naming a shipped executable at another path than the pinned one refuses before any copy. With the
    output directory and the output triple both on the command line, no Cargo setting moves the outputs (a lower-precedence
    x86_64 default is overridden, as the selection sequence shows), so the control edits Cargo's report, which is what the
    check reads: here it names the host release area, where an output built without --target would land."""
    messages = co.root / 'controller/target/pw-build-messages.jsonl'
    moved = co.host_release / 'policy-witness'
    build = co.build('cargo_artifact_elsewhere', variant,
                     hooks=[hook('report-elsewhere', 'cargo', [judge(messages, 'policy-witness', set=dict(executable=str(moved)))], first='build')])
    check(build, 2, f'cargo built policy-witness at {moved}, not at {co.target / "policy-witness"}; '
                    "a Cargo setting or Cargo's report moved it",
          present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
    fired_once(build, 'report-elsewhere')
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
    sentinels = {co.builddir / 'control-sentinel': 'native cache', co.target / 'control-sentinel': 'cargo cache',
                 co.host_release / 'control-sentinel': 'cargo host cache'}
    kept = {co.root / 'controller/target/debug/control-sentinel': 'host debug profile',
            co.root / prov.TRIPLE_DIR / 'debug/control-sentinel': 'triple debug profile',
            co.root / 'controller/target/x86_64-apple-darwin/release/control-sentinel': 'another triple'}
    for path, text in {**sentinels, **kept}.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    first = co.build('sequence-1-fresh', 'partial', env=env, fresh='1')
    passing(co, first, 'partial')
    assert all(not p.exists() for p in sentinels), 'fresh mode left a cache sentinel'
    assert all(p.read_text() == text for p, text in kept.items()), 'fresh mode removed another profile or triple'
    assert {k: v['removed'] for k, v in first.session['fresh']['replacement'].items()} == \
        {'builddir': True, 'cargo_release': True, 'cargo_target_release': True}, first.session['fresh']
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
    assert {k: v for k, v in stamp3['fields'].items() if not k.startswith('compilers.swift.') and k != 'output.swift_target'} == stamp1['fields'], \
        'extension changed another field'
    assert stamp3['fields']['output.swift_target'] == [f'arm64-apple-macosx{co.minimum}'], stamp3['fields']
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
    assert held_after_kill, 'killing the shell released the hold the orphaned compile carries'
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
    assert cargo_only.record['configuration']['build_directories']['cargo_target_release']['state'] == 'created'
    assert cargo_only.record['configuration']['build_directories']['cargo_release']['state'] == 'reused'
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
    build = co.build('replaced_output', variant, hooks=[hook('replace-cached', 'cargo', [replace(replacement, co.target / 'sbpl-check')], first='build')])
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
        for name in ('Makefile', 'tests/lib/sdk_guard.sh', 'tests/lib/python_start.sh', 'tests/lib/python.sh',
                     'tests/lib/release_preflight.py', 'tests/fixtures/docs/prose_baseline.json', 'tests/fixtures/docs/build_baseline.json'):
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


def cargo_configuration(co, files):
    """Write Cargo configuration files below the disposable checkout (the build's invocation directory); returns a remover."""
    written = []
    for relative, text in files.items():
        path = co.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        written.append(path)

    def remove():
        for path in written:
            path.unlink(missing_ok=True)
        for directory in sorted({p.parent for p in written}, key=lambda d: -len(d.parts)):
            if directory != co.root and directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
    return remove


def control_cargo_configuration_unresolved(co, variant):
    """A Cargo configuration the build cannot resolve (a missing required include, invalid TOML, an unsupported value type, a
    program not on Cargo's PATH) refuses before Cargo runs: at the stamp check in incremental mode, at Cargo admission in
    fresh mode, before either cache is removed."""
    build = None
    for label, files, needle in (
            ('required-include', {'.cargo/config.toml': 'include = ["absent.toml"]\n'}, 'required include'),
            ('malformed', {'.cargo/config.toml': '[build\n'}, 'not valid TOML'),
            ('value-type', {'.cargo/config.toml': '[build]\nrustc = ["/an", "array"]\n'}, 'not a string program path'),
            ('not-on-path', {'.cargo/config.toml': 'include = ["selection.toml"]\n', '.cargo/selection.toml': '[build]\nrustc-wrapper = "pw-absent-wrapper"\n'},
             'not on the PATH Cargo gives the compiler')):
        for fresh in ('0', '1'):
            remove = cargo_configuration(co, files)
            try:
                build = co.build(f'cargo_configuration_unresolved-{label}-{"fresh" if fresh == "1" else "incremental"}', variant, fresh=fresh)
            finally:
                remove()
            step = 'Admitting the Cargo output' if fresh == '1' else 'Checking the native build directory'
            check(build, 2, 'Cargo configuration cannot be resolved', present=(step,), absent=('Replacing the build caches', 'Building Rust'))
            assert needle in build.stderr, (label, build.stderr[-1000:])
            assert (co.builddir / 'build.ninja').exists() and co.target.is_dir(), 'a refusal removed a cache'
            no_compiles(build)
            preserved(build)
    return build


def control_cargo_environment_conflict(co, variant):
    """Cargo's [env] forcing a compiler input that differs from the build's selection (the deployment target or the SDK path)
    refuses before Cargo runs; forcing the build's own value is the valid neighbour and packages."""
    sdkroot = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
    respelled = str(Path(sdkroot).parent / 'MacOSX.sdk') if Path(sdkroot).name != 'MacOSX.sdk' else sdkroot + '/'
    build = None
    for label, entry, name in (('deployment', 'MACOSX_DEPLOYMENT_TARGET = { value = "26.1", force = true }', 'MACOSX_DEPLOYMENT_TARGET'),
                               ('sdk', f'SDKROOT = {{ value = "{respelled}", force = true }}', 'SDKROOT')):
        for fresh in ('0', '1'):
            remove = cargo_configuration(co, {'.cargo/config.toml': f'[env]\n{entry}\n'})
            try:
                build = co.build(f'cargo_environment_conflict-{label}-{"fresh" if fresh == "1" else "incremental"}', variant, fresh=fresh)
            finally:
                remove()
            check(build, 1, f"Cargo's [env] gives the compiler {name}=", absent=('Replacing the build caches', 'Building Rust'))
            assert 'conflicts with build policy' in build.stderr
            assert (co.builddir / 'build.ninja').exists() and co.target.is_dir()
            no_compiles(build)
            preserved(build)
    remove = cargo_configuration(co, {'.cargo/config.toml': f'[env]\nMACOSX_DEPLOYMENT_TARGET = {{ value = "{co.minimum}", force = true }}\n'})
    try:
        neighbour = co.build('cargo_environment_conflict-equal', variant)
    finally:
        remove()
    passing(co, neighbour, variant)
    assert neighbour.record['toolchain']['rustc']['selection']['env_entries']['MACOSX_DEPLOYMENT_TARGET']['applied'] is True
    return build


def control_cargo_judgment_unknown(co, variant):
    """Cargo's report for a shipped target with no literal boolean fresh judgment (null, missing, a string, a number, or a
    contradictory second message) refuses before Meson in both modes, naming the target."""
    messages = co.root / 'controller/target/pw-build-messages.jsonl'
    build = None
    for label, change in (('null', dict(set=dict(fresh=None))), ('missing', dict(unset=['fresh'])), ('string', dict(set=dict(fresh='false'))),
                          ('number', dict(set=dict(fresh=0))), ('contradictory', dict(duplicate=True, set=dict(fresh=True)))):
        for fresh in ('0', '1'):
            build = co.build(f'cargo_judgment_unknown-{label}-{"fresh" if fresh == "1" else "incremental"}', variant, fresh=fresh,
                             hooks=[hook(f'judge-{label}', 'cargo', [judge(messages, 'sbpl-check', **change)], first='build')])
            check(build, 2, "Cargo's report establishes no literal boolean fresh judgment for the admitted executable of sbpl-check (",
                  present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
            fired_once(build, f'judge-{label}')
            assert build.judgments()['sbpl-check']['status'] == 'unknown'
            no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
            preserved(build)
    return build


def control_cargo_selection_sequence(co, variant):
    """Compiler selection and flags through the real script with retained caches, Cargo's compilations as the oracle: an
    included file selecting a forwarding compiler by a relative path, a change to only that file refused reuse, a forced
    [env] PATH selecting another compiler (the review's counterexample), the encoded flags over RUSTFLAGS and target rules
    over build.rustflags each rebuilding with the winner recorded, and recovery without configuration."""
    real = subprocess.check_output(['rustup', 'which', 'rustc'], text=True).strip() if shutil.which('rustup') else shutil.which('rustc')
    tools = co.root / 'pw-selection-tools'
    first = co.forwarding('rustc-included-a', real, mode='direct', label='A', record_env=['MACOSX_DEPLOYMENT_TARGET', 'RUSTUP_TOOLCHAIN'])
    second = co.forwarding('rustc-included-b', real, mode='direct', label='B', record_env=['MACOSX_DEPLOYMENT_TARGET', 'RUSTUP_TOOLCHAIN'])
    tools.mkdir(exist_ok=True)
    for forwarder in (first, second):
        shutil.copy2(forwarder, tools / forwarder.name)
    include = {'.cargo/config.toml': 'include = ["pw-selection.toml"]\n'}
    remove = cargo_configuration(co, dict(include, **{'.cargo/pw-selection.toml': '[build]\nrustc = "pw-selection-tools/rustc-included-a"\n'}))
    try:
        selected = co.build('selection-1-included-fresh', variant, fresh='1')
        passing(co, selected, variant)
        rustc = selected.record['toolchain']['rustc']
        assert (rustc['source'], rustc['command']) == ('build.rustc', str(tools / 'rustc-included-a')), rustc
        assert rustc['selection']['programs']['rustc']['file'].endswith('.cargo/pw-selection.toml'), rustc['selection']
        compiled = {r['path'] for r in selected.forward if r['kind'] == 'compile' and '--crate-name' in r['args']}
        assert compiled == {str(tools / 'rustc-included-a')}, ('Cargo compiled with another compiler than the record names', compiled)
        assert json.loads(selected.stamp)['fields']['rustc.command'] == str(tools / 'rustc-included-a')
        # Only the included file changes: reuse is refused by the field that changed, and fresh mode recovers under B.
        (co.root / '.cargo/pw-selection.toml').write_text('[build]\nrustc = "pw-selection-tools/rustc-included-b"\n')
        refused = co.build('selection-2-included-changed', variant)
        check(refused, 1, 'rustc.command', present=('Checking the native build directory',), absent=BEFORE_CARGO)
        assert refused.stamp == selected.stamp
        recovered = co.build('selection-3-included-fresh-b', variant, fresh='1')
        passing(co, recovered, variant)
        assert {r['path'] for r in recovered.forward if r['kind'] == 'compile' and '--crate-name' in r['args']} == {str(tools / 'rustc-included-b')}
    finally:
        remove()
    # A forced [env] PATH puts another rustc first for every process Cargo starts.
    alternate = co.work / 'selection-alternate'
    alternate.mkdir(exist_ok=True)
    shutil.copy2(co.forwarding('rustc', real, mode='direct', label='PATH', record_env=['MACOSX_DEPLOYMENT_TARGET', 'RUSTUP_TOOLCHAIN']),
                 alternate / 'rustc')
    remove = cargo_configuration(co, {'.cargo/config.toml': f'[env]\nPATH = {{ value = "{alternate}:{co.base_env["PATH"]}", force = true }}\n'})
    try:
        refused = co.build('selection-4-env-path-reuse', variant)
        check(refused, 1, 'rustc.command', absent=BEFORE_CARGO)
        forced = co.build('selection-5-env-path-fresh', variant, fresh='1')
        passing(co, forced, variant)
        rustc = forced.record['toolchain']['rustc']
        assert rustc['command'] == str(alternate / 'rustc') and rustc['selection']['child_environment']['path_replaced_by_env'] is True, rustc
        receipts = [r for r in forced.forward if r['kind'] == 'compile' and '--crate-name' in r['args']]
        assert receipts and {r['path'] for r in receipts} == {str(alternate / 'rustc')}, {r['path'] for r in receipts}
        for receipt in receipts:
            assert receipt['environment']['MACOSX_DEPLOYMENT_TARGET'] == rustc['selection']['child_environment']['MACOSX_DEPLOYMENT_TARGET']
            assert receipt['environment']['RUSTUP_TOOLCHAIN'] == rustc['selection']['child_environment']['RUSTUP_TOOLCHAIN']
    finally:
        remove()
    restored = co.build('selection-6-plain-fresh', variant, fresh='1')
    passing(co, restored, variant)
    # A lower-precedence x86_64 target default, from the environment and from a configuration file, is overridden by the
    # managed --target: recorded as overridden, nothing rebuilt, and every output still the output target.
    remove = cargo_configuration(co, {'.cargo/config.toml': '[build]\ntarget = "x86_64-apple-darwin"\n'})
    try:
        defaulted = co.build('selection-6b-x86_64-default-overridden', variant, env=dict(CARGO_BUILD_TARGET='x86_64-apple-darwin'))
    finally:
        remove()
    passing(co, defaulted, variant)
    selected = defaulted.record['toolchain']['rustc']['selection']['target']
    assert selected == dict(source='--target', triple=prov.TRIPLE, overrides=['CARGO_BUILD_TARGET', 'build.target']), selected
    assert all(j['fresh'] is True for j in defaulted.judgments().values()), 'an overridden default changed what Cargo built'
    assert not (co.root / 'controller/target/x86_64-apple-darwin/release/policy-witness').exists()
    # Flags with retained caches: the encoded variable wins over the script's RUSTFLAGS and Cargo rebuilds with it.
    encoded = co.build('selection-7-encoded-flags', variant, env=dict(CARGO_ENCODED_RUSTFLAGS='-C\x1fdebuginfo=1'))
    passing(co, encoded, variant)
    for name, judgment in encoded.judgments().items():
        assert judgment['fresh'] is False, (name, 'changed flags did not rebuild')
        assert judgment['effective_rustflags'] == ['-C', 'debuginfo=1'], judgment['effective_rustflags']
        source = judgment['rustflags_source']
        assert (source['kind'], source['agrees'], source['overrides']) == ('CARGO_ENCODED_RUSTFLAGS', True, ['RUSTFLAGS']), source
    # Without RUSTFLAGS (inspection off), the output triple's target rules win over build.rustflags; a rule for another
    # triple, the one an Intel compiler would report as its host included, does not apply.
    remove = cargo_configuration(co, {'.cargo/config.toml': f'[build]\nrustflags = ["-C", "opt-level=2"]\n'
                                                            f'[target.{prov.TRIPLE}]\nrustflags = ["-C", "debuginfo=1"]\n'
                                                            f'[target.x86_64-apple-darwin]\nrustflags = ["-C", "opt-level=3"]\n'})
    try:
        rules = co.build('selection-8-target-rules', variant, env=dict(PW_INSPECTION='0'))
    finally:
        remove()
    passing(co, rules, variant)
    for name, judgment in rules.judgments().items():
        assert judgment['effective_rustflags'] == ['-C', 'debuginfo=1'], judgment['effective_rustflags']
        source = judgment['rustflags_source']
        assert (source['kind'], source['resolved'], source['agrees'], source['overrides']) == ('target rules', True, True, ['build.rustflags']), source
    # Back to the script's flags, which an earlier build compiled: Cargo keeps units for different flags side by side and
    # reuses that one, and the record binds the reused unit's own fingerprint through the uplifted executable.
    plain = co.build('selection-9-plain', variant)
    passing(co, plain, variant)
    for name, judgment in plain.judgments().items():
        source = judgment['rustflags_source']
        assert (source['kind'], source['agrees']) == ('RUSTFLAGS (script default)', True), (name, source, judgment['fresh'])
        assert judgment['effective_rustflags'] == ['-C', 'debuginfo=2', '-C', 'force-frame-pointers=yes', '-C', 'opt-level=1'], judgment
    return plain


def mach_o_build_version(path):
    """minos and sdk from otool -l, parsed here rather than by the record's producer."""
    text = subprocess.run(['/usr/bin/otool', '-l', str(path)], capture_output=True, text=True, check=True, timeout=60).stdout
    block = text[text.index('cmd LC_BUILD_VERSION'):]
    return tuple(re.search(r'^\s*' + key + r' (\S+)\s*$', block, re.M).group(1) for key in ('minos', 'sdk'))


def contained_xcrun(fixture, invalid):
    """A BASH_ENV that runs xcrun for the invalid request under a sandbox denying Mach lookups and other executables, so a
    failing SDK lookup cannot reach the installer; every other xcrun call is the real one."""
    fixture.mkdir(parents=True, exist_ok=True)
    prefix = shim_probe.prepare(fixture, exec_allowlist=['/usr/bin/xcrun'])
    script = fixture / 'contained.bash'
    script.write_text('/usr/bin/xcrun() {\n'
                      '  if [[ "${2:-}" == ' + shlex.quote(invalid) + ' ]]; then\n'
                      '    printf "%s\\n" "$*" >> ' + shlex.quote(str(fixture / 'calls')) + '\n'
                      '    command ' + shlex.join(prefix) + ' /usr/bin/xcrun "$@"\n'
                      '    return\n'
                      '  fi\n'
                      '  command /usr/bin/xcrun "$@"\n}\n')
    return script


def control_sdk_requests(co, variant):
    """The caller's SDK request through each entrypoint, kept apart from the SDK the build selects: absent, the default named
    explicitly, explicitly empty, and an explicit path through the shell front end with another owned command nested under
    it. Each build's compilations (forwarding wrappers), the environment they received and the outputs' load commands (read
    here) must agree with the record's effective settings. An invalid explicit request refuses instead of
    falling back to the default, at admission without a shim ever running with it."""
    selected = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
    version = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version'], text=True).strip()
    real_cc = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '-f', 'clang'], text=True).strip()
    real_rustc = subprocess.check_output(['rustup', 'which', 'rustc'], text=True).strip() if shutil.which('rustup') else shutil.which('rustc')
    recorded = ['SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'CPATH', 'LIBRARY_PATH', 'MANPATH']
    cc = co.forwarding('cc-requests', real_cc, mode='direct', record_env=recorded)
    rustc = co.forwarding('rustc-requests', real_rustc, mode='direct', record_env=recorded)
    tools = dict(CC=str(cc), RUSTC=str(rustc))
    front_end = ['/bin/bash', str(co.root / 'tests/lib/checkout_lock.sh'), '--root', str(co.root), '--']
    # The outer owner starts with a path; the nested front end witnesses a different request.
    nested = (f'SDKROOT=macosx CPATH= /bin/bash {shlex.quote(str(co.root / "tests/lib/checkout_lock.sh"))} '
              f'--root {shlex.quote(str(co.root))} -- /bin/bash {shlex.quote(str(co.root / "build.sh"))}')
    cases = (('absent', {}, None, dict(state='unset'), 'xcrun --sdk macosx default'),
             ('default-named', dict(SDKROOT='macosx'), None, dict(state='set', value='macosx'), 'SDKROOT named by the caller'),
             ('explicitly-empty', dict(SDKROOT=''), None, dict(state='set', value=''), 'xcrun --sdk macosx default'),
             ('explicit-path-front-end', dict(SDKROOT=selected), [*front_end, '/bin/bash', str(co.root / 'build.sh')],
              dict(state='set', value=prov.redact(selected)), 'SDKROOT named by the caller'),
             ('nested-environment', dict(SDKROOT=selected), [*front_end, '/bin/bash', '-c', nested],
              dict(state='set', value='macosx'), 'SDKROOT named by the caller'))
    build = None
    for index, (label, env, argv, request, source) in enumerate(cases):
        nested_environment = label == 'nested-environment'
        build = co.build(f'sdk_requests-{label}', variant, env=dict(tools, **env), argv=argv,
                         fresh='1' if index == 0 or nested_environment else '0')
        passing(co, build, variant)
        record = build.record
        assert record['configuration']['requests']['SDKROOT'] == request, (label, record['configuration']['requests'])
        assert record['toolchain']['sdk']['source'] == source, (label, record['toolchain']['sdk'])
        assert build.session['requests']['SDKROOT'] == (dict(state='unset') if request['state'] == 'unset'
                                                        else dict(state='set', value='macosx' if nested_environment else env['SDKROOT'])), build.session['requests']
        assert record['configuration']['sdkroot'] == prov.redact(selected) == record['toolchain']['sdk']['path'], record['configuration']
        assert record['configuration']['deployment_target'] == co.minimum
        compiled = [r for r in build.forward if r['kind'] == 'compile']
        if index == 0 or nested_environment:
            assert {r['wrapper'] for r in compiled} == {'cc-requests', 'rustc-requests'}, {r['wrapper'] for r in compiled}
        for receipt in compiled:
            expected = dict(SDKROOT=selected, MACOSX_DEPLOYMENT_TARGET=co.minimum,
                            CPATH='' if nested_environment else None, LIBRARY_PATH=None, MANPATH=None)
            assert receipt['environment'] == expected, (label, receipt['environment'])
        for output in record['outputs']:
            minos, sdk = mach_o_build_version(build.app / output['rel_path'])
            assert (minos, sdk) == (output['minos'], output['sdk']), (label, output['rel_path'], minos, sdk)
            assert prov.normalize_version(minos) == prov.normalize_version(co.minimum) and prov.normalize_version(sdk) == prov.normalize_version(version)
        if nested_environment:
            assert build.session['requests']['CPATH'] == dict(state='set', value=''), build.session['requests']
    # Admission refuses before lock verification or any session write; no default is substituted.
    invalid = '/private/tmp/pw-no-such-sdk-' + os.urandom(4).hex()
    fixture = co.work / 'sdk-request-invalid'
    session_before = (co.root / SESSION).read_bytes()
    refused = co.build('sdk_requests-invalid', variant, env=dict(SDKROOT=invalid, BASH_ENV=str(contained_xcrun(fixture, invalid))))
    check(refused, 2, f'admission: SDKROOT={invalid} does not resolve to an SDK with a numeric version',
          absent=('Verifying the checkout lock', 'Checking limits documentation', 'Selecting the macOS SDK', 'Building Rust'))
    assert not shim_probe.installation_requests(refused.output), refused.output[-2000:]
    assert (fixture / 'calls').read_text().split('\n')[0].startswith(f'--sdk {invalid}'), (fixture / 'calls').read_text()
    assert (co.root / SESSION).read_bytes() == session_before, 'admission wrote the session'
    assert not refused.receipts
    preserved(refused)
    restored = co.build('sdk_requests-restore', variant, fresh='1')
    passing(co, restored, variant)
    return build


ORACLE_ENV = ('PATH', 'MACOSX_DEPLOYMENT_TARGET', 'RUSTUP_TOOLCHAIN', 'PW_ORACLE_PLAIN', 'PW_ORACLE_RELATIVE',
              'SDKROOT', 'CPATH', 'LIBRARY_PATH', 'MANPATH')


class Oracle:
    """Real Cargo building a scratch crate through recording forwarders, beside the resolver's prediction for the same
    invocation directory and environment. Cargo's compilations, not the resolver, establish what ran."""

    def __init__(self, co):
        self.co = co
        self.base = co.work / 'cargo-oracle'
        if self.base.exists():
            shutil.rmtree(self.base)
        self.base.mkdir()
        self.real = subprocess.check_output(['rustup', 'which', 'rustc'], text=True).strip() if shutil.which('rustup') else shutil.which('rustc')
        self.host = re.search(r'^host: (\S+)$', subprocess.check_output([self.real, '-vV'], text=True), re.M).group(1)
        self.config = self.base / 'forward.json'
        self.results = []

    def place(self, path, mode='direct'):
        """A recording forwarder at path; Cargo passes the compiler to a wrapper, so mode names which slot it fills."""
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FORWARD, path)
        path.chmod(0o755)
        table = json.loads(self.config.read_text()) if self.config.exists() else {}
        table[path.name] = dict(real=self.real, mode=mode, receipt=str(self.base / f'{path.name}.receipts.jsonl'), record_env=list(ORACLE_ENV))
        save(self.config, table)
        return path

    def case(self, label, files, *, env=(), cwd='crate'):
        root = self.base / label
        crate = root / 'crate'
        (crate / 'src').mkdir(parents=True)
        (crate / 'Cargo.toml').write_text('[package]\nname = "oracle"\nversion = "0.1.0"\nedition = "2021"\n\n[workspace]\n')
        (crate / 'src/main.rs').write_text('fn main() {}\n')
        (root / 'home').mkdir()
        for relative, text in files.items():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(text)
        environment = {k: v for k, v in self.co.base_env.items() if k not in prov.CARGO_SELECTION_ENV + prov.CARGO_FLAG_ENV
                       and not k.startswith('PW_ORACLE_')}
        environment.update(CARGO_HOME=str(root / 'home'), CARGO_TARGET_DIR=str(root / 'target'), MACOSX_DEPLOYMENT_TARGET='26.0',
                           PW_FORWARD_CONFIG=str(self.config), CARGO_NET_OFFLINE='true')
        environment.update(dict(env))
        directory = root / cwd
        directory.mkdir(parents=True, exist_ok=True)
        try:
            resolution, unresolved = cargo_config.resolve(str(directory), environment, probe=prov.probe), None
        except cargo_config.Unresolved as exc:
            resolution, unresolved = None, str(exc)
        before = {p.name: len(p.read_text().splitlines()) for p in self.base.glob('*.receipts.jsonl')}
        status, stdout, stderr = command(self.co.out / f'{self.co.prefix}oracle-{label}',
                                         ['cargo', 'build', '--offline', '--manifest-path', str(crate / 'Cargo.toml')],
                                         cwd=directory, env=environment, timeout=300)
        receipts = []
        for path in sorted(self.base.glob('*.receipts.jsonl')):
            receipts += [json.loads(line) for line in path.read_text().splitlines()[before.get(path.name, 0):]]
        compiled = [r for r in receipts if r['kind'] == 'compile']
        summary = cargo_config.summary(resolution, os.environ.get('HOME', '')) if resolution else None
        save(self.co.out / f'{self.co.prefix}oracle-{label}' / 'oracle.json',
             dict(label=label, cargo_status=status, unresolved=unresolved, prediction=summary, compiled=compiled[:20]))
        self.results.append(dict(label=label, cargo_status=status, unresolved=unresolved))
        return dict(resolution=resolution, unresolved=unresolved, status=status, stderr=stderr, compiled=compiled, crate=crate, root=root,
                    environment=environment, merged=resolution['merged'] if resolution else None)


def expect_compiled_by(result, rustc, *, wrappers=()):
    """Cargo's compilations ran the predicted chain: the outer wrapper first, each passing the next, ending at rustc."""
    assert result['status'] == 0, (result['stderr'][-2000:])
    assert result['unresolved'] is None, result['unresolved']
    programs = result['resolution']['programs']
    chain = [programs[role]['command'] for role in ('wrapper', 'workspace_wrapper') if programs[role].get('command')]
    assert chain == [str(w) for w in wrappers], (chain, wrappers)
    assert programs['rustc']['command'] == str(rustc), (programs['rustc'], rustc)
    compiled = [r for r in result['compiled'] if '--crate-name' in r['args'] and 'oracle' in r['args']]
    paths = {r['path'] for r in compiled}
    assert str(rustc) in paths, ('the predicted compiler did not compile the crate', sorted(paths))
    for outer, inner in zip([str(w) for w in wrappers], [str(w) for w in wrappers[1:]] + [str(rustc)]):
        assert any(r['path'] == outer and r['real'] == inner for r in compiled), (outer, inner, compiled[:3])
    for r in compiled:
        assert r['cwd'] == str(result['crate']), ('Cargo compiled from another directory than the predicted probe directory', r['cwd'])
        child = result['resolution']['child']
        for name in ORACLE_ENV:
            want = child.get(name)
            if name == 'PATH' and want is not None:
                want = hashlib.sha256(want.encode()).hexdigest()
            assert r['environment'].get(name) == want, (name, r['environment'].get(name), want)


def control_cargo_configuration_oracle(co, variant):
    """The resolver's prediction against real Cargo for every configuration form the build reads: TOML forms, invocation
    directory discovery, ancestors and Cargo home, environment overrides, both wrappers and an empty reset, includes
    (relative, recursive, precedence, optional), [env] (forced and not, inherited or not, relative, a forced PATH
    selecting another compiler), and flag precedence. Unreadable graphs are refused by the resolver; Cargo's own status
    for them is kept beside the refusal."""
    o = Oracle(co)
    f1 = o.place(o.base / 'tools/f1/rustc-one')
    f2 = o.place(o.base / 'tools/f2/rustc-two')
    w1 = o.place(o.base / 'tools/w1/wrap-one', mode='rustc_wrapper')
    w2 = o.place(o.base / 'tools/w2/wrap-two', mode='rustc_wrapper')
    select = lambda path: f'[build]\nrustc = "{path}"\n'
    for label, text in (('inline', f'build = {{ rustc = "{f1}" }}\n'), ('dotted', f'build.rustc = "{f1}"\n'), ('table', select(f1))):
        expect_compiled_by(o.case(label, {'crate/.cargo/config.toml': text}), f1)
    # Discovery follows the invocation directory, not the manifest's.
    expect_compiled_by(o.case('invocation-directory', {'outer/.cargo/config.toml': select(f1)}, cwd='outer'), f1)
    # The manifest directory's file is not read from another invocation directory: the default compiler runs, not f1.
    default = o.case('manifest-directory-only', {'crate/.cargo/config.toml': select(f1)}, cwd='outer')
    assert default['status'] == 0 and default['resolution']['programs']['rustc']['source'] == 'default', default['stderr'][-1000:]
    assert not [r for r in default['compiled'] if r['path'] == str(f1)], 'Cargo read the manifest directory\'s configuration'
    expect_compiled_by(o.case('ancestor', {'.cargo/config.toml': select(f1)}), f1)
    expect_compiled_by(o.case('cargo-home', {'home/config.toml': select(f1)}), f1)
    overridden = o.case('overridden', {'crate/.cargo/config.toml': select(f1)}, env={'RUSTC': str(f2)})
    expect_compiled_by(overridden, f2)
    assert overridden['resolution']['programs']['rustc']['overrides'] == ['build.rustc']
    both = f'[build]\nrustc = "{f1}"\nrustc-wrapper = "{w1}"\nrustc-workspace-wrapper = "{w2}"\n'
    expect_compiled_by(o.case('wrappers', {'crate/.cargo/config.toml': both}), f1, wrappers=(w1, w2))
    expect_compiled_by(o.case('wrapper-reset', {'crate/.cargo/config.toml': both}, env={'RUSTC_WRAPPER': ''}), f1, wrappers=(w2,))
    # Includes: a relative command from an included file, recursion, precedence and an optional absent file.
    relative = o.place(o.base / 'include-relative/crate/tools/rustc-included')
    expect_compiled_by(o.case('include-relative', {'crate/.cargo/config.toml': 'include = ["inc.toml"]\n',
                                                    'crate/.cargo/inc.toml': '[build]\nrustc = "tools/rustc-included"\n'}), relative)
    expect_compiled_by(o.case('include-recursive', {'crate/.cargo/config.toml': 'include = ["a.toml"]\n',
                                                     'crate/.cargo/a.toml': 'include = ["deeper/b.toml"]\n',
                                                     'crate/.cargo/deeper/b.toml': select(f1)}), f1)
    expect_compiled_by(o.case('include-precedence', {'crate/.cargo/config.toml': 'include = ["inc.toml"]\n' + select(f2),
                                                      'crate/.cargo/inc.toml': select(f1)}), f2)
    expect_compiled_by(o.case('include-optional', {'crate/.cargo/config.toml': 'include = [{ path = "absent.toml", optional = true }]\n' + select(f1)}), f1)
    for label, files, needle in (('include-required-missing', {'crate/.cargo/config.toml': 'include = ["absent.toml"]\n'}, 'required include'),
                                 ('include-malformed', {'crate/.cargo/config.toml': 'include = ["bad.toml"]\n', 'crate/.cargo/bad.toml': 'build = {\n'},
                                  'not valid TOML'),
                                 ('include-cycle', {'crate/.cargo/config.toml': 'include = ["a.toml"]\n', 'crate/.cargo/a.toml': 'include = ["config.toml"]\n'},
                                  'include cycle'),
                                 ('malformed', {'crate/.cargo/config.toml': '[build\n'}, 'not valid TOML')):
        result = o.case(label, files)
        assert result['unresolved'] and needle in result['unresolved'], (label, result['unresolved'])
        assert result['status'] != 0, (label, 'Cargo accepted a configuration the resolver refuses', result['stderr'][-1000:])
    # [env]: a forced PATH selects another compiler (the review's counterexample), forced and unforced inputs, inherited
    # or not, and a relative value.
    alternate = o.place(o.base / 'env-path/alternate/rustc')
    forced_path = o.case('env-path', {'crate/.cargo/config.toml': '[env]\nPATH = { value = "' + str(alternate.parent) + ':' + co.base_env['PATH']
                                      + '", force = true }\n'})
    expect_compiled_by(forced_path, alternate)
    forced = o.case('env-deployment-forced', {'crate/.cargo/config.toml': select(f1) + '[env]\nMACOSX_DEPLOYMENT_TARGET = { value = "26.1", force = true }\n'})
    expect_compiled_by(forced, f1)
    assert cargo_config.conflicts(forced['resolution'], forced['environment']) == [('MACOSX_DEPLOYMENT_TARGET', '26.1', '26.0')]
    unforced = o.case('env-unforced', {'crate/.cargo/config.toml': select(f1) + '[env]\nMACOSX_DEPLOYMENT_TARGET = "26.1"\n'
                                       'PW_ORACLE_PLAIN = "from config"\nPW_ORACLE_RELATIVE = { value = "vendor/lib", relative = true }\n'})
    expect_compiled_by(unforced, f1)
    assert unforced['resolution']['child']['PW_ORACLE_RELATIVE'] == str(unforced['crate'] / 'vendor/lib')
    inherited = o.case('env-inherited', {'crate/.cargo/config.toml': select(f1) + '[env]\nPW_ORACLE_PLAIN = "from config"\n'},
                       env={'PW_ORACLE_PLAIN': 'from caller'})
    expect_compiled_by(inherited, f1)
    assert inherited['resolution']['child']['PW_ORACLE_PLAIN'] == 'from caller'
    # Flags: the encoded variable over RUSTFLAGS, target rules over build.rustflags; Cargo's compilations carry the winner.
    encoded = o.case('flags-encoded', {'crate/.cargo/config.toml': select(f1)},
                     env={'CARGO_ENCODED_RUSTFLAGS': '-C\x1fdebug-assertions=off', 'RUSTFLAGS': '-C overflow-checks=off'})
    expect_compiled_by(encoded, f1)
    requested = cargo_config.requested_flags(encoded['merged'], encoded['environment'], o.host)
    assert requested['source'] == 'CARGO_ENCODED_RUSTFLAGS' and requested['overrides'] == ['RUSTFLAGS']
    args = [r['args'] for r in encoded['compiled'] if 'oracle' in r['args'] and r['path'] == str(f1)][-1]
    assert 'debug-assertions=off' in args and 'overflow-checks=off' not in args, args
    rules = o.case('flags-target', {'crate/.cargo/config.toml': f'[build]\nrustc = "{f1}"\nrustflags = ["-C", "overflow-checks=off"]\n'
                                    f'[target.{o.host}]\nrustflags = ["-C", "debug-assertions=off"]\n'})
    expect_compiled_by(rules, f1)
    requested = cargo_config.requested_flags(rules['merged'], rules['environment'], o.host)
    assert (requested['source'], requested['tokens'], requested['overrides']) == ('target rules', ['-C', 'debug-assertions=off'], ['build.rustflags'])
    args = [r['args'] for r in rules['compiled'] if 'oracle' in r['args'] and r['path'] == str(f1)][-1]
    assert 'debug-assertions=off' in args and 'overflow-checks=off' not in args, args
    save(co.out / f'{co.prefix}cargo-oracle.json', o.results)
    return None


# The manifest's refusals in script order, with the variants each applies to.
# ---- the output target -----------------------------------------------------------------------------------------

def reported_fresh(co, name):
    """Cargo's own judgment for one shipped target, read from its report rather than from the session."""
    for line in (co.root / 'controller/target/pw-build-messages.jsonl').read_text().splitlines():
        message = json.loads(line) if line.strip() else {}
        if message.get('reason') == 'compiler-artifact' and (message.get('target') or {}).get('name') == name:
            return message.get('fresh')
    return None


def cached_unit(path):
    """The deps file a Cargo output was uplifted from: the one unit file of that target with the output's bytes."""
    stem, digest = path.name.replace('-', '_'), artifact.digest(path)
    units = [p for p in sorted((path.parent / 'deps').iterdir())
             if re.fullmatch(re.escape(stem) + r'-[0-9a-f]{16}', p.name) and artifact.digest(p) == digest]
    assert len(units) == 1, (path, units)
    return units[0]


def control_output_target_mismatch(co, variant):
    """Outputs outside the output target are refused at each boundary a check guards, before the operation it protects, by
    the check of the bytes, never by the minimum, SDK or identity checks (each substitute carries the plist's minimum
    and the selected SDK). A Cargo output replaced after Cargo reported it (x86_64, then a truncated arm64 file) refuses
    before Meson; because Cargo judges the replaced file current and keeps it, the next build without any fault refuses
    it again. A native output replaced after the compile (universal for the last output; a one-slice fat container of an
    arm64 executable for the worker, which the identity check would otherwise run) refuses before assembly. Cargo copies
    each output from its cached unit on every build, so a replaced output alone is restored by the next one; the x86_64
    bytes therefore replace the cached unit as well, as a corrupted cache would, newer than its compile so that Cargo
    judges it current, while the truncated file replaces only the output. A copy
    replaced in the assembled bundle, with an unlisted universal file added beside it, refuses before any signature.
    The standalone observer replaced after the app seal refuses before it is signed, and the sealed bundle's code
    replaced after that refuses before the ZIP is written."""
    message = 'outputs are not thin arm64 Mach-O executables for macOS'
    unrelated = ('is built for macOS', 'disagree with the selected SDK', 'reports identity')

    def refused_by_target(build, *names):
        check(build, 1, message)
        for name in names:
            assert name in build.stderr, (build.name, name, build.stderr[-3000:])
        for text in unrelated:
            assert text not in build.stderr, (build.name, 'an unrelated check refused instead', text)

    # Cargo outputs, after Cargo reported them, before Meson.
    for label, fixture, binary, reason in (('x86_64', 'x86_64', 'sbpl-check', 'architecture x86_64, not exactly arm64'),
                                           ('truncated', 'truncated', 'policy-witness', 'no readable LC_BUILD_VERSION platform')):
        target = co.target / binary
        unit = cached_unit(target) if label == 'x86_64' else None
        actions = [replace(co.forbidden(fixture), path) for path in ((unit, target) if unit else (target,))]
        build = co.build(f'output_target_mismatch-cargo-{label}', variant,
                         hooks=[hook(f'replace-{binary}', 'cargo', actions, first='build')])
        try:
            refused_by_target(build, f'{target}: {reason}')
            assert 'Building Rust controller + tools' in build.stdout
            for banner in BEFORE_TOOLCHAIN:
                assert banner not in build.stdout, (build.name, banner)
            fired_once(build, f'replace-{binary}')
            no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
            preserved(build)
            assert len(build.session['output_check']['cargo']['problems']) == 1, build.session['output_check']
            if label == 'x86_64':
                # Reuse is no bypass: Cargo judges the replaced unit current, copies it out again, and the next build's
                # check refuses it again.
                again = co.build('output_target_mismatch-cargo-reused', variant)
                refused_by_target(again, f'{target}: {reason}')
                assert reported_fresh(co, binary) is True, 'Cargo rebuilt the output; reuse was not exercised'
                no_calls(again, 'meson', 'ninja', 'codesign', 'cp')
                preserved(again)
        finally:
            if unit is not None:
                unit.unlink(missing_ok=True)  # the cached unit itself was replaced: Cargo compiles it again
            target.unlink(missing_ok=True)  # otherwise Cargo copies its untouched unit out again
    # Native outputs, after the compile, before assembly and before the worker is run for its identity.
    last = co.builddir / ('PWRunner' if variant == 'full' else 'pw-extension-issuer')
    worker = co.builddir / 'pw-probe-runner'
    for label, path, fixture, reason in (('universal-last', last, 'universal', 'a fat container with 2 slice(s) (arm64 x86_64), not a thin Mach-O'),
                                         ('one-slice-fat-worker', worker, 'one-slice-fat', 'a fat container with 1 slice(s) (arm64), not a thin Mach-O')):
        build = co.build(f'output_target_mismatch-native-{label}', variant,
                         hooks=[hook(f'replace-{path.name}', 'meson', [replace(co.forbidden(fixture), path)], first='compile')])
        try:
            refused_by_target(build, f'{path}: ')
            assert reason.split(' (')[0] in build.stderr, (build.name, reason, build.stderr[-2000:])
            check(build, 1, message, present=('Checking the configured native source lists',),
                  absent=('Assembling app bundle', 'Checking host/worker identity again'))
            fired_once(build, f'replace-{path.name}')
            no_calls(build, 'codesign', 'cp')
            assert 'worker_identity' not in build.session, 'the worker ran before the output check refused it'
            preserved(build)
        finally:
            path.unlink(missing_ok=True)  # Ninja links the output again when it is missing
    # The assembled bundle: a copy replaced as it is made and an unlisted universal file beside it, before any signature.
    app = co.app(variant, 'output_target_mismatch-assembled')
    copied, unlisted = app / 'Contents/MacOS/sbpl-check', app / 'Contents/Resources/unlisted.dylib'
    build = co.build('output_target_mismatch-assembled', variant,
                     hooks=[hook('replace-copy', 'cp', [replace(co.forbidden('x86_64'), copied), replace(co.forbidden('universal'), unlisted)],
                                 last=str(copied))])
    refused_by_target(build, f'{copied}: architecture x86_64, not exactly arm64', f'{unlisted}: a fat container with 2 slice(s)')
    check(build, 1, message, present=('Checking the assembled code against the output target',),
          absent=('Checking host/worker identity again', 'Codesigning embedded MacOS tools'))
    fired_once(build, 'replace-copy')
    assert build.signed() == [], build.signed()
    assert subprocess.check_output(['/usr/bin/lipo', '-archs', str(co.target / 'sbpl-check')], text=True).split() == ['arm64'], \
        'the substitution reached the Cargo output instead of the copy'
    removed_previous(build)
    # The standalone observer, after the app seal and the signer check, before it is signed in place.
    app = co.app(variant, 'output_target_mismatch-observer')
    observer = co.target / 'sandbox-log-observer'
    build = co.build('output_target_mismatch-observer', variant,
                     hooks=[hook('replace-observer', 'codesign', [replace(co.forbidden('x86_64'), observer)], last=str(app), contains='--force')])
    try:
        refused_by_target(build, f'{observer}: architecture x86_64, not exactly arm64')
        check(build, 1, message, present=("Checking every executable's signer", 'Codesigning observer tool (not embedded)'),
              absent=('Staging checked user guide', 'Creating zip'))
        fired_once(build, 'replace-observer')
        assert str(observer) not in build.signed(), 'the observer was signed before its check'
        assert not (build.dist / 'PolicyWitness.zip').exists()
    finally:
        observer.unlink(missing_ok=True)
    # The sealed bundle as packaged, after the observer is signed, before the ZIP.
    app = co.app(variant, 'output_target_mismatch-packaging')
    sealed = app / 'Contents/MacOS/sbpl-check'
    build = co.build('output_target_mismatch-packaging', variant,
                     hooks=[hook('replace-sealed', 'codesign', [replace(co.forbidden('arm64e'), sealed)], last=str(observer), contains='--force')])
    refused_by_target(build, f'{sealed}: architecture arm64e, not exactly arm64')
    check(build, 1, message, present=('Staging checked user guide', 'Creating zip (for notarization)'))
    fired_once(build, 'replace-sealed')
    assert 'DONE:' not in build.stdout
    assert str(observer) in build.signed()
    assert not (build.dist / 'PolicyWitness.zip').exists() and (build.dist / 'PolicyWitness.md').exists()
    # A required path does not disappear from either app-wide gate when its header is no longer recognizable.
    # The packaging substitutions happen after signature verification, so only the final output gate protects the ZIP.
    for stage in ('assembled', 'packaging'):
        for fault in ('text', 'empty', 'short-magic', 'missing'):
            name = f'output_target_mismatch-{stage}-{fault}'
            app = co.app(variant, name)
            target = app / 'Contents/MacOS/sbpl-check'
            actions = {'text': [write(target, '#!/bin/sh\nexit 0\n')], 'empty': [truncate(target, 0)],
                       'short-magic': [truncate(target, 2)], 'missing': [delete(target)]}[fault]
            # Augments are copied after the top-level tools' chmod calls in both variants. Removing the target at
            # its own copy would make chmod refuse first, establishing nothing about the assembled output gate.
            boundary = (hook('damage-required', 'cp', actions, first=str(co.root / 'runner/augments' / co.augment)) if stage == 'assembled' else
                        hook('damage-required', 'codesign', actions, last=str(observer), contains='--force'))
            damaged = co.build(name, variant, hooks=[boundary])
            reason = 'unreadable (FileNotFoundError)' if fault == 'missing' else 'not a Mach-O file'
            refused_by_target(damaged, f'{target}: {reason}')
            fired_once(damaged, 'damage-required')
            assert len(damaged.session['output_check'][stage]['problems']) == 1, damaged.session['output_check'][stage]
            assert not (damaged.dist / 'PolicyWitness.zip').exists()
            assert 'DONE:' not in damaged.stdout
            if stage == 'assembled':
                assert damaged.signed() == [], damaged.signed()
                assert 'Codesigning embedded MacOS tools' not in damaged.stdout
            else:
                assert str(observer) in damaged.signed()
                assert 'Creating zip (for notarization)' in damaged.stdout
    return build


def control_builddir_target_mismatch(co, variant):
    """A stamp naming another output target refuses reuse before any compile, as does a stamp from before the output
    target contract, which is never relabelled; neither is rewritten. Fresh mode then replaces exactly the admitted
    areas (builddir/ and the two Cargo release areas), keeping other profiles and triples, and an unchanged reuse checks
    every cached executable against the target again."""
    if not (co.root / STAMP).exists():
        passing(co, co.build('builddir_target_mismatch-prime', variant), variant)
    stamp = co.root / STAMP
    kept = stamp.read_bytes()
    record = json.loads(kept)
    build = None
    try:
        for label, fields, needle in (('cpu', {'output.cpu_family': 'x86_64'}, "is configured for output output.cpu_family = 'x86_64'"),
                                      ('triple', {'output.cargo_triple': 'x86_64-apple-darwin'}, 'is configured for output output.cargo_triple'),
                                      ('arch', {'output.link_arch': ['x86_64']}, 'is configured for output output.link_arch')):
            text = json.dumps(dict(record, fields=dict(record['fields'], **fields)))
            stamp.write_text(text)
            build = co.build(f'builddir_target_mismatch-{label}', variant)
            check(build, 1, needle, present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
            assert 'a directory configured for another target cannot be reused' in build.stderr
            assert stamp.read_text() == text, 'the refusal rewrote the stamp'
            no_compiles(build)
            preserved(build)
        legacy = dict(record, schema_version=1, fields={k: v for k, v in record['fields'].items() if not k.startswith('output.')})
        stamp.write_text(json.dumps(legacy))
        old = co.build('builddir_target_mismatch-legacy-stamp', variant)
        check(old, 2, 'unsupported schema', present=('Checking the native build directory',), absent=('Checking the signing identity', *BEFORE_CARGO))
        assert 'PW_FRESH_BUILD=1' in old.stderr and json.loads(stamp.read_text()) == legacy, 'an old stamp was adopted or rewritten'
        no_compiles(old)
        preserved(old)
    finally:
        stamp.write_bytes(kept)
    replaced = {co.builddir / 'target-sentinel': 'native cache', co.host_release / 'target-sentinel': 'host cache',
                co.target / 'target-sentinel': 'shipped cache'}
    kept_paths = {co.root / 'controller/target/debug/target-sentinel': 'host debug', co.root / prov.TRIPLE_DIR / 'debug/target-sentinel': 'triple debug',
                  co.root / 'controller/target/x86_64-apple-darwin/release/target-sentinel': 'another triple'}
    for path, text in {**replaced, **kept_paths}.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    recovered = co.build('builddir_target_mismatch-fresh', variant, fresh='1')
    passing(co, recovered, variant)
    assert not any(p.exists() for p in replaced), 'fresh mode kept an admitted area'
    assert all(p.read_text() == text for p, text in kept_paths.items()), 'fresh mode removed another profile or triple'
    assert all(j['fresh'] is False for j in recovered.judgments().values())
    reused = co.build('builddir_target_mismatch-reuse', variant)
    passing(co, reused, variant)
    assert all(j['fresh'] is True for j in reused.judgments().values()), 'reuse rebuilt a Cargo target'
    checked = reused.session['output_check']
    assert {Path(p).name for p in checked['cargo']['outputs']} == set(CARGO_BINS) and not checked['cargo']['problems'], checked['cargo']
    assert len(checked['native']['outputs']) == (5 if variant == 'full' else 3) and not checked['native']['problems'], checked['native']
    for path in kept_paths:
        path.unlink()
    return build


def control_meson_target(co, variant):
    """Meson configured for another host machine is refused by meson.build's output-target assertion at setup, before
    anything compiles and before a stamp is published. A cross file naming an x86_64 macOS host, appended by the tool
    wrapper to the script's own `meson setup`, is only the technique that produces the configuration; the source_drift
    Meson control covers the same assertion directly. A fresh native build restores the directory."""
    cross = co.work / 'cross-x86_64.ini'
    cross.write_text("[binaries]\nc = 'cc'\nswift = 'swiftc'\n[host_machine]\nsystem = 'darwin'\n"
                     "cpu_family = 'x86_64'\ncpu = 'x86_64'\nendian = 'little'\n")
    refused = co.build('meson_target-x86_64-host', variant, fresh='1',
                       hooks=[hook('cross-x86_64', 'meson', append=['--cross-file', str(cross)], first='setup')])
    check(refused, 1, 'Assert failed: output target: the native products are macOS arm64 code, but Meson is configured for host '
                      'darwin x86_64\n', where='output',
          present=('Configuring native build (meson setup, fresh directory)',), absent=('Compiling native executables', 'Assembling app bundle'))
    fired_once(refused, 'cross-x86_64')
    assert not (co.root / STAMP).exists(), 'a refused setup published a stamp'
    no_calls(refused, 'codesign', 'cp')
    preserved(refused)
    restored = co.build('meson_target-native-fresh', variant, fresh='1')
    passing(co, restored, variant)
    assert 'Build type: native build' in restored.stdout
    return refused


def control_cargo_package_target_guard(co, variant):
    """The controller package's build script refuses every Cargo target but aarch64-apple-darwin, for a direct Cargo
    invocation outside build.sh, with isolated output and intermediate directories. Run with --keep-going, so the build
    script runs although the standard library of a target this machine lacks also fails that target's units: the
    guard's own message is the observation, and the missing library is recorded beside it. This establishes that the
    guard fires on TARGET; it does not establish that the guard alone stops a target whose library is installed. The
    output triple builds, and a guard removed or weakened to an aarch64 prefix or an apple-darwin suffix fails this
    control."""
    build_rs = co.root / 'controller/build.rs'
    original = build_rs.read_text()
    work = co.work / 'package-guard'
    outputs = work / 'target'
    env = {k: v for k, v in co.base_env.items() if not k.startswith(('CARGO_TARGET', 'CARGO_BUILD'))}
    env.update(CARGO_TARGET_DIR=str(outputs), CARGO_BUILD_BUILD_DIR=str(outputs), CARGO_NET_OFFLINE='true')
    others = ('x86_64-apple-darwin', 'aarch64-apple-ios')

    def attempt(label, triple):
        case = co.out / f'{co.prefix}package_guard-{label}-{triple}'
        status, stdout, stderr = command(case, [co.tools['cargo'], 'build', '--manifest-path', str(co.root / 'controller/Cargo.toml'),
                                                '--release', '--keep-going', '--target', triple], cwd=co.root, env=env)
        observed = dict(status=status, guard=f"Cargo's TARGET is \"{triple}\"" in stderr,
                        library_missing='may not be installed' in stderr or "can't find crate for" in stderr)
        save(case / 'observed.json', observed)
        return observed

    results = {}
    try:
        neighbour = attempt('original', prov.TRIPLE)
        assert neighbour['status'] == 0 and not neighbour['guard'], neighbour
        for triple in others:
            observed = attempt('original', triple)
            assert observed['status'] != 0 and observed['guard'], (triple, observed)
            results[triple] = observed
        guard = ('    if target != OUTPUT_TRIPLE {\n')
        weakenings = {'guard removed': '    if false {\n', 'an aarch64 prefix': '    if !target.starts_with("aarch64") {\n',
                      'an apple-darwin suffix': '    if !target.ends_with("apple-darwin") {\n'}
        assert original.count(guard) == 1
        mutations = {}
        for label, weakened in weakenings.items():
            build_rs.write_text(original.replace(guard, weakened, 1))
            observed = {triple: attempt(label.replace(' ', '-'), triple) for triple in others}
            accepted = [triple for triple, seen in observed.items() if not seen['guard']]
            assert accepted, f'{label}: the weakened guard still refused every target this control names'
            mutations[label] = dict(observed=observed, accepted=accepted)
    finally:
        build_rs.write_text(original)
        shutil.rmtree(work, ignore_errors=True)
    save(co.out / f'{co.prefix}package_guard.json', dict(neighbour=neighbour, refused=results, mutations=mutations,
                                                          limit='every refused target also lacks its standard library on this machine'))
    return None


CONTROLS = [
    ('native_builder_required', ('full', 'partial'), control_unconfirmed_machine),
    ('missing_tree_input', ('full', 'partial'), control_missing_tree_input),
    ('checkout_busy', ('full', 'partial'), control_checkout_busy),
    ('lock_claim_invalid', ('full', 'partial'), control_lock_claim_invalid),
    ('environment_witness_missing', ('full', 'partial'), control_environment_witness_missing),
    ('environment_witness_changed', ('full', 'partial'), control_environment_witness_changed),
    ('sdk_unavailable', ('full', 'partial'), control_sdk_unavailable),
    ('sdk_version_unreadable', ('full', 'partial'), control_sdk_version_unreadable),
    ('builddir_stamp_missing', ('full', 'partial'), control_builddir_stamp_missing),
    ('builddir_stamp_invalid', ('full', 'partial'), control_builddir_stamp_invalid),
    ('builddir_target_mismatch', ('full', 'partial'), control_builddir_target_mismatch),
    ('cargo_build_dir_redirected', ('full', 'partial'), control_cargo_build_dir_redirected),
    ('cargo_build_dir_unknown', ('full', 'partial'), control_cargo_build_dir_unknown),
    ('cargo_configuration_unresolved', ('full', 'partial'), control_cargo_configuration_unresolved),
    ('cargo_environment_conflict', ('full', 'partial'), control_cargo_environment_conflict),
    ('fresh_removal_failed', ('full', 'partial'), control_fresh_removal_failed),
    ('missing_cargo_output', ('full', 'partial'), control_missing_cargo_output),
    ('cargo_artifact_elsewhere', ('full', 'partial'), control_cargo_artifact_elsewhere),
    ('cargo_failed', ('full', 'partial'), control_cargo_failed),
    ('cargo_target_reused', ('full', 'partial'), control_cargo_target_reused),
    ('cargo_judgment_unknown', ('full', 'partial'), control_cargo_judgment_unknown),
    ('meson_ninja_missing', ('full', 'partial'), control_meson_ninja_missing),
    ('ninja_old', ('full', 'partial'), control_ninja_old),
    ('meson_policy', ('full', 'partial'), control_meson_policy),
    ('meson_target', ('full', 'partial'), control_meson_target),
    ('meson_failed', ('full', 'partial'), control_meson_failed),
    ('native_sources_unreadable', ('full', 'partial'), control_native_sources_unreadable),
    ('missing_native_output', ('full', 'partial'), control_missing_native_output),
    ('output_target_mismatch', ('full', 'partial'), control_output_target_mismatch),
    ('stale_identity_presign', ('full', 'partial'), control_stale_identity_presign),
    ('worker_identity_mismatch', ('full', 'partial'), control_worker_identity_mismatch),
    ('sign_target_not_macho', ('full', 'partial'), control_sign_target_not_macho),
    ('codesign_failed', ('full', 'partial'), control_codesign_failed),
    ('evidence_failed', ('full', 'partial'), control_evidence_failed),
    ('provenance_required_unknown', ('full', 'partial'), control_provenance_required_unknown),
    ('cache_path_unsafe', ('full', 'partial'), control_cache_path_unsafe),
    ('verify_failed', ('full', 'partial'), control_verify_failed),
]
# Controls that drive sequences across variants or establish a limit rather than one refusal; run once each.
SEQUENCES = [
    ('shim_install_detector', control_shim_install_detector),
    ('builddir_toolchain_changed', control_builddir_toolchain_changed),
    ('provenance_probe_failed', control_provenance_probe_failed),
    ('fresh_sequence', control_fresh_sequence),
    ('replaced_cached_output', control_replaced_cached_output_is_recorded_not_detected),
    ('release_entrypoints', control_release_entrypoints_enforce_fresh_mode),
    ('lock_lifetime', control_lock_lifetime),
    ('cargo_configuration_oracle', control_cargo_configuration_oracle),
    ('cargo_selection_sequence', control_cargo_selection_sequence),
    ('sdk_requests', control_sdk_requests),
    ('cargo_package_target_guard', control_cargo_package_target_guard),
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
                     'done\n')
NINJA_GUARD = ('if ! "${PW_PYTHON}" -B -S -P -c \'import sys; v, m = (tuple(int(p) for p in a.split(".")) for a in sys.argv[1:3]); sys.exit(0 if v >= m else 1)\' \\\n'
               '    "${NINJA_VERSION}" "${NINJA_MINIMUM}"; then\n'
               '  echo "ERROR: ninja ${NINJA_VERSION} is older than the ${NINJA_MINIMUM} minimum; see docs/SIGNING.md" 1>&2\n'
               '  exit 2\n'
               'fi\n')
NATIVE_OUTPUT_LOOP = ('for native_bin in "${NATIVE_OUTPUTS[@]}"; do\n'
                      '  if [[ ! -x "${native_bin}" ]]; then\n'
                      '    echo "ERROR: expected Meson output at ${native_bin}" 1>&2\n'
                      '    exit 2\n'
                      '  fi\n'
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
STAMP_CHECK = '  "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/build_provenance.py" stamp-check --root "${ROOT_DIR}" --xpc "${BUILD_XPC}"\n'
WORKER_IDENTITY = ('"${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/build_provenance.py" worker-identity --root "${ROOT_DIR}" \\\n'
                   '  --worker "${PW_PROBE_RUNNER_BIN}" --expected "${GENERATED_WORKER_IDENTITY}"\n')
REQUIRE_REBUILT = '--require-rebuilt "${PW_FRESH_BUILD}"'
PROVENANCE_HELPER = 'tests/lib/build_provenance.py'
CARGO_OUTPUT_CHECK = ('"${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage cargo \\\n'
                      '  "${RUNNER_BIN}" "${SANDBOX_LOG_OBSERVER_BIN}" "${SBPL_CHECK_BIN}"\n')
ASSEMBLED_CHECK = ('echo "==> Checking the assembled code against the output target: ${APP_BUNDLE}"\n'
                   '"${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/build_provenance.py" output-check --root "${ROOT_DIR}" --stage assembled --app "${APP_BUNDLE}"\n')
FIRST_SIGNATURE = 'sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"\n'
OUTPUT_TARGET_HELPER = 'tests/lib/output_target.py'
ARCHITECTURE_EQUALITY = "    if observation['architectures'] != [ARCHITECTURE]:\n"
CONTAINER_RULE = "    if observation['container'] != CONTAINER:\n        found.append("
MESON_TARGET_ASSERTION = ("assert(host_machine.system() == 'darwin' and host_machine.cpu_family() == 'aarch64',\n"
                          "  'output target: the native products are macOS arm64 code, but Meson is configured for host @0@ @1@'.format(\n"
                          "    host_machine.system(), host_machine.cpu_family()))\n")
NATIVE_GUARD = ('if NATIVE_ARM64="$(/usr/sbin/sysctl -n hw.optional.arm64)"; then\n'
                '  NATIVE_ARM64="${NATIVE_ARM64:-<empty>}"\n'
                'else\n'
                '  NATIVE_ARM64="<failed: status $?>"\n'
                'fi\n'
                'if NATIVE_TRANSLATED="$(/usr/sbin/sysctl -n sysctl.proc_translated)"; then\n'
                '  NATIVE_TRANSLATED="${NATIVE_TRANSLATED:-<empty>}"\n'
                'else\n'
                '  NATIVE_TRANSLATED="<failed: status $?>"\n'
                'fi\n'
                'if [[ "${NATIVE_ARM64}" != "1" || "${NATIVE_TRANSLATED}" != "0" ]]; then\n'
                '  echo "ERROR: this build runs only natively on Apple Silicon (hw.optional.arm64=${NATIVE_ARM64}, '
                'sysctl.proc_translated=${NATIVE_TRANSLATED})" 1>&2\n'
                '  exit 2\n'
                'fi\n'
                'unset NATIVE_ARM64 NATIVE_TRANSLATED\n')
PYTHON_START = 'source "${ROOT_DIR}/tests/lib/python_start.sh"\n'
LOCK_FRONT_END = ('  exec /bin/bash "${ROOT_DIR}/tests/lib/checkout_lock.sh" --root "${ROOT_DIR}" -- /bin/bash "${BASH_SOURCE[0]}" "$@"\n'
                  'fi\n')


def _membership(text):
    """The output predicate reduced to arm64 membership: the container rule dropped and equality weakened."""
    for old, new in ((ARCHITECTURE_EQUALITY, "    if ARCHITECTURE not in observation['architectures']:\n"),
                     (CONTAINER_RULE, "    if False:\n        found.append(")):
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    return text


def _admission_disabled(text):
    """BuildPaths follows symlinks and checks nothing: the session is written wherever the path leads, as before the repair."""
    for old, new in (('        self.check(relative, info)\n        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)',
                      '        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=parent_fd)\n        info = os.fstat(fd)'),
                     ('        """Every admitted component from the root down to relative still names the directory admitted."""\n',
                      '        """Every admitted component from the root down to relative still names the directory admitted."""\n        return\n'),
                     ('        """A destination this build replaces: absent, or a regular file of this user with one link."""\n',
                      '        """A destination this build replaces: absent, or a regular file of this user with one link."""\n        return\n')):
        assert text.count(old) == 1, old[:80]
        text = text.replace(old, new)
    return text

MUTATIONS = [
    ('native_builder_required', 'guard removed', lambda t: _remove_block(t, NATIVE_GUARD)),
    ('native_builder_required', 'guard moved past Python and SDK setup', lambda t: _move_block(t, NATIVE_GUARD, PYTHON_START)),
    ('native_builder_required', 'guard moved past the lock front end', lambda t: _move_block(t, NATIVE_GUARD, LOCK_FRONT_END)),
    ('missing_cargo_output', 'guard removed', lambda t: _remove_block(t, CARGO_OUTPUT_LOOP)),
    ('ninja_old', 'guard removed', lambda t: _remove_block(t, NINJA_GUARD)),
    ('missing_native_output', 'guard moved past assembly', lambda t: _move_block(t, NATIVE_OUTPUT_LOOP, ASSEMBLY_ANCHOR)),
    ('missing_tree_input', 'admission moved after the first check', lambda t: _move_block(t, TREE_INPUT_LOOP, LIMITS_ANCHOR)),
    ('sign_target_not_macho', 'check moved after codesign', lambda t: _move_block(t, MACHO_GUARD, SIGN_ANCHOR)),
    ('builddir_stamp_missing', 'stamp validation removed', lambda t: _remove_block(t, STAMP_CHECK)),
    ('worker_identity_mismatch', 'worker identity check removed', lambda t: _remove_block(t, WORKER_IDENTITY)),
    ('cargo_target_reused', 'rebuild requirement dropped', lambda t: t.replace(REQUIRE_REBUILT, '--require-rebuilt "0"', 1)),
    ('cache_path_unsafe', 'path admission disabled in the session helper', _admission_disabled, PROVENANCE_HELPER),
    ('output_target_mismatch', 'Cargo output check removed', lambda t: _remove_block(t, CARGO_OUTPUT_CHECK)),
    ('output_target_mismatch', 'assembled check moved past the first signature', lambda t: _move_block(t, ASSEMBLED_CHECK, FIRST_SIGNATURE)),
    ('output_target_mismatch', 'output predicate reduced to arm64 membership', _membership, OUTPUT_TARGET_HELPER),
    ('meson_target', 'output-target assertion removed', lambda t: _remove_block(t, MESON_TARGET_ASSERTION), 'meson.build'),
]


SELF_CHECK_RE = re.compile(r'^"\$\{PW_PYTHON\}" -B "\$\{ROOT_DIR\}/docs/generate_[a-z_]+\.py" --check\n', re.M)
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
    those checks, or one in a helper the self-checks do not read, fails its
    control by the displacement itself. With the self-checks removed the build
    runs to the displaced guard, and the second stage shows the control failing
    there with no self-check involved. A fresh build with the original script
    and helper precedes the second stage and the repeat, since a mutated run can
    leave the stamp missing or outputs torn down; the original then passes the
    same control again."""
    results = []
    functions = {refusal: function for refusal, _, function in CONTROLS}
    script = co.root / 'build.sh'
    original = co.script
    for index, (refusal, label, mutate, *where) in enumerate(MUTATIONS, 1):
        # Several mutations can guard one refusal: the index keeps each one's case directories apart.
        tag = f'{index:02d}-{refusal}'
        target = co.root / (where[0] if where else 'build.sh')
        kept = target.read_bytes()
        mutated = mutate(kept.decode())
        assert mutated.encode() != kept
        stages = {}
        try:
            for stage in ('self_checks', 'guard'):
                if stage == 'guard':
                    target.write_bytes(kept)
                    _restore(co, script, original, f'restore-before-guard-{tag}-')
                if target == script:
                    text = mutated if stage == 'self_checks' else _without_self_checks(mutated)
                    script.write_bytes(text.encode())
                    co.script = text.encode()
                else:
                    target.write_bytes(mutated.encode())
                    if stage == 'guard':
                        text = _without_self_checks(original.decode())
                        script.write_bytes(text.encode())
                        co.script = text.encode()
                co.prefix = f'mutated-{stage}-{tag}-'
                co.last = None
                failure = _control_failure(functions[refusal], co, 'full')
                assert failure is not None, f'{refusal}: the control passed with the {label} ({stage} stage)'
                assert co.last is not None, f'{refusal}: the control raised before building ({stage} stage): {failure}'
                stages[stage] = dict(control=failure, build=co.last.name, status=co.last.status, stderr=co.last.stderr[-800:],
                                     self_check_refused=any(marker in co.last.stderr for marker in SELF_CHECK_MARKERS))
        finally:
            target.write_bytes(kept)
            script.write_bytes(original)
            co.script = original
            (co.builddir / 'pw-probe-runner').unlink(missing_ok=True)
        assert not stages['guard']['self_check_refused'], stages['guard']
        _restore(co, script, original, f'restore-before-repeat-{tag}-')
        co.prefix = f'repeat-{tag}-'
        functions[refusal](co, 'full')
        co.prefix = ''
        results.append(dict(refusal=refusal, mutation=label, file=str(target.relative_to(co.root)),
                            self_checks=stages['self_checks'], guard=stages['guard']))
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
