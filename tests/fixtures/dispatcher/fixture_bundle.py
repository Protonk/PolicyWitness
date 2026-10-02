"""Fake app bundles for offline dispatch controls: layout and builder, pure Python.

`bundle(app, host)` lays out the shipped inventory with shell-script stand-ins,
except the XPC host, which must be a real Mach-O because the inspector runs
`nm -u` on it: `host` is the path of a stub compiled by
`tests/fixtures/dispatcher/build.sh` (the suite wrapper builds it once per run
and names it in `PW_DISPATCHER_HOST_FIXTURE`; a missing stub is an equipment
error here, never a compile on the side). This inventory is deliberately
independent of `tests/lib/artifact.py`'s `EXECUTABLES`: a mismatch fails the
valid control, which is the point.
"""
import json
from pathlib import Path
import plistlib

from seal_tool import fingerprint, seal as seal_paths

FILES = ['Contents/MacOS/' + name for name in
         ('policy-witness', 'pw-runner-client', 'sbpl-check', 'sandbox-log-observer', 'sb_api_validator')]
XPC = 'Contents/XPCServices/PWRunner.xpc'
FILES += [XPC + '/Contents/MacOS/' + name for name in ('PWRunner', 'pw-probe-runner', 'sb_api_validator')]
HOST = XPC + '/Contents/MacOS/PWRunner'


def seal(app):
    """Seal the app, its XPC bundle and every inventory file with the fake codesign's model."""
    seal_paths(app, [app, app / XPC, *(app / name for name in FILES)])


def bundle(app, host):
    host = Path(host)
    if not host.is_file():
        raise FileNotFoundError(f'compiled fixture host missing: {host} (build tests/fixtures/dispatcher/build.sh)')
    for name in FILES:
        path = app / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == HOST:
            path.write_bytes(host.read_bytes())
        else:
            path.write_text('#!/bin/sh\nexit 0\n')
        path.chmod(0o755)
    for directory, executable in ((app, 'policy-witness'), (app / XPC, 'PWRunner')):
        (directory / 'Contents/Info.plist').write_bytes(plistlib.dumps({
            'CFBundleIdentifier': 'fixture.' + executable, 'CFBundleExecutable': executable}))
    evidence = app / 'Contents/Resources/Evidence'
    evidence.mkdir(parents=True)
    (evidence / 'symbols.json').write_text('{}\n')
    entries = [dict(rel_path=name, sha256=fingerprint(app / name))
               for name in FILES[1:] + ['Contents/Resources/Evidence/symbols.json']]
    (evidence / 'manifest.json').write_text(json.dumps(dict(schema_version=1,
        app_bundle_id='fixture.policy-witness', app_binary_rel_path=FILES[0], entries=entries)))
    seal(app)
