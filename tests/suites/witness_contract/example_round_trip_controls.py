#!/usr/bin/env python3
"""Rejected controls for every assertion of the example round-trip checker.

A constructed document stands in for the app's emission: this case tests the
checker, not the app. Its envelope is the authored ordinary run under
tests/fixtures/blackbox_e2e reduced to one read step, placed in retained
capture files exactly as the live case leaves them. No process is launched
and nothing here is a native observation.

Each rejected control introduces one logical fault and states, independently
of the checker's output, the exact set of (assertion identifier,
classification) pairs it must produce. A control earns coverage for its
target assertions only when the actual set matches. The shared consumer's
aggregate diagnostic is permitted beside any other control's set and earns
nothing there; its own propagation control requires it exactly. Coverage is
complete when every assertion in the checker's table has a matched control.
"""
import base64
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_context
from blackbox import bind_constructed_envelope, envelope_skeleton, recapture_host_reply
import check_example_round_trip as checker
from check_example_round_trip import (CONSISTENCY, EXECUTION_UNAVAILABLE, NATIVE_OBSERVATION,
                                      PREREQUISITE_UNESTABLISHED, REFUSALS, UNKNOWN_MEMBER)

FIXTURE = ROOT / 'tests/fixtures/blackbox_e2e/checker/current/constructed_run.json'
DEVELOPMENT = 'development:' + 'c0' * 32
RELEASE = 'release:v9.9.9'
CONSUMER = ('consumer_validation', CONSISTENCY)
# Everything that reads the run: unevaluated when the emission or its bounds fail.
RUN_GROUPS = ('admission', 'identity', 'execution', 'echo', 'reported', 'readers', 'native', 'refusals')
REPLY_DEPENDENT = ('admission.reply_policy_digest', 'echo.specimen_id', 'echo.step_ids', 'echo.queries',
                   'echo.attempts', 'readers.disposition_integrity', 'readers.disposition_issues',
                   'native.completion', 'native.prediction', 'native.order', 'native.attempt',
                   'native.targets_unchanged')


def pairs(*identifiers):
    return {(ident, checker.CLASSIFICATION[ident]) for ident in identifiers}


# ---------------------------------------------------------------------------
# The constructed passing input
# ---------------------------------------------------------------------------

def constructed_run(identity):
    """The authored run reduced to its first step, read as an allowed, successful file read."""
    envelope = bind_constructed_envelope(json.loads(FIXTURE.read_text()))
    reply = envelope['data']['runner_result']
    step = reply['steps'][0]
    ident = step['step_id']
    reply['steps'] = [step]
    step['sandbox_check']['operation'] = 'file-read-data'
    step['attempt']['requested_action'] = 'open_read'
    phase = reply['phases'][0]
    phase['action_ids'] = [ident]
    validator = phase['validator_subprocess']
    validator['expected_step_ids'] = [ident]
    validator['records'] = [record for record in validator['records'] if record['step_id'] == ident]
    for record in validator['records']:
        record['operation'] = 'file-read-data'
    disposition = reply['runner_subprocess']['disposition']
    disposition['steps'] = [row for row in disposition['steps'] if row['step_id'] == ident]
    envelope['build']['contract'] = identity
    reply['producer']['contract'] = identity
    envelope['data']['runner_client']['transport']['contract'] = identity
    return recapture_host_reply(envelope)


def refusal_envelope(identity, name):
    code, path, names_identity, component = REFUSALS[name]
    failure = {'code': code, 'path': list(path)}
    if names_identity:
        failure['expected_contract'] = identity
    result = dict(normalized_outcome='bad_request', ok=False, exit_code=1, error='constructed refusal')
    if component == 'controller':
        envelope = envelope_skeleton(None)
    else:
        envelope = envelope_skeleton({'producer': build_context.producer(identity), 'normalized_outcome': 'bad_request',
                                      'rc': 1, 'error': 'constructed refusal', 'steps': [], 'phases': [],
                                      'request_failure': dict(failure)})
        envelope['data']['runner_client']['transport']['contract'] = identity
    envelope['build']['contract'] = identity
    envelope['result'].update(result)
    envelope['data']['request_failure'] = failure
    return envelope


