"""Run synthetic inner suites through the pytest host inside fixture repositories; judge the outer evidence.

Every live control runs the public command in a disposable repository whose
one case starts tests/lib/pytest_host.py on an inner test file written here.
What each control establishes is read from the outer evidence: the command's
exit, run.json, the case report and events, the retained assertions log and
receipt, the absence of scratch, and marker files the inner tests write on
body entry. Constructed receipts establish the judge's reading of each rule
separately from execution, including the one no live run can produce: a
pytest module path outside the vendored directory.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import textwrap
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
from repository import install_runner  # noqa: E402
from control import ExitObserver, TreeControl  # noqa: E402
import pytest_host  # noqa: E402

PYTHON = sys.executable
CASE_SCRIPT = textwrap.dedent('''\
    #!/usr/bin/env bash
    set -euo pipefail
    ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
    source "${ROOT_DIR}/tests/lib/case.sh"
    test_begin host inner
    test_step pytest "run the inner suite through the pytest host"
    # shellcheck disable=SC2086
    test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "inner suite failed" \\
      "${ROOT_DIR}/tests/lib/pytest_host.py" --receipt "${PW_TEST_ARTIFACTS}/receipt.jsonl" ${CONTROL_HOST_ARGS:-} -- \\
      "${ROOT_DIR}/tests/inner/test_inner.py"
    test_pass "inner suite passed"
    ''')
MARKER = textwrap.dedent('''\
    import os
    def marker(name):
        with open(os.path.join(os.environ['CONTROL_MARKERS'], name), 'w') as stream:
            stream.write(name)
    ''')
# The rendezvous the cancellation fixture uses: connect, send a role, answer pings, leave on release.
RENDEZVOUS = textwrap.dedent('''\
    import os, socket
    def rendezvous(role):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
            peer.connect(os.environ['CONTROL_SOCKET'])
            peer.sendall(role)
            while True:
                command = peer.recv(1)
                if command == b'p':
                    peer.sendall(b'a')
                elif command in (b'q', b''):
                    return
    ''')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def fixture_repository(work, *, version=None):
    """A disposable repository with the runner, the pytest host and one case that runs the inner file."""
    repo = work / 'fixture repo'
    install_runner(ROOT, repo, {'host': {'command': ['bash', 'tests/suites/host/run.sh'], 'cases': ['inner']}},
                   pytest_host=True)
    script = repo / 'tests/suites/host/run.sh'
    script.parent.mkdir(parents=True)
    script.write_text(CASE_SCRIPT)
    script.chmod(0o755)
    (repo / 'tests/inner').mkdir()
    if version is not None:
        versioned = repo / 'tests/lib/vendor/_pytest/_version.py'
        versioned.write_text(versioned.read_text().replace(repr(pytest_host.PYTEST_PIN), repr(version)))
    return repo


class Outcome:
    """The outer evidence of one public-command run in a fixture repository."""

    def __init__(self, work, repo, result):
        self.work, self.repo, self.result = work, repo, result
        out = repo / 'tests/out/runs/default'
        self.out = out
        self.run = json.loads((out / 'run.json').read_text()) if (out / 'run.json').exists() else None
        case = out / 'suites/host/inner'
        self.report = json.loads((case / 'report.json').read_text()) if (case / 'report.json').exists() else None
        self.events = [json.loads(line) for line in (case / 'events.jsonl').read_text().splitlines()] \
            if (case / 'events.jsonl').exists() else []
        self.log = (case / 'artifacts/assertions.log').read_text(errors='replace') \
            if (case / 'artifacts/assertions.log').exists() else ''
        self.receipt = pytest_host.read_receipt(case / 'artifacts/receipt.jsonl') \
            if (case / 'artifacts/receipt.jsonl').exists() else None
        self.scratch_absent = not os.path.lexists(case / 'scratch')
        self.markers = sorted(p.name for p in (work / 'markers').iterdir())

    def reports(self, when=None, subtest=False):
        return [e for e in (self.receipt or []) if e['event'] == 'report' and bool(e.get('subtest')) == subtest
                and (when is None or e['when'] == when)]


def run_case(name, out, inner, *, host_args='', env_extra=None, files=None, version=None, timeout=60):
    """Run the fixture repository's one case through the public command and gather the outer evidence."""
    work = out / name
    repo = fixture_repository(work, version=version)
    (repo / 'tests/inner/test_inner.py').write_text(MARKER + textwrap.dedent(inner))
    for relative, text in (files or {}).items():
        (repo / 'tests/inner' / relative).write_text(textwrap.dedent(text))
    markers = work / 'markers'
    markers.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('PW_', 'PYTEST'))}
    env.update(PW_TEST_OUT_DIR=str(repo / 'tests/out/runs/default'), PW_TEST_RUN_ID=f'control_{name}',
               PYTHONDONTWRITEBYTECODE='1', CONTROL_HOST_ARGS=host_args, CONTROL_MARKERS=str(markers),
               **(env_extra or {}))
    result = subprocess.run(['bash', str(repo / 'tests/run.sh'), '--case', 'host/inner'], env=env, cwd=work,
                            capture_output=True, timeout=timeout)
    (work / 'stdout').write_bytes(result.stdout)
    (work / 'stderr').write_bytes(result.stderr)
    (work / 'exit.json').write_text(json.dumps({'returncode': result.returncode, 'host_args': host_args}) + '\n')
    return Outcome(work, repo, result)


