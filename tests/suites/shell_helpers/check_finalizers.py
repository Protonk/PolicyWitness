"""Check public finalizers by observing their processes, streams, and files."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'tests/fixtures/shell_case/finalize.sh'


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = []
    functions = [('test_pass', 'pass', 'ok'), ('test_pass_note', 'pass', 'ok'),
                 ('test_fail', 'fail', 'failed'), ('test_skip', 'skip', 'skipped')]
    for function, status, default_message in functions:
        scenarios = [(quiet, variant, 'normal') for quiet in (None, '', '0', '1')
                     for variant in ('default', 'empty', 'literal')]
        scenarios += [(None, 'default', setup) for setup in ('before_begin', 'reassigned_dir')]
        for quiet_value, variant, setup in scenarios:
            quiet = quiet_value == '1'
            label = 'unset' if quiet_value is None else 'empty' if quiet_value == '' else quiet_value
            name = f'{function}_{variant}_quiet_{label}_{setup}'
            work = out / name
            work.mkdir()
            child_out = work / 'output with spaces'
            receipt = work / 'returned.txt'
            canary = work / 'CANARY'
            message = 'literal "quotes" and \'apostrophes\'\\backslash\n$(touch CANARY) — λ'
            data = {'text': message, 'values': [None, False, 0, 2.5], 'nested': {'ok': True}}
            arguments = [message, json.dumps(data)]
            if variant != 'literal':
                message, data = default_message, None
                arguments = [] if variant == 'default' else ['', '']
            suite, case_id = 'finalizer_alias', 'retained_case'
            case = child_out / 'suites' / suite / case_id
            reassigned = work / 'reassigned'
            setup_receipt = work / 'before-finalizer.json'
            env = {key: value for key, value in os.environ.items() if not key.startswith('PW_TEST_')}
            env.update(PW_TEST_OUT_DIR=str(child_out), PW_TEST_EVENTS=str(child_out / 'events.jsonl'),
                       PW_TEST_RUN_ID=name, CONTROL_SUITE=suite, CONTROL_ID=case_id,
                       CONTROL_OUTSIDE_SCRATCH=str(work / 'outside'),
                       CONTROL_SETUP=setup, CONTROL_CASE_DIR=str(case),
                       CONTROL_REASSIGNED_DIR=str(reassigned), CONTROL_SETUP_RECEIPT=str(setup_receipt),
                       CONTROL_FINALIZER=function, CONTROL_RETURN_RECEIPT=str(receipt))
            if quiet_value is not None:
                env['PW_TEST_QUIET'] = quiet_value
            (work / 'input.json').write_text(json.dumps({
                'function': function, 'arguments': arguments, 'quiet': quiet_value,
                'suite': suite, 'test_id': case_id, 'setup': setup,
            }, indent=2) + '\n')
            guard_paths = [case / 'scratch', reassigned / 'scratch'] if setup != 'normal' else []
            try:
                started = time.monotonic()
                result = subprocess.run(['bash', str(FIXTURE), str(ROOT / 'tests/lib/testlib.sh'),
                                         *arguments], cwd=work, env=env, capture_output=True, timeout=10)
                elapsed_ms = (time.monotonic() - started) * 1000
                (work / 'stdout').write_bytes(result.stdout)
                (work / 'stderr').write_bytes(result.stderr)
                (work / 'exit.json').write_text(json.dumps({'returncode': result.returncode}) + '\n')
                assert result.returncode == (1 if status == 'fail' else 0), (name, result.stderr)
                if status == 'fail':
                    assert not receipt.exists(), f'{name}: test_fail returned with errexit disabled'
                else:
                    assert receipt.read_bytes() == b'0\n', f'{name}: finalizer did not return success'
                assert not canary.exists(), f'{name}: a literal argument was evaluated as shell code'

                observed = json.loads(setup_receipt.read_text())
                assert observed == {'scratch': str(case / 'scratch'), 'populated': 'temporary\n'}, (name, observed)
                if setup == 'normal':
                    assert not (case / 'scratch').exists(), name
                else:
                    assert (case / 'scratch/nested/build-state').read_bytes() == b'temporary\n', name
                if setup == 'reassigned_dir':
                    assert (reassigned / 'scratch/retained').read_bytes() == b'reassigned\n', name
                assert sorted(p.name for p in (case / 'artifacts').iterdir()) == ['retained'], name
                assert (case / 'artifacts/retained').read_bytes() == b'evidence\n', name
                assert (work / 'outside/retained').read_bytes() == b'outside\n', name
                assert list(child_out.glob('suites/*/*/report.json')) == [case / 'report.json'], name
                report = json.loads((case / 'report.json').read_text())
                for key, expected in {'suite': suite, 'test_id': case_id, 'status': status,
                                      'message': message, 'artifacts_dir': str(case / 'artifacts')}.items():
                    assert report[key] == expected, (name, key, report)
                assert type(report['duration_ms']) is int and 0 <= report['duration_ms'] <= elapsed_ms + 1000, report
                local = (case / 'events.jsonl').read_bytes()
                assert local == (child_out / 'events.jsonl').read_bytes(), name
                events = [json.loads(line) for line in local.splitlines()]
                expected_events = [] if setup == 'before_begin' else [('test_start', 'start')]
                assert [(event['step'], event['status']) for event in events] == [
                    *expected_events, ('test_end', status)], (name, events)
                for event in events:
                    assert (event['kind'], event['run_id'], event['suite'], event['test_id']) == (
                        'test_event', name, suite, case_id), (name, event)
                terminal = events[-1]
                assert terminal['message'] == message and terminal['data'] == data, (name, terminal)
                assert terminal['duration_ms'] == report['duration_ms'], (name, terminal, report)

                prefix = f'==> [{suite}/{case_id}] '
                stdout = '' if quiet or setup == 'before_begin' else prefix + 'start\n'
                stderr = ''
                if status == 'fail':
                    stderr = f'FAIL: [{suite}/{case_id}] {message}\n'
                elif function == 'test_pass_note':
                    stdout += prefix + message + '\n'
                elif not quiet:
                    stdout += prefix + f'{status}: {message}\n'
                assert result.stdout == stdout.encode(), (name, result.stdout, stdout)
                assert result.stderr == stderr.encode(), (name, result.stderr, stderr)
                inventory.append(name)
                print(f'{name}: ok', flush=True)
            finally:
                for path in guard_paths:
                    if path.exists():
                        shutil.rmtree(path)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} finalizer controls passed')


if __name__ == '__main__':
    main()
