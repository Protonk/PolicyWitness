#!/usr/bin/env python3
"""Write the service-local worker inventory after nested signing, before sealing.

The build supplies the common pre-sign worker artifact and verified generated
identity. This tool never launches a worker and never signs code itself.
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))


INVENTORY_BYTES = 1_048_576
ENTITLEMENT_BYTES = 65_536
ROLES = {'selected': 'Contents/MacOS/pw-probe-runner',
         'unentitled': 'Contents/MacOS/pw-probe-runner-unentitled'}


def command(args):
    result = subprocess.run(args, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f'{args[0]} failed: {result.stderr.decode(errors="replace")[:1024]}')
    return result


def signed_worker(bundle, role, relative):
    path = bundle / relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(bundle.resolve()):
        raise ValueError(f'{role}: expected a regular bundle-local executable')
    command(['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', str(path)])
    display = command(['/usr/bin/codesign', '-dvvv', str(path)]).stderr.decode()
    values = dict(line.split('=', 1) for line in display.splitlines() if '=' in line)
    identifier, team, cdhash = values.get('Identifier'), values.get('TeamIdentifier'), values.get('CDHash')
    if not identifier or len(identifier.encode()) > 255 or not cdhash or not re.fullmatch('[0-9a-f]{40}', cdhash):
        raise ValueError(f'{role}: invalid signature metadata')
    team = None if team in (None, 'not set') else team
    if team is not None and (not team or len(team.encode()) > 255):
        raise ValueError(f'{role}: invalid signature team')
    raw = command(['/usr/bin/codesign', '-d', '--entitlements', ':-', str(path)]).stdout
    if len(raw) > ENTITLEMENT_BYTES:
        raise ValueError(f'{role}: entitlement read-back exceeds limit')
    entitlements = plistlib.loads(raw) if raw.strip() else {}
    if not isinstance(entitlements, dict) or (role == 'unentitled' and entitlements):
        raise ValueError(f'{role}: invalid entitlement dictionary')
    xml = plistlib.dumps(entitlements, fmt=plistlib.FMT_XML, sort_keys=True)
    if len(xml) > ENTITLEMENT_BYTES:
        raise ValueError(f'{role}: serialized entitlement read-back exceeds limit')
    return dict(role=role, relative_path=relative, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                cdhash=cdhash, identifier=identifier, team_id=team, entitlements_xml=xml.decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--unsigned-worker', type=Path, required=True)
    parser.add_argument('--worker-identity', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{64}', args.worker_identity):
        raise ValueError('invalid generated worker identity')
    manifest = dict(schema_version=1, contract=plistlib.loads((args.bundle / "Contents/Info.plist").read_bytes())["PWContract"], worker_identity=args.worker_identity,
                    unsigned_worker_sha256=hashlib.sha256(args.unsigned_worker.read_bytes()).hexdigest(),
                    workers=[signed_worker(args.bundle, role, path) for role, path in ROLES.items()])
    data = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    if len(data) > INVENTORY_BYTES:
        raise ValueError('equipment inventory exceeds limit')
    destination = args.bundle / 'Contents/Resources/worker-equipment.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Bundle assembly owns this path, before the enclosing seal exists.
    destination.write_bytes(data)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(f'ERROR: equipment inventory: {error}', file=sys.stderr)
        raise SystemExit(2)
