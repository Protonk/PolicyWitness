#!/usr/bin/env python3
"""Authored controls for the `test-input run` checker: constructed records, exact diagnostics.

Every record here is written by hand. A control establishes what the checker
accepts and rejects; none is evidence that a submission ran.
"""
import copy
import json
from pathlib import Path
import sys

import check_test_input as publication
import check_test_input_seam as checker
import test_input_controls as constructed
from file_observation import fresh_record

IDENTITY = constructed.IDENTITY
TARGET = '/private/tmp/constructed-test-input/seam-target'
VALIDATOR = '/private/tmp/constructed-test-input/validator.py'
PW = '/constructed/PolicyWitness.app/Contents/MacOS/policy-witness'
CLIENT = '/constructed/PolicyWitness.app/Contents/MacOS/pw-runner-client'
WORKER_PID = 4101
# Rows that are not evaluated when a submission's envelope or capture is not admitted.
DEPENDENT = dict(neighbour=('baseline',), zero_controls=('echo', 'neighbour'), native_range=('boundary',),
                 **{name: ('echo', 'intervention') for name in checker.ACTIVATIONS},
                 **{'legacy_block.' + name: ('refusal',) for name in ('cli', 'inert', 'client')},
                 **{'legacy_block.empty': ('admitted',), 'client.activation': ('intervention',)})


def sample():
    return constructed.sample(TARGET, publication.LONG, 51)


def step(ident='read-target', *, completed=True):
    fields = {key: sample()['stat'][field] for key, field in publication.IDENTITY_FIELDS.items()}
    attempt = dict(result_source='worker', rc=0, errno=None, outcome='ok',
                   fresh_read=fresh_record(publication.LONG, fields, bound=publication.BOUND))
    if not completed:
        attempt = dict(result_source='synthetic', rc=None, errno=None, outcome='no_completed_result')
    return dict(step_id=ident, attempt=attempt, comparison=dict(order='query_first'),
                sandbox_check=dict(result_source='validator', outcome='allow', native_rc=0, errno=0))


def worker(**changes):
    value = dict(pid=WORKER_PID, exit_code=0, term_signal=None, reaped=True, done_observed=True, ready_byte_received=True,
                 partial_steps=False, poll_stop_reason='done', termination_request=None,
                 sentinel_wait=dict(budget_ms=120000, elapsed_ms=3, stop='done'),
                 ready_wait=dict(budget_ms=1000, elapsed_ms=4, stop='received'),
                 worker_evidence=dict(progress=dict(operation=11, stage=2, index=0, raw=186646529)))
    value.update(changes)
    return value


def phase(**changes):
    value = dict(collection_status='collected', validator_subprocess=dict(reaped=True),
                 ordering=dict(validator_disposition='reaped'))
    value.update(changes)
    return value


def reply(outcome='finished', **changes):
    value = dict(producer=dict(contract=IDENTITY), normalized_outcome=outcome, sandboxed_after_apply=True,
                 runner_subprocess=worker(), phases=[phase()], steps=[step()])
    value.update(changes)
    return value


def signaled(partial):
    return worker(exit_code=None, term_signal=9, done_observed=False, partial_steps=partial, poll_stop_reason='child_reaped',
                  worker_evidence=dict(progress=checker.attempt_slot_started(0) if partial
                                       else dict(operation=9, stage=2, index=0, raw=153092097)))


