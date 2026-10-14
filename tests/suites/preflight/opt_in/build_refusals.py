"""Drive the unchanged build script through every refusal the build baseline listed, with real toolchains and signatures.

One disposable checkout of the working tree serves every control. A control
arranges one fault beside the boundary the refusal guards: an environment the
script cannot build in, a source that does not compile, or a file a tool
wrapper removes, moves, truncates or rewrites right before or after one named
cargo, meson, codesign or cp call. The wrapper runs the real tool and records
a receipt; the script's own check makes the refusal. Each control asserts the
diagnostic and status, the banners that must and must not follow, the tool
calls that must not have happened and the output left behind, so the refusal
is placed before the operation it protects. Mutated copies of the script with
a guard removed or moved past that operation must fail their control.
"""
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
WRAPPER = ROOT / 'tests/fixtures/build_refusals/tools.py'
WRAPPED = ('cargo', 'meson', 'ninja', 'codesign', 'cp')
VARIANTS = {'full': '1', 'partial': '0'}
IDENTITY_INPUT = 'runner/Package.swift'   # a digest input Meson never compiles
VALIDATOR_SOURCE = 'controller/tools/sb_api_validator/sb_api_validator.c'   # compiled, but not a digest input
RUST_BIN_SOURCE = 'controller/src/bin/sbpl-check.rs'


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def command(out, argv, *, cwd, env, timeout=600):
    """Keep raw output and a receipt, and reap the build's process group on timeout."""
    out.mkdir(parents=True, exist_ok=True)
    receipt = dict(argv=list(map(str, argv)), returncode=None, timed_out=False)
    started = time.monotonic()
    try:
        with (out / 'stdout').open('wb') as stdout, (out / 'stderr').open('wb') as stderr:
            process = subprocess.Popen(receipt['argv'], cwd=cwd, env=env, stdout=stdout,
                                       stderr=stderr, start_new_session=True)
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


def append(path, text):
    return dict(op='append', path=str(path), text=text)


def write(path, text):
    return dict(op='write', path=str(path), text=text)


def truncate(path, keep):
    return dict(op='truncate', path=str(path), keep=keep)


class Build:
    def __init__(self, name, status, stdout, stderr, receipts, dist, before):
        self.name, self.status, self.stdout, self.stderr = name, status, stdout, stderr
        self.receipts, self.dist, self.before = receipts, dist, before
        self.after = inventory(dist)
        self.app = dist / 'PolicyWitness.app'

    @property
    def output(self):
        return self.stdout + self.stderr

    def fired(self, label):
        return sum(label in r['fired'] for r in self.receipts)

    def calls(self, tool):
        return [r for r in self.receipts if r['tool'] == tool]

    def signed(self):
        """The targets of codesign --force calls, in order."""
        return [r['args'][-1] for r in self.receipts if r['tool'] == 'codesign' and '--force' in r['args']]


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
                         if k not in ('BUILD_XPC', 'PW_INSPECTION', 'DIST_DIR', 'CARGO_TARGET_DIR', 'CARGO_BUILD_TARGET',
                                      'RUSTFLAGS', 'BASH_ENV', 'ENV', 'PW_VERSION', 'PW_BUILD_NUMBER', 'DEVELOPER_DIR')}
        self.builddir = self.root / 'builddir'
        self.target = self.root / 'controller/target/release'
        self.minimum = plistlib.loads((self.root / 'Info.plist').read_bytes())['LSMinimumSystemVersion']
        self.ninja_minimum = re.search(r'^NINJA_MINIMUM="([^"]+)"$', self.script.decode(), re.M).group(1)
        self.host_triple = re.search(r'^host: (\S+)$', subprocess.check_output(['rustc', '-vV'], text=True), re.M).group(1)
        self.augment = sorted(p.name for p in (ROOT / 'runner/augments').glob('*.sb'))[0]
        self.aside = work / 'aside'
        self.aside.mkdir()
        self.config = work / 'config.json'
        self.prefix = ''
        self.records = []

    @staticmethod
    def wrappers(directory, names):
        directory.mkdir()
        for name in names:
            target = directory / name
            shutil.copy2(WRAPPER, target)
            target.chmod(0o755)
        return directory

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

    def build(self, name, variant, *, hooks=(), env=None, bin_dir=None, homebrew=True, previous=True):
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
        config = dict(tools=self.tools, receipt=str(receipt), hooks=list(hooks))
        save(self.config, config)
        save(case / 'fixture.json', dict(config, variant=variant, env=env or {}))
        environment = dict(self.base_env, PATH=self.path(bin_dir or self.bin, homebrew),
                           PW_BUILD_REFUSAL_CONFIG=str(self.config), IDENTITY=self.identity,
                           BUILD_XPC=VARIANTS[variant], PW_INSPECTION='1', DIST_DIR=str(dist),
                           PW_VERSION='0.0.0', PW_BUILD_NUMBER='0', CARGO_NET_OFFLINE='true', **(env or {}))
        status, stdout, stderr = command(case / 'build', ['bash', self.root / 'build.sh'], cwd=self.root, env=environment)
        receipts = [json.loads(line) for line in receipt.read_text().splitlines()] if receipt.exists() else []
        build = Build(name, status, stdout, stderr, receipts, dist, before)
        save(case / 'result.json', dict(status=status, fired=[f for r in receipts for f in r['fired']],
                                        signed=build.signed(), tools=[r['tool'] for r in receipts],
                                        before=before, after=build.after))
        assert (self.root / 'build.sh').read_bytes() == self.script, 'a control changed the build script'
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


