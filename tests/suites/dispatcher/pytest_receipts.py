"""Launch failures, group intervention and the shared baseline cause.

Each expectation comes from the stimulus or an independent observer, never from
the receipt under test. Every control runs; failures are reported together.
"""
import errno
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import time
from unittest import mock

import checkout_lock
import pytest_resources as resources
from pytest_support import read, write


def require(value, message):
    if not value:
        raise AssertionError(message)


def closed_without_hold(root, run_id, path):
    record = read(path)
    require(record['state'] == 'closed', 'launch failure left ownership ' + record['state'])
    require(not Path(record['socket_dir']).exists(), 'launch failure left its recovery endpoint')
    require(all(r['blocking'] == 'closed' for r in resources.inspect(root, run_id)), 'launch failure still holds the checkout')
    require(not resources.recover(root, run_id, apply=True)['unresolved'], 'closed launch failure not idempotently recoverable')
    return record


def spawn_failure(control, integration):
    root, out = control.fixture('launch-spawn-failure')
    # The kernel cannot exec a missing path: no native process can exist.
    with checkout_lock.owned(root, env={}) as scope:
        command = resources.Command(root, out, 'spawn', 'fixture/family', 'fixture/family::one',
                                    ['/does-not-exist/native-tool'], out / 'captured', 5, scope, os.getpid())
        try:
            receipt = command.finish()
        except ValueError as exc:
            raise AssertionError('spawn failure was not settled: ' + str(exc))
    record = closed_without_hold(root, 'spawn', command.path)
    require(receipt['never_launched'] is True and receipt['command_pid'] is None and receipt['returncode'] is None,
            'spawn failure receipt claims a launched command')
    require('No such file' in (receipt.get('launch_error') or ''), 'spawn error missing from receipt')
    return dict(record=str(command.path), launch_error=record['settlement']['launch_error'])


def context_refusal(control, integration):
    root, out = control.fixture('launch-context-refusal')
    marker = root.parent / 'refused-command-ran'
    registered = dict(cwd=str(root), environment_sha256='0' * 64, environment_policy='controlled mismatch')
    with checkout_lock.owned(root, env={}) as scope:
        # Only this process registers the altered intent; the owner computes its own.
        with mock.patch.object(resources, 'command_context', return_value=registered):
            command = resources.Command(root, out, 'context', 'fixture/family', 'fixture/family::one',
                                        ['/usr/bin/touch', str(marker)], out / 'captured', 5, scope, os.getpid())
        try:
            receipt = command.finish()
        except ValueError as exc:
            raise AssertionError('owner refusal was not settled: ' + str(exc))
    require(not marker.exists(), 'refused command ran')
    closed_without_hold(root, 'context', command.path)
    require(receipt['never_launched'] is True and 'context differs' in (receipt.get('launch_error') or ''),
            'owner refusal reason missing from receipt')
    return dict(record=str(command.path), marker_absent=True)


def owner_unstarted(control, integration):
    root, out = control.fixture('launch-owner-unstarted')
    real = subprocess.Popen

    def refuse(argv, *args, **kwargs):
        if any(str(a).endswith('pytest_command_owner.py') for a in argv):
            raise OSError(errno.EAGAIN, 'controlled owner spawn refusal')
        return real(argv, *args, **kwargs)
    with checkout_lock.owned(root, env={}) as scope:
        with mock.patch.object(resources.subprocess, 'Popen', side_effect=refuse):
            try:
                resources.Command(root, out, 'owner', 'fixture/family', 'fixture/family::one',
                                  ['/bin/echo', 'never'], out / 'captured', 5, scope, os.getpid())
            except OSError as exc:
                error = str(exc)
            else:
                raise AssertionError('owner spawn refusal not reported')
    paths = resources.record_paths(root, 'owner')
    require(len(paths) == 1 and 'controlled owner spawn refusal' in error, 'owner spawn refusal identity')
    record = closed_without_hold(root, 'owner', paths[0])
    require(record['settlement']['never_launched'] is True and record.get('owner_pid') is None,
            'unstarted owner settlement')
    return dict(record=str(paths[0]), error=error)


