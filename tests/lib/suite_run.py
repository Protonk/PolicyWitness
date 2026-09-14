"""Dispatch requested suites and reconcile their exits, events, and reports.

Case paths stay stable. Invocation records establish which requested suite
produced each case, including wrapper aliases. Harness errors are separate
from case counts; either kind of failure makes both run.json and the CLI fail.
"""
import json
import os
from pathlib import Path
import re
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


def finish(out, run_id, started, invocations):
    reports = [report for item in invocations for report in item['reports']]
    errors = [error for item in invocations for error in item['harness_errors']]
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
        'requested_suites': [item['requested_suite'] for item in invocations],
        'invocations': invocations, 'harness_errors': errors,
    }
    save(out / 'run.json', run)
    for error in errors:
        print(f"HARNESS: [{error['requested_suite']}] {error['code']}: {error['message']}", file=sys.stderr)
    print(f'Test run summary: {out / "run.json"}', flush=True)
    return 0 if run['ok'] else 1


def main():
    root_arg, out_arg, run_id, start_arg, *suites = sys.argv[1:]
    root, out = Path(root_arg), Path(out_arg)
    invocations = [{'index': index, 'requested_suite': suite, 'state': 'not_started',
                    'returncode': None, 'started_at_unix_ms': None, 'finished_at_unix_ms': None,
                    'report_paths': [], 'reports': [], 'harness_errors': []}
                   for index, suite in enumerate(suites)]
    journal = out / 'dispatch.json'
    save(journal, {'run_id': run_id, 'invocations': invocations})
    previous_events, previous_reports, seen_cases = b'', {}, {}
    interrupted = False
    for item in invocations:
        suite = item['requested_suite']
        script = root / 'tests/suites' / suite / 'run.sh'
        if interrupted:
            problem(item, 'not_run', 'not run because dispatch was interrupted')
        elif not re.fullmatch(r'[a-z][a-z0-9_]*', suite):
            item['state'] = 'invalid'
            problem(item, 'invalid_suite', 'suite name must be a registry identifier')
        elif not script.is_file() or not os.access(script, os.X_OK):
            item['state'] = 'missing'
            problem(item, 'missing_runner', f'missing or nonexecutable suite runner: {script}')
        else:
            print(f'==> [suite] {suite}', flush=True)
            item.update(state='running', started_at_unix_ms=time.time_ns() // 1_000_000)
            save(journal, {'run_id': run_id, 'invocations': invocations})
            try:
                item.update(state='exited', returncode=subprocess.run(['bash', str(script)]).returncode)
                if item['returncode'] != 0:
                    problem(item, 'suite_exit', f"suite exited with status {item['returncode']}")
            except OSError as exc:
                item['state'] = 'launch_failed'
                problem(item, 'launch_failed', str(exc))
            except KeyboardInterrupt:
                item['state'] = 'interrupted'
                interrupted = True
                problem(item, 'interrupted', 'suite execution interrupted')
            item['finished_at_unix_ms'] = time.time_ns() // 1_000_000
            previous_events, previous_reports = reconcile(item, out, run_id, previous_events,
                                                          previous_reports, seen_cases)
        save(journal, {'run_id': run_id, 'invocations': invocations})
    return finish(out, run_id, int(start_arg), invocations)


if __name__ == '__main__':
    sys.exit(main())
