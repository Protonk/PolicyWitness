"""Native queries precede a read and unlink; later host nonresolution remains separate."""
import json
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
from consumer import validate_current_build_evidence


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    target = out / ('unlink-' + secrets.token_hex(8))
    target.write_bytes(b'independent unlink witness\n')
    spec = {
        'schema_version': 1, 'specimen_id': 'removed-target-prediction',
        'policy': {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'},
        'probe_plan': [{
            'step_id': 'read',
            'sandbox_check': {'operation': 'file-read-data',
                              'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(target)},
        }, {
            'step_id': 'unlink',
            'sandbox_check': {'operation': 'file-write-unlink',
                              'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'unlink', 'target': str(target)},
        }],
    }
    with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture']) as run:
        rc = run.wait(timeout=30)
        try:
            target.lstat()
        except FileNotFoundError:
            absent = True
        else:
            absent = False
        (out / 'file-witness.json').write_text(json.dumps({'target': str(target), 'absent': absent}) + '\n')
        assert absent, 'unlink did not remove the independently observed target'
        assert rc == 0, rc
        envelope = run.load_json()
    assert envelope['result']['ok'] is True
    runner = envelope['data']['runner_result']
    assert runner['schema_version'] >= 8, runner  # runner_subprocess.ordering: response 8
    assert runner['normalized_outcome'] == 'ok'
    assert runner.get('test_overrides') is None
    assert runner['runner_subprocess']['exit_code'] == 0
    assert runner['validator_subprocess']['exit_code'] == 0
    assert [step['step_id'] for step in runner['steps']] == ['read', 'unlink']
    ordering = runner["runner_subprocess"]["ordering"]
    assert all(ordering[key] is True for key in ("collection_closed_before_proceed", "proceed_set", "proceed_observed")), ordering
    recorded = {}
    for step, action in zip(runner['steps'], ('open_read', 'unlink')):
        prediction, attempt, comparison = step['sandbox_check'], step['attempt'], step['comparison']
        assert prediction['result_source'] == 'validator', prediction
        assert prediction['outcome'] == 'allow', prediction
        assert prediction['native_rc'] == (0 if prediction['outcome'] == 'allow' else 1), prediction
        assert prediction['filter_value'] == str(target)
        assert attempt['result_source'] == 'worker'
        assert (attempt['requested_kind'], attempt['requested_action'], attempt['requested_path']) == ('file', action, str(target))
        # The worker reads before it unlinks, so both attempts complete successfully.
        assert attempt['outcome'] == 'ok' and attempt['rc'] == 0, attempt
        assert comparison['prediction'] == prediction['outcome']
        assert comparison['observation'] == 'succeeded'
        assert comparison['operation_relation'] == 'matched' and comparison['target_relation'] == 'same_submitted', comparison
        assert comparison['order'] == 'query_first', comparison
        assert comparison['conclusion'] == 'agreement' and step['drift'] is False, step
        assert 'attempt_mutation_order_unestablished' not in comparison['limitations'], comparison
        assert 'host_path_resolution_changed' in comparison['limitations'], comparison
        recorded[step['step_id']] = {'prediction': prediction['outcome'], 'native_rc': prediction['native_rc'],
                                     'comparison': comparison, 'drift': step['drift']}
    errors = validate_current_build_evidence(envelope)
    assert not errors, errors
    (out / 'prediction-observation.json').write_text(json.dumps(recorded, indent=2) + '\n')
    print('removed target retains native ' + '/'.join(recorded[s]['prediction'] for s in ('read', 'unlink'))
          + ' predictions, successful read and unlink, and query_first agreement on both rows')


if __name__ == '__main__':
    main()
