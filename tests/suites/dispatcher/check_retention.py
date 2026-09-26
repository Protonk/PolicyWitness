"""Filesystem observations and independent receipts prove retention and ownership."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Controls:
    def __init__(self, out):
        self.out, self.count = out, 0
        self.completed = []

    def fixture(self, name):
        repo = self.out / name / 'repo'
        install_runner(ROOT, repo, {'probe': {'command': ['bash', 'tests/suites/probe/run.sh'], 'cases': ['witness']}})
        script = repo / 'tests/suites/probe/run.sh'
        script.parent.mkdir(parents=True)
        script.write_text('#!/bin/bash\nexec /usr/bin/python3 -B tests/fixtures/dispatcher/retention_case.py\n')
        script.chmod(0o755)
        fixture = repo / 'tests/fixtures/dispatcher/retention_case.py'
        fixture.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / fixture.relative_to(repo), fixture)
        keep = repo / 'tests/out/kept'
        (keep / 'empty').mkdir(parents=True)
        (keep / 'bytes').write_bytes(b'retained\x00\xff')
        (keep / 'link').symlink_to('bytes')
        self.index(repo, 'kept')
        shutil.copyfile(ROOT / 'Makefile', repo / 'Makefile')
        (repo / 'tests/run.sh').chmod(0o755)
        return repo

    def index(self, repo, path):
        (repo / 'tests/RETAINED.json').write_text(json.dumps(dict(schema_version=1, runs=[dict(
            path=path, run_id='accepted', reason='fixture acceptance', source=None, app_inventory=None)])))

    def env(self, repo, output='tests/out/runs/default', **values):
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
        env.update(PW_TEST_OUT_DIR=output, PW_TEST_RUN_ID='fixture', PYTHONDONTWRITEBYTECODE='1',
                   RETENTION_RECEIPT=str(repo.parent / 'receipts.jsonl'), **values)
        return env

    def call(self, repo, args=(), *, output='tests/out/runs/default', code=0, readonly=False, make=False, **values):
        before = artifact.inventory(repo) if readonly else None
        argv = ['make', 'clean'] if make else ['bash', repo / 'tests/run.sh', *args]
        result = subprocess.run(argv, cwd=repo,
                                env=self.env(repo, output, **values), capture_output=True, timeout=30)
        self.count += 1
        evidence = repo.parent / f'command-{self.count}'
        evidence.mkdir()
        (evidence / 'stdout').write_bytes(result.stdout)
        (evidence / 'stderr').write_bytes(result.stderr)
        (evidence / 'exit.json').write_text(json.dumps(dict(args=list(args), output=output, returncode=result.returncode)))
        require(result.returncode == code, f'{repo.parent.name} {args}: expected {code}, got {result.returncode}: {result.stderr!r}')
        if readonly:
            require(before == artifact.inventory(repo), f'{args}: read-only command changed checkout')
        return result

    def locking(self):
        for crash in (False, True):
            repo = self.fixture('lock-crash' if crash else 'lock-release')
            receipt = repo.parent / 'receipts.jsonl'
            release = repo.parent / 'release'
            with (repo.parent / 'held.stdout').open('wb') as stdout, (repo.parent / 'held.stderr').open('wb') as stderr:
                process = subprocess.Popen(['bash', repo / 'tests/run.sh'], cwd=repo,
                    env=self.env(repo, RETENTION_HOLD=str(release)), stdout=stdout, stderr=stderr)
                child_pid = None
                try:
                    deadline = time.monotonic() + 10
                    while not receipt.exists():
                        require(process.poll() is None and time.monotonic() < deadline, 'held fixture did not reach execution')
                        time.sleep(0.02)
                    child_pid = json.loads(receipt.read_text().splitlines()[0])['pid']
                    lock = repo / 'tests/.checkout.lock'
                    inode = lock.stat().st_ino
                    self.call(repo, ['--help'], readonly=True)
                    self.call(repo, ['--list'], readonly=True)
                    self.call(repo, ['--bad-option'], code=2, readonly=True)
                    preview = json.loads(self.call(repo, ['--prune'], readonly=True).stdout)
                    require(preview['checkout_busy'] is True, 'preview did not report held lock')
                    require(any(r['path'] == 'runs/default' and r['disposition'] == 'keep: active or interrupted'
                                for r in preview['runs']), 'preview mislabeled active output')
                    self.call(repo, ['--prune', '--apply'], code=2, readonly=True)
                    self.call(repo, ['--prune', '--apply', '--unfinished', 'default'], code=2, readonly=True)
                    result = self.call(repo, output='tests/out/runs/competing', code=2, readonly=True)
                    require(b'checkout busy' in result.stderr, 'different output bypassed checkout lock')
                    other = self.fixture('independent-' + str(crash))
                    self.call(other)
                    if crash:
                        process.kill()
                        require(process.wait(timeout=5) != 0, 'crashed owner succeeded')
                        os.killpg(child_pid, signal.SIGTERM)
                        child_pid = None
                        require(not (repo / 'tests/out/runs/default/run.json').exists(), 'crash invented completion')
                        self.call(repo, code=2, readonly=True)
                        self.call(repo, output='tests/out/runs/after-crash')
                    else:
                        release.touch()
                        require(process.wait(timeout=10) == 0, 'held execution failed')
                        child_pid = None
                        self.call(repo)
                    require(lock.stat().st_ino == inode, 'lock file was unlinked or replaced')
                finally:
                    release.touch()
                    if child_pid is not None:
                        try: os.killpg(child_pid, signal.SIGTERM)
                        except ProcessLookupError: pass
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)
            self.completed.append('OS-held checkout lock; owner ' + ('crash' if crash else 'completion'))

    def pruning(self):
        fresh = self.fixture('prune-without-lock')
        self.call(fresh, ['--prune'], readonly=True)
        require(not (fresh / 'tests/.checkout.lock').exists(), 'preview created a lock file')
        repo = self.fixture('pruning')
        base = repo / 'tests/out'
        for name in ('passed', 'failed', 'retained', 'interrupted', 'ambiguous', 'newly-retained', 'now-interrupted'):
            self.call(repo, output='tests/out/runs/' + name, code=1 if name == 'failed' else 0,
                      RETENTION_STATUS='fail' if name == 'failed' else 'pass')
        (base / 'runs/interrupted/run.json').unlink()
        (base / 'runs/ambiguous/run.json').write_text('{')
        (base / 'runs/unmanaged').mkdir()
        (base / 'runs/unmanaged/bytes').write_bytes(b'not owned')
        (base / 'runs/bad-owner').mkdir()
        (base / 'runs/bad-owner/owner.json').write_text('{}')
        (base / 'runs/redirect').symlink_to(repo.parent)
        for path in (base / 'runs/file', base / 'acceptance.inventory.json'):
            path.write_bytes(b'never delete a file outside a candidate directory')
        self.call(repo, output='tests/out/release-acceptance/run-fixture/tests')
        self.index(repo, 'runs/retained')
        retained = artifact.inventory(base / 'runs/retained')
        outside = artifact.inventory(base / 'release-acceptance')
        preview = json.loads(self.call(repo, ['--prune'], readonly=True).stdout)
        rows = {r['path']: r['disposition'] for r in preview['runs']}
        expected = {'passed':'delete', 'failed':'delete', 'retained':'keep: retained',
                    'interrupted':'keep: interrupted', 'ambiguous':'keep: ambiguous',
                    'unmanaged':'keep: unmanaged', 'bad-owner':'keep: ambiguous', 'redirect':'keep: unmanaged'}
        require(all(rows['runs/' + name] == value for name, value in expected.items()), 'wrong prune dispositions')
        require(rows['release-acceptance'] == 'keep: unmanaged', 'release acceptance is disposable')
        # Eligibility changes between preview and apply must be honored.
        index = json.loads((repo / 'tests/RETAINED.json').read_text())
        index['runs'].append(dict(path='runs/newly-retained', run_id='fixture', reason='new retention', source=None, app_inventory=None))
        (repo / 'tests/RETAINED.json').write_text(json.dumps(index))
        (base / 'runs/now-interrupted/run.json').unlink()
        applied = json.loads(self.call(repo, ['--prune', '--apply']).stdout)
        require(set(applied['removed']) == {'runs/passed', 'runs/failed'} and not applied['failures'], 'apply used stale eligibility')
        require(retained == artifact.inventory(base / 'runs/retained'), 'prune changed retained inventory')
        require(outside == artifact.inventory(base / 'release-acceptance'), 'prune changed release acceptance')
        require((base / 'runs/file').is_file() and (base / 'acceptance.inventory.json').is_file(), 'prune deleted a standalone file')
        for name in ('interrupted', 'ambiguous'):
            removed = json.loads(self.call(repo, ['--prune', '--apply', '--unfinished', name]).stdout)
            require(removed['removed'] == ['runs/' + name] and not (base / 'runs' / name).exists(), 'explicit unfinished cleanup failed')
        self.call(repo, output='tests/out/runs/completed')
        for name in ('completed', 'retained', 'newly-retained', 'unmanaged', 'bad-owner', 'redirect', '../kept', '.', 'absent'):
            self.call(repo, ['--prune', '--apply', '--unfinished', name], code=2, readonly=True)
        for args in (['--apply'], ['--unfinished', 'x'], ['--prune', '--unfinished', 'x'],
                     ['--prune', '--suite', 'probe'], ['--prune', '--case', 'probe/witness'],
                     ['--prune', '--all'], ['--prune', '--list']):
            self.call(repo, args, code=2, readonly=True)
        # A candidate containing retained evidence is protected too.
        self.call(repo, output='tests/out/runs/parent')
        (base / 'runs/parent/child').mkdir()
        index['runs'].append(dict(path='runs/parent/child', run_id='child', reason='nested evidence', source=None, app_inventory=None))
        (repo / 'tests/RETAINED.json').write_text(json.dumps(index))
        report = json.loads(self.call(repo, ['--prune', '--apply']).stdout)
        require('runs/parent' not in report['removed'] and (base / 'runs/parent/child').is_dir(), 'retained descendant erased')
        self.call(repo, output='tests/out/runs/undeletable')
        candidate = base / 'runs/undeletable'
        candidate.chmod(0o500)
        before = artifact.inventory(candidate)
        try:
            result = json.loads(self.call(repo, ['--prune', '--apply'], code=1).stdout)
            require(any(r['path'] == 'runs/undeletable' and r['error'] for r in result['failures']), 'deletion failure not reported')
            require(before == artifact.inventory(candidate), 'failed unlink silently changed evidence')
        finally:
            candidate.chmod(0o700)
        cleaned = json.loads(self.call(repo, make=True).stdout)
        require('runs/undeletable' in cleaned['removed'] and not candidate.exists(), 'make clean did not delegate to prune')
        require(retained == artifact.inventory(base / 'runs/retained') and outside == artifact.inventory(base / 'release-acceptance'),
                'make clean changed retained/release inventories')
        self.index(repo, 'runs')
        all_runs = artifact.inventory(base / 'runs')
        result = json.loads(self.call(repo, ['--prune', '--apply']).stdout)
        require(not result['removed'] and all_runs == artifact.inventory(base / 'runs'), 'retained ancestor did not protect runs')
        self.completed.append('prune dispositions, changed eligibility, unfinished, deletion failure and make clean')

    def run(self):
        repo = self.fixture('retained-and-completed')
        kept = artifact.inventory(repo / 'tests/out/kept')
        self.call(repo)
        run = repo / 'tests/out/runs/default'
        receipts = lambda: [json.loads(x) for x in (repo.parent / 'receipts.jsonl').read_text().splitlines()]
        require(receipts()[0]['owner']['run_id'] == 'fixture', 'owner must precede execution')
        (run / 'obsolete').write_text('replace only completed owned output')
        self.call(repo, code=1, RETENTION_STATUS='fail')
        require(not (run / 'obsolete').exists(), 'completed output not replaced')
        require(json.loads((run / 'run.json').read_text())['ok'] is False, 'failure did not execute')
        self.call(repo)
        require(len(receipts()) == 3, 'failed completed run was not replaceable')
        require(kept == artifact.inventory(repo / 'tests/out/kept'), 'retained sibling changed')
        self.completed.append('completed pass and failure replacement; retained sibling unchanged')
        for target in ('tests/out/kept', 'tests/out', 'tests/out/kept/nested'):
            self.call(repo, output=target, code=2, readonly=True)
        self.index(repo, 'absent-retained')
        self.call(repo, output='tests/out/absent-retained', code=2, readonly=True)
        self.call(repo, output='tests/out/absent-retained/child', code=2, readonly=True)
        self.completed.append('retained overlap and absent local retention')

        for mode in ('missing', 'malformed', 'unreadable', 'escape', 'absolute', 'symlink', 'inventory_escape', 'boolean_schema', 'duplicate_keys', 'file_path'):
            repo = self.fixture('index-' + mode)
            index = repo / 'tests/RETAINED.json'
            if mode == 'missing': index.unlink()
            elif mode == 'malformed': index.write_text('{')
            elif mode == 'unreadable': index.chmod(0)
            elif mode == 'escape': self.index(repo, '../elsewhere')
            elif mode == 'absolute': self.index(repo, '/private/tmp')
            elif mode == 'symlink':
                (repo / 'tests/out/redirect').symlink_to(repo.parent)
                self.index(repo, 'redirect/kept')
            elif mode == 'boolean_schema':
                index.write_text('{"schema_version":true,"runs":[]}')
            elif mode == 'duplicate_keys':
                index.write_text('{"schema_version":1,"runs":[],"runs":[]}')
            elif mode == 'file_path': self.index(repo, 'kept/bytes')
            else:
                data = json.loads(index.read_text())
                data['runs'][0]['app_inventory'] = '../escape'
                index.write_text(json.dumps(data))
            # An unreadable index cannot be hashed by the observer either.
            before = artifact.inventory(repo / 'tests/out/kept')
            self.call(repo, code=2, readonly=mode != 'unreadable')
            self.call(repo, ['--prune'], code=2, readonly=mode != 'unreadable')
            self.call(repo, ['--prune', '--apply'], code=2, readonly=mode != 'unreadable')
            self.call(repo, ['--help'], readonly=mode != 'unreadable')
            self.call(repo, ['--list'], readonly=mode != 'unreadable')
            self.call(repo, ['--bad-option'], code=2, readonly=mode != 'unreadable')
            require(artifact.inventory(repo / 'tests/out/kept') == before, 'index failure changed retained inventory')
            require(not (repo.parent / 'receipts.jsonl').exists(), 'invalid index executed work')
            if mode == 'unreadable': index.chmod(0o644)
            self.completed.append('index-' + mode)

        for mode in ('interrupted', 'mismatched', 'malformed', 'owner', 'unmanaged'):
            repo = self.fixture('output-' + mode)
            self.call(repo)
            run = repo / 'tests/out/runs/default'
            if mode == 'interrupted': (run / 'run.json').unlink()
            elif mode == 'mismatched':
                data = json.loads((run / 'run.json').read_text()); data['run_id'] = 'wrong'
                (run / 'run.json').write_text(json.dumps(data))
            elif mode == 'malformed': (run / 'run.json').write_text('{')
            elif mode == 'owner': (run / 'owner.json').write_text('{}')
            else: (run / 'owner.json').unlink()
            self.call(repo, code=2, readonly=True)
            self.call(repo, output='tests/out/runs/fresh')
            self.completed.append('replacement refuses ' + mode)
        repo = self.fixture('output-escapes')
        (repo / 'tests/out/link').symlink_to(repo.parent)
        (repo / 'tests/out/alias').symlink_to('kept')
        for target in ('tests/out/link/run', 'tests/out/alias', 'tests/out/runs/../fresh'):
            self.call(repo, output=target, code=2, readonly=True)
        self.completed.append('symlink redirects and lexical path escapes')
        self.locking()
        self.pruning()
        (self.out / 'controls.json').write_text(json.dumps(self.completed, indent=2) + '\n')
        print(f'{len(self.completed)} retention controls passed ({self.count} invocations)')


if __name__ == '__main__':
    Controls(Path(sys.argv[1]).resolve()).run()
