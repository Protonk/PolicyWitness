#!/usr/bin/env python3
"""Preserve identified Stage 1 observations without changing cleanup ownership.

Run from the repository root after the recorded runs have completed. This is a
record-local preservation utility, not a test dispatcher or a product generator.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEST = HERE / 'evidence'
DEST.mkdir(exist_ok=True)
BASE = '4cd1d6c7f14e3ebacfd2dda219dda85967f64680'


def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def archive(name, source, files):
    files = sorted(files)
    inventory = []
    output = DEST / (name + '.tar.gz')
    with tarfile.open(output, 'w:gz') as tar:
        for path in files:
            relative = str(path.relative_to(source))
            if path.is_symlink():
                inventory.append({'path': relative, 'symlink': str(path.readlink())})
            elif path.is_file():
                inventory.append({'path': relative, 'bytes': path.stat().st_size,
                                  'sha256': digest(path)})
            else:
                continue
            tar.add(path, arcname=relative, recursive=False)
    save(DEST / (name + '.inventory.json'), {'original_root': str(source), 'files': inventory})
    return {'archive': output.name, 'sha256': digest(output),
            'bytes': output.stat().st_size, 'files': len(inventory),
            'original_root': str(source),
            'ownership': 'Copies do not move active cleanup ownership.'}


archives = []
for kind in ('native', 'baseline'):
    run = ROOT / 'tests/out/runs' / ('extension-consolidation-' + kind + '-20261105')
    data = json.loads((run / 'run.json').read_text())
    assert data['completion']['unrun'] == 0
    item = archive(kind, run, [p for p in run.rglob('*') if p.is_file() or p.is_symlink()])
    item['run_id'] = data['run_id']
    item['results'] = data['case_results']
    item['artifact_integrity'] = data['artifact_integrity']
    item['completion'] = data['completion']
    archives.append(item)

for name, source in (
    ('prototype-01-failed', Path('/private/tmp/pw-equipment-prototype-20261105-01')),
    ('prototype-02', Path('/private/tmp/pw-equipment-prototype-20261105-02')),
    ('inheritance-01-partial', Path('/private/tmp/pw-authority-inheritance-20261105-01')),
):
    # Preserve original source package, raw observations, signed fixture bytes,
    # and executed host. Exclude disposable compiler caches/intermediates.
    files = [p for p in source.rglob('*') if (p.is_file() or p.is_symlink())
             and p.relative_to(source).parts[0] != 'build'
             and not any(part.endswith('.dSYM') for part in p.relative_to(source).parts)]
    host = source / 'build/out/Products/Debug/AuthorityPrototype'
    if host.is_file():
        files.append(host)
    archives.append(archive(name, source, files))

# Snapshot exact committed source, rather than relabel a previous dirty build.
# Historical records/reports are not dependencies of the credited controls.
tops = sorted({p.split('/')[0] for p in subprocess.check_output(
    ['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    if p.split('/')[0] not in ('records', 'reports')})
source_archive = DEST / 'source-baseline.tar.gz'
subprocess.run(['git', 'archive', '--format=tar.gz', '--output', str(source_archive),
                BASE, *tops], cwd=ROOT, check=True)
archives.append({'archive': source_archive.name, 'sha256': digest(source_archive),
                 'bytes': source_archive.stat().st_size, 'source_commit': BASE,
                 'excluded_roots': ['records', 'reports']})

app_evidence = ROOT / 'dist/PolicyWitness.app/Contents/Resources/Evidence'
for name in ('manifest.json', 'provenance.json', 'symbols.json'):
    shutil.copyfile(app_evidence / name, DEST / ('baseline-app-' + name))

save(DEST / 'index.json', {'source_commit': BASE, 'archives': archives,
    'credit': 'Stage 1 baseline/prototype observations only; no consolidation candidate exists.',
    'cleanup': 'Prototype 02 container remains owned at its original location; see recovery.json.'})
print(json.dumps([{'archive': a['archive'], 'bytes': a['bytes']} for a in archives], indent=2))
