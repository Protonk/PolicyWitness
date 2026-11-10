"""Archive windows, portable evidence and interrupted cleanup, observed on real files."""
import hashlib
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import plistlib
import zipfile
from unittest.mock import patch

from check_release_publish import ROOT, git, make_repo, make_dist, completed_output
import artifact
import historical_release_storage
import execution_contract
import release_archive
import release_preflight
import release_runs
import retention
import run_ownership


def reject(call, needle):
    try:
        call()
    except (ValueError, OSError) as exc:
        assert needle in str(exc), (needle, exc)
    else:
        raise AssertionError(f'operation should have refused: {needle}')


def make_release(repo, version):
    git(repo, 'tag', '-a', 'v' + version, '-m', 'fixture ' + version)
    dist, attempt = make_dist(repo, version=version)
    acceptance = repo / 'tests/out/release-acceptance' / ('run-' + version.replace('.', '-'))
    (acceptance / 'payload.bin').write_bytes(b'original\x00\xff')
    (acceptance / 'empty').mkdir()
    (acceptance / 'outside-link').symlink_to(repo / 'outside')
    archive = release_archive.archive(attempt, dist=dist, root=repo)
    return archive, acceptance


def fixture(out, name):
    work = out / name
    work.mkdir()
    repo = make_repo(work)
    (repo / 'outside').write_bytes(b'outside evidence')
    old, previous = make_release(repo, '0.9.0')
    new, current = make_release(repo, '0.9.1')
    return repo, old, previous, new, current


def portable(out):
    repo, old, previous, new, _ = fixture(out, 'portable')
    captured = run_ownership.read_object(old / 'release.json')['execution_contract']
    catalog = run_ownership.read_object(repo / 'tests/catalog.json')
    catalog['suites']['fixture']['cases'].append('later-case')
    run_ownership.atomic_json(repo / 'tests/catalog.json', catalog)
    assert execution_contract.defaults(repo) != captured
    assert release_runs.verify_release(old)[0]['execution_contract'] == captured
    original = artifact.inventory(previous)
    copy = out / 'detached-release'
    shutil.copytree(old, copy, symlinks=True)
    shutil.rmtree(repo / 'tests/out')
    _, manifest = release_runs.verify_release(copy)
    assert manifest['schema_version'] == 3 and set(manifest['runs']) == {'acceptance'}, manifest
    assert manifest['runs']['acceptance']['inventory'] == original
    assert manifest['battery'] == dict(role='acceptance', path='tests/run.json'), manifest['battery']
    # Independently inspect every stored file and symlink. No live test path is used.
    with tarfile.open(copy / release_runs.BUNDLE / 'runs.tar.gz') as packed:
        names = set()
        for member in packed:
            assert member.name == 'acceptance' or member.name.startswith('acceptance/'), member.name
            if member.name == 'acceptance':
                continue
            names.add(member.name)
            row = original[member.name[len('acceptance/'):]]
            if member.isfile():
                assert hashlib.sha256(packed.extractfile(member).read()).hexdigest() == row['sha256']
            elif member.issym():
                assert member.linkname == row['symlink']
        assert 'acceptance/tests/run.json' in names, 'the nested battery is not inside the packed acceptance'
    record = json.loads((copy / 'release.json').read_text())
    assert (copy / record['acceptance']['path']).is_file()
    assert (copy / record['battery']['path']).is_file()
    assert json.loads((copy / record['battery']['path']).read_text())['run_id'] == record['battery']['run_id']
    manifest_path = copy / release_runs.BUNDLE / 'manifest.json'
    original_manifest = manifest_path.read_bytes()
    original_record = (copy / 'release.json').read_bytes()
    manifest['runs']['acceptance']['retained']['run_id'] = 'different-owner'
    run_ownership.atomic_json(manifest_path, manifest)
    record['test_evidence']['sha256'] = artifact.digest(manifest_path)
    run_ownership.atomic_json(copy / 'release.json', record)
    reject(lambda: release_runs.verify_release(copy), 'acceptance owner differs')
    manifest_path.write_bytes(original_manifest)
    (copy / 'release.json').write_bytes(original_record)
    (copy / release_runs.BUNDLE / 'runs.tar.gz').write_bytes(b'corrupt')
    reject(lambda: release_runs.verify_release(copy), 'checksum mismatch')