def activation_reply(name, controls):
    """A reply holding the observation the named control's intervention row reads."""
    outcome = checker.ACTIVATIONS[name][2]
    value = reply(outcome, test_overrides=dict(controls))
    if name == 'worker_timeout_ms':
        value['runner_subprocess']['sentinel_wait']['budget_ms'] = 7000
    elif name == 'worker_post_apply_hang_ms':
        value['runner_subprocess']['sentinel_wait']['elapsed_ms'] = 2012
    elif name == 'worker_pre_ready_hang_ms':
        value['runner_subprocess']['ready_wait']['elapsed_ms'] = 414
    elif name == 'worker_post_apply_kill_signal':
        value['runner_subprocess'] = signaled(False)
    elif name == 'worker_kill_before_publish_slot':
        value.update(runner_subprocess=signaled(True), steps=[step(completed=False)])
    elif name == 'validator_executable_path':
        value['phases'] = [phase(validator_subprocess=None, ordering=dict(validator_disposition='not_spawned'),
                                 validator_spawn_failure=dict(origin='runner_host', operation='posix_spawn', return_code=2,
                                                              executable_path=checker.MISSING_VALIDATOR,
                                                              diagnostic='No such file or directory'))]
    elif name == 'validator_io_timeout_ms':
        value['steps'].append(step('read-target-again'))
        value['phases'] = [phase(validator_subprocess=dict(
            reaped=True, stdout_collection_stop='deadline', termination_request=dict(signal=9, rc=0),
            io_error='read(verdicts): exceeded 500 ms I/O deadline; wrote 2 of 2 probe bytes; drained 1 stdout bytes',
            records=[dict(step_id='read-target')]))]
    elif name == 'validator_total_timeout_ms':
        value['phases'] = [phase(collection_status='budget_exhausted', validator_subprocess=None,
                                 ordering=dict(validator_disposition='not_spawned'))]
    return value


def envelope(exit_code, outcome, host=None, **data):
    body = dict(runner_client=dict(submission='invoked'), runner_result=host, request_failure=None,
                specimen=dict(binaries=dict(validator=None)))
    body.update(data)
    return dict(kind='run', build=dict(contract=IDENTITY), data=body,
                result=dict(exit_code=exit_code, ok=exit_code == 0, normalized_outcome=outcome, error=None))


def submission(name, entry, document, controls, exit_code, outcome, host):
    """A record the adapter and the driver would leave for one experimental submission."""
    path = '/constructed/' + name + '/specimen.json'
    text = publication.encode(document)
    if entry == 'cli':
        argv = [PW, 'test-input', 'run', path, *checker.flag_arguments(controls), '--timeout-ms', '20000']
    else:
        argv = [CLIENT, 'run', '--experimental-controls', json.dumps(controls), '--timeout-ms', '20000', 'service', path]
    record = dict(argv=argv, exit=exit_code, stderr='', ordinary=text, delivered=text, delivered_document=document,
                  invocation=dict(requested_route='experimental_' + entry, entry=entry, state='exited',
                                  requested_controls=dict(controls), argv=argv),
                  reply=host, before=sample(), after=sample())
    if entry == 'cli':
        record.update(envelope=envelope(exit_code, outcome, host), consumer_errors=[])
    else:
        record.update(exit=0, capture_errors=[],
                      capture=dict(contract=IDENTITY, terminal='runner_reply', submission=dict(state='invoked')))
    return record


def refusal_reply():
    return dict(producer=dict(contract=IDENTITY), normalized_outcome='bad_request', steps=[], phases=[],
                request_failure=dict(checker.LEGACY_REFUSAL))


def usage_record(name, command, arguments, error):
    path = '/constructed/usage.' + name + '.json'
    refused = envelope(2, 'tool_error', runner_client=None)
    refused['result']['error'] = error
    return dict(argv=[PW, *command, *(path if item is None else item for item in arguments)], exit=2, stderr='',
                request_path=path, envelope=refused)


