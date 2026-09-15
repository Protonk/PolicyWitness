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
from suite_run import account, finish


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


if __name__ == '__main__':
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = check_accounting(out)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} accounting controls passed')
