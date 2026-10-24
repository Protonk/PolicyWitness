"""Fake app bundles for offline dispatch controls: layout and builder, pure Python.

`bundle(app, host)` lays out the shipped inventory around compiled stubs: every
executable must be a real Mach-O because the inspector reads each one's load
commands against the provenance record and runs `nm -u` on the XPC host.
`host` is the path of the clean stub compiled by
`tests/fixtures/dispatcher/build.sh` (the suite wrapper builds it once per run
and names it in `PW_DISPATCHER_HOST_FIXTURE`; a missing stub is an equipment
error here, never a compile on the side); the runnable controller stub beside
it (`<host>.controller`) stands in for the controller, and the clean stub for
every other executable. This inventory is deliberately independent of
`tests/lib/artifact.py`'s `EXECUTABLES`: a mismatch fails the valid control,
which is the point. `record(app)` writes a complete provenance record for a
full build, authored here: nominal toolchain and configuration values of the
documented shape, the stand-ins' hashes and load commands read with this
file's own `otool` parse, their architectures and container from `lipo -archs`
and their own header magic, and the signature facts the linker-signed
stand-ins carry (ad hoc, no leaf, team, runtime or timestamp). The stubs are
compiled for arm64 explicitly, so they are the output target whichever
architecture the compiler or the calling process defaults to. The inspector's checks
over that record are real and independent of this file, so a control that
keeps a stale record beside changed bytes must expect a provenance finding.
"""
import json
from pathlib import Path
import plistlib
import re
import subprocess

from seal_tool import fingerprint, seal as seal_paths

FILES = ['Contents/MacOS/' + name for name in
         ('policy-witness', 'pw-runner-client', 'sbpl-check')]
XPC = 'Contents/XPCServices/PWRunner.xpc'
FILES += [XPC + '/Contents/MacOS/' + name for name in
          ('PWRunner', 'pw-probe-runner', 'sb_api_validator', 'pw-extension-issuer')]
HOST = XPC + '/Contents/MacOS/PWRunner'
WORKER = XPC + '/Contents/MacOS/pw-probe-runner'
CONTROLLER = FILES[0]
RECORD = 'Contents/Resources/Evidence/provenance.json'
SYMBOLS = 'Contents/Resources/Evidence/symbols.json'


def seal(app):
    """Seal the app, its XPC bundle and every inventory file with the fake codesign's model."""
    seal_paths(app, [app, app / XPC, *(app / name for name in FILES)])


CARGO_TARGETS = {'Contents/MacOS/policy-witness', 'Contents/MacOS/sbpl-check'}
ZERO = '0' * 64
LINKER_SIGNED = dict(status='ok', leaf=None, team=None, timestamp=False, runtime=False, adhoc=True, developer_id_chain=False)


def load_commands(path):
    """UUID and LC_BUILD_VERSION as otool prints them, and the architectures and container, parsed here."""
    names = subprocess.run(['/usr/bin/lipo', '-archs', str(path)], capture_output=True, text=True, check=True, timeout=60).stdout.split()
    with open(path, 'rb') as stream:
        container = 'fat' if stream.read(4) in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf') else 'thin'
    text = subprocess.run(['/usr/bin/otool', '-l', str(path)], capture_output=True, text=True, check=True, timeout=60).stdout
    uuid = re.search(r'^\s*uuid (\S+)\s*$', text, re.M).group(1)
    block = text[text.index('cmd LC_BUILD_VERSION'):]
    block = block[:block.index('Load command')] if 'Load command' in block else block
    value = lambda key: re.search(r'^\s*' + key + r' (\S+)\s*$', block, re.M).group(1)
    tools = [dict(tool=tool, version=version) for tool, version in re.findall(r'^\s*tool (\S+)\s*\n\s*version (\S+)\s*$', block, re.M)]
    return dict(uuid=uuid, platform=value('platform'), minos=value('minos'), sdk=value('sdk'), tools=tools,
                architectures=names, container=container)