def build(identity=DEVELOPMENT):
    """Every retained input of a passing case, as values a control can change before they are written."""
    run = constructed_run(identity)
    reply = run['data']['runner_result']
    step = reply['steps'][0]
    target = step['attempt']['requested_path']
    document = {
        'contract': identity, 'specimen_id': reply['specimen_id'],
        'policy': {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'},
        'probe_plan': [{'step_id': step['step_id'],
                        'sandbox_check': {'operation': step['sandbox_check']['operation'],
                                          'filter': {'kind': step['sandbox_check']['filter_kind'],
                                                     'value': step['sandbox_check']['filter_value']}},
                        'attempt': {'kind': 'file', 'action': 'open_read', 'target': target}}],
    }
    emitted = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    digest = hashlib.sha256(document['policy']['sbpl_source'].encode()).hexdigest()
    reply['policy_sha256'] = digest
    run['data']['specimen']['policy']['augmentation'].update(original_sha256=digest, applied_sha256=digest)
    run['data']['runner_client']['request_delivery']['bytes_written'] = len(emitted) - 1
    recapture_host_reply(run)
    content = b'constructed target bytes\n'
    observed = {'targets': [{
        'target': target, 'resolved': target, 'regular_file': True, 'readable': True, 'error': None,
        'sha256': hashlib.sha256(content).hexdigest(), 'bytes_base64': base64.b64encode(content).decode(),
        'stat': {'st_dev': 16777234, 'st_ino': 4242, 'st_mode': 33188, 'st_uid': 0, 'st_gid': 0,
                 'st_size': len(content), 'st_mtime_ns': 1700000000000000000, 'st_ctime_ns': 1700000000000000000}}]}
    version = {'build': build_context.producer(identity), 'kind': 'version', 'generated_at_unix_ms': 1,
               'result': {'ok': True, 'exit_code': 0, 'rc': None, 'normalized_outcome': None, 'errno': None,
                          'error': None, 'stderr': None, 'stdout': None},
               'data': {'contract': identity}}
    state = {
        'version': {'exit': 0, 'envelope': version, 'stderr': b''},
        'example-1': {'exit': 0, 'stdout': emitted, 'stderr': b''},
        'example-2': {'exit': 0, 'stdout': emitted, 'stderr': b''},
        'property-list': {'path': '/constructed/Contents/Info.plist', 'PWContract': identity, 'error': None},
        'contract-example': {'snapshot': 'constructed', 'node': checker.EXAMPLE_NODE,
                             'document': {key: value for key, value in document.items() if key != 'contract'}},
        'targets-before': observed, 'targets-after': copy.deepcopy(observed),
        'run': {'exit': 0, 'envelope': run, 'stderr': b''},
        'refusals': {name: {'input': body, 'exit': 1, 'envelope': refusal_envelope(identity, name), 'stderr': b''}
                     for name, body in checker.refusal_inputs(emitted).items()},
    }
    return state


def write(directory, state):
    directory = Path(directory)
    directory.mkdir(parents=True)

    def invocation(base, entry):
        if 'stdout' in entry:
            stdout = entry['stdout']
        else:
            stdout = (json.dumps(entry['envelope'], indent=2) + '\n').encode()
        for suffix, value in (('.stdout', stdout), ('.stderr', entry.get('stderr'))):
            if value is not None:
                Path(str(base) + suffix).write_bytes(value)
        if entry.get('exit') is not None:
            Path(str(base) + '.exit').write_text(f'{entry["exit"]}\n')

    for name in ('version', 'example-1', 'example-2', 'run'):
        if state.get(name) is not None:
            invocation(directory / name, state[name])
    for name in ('property-list', 'contract-example', 'targets-before', 'targets-after'):
        if state.get(name) is not None:
            (directory / (name + '.json')).write_text(json.dumps(state[name], indent=2) + '\n')
    for name, entry in state['refusals'].items():
        base = directory / 'refusals' / name
        base.mkdir(parents=True)
        if entry.get('input') is not None:
            (base / 'input.json').write_bytes(entry['input'])
        invocation(base / 'run', entry)


# ---------------------------------------------------------------------------
# State accessors used by the controls
# ---------------------------------------------------------------------------

def document_of(state):
    return json.loads(state['example-1']['stdout'].decode())


def set_document(state, change):
    """Change the emitted document itself: both emissions, the snapshot's rendering and the refusal inputs agree."""
    document = document_of(state)
    change(document)
    emitted = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    state['example-1']['stdout'] = state['example-2']['stdout'] = emitted
    state['contract-example']['document'] = {key: value for key, value in document.items() if key != 'contract'}


def envelope_of(state):
    return state['run']['envelope']


def reply_of(state):
    return envelope_of(state)['data']['runner_result']


def step_of(state):
    return reply_of(state)['steps'][0]


def spawn_failed(state):
    """A coherent reply whose validator never ran: no prediction, honest `unestablished` order, exit 1."""
    envelope, reply = envelope_of(state), reply_of(state)
    reply.update(normalized_outcome='validator_spawn_failed', rc=1, error='constructed validator spawn failure')
    reply['phases'][0]['ordering'].update(validator_disposition='not_spawned')
    reply['phases'][0].pop('validator_subprocess')
    for step in reply['steps']:
        step['sandbox_check'].update(result_source='synthetic', native_rc=None, errno=None, outcome='error',
                                     missing_reason='validator_not_invoked')
        step['comparison']['order'] = 'unestablished'
    envelope['result'].update(normalized_outcome='validator_spawn_failed', ok=False, exit_code=1,
                              error='constructed validator spawn failure')
    state['run']['exit'] = 1


def no_reply(state):
    """A controller tool error: no client record, no reply and no assessment."""
    envelope = envelope_of(state)
    envelope['data'].update(runner_client=None, runner_result=None, runner_sandbox_diagnostics=None)
    envelope['result'].update(normalized_outcome='tool_error', ok=False, exit_code=2, error='constructed tool error')
    state['run']['exit'] = 2


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def controls():
    """(name, identity, change, targets, expected pairs, requirements) rows.

    `targets` are the assertions the control is about; `expected` is the full
    set its fault necessarily produces. Requirements name assertions that must
    be unevaluated or must hold, and whether the consumer must read cleanly.
    """
    rows = []

    def add(name, change, targets, also=(), *, identity=DEVELOPMENT, unevaluated=(), holds=(), clean=False,
            recapture=True, exactly_consumer=False):
        expected = pairs(*targets, *also)
        rows.append(dict(name=name, identity=identity, change=change, targets=tuple(targets), expected=expected,
                         unevaluated=tuple(unevaluated), holds=tuple(holds), clean=clean, recapture=recapture,
                         exactly_consumer=exactly_consumer))

    def emission(name, change, targets, also=()):
        # A failed emission prevents submission: nothing that reads a run is evaluated,
        # although the constructed run captures are present.
        add('emission_' + name, change, targets, also, unevaluated=RUN_GROUPS + ('passage.delivery_length',))

    emission('version_exit_nonzero', lambda s: s['version'].update(exit=1), ['emission.version_exit'])
    for which in ('example-1', 'example-2'):
        emission(which + '_exit_2', lambda s, which=which: s[which].update(exit=2), ['emission.example_exit'])
        emission(which + '_stderr', lambda s, which=which: s[which].update(stderr=b'warning\n'), ['emission.stderr_empty'])
    emission('first_malformed', lambda s: s['example-1'].update(stdout=b'{"contract":\n'), ['emission.json_object'])
    emission('second_malformed', lambda s: s['example-2'].update(stdout=b'{"contract":\n'),
             ['emission.json_object'], ['passage.emissions_identical'])
    emission('array', lambda s: (s['example-1'].update(stdout=b'[]\n'), s['example-2'].update(stdout=b'[]\n')),
             ['emission.json_object'])
    emission('framing_missing', lambda s: [s[w].update(stdout=s[w]['stdout'][:-1]) for w in ('example-1', 'example-2')],
             ['emission.framing_newline'])
    emission('framing_doubled', lambda s: [s[w].update(stdout=s[w]['stdout'] + b'\n') for w in ('example-1', 'example-2')],
             ['emission.framing_newline'])

    add('passage_version_build', lambda s: s['version']['envelope']['build'].update(contract=RELEASE),
        ['passage.contract_matches_version'])
    add('passage_version_data', lambda s: s['version']['envelope']['data'].update(contract=RELEASE),
        ['passage.contract_matches_version'])
    add('passage_version_unreadable', lambda s: s['version'].update(stdout=b'not an envelope\n'),
        ['passage.contract_matches_version'])
    add('passage_property_list_differs', lambda s: s['property-list'].update(PWContract=RELEASE),
        ['passage.contract_matches_property_list'])
    add('passage_property_list_absent', lambda s: s.update({'property-list': None}),
        ['passage.contract_matches_property_list'])
    add('passage_unpackaged_identity', lambda s: None, ['passage.contract_packaged_form'], identity='test:unpackaged')
    add('passage_emissions_differ',
        lambda s: s['example-2'].update(stdout=(json.dumps(document_of(s), sort_keys=True) + '\n').encode()),
        ['passage.emissions_identical'])
    add('passage_delivery_length',
        lambda s: envelope_of(s)['data']['runner_client']['request_delivery'].update(
            bytes_written=len(s['example-1']['stdout'])),
        ['passage.delivery_length'], recapture=False)
    add('passage_delivery_length_boolean',
        lambda s: envelope_of(s)['data']['runner_client']['request_delivery'].update(bytes_written=True),
        ['passage.delivery_length'], recapture=False)
    add('passage_rendering_member_differs', lambda s: s['contract-example']['document'].update(specimen_id='another'),
        ['passage.contract_rendering'])
    add('passage_rendering_extra_member', lambda s: s['contract-example']['document'].update(run_kind='label'),
        ['passage.contract_rendering'])
    add('passage_rendering_not_retained', lambda s: s.update({'contract-example': None}), ['passage.contract_rendering'])

    def bounds(name, change, targets, also=()):
        add('bounds_' + name, lambda s: set_document(s, change), targets, also,
            unevaluated=RUN_GROUPS + ('passage.delivery_length',))

    read_step = {'step_id': 'second', 'sandbox_check': {'operation': 'file-read-data',
                                                         'filter': {'kind': 'path', 'value': '/constructed/second'}}}
    bounds('empty_plan', lambda d: d.update(probe_plan=[]), ['bounds.ordinary_form'], ['bounds.paired_read_probe'])
    bounds('plan_not_an_array', lambda d: d.update(probe_plan={'step_id': 'x'}),
           ['bounds.ordinary_form'], ['bounds.paired_read_probe'])
    bounds('unpaired_probe', lambda d: d['probe_plan'][0].pop('sandbox_check'), ['bounds.paired_read_probe'])
    bounds('write_action', lambda d: d['probe_plan'].append(dict(
        read_step, attempt={'kind': 'file', 'action': 'open_write', 'target': '/constructed/second'})),
        ['bounds.read_only_attempts'])
    bounds('unlink_action', lambda d: d['probe_plan'].append(dict(
        read_step, attempt={'kind': 'file', 'action': 'unlink', 'target': '/constructed/second'})),
        ['bounds.read_only_attempts'])
    bounds('exec_action', lambda d: d['probe_plan'].append(dict(
        read_step, attempt={'kind': 'exec', 'action': 'spawn', 'target': '/usr/bin/true'})),
        ['bounds.read_only_attempts'])
    bounds('only_write_action', lambda d: d['probe_plan'][0]['attempt'].update(action='create'),
           ['bounds.read_only_attempts'], ['bounds.paired_read_probe'])
    bounds('test_overrides', lambda d: d.update(_test_overrides={}), ['bounds.no_test_overrides'])
    for key, value in (('runner_id', 'runner-ext'), ('runner_service', 'com.example.runner'),
                       ('runner_mode', 'standard'), ('runner', {'mode': 'byoxpc'})):
        bounds('selector_' + key, lambda d, key=key, value=value: d.update({key: value}), ['bounds.no_runner_selection'])
    bounds('augments', lambda d: d['policy'].update(augments=['constructed']), ['bounds.no_augments'])
    bounds('required_entitlement', lambda d: d.update(required_entitlements=['com.example.entitlement']),
           ['bounds.no_entitlement_requirement'])
    bounds('runner_required_entitlement',
           lambda d: d.update(runner={'required_entitlements': ['com.example.entitlement']}),
           ['bounds.no_entitlement_requirement'], ['bounds.no_runner_selection'])
    bounds('phases_in_place_of_plan',
           lambda d: (d.update(phases=[{'phase_id': 'p', 'actions': d['probe_plan']}]), d.pop('probe_plan')),
           ['bounds.ordinary_form'], ['bounds.paired_read_probe'])
    bounds('actors', lambda d: d.update(actors=[{'actor_id': 'a'}]), ['bounds.ordinary_form'])

    add('admission_request_failure',
        lambda s: envelope_of(s)['data'].update(request_failure={'code': 'unknown_field', 'path': ['x']}),
        ['admission.no_request_failure'], recapture=False)
    add('admission_bad_request_result',
        lambda s: (envelope_of(s)['result'].update(normalized_outcome='bad_request', ok=False, exit_code=1),
                   s['run'].update(exit=1)),
        ['admission.no_request_failure'], recapture=False)

    def host_refuses(state):
        envelope, reply = envelope_of(state), reply_of(state)
        failure = {'code': 'unknown_field', 'path': ['probe_plan', '0', 'unexpected']}
        reply.update(normalized_outcome='bad_request', rc=1, error='constructed host refusal', steps=[],
                     request_failure=dict(failure))
        reply['phases'] = []
        reply.pop('runner_subprocess', None)
        envelope['data']['request_failure'] = failure
        envelope['result'].update(normalized_outcome='bad_request', ok=False, exit_code=1,
                                  error='constructed host refusal')
        state['run']['exit'] = 1
    add('admission_host_refuses_the_example', host_refuses, ['admission.no_request_failure'],
        ['echo.step_ids', 'native.completion'], unevaluated=('echo.queries', 'echo.attempts', 'native.prediction',
                                                             'native.order', 'native.attempt'))
    add('admission_dossier_digest',
        lambda s: envelope_of(s)['data']['specimen']['policy']['augmentation'].update(original_sha256='0' * 64),
        ['admission.dossier_policy_digest'], recapture=False)
    add('admission_reply_digest', lambda s: reply_of(s).update(policy_sha256='0' * 64), ['admission.reply_policy_digest'])

    # Producer identity is compared before any reply is read: nothing behind it is evaluated.
    behind_identity = REPLY_DEPENDENT + ('execution.admitted_reply',)
    add('identity_envelope_build', lambda s: envelope_of(s)['build'].update(contract=RELEASE),
        ['identity.envelope_build'], unevaluated=behind_identity, recapture=False)
    add('identity_client_transport',
        lambda s: envelope_of(s)['data']['runner_client']['transport'].update(contract=RELEASE),
        ['identity.client_transport'], unevaluated=behind_identity, recapture=False)
    add('identity_reply_producer', lambda s: reply_of(s)['producer'].update(contract=RELEASE),
        ['identity.reply_producer'], unevaluated=behind_identity)

    add('echo_specimen_id', lambda s: reply_of(s).update(specimen_id='another'), ['echo.specimen_id'])
    add('echo_extra_step', lambda s: reply_of(s)['steps'].append(dict(copy.deepcopy(step_of(s)), step_id='extra')),
        ['echo.step_ids'])
    add('echo_missing_step', lambda s: reply_of(s).update(steps=[]), ['echo.step_ids'],
        unevaluated=('echo.queries', 'echo.attempts', 'native.prediction', 'native.order', 'native.attempt'))
    add('echo_renamed_step', lambda s: step_of(s).update(step_id='renamed'), ['echo.step_ids'],
        unevaluated=('echo.queries', 'echo.attempts', 'native.prediction', 'native.order', 'native.attempt'))
    add('echo_query_operation', lambda s: step_of(s)['sandbox_check'].update(operation='file-read-metadata'),
        ['echo.queries'])
    add('echo_query_filter_kind', lambda s: step_of(s)['sandbox_check'].update(filter_kind='literal'), ['echo.queries'])
    add('echo_query_filter_value', lambda s: step_of(s)['sandbox_check'].update(filter_value='/constructed/other'),
        ['echo.queries'])
    add('echo_attempt_kind', lambda s: step_of(s)['attempt'].update(requested_kind='exec'), ['echo.attempts'])
    add('echo_attempt_action', lambda s: step_of(s)['attempt'].update(requested_action='access'), ['echo.attempts'])
    add('echo_attempt_target', lambda s: step_of(s)['attempt'].update(requested_path='/constructed/other'),
        ['echo.attempts'])

    add('reported_exit_differs', lambda s: s['run'].update(exit=3), ['reported.exit_code'])
    add('reported_exit_boolean', lambda s: envelope_of(s)['result'].update(exit_code=False),
        ['reported.exit_code'], recapture=False)

    # The consumer's own diagnostic, required exactly: a fault only that reader detects.
    add('readers_consumer_propagation', lambda s: envelope_of(s)['data'].update(unlisted_member=True),
        ['consumer_validation'], recapture=False, exactly_consumer=True)
    add('readers_integrity_invalid',
        lambda s: envelope_of(s)['data']['runner_sandbox_diagnostics'].update(disposition_integrity='invalid'),
        ['readers.disposition_integrity'], recapture=False)
    add('readers_integrity_null',
        lambda s: envelope_of(s)['data']['runner_sandbox_diagnostics'].update(disposition_integrity=None),
        ['readers.disposition_integrity'], recapture=False)
    add('readers_issue_present',
        lambda s: envelope_of(s)['data']['runner_sandbox_diagnostics'].update(
            disposition_issues=[{'kind': 'constructed', 'detail': 'constructed issue'}]),
        ['readers.disposition_issues'], recapture=False)

    consistency_holds = tuple(ident for ident, group, classification, _ in checker.ASSERTIONS
                              if classification == CONSISTENCY)
    add('native_validator_spawn_failed', spawn_failed, ['native.completion', 'native.prediction'],
        unevaluated=('native.order',), holds=consistency_holds + ('native.attempt', 'native.targets_unchanged'),
        clean=True)
    # A nonzero exit alone is not a consistency fault; a reported exit that differs from the observed one is.
    add('native_validator_spawn_failed_exit_0', lambda s: (spawn_failed(s), s['run'].update(exit=0)),
        ['reported.exit_code'], ['native.completion', 'native.prediction'], unevaluated=('native.order',), clean=True)
    add('native_prediction_deny', lambda s: step_of(s)['sandbox_check'].update(outcome='deny', native_rc=1, rc=1),
        ['native.prediction'], unevaluated=('native.order',))
    add('native_prediction_source', lambda s: step_of(s)['sandbox_check'].update(result_source='synthetic'),
        ['native.prediction'], unevaluated=('native.order',))
    add('native_prediction_rc_boolean', lambda s: step_of(s)['sandbox_check'].update(native_rc=False),
        ['native.prediction'], unevaluated=('native.order',))
    add('native_order_unestablished', lambda s: step_of(s)['comparison'].update(order='unestablished'), ['native.order'])
    add('native_attempt_failed', lambda s: step_of(s)['attempt'].update(outcome='open_failed', rc=-1, errno=13),
        ['native.attempt'])
    add('native_attempt_rc', lambda s: step_of(s)['attempt'].update(rc=1), ['native.attempt'])

    def after(state):
        return state['targets-after']['targets'][0]
    changed = b'changed target bytes\n'
    add('native_target_bytes', lambda s: after(s).update(sha256=hashlib.sha256(changed).hexdigest(),
                                                         bytes_base64=base64.b64encode(changed).decode()),
        ['native.targets_unchanged'], holds=consistency_holds, clean=True)
    for field in checker.STAT_FIELDS:
        add('native_target_' + field, lambda s, field=field: after(s)['stat'].update({field: after(s)['stat'][field] + 1}),
            ['native.targets_unchanged'], holds=consistency_holds, clean=True)
    add('native_target_resolved', lambda s: after(s).update(resolved='/constructed/elsewhere'),
        ['native.targets_unchanged'], holds=consistency_holds, clean=True)
    add('native_target_unreadable_after', lambda s: after(s).update(readable=False, error='PermissionError: constructed'),
        ['native.targets_unchanged'], holds=consistency_holds, clean=True)
    add('native_target_not_observed_after', lambda s: s.update({'targets-after': None}),
        ['native.targets_unchanged'], holds=consistency_holds, clean=True)

    native = tuple(ident for ident, _, classification, _ in checker.ASSERTIONS if classification == NATIVE_OBSERVATION)

    def before(state):
        return state['targets-before']['targets'][0]
    add('prerequisite_unreadable', lambda s: before(s).update(readable=False, error='PermissionError: constructed'),
        ['prerequisite.targets_readable'], unevaluated=native, holds=consistency_holds, clean=True)
    add('prerequisite_not_regular', lambda s: before(s).update(regular_file=False),
        ['prerequisite.targets_readable'], unevaluated=native, holds=consistency_holds, clean=True)
    add('prerequisite_target_missing', lambda s: s['targets-before'].update(targets=[]),
        ['prerequisite.targets_readable'], unevaluated=native, holds=consistency_holds, clean=True)
    add('prerequisite_not_observed', lambda s: s.update({'targets-before': None}),
        ['prerequisite.targets_readable'], unevaluated=native, holds=consistency_holds, clean=True)
    # A failed prerequisite withholds native credit and fault alike, whatever the reply says.
    add('prerequisite_unreadable_with_failed_read',
        lambda s: (before(s).update(readable=False, error='PermissionError: constructed'),
                   step_of(s)['attempt'].update(outcome='open_failed', rc=-1, errno=13)),
        ['prerequisite.targets_readable'], unevaluated=native)

    for name, (code, path, names_identity, component) in REFUSALS.items():
        prefix = 'refusal.' + name
        every = [prefix + '.refused', prefix + '.failure'] + ([prefix + '.expected_identity'] if names_identity else []) + \
                [prefix + ('.no_delivery' if component == 'controller' else '.host_reply')]

        def refusal(state, name=name):
            return state['refusals'][name]

        def accepted(state, r=refusal):
            # An accepted run in its place: the passing run's envelope and exit status.
            r(state).update(envelope=copy.deepcopy(envelope_of(state)), exit=0)
        add('refusal_' + name + '_accepted', accepted, every[:1], every[1:])
        add('refusal_' + name + '_exit_0', lambda s, r=refusal: r(s).update(exit=0), [prefix + '.refused'])
        add('refusal_' + name + '_other_outcome',
            lambda s, r=refusal: r(s)['envelope']['result'].update(normalized_outcome='tool_error'),
            [prefix + '.refused'])
        add('refusal_' + name + '_no_envelope', lambda s, r=refusal: r(s).update(stdout=b''), [prefix + '.refused'],
            unevaluated=every[1:])
        add('refusal_' + name + '_wrong_code',
            lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].update(code='type_mismatch'),
            [prefix + '.failure'])
        add('refusal_' + name + '_wrong_path',
            lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].update(path=['policy']),
            [prefix + '.failure'])
        add('refusal_' + name + '_no_failure',
            lambda s, r=refusal: r(s)['envelope']['data'].update(request_failure=None),
            [prefix + '.failure'], [prefix + '.expected_identity'] if names_identity else [])
        if names_identity:
            add('refusal_' + name + '_identity_missing',
                lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].pop('expected_contract'),
                [prefix + '.expected_identity'])
            add('refusal_' + name + '_identity_wrong',
                lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].update(expected_contract=RELEASE),
                [prefix + '.expected_identity'])
        if component == 'controller':
            add('refusal_' + name + '_client_capture',
                lambda s, r=refusal: r(s)['envelope']['data'].update(
                    runner_client=copy.deepcopy(envelope_of(s)['data']['runner_client'])),
                [prefix + '.no_delivery'])
            add('refusal_' + name + '_runner_reply',
                lambda s, r=refusal: r(s)['envelope']['data'].update(runner_result=copy.deepcopy(reply_of(s))),
                [prefix + '.no_delivery'])
        else:
            add('refusal_' + name + '_step_results',
                lambda s, r=refusal: r(s)['envelope']['data']['runner_result'].update(
                    steps=[copy.deepcopy(step_of(s))]),
                [prefix + '.host_reply'])
            add('refusal_' + name + '_reply_finished',
                lambda s, r=refusal: r(s)['envelope']['data']['runner_result'].update(normalized_outcome='finished'),
                [prefix + '.host_reply'])
            add('refusal_' + name + '_controller_refused',
                lambda s, r=refusal: r(s)['envelope']['data'].update(runner_client=None, runner_result=None),
                [prefix + '.host_reply'])
        add('refusal_' + name + '_input_unchanged', lambda s, r=refusal: r(s).update(input=s['example-1']['stdout']),
            [prefix + '.one_change'])
        add('refusal_' + name + '_input_second_change',
            lambda s, r=refusal: r(s).update(input=r(s)['input'].replace(b'"specimen_id"', b'"specimen_ID"')),
            [prefix + '.one_change'])
        add('refusal_' + name + '_input_absent', lambda s, r=refusal: r(s).update(input=None), [prefix + '.one_change'])

    # No admitted reply: only execution is unavailable. Nothing behind the reply is credited or faulted.
    without_reply = REPLY_DEPENDENT + ('passage.delivery_length', 'identity.client_transport', 'identity.reply_producer')
    controller_side = ('identity.envelope_build', 'reported.exit_code', 'admission.no_request_failure',
                       'admission.dossier_policy_digest', 'consumer_validation', 'prerequisite.targets_readable')
    add('execution_tool_error', no_reply, ['execution.admitted_reply'], unevaluated=without_reply,
        holds=controller_side, clean=True)
    add('execution_no_assessment', lambda s: envelope_of(s)['data'].update(runner_sandbox_diagnostics=None),
        ['execution.admitted_reply'], unevaluated=REPLY_DEPENDENT, recapture=False)
    add('execution_capture_without_reply',
        lambda s: (envelope_of(s)['data'].update(runner_result=None, runner_sandbox_diagnostics=None),
                   envelope_of(s)['result'].update(normalized_outcome='xpc_error', ok=False, exit_code=1),
                   s['run'].update(exit=1)),
        ['execution.admitted_reply'], unevaluated=REPLY_DEPENDENT + ('identity.reply_producer',), recapture=False)
    every_run = tuple(ident for ident, group, _, _ in checker.ASSERTIONS
                      if group in ('admission', 'identity', 'echo', 'reported', 'readers')
                      or ident.startswith('native.') or ident == 'passage.delivery_length')
    add('execution_no_envelope', lambda s: s['run'].update(stdout=b'', exit=2), ['execution.admitted_reply'],
        unevaluated=every_run)
    add('execution_stdout_not_an_object', lambda s: s['run'].update(stdout=b'"text"\n'), ['execution.admitted_reply'],
        unevaluated=every_run)
    add('execution_run_not_captured', lambda s: s.update({'run': None}), ['execution.admitted_reply'],
        unevaluated=every_run)
    # A missing reply beside a faulted exit report keeps both; the tool error's own controller-side faults stay visible.
    add('execution_tool_error_and_exit', lambda s: (no_reply(s), s['run'].update(exit=0)),
        ['execution.admitted_reply', 'reported.exit_code'], unevaluated=without_reply)

    # Independent faults in one input each keep their diagnostic.
    def combined(state):
        envelope_of(state)['data']['runner_client']['request_delivery'].update(bytes_written=1)
        reply_of(state).update(specimen_id='another')
        step_of(state)['attempt'].update(outcome='open_failed', rc=-1, errno=13)
        state['run']['exit'] = 3
        state['refusals']['unbound']['envelope']['data']['request_failure'].update(code='type_mismatch')
        state['refusals']['unknown_member']['envelope']['data']['runner_result'].update(steps=[{'step_id': 'x'}])
        state['targets-after']['targets'][0]['stat']['st_size'] += 1
        state['property-list']['PWContract'] = RELEASE
    add('combined_independent_faults', combined,
        ['passage.delivery_length', 'echo.specimen_id', 'native.attempt', 'reported.exit_code',
         'refusal.unbound.failure', 'refusal.unknown_member.host_reply', 'native.targets_unchanged',
         'passage.contract_matches_property_list'])
    add('combined_prerequisite_and_consistency',
        lambda s: (s['targets-before']['targets'][0].update(readable=False), reply_of(s).update(specimen_id='another')),
        ['prerequisite.targets_readable', 'echo.specimen_id'], unevaluated=native)
    return rows


