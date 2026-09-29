"""Assertions for live best-effort log evidence, independent of OS emission.

A completed query may be empty. A budget cutoff needs observations at the
reported boundary and confirmed cleanup; it is never positive capture coverage.
Callers still assert their native execution and specimen-specific candidates.
"""
import errno
import json
import time
from datetime import datetime, timezone
from pathlib import Path

LIMITS = {row['id']: row['value'] for row in json.loads(
    (Path(__file__).resolve().parents[2] / 'docs/limits.json').read_text())['limits']}
FLAGS = ('event_timestamps_available', 'exact_run_membership', 'step_ordering', 'pid_reuse_protection')


def require(ok, reason):
    assert ok, reason


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def stamp(seconds):
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S+0000')


def check_window(window, client):
    require(isinstance(window, dict), 'missing scan window')
    start, end = client['started_at_unix_ms'], client['ended_at_unix_ms']
    require(integer(start) and integer(end) and end >= start, 'live client clock reversed or invalid')
    require(window.get('kind') == 'runner_client_span' and 'last' not in window, 'wrong window kind')
    require((window.get('started_at_unix_ms'), window.get('ended_at_unix_ms')) == (start, end), 'raw client span changed')
    require(window.get('pad_seconds') == 2, 'missing scan padding')
    require((window.get('start'), window.get('end')) == (stamp(start // 1000 - 2), stamp((end + 999) // 1000 + 2)), 'wrong padded bounds')
    require(all(window.get(key) is False for key in FLAGS), 'unsupported temporal claim')


def check_budget(budget, timeout_ms, timeout_source):
    require(isinstance(budget, dict), 'missing collection budget')
    require(budget.get('timeout_ms') == timeout_ms and budget.get('timeout_source') == timeout_source, 'wrong effective timeout')
    start, end = budget.get('started_monotonic_ns'), budget.get('deadline_monotonic_ns')
    require(integer(start) and integer(end) and end - start == timeout_ms * 1_000_000, 'inconsistent shared deadline')


def check_cutoff(cutoff, boundary, report, now_ns):
    require(isinstance(cutoff, dict), 'missing cutoff observations')
    reason, stream = cutoff.get('reason'), cutoff.get('stream')
    if reason == 'deadline':
        require(all(cutoff.get(key) is None for key in ('stream', 'limit', 'observed')), 'deadline misreported as byte limit')
        # elapsed_ms is measured from the shared budget start. Parsing/association
        # can expire after the supervisor's last measurement; check the same OS
        # monotonic clock independently when that later phase is named.
        require(report['elapsed_ms'] >= report['budget']['timeout_ms'] - report['reserve_ms'] or
                (isinstance(cutoff.get('detail'), str) and bool(cutoff['detail']) and
                 now_ns >= report['budget']['deadline_monotonic_ns']), 'deadline not observed')
    else:
        allowed = {
            'observer': {'output_overflow': {'stdout': 'log_observer_output', 'stderr': 'log_observer_stderr'}},
            'log_show': {'output_overflow': {'stdout': 'log_show_stdout', 'stderr': 'log_show_stderr'},
                         'event_overflow': {'deny_events': 'log_deny_events'}},
            'controller': {'json_structure_overflow': {'json_punctuation': 'log_reply_structure'},
                           'event_overflow': {'deny_events': 'log_deny_events'},
                           'correlation_overflow': {'reply_steps': 'log_correlation_steps',
                               'submitted_steps': 'log_correlation_steps', 'deny_events': 'log_deny_events',
                               'matching_evidence': 'log_candidate_count', 'association_bytes': 'log_candidate_bytes'}},
        }
        ident = allowed.get(boundary, {}).get(reason, {}).get(stream)
        require(ident is not None, 'unexpected collection failure: %s/%s/%s' % (boundary, reason, stream))
        require(cutoff.get('limit') == LIMITS[ident] and integer(cutoff.get('observed')) and
                cutoff['observed'] > cutoff['limit'], 'cutoff did not cross the declared limit')
        if reason == 'output_overflow':
            obs = report[stream]
            require(obs['truncated'] is True and obs['bytes_read'] == cutoff['observed'] and
                    obs['bytes_retained'] == cutoff['limit'], 'overflow lacks stream evidence')
    return dict(boundary=boundary, **cutoff)


def check_supervision(report, boundary, timeout_ms, timeout_source, now_ns):
    require(isinstance(report, dict) and report.get('boundary') == boundary, 'missing/wrong supervision boundary')
    require(report.get('reserve_ms') == (LIMITS['log_report_reserve'] if boundary == 'log_show' else 0), 'wrong report reserve')
    check_budget(report.get('budget'), timeout_ms, timeout_source)
    require(integer(report.get('elapsed_ms')), 'missing elapsed observation')
    cutoff = report.get('cutoff')
    for name in ('stdout', 'stderr'):
        obs = report.get(name)
        ident = ('log_observer_output' if name == 'stdout' else 'log_observer_stderr') if boundary == 'observer' else 'log_show_' + name
        require(isinstance(obs, dict) and obs.get('limit_bytes') == LIMITS[ident], 'wrong stream budget')
        read, kept, limit = obs.get('bytes_read'), obs.get('bytes_retained'), obs['limit_bytes']
        require(integer(read) and integer(kept) and kept == min(read, limit) and read <= limit + 1, 'inconsistent bounded byte counts')
        require(obs.get('truncated') is (read > limit) and type(obs.get('eof')) is bool, 'inconsistent pipe observations')
        require(obs.get('read_error') is None, 'unexpected pipe read failure')
        if cutoff is None:
            require(obs['eof'] and not obs['truncated'], 'capture did not finish its pipes')
    process, cleanup = report.get('process'), report.get('cleanup')
    require(isinstance(process, dict) and isinstance(cleanup, dict), 'missing process/cleanup facts')
    require(process.get('wait_error') is None and cleanup.get('detail') is None, 'unresolved wait or cleanup')
    require(cleanup.get('grace_ms') == LIMITS['log_cleanup_grace'], 'wrong cleanup grace')
    scope = 'process_group' if boundary == 'observer' else 'direct_child'
    require(cleanup.get('scope') == scope, 'wrong cleanup ownership scope')
    if process.get('pid') is None:
        require(isinstance(cutoff, dict) and cutoff.get('reason') == 'deadline', 'required collector did not launch')
        require(cleanup.get('target') is None and cleanup.get('ownership') == 'not_started' and
                cleanup.get('outcome') == 'not_started' and cleanup.get('ownership_released') is False and
                cleanup.get('signal') is None and cleanup.get('signal_result') is None and
                cleanup.get('group_probe') is None and cleanup.get('signal_before_reap') is False,
                'unstarted collector has cleanup claims')
        require(process.get('exit_observed') is False and process.get('reaped') is False and
                process.get('exit_code') is None and process.get('term_signal') is None and
                all(report[k]['bytes_read'] == 0 and report[k]['eof'] is False for k in ('stdout', 'stderr')),
                'unstarted collector has process/output claims')
    else:
        require(integer(process['pid'], 1) and process.get('exit_observed') is True and process.get('reaped') is True, 'collector wait incomplete')
        require(cleanup.get('target') == process['pid'] and cleanup.get('ownership') == 'owned' and
                cleanup.get('ownership_released') is True, 'cleanup ownership not confirmed')
        signal = cleanup.get('signal')
        if signal is not None:
            call = cleanup.get('signal_result')
            require(signal == 9 and cleanup.get('signal_before_reap') is True and isinstance(call, dict) and
                    ((call.get('rc') == 0 and call.get('errno') is None) or
                     (call.get('rc') == -1 and integer(call.get('errno'), 1))), 'unsupported cleanup signal')
        else:
            require(cleanup.get('signal_before_reap') is False and cleanup.get('signal_result') is None, 'signal claims without a request')
        if boundary == 'observer':
            require(signal == 9 and cleanup.get('outcome') == 'group_absent' and
                    cleanup.get('group_probe') == {'rc': -1, 'errno': errno.ESRCH}, 'group absence not established')
        else:
            require(cleanup.get('outcome') == 'child_reaped' and cleanup.get('group_probe') is None, 'child cleanup not confirmed')
        normal = process.get('exit_code') == 0 and process.get('term_signal') is None
        killed = process.get('exit_code') is None and process.get('term_signal') == 9 and signal == 9
        require(normal or (cutoff is not None and killed), 'unexplained collector exit')
    return None if cutoff is None else check_cutoff(cutoff, boundary, report, now_ns)


def check_observer_report(observer, pid, start, end, *, timeout_ms=10000, timeout_source='default', now_ns=None):
    """Validate one standalone or embedded observer invocation on its own facts."""
    now_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC) if now_ns is None else now_ns
    require(isinstance(observer, dict) and observer.get('kind') == 'sandbox_log_observer_report', 'missing observer report')
    data = observer.get('data')
    require(isinstance(data, dict) and data.get('observer_schema_version') == 1 and data.get('mode') == 'show', 'malformed observer reply')
    require(data.get('pid') == pid and data.get('process_name') == 'pw-probe-runner', 'wrong observer identity')
    require((data.get('start'), data.get('end'), data.get('last')) == (start, end, None), 'wrong observer query bounds')
    require(data.get('blocked_reason') is None, 'required unified-log access blocked; see tests/README.md sandboxed-harness procedure')
    cutoff = check_supervision(data.get('collection'), 'log_show', timeout_ms, timeout_source, now_ns)
    report = data['collection']
    require(data.get('log_rc') == report['process']['exit_code'], 'log exit differs from wait result')
    require(isinstance(data.get('log_stdout'), str) and isinstance(data.get('log_stderr'), str), 'missing log stream diagnostics')
    events = data.get('deny_events')
    require(isinstance(events, list) and len(events) <= LIMITS['log_deny_events'], 'invalid retained event array')
    require(data.get('observed_deny') is bool(events), 'observed_deny differs from retained events')
    require(all(isinstance(e, dict) and isinstance(e.get('raw_line'), str) for e in events), 'malformed retained event')
    truncated = report['stdout']['truncated'] or report['stderr']['truncated'] or (cutoff is not None and cutoff['reason'] == 'event_overflow')
    require(data.get('log_truncated') is truncated, 'log truncation differs from collection facts')
    if cutoff is None:
        require(data.get('log_error') is None, 'unexplained log error')
        for key in ('stdout', 'stderr'):
            require(len(data['log_' + key].encode()) == report[key]['bytes_retained'], 'log diagnostic byte count changed')
    else:
        require(data.get('log_error') == cutoff['reason'], 'cutoff diagnostic missing')
        if cutoff['reason'] == 'event_overflow':
            require(len(events) == cutoff['limit'] and cutoff['observed'] == cutoff['limit'] + 1, 'event limit lacks retained prefix')
    return cutoff


def check_live_capture(envelope, *, timeout_ms=10000, timeout_source='default', now_ns=None):
    """Return a classification; raise for missing evidence or unexpected failures."""
    now_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC) if now_ns is None else now_ns
    require(integer(envelope.get('schema_version'), 4), 'collection facts require controller envelope 4')
    data = envelope['data']
    capture, diag = data.get('sandbox_log_capture'), data.get('runner_sandbox_diagnostics')
    require(isinstance(capture, dict) and isinstance(diag, dict), 'known worker requires capture and diagnostics')
    status = capture.get('capture_status')
    require(status in ('captured', 'timeout', 'overflow'), 'unexpected live capture status: %s' % status)
    require(diag.get('capture_status') == status, 'capture status projection changed')
    pid = data['runner_result']['runner_subprocess']['pid']
    require(integer(pid, 1) and diag.get('worker_pid') == pid, 'missing authoritative worker identity')
    check_window(capture.get('window'), data['runner_client'])
    outer = capture.get('supervision')
    outer_cutoff = check_supervision(outer, 'observer', timeout_ms, timeout_source, now_ns)
    require(capture.get('capture_limit_bytes') == LIMITS['log_observer_output'], 'wrong receiver budget')
    require(capture.get('tool_exit_code') == (outer['process']['exit_code'] if outer['process']['exit_code'] is not None else 1), 'receiver exit differs from wait result')
    for name in ('stdout', 'stderr'):
        require(capture.get(name + '_bytes_received') == outer[name]['bytes_read'] and
                capture.get(name + '_bytes_retained') == outer[name]['bytes_retained'] and
                capture.get(name + '_truncated') is outer[name]['truncated'], 'receiver/pipe observations differ')
    raw_prefix = capture.get('stdout_raw')
    if raw_prefix is not None:
        require(isinstance(raw_prefix, str) and len(raw_prefix.encode()) <= 3 * outer['stdout']['bytes_retained'],
                'raw diagnostic exceeds observed retention')
    require(capture.get('blocked_reason') is None, 'required log access blocked')
    observer = capture.get('observer')
    inner_cutoff = None
    if observer is not None:
        minimum_bytes = len(json.dumps(observer, ensure_ascii=False, separators=(',', ':')).encode())
        require(outer['stdout']['bytes_retained'] >= minimum_bytes, 'intact observer reply lacks transport bytes')
        inner_cutoff = check_observer_report(observer, pid, capture['window']['start'], capture['window']['end'],
                                            timeout_ms=timeout_ms, timeout_source=timeout_source, now_ns=now_ns)
        require(observer['data']['collection']['budget'] == outer['budget'], 'observer restarted the deadline')
        require(capture.get('deny_events') == observer['data']['deny_events'] and
                capture.get('observed_deny') == observer['data']['observed_deny'], 'retained observer evidence changed')
    else:
        require(capture.get('deny_events') is None and capture.get('observed_deny') is None, 'events recovered from a missing reply')
        require(outer_cutoff is not None or capture.get('processing_cutoff') is not None, 'complete observer reply missing')
        if capture.get('stdout_parse_error') is not None:
            require(not outer['stdout']['eof'] or outer['stdout']['truncated'], 'malformed complete observer reply')
    processing = capture.get('processing_cutoff')
    processing_cutoff = None if processing is None else check_cutoff(processing, 'controller', outer, now_ns)
    if processing_cutoff is not None and processing_cutoff['reason'] == 'json_structure_overflow':
        require(isinstance(raw_prefix, str) and outer['stdout']['bytes_read'] >= processing_cutoff['observed'],
                'JSON cutoff lacks input bytes')
    cutoffs = [c for c in (outer_cutoff, inner_cutoff, processing_cutoff) if c is not None]
    if status == 'captured':
        require(not cutoffs and observer is not None and capture.get('stdout_parse_error') is None and
                capture.get('stdout_capture_error') is None, 'captured without complete collection')
        events, associations = capture['deny_events'], capture.get('step_denies')
        require(isinstance(associations, list), 'complete capture lacks correlation result')
        matches = [i for i, event in enumerate(events) if event.get('pid') == pid]
        require(diag.get('correlation_status') == ('pid_match' if matches else 'no_match') and
                diag.get('first_deny') == ({'event_index': matches[0]} if matches else None), 'incorrect first-deny/correlation projection')
        seen, candidates = set(), set()
        steps = {s['step_id']: s for s in data['runner_result']['steps']}
        for association in associations:
            index, ids = association.get('event_index'), association.get('candidate_step_ids')
            require(integer(index) and index in matches and index not in seen, 'invalid/duplicate candidate reference')
            require(isinstance(ids, list) and ids and len(set(ids)) == len(ids) and all(i in steps for i in ids), 'invalid candidate step IDs')
            require(association.get('association') == ('candidate' if len(ids) == 1 else 'ambiguous'), 'ambiguity changed')
            evidence = association.get('matching_evidence')
            require(isinstance(evidence, list) and [m.get('step_id') for m in evidence] == ids, 'missing matching evidence')
            for match in evidence:
                require(match.get('operation') == events[index].get('operation') and match.get('path') == events[index].get('path') and
                        match.get('operation_source') == 'submitted_attempt' and bool(match.get('path_sources')), 'candidate lacks provenance')
            seen.add(index)
            candidates.update(ids)
        missing = [s['step_id'] for s in steps.values() if s.get('comparison', {}).get('observation') == 'permission_failure' and s['step_id'] not in candidates]
        require(diag.get('permission_failures_without_record') == missing, 'missing-record diagnostics changed')
    else:
        require(cutoffs, 'budget status without a cutoff')
        first = outer_cutoff or processing_cutoff or inner_cutoff
        require(status == ('timeout' if first['reason'] == 'deadline' else 'overflow'), 'budget status disagrees with cutoff')
        require(diag.get('correlation_status') == 'unavailable' and capture.get('step_denies') is None and
                diag.get('first_deny') is None and diag.get('permission_failures_without_record') is None, 'partial capture gained correlation')
    return {'capture_status': status, 'outcome': 'captured' if status == 'captured' else 'budget_exhausted', 'cutoffs': cutoffs}
