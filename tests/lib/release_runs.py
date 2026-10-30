"""Portable, verified copies of the test evidence supporting one release.

Archive members are inspected as streams, never extracted. Symlinks are recorded
without following them. Original paths remain provenance, not archive lookups.

Schemas 2 (historical transport) and 3 (source-bound family obligations) verify. It packs the acceptance directory alone and declares
the battery as the dispatcher run nested inside it (`tests/run.json`).
Schema 3 requires an independently supplied producer contract; unsupported bundles remain unchanged.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import stat
import tarfile
import zipfile

import artifact
import build_provenance
import retention

BUNDLE = 'evidence/test-runs'
# Positive historical producer identities, read from the already accepted release
# records and independently checked against the ZIP's build provenance below.
# Absence of a new declaration is never evidence that a new producer was legacy.
HISTORICAL_PRODUCERS = {
    '50802056dfdf6ef55d36d49c40512603594e65ae',
    '9d35671e1e3e6a09e5c766cd6db73cc1d402fc8a',
    '1046c77bcb862eb9bcf231a2215af86613225371',
    '2717a7495b9c7508a91d09246adab0ae32871143',
    '3c98b39601f2e475bfbcc7d639c6cdcff79b95af',
    '1bf0341cd06c48122af1635e8aa8cac77517d9e1',
}


def producer_contract(record):
    expected = record.get('execution_contract')
    if expected is None and (record.get('schema_version') != 1 or
                             record.get('source_commit') not in HISTORICAL_PRODUCERS):
        raise ValueError('release lacks required producer contract and positive historical source identity')
    return expected



def sync_tree(path):
    """Flush the verified copy before it becomes grounds to retire originals."""
    for child in path.iterdir():
        mode = child.lstat().st_mode
        if stat.S_ISDIR(mode):
            sync_tree(child)
        elif stat.S_ISREG(mode):
            fd = os.open(child, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    retention.sync_directory(path)


def real_path(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise ValueError(f'symlink redirects are not allowed: {path}')
    return path


def pack(destination, *, tag, source, runs, battery, expected_contract=None):
    """Caller holds the checkout lock. runs maps roles to (directory, entry); battery is
    (role, relative path) naming the dispatcher run.json inside that role."""
    role, relative = battery
    snapshots = {}
    for name, (path, entry) in runs.items():
        real_path(path)
        snapshots[name] = dict(retained=entry, inventory=artifact.inventory(path))
    if role not in runs or relative not in snapshots[role]['inventory'] or 'sha256' not in snapshots[role]['inventory'][relative]:
        raise ValueError('the battery summary is not a file inside its run')
    destination.mkdir()
    archive = destination / 'runs.tar.gz'
    with tarfile.open(archive, 'x:gz', dereference=False) as zipped:
        for name, (path, _) in runs.items():
            zipped.add(path, arcname=name)
    summaries = {}
    copies = [(name + '.json', path / ('acceptance.json' if name == 'acceptance' else 'run.json'),
               snapshots[name]['inventory']['acceptance.json' if name == 'acceptance' else 'run.json'])
              for name, (path, _) in runs.items()]
    copies.append(('battery.json', runs[role][0] / relative, snapshots[role]['inventory'][relative]))
    for name, origin, entry in copies:
        target = destination / name
        shutil.copy2(origin, target)
        if artifact.digest(target) != entry['sha256']:
            raise ValueError(f'{name} changed while archiving')
        summaries[name] = artifact.digest(target)
    manifest = dict(schema_version=3 if expected_contract is not None else 2, tag=tag, source_commit=source,
                    archive=archive.name, sha256=artifact.digest(archive),
                    runs=snapshots, battery=dict(role=role, path=relative), summaries=summaries)
    if expected_contract is not None:
        manifest['execution_contract'] = expected_contract
    retention.atomic_json(destination / 'manifest.json', manifest)
    verify_bundle(destination, expected_contract=expected_contract)
    for role, (path, _) in runs.items():
        if artifact.inventory(path) != snapshots[role]['inventory']:
            raise ValueError(f'{role} evidence changed while archiving')
    return dict(path=BUNDLE + '/manifest.json', sha256=artifact.digest(destination / 'manifest.json'))


def battery_source(manifest):
    """The required battery's role and path in a supported bundle manifest."""
    if manifest.get('schema_version') not in (2, 3):
        raise ValueError('unsupported release test evidence schema; expected schema 2')
    declared = manifest.get('battery')
    if not isinstance(declared, dict):
        raise ValueError('a schema 2 evidence manifest declares its battery')
    if declared != dict(role='acceptance', path='tests/run.json'):
        raise ValueError('a schema 2 battery must be acceptance/tests/run.json')
    return declared['role'], declared['path']