def record(app):
    """A full build's provenance record describing the stand-ins as they are now."""
    outputs = []
    for name in FILES:
        found = load_commands(app / name)
        entry = dict(rel_path=name, sha256=None if name == CONTROLLER else fingerprint(app / name), **found)
        if name == CONTROLLER:
            entry['note'] = 'fixture controller: its hash is outside the sealed record'
        else:
            entry['signature'] = dict(LINKER_SIGNED)
        if name in CARGO_TARGETS:
            entry['cargo'] = dict(status='reported', fresh=False,
                                  profile=dict(opt_level='3', debuginfo=0, debug_assertions=False, overflow_checks=False, test=False),
                                  package_id='fixture', executable='fixture',
                                  fingerprint=dict(status='unavailable', binding=None, limitation='fixture bundle'),
                                  effective_rustflags=None, note='fixture bundle',
                                  rustflags_source=dict(kind='none', resolved=True, tokens=[], overrides=[], agrees=None,
                                                        effective_source='fixture bundle'))
        outputs.append(entry)
    minimum, sdk = outputs[0]['minos'], outputs[0]['sdk']
    observed = lambda **fields: dict(status='ok', **fields)
    program = lambda source, command: dict(source=source, command=command, overrides=[], file=None, disabled=False)
    compiler = dict(configured=dict(command=['cc'], id='clang', version='0', full_version=None), observed=observed(command=['cc'], identity='fixture cc 0'))
    data = dict(
        schema_version=3, generated_at='2026-01-01T00:00:00Z',
        source=dict(commit=ZERO[:40], describe='fixture', dirty=False, version='0.0.0', build_number='0', worker_identity=ZERO,
                    input_hashes={name: ZERO for name in ('meson.build', 'meson.options', 'controller/Cargo.lock', 'Info.plist',
                                                          'PolicyWitness.entitlements', 'runner/Services/PWRunner/Entitlements.plist')}),
        toolchain=dict(
            developer_dir=dict(value='/fixture/Developer', source='xcode-select'),
            sdk=dict(path='/fixture/SDK', version=sdk, build='FIXTURE', source='xcrun --sdk macosx default'),
            xcode=dict(status='unknown', reason='launch_failed', returncode=None),
            compilers=dict(c=compiler, swift=dict(compiler, configured=dict(compiler['configured'], command=['swiftc'], id='llvm'))),
            rustc=observed(command='/fixture/rustc', source='default', identity='rustc 0.0.0 (fixture)', release='0.0.0', commit_hash='',
                           host='fixture', llvm_version='', wrappers={}, selection_environment={}, selection_note='fixture bundle',
                           selection=dict(files=[], launcher=dict(kind='cargo', toolchain=None),
                                          programs=dict(rustc=program('default', '/fixture/rustc'), wrapper=program('none', None),
                                                        workspace_wrapper=program('none', None)),
                                          target=dict(source='--target', triple='aarch64-apple-darwin', overrides=[]),
                                          env_entries={}, child_environment=dict(SDKROOT='/fixture/SDK', MACOSX_DEPLOYMENT_TARGET=minimum,
                                                                                 DEVELOPER_DIR=None, RUSTUP_TOOLCHAIN=None,
                                                                                 path_replaced_by_env=False, rustup_home_replaced_by_env=False))),
            cargo=observed(command='/fixture/cargo', version='cargo 0'), meson=observed(command='/fixture/meson', version='0'),
            ninja=observed(command='/fixture/ninja', version='0'),
            python=observed(command='/fixture/python3.14', realpath='/fixture/Cellar/python@3.14/3.14.8/bin/python3.14',
                            keg_version='3.14.8', version='3.14.8')),
        configuration=dict(
            knobs=dict(BUILD_XPC='1', PW_INSPECTION='1', PW_FRESH_BUILD='1'), meson_options=dict(status='unknown'),
            rustflags=dict(requested=dict(source='none', tokens=[]), flag_environment={}, note='fixture bundle'),
            requests={name: dict(state='unset') for name in ('SDKROOT', 'DEVELOPER_DIR', 'MACOSX_DEPLOYMENT_TARGET', 'CPATH',
                                                              'LIBRARY_PATH', 'MANPATH', 'LC_CTYPE')},
            output_target=dict(system='macos', platform='1', architecture='arm64', container='thin',
                               cargo_triple='aarch64-apple-darwin', note='fixture bundle'),
            meson_machines=dict(host=dict(system='darwin', cpu_family='aarch64'), build=dict(system='darwin', cpu_family='aarch64'),
                                note='fixture bundle'),
            deployment_target=minimum, sdkroot='/fixture/SDK',
            build_directories=dict(builddir=dict(state='created', replaced_by_fresh_mode=True, stamp='published'),
                                   cargo_release=dict(state='created', replaced_by_fresh_mode=True),
                                   cargo_target_release=dict(state='created', replaced_by_fresh_mode=True),
                                   fresh_mode=dict(requested=True, replacement={
                                       'builddir': dict(path='builddir', existed=True, removed=True),
                                       'cargo_release': dict(path='controller/target/release', existed=True, removed=True),
                                       'cargo_target_release': dict(path='controller/target/aarch64-apple-darwin/release',
                                                                    existed=True, removed=True)}),
                                   cargo_admission=dict(target_directory='/fixture/target', build_directory='/fixture/target')),
            toolchain_stamp=dict(scope_note='fixture bundle', projection=dict(status='unavailable', reason='fixture bundle'))),
        outputs=outputs,
        signing=dict(identity='fixture: linker-signed stand-ins',
                     nested=[dict(rel_path=o['rel_path'], leaf=None, team=None, timestamp=False) for o in outputs if 'signature' in o],
                     note='fixture bundle'),
        limits=['offline fixture bundle; no build produced it'])
    path = app / RECORD
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return path


def manifest(app):
    """The evidence manifest over the current bytes of every stand-in, the symbols file and the record."""
    entries = [dict(rel_path=name, sha256=fingerprint(app / name)) for name in FILES[1:] + [SYMBOLS, RECORD]]
    (app / 'Contents/Resources/Evidence/manifest.json').write_text(json.dumps(dict(
        schema_version=1, app_bundle_id='fixture.policy-witness', app_binary_rel_path=FILES[0], entries=entries)))


def bundle(app, host, worker=None):
    """`worker`, when given, is the stub laid at the worker path instead of `host`."""
    host = Path(host)
    base = host.with_name(host.name[:-len('.imports-sandbox')] if host.name.endswith('.imports-sandbox') else host.name)
    controller = base.with_name(base.name + '.controller')
    if not host.is_file() or not controller.is_file():
        raise FileNotFoundError(f'compiled fixture stubs missing: {host}, {controller} (build tests/fixtures/dispatcher/build.sh)')
    for name in FILES:
        path = app / name
        path.parent.mkdir(parents=True, exist_ok=True)
        stub = controller if name == CONTROLLER else Path(worker) if worker and name == WORKER else host
        path.write_bytes(stub.read_bytes())
        path.chmod(0o755)
    for directory, executable in ((app, 'policy-witness'), (app / XPC, 'PWRunner')):
        (directory / 'Contents/Info.plist').write_bytes(plistlib.dumps({
            'CFBundleIdentifier': 'fixture.' + executable, 'CFBundleExecutable': executable}))
    evidence = app / 'Contents/Resources/Evidence'
    evidence.mkdir(parents=True)
    (evidence / 'symbols.json').write_text('{}\n')
    record(app)
    manifest(app)
    seal(app)
