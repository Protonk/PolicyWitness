#!/usr/bin/env python3
"""Exercise the checker CLI with independently specified evidence and faults.

Every control here is authored against the current contract: the consumer's
version gate, the uniform data skeleton, the D1 comparison record, the
ordering chain and the reporting-failure rules. The current baseline is explicitly constructed ordinary evidence. Historical
captures are retained only for previous-version refusal. Live BBX cases own
native observations; these controls establish interpretation and rejection.
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/fixtures/blackbox_e2e"
CHECKER = Path(__file__).with_name("validate_run.py")
sys.path.insert(0, str(ROOT / 'tests/lib'))
import contract
import build_context
from blackbox import bind_constructed_envelope, envelope_skeleton, recapture_host_reply
from consumer import lifecycle as live_lifecycle, select, steps as live_steps, validate_fixture as validate, validate_exec_observation
from functools import partial
lifecycle = partial(live_lifecycle, expected_contract=build_context.TEST_CONTRACT)
steps = partial(live_steps, expected_contract=build_context.TEST_CONTRACT)
from lifecycle_adapter import read_lifecycle as live_read_lifecycle
read_lifecycle = partial(live_read_lifecycle, expected_contract=build_context.TEST_CONTRACT)
from lifecycle_oracle import check_fixture_record as check_record
from path_diagnostics_contract import check_cases
from worker_exit_witness import worker_exit_witness
from runner_client_capture import validate_capture


def policy_check_controls(run):
    """Constructed captures distinguish rejected payloads from admitted helper data."""
    base = envelope_skeleton({'producer': build_context.producer(),
        'normalized_outcome': 'xpc_error', 'rc': 1, 'error': 'controlled XPC failure',
        'steps': [], 'phases': []}, ok=False)
    helper = {
        'build': build_context.producer(), 'kind': 'sbpl_check',
        'result': {'normalized_outcome': 'ok', 'ok': True, 'exit_code': 0, 'error': None},
        'data': {'policy_format': 'sbpl', 'policy_sha256': 'f' * 64,
                 'params_present': False, 'params_count': 0,
                 'compile': {'stage': 'compile', 'ok': True, 'error': None},
                 'import_inventory': {'records': [], 'truncated': False, 'cycle': None,
                                      'policy_closure_sha256': 'f' * 64}},
    }

    def capture(payload, status):
        document = copy.deepcopy(base)
        size = len(json.dumps(payload).encode('utf-8'))
        document['data']['policy_check'] = {
            'status': status, 'tool_exit_code': 17, 'envelope': copy.deepcopy(payload),
            'capture_limit_bytes': 8 * 1024 * 1024, 'stdout_bytes_received': size,
            'stdout_bytes_retained': size, 'stdout_truncated': False,
            'stdout_capture_error': None, 'stdout_parse_error': None, 'stdout_raw': None,
            'stderr': '', 'stderr_bytes_received': 0, 'stderr_bytes_retained': 0,
            'stderr_truncated': False,
        }
        return document

    def check(name, document, rejected_by=None):
        before = copy.deepcopy(document)
        run('policy_check_' + name, document, rejected_by=rejected_by)
        assert document == before, (name, 'validation changed the retained evidence')

    # Neither process exit nor compile.ok supplies another verdict. Unfamiliar
    # outcomes, including strings also used for transport statuses, are admitted.
    for outcome in ('ok', 'compile_error', 'setup_error', 'bad_request', 'policy_too_large',
                    'future_outcome', 'invalid_reply', 'tool_error'):
        payload = copy.deepcopy(helper)
        payload['result']['normalized_outcome'] = outcome
        check('admitted_' + outcome, capture(payload, outcome))

    rejected = [('array', [helper]), ('string', 'unrecognized reply'), ('number', 7),
                ('boolean', False), ('null', None), ('object', {'unknown': ['retained', None]})]
    for name, change in [
        ('wrong_kind', lambda p: p.update(kind='another_helper')),
        ('missing_kind', lambda p: p.pop('kind')),
        ('previous_version', lambda p: p.update(build={"contract": "test:previous"})),
        ('next_version', lambda p: p.update(build={"contract": "test:next"})),
        ('integer_contract', lambda p: p.update(build={"contract": 6})),
        ('fractional_contract', lambda p: p.update(build={"contract": 6.5})),
        ('boolean_contract', lambda p: p.update(build={"contract": True})),
        ('missing_contract', lambda p: p.pop('build')),
        ('missing_result', lambda p: p.pop('result')),
        ('nonobject_result', lambda p: p.update(result=[])),
        ('missing_outcome', lambda p: p['result'].pop('normalized_outcome')),
        ('null_outcome', lambda p: p['result'].update(normalized_outcome=None)),
        ('empty_outcome', lambda p: p['result'].update(normalized_outcome='')),
        ('numeric_outcome', lambda p: p['result'].update(normalized_outcome=1)),
    ]:
        payload = copy.deepcopy(helper)
        change(payload)
        # No refused body is interpreted, regardless of why admission failed.
        # These controls supply no historical helper reader.
        payload['data'] = {'unrecognized': {'retained': [1, False, None]}}
        rejected.append((name, payload))
    for name, payload in rejected:
        check('retained_' + name, capture(payload, 'invalid_reply'))
        check('mislabelled_' + name, capture(payload, 'ok'),
              'policy_check.status requires an admitted helper envelope')

    # Other wrapper fields remain governed by the current golden even when
    # the payload is opaque.
    for name, change, diagnostic in [
        ('wrapper_unknown', lambda c: c.update(compiled=True),
         'unknown key envelope.data.policy_check.compiled'),
        ('wrapper_type', lambda c: c.update(tool_exit_code='17'),
         'envelope.data.policy_check.tool_exit_code is string, not number'),
    ]:
        document = capture([], 'invalid_reply')
        change(document['data']['policy_check'])
        check(name, document, diagnostic)

    # Admitted helper bodies retain the normal shape checks. An outcome named
    # invalid_reply is still an admitted outcome, so it cannot bypass them.
    for outcome in ('ok', 'invalid_reply'):
        for name, change, diagnostic in [
            ('unknown', lambda p: p['data'].update(unrecognized=True),
             'unknown key envelope.data.policy_check.envelope.data.unrecognized'),
            ('type', lambda p: p['data']['compile'].update(ok='yes'),
             'envelope.data.policy_check.envelope.data.compile.ok is string, not boolean'),
        ]:
            payload = copy.deepcopy(helper)
            payload['result']['normalized_outcome'] = outcome
            change(payload)
            check('admitted_' + outcome + '_' + name, capture(payload, outcome), diagnostic)
    check('outcome_mismatch', capture(helper, 'compile_error'),
          'policy_check.status differs from the admitted helper outcome')
    check('admitted_marked_invalid', capture(helper, 'invalid_reply'),
          'policy_check.status differs from the admitted helper outcome')
    for status in ('unavailable', 'capture_error', 'parse_error', 'tool_error'):
        document = copy.deepcopy(base)
        document['data']['policy_check'] = {'status': status, 'envelope': None}
        check('without_reply_' + status, document)


def exec_observation_controls(artifacts):
    cases = json.loads((ROOT / 'tests/fixtures/contract/exec_observation.json').read_text())
    receipts = []
    for section in ('valid', 'invalid'):
        for case in cases[section]:
            errors = validate_exec_observation(case['attempt'])
            assert bool(errors) == (section == 'invalid'), (section, case['name'], errors)
            if case['name'] in ('old_producer_absent', 'null_unknown'):
                # Validating absence must not manufacture a negative cleanup fact.
                assert case['attempt'].get('exec_observation') is None
            receipts.append({'case': case['name'], 'accepted': not errors, 'errors': errors})
    (artifacts / 'exec-observation-reader-controls.json').write_text(json.dumps(receipts, indent=2) + '\n')


def diagnostic_subject_controls(run, current):
    """Constructed reference-form controls, independent of finding predicates."""
    absent = object()

    def document(path, actor_scope=False):
        envelope = copy.deepcopy(current)
        issue = dict(kind='constructed_reference', detail='authored reference-form control')
        if path is not absent:
            issue['subject_path'] = copy.deepcopy(path)
        diagnostics = envelope['data']['runner_sandbox_diagnostics']
        # These authored scopes exercise reference reading. The consumer does
        # not certify which predicate produced a finding or recompute its
        # projection. Product-emitted gate associations have their own corpus.
        if actor_scope:
            diagnostics['actors'] = [dict(actor_id='constructed-scope',
                process_disposition='withheld', termination_cause='unknown', stop_reason=None,
                disposition_integrity='invalid', disposition_issues=[issue])]
        else:
            diagnostics.update(process_disposition='withheld', termination_cause='unknown',
                               disposition_integrity='invalid', disposition_issues=[issue])
        return envelope

    positives = [
        ('absent', absent),
        ('root', []),
        ('object', ['steps', '0', 'attempt']),
        ('nonzero_index', ['steps', '1', 'attempt']),
        ('scalar_target', ['steps', '0', 'attempt', 'rc']),
        ('null_target', ['steps', '0', 'attempt', 'errno']),
    ]
    negatives = [
        ('null_path', None, 'must be an array of strings'),
        ('string_path', 'steps.0.attempt', 'must be an array of strings'),
        ('numeric_component', ['steps', 0, 'attempt'], 'must be an array of strings'),
        ('boolean_component', ['steps', True, 'attempt'], 'must be an array of strings'),
        ('leading_zero', ['steps', '01', 'attempt'], 'not a canonical array position'),
        ('negative_index', ['steps', '-1', 'attempt'], 'not a canonical array position'),
        ('decimal_index', ['steps', '1.0', 'attempt'], 'not a canonical array position'),
        ('unicode_index', ['steps', '\u0661', 'attempt'], 'not a canonical array position'),
        ('missing_index', ['steps', '3', 'attempt'], 'outside the retained array'),
        ('oversized_index', ['steps', '9' * 128], 'outside the retained array'),
        ('missing_key', ['steps', '0', 'absent'], 'names an absent object key'),
        ('scalar_traversal', ['steps', '0', 'attempt', 'rc', 'child'], 'traverses a non-container'),
        ('null_traversal', ['steps', '0', 'attempt', 'errno', 'child'], 'traverses a non-container'),
        ('wrong_root', ['data', 'runner_result', 'steps'], 'names an absent object key'),
    ]
    assert len(current['data']['runner_result']['steps']) == 3
    assert current['data']['runner_result']['steps'][0]['attempt']['errno'] is None
    for actor_scope in (False, True):
        scope = 'actor' if actor_scope else 'aggregate'
        for name, path in positives:
            envelope = document(path, actor_scope)
            before = copy.deepcopy(envelope)
            run('subject_' + scope + '_' + name, envelope)
            assert envelope == before, 'reference reading changed retained evidence or projections'
        for name, path, reason in negatives:
            envelope = document(path, actor_scope)
            before = copy.deepcopy(envelope)
            location = ('data.runner_sandbox_diagnostics.actors[0]' if actor_scope else
                        'data.runner_sandbox_diagnostics')
            prefix = location + '.disposition_issues[0].subject_path '
            run('subject_' + scope + '_' + name, envelope, rejected_by=prefix)
            errors = validate(envelope)
            assert any(error.startswith(prefix) and reason in error for error in errors), (name, errors)
            assert envelope == before, 'invalid reference reading changed retained evidence'

    # The envelope version still gates all interpretation; an independent
    # dossier fault still accumulates beside an admitted malformed reference.
    foreign = document(['steps', '01'])
    foreign['build']['contract'] = 'test:foreign'
    run('subject_version_gate', foreign, rejected_by='unsupported controller envelope')
    assert len(validate(foreign)) == 1, validate(foreign)
    combined = document(['steps', '3'])
    del combined['data']['specimen']['host']['arch']
    run('subject_combined_faults', combined, rejected_by='outside the retained array')
    errors = validate(combined)
    assert 'invalid data.specimen.host' in errors, errors


def consumer_controls(artifacts, current):
    """Constructed JSON interpretation controls; no new native observation."""
    records = []

    def run(name, envelope, expected=None, rejected_by=None):
        path = artifacts / ('consumer_' + name + '.json')
        path.write_text(json.dumps(envelope, indent=2) + '\n')
        errors = validate(envelope)
        (artifacts / ('consumer_' + name + '.errors.json')).write_text(json.dumps(errors, indent=2) + '\n')
        if rejected_by is None:
            assert not errors, (name, errors)
            if expected is not None:
                expected(envelope)
            records.append({'control': name, 'rejected': False})
        else:
            assert any(rejected_by in error for error in errors), (name, rejected_by, errors)
            records.append({'control': name, 'rejected': True, 'errors': errors})

    def runner(envelope):
        return envelope['data']['runner_result']

    def first(envelope):
        return runner(envelope)['steps'][0]

    def require(condition, reason):
        assert condition, reason

    # The authored current run validates and its first row is read by field.
    def allowed_write(e):
        chosen = select(steps(e), step_id='fs_write_allowed', observation='succeeded', order='query_first')
        require(len(chosen) == 1 and chosen[0]['attempt']['outcome'] == 'ok', 'allowed write must be selectable by its record')
    run('constructed_current_run', current, allowed_write)
    diagnostic_subject_controls(run, current)

    from runner_client_capture_controls import run_capture_controls
    run_capture_controls(run)

    def run_host(name, envelope, expected=None, rejected_by=None):
        # The authored host record is the input under test, so encode that
        # exact record into its constructed carrier before validating it.
        recapture_host_reply(envelope)
        run(name, envelope, expected, rejected_by)

    # Source identity is provenance across runs, not a reader admission gate.
    # These constructed metadata changes assert no agreement between hosts.
    other_producer = copy.deepcopy(current)
    other_producer['data']['runner_result']['runner_subprocess']['worker_evidence']['abi_identity'] = 'a' * 64
    other_producer['data']['specimen']['host'].update(macos_version='15.0', macos_build='24A000')
    run_host('current_format_other_producer_and_os', other_producer, allowed_write)

    # Version refusal needs only a constructed frame. The version gate must
    # reject it before requiring the current envelope's fields.
    previous = {'build': {'contract': 'test:previous'},
                'kind': 'run', 'data': {}}
    errors = validate(previous)
    assert len(errors) == 1 and 'unsupported controller envelope' in errors[0], errors
    run_host('previous_envelope_rejected', previous, rejected_by='unsupported controller envelope')
    # Context facts have independent readers; the fixture is authored separately
    # from the producer and keeps application observations outside the receipt.
    context_cases = json.loads((ROOT / 'tests/fixtures/contract/compiled_profile.json').read_text())
    for case in context_cases:
        document = copy.deepcopy(current)
        runner(document)['compiled_profile'] = case['receipt']
        run_host('compiled_profile_' + case['name'], document,
            rejected_by=None if case['valid'] else 'compiled_profile')
    retired = copy.deepcopy(current)
    runner(retired)['applied_profile'] = None
    run_host('retired_profile_field', retired, rejected_by='unknown key reply.applied_profile')
    policy_check_controls(run_host)
    from extension_controls import run_extension_controls
    run_extension_controls(run_host)

    # Attempt forms have their own compact contract beside the query forms.
    resolved = copy.deepcopy(current)
    attempt = first(resolved)['attempt']
    attempt['requested_path'] = '/link/file'
    attempt['path_diagnostics'] = dict(input='/link/file', observer='runner_host',
        stage='after_orchestration', same_as_input=[], realpath_resolved='/real/file',
        parent_realpath_resolved=None)
    # The query names the same target so the record's target relation holds.
    first(resolved)['sandbox_check']['filter_value'] = '/link/file'
    first(resolved)['sandbox_check']['path_diagnostics']['input'] = '/link/file'
    for record in runner(resolved)['phases'][0]['validator_subprocess']['records']:
        if record['step_id'] == 'fs_write_allowed':
            record['filter_value'] = '/link/file'
    run_host('attempt_path_forms', resolved)
    for name, change, diagnostic in [
        ('input_mismatch', lambda a: a['path_diagnostics'].update(input='/unrelated/file'), 'input differs from requested_path'),
        ('wrong_observer', lambda a: a['path_diagnostics'].update(observer='worker'), 'host/stage provenance'),
        ('wrong_phase', lambda a: a['path_diagnostics'].update(stage='before_attempt'), 'host/stage provenance'),
        ('missing_compact', lambda a: a['path_diagnostics'].pop('same_as_input'), 'require same_as_input'),
        ('duplicate_form', lambda a: a['path_diagnostics'].update(same_as_input=['realpath_resolved']*2), 'unique supported form names'),
        ('missing_form', lambda a: a['path_diagnostics'].pop('parent_realpath_resolved'), 'exclusively'),
        ('missing_forms', lambda a: a.pop('path_diagnostics'), 'without path diagnostics'),
    ]:
        malformed = copy.deepcopy(resolved)
        change(first(malformed)['attempt'])
        run_host('attempt_path_' + name, malformed, rejected_by=diagnostic)

    # The worker's EOF receipt for the policy pipe is read by field: both members
    # present and within the source capacity, agreement with the host's own
    # expectation on a transfer record, and unequal counts incompatible with
    # completed execution. A pre-compile partial observation is covered by the
    # controller's transfer replay. The receipt is optional, so a
    # retained envelope without it stays valid; a baseline that carries one
    # must report equal counts for its complete delivery, and a baseline without
    # one receives a constructed receipt. The refusal's detail rule is exercised
    # by the retained driver reply in the controller's transfer replay test.
    evidence = runner(current)['runner_subprocess']['worker_evidence']
    if 'policy_read' in evidence:
        receipt = evidence['policy_read']
        require(receipt['bytes_expected'] == receipt['bytes_received'] > 0, 'a complete live delivery reports equal counts')
        with_receipt = current
    else:
        receipt = {'bytes_expected': 64, 'bytes_received': 64}
        with_receipt = copy.deepcopy(current)
        runner(with_receipt)['runner_subprocess']['worker_evidence']['policy_read'] = dict(receipt)
        run_host('policy_read_constructed_receipt', with_receipt)
    partial = copy.deepcopy(with_receipt)
    runner(partial)['runner_subprocess']['worker_evidence']['policy_read']['bytes_received'] = receipt['bytes_expected'] - 1
    run_host('policy_read_mismatch_after_execution', partial, rejected_by='contradict observations after the policy length check')
    for name, change, diagnostic in [
        ('missing_member', lambda s: s['worker_evidence']['policy_read'].pop('bytes_received'),
         'invalid worker_evidence.policy_read'),
        ('negative_count', lambda s: s['worker_evidence']['policy_read'].update(bytes_received=-1),
         'invalid worker_evidence.policy_read'),
        ('out_of_range', lambda s: s['worker_evidence']['policy_read'].update(bytes_expected=262144),
         'invalid worker_evidence.policy_read'),
        ('conflicting_expectation', lambda s: s.update(policy_transfer_error={'errno': 32, 'bytes_written': 1,
            'bytes_expected': s['worker_evidence']['policy_read']['bytes_expected'] + 1}),
         'disagrees with worker_evidence.policy_read'),
    ]:
        malformed = copy.deepcopy(with_receipt)
        change(runner(malformed)['runner_subprocess'])
        run_host('policy_read_' + name, malformed, rejected_by=diagnostic)

    # The shape goldens are the readers' allowlists: an unknown key at a recorded
    # path and a present key of another type are rejected, under the envelope
    # golden for the controller's own objects and under the reply golden for the
    # runner reply. One control of each kind per golden; the suites whose CLIs
    # route envelopes through the consumer keep one mutation each.
    for name, change, diagnostic in [
        ('envelope_unknown_key', lambda e: e['data']['specimen'].update(request_bytes=1),
         'unknown key envelope.data.specimen.request_bytes'),
        ('envelope_wrong_type', lambda e: e['data'].update(timeout_ms='240000'),
         'envelope.data.timeout_ms is string, not number'),
        ('reply_unknown_key', lambda e: first(e).update(drift=False), 'unknown key reply.steps[].drift'),
        ('reply_wrong_type', lambda e: first(e)['attempt'].update(requested_path=7),
         'reply.steps[].attempt.requested_path is number, not string'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        run_host('shape_' + name, broken, rejected_by=diagnostic)

    # Vocabulary and classification against the raw channel fields.
    for name, change, diagnostic in [
        ('foreign_limitation', lambda e: first(e)['comparison']['limitations'].append('sandbox_attribution_unestablished'), 'outside the vocabulary'),
        ('repeated_limitation', lambda e: first(e)['comparison'].update(limitations=['attempt:not_reached'] * 2), 'repeated limitation'),
        ('lifecycle_limitation_on_completed', lambda e: first(e)['comparison'].update(limitations=['attempt:not_reached']), 'lifecycle limitations'),
        ('plan_limitation_without_exclusion', lambda e: first(e)['comparison'].update(limitations=['query_plan:unrecognized_filter_kind']), 'without a planning exclusion'),
        ('observation_disagrees', lambda e: first(e)['comparison'].update(observation='permission_failure', observation_basis='permission_errno'), 'disagrees with the attempt fields'),
        ('basis_disagrees', lambda e: first(e)['comparison'].update(observation_basis='spawned_child'), 'disagrees with the attempt fields'),
        ('operation_relation_disagrees', lambda e: first(e)['comparison'].update(operation_relation='different'), 'disagrees with the submitted operations'),
        ('target_relation_disagrees', lambda e: first(e)['comparison'].update(target_relation='different_submitted'), 'disagrees with the submitted targets'),
        ('unknown_observation', lambda e: first(e)['comparison'].update(observation='agreement'), 'invalid comparison.observation'),
        ('unknown_order', lambda e: first(e)['comparison'].update(order='future_order'), 'invalid comparison.order'),
        ('missing_comparison', lambda e: first(e).pop('comparison'), 'missing comparison'),
        ('missing_query', lambda e: first(e).pop('sandbox_check'), 'missing sandbox_check'),
        ('missing_attempt', lambda e: first(e).pop('attempt'), 'missing attempt'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        run_host('classification_' + name, broken, rejected_by=diagnostic)

    # The ordering chain: query_first needs the complete chain and an eligible
    # native record; an eligible record with the chain must say query_first.
    def ordering(e):
        return runner(e)['phases'][0]['ordering']
    for name, change, diagnostic in [
        ('collection_not_closed', lambda e: ordering(e).update(collection_closed_before_proceed=False), 'lacks eligible record or ordering chain'),
        ('proceed_not_set', lambda e: ordering(e).update(proceed_set=False), 'lacks eligible record or ordering chain'),
        ('proceed_not_observed', lambda e: ordering(e).update(proceed_observed=False), 'lacks eligible record or ordering chain'),
        ('lifetime_unestablished', lambda e: ordering(e).update(worker_lifetime_established=False), 'lacks eligible record or ordering chain'),
        ('failed_apply', lambda e: runner(e).update(sandboxed_after_apply=False), 'lacks eligible record or ordering chain'),
        ('missing_ordering', lambda e: runner(e)['phases'][0].pop('ordering'), 'ordering is required'),
        ('synthetic_query', lambda e: first(e)['sandbox_check'].update(result_source='synthetic'), 'lacks eligible record or ordering chain'),
        ('incoherent_native', lambda e: first(e)['sandbox_check'].update(native_rc=1), 'lacks eligible record or ordering chain'),
        ('wrong_pid', lambda e: first(e)['sandbox_check'].update(pid=runner(e)['runner_subprocess']['pid'] + 1), 'lacks eligible record or ordering chain'),
        ('wrong_tuple', lambda e: runner(e)['phases'][0]['validator_subprocess']['records'][0].update(filter_value='/other'), 'lacks eligible record or ordering chain'),
        ('duplicate_record', lambda e: runner(e)['phases'][0]['validator_subprocess']['records'].append(copy.deepcopy(runner(e)['phases'][0]['validator_subprocess']['records'][0])), 'lacks eligible record or ordering chain'),
        ('unestablished_despite_chain', lambda e: first(e)['comparison'].update(order='unestablished'), 'requires query_first'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        run_host('order_' + name, broken, rejected_by=diagnostic)
    # A recorded violation beside a falsified chain flag is not a contradiction
    # the validator invents: the fault must be listed.
    broken = copy.deepcopy(current)
    ordering(broken).update(proceed_set=False)
    for step in runner(broken)['steps']:
        step['comparison']['order'] = 'unestablished'
    run_host('order_unmarked_violation', broken, rejected_by='unmarked ordering protocol violation')
    # The marked fault is retained beside the raw chain; no row claims an order.
    ordering(broken)['protocol_violations'] = ['acknowledgement_without_release']
    run_host('order_marked_violation_retained', broken)

    # Reporting failures retain diagnostic observations but certify no comparison.
    def degraded(e, retained=True):
        r = runner(e)
        r.update(rc=1, normalized_outcome='runner_reporting_failed', error='host invariant rejected',
                 reporting_failure=dict(origin='runner_host', diagnostic='missing ordering', original_rc=0,
                                        original_normalized_outcome='finished', original_error=None, evidence_retained=retained))
        e['result'].update(ok=False, exit_code=1, normalized_outcome='runner_reporting_failed')
        for step in r['steps']:
            step['comparison'] = None
        if not retained:
            r['steps'] = []
            r.pop('runner_subprocess', None)
            r['phases'] = []
    def preserved(e):
        view = lifecycle(e)
        require(view['reporting'] == 'reported', 'retained lifecycle evidence must remain readable')
        require(all(s['comparison'] is None for s in steps(e)), 'every comparison withheld')
    failed = copy.deepcopy(current)
    degraded(failed)
    run_host('reporting_failure_preserved', failed, preserved)
    # Retention waives ordinary evidence relationships, not the carried
    # query/attempt objects or their already-required member types.
    for name, change, diagnostic in [
        ('query_missing', lambda s: s.pop('sandbox_check'), 'missing sandbox_check'),
        ('attempt_missing', lambda s: s.pop('attempt'), 'missing attempt'),
        ('attempt_rc_missing', lambda s: s['attempt'].pop('rc'), 'invalid attempt.rc'),
        ('attempt_rc_fractional', lambda s: s['attempt'].update(rc=0.5), 'invalid attempt.rc'),
        ('attempt_errno_fractional', lambda s: s['attempt'].update(errno=0.5), 'invalid attempt.errno'),
        ('query_operation_missing', lambda s: s['sandbox_check'].pop('operation'), 'missing sandbox_check.operation'),
        ('query_filter_missing', lambda s: s['sandbox_check'].pop('filter_kind'), 'missing sandbox_check.operation'),
        ('path_input_missing', lambda s: s['attempt']['path_diagnostics'].pop('input'), 'require a string input'),
        ('path_compact_missing', lambda s: s['attempt']['path_diagnostics'].pop('same_as_input'), 'require same_as_input'),
        ('path_compact_type', lambda s: s['attempt']['path_diagnostics'].update(same_as_input=[3]), 'array of strings'),
    ]:
        malformed = copy.deepcopy(failed)
        change(first(malformed))
        run_host('reporting_failure_shape_' + name, malformed, rejected_by=diagnostic)
    retained = copy.deepcopy(failed)
    first(retained)['attempt'].pop('requested_kind')
    first(retained)['attempt'].pop('requested_action')
    first(retained)['attempt']['path_diagnostics'].update(
        observer='retained_unknown', same_as_input=['retained_future_form'])
    run_host('reporting_failure_retained_optional_intent_and_path_relationship', retained)
    # Required timeout members stay typed, while contradictory values and
    # associations are retained for their ordinary reader rather than certified.
    retained = copy.deepcopy(failed)
    timeout = dict(budget_ms=-1, elapsed_ms=0, bytes_written=50, bytes_expected=40)
    runner(retained)['runner_subprocess']['policy_transfer_timeout'] = timeout
    run_host('reporting_failure_timeout_relationship_retained', retained)
    for field in ('budget_ms', 'elapsed_ms', 'bytes_written', 'bytes_expected'):
        malformed = copy.deepcopy(retained)
        runner(malformed)['runner_subprocess']['policy_transfer_timeout'].pop(field)
        run_host('reporting_failure_timeout_missing_' + field, malformed,
                 rejected_by='invalid policy_transfer_timeout observation')
    # Reporting failure retains the contradictory receipt that stopped ordinary
    # encoding. Its values are diagnostics; object/member types remain required.
    for name, receipt in [
        ('execution', {'bytes_expected': 43, 'bytes_received': 28}),
        ('range', {'bytes_expected': 43, 'bytes_received': -1}),
    ]:
        retained = copy.deepcopy(failed)
        runner(retained)['runner_subprocess']['worker_evidence']['policy_read'] = receipt
        run_host('reporting_failure_policy_read_' + name, retained)
    for name, receipt in [('missing', {'bytes_expected': 43}),
                          ('type', {'bytes_expected': 43, 'bytes_received': '28'}),
                          ('fractional', {'bytes_expected': 43, 'bytes_received': 28.5})]:
        malformed = copy.deepcopy(failed)
        runner(malformed)['runner_subprocess']['worker_evidence']['policy_read'] = receipt
        run_host('reporting_failure_policy_read_' + name, malformed, rejected_by='policy_read')
    minimal = copy.deepcopy(current)
    degraded(minimal, retained=False)
    run_host('reporting_failure_minimal', minimal, lambda e: require(steps(e) == [], 'no steps without retention'))
    for name, change, diagnostic in [
        ('comparison_kept', lambda e: first(e).update(comparison=copy.deepcopy(first(current)['comparison'])), 'must withhold every comparison'),
        ('finished_summary', lambda e: runner(e).update(normalized_outcome='finished'), 'reporting failure requires a failed summary'),
        ('rc_zero', lambda e: runner(e).update(rc=0), 'reporting failure requires a failed summary'),
        ('missing_marker', lambda e: runner(e).pop('reporting_failure'), 'invalid reporting_failure diagnostics'),
        ('bad_marker', lambda e: runner(e).update(reporting_failure='invalid'), 'invalid reporting_failure diagnostics'),
        ('false_retention', lambda e: runner(e)['reporting_failure'].update(evidence_retained=False), 'without evidence retention must omit'),
    ]:
        broken = copy.deepcopy(failed)
        change(broken)
        run_host('reporting_failure_' + name, broken, rejected_by=diagnostic)
    for key in ['origin', 'diagnostic', 'original_rc', 'original_normalized_outcome', 'evidence_retained']:
        broken = copy.deepcopy(failed)
        runner(broken)['reporting_failure'].pop(key)
        run_host('reporting_failure_missing_' + key, broken, rejected_by='invalid reporting_failure diagnostics')

    # The host's raw launch evidence is preserved without an errno allowlist.
    spawn = dict(origin='runner_host', operation='posix_spawn',
                 executable_path='/unknown/validator-"é"', return_code=2147483647,
                 diagnostic='unfamiliar native launch diagnostic')
    spawned = copy.deepcopy(current)
    r = runner(spawned)
    r.update(rc=1, normalized_outcome='validator_spawn_failed', error='native launch failure')
    r['phases'][0]['validator_spawn_failure'] = copy.deepcopy(spawn)
    spawned['result'].update(ok=False, exit_code=1, normalized_outcome='validator_spawn_failed')
    r['phases'][0].pop('validator_subprocess')
    r['phases'][0]['ordering']['validator_disposition'] = 'not_spawned'
    for step in r['steps']:
        step['sandbox_check'].update(outcome='error', result_source='synthetic', native_rc=None, errno=None,
                                     missing_reason='validator_not_invoked')
        step['comparison'].update(order='unestablished')
    run_host('unfamiliar_spawn_failure', spawned, lambda e: require(runner(e)['phases'][0]['validator_spawn_failure'] == spawn, 'raw launch record changed'))
    for name, change, diagnostic in [
        ('zero_code', lambda e: runner(e)['phases'][0]['validator_spawn_failure'].update(return_code=0), 'invalid validator_spawn_failure'),
        ('string_code', lambda e: runner(e)['phases'][0]['validator_spawn_failure'].update(return_code='2'), 'invalid validator_spawn_failure'),
        ('missing_path', lambda e: runner(e)['phases'][0]['validator_spawn_failure'].pop('executable_path'), 'invalid validator_spawn_failure'),
        ('foreign_origin', lambda e: runner(e)['phases'][0]['validator_spawn_failure'].update(origin='validator'), 'invalid validator_spawn_failure'),
        ('with_subprocess', lambda e: runner(e)['phases'][0].update(validator_subprocess=dict(reaped=True, records=[])), 'cannot coexist'),
    ]:
        broken = copy.deepcopy(spawned)
        change(broken)
        run_host('malformed_spawn_' + name, broken, rejected_by=diagnostic)

    # The lifecycle record is required beside a worker subprocess.
    unrecorded = copy.deepcopy(current)
    runner(unrecorded)['runner_subprocess'].pop('disposition')
    run_host('record_required', unrecorded, rejected_by='without runner_subprocess.disposition')

    # D5: producer contracts are admitted before interpreting descendants.
    for name, change, diagnostic in [
        ('envelope_previous', lambda e: e.update(build={"contract": "test:previous"}), 'unsupported controller envelope'),
        ('envelope_next', lambda e: e.update(build={"contract": "test:next"}), 'unsupported controller envelope'),
        ('envelope_integer', lambda e: e.update(build={"contract": 6}), 'malformed controller envelope'),
        ('envelope_missing', lambda e: e.pop('build'), 'malformed controller envelope'),
        ('reply_previous', lambda e: runner(e).update(producer={"contract": "test:previous"}), 'unsupported runner response'),
        ('reply_next', lambda e: runner(e).update(producer={"contract": "test:next"}), 'unsupported runner response'),
        ('reply_float', lambda e: runner(e).update(producer={"contract": 6.5}), 'malformed runner response'),
        ('reply_missing', lambda e: runner(e).pop('producer'), 'malformed runner response'),
        ('old_envelope_no_reply', lambda e: (e.update(build={"contract": "test:previous"}),
                                            e['data'].update(runner_result=None)), 'unsupported controller envelope'),
        ('envelope_first', lambda e: (e.update(build={"contract": "test:previous"}),
                                      runner(e).update(producer={"contract": "test:next"})), 'unsupported controller envelope'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        if runner(broken) is not None:
            # An unguarded lifecycle projection would try to read these as objects.
            runner(broken)['steps'] = [{'attempt': 7, 'comparison': False}]
        errors = validate(broken)
        assert len(errors) == 1 and diagnostic in errors[0], (name, errors)
        for reader in (steps, lifecycle, read_lifecycle):
            try:
                reader(broken)
            except ValueError as exc:
                assert diagnostic in str(exc), (name, reader.__name__, exc)
            else:
                raise AssertionError(f'{name}: {reader.__name__} read an unsupported document')
        findings = check_record(broken)
        assert len(findings) == 1 and diagnostic in findings[0]['detail'], (name, findings)
        expected_kind = 'unsupported_version' if diagnostic.startswith('unsupported') else 'malformed_version'
        assert findings[0]['kind'] == expected_kind, (name, findings)
        records.append({'control': 'version_' + name, 'rejected': True, 'errors': errors})
    # An envelope without a reply is read under its own version only.
    no_reply = copy.deepcopy(current)
    no_reply['data'].update(runner_result=None, runner_client=None, runner_sandbox_diagnostics=None)
    no_reply['result'].update(ok=False, exit_code=2, normalized_outcome='tool_error', error='controlled')
    run_host('no_reply_envelope', no_reply, lambda e: require(steps(e) == [], 'absence must not invent evidence'))
    bare = copy.deepcopy(runner(current))
    assert not validate(bare), validate(bare)
    assert lifecycle(bare)['reporting'] == 'reported'
    bare['producer']['contract'] = "test:next"
    errors = validate(bare)
    assert len(errors) == 1 and 'unsupported runner response' in errors[0], errors
    records.append({'control': 'bare_reply_versions', 'rejected': True})

    (artifacts / 'consumer-controls.json').write_text(json.dumps(records, indent=2) + '\n')


def result_consistency_controls(artifacts, current):
    """An admitted reply's outcome binds the envelope's outcome, success flag and exit code.

    Each control names the exact set of result diagnostics it requires and any
    other consumer diagnostic that must remain beside them. Applicability is
    established from the capture, producer, profile context and controller
    assessment; no control here derives an outcome from a body that failed
    admission, an absent reply or a rejected capture.
    """
    prefixes = {'normalized_outcome': 'result.normalized_outcome is ', 'ok': 'result.ok is ',
                'exit_code': 'result.exit_code is ', 'result': 'result is not an object'}
    records = []

    def control(name, envelope, expected=(), beside=()):
        path = artifacts / ('result_' + name + '.json')
        path.write_text(json.dumps(envelope, indent=2) + '\n')
        errors = validate(envelope)
        found = sorted(key for key, prefix in prefixes.items() if any(e.startswith(prefix) for e in errors))
        assert found == sorted(expected), (name, 'result diagnostics', found, sorted(expected), errors)
        for diagnostic in beside:
            assert any(diagnostic in error for error in errors), (name, 'missing', diagnostic, errors)
        if not expected and not beside:
            assert not errors, (name, errors)
        records.append({'control': name, 'expected_result_diagnostics': sorted(expected), 'found_result_diagnostics': found,
                        'required_beside': list(beside), 'errors': errors})

    def failed(outcome):
        document = copy.deepcopy(current)
        document['data']['runner_result'].update(normalized_outcome=outcome, rc=1, error='constructed failure')
        document['result'].update(normalized_outcome=outcome, ok=False, exit_code=1, error='constructed failure')
        return recapture_host_reply(document)

    baselines = {'finished': copy.deepcopy(current), 'worker_timeout': failed('worker_timeout'),
                 'bad_request': failed('bad_request'), 'unfamiliar_outcome': failed('unfamiliar_outcome')}
    for label, baseline in baselines.items():
        control(label + '_coherent', baseline)
        finished = label == 'finished'
        # One result field changes at a time; the other two keep their diagnostics absent.
        changes = [
            ('outcome_tool_error', 'normalized_outcome', lambda r: r.update(normalized_outcome='tool_error')),
            ('outcome_refusal_spelling', 'normalized_outcome',
             lambda r: r.update(normalized_outcome='malformed_runner_response')),
            ('outcome_other', 'normalized_outcome',
             lambda r: r.update(normalized_outcome='worker_timeout' if label != 'worker_timeout' else 'finished')),
            ('outcome_removed', 'normalized_outcome', lambda r: r.pop('normalized_outcome')),
            ('outcome_null', 'normalized_outcome', lambda r: r.update(normalized_outcome=None)),
            ('outcome_number', 'normalized_outcome', lambda r: r.update(normalized_outcome=0)),
            ('ok_flipped', 'ok', lambda r: r.update(ok=not finished)),
            ('ok_removed', 'ok', lambda r: r.pop('ok')),
            ('ok_null', 'ok', lambda r: r.update(ok=None)),
            # Python compares 1 == True and 0 == False; the JSON types differ.
            ('ok_integer', 'ok', lambda r: r.update(ok=1 if finished else 0)),
            ('exit_other', 'exit_code', lambda r: r.update(exit_code=1 if finished else 0)),
            ('exit_tool_error', 'exit_code', lambda r: r.update(exit_code=2)),
            ('exit_removed', 'exit_code', lambda r: r.pop('exit_code')),
            ('exit_null', 'exit_code', lambda r: r.update(exit_code=None)),
            ('exit_boolean', 'exit_code', lambda r: r.update(exit_code=not finished)),
            ('exit_text', 'exit_code', lambda r: r.update(exit_code='0' if finished else '1')),
        ]
        for name, field, change in changes:
            document = copy.deepcopy(baseline)
            change(document['result'])
            control(label + '_' + name, document, expected=(field,))
        document = copy.deepcopy(baseline)
        document['result'].update(normalized_outcome='tool_error', ok=not finished, exit_code=2)
        control(label + '_all_three', document, expected=('normalized_outcome', 'ok', 'exit_code'))
        for name, value in (('result_removed', None), ('result_array', [])):
            document = copy.deepcopy(baseline)
            if value is None:
                document.pop('result')
            else:
                document['result'] = value
            control(label + '_' + name, document, expected=('result',))
        # An unrelated record error in an admitted reply leaves the result mismatch visible, and conversely.
        document = copy.deepcopy(baseline)
        del document['data']['runner_result']['steps'][0]['comparison']
        recapture_host_reply(document)
        control(label + '_record_error_only', document, beside=('missing comparison',))
        document['result']['exit_code'] = 2
        control(label + '_record_error_and_exit', document, expected=('exit_code',), beside=('missing comparison',))

    # Admission failures supply no mapping, whatever the retained body and the result say.
    # Every field disagrees with the finished reply the baseline's bytes carry.
    mismatched = {'normalized_outcome': 'tool_error', 'ok': False, 'exit_code': 7}
    contexts = json.loads((ROOT / 'tests/fixtures/contract/compiled_profile.json').read_text())
    refused_contexts = [case for case in contexts if not case['valid']]
    assert refused_contexts and len(refused_contexts) < len(contexts), 'profile fixture needs admitted and refused contexts'
    for case in contexts:
        document = copy.deepcopy(current)
        document['data']['runner_result']['compiled_profile'] = case['receipt']
        recapture_host_reply(document)
        document['result'].update(mismatched)
        control('profile_' + case['name'] + '_mismatched_result', document,
                expected=('normalized_outcome', 'ok', 'exit_code') if case['valid'] else (),
                beside=() if case['valid'] else ('compiled_profile',))
        if not case['valid']:
            # The controller's own account of this refusal: a retained body and no assessment.
            document['result'].update(normalized_outcome='malformed_runner_response', ok=False, exit_code=1,
                                      error='constructed refusal')
            document['data']['runner_sandbox_diagnostics'] = None
            control('profile_' + case['name'] + '_refused', document, beside=('compiled_profile',))

    # No reply: the controller's own result rules apply, and nothing is derived here.
    for name, result in (('tool_error', dict(normalized_outcome='tool_error', ok=False, exit_code=2)),
                         ('mismatched', mismatched)):
        document = copy.deepcopy(current)
        document['data'].update(runner_result=None, runner_client=None, runner_sandbox_diagnostics=None)
        document['result'].update(result, error='controlled')
        control('absent_reply_' + name, document)

    # A capture this reader rejects cannot admit the bytes it retains.
    for name, change, diagnostic in [
        ('capture_foreign_contract', lambda c: c['transport'].update(contract='test:foreign'),
         'runner client transport admission disagrees'),
        ('capture_truncated_reply', lambda c: c['transport']['runner_reply'].update(truncated=True),
         'runner client transport admission disagrees'),
        ('delivery_failed', lambda c: c['request_delivery'].update(error='constructed delivery failure'),
         'runner client transport admission disagrees'),
        ('reply_diagnostic', lambda c: c.update(runner_reply_error='constructed host-byte diagnostic'),
         'complete parsed host bytes carry a host-byte diagnostic'),
    ]:
        document = copy.deepcopy(current)
        change(document['data']['runner_client'])
        document['result'].update(mismatched)
        control('rejected_' + name, document, beside=(diagnostic,))

    # Without the controller's assessment this reader has no evidence that the
    # controller admitted the reply, so it asserts no mapping. Capacity refusal
    # is a controller gate this reader does not restate.
    document = copy.deepcopy(current)
    document['data']['runner_sandbox_diagnostics'] = None
    document['result'].update(mismatched)
    control('assessment_absent', document)

    # The result is bound to the admitted bytes: a projected record that differs
    # from them is reported, and the result still answers to the bytes.
    document = copy.deepcopy(current)
    document['data']['runner_result']['normalized_outcome'] = 'worker_timeout'
    document['result'].update(normalized_outcome='worker_timeout', ok=False, exit_code=1)
    control('projection_differs_from_bytes', document, expected=('normalized_outcome', 'ok', 'exit_code'),
            beside=('host result differs from exact captured host reply bytes',))

    # A foreign producer is one version error; nothing behind it is read.
    document = copy.deepcopy(current)
    document['data']['runner_result']['producer'] = {'contract': 'test:next'}
    recapture_host_reply(document)
    document['result'].update(mismatched)
    errors = validate(document)
    assert len(errors) == 1 and 'unsupported runner response' in errors[0], errors
    records.append({'control': 'unsupported_reply_version', 'expected_result_diagnostics': [],
                    'found_result_diagnostics': [], 'required_beside': ['unsupported runner response'], 'errors': errors})

    assert len({record['control'] for record in records}) == len(records)
    (artifacts / 'result-consistency-controls.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'result consistency controls: {len(records)} ok', flush=True)


def client_output_control(artifacts):
    """A missing service produces client observations with no host RunResult."""
    app = Path(os.environ.get('PW_APP_DIR') or (ROOT / 'dist/PolicyWitness.app'))
    client = app / 'Contents/MacOS/pw-runner-client'
    assert client.is_file(), f'shipped client missing: {client}'
    request = artifacts / 'client-request.json'
    request.write_text(json.dumps({'contract': build_context.candidate_contract(), 'specimen_id': 'client-control',
                                   'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
                                   'probe_plan': []}) + '\n')
    result = subprocess.run([str(client), 'run', '--timeout-ms', '2000', '--request', '-',
                             'com.example.pw.no-such-service.' + os.urandom(4).hex()],
                            input=request.read_bytes(), capture_output=True, timeout=30)
    (artifacts / 'client.stdout').write_bytes(result.stdout)
    (artifacts / 'client.stderr').write_bytes(result.stderr)
    assert result.returncode == 1, result
    from porcelain import decode
    capture = decode(result.stdout, "capture")
    errors = validate_capture(capture, build_context.candidate_contract())
    assert not errors, errors
    assert capture['terminal'] in ('xpc_timeout', 'acquisition_failed'), capture
    assert capture['submission'] == {'state': 'not_invoked'}, capture
    assert 'runner_reply' not in capture and 'submission_refusal' not in capture, capture
    assert capture['acquisition_stop'] in ('overall_deadline', 'attempt_limit'), capture
    assert all(a['outcome'] in ('transport_error', 'timeout') for a in capture['attempts']), capture
    print('missing-service client capture records no invocation: ' + capture['terminal'], flush=True)


def cleanup_witness_controls(artifacts):
    """Envelope shapes and the staging removal each permits; constructed, no process launched.

    Only a confirmed reap witnesses worker exit. A client xpc_timeout
    observation, a lost reply and the minimal reporting-failure reply carry no
    subprocess record although a worker may have spawned; an unreaped or
    unrecorded reap says it may still run. Each must retain staging.
    """
    cases = [
        ('client_timeout', {'data': {'runner_result': None, 'runner_client': {'submission': 'invoked'}}}, False),
        ('lost_runner_reply', {'data': {'runner_result': None}}, False),
        ('no_envelope', None, False),
        ('minimal_reporting_failure', {'data': {'runner_result': {
            'normalized_outcome': 'runner_reporting_failed', 'steps': [],
            'reporting_failure': {'evidence_retained': False}}}}, False),
        ('unreaped_worker', {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': False}}}}, False),
        ('reap_unrecorded', {'data': {'runner_result': {'runner_subprocess': {'pid': 42}}}}, False),
        ('missing_pid', {'data': {'runner_result': {'runner_subprocess': {'reaped': True}}}}, False),
        ('invalid_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': 0, 'reaped': True}}}}, False),
        ('negative_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': -1, 'reaped': True}}}}, False),
        ('boolean_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': True, 'reaped': True}}}}, False),
        ('string_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': '42', 'reaped': True}}}}, False),
        ('numeric_reaped', {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': 1}}}}, False),
        ('reaped_worker', {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': True}}}}, True),
    ]
    records = []
    for name, envelope, expected in cases:
        witnessed, reason = worker_exit_witness(envelope)
        assert witnessed is expected, f'{name}: staging removal permitted={witnessed}, expected {expected}: {reason}'
        assert reason, name
        records.append({'control': name, 'removal_permitted': witnessed, 'witness': reason})
    (artifacts / 'cleanup-witness-controls.json').write_text(json.dumps(records, indent=2) + '\n')
    print('cleanup witness controls: ok', flush=True)


def mutation_order_controls(artifacts, current):
    """Unordered and ordered unlink rows: the attempt record and `order` are what the row says."""
    records = []
    base = copy.deepcopy(current)
    r = base['data']['runner_result']
    step = r['steps'][0]
    target = step['attempt']['requested_path']
    step['sandbox_check'].update(operation='file-write-unlink')
    step['attempt'].update(requested_action='unlink', outcome='ok', rc=0, errno=None)
    for record in r['phases'][0]['validator_subprocess']['records']:
        if record['step_id'] == step['step_id']:
            record['operation'] = 'file-write-unlink'
    recapture_host_reply(base)
    assert not validate(base), validate(base)
    chosen = select(steps(base), step_id=step['step_id'], order='query_first', observation='succeeded', operation_relation='matched')
    assert len(chosen) == 1 and chosen[0]['attempt']['requested_action'] == 'unlink', chosen
    records.append({'control': 'ordered_unlink', 'rejected': False})
    # No validator ran (its spawn failed): collection closed with nothing to
    # collect, the worker was released, and no row can claim an order.
    unordered = copy.deepcopy(base)
    unordered['data']['runner_result']['phases'][0]['ordering'].update(validator_disposition='not_spawned')
    unordered['data']['runner_result']['phases'][0].pop('validator_subprocess')
    for s in unordered['data']['runner_result']['steps']:
        s['sandbox_check'].update(result_source='synthetic', native_rc=None, errno=None, outcome='error', missing_reason='validator_not_invoked')
        s['comparison']['order'] = 'unestablished'
    recapture_host_reply(unordered)
    assert not validate(unordered), validate(unordered)
    chosen = select(steps(unordered), step_id=step['step_id'], order='unestablished', observation='succeeded')
    assert len(chosen) == 1, chosen
    records.append({'control': 'unordered_unlink', 'rejected': False})
    claimed = copy.deepcopy(unordered)
    claimed['data']['runner_result']['steps'][0]['comparison']['order'] = 'query_first'
    recapture_host_reply(claimed)
    errors = validate(claimed)
    assert any('lacks eligible record' in e for e in errors), errors
    records.append({'control': 'unordered_unlink_claims_order', 'rejected': True, 'errors': errors})
    (artifacts / 'mutation-order-controls.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'{target}: ordered and unordered unlink rows keep their records', flush=True)


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    check_cases(json.loads((ROOT / 'tests/fixtures/contract/path_diagnostics.json').read_text()))
    baseline = bind_constructed_envelope(json.loads((FIXTURES / "checker/current/constructed_run.json").read_text()))
    prediction_error = "fs_write_allowed: expected sandbox_check allow"
    later_attempt_error = "mach_lookup_denied: expected attempt_ok=False"
    failures = []

    def check(name, envelope, diagnostics=(), case="BBX-001"):
        recapture_host_reply(envelope)
        run_path = artifacts / f"{name}.json"
        run_path.write_text(json.dumps(envelope, indent=2) + "\n")
        result = subprocess.run(
            [sys.executable, '-B', '-S', str(CHECKER), '--authored-json-fixture', str(run_path),
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
    for label, summary, diagnostic in [
        ('envelope', lambda e: e['result'], 'expected result.normalized_outcome=finished'),
        ('runner', lambda e: e['data']['runner_result'], 'expected runner normalized_outcome=finished'),
    ]:
        retired = copy.deepcopy(baseline)
        summary(retired)['normalized_outcome'] = 'ok'
        check('retired_run_outcome_' + label, retired, (diagnostic,))
    consumer_controls(artifacts, baseline)
    result_consistency_controls(artifacts, baseline)
    exec_observation_controls(artifacts)
    mutation_order_controls(artifacts, baseline)
    client_output_control(artifacts)
    cleanup_witness_controls(artifacts)
    from disposition_controls import run_controls
    run_controls(artifacts)
    for label, change, diagnostic in [
        ('missing_intent', lambda s: s['attempt'].pop('requested_action'), 'missing attempt.requested_action'),
        ('host_as_validator', lambda s: s['sandbox_check'].update(path_diagnostics={'input': s['sandbox_check']['filter_value'], 'observer': 'validator', 'stage': 'after_orchestration'}), 'path diagnostics lack host/stage provenance'),
    ]:
        lost = copy.deepcopy(baseline)
        change(lost['data']['runner_result']['steps'][0])
        check('current_' + label, lost, (diagnostic,))
    missing = copy.deepcopy(baseline)
    del missing["data"]["runner_result"]["steps"][0]["comparison"]
    check("current_missing_comparison", missing, ("fs_write_allowed: missing comparison",))

    broken = copy.deepcopy(baseline)
    attempt = broken["data"]["runner_result"]["steps"][2]["attempt"]
    attempt.update(outcome="ok", rc=0)
    check("wrong_later_attempt", broken, (later_attempt_error,))

    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("prediction_and_later_attempt", broken, (prediction_error, later_attempt_error))

    mismatch = copy.deepcopy(baseline)
    mismatch["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("wrong_prediction", mismatch, (prediction_error,))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][0]["attempt"].update(rc=-1)
    check("prediction_and_same_attempt", broken,
          (prediction_error, "fs_write_allowed: expected attempt_ok=True"))

    # Neither a malformed prediction object nor a missing attempt may prevent
    # the other channel or a sibling step from being checked.
    broken = copy.deepcopy(baseline)
    first, _, last = broken["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    first["attempt"].update(rc=-1)
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

    # Reuse only the authored input builder; its native-shaped facts are
    # constructed checker controls and carry no filesystem or live-run credit.
    import importlib.util
    spec = importlib.util.spec_from_file_location('menagerie_constructed_inputs',
        ROOT / 'tests/suites/blackbox_menagerie/checker_controls.py')
    authored = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(authored)
    missing, _ = authored.constructed_missing_path_baseline()
    check("expected_unavailable", missing, case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][2]["attempt"].update(rc=1)
    check("unavailable_and_later_attempt", broken,
          ("fs_read_allowed: expected attempt_ok=True",), case="BBX-002")

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