def historical_storage(out):
    """Storage recognition never grants historical evidence current acceptance."""
    root = out / 'historical'; root.mkdir()
    archive = root / 'dist/archive/v0.3.3'
    bundle = archive / release_runs.BUNDLE; bundle.mkdir(parents=True)
    source = '1bf0341cd06c48122af1635e8aa8cac77517d9e1'
    record = dict(schema_version=1, tag='v0.3.3', version='0.3.3', source_commit=source,
                  archive='PolicyWitness-0.3.3.zip', guide='PolicyWitness.md')
    manifest = dict(schema_version=1, tag='v0.3.3', source_commit=source,
                    archive='runs.tar.gz', runs={}, summaries={})
    with tarfile.open(bundle / 'runs.tar.gz', 'w:gz') as packed:
        for role in ('acceptance', 'battery'):
            relative = ('release-acceptance/' if role == 'acceptance' else 'runs/') + role
            path = root / 'tests/out' / relative; path.mkdir(parents=True)
            summary = 'acceptance.json' if role == 'acceptance' else 'run.json'
            # Deliberately not valid current acceptance or default-battery evidence.
            (path / summary).write_text(json.dumps(dict(run_id=role, historical_storage=True)))
            (path / 'owner.json').write_text(json.dumps(dict(schema_version=1, run_id=role, out_dir=str(path))))
            entry = dict(path=relative, run_id=role, source=source, release='v0.3.3')
            manifest['runs'][role] = dict(retained=entry, inventory=artifact.inventory(path))
            packed.add(path, arcname=role)
            shutil.copy2(path / summary, bundle / (role + '.json'))
            manifest['summaries'][role + '.json'] = artifact.digest(bundle / (role + '.json'))
            record[role] = dict(path=release_runs.BUNDLE + '/' + role + '.json',
                                original_path=relative + '/acceptance.json' if role == 'acceptance' else relative)
            if role == 'battery': record[role]['run_id'] = role
    manifest['sha256'] = artifact.digest(bundle / 'runs.tar.gz')
    with zipfile.ZipFile(archive / record['archive'], 'w') as zipped:
        zipped.writestr('PolicyWitness.app/Contents/Info.plist', plistlib.dumps(dict(
            PWBuildCommit=source, PWBuildDescribe=record['tag'], CFBundleShortVersionString=record['version'])))
    (archive / 'PolicyWitness.md').write_text('historical guide')
    record['sha256'] = artifact.digest(archive / record['archive'])
    (archive / 'SHA256SUMS').write_text(''.join(artifact.digest(archive / name) + '  ' + name + '\n'
                                            for name in (record['archive'], 'PolicyWitness.md')))
    def write():
        run_ownership.atomic_json(bundle / 'manifest.json', manifest)
        record['test_evidence'] = dict(path=release_runs.BUNDLE + '/manifest.json', sha256=artifact.digest(bundle / 'manifest.json'))
        run_ownership.atomic_json(archive / 'release.json', record)
    write()
    before = artifact.inventory(root)
    assert retention.archives(root, verify=True)[0]['record'] == record
    assert artifact.inventory(root) == before
    reject(lambda: release_runs.producer_contract(record), 'producer execution contract')
    reject(lambda: release_runs.verify_bundle(bundle, expected_contract={}), 'expected schema 3')
    original_record, original_manifest = copy.deepcopy(record), copy.deepcopy(manifest)
    for mutation, diagnostic in (
        ('source', 'unrecognized historical'), ('layout', 'historical run identity'),
        ('summary', 'summary checksum'), ('bundle', 'archive checksum'),
        ('relabel', 'must be acceptance/tests/run.json')):
        record, manifest = copy.deepcopy(original_record), copy.deepcopy(original_manifest)
        if mutation == 'source':
            record['source_commit'] = manifest['source_commit'] = 'f' * 40
        elif mutation == 'layout': manifest['runs']['battery']['retained']['path'] = '../escape'
        elif mutation == 'summary': manifest['summaries']['battery.json'] = '0' * 64
        elif mutation == 'bundle': manifest['sha256'] = '0' * 64
        else:
            record['schema_version'] = 2
            manifest.update(schema_version=3, battery=dict(role='battery', path='run.json'))
        write()
        if mutation == 'layout': diagnostic = 'invalid relative path'
        reject(lambda: retention.archives(root, verify=True), diagnostic)
    record, manifest = original_record, original_manifest; write()
    summary = bundle / 'battery.json'; saved = summary.read_bytes()
    summary.unlink(); summary.symlink_to(root / 'tests/out/runs/battery/run.json')
    reject(lambda: retention.archives(root, verify=True), 'symlink redirects')
    summary.unlink(); summary.write_bytes(saved)
    assert retention.archives(root, verify=True)


