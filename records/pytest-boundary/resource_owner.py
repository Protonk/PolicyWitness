"""A bounded persistent resource adapter: owned file, child and recovery channel."""
import json
import os
from pathlib import Path
import select
import signal
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import append, read


def main():
    gate = socket.socket(fileno=int(sys.argv[1]))
    # EOF before permission cannot acquire anything, even if the parent dies
    # between spawn and publication of the PID.
    if gate.recv(1) != b'g':
        return
    record = read(sys.argv[2])
    fd = int(sys.argv[3])
    assert os.fstat(fd).st_ino == record['lock_inode']
    queue = select.kqueue()
    queue.control([select.kevent(record['engine_pid'], filter=select.KQ_FILTER_PROC,
                  flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT, fflags=select.KQ_NOTE_EXIT)], 0, 0)
    directory = Path(record['socket_dir'])
    directory.mkdir(mode=0o700)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(directory / 'recover'))
    listener.listen(1)
    resource = Path(record['resource'])
    with resource.open('xb') as stream:
        stream.write(b'owned resource\n')
        stream.flush()
        os.fsync(stream.fileno())
    append(Path(record['witness']) / 'resource.jsonl', dict(event='acquired', pid=os.getpid(),
           intent=read(sys.argv[2]), lock_inode=os.fstat(fd).st_ino,
           stdin=os.read(0, 1).hex(), stdout_mode=os.fstat(1).st_mode, stderr_mode=os.fstat(2).st_mode))
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    gate.sendall(b'a')
    gate.close()
    peer = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    peer.connect(os.environ['CONTROL_CANCEL_SOCKET'])
    peer.sendall(b'C')
    engine_exited = False
    while not (Path(sys.argv[2]).parent / 'release').exists():
        for event in queue.control(None, 1, 0):
            if event.fflags & select.KQ_NOTE_EXIT:
                engine_exited = True
                append(Path(sys.argv[2]).parent / 'observations.jsonl', dict(event='engine_exit', pid=event.ident))
        ready, _, _ = select.select([peer, listener], [], [], 0.02)
        if peer in ready:
            command = peer.recv(1)
            if command == b'p':
                peer.sendall(b'a')
            elif command in (b'q', b''):
                break  # External safety release, never credited as candidate cleanup.
        if listener in ready:
            connection, _ = listener.accept()
            connection.settimeout(2)
            try:
                request = json.loads(connection.recv(4096))
                if request != {'nonce': record['nonce']} or not engine_exited:
                    connection.sendall(b'{"refused":true}')
                else:
                    socket.send_fds(connection, [json.dumps(dict(pid=os.getpid(), engine_exited=True,
                                    nonce=record['nonce'])).encode()], [fd])
                    if connection.recv(16) == b'release':
                        break
            finally:
                connection.close()
    peer.close()
    listener.close()
    queue.close()
    (directory / 'recover').unlink()


if __name__ == '__main__':
    main()
