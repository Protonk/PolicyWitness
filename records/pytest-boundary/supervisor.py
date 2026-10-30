"""One engine process, publication barrier, resource leases and terminal join.

There is no ordinary case invocation loop. Resource leases last through the
session, including a fixture that never yielded; they are not pytest finalizers.
"""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, checkout_lock, retention, write, read, finish
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import ExitObserver


def close_resource(record_path):
    record = read(record_path)
    Path(record['resource']).unlink()
    Path(record['socket_dir']).rmdir()
    record.update(state='closed', cleanup_basis='kernel_child_exit')
    write(record_path, record)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--python', required=True)
    parser.add_argument('pytest_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    out = retention.bounded_path(ROOT, args.out)
    environment = {k: v for k, v in os.environ.items() if not k.startswith(('PYTHON', 'PYTEST', 'PW_CHECKOUT'))}
    environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
                       PYTHONCOERCECLOCALE='0')
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
    command = [args.python, '-B', '-I', str(Path(__file__).with_name('engine.py')), str(child.fileno()),
               '-c', str(Path(__file__).with_name('pytest.ini'))] + args.pytest_args
    engine = subprocess.Popen(command, env=environment, pass_fds=(child.fileno(),),
                              stdin=subprocess.DEVNULL, start_new_session=True)
    child.close()
    pending, interrupted, selected, scope = [], [], None, None
    published = False
    leases = []
    observer = ExitObserver()

    def interrupt(signum, _frame):
        if not interrupted:
            interrupted.append(time.monotonic())
        try:
            os.killpg(engine.pid, signum)
        except ProcessLookupError:
            pass

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupt)
    with ExitStack() as stack:
        while engine.poll() is None:
            if interrupted and time.monotonic() - interrupted[0] > 1:
                try:
                    os.killpg(engine.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if not select.select([parent], [], [], 0.02)[0]:
                continue
            message = json.loads(parent.recv(65536))
            try:
                if message['op'] == 'selection':
                    selected = message['ids']
                    if not selected or len(selected) != len(set(selected)):
                        raise ValueError('empty or duplicate selection')
                    if message['preview']:
                        parent.send(b'{"op":"eligible"}')
                        continue
                    scope = stack.enter_context(checkout_lock.owned(ROOT, env={}))
                    retention.replacement_allowed(ROOT, out, retention.load_index(ROOT))
                    if out.exists():
                        raise ValueError('candidate requires a fresh output path')
                    out.mkdir(parents=True)
                    started = time.time_ns() // 1_000_000
                    write(out / 'owner.json', dict(schema_version=1, run_id=out.name, out_dir=str(out),
                                                  started_at_unix_ms=started))
                    write(out / 'plan.json', dict(cases=[dict(id=node) for node in selected],
                                                 configuration={'out_dir': str(out)}, command=command))
                    write(out / 'engine.json', dict(pid=engine.pid, supervisor_pid=os.getpid()))
                    (out / 'resources').mkdir()
                    published = True
                    reply = dict(op='eligible', out=str(out), env=scope.child_env({}))
                    socket.send_fds(parent, [json.dumps(reply).encode()], list(scope.pass_fds()))
                elif message['op'] == 'acquire':
                    if scope is None or message['nodeid'] not in selected:
                        raise ValueError('resource request without eligible item')
                    folder = out / 'resources' / str(len(leases))
                    folder.mkdir()
                    record_path = folder / 'record.json'
                    record = dict(state='intent', nodeid=message['nodeid'], nonce=scope.nonce,
                                  lock_inode=os.fstat(scope.fd).st_ino, engine_pid=engine.pid,
                                  resource=str(folder / 'owned'), socket_dir='/private/tmp/pw-py-res-'+uuid.uuid4().hex,
                                  witness=os.environ['BOUNDARY_WITNESS'])
                    write(record_path, record)
                    gate, gated = socket.socketpair()
                    logs = [stack.enter_context((folder / name).open('wb')) for name in ('stdout', 'stderr')]
                    process = subprocess.Popen([args.python, '-B', '-I', str(Path(__file__).with_name('resource_owner.py')),
                               str(gated.fileno()), str(record_path), str(scope.fd)], env=environment,
                               pass_fds=(gated.fileno(), scope.fd), stdin=subprocess.DEVNULL,
                               stdout=logs[0], stderr=logs[1], start_new_session=True)
                    gated.close()
                    observer.watch(process.pid)
                    leases.append((process, record_path))
                    record.update(state='launched', pid=process.pid)
                    write(record_path, record)
                    gate.settimeout(5)
                    gate.sendall(b'g')
                    if gate.recv(1) != b'a':
                        raise RuntimeError('resource acquisition did not acknowledge')
                    gate.close()
                    record.update(state='acquired')
                    write(record_path, record)
                    parent.send(json.dumps(dict(op='acquired', record=str(record_path))).encode())
                else:
                    raise ValueError('unknown control message')
            except Exception as exc:
                pending.append(str(exc))
                parent.send(json.dumps(dict(op='refused', reason=str(exc))).encode())
        code = engine.wait()
        for process, record_path in leases:
            (record_path.parent / 'release').touch()
        if leases:
            try:
                observer.assert_stopped(timeout=5)
                for process, record_path in leases:
                    process.wait(timeout=2)
                    close_resource(record_path)
            except Exception as exc:
                pending.append('cleanup:' + str(exc))
        if published:
            write(out / 'supervisor.json', dict(engine_returncode=code, errors=pending,
                  child_exit_events=sorted(observer.exited), interrupted=bool(interrupted)))
            result = finish(out, code)
            if pending and result == 0:
                run = read(out / 'run.json')
                run['ok'] = False
                run['harness_errors'] += pending
                write(out / 'run.json', run)
                result = 1
        else:
            result = code or (2 if pending else 0)
    observer.close()
    parent.close()
    return result


if __name__ == '__main__':
    raise SystemExit(main())
