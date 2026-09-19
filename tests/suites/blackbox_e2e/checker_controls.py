#!/usr/bin/env python3
"""Exercise the checker CLI with independently specified evidence and faults."""
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/fixtures/blackbox_e2e"
CHECKER = Path(__file__).with_name("validate_run.py")
sys.path.insert(0, str(ROOT / 'tests/lib'))
from consumer import recover_evidence, validate_evidence_shape


def consumer_controls(artifacts, baseline, current):
    """Constructed JSON interpretation and bounded loss controls, not native proof."""
    records = []

    def run(name, envelope, expected, reject=False):
        path = artifacts / ('consumer_' + name + '.json')
        path.write_text(json.dumps(envelope, indent=2) + '\n')
        answers = recover_evidence(envelope)
        (artifacts / ('consumer_' + name + '.answers.json')).write_text(json.dumps(answers, indent=2) + '\n')
        try:
            expected(answers)
        except AssertionError as exc:
            assert reject, (name, str(exc))
            records.append({'control': name, 'rejected': True, 'reason': str(exc)})
        else:
            assert not reject, name + ': loss escaped its consumer expectation'
            records.append({'control': name, 'rejected': False})

    def require(condition, reason):
        assert condition, reason

    def agreement(a):
        require(a['comparison_groups']['agreement'] == ['fs_write_allowed'], 'supported agreement must remain recoverable')

    run('supported_agreement', current, agreement)
    unknown = copy.deepcopy(current)
    unknown['data']['runner_result']['steps'][0]['comparison']['conclusion'] = 'unavailable'
    unknown['data']['runner_result']['steps'][0]['drift'] = None
    # Even a shape-valid null projection must not erase independently expected agreement.
    assert not validate_evidence_shape(unknown)
    run('blanket_unknown', unknown, agreement, reject=True)

    missing = copy.deepcopy(current)
    step = missing['data']['runner_result']['steps'][0]
    step['drift'] = None
    step['comparison'].update(prediction='unavailable', observation='unavailable',
        observation_basis='no_completed_worker_result', conclusion='unavailable',
        target_relation='different_submitted', limitations=[
            'query_attempt_order_unestablished', 'state_stability_unestablished',
            'prediction:validator_no_verdict', 'attempt:slot_incomplete', 'target:different_submitted'])
    step['sandbox_check'].update(outcome='error', result_source='synthetic', native_rc=None, missing_reason='validator_no_verdict')
    step['attempt'].update(outcome='not_run_worker_died', result_source='synthetic', native_rc=None, missing_reason='slot_incomplete')

    def simultaneous(a):
        s = a['steps'][0]
        require({'prediction:validator_no_verdict', 'attempt:slot_incomplete', 'target:different_submitted'} <= set(s['comparison']['limitations']), 'all simultaneous limits are required')
        require(s['prediction_missing_reason'] == 'validator_no_verdict' and s['attempt_missing_reason'] == 'slot_incomplete', 'distinct missing reasons must survive')
        require(a['failure_groups']['missing_result'] == ['fs_write_allowed'], 'missing result is not an observed failure')

    run('simultaneous_limits', missing, simultaneous)
    lost = copy.deepcopy(missing)
    lost['data']['runner_result']['steps'][0]['comparison']['limitations'].remove('target:different_submitted')
    assert not validate_evidence_shape(lost)
    run('lost_one_limit', lost, simultaneous, reject=True)

    spawned = copy.deepcopy(current)
    s = spawned['data']['runner_result']['steps'][0]
    s['comparison'].update(observation_basis='spawned_child', limitations=[
        'query_attempt_order_unestablished', 'state_stability_unestablished',
        'exec_query_not_full_spawn_prediction', 'exec_result_failed_after_spawn', 'sandbox_attribution_unestablished'])
    s['attempt'].update(requested_kind='exec', requested_action='spawn', outcome='exec_failed',
        rc=37, child_pid=123, child_exit_code=37, stdout='controlled child marker')

    def child_failure(a):
        s = a['steps'][0]
        require(s['failed_after_spawn'] and s['failure'] == 'unattributed_failure', 'failed exec result must survive successful spawn')
        require(s['comparison']['conclusion'] == 'agreement' and s['attempt']['child_exit_code'] == 37, 'spawn comparison and child result are independent')

    run('failed_after_spawn', spawned, child_failure)
    lost = copy.deepcopy(spawned)
    lost['data']['runner_result']['steps'][0]['comparison']['limitations'].remove('exec_result_failed_after_spawn')
    run('lost_failed_exec', lost, child_failure, reject=True)

    for version in (4, 5, 6):
        old = copy.deepcopy(baseline)
        old['data']['runner_result']['schema_version'] = version
        # Deliberately populate the old boolean to test absence of a new meaning.
        old['data']['runner_result']['steps'][0]['drift'] = False
        old['data']['runner_result']['steps'][0]['sandbox_check']['path_diagnostics'] = {'input':'/old','realpath_resolved':'/old'}
        def legacy(a):
            require(a['comparison_groups']['agreement'] == [], 'old false does not imply response-7 agreement')
            require(len(a['failure_groups']['not_reported']) == 3, 'legacy derivation must stay unreported')
            require(a['steps'][0]['drift'] is False and a['steps'][0]['path_reporting'] == 'provenance_not_reported', 'legacy value/provenance changed')
        run('legacy_' + str(version), old, legacy)

    # New controller evidence can accompany an old runner reply.
    logged = copy.deepcopy(old)
    event = {'pid':42, 'operation':'file-write-data', 'path':'/attempt', 'raw_line':'controlled denial'}
    match = {'step_id':'fs_write_allowed', 'operation':'file-write-data', 'operation_source':'submitted_attempt',
             'requested_kind':'file', 'requested_action':'open_write', 'path':'/attempt', 'path_sources':['submitted_attempt.target']}
    window = {'kind':'trailing', 'last':'10s', 'event_timestamps_available':False, 'exact_run_membership':False, 'step_ordering':False, 'pid_reuse_protection':False}
    logged['data']['sandbox_log_capture'] = {'capture_status':'captured', 'window':window,
        'deny_events':[event, dict(event, pid=99)], 'step_denies':[{'event_index':0,
        'candidate_step_ids':['fs_write_allowed'], 'association':'candidate', 'matching_evidence':[match]}]}
    logged['data']['runner_sandbox_diagnostics'] = {'capture_status':'captured', 'correlation_status':'pid_match', 'termination_cause':'unknown'}

    def candidate(a):
        d = a['denials']; c = d['candidates'][0]
        require(d['events'] == [event, dict(event,pid=99)], 'unmatched raw events must survive')
        require(c['event_index'] == 0 and c['event'] == event and c['association'] == 'candidate', 'candidate reference is not unique occurrence')
        require(c['matching_evidence'] == [match], 'matching provenance must survive')
        require(d['window'] == window and d['diagnostics']['termination_cause'] == 'unknown', 'capture limits and unknown cause must survive')

    run('legacy_with_controller_candidates', logged, candidate)
    lost = copy.deepcopy(logged)
    del lost['data']['sandbox_log_capture']['step_denies'][0]['matching_evidence'][0]['operation_source']
    run('lost_matching_owner', lost, candidate, reject=True)
    lost = copy.deepcopy(logged)
    lost['data']['sandbox_log_capture']['window']['exact_run_membership'] = True
    run('invented_exact_run', lost, candidate, reject=True)
    for status, correlation in [('captured','no_match'), ('blocked','unavailable'),
                                ('requested_unavailable','unavailable'), ('disabled','not_attempted'), ('no_worker','not_attempted')]:
        absent = copy.deepcopy(logged)
        absent['data']['runner_sandbox_diagnostics'].update(capture_status=status, correlation_status=correlation)
        absent['data']['sandbox_log_capture'] = (dict(capture_status=status, window=window,
            deny_events=[dict(event,pid=99)] if status=='captured' else None,
            step_denies=[] if status=='captured' else None, blocked_reason='controlled blockage' if status=='blocked' else None)
            if status not in ('disabled','no_worker') else None)
        def availability(a):
            d=a['denials']
            require((d['capture_status'],d['correlation_status']) == (status,correlation), 'capture states must remain distinct')
            require(d['candidates'] == ([] if status=='captured' else None), 'no match and no report differ')
            if status=='blocked': require(d['capture']['blocked_reason']=='controlled blockage', 'capture detail lost')
        run('capture_'+status, absent, availability)
    for name, runner, state in [('no_reply',None,'no_runner_reply'), ('no_steps',{'schema_version':7,'steps':[]},'no_admitted_steps')]:
        run(name, {'data':{'runner_result':runner}}, lambda a: require(a['step_reporting']==state and a['steps']==[], 'run absence must not invent step comparisons'))
    (artifacts / 'consumer-controls.json').write_text(json.dumps(records, indent=2) + '\n')


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    baseline = json.loads((FIXTURES / "checker/valid_run.json").read_text())
    prediction_error = "fs_write_allowed: expected sandbox_check allow"
    later_attempt_error = "mach_lookup_denied: expected attempt_ok=False"
    failures = []

    def check(name, envelope, diagnostics=(), case="BBX-001"):
        run_path = artifacts / f"{name}.json"
        run_path.write_text(json.dumps(envelope, indent=2) + "\n")
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(run_path),
             str(FIXTURES / case / "expected.json")],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout + result.stderr
        (artifacts / f"{name}.log").write_text(f"rc={result.returncode}\n{output}")
        expected_rc = 1 if diagnostics else 0
        if result.returncode != expected_rc or any(note not in output for note in diagnostics):
            failures.append(f"{name}: expected rc={expected_rc}, diagnostics={diagnostics!r}; "
                            f"got rc={result.returncode}, output={output!r}")
        else:
            print(f"{name}: ok", flush=True)

    check("valid", baseline)

    current = copy.deepcopy(baseline)
    current["data"]["runner_result"]["schema_version"] = 7
    for i, step in enumerate(current["data"]["runner_result"]["steps"]):
        step["attempt"].update(requested_kind="mach_lookup" if i == 2 else "file",
                               requested_action="bootstrap_look_up" if i == 2 else "open_write")
        step["drift"] = False if i == 0 else None
        step["comparison"] = dict(scope="submitted_operation_and_target",
            prediction="allow" if i == 0 else "deny",
            observation="succeeded" if i == 0 else "permission_failure",
            observation_basis="completed_worker_status" if i == 0 else "permission_errno",
            operation_relation="matched", target_relation="same_submitted",
            conclusion="agreement" if i == 0 else "directional_consistency",
            limitations=["query_attempt_order_unestablished", "state_stability_unestablished"])
        if i != 0:
            step['comparison']['limitations'].append('sandbox_attribution_unestablished')
        paths = step["sandbox_check"].get("path_diagnostics")
        if paths is not None:
            paths.update(observer="runner_host", phase="after_orchestration")
    check("response7", current)
    consumer_controls(artifacts, baseline, current)
    for label, change, diagnostic in [
        ('missing_intent', lambda s: s['attempt'].pop('requested_action'), 'missing attempt.requested_action'),
        ('missing_temporal_limit', lambda s: s['comparison']['limitations'].remove('state_stability_unestablished'), 'missing comparison limitation state_stability_unestablished'),
        ('host_as_validator', lambda s: s['sandbox_check'].update(path_diagnostics={'input':'/owned','observer':'validator','phase':'after_orchestration'}), 'path diagnostics lack host/phase provenance'),
    ]:
        lost = copy.deepcopy(current)
        change(lost['data']['runner_result']['steps'][0])
        check('response7_' + label, lost, (diagnostic,))
    lost = copy.deepcopy(current)
    lost['data']['runner_result']['steps'][1]['comparison']['limitations'].remove('sandbox_attribution_unestablished')
    check('response7_missing_attribution_limit', lost,
          ('missing comparison limitation sandbox_attribution_unestablished',))
    missing = copy.deepcopy(current)
    del missing["data"]["runner_result"]["steps"][0]["comparison"]
    check("response7_missing_comparison", missing, ("fs_write_allowed: missing comparison",))
    broken_current = copy.deepcopy(current)
    first, _, last = broken_current["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    last["attempt"] = None
    check("response7_malformed_independent_channels", broken_current,
          ("missing sandbox_check for fs_write_allowed", "missing attempt for mach_lookup_denied"))

    broken = copy.deepcopy(baseline)
    attempt = broken["data"]["runner_result"]["steps"][2]["attempt"]
    attempt.update(outcome="ok", rc=0, exit_code=0)
    check("wrong_later_attempt", broken, (later_attempt_error,))

    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("prediction_and_later_attempt", broken, (prediction_error, later_attempt_error))

    mismatch = copy.deepcopy(baseline)
    mismatch["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("wrong_prediction", mismatch, (prediction_error,))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][0]["attempt"].update(rc=-1, exit_code=-1)
    check("prediction_and_same_attempt", broken,
          (prediction_error, "fs_write_allowed: expected attempt_ok=True"))

    # Neither a malformed prediction object nor a missing attempt may prevent
    # the other channel or a sibling step from being checked.
    broken = copy.deepcopy(baseline)
    first, _, last = broken["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    first["attempt"].update(rc=-1, exit_code=-1)
    del last["attempt"]
    check("malformed_channels", broken,
          ("missing sandbox_check for fs_write_allowed",
           "fs_write_allowed: expected attempt_ok=True", "missing attempt for mach_lookup_denied"))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][2]["step_id"] = "fs_write_denied"
    check("prediction_and_duplicate_id", broken, (prediction_error, "expected step IDs in order"))

    broken = copy.deepcopy(baseline)
    broken["data"]["runner_result"]["steps"].reverse()
    check("reordered_steps", broken, ("expected step IDs in order",))

    missing = json.loads((FIXTURES / "checker/missing_path_run.json").read_text())
    check("expected_unavailable", missing, case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][2]["attempt"].update(rc=1, exit_code=1)
    check("unavailable_and_later_attempt", broken,
          ("fs_read_allowed: expected attempt_ok=True",), case="BBX-002")

    broken = copy.deepcopy(missing)
    del broken["data"]["runner_result"]["steps"][0]["drift"]
    check("unavailable_missing_drift", broken,
          ("fs_read_missing: expected unavailable prediction to have explicit drift=null",), case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["rc"] = 0
    check("unavailable_wrong_sentinel", broken,
          ("fs_read_missing: expected unavailable sandbox_check.rc=-1",), case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"].update(outcome="allow", rc=0, filter_type_id=1)
    check("invented_missing_path_prediction", broken,
          ("fs_read_missing: expected sandbox_check prediction_unavailable",), case="BBX-002")

    broken = copy.deepcopy(baseline)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["filter_type_id"] = None
    check("real_verdict_missing_filter_type", broken,
          ("fs_write_allowed: invalid sandbox_check.filter_type_id=None",))

    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
