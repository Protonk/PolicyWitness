#!/usr/bin/env python3
"""Rejected controls for every assertion of the example round-trip checker.

A constructed document stands in for the app's emission: this case tests the
checker, not the app. Its envelope is the authored ordinary run under
tests/fixtures/blackbox_e2e, whose allowed and denied file steps are read as
the workload's first and third steps, with one fresh-read step and three
target samples authored here. Everything is placed in retained capture files
exactly as the live case leaves them. No process is launched and nothing here
is a native observation.

Each rejected control introduces one logical fault and states, independently
of the checker's output, the exact set of (assertion identifier,
classification) pairs it must produce. A control earns coverage for its
target assertions only when the actual set matches. The shared consumer's
aggregate diagnostic is permitted beside any other control's set and earns
nothing there; its own propagation control requires it exactly. Coverage is
complete when every assertion in the checker's table has a matched control.

A coherent control changes every dependent field, so the shared consumer reads
the altered reply without error and only the stated assertion rejects it.
Constructed controls establish what the checker distinguishes. They do not
establish that a native producer ever makes these faults.
"""
import copy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_context
from blackbox import bind_constructed_envelope, envelope_skeleton, recapture_host_reply
import check_example_round_trip as checker
from check_example_round_trip import REFUSALS, UNKNOWN_MEMBER

# The classifications this case expects, spelled here and not read from the checker.
CONSISTENCY = 'consistency'
EXECUTION_UNAVAILABLE = 'execution_unavailable'
PREREQUISITE_UNESTABLISHED = 'prerequisite_unestablished'
NATIVE_OBSERVATION = 'native_observation'

FIXTURE = ROOT / 'tests/fixtures/blackbox_e2e/checker/current/constructed_run.json'
DEVELOPMENT = 'development:' + 'c0' * 32
RELEASE = 'release:v9.9.9'
CONSUMER = ('consumer_validation', CONSISTENCY)
# Everything that reads the run: unevaluated when the emission or its bounds fail.
RUN_GROUPS = ('admission', 'identity', 'execution', 'echo', 'reported', 'readers', 'native', 'refusals')
# The native assertions of each step, and all of them, spelled here.
STEP_NATIVE = {
    1: ('native.step1.prediction', 'native.step1.attempt'),
    2: ('native.step2.prediction', 'native.step2.attempt', 'native.step2.fresh_syscalls',
        'native.step2.fresh_identity', 'native.step2.fresh_content'),
    3: ('native.step3.prediction', 'native.step3.attempt'),
}
FRESH_CORRESPONDENCE = ('native.step2.fresh_identity', 'native.step2.fresh_content')
STEP_ATTEMPT = {number: tuple(ident for ident in STEP_NATIVE[number] if not ident.endswith('.prediction'))
                for number in STEP_NATIVE}
NATIVE = ('native.process_status', 'native.completion', 'native.order', 'native.targets_unchanged') + \
    STEP_NATIVE[1] + STEP_NATIVE[2] + STEP_NATIVE[3]
PREREQUISITES = ('prerequisite.targets_readable', 'prerequisite.distinct_identities',
                 'prerequisite.distinguishing_prefixes')
REPLY_DEPENDENT = ('admission.reply_policy_digest', 'echo.specimen_id', 'echo.step_ids', 'echo.queries',
                   'echo.attempts', 'readers.disposition_integrity', 'readers.disposition_issues') + NATIVE
# What one `read_fresh` reads at most, and the permission errnos, spelled here.
BOUND = 64
EPERM, ENOENT, EACCES = 1, 2, 13
# The three constructed targets by role. C is longer than the bound; its prefix differs from A's and B's.
CONTENT = {'A': b'constructed first target\n' * 2,
           'B': b'constructed second target\n' * 2,
           'C': bytes(range(32, 127)) + b'\n'}
IDENTITY = {'A': (16777234, 4242), 'B': (16777234, 4243), 'C': (16777234, 4244)}
ALLOW = dict(outcome='allow', native_rc=0, rc=0, errno=0, error=None)
DENY = dict(outcome='deny', native_rc=1, rc=1, errno=0, error=None)


def expected_classification(ident):
    """The classification each assertion must carry, authored independently of the checker's table."""
    if ident == 'execution.admitted_reply':
        return EXECUTION_UNAVAILABLE
    if ident.startswith('prerequisite.'):
        return PREREQUISITE_UNESTABLISHED
    if ident.startswith('native.'):
        return NATIVE_OBSERVATION
    return CONSISTENCY


def pairs(*identifiers):
    return {(ident, expected_classification(ident)) for ident in identifiers}


# ---------------------------------------------------------------------------
# The constructed passing input
# ---------------------------------------------------------------------------

def sample(role, target):
    """What the checker's observer records for one target: identity and content from one descriptor."""
    content, (device, inode) = CONTENT[role], IDENTITY[role]
    return {'target': target, 'resolved': target, 'regular_file': True, 'readable': True, 'error': None,
            'sha256': hashlib.sha256(content).hexdigest(), 'length': len(content),
            'prefix_sha256': hashlib.sha256(content[:BOUND]).hexdigest(), 'prefix_length': len(content[:BOUND]),
            'stat': {'st_dev': device, 'st_ino': inode, 'st_mode': 33188, 'st_uid': 0, 'st_gid': 0,
                     'st_size': len(content), 'st_mtime_ns': 1700000000000000000, 'st_ctime_ns': 1700000000000000000}}


def fresh_read(role, *, count=BOUND, descriptor=5):
    """A completed fresh read of one constructed target, as the worker reports it."""
    device, inode = IDENTITY[role]
    return {'open_rc': descriptor, 'stat_rc': 0, 'read_rc': len(CONTENT[role][:count]), 'close_rc': 0,
            'identity': {'device': device, 'inode': inode, 'mode': 33188, 'uid': 0, 'gid': 0},
            'content_hex': CONTENT[role][:count].hex()}


