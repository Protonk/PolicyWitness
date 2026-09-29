"""Archive an accepted release attempt under dist/archive/v<version>/ and retain its evidence.

The archive holds the exact accepted ZIP renamed with its version, the staged
guide from the same build, SHA256SUMS, release.json and the attempt's receipts
moved under evidence/ (a `<attempt>.archived` pointer stays behind). The attempt
must record an accepted notarization and a passed archive acceptance of the same
bytes, and the ZIP must be stamped exactly at the annotated tag v<version>. A
completed default battery run against the final app can be recorded beside the
acceptance run; both are appended to tests/RETAINED.json. Publishing is the
separate release_publish.py step, which fills `origin` afterwards.
"""
import argparse
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import zipfile

from artifact import digest
import retention

ROOT = Path(__file__).resolve().parents[2]
STEPS = ('notarization', 'staple', 'staple-validation', 'gatekeeper', 're-zip')


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def load_attempt(attempt):
    attempt = Path(attempt).resolve()
    record = retention.read_object(attempt / 'release.json')
    acceptance = retention.read_object(attempt / 'acceptance.json')
    notarization = retention.read_object(attempt / 'notarization/result.json')
    return attempt, record, acceptance, notarization


def find_latest(dist):
    """The one attempt whose accepted archive is the current final ZIP."""
    final = Path(dist) / 'PolicyWitness.zip'
    if not final.is_file():
        raise ValueError(f'no final archive at {final}')
    final_hash = digest(final)
    base = Path(dist) / 'evidence'
    matches = []
    for candidate in sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []:
        try:
            _, record, acceptance, notarization = load_attempt(candidate)
        except (OSError, ValueError):
            continue
        if (record.get('archive') == str(final.resolve()) and acceptance.get('ok') is True
                and acceptance.get('sha256') == final_hash and notarization.get('state') == 'accepted'):
            matches.append(candidate)
    if len(matches) != 1:
        raise ValueError(f'expected exactly one accepted attempt for {final}; found {len(matches)}')
    return matches[0]


def battery_record(root, dist, battery):
    path = retention.bounded_path(root, battery)
    run = retention.read_object(path / 'run.json')
    problems = []
    if run.get('ok') is not True or run.get('terminal') is not True:
        problems.append('battery run is not a completed passing run')
    counts, completion = run.get('counts') or {}, run.get('completion') or {}
    if counts.get('fail') or completion.get('skipped') or completion.get('unrun') or run.get('harness_errors'):
        problems.append('battery has failures, skips, unrun cases or harness errors')
    if run.get('requested_cases') or run.get('requested_suites'):
        problems.append('battery must be the default selection')
    integrity = run.get('artifact_integrity') or {}
    if integrity.get('unchanged') is not True or integrity.get('valid_before') is not True:
        problems.append('battery did not confirm an unchanged, valid app')
    if integrity.get('app') != str((Path(dist) / 'PolicyWitness.app').resolve()):
        problems.append('battery did not run against the final app')
    if problems:
        raise ValueError('; '.join(problems))
    inventory = 'artifact-integrity/before.json'
    return dict(path=str(path.relative_to(root / 'tests/out')), run_id=run['run_id'],
                app_inventory=inventory if (path / inventory).is_file() else None)


def retain(root, entries):
    """Append entries to tests/RETAINED.json; restore the file if the result would be invalid."""
    path = root / 'tests/RETAINED.json'
    original = path.read_text()
    index = retention.read_object(path)
    existing = {entry.get('path') for entry in index['runs']}
    added = [entry for entry in entries if entry['path'] not in existing]
    index['runs'] += added
    path.write_text(json.dumps(index, indent=2) + '\n')
    try:
        retention.load_index(root)
    except ValueError:
        path.write_text(original)
        raise
    return added