def battery_contract(out):
    """Only a default-selection nested battery can support the release."""
    work = out / 'battery-contract'
    work.mkdir()
    repo = make_repo(work)
    archive, acceptance = make_release(repo, '0.9.0')
    battery = acceptance / 'tests'
    record, manifest = release_runs.verify_release(archive)
    run = run_ownership.read_object(battery / 'run.json')
    run['plan']['selection']['mode'] = 'all'
    run_ownership.atomic_json(battery / 'run.json', run)
    runs = {role: (repo / 'tests/out' / value['retained']['path'], value['retained'])
            for role, value in manifest['runs'].items()}
    shutil.rmtree(archive / release_runs.BUNDLE)
    with run_ownership.checkout_lock(repo):
        reference = release_runs.pack(archive / release_runs.BUNDLE, tag=record['tag'],
                                      source=record['source_commit'], runs=runs,
                                      battery=('acceptance', 'tests/run.json'), expected_contract=record['execution_contract'])
    record['test_evidence'] = reference
    run_ownership.atomic_json(archive / 'release.json', record)
    reject(lambda: release_runs.verify_release(archive), 'not the default selection')
    # Malformed references must produce a refusal, not an uncaught TypeError.
    record['battery'] = None
    run_ownership.atomic_json(archive / 'release.json', record)
    reject(lambda: release_runs.verify_release(archive), 'does not support the release')
    manifest = run_ownership.read_object(archive / release_runs.BUNDLE / 'manifest.json')
    manifest['battery']['path'] = 'acceptance.json'
    run_ownership.atomic_json(archive / release_runs.BUNDLE / 'manifest.json', manifest)
    reject(lambda: release_runs.verify_bundle(archive / release_runs.BUNDLE, expected_contract=record['execution_contract']),
           'must be acceptance/tests/run.json')



