#!/usr/bin/env python3
"""Independent expectations for submissions made with `test-input run`.

Three things are kept apart for every control. The submission row reads what
was launched: the recorded command, the route and the delivered request. The
echo row reads the reply's `test_overrides`, which states what the host was
given. The intervention row reads only what the host or the worker observed
of its own execution, and never the echo; it alone credits activation.

Refusals are read at the boundary that made them: a usage refusal has no
client capture, a host refusal has no worker, and a native argument refusal
has a worker that exited before readiness. Constructed controls are not
evidence of native occurrence.
"""
import json

from check_test_input import BOUND, IDENTITY_FIELDS, Results, exact, expected_document, get, mapping, sample_ok
from file_observation import fresh_content, fresh_identity, fresh_syscalls, target_changes

# Authored here from the documented allowances, not read from the limits manifest.
SENTINEL_MS = 120000
SENTINEL_FLOOR_MS = 50
READY_BUDGET_MS = 1000
QUICK_READY_MS = 300
QUICK_SENTINEL_MS = 1000
MISSING_VALIDATOR = '/nonexistent/pw-test-input-validator'
MISSING_WORKER = '/nonexistent/pw-test-input-worker'
MISSING_EQUIPMENT = '/nonexistent/pw-test-input-equipment'
FLAGS = dict(
    worker_timeout_ms='--worker-timeout-ms', worker_pre_ready_hang_ms='--worker-pre-ready-hang-ms',
    worker_post_apply_hang_ms='--worker-post-apply-hang-ms', worker_post_apply_kill_signal='--worker-post-apply-kill-signal',
    worker_kill_before_publish_slot='--worker-kill-before-publish-slot',
    validator_executable_path='--validator-executable-path', validator_io_timeout_ms='--validator-io-timeout-ms',
    validator_total_timeout_ms='--validator-total-timeout-ms')
# One submission per selected control: its controls and the observed exit and outcome.
ACTIVATIONS = dict(
    worker_timeout_ms=(dict(worker_timeout_ms=7000), 0, 'finished'),
    worker_post_apply_hang_ms=(dict(worker_post_apply_hang_ms=2000), 0, 'finished'),
    worker_pre_ready_hang_ms=(dict(worker_pre_ready_hang_ms=400), 0, 'finished'),
    worker_post_apply_kill_signal=(dict(worker_post_apply_kill_signal=9), 1, 'runner_failed'),
    worker_kill_before_publish_slot=(dict(worker_kill_before_publish_slot=0), 1, 'runner_failed'),
    validator_executable_path=(dict(validator_executable_path=MISSING_VALIDATOR), 1, 'validator_spawn_failed'),
    # The substituted transcript validator is this submission's instrument; `validator` is its path.
    validator_io_timeout_ms=(dict(validator_executable_path=None, validator_io_timeout_ms=500), 1, 'validator_no_reply'),
    validator_total_timeout_ms=(dict(validator_total_timeout_ms=1), 1, 'validator_unavailable'))
assert set(ACTIVATIONS) == set(FLAGS)
# Arguments after `test-input run`, with the request path where None stands, and the refusal's text.
USAGE = dict(
    not_an_integer=(['--worker-timeout-ms', 'soon', None], 'invalid value for --worker-timeout-ms'),
    fractional=(['--worker-timeout-ms', '1.5', None], 'invalid value for --worker-timeout-ms'),
    beyond_64_bits=(['--worker-timeout-ms', '9223372036854775808', None], 'invalid value for --worker-timeout-ms'),
    missing_value=([None, '--validator-io-timeout-ms'], 'missing value for --validator-io-timeout-ms'),
    duplicate=(['--worker-timeout-ms', '5000', '--worker-timeout-ms', '6000', None], 'duplicate argument: --worker-timeout-ms'),
    unknown_flag=(['--worker-timeout', '5000', None], 'unknown argument: --worker-timeout'))
# The same flag after plain `run`, which has no such option.
ORDINARY_USAGE = (['--worker-timeout-ms', '5000', None], 'unknown argument: --worker-timeout-ms')
# One value above each worker argument's own range, each its own submission.
NATIVE_RANGE = dict(worker_post_apply_hang_ms=60001, worker_pre_ready_hang_ms=60001,
                    worker_post_apply_kill_signal=32, worker_kill_before_publish_slot=256)
