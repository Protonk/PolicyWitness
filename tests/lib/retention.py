"""Four local release archives, current acceptance, and one resumable prune policy.

No discretionary pins, age cutoffs, completion requirements or retention knobs.
Ownership, active locks and unresolved resource cleanup remain deletion blockers.
"""
import json
import os
from pathlib import Path
import re
import plistlib
import zipfile
import shutil
import uuid

import artifact
import run_ownership as ownership

ARCHIVE_COUNT = 4
QUARANTINE = 'tests/out/.retention'
CONTAINERS = ('runs', 'release-acceptance')


def version(tag):
    if not isinstance(tag, str) or not ownership.RELEASE_TAG.fullmatch(tag):
        raise ValueError(f'invalid release tag: {tag!r}')
    return tuple(map(int, tag[1:].split('.')))


def real(path):
    path = Path(path).absolute()
    if '..' in path.parts or path.resolve() != path:
        raise ValueError(f'symlink redirects are not allowed: {path}')
    return path


def distribution(root, dist=None):
    expected = real(Path(root) / 'dist')
    actual = expected if dist is None else real(Path(root) / dist)
    if actual != expected:
        raise ValueError('releases require the checkout distribution root dist/')
    return expected


def old_transactions(root):
    pending = real(root / 'tests/out/.release-rotation')
    if pending.exists() and any(pending.iterdir()):
        raise ValueError('unfinished old release quarantine; resolve with the original recovery tools')
    base = distribution(root) / 'archive'
    for archive in sorted(base.iterdir()) if base.exists() else []:
        if archive.is_symlink():
            raise ValueError(f'symlink redirects are not allowed: {archive}')
        receipt = archive / 'evidence/rotation.json'
        if os.path.lexists(receipt) and ownership.read_object(real(receipt)).get('state') != 'complete':
            raise ValueError(f'unfinished old release journal: {receipt}')


def archives(root, *, verify=False):
    """Read identities cheaply for protection; fully verify before destructive planning."""
    import release_runs
    root = Path(root)
    old_transactions(root)
    base = real(distribution(root) / 'archive')
    found = []
    for path in sorted(base.iterdir()) if base.exists() else []:
        real(path)
        if path.name.startswith('.'):
            continue  # An unpublished staging directory cannot advance the window.
        order = version(path.name)
        record = ownership.read_object(path / 'release.json')
        manifest_path = real(path / release_runs.BUNDLE / 'manifest.json')
        manifest = ownership.read_object(manifest_path)
        if (record.get('tag') != path.name or record.get('version') != path.name[1:]
                or record.get('archive') != 'PolicyWitness-' + path.name[1:] + '.zip'
                or record.get('guide') != 'PolicyWitness.md'
                or record.get('test_evidence') != dict(path=release_runs.BUNDLE + '/manifest.json', sha256=artifact.digest(manifest_path))
                or manifest.get('tag') != path.name or manifest.get('source_commit') != record.get('source_commit')):
            raise ValueError(f'inconsistent release archive: {path}')
        for name in (record['archive'], record['guide'], 'SHA256SUMS', release_runs.BUNDLE + '/runs.tar.gz'):
            if not real(path / name).is_file():
                raise ValueError(f'incomplete release archive: {path / name}')
        if manifest.get('schema_version') == 1:
            import historical_release_storage
            historical_release_storage.inspect(path, record, manifest, verify=verify)
        else:
            release_runs.battery_source(manifest)
            if manifest.get('execution_contract') != release_runs.producer_contract(record):
                raise ValueError('archive producer contract differs from portable evidence')
            if verify:
                release_runs.verify_release(path)
        found.append(dict(path=path, record=record, manifest=manifest, order=order))
    return sorted(found, key=lambda r: r['order'])


def require_new_release(root, tag):
    found = archives(root, verify=True)
    if found and version(tag) <= found[-1]['order']:
        raise ValueError(f'{tag} must be newer than completed local release {found[-1]["record"]["tag"]}; a version is released once')