def fired_once(build, label):
    assert build.fired(label) == 1, (build.name, label, build.receipts)


def no_evidence(build):
    for banner in ('Writing evidence manifest', 'Codesigning app bundle', 'Verifying signature', "Checking every executable's signer",
                   'Codesigning observer tool', 'Staging checked user guide', 'Creating zip'):
        assert banner not in build.stdout, (build.name, banner)
    assert not (build.app / 'Contents/Resources/Evidence').exists(), build.name
    assert not (build.dist / 'PolicyWitness.zip').exists(), build.name
    assert not (build.dist / 'PolicyWitness.md').exists(), build.name


BEFORE_TOOLCHAIN = ('Checking the native toolchain', 'Configuring native build', 'Compiling native executables', 'Assembling app bundle')
BEFORE_ASSEMBLY = ('Assembling app bundle', 'Checking host/worker identity again', 'Codesigning embedded MacOS tools')
BEFORE_SIGNING = ('Codesigning embedded MacOS tools', 'Codesigning embedded XPC services', 'Writing evidence manifest')


# ---- controls: one per refusal; the function name is the manifest's citation ----

def control_none(co, variant):
    """The valid neighbour: the same checkout, wrappers and variant package a signed app."""
    build = co.build('none', variant)
    assert build.status == 0, (build.status, build.stderr[-4000:])
    assert 'DONE:' in build.stdout
    assert (build.dist / 'PolicyWitness.zip').stat().st_size > 0
    assert (build.dist / 'PolicyWitness.md').read_bytes() == (co.root / 'docs/PolicyWitness.md').read_bytes()
    assert (build.app / 'Contents/XPCServices/PWRunner.xpc').exists() == (variant == 'full')
    assert any(r['tool'] == 'codesign' and '--verify' in r['args'] and r['status'] == 0 for r in build.receipts), build.receipts
    assert not any(f for r in build.receipts for f in r['fired']), build.receipts
    return build


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


def _cargo_output_removed(co, variant, binary, refusal):
    label = f'remove-{binary}'
    build = co.build(refusal, variant, hooks=[hook(label, 'cargo', [delete(co.target / binary)])])
    check(build, 2, f'expected {binary} binary at {co.target / binary}',
          present=('Building Rust controller + tools',), absent=BEFORE_TOOLCHAIN)
    fired_once(build, label)
    assert len(build.calls('cargo')) == 1, build.receipts
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    return build


def control_missing_controller(co, variant):
    return _cargo_output_removed(co, variant, 'policy-witness', 'missing_controller')


def control_missing_observer(co, variant):
    return _cargo_output_removed(co, variant, 'sandbox-log-observer', 'missing_observer')


def control_missing_sbpl_check(co, variant):
    return _cargo_output_removed(co, variant, 'sbpl-check', 'missing_sbpl_check')


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


def control_meson_ninja_missing(co, variant):
    """A PATH with Cargo and the system tools but neither meson nor ninja."""
    build = co.build('meson_ninja_missing', variant, bin_dir=co.bin_without_meson, homebrew=False)
    check(build, 2, 'meson and ninja are required for the native build (brew install meson ninja); see docs/SIGNING.md',
          present=('Building Rust controller + tools', 'Checking the native toolchain'),
          absent=('Configuring native build', 'Compiling native executables', 'Assembling app bundle'))
    assert len(build.calls('cargo')) == 1, build.receipts
    no_calls(build, 'meson', 'ninja', 'codesign', 'cp')
    preserved(build)
    return build


