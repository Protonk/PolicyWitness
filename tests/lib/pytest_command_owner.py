"""One gated native command, independent of the pytest engine's lifetime."""
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time

import checkout_lock
from pytest_resources import command_context, command_environment, transition
from pytest_support import read, write


def main(path, gate_fd, lock_fd):
    record = read(path)
    gate = socket.socket(fileno=gate_fd)
    directory = Path(record['socket_dir'])
    directory.mkdir(mode=0o700)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(directory / 'recover'))
    listener.listen(1)
    queue = select.kqueue()
    gone = set()
    for pid in (record['engine_pid'], record['controller_pid']):
        try:
            queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                          flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT, fflags=select.KQ_NOTE_EXIT)], 0, 0)
        except ProcessLookupError:
            gone.add(pid)
    gate.sendall(b'ready')
    released = gate.recv(1) == b'g'
    record = read(path)
    command, code, timed_out, cancelled, group_absent = None, None, False, False, True
    recovery_peer = None
    if released:
        if record['state'] != 'command_release_authorized':
            raise ValueError('command release has no durable authorization')
        artifact = Path(record['artifacts'])
        artifact.mkdir(parents=True, exist_ok=True)
        environment = command_environment()
        if record['context'] != command_context(record['root'], environment):
            raise ValueError('command execution context differs from registered intent')
        started = time.monotonic()
        with (artifact / 'stdout').open('wb') as stdout, (artifact / 'stderr').open('wb') as stderr:
            command = subprocess.Popen(record['argv'], cwd=record['root'], env=environment,
                                       stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       pass_fds=(lock_fd,), start_new_session=True)
            transition(path, 'command_started', command_pid=command.pid, command_pgid=command.pid)
            stopping = None
            while True:
                for event in queue.control(None, 4, 0):
                    if event.fflags & select.KQ_NOTE_EXIT:
                        gone.add(event.ident)
                if listener in select.select([listener], [], [], 0)[0]:
                    peer, _ = listener.accept()
                    peer.settimeout(5)
                    request = json.loads(peer.recv(4096))
                    if request.get('token') != record['token'] or not gone:
                        peer.sendall(b'{"error":"identity mismatch or active session"}')
                        peer.close()
                    else:
                        socket.send_fds(peer, [json.dumps(dict(token=record['token'])).encode()], [lock_fd])
                        if peer.recv(16) == b'settle':
                            recovery_peer = peer
                            cancelled = True
                if gate in select.select([gate], [], [], 0)[0]:
                    if gate.recv(1) in (b'', b'c'):
                        cancelled = True
                timed_out |= time.monotonic() - started > record['timeout']
                cancelled |= bool(gone)
                code = command.poll()
                if code is not None:
                    break
                if timed_out or cancelled:
                    if stopping is None:
                        stopping = time.monotonic()
                        try:
                            os.killpg(command.pid, signal.SIGINT)
                        except (ProcessLookupError, PermissionError):
                            # EPERM can denote an unreaped zombie on macOS.
                            # It is not absence evidence; poll/group observation follows.
                            pass
                    elif time.monotonic() - stopping > 1:
                        try:
                            os.killpg(command.pid, signal.SIGKILL)
                        except (ProcessLookupError, PermissionError):
                            # EPERM can denote an unreaped zombie on macOS.
                            # It is not absence evidence; poll/group observation follows.
                            pass
                code = command.poll()
                if code is not None:
                    break
                time.sleep(0.01)
            group_absent = checkout_lock.group_finished(command.pid, 1, command)
            if not group_absent:
                try:
                    os.killpg(command.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                group_absent = checkout_lock.group_finished(command.pid, 5, command)
            stdout.flush(); stderr.flush()
            os.fsync(stdout.fileno()); os.fsync(stderr.fileno())
    # Do not publish quiescence or release the inherited hold while a group survives.
    while not group_absent:
        time.sleep(1)
        group_absent = checkout_lock.group_finished(command.pid, 0)
    # Closing the endpoint and revoking launch authority precede settlement.
    listener.close()
    (directory / 'recover').unlink()
    receipt = dict(token=record['token'], authority_revoked=True, group_absent=group_absent,
                   never_launched=command is None, command_pid=command.pid if command else None,
                   returncode=code, timed_out=timed_out, cancelled=cancelled, parent_exit_events=sorted(gone))
    transition(path, 'quiescent_retained' if group_absent else 'unresolved', settlement=receipt)
    if command:
        write(Path(record['artifacts']) / 'command.json', dict(argv=record['argv'], context=record['context'], **receipt))
    if recovery_peer:
        recovery_peer.close()
    gate.close()
    queue.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])))
