#!/usr/bin/python3
"""Independent capture control: exact bytes, explicit exit, optional socket gate.

Accept the public CLI's argv shape without importing any PW or capture code.
The socket acknowledges that both output streams have been flushed; commands
let the test observe liveness and choose when the process may exit.
"""
import json
from pathlib import Path
import socket
import sys


def main():
    assert sys.argv[1] == 'run'
    request = Path(sys.argv[2])
    specimen = json.loads(request.read_text())
    request.with_name('fixture.received.json').write_text(
        json.dumps({'argv': sys.argv[1:], 'specimen': specimen}) + '\n')
    sys.stdout.buffer.write(bytes.fromhex(specimen['stdout_hex']))
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(bytes.fromhex(specimen['stderr_hex']))
    sys.stderr.buffer.flush()
    if specimen.get('gate'):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
            peer.settimeout(15)  # Independent backstop if the test disappears.
            peer.connect(specimen['gate'])
            peer.sendall(b'r')
            while True:
                command = peer.recv(1)
                if command == b'p':
                    peer.sendall(b'a')
                elif command == b'q':
                    break
                else:
                    raise RuntimeError(f'gate closed or invalid command: {command!r}')
    return specimen['exit_code']


if __name__ == '__main__':
    sys.exit(main())