def constructed_run(identity):
    """The authored run read as the three-step workload.

    Its allowed and denied file steps become a data-read open that succeeds
    and one that fails with `EPERM`. Between them stands an authored step: an
    allowed metadata query on the denied step's target beside a fresh read of
    a third target.
    """
    envelope = bind_constructed_envelope(json.loads(FIXTURE.read_text()))
    reply = envelope['data']['runner_result']
    allowed, denied = reply['steps'][0], reply['steps'][1]
    assert (allowed['sandbox_check']['outcome'], allowed['attempt']['outcome']) == ('allow', 'ok')
    assert (denied['sandbox_check']['outcome'], denied['attempt']['outcome'], denied['attempt']['errno']) == \
        ('deny', 'open_failed', EPERM)
    phase = reply['phases'][0]
    validator = phase['validator_subprocess']
    disposition = reply['runner_subprocess']['disposition']
    records = {record['step_id']: record for record in validator['records']}
    rows = {row['step_id']: row for row in disposition['steps']}
    for step in (allowed, denied):
        step['sandbox_check']['operation'] = 'file-read-data'
        step['attempt']['requested_action'] = 'open_read'
        line = json.loads(records[step['step_id']]['raw_line'])
        assert json.dumps(line, separators=(',', ':')) == records[step['step_id']]['raw_line']
        line['operation'] = records[step['step_id']]['operation'] = 'file-read-data'
        records[step['step_id']]['raw_line'] = json.dumps(line, separators=(',', ':'))
    denied['attempt']['error'] = 'open(O_RDONLY): Operation not permitted'

    ident = 'constructed_metadata_query_fresh_read'
    queried = denied['attempt']['requested_path']
    target = queried.replace('deny-write', 'fresh-read')
    assert target not in (queried, allowed['attempt']['requested_path'])
    fresh = copy.deepcopy(allowed)
    fresh['step_id'] = ident
    fresh['sandbox_check'] = dict(copy.deepcopy(denied['sandbox_check']), operation='file-read-metadata', **ALLOW)
    fresh['attempt'].update(requested_action='read_fresh', requested_path=target, observed_path=None,
                            fresh_read=fresh_read('C'))
    fresh['attempt']['path_diagnostics']['input'] = target
    fresh['comparison'].update(operation_relation='different', target_relation='different_submitted')
    record = copy.deepcopy(records[denied['step_id']])
    line = dict(json.loads(record['raw_line']), step_id=ident, operation='file-read-metadata', rc=0, outcome='allow')
    record.update(step_id=ident, operation='file-read-metadata', rc=0, outcome='allow',
                  raw_line=json.dumps(line, separators=(',', ':')))

    reply['steps'] = [allowed, fresh, denied]
    order = [step['step_id'] for step in reply['steps']]
    phase['action_ids'] = validator['expected_step_ids'] = order
    validator['records'] = [records[order[0]], record, records[order[2]]]
    disposition['steps'] = [dict(copy.deepcopy(rows[order[0]]), index=0),
                            dict(copy.deepcopy(rows[order[0]]), index=1, step_id=ident),
                            dict(copy.deepcopy(rows[order[2]]), index=2)]
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
    document = {
        'contract': identity, 'specimen_id': reply['specimen_id'],
        'policy': {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'},
        'probe_plan': [{'step_id': step['step_id'],
                        'sandbox_check': {'operation': step['sandbox_check']['operation'],
                                          'filter': {'kind': step['sandbox_check']['filter_kind'],
                                                     'value': step['sandbox_check']['filter_value']}},
                        'attempt': {'kind': 'file', 'action': step['attempt']['requested_action'],
                                    'target': step['attempt']['requested_path']}}
                       for step in reply['steps']],
    }
    emitted = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()
    digest = hashlib.sha256(document['policy']['sbpl_source'].encode()).hexdigest()
    reply['policy_sha256'] = digest
    run['data']['specimen']['policy']['augmentation'].update(original_sha256=digest, applied_sha256=digest)
    run['data']['runner_client']['request_delivery']['bytes_written'] = len(emitted) - 1
    recapture_host_reply(run)
    # The order in which the checker's observer meets the paths: A, then B as step 2's query, then C.
    paths = (reply['steps'][0]['attempt']['requested_path'], reply['steps'][1]['sandbox_check']['filter_value'],
             reply['steps'][1]['attempt']['requested_path'])
    observed = {'targets': [sample(role, path) for role, path in zip('ABC', paths)]}
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


def step_of(state, number=1):
    return reply_of(state)['steps'][number - 1]


def validator_record(state, number):
    return reply_of(state)['phases'][0]['validator_subprocess']['records'][number - 1]


def before(state, role):
    return state['targets-before']['targets']['ABC'.index(role)]


def after(state, role):
    return state['targets-after']['targets']['ABC'.index(role)]


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


def answer_of(state, number):
    return {key: step_of(state, number)['sandbox_check'][key] for key in ALLOW}


def set_answer(state, number, answer):
    """Give one step a validator answer, in its step record and in the validator's own record and line."""
    step_of(state, number)['sandbox_check'].update(answer)
    record = validator_record(state, number)
    line = json.loads(record['raw_line'])
    line.update(rc=answer['native_rc'], errno=answer['errno'], outcome=answer['outcome'], error=answer['error'])
    record.update(rc=answer['native_rc'], errno=answer['errno'], outcome=answer['outcome'],
                  raw_line=json.dumps(line, separators=(',', ':')))


def exchange_answers(state, first, second):
    """Two steps trade validator answers. Each query still echoes its own submitted operation and path."""
    one, other = answer_of(state, first), answer_of(state, second)
    set_answer(state, first, other)
    set_answer(state, second, one)


def set_open(state, number, errno=None):
    """An open that succeeds, or fails with one errno, with the comparison that observation supports."""
    step = step_of(state, number)
    attempt = step['attempt']
    if errno is None:
        attempt.update(outcome='ok', rc=0, errno=None, observed_path=attempt['requested_path'])
        attempt.pop('error', None)
        step['comparison'].update(observation='succeeded', observation_basis='completed_worker_status')
        return
    attempt.update(outcome='open_failed', rc=1, errno=errno, observed_path=None,
                   error='open(O_RDONLY): ' + os.strerror(errno))
    permission = errno in (EPERM, EACCES)
    step['comparison'].update(observation='permission_failure' if permission else 'other_failure',
                              observation_basis='permission_errno' if permission else 'completed_worker_status')


def set_fresh(state, **members):
    step_of(state, 2)['attempt']['fresh_read'].update(members)


def fresh_fails(state, call, errno=EPERM):
    """The fresh read fails at one call; later calls supply nothing and the attempt carries the first failure."""
    step = step_of(state, 2)
    read = step['attempt']['fresh_read']
    if call == 'open':
        step['attempt']['fresh_read'] = {'open_rc': -1, 'open_errno': errno}
    else:
        read.update({call + '_rc': -1, call + '_errno': errno})
        if call == 'stat':
            read.pop('identity')
        if call == 'read':
            read.pop('content_hex')
    step['attempt'].update(outcome='read_failed', rc=-1, errno=errno)
    step['comparison'].update(observation='permission_failure', observation_basis='permission_errno')


def coherent_unestablished(state):
    """The validator answered, and the chain that would order it first lacks an established worker lifetime."""
    reply_of(state)['phases'][0]['ordering'].update(worker_lifetime_established=False)
    for step in reply_of(state)['steps']:
        step['comparison']['order'] = 'unestablished'


def exchange_records(state, member, first, second):
    """Two steps trade whole query or attempt records and keep their identifiers."""
    one, other = step_of(state, first), step_of(state, second)
    one[member], other[member] = other[member], one[member]


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
    `rest_holds` requires every assertion outside the expected and unevaluated
    sets to hold, so the control states the whole report.
    """
    rows = []

    def add(name, change, targets, also=(), *, identity=DEVELOPMENT, unevaluated=(), holds=(), clean=False,
            recapture=True, exactly_consumer=False, rest_holds=False):
        expected = pairs(*targets, *also)
        rows.append(dict(name=name, identity=identity, change=change, targets=tuple(targets), expected=expected,
                         unevaluated=tuple(unevaluated), holds=tuple(holds), clean=clean, recapture=recapture,
                         exactly_consumer=exactly_consumer, rest_holds=rest_holds))

    def coherent(name, change, targets, also=(), *, unevaluated=()):
        """The consumer reads the altered reply cleanly, and the stated sets are the whole report."""
        add(name, change, targets, also, unevaluated=unevaluated, clean=True, rest_holds=True)

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
            unevaluated=RUN_GROUPS + PREREQUISITES + ('passage.delivery_length',))

    def plan(document, number):
        return document['probe_plan'][number - 1]

    def retarget(step, path, *, query=True, attempt=True):
        if query:
            step['sandbox_check']['filter']['value'] = path
        if attempt:
            step['attempt']['target'] = path

    def target(document, role):
        return {'A': plan(document, 1)['attempt']['target'], 'B': plan(document, 3)['attempt']['target'],
                'C': plan(document, 2)['attempt']['target']}[role]

    read_step = {'step_id': 'fourth', 'sandbox_check': {'operation': 'file-read-data',
                                                         'filter': {'kind': 'path', 'value': '/constructed/fourth'}}}
    roles = ['bounds.workload_roles']
    bounds('empty_plan', lambda d: d.update(probe_plan=[]), ['bounds.ordinary_form'], roles)
    bounds('plan_not_an_array', lambda d: d.update(probe_plan={'step_id': 'x'}), ['bounds.ordinary_form'], roles)
    bounds('write_action', lambda d: d['probe_plan'].append(dict(
        read_step, attempt={'kind': 'file', 'action': 'open_write', 'target': '/constructed/fourth'})),
        ['bounds.read_only_attempts'], roles)
    bounds('unlink_action', lambda d: d['probe_plan'].append(dict(
        read_step, attempt={'kind': 'file', 'action': 'unlink', 'target': '/constructed/fourth'})),
        ['bounds.read_only_attempts'], roles)
    bounds('exec_action', lambda d: d['probe_plan'].append(dict(
        read_step, attempt={'kind': 'exec', 'action': 'spawn', 'target': '/usr/bin/true'})),
        ['bounds.read_only_attempts'], roles)
    for number in (1, 2, 3):
        bounds(f'step{number}_write_action', lambda d, number=number: plan(d, number)['attempt'].update(action='create'),
               ['bounds.read_only_attempts'], roles)
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
           ['bounds.ordinary_form'], roles)
    bounds('actors', lambda d: d.update(actors=[{'actor_id': 'a'}]), ['bounds.ordinary_form'])

    # Another workload: every attempt is still read-only, and only the roles refuse it.
    def role(name, change):
        bounds('roles_' + name, change, roles)
    role('step3_collapsed_onto_step1_target', lambda d: retarget(plan(d, 3), target(d, 'A')))
    role('step3_collapsed_onto_fresh_read_target', lambda d: retarget(plan(d, 3), target(d, 'C')))
    role('step3_opens_another_target_than_it_queries', lambda d: retarget(plan(d, 3), target(d, 'A'), query=False))
    role('step3_queries_another_target_than_it_opens', lambda d: retarget(plan(d, 3), target(d, 'A'), attempt=False))
    role('step3_metadata_query', lambda d: plan(d, 3)['sandbox_check'].update(operation='file-read-metadata'))
    role('step3_access', lambda d: plan(d, 3)['attempt'].update(action='access'))
    role('step1_collapsed_onto_queried_target', lambda d: retarget(plan(d, 1), target(d, 'B')))
    role('step1_collapsed_onto_fresh_read_target', lambda d: retarget(plan(d, 1), target(d, 'C')))
    role('step1_access', lambda d: plan(d, 1)['attempt'].update(action='access'))
    role('step1_unpaired', lambda d: plan(d, 1).pop('sandbox_check'))
    role('step1_filter_not_a_path', lambda d: plan(d, 1)['sandbox_check']['filter'].update(kind='literal'))
    role('step2_fresh_read_of_queried_target', lambda d: retarget(plan(d, 2), target(d, 'B'), query=False))
    role('step2_fresh_read_of_step1_target', lambda d: retarget(plan(d, 2), target(d, 'A'), query=False))
    role('step2_queries_step1_target', lambda d: retarget(plan(d, 2), target(d, 'A'), attempt=False))
    role('step2_data_query', lambda d: plan(d, 2)['sandbox_check'].update(operation='file-read-data'))
    role('step2_open_read', lambda d: plan(d, 2)['attempt'].update(action='open_read'))
    role('missing_fresh_read_step', lambda d: d['probe_plan'].pop(1))
    role('missing_second_open_step', lambda d: d['probe_plan'].pop(2))
    role('missing_first_open_step', lambda d: d['probe_plan'].pop(0))
    role('one_step', lambda d: d.update(probe_plan=d['probe_plan'][:1]))
    role('duplicated_step_appended', lambda d: d['probe_plan'].append(dict(copy.deepcopy(plan(d, 1)), step_id='again')))
    role('step3_duplicates_step1', lambda d: d['probe_plan'].__setitem__(2, dict(copy.deepcopy(plan(d, 1)), step_id='again')))
    role('duplicate_step_identifier', lambda d: plan(d, 3).update(step_id=plan(d, 1)['step_id']))
    role('reordered_fresh_read_last', lambda d: d['probe_plan'].append(d['probe_plan'].pop(1)))
    role('reordered_fresh_read_first', lambda d: d['probe_plan'].insert(0, d['probe_plan'].pop(1)))
    role('reordered_opens_exchanged', lambda d: d['probe_plan'].reverse())

    add('admission_request_failure',
        lambda s: envelope_of(s)['data'].update(request_failure={'code': 'unknown_field', 'path': ['x']}),
        ['admission.no_request_failure'], recapture=False)
    add('admission_bad_request_result',
        lambda s: (envelope_of(s)['result'].update(normalized_outcome='bad_request', ok=False, exit_code=1),
                   s['run'].update(exit=1)),
        ['admission.no_request_failure'], ['native.process_status'], recapture=False)

    every_step = STEP_NATIVE[1] + STEP_NATIVE[2] + STEP_NATIVE[3]

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
        ['echo.step_ids', 'native.completion', 'native.process_status'],
        unevaluated=('echo.queries', 'echo.attempts', 'native.order') + every_step)
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

    # Association. Reply steps are found by identifier, order is its own assertion, and a native
    # expectation is read only from the one record that carries a step's identifier and echoes
    # what that step submitted.
    add('echo_specimen_id', lambda s: reply_of(s).update(specimen_id='another'), ['echo.specimen_id'], rest_holds=True)
    add('echo_extra_step', lambda s: reply_of(s)['steps'].append(dict(copy.deepcopy(step_of(s)), step_id='extra')),
        ['echo.step_ids'], rest_holds=True)
    add('echo_no_steps', lambda s: reply_of(s).update(steps=[]), ['echo.step_ids'],
        unevaluated=('echo.queries', 'echo.attempts', 'native.order') + every_step, rest_holds=True)
    add('echo_reversed_records', lambda s: reply_of(s)['steps'].reverse(), ['echo.step_ids'], rest_holds=True)
    add('echo_rotated_records', lambda s: reply_of(s)['steps'].append(reply_of(s)['steps'].pop(0)),
        ['echo.step_ids'], rest_holds=True)
    for number in (1, 2, 3):
        add(f'echo_step{number}_record_dropped', lambda s, number=number: reply_of(s)['steps'].pop(number - 1),
            ['echo.step_ids'], unevaluated=STEP_NATIVE[number], rest_holds=True)
        add(f'echo_step{number}_record_renamed', lambda s, number=number: step_of(s, number).update(step_id='renamed'),
            ['echo.step_ids'], unevaluated=STEP_NATIVE[number], rest_holds=True)
        add(f'echo_step{number}_record_duplicated',
            lambda s, number=number: reply_of(s)['steps'].append(copy.deepcopy(step_of(s, number))),
            ['echo.step_ids'], unevaluated=STEP_NATIVE[number], rest_holds=True)
        add(f'echo_step{number}_query_operation',
            lambda s, number=number: step_of(s, number)['sandbox_check'].update(operation='file-read-xattr'),
            ['echo.queries'], unevaluated=(f'native.step{number}.prediction',), rest_holds=True)
        add(f'echo_step{number}_query_filter_kind',
            lambda s, number=number: step_of(s, number)['sandbox_check'].update(filter_kind='literal'),
            ['echo.queries'], unevaluated=(f'native.step{number}.prediction',), rest_holds=True)
        add(f'echo_step{number}_query_filter_value',
            lambda s, number=number: step_of(s, number)['sandbox_check'].update(filter_value='/constructed/other'),
            ['echo.queries'], unevaluated=(f'native.step{number}.prediction',), rest_holds=True)
        add(f'echo_step{number}_attempt_kind',
            lambda s, number=number: step_of(s, number)['attempt'].update(requested_kind='exec'),
            ['echo.attempts'], unevaluated=STEP_ATTEMPT[number], rest_holds=True)
        add(f'echo_step{number}_attempt_action',
            lambda s, number=number: step_of(s, number)['attempt'].update(requested_action='access'),
            ['echo.attempts'], unevaluated=STEP_ATTEMPT[number], rest_holds=True)
        add(f'echo_step{number}_attempt_target',
            lambda s, number=number: step_of(s, number)['attempt'].update(requested_path='/constructed/other'),
            ['echo.attempts'], unevaluated=STEP_ATTEMPT[number], rest_holds=True)

    # A duplicate that would pass in the original's place: neither record is chosen.
    def passing_duplicate_first(state):
        duplicate = copy.deepcopy(step_of(state, 3))
        duplicate['sandbox_check'].update(ALLOW)
        reply_of(state)['steps'].insert(0, duplicate)
    add('echo_step3_conflicting_duplicate_first', passing_duplicate_first, ['echo.step_ids'],
        unevaluated=STEP_NATIVE[3], rest_holds=True)
    # Whole records exchanged under unchanged identifiers: the echoes name the wrong association,
    # and no answer or attempt is read from a record that does not echo its step.
    for first, second in ((1, 2), (1, 3), (2, 3)):
        add(f'echo_query_records_exchanged_{first}_{second}',
            lambda s, first=first, second=second: exchange_records(s, 'sandbox_check', first, second),
            ['echo.queries'], unevaluated=(f'native.step{first}.prediction', f'native.step{second}.prediction'),
            rest_holds=True)
        add(f'echo_attempt_records_exchanged_{first}_{second}',
            lambda s, first=first, second=second: exchange_records(s, 'attempt', first, second),
            ['echo.attempts'], unevaluated=STEP_ATTEMPT[first] + STEP_ATTEMPT[second], rest_holds=True)

    # The observed process status and the envelope's report of it are read apart.
    add('status_observed_3_reported_0', lambda s: s['run'].update(exit=3),
        ['native.process_status', 'reported.exit_code'], rest_holds=True)
    add('status_observed_0_reported_1', lambda s: envelope_of(s)['result'].update(exit_code=1),
        ['reported.exit_code'], holds=('native.process_status',), recapture=False)
    add('status_observed_1_reported_1', lambda s: (envelope_of(s)['result'].update(exit_code=1), s['run'].update(exit=1)),
        ['native.process_status'], holds=('reported.exit_code',), recapture=False)
    add('status_reported_boolean', lambda s: envelope_of(s)['result'].update(exit_code=False),
        ['reported.exit_code'], holds=('native.process_status',), recapture=False)
    add('status_not_captured_as_integer', lambda s: s['run'].update(exit='0x0'),
        ['execution.admitted_reply'], unevaluated=REPLY_DEPENDENT)

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

    predictions = tuple(f'native.step{number}.prediction' for number in (1, 2, 3))
    coherent('native_validator_spawn_failed', spawn_failed,
             ['native.completion', 'native.process_status', *predictions], unevaluated=('native.order',))
    # A nonzero exit alone is not a consistency fault; a reported exit that differs from the observed one is.
    add('native_validator_spawn_failed_exit_0', lambda s: (spawn_failed(s), s['run'].update(exit=0)),
        ['reported.exit_code'], ['native.completion', *predictions], unevaluated=('native.order',), clean=True,
        rest_holds=True)

    # One step's answer or attempt changed coherently: the consumer reads the reply cleanly and
    # exactly that step's own assertion rejects it. The step-3 pair shows the answer and the
    # attempt are read apart: neither passes because the other is as expected, and neither
    # fails because the two no longer look alike.
    coherent('native_step1_deny_answer', lambda s: set_answer(s, 1, DENY), ['native.step1.prediction'])
    coherent('native_step2_deny_answer', lambda s: set_answer(s, 2, DENY), ['native.step2.prediction'])
    coherent('native_step3_allow_answer_with_eperm', lambda s: set_answer(s, 3, ALLOW), ['native.step3.prediction'])
    coherent('native_step3_deny_answer_with_successful_open', lambda s: set_open(s, 3), ['native.step3.attempt'])
    coherent('native_step3_allow_answer_with_successful_open', lambda s: (set_answer(s, 3, ALLOW), set_open(s, 3)),
             ['native.step3.prediction', 'native.step3.attempt'])
    coherent('native_step3_eacces', lambda s: set_open(s, 3, EACCES), ['native.step3.attempt'])
    coherent('native_step3_enoent', lambda s: set_open(s, 3, ENOENT), ['native.step3.attempt'])
    coherent('native_step1_eperm', lambda s: set_open(s, 1, EPERM), ['native.step1.attempt'])
    # The same answers attached to other queries, every echo still its own step's.
    coherent('native_answers_exchanged_2_3', lambda s: exchange_answers(s, 2, 3),
             ['native.step2.prediction', 'native.step3.prediction'])
    coherent('native_answers_exchanged_1_3', lambda s: exchange_answers(s, 1, 3),
             ['native.step1.prediction', 'native.step3.prediction'])
    coherent('native_order_unestablished', coherent_unestablished, ['native.order'])
    # Step 3's answer is not a deny the validator returned with errno 0.
    add('native_step3_deny_with_query_errno',
        lambda s: set_answer(s, 3, dict(DENY, errno=EACCES)), ['native.step3.prediction'], rest_holds=True)
    add('native_step3_error_answer',
        lambda s: set_answer(s, 3, dict(outcome='error', native_rc=-1, rc=-1, errno=22, error='constructed query error')),
        ['native.step3.prediction'], rest_holds=True)
    add('native_step3_deny_with_native_rc_0', lambda s: step_of(s, 3)['sandbox_check'].update(native_rc=0),
        ['native.step3.prediction'], rest_holds=True)
    add('native_step3_attempt_errno_boolean', lambda s: step_of(s, 3)['attempt'].update(errno=True),
        ['native.step3.attempt'], rest_holds=True)
    add('native_step3_attempt_not_from_worker', lambda s: step_of(s, 3)['attempt'].update(result_source='synthetic'),
        ['native.step3.attempt'], rest_holds=True)
    # Incoherent replies: the checker still names its own assertion beside the consumer's diagnostic.
    for number in (1, 2, 3):
        add(f'native_step{number}_prediction_source',
            lambda s, number=number: step_of(s, number)['sandbox_check'].update(result_source='synthetic'),
            [f'native.step{number}.prediction'], rest_holds=True)
        add(f'native_step{number}_prediction_rc_boolean',
            lambda s, number=number: step_of(s, number)['sandbox_check'].update(native_rc=False),
            [f'native.step{number}.prediction'], rest_holds=True)
        add(f'native_step{number}_order_unestablished',
            lambda s, number=number: step_of(s, number)['comparison'].update(order='unestablished'),
            ['native.order'], rest_holds=True)
    for number in (1, 2):
        add(f'native_step{number}_attempt_rc', lambda s, number=number: step_of(s, number)['attempt'].update(rc=1),
            [f'native.step{number}.attempt'], rest_holds=True)
        add(f'native_step{number}_attempt_not_from_worker',
            lambda s, number=number: step_of(s, number)['attempt'].update(result_source='synthetic'),
            [f'native.step{number}.attempt'], rest_holds=True)

    # The fresh read. Its identity and its content each have their own assertion against what
    # the checker observed for C, and a record that reads cleanly is not thereby a read of C.
    def fresh_of(state, role, *, identity=True, content=True, count=BOUND):
        other = fresh_read(role, count=count)
        members = ({'identity': other['identity']} if identity else {}) | \
            ({'content_hex': other['content_hex'], 'read_rc': other['read_rc']} if content else {})
        set_fresh(state, **members)
    for other in ('A', 'B'):
        coherent(f'fresh_identity_and_content_of_{other}', lambda s, other=other: fresh_of(s, other),
                 ['native.step2.fresh_identity', 'native.step2.fresh_content'])
        coherent(f'fresh_identity_of_{other}', lambda s, other=other: fresh_of(s, other, content=False),
                 ['native.step2.fresh_identity'])
        coherent(f'fresh_content_of_{other}', lambda s, other=other: fresh_of(s, other, identity=False),
                 ['native.step2.fresh_content'])
    coherent('fresh_device_alone', lambda s: step_of(s, 2)['attempt']['fresh_read']['identity'].update(device=1),
             ['native.step2.fresh_identity'])
    coherent('fresh_inode_alone', lambda s: step_of(s, 2)['attempt']['fresh_read']['identity'].update(inode=1),
             ['native.step2.fresh_identity'])
    coherent('fresh_count_alone_short', lambda s: fresh_of(s, 'C', identity=False, count=BOUND - 1),
             ['native.step2.fresh_content'])
    coherent('fresh_count_zero', lambda s: fresh_of(s, 'C', identity=False, count=0), ['native.step2.fresh_content'])
    coherent('fresh_one_byte_differs',
             lambda s: set_fresh(s, content_hex='00' + step_of(s, 2)['attempt']['fresh_read']['content_hex'][2:]),
             ['native.step2.fresh_content'])
    add('fresh_count_alone_without_bytes', lambda s: set_fresh(s, read_rc=BOUND - 1),
        ['native.step2.fresh_content'], rest_holds=True)
    add('fresh_content_not_hex', lambda s: set_fresh(s, content_hex='zz' * BOUND),
        ['native.step2.fresh_content'], rest_holds=True)
    add('fresh_count_beyond_the_bound', lambda s: set_fresh(s, read_rc=BOUND + 1, content_hex=CONTENT['C'][:BOUND + 1].hex()),
        ['native.step2.fresh_syscalls', 'native.step2.fresh_content'], rest_holds=True)
    add('fresh_record_absent', lambda s: step_of(s, 2)['attempt'].pop('fresh_read'),
        ['native.step2.fresh_syscalls'], unevaluated=FRESH_CORRESPONDENCE, rest_holds=True)
    # A failed call supplies no later observation: the claim that needs it is withheld, not failed.
    coherent('fresh_open_fails', lambda s: fresh_fails(s, 'open'),
             ['native.step2.attempt', 'native.step2.fresh_syscalls'], unevaluated=FRESH_CORRESPONDENCE)
    coherent('fresh_stat_fails', lambda s: fresh_fails(s, 'stat'),
             ['native.step2.attempt', 'native.step2.fresh_syscalls'], unevaluated=('native.step2.fresh_identity',))
    coherent('fresh_read_fails', lambda s: fresh_fails(s, 'read'),
             ['native.step2.attempt', 'native.step2.fresh_syscalls'], unevaluated=('native.step2.fresh_content',))
    coherent('fresh_close_fails', lambda s: fresh_fails(s, 'close'),
             ['native.step2.attempt', 'native.step2.fresh_syscalls'])

    # The checker's two samples of each target. A changed sample of C also withholds the
    # correspondence that needs one stable observation of C.
    changed = hashlib.sha256(b'changed target bytes\n').hexdigest()
    for role_name in 'ABC':
        withheld = FRESH_CORRESPONDENCE if role_name == 'C' else ()

        def target_control(name, change, role_name=role_name, withheld=withheld):
            coherent(f'target_{role_name}_{name}', lambda s: change(s, after(s, role_name), before(s, role_name)),
                     ['native.targets_unchanged'], unevaluated=withheld)
        target_control('digest', lambda s, later, earlier: later.update(sha256=changed))
        target_control('length', lambda s, later, earlier: later.update(length=later['length'] + 1))
        target_control('prefix_digest', lambda s, later, earlier: later.update(prefix_sha256=changed))
        target_control('prefix_length', lambda s, later, earlier: later.update(prefix_length=later['prefix_length'] - 1))
        target_control('digest_absent', lambda s, later, earlier: (earlier.pop('sha256'), later.pop('sha256')))
        for field in checker.STAT_FIELDS:
            target_control(field, lambda s, later, earlier, field=field: later['stat'].update({field: later['stat'][field] + 1}))
        target_control('resolved', lambda s, later, earlier: later.update(resolved='/constructed/elsewhere'))
        target_control('unreadable_after',
                       lambda s, later, earlier: later.update(readable=False, error='PermissionError: constructed'))
        target_control('not_sampled_after',
                       lambda s, later, earlier: s['targets-after']['targets'].remove(later))
    coherent('targets_not_observed_after', lambda s: s.update({'targets-after': None}),
             ['native.targets_unchanged'], unevaluated=FRESH_CORRESPONDENCE)

    # A missing prerequisite withholds native credit and fault alike. B is only ever queried and
    # opened without success, so the reply alone would never show that this user cannot read it.
    other_prerequisites = PREREQUISITES[1:]
    for role_name in 'ABC':
        coherent(f'prerequisite_{role_name}_unreadable',
                 lambda s, role_name=role_name: before(s, role_name).update(readable=False, error='PermissionError: constructed'),
                 ['prerequisite.targets_readable'], unevaluated=NATIVE + other_prerequisites)
        coherent(f'prerequisite_{role_name}_not_regular',
                 lambda s, role_name=role_name: before(s, role_name).update(regular_file=False),
                 ['prerequisite.targets_readable'], unevaluated=NATIVE + other_prerequisites)
        coherent(f'prerequisite_{role_name}_not_sampled',
                 lambda s, role_name=role_name: s['targets-before']['targets'].remove(before(s, role_name)),
                 ['prerequisite.targets_readable'], unevaluated=NATIVE + other_prerequisites)
    coherent('prerequisite_not_observed', lambda s: s.update({'targets-before': None}),
             ['prerequisite.targets_readable'], unevaluated=NATIVE + other_prerequisites)

    def same_file(state, one, other):
        for sampled in (before, after):
            sampled(state, one)['stat'].update(st_dev=sampled(state, other)['stat']['st_dev'],
                                               st_ino=sampled(state, other)['stat']['st_ino'])

    def same_prefix(state, one, other):
        for sampled in (before, after):
            sampled(state, one).update(prefix_sha256=sampled(state, other)['prefix_sha256'],
                                       prefix_length=sampled(state, other)['prefix_length'])
    for one, other in (('A', 'B'), ('C', 'A'), ('C', 'B')):
        coherent(f'prerequisite_{one}_and_{other}_one_file', lambda s, one=one, other=other: same_file(s, one, other),
                 ['prerequisite.distinct_identities'], unevaluated=NATIVE)
    coherent('prerequisite_identity_not_observed',
             lambda s: [sampled(s, 'B')['stat'].pop('st_ino') for sampled in (before, after)],
             ['prerequisite.distinct_identities'], unevaluated=NATIVE)
    for other in ('A', 'B'):
        coherent(f'prerequisite_C_prefix_equals_{other}', lambda s, other=other: same_prefix(s, 'C', other),
                 ['prerequisite.distinguishing_prefixes'], unevaluated=NATIVE)
    for role_name in 'ABC':
        coherent(f'prerequisite_{role_name}_prefix_empty',
                 lambda s, role_name=role_name: [sampled(s, role_name).update(
                     prefix_length=0, prefix_sha256=hashlib.sha256(b'').hexdigest()) for sampled in (before, after)],
                 ['prerequisite.distinguishing_prefixes'], unevaluated=NATIVE)
    # Whatever the reply says, it earns nothing without the prerequisite.
    add('prerequisite_B_unreadable_with_other_native_results',
        lambda s: (before(s, 'B').update(readable=False, error='PermissionError: constructed'),
                   set_answer(s, 3, ALLOW), set_open(s, 3), s['run'].update(exit=3)),
        ['prerequisite.targets_readable'], ['reported.exit_code'], unevaluated=NATIVE + other_prerequisites,
        rest_holds=True)

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
        add('refusal_' + name + '_input_of_another_refusal',
            lambda s, r=refusal, name=name: r(s).update(
                input=s['refusals']['unbound' if name != 'unbound' else 'other_release']['input']),
            [prefix + '.one_change'])

    add('refusal_other_development_two_digits',
        lambda s: s['refusals']['other_development'].update(
            input=s['example-1']['stdout'].replace(DEVELOPMENT.encode(), b'development:' + b'c1' * 32)),
        ['refusal.other_development.one_change'])

    # No admitted reply: only execution is unavailable. Nothing behind the reply is credited or faulted,
    # and no other execution's observations stand in for it.
    without_reply = REPLY_DEPENDENT + ('passage.delivery_length', 'identity.client_transport', 'identity.reply_producer')
    controller_side = ('identity.envelope_build', 'reported.exit_code', 'admission.no_request_failure',
                       'admission.dossier_policy_digest', 'consumer_validation') + PREREQUISITES
    add('execution_tool_error', no_reply, ['execution.admitted_reply'], unevaluated=without_reply,
        holds=controller_side, clean=True)
    # The capture retains only part of the host bytes: no reply is admitted from them.
    add('execution_reply_truncated',
        lambda s: (envelope_of(s)['data']['runner_client']['transport']['runner_reply'].update(truncated=True),
                   envelope_of(s)['data'].update(runner_result=None, runner_sandbox_diagnostics=None),
                   envelope_of(s)['result'].update(normalized_outcome='runner_reply_truncated', ok=False, exit_code=1),
                   s['run'].update(exit=1)),
        ['execution.admitted_reply'], unevaluated=REPLY_DEPENDENT + ('identity.reply_producer',), recapture=False)
    # An admitted reply without the controller's assessment is a consistency fault, not missing execution.
    add('readers_assessment_absent', lambda s: envelope_of(s)['data'].update(runner_sandbox_diagnostics=None),
        ['readers.disposition_integrity', 'readers.disposition_issues'], holds=('execution.admitted_reply',),
        recapture=False)
    add('readers_assessment_absent_and_result',
        lambda s: (envelope_of(s)['data'].update(runner_sandbox_diagnostics=None),
                   envelope_of(s)['result'].update(normalized_outcome='tool_error', ok=False, exit_code=0)),
        ['readers.disposition_integrity', 'readers.disposition_issues', 'consumer_validation'],
        holds=('execution.admitted_reply', 'reported.exit_code'), recapture=False)
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
        step_of(state, 1)['attempt'].update(outcome='open_failed', rc=-1, errno=13)
        state['run']['exit'] = 3
        state['refusals']['unbound']['envelope']['data']['request_failure'].update(code='type_mismatch')
        state['refusals']['unknown_member']['envelope']['data']['runner_result'].update(steps=[{'step_id': 'x'}])
        after(state, 'A')['stat']['st_size'] += 1
        state['property-list']['PWContract'] = RELEASE
    add('combined_independent_faults', combined,
        ['passage.delivery_length', 'echo.specimen_id', 'native.step1.attempt', 'reported.exit_code',
         'native.process_status', 'refusal.unbound.failure', 'refusal.unknown_member.host_reply',
         'native.targets_unchanged', 'passage.contract_matches_property_list'], rest_holds=True)
    add('combined_prerequisite_and_consistency',
        lambda s: (before(s, 'A').update(readable=False), reply_of(s).update(specimen_id='another')),
        ['prerequisite.targets_readable', 'echo.specimen_id'], unevaluated=NATIVE + other_prerequisites,
        rest_holds=True)
    # An association fault beside a native fault in another step: both stay visible.
    add('combined_reordered_and_step3_eacces', lambda s: (set_open(s, 3, EACCES), reply_of(s)['steps'].reverse()),
        ['echo.step_ids', 'native.step3.attempt'], rest_holds=True)
    add('combined_query_records_exchanged_and_step1_eperm',
        lambda s: (set_open(s, 1, EPERM), exchange_records(s, 'sandbox_check', 2, 3)),
        ['echo.queries', 'native.step1.attempt'],
        unevaluated=('native.step2.prediction', 'native.step3.prediction'), rest_holds=True)
    add('combined_step2_dropped_and_answers_exchanged_1_3',
        lambda s: (exchange_answers(s, 1, 3), reply_of(s)['steps'].pop(1)),
        ['echo.step_ids', 'native.step1.prediction', 'native.step3.prediction'],
        unevaluated=STEP_NATIVE[2] + ('native.order',), rest_holds=True)
    # Two native faults in one step and one in another, with a changed sample of an unrelated target.
    coherent('combined_native_faults',
             lambda s: (set_answer(s, 3, ALLOW), set_open(s, 3, EACCES), set_answer(s, 1, DENY),
                        after(s, 'A').update(length=after(s, 'A')['length'] + 1)),
             ['native.step1.prediction', 'native.step3.prediction', 'native.step3.attempt', 'native.targets_unchanged'])
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
    withheld = set()
    for selector in row['unevaluated']:
        chosen = [ident for ident, group, _, _ in checker.ASSERTIONS if ident == selector or group == selector]
        assert chosen, selector
        withheld.update(chosen)
        problems.extend(f'{ident} is {statuses[ident]}, not unevaluated' for ident in chosen
                        if statuses[ident] != 'not_evaluated')
    holding = set(row['holds'])
    if row['rest_holds']:
        holding.update(ident for ident in statuses if ident not in withheld and ident != CONSUMER[0])
    problems.extend(f'{ident} is {statuses[ident]}, not holding' for ident in sorted(holding)
                    if statuses[ident] != 'pass' and (ident, expected_classification(ident)) not in row['expected'])
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


def prepare_controls(artifacts):
    """`prepare` is what the live case runs before submitting: a failed gate writes a report and nothing to run."""
    import plistlib
    records = []
    app = artifacts / 'captures' / 'prepare-app'
    (app / 'Contents').mkdir(parents=True)
    (app / 'Contents/Info.plist').write_bytes(plistlib.dumps({'PWContract': DEVELOPMENT}))
    for name, change, failing in [
        ('passing', lambda s: None, ()),
        ('emission_exit_2', lambda s: s['example-1'].update(exit=2), ('emission.example_exit',)),
        ('emission_stderr', lambda s: s['example-2'].update(stderr=b'warning\n'), ('emission.stderr_empty',)),
        ('emission_not_an_object', lambda s: [s[w].update(stdout=b'[]\n') for w in ('example-1', 'example-2')],
         ('emission.json_object',)),
        ('version_exit_1', lambda s: s['version'].update(exit=1), ('emission.version_exit',)),
        ('bound_write_action',
         lambda s: set_document(s, lambda d: d['probe_plan'][0]['attempt'].update(action='open_write')),
         ('bounds.workload_roles', 'bounds.read_only_attempts')),
        ('bound_another_workload',
         lambda s: set_document(s, lambda d: d['probe_plan'].reverse()), ('bounds.workload_roles',)),
        ('bound_test_overrides', lambda s: set_document(s, lambda d: d.update(_test_overrides={})),
         ('bounds.no_test_overrides',)),
    ]:
        state = build()
        change(state)
        snapshot = artifacts / 'captures' / ('prepare-' + name + '.snapshot.json')
        snapshot.write_text(json.dumps({'surfaces': [{'id': 'request', 'public': {'nodes': [
            {'id': checker.EXAMPLE_NODE, 'document': state['contract-example']['document']}]}}]}))
        # As the live case leaves the directory before `prepare`: the three invocations only.
        for key in ('run', 'property-list', 'contract-example', 'targets-before', 'targets-after'):
            state[key] = None
        state['refusals'] = {}
        directory = artifacts / 'captures' / ('prepare-' + name)
        write(directory, state)
        status = checker.prepare(directory, app, snapshot)
        produced = sorted(path.relative_to(directory).as_posix() for path in directory.rglob('*') if path.is_file())
        runnable = [path for path in produced if path.startswith('refusals/') or path == 'targets-before.json']
        if failing:
            report = json.loads((directory / 'report.json').read_text())
            assert status == 1 and not runnable, (name, status, runnable)
            assert checker.diagnostics(report) == pairs(*failing), (name, checker.diagnostics(report))
            assert all(row['status'] == 'not_evaluated' for row in report['assertions']
                       if row['group'] in RUN_GROUPS), name
        else:
            assert status == 0 and 'report.json' not in produced, (name, status, produced)
            assert runnable == sorted(['targets-before.json'] + [f'refusals/{refusal}/input.json' for refusal in REFUSALS]), runnable
            assert json.loads((directory / 'property-list.json').read_text())['PWContract'] == DEVELOPMENT
            assert json.loads((directory / 'contract-example.json').read_text())['document'] == \
                {key: value for key, value in document_of(state).items() if key != 'contract'}
            emitted = state['example-1']['stdout']
            for refusal in REFUSALS:
                submitted = (directory / 'refusals' / refusal / 'input.json').read_bytes()
                assert checker._one_change(refusal, emitted, document_of(state), submitted) == [], refusal
        records.append({'control': 'prepare_' + name, 'status': status, 'failing': list(failing), 'files': produced})
    return records


def accepted_variants():
    """Alterations the checker must accept, each for a stated reason."""
    def short_target(state):
        # C shorter than the bound: the whole file is its bounded prefix.
        count = 10
        for sampled in (before, after):
            sampled(state, 'C').update(sample('C', sampled(state, 'C')['target']), length=count,
                                       sha256=hashlib.sha256(CONTENT['C'][:count]).hexdigest(),
                                       prefix_length=count, prefix_sha256=hashlib.sha256(CONTENT['C'][:count]).hexdigest())
            sampled(state, 'C')['stat']['st_size'] = count
        set_fresh(state, read_rc=count, content_hex=CONTENT['C'][:count].hex())
    return [
        # A descriptor is any nonnegative integer; zero is a successful open.
        ('fresh_open_returns_descriptor_0', lambda s: set_fresh(s, open_rc=0)),
        ('fresh_read_of_a_target_shorter_than_the_bound', short_target),
        # Steps 1 and 2 expect the same answer, so exchanging those two answers changes nothing
        # in the capture. This is the workload's stated blind spot, not a distinction it makes.
        ('answers_exchanged_1_2', lambda s: exchange_answers(s, 1, 2)),
    ]


def uniform_answer_demonstration(artifacts):
    """What a workload with uniform answers could not show, by construction and without a second checker.

    Under a policy that allows everything, every step's answer is the same
    allow. Exchanging two steps' answers there is the identity on the capture:
    no reader of any kind can tell the exchanged capture from the original.
    In the present workload the same exchange changes the capture for each
    pair that involves step 3, and not for steps 1 and 2.
    """
    uniform = build()
    set_answer(uniform, 3, ALLOW)
    set_open(uniform, 3)
    recapture_host_reply(uniform['run']['envelope'])
    directory = artifacts / 'captures' / 'uniform_answers'
    write(directory, uniform)
    report = checker.evaluate(checker.load(directory), authored_fixture=True)
    # The uniform capture is itself a reply the consumer reads cleanly; the present checker rejects
    # only step 3's own two expectations in it.
    assert not report['consumer_errors'], report['consumer_errors']
    assert checker.diagnostics(report) == pairs('native.step3.prediction', 'native.step3.attempt'), checker.diagnostics(report)
    records = []
    for name, base, changing in (('uniform_answers', uniform, set()), ('present_workload', build(), {(1, 3), (2, 3)})):
        for first, second in ((1, 2), (1, 3), (2, 3)):
            state = copy.deepcopy(base)
            exchange_answers(state, first, second)
            changed = state != base
            assert changed == ((first, second) in changing), (name, first, second, changed)
            records.append({'capture': name, 'answers_exchanged_between_steps': [first, second],
                            'capture_changed': changed})
    return records


def main():
    artifacts = Path(sys.argv[1])
    if (artifacts / 'captures').exists():
        shutil.rmtree(artifacts / 'captures')
    results = {'baselines': [], 'accepted_variants': [], 'controls': [], 'perturbations': perturbation_controls(),
               'prepare': prepare_controls(artifacts),
               'uniform_answer_demonstration': uniform_answer_demonstration(artifacts)}
    failures = []
    # The checker's table must carry the classification this case authors for each assertion.
    disagreeing = [ident for ident, _, carried, _ in checker.ASSERTIONS if carried != expected_classification(ident)]
    if disagreeing:
        failures.append('classification differs from this case\'s expectation: ' + ', '.join(disagreeing))
    # The selector controls below name every selection key the checker reads from the shape golden.
    if set(checker.RUNNER_SELECTION_KEYS) != {'runner', 'runner_id', 'runner_service', 'runner_mode'} or \
            checker.ENTITLEMENT_KEY not in checker.SELECTOR_FIELDS:
        failures.append('the controller selection keys changed; add a bounds control for each: ' +
                        ', '.join(checker.SELECTOR_FIELDS))
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
    for name, change in accepted_variants():
        state = build()
        change(state)
        recapture_host_reply(state['run']['envelope'])
        directory = artifacts / 'captures' / ('accepted_' + name)
        write(directory, state)
        report = checker.evaluate(checker.load(directory), authored_fixture=True)
        (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        unsettled = [row['id'] for row in report['assertions'] if row['status'] != 'pass']
        results['accepted_variants'].append({'variant': name, 'status': report['status'], 'not_passing': unsettled,
                                             'consumer_errors': report['consumer_errors']})
        if report['status'] != 'pass' or unsettled or report['consumer_errors']:
            failures.append(f'accepted variant {name}: {checker.render(report)} {report["consumer_errors"]}')
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