def run_control(artifacts, row):
    state = build(row['identity'])
    row['change'](state)
    if row['recapture'] and state.get('run') is not None and 'envelope' in state['run']:
        recapture_host_reply(state['run']['envelope'])
    directory = artifacts / 'captures' / row['name']
    write(directory, state)
    report = checker.evaluate(checker.load(directory), authored_fixture=True)
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    actual = checker.diagnostics(report)
    statuses = {assertion['id']: assertion['status'] for assertion in report['assertions']}
    problems = []
    permitted = set() if row['exactly_consumer'] or CONSUMER in row['expected'] else {CONSUMER}
    if actual - permitted != row['expected'] - permitted or not row['expected'] <= actual:
        problems.append('diagnostics differ: missing ' + repr(sorted(row['expected'] - actual)) +
                        ', unexpected ' + repr(sorted(actual - row['expected'] - permitted)))
    for selector in row['unevaluated']:
        chosen = [ident for ident, group, _, _ in checker.ASSERTIONS if ident == selector or group == selector]
        assert chosen, selector
        problems.extend(f'{ident} is {statuses[ident]}, not unevaluated' for ident in chosen
                        if statuses[ident] != 'not_evaluated')
    problems.extend(f'{ident} is {statuses[ident]}, not holding' for ident in row['holds']
                    if statuses[ident] != 'pass' and (ident, checker.CLASSIFICATION[ident]) not in row['expected'])
    if row['clean'] and report['consumer_errors']:
        problems.append('the consumer reports ' + repr(report['consumer_errors']))
    # A diagnostic must name its assertion and classification to a reader of the report alone.
    rendered = checker.render(report)
    for ident, classification in row['expected']:
        if f'FAIL {ident} [{classification}]: ' not in rendered:
            problems.append(f'the rendered report does not name {ident} [{classification}]')
    covered = sorted(row['targets']) if not problems else []
    return {'control': row['name'], 'targets': sorted(row['targets']),
            'expected': sorted(map(list, row['expected'])), 'actual': sorted(map(list, actual)),
            'consumer_errors': report['consumer_errors'], 'matched': not problems, 'problems': problems,
            'earned_coverage': covered}


