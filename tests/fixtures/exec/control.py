"""Test-owned Unix rendezvous and OS exit observation for helper --tree.

PIDs come from LOCAL_PEERPID, and exit evidence comes from EVFILT_PROC.
No PW output, PID polling, shared-memory layout, or sandbox API is consulted.
"""
import os
import select
import signal
import socket
import time


class TreeControl:
    def __init__(self, path):
        self.path = str(path)
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(2)
        self.queue = select.kqueue()
        self.peers = {}
        self.pids = {}
        self.exited = set()

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
                self.queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                                   flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                   fflags=select.KQ_NOTE_EXIT)], 0, 0)
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
        for event in self.queue.control(None, 2, timeout):
            assert not event.flags & select.KQ_EV_ERROR, f"exit observation failed: {event}"
            if event.fflags & select.KQ_NOTE_EXIT:
                self.exited.add(event.ident)
        return set(self.exited)

    def assert_stopped(self, timeout=2):
        assert set(self.pids) == {'P', 'C'}, "both processes must be observed before checking exit"
        deadline = time.monotonic() + timeout
        while self.exits() != set(self.pids.values()):
            left = deadline - time.monotonic()
            assert left > 0, f"processes still running: {set(self.pids.values()) - self.exited}"
            self.exits(min(left, 0.1))

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
        self.queue.close()
