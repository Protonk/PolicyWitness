"""Supplied evidence controls for live acceptance; no app or OS log access."""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import contract
from log_capture_contract import check_live_capture, check_observer_report
from consumer import denials
from check_deny_capture_window import checked_reads

NOW = 12_000_000_000


def supervision(boundary):
    budget = dict(timeout_ms=10000, timeout_source='default', started_monotonic_ns=1_000_000_000,
                  deadline_monotonic_ns=11_000_000_000)
    def stream(limit):
        return dict(limit_bytes=limit, bytes_read=0, bytes_retained=0, eof=True, truncated=False, read_error=None)
    outer = boundary == 'observer'
    return dict(boundary=boundary, budget=budget, reserve_ms=0 if outer else 1000, elapsed_ms=20, cutoff=None,
        stdout=stream(33554432 if outer else 1048576), stderr=stream(131072),
        process=dict(pid=101 if outer else 102, exit_observed=True, reaped=True, exit_code=0, term_signal=None, wait_error=None),
        cleanup=dict(scope='process_group' if outer else 'direct_child', target=101 if outer else 102,
            grace_ms=1000, ownership='owned', ownership_released=True,
            signal=9 if outer else None, signal_before_reap=outer,
            signal_result=dict(rc=0, errno=None) if outer else None,
            group_probe=dict(rc=-1, errno=3) if outer else None,
            outcome='group_absent' if outer else 'child_reaped', detail=None))


def complete(which=('early', 'late')):
    events = [dict(pid=42, process='pw-probe-runner', operation='file-read-data', path='/'+name,
                   raw_line='Sandbox: pw-probe-runner(42) deny(1) file-read-data /'+name) for name in which]
    window = dict(kind='runner_client_span', started_at_unix_ms=1000, ended_at_unix_ms=2500,
        pad_seconds=2, start='1969-12-31 23:59:59+0000', end='1970-01-01 00:00:05+0000',
        event_timestamps_available=False, exact_run_membership=False, step_ordering=False, pid_reuse_protection=False)
    inner = supervision('log_show')
    raw = '\n'.join(e['raw_line'] for e in events)
    inner['stdout'].update(bytes_read=len(raw), bytes_retained=len(raw))
    observer = dict(kind='sandbox_log_observer_report', data=dict(observer_schema_version=1, mode='show', pid=42,
        process_name='pw-probe-runner', start=window['start'], end=window['end'], last=None,
        log_rc=0, log_stdout=raw, log_stderr='', log_error=None, blocked_reason=None,
        log_truncated=False, observed_deny=bool(events), deny_events=events, collection=inner))
    outer = supervision('observer')
    associations = [dict(event_index=i, candidate_step_ids=[name], association='candidate',
        matching_evidence=[dict(step_id=name, operation='file-read-data', operation_source='submitted_attempt',
            requested_kind='file', requested_action='open_read', path='/'+name, path_sources=['submitted_attempt.target'])])
        for i, name in enumerate(which)]
    capture = dict(window=window, capture_status='captured', tool_exit_code=0, capture_limit_bytes=33554432,
        stdout_bytes_received=0, stdout_bytes_retained=0, stdout_truncated=False, stdout_raw=None,
        stdout_capture_error=None, stdout_parse_error=None, stderr_bytes_received=0, stderr_bytes_retained=0,
        stderr_truncated=False, stderr='', observer=observer, deny_events=events, observed_deny=bool(events),
        step_denies=associations, blocked_reason=None, supervision=outer, processing_cutoff=None)
    diag = dict(process_disposition='clean_exit', termination_cause=None, stop_reason='done',
        disposition_integrity='valid', disposition_issues=[],
        correlation_status='pid_match' if events else 'no_match',
        permission_failures_without_record=[name for name in ('early','late') if name not in which])
    return dict(schema_version=contract.CONTROLLER_ENVELOPE, result=dict(ok=True, exit_code=0, normalized_outcome='ok'), data=dict(
        runner_client=dict(started_at_unix_ms=1000, ended_at_unix_ms=2500, request_delivery=dict(bytes_written=2, error=None)),
        runner_result=dict(schema_version=contract.RESPONSE_SCHEMA, normalized_outcome='ok', runner_subprocess=dict(pid=42, exit_code=0),
            steps=[dict(step_id=name, attempt=dict(rc=-1, errno=1),
                        comparison=dict(observation='permission_failure')) for name in ('early','late')]),
        sandbox_log_capture=capture, runner_sandbox_diagnostics=diag))


