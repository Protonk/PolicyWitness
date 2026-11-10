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
        script.write_text('#!/bin/bash\nexec "${PW_PYTHON}" -B -S tests/fixtures/dispatcher/retention_case.py\n')
        script.chmod(0o755)
        fixture = repo / 'tests/fixtures/dispatcher/retention_case.py'
        fixture.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / fixture.relative_to(repo), fixture)
        keep = repo / 'tests/out/kept'
        (keep / 'empty').mkdir(parents=True)
        (keep / 'bytes').write_bytes(b'retained\x00\xff')
        (keep / 'link').symlink_to('bytes')
        shutil.copyfile(ROOT / 'Makefile', repo / 'Makefile')
        (repo / 'tests/run.sh').chmod(0o755)
        return repo

    def index(self, repo, path):
        (repo / 'tests/RETAINED.json').write_text(json.dumps(dict(schema_version=1, runs=[dict(
            path=path, run_id='accepted', reason='fixture acceptance', source=None, app_inventory=None)])))

    def env(self, repo, output='tests/out/runs/default', **values):
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_') and k not in ('APPLY', 'MAKEFLAGS', 'MFLAGS')}
        env.update(PW_TEST_OUT_DIR=output, PW_TEST_RUN_ID='fixture', PYTHONDONTWRITEBYTECODE='1',
                   RETENTION_RECEIPT=str(repo.parent / 'receipts.jsonl'), **values)
        return env

    def call(self, repo, args=(), *, output='tests/out/runs/default', code=0, readonly=False, make=False, **values):
        before = artifact.inventory(repo) if readonly else None
        argv = ['make', *args] if make else ['bash', repo / 'tests/run.sh', *args]
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
                    first = self.first_receipt(process, receipt)
                    child_pid = first['pid']
                    lock = repo / 'tests/.checkout.lock'
                    inode = lock.stat().st_ino
                    self.call(repo, ['--help'], readonly=True)
                    self.call(repo, ['--list'], readonly=True)
                    self.call(repo, ['--bad-option'], code=2, readonly=True)
                    preview = json.loads(self.call(repo, ['--prune'], readonly=True).stdout)
                    require(preview['checkout_busy'] is True, 'preview did not report held lock')
                    require(any(r['path'] == 'runs/default' and r['disposition'] == 'keep: blocked' and 'active' in r['reason']
                                for r in preview['runs']), 'preview mislabeled active output')
                    self.call(repo, ['--prune', '--apply'], code=2, readonly=True)
                    result = self.call(repo, output='tests/out/runs/competing', code=2, readonly=True)
                    require(b'checkout busy' in result.stderr, 'different output bypassed checkout lock')
                    other = self.fixture('independent-' + str(crash))
                    self.call(other)
                    if crash:
                        process.kill()
                        require(process.wait(timeout=5) != 0, 'crashed owner succeeded')
                        # The case still holds the descriptor the dispatcher passed: the lock outlives the dispatcher.
                        busy = self.call(repo, output='tests/out/runs/while-orphaned', code=2, readonly=True)
                        require(b'checkout busy' in busy.stderr, 'a killed dispatcher released the lock its case holds')
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
        observed = self.orphaned_grandchild('pass')
        self.check_orphan(observed)
        dropped = self.orphaned_grandchild('drop')
        try:
            self.check_orphan(dropped)
        except AssertionError:
            pass
        else:
            raise AssertionError('a case wrapper that drops the descriptor passed the lifetime control')
        require(dropped['held_after_kill'] is False, f'the dropping wrapper still held the lock: {dropped}')
        self.completed.append('the lock outlives a killed dispatcher and case wrapper while a protected grandchild runs; '
                              'a wrapper that drops the descriptor fails that control')

    def first_receipt(self, process, receipt):
        deadline = time.monotonic() + 10
        # The receipt exists before its first line is complete; wait for the line, not the file.
        while True:
            require(process.poll() is None and time.monotonic() < deadline, 'held fixture did not reach execution')
            lines = receipt.read_text().splitlines() if receipt.exists() else []
            try:
                if lines:
                    return json.loads(lines[0])
            except ValueError:
                pass
            time.sleep(0.02)

    def orphaned_grandchild(self, mode):
        """Kill the dispatcher, then the case process, while the case's grandchild runs; what an outside observer sees."""
        repo = self.fixture(f'lock-orphan-{mode}')
        receipt, release, grandchild_release = repo.parent / 'receipts.jsonl', repo.parent / 'release', repo.parent / 'grandchild.release'
        observed = dict(mode=mode)
        with (repo.parent / 'held.stdout').open('wb') as stdout, (repo.parent / 'held.stderr').open('wb') as stderr:
            process = subprocess.Popen(['bash', repo / 'tests/run.sh'], cwd=repo, stdout=stdout, stderr=stderr,
                                       env=self.env(repo, RETENTION_HOLD=str(release), RETENTION_GRANDCHILD=mode,
                                                    RETENTION_GRANDCHILD_RELEASE=str(grandchild_release)))
            first = None
            try:
                first = self.first_receipt(process, receipt)
                process.kill()
                process.wait(timeout=5)
                os.killpg(first['pid'], signal.SIGKILL)
                deadline = time.monotonic() + 10
                while self.alive(first['pid']):
                    require(time.monotonic() < deadline, 'the case process survived SIGKILL')
                    time.sleep(0.02)
                observed['grandchild_alive_after_kills'] = self.alive(first['grandchild'])
                competing = subprocess.run(['bash', repo / 'tests/run.sh'], cwd=repo, capture_output=True, timeout=30,
                                           env=self.env(repo, 'tests/out/runs/while-orphaned'))
                observed['held_after_kill'] = competing.returncode == 2 and b'checkout busy' in competing.stderr
                (repo.parent / 'competing.stderr').write_bytes(competing.stderr)
                grandchild_release.touch()
                deadline = time.monotonic() + 10
                while self.alive(first['grandchild']):
                    require(time.monotonic() < deadline, 'the grandchild did not exit after release')
                    time.sleep(0.02)
                after = subprocess.run(['bash', repo / 'tests/run.sh'], cwd=repo, capture_output=True, timeout=30,
                                       env=self.env(repo, 'tests/out/runs/after-orphan'))
                observed['after_returncode'] = after.returncode
            finally:
                release.touch()
                grandchild_release.touch()
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
        (repo.parent / 'observed.json').write_text(json.dumps(observed, indent=2))
        return observed

    @staticmethod
    def alive(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        try:
            state = subprocess.run(['/bin/ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
        except OSError:
            return True
        return bool(state) and not state.startswith('Z')

    @staticmethod
    def check_orphan(observed):
        require(observed['grandchild_alive_after_kills'], f'the grandchild did not survive: {observed}')
        require(observed['held_after_kill'], f'a killed dispatcher and wrapper released the lock the grandchild holds: {observed}')
        require(observed['after_returncode'] == 0, f'the execution after the last exit failed: {observed}')

    def pruning(self):
        fresh = self.fixture('prune-without-lock')
        self.call(fresh, ['--prune'], readonly=True)
        require(not (fresh / 'tests/.checkout.lock').exists(), 'preview created a lock file')
        # Finder metadata is disposable; other standalone bytes are not run ownership.
        loose = self.fixture('prune-loose-file')
        (loose / 'tests/out/kept/link').unlink()
        (loose / 'tests/out/runs').mkdir()
        (loose / 'tests/out/runs/.DS_Store').write_bytes(b'finder')
        (loose / 'tests/out/.DS_Store').write_bytes(b'finder root')
        (loose / 'tests/out/kept/.DS_Store').write_bytes(b'finder nested')
        self.call(loose, output='tests/out/runs/done')
        preview = json.loads(self.call(loose, ['--prune'], readonly=True).stdout)
        metadata = {'tests/out/.DS_Store', 'tests/out/runs/.DS_Store', 'tests/out/kept/.DS_Store'}
        require({r['path'] for r in preview['targets'] if r['kind']=='metadata'} == metadata, 'metadata preview differs')
        report = json.loads(self.call(loose, ['--prune', '--apply']).stdout)
        rows = {r['path']: r['disposition'] for r in report['runs']}
        require(set(report['removed']) == metadata | {'tests/out/runs/done'} and not report['failures'], f'metadata cleanup failed: {report}')
        require(rows['runs/.DS_Store'] == 'delete' and rows['kept/bytes'] == 'keep: unmanaged', f'loose files were not distinguished: {rows}')
        require(all(not (loose / p).exists() for p in metadata) and (loose / 'tests/out/kept/bytes').exists(), 'wrong loose file removed')
        (loose / 'tests/out/runs/.DS_Store').symlink_to(loose / 'tests/out/kept/bytes')
        report = json.loads(self.call(loose, ['--prune', '--apply'], code=1).stdout)
        require((loose / 'tests/out/runs/.DS_Store').is_symlink() and (loose / 'tests/out/kept/bytes').exists(), 'metadata cleanup followed redirect')
        require(any(r['path']=='tests/out/runs/.DS_Store' for r in report['failures']), 'metadata redirect was not refused')
        repo = self.fixture('pruning')
        base = repo / 'tests/out'
        names = ('passed', 'failed', 'interrupted', 'ambiguous', 'formerly-pinned')
        for name in names:
            self.call(repo, output='tests/out/runs/' + name, code=1 if name == 'failed' else 0,
                      RETENTION_STATUS='fail' if name == 'failed' else 'pass')
        for relative in ('custom', 'elsewhere/deep/output'):
            self.call(repo, output='tests/out/' + relative)
        (base / 'runs/interrupted/run.json').unlink()
        (base / 'runs/ambiguous/run.json').write_text('{')
        self.index(repo, 'runs/formerly-pinned')
        (base / 'runs/formerly-pinned/KEEP').touch()
        (base / 'runs/unmanaged').mkdir()
        (base / 'runs/unmanaged/bytes').write_bytes(b'not owned')
        # An owner inside an unowned conventional run is fixture content, not authority.
        self.call(repo, output='tests/out/runs/unmanaged/fixture')
        (base / 'runs/bad-owner').mkdir()
        (base / 'runs/bad-owner/owner.json').write_text('{}')
        (base / 'runs/redirect').symlink_to(repo.parent)
        blocked = {p: artifact.inventory(base / 'runs' / p) for p in ('unmanaged', 'bad-owner')}
        preview = json.loads(self.call(repo, ['prune'], make=True, readonly=True).stdout)
        rows = {r['path']: r['disposition'] for r in preview['runs']}
        require(all(rows['runs/' + name] == 'delete' for name in names), 'completion or old pin retained output')
        # A preview cannot authorize deletion of changed ownership.
        (base / 'runs/passed/owner.json').write_text('{}')
        report = json.loads(self.call(repo, ['prune', 'APPLY=1'], make=True, code=2).stdout)
        require(set(report['removed']) == {'tests/out/runs/' + name for name in names if name != 'passed'} | {'tests/out/custom', 'tests/out/elsewhere/deep/output'}, 'wrong deletion set')
        require((base / 'runs/passed').exists(), 'changed owner erased')
        for name, before in blocked.items():
            require(artifact.inventory(base / 'runs' / name) == before, 'unknown ownership changed')
        require((base / 'runs/redirect').is_symlink(), 'redirect removed')
        for args in (['--apply'], ['--unfinished', 'x'], ['--prune', '--suite', 'probe'],
                     ['--prune', '--case', 'probe/witness'], ['--prune', '--all'], ['--prune', '--list']):
            self.call(repo, args, code=2, readonly=True)
        runner = repo / 'tests/run.sh'
        original = runner.read_bytes()
        marker = repo / 'unexpected-prune'
        runner.write_text('#!/bin/sh\ntouch unexpected-prune\nexit 97\n')
        try:
            for value in ('', '0', '2', 'true', '1 '):
                result = self.call(repo, ['prune', 'APPLY=' + value], make=True, code=2, readonly=True)
                require(b'APPLY must be 1' in result.stderr, 'invalid APPLY diagnostic missing')
            for value in ('', ' 1', '1 '):
                self.call(repo, ['prune'], make=True, code=2, readonly=True, APPLY=value)
            self.call(repo, ['clean'], make=True, code=2, readonly=True)
            require(not marker.exists(), 'invalid prune request invoked the dispatcher')
        finally:
            runner.write_bytes(original)
        self.completed.append('ordinary prune removes inactive completed/interrupted output, ignores pins, and preserves unknown owners')

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
        require(kept == artifact.inventory(repo / 'tests/out/kept'), 'unmanaged sibling changed')
        self.completed.append('completed pass and failure replacement; unmanaged sibling unchanged')
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
        for target in ('tests/out/link/run', 'tests/out/alias', 'tests/out/runs/../fresh',
                       'tests/out', 'tests/out/runs', 'tests/out/pytest-owners/fake', 'tests/out/.retention/fake'):
            self.call(repo, output=target, code=2, readonly=True)
        self.completed.append('symlink redirects and lexical path escapes')
        self.locking()
        self.pruning()
        (self.out / 'controls.json').write_text(json.dumps(self.completed, indent=2) + '\n')
        print(f'{len(self.completed)} retention controls passed ({self.count} invocations)')


if __name__ == '__main__':
    Controls(Path(sys.argv[1]).resolve()).run()
