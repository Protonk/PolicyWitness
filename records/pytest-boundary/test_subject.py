"""Investigation-only stimuli. Receipts do not import the candidate accountant."""
import json
import os
from pathlib import Path
import socket
import subprocess

import pytest

WITNESS = Path(os.environ['BOUNDARY_WITNESS'])
MODE = os.environ['BOUNDARY_MODE']
if MODE == 'collection_error':
    raise RuntimeError('deliberate collection failure')


def receipt(stage):
    with (WITNESS / 'starts.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(stage=stage, pid=os.getpid())) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def rendezvous():
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
        peer.connect(os.environ['CONTROL_CANCEL_SOCKET'])
        peer.sendall(b'P')
        while True:
            command = peer.recv(1)
            if command == b'p':
                peer.sendall(b'a')
            elif command in (b'q', b''):
                return


@pytest.fixture
def leased_resource(request):
    receipt('active.setup')
    request.config.boundary.acquire(request.node.nodeid)
    if MODE == 'setup_failure':
        rendezvous()
        raise RuntimeError('setup failed after acquisition before yield')
    yield
    receipt('active.teardown')
    if MODE == 'double_failure':
        raise RuntimeError('distinct teardown failure')


def test_completed():
    receipt('completed.body')


def test_active(leased_resource):
    receipt('active.body')
    (WITNESS / 'partial.bin').write_bytes(b'partial observation\x00\xff\n')
    rendezvous()
    if MODE == 'double_failure':
        raise AssertionError('distinct body failure')


def test_queued():
    receipt('queued.body')


def test_environment():
    receipt('environment.body')
    interpreter = '/opt/homebrew/opt/python@3.14/bin/python3.14'
    implicit = subprocess.run([interpreter, '-B', '-I', '-S', '-c',
                               'import os; os.write(1,b"implicit stdout\\n"); os.write(2,b"implicit stderr\\n")'])
    assert implicit.returncode == 0
    code = '''import json,os,sys
fds=[]
for i in range(3,128):
 try: os.fstat(i); fds.append(i)
 except OSError: pass
print(json.dumps(dict(argv=sys.argv[1:],cwd=os.getcwd(),env=dict(os.environ),stdin=os.read(0,99).hex(),fds=fds,executable=sys.executable)))
os.write(2,b'explicit stderr\\n')
'''
    explicit = subprocess.run([interpreter, '-B', '-I', '-S', '-c', code, 'literal $() ; spaces'],
                              env={'LC_ALL': 'C', 'LANG': 'C', 'BOUNDARY_SENTINEL': 'exact'},
                              cwd=WITNESS, input=b'literal\x00input', capture_output=True)
    (WITNESS / 'helper.stdout').write_bytes(explicit.stdout)
    (WITNESS / 'helper.stderr').write_bytes(explicit.stderr)
    assert explicit.returncode == 0
    observed = json.loads(explicit.stdout)
    assert observed['fds'] == [] and observed['stdin'] == b'literal\x00input'.hex()
    assert observed['argv'] == ['literal $() ; spaces']