def unavailable(e, status):
    c=e['data']['sandbox_log_capture']; d=e['data']['runner_sandbox_diagnostics']
    c.update(capture_status=status, step_denies=None)
    d.update(correlation_status='unavailable', permission_failures_without_record=None)


def limit_case(boundary, reason='output_overflow', stream='stdout'):
    e=complete(); c=e['data']['sandbox_log_capture']; d=c['observer']['data']
    report=c['supervision'] if boundary=='observer' else d['collection']
    if reason=='deadline':
        cutoff=dict(reason='deadline', stream=None, limit=None, observed=None, detail=None)
        report['elapsed_ms']=10000
    else:
        cap=report[stream]['limit_bytes']
        cutoff=dict(reason='output_overflow', stream=stream, limit=cap, observed=cap+1, detail=None)
        report[stream].update(bytes_read=cap+1, bytes_retained=cap, truncated=True, eof=False)
    report['cutoff']=cutoff
    unavailable(e, 'timeout' if reason=='deadline' else 'overflow')
    if boundary=='observer':
        for key in ('stdout','stderr'):
            c[key+'_bytes_received']=report[key]['bytes_read']; c[key+'_bytes_retained']=report[key]['bytes_retained']
            c[key+'_truncated']=report[key]['truncated']
        # A deadline may leave only a raw prefix; no fragment event recovery.
        if reason=='deadline' or stream=='stdout':
            c.update(observer=None, deny_events=None, observed_deny=None, stdout_raw='{"data":',
                     stdout_parse_error='EOF', stdout_capture_error='stream exceeded' if reason!='deadline' else None)
            report['stdout']['eof']=False
            if reason=='deadline':
                n=len(c['stdout_raw'].encode())
                report['stdout'].update(bytes_read=n,bytes_retained=n)
                c.update(stdout_bytes_received=n,stdout_bytes_retained=n)
    else:
        d.update(log_error=reason, log_truncated=reason!='deadline')
    return e


def projection(e):
    e=copy.deepcopy(e); e['data'].pop('sandbox_log_capture')
    for key in ('correlation_status','permission_failures_without_record'):
        e['data']['runner_sandbox_diagnostics'].pop(key)
    return e


