"""Portable, verified copies of the test evidence supporting one release.

Archive members are inspected as streams, never extracted. Symlinks are recorded
without following them. Original paths remain provenance, not archive lookups.
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import stat
import tarfile
import zipfile

import artifact
import retention

BUNDLE = 'evidence/test-runs'


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


def pack(destination, *, tag, source, runs):
    """Caller holds the checkout lock. runs maps roles to (directory, entry)."""
    snapshots = {}
    for role, (path, entry) in runs.items():
        real_path(path)
        snapshots[role] = dict(retained=entry, inventory=artifact.inventory(path))
    destination.mkdir()
    archive = destination / 'runs.tar.gz'
    with tarfile.open(archive, 'x:gz', dereference=False) as zipped:
        for role, (path, _) in runs.items():
            zipped.add(path, arcname=role)
    summaries = {}
    for role, (path, _) in runs.items():
        name = 'acceptance.json' if role == 'acceptance' else 'run.json'
        target = destination / (role + '.json')
        shutil.copy2(path / name, target)
        if artifact.digest(target) != snapshots[role]['inventory'][name]['sha256']:
            raise ValueError(f'{role} summary changed while archiving')
        summaries[target.name] = artifact.digest(target)
    manifest = dict(schema_version=1, tag=tag, source_commit=source,
                    archive=archive.name, sha256=artifact.digest(archive),
                    runs=snapshots, summaries=summaries)
    retention.atomic_json(destination / 'manifest.json', manifest)
    verify_bundle(destination)
    for role, (path, _) in runs.items():
        if artifact.inventory(path) != snapshots[role]['inventory']:
            raise ValueError(f'{role} evidence changed while archiving')
    return dict(path=BUNDLE + '/manifest.json', sha256=artifact.digest(destination / 'manifest.json'))


def verify_bundle(destination):
    destination = real_path(destination)
    manifest = retention.read_object(destination / 'manifest.json')
    if (manifest.get('schema_version') != 1 or manifest.get('archive') != 'runs.tar.gz'
            or set(manifest.get('runs', {})) not in ({'acceptance'}, {'acceptance', 'battery'})):
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
    expected_summaries = {role + '.json' for role in manifest['runs']}
    if set(manifest.get('summaries', {})) != expected_summaries:
        raise ValueError('release test evidence summaries are incomplete')
    for role, run in manifest['runs'].items():
        name = role + '.json'
        summary = real_path(destination / name)
        source = 'acceptance.json' if role == 'acceptance' else 'run.json'
        if (artifact.digest(summary) != manifest['summaries'][name]
                or manifest['summaries'][name] != run['inventory'][source]['sha256']):
            raise ValueError(f'{role} summary checksum mismatch')
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
    reference = record.get('test_evidence') or {}
    if (reference.get('path') != BUNDLE + '/manifest.json'
            or artifact.digest(real_path(archive / reference['path'])) != reference.get('sha256')):
        raise ValueError('release has no verified portable test evidence')
    manifest = verify_bundle(archive / BUNDLE)
    if manifest['tag'] != tag or manifest['source_commit'] != record['source_commit']:
        raise ValueError('test evidence belongs to a different release')
    accepted = retention.read_object(archive / BUNDLE / 'acceptance.json')
    if (record['acceptance']['path'] != BUNDLE + '/acceptance.json'
            or accepted.get('ok') is not True or accepted.get('sha256_before') != record['sha256']
            or accepted.get('sha256_after') != record['sha256']):
        raise ValueError('archived acceptance does not support the ZIP')
    if 'battery' in manifest['runs']:
        battery = retention.read_object(archive / BUNDLE / 'battery.json')
        entry = manifest['runs']['battery']['retained']
        if (record['battery']['path'] != BUNDLE + '/battery.json' or battery.get('ok') is not True
                or battery.get('terminal') is not True or battery.get('run_id') != entry['run_id']
                or entry.get('release') != tag or entry['source'] != record['source_commit']
                or record['battery']['run_id'] != entry['run_id']):
            raise ValueError('archived battery does not support the release')
    elif record.get('battery') is not None:
        raise ValueError('missing archived battery evidence')
    return record, manifest