def control_ninja_old(co, variant):
    """A ninja that reports a version below the minimum the script states."""
    build = co.build('ninja_old', variant, hooks=[hook('old-ninja', 'ninja', args=['--version'], respond=dict(stdout='1.0.0\n', status=0))])
    check(build, 2, f'ninja 1.0.0 is older than the {co.ninja_minimum} minimum; see docs/SIGNING.md',
          present=('Checking the native toolchain',),
          absent=('Configuring native build', 'Compiling native executables', 'Assembling app bundle'))
    fired_once(build, 'old-ninja')
    assert [r['args'] for r in build.calls('ninja')] == [['--version']], build.receipts
    no_calls(build, 'meson', 'codesign', 'cp')
    preserved(build)
    return build


def control_meson_buildtype(co, variant):
    """A configured directory whose buildtype label departs while the levels it is derived from still agree."""
    assert (co.builddir / 'build.ninja').exists(), 'the valid neighbour configures the directory first'
    poison = co.meson('configure', str(co.builddir), '-Dbuildtype=custom', '-Doptimization=plain', '-Ddebug=false')
    assert poison.returncode == 0, poison.stdout + poison.stderr
    try:
        build = co.build('meson_buildtype', variant)
    finally:
        restore = co.meson('configure', str(co.builddir), '-Dbuildtype=plain')
        assert restore.returncode == 0, restore.stdout + restore.stderr
    check(build, 1, 'Assert failed: fixed native policy: buildtype must be plain (got custom)', where='output',
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


def control_missing_info_plist(co, variant):
    """Info.plist gone between the minimum step that read it and the assembly that copies it."""
    try:
        build = co.build('missing_info_plist', variant,
                         hooks=[hook('remove-info-plist', 'meson', [move(co.root / 'Info.plist', co.parked('Info.plist'))], first='compile')])
    finally:
        co.restore_aside('Info.plist')
    check(build, 2, f'missing {co.root / "Info.plist"} at repo root',
          present=('Assembling app bundle',), absent=('Checking host/worker identity again', 'Codesigning embedded MacOS tools'))
    fired_once(build, 'remove-info-plist')
    removed_previous(build)
    assert (build.app / 'Contents/MacOS').is_dir(), build.name
    assert not (build.app / 'Contents/Info.plist').exists(), build.name
    assert not (build.app / 'Contents/MacOS/policy-witness').exists(), 'the refusal copied an executable'
    assert not [r for r in build.calls('cp') if r['args'][-1].startswith(str(build.app))], build.receipts
    no_calls(build, 'codesign')
    return build


def control_missing_augments_dir(co, variant):
    """The augments directory gone after compile; the refusal lands between the tool copies and the embed steps."""
    try:
        build = co.build('missing_augments_dir', variant,
                         hooks=[hook('remove-augments', 'meson', [move(co.root / 'runner/augments', co.parked('runner/augments'))], first='compile')])
    finally:
        co.restore_aside('runner/augments')
    check(build, 2, f'missing augments source dir at {co.root / "runner/augments"}',
          present=('Assembling app bundle',),
          absent=('Embedding PW runner client', 'Skipping embedded XPC build', 'Checking host/worker identity again'))
    fired_once(build, 'remove-augments')
    removed_previous(build)
    assert (build.app / 'Contents/MacOS/sbpl-check').exists(), build.name
    assert not (build.app / 'Contents/Resources/Augments').exists(), build.name
    assert not (build.app / 'Contents/MacOS/pw-runner-client').exists(), build.name
    no_calls(build, 'codesign')
    return build


def control_missing_client_output(co, variant):
    """The client output gone between the native check and the client copy (full builds only)."""
    output = co.builddir / 'pw-runner-client'
    app = co.app(variant, 'missing_client_output')
    build = co.build('missing_client_output', variant,
                     hooks=[hook('remove-client', 'cp', [delete(output)], last=str(app / 'Contents/MacOS/sbpl-check'))])
    check(build, 2, f'expected Meson output at {output}',
          present=('Assembling app bundle', 'Embedding PW runner client'),
          absent=('Embedding PWRunner XPC services', 'Checking host/worker identity again'))
    fired_once(build, 'remove-client')
    removed_previous(build)
    assert not (build.app / 'Contents/MacOS/pw-runner-client').exists(), build.name
    assert not (build.app / 'Contents/XPCServices').exists(), build.name
    no_calls(build, 'codesign')
    return build


def _service_input_removed(co, variant, refusal, relative, message, *, parked_dir=False):
    """A service input gone after the client copy: the refusal precedes service assembly."""
    app = co.app(variant, refusal)
    try:
        build = co.build(refusal, variant, hooks=[hook('remove-input', 'cp', [move(co.root / relative, co.parked(relative))],
                                                       last=str(app / 'Contents/MacOS/pw-runner-client'))])
    finally:
        co.restore_aside(relative)
    check(build, 2, message, present=('Embedding PW runner client', 'Embedding PWRunner XPC services'),
          absent=('Checking host/worker identity again', 'Codesigning embedded MacOS tools'))
    fired_once(build, 'remove-input')
    removed_previous(build)
    assert not (build.app / 'Contents/XPCServices').exists(), build.name
    no_calls(build, 'codesign')
    return build


def control_missing_service_dir(co, variant):
    return _service_input_removed(co, variant, 'missing_service_dir', 'runner/Services/PWRunner',
                                  f'missing PWRunner service dir at {co.root / "runner/Services/PWRunner"}')


def control_missing_service_plist(co, variant):
    return _service_input_removed(co, variant, 'missing_service_plist', 'runner/Services/PWRunner/Info.plist',
                                  'PWRunner service is missing Info.plist')


def control_missing_host_output(co, variant):
    """The host output gone between the native check and the service assembly (full builds only)."""
    output = co.builddir / 'PWRunner'
    app = co.app(variant, 'missing_host_output')
    build = co.build('missing_host_output', variant,
                     hooks=[hook('remove-host', 'cp', [delete(output)], last=str(app / 'Contents/MacOS/pw-runner-client'))])
    check(build, 2, f'expected Meson output at {output}',
          present=('Embedding PW runner client', 'Embedding PWRunner XPC services'),
          absent=('Checking host/worker identity again', 'Codesigning embedded MacOS tools'))
    fired_once(build, 'remove-host')
    removed_previous(build)
    assert not (build.app / 'Contents/XPCServices').exists(), build.name
    no_calls(build, 'codesign')
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


def control_missing_entitlements(co, variant):
    """The entitlements plist gone during assembly; the refusal precedes every signature."""
    app = co.app(variant, 'missing_entitlements')
    relative = 'PolicyWitness.entitlements'
    try:
        build = co.build('missing_entitlements', variant,
                         hooks=[hook('remove-entitlements', 'cp', [move(co.root / relative, co.parked(relative))],
                                     last=str(app / 'Contents/MacOS/sbpl-check'))])
    finally:
        co.restore_aside(relative)
    check(build, 2, f'missing entitlements plist: {co.root / relative}',
          present=('Checking host/worker identity again, before signing',),
          absent=BEFORE_SIGNING)
    fired_once(build, 'remove-entitlements')
    removed_previous(build)
    no_calls(build, 'codesign')
    return build


def _tool_sign_refused(co, variant, refusal, actions, message):
    """A signing-list target damaged after the observer is signed: the next sign_macho refuses."""
    app = co.app(variant, refusal)
    build = co.build(refusal, variant, hooks=[hook('damage-target', 'codesign', actions,
                                                   last=str(app / 'Contents/MacOS/sandbox-log-observer'), contains='--force')])
    check(build, 2, message, present=('Codesigning embedded MacOS tools',),
          absent=('Codesigning embedded XPC services', 'Writing evidence manifest'))
    fired_once(build, 'damage-target')
    expected = ([str(app / 'Contents/MacOS/pw-runner-client')] if variant == 'full' else []) + [str(app / 'Contents/MacOS/sandbox-log-observer')]
    assert build.signed() == expected, (build.signed(), expected)
    no_evidence(build)
    return build


def control_sign_target_missing(co, variant):
    app = co.app(variant, 'sign_target_missing')
    target = app / 'Contents/MacOS/sbpl-check'
    return _tool_sign_refused(co, variant, 'sign_target_missing', [delete(target)], f'expected a Mach-O to sign at {target}')


def control_sign_target_not_macho(co, variant):
    app = co.app(variant, 'sign_target_not_macho')
    target = app / 'Contents/MacOS/sbpl-check'
    return _tool_sign_refused(co, variant, 'sign_target_not_macho', [write(target, 'not an executable\n')],
                              f'{target} is not a Mach-O; the signing list names only executables')


def control_missing_service_bundle(co, variant):
    """The assembled service bundle gone after the tools are signed (full builds only)."""
    app = co.app(variant, 'missing_service_bundle')
    bundle = app / 'Contents/XPCServices/PWRunner.xpc'
    build = co.build('missing_service_bundle', variant,
                     hooks=[hook('remove-service-bundle', 'codesign', [delete(bundle)], last=str(app / 'Contents/MacOS/sbpl-check'), contains='--force')])
    check(build, 2, f'expected XPC service bundle at {bundle}',
          present=('Codesigning embedded MacOS tools', 'Codesigning embedded XPC services'), absent=('Writing evidence manifest',))
    fired_once(build, 'remove-service-bundle')
    assert build.signed() == [str(app / 'Contents/MacOS' / name) for name in ('pw-runner-client', 'sandbox-log-observer', 'sbpl-check')], build.signed()
    no_evidence(build)
    return build


def control_missing_service_entitlements(co, variant):
    """The service entitlements gone before service signing (full builds only)."""
    app = co.app(variant, 'missing_service_entitlements')
    relative = 'runner/Services/PWRunner/Entitlements.plist'
    try:
        build = co.build('missing_service_entitlements', variant,
                         hooks=[hook('remove-service-entitlements', 'cp', [move(co.root / relative, co.parked(relative))],
                                     last=str(app / 'Contents/MacOS/pw-runner-client'))])
    finally:
        co.restore_aside(relative)
    check(build, 2, f'PWRunner service is missing Entitlements.plist at {co.root / relative}',
          present=('Codesigning embedded XPC services',), absent=('Writing evidence manifest',))
    fired_once(build, 'remove-service-entitlements')
    assert build.signed() == [str(app / 'Contents/MacOS' / name) for name in ('pw-runner-client', 'sandbox-log-observer', 'sbpl-check')], build.signed()
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
          present=('Writing evidence manifest (signed BOM)',),
          absent=('Codesigning app bundle', 'Verifying signature', 'Creating zip'))
    fired_once(build, 'remove-contents')
    assert str(app) not in build.signed(), build.signed()
    assert not (build.dist / 'PolicyWitness.zip').exists()
    assert not (build.dist / 'PolicyWitness.md').exists()
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
    return build


