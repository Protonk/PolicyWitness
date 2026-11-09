"""Temporary storage inspection for the six schema-1 local releases.

This does not admit historical evidence for publishing or acceptance. Remove this
module and its controls after the final schema-1 archive and dependent quarantine
expire (v0.3.3 is the last one in the migration inventory).
"""
import re
import json
import plistlib
import tarfile
import zipfile

import artifact
import release_runs
import run_ownership as ownership

HISTORICAL_PRODUCERS = {
    '50802056dfdf6ef55d36d49c40512603594e65ae',
    '9d35671e1e3e6a09e5c766cd6db73cc1d402fc8a',
    '1046c77bcb862eb9bcf231a2215af86613225371',
    '2717a7495b9c7508a91d09246adab0ae32871143',
    '3c98b39601f2e475bfbcc7d639c6cdcff79b95af',
    '1bf0341cd06c48122af1635e8aa8cac77517d9e1',
}


def inspect(archive, record, manifest, *, verify=False):
    if (type(record.get('schema_version')) is not int or record['schema_version'] != 1
            or type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1
            or record.get('source_commit') not in HISTORICAL_PRODUCERS
            or set(manifest.get('runs', {})) != {'acceptance', 'battery'}
            or manifest.get('archive') != 'runs.tar.gz'):
        raise ValueError('unrecognized historical release storage')
    for role, summary in [('acceptance', 'acceptance.json'), ('battery', 'run.json')]:
        entry = manifest['runs'][role]['retained']
        relative = ownership.relative_path(entry['path'])
        if (len(relative.parts) != 2 or relative.parts[0] not in ('runs', 'release-acceptance')
                or not ownership.RUN_ID.fullmatch(relative.name)
                or not ownership.RUN_ID.fullmatch(entry['run_id'])
                or entry.get('release') != record['tag'] or entry.get('source') != record['source_commit']):
            raise ValueError('historical run identity differs from its release')
        reference = record[role]
        original = str(relative) + '/acceptance.json' if role == 'acceptance' else str(relative)
        if reference.get('original_path') != original or reference.get('path') != release_runs.BUNDLE + '/' + role + '.json':
            raise ValueError('historical original path differs from its release')
        if role == 'battery' and reference.get('run_id') != entry['run_id']:
            raise ValueError('historical battery identity differs from its release')
        digest = manifest['runs'][role]['inventory'].get(summary, {}).get('sha256')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('historical summary is absent from its inventory')
        copied = archive / release_runs.BUNDLE / (role + '.json')
        if artifact.digest(release_runs.real_path(copied)) != digest or manifest['summaries'].get(role + '.json') != digest:
            raise ValueError('historical summary checksum mismatch')
        if role == 'battery' and ownership.read_object(copied).get('run_id') != entry['run_id']:
            raise ValueError('historical battery summary identity differs')
    if verify:
        sums = {}
        for line in (archive / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split()
            if name in sums:
                raise ValueError('duplicate historical asset checksum')
            sums[name] = digest
        if set(sums) != {record['archive'], 'PolicyWitness.md'} or sums[record['archive']] != record['sha256']:
            raise ValueError('historical asset references differ')
        for name, digest in sums.items():
            if artifact.digest(release_runs.real_path(archive / name)) != digest:
                raise ValueError('historical asset checksum mismatch')
        with zipfile.ZipFile(archive / record['archive']) as zipped:
            info = plistlib.loads(zipped.read('PolicyWitness.app/Contents/Info.plist'))
        if (info.get('PWBuildCommit') != record['source_commit'] or info.get('PWBuildDescribe') != record['tag']
                or info.get('CFBundleShortVersionString') != record['version']):
            raise ValueError('historical asset source identity differs')
        release_runs.verify_transport(archive / release_runs.BUNDLE, manifest, ('battery', 'run.json'))
        with tarfile.open(archive / release_runs.BUNDLE / 'runs.tar.gz', 'r:gz') as packed:
            for role, run in manifest['runs'].items():
                owner = json.loads(packed.extractfile(role + '/owner.json').read())
                if (owner.get('schema_version') != 1 or owner.get('run_id') != run['retained']['run_id']
                        or not str(owner.get('out_dir', '')).endswith('/tests/out/' + run['retained']['path'])):
                    raise ValueError('historical packed owner identity differs')
