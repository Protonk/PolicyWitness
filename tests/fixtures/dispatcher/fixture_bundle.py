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
which is the point. `record(app)` writes a provenance record describing the
stand-ins' current bytes and load commands; the inspector's checks over that
record are real, so a control that keeps a stale record beside changed bytes
must expect a provenance finding.
"""
import json
from pathlib import Path
import plistlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import build_provenance
from seal_tool import fingerprint, seal as seal_paths

FILES = ['Contents/MacOS/' + name for name in
         ('policy-witness', 'pw-runner-client', 'sbpl-check', 'sandbox-log-observer')]
XPC = 'Contents/XPCServices/PWRunner.xpc'
FILES += [XPC + '/Contents/MacOS/' + name for name in
          ('PWRunner', 'pw-probe-runner', 'sb_api_validator', 'pw-extension-issuer')]
HOST = XPC + '/Contents/MacOS/PWRunner'
CONTROLLER = FILES[0]
RECORD = 'Contents/Resources/Evidence/provenance.json'
SYMBOLS = 'Contents/Resources/Evidence/symbols.json'


def seal(app):
    """Seal the app, its XPC bundle and every inventory file with the fake codesign's model."""
    seal_paths(app, [app, app / XPC, *(app / name for name in FILES)])


def record(app):
    """A provenance record describing the stand-ins as they are now; the fixture's other sections are nominal."""
    outputs = []
    for name in FILES:
        metadata = build_provenance.output_metadata(app / name)
        if metadata.get('status') != 'ok':
            raise ValueError(f'fixture executable has no readable load commands: {name}')
        entry = dict(rel_path=name, uuid=metadata['uuid'], platform=metadata['platform'], minos=metadata['minos'],
                     sdk=metadata['sdk'], tools=metadata['tools'],
                     sha256=None if name == CONTROLLER else fingerprint(app / name))
        if name in build_provenance.CARGO_TARGETS:
            entry['cargo'] = dict(status='fixture')
        outputs.append(entry)
    data = dict(schema_version=build_provenance.SCHEMA_VERSION, generated_at='fixture', source=dict(kind='fixture'),
                toolchain=dict(kind='fixture'), configuration=dict(kind='fixture'), outputs=outputs,
                signing=dict(identity=None, nested=[]), limits=['offline fixture bundle; no build produced it'])
    path = app / RECORD
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return path


def manifest(app):
    """The evidence manifest over the current bytes of every stand-in, the symbols file and the record."""
    entries = [dict(rel_path=name, sha256=fingerprint(app / name)) for name in FILES[1:] + [SYMBOLS, RECORD]]
    (app / 'Contents/Resources/Evidence/manifest.json').write_text(json.dumps(dict(
        schema_version=1, app_bundle_id='fixture.policy-witness', app_binary_rel_path=FILES[0], entries=entries)))


def bundle(app, host):
    host = Path(host)
    base = host.with_name(host.name[:-len('.imports-sandbox')] if host.name.endswith('.imports-sandbox') else host.name)
    controller = base.with_name(base.name + '.controller')
    if not host.is_file() or not controller.is_file():
        raise FileNotFoundError(f'compiled fixture stubs missing: {host}, {controller} (build tests/fixtures/dispatcher/build.sh)')
    for name in FILES:
        path = app / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((controller if name == CONTROLLER else host).read_bytes())
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