# The baseline's refusals in script order, with the variants each applies to.
CONTROLS = [
    ('sdk_unavailable', ('full', 'partial'), control_sdk_unavailable),
    ('missing_controller', ('full', 'partial'), control_missing_controller),
    ('missing_observer', ('full', 'partial'), control_missing_observer),
    ('missing_sbpl_check', ('full', 'partial'), control_missing_sbpl_check),
    ('cargo_artifact_elsewhere', ('full', 'partial'), control_cargo_artifact_elsewhere),
    ('cargo_failed', ('full', 'partial'), control_cargo_failed),
    ('meson_ninja_missing', ('full', 'partial'), control_meson_ninja_missing),
    ('ninja_old', ('full', 'partial'), control_ninja_old),
    ('meson_buildtype', ('full', 'partial'), control_meson_buildtype),
    ('meson_failed', ('full', 'partial'), control_meson_failed),
    ('native_sources_unreadable', ('full', 'partial'), control_native_sources_unreadable),
    ('missing_native_output', ('full', 'partial'), control_missing_native_output),
    ('missing_info_plist', ('full', 'partial'), control_missing_info_plist),
    ('missing_augments_dir', ('full', 'partial'), control_missing_augments_dir),
    ('missing_client_output', ('full',), control_missing_client_output),
    ('missing_service_dir', ('full',), control_missing_service_dir),
    ('missing_service_plist', ('full',), control_missing_service_plist),
    ('missing_host_output', ('full',), control_missing_host_output),
    ('stale_identity_presign', ('full', 'partial'), control_stale_identity_presign),
    ('missing_entitlements', ('full', 'partial'), control_missing_entitlements),
    ('sign_target_missing', ('full', 'partial'), control_sign_target_missing),
    ('sign_target_not_macho', ('full', 'partial'), control_sign_target_not_macho),
    ('missing_service_bundle', ('full',), control_missing_service_bundle),
    ('missing_service_entitlements', ('full',), control_missing_service_entitlements),
    ('codesign_failed', ('full', 'partial'), control_codesign_failed),
    ('evidence_failed', ('full', 'partial'), control_evidence_failed),
    ('verify_failed', ('full', 'partial'), control_verify_failed),
]