def expect_outer(outcome, *, passed, rule=None, markers=None):
    """The outer evidence of a passed or failed case, with the first refused rule named in the log."""
    name = outcome.work.name
    require(outcome.result.returncode == (0 if passed else 1), f'{name}: exit {outcome.result.returncode}')
    require(outcome.run is not None and outcome.run['ok'] is passed, f'{name}: run.json ok disagrees')
    require(outcome.run['counts'] == {'pass': 1 if passed else 0, 'fail': 0 if passed else 1, 'skip': 0, 'total': 1},
            f'{name}: counts {outcome.run["counts"]}')
    require(not outcome.run['harness_errors'] or not passed, f'{name}: harness errors {outcome.run["harness_errors"]}')
    require(outcome.report is not None and outcome.report['status'] == ('pass' if passed else 'fail'),
            f'{name}: report {outcome.report}')
    steps = [(e['step'], e['status']) for e in outcome.events]
    require(steps[0] == ('test_start', 'start') and steps[-1] == ('test_end', 'pass' if passed else 'fail')
            and sum(s == 'test_start' for s, _ in steps) == 1 and sum(s == 'test_end' for s, _ in steps) == 1,
            f'{name}: events {steps}')
    require(outcome.scratch_absent, f'{name}: scratch remains')
    if rule is not None:
        require(f'pytest host refused: {rule}:' in outcome.log, f'{name}: the log does not name {rule} first:\n{outcome.log[-1500:]}')
    if markers is not None:
        require(outcome.markers == sorted(markers), f'{name}: markers {outcome.markers}, expected {sorted(markers)}')