def verify_bundle(destination, *, expected_contract=None):
    destination = real_path(destination)
    manifest = retention.read_object(destination / 'manifest.json')
    battery = battery_source(manifest)
    if manifest.get('archive') != 'runs.tar.gz' or set(manifest.get('runs', {})) != {'acceptance'}:
        raise ValueError('invalid release test evidence manifest')
    archive = real_path(destination / 'runs.tar.gz')
    if artifact.digest(archive) != manifest['sha256']:
        raise ValueError('release test evidence archive checksum mismatch')
    expected = {}
    for role, run in manifest['runs'].items():
        for relative, entry in run['inventory'].items():
            name = role if relative == '.' else role + '/' + str(retention.relative_path(relative))
            expected[name] = entry
    found = {}
    with tarfile.open(archive, 'r:gz') as zipped:
        for member in zipped:
            path = PurePosixPath(member.name)
            if (member.name in found or member.name not in expected or path.is_absolute()
                    or '..' in path.parts or str(path) != member.name):
                raise ValueError(f'unsupported test evidence member: {member.name}')
            if member.isdir():
                entry = dict(mode=stat.S_IFDIR | member.mode)
            elif member.issym():
                entry = dict(mode=stat.S_IFLNK | member.mode, symlink=member.linkname)
            elif member.isfile() or member.islnk():
                if member.islnk() and member.linkname not in expected:
                    raise ValueError('test evidence hard link leaves the inventory')
                digest = hashlib.sha256()
                with zipped.extractfile(member) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(block)
                entry = dict(mode=stat.S_IFREG | member.mode, sha256=digest.hexdigest())
            else:
                raise ValueError(f'unsupported test evidence member type: {member.name}')
            found[member.name] = entry
    if found != expected:
        raise ValueError('release test evidence differs from its file inventory')
    role, relative = battery
    inventory = manifest['runs'].get(role, {}).get('inventory', {})
    if 'sha256' not in inventory.get(relative, {}):
        raise ValueError('release test evidence names no battery summary inside its runs')
    sources = {'acceptance.json': ('acceptance', 'acceptance.json'), 'battery.json': battery}
    if set(manifest.get('summaries', {})) != set(sources):
        raise ValueError('release test evidence summaries are incomplete')
    for name, (role, relative) in sources.items():
        summary = real_path(destination / name)
        if (artifact.digest(summary) != manifest['summaries'][name]
                or manifest['summaries'][name] != manifest['runs'][role]['inventory'][relative]['sha256']):
            raise ValueError(f'{name[:-5]} summary checksum mismatch')
    if expected_contract is not None or manifest['schema_version'] == 3:
        import execution_contract
        if expected_contract is None or manifest.get('execution_contract') != expected_contract:
            raise ValueError('portable evidence requires the independently expected producer contract')
        with tarfile.open(archive, 'r:gz') as zipped:
            def load(name):
                return json.loads(zipped.extractfile('acceptance/tests/' + str(retention.relative_path(name))).read())
            errors = execution_contract.problems(load('run.json'), expected_contract, load)
        if errors:
            raise ValueError('; '.join(errors))
    return manifest