def perturbation_controls():
    """Each refusal input differs from the emitted bytes in exactly its one stated place."""
    records = []
    for identity in (DEVELOPMENT, RELEASE):
        emitted = build(identity)['example-1']['stdout']
        document = json.loads(emitted)
        inputs = checker.refusal_inputs(emitted)
        assert set(inputs) == set(REFUSALS)
        for name in ('other_development', 'other_release', 'unbound'):
            changed = json.loads(inputs[name])
            assert {k: v for k, v in changed.items() if k != 'contract'} == {k: v for k, v in document.items() if k != 'contract'}
            assert changed['contract'] != identity and len(inputs[name]) - len(emitted) == len(changed['contract']) - len(identity)
        other = json.loads(inputs['other_development'])['contract']
        assert checker.PACKAGED_IDENTITY.fullmatch(other) and other.startswith('development:')
        if identity == DEVELOPMENT:
            assert sum(a != b for a, b in zip(other, identity)) == 1 and len(other) == len(identity)
        assert json.loads(inputs['other_release'])['contract'] == 'release:v0.0.0'
        assert json.loads(inputs['unbound'])['contract'] == 'unbound'
        assert json.loads(inputs['absent_identity']) == {k: v for k, v in document.items() if k != 'contract'}
        assert inputs['truncated_document'] == emitted[:-2] + b'\n'
        try:
            json.loads(inputs['truncated_document'])
        except ValueError:
            pass
        else:
            raise AssertionError('the truncated input still parses')
        assert json.loads(inputs['unknown_member']) == dict(document, **{UNKNOWN_MEMBER: True})
        records.append({'identity': identity, 'refusal_inputs': sorted(inputs)})
    # An identity that also occurs as another value is replaced as a member, never by its bytes.
    document = json.loads(build()['example-1']['stdout'])
    document['specimen_id'] = document['contract']
    emitted = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    changed = json.loads(checker.refusal_inputs(emitted)['unbound'])
    assert changed == dict(document, contract='unbound'), changed
    return records