# Two controls in one submission, a slot the one-step plan never reaches, an allowance below the
# floor beside a delay that outlasts it, and a control beside a request the host refuses to decode.
COMBINED = dict(worker_timeout_ms=7000, worker_pre_ready_hang_ms=400)
UNREACHED = dict(worker_kill_before_publish_slot=5)
FLOOR = dict(worker_timeout_ms=1, worker_post_apply_hang_ms=2000)
EARLY = dict(worker_post_apply_kill_signal=9)
EARLY_REFUSAL = dict(code='unknown_field', path=['misspelled_intent'])
LEGACY_REFUSAL = dict(code='inapplicable_field', path=['_test_overrides'])
# A request block on an experimental submission, and the controls submitted beside it.
LEGACY_BLOCKS = dict(cli=(dict(worker_timeout_ms=5000), {}), inert=(dict(worker_executable_path=None), {}),
                     mixed=(dict(worker_executable_path=MISSING_WORKER), dict(worker_post_apply_kill_signal=9)),
                     client=(dict(worker_timeout_ms=5000), {}))
CLIENT_CONTROLS = dict(worker_timeout_ms=7000)
CLIENT_FRACTIONAL = dict(worker_timeout_ms=1.5)
CLIENT_FRACTIONAL_REFUSAL = dict(code='type_mismatch', path=['_test_overrides', 'worker_timeout_ms'])
# A control in an ordinary request's block is refused at its member whatever value it holds. Beside
# each control's acting value stands one the host would not forward or would read as absent.
ORDINARY_INERT = dict(worker_timeout_ms=None, worker_pre_ready_hang_ms=0, worker_post_apply_hang_ms=-1,
                      worker_post_apply_kill_signal=0, worker_kill_before_publish_slot=-1,
                      validator_executable_path=None, validator_io_timeout_ms=None, validator_total_timeout_ms=None)
assert set(ORDINARY_INERT) == set(FLAGS)
# A control beside the worker substitution, and two controls: the block and the member the host names,
# the first of the controls in the host's own order.
ORDINARY_BLOCKS = dict(mixed=(dict(worker_executable_path=MISSING_WORKER, worker_timeout_ms=5000), 'worker_timeout_ms'),
                       combined=(dict(validator_total_timeout_ms=1, worker_post_apply_hang_ms=2000), 'worker_post_apply_hang_ms'))
# The two substitutions an ordinary request's block keeps, each on its own request form.
UNSELECTED = dict(worker=dict(worker_executable_path=MISSING_WORKER),
                  actor_equipment=dict(actor_equipment_executable_paths=dict(selected=MISSING_EQUIPMENT)))
DENIAL = '(version 1)(allow default)(deny process-fork)'


def attempt_slot_started(index):
    """The worker's progress word for an attempt it started and did not complete."""
    return dict(operation=9, stage=1, index=index, raw=(9 << 24) | (1 << 20) | (index + 1))


def two_reads(identity, target):
    """The published read with a second, identical read: the transcript validator answers the first only."""
    document = expected_document(identity, target)
    second = json.loads(json.dumps(document['probe_plan'][0]))
    second['step_id'] = 'read-target-again'
    document['probe_plan'].append(second)
    return document


def actor_form(document):
    """The same policy and read as the one visit of one applied actor."""
    document = dict(document)
    policy, plan = document.pop('policy'), document.pop('probe_plan')
    document['actors'] = [dict(actor_id='subject', equipment='selected', sandbox=dict(mode='apply', policy=policy))]
    document['phases'] = [dict(phase_id='main', actor_id='subject', actions=plan)]
    return document


def request_for(name, identity, target, block=None):
    document = two_reads(identity, target) if name == 'validator_io_timeout_ms' else expected_document(identity, target)
    if name == 'early_refusal':
        document['misspelled_intent'] = True
    if name == 'actor_equipment':
        document = actor_form(document)
    if block is not None:
        document['_test_overrides'] = block
    return document


def controls_for(name, state):
    controls = dict(ACTIVATIONS[name][0])
    if controls.get('validator_executable_path', '') is None:
        controls['validator_executable_path'] = state.get('validator')
    return controls


def ordinary_block(key, state, *, inert=False):
    """The one-member block naming a control: its acting value, or the inert one."""
    return {key: ORDINARY_INERT[key] if inert else controls_for(key, state)[key]}


