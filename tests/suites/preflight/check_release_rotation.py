"""Real files, portable archives, abrupt exits and competing processes test rotation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from unittest.mock import patch

from check_release_publish import ROOT, git, make_repo, make_dist, make_battery, completed_output
import artifact
import release_archive
import release_cleanup
import release_rotate
import release_runs
import retention


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
    battery = make_battery(repo, dist, version=version)
    clock = 100 + int(version.split('.')[-1]) * 100
    acceptance = repo / 'tests/out/release-acceptance' / ('run-' + version.replace('.', '-'))
    set_times(acceptance / 'tests', clock, clock + 1)
    owner = retention.read_object(acceptance / 'owner.json')
    owner.update(started_at_unix_ms=clock, finished_at_unix_ms=clock + 1)
    retention.atomic_json(acceptance / 'owner.json', owner)
    set_times(battery, clock + 10, clock + 11)
    (battery / 'payload.bin').write_bytes(b'original\x00\xff')
    (battery / 'empty').mkdir()
    (battery / 'outside-link').symlink_to(repo / 'outside')
    archive, _ = release_archive.archive(attempt, dist=dist, root=repo, battery=battery)
    return archive, battery


def set_times(path, started, finished=None, *, ok=True):
    owner = retention.read_object(path / 'owner.json')
    owner['started_at_unix_ms'] = started
    retention.atomic_json(path / 'owner.json', owner)
    if finished is None:
        (path / 'run.json').unlink(missing_ok=True)
    else:
        run = retention.read_object(path / 'run.json')
        run.update(started_at_unix_ms=started, finished_at_unix_ms=finished,
                   duration_ms=finished - started, ok=ok)
        retention.atomic_json(path / 'run.json', run)


def local_run(repo, name, started, finished=None, *, ok=True):
    path = repo / 'tests/out/runs' / name
    completed_output(path)
    set_times(path, started, finished, ok=ok)
    return path


def fixture(out, name):
    work = out / name
    work.mkdir()
    repo = make_repo(work)
    (repo / 'outside').write_bytes(b'do not follow or delete this symlink target')
    (repo / '.tmp').mkdir()
    (repo / '.tmp/scratch').write_bytes(b'not release rotation')
    old, battery = make_release(repo, '0.9.0')
    new, current = make_release(repo, '0.9.1')
    return repo, old, battery, new, current


def change_entry(repo, path, change):
    value = retention.read_object(repo / 'tests/RETAINED.json')
    entry = next(e for e in value['runs'] if e['path'] == str(path.relative_to(repo / 'tests/out')))
    change(entry)
    with retention.checkout_lock(repo):
        retention.write_index(repo, value)


def portable(out):
    repo, old, battery, new, _ = fixture(out, 'portable')
    original = artifact.inventory(battery)
    copy = out / 'detached-release'
    shutil.copytree(old, copy, symlinks=True)
    shutil.rmtree(repo / 'tests/out')
    _, manifest = release_runs.verify_release(copy)
    assert manifest['runs']['battery']['inventory'] == original
    # Independently inspect every stored file and symlink. No live test path is used.
    with tarfile.open(copy / release_runs.BUNDLE / 'runs.tar.gz') as packed:
        for member in packed:
            if not member.name.startswith('battery/'):
                continue
            row = original[member.name[len('battery/'):]]
            if member.isfile():
                assert hashlib.sha256(packed.extractfile(member).read()).hexdigest() == row['sha256']
            elif member.issym():
                assert member.linkname == row['symlink']
    record = json.loads((copy / 'release.json').read_text())
    assert (copy / record['acceptance']['path']).is_file()
    assert (copy / record['battery']['path']).is_file()
    (copy / release_runs.BUNDLE / 'runs.tar.gz').write_bytes(b'corrupt')
    reject(lambda: release_runs.verify_release(copy), 'checksum mismatch')


def ordinary(out):
    repo, old, battery, new, current = fixture(out, 'ordinary')
    loose = local_run(repo, 'zzz-old-development', 120, 121)
    latest = local_run(repo, 'aaa-newest-failed', 300, 301, ok=False)
    os.utime(loose, (999999999, 999999999))
    os.utime(latest, (1, 1))  # Neither name nor filesystem mtime establishes recency.
    acceptance = repo / 'tests/out/release-acceptance/run-0-9-1'
    accepted = artifact.inventory(acceptance)
    old_archive = artifact.inventory(old)
    before = artifact.inventory(repo)
    preview = release_rotate.rotate(new, root=repo)
    assert before == artifact.inventory(repo), 'preview changed files'
    assert {r['path'] for r in preview['runs']} == {
        'runs/release-0.9.0-default', 'release-acceptance/run-0-9-0', 'runs/zzz-old-development'}
    assert preview['newest'] == ['runs/aaa-newest-failed']
    lock_inode = (repo / 'tests/.checkout.lock').stat().st_ino
    result = release_rotate.rotate(new, root=repo, apply=True)
    assert result['state'] == 'complete' and result['runs'][0]['state'] == 'removed'
    assert not battery.exists() and current.is_dir() and latest.is_dir() and not loose.exists()
    assert artifact.inventory(old) == old_archive, 'rotation rewrote the historical archive'
    assert artifact.inventory(acceptance) == accepted
    assert not (repo / 'tests/out/release-acceptance/run-0-9-0').exists()
    assert (repo / '.tmp/scratch').read_bytes() == b'not release rotation'
    assert (repo / 'outside').read_bytes().startswith(b'do not follow')
    assert (repo / 'tests/.checkout.lock').stat().st_ino == lock_inode
    retained = retention.read_object(repo / 'tests/RETAINED.json')['runs']
    assert len(retained) == 2 and all(e.get('release') == 'v0.9.1' for e in retained)
    completed_output(battery)  # A replacement at the old path is not part of this transaction.
    assert release_rotate.rotate(new, root=repo, apply=True) == result
    assert battery.is_dir()


def protections(out):
    for name in ('legacy', 'pin', 'wrong_owner', 'overlap'):
        repo, _, battery, new, _ = fixture(out, name)
        if name == 'legacy':
            change_entry(repo, battery, lambda e: e.pop('release'))
        elif name == 'pin':
            change_entry(repo, battery, lambda e: e.update(release=None))
        elif name == 'wrong_owner':
            change_entry(repo, battery, lambda e: e.update(run_id='different'))
        else:
            value = retention.read_object(repo / 'tests/RETAINED.json')
            value['runs'].append(dict(path='runs', run_id='manual', reason='pin the subtree', source=None, app_inventory=None))
            with retention.checkout_lock(repo):
                retention.write_index(repo, value)
        before, index_before = artifact.inventory(battery), (repo / 'tests/RETAINED.json').read_bytes()
        result = release_rotate.rotate(new, root=repo)
        assert 'runs/release-0.9.0-default' not in {r['path'] for r in result['runs']}, name
        assert artifact.inventory(battery) == before and (repo / 'tests/RETAINED.json').read_bytes() == index_before
    repo, _, battery, new, _ = fixture(out, 'corrupt-new')
    original_index = (repo / 'tests/RETAINED.json').read_bytes()
    (new / release_runs.BUNDLE / 'runs.tar.gz').write_bytes(b'corrupt')
    reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'checksum mismatch')
    assert battery.is_dir() and (repo / 'tests/RETAINED.json').read_bytes() == original_index
    assert not (new / 'evidence/rotation.json').exists()
    repo, _, _, new, _ = fixture(out, 'newer-release')
    make_release(repo, '0.9.2')
    reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'newer release')
    repo, _, battery, new, _ = fixture(out, 'quarantine-link')
    outside = repo.parent / 'external'
    outside.mkdir()
    (outside / 'canary').write_bytes(b'untouched')
    (repo / 'tests/out/.release-rotation').symlink_to(outside)
    reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'symlink redirects')
    assert battery.is_dir() and list(outside.iterdir()) == [outside / 'canary']
    repo, _, battery, new, _ = fixture(out, 'run-link')
    moved = battery.rename(repo.parent / 'external-run')
    battery.symlink_to(moved)
    reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'symlink redirects')
    assert (moved / 'payload.bin').read_bytes() == b'original\x00\xff'


def checkpoint_policy(out):
    repo, old, battery, new, current = fixture(out, 'checkpoint-policy')
    # Explicitly migrated entries expire even when the older release predates
    # portable bundles. Cleanup does not back up every old development run.
    record = retention.read_object(old / 'release.json')
    record.pop('test_evidence')
    retention.atomic_json(old / 'release.json', record)
    shutil.rmtree(old / release_runs.BUNDLE)
    legacy = repo / 'tests/out/release-acceptance/run-0-9-0'
    (legacy / 'owner.json').unlink()
    (legacy / 'acceptance.lock').unlink()
    change_entry(repo, legacy, lambda e: e.update(run_id='nested-accept-0.9.0'))
    history = artifact.inventory(old)
    failed = local_run(repo, 'old-failed', 120, 121, ok=False)
    abandoned = local_run(repo, 'abandoned', 130)
    ambiguous = local_run(repo, 'ambiguous', 140, 141)
    (ambiguous / 'run.json').write_text('{unfinished')
    recent = local_run(repo, 'recent-unfinished', 220)
    pending = local_run(repo, 'pending-cleanup', 150, 151)
    session = pending / 'suites/runner_byoxpc/runner_install/artifacts/session.json'
    session.parent.mkdir(parents=True)
    retention.atomic_json(session, dict(removed=False, cleanup_error='service still present'))
    registry = local_run(repo, 'registry-cleanup', 160)
    (registry / 'suites/runner_byoxpc/registry_recovery/artifacts').mkdir(parents=True)
    finished_cleanup = local_run(repo, 'finished-cleanup', 170, 171)
    cleared = finished_cleanup / 'suites/runner_byoxpc/runner_install/artifacts/session.json'
    cleared.parent.mkdir(parents=True)
    retention.atomic_json(cleared, dict(removed=True))
    unmanaged = repo / 'tests/out/runs/unmanaged'
    unmanaged.mkdir()
    (unmanaged / 'notes').write_text('no ownership')
    stray = repo / 'tests/out/standalone.json'
    stray.write_text('{}')
    newest = local_run(repo, 'newest-failed', 300, 301, ok=False)
    tied = local_run(repo, 'same-recorded-completion', 290, 301)
    # A missing older indexed run should not remain a permanent index entry.
    value = retention.read_object(repo / 'tests/RETAINED.json')
    value['runs'].append(dict(value['runs'][1], path='runs/absent-old'))
    with retention.checkout_lock(repo):
        retention.write_index(repo, value)
    result = release_rotate.rotate(new, root=repo, apply=True)
    assert all(not p.exists() for p in (battery, legacy, failed, abandoned, ambiguous, finished_cleanup))
    assert all(p.is_dir() for p in (current, recent, pending, registry, unmanaged, newest, tied))
    assert stray.read_text() == '{}'
    assert result['newest'] == ['runs/newest-failed', 'runs/same-recorded-completion']
    assert len(retention.read_object(repo / 'tests/RETAINED.json')['runs']) == 2
    assert artifact.inventory(old) == history


def acceptance_lifetime(out):
    repo, _, _, new, _ = fixture(out, 'acceptance-lifetime')
    active = repo / 'tests/out/release-acceptance/active'
    command = [sys.executable, '-B', __file__, '--hold-acceptance', str(repo), str(active)]
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert child.stdout.readline() == b'ready\n'
        preview = release_rotate.rotate(new, root=repo)
        assert any(r['path'] == 'release-acceptance/active' and r['reason'] == 'active acceptance'
                   for r in preview['kept'])
        assert active.exists()
    finally:
        child.kill()
        child.communicate(timeout=10)
    assert release_cleanup.describe(active)['disposition'] == 'interrupted'
    release_rotate.rotate(new, root=repo, apply=True)
    assert not active.exists(), 'abandoned owned acceptance survived the release checkpoint'
    # Normal lifetime completion is recorded even when acceptance raises.
    finished = repo / 'tests/out/release-acceptance/finished-failure'
    try:
        with retention.acceptance_output(repo, finished):
            raise ValueError('controlled acceptance failure')
    except ValueError:
        pass
    assert release_cleanup.describe(finished)['disposition'] == 'completed'
    assert not release_cleanup.acceptance_busy(finished)


def crash(repo, mode):
    archive = repo / 'dist/archive/v0.9.1'
    rename, write, remove = Path.rename, retention.write_index, shutil.rmtree
    def interrupted_rename(path, target):
        result = rename(path, target)
        if path.name == 'release-0.9.0-default':
            os._exit(91)
        return result
    def interrupted_index(root, value):
        write(root, value)
        os._exit(92)
    def interrupted_delete(path, *args, **kwargs):
        if Path(path).name != 'release-0.9.0-default':
            return remove(path, *args, **kwargs)
        if mode == 'partial':
            (Path(path) / 'payload.bin').unlink()
            os._exit(93)
        remove(path, *args, **kwargs)
        os._exit(94)
    target, attribute, replacement = {
        'rename': (Path, 'rename', interrupted_rename),
        'index': (retention, 'write_index', interrupted_index),
        'partial': (shutil, 'rmtree', interrupted_delete),
        'deleted': (shutil, 'rmtree', interrupted_delete),
    }[mode]
    with patch.object(target, attribute, replacement):
        release_rotate.rotate(archive, root=repo, apply=True)
    raise AssertionError('crash boundary was not reached')


def interrupted(out):
    for mode, code in (('rename', 91), ('index', 92), ('partial', 93), ('deleted', 94)):
        repo, _, battery, new, current = fixture(out, 'crash-' + mode)
        process = subprocess.run([sys.executable, '-B', __file__, '--crash', str(repo), mode],
                                 capture_output=True, timeout=30)
        assert process.returncode == code, (mode, process.stderr)
        (repo.parent / 'crash.json').write_text(json.dumps(dict(mode=mode, returncode=process.returncode)))
        receipt = retention.read_object(new / 'evidence/rotation.json')
        row = next(r for r in receipt['runs'] if r['path'] == 'runs/release-0.9.0-default')
        quarantine = repo / 'tests/out' / row['quarantine']
        if mode == 'rename':
            original_index = (repo / 'tests/RETAINED.json').read_bytes()
            (quarantine / 'payload.bin').write_bytes(b'changed after interruption')
            reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'quarantined evidence differs')
            assert (repo / 'tests/RETAINED.json').read_bytes() == original_index
            assert (quarantine / 'payload.bin').read_bytes() == b'changed after interruption'
            (quarantine / 'payload.bin').write_bytes(b'original\x00\xff')
        if mode in ('partial', 'deleted'):
            completed_output(battery)
            replacement = artifact.inventory(battery)
        result = release_rotate.rotate(new, root=repo, apply=True)
        assert result['state'] == 'complete' and not quarantine.exists() and current.is_dir()
        if mode in ('partial', 'deleted'):
            assert artifact.inventory(battery) == replacement, 'resume deleted a replacement run'
        else:
            assert not battery.exists()
    repo, _, battery, new, _ = fixture(out, 'stale-pin')
    with patch.object(release_rotate, 'apply_journal', side_effect=OSError('pause before mutation')):
        reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'pause before mutation')
    change_entry(repo, battery, lambda e: e.update(release=None))
    reject(lambda: release_rotate.rotate(new, root=repo, apply=True), 'retention changed')
    assert battery.is_dir()

    # A later release cannot orphan an earlier transaction's quarantine by
    # treating the old indexed original as merely absent.
    repo, _, _, new, _ = fixture(out, 'successive-checkpoints')
    process = subprocess.run([sys.executable, '-B', __file__, '--crash', str(repo), 'rename'],
                             capture_output=True, timeout=30)
    assert process.returncode == 91, process.stderr
    newer, current = make_release(repo, '0.9.2')
    reject(lambda: release_rotate.rotate(newer, root=repo, apply=True), 'unfinished release cleanup')
    assert not (newer / 'evidence/rotation.json').exists()
    release_rotate.rotate(new, root=repo, apply=True)
    release_rotate.rotate(newer, root=repo, apply=True)
    assert current.is_dir()
    assert all(e['release'] == 'v0.9.2' for e in retention.read_object(repo / 'tests/RETAINED.json')['runs'])


def atomic_and_locking(out):
    repo, _, battery, new, _ = fixture(out, 'locking')
    index_path = repo / 'tests/RETAINED.json'
    original = index_path.read_bytes()
    replace = os.replace
    def fail_index(src, dst):
        if Path(dst) == index_path:
            raise OSError('atomic replacement failed')
        return replace(src, dst)
    with retention.checkout_lock(repo), patch.object(os, 'replace', fail_index):
        reject(lambda: retention.write_index(repo, dict(schema_version=1, runs=[])), 'atomic replacement failed')
    assert index_path.read_bytes() == original
    with retention.checkout_lock(repo):
        command = [sys.executable, '-B', '-c',
            'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
            'import release_rotate; release_rotate.rotate(Path(sys.argv[2]),root=Path(sys.argv[3]),apply=True)',
            str(ROOT / 'tests/lib'), str(new), str(repo)]
        before = artifact.inventory(repo)
        result = subprocess.run(command, capture_output=True, timeout=30)
        assert result.returncode != 0 and b'checkout busy' in result.stderr
        assert artifact.inventory(repo) == before
    assert battery.is_dir() and index_path.read_bytes() == original
    # Copy/verification failures cannot create a final archive or retire anything.
    git(repo, 'tag', '-a', 'v0.9.2', '-m', 'fixture')
    dist, attempt = make_dist(repo, version='0.9.2')
    fresh = make_battery(repo, dist, version='0.9.2')
    with patch.object(release_runs, 'pack', side_effect=OSError('copy failed')):
        reject(lambda: release_archive.archive(attempt, dist=dist, root=repo, battery=fresh), 'copy failed')
    assert attempt.is_dir() and fresh.is_dir() and not (dist / 'archive/v0.9.2').exists()
    assert index_path.read_bytes() == original


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    portable(out)
    ordinary(out)
    protections(out)
    checkpoint_policy(out)
    acceptance_lifetime(out)
    interrupted(out)
    atomic_and_locking(out)
    print('release cleanup controls passed: latest release and newest local output, '
          'acceptance lifetime, abandoned output, resource cleanup, pins, atomic retention '
          'and four abrupt-exit recovery boundaries')


if __name__ == '__main__':
    if sys.argv[1] == '--crash':
        crash(Path(sys.argv[2]), sys.argv[3])
    elif sys.argv[1] == '--hold-acceptance':
        with patch.object(retention.time, 'time_ns', return_value=1_000_000):
            with retention.acceptance_output(Path(sys.argv[2]), Path(sys.argv[3])):
                print('ready', flush=True)
                sys.stdin.read()
    else:
        main(Path(sys.argv[1]))
