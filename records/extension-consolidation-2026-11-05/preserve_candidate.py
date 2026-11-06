#!/usr/bin/env python3
"""Preserve identified candidate sources or terminal run evidence, without moving ownership."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent / 'evidence'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def preserve(name, source, paths, context):
    output = DEST / (name + '.tar.gz')
    manifest = DEST / (name + '.json')
    assert not output.exists() and not manifest.exists(), 'preserved observations are immutable'
    files = []
    with tarfile.open(output, 'w:gz') as archive:
        for path in sorted(set(paths)):
            relative = str(path.relative_to(source))
            if path.is_symlink():
                files.append(dict(path=relative, symlink=str(path.readlink())))
            elif path.is_file():
                files.append(dict(path=relative, bytes=path.stat().st_size, sha256=digest(path)))
            else:
                continue
            archive.add(path, arcname=relative, recursive=False)
    value = dict(context, archive=output.name, sha256=digest(output),
                 bytes=output.stat().st_size, original_root=str(source), files=files,
                 ownership='Identified copies do not relocate active ownership or establish resource settlement.')
    save(manifest, value)
    print(json.dumps({k: value[k] for k in ('archive', 'sha256', 'bytes')}))


def source_snapshot(name):
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    # Include previously reviewed generated C/Swift inputs even when ignored.
    previous = json.loads((DEST / 'candidate-11-source.json').read_text())
    names.extend(row['path'] for row in previous['files'])
    paths = []
    for name_in_tree in set(names) - {''}:
        path = Path(name_in_tree)
        if path.parts[0] in ('records', 'reports') or name_in_tree.startswith(('tests/out/', 'builddir/', 'controller/target/', 'runner/.build/')):
            continue
        paths.append(ROOT / path)
    preserve(name, ROOT, paths, dict(
        base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        working_tree_dirty=True,
        worker_identity='6011ef48cde40586569e588279d435e53c7c0e7ddcb86aa28f261053f9ae278b',
        scope='Current source, scripts, fixtures and generated inputs; excludes records/reports and build outputs. This is not a committed implementation.'))


def run_snapshot(name, failed_only):
    source = ROOT / 'tests/out/runs' / name
    result = json.loads((source / 'run.json').read_text())
    owner = json.loads((source / 'owner.json').read_text())
    assert owner['run_id'] == result['run_id'] and Path(owner['out_dir']) == source
    files = [p for p in source.rglob('*') if p.is_file() or p.is_symlink()]
    if failed_only:
        failed = {row['id'] for row in result['case_results'] if row['status'] != 'pass'}
        files = [p for p in files if p.relative_to(source).parts[0] != 'suites'
                 or '/'.join(p.relative_to(source).parts[1:3]) in failed]
    preserve(name + ('-failures' if failed_only else '-complete'), source, files, dict(
        run_id=result['run_id'], completion=result['completion'],
        case_outcome_counts=result['case_outcome_counts'], case_results=result['case_results'],
        scope='Run metadata and complete nonpassing case observations; passed case raw output omitted.' if failed_only else 'Complete terminal run, including raw observations, sources and receipts.',
        artifact_integrity=result.get('artifact_integrity')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source')
    parser.add_argument('--run')
    parser.add_argument('--failures-only', action='store_true')
    args = parser.parse_args()
    assert bool(args.source) != bool(args.run)
    DEST.mkdir(exist_ok=True)
    if args.source:
        source_snapshot(args.source)
    else:
        run_snapshot(args.run, args.failures_only)
