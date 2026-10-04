"""Prune working test output once a new release has been packaged and verified.

Keep the release's acceptance and battery, the newest completed local output
(including failures), explicit pins and pending resource cleanup. This command
is never triggered by a test, elapsed time or disk usage.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import uuid

import artifact
import release_cleanup
import release_runs
import retention

ROOT = Path(__file__).resolve().parents[2]


def version(tag):
    if not isinstance(tag, str) or not retention.RELEASE_TAG.fullmatch(tag):
        raise ValueError(f'invalid release tag: {tag!r}')
    return tuple(map(int, tag[1:].split('.')))


def index(root):
    retention.load_index(root)
    return retention.read_object(root / 'tests/RETAINED.json')


def plan(archive, root, record, manifest):
    pending = retention.bounded_path(root, root / 'tests/out/.release-rotation')
    if pending.exists() and any(pending.iterdir()):
        raise ValueError('unfinished release cleanup; resume its existing archive journal before starting another')
    battery = manifest['runs'].get('battery')
    if battery is None:
        raise ValueError('rotation requires a verified default battery for the new release')
    entries = index(root)['runs']
    current = {run['retained']['path']: run['retained']['run_id'] for run in manifest['runs'].values()}
    for path, run_id in current.items():
        if not any(e['path'] == path and e['run_id'] == run_id for e in entries):
            raise ValueError('new release acceptance and battery must be retained before rotation')
    if any(e.get('release') and version(e['release']) > version(record['tag']) for e in entries):
        raise ValueError('a newer release is retained; clean up from its archive instead')
    checkpoint = retention.read_object(archive / release_runs.BUNDLE / 'battery.json')['started_at_unix_ms']
    found, kept = release_cleanup.candidates(root)
    completed = [m['finished_at_unix_ms'] for m in found.values() if m['disposition'] == 'completed']
    newest_time = max(completed, default=None)
    newest = sorted(p for p, m in found.items()
                    if m['disposition'] == 'completed' and m['finished_at_unix_ms'] == newest_time)
    by_path = {e['path']: e for e in entries}
    # Absent rotating entries can be retired too. Manual pins remain meaningful
    # even when the protected working directory is absent.
    for entry in entries:
        path = root / 'tests/out' / entry['path']
        if entry.get('release') and not os.path.lexists(path):
            found[entry['path']] = None
    selected = []
    for relative, metadata in sorted(found.items()):
        entry = by_path.get(relative)
        path = root / 'tests/out' / relative
        reason = None
        if relative in current:
            reason = 'latest release'
        elif relative in newest:
            reason = 'newest completed local output'
        elif entry and entry.get('release') is None:
            reason = 'explicit pin'
        elif entry and version(entry['release']) >= version(record['tag']):
            reason = 'current release entry'
        elif any(e != entry and retention.overlaps(path, root / 'tests/out' / e['path']) for e in entries):
            reason = 'overlaps another retained entry'
        elif metadata and entry and metadata['run_id'] != entry['run_id']:
            reason = 'retained ownership differs'
        elif metadata and metadata['disposition'] != 'completed' and metadata['started_at_unix_ms'] >= checkpoint:
            reason = 'unfinished output started since the release battery'
        elif metadata:
            try:
                reason = release_cleanup.cleanup_blocker(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                reason = f'cannot verify resource cleanup: {exc}'
        if reason:
            kept.append(dict(path=relative, reason=reason))
            continue
        try:
            snapshot = artifact.inventory(path) if metadata else None
        except (OSError, ValueError) as exc:
            kept.append(dict(path=relative, reason=f'cannot inventory output: {exc}'))
            continue
        selected.append(dict(path=relative, entry=entry, metadata=metadata, inventory=snapshot, state='planned'))
    return dict(schema_version=2, archive=str(archive), root=str(root), release=record['tag'],
                checkpoint_started_at_unix_ms=checkpoint, newest=newest,
                state='staging', runs=selected, kept=kept)


def validate_journal(journal, archive, root, record):
    if (journal.get('schema_version') != 2 or journal.get('root') != str(root)
            or journal.get('archive') != str(archive) or journal.get('release') != record['tag']
            or journal.get('state') not in ('staging', 'retiring', 'deleting', 'complete')
            or not isinstance(journal.get('runs'), list)):
        raise ValueError('rotation journal does not identify this checkout and release')
    transaction = journal.get('transaction')
    if not isinstance(transaction, str) or len(transaction) != 32 or any(c not in '0123456789abcdef' for c in transaction):
        raise ValueError('invalid rotation transaction')
    protected = {record['battery']['original_path'], str(Path(record['acceptance']['original_path']).parent)}
    seen = set()
    for row in journal['runs']:
        relative = release_cleanup.output_path(row['path'])
        if (row['path'] in seen or row['path'] in protected or row['path'] in journal['newest']
                or row.get('state') not in ('planned', 'staged', 'deleting', 'removed')):
            raise ValueError('invalid rotation target')
        entry = row['entry']
        if entry is not None:
            retention.index_paths(root, dict(schema_version=1, runs=[entry]))
            if entry['path'] != row['path'] or version(entry.get('release')) >= version(record['tag']):
                raise ValueError('invalid rotating retention entry')
        if row['metadata'] is None:
            if entry is None or row['inventory'] is not None:
                raise ValueError('missing output has no rotating retention entry')
        elif not isinstance(row['inventory'], dict) or '.' not in row['inventory']:
            raise ValueError('missing cleanup inventory')
        expected = f'.release-rotation/{transaction}/{relative}'
        if row.get('quarantine') != expected:
            raise ValueError('rotation quarantine path differs from its transaction')
        seen.add(row['path'])


def check_retention(root, row, *, retired=False):
    active = index(root)['runs']
    match = next((e for e in active if e['path'] == row['path']), None)
    if match != row['entry'] and not (match is None and retired):
        raise ValueError('retention changed since rotation was planned; evidence preserved')
    other_paths = [root / 'tests/out' / e['path'] for e in active if e != row['entry']]
    for relative in (row['path'], row['quarantine']):
        if retention.retained_overlap(root / 'tests/out' / relative, other_paths):
            raise ValueError('rotation now overlaps a retained pin')
    return match


def apply_journal(journal, archive, root, record):
    receipt = archive / 'evidence/rotation.json'
    validate_journal(journal, archive, root, record)
    if journal['state'] == 'complete':
        return journal
    if journal['state'] in ('staging', 'retiring'):
        for row in journal['runs']:
            if row['state'] not in ('planned', 'staged'):
                raise ValueError('inconsistent staging journal')
            source = retention.bounded_path(root, root / 'tests/out' / row['path'])
            target = retention.bounded_path(root, root / 'tests/out' / row['quarantine'])
            match = check_retention(root, row, retired=journal['state'] == 'retiring')
            if row['metadata'] is None:
                if os.path.lexists(source) or os.path.lexists(target):
                    raise ValueError('previously absent output appeared; evidence preserved')
            elif target.exists():
                if source.exists() and match is not None:
                    raise ValueError('both retained original and quarantine exist; evidence preserved')
                if artifact.inventory(target) != row['inventory']:
                    raise ValueError('quarantined evidence differs from its cleanup inventory')
            elif row['state'] == 'planned' and source.is_dir():
                if (release_cleanup.describe(source) != row['metadata']
                        or release_cleanup.cleanup_blocker(source)
                        or artifact.inventory(source) != row['inventory']):
                    raise ValueError('run changed since rotation was planned; evidence preserved')
                target.parent.mkdir(parents=True, exist_ok=True)
                retention.bounded_path(root, target)
                for directory in (target.parent, target.parent.parent, target.parent.parent.parent, root / 'tests/out'):
                    retention.sync_directory(directory)
                source.rename(target)
                retention.sync_directory(source.parent)
                retention.sync_directory(target.parent)
            else:
                raise ValueError('rotation evidence is missing before retirement')
            row['state'] = 'staged'
            retention.atomic_json(receipt, journal)
        journal['state'] = 'retiring'
        retention.atomic_json(receipt, journal)
        current = index(root)
        retired = {row['path']: row['entry'] for row in journal['runs'] if row['entry'] is not None}
        for entry in current['runs']:
            if entry['path'] in retired and entry != retired[entry['path']]:
                raise ValueError('retention changed before retirement; evidence preserved')
        current['runs'] = [e for e in current['runs'] if e['path'] not in retired]
        retention.write_index(root, current)
        journal['state'] = 'deleting'
        retention.atomic_json(receipt, journal)
    for row in journal['runs']:
        if row['state'] == 'removed':
            continue
        if row['state'] not in ('staged', 'deleting'):
            raise ValueError('inconsistent deletion journal')
        target = retention.bounded_path(root, root / 'tests/out' / row['quarantine'])
        retained = retention.load_index(root)
        if any(retention.retained_overlap(root / 'tests/out' / p, retained)
               for p in (row['path'], row['quarantine'])):
            raise ValueError('rotation deletion overlaps a retained pin')
        # Only visit the quarantine. A replacement at the original path is safe.
        if row['metadata'] is None:
            if os.path.lexists(target):
                raise ValueError('unexpected quarantine for absent output')
        elif target.exists():
            remaining = artifact.inventory(target)
            if (row['state'] == 'staged' and remaining != row['inventory']
                    or any(row['inventory'].get(name) != value for name, value in remaining.items())):
                raise ValueError('quarantined evidence changed; deletion refused')
            row['state'] = 'deleting'
            retention.atomic_json(receipt, journal)
            shutil.rmtree(target)
            retention.sync_directory(target.parent)
        elif row['state'] != 'deleting':
            raise ValueError('quarantined evidence disappeared before deletion')
        row['state'] = 'removed'
        retention.atomic_json(receipt, journal)
    quarantine = retention.bounded_path(root, root / 'tests/out/.release-rotation' / journal['transaction'])
    for directory in [*(quarantine / name for name in release_cleanup.CONTAINERS), quarantine]:
        if directory.exists():
            directory.rmdir()  # Never recursively delete unexpected contents.
            retention.sync_directory(directory.parent)
    journal['state'] = 'complete'
    journal.pop('error', None)
    retention.atomic_json(receipt, journal)
    return journal


def rotate(archive, *, root=ROOT, apply=False):
    root, archive = Path(root).resolve(), release_runs.real_path(archive)
    with retention.checkout_lock(root, preview=not apply) as busy:
        record, manifest = release_runs.verify_release(archive)
        if archive.name != record['tag'] or archive.parent.name != 'archive':
            raise ValueError('rotation requires dist/archive/<release-tag>')
        receipt = archive / 'evidence/rotation.json'
        if receipt.exists() or receipt.is_symlink():
            journal = retention.read_object(receipt)
            validate_journal(journal, archive, root, record)
        else:
            journal = plan(archive, root, record, manifest)
            journal['transaction'] = uuid.uuid4().hex
            for row in journal['runs']:
                row['quarantine'] = '.release-rotation/' + journal['transaction'] + '/' + row['path']
            if apply:
                retention.atomic_json(receipt, journal)
        if not apply:
            return dict(journal, apply=False, checkout_busy=busy)
        try:
            return apply_journal(journal, archive, root, record)
        except (OSError, ValueError, KeyError) as exc:
            journal['error'] = str(exc)
            retention.atomic_json(receipt, journal)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('archive', type=Path, help='verified new release archive')
    parser.add_argument('--apply', action='store_true', help='apply or resume cleanup; otherwise preview only')
    args = parser.parse_args(argv)
    try:
        result = rotate(args.archive, root=ROOT, apply=args.apply)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'STOP: {exc}\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
