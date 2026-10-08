#!/usr/bin/env python3
"""Make a signed, disposable copy of an app with its native executables replaced.

This is the signed-copy substitution the Meson migration uses to test
Meson-built executables inside an otherwise untouched baseline app. It copies
the baseline with ditto to a fresh directory under /private/tmp, replaces the
worker, validator, client and host, gives the app and its XPC service fresh
bundle identifiers so launchd cannot confuse the copy with the baseline, signs
the replaced helpers and client, then the service with its entitlements,
regenerates the evidence manifest from the signed bytes, signs the outer app
with its entitlements, verifies the signatures and runs the shared artifact
inspection. The baseline is never modified; its inventory is checked after.

    native_substitute.py --baseline APP --out OUT --identity IDENTITY \\
        --worker PATH --validator PATH --client PATH --host PATH

Prints the copy's path. Every command leaves a receipt under OUT.
"""
import argparse
import hashlib
import json
import plistlib
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import artifact

SERVICE = Path(artifact.SERVICE)
REPLACEMENTS = {
    'worker': SERVICE / 'Contents/MacOS/pw-probe-runner',
    'validator': SERVICE / 'Contents/MacOS/sb_api_validator',
    'host': SERVICE / 'Contents/MacOS/PWRunner',
    'client': Path('Contents/MacOS/pw-runner-client'),
}
SERVICE_ENTITLEMENTS = ROOT / 'runner/Services/PWRunner/Entitlements.plist'
APP_ENTITLEMENTS = ROOT / 'PolicyWitness.entitlements'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def command(out, argv, *, timeout=120):
    out.mkdir(parents=True)
    argv = [str(a) for a in argv]
    record = dict(argv=argv, returncode=None)
    save(out / 'command.json', record)
    started = time.monotonic()
    with (out / 'stdout').open('wb') as stdout, (out / 'stderr').open('wb') as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=timeout)
    record.update(returncode=result.returncode, elapsed_seconds=round(time.monotonic() - started, 3))
    save(out / 'command.json', record)
    if result.returncode != 0:
        raise SystemExit(f'command failed ({out}): {(out / "stderr").read_text()}')
    return record


def sign(out, identity, target, entitlements=None):
    argv = ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp']
    if entitlements:
        argv += ['--entitlements', entitlements]
    command(out, argv + ['-s', identity, target])


def substitute(baseline, out, identity, replacements, work_parent='/private/tmp'):
    baseline = Path(baseline).resolve()
    out.mkdir(parents=True)
    before = artifact.inventory(baseline)
    save(out / 'baseline-inventory.json', before)
    work = Path(tempfile.mkdtemp(prefix='pw-meson-copy-', dir=work_parent))
    app = work / 'PolicyWitness.app'
    command(out / 'copy', ['/usr/bin/ditto', baseline, app])
    replaced = {}
    for name, relative in REPLACEMENTS.items():
        source = Path(replacements[name]).resolve()
        target = app / relative
        replaced[str(relative)] = dict(source=str(source), source_sha256=artifact.digest(source),
                                       replaced_sha256=artifact.digest(target))
        shutil.copy2(source, target)
        target.chmod(0o755)
    identifiers = {}
    for bundle, prefix in ((app, 'com.policywitness.test.meson.a'), (app / SERVICE, 'com.policywitness.test.meson.s')):
        plist = bundle / 'Contents/Info.plist'
        value = plistlib.loads(plist.read_bytes())
        identifiers[str(bundle.relative_to(work))] = dict(before=value['CFBundleIdentifier'])
        value['CFBundleIdentifier'] = prefix + secrets.token_hex(10)
        identifiers[str(bundle.relative_to(work))]['after'] = value['CFBundleIdentifier']
        plist.write_bytes(plistlib.dumps(value))
    save(out / 'replaced.json', dict(app=str(app), replacements=replaced, bundle_identifiers=identifiers))
    for name in ('worker', 'validator'):
        sign(out / f'sign-{name}', identity, app / REPLACEMENTS[name])
    sign(out / 'sign-client', identity, app / REPLACEMENTS['client'])
    sign(out / 'sign-service', identity, app / SERVICE, SERVICE_ENTITLEMENTS)
    command(out / 'evidence', ['/usr/bin/python3', ROOT / 'tests/build-evidence.py', '--app-bundle', app,
                               '--app-entitlements', APP_ENTITLEMENTS])
    sign(out / 'sign-app', identity, app, APP_ENTITLEMENTS)
    command(out / 'verify', ['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', app])
    report = artifact.inspect(app)
    save(out / 'artifact.json', report)
    if not report['ok']:
        raise SystemExit(f'artifact inspection failed: {report["errors"]}')
    save(out / 'copy-inventory.json', artifact.inventory(app))
    save(out / 'hashes.json', {str(rel): artifact.digest(app / rel) for rel in list(REPLACEMENTS.values()) + [Path(artifact.MANIFEST)]})
    if artifact.inventory(baseline) != before:
        raise SystemExit('baseline app changed during substitution')
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    for name in REPLACEMENTS:
        parser.add_argument(f'--{name}', type=Path, required=True)
    args = parser.parse_args()
    app = substitute(args.baseline, args.out.resolve(), args.identity,
                     {name: getattr(args, name) for name in REPLACEMENTS})
    print(app)
    return 0


if __name__ == '__main__':
    sys.exit(main())
