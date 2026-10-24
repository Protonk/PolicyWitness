"""Characterize closed worker stderr without rebuilding or changing the worker.

The case uses a retained copy of the existing direct ABI harness, adding only
an explicit result for its actual waitpid observation. A case-local adapter
closes fd 2 at worker entry. Child descriptor/write observations arrive both
through an independent Unix peer channel and through the worker's result slot.
This is a direct-worker starting-state control, not an XPC launch observation.
"""
import errno
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import ExitObserver


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(argv, log):
    save(log.with_suffix('.command.json'), argv)
    with log.open('wb') as stream:
        subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT,
                       check=True, timeout=60)


def receive(peer):
    peer.settimeout(2)
    raw = b''
    while not raw.endswith(b'\n'):
        block = peer.recv(4096 - len(raw))
        if not block:
            raise AssertionError('observer closed before its complete receipt')
        raw += block
        assert len(raw) < 4096, 'observer receipt exceeded its bound'
    assert raw.count(b'\n') == 1, 'multiple observer records on one connection'
    return raw


def run_case(name, worker, helper, harness, listener, out, case_captures):
    out.mkdir()
    nonce = name + '-' + secrets.token_hex(12)
    argv = [str(harness), str(worker), 'exec_inheritance', str(helper), nonce, '200']
    capture = dict(argv=argv, nonce=nonce, started=False, harness_pid=None, harness_rc=None,
                   kill_group_requested=False, cleanup_errors=[], peers=[], exited=[],
                   expected_peers=4, receipts_received=0, peer_ownership_complete=False,
                   exits_confirmed=False, harness_reaped=False, cleanup_retained=True,
                   primary_error=None)
    case_captures.append(capture)
    save(out / 'capture.json', capture)
    receipts, peers = [], []
    observer = ExitObserver()
    process = None
    primary_error = None
    started = time.monotonic()
    try:
        with (out / 'harness.jsonl').open('wb') as stdout, (out / 'harness.stderr').open('wb') as stderr:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, env={}, start_new_session=True)
            capture['started'] = True
        capture['harness_pid'] = process.pid
        save(out / 'capture.json', capture)
        deadline = started + 15
        while len(receipts) < 4:
            assert time.monotonic() < deadline, 'observer rendezvous deadline expired'
            listener.settimeout(min(.1, max(.001, deadline - time.monotonic())))
            try:
                peer, _ = listener.accept()
            except socket.timeout:
                assert process.poll() is None, 'harness exited before all four observer receipts'
                continue
            peers.append(peer)
            # The PID comes from the kernel, before trusting any JSON field.
            pid = peer.getsockopt(0, 2)  # Darwin SOL_LOCAL / LOCAL_PEERPID
            try:
                observer.watch(pid)
            except BaseException:
                # The source-controlled peer is waiting for our acknowledgement.
                # Kill it while the rendezvous still holds its lifetime.
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError as error:
                    capture['cleanup_errors'].append(f'failed to terminate unregistered peer {pid}: {error}')
                raise
            capture['peers'].append(pid)
            save(out / 'capture.json', capture)
            raw = receive(peer)
            (out / f'peer-{len(receipts)}.json').write_bytes(raw)
            receipt = json.loads(raw)
            assert receipt['pid'] == pid, 'JSON PID differs from LOCAL_PEERPID'
            if not receipts:
                assert receipt['role'] == 'adapter' and receipt['nonce'] == nonce, receipt
                assert receipt['ppid'] == process.pid, receipt
            else:
                assert receipt['role'] == 'child', receipt
                assert receipt['nonce'] == f'{nonce}-{len(receipts) - 1}', receipt
                assert receipt['ppid'] == receipts[0]['pid'], receipt
            receipts.append(receipt)
            peer.sendall(b'g')
            peer.close()
        capture['harness_rc'] = process.wait(timeout=max(.1, deadline - time.monotonic()))
        observer.assert_stopped(timeout=2)
        assert capture['harness_rc'] == 0, capture
        lines = (out / 'harness.jsonl').read_text().splitlines()
        assert len(lines) == 2, f'expected worker-entry receipt and harness result, got {len(lines)} lines'
        entry, result = map(json.loads, lines)
        save(out / 'worker-entry.json', entry)
        save(out / 'worker-result.json', result)
        assert entry['role'] == 'worker_entry' and entry['nonce'] == nonce, entry
        assert entry['pid'] == receipts[0]['pid'] == result['worker_pid'], (entry, result)
        assert entry['ppid'] == process.pid, entry
        assert entry['close_requested'] is (name == 'closed'), entry
        assert entry['close_rc'] == 0 and entry['close_errno'] == 0, entry
        before = {s['fd']: s for s in entry['before']}
        after = {s['fd']: s for s in entry['after']}
        assert set(before) == set(after) == set(range(5)), entry
        assert all(s['flags'] >= 0 and s['stat_rc'] == 0 for s in before.values()), entry
        assert stat.S_ISFIFO(before[0]['mode']) and stat.S_ISFIFO(before[4]['mode']), entry
        assert before[3]['size'] > 0, 'evidence descriptor has no sized backing object'
        for fd in (0, 1, 3, 4):
            assert before[fd] == after[fd], f'protocol/stdout descriptor {fd} changed'
        if name == 'closed':
            assert after[2]['flags'] == -1 and after[2]['flags_errno'] == errno.EBADF, entry
            assert after[2]['stat_rc'] == -1 and after[2]['stat_errno'] == errno.EBADF, entry
        else:
            assert before[2] == after[2], entry
        assert result['scenario'] == 'exec_inheritance', result
        assert result['ready_byte_received'] and result['applied'] and result['done'], result
        assert result['apply_rc'] == 0 and result['failure_published'] == 0, result
        assert result['proceed_set'] and result['proceed_observed'] == 1, result
        assert result['worker_reaped'] is True, 'harness did not actually reap its worker'
        assert result['exit_code'] == 0 and result['term_signal'] is None and not result['sent_sigkill'], result
        assert result['policy_read_published'] == 1, result
        assert (result['policy_bytes_received'] == result['policy_bytes_expected']
                == result['header_bytes_expected'] == result['policy_bytes_written']), result
        assert len(result['slots']) == 3, result
        for i, slot in enumerate(result['slots']):
            assert slot['step_id'] == f'inspect_{i}' and slot['completed'] == 1, slot
            assert slot['rc'] == 0 and slot['errno'] == 0 and not slot['error'], slot
            assert slot['child_exit_code'] == 0 and slot['child_term_signal'] == 0, slot
            native = receipts[i + 1]
            assert slot['child_pid'] == native['pid'], (slot, native)
            assert json.loads(slot['stdout']) == native, 'worker publication differs from independent receipt'
            marker = f'stderr:{nonce}-{i}\n'
            assert native['write_expected'] == len(marker.encode()), native
            if name == 'closed':
                assert native['fd2_flags'] == -1 and native['fd2_errno'] == errno.EBADF, native
                assert native['fd2_stat_rc'] == -1 and native['fd2_stat_errno'] == errno.EBADF, native
                assert native['write_rc'] == -1 and native['write_errno'] == errno.EBADF, native
                assert slot['stderr'] == '', slot
            else:
                assert native['fd2_flags'] >= 0 and native['fd2_errno'] == 0, native
                assert native['fd2_stat_rc'] == 0 and native['fd2_stat_errno'] == 0, native
                assert stat.S_ISFIFO(native['fd2_mode']), native
                assert native['write_rc'] == native['write_expected'] and native['write_errno'] == 0, native
                assert slot['stderr'] == marker, slot
        save(out / 'observations.json', dict(worker_entry=entry, children=receipts[1:],
             interpretation='direct worker starting-state characterization; not an XPC launch observation'))
        return dict(case=name, worker_pid=result['worker_pid'], child_pids=[r['pid'] for r in receipts[1:]])
    except BaseException as error:
        primary_error = error
        capture['primary_error'] = repr(error)
        raise
    finally:
        # Release any connected observer first, then clean up known processes.
        # Registered exit events keep observed exits separate from kill requests.
        for peer in peers:
            try:
                peer.sendall(b'q')
            except OSError:
                pass
            except BaseException as error:
                capture['cleanup_errors'].append(f'peer release: {error}')
            try:
                peer.close()
            except BaseException as error:
                capture['cleanup_errors'].append(f'peer close: {error}')
        try:
            if process is not None and process.poll() is None:
                capture['kill_group_requested'] = True
                os.killpg(process.pid, signal.SIGKILL)
                capture['harness_rc'] = process.wait(timeout=5)
            deadline = time.monotonic() + 2
            while observer.pids - observer.exits() and time.monotonic() < deadline:
                observer.exits(.05)
            for pid in observer.pids - observer.exits():
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if observer.pids:
                observer.assert_stopped(timeout=3)
            observer.exits()
        except BaseException as error:
            capture['cleanup_errors'].append(str(error))
        finally:
            try:
                if process is not None:
                    capture['harness_rc'] = process.poll()
            except BaseException as error:
                capture['cleanup_errors'].append(f'harness reap observation: {error}')
            capture['exited'] = sorted(observer.exited)
            capture['receipts_received'] = len(receipts)
            capture['registered_peers'] = sorted(observer.pids)
            capture['peer_ownership_complete'] = len(receipts) == len(observer.pids) == capture['expected_peers']
            capture['exits_confirmed'] = (capture['peer_ownership_complete']
                                          and observer.exited == observer.pids)
            capture['harness_reaped'] = process is None or process.returncode is not None
            try:
                observer.close()
            except BaseException as error:
                capture['cleanup_errors'].append(f'exit observer close: {error}')
            capture['cleanup_retained'] = bool(capture['cleanup_errors']) or (
                capture['started'] and not (capture['peer_ownership_complete']
                                            and capture['exits_confirmed'] and capture['harness_reaped']))
            capture['elapsed_seconds'] = time.monotonic() - started
            try:
                save(out / 'capture.json', capture)
            except BaseException as error:
                capture['cleanup_errors'].append(f'capture persistence: {error}')
                capture['cleanup_retained'] = True
                if primary_error is None:
                    raise
        if capture['cleanup_retained'] and primary_error is None:
            raise AssertionError(f'unconfirmed owned-process cleanup: {capture}')