def build():
    document = checker.expected_document(IDENTITY, TARGET)
    state = dict(identity=IDENTITY, target=TARGET, payload_hex=publication.LONG.hex(), validator=VALIDATOR, read={}, scenarios={})
    emitted = dict(argv=[PW, 'test-input', 'read', '--target', TARGET], exit=0, stderr='', stdout=publication.encode(document))
    denial = ['/usr/bin/sandbox-exec', '-p', checker.DENIAL, PW]
    state['read'] = dict(first=copy.deepcopy(emitted), last=copy.deepcopy(emitted),
                         denied=dict(emitted, argv=[*denial, 'test-input', 'read', '--target', TARGET]))
    scenarios = state['scenarios']
    scenarios['neighbour'] = dict(argv=[PW, 'run', '/constructed/neighbour/specimen.json', '--timeout-ms', '20000'], exit=0,
                                  stderr='', delivered_document=document, envelope=envelope(0, 'finished', reply()),
                                  consumer_errors=[], reply=reply(), before=sample(), after=sample())
    scenarios['zero_controls'] = submission('zero_controls', 'cli', document, {}, 0, 'finished', reply(test_overrides={}))
    for name, (_, exit_code, outcome) in checker.ACTIVATIONS.items():
        controls = checker.controls_for(name, state)
        scenarios[name] = submission(name, 'cli', checker.request_for(name, IDENTITY, TARGET), controls, exit_code, outcome,
                                     activation_reply(name, controls))
    scenarios['validator_executable_path']['envelope']['data']['specimen']['binaries']['validator'] = dict(
        path=checker.MISSING_VALIDATOR, actual_sha256=None, baseline_sha256='0' * 64, verification='unavailable',
        reason='cannot stat ' + checker.MISSING_VALIDATOR)
    scenarios['validator_io_timeout_ms']['validator_receipt'] = dict(
        target_pid=WORKER_PID, probes=[dict(step_id='read-target'), dict(step_id='read-target-again')])
    for name, (arguments, error) in checker.USAGE.items():
        scenarios['usage.' + name] = usage_record(name, ['test-input', 'run'], arguments, error)
    scenarios['usage.ordinary_run'] = usage_record('ordinary_run', ['run'], *checker.ORDINARY_USAGE)
    refused = reply('runner_failed', sandboxed_after_apply=None, test_overrides=dict(checker.NATIVE_RANGE),
                    steps=[step(completed=False)],
                    runner_subprocess=worker(exit_code=2, done_observed=False, ready_byte_received=False, partial_steps=True,
                                             poll_stop_reason='child_reaped'))
    scenarios['native_range'] = submission('native_range', 'cli', document, checker.NATIVE_RANGE, 1, 'runner_failed', refused)
    for name in ('cli', 'inert'):
        record = submission('legacy_block.' + name, 'cli', checker.request_for(name, IDENTITY, TARGET, checker.LEGACY_BLOCKS[name]),
                            {}, 1, 'bad_request', refusal_reply())
        record['envelope']['data']['request_failure'] = dict(checker.LEGACY_REFUSAL)
        scenarios['legacy_block.' + name] = record
    scenarios['legacy_block.empty'] = submission('legacy_block.empty', 'cli', checker.request_for('empty', IDENTITY, TARGET, {}),
                                                 {}, 0, 'finished', reply(test_overrides={}))
    host = reply(test_overrides=dict(checker.CLIENT_CONTROLS))
    host['runner_subprocess']['sentinel_wait']['budget_ms'] = 7000
    scenarios['client.activation'] = submission('client.activation', 'client', document, checker.CLIENT_CONTROLS, 0, 'finished', host)
    scenarios['legacy_block.client'] = submission(
        'legacy_block.client', 'client', checker.request_for('client', IDENTITY, TARGET, checker.LEGACY_BLOCKS['client']),
        {}, 0, 'bad_request', refusal_reply())
    denied = envelope(2, 'tool_error', runner_client=None)
    denied['result']['error'] = 'failed to run pw-runner-client: failed to launch "' + CLIENT + '": Operation not permitted (os error 1)'
    scenarios['denied_run'] = dict(argv=[*denial, 'test-input', 'run', '/constructed/denied-run.json'], exit=2, stderr='',
                                   envelope=denied)
    return state


def failed(*names):
    return {(name, 'failed') for name in names}


def unread(label):
    return {(label + '.' + row, 'not_evaluated') for row in DEPENDENT[label]}


