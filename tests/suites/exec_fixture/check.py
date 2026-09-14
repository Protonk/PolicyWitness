"""Exercise the shared fixture directly, independently of any PW implementation."""
import json
import fcntl
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fixtures" / "exec"))
from control import TreeControl, process_snapshot
from inspection import (ENV_KEY, parse_report, assert_clean, assert_empty_environment,
                        assert_isolated_descriptors, assert_stdin_eof)


def expect_rejection(check, report, message):
    try:
        check(report)
    except AssertionError as error:
        assert message in str(error), str(error)
        print(f"expected rejection: {error}", flush=True)
    else:
        raise AssertionError(f"observer accepted bad state: {message}")


def exercise_inspection(helper, out):
    with tempfile.TemporaryFile() as resource:
        canary = secrets.token_bytes(32)
        resource.write(canary)
        resource.flush()
        high_fd = fcntl.fcntl(resource.fileno(), fcntl.F_DUPFD, 200)
        try:
            for name, dirty_env, dirty_fd, stdin in [
                    ('clean', False, False, b''),
                    ('environment', True, False, b''),
                    ('descriptor', False, True, b''),
                    ('both', True, True, b''),
                    ('excluded_again', False, False, b''),
                    ('stdin_data', False, False, b'X')]:
                nonce = secrets.token_hex(16)
                args = [helper, '--inspect', nonce, '--read-fd', str(high_fd)]
                result = subprocess.run(args, env={ENV_KEY: nonce} if dirty_env else {},
                                        pass_fds=(high_fd,) if dirty_fd else (),
                                        input=stdin, capture_output=True, timeout=5)
                assert result.returncode == 0, result.stderr
                assert result.stderr == f'inspect:{nonce}\n'.encode(), result.stderr
                report = parse_report(result.stdout, nonce, high_fd)
                (out / f'inspect_{name}.json').write_bytes(result.stdout)
                assert report['env_count'] == int(dirty_env), report
                assert report['env_value'] == (nonce if dirty_env else None), report
                if dirty_env:
                    expect_rejection(assert_empty_environment, report, 'inherited environment:')
                else:
                    assert_empty_environment(report)
                if dirty_fd:
                    assert sorted(n for n, _ in report['fds']) == [0, 1, 2, high_fd], report
                    assert report['canary_rc'] == 32 and report['canary_errno'] == 0, report
                    assert report['canary_hex'] == canary.hex(), report
                    expect_rejection(assert_isolated_descriptors, report, 'inherited descriptors:')
                else:
                    assert_isolated_descriptors(report)
                if stdin:
                    assert report['stdin_rc'] == 1, report
                    expect_rejection(assert_stdin_eof, report, 'stdin did not yield EOF:')
                else:
                    assert_stdin_eof(report)
                if not dirty_env and not dirty_fd and not stdin:
                    assert_clean(report)

            # Verify the launch-state witness used by the worker harness:
            # same PID across exec, same environment/resource, unread stdin.
            first, second = secrets.token_hex(16), secrets.token_hex(16)
            args = [helper, '--inspect', first, '--read-fd', str(high_fd), '--then-exec',
                    helper, '--inspect', second, '--read-fd', str(high_fd)]
            with subprocess.Popen(args, env={ENV_KEY: first}, pass_fds=(high_fd,),
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE) as child:
                stdout, stderr = child.communicate(b'X', timeout=5)
                assert child.returncode == 0, stderr
                before_raw, after_raw = stdout.splitlines()
                before = parse_report(before_raw, first, high_fd)
                after = parse_report(after_raw, second, high_fd)
                assert before['pid'] == after['pid'] == child.pid
                assert before['stdin_skipped'] is True and after['stdin_rc'] == 1
                for report in (before, after):
                    assert report['env_value'] == first and report['env_count'] == 1, report
                    assert report['canary_hex'] == canary.hex(), report
                    assert sorted(n for n, _ in report['fds']) == [0, 1, 2, high_fd], report
                assert stderr == f'inspect:{first}\ninspect:{second}\n'.encode()
                (out / 'inspect_forward.jsonl').write_bytes(stdout)
            # Missing/truncated/stale evidence must never become "empty".
            for broken in (b'', b'{}', after_raw[:-2],
                           json.dumps(dict(after, complete=False)).encode(),
                           json.dumps(dict(after, nonce=first)).encode()):
                try:
                    parse_report(broken, second, high_fd)
                except (ValueError, KeyError, AssertionError):
                    pass
                else:
                    raise AssertionError('parser accepted missing, incomplete, or stale evidence')
            print('inspection controls: environment, high FD, stdin, forwarding, and invalid reports verified',
                  flush=True)
        finally:
            os.close(high_fd)


def expect_live(control):
    # Check the exact assertion used by the CLI test, then prove the peers
    # can still execute. An always-successful exit observer must fail here.
    try:
        control.assert_stopped(timeout=0.1)
    except AssertionError as error:
        assert "processes still running:" in str(error), str(error)
        print(f"expected rejection: {error}", flush=True)
    else:
        raise AssertionError("exit observer falsely accepted a live process")
    for role, pid in control.pids.items():
        if pid not in control.exits():
            control.ping(role)


