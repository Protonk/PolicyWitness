"""Publish an archived release to GitHub and record the published asset identities.

Pushes the release tag when the remote lacks it, creates the release once from
the archive's assets with the tag verified, then reads the release back,
downloads every asset and compares bytes and digests with SHA256SUMS. Only then
does it record the release and asset URLs in release.json and the reply in
evidence/github-release.json. Re-running against an existing release verifies
it again and changes nothing on GitHub. `run` is the one external-tool boundary.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil

from artifact import digest
import release_runs

ROOT = Path(__file__).resolve().parents[2]
VIEW_FIELDS = 'assets,isDraft,publishedAt,tagName,targetCommitish,url'


def run(argv, *, cwd=None):
    """External tool boundary for git and gh; controls replace it."""
    return subprocess.run(list(map(str, argv)), cwd=cwd, capture_output=True, text=True)


def call(argv, *, cwd=None):
    result = run(argv, cwd=cwd)
    if result.returncode != 0:
        raise ValueError(f"{argv[0]} {argv[1]} failed: {result.stderr.strip() or result.returncode}")
    return result.stdout


def publish(archive_dir, *, notes=None, remote='origin', root=ROOT):
    archive_dir, root = Path(archive_dir).resolve(), Path(root)
    record_path = archive_dir / 'release.json'
    record = json.loads(record_path.read_text())
    if 'test_evidence' in record:
        release_runs.verify_release(archive_dir)
    version, tag = record['version'], record['tag']
    assets = [record['archive'], 'SHA256SUMS', record['guide']]
    sums = {}
    for line in (archive_dir / 'SHA256SUMS').read_text().splitlines():
        value, name = line.split()
        sums[name] = value
    for name in (record['archive'], record['guide']):
        if digest(archive_dir / name) != sums.get(name):
            raise ValueError(f'{name} does not match SHA256SUMS')
    if record['sha256'] != sums[record['archive']]:
        raise ValueError('release.json sha256 does not match SHA256SUMS')
    archived_notes = archive_dir / 'evidence/release-notes.md'
    notes = Path(notes).resolve() if notes is not None else archived_notes
    if not notes.is_file():
        raise ValueError(f'release notes missing: {notes}')

    local_tag = call(['git', '-C', root, 'rev-parse', tag]).strip()
    if call(['git', '-C', root, 'rev-parse', f'{tag}^{{commit}}']).strip() != record['source_commit']:
        raise ValueError(f'local {tag} does not name the archived commit {record["source_commit"]}')
    listing = call(['git', '-C', root, 'ls-remote', '--tags', remote, f'refs/tags/{tag}'])
    remote_ids = [line.split()[0] for line in listing.splitlines()
                  if len(line.split()) == 2 and line.split()[1] == f'refs/tags/{tag}']
    if remote_ids and remote_ids[0] != local_tag:
        raise ValueError(f'{remote} holds a different {tag}; not publishing')
    if not remote_ids:
        call(['git', '-C', root, 'push', remote, tag])

    created = False
    if run(['gh', 'release', 'view', tag], cwd=root).returncode != 0:
        call(['gh', 'release', 'create', tag, *[archive_dir / name for name in assets],
              '--title', f'PolicyWitness {version}', '--notes-file', notes, '--verify-tag'], cwd=root)
        created = True
    view = call(['gh', 'release', 'view', tag, '--json', VIEW_FIELDS], cwd=root)
    meta = json.loads(view)
    problems = []
    if meta.get('tagName') != tag or meta.get('isDraft') is not False:
        problems.append(f"release is {meta.get('tagName')!r}, draft={meta.get('isDraft')!r}")
    by_name = {asset.get('name'): asset for asset in meta.get('assets', [])}
    with tempfile.TemporaryDirectory(prefix='pw-release-verify-') as temporary:
        for name in assets:
            asset = by_name.get(name)
            local = digest(archive_dir / name)
            if asset is None or asset.get('state') != 'uploaded':
                problems.append(f'{name}: missing or not uploaded')
                continue
            if asset.get('digest') != f'sha256:{local}':
                problems.append(f"{name}: GitHub digest {asset.get('digest')} != local sha256:{local}")
            call(['gh', 'release', 'download', tag, '--pattern', name, '--dir', temporary, '--clobber'], cwd=root)
            downloaded = Path(temporary) / name
            if not downloaded.is_file() or digest(downloaded) != local:
                problems.append(f'{name}: downloaded bytes differ from the archive')
    if problems:
        raise ValueError('published release does not match the archive: ' + '; '.join(problems))

    if notes != archived_notes:
        shutil.copy2(notes, archived_notes)
    (archive_dir / 'evidence/github-release.json').write_text(view if view.endswith('\n') else view + '\n')
    record['origin'] = dict(kind='github_release', release_url=meta['url'],
                            asset_url=by_name[record['archive']]['url'])
    receipt = dict(original_path=f'gh release view {tag} --json {VIEW_FIELDS}',
                   archived_path='evidence/github-release.json')
    record['receipts'] = [r for r in record.get('receipts', [])
                          if r.get('archived_path') != receipt['archived_path']] + [receipt]
    record['notes'] = ['The published asset digests match GitHub metadata and SHA256SUMS, and every '
                       'downloaded asset matches the archived bytes. The ZIP also matches the retained '
                       'release-acceptance report.']
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    return meta, created


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('archive', type=Path, help='archived release directory, e.g. dist/archive/v0.2.4')
    parser.add_argument('--notes', type=Path, help='release notes; defaults to the archived evidence/release-notes.md')
    parser.add_argument('--remote', default='origin')
    args = parser.parse_args(argv)
    try:
        meta, created = publish(args.archive, notes=args.notes, remote=args.remote, root=ROOT)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'STOP: {exc}\n')
    print(f"{'created' if created else 'verified'} {meta['url']}")
    for asset in meta['assets']:
        print(f"{asset.get('digest')}  {asset.get('name')}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
