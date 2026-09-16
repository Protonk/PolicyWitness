"""Independent fake bundles and codesign equipment for offline dispatch controls.

Only isolated copies of artifact.py point to this executable. Production has no
environment override or switch to bypass signing checks. Seals live outside the
app; they are a file-change model, not a claim about Apple's signing behavior.
"""
import hashlib
import json
from pathlib import Path
import plistlib
import sys

FILES = ['Contents/MacOS/' + name for name in
         ('policy-witness', 'pw-runner-client', 'sbpl-check', 'sandbox-log-observer', 'sb_api_validator')]
XPC = 'Contents/XPCServices/PWRunner.xpc'
FILES += [XPC + '/Contents/MacOS/' + name for name in ('PWRunner', 'pw-probe-runner', 'sb_api_validator')]


def fingerprint(path):
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


def seal(app):
    targets = [app, app / XPC, *(app / name for name in FILES)]
    seals = {str(p): fingerprint(p) for p in targets}
    app.with_suffix('.fixture-seals.json').write_text(json.dumps(seals))


def bundle(app):
    for name in FILES:
        path = app / name
        path.parent.mkdir(parents=True, exist_ok=True)
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


def main():
    target = Path(sys.argv[-1]).resolve()
    app = next(p for p in (target, *target.parents) if p.suffix == '.app')
    receipt = app.with_suffix('.fixture-verification.jsonl')
    with receipt.open('a') as stream:
        stream.write(json.dumps(sys.argv[1:]) + '\n')
    try:
        seals = json.loads(app.with_suffix('.fixture-seals.json').read_text())
        valid = target.exists() and seals[str(target)] == fingerprint(target)
    except (OSError, KeyError):
        valid = False
    if not valid:
        print('fixture signature invalid', file=sys.stderr)
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
