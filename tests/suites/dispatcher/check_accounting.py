"""Exercise the executor's accounting boundary with independent handoff records.

The public-command controls reject catalog collisions before execution. These
controls supply records directly to check the executor's separate responsibility:
retain every selection and refuse a successful summary for incomplete accounting.
"""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import suite_run
from suite_run import account, finish, system_sleep


def check_accounting(out):
    cases = [dict(id=f'{suite}/x', suite=suite, test_id='x', report_suite=suite,
                  context='byoxpc', skip_reasons=[]) for suite in ('alpha', 'beta')]
    reports = [dict(suite=suite, test_id='x', status='pass', message='observed')
               for suite in ('alpha', 'beta')]
    results = [dict(id=f'{suite}/x', context='byoxpc', state='completed', status='pass', reason='observed')
               for suite in ('alpha', 'beta')]
    inventory = []
    for name in ('distinct', 'single_alias', 'collision', 'missing_result', 'duplicate_result',
                 'unexpected_result', 'invalid_state', 'unrun_without_error', 'reordered_results'):
        work = out / ('accounting_' + name)
        work.mkdir()
        selected, evidence, supplied = deepcopy(cases), deepcopy(reports), deepcopy(results)
        expected_ok, expected_unrun = True, 0
        diagnostic = None
        if name == 'single_alias':
            selected = [selected[0]]
            selected[0]['report_suite'] = 'beta'
            evidence = [evidence[1]]
        elif name == 'collision':
            selected[0]['report_suite'] = 'beta'
            evidence = [evidence[1]]
            expected_ok, expected_unrun, diagnostic = False, 2, 'ambiguous_case_path'
        elif name == 'missing_result':
            supplied.pop()
        elif name == 'duplicate_result':
            supplied[1] = deepcopy(supplied[0])
        elif name == 'unexpected_result':
            supplied[1]['id'] = 'unselected/x'
        elif name == 'invalid_state':
            supplied[1]['state'] = 'forgotten'
        elif name == 'unrun_without_error':
            supplied[1].update(state='unrun', status=None)
        elif name == 'reordered_results':
            supplied.reverse()
        direct_finish = name not in ('distinct', 'single_alias', 'collision')
        if direct_finish and name != 'reordered_results':
            expected_ok, diagnostic = False, 'incomplete_accounting'
        item = dict(index=0, requested_suite='alpha', cases=selected, reports=evidence,
                    harness_errors=[], case_results=supplied if direct_finish else [])
        plan = dict(cases=selected, selection={'suites': [], 'cases': [c['id'] for c in selected]},
                    configuration={})
        (work / 'input.json').write_text(json.dumps({'invocation': item, 'plan': plan}, indent=2) + '\n')
        if not direct_finish:
            account(item)
        with (work / 'stdout').open('w') as stdout, (work / 'stderr').open('w') as stderr:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = finish(work, name, time.time_ns() // 1_000_000, [item], plan)
        (work / 'exit.json').write_text(json.dumps({'returncode': code}) + '\n')
        run = json.loads((work / 'run.json').read_text())
        if code != (0 if expected_ok else 1) or run['ok'] is not expected_ok:
            raise AssertionError(f'{name}: exit/summary accepted invalid accounting: {run}')
        if diagnostic and diagnostic not in {e['code'] for e in run['harness_errors']}:
            raise AssertionError(f'{name}: missing diagnostic: {run["harness_errors"]}')
        if not direct_finish:
            if [c['id'] for c in run['case_results']] != [c['id'] for c in selected]:
                raise AssertionError(f'{name}: a selection disappeared')
            expected = dict(selected=len(selected), completed=len(selected) - expected_unrun,
                            skipped=0, unrun=expected_unrun)
            if run['completion'] != expected:
                raise AssertionError(f'{name}: incorrect accounting: {run["completion"]}')
        inventory.append('accounting_' + name)
    return inventory


def check_sleep(out):
    """Sleep records come from constructed readings; they never change a result."""
    inventory = []
    second = 1_000_000_000
    readings = {
        'equal': (((0, 0), (5 * second, 5 * second)), (0, None)),
        'read_skew': (((0, 0), (999_999, 0)), (0, None)),
        'uptime_skew': (((0, 0), (0, 999_999)), (0, None)),
        'one_ms': (((0, 0), (1_000_000, 0)), (1, None)),
        'two_seconds': (((0, 0), (2 * second + 5, 5)), (2000, None)),
    }
    for name, ((before, after), expected) in readings.items():
        if system_sleep(before, after) != expected:
            raise AssertionError(f'sleep_{name}: {system_sleep(before, after)} != {expected}')
        inventory.append('sleep_' + name)
    slept, error = system_sleep((0, 0), (0, 1_000_000))
    if slept is not None or 'uptime clock advanced' not in error:
        raise AssertionError(f'sleep_uptime_ahead: negative gap recorded as {slept}, {error}')
    slept, error = system_sleep('clock read failed: constructed', (0, 0))
    if slept is not None or error != 'clock read failed: constructed':
        raise AssertionError(f'sleep_failed_read: recorded as {slept}, {error}')
    inventory += ['sleep_uptime_ahead', 'sleep_failed_read']

    def finished(name, invocations, assertion=None):
        work = out / name
        work.mkdir()
        cases = [case for item in invocations for case in item['cases']]
        plan = dict(cases=cases, selection={'suites': [], 'cases': [c['id'] for c in cases]}, configuration={})
        for item in invocations:
            account(item)
        with (work / 'stdout').open('w') as stdout, (work / 'stderr').open('w') as stderr:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = finish(work, name, time.time_ns() // 1_000_000, invocations, plan,
                              idle_sleep_assertion=assertion)
        return code, json.loads((work / 'run.json').read_text()), (work / 'stderr').read_text()

    def invocation(index, status, slept):
        case = dict(id=f'sleep/{status}', suite='sleep', test_id=status, report_suite='sleep',
                    context='standard', skip_reasons=[])
        report = dict(suite='sleep', test_id=status, status=status, message='observed')
        return dict(index=index, requested_suite='sleep', cases=[case], reports=[report],
                    harness_errors=[], case_results=[], system_sleep_ms=slept, system_sleep_error=None)

    code, run, stderr = finished('sleep_mixed', [invocation(0, 'fail', 2000), invocation(1, 'pass', 2000)])
    lines = [line for line in stderr.splitlines() if line.startswith('SLEEP:')]
    if code != 1 or run['ok'] is not False or [c['status'] for c in run['case_results']] != ['fail', 'pass']:
        raise AssertionError(f'sleep_mixed: sleep changed a result: {run}')
    if [c['system_sleep_ms'] for c in run['case_results']] != [2000, 2000]:
        raise AssertionError(f'sleep_mixed: case results lost the record: {run["case_results"]}')
    if lines != ['SLEEP: [sleep] sleep/fail (fail): the system slept 2000 ms during this invocation; '
                 'a failure here is not creditable product evidence',
                 'SLEEP: [sleep] sleep/pass (pass): the system slept 2000 ms during this invocation']:
        raise AssertionError(f'sleep_mixed: unexpected report: {lines}')
    code, run, stderr = finished('sleep_passing', [invocation(0, 'pass', 2000)])
    if code != 0 or run['ok'] is not True or 'not creditable' in stderr:
        raise AssertionError(f'sleep_passing: sleep changed a passing result: {run}, {stderr}')
    code, run, stderr = finished('sleep_awake', [invocation(0, 'fail', 0)])
    if code != 1 or 'SLEEP:' in stderr:
        raise AssertionError(f'sleep_awake: an awake invocation reported sleep: {stderr}')
    inventory += ['sleep_mixed', 'sleep_passing', 'sleep_awake']

    # Unavailable or early-exiting assertions are recorded and reported, never fatal.
    original = suite_run.CAFFEINATE
    try:
        suite_run.CAFFEINATE = (str(out / 'absent-caffeinate'), '-i', '-w')
        process, absent = suite_run.hold_idle_sleep()
        suite_run.CAFFEINATE = ('/usr/bin/false',)
        early_process, early = suite_run.hold_idle_sleep()
        early_process.wait(timeout=10)
        suite_run.release_idle_sleep(early_process, early)
    finally:
        suite_run.CAFFEINATE = original
    if process is not None or absent['launched'] or 'cannot launch caffeinate' not in absent['error']:
        raise AssertionError(f'assertion_absent: {absent}')
    if not early['launched'] or early['running_at_end'] is not False or early['error'] != 'caffeinate exited early with status 1':
        raise AssertionError(f'assertion_early_exit: {early}')
    for name, record in (('assertion_absent', absent), ('assertion_early_exit', early)):
        code, run, stderr = finished(name, [invocation(0, 'pass', 0)], record)
        if code != 0 or run['ok'] is not True or run['idle_sleep_assertion'] != record:
            raise AssertionError(f'{name}: assertion failure changed the run: {run}')
        if f"SLEEP: idle sleep was not blocked: {record['error']}" not in stderr.splitlines():
            raise AssertionError(f'{name}: failure not reported: {stderr}')
        inventory.append(name)
    return inventory


if __name__ == '__main__':
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = check_accounting(out) + check_sleep(out)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} accounting controls passed')