def main():
    out=Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    records=[]
    def check(name, e, expected='captured', rejection=None, now_ns=NOW):
        # Model the serialized observer pipe independently of the assertions.
        c=e['data']['sandbox_log_capture']; r=c['supervision']
        if c.get('observer') is not None and not r['stdout']['truncated']:
            n=len(json.dumps(c['observer']).encode())
            r['stdout'].update(bytes_read=n,bytes_retained=n)
            c.update(stdout_bytes_received=n,stdout_bytes_retained=n)
        (out/(name+'.json')).write_text(json.dumps(e,indent=2)+'\n')
        try:
            result=check_live_capture(e, now_ns=now_ns)
            assert result['outcome']==expected, result
            assert projection(e)==projection(complete()), 'execution evidence changed'
        except AssertionError as error:
            assert rejection is not None and rejection in str(error), (name, str(error), rejection)
            records.append(dict(name=name, rejected=True, reason=str(error)))
        else:
            assert rejection is None, name+': invalid evidence was accepted'
            a=denials(e)
            assert a['capture']==e['data']['sandbox_log_capture']
            records.append(dict(name=name, rejected=False, result=result))
    for name, selected in [('full',('early','late')), ('early_only',('early',)), ('late_only',('late',)), ('empty',())]:
        check(name,complete(selected))
    for boundary in ('observer','log_show'):
        for stream in ('stdout','stderr'):
            check(boundary+'_'+stream+'_overflow',limit_case(boundary,stream=stream),'budget_exhausted')
        check(boundary+'_deadline',limit_case(boundary,'deadline'),'budget_exhausted')
    # Parsing may cross the inner reserved deadline just after the supervisor's
    # last elapsed-time sample. It must not wait for the outer deadline to count.
    for boundary, deadline, elapsed in [('log_show',10_000_000_000,8999), ('observer',11_000_000_000,9999)]:
        e=limit_case(boundary,'deadline'); c=e['data']['sandbox_log_capture']
        r=c['supervision'] if boundary=='observer' else c['observer']['data']['collection']
        r['elapsed_ms']=elapsed
        r['cutoff']['detail']='output parsing exceeded the collection deadline'
        check(boundary+'_parsing_deadline',e,'budget_exhausted',now_ns=deadline)
        check('reject_'+boundary+'_parsing_before_deadline',copy.deepcopy(e),
              rejection='deadline not observed',now_ns=deadline-1)
    e=limit_case('observer','deadline'); c=e['data']['sandbox_log_capture']; r=c['supervision']
    c.update(tool_exit_code=1,stdout_raw=None,stdout_parse_error=None,stdout_bytes_received=0,stdout_bytes_retained=0)
    r['process'].update(pid=None,exit_observed=False,reaped=False,exit_code=None)
    r['cleanup'].update(target=None,ownership='not_started',ownership_released=False,signal=None,
                        signal_result=None,signal_before_reap=False,group_probe=None,outcome='not_started')
    for stream in ('stdout','stderr'): r[stream].update(bytes_read=0,bytes_retained=0,eof=False)
    check('deadline_before_launch',e,'budget_exhausted')
    # Later processing may exhaust the shared deadline after both subprocesses
    # completed. No process status or retained evidence is changed to excuse it.
    processing=complete(); c=processing['data']['sandbox_log_capture']
    c['processing_cutoff']=dict(reason='deadline',stream=None,limit=None,observed=None,
                                detail='candidate association exceeded the collection deadline')
    unavailable(processing,'timeout'); check('processing_deadline',processing,'budget_exhausted')
    for stream,limit in [('matching_evidence',4096),('association_bytes',8388608),('reply_steps',256),('submitted_steps',256)]:
        e=complete(); c=e['data']['sandbox_log_capture']
        c['processing_cutoff']=dict(reason='correlation_overflow',stream=stream,limit=limit,observed=limit+1,detail=None)
        unavailable(e,'overflow'); check('correlation_'+stream,e,'budget_exhausted')
    e=complete(); c=e['data']['sandbox_log_capture']; c.update(observer=None,deny_events=None,observed_deny=None,
        stdout_raw='['+'0,'*262144+'0]',stdout_capture_error='observer JSON structure limit exceeded',
        processing_cutoff=dict(reason='json_structure_overflow',stream='json_punctuation',limit=262144,observed=262145,detail=None))
    n=len(c['stdout_raw'].encode()); c['supervision']['stdout'].update(bytes_read=n,bytes_retained=n)
    c.update(stdout_bytes_received=n,stdout_bytes_retained=n)
    unavailable(e,'overflow'); check('json_structure',e,'budget_exhausted')
    e=complete(); c=e['data']['sandbox_log_capture']; d=c['observer']['data']; event=d['deny_events'][0]
    d['deny_events']=[event]*8192; c['deny_events']=d['deny_events']
    d['collection']['cutoff']=dict(reason='event_overflow',stream='deny_events',limit=8192,observed=8193,detail=None)
    d.update(log_error='event_overflow',log_truncated=True)
    unavailable(e,'overflow'); check('event_limit',e,'budget_exhausted')

    # Unsupported statuses cannot borrow an unavailable projection as an excuse.
    for status in ('requested_unavailable','blocked','invalid_reply','window_mismatch','parse_error','capture_error','error','disabled'):
        e=complete(); unavailable(e,status); check('reject_'+status,e,rejection='unexpected live capture status')
    faults=[
        ('no_cutoff',lambda e:unavailable(e,'timeout'),'budget status without a cutoff'),
        ('missing_report',lambda e:e['data']['sandbox_log_capture'].update(observer=None,deny_events=None,observed_deny=None),'complete observer reply missing'),
        ('bad_bounds',lambda e:e['data']['sandbox_log_capture']['observer']['data'].update(end='1970-01-01 00:00:06+0000'),'wrong observer query bounds'),
        ('wrong_reserve',lambda e:e['data']['sandbox_log_capture']['observer']['data']['collection'].update(reserve_ms=0),'wrong report reserve'),
        ('old_envelope',lambda e:e.update(schema_version=contract.CONTROLLER_ENVELOPE-1),'read under controller envelope'),
        ('removed_diagnostic_copy',lambda e:e['data']['runner_sandbox_diagnostics'].update(capture_status='captured'),'removed diagnostic copy'),
        ('blocked_data',lambda e:e['data']['sandbox_log_capture']['observer']['data'].update(blocked_reason='Cannot run while sandboxed'),'required unified-log access blocked'),
        ('bad_shape',lambda e:e['data']['sandbox_log_capture']['observer']['data'].update(observer_schema_version=None),'malformed observer reply'),
        ('wrong_worker',lambda e:e['data']['sandbox_log_capture']['observer']['data'].update(pid=99),'wrong observer identity'),
        ('unfinished_pipe',lambda e:e['data']['sandbox_log_capture']['supervision']['stdout'].update(eof=False),'capture did not finish its pipes'),
        ('lost_ownership',lambda e:e['data']['sandbox_log_capture']['supervision']['cleanup'].update(ownership='lost'),'cleanup ownership not confirmed'),
        ('no_group_proof',lambda e:e['data']['sandbox_log_capture']['supervision']['cleanup'].update(group_probe=None),'group absence not established'),
        ('signal_after_reap',lambda e:e['data']['sandbox_log_capture']['supervision']['cleanup'].update(signal_before_reap=False),'unsupported cleanup signal'),
        ('bad_exit',lambda e:e['data']['sandbox_log_capture']['supervision']['process'].update(exit_code=7),'unexplained collector exit'),
        ('bad_reference',lambda e:e['data']['sandbox_log_capture']['step_denies'][0].update(event_index=9),'invalid/duplicate candidate reference'),
        ('invented_step',lambda e:e['data']['sandbox_log_capture']['step_denies'][0].update(candidate_step_ids=['invented']),'invalid candidate step IDs'),
        ('missing_diagnostic',lambda e:e['data']['runner_sandbox_diagnostics'].update(permission_failures_without_record=['early']),'missing-record diagnostics changed'),
        ('execution_changed',lambda e:e['result'].update(ok=False),'execution evidence changed'),
    ]
    for name,mutate,reason in faults:
        e=complete(); mutate(e); check('reject_'+name,e,rejection=reason)
    for name,mutate,reason in [
        ('wrong_limit',lambda c:c['supervision']['cutoff'].update(limit=999),'cutoff did not cross'),
        ('no_excess',lambda c:c['supervision']['cutoff'].update(observed=33554432),'cutoff did not cross'),
        ('unknown_reason',lambda c:c['supervision']['cutoff'].update(reason='decode_error'),'unexpected collection failure'),
        ('incomplete_cleanup',lambda c:c['supervision']['cleanup'].update(outcome='unconfirmed',detail='cleanup grace exhausted'),'unresolved wait or cleanup'),
        ('partial_association',lambda c:c.update(step_denies=[]),'partial capture gained correlation'),
    ]:
        e=limit_case('observer'); mutate(e['data']['sandbox_log_capture']); check('reject_'+name,e,rejection=reason)
    e=limit_case('observer','deadline'); e['data']['sandbox_log_capture']['supervision']['elapsed_ms']=1
    check('reject_premature_deadline',e,rejection='deadline not observed')
    e=limit_case('observer','deadline'); e['data']['sandbox_log_capture']['supervision']['stdout']['eof']=True
    check('reject_malformed_complete_after_timeout',e,rejection='malformed complete observer reply')
    e=complete(); b=e['data']['sandbox_log_capture']['observer']['data']['collection']['budget']
    b['started_monotonic_ns']+=1; b['deadline_monotonic_ns']+=1
    check('reject_restarted_budget',e,rejection='observer restarted the deadline')
    # The actual live window content checker must not interpret a truncated
    # diagnostic path as a completed query's record or candidate.
    partial=limit_case('log_show'); c=partial['data']['sandbox_log_capture']
    c['deny_events'][0].update(path='/trunc',raw_line='truncated diagnostic')
    assert checked_reads(c,42,-1,5,{'/early':'early','/late':'late'})==[]
    empty=complete(())['data']['sandbox_log_capture']
    assert checked_reads(empty,42,-1,5,{'/early':'early','/late':'late'})==[]
    full=complete()['data']['sandbox_log_capture']
    for event in full['deny_events']:
        event['raw_line']='1970-01-01 00:00:02.000000+0000 localhost kernel[0]: '+event['raw_line']
    assert len(checked_reads(full,42,-1,5,{'/early':'early','/late':'late'}))==2
    records.append(dict(name='partial_read_is_diagnostic',rejected=False))
    # The retired invocation is allowed to observe a record absent in the first
    # capture. Each invocation independently validates its own bounds and facts.
    first=complete(()); later=complete(('late',))
    check('earlier_empty',first)
    d=later['data']['sandbox_log_capture']['observer']['data']
    assert check_observer_report(later['data']['sandbox_log_capture']['observer'],42,d['start'],d['end'],now_ns=NOW) is None
    records.append(dict(name='later_record_is_independent',rejected=False))
    (out/'controls.json').write_text(json.dumps(records,indent=2)+'\n')
    print('%d live-capture acceptance and rejection controls passed' % len(records))


if __name__=='__main__':
    main()