def handoffs(root):
    """Select accepted unarchived attempts by the same final-ZIP predicate as archival."""
    dist = distribution(root)
    final = real(dist / 'PolicyWitness.zip')
    digest = artifact.digest(final) if final.is_file() else None
    base = real(dist / 'evidence')
    matches = []
    for path in sorted(base.iterdir()) if base.exists() else []:
        real(path)
        if not path.is_dir():
            continue
        accepted_path = path / 'acceptance.json'
        if not accepted_path.exists():
            continue
        accepted = ownership.read_object(accepted_path)
        if accepted.get('ok') is not True:
            continue
        record = ownership.read_object(path / 'release.json')
        notarization = ownership.read_object(path / 'notarization/result.json')
        if (record.get('archive') == str(final) and accepted.get('sha256') == digest
                and digest is not None and notarization.get('state') == 'accepted'):
            matches.append((path, accepted))
    if len(matches) > 1:
        raise ValueError('ambiguous accepted release handoff')
    return matches


def protected_paths(root, found=None):
    root = Path(root)
    found = archives(root) if found is None else found
    protected = []
    if found:
        latest = found[-1]
        entry = latest['manifest']['runs']['acceptance']['retained']
        relative = ownership.relative_path(entry['path'])
        if len(relative.parts) != 2 or relative.parts[0] != 'release-acceptance':
            raise ValueError('release acceptance must name one managed acceptance directory')
        path = ownership.bounded_path(root, root / 'tests/out' / relative)
        record = latest['record']
        if (record['acceptance']['original_path'] != str(relative) + '/acceptance.json'
                or entry.get('release') != record['tag'] or entry.get('source') != record['source_commit']):
            raise ValueError('release acceptance identity differs from its archive')
        if path.exists():
            if ownership.valid_owner(path)['run_id'] != entry['run_id']:
                raise ValueError('release acceptance owner differs from its archive')
            protected.append(path)
    for attempt, accepted in handoffs(root):
        receipt = ownership.bounded_path(root, Path(accepted['path']))
        if receipt.name != 'acceptance.json' or receipt.parent.parent != root / 'tests/out/release-acceptance':
            raise ValueError('handoff must name a managed acceptance receipt')
        owner = ownership.valid_owner(receipt.parent)
        local = ownership.read_object(receipt)
        if (owner.get('kind') != 'release_acceptance' or local.get('run_id') != owner['run_id']
                or local.get('ok') is not True or local.get('sha256_before') != accepted['sha256']
                or local.get('sha256_after') != accepted['sha256']):
            raise ValueError(f'inconsistent accepted handoff: {attempt}')
        protected.append(receipt.parent)
    return protected


def cleanup_blocker(root, path):
    """Inspect actual case receipts, never nested fixtures or historical process IDs."""
    import pytest_resources
    pytest_resources.guard(root, purpose='disposal', target=path)
    owner = ownership.valid_owner(path)
    tests = path / 'tests' if owner.get('kind') == 'release_acceptance' else path
    suites = tests / 'suites'
    real(tests)
    real(suites)
    if not suites.exists():
        return None
    for suite in suites.iterdir():
        real(suite)
        if not suite.is_dir():
            continue
        for case in suite.iterdir():
            real(case)
            if not case.is_dir():
                continue
            artifacts = real(case / 'artifacts')
            session = artifacts / 'session.json'
            if os.path.lexists(session):
                state = ownership.read_object(session)
                if state.get('removed') is not True or state.get('cleanup_error'):
                    return f'pending external-runner cleanup: {session.relative_to(path)}'
            if suite.name == 'runner_byoxpc' and case.name == 'registry_recovery':
                receipt = artifacts / 'controls.json'
                if not receipt.exists() or ownership.read_object(receipt).get('cleanup_verified') is not True:
                    return 'pending registry recovery cleanup'
    return None


def snapshot(path):
    return artifact.inventory(path) if path.is_dir() else {'.': dict(mode=path.lstat().st_mode, sha256=artifact.digest(path))}