# ---- mutations: a guard removed or moved past its operation must fail its control ----

def _move_block(text, block, anchor):
    assert text.count(block) == 1 and text.count(anchor) == 1, (block[:60], anchor[:60])
    return text.replace(block, '', 1).replace(anchor, anchor + block, 1)


def _remove_block(text, block):
    assert text.count(block) == 1, block[:60]
    return text.replace(block, '', 1)


CONTROLLER_GUARD = ('if [[ ! -x "${RUNNER_BIN}" ]]; then\n'
                    '  echo "ERROR: expected policy-witness binary at ${RUNNER_BIN}" 1>&2\n'
                    '  exit 2\n'
                    'fi\n')
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
ENTITLEMENTS_GUARD = ('if [[ ! -f "${ENTITLEMENTS_PLIST}" ]]; then\n'
                      '  echo "ERROR: missing entitlements plist: ${ENTITLEMENTS_PLIST}" 1>&2\n'
                      '  exit 2\n'
                      'fi\n')
TOOL_SIGNING_ANCHOR = 'sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"\n'
MACHO_GUARD = ('  if ! /usr/bin/file -b "${target}" | /usr/bin/grep -q "Mach-O"; then\n'
               '    echo "ERROR: ${target} is not a Mach-O; the signing list names only executables" 1>&2\n'
               '    exit 2\n'
               '  fi\n')
