"""Bounded private protocol, separate from the durable evidence streams."""
import json
import struct


def send(peer, value):
    raw = json.dumps(value).encode()
    if len(raw) > 1024 * 1024:
        raise ValueError('engine message exceeds bound')
    peer.sendall(struct.pack('!I', len(raw)) + raw)


def exact(peer, size):
    result = b''
    while len(result) < size:
        part = peer.recv(size - len(result))
        if not part:
            raise EOFError('engine channel closed')
        result += part
    return result


def receive(peer):
    size, = struct.unpack('!I', exact(peer, 4))
    if size > 1024 * 1024:
        raise ValueError('engine message exceeds bound')
    return json.loads(exact(peer, size))
