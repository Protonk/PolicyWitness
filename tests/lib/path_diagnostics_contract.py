"""Shared fixture assertions used directly and after Rust receiver forwarding.

Each fixture row is one compact path-diagnostics object under the current
contract: the small reader classifies it, and the full document validator
sees the same object inside a constructed step.
"""
import copy
import json
import sys

import contract
from consumer import PATH_FORMS, path_form, steps, validate, validate_path_diagnostics


def _reply_with(diagnostic):
    """A bare reply whose one step carries `diagnostic` on its query channel."""
    step = dict(step_id='path',
                sandbox_check=dict(operation='file-read-data', filter_kind='path', filter_value='/submitted',
                                   outcome='allow', rc=0, path_diagnostics=diagnostic),
                attempt=dict(requested_kind='file', requested_action='open_read', rc=-1, result_source='synthetic'),
                comparison=dict(observation='unavailable', observation_basis='no_completed_worker_result',
                                operation_relation='matched', target_relation='unresolved',
                                order='unestablished', limitations=[]))
    return dict(schema_version=contract.RESPONSE_SCHEMA, normalized_outcome='ok', steps=[step])


def check_cases(cases):
    for case in cases:
        assert case['schema_version'] == contract.RESPONSE_SCHEMA, (case['name'], case['schema_version'])
        path = case['path']
        errors = validate_path_diagnostics(path)
        assert bool(errors) != case['valid'], (case['name'], errors)
        if case['valid']:
            for name in PATH_FORMS:
                state = path_form(path, name)
                assert state == case['states'][name], (case['name'], name, state)
                value = path['input'] if state == 'same_as_input' else path.get(name)
                assert value == case['values'].get(name), (case['name'], name, value)
        else:
            assert all(path_form(path, name) == 'invalid' for name in PATH_FORMS), case['name']

        # The document validator reaches the same verdict through a step, and
        # the accessor returns the object unchanged.
        diagnostic = dict(copy.deepcopy(path), observer='runner_host', phase='after_orchestration')
        reply = _reply_with(diagnostic)
        errors = validate(reply)
        assert bool(errors) != case['valid'], (case['name'], errors)
        assert steps(reply)[0]['sandbox_check']['path_diagnostics'] == diagnostic

    # Provenance is part of the shape: a diagnostic without the host observer
    # and phase is rejected even when its path states are valid.
    bare = dict(input='/submitted', same_as_input=list(PATH_FORMS))
    assert not validate_path_diagnostics(bare)
    assert validate(_reply_with(bare)), 'path diagnostics without provenance accepted'
    # Another response version is refused before any path state is read.
    other = _reply_with(dict(bare, observer='runner_host', phase='after_orchestration'))
    other['schema_version'] = contract.RESPONSE_SCHEMA + 1
    errors = validate(other)
    assert errors and 'unsupported' in errors[0], errors


if __name__ == '__main__':
    check_cases(json.load(sys.stdin))
