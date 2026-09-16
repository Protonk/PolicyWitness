"""Independent command with flushed bytes and a stubborn child; no release imports.

Uses the exec fixture's P/C, ping, and release protocol. Both processes ignore
SIGINT unless configured to let the parent exit zero after interruption. They
keep their inherited process group so the wrapper must supply group ownership.
"""
import json
import os
from pathlib import Path
import signal
import socket
import sys


def rendezvous(path, role):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
        peer.connect(path)
        peer.sendall(role)
        while True:
            request = peer.recv(1)
            if request == b'p':
                peer.sendall(b'a')
            elif request == b'q':
                return
            else:
                raise RuntimeError(f'fixture gate closed or invalid request: {request!r}')


def main():
    config = json.loads(Path(sys.argv[1]).read_text())
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    # Fail independently if the observer disappears. This is longer than the
    # test's outer deadline and cannot supply a successful timeout observation.
    signal.alarm(45)
    with Path(config['receipts']).open('a') as stream:
        stream.write(json.dumps({'pid': os.getpid(), 'argv': sys.argv[1:]}) + '\n')
    sys.stdout.buffer.write(bytes.fromhex(config['stdout_hex']))
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(bytes.fromhex(config['stderr_hex']))
    sys.stderr.buffer.flush()
    child = os.fork()
    if child == 0:
        signal.alarm(45)  # alarms are not inherited across fork
        rendezvous(config['socket'], b'C')
        return 0
    if config['parent_exits_on_interrupt']:
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    rendezvous(config['socket'], b'P')
    _, status = os.waitpid(child, 0)
    return os.waitstatus_to_exitcode(status)


if __name__ == '__main__':
    raise SystemExit(main())
