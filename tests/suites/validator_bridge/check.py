"""Direct bridge controls: native oracle, query/emission/closure, gate EOF."""
import ctypes
import json
from pathlib import Path
import select
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/validator'))
from gate import Gate, install_bridge
from control import TreeControl


def native(pid, query):
    library = ctypes.CDLL('/usr/lib/libsandbox.dylib', use_errno=True)
    call = library.sandbox_check
    call.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    call.restype = ctypes.c_int
    kind = 1 if query['filter_type'] == 'PATH' else 0
    ctypes.set_errno(0)
    args = [pid, query['operation'].encode(), kind]
    if kind:
        args.append(ctypes.c_char_p(query['filter_value'].encode()))
    result = call(*args)
    return result, ctypes.get_errno()


def assert_silent(process):
    assert process.poll() is None, 'bridge exited while held'
    assert not select.select([process.stdout], [], [], 0)[0], 'stdout before emission gate'


def main():
    bridge, helper, out_arg = sys.argv[1:]
    out = Path(out_arg)
    with tempfile.TemporaryDirectory(prefix='pw-bridge-', dir='/private/tmp') as work:
        work = Path(work)
        allowed, denied = work / 'allowed', work / 'denied'
        allowed.write_bytes(b'allow'); denied.write_bytes(b'deny')
        tree = TreeControl(work / 'tree')
        profile = f'(version 1)(allow default)(deny file-read-data (literal "{denied}"))'
        target = subprocess.Popen(['/usr/bin/sandbox-exec', '-p', profile, helper, '--tree', str(work / 'tree')],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            pid = tree.accept()['P']
            probes = [dict(step_id='query-"é-' + str(i), operation='file-read-data',
                           filter_type='PATH', filter_value=str(path)) for i, path in enumerate((allowed, denied))]
            probes.append(dict(step_id='none', operation='file-read-data', filter_type='NONE'))
            oracle = [native(pid, p) for p in probes]
            assert oracle[0][0] == 0 and oracle[1] == (1, 0), oracle
            (out / 'native-oracle.json').write_text(json.dumps(oracle) + '\n')
            for mode in ('emit', 'close_pending', 'disconnect'):
                gate = Gate(work / ('gate-' + mode))
                # Exercise the sidecar path used by XPC, as well as --gate argv.
                binary = install_bridge(bridge, out / mode, gate.path)
                argv = [str(binary), '--batch', str(pid)]
                if mode == 'close_pending': argv += ['--gate', gate.path]
                process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    process.stdin.write((''.join(json.dumps(p) + '\n' for p in probes)).encode())
                    process.stdin.close()
                    ready = gate.accept()
                    assert ready['target_pid'] == pid and ready['queries'] == 3, ready
                    assert gate.ping() == dict(event='held', closed=False, next=0, pending=False)
                    assert_silent(process)
                    for index, q in enumerate(probes):
                        record = gate.query()
                        assert (record['rc'], record['errno']) == oracle[index], record
                        assert record['outcome'] == ('allow' if oracle[index][0] == 0 else 'deny'), record
                        assert all(record[k] == v for k, v in q.items()), record
                        assert gate.ping()['pending'] is True
                        assert_silent(process)
                        if mode != 'emit': break
                        gate.emit()
                        assert json.loads(process.stdout.readline()) == record
                    if mode == 'emit':
                        assert gate.ping() == dict(event='held', closed=False, next=3, pending=False)
                        assert_silent(process)  # all records sent, collection still open
                        gate.finish()
                    elif mode == 'close_pending':
                        gate.command('c', 'closed')
                        assert process.stdout.read() == b''
                        for command in ('q', 'e'):
                            assert gate.command(command, 'rejected')['reason'] == 'collection_closed'
                        assert gate.ping()['closed'] is True and process.poll() is None
                        gate.peer.sendall(b'x')
                    else:
                        gate.peer.shutdown(socket.SHUT_RDWR)
                    assert process.wait(timeout=3) == 0
                    assert process.stdout.read() == b''
                    assert process.stderr.read() == b''
                finally:
                    gate.save(out / (mode + '-events.json'))
                    gate.close()
                    if process.poll() is None: process.kill()
                    process.wait(timeout=3)
            tree.release(); tree.assert_stopped()
            assert target.wait(timeout=3) == 0
        finally:
            tree.close()
            if target.poll() is None: target.kill()
            target.wait(timeout=3)
    print('bridge: native allow/deny/NONE, emission gate, held EOF, closed gate and disconnect verified')


if __name__ == '__main__':
    main()