def windows(out):
    work = out / 'windows'; work.mkdir()
    repo = make_repo(work)
    versions = ['0.3.7', '0.3.8', '0.3.9', '0.3.10', '0.4.0', '0.4.1']
    assert retention.prune(repo)['kept'] == []
    entries = []
    for i, version in enumerate(versions):
        archive, acceptance = make_release(repo, version)
        entries.append((archive, acceptance))
        before = artifact.inventory(repo)
        report = retention.prune(repo)
        assert artifact.inventory(repo) == before, 'preview wrote files'
        assert report['kept'] == ['v' + v for v in versions[max(0,i-3):i+1]]
        archives = {row['path'] for row in report['targets'] if row['kind'] == 'archive'}
        assert archives == {'dist/archive/v' + v for v in versions[:max(0,i-3)]}
    survivors = {p: artifact.inventory(p) for p,_ in entries[-4:]}
    historical = repo / 'dist/archive/v0.3.3'
    shutil.copytree(out / 'historical/dist/archive/v0.3.3', historical)
    # Positively linked superseded copies expire; unrelated material cannot borrow a name.
    linked = repo / 'dist/evidence/superseded'; linked.mkdir()
    record = run_ownership.read_object(entries[0][0] / 'release.json')
    (linked / 'release.json').write_text(json.dumps(dict(submitted_sha256=record['sha256'])))
    (linked / 'duplicate.zip').write_bytes(b'fixture bytes')
    unrelated = repo / 'dist/evidence/unrelated'; unrelated.mkdir()
    (unrelated / 'file').write_text('unassociated')
    before_unrelated = artifact.inventory(unrelated)
    rehearsal = repo / 'dist/evidence/rehearsal'; rehearsal.mkdir()
    (rehearsal / 'release.json').write_text(json.dumps(dict(schema_version=1, build=dict(
        PWBuildDescribe='v0.4.1-1-g1234567', CFBundleShortVersionString='0.4.1'), submitted_sha256='e' * 64)))
    before_rehearsal = artifact.inventory(rehearsal)
    metadata = [repo / name / '.DS_Store' for name in ('dist', 'dist/archive', 'dist/evidence')]
    for path in metadata: path.write_bytes(b'finder')
    loose = repo / 'dist/evidence/operator-note'; loose.write_bytes(b'keep')
    result = retention.prune(repo, apply=True)
    assert not linked.exists() and artifact.inventory(unrelated) == before_unrelated
    assert not result['failures'], result['failures']
    assert {'dist/evidence/unrelated', 'dist/evidence/rehearsal'} <= set(result['unmanaged'])
    assert artifact.inventory(rehearsal) == before_rehearsal
    # A file that is neither an attempt nor a pointer is reported, kept and not a failure.
    assert loose.read_bytes() == b'keep' and 'dist/evidence/operator-note' in result['unmanaged']
    assert all(not p.exists() and str(p.relative_to(repo)) in result['removed'] for p in metadata)
    # Missing association is normal; an unreadable record is still a real blocker.
    receipt = rehearsal / 'release.json'; saved = receipt.read_bytes()
    receipt.write_text('{')
    refused = retention.prune(repo, apply=True)
    assert any(r['path']=='dist/evidence/rehearsal' for r in refused['failures'])
    receipt.write_bytes(saved)
    assert not retention.prune(repo, apply=True)['failures'], 'unassociated evidence permanently failed cleanup'
    assert sorted((p.name for p in (repo / 'dist/archive').iterdir()), key=retention.version) == ['v' + v for v in versions[-4:]]
    assert not historical.exists() and retention.pending(repo) is None, 'last historical storage obligation did not expire'
    assert [p.exists() for _,p in entries] == [False]*5 + [True]
    for path, inventory in survivors.items():
        assert artifact.inventory(path) == inventory, 'cleanup changed surviving archive bytes'
    for pointer in (repo / 'dist/evidence').glob('*.archived'):
        assert Path(pointer.read_text().strip()).is_dir(), 'dangling archived pointer'
    for tag in ('v0.3.7', 'v0.3.11', 'v0.4.1'):
        reject(lambda: retention.require_new_release(repo, tag), 'must be newer')
    retention.require_new_release(repo, 'v0.4.2')
    # Both strict preflight and direct archival use the same monotonic guard.
    git(repo, 'checkout', '--detach', 'v0.3.7')
    _, problems = release_preflight.inspect(repo)
    assert any('must be newer' in p for p in problems), problems
    dist, attempt = make_dist(repo, version='0.3.7')
    reject(lambda: release_archive.archive(attempt, dist=dist, root=repo), 'must be newer')
    reject(lambda: retention.distribution(repo, repo / 'alternate'), 'checkout distribution root')
    # Fresh provenance cites the archive's captured identities, not current measurements.
    latest = run_ownership.read_object(entries[-1][0] / 'release.json')
    manifest = run_ownership.read_object(entries[-1][0] / release_runs.BUNDLE / 'manifest.json')
    footprint = repo / 'docs/FOOTPRINT.md'
    prefix = '## Provenance of measured rows\n'
    valid = prefix + 'dist/archive/v0.4.1/evidence/test-runs/runs.tar.gz\n`' + latest['battery']['run_id'] + '`\n`' + manifest['runs']['acceptance']['retained']['run_id'] + '`\n'
    footprint.write_text(valid)
    assert release_preflight.footprint_provenance(repo)['status'] == 'current'
    for changed in (valid.replace('v0.4.1','v0.3.10'), valid.replace(latest['battery']['run_id'],'wrong'), valid.replace(manifest['runs']['acceptance']['retained']['run_id'],'wrong')):
        footprint.write_text(changed)
        reject(lambda: release_preflight.footprint_provenance(repo), 'measured-row provenance')


