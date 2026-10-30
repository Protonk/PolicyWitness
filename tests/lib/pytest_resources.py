"""Test command ownership and recovery. No pytest imports or test selection policy.

The registry is outside disposable runs. Reading a state is not exit evidence:
closure requires a matching settlement receipt with revoked launch authority.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import select
import shutil
import socket
import subprocess
import sys
import time
import uuid

from pytest_support import append, contained, digest, read, write

RUN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')


def base(root):
    return Path(root).resolve() / 'tests/out/pytest-owners'


def record_paths(root, run_id=None):
    parent = base(root)
    if run_id is not None:
        if not RUN.fullmatch(run_id) or run_id in ('.', '..'):
            raise ValueError('invalid ownership run ID')
        parent /= run_id
    if not parent.exists():
        return []
    if parent.resolve() != parent:
        raise ValueError('redirected ownership registry')
    return sorted(parent.glob('*/record.json') if run_id else parent.glob('*/*/record.json'))


def validate(root, path):
    contained(base(root), path)
    record = read(path)
    if record['schema_version'] != 1 or record['root'] != str(Path(root).resolve()):
        raise ValueError('foreign ownership record')
    if path.parent.name != record['operation_id'] or path.parent.parent.name != record['run_id']:
        raise ValueError('ownership record identity mismatch')
    contained(Path(root) / 'tests/out', record['out'])
    contained(Path(record['out']), record['artifacts'])
    return record


def settled(record):
    receipt = record.get('settlement', {})
    return (receipt.get('token') == record.get('token') and receipt.get('authority_revoked') is True
            and receipt.get('group_absent') is True
            and (receipt.get('never_launched') is True or
                 (receipt.get('command_pid') == record.get('command_pid') and
                  type(receipt.get('returncode')) is int)))


def disposition(record):
    if not settled(record):
        return 'checkout'
    return 'closed' if record.get('state') == 'closed' else 'output'


def inspect(root, run_id=None):
    results = []
    try:
        paths = record_paths(root, run_id)
        # Empty/incomplete operation directories are not silently ignored.
        parent = base(root) / run_id if run_id else base(root)
        dirs = sorted(parent.glob('*') if run_id else parent.glob('*/*')) if parent.exists() else []
        for directory in dirs:
            if directory.is_dir() and not (directory / 'record.json').is_file():
                results.append(dict(path=str(directory), blocking='checkout', error='missing ownership record'))
        for path in paths:
            try:
                record = validate(root, path)
                results.append(dict(path=str(path), run_id=record['run_id'], out=record['out'],
                                    state=record['state'], blocking=disposition(record),
                                    recovery=f'tests/run.sh --recover-ownership {record["run_id"]}'))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                results.append(dict(path=str(path), blocking='checkout', error=str(exc)))
    except (OSError, ValueError) as exc:
        results.append(dict(path=str(base(root)), blocking='checkout', error=str(exc)))
    return results


def guard(root, *, purpose='execution', target=None):
    for row in inspect(root):
        blocked = row['blocking'] == 'checkout' if purpose == 'execution' else False
        if purpose == 'disposal' and row['blocking'] != 'closed':
            if not row.get('out') or target is None:
                blocked = True
            else:
                out, target_path = Path(row['out']), Path(target).absolute()
                blocked = out == target_path or out in target_path.parents or target_path in out.parents
        if blocked:
            raise ValueError('pytest ownership ' + row['blocking'] + ' hold: ' + row['path'] +
                             '; ' + row.get('recovery', 'inspect the malformed ownership registry') +
                             '; closure requires settlement and revoked launch authority')


def reserve(root, out, run_id, family, item, command, artifacts, timeout, scope, engine_pid):
    op = uuid.uuid4().hex
    folder = base(root) / run_id / op
    folder.mkdir(parents=True)
    record = dict(schema_version=1, root=str(root), out=str(out), run_id=run_id, family=family,
                  item=item, operation_id=op, state='reserved', token=uuid.uuid4().hex,
                  nonce=scope.nonce, lock_identity=list(scope.identity), engine_pid=engine_pid,
                  controller_pid=os.getpid(), argv=list(map(str, command)), artifacts=str(artifacts),
                  timeout=timeout, socket_dir='/private/tmp/pwpx-' + uuid.uuid4().hex)
    write(folder / 'record.json', record)
    return folder / 'record.json'


def transition(path, state, **fields):
    record = read(path)
    record.update(state=state, **fields)
    write(path, record)
    append(path.parent / 'history.jsonl', dict(state=state, time_ns=time.time_ns(), **fields))
    return record


def close_record(path):
    record = read(path)
    if not settled(record):
        raise ValueError('no settlement/revocation basis for closure')
    directory = Path(record['socket_dir'])
    if directory.exists():
        if directory.is_symlink() or directory.parent != Path('/private/tmp') or not directory.name.startswith('pwpx-'):
            raise ValueError('invalid recovery directory')
        # The owner removes its endpoint before publishing settlement.
        directory.rmdir()
    return transition(path, 'closed', cleanup_basis='settled_group_and_revoked_authority')


def snapshot(root, run_id):
    records = [validate(root, p) for p in record_paths(root, run_id)]
    problems = [r for r in inspect(root, run_id) if r['blocking'] != 'closed']
    return dict(schema_version=1, run_id=run_id, commands=records,
                closed=not problems, problems=problems)


def recover(root, run_id, *, apply=False):
    report = dict(run_id=run_id, apply=apply, before=inspect(root, run_id), actions=[], unresolved=[])
    if not apply:
        return report
    import checkout_lock
    for path in record_paths(root, run_id):
        before = digest(path)
        try:
            record = validate(root, path)
            if disposition(record) == 'closed':
                continue
            endpoint = Path(record['socket_dir']) / 'recover'
            if endpoint.exists():
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
                    peer.settimeout(8)
                    peer.connect(str(endpoint))
                    if peer.getsockopt(0, 2) != record.get('owner_pid'):
                        raise ValueError('recovery peer PID mismatch; no signal sent')
                    peer.sendall(json.dumps(dict(token=record['token'], action='recover')).encode())
                    data, descriptors, _, _ = socket.recv_fds(peer, 8192, 1)
                    reply = json.loads(data)
                    if len(descriptors) != 1:
                        raise ValueError('owner refuses recovery: ' + str(reply))
                    fd = descriptors[0]
                    try:
                        info = os.fstat(fd)
                        if ((info.st_dev, info.st_ino) != tuple(record['lock_identity']) or
                                checkout_lock.read_owner(fd)['nonce'] != record['nonce'] or
                                reply.get('token') != record['token']):
                            raise ValueError('recovery descriptor/nonce mismatch')
                        queue = select.kqueue()
                        try:
                            queue.control([select.kevent(record['owner_pid'], filter=select.KQ_FILTER_PROC,
                                          flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                          fflags=select.KQ_NOTE_EXIT)], 0, 0)
                            peer.sendall(b'settle')
                            events = queue.control(None, 1, 8)
                            if not events or not events[0].fflags & select.KQ_NOTE_EXIT:
                                raise ValueError('owner exit not observed')
                            close_record(path)
                        finally:
                            queue.close()
                    finally:
                        os.close(fd)
            else:
                # A new lock claim is recovery-only; it never admits execution.
                # The old bytes were retained above and are never replaced by this claim.
                with checkout_lock.owned(root, purpose='recovery'):
                    record = validate(root, path)
                    if record['state'] == 'reserved':
                        record = transition(path, 'quiescent_retained', settlement=dict(token=record['token'], authority_revoked=True, group_absent=True, never_launched=True), recovery_basis='durable reservation without any launch authorization')
                    if not settled(record):
                        raise ValueError('missing live peer and settlement evidence; historical PID not signalled')
                    close_record(path)
            report['actions'].append(dict(path=str(path), before_sha256=before, after_sha256=digest(path)))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report['unresolved'].append(dict(path=str(path), error=str(exc)))
    report['after'] = inspect(root, run_id)
    report['unresolved'] += [r for r in report['after'] if r['blocking'] != 'closed' and r not in report['unresolved']]
    if (base(root) / run_id).is_dir():
        write(base(root) / run_id / ('recovery-' + uuid.uuid4().hex + '.json'), report)
    return report


def retire_closed(root, out):
    for run in base(root).iterdir() if base(root).exists() else ():
        paths = record_paths(root, run.name) if run.is_dir() else []
        records = [validate(root, p) for p in paths]
        if records and all(r['out'] == str(out) and disposition(r) == 'closed' for r in records):
            shutil.rmtree(run)


class Command:
    """The supervisor's handle to one separately owned command; never runs a test item."""
    def __init__(self, root, out, run_id, family, item, argv, artifacts, timeout, scope, engine_pid):
        self.path = reserve(root, out, run_id, family, item, argv, artifacts, timeout, scope, engine_pid)
        self.gate, child = socket.socketpair()
        transition(self.path, 'owner_launch_authorized')
        self.logs = [(self.path.parent / name).open('wb') for name in ('owner.stdout', 'owner.stderr')]
        try:
            self.process = subprocess.Popen([sys.executable, '-B', '-S',
                    str(Path(__file__).with_name('pytest_command_owner.py')), str(self.path),
                    str(child.fileno()), str(scope.fd)], pass_fds=(child.fileno(), scope.fd),
                    stdin=subprocess.DEVNULL, stdout=self.logs[0], stderr=self.logs[1], start_new_session=True)
            child.close()
            transition(self.path, 'owner_bound', owner_pid=self.process.pid)
            self.gate.settimeout(5)
            if self.gate.recv(16) != b'ready':
                raise ValueError('command owner did not become ready')
            transition(self.path, 'command_release_authorized')
            self.gate.sendall(b'g')
        except BaseException:
            child.close()
            self.gate.close()
            raise

    def cancel(self):
        try:
            self.gate.sendall(b'c')
        except OSError:
            pass

    def poll(self):
        return self.process.poll()

    def finish(self):
        code = self.process.wait(timeout=10)
        self.gate.close()
        for log in self.logs:
            log.close()
        record = read(self.path)
        if code != 0 or not settled(record):
            raise ValueError('command ownership unresolved: ' + str(self.path))
        record = close_record(self.path)
        return dict(operation_id=record['operation_id'], record=str(self.path),
                    artifacts=record['artifacts'], **record['settlement'])