def verify_release(archive):
    """Verify portable evidence and its binding to the exact accepted ZIP."""
    archive = real_path(archive)
    record = retention.read_object(archive / 'release.json')
    tag = record['tag']
    if tag != 'v' + record['version'] or not retention.RELEASE_TAG.fullmatch(tag):
        raise ValueError('invalid archived release version')
    name = 'PolicyWitness-' + record['version'] + '.zip'
    if record['archive'] != name or record['guide'] != 'PolicyWitness.md':
        raise ValueError('invalid archived release assets')
    sums = {}
    for line in real_path(archive / 'SHA256SUMS').read_text().splitlines():
        digest, filename = line.split()
        if filename in sums:
            raise ValueError('duplicate release checksum')
        sums[filename] = digest
    if set(sums) != {name, 'PolicyWitness.md'}:
        raise ValueError('release checksums do not identify the expected assets')
    for filename, digest in sums.items():
        if artifact.digest(real_path(archive / filename)) != digest:
            raise ValueError(f'{filename} does not match SHA256SUMS')
    if sums[name] != record['sha256']:
        raise ValueError('release.json checksum differs from the ZIP')
    with zipfile.ZipFile(archive / name) as zipped:
        info = plistlib.loads(zipped.read('PolicyWitness.app/Contents/Info.plist'))
    if (info.get('PWBuildCommit') != record['source_commit'] or info.get('PWBuildDescribe') != tag
            or info.get('CFBundleShortVersionString') != record['version']):
        raise ValueError('archived ZIP stamp differs from the release record')
    provenance = record.get('provenance')
    if provenance is None:
        raise ValueError('archived release has no provenance object')
    if not isinstance(provenance, dict) or provenance.get('path') != 'evidence/provenance.json':
        raise ValueError('invalid archived provenance reference')
    archived_record = real_path(archive / provenance['path'])
    if artifact.digest(archived_record) != provenance.get('sha256'):
        raise ValueError('archived provenance record checksum mismatch')
    member, controller = build_provenance.read_zip_record(archive / name)
    if member != archived_record.read_bytes():
        raise ValueError('archived provenance record differs from the record inside the ZIP')
    if controller != provenance.get('controller_sha256'):
        raise ValueError('archived controller hash differs from the ZIP')
    if not isinstance(provenance.get('app_signature'), dict):
        raise ValueError('archived release lacks its app seal facts')
    reference = record.get('test_evidence') or {}
    if (reference.get('path') != BUNDLE + '/manifest.json'
            or artifact.digest(real_path(archive / reference['path'])) != reference.get('sha256')):
        raise ValueError('release has no verified portable test evidence')
    expected_contract = producer_contract(record)
    manifest = verify_bundle(archive / BUNDLE, expected_contract=expected_contract)
    if manifest['tag'] != tag or manifest['source_commit'] != record['source_commit']:
        raise ValueError('test evidence belongs to a different release')
    accepted = retention.read_object(archive / BUNDLE / 'acceptance.json')
    if (record['acceptance']['path'] != BUNDLE + '/acceptance.json'
            or accepted.get('ok') is not True or accepted.get('sha256_before') != record['sha256']
            or accepted.get('sha256_after') != record['sha256']):
        raise ValueError('archived acceptance does not support the ZIP')
    role, relative = battery_source(manifest)
    battery = retention.read_object(archive / BUNDLE / 'battery.json')
    entry = manifest['runs'][role]['retained']
    reference = record.get('battery')
    if not isinstance(reference, dict):
        raise ValueError('archived battery does not support the release')
    original = entry['path'] + '/' + str(PurePosixPath(relative).parent)
    if (reference.get('path') != BUNDLE + '/battery.json'
            or battery.get('ok') is not True or battery.get('terminal') is not True
            or reference.get('run_id') != battery.get('run_id')
            or reference.get('original_path') != original
            or entry.get('release') != tag or entry['source'] != record['source_commit']):
        raise ValueError('archived battery does not support the release')
    if (battery.get('requested_cases') or battery.get('requested_suites')
            or (battery.get('plan') or {}).get('selection', {}).get('mode') != 'default'):
        raise ValueError('archived battery is not the default selection')
    return record, manifest