def readiness_lost(control, integration):
    root = integration.fixture('launch-readiness-lost')
    out = root / 'tests/out/runs/control'
    out.mkdir(parents=True)
    owner = root / 'tests/lib/pytest_command_owner.py'
    text = owner.read_text()
    anchor = "    gate.sendall(b'ready')"
    require(text.count(anchor) == 1, 'readiness anchor')
    # The supervisor waits five seconds for readiness; this owner is slower.
    owner.write_text(text.replace(anchor, '    time.sleep(7)\n' + anchor))
    marker = root.parent / 'unreleased-command-ran'
    driver = root.parent / 'driver.py'
    driver.write_text('''import json,os,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import checkout_lock
from pytest_resources import Command
root,out=map(Path,sys.argv[2:4])
with checkout_lock.owned(root,env={}) as scope:
    try:
        Command(root,out,'ready','fixture/family','fixture/family::one',['/usr/bin/touch',sys.argv[4]],out/'captured',5,scope,os.getpid())
        print(json.dumps(dict(error=None)))
    except Exception as exc:
        print(json.dumps(dict(error=repr(exc))))
''')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('PW_CHECKOUT', 'PYTHON'))}
    result = subprocess.run([sys.executable, '-B', '-S', str(driver), str(root / 'tests/lib'), str(root), str(out), str(marker)],
                            env=env, capture_output=True, text=True, timeout=30)
    write(root.parent / 'driver.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    require(result.returncode == 0 and '"error": null' not in result.stdout, 'supervisor did not give up on readiness')
    paths = resources.record_paths(root, 'ready')
    require(len(paths) == 1, 'readiness record identity')
    pid = read(paths[0]).get('owner_pid')
    require(type(pid) is int, 'owner identity not bound before readiness')
    queue = select.kqueue()
    try:
        queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                     fflags=select.KQ_NOTE_EXIT)], 0, 0)
        events = queue.control(None, 1, 15)
    finally:
        queue.close()
    require(events and events[0].fflags & select.KQ_NOTE_EXIT, 'slow owner exit not observed')
    require(not marker.exists(), 'unreleased command ran')
    record = read(paths[0])
    require(record.get('settlement', {}).get('never_launched') is True, 'owner left readiness loss unsettled')
    # The supervisor already gave up, so closure is left to public recovery.
    require([r['blocking'] for r in resources.inspect(root, 'ready')] == ['output'], 'settled readiness loss should hold only its output')
    require(not resources.recover(root, 'ready', apply=True)['unresolved'], 'settled readiness loss not recoverable')
    record = closed_without_hold(root, 'ready', paths[0])
    return dict(record=str(paths[0]), owner_pid=pid, launch_error=record['settlement'].get('launch_error'))


def survivor(control, integration):
    root, out = control.fixture('group-survivor')
    directory = Path('/private/tmp') / ('pw-survivor-' + str(os.getpid()))
    directory.mkdir()
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(directory / 'peer')); listener.listen(2); listener.settimeout(10)
    # The leader exits normally after its same-group child is independently identified.
    native = ("import os,socket,sys,time\nchild=os.fork()\ns=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1])\n"
              "s.sendall(b'child' if child==0 else b'leader'); s.recv(1)\nif child==0: time.sleep(30)\n")
    queue = select.kqueue()
    peers, pids, exits = [], {}, {}
    try:
        with checkout_lock.owned(root, env={}) as scope:
            command = resources.Command(root, out, 'survivor', 'fixture/family', 'fixture/family::one',
                                        [sys.executable, '-B', '-S', '-P', '-c', native, str(directory / 'peer')],
                                        out / 'captured', 20, scope, os.getpid())
            while len(pids) < 2:
                peer, _ = listener.accept(); peers.append(peer)
                pid = peer.getsockopt(0, 2); role = peer.recv(16).decode(); pids[role] = pid
                queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC, flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                             fflags=select.KQ_NOTE_EXIT)], 0, 0)
            require(set(pids) == {'child', 'leader'}, 'independent identities missing')
            for role in ('child', 'leader'):
                next(p for p in peers if p.getsockopt(0, 2) == pids[role]).sendall(b'g')
            deadline = time.monotonic() + 15
            while len(exits) < 2 and time.monotonic() < deadline:
                for event in queue.control(None, 2, 1):
                    if event.fflags & select.KQ_NOTE_EXIT:
                        exits[event.ident] = time.monotonic()
            receipt = command.finish()
        require(set(exits) == set(pids.values()), 'leader/child exits not independently observed')
        require(exits[pids['child']] - exits[pids['leader']] < 20, 'child exited on its own schedule')
        require(receipt['returncode'] == 0 and not receipt['timed_out'] and not receipt['cancelled'], 'stimulus did not complete normally')
        require(receipt.get('group_signalled_after_leader_exit') is True,
                'owner killed a surviving group member but published a clean ordinary receipt')
        return dict(record=str(command.path), pids=pids, child_after_leader_s=round(exits[pids['child']] - exits[pids['leader']], 3))
    finally:
        queue.close()
        for peer in peers:
            peer.close()
        listener.close(); (directory / 'peer').unlink(); directory.rmdir()


