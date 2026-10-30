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
import signal
import subprocess
import sys
import time
import artifact

# Blocks idle sleep until the dispatcher exits; lid close and requested sleep
# still happen, so every invocation also records how long the system slept.
CAFFEINATE = ('/usr/bin/caffeinate', '-i', '-w')


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


def reconcile(invocation, out, run_id, previous_events, previous_reports, seen_cases, interpreter=None):
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
        # The case's shell resolved the interpreter itself; its report must name the one this run resolved.
        declared = report.get('interpreter')
        declared = declared.get('realpath') if isinstance(declared, dict) else None
        if interpreter is not None and declared != interpreter:
            problem(invocation, 'interpreter_mismatch',
                    f'{relative}: report declares interpreter {declared!r}; this run resolved {interpreter!r}', **details)
        invocation['reports'].append(report)
        case_dir = out / Path(relative).parent
        # Inspect directory entries without traversing symlinks, including a
        # symlink at the case root. Scratch itself must be absent after finish.
        if os.path.lexists(case_dir / 'scratch'):
            problem(invocation, 'scratch_retained', f'{relative}: case scratch remains',
                    **{**details, 'path': str((case_dir / 'scratch').relative_to(out))})
        if not case_dir.is_symlink():
            for directory, names, _ in os.walk(case_dir, followlinks=False):
                for name in names:
                    path = Path(directory) / name
                    if name == '.build' and not path.is_symlink():
                        problem(invocation, 'build_tree_in_evidence',
                                f'{relative}: SwiftPM build tree remains at {path.relative_to(out)}',
                                **{**details, 'path': str(path.relative_to(out))})
                # A build tree is one violation, regardless of its contents.
                names[:] = [name for name in names if name != '.build']
    return current_events, current_reports


def sleep_clocks():
    """Read the clock that counts system sleep and the one that does not."""
    try:
        return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW), time.clock_gettime_ns(time.CLOCK_UPTIME_RAW)
    except OSError as exc:
        return f'clock read failed: {exc}'


def system_sleep(before, after):
    """Whole milliseconds the system slept between two readings, or None and why.

    The raw pair shares one timebase and differs only by sleep, so the gap
    between their advances is the sleep. Reading the pair takes a few
    microseconds, so a gap within a millisecond either way is read skew.
    """
    for reading in (before, after):
        if isinstance(reading, str):
            return None, reading
    gap = (after[0] - before[0]) - (after[1] - before[1])
    if gap <= -1_000_000:
        return None, f'uptime clock advanced {-gap} ns more than the sleep-counting clock'
    return max(gap, 0) // 1_000_000, None