def candidate(root, path, kind):
    if kind == 'run':
        identity = ownership.valid_owner(path)
    elif kind == 'archive':
        record = ownership.read_object(path / 'release.json')
        identity = {k: record[k] for k in ('tag', 'source_commit', 'sha256')}
    elif kind == 'pointer':
        identity = dict(destination=path.read_text().strip())
    elif kind == 'metadata':
        identity = dict(name=path.name)
    else:
        identity = dict(release_record=artifact.digest(path / 'release.json')) if (path / 'release.json').exists() else {}
    return dict(path=str(path.relative_to(root)), kind=kind, identity=identity, inventory=snapshot(path), state='planned')


def working_output(root):
    """Find owned roots anywhere in tests/out, never descending into owned evidence."""
    base = real(root / 'tests/out')
    blocked = []
    found = []
    loose = []
    def visit(path):
        try:
            real(path)
            if not path.is_dir():
                # A file outside every owned run was never a deletion target:
                # report it, but it is not an obstacle to this cleanup.
                loose.append(path)
                return
            if os.path.lexists(path / 'owner.json'):
                owner = ownership.valid_owner(path)
                found.append((path, owner))
                return  # Nested fixture records are content, not cleanup authority.
            if (path.parent in (base / name for name in CONTAINERS)
                    or any(os.path.lexists(path / name) for name in ('run.json', 'acceptance.json', 'suites'))):
                raise ValueError('missing managed output owner')
            children = list(path.iterdir())
            if not children:
                return  # Empty structural containers carry no evidence.
            for child in children:
                visit(child)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            blocked.append(dict(path=str(path.relative_to(root)), reason=str(exc)))
    if base.exists():
        for child in base.iterdir():
            if child.name not in ('.retention', '.release-rotation', 'pytest-owners'):
                visit(child)
    return found, blocked, loose


