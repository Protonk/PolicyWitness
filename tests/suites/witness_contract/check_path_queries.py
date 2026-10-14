"""Exploratory native observations; no prediction/enforcement agreement oracle."""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import select
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
CONTENTS = b'PW path-query independent witness\n'
OPS = {'read': 'file-read-data', 'create': 'file-write-create',
       'unlink': 'file-write-unlink', 'stat': 'file-read-metadata'}
SHAPES = ['existing', 'absent_leaf', 'absent_parent', 'dangling_leaf',
          'dangling_parent', 'symlink_loop', 'not_directory', 'no_search', 'mode_zero']
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.realpath.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
LIBC.realpath.restype = ctypes.c_void_p


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def capture(command, out, name, *, stdin=None, cwd=None):
    started = time.monotonic_ns()
    r = subprocess.run([str(x) for x in command], input=stdin, capture_output=True,
                       cwd=cwd, timeout=40)
    (out / (name + '.stdout')).write_bytes(r.stdout)
    (out / (name + '.stderr')).write_bytes(r.stderr)
    save(out / (name + '.command.json'), dict(argv=[str(x) for x in command],
         cwd=str(cwd) if cwd else None, returncode=r.returncode,
         start_ns=started, end_ns=time.monotonic_ns()))
    assert r.returncode == 0, (name, r.returncode, r.stderr.decode(errors='replace'))
    return r


def path_state(path):
    path = str(path)
    buf = ctypes.create_string_buffer(4096)
    ctypes.set_errno(0)
    resolved = LIBC.realpath(os.fsencode(path), buf)
    result = dict(path=path, realpath= os.fsdecode(buf.value) if resolved else None,
                  realpath_errno=ctypes.get_errno() if not resolved else 0)
    for name, call in [('lstat', os.lstat), ('stat', os.stat)]:
        try:
            s = call(path)
            result[name] = dict(device=s.st_dev, inode=s.st_ino, mode=s.st_mode,
                                uid=s.st_uid, gid=s.st_gid, size=s.st_size)
        except OSError as e:
            result[name] = dict(errno=e.errno)
    if 'mode' in result['lstat'] and stat.S_ISLNK(result['lstat']['mode']):
        result['link'] = os.readlink(path)
    if 'mode' in result['stat'] and stat.S_ISREG(result['stat']['mode']):
        try:
            result['content_hex'] = Path(path).read_bytes().hex()
        except OSError as e:
            result['read_errno'] = e.errno
    return result


def prepare(directory, shape):
    if directory.exists():
        # Only exact test-owned mode-zero directories need restoration.
        for name in ('blocked', 'sibling'):
            branch = directory / name
            if branch.exists(): branch.chmod(0o700)
        shutil.rmtree(directory)
    directory.mkdir()
    paths = {}
    for name in ('blocked', 'sibling'):
        branch = directory / name
        branch.mkdir()
        target = branch / 'target'
        if shape in ('existing', 'no_search', 'mode_zero'):
            target.write_bytes(CONTENTS)
        elif shape == 'absent_parent': target = branch / 'missing' / 'target'
        elif shape == 'dangling_leaf': target.symlink_to(branch / 'missing-destination')
        elif shape == 'dangling_parent':
            (branch / 'link').symlink_to(branch / 'missing-directory')
            target = branch / 'link' / 'target'
        elif shape == 'symlink_loop': target.symlink_to(target)
        elif shape == 'not_directory':
            (branch / 'file').write_bytes(CONTENTS)
            target = branch / 'file' / 'target'
        elif shape != 'absent_leaf': raise AssertionError(shape)
        paths[name] = target
        if shape == 'no_search': branch.chmod(0)
        if shape == 'mode_zero': target.chmod(0)
    for name in ('anchor_denied', 'anchor_allowed'):
        target = directory / name
        target.write_bytes(CONTENTS)
        paths[name] = target
    return paths


