"""Test-owned bridge rendezvous. No PW JSON, ABI, or classifier inputs."""
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'exec'))
from control import ExitObserver


def install_bridge(binary, directory, socket_path):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'validator-bridge'
    shutil.copy2(binary, target)
    Path(str(target) + '.gate').write_text(str(socket_path) + '\n')
    return target


class Gate:
    def __init__(self, path):
        self.path = str(path)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(1)
        self.peer = None
        self.reader = None
        self.pid = None
        self.events = []
        self.observer = ExitObserver()

    def receive(self, event):
        value = json.loads(self.reader.readline())
        self.events.append(value)
        assert value['event'] == event, (event, value)
        return value

    def accept(self):
        self.listener.settimeout(8)
        self.peer, _ = self.listener.accept()
        self.peer.settimeout(5)
        self.pid = self.peer.getsockopt(0, 2)  # LOCAL_PEERPID
        self.observer.watch(self.pid)
        self.reader = self.peer.makefile('rb')
        ready = self.receive('ready')
        assert ready['pid'] == self.pid and ready['target_pid'] > 0, ready
        return ready

    def command(self, command, event):
        self.peer.sendall(command.encode())
        return self.receive(event)

    def query(self):
        return self.command('q', 'queried')['record']

    def emit(self):
        return self.command('e', 'emitted')

    def ping(self):
        assert not self.observer.exits(), 'bridge exited while collection held'
        return self.command('p', 'held')

    def finish(self):
        self.command('c', 'closed')
        self.peer.sendall(b'x')

    def close(self):
        if self.peer:
            try:
                self.peer.sendall(b'x')
            except OSError:
                pass
            try:
                self.observer.assert_stopped(timeout=2)
            except AssertionError:
                if self.pid not in self.observer.exits():
                    try:
                        os.kill(self.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                self.observer.assert_stopped(timeout=2)
            self.reader.close()
            self.peer.close()
        self.listener.close()
        self.observer.close()

    def save(self, path):
        Path(path).write_text(json.dumps(self.events, indent=2) + '\n')