def linked_attempts(root, expired, kept):
    """Use archived pointer destinations, release stamps, hashes or submission IDs."""
    base = real(distribution(root) / 'evidence')
    selected, blocked, loose = [], [], []
    all_records = expired + kept
    for path in sorted(base.iterdir()) if base.exists() else []:
        try:
            real(path)
            if path.is_file() and path.suffix != '.archived':
                loose.append(path)  # Neither an attempt nor a pointer: reported, never a target.
                continue
            tags = set()
            if path.is_file() and path.suffix == '.archived':
                destination = Path(path.read_text().strip())
                for row in all_records:
                    if destination == row['path'] / 'evidence':
                        tags.add(row['record']['tag'])
            elif path.is_dir():
                release = path / 'release.json'
                if release.exists():
                    value = ownership.read_object(release)
                    build = value.get('build') or {}
                    for row in all_records:
                        record = row['record']
                        if value.get('submitted_sha256') in {record.get('submitted_sha256'), record['sha256']} - {None}:
                            tags.add(record['tag'])
                    submitted = real(path / 'notarization/submitted.zip')
                    if build and submitted.is_file():
                        if artifact.digest(submitted) != value.get('submitted_sha256'):
                            raise ValueError('attempt submitted ZIP checksum mismatch')
                        with zipfile.ZipFile(submitted) as zipped:
                            info = plistlib.loads(zipped.read('PolicyWitness.app/Contents/Info.plist'))
                        if any(info.get(k) != v for k,v in build.items()):
                            raise ValueError('attempt submitted ZIP source differs from its record')
                        tag = build.get('PWBuildDescribe')
                        if tag == 'v' + str(build.get('CFBundleShortVersionString')) and tag in {r['record']['tag'] for r in all_records}:
                            tags.add(tag)
                # A successful notarytool lookup has a durable command/result pair.
                command = path / 'command/command.json'
                if command.exists():
                    value = ownership.read_object(real(command))
                    argv = value.get('argv', [])
                    if (argv[:3] == ['/usr/bin/xcrun', 'notarytool', 'info'] and len(argv) > 3
                            and value.get('returncode') == 0 and not value.get('interrupted') and not value.get('timed_out')):
                        result = ownership.read_object(real(path / 'command/stdout'))
                        if result.get('id') != argv[3]:
                            raise ValueError('notarization lookup identity mismatch')
                        for row in all_records:
                            if result['id'] == row['record'].get('notarization_submission_id'):
                                tags.add(row['record']['tag'])
                for name in ('notarization/result.json', 'notarization/info.json'):
                    receipt = path / name
                    if receipt.exists():
                        value = ownership.read_object(real(receipt))
                        identity = value.get('submission_id') or value.get('id')
                        for row in all_records:
                            if identity and identity == row['record'].get('notarization_submission_id'):
                                tags.add(row['record']['tag'])
            if len(tags) > 1:
                raise ValueError('attempt has conflicting release associations')
            if tags and tags <= {r['record']['tag'] for r in expired}:
                selected.append(candidate(root, path, 'pointer' if path.is_file() else 'attempt'))
            elif not tags:
                # No archive association supplies deletion authority. This is
                # normal for an untagged rehearsal or an attempt still underway,
                # not a failed cleanup operation. Contradictions still refuse.
                loose.append(path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            blocked.append(dict(path=str(path.relative_to(root)), reason=str(exc)))
    return selected, blocked, loose


def plan(root, *, busy=False):
    root = Path(root)
    found = archives(root, verify=True)
    kept, expired = found[-ARCHIVE_COUNT:], found[:-ARCHIVE_COUNT]
    protected = protected_paths(root, found)
    selected, blocked, unmanaged = linked_attempts(root, expired, kept)
    selected += [candidate(root, row['path'], 'archive') for row in expired]
    rows = []
    missing = []
    # Inspect only the distribution containers, never inside a retained archive
    # or signed app. Test-output discovery likewise stops at each owned run.
    for parent in (distribution(root), distribution(root) / 'archive'):
        path = parent / '.DS_Store'
        if os.path.lexists(path):
            try:
                real(path)
                if not path.is_file():
                    raise ValueError('Finder metadata is not a regular file')
                unmanaged.append(path)
            except (OSError, ValueError) as exc:
                blocked.append(dict(path=str(path.relative_to(root)), reason=str(exc)))
    if found:
        relative = found[-1]['manifest']['runs']['acceptance']['retained']['path']
        if not (root / 'tests/out' / relative).exists():
            missing.append('tests/out/' + relative)
    working, unknown, loose = working_output(root)
    blocked += unknown
    rows += [dict(path=str(Path(row['path']).relative_to('tests/out')), disposition='keep: blocked', reason=row['reason']) for row in unknown]
    rows += [dict(path=str(path.relative_to(root / 'tests/out')),
                  disposition='delete' if path.name == '.DS_Store' and not busy else 'keep: unmanaged',
                  reason='Finder metadata' if path.name == '.DS_Store' else 'standalone file') for path in loose]
    unmanaged += loose
    for path in list(unmanaged):
        if path.name == '.DS_Store':
            unmanaged.remove(path)
            if not path.is_file():
                blocked.append(dict(path=str(path.relative_to(root)), reason='Finder metadata is not a regular file'))
            elif busy:
                blocked.append(dict(path=str(path.relative_to(root)), reason='checkout is active'))
            else:
                selected.append(candidate(root, path, 'metadata'))
    for path, owner in working:
        try:
            if ownership.retained_overlap(path, protected):
                rows.append(dict(path=str(path.relative_to(root / 'tests/out')), disposition='keep: release'))
                continue
            if busy:
                raise ValueError('checkout is active')
            if path.parent.name == 'release-acceptance' and owner.get('kind') != 'release_acceptance':
                raise ValueError('unrecognized acceptance owner')
            if owner.get('kind') == 'release_acceptance' and ownership.acceptance_busy(path):
                raise ValueError('active acceptance')
            reason = cleanup_blocker(root, path)
            if reason:
                raise ValueError(reason)
            selected.append(candidate(root, path, 'run'))
            rows.append(dict(path=str(path.relative_to(root / 'tests/out')), disposition='delete'))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            blocked.append(dict(path=str(path.relative_to(root)), reason=str(exc)))
            rows.append(dict(path=str(path.relative_to(root / 'tests/out')), disposition='keep: blocked', reason=str(exc)))
    return dict(schema_version=1, kept=[r['record']['tag'] for r in kept],
                protected=[str(p.relative_to(root)) for p in protected], targets=selected,
                blocked=blocked, unmanaged=[str(p.relative_to(root)) for p in unmanaged],
                runs=rows, missing_acceptance=missing)


def target_path(root, relative, *, metadata=False):
    relative = ownership.relative_path(relative)
    parts = relative.parts
    valid = (len(parts) >= 3 and parts[:2] == ('tests', 'out')
             and parts[2] not in ('.retention', '.release-rotation', 'pytest-owners')
             and (len(parts) > 3 or parts[2] not in CONTAINERS)
             or len(parts) == 3 and parts[:2] == ('dist', 'archive') and ownership.RELEASE_TAG.fullmatch(parts[2])
             or len(parts) == 3 and parts[:2] == ('dist', 'evidence') and ownership.RUN_ID.fullmatch(parts[2]))
    if metadata:
        valid = (parts[-1] == '.DS_Store' and
                 (valid or parts in (('dist', '.DS_Store'), ('dist', 'archive', '.DS_Store'),
                                     ('dist', 'evidence', '.DS_Store'))))
    if not valid:
        raise ValueError('invalid retention transaction target')
    return real(root / relative)


def pending(root):
    base = real(root / QUARANTINE)
    entries = list(base.iterdir()) if base.exists() else []
    if len(entries) > 1:
        raise ValueError('multiple retention quarantines require inspection')
    if entries and (not re.fullmatch('[0-9a-f]{32}', entries[0].name) or not entries[0].is_dir()):
        raise ValueError('unrecognized retention quarantine')
    return real(entries[0]) if entries else None


def apply_journal(root, directory):
    """Stage all exact targets before deleting; resume only inventoried quarantine bytes."""
    import pytest_resources
    receipt = directory / 'journal.json'
    if not any(directory.iterdir()):
        directory.rmdir()  # Final journal unlink completed before a crash.
        ownership.sync_directory(directory.parent)
        return []
    journal = ownership.read_object(receipt)
    if (journal.get('schema_version') != 1 or journal.get('root') != str(root)
            or journal.get('transaction') != directory.name or journal.get('state') not in ('staging', 'deleting', 'complete')):
        raise ValueError('invalid retention journal identity')
    rows = journal['targets']
    if not isinstance(rows, list) or not rows:
        raise ValueError('invalid retention journal targets')
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('inventory'), dict)
                or not isinstance(row.get('path'), str) or row.get('kind') not in ('run', 'archive', 'attempt', 'pointer', 'metadata')):
            raise ValueError('invalid retention journal target identity')
        if row['kind'] == 'metadata':
            target_path(root, row['path'], metadata=True)
            continue
        prefix = {'run': 'tests/out/', 'archive': 'dist/archive/',
                  'attempt': 'dist/evidence/', 'pointer': 'dist/evidence/'}[row['kind']]
        if not row['path'].startswith(prefix) or row['kind'] == 'pointer' and not row['path'].endswith('.archived'):
            raise ValueError('retention journal target kind differs from its path')
    paths = [target_path(root, row['path'], metadata=row['kind'] == 'metadata') for row in rows]
    if any(ownership.overlaps(a, b) for i,a in enumerate(paths) for b in paths[i+1:]):
        raise ValueError('overlapping retention journal targets')
    protected = protected_paths(root)
    if any(ownership.retained_overlap(p, protected) for p in paths):
        raise ValueError('retention transaction overlaps current release protection')
    if journal['state'] == 'staging':
        for i, (row, source) in enumerate(zip(rows, paths)):
            target = real(directory / str(i))
            if row['state'] == 'staged':
                if not target.exists() or snapshot(target) != row['inventory']:
                    raise ValueError('staged retention bytes changed')
                continue
            if row['state'] != 'planned':
                raise ValueError('invalid staging state')
            if target.exists():
                if snapshot(target) != row['inventory']:
                    raise ValueError('quarantine differs from planned bytes')
            else:
                if not source.exists() or snapshot(source) != row['inventory']:
                    raise ValueError('retention target changed since planning')
                if row['kind'] == 'metadata' and not source.is_file():
                    raise ValueError('Finder metadata is not a regular file')
                if row['kind'] == 'run':
                    owner = ownership.valid_owner(source)
                    if owner.get('kind') == 'release_acceptance' and ownership.acceptance_busy(source):
                        raise ValueError('active acceptance')
                    reason = cleanup_blocker(root, source)
                    if reason:
                        raise ValueError(reason)
                if source.stat().st_dev != directory.stat().st_dev:
                    raise ValueError('retention quarantine cannot cross filesystems')
                source.rename(target)
                ownership.sync_directory(source.parent)
                ownership.sync_directory(directory)
            row['state'] = 'staged'
            ownership.atomic_json(receipt, journal)
        journal['state'] = 'deleting'
        ownership.atomic_json(receipt, journal)
    for i, (row, source) in enumerate(zip(rows, paths)):
        target = real(directory / str(i))
        if row['state'] == 'removed':
            if target.exists():
                raise ValueError('removed quarantine target reappeared')
            continue
        if row['state'] not in ('staged', 'deleting'):
            raise ValueError('invalid deletion state')
        pytest_resources.guard(root, purpose='disposal', target=source)
        if target.exists():
            remaining = snapshot(target)
            if (row['state'] == 'staged' and remaining != row['inventory']
                    or any(row['inventory'].get(k) != v for k,v in remaining.items())):
                raise ValueError('quarantined bytes changed; deletion refused')
            row['state'] = 'deleting'
            ownership.atomic_json(receipt, journal)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            ownership.sync_directory(directory)
        elif row['state'] != 'deleting':
            raise ValueError('quarantine disappeared before deletion')
        row['state'] = 'removed'
        ownership.atomic_json(receipt, journal)
    journal['state'] = 'complete'
    ownership.atomic_json(receipt, journal)
    if set(p.name for p in directory.iterdir()) != {'journal.json'}:
        raise ValueError('unexpected quarantine contents')
    receipt.unlink()
    directory.rmdir()
    ownership.sync_directory(directory.parent)
    return [row['path'] for row in rows]