def policy_for(paths, operation, matcher, denied):
    policy = '(version 1) (allow default)'
    if not denied: return policy
    if matcher == 'literal': predicate = '(literal ' + json.dumps(str(paths['blocked'])) + ')'
    elif matcher == 'subpath':
        # The branch spelling also covers dangling/absent descendants.
        branch = str(paths['anchor_denied'].parent / 'blocked')
        predicate = '(subpath ' + json.dumps(branch) + ')'
    elif matcher == 'regex':
        branch = str(paths['anchor_denied'].parent / 'blocked')
        pattern = '^' + re.escape(branch) + '(/|$)'
        predicate = '(regex #' + json.dumps(pattern) + ')'
    else: raise AssertionError(matcher)
    return policy + ' (deny ' + operation + ' ' + predicate + ') (deny ' + operation + ' (literal ' + json.dumps(str(paths['anchor_denied'])) + '))'


class Target:
    def __init__(self, binary, policy, out, cwd, receipts):
        self.out, self.receipts = out, receipts
        self.stderr = (out / 'target.stderr').open('wb')
        self.child = subprocess.Popen([str(binary), policy], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=self.stderr, cwd=cwd)
        self.receipt = dict(pid=self.child.pid, argv=[str(binary), policy], cwd=str(cwd), reaped=False)
        receipts.append(self.receipt)
        save(out / 'target-process.json', self.receipt)
    def receive(self):
        assert select.select([self.child.stdout], [], [], 10)[0], 'native target response timeout'
        raw = self.child.stdout.readline(16384)
        with (self.out / 'target.stdout').open('ab') as stream: stream.write(raw)
        assert raw.endswith(b'\n'), ('incomplete target response', raw)
        return json.loads(raw)
    def start(self):
        ready = self.receive()
        assert ready['ready'] and ready['pid'] == self.child.pid and ready['apply_rc'] == 0
        return ready
    def attempt(self, action, path):
        assert not any(c in str(path) for c in '\n\r\t')
        command = action + '\t' + str(path) + '\n'
        with (self.out / 'target.stdin').open('a') as stream: stream.write(command)
        self.child.stdin.write(command.encode()); self.child.stdin.flush()
        return self.receive()
    def finish(self, normal):
        try:
            if normal:
                self.child.stdin.write(b'exit\n'); self.child.stdin.flush()
                code = self.child.wait(timeout=5)
                assert code == 0, code
            elif self.child.poll() is None:
                self.child.kill()
        finally:
            if self.child.poll() is None: self.child.kill()
            code = self.child.wait(timeout=5)
            self.receipt.update(reaped=True, returncode=code)
            save(self.out / 'target-process.json', self.receipt)
            self.child.stdin.close(); self.child.stdout.close(); self.stderr.close()


def boundary(validator, child, paths, action, out, label):
    before = {k: path_state(v) for k, v in paths.items()}
    probes = [dict(step_id=k, operation=OPS[action], filter_type='PATH', filter_value=str(v))
              for k, v in paths.items()]
    data = ''.join(json.dumps(p) + '\n' for p in probes).encode()
    (out / (label + '.queries.ndjson')).write_bytes(data)
    result = capture([validator, '--batch', str(child.child.pid)], out, label + '.validator', stdin=data)
    records = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(records) == len(probes)
    for record, probe in zip(records, probes):
        for key in ('step_id', 'operation', 'filter_type', 'filter_value'): assert record[key] == probe[key]
        assert record['filter_type_id'] == 1
    attempts = {}
    # Each side is independently attempted after this batch has exited/reaped.
    for name in ('blocked', 'sibling'):
        attempts[name] = child.attempt(action, paths[name])
    after = {k: path_state(v) for k, v in paths.items()}
    record = dict(label=label, pid=child.child.pid, action=action, before=before,
                  queries=records, attempts=attempts, after=after)
    save(out / (label + '.observations.json'), record)
    for name, attempt in attempts.items():
        if attempt['rc'] >= 0:
            if action == 'read':
                assert attempt['io_rc'] >= 0 and attempt['close_rc'] == 0
                assert attempt['content_hex'] == before[name]['content_hex']
                assert attempt['inode'] == before[name]['stat']['inode']
            elif action == 'create':
                assert attempt['io_rc'] == 1 and attempt['close_rc'] == 0
                assert after[name]['content_hex'] == b'P'.hex()
            elif action == 'unlink': assert after[name]['lstat'].get('errno') == errno.ENOENT
    return record