def ordinary_refusal(key):
    return dict(code='inapplicable_field', path=['_test_overrides', key])


def flag_arguments(controls):
    return [item for key, value in controls.items() for item in (FLAGS[key], str(value))]


def submitted(record, entry, document, controls):
    """The recorded launch: route, command, controls and a delivered request equal to the ordinary one."""
    invocation = mapping(record.get('invocation'))
    argv = invocation.get('argv') if isinstance(invocation.get('argv'), list) else []
    try:
        delivered = json.loads(record.get('delivered'))
    except (TypeError, ValueError):
        delivered = None
    if entry == 'cli':
        command = argv[1:3] == ['test-input', 'run'] and argv[4:4 + 2 * len(controls)] == flag_arguments(controls)
    else:
        command = argv[1:4] == ['run', '--experimental-controls', json.dumps(controls)]
    return invocation.get('requested_route') == 'experimental_' + entry and invocation.get('entry') == entry and \
        invocation.get('state') == 'exited' and invocation.get('requested_controls') == controls and command and \
        delivered == document and isinstance(record.get('delivered'), str) and record.get('delivered') == record.get('ordinary')


def read_completed(step, sample, target):
    """One completed fresh read of the sampled file, answered `allow` by the validator when one answered."""
    attempt = mapping(mapping(step).get('attempt'))
    identity = {key: get(sample, 'stat', field) for key, field in IDENTITY_FIELDS.items()}
    return attempt.get('outcome') == 'ok' and exact(attempt.get('rc'), 0) and not fresh_syscalls(attempt, BOUND) and \
        not fresh_identity(attempt, identity, target) and not fresh_content(attempt, sample or {}, target)


def refused_before_launch(reply, failure):
    return isinstance(reply, dict) and reply.get('normalized_outcome') == 'bad_request' and \
        reply.get('request_failure') == failure and reply.get('steps') == [] and \
        reply.get('runner_subprocess') is None and not reply.get('phases') and reply.get('test_overrides') is None


def client_received(record, identity):
    """An admitted client capture of the inspected build carrying one host reply."""
    capture = mapping(record.get('capture'))
    return exact(record.get('exit'), 0) and record.get('capture_errors') == [] and capture.get('contract') == identity and \
        capture.get('terminal') == 'runner_reply' and get(capture, 'submission', 'state') == 'invoked' and \
        isinstance(record.get('reply'), dict) and get(record.get('reply'), 'producer', 'contract') == identity


def worker_signaled(worker, *, partial):
    return exact(worker.get('term_signal'), 9) and worker.get('exit_code') is None and worker.get('reaped') is True and \
        worker.get('termination_request') is None and worker.get('done_observed') is False and \
        worker.get('partial_steps') is partial and worker.get('poll_stop_reason') == 'child_reaped'


