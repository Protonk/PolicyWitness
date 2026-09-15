"""Check public finalizers by observing their processes, streams, and files."""
import json
import os
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
        for quiet_value in (None, '', '0', '1'):
            quiet = quiet_value == '1'
            for variant in ('default', 'empty', 'literal'):
                label = 'unset' if quiet_value is None else 'empty' if quiet_value == '' else quiet_value
                name = f'{function}_{variant}_quiet_{label}'
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
                env = {key: value for key, value in os.environ.items() if not key.startswith('PW_TEST_')}
                env.update(PW_TEST_OUT_DIR=str(child_out), PW_TEST_EVENTS=str(child_out / 'events.jsonl'),
                           PW_TEST_RUN_ID=name, CONTROL_SUITE=suite, CONTROL_ID=case_id,
                           CONTROL_FINALIZER=function, CONTROL_RETURN_RECEIPT=str(receipt))
                if quiet_value is not None:
                    env['PW_TEST_QUIET'] = quiet_value
                (work / 'input.json').write_text(json.dumps({
                    'function': function, 'arguments': arguments, 'quiet': quiet_value,
                    'suite': suite, 'test_id': case_id,
                }, indent=2) + '\n')
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

                case = child_out / 'suites' / suite / case_id
                assert list(child_out.glob('suites/*/*/report.json')) == [case / 'report.json'], name
                report = json.loads((case / 'report.json').read_text())
                for key, expected in {'suite': suite, 'test_id': case_id, 'status': status,
                                      'message': message, 'artifacts_dir': str(case / 'artifacts')}.items():
                    assert report[key] == expected, (name, key, report)
                assert type(report['duration_ms']) is int and 0 <= report['duration_ms'] <= elapsed_ms + 1000, report
                local = (case / 'events.jsonl').read_bytes()
                assert local == (child_out / 'events.jsonl').read_bytes(), name
                events = [json.loads(line) for line in local.splitlines()]
                assert [(event['step'], event['status']) for event in events] == [
                    ('test_start', 'start'), ('test_end', status)], (name, events)
                for event in events:
                    assert (event['kind'], event['run_id'], event['suite'], event['test_id']) == (
                        'test_event', name, suite, case_id), (name, event)
                terminal = events[-1]
                assert terminal['message'] == message and terminal['data'] == data, (name, terminal)
                assert terminal['duration_ms'] == report['duration_ms'], (name, terminal, report)

                prefix = f'==> [{suite}/{case_id}] '
                stdout = '' if quiet else prefix + 'start\n'
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
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} finalizer controls passed')


if __name__ == '__main__':
    main()
