"""Independent cases and a stubborn descendant for dispatcher cancellation."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys


def rendezvous(role):
    # Same readiness/ping/release protocol as the existing tree observer.
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
        peer.connect(os.environ['CONTROL_CANCEL_SOCKET'])
        peer.sendall(role)
        while True:
            command = peer.recv(1)
            if command == b'p':
                peer.sendall(b'a')
            elif command in (b'q', b''):
                return


case = sys.argv[1]
if case == 'helper':
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    rendezvous(b'C')
    raise SystemExit(0)

out = Path(os.environ['PW_TEST_OUT_DIR'])
path = out / 'suites/cancel' / case
path.mkdir(parents=True)
with Path(os.environ['CONTROL_CANCEL_RECEIPTS']).open('a') as stream:
    stream.write(json.dumps({'case': case}) + '\n')


def event(step, status):
    with (out / 'events.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='test_event', run_id=os.environ['PW_TEST_RUN_ID'],
                                     suite='cancel', test_id=case, step=step, status=status)) + '\n')


event('test_start', 'start')
if case == 'active':
    (path / 'artifacts').mkdir()
    (path / 'artifacts/partial.bin').write_bytes(b'partial observation\x00\xff\n')
    print('active fixture reached rendezvous', flush=True)
    helper = subprocess.Popen([sys.executable, '-B', __file__, 'helper'])
    rendezvous(b'P')
    helper.wait(timeout=3)

(path / 'report.json').write_text(json.dumps(dict(suite='cancel', test_id=case,
                                                status='pass', message='fixture completed')) + '\n')
event('test_end', 'pass')