def exercise_tree(helper, out, mode):
    with tempfile.TemporaryDirectory(prefix="pw-fixture-", dir="/private/tmp") as work:
        control = TreeControl(Path(work) / "control")
        child = None
        try:
            child = subprocess.Popen([helper, "--tree", control.path], start_new_session=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={})
            pids = control.accept()
            assert pids['P'] == child.pid, "socket credentials must identify the launched helper"
            groups = {role: os.getpgid(pid) for role, pid in pids.items()}
            assert groups['P'] == groups['C'] == child.pid, (pids, groups)
            assert control.exits() == set(), "fixture exited before the test acted"
            expect_live(control)
            if mode == 'release':
                control.release()
                expected_status = 0
            elif mode == 'group_kill':
                os.killpg(child.pid, signal.SIGKILL)
                expected_status = -signal.SIGKILL
            else:
                # Model a broken cleanup implementation that kills only the
                # leader. Its child retains the pipes and must still respond.
                os.kill(child.pid, signal.SIGKILL)
                assert child.wait(timeout=2) == -signal.SIGKILL
                expect_live(control)
                assert control.exits() == {pids['P']}, control.exits()
                control.ping('C')
                control.release()
                expected_status = -signal.SIGKILL
            control.assert_stopped()
            stdout, stderr = child.communicate(timeout=2)
            assert child.returncode == expected_status, child.returncode
            assert stdout == b'exec_fixture: hello from helper\n' and stderr == b''
            (out / f"{mode}.json").write_text(json.dumps({
                'pids': pids, 'groups': groups, 'exited': sorted(control.exited),
                'returncode': child.returncode,
            }, indent=2) + '\n')
            print(f"{mode}: both peers observed alive and exited; output was not duplicated", flush=True)
        finally:
            control.close()
            if child is not None:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=2)


def exercise_independent_trees(helper, out):
    with tempfile.TemporaryDirectory(prefix='pw-two-trees-', dir='/private/tmp') as work:
        controls = [TreeControl(Path(work) / name) for name in ('a', 'b')]
        children = []
        observations = []
        try:
            for control in controls:
                child = subprocess.Popen([helper, '--tree', control.path], start_new_session=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={})
                children.append(child)
                pids = control.accept()
                assert pids['P'] == child.pid
                leader = process_snapshot(helper, pids['P'])
                descendant = process_snapshot(helper, pids['C'])
                assert leader['ppid'] == os.getpid(), leader
                assert descendant['ppid'] == child.pid, descendant
                assert leader['path'] == descendant['path'] == str(Path(helper).resolve())
                observations.append({'leader': leader, 'child': descendant})
                control.assert_running()
            assert len({pid for control in controls for pid in control.pids.values()}) == 4
            a, b = controls
            b.release()
            b.assert_stopped()
            assert children[1].wait(timeout=2) == 0
            a.assert_running()
            assert process_snapshot(helper, a.pids['P']) == observations[0]['leader']
            assert process_snapshot(helper, a.pids['C']) == observations[0]['child']
            # The same liveness assertion must reject B after its normal exit.
            expect_rejection(lambda control: control.assert_running(), b, 'tree already exited:')
            a.release()
            a.assert_stopped()
            assert children[0].wait(timeout=2) == 0
            for child in children:
                stdout, stderr = child.communicate(timeout=2)
                assert stdout == b'exec_fixture: hello from helper\n' and stderr == b''
            absent = subprocess.run([helper, '--process', str(children[1].pid)],
                                    capture_output=True, timeout=2)
            assert absent.returncode == 2 and absent.stdout == b'', absent
            (out / 'independent_trees.json').write_text(json.dumps(observations, indent=2) + '\n')
            print('independent release: B exited, A still responded with unchanged OS identities', flush=True)
        finally:
            for control in controls:
                control.close()
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=2)


def main():
    helper, out_arg = sys.argv[1:]
    out = Path(out_arg)
    # Prove the generator's exact bytes and statuses independently of PW's
    # capture, including the size used by the truncation test and empty output.
    for count, status in [(None, 0), (0, 37), (4096, 0), (17, 37)]:
        marker = secrets.token_hex(16)
        args = [helper, '--exit', str(status), '--stderr', marker]
        if count is not None:
            args += ['--stdout-bytes', str(count)]
        result = subprocess.run(args, env={}, capture_output=True, timeout=5)
        expected = b'exec_fixture: hello from helper\n' if count is None else b'A' * count
        assert result.returncode == status, result.returncode
        assert result.stdout == expected, result.stdout
        assert result.stderr == (marker + '\n').encode(), result.stderr
        print(f"output bytes={len(expected)}, stderr nonce, exit={status}: correct", flush=True)
    for mode in ('release', 'group_kill', 'leader_kill'):
        exercise_tree(helper, out, mode)
    exercise_independent_trees(helper, out)
    exercise_inspection(helper, out)


if __name__ == '__main__':
    main()