SIGN_ANCHOR = '  codesign --force --options runtime --timestamp -s "${IDENTITY}" "${target}"\n'

MUTATIONS = [
    ('missing_controller', 'guard removed', lambda t: _remove_block(t, CONTROLLER_GUARD)),
    ('ninja_old', 'guard removed', lambda t: _remove_block(t, NINJA_GUARD)),
    ('missing_native_output', 'guard moved past assembly', lambda t: _move_block(t, NATIVE_OUTPUT_LOOP, ASSEMBLY_ANCHOR)),
    ('missing_entitlements', 'guard moved past tool signing', lambda t: _move_block(t, ENTITLEMENTS_GUARD, TOOL_SIGNING_ANCHOR)),
    ('sign_target_not_macho', 'check moved after codesign', lambda t: _move_block(t, MACHO_GUARD, SIGN_ANCHOR)),
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


def demonstrate_bypass(co):
    """A guard removed or moved past its operation must fail its control, in two stages.

    The mutated script alone never reaches the guard: the build's documentation
    and identity checks refuse a script that disagrees with the manifest or the
    digest, which the first stage records. With those self-checks removed the
    build runs to the displaced guard, and the second stage shows the control
    failing there. The original script then passes the same control again."""
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
                script.write_bytes(text.encode())
                co.script = text.encode()
                co.prefix = f'mutated-{stage}-{refusal}-'
                failure = _control_failure(functions[refusal], co, 'full')
                assert failure is not None, f'{refusal}: the control passed with the {label} ({stage} stage)'
                stages[stage] = failure
        finally:
            script.write_bytes(original)
            co.script = original
        assert any(marker in stages['self_checks'] for marker in SELF_CHECK_MARKERS), stages['self_checks']
        assert not any(marker in stages['guard'] for marker in SELF_CHECK_MARKERS), stages['guard']
        # The mutated runs may have torn down outputs the next control expects; the
        # original script rebuilds them, and the same control passes again.
        co.prefix = f'repeat-{refusal}-'
        functions[refusal](co, 'full')
        co.prefix = ''
        results.append(dict(refusal=refusal, mutation=label, self_check_refusal=stages['self_checks'], guard_failure=stages['guard']))
        print(f"mutation {refusal}: {label}; refused by the self-checks, then failed at the guard: {stages['guard'][:140]}", flush=True)
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
        mutations = demonstrate_bypass(co)
        save(out / 'mutations.json', mutations)
    expected = sum(len(applicable) for _, applicable, _ in CONTROLS) + len(VARIANTS)
    assert len(records) == expected, (len(records), expected)
    print(f'{expected} build refusal controls and {len(mutations)} bypass demonstrations passed')


if __name__ == '__main__':
    test_build_refusals(Path(sys.argv[1]).resolve(), sys.argv[2])
