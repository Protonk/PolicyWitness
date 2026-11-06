"""Shared public CLI capture with independent envelope and lifecycle checks.

RunCapture retains the raw request, output, diagnostics and process receipts.
The 40-second capture deadline is a harness boundary, separate from client,
host setup, execution, collection and native-operation allowances. Assertions
about ordinary attempts, phases and actor effects remain with their cases.
"""
import consumer
from run_capture import RunCapture


def capture(pw, out, name, spec, *, expected_rc=0, session_state=None):
    directory = out / name
    if session_state:
        spec['runner'] = {'mode': 'byoxpc', 'service': session_state['service_name']}
        directory.mkdir(parents=True, exist_ok=True)
    with RunCapture(pw, directory, spec, cli_args=[]) as captured:
        assert captured.wait(timeout=40) == expected_rc, captured.metadata_path
        envelope = captured.load_json()
    errors = consumer.validate(envelope)
    assert not errors, errors
    from lifecycle_oracle import check_record
    errors = check_record(envelope)
    assert not errors, errors
    return envelope, envelope['data']['runner_result']
