"""Independent roles over constructed Swift frames and Rust public envelopes.

General report validity, ordinary actor/extension semantics and retained worker
lifecycle claims have different scopes. The receipt records each answer before
any assertion. JSON-only controls retain both authored and test-normalized views.
"""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import actor_evidence
import consumer
import extension_evidence
import lifecycle_oracle
import porcelain


def replay(directory):
    report = json.loads((directory / 'rust.json').read_text())
    # Swift PW_UNIT_TEST_CONTEXT and Rust cfg(test) declare this producer identity.
    contract = 'test:policy-witness'
    rows, problems = [], []

    def check(condition, message):
        if not condition:
            problems.append(message)

    def inspect(call):
        try:
            return call()
        except Exception as error:
            # Keep the receipt of a reader crash, then fail the control.
            problems.append(f'{type(error).__name__}: {error}')
            return [{'reader_exception': type(error).__name__, 'detail': str(error)}]

    for case in report['cases']:
        identity, reply, envelope = case['id'], case['reply'], case['envelope']
        expected = case['expected_semantic']
        check(reply['producer']['contract'] == contract, identity + ': unexpected producer contract')
        row = {'id': identity, 'origin': case['origin'], 'rule': case['rule']}
        if case.get('expected_reporting_failure') is True:
            check((reply.get('reporting_failure') or {}).get('evidence_retained') is True and
                  all(step.get('comparison') is None for step in reply['steps']) and
                  any(actor.get('mode') == 'apply' and actor.get('setup_status') == 'unapplied_declared'
                      for actor in reply.get('actors', [])),
                  identity + ': host degradation lost the setup conflict or retained comparisons')
        if 'application_expected' in case:
            expected_pair = case['application_expected']
            subject = next(actor for actor in reply['actors'] if actor['actor_id'] == expected_pair['actor_id'])
            row['application_expected'] = expected_pair
            check(subject['application'] == {key: expected_pair[key] for key in ('state', 'basis')},
                  identity + ': decoded assessment differs from eligible source')
        try:
            wire = (directory / case.get('raw_file', identity + '.pwp')).read_bytes()
            independent = porcelain.decode_bound(wire, 'reply', contract)
            row['binary_projection_equal'] = independent == reply
            check(independent == reply, identity + ': binary readers project different retained records')
        except Exception as error:
            row['binary_error'] = str(error)
            problems.append(identity + ': independent binary decode failed: ' + str(error))
        if 'writer_receipt' in case:
            receipt = case['writer_receipt']
            row['writer_receipt'] = receipt
            check(receipt['input'] == 'constructed attempt.error' and
                  receipt['input_utf8_bytes'] == 134_217_729 and receipt['frame_limit_bytes'] == 134_217_728 and
                  receipt['writer_calls'] == 2 and receipt['writer_failures'] == ['text exceeds byte limit'] * 2 and
                  receipt['emitted_bytes'] == len(wire), identity + ': writer failure provenance changed')
            normal = porcelain.decode_bound((directory.parent / 'porcelain-replies/normal.pwp').read_bytes(), 'reply', contract)
            identity_fields = ('producer', 'specimen_id', 'run_kind', 'pid', 'bundle_id', 'policy_format', 'policy_sha256')
            check(all(reply.get(key) == normal.get(key) for key in identity_fields), identity + ': minimal identity changed')
            failure = reply['reporting_failure']
            check(all(failure.get('original_' + key) == normal.get(key) for key in ('rc', 'normalized_outcome', 'error')),
                  identity + ': original summary changed')
            check(reply['rc'] == 1 and reply['normalized_outcome'] == 'runner_reporting_failed' and
                  reply['steps'] == [] and reply['phases'] == [] and failure['evidence_retained'] is False,
                  identity + ': real capacity refusal did not retain minimal failure form')
            check(set(reply) <= set(identity_fields) | {'rc', 'normalized_outcome', 'error', 'steps', 'phases', 'reporting_failure'},
                  identity + ': minimal frame retained rich evidence')
            check(failure['diagnostic'].count('text exceeds byte limit') == 2 and
                  '; evidence-preserving encoding also failed: ' in failure['diagnostic'],
                  identity + ': both observed real writer failures must survive')
        general = inspect(lambda: consumer.validate_fixture(reply, expected_contract=contract))
        assembled = inspect(lambda: consumer.validate_fixture(envelope, expected_contract=contract))
        actor = inspect(lambda: actor_evidence.validate_actor_evidence(reply))
        extensions = inspect(lambda: extension_evidence.validate_extensions(reply))
        lifecycle = inspect(lambda: lifecycle_oracle.check_record(envelope, contract))
        row.update(general_findings=general, envelope_findings=assembled,
                   actor_findings=actor, extension_findings=extensions,
                   lifecycle_findings=lifecycle,
                   actor_scope='inapplicable_degraded' if reply.get('reporting_failure') is not None else 'ordinary_relationships')
        if 'expected_lifecycle_findings' in case:
            row['expected_lifecycle_findings'] = case['expected_lifecycle_findings']
            check(lifecycle == case['expected_lifecycle_findings'],
                  f'{identity}: retained lifecycle findings {lifecycle}')
        if 'unrecorded_host_form' in case:
            actor_form = case['unrecorded_host_form'] == 'actors'
            def subject(value):
                return value['actors'][0]['subprocess'] if actor_form else value['runner_subprocess']
            sub = subject(reply)
            path = 'reply.' + ('actors[].subprocess' if actor_form else 'runner_subprocess')
            row['fallback_shape_controls'] = []
            for question, observation in [('stop_reason', 'poll_stop_reason'), ('collection_basis', 'collection_basis')]:
                claim = sub['disposition']['questions'][question]
                check(observation not in sub and claim == {'state': 'unresolved', 'reason': 'not_recorded'},
                      identity + ': fallback acquired a fact or lost its exact unresolved claim')
                for fault, change, expected_finding in [
                    ('reason_type', {'reason': 7}, f'{path}.disposition.questions.{question}.reason is number, not string'),
                    ('unknown_key', {'invented_observation': True}, f'unknown key {path}.disposition.questions.{question}.invented_observation'),
                ]:
                    altered = copy.deepcopy(reply)
                    subject(altered)['disposition']['questions'][question].update(change)
                    findings = inspect(lambda: consumer.validate_fixture(altered, expected_contract=contract))
                    row['fallback_shape_controls'].append(dict(question=question, fault=fault, findings=findings))
                    check(expected_finding in findings, identity + ': missing fallback shape refusal: ' + expected_finding)
        check((not general) == expected, f'{identity}: general consumer {general}')
        check((not assembled) == expected, f'{identity}: envelope consumer {assembled}')
        degraded = reply.get('reporting_failure') is not None
        if degraded:
            check(not actor and not extensions, identity + ': ordinary subaccount reader escaped applicability')
        elif reply.get('execution_form') == 'actors':
            # Actor identity belongs to the general reader. Record a separate
            # expectation when a case falls outside the extension family's scope.
            expected_extensions = case.get('expected_extensions', expected)
            row['expected_extensions'] = expected_extensions
            check((not extensions) == expected_extensions, f'{identity}: actor/extension reader {extensions}')
        previous_issue = -1
        for message in case.get('required_consumer_issues', []):
            check(message in general, f'{identity}: consumer missed exact finding {message!r}')
            if message in general:
                position = general.index(message)
                check(position > previous_issue, identity + ': required consumer finding order changed')
                previous_issue = position
        required_subjects = case.get('required_subject_issues', [])
        if required_subjects:
            row['required_subject_issues'] = required_subjects
        for expected_subject in required_subjects:
            matched = [finding for finding in envelope['data']['runner_sandbox_diagnostics'].get('disposition_issues', [])
                       if finding.get('detail') == expected_subject['detail'] and
                       finding.get('subject_path') == expected_subject['subject_path']]
            check(len(matched) == 1,
                  f'{identity}: expected exactly one finding at the inspected subject {expected_subject!r}')
        # Subjects are optional for older records. Every emitted path must
        # identify retained evidence, including when its labels are invalid.
        for finding in envelope['data']['runner_sandbox_diagnostics'].get('disposition_issues', []):
            if 'subject_path' not in finding:
                continue
            subject = reply
            try:
                for component in finding['subject_path']:
                    check(isinstance(component, str), identity + ': non-string subject component')
                    if isinstance(subject, list):
                        check(component.isdecimal() and str(int(component)) == component,
                              identity + ': noncanonical collection position')
                        subject = subject[int(component)]
                    else:
                        subject = subject[component]
                row.setdefault('resolved_subjects', []).append(finding['subject_path'])
            except (KeyError, IndexError, TypeError, ValueError) as error:
                problems.append(f'{identity}: unresolved subject {finding["subject_path"]!r}: {error}')
        rows.append(row)
    # Independent completeness inventory: every closed pair has a full-reply
    # positive, in addition to the applied-baseline spelling substitutions.
    expected_pairs = {
        ('not_requested', 'unapplied_declaration'),
        ('not_attempted', 'worker_not_launched'),
        ('not_attempted', 'terminal_authority_setup_refusal'),
        ('not_attempted', 'terminal_input_refusal'),
        ('not_attempted', 'terminal_parameter_refusal'),
        ('not_attempted', 'terminal_compile_refusal'),
        ('not_attempted', 'terminal_timing_refusal'),
        ('observed', 'applied_publication'),
        ('observed', 'apply_failure_publication'),
        ('unobserved', 'apply_call_boundary_without_result'),
        ('unobserved', 'no_eligible_apply_publication'),
    }
    application_rows = [row for row in rows if 'application_expected' in row]
    observed_pairs = {(row['application_expected']['state'], row['application_expected']['basis']) for row in application_rows}
    check(observed_pairs == expected_pairs and len(application_rows) == len(expected_pairs),
          'full-reply application pair inventory is incomplete or duplicated')
    by_id = {row['id']: row for row in rows}
    cases = {row['id']: row for row in report['cases']}
    for case in report['cases']:
        identity = case['id']
        if 'lifecycle_like' in case:
            peer = case['lifecycle_like']
            check(by_id[identity]['lifecycle_findings'] == by_id[peer]['lifecycle_findings'],
                  f'{identity}: retained lifecycle assessment changed from {peer}')
        if 'projections_like' in case:
            peer = case['projections_like']
            own = case['envelope']['data']['runner_sandbox_diagnostics'].get('actors')
            prior = cases[peer]['envelope']['data']['runner_sandbox_diagnostics'].get('actors')
            check(own == prior, f'{identity}: gate finding changed independent actor projections')
    json_rows = []
    for case in report['json_only']:
        raw = inspect(lambda: consumer.validate_fixture(case['input'], expected_contract=contract))
        row = {'id': case['id'], 'origin': case['origin'], 'raw_findings': raw,
               'typed_decode': case['typed_decode']}
        check((not raw) == case['expected_raw_consumer'], f'{case["id"]}: raw JSON consumer {raw}')
        if case['typed_decode']:
            normalized = inspect(lambda: consumer.validate_fixture(case['normalized'], expected_contract=contract))
            row['normalized_findings'] = normalized
            row['normalization_changed_input'] = case['input'] != case['normalized']
            check((not normalized) == case['expected_normalized_semantic'],
                  f'{case["id"]}: normalized consumer {normalized}')
        json_rows.append(row)
    receipt = {'domain': report['domain'], 'cases': rows, 'json_only': json_rows, 'failures': problems}
    (directory / 'python.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    if problems:
        raise AssertionError('\n'.join(problems))
    print(f"reader corpus: {len(rows)} typed and {len(json_rows)} JSON-only controls")


if __name__ == '__main__':
    replay(Path(sys.argv[1]))