def hold_idle_sleep():
    """Start the idle-sleep assertion; a failure is recorded, never fatal."""
    record = {'command': [*CAFFEINATE, str(os.getpid())], 'launched': False,
              'running_at_end': None, 'error': None}
    try:
        # Closed descriptors keep the checkout lock out of the helper, and its
        # own session keeps a terminal interrupt from ending the assertion early.
        process = subprocess.Popen(record['command'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
    except OSError as exc:
        record['error'] = f'cannot launch caffeinate: {exc}'
        return None, record
    record['launched'] = True
    return process, record


def release_idle_sleep(process, record):
    if process is None:
        return
    status = process.poll()
    record['running_at_end'] = status is None
    if status is not None:
        record['error'] = f'caffeinate exited early with status {status}'
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def counts(reports):
    result = {'pass': 0, 'fail': 0, 'skip': 0, 'total': 0}
    for report in reports:
        result[report['status']] += 1
        result['total'] += 1
    return result


def finish(out, run_id, started, invocations, plan, integrity=None, idle_sleep_assertion=None):
    reports = [report for item in invocations for report in item['reports']]
    errors = [error for item in invocations for error in item['harness_errors']]
    if integrity:
        errors.extend(integrity['harness_errors'])
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
        'schema_version': 1, 'terminal': True, 'run_id': run_id, 'started_at_unix_ms': started,
        'finished_at_unix_ms': finished, 'duration_ms': finished - started,
        'ok': not errors and totals['fail'] == 0 and all(c['status'] in ('pass', 'skip') for c in case_results),
        'execution_contract': plan.get('execution_contract'),
        'counts_scope': 'legacy reports only',
        'case_outcome_counts': dict(Counter(c['status'] or c['state'] for c in case_results)),
        'counts': totals, 'suites': by_suite, 'reports': reports,
        'requested_suites': plan['selection']['suites'],
        'requested_cases': plan['selection']['cases'],
        'invocations': invocations, 'harness_errors': errors,
        'plan': plan, 'configuration': plan['configuration'],
        'case_results': case_results,
        'artifact_integrity': integrity,
        'idle_sleep_assertion': idle_sleep_assertion,
    }
    run['completion'] = {state: sum(c['state'] == state for c in run['case_results'])
                         for state in ('completed', 'skipped', 'unrun')}
    run['completion']['selected'] = len(plan['cases'])
    save(out / 'run.json', run)
    for error in errors:
        print(f"HARNESS: [{error['requested_suite']}] {error['code']}: {error['message']}", file=sys.stderr)
    if idle_sleep_assertion and idle_sleep_assertion['error']:
        print(f"SLEEP: idle sleep was not blocked: {idle_sleep_assertion['error']}", file=sys.stderr)
    for item in invocations:
        slept = item.get('system_sleep_ms')
        if slept:
            failed = item['harness_errors'] or any(case['status'] == 'fail' for case in item['case_results'])
            cases = ', '.join(f"{case['id']} ({case['status'] or case['state']})" for case in item['case_results'])
            note = '; a failure here is not creditable product evidence' if failed else ''
            print(f"SLEEP: [{item['requested_suite']}] {cases}: the system slept {slept} ms during this invocation{note}",
                  file=sys.stderr)
        elif item.get('system_sleep_error'):
            print(f"SLEEP: [{item['requested_suite']}] system sleep unknown: {item['system_sleep_error']}", file=sys.stderr)
    print(f'Test run summary: {out / "run.json"}', flush=True)
    return 0 if run['ok'] else 1


ROSETTA_PROBE = ('/usr/bin/arch', '-x86_64', '/bin/bash', '-c', '/usr/sbin/sysctl -n sysctl.proc_translated')


def rosetta_probe():
    """Whether x86_64 code runs here under Rosetta: a translated shell must read sysctl.proc_translated as 1.

    Nothing is installed. A launch error, a timeout, a failed probe or another
    value is missing equipment, and the record keeps the diagnostic."""
    record = dict(argv=list(ROSETTA_PROBE), status=None, stdout='', stderr='', error=None)
    try:
        result = subprocess.run(ROSETTA_PROBE, capture_output=True, text=True, timeout=20)
        record.update(status=result.returncode, stdout=result.stdout[:200], stderr=result.stderr[:1000])
    except (OSError, subprocess.TimeoutExpired) as exc:
        record['error'] = f'{type(exc).__name__}: {exc}'
    record['ok'] = record['status'] == 0 and record['stdout'] == '1\n'
    return record


def requirements(case, config, env, root, cache, probes=None):
    missing = []
    for name in case['requires']:
        if name not in cache:
            if name == 'pytest':
                ok = not case.get('engine_unavailable')
            elif name == 'rosetta':
                record = rosetta_probe()
                if probes is not None:
                    probes[name] = record
                ok = record['ok']
            elif name == 'app':
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
    if item['cases'][0].get('engine') == 'pytest':
        case = item['cases'][0]
        family = item.get('family')
        complete = bool(family and family['accounting_state'] == 'complete')
        item['case_results'] = [dict(id=case['id'], context=case['context'], engine='pytest',
            state='completed' if complete else 'unrun', status=('pass' if family['ok'] else 'fail') if complete else None,
            execution_state=family['execution_state'] if family else 'not_started',
            accounting_state=family['accounting_state'] if family else 'unavailable',
            family_report='suites/' + case['id'] + '/family.json' if family else None,
            reason=item.get('blocked_reason') or ('; '.join(family['errors']) if family else 'execution never began'),
            system_sleep_ms=item.get('system_sleep_ms'))]
        if not complete:
            problem(item, 'unrun_case', case['id'] + ': ' + item['case_results'][0]['execution_state'] + '/' + item['case_results'][0]['accounting_state'])
        if not family:
            print('FAMILY ' + case['id'] + ': not_started/unavailable; ' + str(item.get('blocked_reason')), flush=True)
        return
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
        if reason is None and item.get('state') == 'interrupted':
            reason = 'interrupted'
        if report:
            status = report['status']
            state = 'skipped' if status == 'skip' else 'completed'
            reason = report.get('message')
            if status == 'skip' and report.get('skip_reason') not in case['skip_reasons']:
                problem(item, 'unexpected_skip', f'{case["id"]}: skip is not declared by this case contract')
        else:
            problem(item, 'unrun_case', f'selected case has no readable terminal report: {case["id"]}')
        item['case_results'].append({'id': case['id'], 'context': case['context'],
                                     'state': state, 'status': status, 'reason': reason,
                                     'system_sleep_ms': item.get('system_sleep_ms')})


def run_standard_command(command, root, env, scope):
    # Own the ordinary case's process group so cancellation can reach helpers
    # even after the immediate child has exited. Stream output as before. The
    # case is a protected child: it holds the checkout lock descriptor, so the
    # hold outlives a killed dispatcher until the case's last descendant exits.
    with scope.popen(command, cwd=root, env=env, start_new_session=True) as process:
        try:
            return process.wait()
        except KeyboardInterrupt:
            previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                # Allow the case to handle SIGINT, then stop remaining group
                # members even when waiting for the leader already succeeded.
                for sig, timeout in ((signal.SIGINT, 1), (signal.SIGKILL, None)):
                    try:
                        os.killpg(process.pid, sig)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        pass
            finally:
                signal.signal(signal.SIGINT, previous)
            raise


def execute(root, out, run_id, started, plan, config, scope, collectors=None):
    collectors = collectors or {}
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
                    'system_sleep_ms': None, 'system_sleep_error': None,
                    'report_paths': [], 'reports': [], 'harness_errors': []}
                   for index, group in enumerate(groups)]
    caffeinate, idle_sleep_assertion = hold_idle_sleep()
    journal = out / 'dispatch.json'
    save(journal, {'run_id': run_id, 'invocations': invocations})
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_TEST_')}
    env.update(PW_APP_DIR=config['app_dir'], PW_BIN=config['pw_bin'], PW_BIN_PATH=config['pw_bin'],
               PW_TEST_OUT_DIR=str(out), PW_TEST_EVENTS=str(out / 'events.jsonl'),
               PW_TEST_RUN_ID=run_id, PW_TEST_QUIET='1' if config['quiet'] else '',
               PYTHONDONTWRITEBYTECODE='1')
    previous_events, previous_reports, seen_cases = b'', {}, {}
    interrupted, cache, outcomes, probes = False, {}, {}, {}
    integrity = None
    if any({'app', 'worker'} & set(c['requires']) for c in plan['cases']):
        integrity = {'app': config['app_dir'], 'valid_before': False, 'unchanged': None,
                     'report_dir': 'artifact-integrity', 'harness_errors': []}
        evidence = out / integrity['report_dir']
        evidence.mkdir()
        before = None
        try:
            before = artifact.inventory(Path(config['app_dir']))
            save(evidence / 'before.json', before)
            inspection = artifact.inspect(Path(config['app_dir']))
            save(evidence / 'inspection.json', inspection)
            integrity['valid_before'] = inspection['ok']
            if not inspection['ok']:
                integrity_error(integrity, 'artifact_invalid',
                                'selected app failed inspection; see artifact-integrity/inspection.json',
                                findings=inspection['errors'])
        except (OSError, ValueError) as exc:
            integrity_error(integrity, 'artifact_inspection_failed', str(exc))
        except KeyboardInterrupt:
            interrupted = True
            integrity_error(integrity, 'artifact_inspection_interrupted', 'artifact inspection interrupted')
        cache.update(app=integrity['valid_before'], worker=integrity['valid_before'])
    try:
        for item in invocations:
            group = item['cases']
            group_ids = {c['id'] for c in group}
            try:
                missing = [] if interrupted else sorted({req for c in group for req in requirements(c, config, env, root, cache, probes)})
            except (OSError, subprocess.TimeoutExpired) as exc:
                missing = [f'prerequisite check failed: {exc}']
            except KeyboardInterrupt:
                missing = []
                interrupted = True
            # Equipment observed by a probe keeps its raw record beside the invocation that required it.
            observed = {req: probes[req] for c in group for req in c['requires'] if req in probes}
            if observed:
                item['equipment'] = observed
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
                command = group[0].get('command')
                clocks_before = sleep_clocks()
                try:
                    if group[0].get('engine') == 'pytest':
                        item['family'], was_interrupted = collectors[group[0]['id']].execute(out, run_id, scope)
                        interrupted |= was_interrupted
                        returncode = 0 if item['family']['ok'] else 1
                    elif group[0]['context'] == 'standard':
                        returncode = run_standard_command(command, root, child_env, scope)
                    else:
                        returncode = subprocess.run(command, cwd=root, env=scope.child_env(child_env),
                                                    pass_fds=scope.pass_fds()).returncode
                    item.update(state='exited', returncode=returncode)
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
                item['system_sleep_ms'], item['system_sleep_error'] = system_sleep(clocks_before, sleep_clocks())
                if group[0].get('engine') != 'pytest':
                    previous_events, previous_reports = reconcile(item, out, run_id, previous_events,
                                                                  previous_reports, seen_cases, config['python']['realpath'])
            account(item)
            for case in item['case_results']:
                outcomes[case['id']] = case['status'] if not item['harness_errors'] else 'fail'
            save(journal, {'run_id': run_id, 'invocations': invocations})
    except KeyboardInterrupt:
        # Also account for cancellation between commands or during reconciliation.
        for item in invocations:
            if not item['case_results']:
                item.update(state='blocked', blocked_reason='interrupted')
                problem(item, 'interrupted', 'test execution interrupted')
                account(item)
        save(journal, {'run_id': run_id, 'invocations': invocations})
    finally:
        if integrity:
            # Cancellation must not suppress the final read-only inventory. Ignore
            # repeated Ctrl-C only for this bounded finalization step.
            previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                after = artifact.inventory(Path(config['app_dir']))
                save(evidence / 'after.json', after)
                if before is not None:
                    delta = artifact.changes(before, after)
                    save(evidence / 'changes.json', delta)
                    integrity['unchanged'] = not delta
                    if delta:
                        integrity_error(integrity, 'artifact_changed',
                                        'selected app changed during testing; see artifact-integrity/changes.json',
                                        paths=list(delta))
            except (OSError, ValueError) as exc:
                integrity_error(integrity, 'artifact_inventory_failed', str(exc))
            finally:
                signal.signal(signal.SIGINT, previous)
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            release_idle_sleep(caffeinate, idle_sleep_assertion)
        finally:
            signal.signal(signal.SIGINT, previous)
    return finish(out, run_id, started, invocations, plan, integrity, idle_sleep_assertion)


def integrity_error(integrity, code, message, **details):
    integrity['harness_errors'].append(dict(invocation=None, requested_suite='dispatcher',
                                           code=code, message=message, **details))
