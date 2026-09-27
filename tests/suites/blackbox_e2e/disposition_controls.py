"""Exercise disposition test cleanup and Rust selection without launching a worker."""
from contextlib import ExitStack, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
TEST_NAME = 'run_flow::tests::conflicting_status_representation_is_not_silently_resolved'


def capture_controls(out):
    spec = importlib.util.spec_from_file_location(
        'attempt_in_flight_controls', ROOT / 'tests/suites/witness_contract/check_attempt_in_flight.py')
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    from run_capture import HarnessTimeout
    records = []
    for mode in ('reaped', 'client_timeout', 'unreaped', 'malformed_reap', 'malformed', 'harness_timeout',
                 'fifo_setup', 'capture_setup', 'launch_error', 'removal_error', 'metadata_error'):
        primary = (HarnessTimeout('controlled harness timeout') if mode == 'harness_timeout'
                   else ValueError('controlled capture failure'))
        setup_error = OSError('controlled FIFO setup failure')
        entered = []
        envelope = {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': True}}}}
        if mode == 'client_timeout':
            envelope = {'data': {'runner_result': {'normalized_outcome': 'xpc_timeout'}}}
        if mode == 'unreaped':
            envelope['data']['runner_result']['runner_subprocess']['reaped'] = False
        if mode == 'malformed_reap':
            envelope['data']['runner_result']['runner_subprocess']['pid'] = False

        class Capture:
            elapsed_seconds = 0

            def __init__(self, pw, artifacts, specimen, **kwargs):
                assert Path(specimen['fifo']).is_fifo()
                if mode == 'capture_setup':
                    raise primary

            def __enter__(self):
                entered.append(True)
                if mode == 'launch_error':
                    raise primary
                return self

            def __exit__(self, *args):
                pass

            def wait(self, **kwargs):
                if mode == 'harness_timeout':
                    raise primary
                return 1

            def load_json(self):
                if mode in ('malformed', 'metadata_error'):
                    raise primary
                return envelope

        stderr = io.StringIO()
        write_text = Path.write_text

        def fail_metadata(path, *args, **kwargs):
            if path.name == 'cleanup.json':
                raise OSError('controlled cleanup metadata failure')
            return write_text(path, *args, **kwargs)

        caught = None
        with ExitStack() as patches, redirect_stderr(stderr):
            patches.enter_context(patch.object(target, 'RunCapture', Capture))
            if mode == 'fifo_setup':
                patches.enter_context(patch.object(target.os, 'mkfifo', side_effect=setup_error))
            if mode == 'removal_error':
                patches.enter_context(patch.object(target.shutil, 'rmtree', side_effect=OSError('controlled removal failure')))
            if mode == 'metadata_error':
                patches.enter_context(patch.object(Path, 'write_text', fail_metadata))
            try:
                target.execute('unused', out, mode, lambda fifo: {'fifo': str(fifo)}, fifo=True)
            except Exception as exc:
                caught = exc
        work = out / mode
        (work / 'stderr.txt').write_text(stderr.getvalue())
        staging = Path(json.loads((work / 'staging.json').read_text())['staging'])
        retained = staging.exists()
        try:
            if mode == 'reaped':
                assert caught is None and not retained
            elif mode == 'fifo_setup':
                assert caught is setup_error and not entered and not retained
            elif mode == 'capture_setup':
                assert caught is primary and not entered and not retained
            elif mode in ('malformed', 'harness_timeout', 'metadata_error', 'launch_error'):
                assert caught is primary and retained, (mode, caught, retained)
                assert 'cleanup:' in stderr.getvalue(), stderr.getvalue()
            else:
                assert isinstance(caught, AssertionError) and retained, (mode, caught, retained)
            if mode != 'metadata_error':
                cleanup = json.loads((work / 'cleanup.json').read_text())
                assert cleanup['removed'] is (not retained), cleanup
            else:
                assert 'controlled cleanup metadata failure' in stderr.getvalue()
            records.append({'mode': mode, 'staging_retained': retained,
                            'primary': str(caught) if caught else None})
        finally:
            # Capture never spawns a process; only this control owns this staging.
            if staging.exists():
                shutil.rmtree(staging)
                (work / 'control-recovery.json').write_text(json.dumps({
                    'removed': True, 'basis': 'controlled capture launched no process'}) + '\n')

    # Existing evidence must be refused before even creating temporary staging.
    occupied = out / 'occupied'
    occupied.mkdir()
    receipt = occupied / 'cleanup.json'
    receipt.write_text('preserve prior evidence\n')
    with patch.object(target.tempfile, 'mkdtemp') as create:
        try:
            target.execute('unused', out, 'occupied', lambda fifo: {}, fifo=True)
        except FileExistsError:
            pass
        else:
            raise AssertionError('reused artifact directory accepted')
        create.assert_not_called()
    assert receipt.read_text() == 'preserve prior evidence\n'
    records.append({'mode': 'occupied', 'prior_evidence_preserved': True})
    (out / 'capture-controls.json').write_text(json.dumps(records, indent=2) + '\n')


def rust_wrapper_controls(out):
    repo = out / 'fixture repo'
    wrapper = 'tests/suites/unit/disposition_reds.sh'
    for relative in (wrapper, 'tests/lib/testlib.sh'):
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    cargo = repo / 'bin/cargo'
    cargo.parent.mkdir()
    cargo.write_text('''#!/usr/bin/python3
import json, os, pathlib, sys
p = pathlib.Path(os.environ['DISPOSITION_CARGO_FIXTURE'])
config = json.loads(p.read_text())
p.with_name('argv.json').write_text(json.dumps(sys.argv[1:]))
sys.stdout.write(config['stdout'])
sys.exit(config['status'])
''')
    cargo.chmod(0o755)
    failed = f'test {TEST_NAME} ... FAILED\ntest result: FAILED. 0 passed; 1 failed; 0 ignored;\n'
    assertion = ('exit_code 0 beside term_signal 9 is an invalid status pair; an unqualified disposition '
                 '(signaled) resolves it silently\n')
    passed = f'test {TEST_NAME} ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored;\n'
    scenarios = (
        ('red', 101, failed + assertion, 'fail', 'B1 behavioral red'),
        ('build_failure', 101, 'error: could not compile policy-witness\n', 'fail', 'without the expected B1 assertion'),
        ('other_failure', 101, failed + 'unrelated assertion failed\n', 'fail', 'without the expected B1 assertion'),
        ('missing_cargo', 127, 'cargo: not found\n', 'fail', 'without the expected B1 assertion'),
        ('empty', 0, 'test result: ok. 0 passed; 0 failed; 0 ignored;\n', 'fail', 'did not run successfully'),
        ('wrong_test', 0, passed.replace(TEST_NAME, 'some_other_test'), 'fail', 'did not run successfully'),
        ('green', 0, passed, 'pass', 'disposition test passes'),
    )
    records = []
    for name, status, stdout, expected_status, message in scenarios:
        work = out / name
        work.mkdir(parents=True)
        config = work / 'cargo.json'
        config.write_text(json.dumps({'stdout': stdout, 'status': status}))
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_') and k != 'BASH_ENV'}
        env.update(PATH=str(cargo.parent) + os.pathsep + env['PATH'],
                   DISPOSITION_CARGO_FIXTURE=str(config), PW_TEST_OUT_DIR=str(work / 'output'),
                   PW_TEST_RUN_ID='disposition_control')
        result = subprocess.run(['bash', str(repo / wrapper)], env=env, cwd=work,
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
        (work / 'wrapper.stdout').write_bytes(result.stdout)
        (work / 'wrapper.stderr').write_bytes(result.stderr)
        report = json.loads((work / 'output/suites/unit/rust.disposition_reds/report.json').read_text())
        assert report['status'] == expected_status and message in report['message'], (name, report)
        assert result.returncode == (0 if expected_status == 'pass' else 1), (name, result)
        argv = json.loads((work / 'argv.json').read_text())
        assert argv[-4:] == ['--', '--include-ignored', '--exact', TEST_NAME], argv
        assert argv[argv.index('--bin') + 1] == 'policy-witness', argv
        records.append({'mode': name, 'returncode': result.returncode, 'report': report})
    (out / 'wrapper-controls.json').write_text(json.dumps(records, indent=2) + '\n')


def run_controls(artifacts):
    out = Path(artifacts).resolve() / 'disposition-controls'
    out.mkdir()
    capture_controls(out / 'capture')
    rust_wrapper_controls(out / 'rust')
    # The contract skeleton's structural check plus the independent oracle's
    # self-check: every hand-reviewed example is reproduced by the claim tables,
    # a record built from it is accepted, its mutations are rejected with the
    # expected rule, and the core D-model evaluates totally. Constructed only.
    sys.path.insert(0, str(ROOT / 'tests/lib'))
    from lifecycle_oracle import self_check
    summary = self_check()
    (out / 'oracle-self-check.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'disposition capture, Rust wrapper and oracle controls: ok {summary}', flush=True)


if __name__ == '__main__':
    artifacts = Path(sys.argv[1]).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    run_controls(artifacts)
