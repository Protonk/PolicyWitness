#!/usr/bin/env python3
"""Every executable and both seals carry the build's signature with its guarantees.

build.sh runs this after the outer seal and the deep verification. It lists
the regular files directly under the app's Contents/MacOS and under each XPC
service's Contents/MacOS, whether or not the signing list named them, plus the
app seal and each service seal, and reads each signature as `codesign -dvv`
displays it. Each executable must be a Mach-O; each signature must name
IDENTITY as its leaf authority, carry the hardened runtime, chain through the
Developer ID Certification Authority to the Apple Root CA, carry the team
identifier the leaf names, and carry a secure timestamp (`Timestamp=`; a
`Signed Time=` line is the signer's clock, not a timestamp authority's). The
linker leaves every compiler output ad hoc-signed, and an ad hoc executable
can pass the bundle seal and deep verification. This check refuses it before
packaging; the artifact inspector separately rejects listed executables whose
signer differs from the controller's. The dSYM bundles beside the Swift
executables are sealed resources, not executables, and are not listed.

Display output that cannot be read establishes nothing: an unreadable chain
or timestamp line is a finding, not a pass. Real signature verification runs
beside this parser in the build; this check reads what codesign displays.

    signer_check.py APP IDENTITY

Prints one bounded observation line per signature. Exit 1 with one line per
signature that fails; exit 2 when the app has no Contents directory or
codesign cannot be run.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

CODESIGN = '/usr/bin/codesign'
MACHO_MAGICS = {b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe',
                b'\xca\xfe\xba\xbe'}
DEVELOPER_ID_CA = 'Developer ID Certification Authority'
APPLE_ROOT = 'Apple Root CA'
TEAM_RE = re.compile(r'\(([A-Z0-9]{10})\)\s*$')


def executables(app):
    """The regular files directly under the app's and each service's code directory."""
    directories = [app / 'Contents/MacOS',
                   *sorted((app / 'Contents/XPCServices').glob('*.xpc/Contents/MacOS'))]
    return [path for directory in directories if directory.is_dir()
            for path in sorted(directory.iterdir()) if path.is_file() and not path.is_symlink()]


def seals(app):
    """The app itself and each embedded XPC service bundle."""
    return [app, *sorted((app / 'Contents/XPCServices').glob('*.xpc'))]


def parse_display(text):
    """The facts a codesign -dvv display establishes; `readable` is False when the display is ambiguous."""
    authorities = re.findall(r'^Authority=(.*)$', text, re.M)
    flags = re.search(r'^CodeDirectory .*flags=0x[0-9a-f]+\(([^)]*)\)', text, re.M)
    teams = re.findall(r'^TeamIdentifier=(.*)$', text, re.M)
    timestamps = re.findall(r'^Timestamp=(.*)$', text, re.M)
    signed_times = re.findall(r'^Signed Time=(.*)$', text, re.M)
    directories = re.findall(r'^CodeDirectory ', text, re.M)
    readable = len(directories) == 1 and len(teams) <= 1 and len(timestamps) <= 1
    return dict(leaf=authorities[0] if authorities else None,
                authorities=authorities,
                adhoc='Signature=adhoc' in text,
                runtime='runtime' in (flags.group(1).split(',') if flags else []),
                team=teams[0].strip() if teams and teams[0].strip() != 'not set' else None,  # codesign's words for no team
                timestamp=bool(timestamps),
                signed_time=bool(signed_times),
                readable=readable)


def signature(path):
    """Leaf authority, chain, team, runtime flag, timestamp presence and ad hoc status as codesign -dvv reports them.

    An unsigned file reports no leaf and is a finding, not an error."""
    result = subprocess.run([CODESIGN, '-dvv', str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        if 'not signed at all' in result.stderr:
            return dict(leaf=None, authorities=[], adhoc=False, runtime=False, team=None, timestamp=False,
                        signed_time=False, readable=True)
        raise OSError(f'codesign could not read {path}: {result.stderr.strip() or result.returncode}')
    return parse_display(result.stderr)


def facts(found):
    """The bounded signature facts a provenance record claims, from one parsed display."""
    chain = found['authorities'][1:]
    return dict(status='ok', leaf=found['leaf'], team=found['team'], timestamp=bool(found['timestamp']),
                runtime=bool(found['runtime']), adhoc=bool(found['adhoc']),
                developer_id_chain=bool(chain) and chain[-1] == APPLE_ROOT and DEVELOPER_ID_CA in chain)


def expected_team(identity):
    match = TEAM_RE.search(identity)
    return match.group(1) if match else None


def signature_problems(found, identity):
    """Why a signature's facts fall short of the build's guarantees; empty when they do not."""
    out = []
    if not found['readable']:
        return ['codesign display is ambiguous; the chain and timestamp cannot be established']
    if found['adhoc'] or found['leaf'] != identity:
        signer = 'ad hoc' if found['adhoc'] else (found['leaf'] or 'nobody')
        return [f'signed by {signer}, not {identity}']
    if not found['runtime']:
        out.append('signed without the hardened runtime')
    chain = found['authorities'][1:]
    if DEVELOPER_ID_CA not in chain or not chain or chain[-1] != APPLE_ROOT:
        out.append(f'certificate chain is {found["authorities"] or "absent"}, not the Developer ID chain to {APPLE_ROOT}')
    team = expected_team(identity)
    if team is None:
        out.append('the identity names no team identifier')
    elif found['team'] != team:
        out.append(f'team identifier is {found["team"] or "not set"}, not {team}')
    if not found['timestamp']:
        out.append('no secure timestamp' + (' (only a Signed Time, the signer\'s own clock)' if found['signed_time'] else ''))
    return out


def observation(relative, found):
    chain = 'Developer ID chain' if found['authorities'][1:] and found['authorities'][-1] == APPLE_ROOT and DEVELOPER_ID_CA in found['authorities'] else 'other chain'
    return (f'{relative}: leaf={found["leaf"] or ("ad hoc" if found["adhoc"] else "none")}; {chain}; '
            f'team={found["team"] or "not set"}; runtime={"yes" if found["runtime"] else "no"}; '
            f'timestamp={"secure" if found["timestamp"] else ("signed time only" if found["signed_time"] else "none")}')


def problems(app, identity, observations=None):
    """One line per executable or seal that is not signed by identity with every guarantee; observations collect facts."""
    out = []
    for path in executables(app):
        relative = path.relative_to(app)
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic not in MACHO_MAGICS:
            out.append(f'{relative}: not a Mach-O; only executables belong in this directory')
            continue
        found = signature(path)
        if observations is not None:
            observations.append(observation(str(relative), found))
        out += [f'{relative}: {line}' for line in signature_problems(found, identity)]
    for bundle in seals(app):
        relative = bundle.relative_to(app) if bundle != app else Path('.')
        found = signature(bundle)
        label = 'app seal' if bundle == app else f'{relative} seal'
        if observations is not None:
            observations.append(observation(label, found))
        out += [f'{label}: {line}' for line in signature_problems(found, identity)]
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
    observations = []
    try:
        found = problems(app, args.identity, observations)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f'signer check: {exc}', file=sys.stderr)
        return 2
    for line in observations:
        print(f'    {line}')
    if found:
        print(f'executables or seals not signed by {args.identity} with the hardened runtime, the Developer ID chain, '
              f'its team identifier and a secure timestamp:', file=sys.stderr)
        for line in found:
            print(f'  {line}', file=sys.stderr)
        return 1
    print(f'ok: {len(executables(app))} executables and {len(seals(app))} seals signed by {args.identity} with the '
          f'hardened runtime, the Developer ID chain, its team identifier and a secure timestamp')
    return 0


if __name__ == '__main__':
    sys.exit(main())