def blockers_and_handoff(out):
    repo, old, previous, new, current = fixture(out, 'blockers')
    for path in (current, current / 'tests', current.parent):
        reject(lambda: run_ownership.replacement_allowed(repo, path, retention.protected_paths(repo)), 'overlaps retained')
    idle = repo / 'tests/out/runs/interrupted'; completed_output(idle)
    (idle / 'run.json').unlink()
    session = idle / 'suites/runner_byoxpc/control/artifacts/session.json'
    session.parent.mkdir(parents=True); session.write_text('{"removed":false}')
    report = retention.prune(repo, apply=True)
    assert idle.exists() and any('pending external' in r['reason'] for r in report['failures'])
    session.write_text('{"removed":true}')
    assert 'tests/out/runs/interrupted' in retention.prune(repo, apply=True)['removed']
    active = repo / 'tests/out/release-acceptance/active'
    with run_ownership.acceptance_output(repo, active, lambda: retention.protected_paths(repo)):
        assert any('active acceptance' in r['reason'] for r in retention.prune(repo)['blocked'])
    assert 'tests/out/release-acceptance/active' in retention.prune(repo, apply=True)['removed']
    # Interrupted after acceptance, before archive: derive protection from existing receipts.
    git(repo, 'tag', '-a', 'v0.9.2', '-m', 'next')
    dist, attempt = make_dist(repo, version='0.9.2')
    handoff = repo / 'tests/out/release-acceptance/run-0-9-2'
    assert handoff in retention.protected_paths(repo)
    retention.prune(repo, apply=True)
    assert handoff.exists() and current.exists()
    pointer = attempt / 'acceptance.json'; original = pointer.read_bytes()
    data = json.loads(original); data['sha256'] = '0'*64; pointer.write_text(json.dumps(data))
    assert handoff not in retention.protected_paths(repo), 'foreign final hash manufactured protection'
    pointer.write_bytes(original)
    owner = handoff / 'owner.json'; saved = owner.read_bytes()
    data = json.loads(saved); data['run_id'] = 'changed'; owner.write_text(json.dumps(data))
    reject(lambda: retention.prune(repo), 'inconsistent accepted handoff')
    owner.write_bytes(saved)
    duplicate = attempt.with_name(attempt.name + '-duplicate'); shutil.copytree(attempt, duplicate)
    reject(lambda: retention.prune(repo), 'ambiguous accepted release handoff')
    shutil.rmtree(duplicate)
    # Copy failure leaves both current acceptance and unarchived handoff intact.
    with patch.object(release_runs, 'pack', side_effect=OSError('controlled pack failure')):
        reject(lambda: release_archive.archive(attempt, dist=dist, root=repo), 'controlled pack failure')
    assert not (dist / 'archive/v0.9.2').exists() and current.exists() and handoff.exists()
    archived = release_archive.archive(attempt, dist=dist, root=repo)
    retention.prune(repo, apply=True)
    assert archived.exists() and handoff.exists() and not current.exists()
    # Old recovery state is a blocker, never silently interpreted as a new journal.
    receipt = old / 'evidence/rotation.json'; receipt.write_text('{"state":"staging"}')
    reject(lambda: retention.prune(repo, apply=True), 'unfinished old release journal')
    receipt.write_text('{"state":"complete"}')
    pending = repo / 'tests/out/.release-rotation'; pending.mkdir()
    (pending / 'old').touch()
    reject(lambda: retention.prune(repo), 'unfinished old release quarantine')