def main():
    artifacts = Path(sys.argv[1])
    if (artifacts / 'captures').exists():
        shutil.rmtree(artifacts / 'captures')
    results = {'baselines': [], 'controls': [], 'perturbations': perturbation_controls()}
    failures = []
    for identity in (DEVELOPMENT, RELEASE):
        directory = artifacts / 'captures' / ('baseline_' + identity.split(':')[0])
        write(directory, build(identity))
        report = checker.evaluate(checker.load(directory), authored_fixture=True)
        (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        unsettled = [row['id'] for row in report['assertions'] if row['status'] != 'pass']
        results['baselines'].append({'identity': identity, 'status': report['status'], 'not_passing': unsettled,
                                     'consumer_errors': report['consumer_errors']})
        if report['status'] != 'pass' or unsettled or report['consumer_errors']:
            failures.append(f'baseline {identity}: {checker.render(report)} {report["consumer_errors"]}')
    names = set()
    covered = {}
    for row in controls():
        assert row['name'] not in names, row['name']
        names.add(row['name'])
        assert row['targets'] and pairs(*row['targets']) <= row['expected'], row['name']
        record = run_control(artifacts, row)
        results['controls'].append(record)
        if not record['matched']:
            failures.append(f'{record["control"]}: ' + '; '.join(record['problems']))
        for ident in record['earned_coverage']:
            covered.setdefault(ident, []).append(record['control'])
    table = [ident for ident, _, _, _ in checker.ASSERTIONS]
    uncovered = [ident for ident in table if ident not in covered]
    results['coverage'] = {
        'assertions': len(table), 'covered': {ident: covered[ident] for ident in table if ident in covered},
        'uncovered': uncovered,
        'resting_on_other_evidence': [
            'Shape and record validity, ordering and the envelope-result relationship come from consumer.validate, '
            'whose rejected controls are blackbox_e2e/checker_controls; readers_consumer_propagation establishes '
            'only that a consumer error fails this case.',
            "That the app is validly signed and unchanged comes from the dispatcher's inspection and inventory, "
            'controlled in the dispatcher suite.'],
    }
    if uncovered:
        failures.append('assertions without a matched rejected control: ' + ', '.join(uncovered))
    (artifacts / 'example-round-trip-controls.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'{len(results["controls"])} controls, {len(table) - len(uncovered)} of {len(table)} assertions covered', flush=True)
    if failures:
        raise SystemExit('\n'.join(failures))


if __name__ == '__main__':
    main()
