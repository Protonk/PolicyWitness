"""Recover only a published live resource; never admit another test engine."""
import json
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read, write, checkout_lock, finish
from supervisor import close_resource
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import ExitObserver


def recover(out):
    for path in sorted((out / 'resources').glob('*/record.json')):
        record = read(path)
        if record['state'] == 'closed':
            continue
        peer = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        peer.settimeout(5)
        peer.connect(str(Path(record['socket_dir']) / 'recover'))
        assert peer.getsockopt(0, 2) == record['pid'], 'recovery peer PID mismatch'
        peer.sendall(json.dumps(dict(nonce=record['nonce'])).encode())
        data, fds, _, _ = socket.recv_fds(peer, 4096, 1)
        observed = json.loads(data)
        assert len(fds) == 1 and observed == dict(pid=record['pid'], engine_exited=True, nonce=record['nonce'])
        fd = fds[0]
        try:
            held = os.fstat(fd)
            assert (held.st_dev, held.st_ino) == checkout_lock.lock_identity(ROOT)
            assert held.st_ino == record['lock_inode']
            assert checkout_lock.read_owner(fd)['nonce'] == record['nonce']
            observer = ExitObserver()
            observer.watch(record['pid'])
            peer.sendall(b'release')
            observer.assert_stopped(timeout=5)
            write(path.parent / 'recovery.json', dict(peer_pid=record['pid'], held_inode=held.st_ino,
                  engine_exit_observed=True, child_exit_events=sorted(observer.exited)))
            close_resource(path)
            observer.close()
        finally:
            os.close(fd)
            peer.close()
    # Missing terminal reports remain missing; do not infer an engine status.
    finish(out, None, recovery=True)


if __name__ == '__main__':
    recover(Path(sys.argv[1]))
