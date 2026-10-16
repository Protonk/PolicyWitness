"""Observe build refusals before assembly and packaging, with real toolchains and signatures.

Each scenario drives the unchanged build script in a disposable checkout with
one fault injected by a tool wrapper: a Cargo or Meson output replaced by a
real Mach-O built for another macOS minimum, one or every shipped output
replaced by a Mach-O built against another installed SDK, a helper signed ad
hoc, or a helper, the XPC seal or the app seal signed without a secure
timestamp (`--timestamp=none`; merely omitting the flag is not a reliable
fault). The script's own checks make every refusal; the scenario asserts the
diagnostic, the status, the banners before and after, the signatures that
were and were not made, the preserved or absent outputs, and inspects a
timestamp-less signature independently before crediting the refusal.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import build_provenance


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(out, argv, *, cwd, env, timeout=900):
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
    return receipt['returncode'], (out / 'stdout').read_text(errors='replace'), (out / 'stderr').read_text(errors='replace')


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def other_sdk(selected_version):
    """An installed macOS SDK whose numeric version differs from the selected one; equipment, not a fabrication."""
    roots = [Path('/Library/Developer/CommandLineTools/SDKs'),
             Path(subprocess.check_output(['/usr/bin/xcode-select', '-p'], text=True).strip()) / 'Platforms/MacOSX.platform/Developer/SDKs']
    wanted = build_provenance.normalize_version(selected_version)
    for base in roots:
        for sdk in sorted(base.glob('MacOSX*.sdk')) if base.is_dir() else []:
            if sdk.is_symlink():
                continue
            try:
                version = plistlib.loads((sdk / 'SDKSettings.plist').read_bytes()).get('Version')
            except (OSError, ValueError):
                continue
            if build_provenance.normalize_version(str(version)) not in (None, wanted):
                return sdk, str(version)
    return None, None


def display(path):
    text = subprocess.run(['/usr/bin/codesign', '-dvv', str(path)], capture_output=True, text=True, timeout=60).stderr
    return dict(timestamp=bool(re.search(r'^Timestamp=', text, re.M)), signed_time=bool(re.search(r'^Signed Time=', text, re.M)),
                leaf=(re.findall(r'^Authority=(.*)$', text, re.M) or [None])[0], adhoc='Signature=adhoc' in text)


def test_build_guards(out, identity):
    tools = {name: shutil.which(name) for name in ('cargo', 'meson', 'codesign')}
    assert all(tools.values()), tools
    assert identity.startswith('Developer ID Application: '), 'a Developer ID Application identity is required'
    base_env = {k: v for k, v in os.environ.items()
                if k not in ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD', 'DIST_DIR', 'CARGO_TARGET_DIR', 'CARGO_BUILD_BUILD_DIR',
                             'RUSTFLAGS', 'BASH_ENV', 'ENV', 'PW_VERSION', 'PW_BUILD_NUMBER', 'PW_CHECKOUT_LOCK_FD',
                             'PW_CHECKOUT_LOCK_ROOT', 'PW_CHECKOUT_LOCK_NONCE')}
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
        # A real Mach-O built against another installed SDK, with the plist's minimum, so only the SDK check can tell it apart.
        selected_sdk = subprocess.check_output(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version'], text=True).strip()
        sdk, sdk_version = other_sdk(selected_sdk)
        assert sdk is not None, f'equipment: no installed macOS SDK with a version other than the selected {selected_sdk}'
        wrong_sdk_binary = work / 'wrong-sdk'
        status, _, stderr = command(out / 'compile-wrong-sdk',
            ['/usr/bin/xcrun', 'clang', '-isysroot', sdk, f'-mmacosx-version-min={minimum}', source, '-o', wrong_sdk_binary],
            cwd=work, env=base_env)
        assert status == 0, stderr
        metadata = build_provenance.output_metadata(wrong_sdk_binary)
        (out / 'wrong-sdk.load-commands').write_text(json.dumps(metadata, indent=2))
        assert metadata['minos'] == minimum and build_provenance.normalize_version(metadata['sdk']) == build_provenance.normalize_version(sdk_version), metadata
        assert build_provenance.normalize_version(metadata['sdk']) != build_provenance.normalize_version(selected_sdk)
        save(out / 'equipment.json', dict(selected_sdk=selected_sdk, other_sdk=str(sdk), other_sdk_version=sdk_version, minimum=minimum, wrong_minimum=wrong_minimum))

        cargo_outputs = [root / 'controller/target/release' / name for name in ('policy-witness', 'sandbox-log-observer', 'sbpl-check')]
        for variant, xpc in (('full', '1'), ('partial', '0')):
            meson_outputs = [root / 'builddir' / name for name in ('sb_api_validator', 'pw-probe-runner', 'pw-extension-issuer')]
            if xpc == '1':
                meson_outputs += [root / 'builddir/pw-runner-client', root / 'builddir/PWRunner']
            # The final loop members catch a check accidentally limited to the
            # first output, as well as a removed check or one moved past assembly.
            last = {'cargo': cargo_outputs[-1], 'meson': meson_outputs[-1]}
            faults = ['cargo', 'meson', 'sdk_cargo', 'sdk_all', 'signer', 'timestamp_helper', 'timestamp_app']
            if xpc == '1':
                faults.insert(6, 'timestamp_seal')
            faults.append('none')
            for fault in faults:
                name = f'{variant}-{fault}'
                case = out / name
                case.mkdir()
                dist = work / f'dist-{name}'
                dist.mkdir()
                # A refusal before assembly must preserve existing distribution bytes,
                # not merely leave a missing output directory missing.
                app = dist / 'PolicyWitness.app'
                app.mkdir()
                (app / 'previous-build').write_text('previous app\n')
                (dist / 'PolicyWitness.zip').write_bytes(b'previous zip\n')
                (dist / 'PolicyWitness.md').write_text('previous guide\n')
                before = inventory(dist)
                backups = work / 'backups'
                config = dict(tools=tools, fault=fault, backups=str(backups), receipt=str(case / 'tools.jsonl'), replacements=[])
                if fault in ('cargo', 'meson'):
                    config['replacements'] = [dict(tool=fault, first='build' if fault == 'cargo' else 'compile',
                                                   targets=[str(last[fault])], source=str(wrong_binary))]
                elif fault == 'sdk_cargo':
                    config['replacements'] = [dict(tool='cargo', first='build', targets=[str(cargo_outputs[-1])], source=str(wrong_sdk_binary))]
                elif fault == 'sdk_all':
                    config['replacements'] = [dict(tool='cargo', first='build', targets=list(map(str, cargo_outputs)), source=str(wrong_sdk_binary)),
                                              dict(tool='meson', first='compile', targets=list(map(str, meson_outputs)), source=str(wrong_sdk_binary))]
                elif fault == 'signer':
                    config['codesign'] = dict(target=str(app / 'Contents/MacOS/sbpl-check'), argv=['--force', '--options', 'runtime', '-s', '-'])
                elif fault.startswith('timestamp_'):
                    target = {'helper': app / 'Contents/MacOS/sbpl-check', 'seal': app / 'Contents/XPCServices/PWRunner.xpc', 'app': app}[fault[len('timestamp_'):]]
                    argv = ['--force', '--options', 'runtime', '--timestamp=none']
                    if fault == 'timestamp_seal':
                        argv += ['--entitlements', str(root / 'runner/Services/PWRunner/Entitlements.plist')]
                    if fault == 'timestamp_app':
                        argv += ['--entitlements', str(root / 'PolicyWitness.entitlements')]
                    config['codesign'] = dict(target=str(target), argv=argv + ['-s', identity])
                save(config_path, config)
                save(case / 'fixture.json', config)
                env = dict(base_env, PATH=str(bin_dir) + os.pathsep + base_env['PATH'],
                           PW_BUILD_GUARD_CONFIG=str(config_path), IDENTITY=identity,
                           BUILD_XPC=xpc, PW_INSPECTION='1', DIST_DIR=str(dist),
                           PW_VERSION='0.0.0', PW_BUILD_NUMBER='0', CARGO_NET_OFFLINE='true')
                try:
                    status, stdout, stderr = command(case / 'build', ['bash', root / 'build.sh'], cwd=root, env=env)
                    receipts = [json.loads(line) for line in (case / 'tools.jsonl').read_text().splitlines()]
                    injected = [i for r in receipts for i in r['injected']]
                    expected_injections = {'none': 0, 'cargo': 1, 'meson': 1, 'sdk_cargo': 1, 'sdk_all': len(cargo_outputs) + len(meson_outputs)}.get(fault, 1)
                    assert len(injected) == expected_injections, (fault, injected)
                    signed = [r['args'][-1] for r in receipts if r['tool'] == 'codesign' and '--force' in r['args']]
                    if fault in ('cargo', 'meson'):
                        assert status == 2, (name, status, stderr[-4000:])
                        assert f'{last[fault]} is built for macOS {wrong_minimum}; Info.plist declares {minimum}' in stderr, stderr
                        assert 'Assembling app bundle' not in stdout, stdout
                        assert inventory(dist) == before, 'minimum refusal changed previous distribution output'
                        assert not any(r['tool'] == 'codesign' for r in receipts), receipts
                        if fault == 'cargo':
                            # The stamp check probes meson's version before Cargo; no configure, setup or compile may follow.
                            assert not any(r['tool'] == 'meson' and r['args'][:1] != ['--version'] for r in receipts), receipts
                        else:
                            assert 'Checking the configured native source lists and the identity closure against the tree' in stdout, stdout
                    elif fault in ('sdk_cargo', 'sdk_all'):
                        # The minimum check passes the substitute; the SDK comparison names every disagreeing output before assembly.
                        assert status == 1, (name, status, stderr[-4000:])
                        assert 'shipped outputs disagree with the selected SDK version' in stderr, stderr[-4000:]
                        named = cargo_outputs[-1:] if fault == 'sdk_cargo' else cargo_outputs + meson_outputs
                        for path in named:
                            assert f'{path}: built against SDK {metadata["sdk"]}; the selected SDK is {selected_sdk}' in stderr, (path, stderr[-4000:])
                        assert 'Checking the configured native source lists' in stdout and 'Assembling app bundle' not in stdout, stdout
                        assert inventory(dist) == before, 'SDK refusal changed previous distribution output'
                        assert not any(r['tool'] == 'codesign' for r in receipts), receipts
                        assert not (root / 'dist/PolicyWitness.app').exists()
                    else:
                        # This receipt observes successful deep verification, not
                        # just the banner printed before codesign was invoked.
                        assert any(r['tool'] == 'codesign' and '--verify' in r['args']
                                   and r['status'] == 0 for r in receipts), receipts
                        if fault == 'signer':
                            assert status == 1, (name, status, stderr[-4000:])
                            assert f'Contents/MacOS/sbpl-check: signed by ad hoc, not {identity}' in stderr, stderr
                        if fault.startswith('timestamp_'):
                            assert status == 1, (name, status, stderr[-4000:])
                            label = {'timestamp_helper': 'Contents/MacOS/sbpl-check', 'timestamp_seal': 'Contents/XPCServices/PWRunner.xpc seal',
                                     'timestamp_app': 'app seal'}[fault]
                            assert f'{label}: no secure timestamp (only a Signed Time, the signer\'s own clock)' in stderr, stderr[-4000:]
                            # Independent inspection of the signature that was actually made.
                            facts = display(config['codesign']['target'])
                            save(case / 'signature-display.json', facts)
                            assert facts['signed_time'] and not facts['timestamp'] and facts['leaf'] == identity and not facts['adhoc'], facts
                            assert config['codesign']['target'] in signed, (signed, config['codesign']['target'])
                        if fault != 'none':
                            assert "Checking every executable's signer" in stdout, stdout
                            for banner in ('Codesigning observer tool (not embedded)', 'Staging checked user guide', 'Creating zip'):
                                assert banner not in stdout, stdout
                            assert not (dist / 'PolicyWitness.zip').exists()
                            assert not (dist / 'PolicyWitness.md').exists()
                            assert str(root / 'controller/target/release/sandbox-log-observer') not in signed, signed
                        else:
                            assert status == 0, (name, status, stderr[-4000:])
                            assert 'DONE:' in stdout
                            assert (dist / 'PolicyWitness.zip').stat().st_size > 0
                            assert (dist / 'PolicyWitness.md').read_bytes() == (root / 'docs/PolicyWitness.md').read_bytes()
                            assert (app / 'Contents/XPCServices/PWRunner.xpc').exists() == (xpc == '1')
                            facts = display(app)
                            assert facts['timestamp'] and facts['leaf'] == identity, facts
                    scenarios.append(dict(name=name, status=status, before=before, after=inventory(dist), injected=injected))
                    save(out / 'controls.json', scenarios)
                    print(f'{name}: expected status {status}; protected operations checked', flush=True)
                finally:
                    if backups.exists():
                        for replacement in config['replacements']:
                            for path in replacement['targets']:
                                backup = backups / Path(path).name
                                if backup.exists():
                                    shutil.copy2(backup, path)
                                    backup.unlink()
                        shutil.rmtree(backups)
                    assert (root / 'build.sh').read_bytes() == script, 'control changed the build script'
    assert len(scenarios) == 17, scenarios
    print(f'{len(scenarios)} build ordering controls passed')


if __name__ == '__main__':
    test_build_guards(Path(sys.argv[1]).resolve(), sys.argv[2])