def retire_ownership(root):
    # A replacement at an original path keeps its ownership: only closed records
    # whose output is absent are retired, including an acceptance's nested battery.
    import pytest_resources
    pytest_resources.retire_closed(root)


def prune(root, *, apply=False):
    root = real(root)
    with ownership.checkout_lock(root, preview=not apply, purpose='disposal') as busy:
        old_transactions(root)
        directory = pending(root)
        removed = []
        if directory:
            if not apply:
                return dict(apply=False, checkout_busy=busy, pending=str(directory), runs=[], removed=[], failures=[])
            removed += apply_journal(root, directory)
            retire_ownership(root)
            return dict(apply=True, checkout_busy=False, resumed=True, removed=removed, runs=[], failures=[])
        result = plan(root, busy=bool(busy) if not apply else False)
        if apply and result['targets']:
            base = real(root / QUARANTINE)
            base.mkdir(parents=True, exist_ok=True)
            directory = base / uuid.uuid4().hex
            directory.mkdir()
            ownership.sync_directory(base)
            journal = dict(schema_version=1, root=str(root), transaction=directory.name,
                           state='staging', targets=result['targets'])
            ownership.atomic_json(directory / 'journal.json', journal)
            removed += apply_journal(root, directory)
        if apply:
            retire_ownership(root)
        result.update(apply=apply, checkout_busy=bool(busy) if not apply else False, removed=removed,
                      failures=result['blocked'] if apply else [])
        # Inventories live only in the transaction, not in the console report.
        result['targets'] = [{k:v for k,v in row.items() if k != 'inventory'} for row in result['targets']]
        return result
