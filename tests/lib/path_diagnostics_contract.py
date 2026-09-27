"""Shared fixture assertions used directly and after Rust receiver forwarding."""
import copy
import json
import sys

from consumer import (PATH_FORMS, path_form, recover_evidence,
                      validate_evidence_shape, validate_path_diagnostics)


def check_cases(cases):
    for case in cases:
        path = case['path']
        errors = validate_path_diagnostics(path, require_compact=case['schema_version'] >= 9)
        assert bool(errors) != case['valid'], (case['name'], errors)
        if case['valid']:
            for name in PATH_FORMS:
                state = path_form(path, name)
                assert state == case['states'][name], (case['name'], name, state)
                value = path['input'] if state == 'same_as_input' else path.get(name)
                assert value == case['values'].get(name), (case['name'], name, value)
        else:
            assert all(path_form(path, name) == 'invalid' for name in PATH_FORMS), case['name']

        # Exercise the universal envelope checks as well as the small reader.
        diagnostic = dict(copy.deepcopy(path), observer='runner_host', phase='after_orchestration')
        step = dict(step_id='path', drift=None,
                    sandbox_check=dict(path_diagnostics=diagnostic),
                    attempt=dict(requested_kind='file', requested_action='open_read'),
                    comparison=dict(scope='submitted_operation_and_target', prediction='unavailable',
                        observation='unavailable', observation_basis='no_completed_worker_result',
                        operation_relation='unresolved', target_relation='unresolved',
                        conclusion='unavailable', order='unestablished',
                        limitations=['query_attempt_order_unestablished', 'state_stability_unestablished']))
        envelope = dict(data=dict(runner_result=dict(schema_version=case['schema_version'], steps=[step])))
        errors = validate_evidence_shape(envelope)
        assert bool(errors) != case['valid'], (case['name'], errors)
        assert recover_evidence(envelope)['steps'][0]['path_diagnostics'] == diagnostic

    # Only the enclosing version distinguishes absent legacy forms from a lost
    # response-9 marker. Removing the marker must not bypass envelope validation.
    step['sandbox_check']['path_diagnostics'] = dict(input='/old', observer='runner_host', phase='after_orchestration')
    for version in (8, 9):
        envelope['data']['runner_result']['schema_version'] = version
        errors = validate_evidence_shape(envelope)
        assert bool(errors) == (version == 9), (version, errors)


if __name__ == '__main__':
    check_cases(json.load(sys.stdin))