def integrated_spawn_failure(control, integration):
    from pytest_integration import F, DOMAIN
    # Mixed selection: the family and the independent legacy sentinel.
    root, out, run, family = integration.fault('launch-integrated', DOMAIN, "'/usr/bin/xcrun'", "'/does-not-exist/xcrun'")
    ownership = read(out / 'suites' / F / 'ownership.json')
    require(len(ownership['commands']) == 1 and ownership['commands'][0]['settlement']['never_launched'] is True,
            'family launch failure receipt')
    diagnostic = family['items'][0]['phases']['call']['diagnostic']
    require('not launched' in diagnostic and 'No such file' in diagnostic, 'launch failure not named by the item')
    require(all(i['phases']['setup']['outcome'] == 'failed' and 'call' not in i['phases'] for i in family['items'][1:]),
            'launch failure allowed dependent bodies')
    return dict(output=str(out))


def integrated_survivor(control, integration):
    from pytest_integration import F, DOMAIN
    before = "        run = self.equipment.command([str(output)], directory / 'run', 20)"
    # The leader becomes the real native binary (same ledger); a forked child survives.
    native = "import os,sys,time\nif os.fork()==0:\n    time.sleep(30); os._exit(0)\nos.execv(sys.argv[1],[sys.argv[1]])"
    after = ("        if name == 'production':\n            import sys\n            run = self.equipment.command([sys.executable,'-B','-S','-P','-c',"
             + repr(native) + ",str(output)], directory / 'run', 20)\n        else:\n    " + before)
    root, out, run, family = integration.fault('survivor-integrated', DOMAIN, before, after)
    folder = out / 'suites' / F
    require(read(folder / 'artifacts/production/observed-call-policy.json') == read(root / 'tests/fixtures/worker_lifecycle/exec_call_policy.json')['attempts'],
            'stimulus changed the native ledger')
    diagnostic = family['items'][0]['phases']['call']['diagnostic']
    require('remained after the native command exited' in diagnostic, 'group intervention not named by the item')
    require(all(i['phases']['setup']['outcome'] == 'failed' and 'call' not in i['phases'] for i in family['items'][1:]),
            'credited production despite group intervention')
    require(len(read(folder / 'ownership.json')['commands']) == 2, 'survivor baseline repeated')
    return dict(output=str(out))


def baseline_cause(control, integration):
    from pytest_integration import F
    # A producer that closes a descriptor no pipe created passes native assertions;
    # the ledger reader then cannot normalize it.
    root, out, run, family = integration.fault('baseline-ledger-cause', 'controller/tools/pw_probe_runner/pw_worker_exec.h',
                                               '    slot->exec_valid = 1;', '    (void)close(-1);\n    slot->exec_valid = 1;')
    folder = out / 'suites' / F
    require(family['items'][0]['phases']['call']['outcome'] == 'failed', 'ledger failure did not fail production')
    require(all(i['phases']['setup']['outcome'] == 'failed' and 'call' not in i['phases'] for i in family['items'][1:]),
            'ledger failure allowed dependent bodies')
    require(len(read(folder / 'ownership.json')['commands']) == 2, 'failed baseline was attempted again')
    shared = (folder / 'summary.txt').read_text().splitlines()[1]
    require(shared.startswith('SHARED BASELINE:') and 'KeyError' in shared and 'File exists' not in shared,
            'shared baseline line names a cause other than the ledger failure: ' + shared)
    require('KeyError' in read(folder / 'artifacts/baseline.json')['error'], 'baseline record lost its cause')
    return dict(output=str(out), shared=shared)


CONTROLS = (spawn_failure, context_refusal, owner_unstarted, readiness_lost, survivor,
            integrated_spawn_failure, integrated_survivor, baseline_cause)


def exercise(control, integration):
    failures = []
    for check in CONTROLS:
        try:
            facts = check(control, integration)
        except AssertionError as exc:
            failures.append(dict(control=check.__name__, error=str(exc)))
            print('FAILED:', check.__name__ + ':', exc, flush=True)
        else:
            control.note(check.__name__, **facts)
    write(control.out / 'receipt-controls.json', dict(controls=[c.__name__ for c in CONTROLS], failures=failures))
    if failures:
        raise AssertionError('receipt controls failed: ' + ', '.join(f['control'] for f in failures))
