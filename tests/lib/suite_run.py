"""Dispatch requested suites and reconcile their exits, events, and reports.

Case paths stay stable. Invocation records establish which requested suite
produced each case, including wrapper aliases. Harness errors are separate
from case counts; either kind of failure makes both run.json and the CLI fail.
"""
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(path)


def problem(invocation, code, message, **details):
    invocation['harness_errors'].append({
        'invocation': invocation['index'], 'requested_suite': invocation['requested_suite'],
        'code': code, 'message': message, **details,
    })


def identity(suite, case):
    return (suite, case) if all(isinstance(part, str) and part not in ('', '.', '..')
                                and '/' not in part for part in (suite, case)) else None


def reconcile(invocation, out, run_id, previous_events, previous_reports, seen_cases):
    """Read this invocation's evidence without aborting on malformed input."""
    event_path = out / 'events.jsonl'
    try:
        current_events = event_path.read_bytes() if event_path.exists() else b''
    except OSError as exc:
        problem(invocation, 'unreadable_events', f'cannot read events.jsonl: {exc}')
        current_events = b''
    if current_events.startswith(previous_events):
        appended = current_events[len(previous_events):]
    else:
        problem(invocation, 'events_rewritten', 'suite removed or rewrote earlier events')
        appended = current_events
    starts, ends = {}, {}
    for number, line in enumerate(appended.splitlines(), 1):
        try:
            event = json.loads(line)
            if not isinstance(event, dict) or event.get('kind') != 'test_event' or event.get('run_id') != run_id:
                raise ValueError('expected a test event from this run')
            key = identity(event.get('suite'), event.get('test_id'))
            if key is None:
                raise ValueError('invalid case identity')
            step = event.get('step')
            if step == 'test_start':
                if event.get('status') != 'start':
                    raise ValueError('invalid start status')
                starts[key] = starts.get(key, 0) + 1
            elif step == 'test_end':
                if event.get('status') not in ('pass', 'fail', 'skip'):
                    raise ValueError('invalid terminal status')
                if starts.get(key, 0) != 1:
                    problem(invocation, 'case_order', f'{key}: test_end without one preceding test_start')
                ends.setdefault(key, []).append(event['status'])
        except ValueError as exc:
            problem(invocation, 'invalid_event', f'invalid event at invocation line {number}: {exc}')

    current_reports = {}
    for path in sorted(out.glob('suites/*/*/report.json')):
        relative = str(path.relative_to(out))
        try:
            current_reports[relative] = path.read_bytes()
        except OSError as exc:
            current_reports[relative] = None
            problem(invocation, 'unreadable_report', f'cannot read {relative}: {exc}', path=relative)
    changed = {path for path, raw in current_reports.items()
               if path not in previous_reports or raw != previous_reports[path]}
    for path in previous_reports.keys() - current_reports.keys():
        problem(invocation, 'report_removed', f'suite removed earlier report: {path}', path=path)

    keys = starts.keys() | ends.keys()
    paths = changed | {f'suites/{suite}/{case}/report.json' for suite, case in keys}
    invocation['report_paths'] = sorted(paths)
    if not paths and invocation['state'] == 'exited':
        problem(invocation, 'empty_suite', 'suite exited without any case reports or case lifecycle events')
    for relative in sorted(paths):
        parts = Path(relative).parts
        key = (parts[1], parts[2])
        details = {'reported_suite': key[0], 'test_id': key[1], 'path': relative}
        if starts.get(key, 0) != 1:
            problem(invocation, 'case_start', f'{relative}: expected one test_start, got {starts.get(key, 0)}', **details)
        terminal = ends.get(key, [])
        if len(terminal) != 1:
            problem(invocation, 'case_end', f'{relative}: expected one test_end, got {len(terminal)}', **details)
        if key in seen_cases:
            problem(invocation, 'reused_case', f'case path was already used by invocation {seen_cases[key]}', **details)
        else:
            seen_cases[key] = invocation['index']
        if relative not in current_reports:
            problem(invocation, 'missing_report', f'missing report: {relative}', **details)
            continue
        raw = current_reports[relative]
        if raw is None:
            continue
        try:
            report = json.loads(raw)
            if not isinstance(report, dict):
                raise ValueError('report is not an object')
            if identity(report.get('suite'), report.get('test_id')) != key:
                raise ValueError('report identity disagrees with its path')
            if report.get('status') not in ('pass', 'fail', 'skip'):
                raise ValueError('invalid report status')
        except ValueError as exc:
            problem(invocation, 'invalid_report', f'invalid {relative}: {exc}', **details)
            continue
        if len(terminal) == 1 and report['status'] != terminal[0]:
            problem(invocation, 'status_mismatch', f'{relative}: report status disagrees with test_end', **details)
        invocation['reports'].append(report)
    return current_events, current_reports