def intervened(name, record, state):
    """What the host or worker observed of the named control, without reading the echo."""
    reply = mapping(record.get('reply'))
    worker = mapping(reply.get('runner_subprocess'))
    phase = mapping(get(reply, 'phases', 0))
    step = mapping(get(reply, 'steps', 0))
    sample, target = record.get('before'), state.get('target')
    if name == 'worker_timeout_ms':
        return exact(get(worker, 'sentinel_wait', 'budget_ms'), 7000) and get(worker, 'sentinel_wait', 'stop') == 'done'
    if name == 'worker_post_apply_hang_ms':
        elapsed = get(worker, 'sentinel_wait', 'elapsed_ms')
        return type(elapsed) is int and elapsed >= 1900 and get(worker, 'sentinel_wait', 'stop') == 'done' and \
            exact(get(worker, 'sentinel_wait', 'budget_ms'), SENTINEL_MS) and read_completed(step, sample, target)
    if name == 'worker_pre_ready_hang_ms':
        elapsed = get(worker, 'ready_wait', 'elapsed_ms')
        return type(elapsed) is int and 380 <= elapsed and get(worker, 'ready_wait', 'stop') == 'received' and \
            exact(get(worker, 'ready_wait', 'budget_ms'), READY_BUDGET_MS)
    if name == 'worker_post_apply_kill_signal':
        return worker_signaled(worker, partial=False) and read_completed(step, sample, target)
    if name == 'worker_kill_before_publish_slot':
        return worker_signaled(worker, partial=True) and get(worker, 'worker_evidence', 'progress') == attempt_slot_started(0) and \
            get(step, 'attempt', 'outcome') == 'no_completed_result'
    if name == 'validator_executable_path':
        failure = mapping(phase.get('validator_spawn_failure'))
        return failure.get('executable_path') == MISSING_VALIDATOR and failure.get('operation') == 'posix_spawn' and \
            failure.get('origin') == 'runner_host' and exact(failure.get('return_code'), 2) and \
            phase.get('validator_subprocess') is None and read_completed(step, sample, target)
    if name == 'validator_io_timeout_ms':
        child = mapping(phase.get('validator_subprocess'))
        receipt = mapping(record.get('validator_receipt'))
        return child.get('stdout_collection_stop') == 'deadline' and '500 ms I/O deadline' in str(child.get('io_error')) and \
            exact(get(child, 'termination_request', 'signal'), 9) and child.get('reaped') is True and \
            [get(row, 'step_id') for row in child.get('records') or []] == ['read-target'] and \
            type(worker.get('pid')) is int and exact(receipt.get('target_pid'), worker.get('pid')) and \
            [get(probe, 'step_id') for probe in receipt.get('probes') or []] == ['read-target', 'read-target-again']
    if name == 'validator_total_timeout_ms':
        return phase.get('collection_status') == 'budget_exhausted' and phase.get('validator_subprocess') is None and \
            phase.get('validator_spawn_failure') is None and get(phase, 'ordering', 'validator_disposition') == 'not_spawned' and \
            read_completed(step, sample, target)
    raise KeyError(name)


def envelope_rows(r, label, record, identity, exit_code, outcome):
    """Observed status beside the published result, the build, and the independent consumer's reading."""
    envelope = record.get('envelope')
    r.check(label + '.status', exact(record.get('exit'), exit_code) and exact(get(envelope, 'result', 'exit_code'), exit_code) and
            exact(get(envelope, 'result', 'ok'), exit_code == 0) and get(envelope, 'kind') == 'run' and
            get(envelope, 'result', 'normalized_outcome') == outcome, 'observed and published status independently pinned')
    identified = get(envelope, 'build', 'contract') == identity
    r.check(label + '.build', identified, 'envelope identity before reply interpretation')
    r.check(label + '.consumer', identified and record.get('consumer_errors') == [], record.get('consumer_errors'))
    return identified and isinstance(record.get('reply'), dict)


def unchanged(record, target, payload):
    before, after = record.get('before'), record.get('after')
    return sample_ok(before, target, payload) and sample_ok(after, target, payload) and \
        not target_changes({target: before}, {target: after})


def baseline(reply, sample, target):
    """An ordinary finished run of the one read: default allowances and one collected query."""
    worker = mapping(reply.get('runner_subprocess'))
    phase = mapping(get(reply, 'phases', 0))
    query = mapping(get(reply, 'steps', 0, 'sandbox_check'))
    ready, sentinel = get(worker, 'ready_wait', 'elapsed_ms'), get(worker, 'sentinel_wait', 'elapsed_ms')
    return reply.get('normalized_outcome') == 'finished' and exact(worker.get('exit_code'), 0) and \
        worker.get('reaped') is True and worker.get('done_observed') is True and \
        exact(get(worker, 'sentinel_wait', 'budget_ms'), SENTINEL_MS) and type(sentinel) is int and sentinel < QUICK_SENTINEL_MS and \
        exact(get(worker, 'ready_wait', 'budget_ms'), READY_BUDGET_MS) and type(ready) is int and ready < QUICK_READY_MS and \
        phase.get('collection_status') == 'collected' and get(phase, 'validator_subprocess', 'reaped') is True and \
        query.get('result_source') == 'validator' and query.get('outcome') == 'allow' and \
        get(reply, 'steps', 0, 'comparison', 'order') == 'query_first' and len(reply.get('steps') or []) == 1 and \
        read_completed(get(reply, 'steps', 0), sample, target)


