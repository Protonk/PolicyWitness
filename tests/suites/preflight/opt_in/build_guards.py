"""Observe build refusals before assembly and packaging, with real toolchains and signatures."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(out, argv, *, cwd, env, timeout=600):
    """Keep raw output and a receipt, and reap the build's process group on timeout."""
    out.mkdir(parents=True)
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
    return receipt['returncode'], (out / 'stdout').read_text(), (out / 'stderr').read_text()


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def test_build_guards(out, identity):
    tools = {name: shutil.which(name) for name in ('cargo', 'meson', 'codesign')}
    assert all(tools.values()), tools
    assert identity.startswith('Developer ID Application: '), 'a Developer ID Application identity is required'
    base_env = {k: v for k, v in os.environ.items()
                if k not in ('BUILD_XPC', 'PW_INSPECTION', 'DIST_DIR', 'CARGO_TARGET_DIR',
                             'RUSTFLAGS', 'BASH_ENV', 'ENV', 'PW_VERSION', 'PW_BUILD_NUMBER')}
    scenarios = []
    with tempfile.TemporaryDirectory(prefix='pw-build-guards-', dir='/private/tmp') as temporary:
        work = Path(temporary)
        root = work / 'checkout'
        root.mkdir()
        # Copy working-tree bytes, including pending changes, without importing
        # the production caches, app, git metadata or test output.
        names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        for name in set(names.decode().split('\0')) - {''}:
            source, target = ROOT / name, root / name
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        script = (root / 'build.sh').read_bytes()
        config_path = work / 'config.json'
        bin_dir = work / 'bin'
        bin_dir.mkdir()
        for name in tools:
            target = bin_dir / name
            shutil.copy2(ROOT / 'tests/fixtures/build_guards/tools.py', target)
            target.chmod(0o755)
        minimum = plistlib.loads((root / 'Info.plist').read_bytes())['LSMinimumSystemVersion']
        wrong_minimum = '11.0' if minimum != '11.0' else '12.0'
        source = work / 'wrong.c'
        source.write_text('int main(void) { return 0; }\n')
        wrong_binary = work / 'wrong-minimum'
        status, _, stderr = command(out / 'compile-wrong-minimum',
            ['/usr/bin/xcrun', 'clang', f'-mmacosx-version-min={wrong_minimum}', source, '-o', wrong_binary],
            cwd=work, env=base_env)
        assert status == 0, stderr
        load_commands = subprocess.check_output(['/usr/bin/otool', '-l', wrong_binary], text=True)
        (out / 'wrong-minimum.load-commands').write_text(load_commands)
        assert f'minos {wrong_minimum}' in load_commands, load_commands

        for variant, xpc in (('full', '1'), ('partial', '0')):
            # The final loop members catch a check accidentally limited to the
            # first output, as well as a removed check or one moved past assembly.
            targets = {'cargo': root / 'controller/target/release/sbpl-check',
                       'meson': root / ('builddir/PWRunner' if xpc == '1' else 'builddir/pw-probe-runner')}
            for fault in ('cargo', 'meson', 'signer', 'none'):
                name = f'{variant}-{fault}'
                case = out / name
                case.mkdir()
                dist = work / f'dist-{name}'
                dist.mkdir()
                # A minimum refusal must preserve existing distribution bytes,
                # not merely leave a missing output directory missing.
                app = dist / 'PolicyWitness.app'
                app.mkdir()
                (app / 'previous-build').write_text('previous app\n')
                (dist / 'PolicyWitness.zip').write_bytes(b'previous zip\n')
                (dist / 'PolicyWitness.md').write_text('previous guide\n')
                before = inventory(dist)
                backup = work / 'original-output'
                config = dict(tools=tools, fault=fault, target=str(targets.get(fault, '')),
                              backup=str(backup), wrong_binary=str(wrong_binary),
                              dist=str(dist), receipt=str(case / 'tools.jsonl'))
                save(config_path, config)
                save(case / 'fixture.json', config)
                env = dict(base_env, PATH=str(bin_dir) + os.pathsep + base_env['PATH'],
                           PW_BUILD_GUARD_CONFIG=str(config_path), IDENTITY=identity,
                           BUILD_XPC=xpc, PW_INSPECTION='1', DIST_DIR=str(dist),
                           PW_VERSION='0.0.0', PW_BUILD_NUMBER='0', CARGO_NET_OFFLINE='true')
                try:
                    status, stdout, stderr = command(case / 'build', ['bash', root / 'build.sh'], cwd=root, env=env)
                    receipts = [json.loads(line) for line in (case / 'tools.jsonl').read_text().splitlines()]
                    injected = [r for r in receipts if r['injected']]
                    assert len(injected) == (0 if fault == 'none' else 1), receipts
                    if fault in targets:
                        assert status == 2, (name, status, stderr[-4000:])
                        assert f'{targets[fault]} is built for macOS {wrong_minimum}; Info.plist declares {minimum}' in stderr, stderr
                        assert 'Assembling app bundle' not in stdout, stdout
                        assert inventory(dist) == before, 'minimum refusal changed previous distribution output'
                        assert not any(r['tool'] == 'codesign' for r in receipts), receipts
                        if fault == 'cargo':
                            assert not any(r['tool'] == 'meson' for r in receipts), receipts
                        else:
                            assert 'Checking the configured native source lists and the identity closure against the tree' in stdout, stdout
                    else:
                        # This receipt observes successful deep verification, not
                        # just the banner printed before codesign was invoked.
                        assert any(r['tool'] == 'codesign' and '--verify' in r['args']
                                   and r['status'] == 0 for r in receipts), receipts
                        if fault == 'signer':
                            assert status == 1, (name, status, stderr[-4000:])
                            assert f'Contents/MacOS/sbpl-check: signed by ad hoc, not {identity}' in stderr, stderr
                            assert "Checking every executable's signer" in stdout, stdout
                            for banner in ('Codesigning observer tool (not embedded)', 'Staging checked user guide', 'Creating zip'):
                                assert banner not in stdout, stdout
                            assert not (dist / 'PolicyWitness.zip').exists()
                            assert not (dist / 'PolicyWitness.md').exists()
                            assert not any(r['tool'] == 'codesign' and '--force' in r['args']
                                           and r['args'][-1] == str(root / 'controller/target/release/sandbox-log-observer')
                                           for r in receipts), receipts
                        else:
                            assert status == 0, (name, status, stderr[-4000:])
                            assert 'DONE:' in stdout
                            assert (dist / 'PolicyWitness.zip').stat().st_size > 0
                            assert (dist / 'PolicyWitness.md').read_bytes() == (root / 'docs/PolicyWitness.md').read_bytes()
                            assert (app / 'Contents/XPCServices/PWRunner.xpc').exists() == (xpc == '1')
                    scenarios.append(dict(name=name, status=status, before=before, after=inventory(dist)))
                    save(out / 'controls.json', scenarios)
                    print(f'{name}: expected status {status}; protected operations checked', flush=True)
                finally:
                    if backup.exists():
                        shutil.copy2(backup, targets[fault])
                        backup.unlink()
                    assert (root / 'build.sh').read_bytes() == script, 'control changed the build script'
    assert len(scenarios) == 8, scenarios
    print('8 build ordering controls passed')


if __name__ == '__main__':
    test_build_guards(Path(sys.argv[1]).resolve(), sys.argv[2])