def counts(reports):
    result = {'pass': 0, 'fail': 0, 'skip': 0, 'total': 0}
    for report in reports:
        result[report['status']] += 1
        result['total'] += 1
    return result


def finish(out, run_id, started, invocations, plan):
    reports = [report for item in invocations for report in item['reports']]
    errors = [error for item in invocations for error in item['harness_errors']]
    case_results = [case for item in invocations for case in item['case_results']]
    selected = Counter(case['id'] for case in plan['cases'])
    accounted = Counter(case['id'] for case in case_results)
    invalid_states = [case['id'] for case in case_results
                      if case['state'] not in ('completed', 'skipped', 'unrun')]
    unrun = [case['id'] for case in case_results if case['state'] == 'unrun']
    if (selected != accounted or any(n != 1 for n in selected.values()) or invalid_states
            or (unrun and not errors)):
        errors.append({'invocation': None, 'requested_suite': 'dispatcher', 'code': 'incomplete_accounting',
                       'message': 'expected exactly one valid result per selection and a diagnostic for unrun cases',
                       'missing_cases': sorted(selected.keys() - accounted.keys()),
                       'unexpected_cases': sorted(accounted.keys() - selected.keys()),
                       'duplicate_cases': sorted(key for key in selected.keys() | accounted.keys()
                                                 if selected[key] > 1 or accounted[key] > 1),
                       'invalid_states': invalid_states, 'unrun_cases': unrun})
    totals = counts(reports)
    by_suite = {}
    for name in sorted({report['suite'] for report in reports}):
        by_suite[name] = counts([report for report in reports if report['suite'] == name])
    finished = time.time_ns() // 1_000_000
    run = {
        'schema_version': 1, 'run_id': run_id, 'started_at_unix_ms': started,
        'finished_at_unix_ms': finished, 'duration_ms': finished - started,
        'ok': not errors and totals['fail'] == 0,
        'counts': totals, 'suites': by_suite, 'reports': reports,
        'requested_suites': plan['selection']['suites'],
        'requested_cases': plan['selection']['cases'],
        'invocations': invocations, 'harness_errors': errors,
        'plan': plan, 'configuration': plan['configuration'],
        'case_results': case_results,
    }
    run['completion'] = {state: sum(c['state'] == state for c in run['case_results'])
                         for state in ('completed', 'skipped', 'unrun')}
    run['completion']['selected'] = len(plan['cases'])
    save(out / 'run.json', run)
    for error in errors:
        print(f"HARNESS: [{error['requested_suite']}] {error['code']}: {error['message']}", file=sys.stderr)
    print(f'Test run summary: {out / "run.json"}', flush=True)
    return 0 if run['ok'] else 1


def requirements(case, config, env, root, cache):
    missing = []
    for name in case['requires']:
        if name not in cache:
            if name == 'app':
                ok = Path(config['pw_bin']).is_file() and os.access(config['pw_bin'], os.X_OK)
            elif name == 'worker':
                worker = Path(config['app_dir']) / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
                ok = worker.is_file() and os.access(worker, os.X_OK)
            elif name == 'gui':
                ok = subprocess.run(['/bin/launchctl', 'print', f'gui/{os.getuid()}'],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10).returncode == 0
            elif name == 'identity':
                result = subprocess.run(['bash', '-c', 'source "$1/tests/lib/testlib.sh"; resolve_app_signing_identity "$PW_APP_DIR"',
                                         'identity', str(root)], env=env, capture_output=True, text=True, timeout=20)
                value = result.stdout.strip()
                ok = result.returncode == 0 and bool(value)
                if ok:
                    env['PW_BYOXPC_IDENTITY'] = value
            else:
                ok = shutil.which(name, path=env.get('PATH')) is not None
            cache[name] = ok
        if not cache[name]:
            missing.append(name)
    return missing


