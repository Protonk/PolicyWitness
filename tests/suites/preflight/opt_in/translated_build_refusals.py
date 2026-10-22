"""Under Rosetta, the unchanged build script refuses at admission, through both entry points and in both variants.

A disposable admission fixture copies the working tree's tracked and unignored
files, plants previous distribution output, a session and the two cache
directories, holds the checkout lock independently and puts recording
wrappers for cargo, meson, ninja, codesign and cp first on a fixed PATH. A
wrapper records any call, a version probe included, and then fails. The
script run by a translated shell (`arch -x86_64 /bin/bash`) and `make build`
run by a translated make (`arch -x86_64 /usr/bin/make`) must refuse naming
sysctl.proc_translated=1, with SDKROOT unset or valid, leaving an empty
receipt list, the inventories as they were and the holder's lock untouched.
Make's own launch and its SDK check precede the script and are outside that
claim. Under translation the builder refusal also wins over --help, an
unknown argument, a bad knob, a missing tracked input and an invalid
SDKROOT, while make given an invalid SDKROOT on its command line refuses at
parse time and never enters the script. Invalid SDK requests run under the
ordinary shim-probe containment with arch inside it. Reaching admission needs
Rosetta and nothing else: no signed build, app, identity or compiler.
"""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shim_probe  # noqa: E402
import suite_run  # noqa: E402
from build_refusals import (NATIVE_REFUSAL, VARIANTS, WRAPPED, WRAPPER, SESSION, STAMP,  # noqa: E402
                            cache_inventory, command, inventory, lock_free, save)

TRANSLATED = NATIVE_REFUSAL.format(arm64='1', translated='1')
SYSTEM_PATH = '/usr/bin:/bin:/usr/sbin:/sbin'
FAILING_TOOL = '/usr/bin/false'
IDENTITY = 'Developer ID Application: Admission Fixture (FIXTURE000)'
HOLDER = b'{"pid": 0, "started_at_unix_ms": 0, "nonce": "translated-builder-control"}\n'