def main():
    pw, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    service = pw.parent.parent / 'XPCServices/PWRunner.xpc/Contents/MacOS'
    validator = service / 'sb_api_validator'
    identity = os.environ.get('PW_BYOXPC_IDENTITY') or os.environ.get('IDENTITY')
    assert identity and identity.startswith('Developer ID Application: ')
    workspace = Path(tempfile.mkdtemp(prefix='pw-path-query-', dir='/private/tmp'))
    receipts, observations = [], []
    owner = dict(path=str(workspace), creator_pid=os.getpid(), cleanup_retained=True)
    save(workspace / 'owner.json', owner); save(out / 'workspace-owner.json', owner)
    binary = workspace / 'target'
    try:
        capture(['/usr/bin/sw_vers'], out, 'os')
        capture(['/usr/bin/uname', '-a'], out, 'kernel')
        capture(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', ROOT / 'tests/fixtures/path_query/target.c', '-lsandbox', '-o', binary], out, 'compile')
        capture(['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp=none', '-s', identity, binary], out, 'sign')
        capture(['/usr/bin/codesign', '--verify', '--strict', binary], out, 'verify')
        signature = capture(['/usr/bin/codesign', '-dvv', binary], out, 'signature')
        assert ('Authority=' + identity).encode() in signature.stderr and b'runtime' in signature.stderr
        entitlements = capture(['/usr/bin/codesign', '-d', '--entitlements', ':-', binary], out, 'entitlements')
        assert not entitlements.stdout.strip() or plistlib.loads(entitlements.stdout) == {}
        shutil.copy2(binary, out / 'target')
        for source in ['tests/fixtures/path_query/target.c', 'tests/suites/witness_contract/check_path_queries.py']:
            shutil.copy2(ROOT / source, out / Path(source).name)
        save(out / 'equipment.json', dict(source=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), source_diff=subprocess.check_output(['git', 'diff'], cwd=ROOT, text=True), identity=identity, validator=str(validator), validator_sha256=hashlib.sha256(validator.read_bytes()).hexdigest(), target_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(), uid=os.getuid(), euid=os.geteuid(), cwd=str(workspace)))
        for shape in SHAPES:
            for action in OPS:
                for matcher in ('literal', 'subpath', 'regex'):
                    directory = workspace / 'paths'
                    for denied in (False, True):
                        name = '-'.join((shape, action, matcher, 'deny' if denied else 'allow'))
                        case = out / name; case.mkdir()
                        paths = prepare(directory, shape)
                        policy = policy_for(paths, OPS[action], matcher, denied)
                        child = Target(binary, policy, case, workspace, receipts)
                        normal = False
                        try:
                            child.start()
                            row = boundary(validator, child, paths, action, case, 'boundary')
                            row.update(case=name, shape=shape, matcher=matcher, denied=denied)
                            observations.append(row)
                            normal = True
                        finally: child.finish(normal)
        for matcher in ('literal', 'subpath', 'regex'):
            case = out / ('transition-' + matcher); case.mkdir()
            paths = prepare(workspace / 'paths', 'existing')
            child = Target(binary, policy_for(paths, OPS['read'], matcher, True), case, workspace, receipts)
            normal = False
            try:
                child.start()
                for label, action in [('present', 'read'), ('remove', 'unlink'), ('absent', 'read'), ('recreate', 'create'), ('recreated', 'read')]:
                    row = boundary(validator, child, paths, action, case, label)
                    row.update(case=case.name, shape='transition', matcher=matcher, denied=True)
                    observations.append(row)
                normal = True
            finally: child.finish(normal)
        save(out / 'observations.json', observations)
        save(out / 'summary.json', dict(native_processes=len(receipts), boundaries=len(observations), queries=sum(len(r['queries']) for r in observations), attempts=sum(len(r['attempts']) for r in observations), observation_only=True))
    finally:
        save(out / 'process-cleanup.json', receipts)
        if all(r['reaped'] for r in receipts):
            if (workspace / 'paths').exists():
                for name in ('blocked', 'sibling'):
                    (workspace / 'paths' / name).chmod(0o700)
            shutil.rmtree(workspace)
            owner.update(cleanup_retained=False, absent=not workspace.exists())
        save(out / 'workspace-owner.json', owner)
    assert not owner['cleanup_retained']
    print(json.dumps(json.loads((out / 'summary.json').read_text())))


if __name__ == '__main__':
    main()