def main():
    worker, out = map(lambda p: Path(p).resolve(), sys.argv[1:])
    assert worker.is_file() and os.access(worker, os.X_OK), 'built worker is missing'
    out.mkdir(parents=True, exist_ok=True)
    equipment = out / 'equipment'
    equipment.mkdir()
    workspace = Path(tempfile.mkdtemp(prefix='pw-closed-stderr-', dir='/private/tmp'))
    owner = dict(path=str(workspace), creator_pid=os.getpid(), cleanup_retained=True,
                 primary_error=None, cleanup_errors=[])
    save(out / 'workspace-owner.json', owner)
    worker_before = digest(worker)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    complete_cleanup = True
    primary_error = None
    case_captures = []
    try:
        socket_path = workspace / 'control'
        listener.bind(str(socket_path))
        listener.listen(8)
        abi = equipment / 'abi'
        abi.mkdir()
        abi_headers = sorted((ROOT / 'controller/tools/pw_probe_runner').glob('*.h'))
        assert abi_headers, 'no ABI header inputs found'
        # The harness also includes the first-touch probe header kept beside the
        # worker_lifecycle fixtures; copy it into the same include directory.
        probe_header = ROOT / 'tests/fixtures/worker_lifecycle/first_touch_probe.h'
        headers = abi_headers + [probe_header]
        for path in headers:
            shutil.copy2(path, abi / path.name)
        original = ROOT / 'tests/suites/runner_c_worker_harness/harness.c'
        original_bytes = original.read_bytes()
        source = original_bytes.decode()
        (equipment / 'harness.original.c').write_bytes(original_bytes)
        anchor = '    printf(",\\\"worker_pid\\\":%d", pid);'
        anchor_matches = source.count(anchor)
        assert anchor_matches == 1, 'harness reap observation anchor changed; review adaptation'
        source = source.replace(anchor, anchor + '\n    printf(",\\\"worker_reaped\\\":%s", reaped == pid ? "true" : "false");', 1)
        harness_source = equipment / 'harness.c'
        harness_source.write_text(source)
        observer_source = equipment / 'closed_worker_stderr_observer.c'
        shutil.copy2(HERE / observer_source.name, observer_source)
        shutil.copy2(ROOT / 'tests/fixtures/exec/control.py', equipment / 'control.py')
        config = equipment / 'closed_worker_stderr_config.h'
        config.write_text('#define PW_CLOSED_STDERR_SOCKET ' + json.dumps(str(socket_path)) + '\n')
        copies = [(original, equipment / 'harness.original.c'),
                  (HERE / observer_source.name, observer_source),
                  (ROOT / 'tests/fixtures/exec/control.py', equipment / 'control.py')]
        copies += [(path, abi / path.name) for path in headers]
        copied_inputs = [dict(source=str(source_path), copy=str(copy_path.relative_to(equipment)),
                             source_sha256=digest(source_path), copy_sha256=digest(copy_path))
                         for source_path, copy_path in copies]
        assert all(item['source_sha256'] == item['copy_sha256'] for item in copied_inputs), 'input copy changed bytes'
        input_counts = dict(original_harness=1, adapted_harness=1, observer_adapter_source=1,
                            shared_exit_observer=1, abi_headers=len(abi_headers), harness_probe_header=1,
                            generated_config=1,
                            harness_reap_anchor_matches=anchor_matches, harness_reap_replacements=1)
        save(equipment / 'inputs.json', dict(counts=input_counts, copied_inputs=copied_inputs,
             adapted_harness_sha256=digest(harness_source), config_sha256=digest(config)))
        harness, helper = workspace / 'harness', workspace / 'observer'
        assert len(str(helper).encode()) < 128, 'observer path exceeds the worker argv bound'
        common = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror', '-O2', '-std=c11']
        build([*common, '-I', str(abi), str(harness_source), '-o', str(harness)], equipment / 'harness-build.log')
        build([*common, str(observer_source), '-o', str(helper)], equipment / 'observer-build.log')
        shutil.copy2(harness, equipment / 'harness')
        shutil.copy2(helper, equipment / 'observer')
        save(equipment / 'manifest.json', dict(worker_path=str(worker), worker_sha256=worker_before,
             harness_source=str(original), original_harness_sha256=digest(original),
             input_counts=input_counts,
             adaptation='only emit whether waitpid returned the worker PID',
             files={str(p.relative_to(equipment)): digest(p) for p in sorted(equipment.rglob('*')) if p.is_file()}))
        summaries = []
        for name in ('baseline', 'closed'):
            summaries.append(run_case(name, worker, helper, harness, listener, out / name, case_captures))
        save(out / 'summary.json', dict(cases=summaries, worker_unchanged=digest(worker) == worker_before,
             result='baseline stderr works; closed-entry children independently report EBADF'))
        assert digest(worker) == worker_before, 'shipped worker bytes changed'
        print('paired direct-worker control: baseline stderr writes succeed; closed-entry child fd 2 and writes report EBADF')
    except BaseException as error:
        primary_error = error
        owner['primary_error'] = repr(error)
        raise
    finally:
        try:
            listener.close()
        except BaseException as error:
            owner['cleanup_errors'].append(f'listener close: {error}')
            complete_cleanup = False
        # A spelling census is supplementary only. It can reveal an unexpected
        # process, but cannot discharge missing peer ownership or exit evidence.
        # An observer's self-deadline likewise does not prove its observed exit.
        helper_path = str(workspace / 'observer')
        leftovers = []
        owner['case_cleanup'] = case_captures
        try:
            listing = subprocess.run(['/bin/ps', '-wwaxo', 'pid=,args='], capture_output=True,
                                     text=True, timeout=3, check=True).stdout
            leftovers = [line for line in listing.splitlines()
                         if len(line.strip().split(None, 1)) == 2
                         and line.strip().split(None, 1)[1].startswith(helper_path + ' --inspect ')]
            save(out / 'processes-after.json', dict(helper_path=helper_path, matches=leftovers))
            for capture in case_captures:
                if capture['cleanup_retained'] or (capture['started'] and not (
                        capture['peer_ownership_complete'] and capture['exits_confirmed']
                        and capture['harness_reaped'])):
                    complete_cleanup = False
            if leftovers:
                complete_cleanup = False
            owner.update(observer_processes_after=leftovers, case_cleanup=case_captures,
                         children_confirmed=complete_cleanup,
                         worker_sha256_after=digest(worker))
            if complete_cleanup:
                shutil.rmtree(workspace)
                owner.update(cleanup_retained=False, absent=not workspace.exists())
        except BaseException as error:
            owner['cleanup_errors'].append(str(error))
            complete_cleanup = False
        if not complete_cleanup:
            owner['cleanup_retained'] = True
            owner['children_confirmed'] = False
        try:
            save(out / 'workspace-owner.json', owner)
        except BaseException:
            if primary_error is None:
                raise
        if not complete_cleanup and primary_error is None:
            raise AssertionError(f'cleanup unconfirmed; retain {workspace} and {out / "workspace-owner.json"}')


if __name__ == '__main__':
    main()