def crash(repo, mode):
    rename, write, remove, unlink = Path.rename, run_ownership.atomic_json, shutil.rmtree, Path.unlink
    def interrupted_rename(path, target):
        result = rename(path, target)
        if path.name == 'run-0-9-0':
            os._exit(91)
        return result
    def interrupted_write(path, value):
        write(path, value)
        if path.name == 'journal.json' and value.get('state') == 'deleting':
            os._exit(92)
    def interrupted_delete(path, *args, **kwargs):
        if (Path(path) / 'payload.bin').exists():
            if mode == 'partial':
                (Path(path) / 'payload.bin').unlink()
                os._exit(93)
            remove(path, *args, **kwargs)
            os._exit(94)
        return remove(path, *args, **kwargs)
    def interrupted_pointer(path, *args, **kwargs):
        pointer = (path.parent.parent == repo / retention.QUARANTINE and path.name.isdigit()
                   and path.is_file() and path.read_text().endswith('/dist/archive/v0.9.0/evidence\n'))
        result = unlink(path, *args, **kwargs)
        if pointer:
            os._exit(95)
        return result
    target, attribute, replacement = {
        'rename': (Path, 'rename', interrupted_rename),
        'staged': (run_ownership, 'atomic_json', interrupted_write),
        'partial': (shutil, 'rmtree', interrupted_delete),
        'deleted': (shutil, 'rmtree', interrupted_delete),
        'pointer': (Path, 'unlink', interrupted_pointer),
    }[mode]
    with patch.object(target, attribute, replacement):
        retention.prune(repo, apply=True)
    raise AssertionError('crash boundary not reached')


def interrupted(out):
    for mode, code in [('rename',91),('staged',92),('partial',93),('deleted',94),('pointer',95)]:
        repo, old, previous, new, current = fixture(out, 'crash-' + mode)
        if mode == 'pointer':
            for version in ('0.9.2', '0.9.3', '0.9.4'):
                _, current = make_release(repo, version)
        before = artifact.inventory(new)
        process = subprocess.run([sys.executable, '-B', '-S', __file__, '--crash', str(repo), mode], capture_output=True, timeout=60)
        assert process.returncode == code, (mode,process.stderr)
        quarantine = retention.pending(repo)
        journal = run_ownership.read_object(quarantine / 'journal.json')
        index = next(i for i,r in enumerate(journal['targets']) if r['path'].endswith('/run-0-9-0'))
        target = quarantine / str(index)
        if mode == 'rename':
            (target / 'payload.bin').write_bytes(b'changed')
            reject(lambda: retention.prune(repo, apply=True), 'quarantine differs')
            (target / 'payload.bin').write_bytes(b'original\x00\xff')
        completed_output(previous)
        replacement = artifact.inventory(previous)
        result = retention.prune(repo, apply=True)
        assert result['resumed'] and retention.pending(repo) is None
        assert artifact.inventory(previous) == replacement, 'resume deleted replacement at original path'
        assert artifact.inventory(new) == before and current.exists()
        for pointer in (repo / 'dist/evidence').glob('*.archived'):
            assert Path(pointer.read_text().strip()).is_dir(), 'resumption left a dangling archived pointer'
    repo, _, previous, new, _ = fixture(out, 'locking')
    with run_ownership.checkout_lock(repo):
        env = {k:v for k,v in os.environ.items() if not k.startswith('PW_CHECKOUT_LOCK_')}
        result = subprocess.run([sys.executable,'-B','-S','-c',
            'import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import retention;retention.prune(Path(sys.argv[2]),apply=True)',
            str(ROOT / 'tests/lib'),str(repo)],env=env,capture_output=True,timeout=30)
        assert result.returncode and b'checkout busy' in result.stderr
    assert previous.exists()


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    portable(out)
    historical_storage(out)
    battery_contract(out)
    windows(out)
    blockers_and_handoff(out)
    interrupted(out)
    print('release retention controls passed: exact window, current evidence, derived protection, resource blockers and crash recovery')


if __name__ == '__main__':
    if sys.argv[1] == '--crash':
        crash(Path(sys.argv[2]), sys.argv[3])
    else:
        main(Path(sys.argv[1]).resolve())
