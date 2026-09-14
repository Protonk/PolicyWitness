"""Test-owned Unix rendezvous and OS exit observation for helper --tree.

PIDs come from LOCAL_PEERPID, and exit evidence comes from EVFILT_PROC.
No PW output, PID polling, shared-memory layout, or sandbox API is consulted.
"""
import os
import json
import select
import signal
import socket
import subprocess
import time


def process_snapshot(helper, pid):
    """Query libproc through the shared fixture, without trusting PW metadata."""
    result = subprocess.run([str(helper), '--process', str(pid)],
                            capture_output=True, text=True, timeout=2)
    assert result.returncode == 0, f'process {pid}: {result.stderr}'
    info = json.loads(result.stdout)
    assert info['version'] == 1 and info['complete'] is True, info
    assert type(info['pid']) is int and info['pid'] == pid, info
    assert type(info['ppid']) is int and info['ppid'] >= 0, info
    assert type(info['start_sec']) is int and info['start_sec'] > 0, info
    assert type(info['start_usec']) is int and 0 <= info['start_usec'] < 1_000_000, info
    assert isinstance(info['path'], str) and info['path'].startswith('/'), info
    return info


class ExitObserver:
    """Register live processes now; require their OS exit events later."""
    def __init__(self):
        self.queue = select.kqueue()
        self.pids = set()
        self.exited = set()

    def watch(self, pid):
        assert pid > 0 and pid not in self.pids, f'invalid or duplicate watched PID: {pid}'
        self.queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                           flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                           fflags=select.KQ_NOTE_EXIT)], 0, 0)
        self.pids.add(pid)

    def exits(self, timeout=0):
        for event in self.queue.control(None, max(1, len(self.pids)), timeout):
            assert not event.flags & select.KQ_EV_ERROR, f"exit observation failed: {event}"
            if event.fflags & select.KQ_NOTE_EXIT:
                self.exited.add(event.ident)
        return set(self.exited)

    def assert_stopped(self, timeout=2):
        assert self.pids, 'register live processes before checking exit'
        deadline = time.monotonic() + timeout
        while self.exits() != self.pids:
            left = deadline - time.monotonic()
            assert left > 0, f"processes still running: {self.pids - self.exited}"
            self.exits(min(left, 0.1))

    def close(self):
        self.queue.close()


class TreeControl:
    def __init__(self, path):
        self.path = str(path)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(2)
        self.observer = ExitObserver()
        self.peers = {}
        self.pids = {}

    @property
    def exited(self):
        return self.observer.exited

    def accept(self, timeout=5):
        deadline = time.monotonic() + timeout
        while len(self.peers) < 2:
            self.listener.settimeout(max(0.01, deadline - time.monotonic()))
            peer, _ = self.listener.accept()
            try:
                peer.settimeout(max(0.01, deadline - time.monotonic()))
                role = peer.recv(1).decode('ascii')
                assert role in ('P', 'C') and role not in self.peers, f"unexpected role {role!r}"
                # macOS sys/un.h: SOL_LOCAL=0, LOCAL_PEERPID=2.
                pid = peer.getsockopt(0, 2)
                assert pid > 0 and pid not in self.pids.values(), f"invalid peer PID {pid}"
                self.observer.watch(pid)
                self.peers[role], self.pids[role] = peer, pid
                self.ping(role)
            except BaseException:
                peer.close()
                raise
        return self.pids

    def ping(self, role):
        peer = self.peers[role]
        peer.settimeout(1)
        peer.sendall(b'p')
        assert peer.recv(1) == b'a', f"{role}: no live response"

    def exits(self, timeout=0):
        return self.observer.exits(timeout)

    def assert_running(self):
        assert set(self.pids) == {'P', 'C'}, 'both processes must be observed before checking liveness'
        assert not self.exits(), f'tree already exited: {self.exited}'
        for role in ('P', 'C'):
            self.ping(role)
        assert not self.exits(), f'tree exited during liveness check: {self.exited}'

    def assert_stopped(self, timeout=2):
        assert set(self.pids) == {'P', 'C'}, "both processes must be observed before checking exit"
        self.observer.assert_stopped(timeout)

    def release(self):
        for peer in self.peers.values():
            try:
                peer.sendall(b'q')
            except OSError:
                pass

    def close(self):
        self.release()
        # Use exit events to avoid signalling peers already observed exiting.
        deadline = time.monotonic() + 2
        while self.pids and self.exits() != set(self.pids.values()) and time.monotonic() < deadline:
            self.exits(0.1)
        for pid in set(self.pids.values()) - self.exits():
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for peer in self.peers.values():
            peer.close()
        self.listener.close()
        self.observer.close()