class Fixture:
    """A disposable checkout that only admission can reach: previous outputs, a session and caches to observe, and a held lock."""

    def __init__(self, work, out):
        self.work, self.out = work, out
        self.root = work / 'checkout'
        self.root.mkdir()
        names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        for name in set(names.decode().split('\0')) - {''}:
            source, target = ROOT / name, self.root / name
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        self.script = (self.root / 'build.sh').read_bytes()
        for relative, text in ((STAMP, '{"fixture": "stamp"}\n'), ('builddir/build.ninja', '# fixture\n'),
                               (SESSION, '{"fixture": "session"}\n'), ('controller/target/release/fixture', 'cache\n'),
                               ('dist/PolicyWitness.app/previous-build', 'previous app\n'),
                               ('dist/PolicyWitness.zip', 'previous zip\n'), ('dist/PolicyWitness.md', 'previous guide\n')):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            (self.root / relative).write_text(text)
        self.bin = work / 'bin'
        self.bin.mkdir()
        for name in WRAPPED:
            shutil.copy2(WRAPPER, self.bin / name)
            (self.bin / name).chmod(0o755)
        self.config = work / 'config.json'
        self.selected = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
        self.containment = None
        self.lock = self.root / 'tests/.checkout.lock'
        self.fd = None
        self.results = []

    def hold(self):
        self.fd = os.open(self.lock, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(self.fd, 0)
        os.write(self.fd, HOLDER)
        self.inode = os.fstat(self.fd).st_ino

    def release(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def contained(self):
        """The ordinary shim-probe containment, prepared once; the receipts directory stays writable."""
        if self.containment is None:
            self.containment = shim_probe.prepare(self.work / 'containment', write_paths=[self.out])
        return self.containment

    def run(self, name, variant, argv, env=None):
        case = self.out / f'{variant}-{name}'
        case.mkdir(parents=True)
        receipt = case / 'tools.jsonl'
        # Every wrapped tool would fail after recording its call: reaching admission needs none of them.
        save(self.config, dict(tools={tool: FAILING_TOOL for tool in WRAPPED}, receipt=str(receipt), hooks=[], stderr_canary=''))
        environment = dict(HOME=os.environ['HOME'], PATH=f'{self.bin}:{SYSTEM_PATH}', TMPDIR=os.environ.get('TMPDIR', '/tmp'),
                           PW_PYTHON=sys.executable, PYTHONCOERCECLOCALE='0', PW_BUILD_REFUSAL_CONFIG=str(self.config),
                           IDENTITY=IDENTITY, BUILD_XPC=VARIANTS[variant], PW_INSPECTION='1', PW_FRESH_BUILD='0',
                           DIST_DIR=str(self.root / 'dist'))
        environment.update(env or {})
        dist, caches = inventory(self.root / 'dist'), cache_inventory(self.root)
        status, stdout, stderr = command(case / 'build', argv, cwd=self.root, env=environment, timeout=120)
        receipts = [json.loads(line) for line in receipt.read_text().splitlines()] if receipt.exists() else []
        result = dict(name=name, variant=variant, argv=list(map(str, argv)),
                      env={k: v for k, v in environment.items() if k not in ('HOME', 'TMPDIR')}, status=status, stdout=stdout,
                      stderr=stderr, receipts=receipts, dist_unchanged=inventory(self.root / 'dist') == dist,
                      caches_unchanged=cache_inventory(self.root) == caches, lock_inode=self.lock.stat().st_ino,
                      lock_record=self.lock.read_text(), lock_held=not lock_free(self.root),
                      install_requests=shim_probe.installation_requests(stdout, stderr))
        save(case / 'result.json', result)
        self.results.append(result)
        assert (self.root / 'build.sh').read_bytes() == self.script, 'a control changed the build script'
        return result


def untouched(fixture, result):
    """No wrapped tool call, version probes included; distribution, session and caches as they were; the holder's lock held."""
    name = f"{result['variant']}-{result['name']}"
    assert result['receipts'] == [], (name, result['receipts'])
    assert result['dist_unchanged'] and result['caches_unchanged'], (name, 'a refused build changed outputs, the session or a cache')
    assert result['lock_inode'] == fixture.inode and result['lock_record'] == HOLDER.decode() and result['lock_held'], (name, 'lock')
    assert not result['install_requests'], (name, result['install_requests'])
    assert 'checkout busy' not in result['stderr'], (name, 'the front end was reached')


def refused_translated(fixture, result, *, make=False):
    name = f"{result['variant']}-{result['name']}"
    assert result['status'] == 2, (name, result['status'], result['stderr'][-2000:])
    errors = [line for line in result['stderr'].splitlines() if line.startswith('ERROR:')]
    assert errors == ['ERROR: ' + TRANSLATED], (name, result['stderr'][-2000:])
    if make:
        # Make echoes its recipe and reports the failed target; the script printed nothing else.
        assert '==> [build]' in result['stdout'], (name, result['stdout'][-2000:])
        assert 'usage:' not in result['stdout'] + result['stderr']
    else:
        assert result['stdout'] == '', (name, result['stdout'][-2000:])
    untouched(fixture, result)


def control_translated_builder(fixture, variant):
    """The script by a translated shell and make build by a translated make, each refused at admission naming
    sysctl.proc_translated=1; the builder refusal ahead of every other admission check; make's own SDK refusal first."""
    script = str(fixture.root / 'build.sh')
    shell = ['/usr/bin/arch', '-x86_64', '/bin/bash', script]
    make = ['/usr/bin/arch', '-x86_64', '/usr/bin/make', 'build']
    refused_translated(fixture, fixture.run('direct-sdk-unset', variant, shell))
    refused_translated(fixture, fixture.run('direct-sdk-valid', variant, shell, dict(SDKROOT=fixture.selected)))
    refused_translated(fixture, fixture.run('make-sdk-unset', variant, make), make=True)
    refused_translated(fixture, fixture.run('make-sdk-valid', variant, [*make, 'SDKROOT=' + fixture.selected]), make=True)
    for label, args, env in (('help', ['--help'], {}), ('unknown_argument', ['--bogus'], {}), ('knob', [], dict(PW_FRESH_BUILD='2'))):
        refused_translated(fixture, fixture.run(f'direct-{label}', variant, [*shell, *args], env))
    parked = fixture.work / 'Info.plist'
    shutil.move(str(fixture.root / 'Info.plist'), str(parked))
    try:
        refused_translated(fixture, fixture.run('direct-missing_tree_input', variant, shell))
    finally:
        shutil.move(str(parked), str(fixture.root / 'Info.plist'))
    invalid = '/private/tmp/pw-no-such-sdk-' + os.urandom(4).hex()
    contained = fixture.contained()
    containment_env = dict(TMPDIR=str(fixture.work / 'containment/tmp'))
    refused_translated(fixture, fixture.run('direct-sdk-invalid', variant, [*contained, *shell], dict(containment_env, SDKROOT=invalid)))
    result = fixture.run('make-sdk-invalid', variant, [*contained, *make, 'SDKROOT=' + invalid], containment_env)
    name = f'{variant}-make-sdk-invalid'
    assert result['status'] == 2, (name, result['stderr'][-2000:])
    assert f'admission: SDKROOT={invalid} does not resolve to an SDK with a numeric version' in result['stderr'], (name, result['stderr'])
    assert TRANSLATED not in result['stderr'] and '==> [build]' not in result['stdout'], (name, 'make entered the recipe')
    untouched(fixture, result)


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    equipment = suite_run.rosetta_probe()
    save(out / 'rosetta-equipment.json', equipment)
    assert equipment['ok'], f'Rosetta is required equipment for this case: {equipment}'
    with tempfile.TemporaryDirectory(prefix='pw-translated-refusals-', dir='/private/tmp') as temporary:
        fixture = Fixture(Path(temporary), out)
        fixture.hold()
        try:
            for variant in VARIANTS:
                control_translated_builder(fixture, variant)
                print(f'{variant}: translated builds refused at admission through both entry points', flush=True)
        finally:
            fixture.release()
            save(out / 'results.json', [{k: v for k, v in r.items() if k not in ('stdout', 'stderr')} for r in fixture.results])
        assert lock_free(fixture.root)
    print(f'{len(fixture.results)} translated admission runs refused before the lock, any tool or any write')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