def reporting_controls(out):
    inventory = []

    def control(name, inner, *, passed, rule=None, markers=None, host_args='', files=None, check=None):
        outcome = run_case(name, out, inner, host_args=host_args, files=files)
        expect_outer(outcome, passed=passed, rule=rule, markers=markers)
        if check is not None:
            check(outcome)
        inventory.append(name)
        print(f'{name}: ok', flush=True)
        return outcome

    def three_passed(outcome):
        require([(r['when'], r['outcome']) for r in outcome.reports()] == [('setup', 'passed'), ('call', 'passed'), ('teardown', 'passed')],
                f'{outcome.work.name}: item reports {outcome.reports()}')
        require([e['event'] for e in outcome.receipt][-1] == 'session_finish', f'{outcome.work.name}: no finish')

    control('passing', '''
        def test_passes():
            marker('body')
        ''', passed=True, markers=['body'], host_args='--expect-collected 1', check=three_passed)
    control('failing_body', '''
        def test_fails():
            marker('body')
            assert False, 'deliberate'
        ''', passed=False, rule='child_exit', markers=['body'],
            check=lambda o: require([r['outcome'] for r in o.reports('call')] == ['failed'], 'call not failed'))
    control('testcase_setup_error', '''
        import unittest
        class Case(unittest.TestCase):
            def setUp(self):
                raise RuntimeError('setUp refuses')
            def test_body(self):
                marker('body')
        ''', passed=False, rule='child_exit', markers=[],
            check=lambda o: require([r['outcome'] for r in o.reports('call')] == ['failed'],
                                    'a TestCase setUp error is reported in the call phase'))
    control('fixture_setup_error', '''
        import pytest
        @pytest.fixture
        def broken():
            raise RuntimeError('fixture refuses')
        def test_body(broken):
            marker('body')
        ''', passed=False, rule='child_exit', markers=[],
            check=lambda o: require([r['outcome'] for r in o.reports('setup')] == ['failed'] and not o.reports('call'),
                                    'setup must fail with no call report'))
    control('teardown_error', '''
        import pytest
        @pytest.fixture
        def tidy():
            yield
            raise RuntimeError('teardown refuses')
        def test_body(tidy):
            marker('body')
        ''', passed=False, rule='child_exit', markers=['body'],
            check=lambda o: require([r['outcome'] for r in o.reports('call')] == ['passed']
                                    and [r['outcome'] for r in o.reports('teardown')] == ['failed'],
                                    'a passing body with a failing teardown must show both'))
    control('body_and_teardown_error', '''
        import pytest
        @pytest.fixture
        def tidy():
            yield
            raise RuntimeError('teardown refuses')
        def test_body(tidy):
            marker('body')
            assert False, 'body refuses'
        ''', passed=False, rule='child_exit', markers=['body'],
            check=lambda o: require([r['outcome'] for r in o.reports('call')] == ['failed']
                                    and [r['outcome'] for r in o.reports('teardown')] == ['failed'],
                                    'both faults must remain visible'))
    control('empty_file', '''
        CONSTANT = 1
        ''', passed=False, rule='child_exit', markers=[],
            check=lambda o: require('child_exit: the pytest child exited 5' in o.log and 'collected: nothing was collected' in o.log,
                                    'exit 5 and an empty collection must both be named'))
    control('deselect_all', '''
        def test_body():
            marker('body')
        ''', passed=False, rule='child_exit', markers=[], host_args='--pytest-arg=-k --pytest-arg=nomatch',
            check=lambda o: require('deselected: 1 items were deselected' in o.log, 'deselection must be named'))
    control('skip', '''
        import pytest
        @pytest.mark.skip(reason='declared nowhere')
        def test_body():
            marker('body')
        ''', passed=False, rule='item_reports', markers=[],
            check=lambda o: require('setup skipped' in o.log and 'child_exit' not in o.log.split('refused:')[1].splitlines()[0],
                                    'a skip exits 0 and is refused by the receipt alone'))
    control('bad_option', '''
        def test_body():
            marker('body')
        ''', passed=False, rule='child_exit', markers=[], host_args='--pytest-arg=--no-such-option',
            check=lambda o: require('exited 4' in o.log, 'a usage error exits 4'))
    control('syntax_error', '''
        def test_body(:
            marker('body')
        ''', passed=False, rule='child_exit', markers=[],
            check=lambda o: require('exited 2' in o.log and any(e['event'] == 'collect_error' for e in o.receipt),
                                    'a collection error exits 2 and is recorded'))
    return inventory