def account(item):
    expected = Counter((c['report_suite'], c['test_id']) for c in item['cases'])
    observed = {(r['suite'], r['test_id']): r for r in item['reports']}
    ambiguous = {key for key, count in expected.items() if count > 1}
    for key in sorted(ambiguous):
        problem(item, 'ambiguous_case_path', f'distinct selections share a report path: {key}')
    for key in observed.keys() - expected.keys():
        problem(item, 'unselected_case', f'unselected case produced evidence: {key}')
    item['case_results'] = []
    for case in item['cases']:
        key = (case['report_suite'], case['test_id'])
        report = observed.get(key) if key not in ambiguous else None
        state = 'unrun'
        status = None
        reason = 'ambiguous report path' if key in ambiguous else item.get('blocked_reason')
        if report:
            status = report['status']
            state = 'skipped' if status == 'skip' else 'completed'
            reason = report.get('message')
            if status == 'skip' and report.get('skip_reason') not in case['skip_reasons']:
                problem(item, 'unexpected_skip', f'{case["id"]}: skip is not declared by this case contract')
        else:
            problem(item, 'unrun_case', f'selected case has no readable terminal report: {case["id"]}')
        item['case_results'].append({'id': case['id'], 'context': case['context'],
                                     'state': state, 'status': status, 'reason': reason})


def execute(root, out, run_id, started, plan, config):
    # Most cases get their own process, so a failure cannot suppress a sibling.
    # BYOXPC shares installation and cleanup across its explicitly selected leaves.
    groups = []
    for case in plan['cases']:
        if (case['context'] == 'byoxpc' and groups and groups[-1][0]['context'] == 'byoxpc'
                and case['command'] == groups[-1][0]['command']):
            groups[-1].append(case)
        else:
            groups.append([case])
    invocations = [{'index': index, 'requested_suite': group[0]['suite'], 'cases': group,
                    'state': 'not_started', 'case_results': [], 'returncode': None,
                    'started_at_unix_ms': None, 'finished_at_unix_ms': None,
                    'report_paths': [], 'reports': [], 'harness_errors': []}
                   for index, group in enumerate(groups)]
    journal = out / 'dispatch.json'
    save(journal, {'run_id': run_id, 'invocations': invocations})
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_TEST_')}
    env.update(PW_APP_DIR=config['app_dir'], PW_BIN=config['pw_bin'], PW_BIN_PATH=config['pw_bin'],
               PW_TEST_OUT_DIR=str(out), PW_TEST_EVENTS=str(out / 'events.jsonl'),
               PW_TEST_RUN_ID=run_id, PW_TEST_QUIET='1' if config['quiet'] else '',
               PYTHONDONTWRITEBYTECODE='1')
    previous_events, previous_reports, seen_cases = b'', {}, {}
    interrupted, cache, outcomes = False, {}, {}
    for item in invocations:
        group = item['cases']
        group_ids = {c['id'] for c in group}
        try:
            missing = [] if interrupted else sorted({req for c in group for req in requirements(c, config, env, root, cache)})
        except (OSError, subprocess.TimeoutExpired) as exc:
            missing = [f'prerequisite check failed: {exc}']
        except KeyboardInterrupt:
            missing = []
            interrupted = True
        dependencies = {dep for c in group for dep in c['depends_on'] if dep not in group_ids}
        failed_deps = sorted(dep for dep in dependencies if outcomes.get(dep) != 'pass')
        if interrupted or missing or failed_deps:
            item['state'] = 'blocked'
            reason = 'interrupted' if interrupted else f'missing prerequisites: {missing}' if missing else f'dependencies did not pass: {failed_deps}'
            item['blocked_reason'] = reason
            problem(item, 'not_run', reason)
        else:
            print('==> [selection] ' + ', '.join(c['id'] for c in group), flush=True)
            item.update(state='running', started_at_unix_ms=time.time_ns() // 1_000_000)
            save(journal, {'run_id': run_id, 'invocations': invocations})
            child_env = {**env, 'PW_TEST_CASES': '\n'.join(c['test_id'] for c in group)}
            command = group[0]['command']
            try:
                item.update(state='exited', returncode=subprocess.run(command, cwd=root, env=child_env).returncode)
                if item['returncode'] != 0:
                    problem(item, 'suite_exit', f"case command exited with status {item['returncode']}")
            except OSError as exc:
                item['state'] = 'launch_failed'
                problem(item, 'launch_failed', str(exc))
            except KeyboardInterrupt:
                item['state'] = 'interrupted'
                interrupted = True
                problem(item, 'interrupted', 'test execution interrupted')
            item['finished_at_unix_ms'] = time.time_ns() // 1_000_000
            previous_events, previous_reports = reconcile(item, out, run_id, previous_events,
                                                          previous_reports, seen_cases)
        account(item)
        for case in item['case_results']:
            outcomes[case['id']] = case['status'] if not item['harness_errors'] else 'fail'
        save(journal, {'run_id': run_id, 'invocations': invocations})
    return finish(out, run_id, started, invocations, plan)
