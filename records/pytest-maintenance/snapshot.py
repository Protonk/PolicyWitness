"""Read-only comparison inputs; writes only this package's preservation.json.

Run with the pinned interpreter and -B -I. --verify compares with the saved
snapshot without writing. This is investigation equipment, not a run pruner,
resource recovery command, candidate interpreter or new architecture experiment.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = Path('/Users/raccoon/Desktop/Security/PolicyWitness')
DEMO = Path('/private/tmp/pw-pytest-boundary-20261030')
ACCEPTED = '77eb987554eef10ffa3371ffb21b235097562a78'
FROZEN = '9e46c7b94207c6baa28a1c62f4aa78defc6efb25'


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root,
                                   env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def entry(path):
    if not os.path.lexists(path):
        return {'exists': False}
    s = path.lstat()
    result = dict(exists=True, mode=s.st_mode, device=s.st_dev, inode=s.st_ino,
                  uid=s.st_uid, gid=s.st_gid, size=s.st_size, mtime_ns=s.st_mtime_ns)
    if stat.S_ISREG(s.st_mode):
        result['sha256'] = digest(path.read_bytes())
    elif stat.S_ISLNK(s.st_mode):
        result['target'] = os.readlink(path)
    elif stat.S_ISDIR(s.st_mode):
        result['children'] = sorted(p.name for p in path.iterdir())
    return result


def tree_digest(root):
    # Relative names, types/modes, bytes/targets; omit mutable filesystem times.
    # Do not traverse symlink directories or interpret candidate result fields.
    rows = []
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(base) / name
            s = path.lstat()
            row = [str(path.relative_to(root)), s.st_mode]
            if stat.S_ISREG(s.st_mode):
                row += [s.st_size, digest(path.read_bytes())]
            elif stat.S_ISLNK(s.st_mode):
                row += [os.readlink(path)]
            rows.append(row)
    return dict(entries=len(rows), sha256=digest(json.dumps(sorted(rows), separators=(',', ':')).encode()))


def snapshot():
    assert git(MAIN, 'rev-parse', 'HEAD').decode().strip() == ACCEPTED
    assert git(DEMO, 'rev-parse', 'HEAD').decode().strip() == FROZEN
    assert not git(DEMO, 'status', '--porcelain')
    assert not git(MAIN, 'diff', '--name-only', ACCEPTED)
    assert not git(ROOT, 'diff', '--name-only', FROZEN, '--', 'tests', 'controller', 'runner', 'docs')
    old_inventory = read(DEMO / 'records/pytest-boundary/inventory.json')
    pins = read(DEMO / 'tests/RETAINED.json')['runs']
    assert (ROOT / 'tests/RETAINED.json').read_bytes() == (DEMO / 'tests/RETAINED.json').read_bytes()
    assert (MAIN / 'tests/RETAINED.json').read_bytes() == git(MAIN, 'show', ACCEPTED + ':tests/RETAINED.json')
    frozen_paths = git(DEMO, 'ls-tree', '-r', '--name-only', FROZEN, '--',
                       'records/pytest-boundary', 'records/PYTEST-BOUNDARY-PLAN.md',
                       'tests/RETAINED.json').decode().splitlines()
    frozen_files = {}
    for name in frozen_paths:
        expected = git(DEMO, 'show', FROZEN + ':' + name)
        assert (DEMO / name).read_bytes() == expected == (ROOT / name).read_bytes(), name
        frozen_files[name] = digest(expected)
    runs = []
    for old in old_inventory['retained_runs']:
        path = Path(old['path'])
        run = read(path / 'run.json')
        pin = [p for p in pins if p['path'] == str(path.relative_to(DEMO / 'tests/out'))]
        assert len(pin) == 1 and pin[0]['run_id'] == old['run_id'] == run['run_id']
        assert digest((path / 'run.json').read_bytes()) == old['run_sha256']
        runs.append(dict(path=str(path), run_id=run['run_id'], pin=pin[0],
                         run_sha256=old['run_sha256'], tree=tree_digest(path)))
    app = MAIN / 'dist/PolicyWitness.app'
    inventory_path = MAIN / 'tests/out/runs/f2-reservation-final-01/artifact-integrity/before.json'
    inventory = read(inventory_path)
    assert {'.'} | {str(p.relative_to(app)) for p in app.rglob('*')} == set(inventory)
    for name, expected in inventory.items():
        p = app / name
        assert p.lstat().st_mode == expected['mode'], name
        if 'sha256' in expected:
            assert digest(p.read_bytes()) == expected['sha256'], name
    c0 = git(ROOT, 'show', '0c22d256:records/workset/pytest-first.md')
    # C0.2 is a historical object, not a promise that its old path still exists.
    assert digest(c0) == old_inventory['c0_2_sha256']

    base = DEMO / 'tests/out/runs/pytest-boundary-demo-01'
    candidate = base / 'candidates/setup_failure'
    lease = candidate / 'resources/0'
    observation = base / 'observations/setup_failure'
    raw_paths = [base / 'owner.json', base / 'source.json', candidate / 'owner.json',
                 candidate / 'engine.json', lease / 'record.json', lease / 'observations.jsonl',
                 observation / 'observation.json', observation / 'witness/resource.jsonl']
    raw = {str(p): dict(sha256=digest(p.read_bytes()), text=p.read_text()) for p in raw_paths}
    record = read(lease / 'record.json')
    facts = {str(p): entry(p) for p in [Path(record['resource']), Path(record['socket_dir']),
             Path(record['socket_dir']) / 'recover', candidate / 'supervisor.json',
             lease / 'recovery.json', DEMO / 'tests/.checkout.lock']}
    lock = read(DEMO / 'tests/.checkout.lock')
    resource = dict(raw=raw, current_filesystem=facts, current_lock_owner=lock,
                    current_lock_nonce_matches_lease=lock['nonce'] == record['nonce'],
                    disposition='preserved; cleanup not established',
                    missing=['durable post-safety-cleanup exit/reap observation for historical child 71948',
                             'live authenticated recovery peer with matching PID, nonce and held descriptor',
                             'if live peer is absent, an independently justified alternative cleanup basis'],
                    no_process_probe_or_signal=True, no_lock_acquisition=True)
    owners = ['tests/lib/test_cli.py', 'tests/lib/suite_run.py', 'tests/lib/testlib.sh',
              'tests/lib/case.sh', 'tests/lib/checkout_lock.py', 'tests/lib/retention.py',
              'tests/lib/release_cleanup.py', 'tests/lib/run_capture.py', 'tests/lib/artifact.py',
              'tests/fixtures/byoxpc/session.py', 'tests/fixtures/exec/control.py',
              'tests/catalog.json', 'tests/run.sh', 'tests/lib/python.sh', 'tests/lib/python_start.sh',
              'tests/suites/runner_c_worker_harness/check_exec_evidence.py',
              'tests/suites/runner_c_worker_harness/run.sh', 'tests/suites/source_drift/contract.py',
              'tests/fixtures/worker_lifecycle/exec_control.c',
              'tests/fixtures/worker_lifecycle/exec_call_policy.json']
    source_owners = {}
    for name in owners:
        data = git(ROOT, 'show', ACCEPTED + ':' + name)
        assert data == (ROOT / name).read_bytes() == (MAIN / name).read_bytes()
        source_owners[name] = dict(sha256=digest(data), physical_lines=len(data.splitlines()))
    return dict(accepted_source=ACCEPTED, frozen_demonstration=FROZEN,
                accepted_status=git(MAIN, 'status', '--porcelain').decode(),
                demonstration_status=git(DEMO, 'status', '--porcelain').decode(),
                c0_2_sha256=digest(c0), accepted_app_inventory_sha256=digest(inventory_path.read_bytes()),
                accepted_app_paths_modes_hashes_match=True, frozen_files=frozen_files,
                source_owners=source_owners, retention_entries=len(pins), retained_runs=runs,
                unresolved_resource=resource,
                protected_paths={str(p): entry(p) for p in map(Path, [
                    '/private/tmp/pw-extension-directory-uge3532e', '/private/tmp/pw-f2-stage1',
                    '/private/tmp/pw-f2-controlled-prep',
                    '/Users/raccoon/Desktop/Security/PolicyWitness-pytest-trial-evidence'])},
                limitations=['Filesystem and hash checks establish identity, not new lifecycle evidence.',
                             'No signature check, process recovery, native execution or pytest execution performed.',
                             'Raw retained runs remain gitignored in the frozen demonstration worktree.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = snapshot()
    target = HERE / 'preservation.json'
    if args.verify:
        expected = read(target)
        expected.pop('observed_at_utc')
        assert result == expected, 'preservation snapshot changed; inspect before proceeding'
    else:
        result['observed_at_utc'] = datetime.now(timezone.utc).isoformat()
        target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(verified=args.verify, retained_runs=len(result['retained_runs']),
                          retention_entries=result['retention_entries'],
                          unresolved_resource=result['unresolved_resource']['disposition'])))