def receipt_controls(out):
    inventory = []

    def control(name, inner, *, passed, rule, markers, host_args='', env_extra=None, check=None, version=None):
        outcome = run_case(name, out, inner, host_args=host_args, env_extra=env_extra, version=version)
        expect_outer(outcome, passed=passed, rule=rule, markers=markers)
        if check is not None:
            check(outcome)
        inventory.append(name)
        print(f'{name}: ok', flush=True)

    plain = '''
        def test_body():
            marker('body')
        '''
    control('collect_only', plain, passed=False, rule='item_reports', markers=[], host_args='--pytest-arg=--collect-only',
            check=lambda o: require('child_exit' not in o.log and not o.reports() and len(o.receipt) >= 3,
                                    'collection alone exits 0, collects, and leaves no item report'))
    control('setup_only', plain, passed=False, rule='item_reports', markers=[], host_args='--pytest-arg=--setup-only',
            check=lambda o: require('0 call reports' in o.log and o.reports('setup') and o.reports('teardown'),
                                    'setup only leaves no call report'))
    control('os_exit', '''
        import os
        def test_body():
            marker('body')
            os._exit(0)
        ''', passed=False, rule='session_finish', markers=['body'],
            check=lambda o: require('child_exit' not in o.log.split('refused:')[1].splitlines()[0]
                                    and not any(e['event'] == 'session_finish' for e in o.receipt),
                                    'an exit 0 without a finish line is refused'))
    control('killed_child', '''
        import os, signal
        def test_body():
            marker('body')
            os.kill(os.getpid(), signal.SIGKILL)
        ''', passed=False, rule='child_exit', markers=['body'],
            check=lambda o: require('exited -9 (a signal)' in o.log, 'a killed child is named with its signal'))
    control('early_stop', '''
        def test_first():
            marker('first')
            assert False, 'stop here'
        def test_second():
            marker('second')
        ''', passed=False, rule='child_exit', markers=['first'], host_args='--pytest-arg=-x',
            check=lambda o: require('test_second: 0 setup reports' in o.log, 'the unreached item must be named'))
    control('env_addopts', plain, passed=False, rule=None, markers=[], env_extra={'PYTEST_ADDOPTS': '--collect-only'},
            check=lambda o: require('pytest_environment_set: PYTEST_ADDOPTS set' in o.log and o.receipt is None,
                                    'an inherited PYTEST_ADDOPTS is refused before pytest starts'))
    control('env_plugins', plain, passed=False, rule=None, markers=[], env_extra={'PYTEST_PLUGINS': 'os'},
            check=lambda o: require('pytest_environment_set: PYTEST_PLUGINS set' in o.log and o.receipt is None,
                                    'an inherited PYTEST_PLUGINS is refused before pytest starts'))
    control('version_pin', plain, passed=False, rule='pytest_version', markers=['body'], version='9.1.1+local',
            check=lambda o: require("pytest '9.1.1+local' ran; the vendored pin is 9.1.1" in o.log, 'the pin is named'))
    return inventory


def configuration_controls(out):
    inventory = []
    outcome = run_case('conftest_ignored', out, '''
        def test_body():
            marker('body')
        ''', files={'conftest.py': '''
        import os
        with open(os.path.join(os.environ['CONTROL_MARKERS'], 'conftest'), 'w') as stream:
            stream.write('imported')
        def pytest_collection_modifyitems(items):
            items.clear()
        '''})
    expect_outer(outcome, passed=True, markers=['body'])
    inventory.append('conftest_ignored')
    print('conftest_ignored: ok', flush=True)
    outcome = run_case('ini_ignored', out, '''
        def test_body():
            marker('body')
        ''', files={'pytest.ini': '''
        [pytest]
        addopts = --collect-only
        '''})
    expect_outer(outcome, passed=True, markers=['body'])
    require(len(outcome.reports()) == 3, 'an ini file beside the inner file must not add arguments')
    inventory.append('ini_ignored')
    print('ini_ignored: ok', flush=True)
    return inventory


def lock_admission_control(out):
    outcome = run_case('lock_admission', out, '''
        import os, sys
        sys.path.insert(0, os.path.join(os.environ['CONTROL_REPO'], 'tests/lib'))
        import checkout_lock
        def test_admitted_under_the_inherited_claim():
            fds = checkout_lock.inherited_fds()
            assert len(fds) == 2, fds
            admission = checkout_lock.admit(os.environ['CONTROL_REPO'])
            assert admission.nonce == os.environ[checkout_lock.ENV_NONCE]
            admission.close()
            marker('admitted')
        ''', env_extra={'CONTROL_REPO': str(out / 'lock_admission/fixture repo')})
    expect_outer(outcome, passed=True, markers=['admitted'])
    print('lock_admission: ok', flush=True)
    return ['lock_admission']


def lock_free(repo):
    """Whether the lock can be taken now, observed with a separate open from outside every owner."""
    fd = os.open(repo / 'tests/.checkout.lock', os.O_RDWR)
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False
    finally:
        os.close(fd)