def controls():
    """(name, change to the constructed state, exact non-passing rows)."""
    yield 'baseline', lambda s: None, set()
    scenario = lambda s, name: s['scenarios'][name]
    cli = ['zero_controls', 'native_range', 'legacy_block.cli', 'legacy_block.inert', 'legacy_block.empty', *checker.ACTIVATIONS]
    # Rows every recorded submission has.
    for label in cli + ['client.activation', 'legacy_block.client']:
        yield label + ':legacy_route', lambda s, label=label: scenario(s, label)['invocation'].update(
            requested_route='legacy_request_block'), failed(label + '.submission')
        yield label + ':controls_in_request', lambda s, label=label: scenario(s, label).update(
            delivered=publication.encode(dict(json.loads(scenario(s, label)['delivered']),
                                              _test_overrides=dict(worker_timeout_ms=1)))), failed(label + '.submission')
    for label in ['neighbour', *cli]:
        yield label + ':observed_exit', lambda s, label=label: scenario(s, label).update(exit=3), failed(label + '.status')
        yield label + ':other_build', lambda s, label=label: scenario(s, label)['envelope']['build'].update(
            contract='development:' + '5' * 64), failed(label + '.build', label + '.consumer') | unread(label)
        yield label + ':consumer_refused', lambda s, label=label: scenario(s, label).update(
            consumer_errors=['constructed reader refusal']), failed(label + '.consumer')
    # The echo and the intervention are separate: each control's reply with one of them removed.
    for name in checker.ACTIVATIONS:
        yield name + ':no_echo', lambda s, name=name: scenario(s, name)['reply'].pop('test_overrides'), failed(name + '.echo')

        def echo_only(s, name=name):
            record = scenario(s, name)
            record['reply'] = reply(test_overrides=dict(record['reply']['test_overrides']))
        yield name + ':echo_without_intervention', echo_only, failed(name + '.intervention')

        def moved(s, name=name):
            scenario(s, name)['after']['stat']['st_mtime_ns'] += 1
        yield name + ':target_changed', moved, failed(name + '.intervention')
    observed = lambda s, name: scenario(s, name)['reply']['runner_subprocess']
    child = lambda s: scenario(s, 'validator_io_timeout_ms')['reply']['phases'][0]['validator_subprocess']
    for name, change, rejected in (
            ('worker_timeout_ms:default_allowance', lambda s: observed(s, 'worker_timeout_ms')['sentinel_wait'].update(budget_ms=120000), True),
            ('worker_post_apply_hang_ms:short', lambda s: observed(s, 'worker_post_apply_hang_ms')['sentinel_wait'].update(elapsed_ms=1899), True),
            ('worker_post_apply_hang_ms:at_bound', lambda s: observed(s, 'worker_post_apply_hang_ms')['sentinel_wait'].update(elapsed_ms=1900), False),
            ('worker_pre_ready_hang_ms:short', lambda s: observed(s, 'worker_pre_ready_hang_ms')['ready_wait'].update(elapsed_ms=379), True),
            ('worker_pre_ready_hang_ms:at_bound', lambda s: observed(s, 'worker_pre_ready_hang_ms')['ready_wait'].update(elapsed_ms=380), False),
            ('worker_pre_ready_hang_ms:not_received', lambda s: observed(s, 'worker_pre_ready_hang_ms')['ready_wait'].update(stop='deadline'), True),
            ('worker_post_apply_kill_signal:host_kill', lambda s: observed(s, 'worker_post_apply_kill_signal').update(
                termination_request=dict(signal=9, rc=0)), True),
            ('worker_post_apply_kill_signal:other_signal', lambda s: observed(s, 'worker_post_apply_kill_signal').update(term_signal=15), True),
            ('worker_kill_before_publish_slot:published', lambda s: observed(s, 'worker_kill_before_publish_slot')['worker_evidence'].update(
                progress=dict(operation=9, stage=2, index=0, raw=153092097)), True),
            ('worker_kill_before_publish_slot:result_reported', lambda s: scenario(s, 'worker_kill_before_publish_slot')['reply'].update(
                steps=[step()]), True),
            ('validator_executable_path:other_path', lambda s: scenario(s, 'validator_executable_path')['reply']['phases'][0][
                'validator_spawn_failure'].update(executable_path='/nonexistent/another'), True),
            ('validator_executable_path:validator_ran', lambda s: scenario(s, 'validator_executable_path')['reply']['phases'][0].update(
                validator_subprocess=dict(reaped=True)), True),
            ('validator_io_timeout_ms:ended_at_eof', lambda s: child(s).update(stdout_collection_stop='eof'), True),
            ('validator_io_timeout_ms:other_deadline', lambda s: child(s).update(io_error='read(verdicts): exceeded 30000 ms I/O deadline'), True),
            ('validator_io_timeout_ms:other_worker', lambda s: scenario(s, 'validator_io_timeout_ms')['validator_receipt'].update(target_pid=7), True),
            ('validator_io_timeout_ms:no_receipt', lambda s: scenario(s, 'validator_io_timeout_ms').update(validator_receipt=None), True),
            ('validator_total_timeout_ms:collected', lambda s: scenario(s, 'validator_total_timeout_ms')['reply'].update(phases=[phase()]), True)):
        yield name, change, failed(name.split(':')[0] + '.intervention') if rejected else set()
    yield 'validator_executable_path:packaged_provenance', lambda s: scenario(s, 'validator_executable_path')['envelope']['data'][
        'specimen']['binaries'].update(validator=None), failed('validator_executable_path.provenance')
    yield 'validator_executable_path:neighbour_substituted', lambda s: scenario(s, 'neighbour')['envelope']['data']['specimen'][
        'binaries'].update(validator=dict(path='/x')), failed('validator_executable_path.provenance')

    # The neighbour and the submission without controls.
    yield 'neighbour:echo', lambda s: scenario(s, 'neighbour')['reply'].update(test_overrides={}), failed('neighbour.baseline')
    yield 'neighbour:slow_ready', lambda s: scenario(s, 'neighbour')['reply']['runner_subprocess']['ready_wait'].update(elapsed_ms=300), \
        failed('neighbour.baseline')
    yield 'zero_controls:no_echo', lambda s: scenario(s, 'zero_controls')['reply'].pop('test_overrides'), failed('zero_controls.echo')
    yield 'zero_controls:null_echo', lambda s: scenario(s, 'zero_controls')['reply'].update(test_overrides=None), failed('zero_controls.echo')
    yield 'zero_controls:other_allowance', lambda s: scenario(s, 'zero_controls')['reply']['runner_subprocess']['sentinel_wait'].update(
        budget_ms=7000), failed('zero_controls.neighbour')
    yield 'zero_controls:no_collection', lambda s: scenario(s, 'zero_controls')['reply'].update(
        phases=[phase(collection_status='not_needed')]), failed('zero_controls.neighbour')
    yield 'zero_controls:extra_flag', lambda s: scenario(s, 'zero_controls')['invocation']['argv'].extend(
        ['--worker-timeout-ms', '7000']), failed('zero_controls.submission')

    # Usage refusals stop in the controller.
    for name in [*checker.USAGE, 'ordinary_run']:
        label = 'usage.' + name
        yield label + ':submitted', lambda s, label=label: scenario(s, label)['envelope']['data'].update(
            runner_client=dict(submission='invoked')), failed(label)
        yield label + ':host_refusal', lambda s, label=label: (scenario(s, label).update(exit=1), scenario(s, label)['envelope']['result'].update(
            exit_code=1, normalized_outcome='bad_request')), failed(label)
        yield label + ':other_reason', lambda s, label=label: scenario(s, label)['envelope']['result'].update(
            error='missing <request.json>'), failed(label)
        yield label + ':no_envelope', lambda s, label=label: scenario(s, label).update(
            envelope=None, stderr='policy-witness test-input: expected test-input read --target PATH\n'), failed(label)

    # A native argument refusal is neither a usage refusal nor a request refusal.
    yield 'native_range:usage_refusal', lambda s: scenario(s, 'native_range')['envelope']['data'].update(runner_client=None), \
        failed('native_range.boundary')
    yield 'native_range:request_refusal', lambda s: scenario(s, 'native_range')['reply'].update(
        request_failure=dict(code='invalid_value', path=['_test_overrides', 'worker_post_apply_hang_ms'])), failed('native_range.boundary')
    yield 'native_range:worker_ran', lambda s: scenario(s, 'native_range')['reply']['runner_subprocess'].update(
        exit_code=0, ready_byte_received=True), failed('native_range.boundary')

    # The experimental route refuses a request block that holds any member.
    for name in ('cli', 'inert', 'client'):
        label = 'legacy_block.' + name
        yield label + ':other_location', lambda s, label=label: scenario(s, label)['reply']['request_failure'].update(
            path=['_test_overrides', 'worker_timeout_ms']), failed(label + '.refusal')
        yield label + ':worker_launched', lambda s, label=label: scenario(s, label)['reply'].update(
            runner_subprocess=worker()), failed(label + '.refusal')
        yield label + ':block_echoed', lambda s, label=label: scenario(s, label)['reply'].update(
            test_overrides=dict(worker_timeout_ms=5000)), failed(label + '.refusal')
    yield 'legacy_block.cli:envelope_without_refusal', lambda s: scenario(s, 'legacy_block.cli')['envelope']['data'].update(
        request_failure=None), failed('legacy_block.cli.refusal')
    yield 'legacy_block.empty:refused', lambda s: scenario(s, 'legacy_block.empty').update(reply=refusal_reply()), \
        failed('legacy_block.empty.admitted')
    yield 'legacy_block.empty:no_echo', lambda s: scenario(s, 'legacy_block.empty')['reply'].pop('test_overrides'), \
        failed('legacy_block.empty.admitted')

    # The client's own submission.
    for label in ('client.activation', 'legacy_block.client'):
        yield label + ':no_reply', lambda s, label=label: scenario(s, label)['capture'].update(terminal='xpc_error'), \
            failed(label + '.capture') | unread(label)
        yield label + ':capture_refused', lambda s, label=label: scenario(s, label).update(
            capture_errors=['constructed capture refusal']), failed(label + '.capture') | unread(label)
        yield label + ':not_invoked', lambda s, label=label: scenario(s, label)['capture']['submission'].update(
            state='not_invoked'), failed(label + '.capture') | unread(label)
    yield 'client.activation:default_allowance', lambda s: scenario(s, 'client.activation')['reply']['runner_subprocess'][
        'sentinel_wait'].update(budget_ms=120000), failed('client.activation.intervention')
    yield 'client.activation:ordinary_argument', lambda s: scenario(s, 'client.activation')['invocation']['argv'].__setitem__(
        2, '--request'), failed('client.activation.submission')

    # The read publisher.
    yield 'read:changed_after', lambda s: s['read']['last'].update(stdout=s['read']['last']['stdout'].replace('read-target', 'read-other')), \
        failed('read.publication')
    yield 'read:other_body', lambda s: [s['read'][name].update(stdout=publication.encode(dict(specimen_id='other')))
                                        for name in ('first', 'last', 'denied')], failed('read.publication')
    yield 'read:denied_differs', lambda s: s['read']['denied'].update(stdout='{}\n'), failed('read.launches_nothing')
    yield 'read:denied_fails', lambda s: s['read']['denied'].update(exit=2, stdout=''), failed('read.launches_nothing')
    yield 'read:no_profile', lambda s: s['read']['denied'].update(argv=s['read']['first']['argv']), failed('read.launches_nothing')
    yield 'read:profile_allows_launch', lambda s: (scenario(s, 'denied_run').update(exit=0), scenario(s, 'denied_run')['envelope']['data'].update(
        runner_client=dict(submission='invoked'))), failed('read.denial_applies')
    yield 'read:launch_not_attempted', lambda s: scenario(s, 'denied_run')['envelope']['result'].update(
        error='missing <request.json>'), failed('read.denial_applies')


def main(directory):
    directory = Path(directory)
    directory.mkdir()
    records, rejected = [], set()
    for name, change, expected in controls():
        state = build()
        change(state)
        report = checker.evaluate(state)
        found = publication.diagnostics(report)
        dest = directory / name.replace(':', '--')
        dest.mkdir()
        (dest / 'state.json').write_text(publication.encode(state))
        (dest / 'report.json').write_text(publication.encode(report))
        assert found == expected, (name, sorted(expected), sorted(found))
        rejected |= {ident for ident, status in found if status == 'failed'}
        records.append(dict(name=name, expected=sorted(expected), actual=sorted(found)))
    # Every row the checker reports has a control that fails it.
    obligations = {row['id'] for row in checker.evaluate(build())['rows']}
    assert obligations == rejected, (sorted(obligations - rejected), sorted(rejected - obligations))
    (directory / 'controls.json').write_text(publication.encode(records))
    print(f'{len(records)} exact test-input run controls matched; {len(obligations)} rows each rejected by a control')


if __name__ == '__main__':
    main(sys.argv[1])