def evaluate(state):
    r = Results()
    identity, target, payload = state.get('identity'), state.get('target'), bytes.fromhex(state.get('payload_hex') or '')
    scenarios = mapping(state.get('scenarios'))

    # `test-input read`: the same bytes before and after the submissions, and under a profile that denies fork.
    read = mapping(state.get('read'))
    first, last, denied = (mapping(read.get(name)) for name in ('first', 'last', 'denied'))
    r.check('read.publication', all(exact(item.get('exit'), 0) and item.get('stderr') == '' for item in (first, last)) and
            isinstance(first.get('stdout'), str) and first.get('stdout') == last.get('stdout') and
            first['stdout'].endswith('}\n') and json.loads(first['stdout']) == expected_document(identity, target) and
            first.get('argv', [])[1:] == ['test-input', 'read', '--target', target] == last.get('argv', [])[1:],
            'the published read input is the independently authored body, before and after the submissions')
    r.check('read.launches_nothing', exact(denied.get('exit'), 0) and denied.get('stderr') == '' and
            first.get('stdout') is not None and denied.get('stdout') == first.get('stdout') and
            denied.get('argv', [])[:3] == ['/usr/bin/sandbox-exec', '-p', DENIAL] and
            denied.get('argv', [])[4:] == ['test-input', 'read', '--target', target],
            'publication completes unchanged where the process may not fork')
    bitten = mapping(scenarios.get('denied_run'))
    r.check('read.denial_applies', exact(bitten.get('exit'), 2) and
            bitten.get('argv', [])[:3] == ['/usr/bin/sandbox-exec', '-p', DENIAL] and
            bitten.get('argv', [])[4:6] == ['test-input', 'run'] and
            get(bitten.get('envelope'), 'result', 'normalized_outcome') == 'tool_error' and
            'pw-runner-client' in str(get(bitten.get('envelope'), 'result', 'error')) and
            'Operation not permitted' in str(get(bitten.get('envelope'), 'result', 'error')) and
            get(bitten.get('envelope'), 'data', 'runner_client') is None,
            'the same profile stops a command that must launch its client')

    # The ordinary neighbour and the experimental submission without controls.
    neighbour = mapping(scenarios.get('neighbour'))
    document = expected_document(identity, target)
    admitted = envelope_rows(r, 'neighbour', neighbour, identity, 0, 'finished')
    r.check('neighbour.baseline', neighbour.get('argv', [])[1:2] == ['run'] and neighbour.get('delivered_document') == document and
            baseline(mapping(neighbour.get('reply')), neighbour.get('before'), target) and
            mapping(neighbour.get('reply')).get('test_overrides') is None and unchanged(neighbour, target, payload),
            'ordinary run: default allowances, one collected query, one completed read and no echo', available=admitted)
    zero = mapping(scenarios.get('zero_controls'))
    r.check('zero_controls.submission', submitted(zero, 'cli', document, {}) and
            len(mapping(zero.get('invocation')).get('argv') or []) == 6, 'test-input run with the request and a timeout only')
    admitted = envelope_rows(r, 'zero_controls', zero, identity, 0, 'finished')
    r.check('zero_controls.echo', mapping(zero.get('reply')).get('test_overrides') == {} and
            'test_overrides' in mapping(zero.get('reply')), 'an empty controls object is echoed as supplied', available=admitted)
    r.check('zero_controls.neighbour', baseline(mapping(zero.get('reply')), zero.get('before'), target) and
            unchanged(zero, target, payload), 'the allowances, collection and read of the ordinary neighbour', available=admitted)

    for name, (_, exit_code, outcome) in ACTIVATIONS.items():
        record = mapping(scenarios.get(name))
        controls = controls_for(name, state)
        r.check(name + '.submission', submitted(record, 'cli', request_for(name, identity, target), controls),
                'recorded route, flags and an unchanged delivered request')
        admitted = envelope_rows(r, name, record, identity, exit_code, outcome)
        reply = mapping(record.get('reply'))
        r.check(name + '.echo', reply.get('test_overrides') == controls, 'the reply mirrors the supplied controls', available=admitted)
        r.check(name + '.intervention', admitted and unchanged(record, target, payload) and intervened(name, record, state),
                'the host or worker observation of the control, independent of the echo', available=admitted)
    provenance = mapping(get(mapping(scenarios.get('validator_executable_path')).get('envelope'), 'data', 'specimen', 'binaries', 'validator'))
    r.check('validator_executable_path.provenance', provenance.get('path') == MISSING_VALIDATOR and
            provenance.get('verification') == 'unavailable' and provenance.get('actual_sha256') is None and
            get(neighbour.get('envelope'), 'data', 'specimen', 'binaries', 'validator') is None and
            'validator' in mapping(get(neighbour.get('envelope'), 'data', 'specimen', 'binaries')),
            'the dossier names the validator the control selected; the neighbour selects the packaged one')

    # Malformed syntax: refused by the controller with no client invocation.
    for name, (arguments, error) in dict(USAGE, ordinary_run=ORDINARY_USAGE).items():
        record = mapping(scenarios.get('usage.' + name))
        envelope = record.get('envelope')
        command = ['run'] if name == 'ordinary_run' else ['test-input', 'run']
        path = record.get('request_path')
        r.check('usage.' + name, exact(record.get('exit'), 2) and record.get('stderr') == '' and isinstance(path, str) and
                record.get('argv', [])[1:] == command + [path if item is None else item for item in arguments] and
                get(envelope, 'kind') == 'run' and get(envelope, 'result', 'normalized_outcome') == 'tool_error' and
                exact(get(envelope, 'result', 'exit_code'), 2) and get(envelope, 'result', 'error') == error and
                isinstance(get(envelope, 'data'), dict) and get(envelope, 'data', 'runner_client') is None and
                get(envelope, 'data', 'runner_result') is None, 'usage refusal with exit 2 and no client capture')

    # Two controls in one submission: each read from the host's own wait record.
    record = mapping(scenarios.get('combined'))
    r.check('combined.submission', submitted(record, 'cli', document, COMBINED), 'both controls travel as flags')
    admitted = envelope_rows(r, 'combined', record, identity, 0, 'finished')
    reply = mapping(record.get('reply'))
    worker = mapping(reply.get('runner_subprocess'))
    delay = get(worker, 'ready_wait', 'elapsed_ms')
    r.check('combined.echo', reply.get('test_overrides') == COMBINED, 'the reply mirrors both controls', available=admitted)
    r.check('combined.intervention', unchanged(record, target, payload) and
            exact(get(worker, 'sentinel_wait', 'budget_ms'), 7000) and get(worker, 'sentinel_wait', 'stop') == 'done' and
            type(delay) is int and delay >= 380 and get(worker, 'ready_wait', 'stop') == 'received' and
            read_completed(get(reply, 'steps', 0), record.get('before'), target),
            'the allowance and the delay, each observed by the host', available=admitted)

    # A control whose boundary no action reaches: echoed, with the ordinary neighbour's completion.
    record = mapping(scenarios.get('unreached'))
    r.check('unreached.submission', submitted(record, 'cli', document, UNREACHED), 'a slot beyond the one-step plan travels as a flag')
    admitted = envelope_rows(r, 'unreached', record, identity, 0, 'finished')
    reply = mapping(record.get('reply'))
    r.check('unreached.echo', reply.get('test_overrides') == UNREACHED, 'the reply mirrors a control that was supplied', available=admitted)
    r.check('unreached.no_intervention', baseline(reply, record.get('before'), target) and unchanged(record, target, payload),
            'no action reached the slot: the neighbour\'s allowances, collection and completed read', available=admitted)

    # The ordinary worker allowance has a floor: one millisecond is submitted and the host waits the floor.
    record = mapping(scenarios.get('floor'))
    r.check('floor.submission', submitted(record, 'cli', document, FLOOR), 'the allowance below the floor travels as written')
    admitted = envelope_rows(r, 'floor', record, identity, 1, 'runner_timeout')
    reply = mapping(record.get('reply'))
    worker = mapping(reply.get('runner_subprocess'))
    wait = mapping(worker.get('sentinel_wait'))
    r.check('floor.echo', reply.get('test_overrides') == FLOOR, 'the reply mirrors the supplied value, not the floored one', available=admitted)
    r.check('floor.intervention', exact(wait.get('budget_ms'), SENTINEL_FLOOR_MS) and wait.get('stop') == 'sentinel_deadline' and
            type(wait.get('elapsed_ms')) is int and type(wait.get('excluded_ms')) is int and
            wait['elapsed_ms'] - wait['excluded_ms'] >= SENTINEL_FLOOR_MS and exact(worker.get('term_signal'), 9) and
            exact(get(worker, 'termination_request', 'signal'), 9) and worker.get('reaped') is True and
            worker.get('done_observed') is False and unchanged(record, target, payload),
            'the host waited the floor and ended the delayed worker at that deadline', available=admitted)

    # A control beside a request the host refuses to decode: refused before the control could act.
    record = mapping(scenarios.get('early_refusal'))
    r.check('early_refusal.submission', submitted(record, 'cli', request_for('early_refusal', identity, target), EARLY),
            'the control travels beside the request the host will refuse')
    admitted = envelope_rows(r, 'early_refusal', record, identity, 1, 'bad_request')
    r.check('early_refusal.refusal', refused_before_launch(record.get('reply'), EARLY_REFUSAL) and
            get(record.get('envelope'), 'data', 'request_failure') == EARLY_REFUSAL and unchanged(record, target, payload),
            'host refusal at the unknown request field, before any worker and with no echo', available=admitted)

    # A value the worker's own argument grammar refuses: submitted, and refused by the launched worker.
    for key, value in NATIVE_RANGE.items():
        label, controls = 'native_range.' + key, {key: value}
        record = mapping(scenarios.get(label))
        r.check(label + '.submission', submitted(record, 'cli', document, controls), 'the out-of-range value travels as a flag')
        admitted = envelope_rows(r, label, record, identity, 1, 'runner_failed')
        reply = mapping(record.get('reply'))
        worker = mapping(reply.get('runner_subprocess'))
        r.check(label + '.boundary', exact(worker.get('exit_code'), 2) and worker.get('term_signal') is None and
                worker.get('reaped') is True and worker.get('ready_byte_received') is False and worker.get('done_observed') is False and
                reply.get('sandboxed_after_apply') is not True and reply.get('request_failure') is None and
                get(record.get('envelope'), 'data', 'request_failure') is None and reply.get('test_overrides') == controls and
                get(record.get('envelope'), 'data', 'runner_client', 'submission') == 'invoked' and
                get(reply, 'steps', 0, 'attempt', 'outcome') == 'no_completed_result' and unchanged(record, target, payload),
                'the launched worker exits 2 before readiness; no request refusal', available=admitted)

    # A request that carries its own block on an experimental submission, alone or beside a control.
    for name in ('cli', 'inert', 'mixed'):
        block, controls = LEGACY_BLOCKS[name]
        record = mapping(scenarios.get('legacy_block.' + name))
        r.check('legacy_block.' + name + '.submission',
                submitted(record, 'cli', request_for(name, identity, target, block), controls),
                'the block is delivered as written, beside the controls given')
        admitted = envelope_rows(r, 'legacy_block.' + name, record, identity, 1, 'bad_request')
        r.check('legacy_block.' + name + '.refusal', refused_before_launch(record.get('reply'), LEGACY_REFUSAL) and
                get(record.get('envelope'), 'data', 'request_failure') == LEGACY_REFUSAL and unchanged(record, target, payload),
                'host refusal at the block, before any worker', available=admitted)
    record = mapping(scenarios.get('legacy_block.empty'))
    r.check('legacy_block.empty.submission', submitted(record, 'cli', request_for('empty', identity, target, {}), {}),
            'an empty block is delivered as written')
    admitted = envelope_rows(r, 'legacy_block.empty', record, identity, 0, 'finished')
    r.check('legacy_block.empty.admitted', baseline(mapping(record.get('reply')), record.get('before'), target) and
            mapping(record.get('reply')).get('test_overrides') == {}, 'an empty block is admitted', available=admitted)

    # The runner client's own experimental submission, without the controller.
    for name, controls, block, refusal in (('client.activation', CLIENT_CONTROLS, None, None),
                                           ('legacy_block.client', {}, LEGACY_BLOCKS['client'][0], LEGACY_REFUSAL),
                                           ('client.fractional', CLIENT_FRACTIONAL, None, CLIENT_FRACTIONAL_REFUSAL)):
        record = mapping(scenarios.get(name))
        r.check(name + '.submission', submitted(record, 'client', request_for(name, identity, target, block), controls),
                'the client receives the request and one controls object')
        received = client_received(record, identity)
        r.check(name + '.capture', received, 'an admitted client capture carrying one host reply')
        reply = mapping(record.get('reply'))
        if refusal is None:
            r.check(name + '.intervention', exact(get(reply, 'runner_subprocess', 'sentinel_wait', 'budget_ms'), 7000) and
                    reply.get('normalized_outcome') == 'finished' and reply.get('test_overrides') == controls and
                    read_completed(get(reply, 'steps', 0), record.get('before'), target) and unchanged(record, target, payload),
                    'the host used the allowance the controls object named', available=received)
        else:
            r.check(name + '.refusal', refused_before_launch(record.get('reply'), refusal) and unchanged(record, target, payload),
                    'host refusal at the block or the control, before any worker', available=received)

    # A control in an ordinary request's block: refused at its member through plain `run` and through
    # the runner client's ordinary call, before any worker, with a value that would act and with an inert one.
    def ordinary_rows(label, block, key, *, client=False):
        record = mapping(scenarios.get(label))
        refusal, wanted = ordinary_refusal(key), request_for(key, identity, target, block)
        argv = record.get('argv') if isinstance(record.get('argv'), list) else []
        ordinary = argv[1:2] == ['run'] and '--experimental-controls' not in argv and record.get('delivered_document') == wanted
        if client:
            received = client_received(record, identity)
            r.check(label + '.capture', received, 'an admitted client capture carrying one host reply')
            r.check(label + '.refusal', ordinary and refused_before_launch(record.get('reply'), refusal) and
                    unchanged(record, target, payload),
                    'the ordinary call refuses the block at the control, before any worker', available=received)
        else:
            admitted = envelope_rows(r, label, record, identity, 1, 'bad_request')
            r.check(label + '.refusal', ordinary and refused_before_launch(record.get('reply'), refusal) and
                    get(record.get('envelope'), 'data', 'request_failure') == refusal and unchanged(record, target, payload),
                    'plain run delivers the block and the host refuses it at the control, before any worker', available=admitted)

    for key in FLAGS:
        ordinary_rows('ordinary.' + key + '.cli', ordinary_block(key, state), key)
        ordinary_rows('ordinary.' + key + '.inert', ordinary_block(key, state, inert=True), key)
        ordinary_rows('ordinary.' + key + '.client', ordinary_block(key, state), key, client=True)
    for name, (block, key) in ORDINARY_BLOCKS.items():
        ordinary_rows('ordinary.' + name, block, key)

    # The two substitutions an ordinary request's block still carries, through plain `run`.
    record = mapping(scenarios.get('unselected.worker'))
    block = UNSELECTED['worker']
    admitted = envelope_rows(r, 'unselected.worker', record, identity, 1, 'worker_spawn_failed')
    reply = mapping(record.get('reply'))
    provenance = mapping(get(record.get('envelope'), 'data', 'specimen', 'binaries', 'worker'))
    r.check('unselected.worker.substitution', record.get('argv', [])[1:2] == ['run'] and
            record.get('delivered_document') == request_for('worker', identity, target, block) and
            reply.get('test_overrides') == block and reply.get('request_failure') is None and
            reply.get('runner_subprocess') is None and 'posix_spawn' in str(reply.get('error')) and
            get(reply, 'steps', 0, 'attempt', 'outcome') == 'no_completed_result' and
            provenance.get('path') == MISSING_WORKER and provenance.get('verification') == 'unavailable' and
            unchanged(record, target, payload),
            'the host tried to spawn the worker the block names, and the dossier names it', available=admitted)
    record = mapping(scenarios.get('unselected.actor_equipment'))
    block = UNSELECTED['actor_equipment']
    admitted = envelope_rows(r, 'unselected.actor_equipment', record, identity, 1, 'runner_failed')
    reply = mapping(record.get('reply'))
    r.check('unselected.actor_equipment.substitution', record.get('argv', [])[1:2] == ['run'] and
            record.get('delivered_document') == request_for('actor_equipment', identity, target, block) and
            reply.get('test_overrides') == block and reply.get('request_failure') is None and
            get(reply, 'preparation_failure', 'code') == 'equipment_binding_refused' and
            get(reply, 'preparation_failure', 'stage') == 'equipment' and
            [(get(actor, 'actor_id'), get(actor, 'launch'), get(actor, 'subprocess')) for actor in reply.get('actors') or []] ==
            [('subject', None, None)] and reply.get('steps') == [] and unchanged(record, target, payload),
            'equipment preparation refused the binding the block names, before any actor launch', available=admitted)
    return r.report()