def parent_of(pid):
    text = subprocess.run(['/bin/ps', '-o', 'ppid=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
    return int(text) if text else None


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def lifetime(out, mode):
    """Kill the fixture dispatcher, the case shell and the launcher parent while the inner child waits; what a separate open sees."""
    name = f'lock_lifetime_{mode}'
    work = out / name
    repo = fixture_repository(work)
    (repo / 'tests/inner/test_inner.py').write_text(MARKER + RENDEZVOUS + textwrap.dedent('''
        import json, os, socket, subprocess, sys
        def test_waits_for_release():
            marker('waiting')
            helper = subprocess.Popen([sys.executable, '-B', '-S', '-P', '-c',
                                       'import os, signal, socket\\n' + RENDEZVOUS_SOURCE + 'rendezvous(b"C")'])
            rendezvous(b'P')
            helper.wait(timeout=5)
        ''').replace('RENDEZVOUS_SOURCE', repr(RENDEZVOUS)))
    markers = work / 'markers'
    markers.mkdir()
    observed = {'mode': mode}
    with tempfile.TemporaryDirectory(prefix='pw-host-lifetime-', dir='/private/tmp') as socket_dir:
        tree = TreeControl(Path(socket_dir) / 'gate')
        holders = ExitObserver()
        env = {key: value for key, value in os.environ.items() if not key.startswith(('PW_', 'PYTEST'))}
        env.update(PW_TEST_OUT_DIR=str(repo / 'tests/out/runs/default'), PW_TEST_RUN_ID=name, PYTHONDONTWRITEBYTECODE='1',
                   CONTROL_HOST_ARGS='--drop-claim-descriptors' if mode == 'drop' else '', CONTROL_MARKERS=str(markers),
                   CONTROL_SOCKET=tree.path)
        process = None
        try:
            with (work / 'stdout').open('wb') as stdout, (work / 'stderr').open('wb') as stderr:
                process = subprocess.Popen(['bash', str(repo / 'tests/run.sh'), '--case', 'host/inner'], cwd=work, env=env,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                peers = tree.accept()
                tree.assert_running()
                child = peers['P']
                launcher = parent_of(child)
                shell = parent_of(launcher)
                require(parent_of(shell) == process.pid, f'the case shell {shell} is not the dispatcher\'s child')
                observed.update(dispatcher=process.pid, shell=shell, launcher=launcher, child=child, helper=peers['C'])
                observed['held_while_waiting'] = not lock_free(repo)
                for pid in (process.pid, shell, launcher):
                    holders.watch(pid)
                for pid in (process.pid, shell, launcher):
                    os.kill(pid, signal.SIGKILL)
                holders.assert_stopped(timeout=5)
                process.wait(timeout=5)
                tree.assert_running()
                observed['child_alive_after_kills'] = alive(child) and alive(peers['C'])
                observed['held_after_kills'] = not lock_free(repo)
                tree.release()
                tree.assert_stopped(timeout=5)
                deadline = time.monotonic() + 5
                while not lock_free(repo) and time.monotonic() < deadline:
                    time.sleep(0.05)
                observed['free_after_child_exit'] = lock_free(repo)
        finally:
            (work / 'observation.json').write_text(json.dumps(observed, indent=2) + '\n')
            tree.close()
            holders.close()
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
    return observed


def check_lifetime(observed):
    require(observed['held_while_waiting'], f'the lock was not held while the inner child waited: {observed}')
    require(observed['child_alive_after_kills'], f'the inner child did not survive the kills: {observed}')
    require(observed['held_after_kills'], f'the killed dispatcher, shell and launcher released the lock the child holds: {observed}')
    require(observed['free_after_child_exit'], f'the lock stayed held after the child exited: {observed}')


def lock_lifetime_controls(out):
    passing = lifetime(out, 'pass')
    check_lifetime(passing)
    print('lock_lifetime_pass: ok', flush=True)
    dropped = lifetime(out, 'drop')
    try:
        check_lifetime(dropped)
    except AssertionError:
        pass
    else:
        raise AssertionError(f'a launcher that drops the descriptors passed the lifetime check: {dropped}')
    require(dropped['child_alive_after_kills'] and not dropped['held_after_kills'],
            f'without the descriptors the child must not hold the lock after the kills: {dropped}')
    print('lock_lifetime_drop: ok', flush=True)
    return ['lock_lifetime_pass', 'lock_lifetime_drop']


def interruption_control(out):
    name = 'interruption'
    work = out / name
    repo = fixture_repository(work)
    (repo / 'tests/inner/test_inner.py').write_text(MARKER + RENDEZVOUS + textwrap.dedent('''
        import os, signal, socket, subprocess, sys
        def test_waits():
            marker('waiting')
            helper = subprocess.Popen([sys.executable, '-B', '-S', '-P', '-c',
                                       'import os, signal, socket\\nsignal.signal(signal.SIGINT, signal.SIG_IGN)\\n'
                                       + RENDEZVOUS_SOURCE + 'rendezvous(b"C")'])
            rendezvous(b'P')
            helper.wait(timeout=5)
        ''').replace('RENDEZVOUS_SOURCE', repr(RENDEZVOUS)))
    markers = work / 'markers'
    markers.mkdir()
    observation = {}
    with tempfile.TemporaryDirectory(prefix='pw-host-interrupt-', dir='/private/tmp') as socket_dir:
        tree = TreeControl(Path(socket_dir) / 'gate')
        dispatcher = ExitObserver()
        env = {key: value for key, value in os.environ.items() if not key.startswith(('PW_', 'PYTEST'))}
        env.update(PW_TEST_OUT_DIR=str(repo / 'tests/out/runs/default'), PW_TEST_RUN_ID=name, PYTHONDONTWRITEBYTECODE='1',
                   CONTROL_HOST_ARGS='', CONTROL_MARKERS=str(markers), CONTROL_SOCKET=tree.path)
        process = None
        try:
            with (work / 'stdout').open('wb') as stdout, (work / 'stderr').open('wb') as stderr:
                process = subprocess.Popen(['bash', str(repo / 'tests/run.sh'), '--case', 'host/inner'], cwd=work, env=env,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                dispatcher.watch(process.pid)
                peers = tree.accept()
                tree.assert_running()
                os.kill(peers['C'], signal.SIGINT)
                tree.assert_running()
                started = time.monotonic()
                os.killpg(process.pid, signal.SIGINT)
                observation['returncode'] = process.wait(timeout=10)
                observation['elapsed'] = time.monotonic() - started
                dispatcher.assert_stopped()
                tree.assert_stopped(timeout=3)
                observation['exited_peers'] = sorted(tree.exited)
            run = json.loads((repo / 'tests/out/runs/default/run.json').read_text())
            require(observation['returncode'] != 0 and run['ok'] is False, f'{name}: {observation} {run["ok"]}')
            require(run['invocations'][0]['state'] == 'interrupted', run['invocations'][0]['state'])
            # The signal reaches the child directly: it exits, the parent refuses the incomplete receipt within the
            # dispatcher's grace, and the case shell may still write its failed report before the group is killed.
            case = run['case_results'][0]
            require((case['state'], case['status']) in (('unrun', None), ('completed', 'fail')), case)
            observation['case_result'] = case
            require(observation['exited_peers'] == sorted(peers.values()), 'both the inner child and its helper must exit')
            observation['ok'] = True
        finally:
            (work / 'observation.json').write_text(json.dumps(observation, indent=2) + '\n')
            tree.close()
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
            dispatcher.close()
    print('interruption: ok', flush=True)
    return ['interruption']


def judge_controls(out):
    """Each acceptance rule read from a constructed receipt, including the path rule no live run can reach."""
    vendor = pytest_host.VENDOR
    pin = pytest_host.PYTEST_PIN

    def receipt(items=('a::test_x',), *, version=pin, file=None, finish=0, deselected=0, phases=None, subtests=(), extra=()):
        events = [dict(event='session_start', pytest_version=version, pytest_file=file or str(vendor / 'pytest/__init__.py')),
                  dict(event='collected', node_ids=list(items))]
        if deselected:
            events.append(dict(event='deselected', count=deselected))
        for node in items:
            for when, outcome in (phases or {}).get(node, [('setup', 'passed'), ('call', 'passed'), ('teardown', 'passed')]):
                events.append(dict(event='report', node_id=node, when=when, outcome=outcome, duration=0.0, subtest=False))
        for node, outcome in subtests:
            events.append(dict(event='report', node_id=node, when='call', outcome=outcome, duration=0.0, subtest=True,
                               subtest_msg=None, subtest_params={}))
        events.extend(extra)
        if finish is not None:
            events.append(dict(event='session_finish', exitstatus=finish))
        return events

    def rules(events, returncode=0, **expect):
        return [rule for rule, _ in pytest_host.judge(events, returncode, **expect)]

    expectations = [
        ('accepted', rules(receipt()), []),
        ('accepted_with_subtests', rules(receipt(subtests=[('a::test_x', 'passed')] * 3), expect_subtests=3), []),
        ('child_exit', rules(receipt(), returncode=1), ['child_exit']),
        ('child_signal', rules(receipt(finish=None), returncode=-9), ['child_exit', 'session_finish']),
        ('version', rules(receipt(version='9.0.0')), ['pytest_version']),
        ('path_outside_vendor', rules(receipt(file='/opt/homebrew/lib/python3.14/site-packages/pytest/__init__.py')), ['pytest_path']),
        ('no_start', rules([e for e in receipt() if e['event'] != 'session_start']), ['session_start']),
        ('no_finish', rules(receipt(finish=None)), ['session_finish']),
        ('finish_status', rules(receipt(finish=1)), ['session_finish']),
        ('nothing_collected', rules(receipt(items=())), ['collected']),
        ('expected_collected', rules(receipt(), expect_collected=2), ['expected_collected']),
        ('deselected', rules(receipt(deselected=1)), ['deselected']),
        ('missing_call', rules(receipt(phases={'a::test_x': [('setup', 'passed'), ('teardown', 'passed')]})), ['item_reports']),
        ('missing_teardown', rules(receipt(phases={'a::test_x': [('setup', 'passed'), ('call', 'passed')]})), ['item_reports']),
        ('duplicate_call', rules(receipt(phases={'a::test_x': [('setup', 'passed'), ('call', 'passed'), ('call', 'passed'), ('teardown', 'passed')]})), ['item_reports']),
        ('failed_phase', rules(receipt(phases={'a::test_x': [('setup', 'passed'), ('call', 'failed'), ('teardown', 'passed')]})), ['item_reports']),
        ('skipped_phase', rules(receipt(phases={'a::test_x': [('setup', 'skipped'), ('teardown', 'passed')]})), ['item_reports', 'item_reports']),
        ('stray_item', rules(receipt(extra=[dict(event='report', node_id='a::test_y', when='call', outcome='passed', duration=0.0, subtest=False)])), ['item_reports']),
        ('failed_subtest', rules(receipt(subtests=[('a::test_x', 'failed')])), ['subtest_reports']),
        ('skipped_subtest', rules(receipt(subtests=[('a::test_x', 'skipped')])), ['subtest_reports']),
        ('expected_subtests', rules(receipt(subtests=[('a::test_x', 'passed')]), expect_subtests=2), ['expected_subtests']),
    ]
    inventory = []
    for name, found, expected in expectations:
        require(found == expected, f'judge {name}: {found} != {expected}')
        inventory.append(f'judge_{name}')
    require(pytest_host.refused_environment({'PYTEST_ADDOPTS': '', 'PYTHONPATH': 'x', 'PYTESTX': '1'}) == ['PYTESTX', 'PYTEST_ADDOPTS'],
            'every PYTEST* name is refused')
    (out / 'judge.json').write_text(json.dumps([dict(name=n, found=f, expected=e) for n, f, e in expectations], indent=2) + '\n')
    print(f'{len(inventory)} constructed-receipt controls: ok', flush=True)
    return inventory


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = []
    inventory += judge_controls(out)
    inventory += reporting_controls(out)
    inventory += receipt_controls(out)
    inventory += configuration_controls(out)
    inventory += lock_admission_control(out)
    inventory += lock_lifetime_controls(out)
    inventory += interruption_control(out)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} pytest host controls passed')


if __name__ == '__main__':
    main()
