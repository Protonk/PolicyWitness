"""Bounded, independent-owner experiment for one proposed group boundary.

Run only in the coordinator's allocated execution window, under checkout_lock.
Arguments: fresh absolute output directory. No app bytes are changed. This is
not an app acceptance test or a promise of arbitrary descendant containment.
"""
import hashlib
import errno
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import TreeControl, ExitObserver, process_snapshot


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def read_marker(process, expected):
    assert select.select([process.stdout], [], [], 3)[0], 'marker deadline'
    got = os.read(process.stdout.fileno(), 1)
    assert got == expected, (got, expected)


def identity(value):
    return {k: value[k] for k in ('pid', 'start_sec', 'start_usec', 'path')}


def group_probe(group):
    try:
        os.killpg(group, 0)
        return dict(rc=0, errno=0)
    except OSError as error:
        return dict(rc=-1, errno=error.errno)


def await_exits(observer, required):
    deadline = time.monotonic() + 3
    while not required <= observer.exits(0.05):
        assert time.monotonic() < deadline, ('missing exits', required - observer.exited)


def scenario(out, binary, helper, escape):
    out.mkdir()
    account = dict(state='prepared', cleanup_retained=True, controller_pid=os.getpid(),
                   children={}, helper_pids={}, cleanup_errors=[])
    write(out / 'cleanup.json', account)
    control, observation = TreeControl(out / 'sock'), ExitObserver()
    anchor = worker = None
    anchor_file = worker_file = None
    primary = None
    facts = dict(escape_requested=escape, stage='prepared')
    write(out / 'observations.json', facts)
    try:
        anchor_file = (out / 'anchor.stderr').open('wb')
        anchor = subprocess.Popen([str(binary), 'anchor'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=anchor_file)
        account['children']['anchor'] = anchor.pid
        write(out / 'cleanup.json', account)
        observation.watch(anchor.pid)
        read_marker(anchor, b'A')
        group = os.getpgid(anchor.pid)
        assert group == anchor.pid
        facts.update(anchor=process_snapshot(helper, anchor.pid), group=group,
                     anchor_session=os.getsid(anchor.pid), controller_session=os.getsid(0))
        assert facts['anchor_session'] == facts['controller_session']
        worker_file = (out / 'worker.stderr').open('wb')
        worker = subprocess.Popen([str(binary), 'spawn', str(group), str(helper), control.path],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=worker_file)
        account['children']['worker'] = worker.pid
        write(out / 'cleanup.json', account)
        observation.watch(worker.pid)
        read_marker(worker, b'A')
        facts.update(worker=process_snapshot(helper, worker.pid), worker_session=os.getsid(worker.pid),
                     applied_marker=True, stage='applied_before_spawn')
        assert facts['worker_session'] == facts['anchor_session']
        write(out / 'observations.json', facts)
        worker.stdin.write(b'g'); worker.stdin.flush()
        read_marker(worker, b'S')
        pids = dict(control.accept())
        account['helper_pids'] = pids
        write(out / 'cleanup.json', account)
        control.assert_running()
        peers = {role: process_snapshot(helper, pid) for role, pid in pids.items()}
        groups = {role: os.getpgid(pid) for role, pid in pids.items()}
        assert set(groups.values()) == {group}, groups
        assert peers['P']['ppid'] == worker.pid and peers['C']['ppid'] == pids['P']
        facts.update(stage='spawned_without_identity_publication', native_success_marker=True,
                     child_identity_published=False, peers=peers, groups=groups)
        write(out / 'observations.json', facts)
        if escape:
            peer = control.peers['C']
            peer.sendall(b's')
            assert peer.recv(1) == b'a', 'setsid failed'
            control.ping('C')
            assert identity(process_snapshot(helper, pids['C'])) == identity(peers['C'])
            assert os.getpgid(pids['C']) == os.getsid(pids['C']) == pids['C']
            facts['escaped_group'] = os.getpgid(pids['C'])
            facts['escaped_session'] = os.getsid(pids['C'])
        os.kill(worker.pid, signal.SIGKILL)
        await_exits(observation, {worker.pid})
        assert worker.wait(timeout=1) == -signal.SIGKILL
        control.assert_running()
        facts.update(stage='worker_dead_helpers_live', worker_exit_observed=True)
        write(out / 'observations.json', facts)
        # Anchor is still our unreaped direct child. No numeric group target is
        # used after its wait/reap below. SIGKILL also terminates the anchor.
        assert identity(process_snapshot(helper, anchor.pid)) == identity(facts['anchor'])
        os.killpg(group, signal.SIGKILL)
        await_exits(observation, {anchor.pid, worker.pid})
        await_exits(control.observer, {pids['P']} if escape else set(pids.values()))
        facts.update(stage='group_signal_observed', group_signal=signal.SIGKILL,
                     helper_exit_events=sorted(control.exits()),
                     anchor_exit_observed_before_reap=True,
                     group_probe_with_anchor_unreaped=group_probe(group))
        if escape:
            assert pids['C'] not in control.exits()
            control.ping('C')
            current = process_snapshot(helper, pids['C'])
            assert identity(current) == identity(peers['C'])
            facts['escaped_survivor'] = current
            facts['escaped_survivor_ping'] = True
            control.release()
            control.assert_stopped(timeout=3)
            facts['escaped_exit_after_fixture_release'] = sorted(control.exits())
        else:
            control.assert_stopped(timeout=3)
        # Reaping status belongs to anchor, not to the worker's exec leader.
        assert anchor.wait(timeout=1) == -signal.SIGKILL
        facts['anchor_reaped'] = True
        facts['stage'] = 'complete'
        write(out / 'observations.json', facts)
    except BaseException as error:
        primary = error
        facts['failure'] = repr(error)
        write(out / 'observations.json', facts)
        raise
    finally:
        # The independent controller stays alive when the worker/anchor die.
        # Persist ownership before intervention; release helpers before any
        # PID signal and require exit events, rather than assuming kill worked.
        def attempt(name, action):
            try: return action()
            except BaseException as error:
                account['cleanup_errors'].append(dict(stage=name, error=repr(error)))
        attempt('release_helpers', control.release)
        if anchor is not None and anchor.returncode is None and facts.get('group') == anchor.pid:
            # We have not reaped this direct child, even if it already exited.
            # This also covers a helper created before a failed rendezvous.
            account['group_cleanup_requested'] = anchor.pid
            write(out / 'cleanup.json', account)
            def kill_owned_group():
                try: os.killpg(anchor.pid, signal.SIGKILL)
                except OSError as error:
                    if error.errno != errno.ESRCH: raise
            attempt('kill_owned_group', kill_owned_group)
        if control.observer.pids:
            attempt('helper_exit', lambda: control.observer.assert_stopped(timeout=3))
        for name, child in (('worker', worker), ('anchor', anchor)):
            if child is not None and child.poll() is None:
                attempt('kill_' + name, child.kill)
                attempt('reap_' + name, lambda child=child: child.wait(timeout=3))
        known = set(control.pids) == {'P', 'C'}
        account.update(helper_exit_events=sorted(control.exits()),
                       helper_pids=dict(control.pids),
                       child_exit_events=sorted(observation.exits()),
                       primary_error=None if primary is None else repr(primary))
        all_children = all(c is None or c.returncode is not None for c in (worker, anchor))
        account['cleanup_retained'] = not (known and control.exits() == control.observer.pids and all_children)
        account['state'] = 'cleanup_complete' if not account['cleanup_retained'] else 'cleanup_unconfirmed'
        write(out / 'cleanup.json', account)
        for peer in control.peers.values(): peer.close()
        control.listener.close(); control.observer.close(); observation.close()
        for child in (worker, anchor):
            if child:
                child.stdin.close(); child.stdout.close()
        for stream in (worker_file, anchor_file):
            if stream: stream.close()
        if primary is None:
            assert not account['cleanup_retained'] and not account['cleanup_errors'], account


def main():
    out = Path(sys.argv[1]).resolve()
    assert not out.exists(), 'output must be fresh'
    out.mkdir()
    source = ROOT / 'records/worker-exec-supervision/anchor_probe.c'
    original = ROOT / 'tests/fixtures/exec/helper.c'
    copied = out / 'helper.c'
    fixture = original.read_text()
    needle = "        if (command == 'x') _exit(0);\n"
    replacement = needle + "        if (command == 's') {\n            if (setsid() < 0 || write(fd, \"a\", 1) != 1) break;\n            continue;\n        }\n"
    assert fixture.count(needle) == 1
    copied.write_text(fixture.replace(needle, replacement))
    inputs = [source, Path(__file__), original, ROOT / 'tests/fixtures/exec/control.py']
    write(out / 'source.json', dict(base_commit='503156f0693dd8a22acf633efccdc93e300f2ebc',
          inputs={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
          mutation=dict(source='tests/fixtures/exec/helper.c', needle=needle, replacement=replacement,
                        copied_sha256=hashlib.sha256(copied.read_bytes()).hexdigest())))
    binary, helper = out / 'anchor_probe', out / 'helper'
    commands = []
    for src, dest, extra in ((source, binary, ['-lsandbox']), (copied, helper, [])):
        cmd = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
               '-O2', '-std=c11', str(src), '-o', str(dest), *extra]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        commands.append(dict(command=cmd, rc=result.returncode, stdout=result.stdout, stderr=result.stderr))
        write(out / 'build.json', commands)
        assert result.returncode == 0, result.stderr
    for escape in (False, True):
        scenario(out / ('escaped' if escape else 'same_group'), binary, helper, escape)
    write(out / 'result.json', dict(completed=True, cases=['same_group', 'escaped'],
          meaning='native group-assignment feasibility and controlled boundary; not production acceptance'))
    print(out)


if __name__ == '__main__':
    main()
