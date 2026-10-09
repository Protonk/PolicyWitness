#!/usr/bin/env python3
"""Every executable the bundle ships carries the build's signature.

build.sh runs this after the outer seal and the deep verification. It lists
the regular files directly under the app's Contents/MacOS and under each XPC
service's Contents/MacOS, whether or not the signing list named them, and
requires each to be a Mach-O whose signature names IDENTITY as its leaf
authority with the hardened runtime. The linker leaves every compiler output
ad hoc-signed, and an ad hoc executable passes the bundle seal, the deep
verification and the artifact inspector; only notarization would refuse it.
The dSYM bundles beside the Swift executables are sealed resources, not
executables, and are not listed.

    signer_check.py APP IDENTITY

Exit 1 with one line per executable that fails; exit 2 when the app has no
Contents directory or codesign cannot be run.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

CODESIGN = '/usr/bin/codesign'
MACHO_MAGICS = {b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe',
                b'\xca\xfe\xba\xbe'}


def executables(app):
    """The regular files directly under the app's and each service's code directory."""
    directories = [app / 'Contents/MacOS',
                   *sorted((app / 'Contents/XPCServices').glob('*.xpc/Contents/MacOS'))]
    return [path for directory in directories if directory.is_dir()
            for path in sorted(directory.iterdir()) if path.is_file() and not path.is_symlink()]


def signature(path):
    """Leaf authority, hardened-runtime flag and ad hoc status as codesign -dvv reports them.

    An unsigned file reports no leaf and is a finding, not an error."""
    result = subprocess.run([CODESIGN, '-dvv', str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        if 'not signed at all' in result.stderr:
            return dict(leaf=None, adhoc=False, runtime=False)
        raise OSError(f'codesign could not read {path}: {result.stderr.strip() or result.returncode}')
    text = result.stderr
    authorities = re.findall(r'^Authority=(.*)$', text, re.M)
    flags = re.search(r'flags=0x[0-9a-f]+\(([^)]*)\)', text)  # inside the CodeDirectory line
    return dict(leaf=authorities[0] if authorities else None,
                adhoc='Signature=adhoc' in text,
                runtime='runtime' in (flags.group(1).split(',') if flags else []))


def problems(app, identity):
    """One line per executable that is not a Mach-O signed by identity with the hardened runtime."""
    out = []
    for path in executables(app):
        relative = path.relative_to(app)
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic not in MACHO_MAGICS:
            out.append(f'{relative}: not a Mach-O; only executables belong in this directory')
            continue
        found = signature(path)
        if found['adhoc'] or found['leaf'] != identity:
            signer = 'ad hoc' if found['adhoc'] else (found['leaf'] or 'nobody')
            out.append(f'{relative}: signed by {signer}, not {identity}')
        elif not found['runtime']:
            out.append(f'{relative}: signed without the hardened runtime')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('app', type=Path)
    parser.add_argument('identity')
    args = parser.parse_args()
    app = args.app.resolve()
    if not (app / 'Contents').is_dir():
        print(f'signer check: {app} has no Contents directory', file=sys.stderr)
        return 2
    try:
        found = problems(app, args.identity)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f'signer check: {exc}', file=sys.stderr)
        return 2
    if found:
        print(f'executables not signed by {args.identity} with the hardened runtime:', file=sys.stderr)
        for line in found:
            print(f'  {line}', file=sys.stderr)
        return 1
    print(f'ok: {len(executables(app))} executables signed by {args.identity} with the hardened runtime')
    return 0


if __name__ == '__main__':
    sys.exit(main())