def archive(attempt, *, dist, root=ROOT, notes=None, battery=None):
    attempt, record, acceptance, notarization = load_attempt(attempt)
    root, dist = Path(root), Path(dist)
    problems = []
    if notarization.get('state') != 'accepted':
        problems.append(f"notarization state is {notarization.get('state')!r}, not accepted")
    if acceptance.get('ok') is not True:
        problems.append('archive acceptance did not pass')
    final = Path(record['archive'])
    if not final.is_file():
        raise ValueError(f'final archive missing: {final}')
    final_hash = digest(final)
    if acceptance.get('sha256') != final_hash:
        problems.append('final ZIP bytes differ from the accepted archive')
    guide = final.parent / 'PolicyWitness.md'
    if not guide.is_file():
        problems.append(f'staged guide missing beside the archive: {guide}')
    with zipfile.ZipFile(final) as zipped:
        info = plistlib.loads(zipped.read('PolicyWitness.app/Contents/Info.plist'))
    version = str(info.get('CFBundleShortVersionString'))
    tag = f'v{version}'
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        problems.append(f'ZIP stamps version {version!r}')
    commit = git(root, 'rev-parse', f'{tag}^{{commit}}')
    if commit is None:
        problems.append(f'no local tag {tag}')
    else:
        if git(root, 'cat-file', '-t', tag) != 'tag':
            problems.append(f'{tag} is a lightweight tag; release tags are annotated')
        if info.get('PWBuildCommit') != commit:
            problems.append(f"ZIP was built from {info.get('PWBuildCommit')}, but {tag} names {commit}")
        if info.get('PWBuildDescribe') != tag:
            problems.append(f"ZIP was built at {info.get('PWBuildDescribe')!r}, not exactly at {tag}")
    dest = dist / 'archive' / tag
    if dest.exists():
        problems.append(f'{dest} already exists; a version is archived once')
    acceptance_run = Path(acceptance['path']).parent
    try:
        acceptance_entry = dict(
            path=str(acceptance_run.relative_to(root / 'tests/out')),
            run_id=retention.read_object(acceptance_run / 'tests/run.json')['run_id'],
            reason=f'PolicyWitness {version} release ZIP acceptance: signatures, staple, Gatekeeper, allow and '
                   f'deny witnesses, and unchanged archive and extracted app; archived as {tag}.',
            source=commit, app_inventory='before.json' if (acceptance_run / 'before.json').is_file() else None)
    except (ValueError, OSError, KeyError) as exc:
        problems.append(f'acceptance run is not readable: {exc}')
        acceptance_entry = None
    battery_entry = None
    if battery is not None:
        try:
            found = battery_record(root, dist, battery)
            battery_entry = dict(path=found['path'], run_id=found['run_id'],
                                 reason=f'PolicyWitness {version} release validation: the default battery passed '
                                        f'against the final stapled app with no skips, unrun cases or harness '
                                        f'errors and an unchanged app; archived as {tag}.',
                                 source=commit, app_inventory=found['app_inventory'])
        except (ValueError, OSError, KeyError) as exc:
            problems.append(f'battery run rejected: {exc}')
    if notes is not None and not Path(notes).is_file():
        problems.append(f'release notes missing: {notes}')
    if problems:
        raise ValueError('; '.join(problems))

    dest.mkdir(parents=True)
    name = f'PolicyWitness-{version}.zip'
    shutil.copy2(final, dest / name)
    shutil.copy2(guide, dest / 'PolicyWitness.md')
    (dest / 'SHA256SUMS').write_text(f'{digest(dest / name)}  {name}\n'
                                     f'{digest(dest / "PolicyWitness.md")}  PolicyWitness.md\n')
    evidence = dest / 'evidence'
    shutil.move(str(attempt), str(evidence))
    attempt.with_name(attempt.name + '.archived').write_text(f'{evidence}\n')
    if notes is not None:
        shutil.copy2(notes, evidence / 'release-notes.md')
    relative_attempt = attempt.relative_to(root) if root in attempt.parents else attempt
    receipts = [dict(original_path=str(relative_attempt / step), archived_path=f'evidence/{step}')
                for step in STEPS if (evidence / step).is_dir()]
    receipts += [dict(original_path=str(relative_attempt / item), archived_path=f'evidence/{item}')
                 for item in ('acceptance.json', 'release.json')]
    entries = [entry for entry in (acceptance_entry, battery_entry) if entry is not None]
    (dest / 'release.json').write_text(json.dumps(dict(
        schema_version=1, version=version, build_number=str(info.get('CFBundleVersion')), tag=tag,
        source_commit=commit, origin=None, archive=name, sha256=final_hash, guide='PolicyWitness.md',
        notarization_submission_id=notarization.get('submission_id'),
        submitted_sha256=record.get('submitted_sha256'),
        acceptance=dict(path=acceptance_entry['path'] + '/acceptance.json', ok=True, sha256=final_hash),
        battery=None if battery_entry is None else dict(path=battery_entry['path'], run_id=battery_entry['run_id']),
        receipts=receipts, notes=[]), indent=2) + '\n')
    added = retain(root, entries)
    return dest, added


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('attempt', nargs='?', type=Path, help='release attempt directory')
    parser.add_argument('--latest', action='store_true',
                        help='select the one attempt that accepted the current final ZIP')
    parser.add_argument('--dist', default='dist', type=Path, help='distribution directory')
    parser.add_argument('--battery', type=Path, help='completed default battery run against the final app')
    parser.add_argument('--notes', type=Path, help='release notes to archive as evidence/release-notes.md')
    args = parser.parse_args(argv)
    if bool(args.attempt) == args.latest:
        parser.error('name one attempt directory or pass --latest')
    dist = args.dist if args.dist.is_absolute() else ROOT / args.dist
    try:
        attempt = find_latest(dist) if args.latest else args.attempt
        dest, added = archive(attempt, dist=dist, root=ROOT, notes=args.notes, battery=args.battery)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'STOP: {exc}\n')
    print(dest)
    print((dest / 'SHA256SUMS').read_text(), end='')
    for entry in added:
        print(f"retained {entry['path']} ({entry['run_id']})")
    if added:
        print('Commit the retention index: git commit tests/RETAINED.json -m '
              f'"Retain the {json.loads((dest / "release.json").read_text())["version"]} release evidence"')
    return 0


if __name__ == '__main__':
    sys.exit(main())
