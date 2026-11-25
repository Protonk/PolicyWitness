#!/usr/bin/env python3
"""Rejected controls for every row and every condition of the example round-trip checker.

A constructed capture stands in for the app's emission and its three runs:
this case tests the checker, not the app. The emitted document is phased, and
its flat and single-actor derivatives are authored here beside it. The
ordinary envelopes are the authored run under tests/fixtures/blackbox_e2e,
whose allowed and denied file steps are read as the workload's first and third
steps, with one fresh-read step and three target samples authored here; the
actor envelope is the authored fixture under tests/fixtures/example_round_trip.
Everything is placed in retained capture files exactly as the live case leaves
them, and read through the one `evaluate` the live case runs. No process is
launched and nothing here is a native observation. The observer controls alone
touch real files: two this case writes in its own directory.

Each rejected control introduces one logical fault in one form and states,
independently of the checker's output, the exact set of (assertion identifier,
classification) pairs that form must produce; the other forms must hold. A
control that changes one submission's capture runs once in each form. A
control earns coverage for its target rows only when the actual set matches.
The shared consumer's aggregate diagnostic is permitted beside any other
control's set and earns nothing there; its own propagation control requires it
exactly. Coverage is complete when every row of the passing three-form report
has a matched control in its form, and every condition the checker declares
has a matched control that fails that condition alone in its row.

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
import consumer
from blackbox import bind_constructed_envelope, envelope_skeleton, recapture_host_reply
import file_observation
import check_example_round_trip as checker
from check_extension_example import reader_policy_mismatches
from check_example_round_trip import FORMS, REFUSALS, UNKNOWN_MEMBER

# The classifications this case expects, spelled here and not read from the checker.
CONSISTENCY = 'consistency'
EXECUTION_UNAVAILABLE = 'execution_unavailable'
PREREQUISITE_UNESTABLISHED = 'prerequisite_unestablished'
NATIVE_OBSERVATION = 'native_observation'

FIXTURE = ROOT / 'tests/fixtures/blackbox_e2e/checker/current/constructed_run.json'
ACTOR_FIXTURE = ROOT / 'tests/fixtures/example_round_trip/constructed_actor_run.json'
DEVELOPMENT = 'development:' + 'c0' * 32
RELEASE = 'release:v9.9.9'
CONSUMER = ('consumer_validation', CONSISTENCY)
# Everything that reads the run: unevaluated when the emission or its bounds fail.
RUN_GROUPS = ('admission', 'identity', 'execution', 'echo', 'reported', 'readers', 'native', 'refusals', 'structure')
# The labels this case gives its constructed phases and actor. The checker reads none of them.
PHASE_LABELS = ('constructed-initial', 'constructed-restricted')
ACTOR_LABEL = 'constructed-reader'
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
                   'echo.attempts', 'readers.disposition_integrity', 'readers.disposition_issues', 'structure') + NATIVE
EMITTED = ('emitted',)
CONTAINER = 'bounds.ordinary_form'
COLLECTIONS = 'structure.collections'
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


def triples(form, *identifiers):
    return {(form, ident, expected_classification(ident)) for ident in identifiers}


def phase_count(form):
    """How many phases this case's constructed reply holds in one form."""
    return 1 if form == 'flat' else len(PHASE_LABELS)


def each_phase(*names):
    """The named condition in every phase of whichever form a control runs in."""
    return lambda form: [f'phase{number}.{name}' for number in range(1, phase_count(form) + 1) for name in names]


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
    return file_observation.fresh_record(CONTENT[role],
        dict(device=device, inode=inode, mode=33188, uid=0, gid=0), bound=count, descriptor=descriptor)



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


def repartition(reply, partitions):
    """Author a coherent partition of one reply: phase records, collection ownership and step echoes."""
    templates = copy.deepcopy(reply['phases'])
    records = {record['step_id']: record for phase in templates for record in phase['validator_subprocess']['records']}
    reply['phases'] = []
    for ordinal, (label, steps) in enumerate(partitions, 1):
        phase = copy.deepcopy(templates[0])
        ids = [step['step_id'] for step in steps]
        phase.update(phase_id=label, ordinal=ordinal, action_ids=ids)
        phase['validator_subprocess'].update(phase_id=label, ordinal=ordinal, pid=52000 + ordinal,
                                             expected_step_ids=ids, records=[records[ident] for ident in ids])
        if reply.get('execution_form') == 'actors':
            phase.update(actor_id=reply['actors'][0]['actor_id'], actor_visit=ordinal)
        for step in steps:
            step['phase_id'] = label
        reply['phases'].append(phase)


def serialized(document):
    return (json.dumps(document, indent=2, sort_keys=True) + '\n').encode()


def build(identity=DEVELOPMENT, counts=(2, 1)):
    """Every retained input of a passing case, as values a control can change before they are written.

    The emitted document is phased with `counts` actions in each phase. Its
    flat and actor derivatives are authored here, each with its own run and
    samples; the checker's constructor is not their source.
    """
    def ordinary(partitioned):
        run = constructed_run(identity)
        reply = run['data']['runner_result']
        if partitioned:
            stops = [sum(counts[:index + 1]) for index in range(len(counts))]
            repartition(reply, [(label, reply['steps'][stop - count:stop])
                                for label, count, stop in zip(PHASE_LABELS, counts, stops)])
        return run

    run = ordinary(True)
    reply = run['data']['runner_result']
    actions = [{'step_id': step['step_id'],
                'sandbox_check': {'operation': step['sandbox_check']['operation'],
                                  'filter': {'kind': step['sandbox_check']['filter_kind'],
                                             'value': step['sandbox_check']['filter_value']}},
                'attempt': {'kind': 'file', 'action': step['attempt']['requested_action'],
                            'target': step['attempt']['requested_path']}}
               for step in reply['steps']]
    policy = {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'}
    stops = [sum(counts[:index + 1]) for index in range(len(counts))]
    phases = [{'phase_id': label, 'actions': actions[stop - count:stop]}
              for label, count, stop in zip(PHASE_LABELS, counts, stops)]
    document = {'contract': identity, 'specimen_id': reply['specimen_id'], 'policy': policy, 'phases': phases}
    flat_document = {'contract': identity, 'specimen_id': reply['specimen_id'], 'policy': copy.deepcopy(policy),
                     'probe_plan': copy.deepcopy(actions)}
    actor_document = {'contract': identity, 'specimen_id': reply['specimen_id'],
                      'actors': [{'actor_id': ACTOR_LABEL, 'equipment': 'selected',
                                  'sandbox': {'mode': 'apply', 'policy': copy.deepcopy(policy)}}],
                      'phases': [dict(copy.deepcopy(phase), actor_id=ACTOR_LABEL) for phase in phases]}
    actor_run = bind_constructed_envelope(json.loads(ACTOR_FIXTURE.read_text()))
    actor_run['build']['contract'] = actor_run['data']['runner_client']['transport']['contract'] = identity
    actor_run['data']['runner_result']['producer']['contract'] = identity
    if tuple(counts) != (2, 1):
        actor_reply = actor_run['data']['runner_result']
        repartition(actor_reply, [(label, actor_reply['steps'][stop - count:stop])
                                  for label, count, stop in zip(PHASE_LABELS, counts, stops)])
    digest = hashlib.sha256(policy['sbpl_source'].encode()).hexdigest()
    emitted = serialized(document)
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
        'forms': {},
    }
    for form, derived, envelope in (('flat', flat_document, ordinary(False)), ('actor', actor_document, actor_run)):
        state['forms'][form] = {'input': serialized(derived), 'run': {'exit': 0, 'envelope': envelope, 'stderr': b''},
                                'targets-before': copy.deepcopy(observed), 'targets-after': copy.deepcopy(observed)}
    for form in FORMS:
        view = capture(state, form)
        envelope = view['run']['envelope']
        if form != 'actor':
            envelope['data']['runner_result']['policy_sha256'] = digest
            envelope['data']['specimen']['policy']['augmentation'].update(original_sha256=digest, applied_sha256=digest)
        envelope['data']['runner_client']['request_delivery']['bytes_written'] = len(submitted_of(view)) - 1
        recapture_host_reply(envelope)
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

    def submission(base, entry):
        if entry.get('run') is not None:
            invocation(base / 'run', entry['run'])
        for name in ('targets-before', 'targets-after'):
            if entry.get(name) is not None:
                (base / (name + '.json')).write_text(json.dumps(entry[name], indent=2) + '\n')

    for name in ('version', 'example-1', 'example-2'):
        if state.get(name) is not None:
            invocation(directory / name, state[name])
    for name in ('property-list', 'contract-example'):
        if state.get(name) is not None:
            (directory / (name + '.json')).write_text(json.dumps(state[name], indent=2) + '\n')
    submission(directory, state)
    for form, entry in state.get('forms', {}).items():
        (directory / form).mkdir()
        if entry.get('input') is not None:
            (directory / form / 'input.json').write_bytes(entry['input'])
        submission(directory / form, entry)
    for name, entry in state['refusals'].items():
        base = directory / 'refusals' / name
        base.mkdir(parents=True)
        if entry.get('input') is not None:
            (base / 'input.json').write_bytes(entry['input'])
        invocation(base / 'run', entry)


# ---------------------------------------------------------------------------
# State accessors used by the controls
# ---------------------------------------------------------------------------

def capture(state, form):
    """One submission's retained inputs. The emitted submission's sit beside the publication records."""
    return state if form == 'emitted' else state['forms'][form]


def submitted_of(view):
    """The bytes one submission handed to `run`."""
    return view['input'] if 'input' in view else view['example-1']['stdout']


def document_of(view):
    return json.loads(submitted_of(view).decode())


def set_document(state, change):
    """Change the emitted document itself: both emissions and the snapshot's rendering agree."""
    document = document_of(state)
    change(document)
    emitted = serialized(document)
    state['example-1']['stdout'] = state['example-2']['stdout'] = emitted
    state['contract-example']['document'] = {key: value for key, value in document.items() if key != 'contract'}


def set_input(view, change):
    """Change one derivative's submitted document."""
    document = document_of(view)
    change(document)
    view['input'] = serialized(document)


def envelope_of(view):
    return view['run']['envelope']


def reply_of(view):
    return envelope_of(view)['data']['runner_result']


def actor_of(view):
    """The sole actor's record when the reply is in actor form."""
    reply = reply_of(view)
    return reply['actors'][0] if reply.get('execution_form') == 'actors' else None


def policy_record(view):
    """The record that carries the reply's policy digest in this form."""
    return actor_of(view) or reply_of(view)


def dossier_policy(view):
    specimen = envelope_of(view)['data']['specimen']
    return (specimen['actors'][0] if actor_of(view) else specimen)['policy']


def worker_of(view):
    actor = actor_of(view)
    return actor['subprocess'] if actor else reply_of(view)['runner_subprocess']


def phase_of(view, number):
    return reply_of(view)['phases'][number - 1]


def step_of(state, number=1):
    return reply_of(state)['steps'][number - 1]


def validator_record(state, number):
    ident = step_of(state, number)['step_id']
    return next(record for phase in reply_of(state)['phases']
                for record in phase['validator_subprocess']['records'] if record['step_id'] == ident)


def before(state, role):
    return state['targets-before']['targets']['ABC'.index(role)]


def after(state, role):
    return state['targets-after']['targets']['ABC'.index(role)]


def spawn_failed(state):
    """A coherent reply whose validator never ran: no prediction, honest `unestablished` order, exit 1."""
    envelope, reply = envelope_of(state), reply_of(state)
    reply.update(normalized_outcome='validator_spawn_failed', rc=1, error='constructed validator spawn failure')
    for phase in reply['phases']:
        phase['ordering'].update(validator_disposition='not_spawned')
        phase.pop('validator_subprocess')
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
    for phase in reply_of(state)['phases']:
        phase['ordering'].update(worker_lifetime_established=False)
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

class Rows:
    """Control rows: (name, forms, change, targets, expected identifiers, requirements).

    `targets` are the assertions the control is about; `expected` is the full
    set its fault necessarily produces in the form it runs in. `conditions`
    states, for each expected row built from conditions, exactly which fail.
    Requirements name assertions that must be unevaluated or must hold,
    whether the consumer must read cleanly, and a reader rule the consumer
    must report when the control is about that rule. `rest_holds` requires every
    assertion of that form outside the expected and unevaluated sets to hold,
    so the control states the form's whole report. The other forms hold, or
    are wholly unevaluated when the emission itself is refused.
    """

    def __init__(self):
        self.rows = []

    def add(self, name, change, targets, also=(), *, identity=DEVELOPMENT, unevaluated=(), holds=(), clean=False,
            recapture=True, exactly_consumer=False, rest_holds=False, forms=FORMS, conditions=None,
            derivatives_withheld=False, per_form=None, consumer_reports=None, whole_state=False):
        self.rows.append(dict(name=name, identity=identity, change=change, targets=tuple(targets),
                              expected=tuple(targets) + tuple(also), unevaluated=tuple(unevaluated),
                              holds=tuple(holds), clean=clean, recapture=recapture,
                              exactly_consumer=exactly_consumer, rest_holds=rest_holds, forms=tuple(forms),
                              conditions=dict(conditions or {}), derivatives_withheld=derivatives_withheld,
                              per_form=dict(per_form or {}), consumer_reports=consumer_reports,
                              whole_state=whole_state))

    def coherent(self, name, change, targets, also=(), *, unevaluated=(), **requirements):
        """The consumer reads the altered reply cleanly, and the stated sets are the form's whole report."""
        self.add(name, change, targets, also, unevaluated=unevaluated, clean=True, rest_holds=True, **requirements)


def controls():
    """The rows for every scalar assertion. A row that changes one submission's capture runs in every form."""
    collected = Rows()
    add, coherent = collected.add, collected.coherent
    rows = collected.rows

    def emission(name, change, targets, also=()):
        # A failed emission prevents submission: nothing that reads a run is evaluated,
        # although the constructed run captures are present, and no derivative is judged.
        add('emission_' + name, change, targets, also, unevaluated=RUN_GROUPS + ('passage.delivery_length',),
            forms=EMITTED, derivatives_withheld=True)

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
        ['passage.contract_matches_version'], forms=EMITTED)
    add('passage_version_data', lambda s: s['version']['envelope']['data'].update(contract=RELEASE),
        ['passage.contract_matches_version'], forms=EMITTED)
    add('passage_version_unreadable', lambda s: s['version'].update(stdout=b'not an envelope\n'),
        ['passage.contract_matches_version'], forms=EMITTED)
    add('passage_property_list_differs', lambda s: s['property-list'].update(PWContract=RELEASE),
        ['passage.contract_matches_property_list'], forms=EMITTED)
    add('passage_property_list_absent', lambda s: s.update({'property-list': None}),
        ['passage.contract_matches_property_list'], forms=EMITTED)
    add('passage_unpackaged_identity', lambda s: None, ['passage.contract_packaged_form'], identity='test:unpackaged', forms=EMITTED)
    add('passage_emissions_differ',
        lambda s: s['example-2'].update(stdout=(json.dumps(document_of(s), sort_keys=True) + '\n').encode()),
        ['passage.emissions_identical'], forms=EMITTED)
    add('passage_delivery_length',
        lambda s: envelope_of(s)['data']['runner_client']['request_delivery'].update(
            bytes_written=len(submitted_of(s))),
        ['passage.delivery_length'], recapture=False)
    add('passage_delivery_length_boolean',
        lambda s: envelope_of(s)['data']['runner_client']['request_delivery'].update(bytes_written=True),
        ['passage.delivery_length'], recapture=False)
    add('passage_rendering_member_differs', lambda s: s['contract-example']['document'].update(specimen_id='another'),
        ['passage.contract_rendering'], forms=EMITTED)
    add('passage_rendering_extra_member', lambda s: s['contract-example']['document'].update(run_kind='label'),
        ['passage.contract_rendering'], forms=EMITTED)
    add('passage_rendering_not_retained', lambda s: s.update({'contract-example': None}), ['passage.contract_rendering'], forms=EMITTED)

    def bounds(name, change, targets, also=(), conditions=None):
        add('bounds_' + name, lambda s: set_document(s, change), targets, also,
            unevaluated=RUN_GROUPS + PREREQUISITES + ('passage.delivery_length',), forms=EMITTED,
            derivatives_withheld=True, conditions={CONTAINER: conditions} if conditions else None)

    def plan(document, number):
        return checker.actions(document)[number - 1]

    def planned(document):
        return list(checker.actions(document))

    def replan(document, steps):
        """Place a list of steps in the phases: each phase keeps its count while steps remain, the last takes the rest."""
        counts = [len(phase['actions']) for phase in document['phases']]
        position = 0
        for index, phase in enumerate(document['phases']):
            stop = len(steps) if index == len(counts) - 1 else position + counts[index]
            phase['actions'] = steps[position:stop]
            position = stop

    def retarget(step, path, *, query=True, attempt=True):
        if query:
            step['sandbox_check']['filter']['value'] = path
        if attempt:
            step['attempt']['target'] = path

    def target(document, role):
        return {'A': plan(document, 1)['attempt']['target'], 'B': plan(document, 3)['attempt']['target'],
                'C': plan(document, 2)['attempt']['target']}[role]

    def fourth(**attempt):
        return {'step_id': 'fourth', 'sandbox_check': {'operation': 'file-read-data',
                                                         'filter': {'kind': 'path', 'value': '/constructed/fourth'}},
                'attempt': attempt}
    roles = ['bounds.workload_roles']
    # The container. Each control fails one of its conditions; a document with another number of
    # steps is also another workload.
    bounds('empty_plan', lambda d: d.update(phases=[]), [CONTAINER], roles, ['phases'])
    bounds('plan_not_an_array', lambda d: d.update(phases={'phase_id': 'x'}), [CONTAINER], roles, ['phases'])
    bounds('third_phase', lambda d: d['phases'].append({'phase_id': 'third', 'actions': []}), [CONTAINER],
           conditions=['phases'])
    bounds('plan_in_place_of_phases', lambda d: (d.update(probe_plan=planned(d)), d.pop('phases')), [CONTAINER],
           conditions=['phases', 'no_probe_plan'])
    bounds('plan_member_beside_phases', lambda d: d.update(probe_plan=None), [CONTAINER], conditions=['no_probe_plan'])
    bounds('actors', lambda d: d.update(actors=[{'actor_id': 'a'}]), [CONTAINER], conditions=['no_actors'])
    bounds('phase_identifiers_equal', lambda d: d['phases'][1].update(phase_id=d['phases'][0]['phase_id']),
           [CONTAINER], conditions=['distinct_phase_ids'])
    for number in (1, 2):
        bounds(f'phase{number}_extra_member', lambda d, number=number: d['phases'][number - 1].update(actor_id='a'),
               [CONTAINER], conditions=[f'phase{number}.members'])
        bounds(f'phase{number}_member_absent', lambda d, number=number: d['phases'][number - 1].pop('phase_id'),
               [CONTAINER], conditions=[f'phase{number}.members'])
        bounds(f'phase{number}_identifier_empty', lambda d, number=number: d['phases'][number - 1].update(phase_id=''),
               [CONTAINER], conditions=[f'phase{number}.phase_id'])
        bounds(f'phase{number}_identifier_not_a_string', lambda d, number=number: d['phases'][number - 1].update(phase_id=7),
               [CONTAINER], conditions=[f'phase{number}.phase_id'])
        bounds(f'phase{number}_fourth_read_action',
               lambda d, number=number: d['phases'][number - 1]['actions'].append(
                   fourth(kind='file', action='access', target='/constructed/fourth')),
               [CONTAINER], roles, [f'phase{number}.actions'])
        bounds(f'phase{number}_actions_not_an_array', lambda d, number=number: d['phases'][number - 1].update(actions={}),
               [CONTAINER], roles, [f'phase{number}.actions'])
    bounds('action_moved_to_the_second_phase', lambda d: d['phases'][1]['actions'].insert(0, d['phases'][0]['actions'].pop()),
           [CONTAINER], conditions=['phase1.actions', 'phase2.actions'])
    for action, attempt in (('write', dict(kind='file', action='open_write', target='/constructed/fourth')),
                            ('unlink', dict(kind='file', action='unlink', target='/constructed/fourth')),
                            ('exec', dict(kind='exec', action='spawn', target='/usr/bin/true'))):
        bounds(action + '_action', lambda d, attempt=attempt: d['phases'][-1]['actions'].append(fourth(**attempt)),
               ['bounds.read_only_attempts'], roles + [CONTAINER], ['phase2.actions'])
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

    # Another workload: every attempt is still read-only, and the roles refuse it. Where the
    # change also leaves a phase with another number of actions, the container says which.
    def role(name, change, container=None):
        bounds('roles_' + name, change, roles, [CONTAINER] if container else (), container)
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
    # Neither operand a path: nothing would then tie the step to a target at all.
    for number in (1, 3):
        role(f'step{number}_neither_operand_a_path',
             lambda d, number=number: (plan(d, number)['sandbox_check']['filter'].update(kind='literal'),
                                       plan(d, number)['attempt'].update(target=None)))
    role('step2_fresh_read_of_queried_target', lambda d: retarget(plan(d, 2), target(d, 'B'), query=False))
    role('step2_fresh_read_of_step1_target', lambda d: retarget(plan(d, 2), target(d, 'A'), query=False))
    role('step2_queries_step1_target', lambda d: retarget(plan(d, 2), target(d, 'A'), attempt=False))
    role('step2_data_query', lambda d: plan(d, 2)['sandbox_check'].update(operation='file-read-data'))
    role('step2_open_read', lambda d: plan(d, 2)['attempt'].update(action='open_read'))
    role('missing_fresh_read_step', lambda d: replan(d, [plan(d, 1), plan(d, 3)]), ['phase2.actions'])
    role('missing_second_open_step', lambda d: replan(d, planned(d)[:2]), ['phase2.actions'])
    role('missing_first_open_step', lambda d: replan(d, planned(d)[1:]), ['phase2.actions'])
    role('one_step', lambda d: replan(d, planned(d)[:1]), ['phase1.actions', 'phase2.actions'])
    role('duplicated_step_appended', lambda d: replan(d, planned(d) + [dict(copy.deepcopy(plan(d, 1)), step_id='again')]),
         ['phase2.actions'])
    role('step3_duplicates_step1', lambda d: replan(d, planned(d)[:2] + [dict(copy.deepcopy(plan(d, 1)), step_id='again')]))
    role('duplicate_step_identifier', lambda d: plan(d, 3).update(step_id=plan(d, 1)['step_id']))
    role('reordered_fresh_read_last', lambda d: replan(d, [plan(d, 1), plan(d, 3), plan(d, 2)]))
    role('reordered_fresh_read_first', lambda d: replan(d, [plan(d, 2), plan(d, 1), plan(d, 3)]))
    role('reordered_opens_exchanged', lambda d: replan(d, planned(d)[::-1]))

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
    unworked = ['reply_pid', 'pid', 'reaped', 'ready_byte_received', 'done_observed', 'exit_code', 'collection_basis']
    add('admission_host_refuses_the_example', host_refuses, ['admission.no_request_failure'],
        ['echo.step_ids', 'native.completion', 'native.process_status', 'structure.phase_membership', COLLECTIONS],
        unevaluated=('echo.queries', 'echo.attempts', 'native.order') + every_step,
        conditions={'structure.phase_membership': ['phase_count'], COLLECTIONS: each_phase('unique')},
        per_form={form: {'also': ['structure.worker'], 'conditions': {'structure.worker': unworked}}
                  for form in ('emitted', 'flat')})
    add('admission_dossier_digest',
        lambda s: dossier_policy(s)['augmentation'].update(original_sha256='0' * 64),
        ['admission.dossier_policy_digest'], recapture=False)
    add('admission_reply_digest', lambda s: policy_record(s).update(policy_sha256='0' * 64), ['admission.reply_policy_digest'])

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
             ['native.completion', 'native.process_status', *predictions], [COLLECTIONS], unevaluated=('native.order',),
             conditions={COLLECTIONS: each_phase('validator_reaped', 'validator_disposition', 'expected_step_ids')})
    # A nonzero exit alone is not a consistency fault; a reported exit that differs from the observed one is.
    add('native_validator_spawn_failed_exit_0', lambda s: (spawn_failed(s), s['run'].update(exit=0)),
        ['reported.exit_code'], ['native.completion', *predictions, COLLECTIONS], unevaluated=('native.order',),
        clean=True, rest_holds=True, conditions={COLLECTIONS: each_phase('validator_reaped', 'validator_disposition', 'expected_step_ids')})

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
    coherent('native_order_unestablished', coherent_unestablished, ['native.order'], [COLLECTIONS],
             conditions={COLLECTIONS: each_phase('worker_lifetime_established')})
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

    # A missing prerequisite withholds every native pass. B is only ever queried and opened
    # without success, so the reply alone would never show that this user cannot read it.
    other_prerequisites = PREREQUISITES[1:]

    def unreadable(state, role_name):
        """The first sample as the observer leaves it when its open is refused: no metadata and no digests."""
        record = before(state, role_name)
        kept = {'target': record['target'], 'resolved': record['resolved'], 'regular_file': False, 'readable': False,
                'error': 'PermissionError: constructed'}
        record.clear()
        record.update(kept)

    def not_regular(state, role_name):
        """The first sample of something that is not a regular file: its metadata, and nothing read."""
        record = before(state, role_name)
        for member in ('sha256', 'length', 'prefix_sha256', 'prefix_length'):
            record.pop(member)
        record.update(regular_file=False, readable=False)

    def unsampled(state, role_name):
        state['targets-before']['targets'].remove(before(state, role_name))
    for role_name in 'ABC':
        coherent(f'prerequisite_{role_name}_unreadable', lambda s, role_name=role_name: unreadable(s, role_name),
                 ['prerequisite.targets_readable'], unevaluated=NATIVE + other_prerequisites)
        coherent(f'prerequisite_{role_name}_not_regular', lambda s, role_name=role_name: not_regular(s, role_name),
                 ['prerequisite.targets_readable'], unevaluated=NATIVE + other_prerequisites)
        coherent(f'prerequisite_{role_name}_not_sampled', lambda s, role_name=role_name: unsampled(s, role_name),
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
    # Where C's sample changes, the fresh read is of the file the sample now describes, so the
    # reply still corresponds and the prerequisite is the only fault.
    coherent('prerequisite_A_and_B_one_file', lambda s: same_file(s, 'A', 'B'),
             ['prerequisite.distinct_identities'], unevaluated=NATIVE)
    for other in ('A', 'B'):
        coherent(f'prerequisite_C_and_{other}_one_file',
                 lambda s, other=other: (same_file(s, 'C', other), fresh_of(s, other, content=False)),
                 ['prerequisite.distinct_identities'], unevaluated=NATIVE)
        coherent(f'prerequisite_C_prefix_equals_{other}',
                 lambda s, other=other: (same_prefix(s, 'C', other), fresh_of(s, other, identity=False)),
                 ['prerequisite.distinguishing_prefixes'], unevaluated=NATIVE)

    def identity_not_observed(state, role_name):
        for sampled in (before, after):
            sampled(state, role_name)['stat'].pop('st_ino')

    def empty_prefix(state, role_name):
        for sampled in (before, after):
            sampled(state, role_name).update(prefix_length=0, prefix_sha256=hashlib.sha256(b'').hexdigest())
        if role_name == 'C':
            fresh_of(state, 'C', identity=False, count=0)
    for role_name in 'ABC':
        coherent(f'prerequisite_{role_name}_identity_not_observed',
                 lambda s, role_name=role_name: identity_not_observed(s, role_name),
                 ['prerequisite.distinct_identities'], unevaluated=NATIVE)
        coherent(f'prerequisite_{role_name}_prefix_empty', lambda s, role_name=role_name: empty_prefix(s, role_name),
                 ['prerequisite.distinguishing_prefixes'], unevaluated=NATIVE)

    # An expectation that is read and not met fails beside the missing prerequisite. Every native
    # assertion not named as failing is unevaluated: without the prerequisite none passes.
    def beside(name, change, prerequisite, faults, also=(), conditions=None):
        failing = tuple(faults) + tuple(also) + tuple(conditions or ())
        withheld = tuple(ident for ident in NATIVE if ident not in failing)
        if prerequisite == 'prerequisite.targets_readable':
            withheld += other_prerequisites
        add('prerequisite_' + name, change, [prerequisite, *faults], tuple(also) + tuple(conditions or ()),
            unevaluated=withheld, clean=not also, rest_holds=True, conditions=conditions)

    readable = 'prerequisite.targets_readable'
    # The fresh read is compared with this checker's sample of C, whatever is known of B or A.
    for role_name in 'AB':
        beside(f'{role_name}_not_sampled_and_fresh_identity_of_A',
               lambda s, role_name=role_name: (fresh_of(s, 'A', content=False), unsampled(s, role_name)),
               readable, ['native.step2.fresh_identity'])
        beside(f'{role_name}_unreadable_and_fresh_content_of_B',
               lambda s, role_name=role_name: (fresh_of(s, 'B', identity=False), unreadable(s, role_name)),
               readable, ['native.step2.fresh_content'])
    beside('B_unreadable_and_step1_open_fails', lambda s: (unreadable(s, 'B'), set_open(s, 1, EACCES)),
           readable, ['native.step1.attempt'])
    beside('B_unreadable_and_step1_denied', lambda s: (unreadable(s, 'B'), set_answer(s, 1, DENY)),
           readable, ['native.step1.prediction'])
    beside('A_unreadable_and_step3_eacces', lambda s: (unreadable(s, 'A'), set_open(s, 3, EACCES)),
           readable, ['native.step3.attempt'])
    beside('C_unreadable_and_answers_exchanged_2_3', lambda s: (unreadable(s, 'C'), exchange_answers(s, 2, 3)),
           readable, ['native.step2.prediction', 'native.step3.prediction'])
    beside('A_unreadable_and_fresh_close_fails', lambda s: (unreadable(s, 'A'), fresh_fails(s, 'close')),
           readable, ['native.step2.attempt', 'native.step2.fresh_syscalls'])
    beside('B_unreadable_and_order_unestablished', lambda s: (unreadable(s, 'B'), coherent_unestablished(s)),
           readable, ['native.order'], conditions={COLLECTIONS: each_phase('worker_lifetime_established')})
    beside('B_unreadable_and_A_changed',
           lambda s: (unreadable(s, 'B'), after(s, 'A').update(length=after(s, 'A')['length'] + 1)),
           readable, ['native.targets_unchanged'])
    beside('C_unreadable_and_validator_spawn_failed', lambda s: (unreadable(s, 'C'), spawn_failed(s)),
           readable, ['native.completion', 'native.process_status', 'native.step1.prediction',
                      'native.step2.prediction', 'native.step3.prediction'],
           conditions={COLLECTIONS: each_phase('validator_reaped', 'validator_disposition', 'expected_step_ids')})
    beside('C_not_sampled_and_status_3', lambda s: (unsampled(s, 'C'), s['run'].update(exit=3)),
           readable, ['native.process_status'], ['reported.exit_code'])
    beside('A_and_B_one_file_and_step3_eacces', lambda s: (same_file(s, 'A', 'B'), set_open(s, 3, EACCES)),
           'prerequisite.distinct_identities', ['native.step3.attempt'])
    beside('C_and_A_one_file_and_fresh_identity_of_neither', lambda s: same_file(s, 'C', 'A'),
           'prerequisite.distinct_identities', ['native.step2.fresh_identity'])
    beside('C_prefix_equals_A_and_fresh_content_of_neither', lambda s: same_prefix(s, 'C', 'A'),
           'prerequisite.distinguishing_prefixes', ['native.step2.fresh_content'])
    beside('C_prefix_equals_A_and_step1_denied', lambda s: (same_prefix(s, 'C', 'A'), fresh_of(s, 'A', identity=False),
                                                           set_answer(s, 1, DENY)),
           'prerequisite.distinguishing_prefixes', ['native.step1.prediction'])

    # An expectation about a target this checker did not read is not read at all: an unmet one
    # there is what the missing file itself would produce, and only the prerequisite reports it.
    for name, change in (
            ('A_unreadable_and_step1_open_fails', lambda s: (unreadable(s, 'A'), set_open(s, 1, ENOENT))),
            ('A_not_sampled_and_step1_denied', lambda s: (unsampled(s, 'A'), set_answer(s, 1, DENY))),
            ('B_unreadable_and_step2_denied', lambda s: (unreadable(s, 'B'), set_answer(s, 2, DENY))),
            ('B_unreadable_and_step3_allowed', lambda s: (unreadable(s, 'B'), set_answer(s, 3, ALLOW))),
            ('B_not_sampled_and_step3_open_enoent', lambda s: (unsampled(s, 'B'), set_open(s, 3, ENOENT))),
            ('B_not_regular_and_step3_succeeds', lambda s: (not_regular(s, 'B'), set_open(s, 3))),
            ('C_unreadable_and_fresh_identity_and_content_of_A', lambda s: (unreadable(s, 'C'), fresh_of(s, 'A'))),
            ('C_not_sampled_and_fresh_open_fails', lambda s: (unsampled(s, 'C'), fresh_fails(s, 'open'))),
            ('not_observed_and_every_step_altered',
             lambda s: (s.update({'targets-before': None}), set_answer(s, 1, DENY), set_open(s, 3), fresh_of(s, 'A')))):
        coherent('prerequisite_' + name, change, [readable], unevaluated=NATIVE + other_prerequisites)
    # A sample of C without an identity leaves the reply's identity nothing to be compared with.
    coherent('prerequisite_C_identity_not_observed_and_fresh_identity_of_A',
             lambda s: (identity_not_observed(s, 'C'), fresh_of(s, 'A', content=False)),
             ['prerequisite.distinct_identities'], unevaluated=NATIVE)
    # The plan's absent B: the answer is unavailable and the open fails as a missing file does.
    # Step 3 is not read, and the status and the unrelated fault in step 1 still are.
    add('prerequisite_B_unreadable_with_other_native_results',
        lambda s: (unreadable(s, 'B'), set_answer(s, 3, ALLOW), set_open(s, 3), set_open(s, 1, EACCES),
                   s['run'].update(exit=3)),
        [readable, 'native.process_status', 'native.step1.attempt'], ['reported.exit_code'],
        unevaluated=tuple(ident for ident in NATIVE if ident not in ('native.process_status', 'native.step1.attempt'))
        + other_prerequisites, rest_holds=True)

    def refuse(*arguments, **requirements):
        add(*arguments, forms=EMITTED, **requirements)

    for name, (code, path, names_identity, component) in REFUSALS.items():
        prefix = 'refusal.' + name
        every = [prefix + '.refused', prefix + '.failure'] + ([prefix + '.expected_identity'] if names_identity else []) + \
                [prefix + ('.no_delivery' if component == 'controller' else '.host_reply')]

        def refusal(state, name=name):
            return state['refusals'][name]

        def accepted(state, r=refusal):
            # An accepted run in its place: the passing run's envelope and exit status.
            r(state).update(envelope=copy.deepcopy(envelope_of(state)), exit=0)
        refuse('refusal_' + name + '_accepted', accepted, every[:1], every[1:])
        refuse('refusal_' + name + '_exit_0', lambda s, r=refusal: r(s).update(exit=0), [prefix + '.refused'])
        refuse('refusal_' + name + '_other_outcome',
            lambda s, r=refusal: r(s)['envelope']['result'].update(normalized_outcome='tool_error'),
            [prefix + '.refused'])
        refuse('refusal_' + name + '_no_envelope', lambda s, r=refusal: r(s).update(stdout=b''), [prefix + '.refused'],
            unevaluated=every[1:])
        refuse('refusal_' + name + '_wrong_code',
            lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].update(code='type_mismatch'),
            [prefix + '.failure'])
        refuse('refusal_' + name + '_wrong_path',
            lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].update(path=['policy']),
            [prefix + '.failure'])
        refuse('refusal_' + name + '_no_failure',
            lambda s, r=refusal: r(s)['envelope']['data'].update(request_failure=None),
            [prefix + '.failure'], [prefix + '.expected_identity'] if names_identity else [])
        if names_identity:
            refuse('refusal_' + name + '_identity_missing',
                lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].pop('expected_contract'),
                [prefix + '.expected_identity'])
            refuse('refusal_' + name + '_identity_wrong',
                lambda s, r=refusal: r(s)['envelope']['data']['request_failure'].update(expected_contract=RELEASE),
                [prefix + '.expected_identity'])
        if component == 'controller':
            refuse('refusal_' + name + '_client_capture',
                lambda s, r=refusal: r(s)['envelope']['data'].update(
                    runner_client=copy.deepcopy(envelope_of(s)['data']['runner_client'])),
                [prefix + '.no_delivery'])
            refuse('refusal_' + name + '_runner_reply',
                lambda s, r=refusal: r(s)['envelope']['data'].update(runner_result=copy.deepcopy(reply_of(s))),
                [prefix + '.no_delivery'])
        else:
            refuse('refusal_' + name + '_step_results',
                lambda s, r=refusal: r(s)['envelope']['data']['runner_result'].update(
                    steps=[copy.deepcopy(step_of(s))]),
                [prefix + '.host_reply'])
            refuse('refusal_' + name + '_reply_finished',
                lambda s, r=refusal: r(s)['envelope']['data']['runner_result'].update(normalized_outcome='finished'),
                [prefix + '.host_reply'])
            refuse('refusal_' + name + '_controller_refused',
                lambda s, r=refusal: r(s)['envelope']['data'].update(runner_client=None, runner_result=None),
                [prefix + '.host_reply'])
        refuse('refusal_' + name + '_input_unchanged', lambda s, r=refusal: r(s).update(input=s['example-1']['stdout']),
            [prefix + '.one_change'])
        refuse('refusal_' + name + '_input_second_change',
            lambda s, r=refusal: r(s).update(input=r(s)['input'].replace(b'"specimen_id"', b'"specimen_ID"')),
            [prefix + '.one_change'])
        refuse('refusal_' + name + '_input_absent', lambda s, r=refusal: r(s).update(input=None), [prefix + '.one_change'])
        refuse('refusal_' + name + '_input_of_another_refusal',
            lambda s, r=refusal, name=name: r(s).update(
                input=s['refusals']['unbound' if name != 'unbound' else 'other_release']['input']),
            [prefix + '.one_change'])

    refuse('refusal_other_development_two_digits',
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
    # The actor's own assessment is part of what is absent.
    without_actor_assessment = dict(per_form={'actor': {'also': ['structure.actor_ownership'],
        'conditions': {'structure.actor_ownership': ['diagnostics_actors']}}})
    add('readers_assessment_absent', lambda s: envelope_of(s)['data'].update(runner_sandbox_diagnostics=None),
        ['readers.disposition_integrity', 'readers.disposition_issues'], holds=('execution.admitted_reply',),
        recapture=False, **without_actor_assessment)
    add('readers_assessment_absent_and_result',
        lambda s: (envelope_of(s)['data'].update(runner_sandbox_diagnostics=None),
                   envelope_of(s)['result'].update(normalized_outcome='tool_error', ok=False, exit_code=0)),
        ['readers.disposition_integrity', 'readers.disposition_issues', 'consumer_validation'],
        holds=('execution.admitted_reply', 'reported.exit_code'), recapture=False, **without_actor_assessment)
    every_run = ('admission', 'identity', 'echo', 'reported', 'readers', 'structure', 'native.',
                 'passage.delivery_length')
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
         'native.targets_unchanged', 'passage.contract_matches_property_list'], rest_holds=True, forms=EMITTED)
    add('combined_prerequisite_and_consistency',
        lambda s: (before(s, 'A').update(readable=False, regular_file=False), reply_of(s).update(specimen_id='another')),
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


def selected(form, selector):
    """The rows of one form a selector names: an identifier, a group, or a prefix ending in a period."""
    return [ident for ident, group, _, _ in checker.table(form)
            if ident == selector or group == selector or (selector.endswith('.') and ident.startswith(selector))]


def judge(report, form, expected, *, conditions=None, unevaluated=(), holds=(), rest_holds=False, clean=False,
          exactly_consumer=False, derivatives_withheld=False, consumer_reports=None):
    """The ways a report differs from what a control states about one form. Empty when it matches."""
    problems = []
    actual = checker.diagnostics(report)
    wanted = triples(form, *expected)
    consumer_row = (form,) + CONSUMER
    permitted = set() if exactly_consumer or consumer_row in wanted else {consumer_row}
    if actual - permitted != wanted - permitted or not wanted <= actual:
        problems.append('diagnostics differ: missing ' + repr(sorted(wanted - actual)) +
                        ', unexpected ' + repr(sorted(actual - wanted - permitted)))
    statuses = {(row['form'], row['id']): row['status'] for row in report['assertions']}
    present = {ident for other, ident in statuses if other == form}
    withheld = set()
    for selector in unevaluated:
        assert any(selected(other, selector) for other in FORMS), selector
        chosen = selected(form, selector)
        withheld.update(chosen)
        problems.extend(f'{ident} is {statuses[form, ident]}, not unevaluated' for ident in chosen
                        if statuses[form, ident] != 'not_evaluated')
    holding = set(holds) & present
    if rest_holds:
        holding.update(ident for ident in present if ident not in withheld and ident != CONSUMER[0])
    problems.extend(f'{ident} is {statuses[form, ident]}, not holding' for ident in sorted(holding)
                    if statuses[form, ident] != 'pass' and ident not in expected)
    # A fault in one submission leaves the others as they were; a refused emission leaves none judged.
    for other in FORMS:
        if other == form:
            continue
        settled = 'not_evaluated' if derivatives_withheld else 'pass'
        wrong = sorted(ident for (found, ident), status in statuses.items() if found == other and status != settled)
        if wrong:
            problems.append(f'{other} rows are not {settled}: ' + ', '.join(wrong))
        if report['forms'][other]['consumer_errors']:
            problems.append(f'the consumer reports for {other}: ' + repr(report['forms'][other]['consumer_errors']))
    declared = checker.conditions(form)
    found = checker.failed_conditions(report)
    stated = {ident: names(form) if callable(names) else names for ident, names in (conditions or {}).items()}
    for ident, names in stated.items():
        if ident not in expected:
            problems.append(f'{ident} states conditions but is not an expected failing row')
        if ident not in declared:
            problems.append(f'{ident} states conditions but is not a declared conditioned row')
        elif names is not None:
            unknown = sorted(set(names) - set(declared[ident]))
            if unknown:
                problems.append(f'{ident} states undeclared conditions: {unknown!r}')
            if len(set(names)) != len(names):
                problems.append(f'{ident} repeats a stated condition')
    for ident in sorted(set(expected) & set(declared)):
        if stated.get(ident) is None:
            problems.append(f'{ident} is expected to fail and its failed conditions are not stated')
        elif sorted(found.get((form, ident), ())) != sorted(stated[ident]):
            problems.append(f'{ident} failed conditions {sorted(found.get((form, ident), ()))}, not {sorted(stated[ident])}')
    if clean and report['forms'][form]['consumer_errors']:
        problems.append('the consumer reports ' + repr(report['forms'][form]['consumer_errors']))
    if consumer_reports and not any(consumer_reports in error for error in report['forms'][form]['consumer_errors']):
        problems.append(f'the consumer does not report {consumer_reports!r}: ' + repr(report['forms'][form]['consumer_errors']))
    # A diagnostic must name its form, assertion and classification to a reader of the report alone.
    rendered = checker.render(report)
    for _, ident, classification in wanted:
        if f'FAIL {form} {ident} [{classification}]: ' not in rendered:
            problems.append(f'the rendered report does not name {form} {ident} [{classification}]')
    earned = [(ident, stated[ident][0]) for ident in sorted(set(expected) & set(declared))
              if stated.get(ident) is not None and len(stated[ident]) == 1]
    return problems, earned


def run_control(artifacts, row, form):
    state = build(row['identity'])
    view = capture(state, form)
    # A control changes the one submission it runs in; a few need another submission's bytes as well.
    row['change'](state if row['whole_state'] else view)
    if row['recapture'] and view.get('run') is not None and 'envelope' in view['run']:
        recapture_host_reply(view['run']['envelope'])
    directory = artifacts / 'captures' / form / row['name']
    write(directory, state)
    report = checker.evaluate(checker.load(directory), authored_fixture=True)
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    more = row['per_form'].get(form, {})
    expected = row['expected'] + tuple(more.get('also', ()))
    problems, earned = judge(report, form, expected, conditions=row['conditions'] | more.get('conditions', {}),
                             unevaluated=row['unevaluated'] + tuple(more.get('unevaluated', ())), holds=row['holds'],
                             rest_holds=row['rest_holds'], clean=row['clean'],
                             exactly_consumer=row['exactly_consumer'],
                             derivatives_withheld=row['derivatives_withheld'], consumer_reports=row['consumer_reports'])
    return {'control': row['name'], 'form': form, 'targets': sorted(row['targets']), 'expected': sorted(expected),
            'actual': sorted(map(list, checker.diagnostics(report))),
            'failed_conditions': {ident: list(names) for (found, ident), names in checker.failed_conditions(report).items()
                                  if found == form},
            'consumer_errors': report['consumer_errors'], 'matched': not problems, 'problems': problems,
            'earned_coverage': sorted(row['targets']) if not problems else [],
            'earned_conditions': [list(pair) for pair in earned] if not problems else []}


def evaluated(artifacts, name, state):
    """A constructed capture written as the live case leaves it and read through the checker."""
    for form in FORMS:
        recapture_host_reply(capture(state, form)['run']['envelope'])
    directory = artifacts / 'captures' / name
    write(directory, state)
    inputs = checker.load(directory)
    report = checker.evaluate(inputs, authored_fixture=True)
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return inputs, report


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
    emitted = serialized(document)
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
        ('version_build_identity', lambda s: s['version']['envelope']['build'].update(contract=RELEASE),
         ('passage.contract_matches_version',)),
        ('version_data_identity', lambda s: s['version']['envelope']['data'].update(contract=RELEASE),
         ('passage.contract_matches_version',)),
        ('version_unreadable', lambda s: s['version'].update(stdout=b'not JSON\n'),
         ('passage.contract_matches_version',)),
        ('property_list_identity', lambda s: s['property-list'].update(PWContract=RELEASE),
         ('passage.contract_matches_property_list',)),
        ('property_list_missing', lambda s: s.update({'property-list': None}),
         ('passage.contract_matches_property_list',)),
        ('snapshot_member', lambda s: s['contract-example']['document'].update(specimen_id='another'),
         ('passage.contract_rendering',)),
        ('snapshot_missing', lambda s: s.update({'contract-example': {'document': None}}),
         ('passage.contract_rendering',)),
        ('emissions_differ', lambda s: s['example-2'].update(stdout=b' ' + s['example-2']['stdout']),
         ('passage.emissions_identical',)),
        ('identity_absent', lambda s: set_document(s, lambda d: d.pop('contract')),
         ('passage.contract_matches_version', 'passage.contract_matches_property_list', 'passage.contract_packaged_form')),
        ('identity_unpackaged', lambda s: (s.clear(), s.update(build('test:unpackaged'))),
         ('passage.contract_packaged_form',)),
        ('bound_write_action',
         lambda s: set_document(s, lambda d: d['phases'][0]['actions'][0]['attempt'].update(action='open_write')),
         ('bounds.workload_roles', 'bounds.read_only_attempts')),
        ('bound_another_workload',
         lambda s: set_document(s, lambda d: d['phases'].reverse()), ('bounds.workload_roles', CONTAINER)),
        ('flat_emission', lambda s: set_document(s, lambda d: (d.update(probe_plan=checker.actions(d)), d.pop('phases'))),
         (CONTAINER,)),
        ('collapsed_partition', lambda s: set_document(s, lambda d: d.update(phases=[
            {'phase_id': 'one-phase', 'actions': checker.actions(d)}])), (CONTAINER,)),
        ('lost_action', lambda s: set_document(s, lambda d: d['phases'][0]['actions'].pop()),
         (CONTAINER, 'bounds.workload_roles')),
        ('bound_test_overrides', lambda s: set_document(s, lambda d: d.update(_test_overrides={})),
         ('bounds.no_test_overrides',)),
    ]:
        state = build()
        change(state)
        listed = state['property-list']
        plist = app / 'Contents/Info.plist'
        if listed is None:
            plist.unlink()
        else:
            plist.write_bytes(plistlib.dumps({'PWContract': listed['PWContract']}))
        snapshot = artifacts / 'captures' / ('prepare-' + name + '.snapshot.json')
        snapshot.write_text(json.dumps({'surfaces': [{'id': 'request', 'public': {'nodes': [
            {'id': checker.EXAMPLE_NODE, 'document': state['contract-example']['document']}]}}]}))
        # As the live case leaves the directory before `prepare`: the three invocations only.
        for key in ('run', 'property-list', 'contract-example', 'targets-before', 'targets-after'):
            state[key] = None
        state['refusals'], state['forms'] = {}, {}
        directory = artifacts / 'captures' / ('prepare-' + name)
        write(directory, state)
        status = checker.prepare(directory, app, snapshot)
        produced = sorted(path.relative_to(directory).as_posix() for path in directory.rglob('*') if path.is_file())
        runnable = [path for path in produced if path.startswith('refusals/') or path in ('flat/input.json', 'actor/input.json')]
        if failing:
            report = json.loads((directory / 'report.json').read_text())
            assert status == 1 and not runnable, (name, status, runnable)
            assert not any(path.endswith(('targets-before.json', 'targets-after.json', 'run.stdout'))
                           for path in produced), (name, produced)
            assert checker.diagnostics(report) == triples('emitted', *failing), (name, checker.diagnostics(report))
            assert all(row['status'] == 'not_evaluated' for row in report['assertions']
                       if row['group'] in RUN_GROUPS or row['form'] != 'emitted'), name
        else:
            assert status == 0 and 'report.json' not in produced, (name, status, produced)
            assert runnable == sorted(['flat/input.json', 'actor/input.json'] + [f'refusals/{refusal}/input.json' for refusal in REFUSALS]), runnable
            assert json.loads((directory / 'property-list.json').read_text())['PWContract'] == DEVELOPMENT
            assert json.loads((directory / 'contract-example.json').read_text())['document'] == \
                {key: value for key, value in document_of(state).items() if key != 'contract'}
            emitted = state['example-1']['stdout']
            for refusal in REFUSALS:
                submitted = (directory / 'refusals' / refusal / 'input.json').read_bytes()
                assert checker.one_change_problems(refusal, emitted, document_of(state), submitted) == [], refusal
            # What `prepare` wrote for each derivative is what the checker then judges: both transformations hold.
            source = json.loads(emitted)
            for form in ('flat', 'actor'):
                derived = json.loads((directory / form / 'input.json').read_bytes())
                assert checker.transformation_problems(source, derived, form) == [], form
        records.append({'control': 'prepare_' + name, 'status': status, 'failing': list(failing), 'files': produced})
    return records


def judgment_controls(artifacts):
    """All named conditions are checked, including names that cannot earn singleton coverage."""
    state = build()
    phase_of(state, 1)['completion_observed'] = False
    _, report = evaluated(artifacts, 'judgment_conditions', state)
    expected = {COLLECTIONS: ['phase1.completion_observed']}
    problems, earned = judge(report, 'emitted', [COLLECTIONS], conditions=expected, rest_holds=True)
    assert not problems and earned == [(COLLECTIONS, 'phase1.completion_observed')], (problems, earned)
    records = []
    for name, stated, diagnostic in (
        ('undeclared_alongside_declared', {COLLECTIONS: ['phase1.completion_observed', 'invented']},
         f"{COLLECTIONS} states undeclared conditions: ['invented']"),
        ('undeclared_row', dict(expected, invented=['one', 'two']),
         'invented states conditions but is not a declared conditioned row'),
        ('unexpected_conditioned_row', dict(expected, **{'structure.worker': ['reaped']}),
         'structure.worker states conditions but is not an expected failing row'),
        ('duplicated_condition', {COLLECTIONS: ['phase1.completion_observed'] * 2},
         f'{COLLECTIONS} repeats a stated condition'),
    ):
        problems, _ = judge(report, 'emitted', [COLLECTIONS], conditions=stated, rest_holds=True)
        assert diagnostic in problems, (name, problems)
        records.append({'control': name, 'required_diagnostic': diagnostic, 'problems': problems})
    return records


def observer_controls(artifacts):
    """The observer's sample describes the file it opened, whatever its path names afterwards.

    Each control runs the checker's observer on a file this case wrote, with
    an opener that changes what the path names as the open returns. The
    sample must carry the opened file's identity and content. The path is then read again here, by
    name, to show that an observer which went back to the path for either
    would have recorded something else.
    """
    directory = artifacts / 'captures' / 'observer'
    directory.mkdir(parents=True)
    opened_bytes = b'the file the observer opened\n' * 4
    placed_bytes = b'another file placed at that path afterwards\n' * 4
    assert opened_bytes[:BOUND] != placed_bytes[:BOUND] and len(opened_bytes) > BOUND

    def digests(content):
        return {'sha256': hashlib.sha256(content).hexdigest(), 'length': len(content),
                'prefix_sha256': hashlib.sha256(content[:BOUND]).hexdigest(), 'prefix_length': len(content[:BOUND])}

    def identity(status):
        return {'st_dev': status.st_dev, 'st_ino': status.st_ino}

    records = []
    for name in ('path_replaced_after_open', 'path_unlinked_after_open'):
        target, other = directory / (name + '.target'), directory / (name + '.other')
        target.write_bytes(opened_bytes)
        other.write_bytes(placed_bytes)
        opened, placed = identity(os.stat(target)), identity(os.stat(other))
        assert opened != placed, name
        calls = []

        def open_then_change(path, flags):
            descriptor = os.open(path, flags)
            calls.append(path)
            if name == 'path_replaced_after_open':
                os.replace(other, path)
            else:
                os.unlink(path)
            return descriptor
        sample_taken = checker.observe_target(str(target), opener=open_then_change)
        assert calls == [str(target)], (name, calls)
        problems = []
        if not (sample_taken['readable'] and sample_taken['regular_file'] and sample_taken['error'] is None):
            problems.append('the sample is not a read of a regular file: ' + repr(sample_taken['error']))
        found = {key: member_of(sample_taken, 'stat', key) for key in opened}
        if found != opened:
            problems.append(f'the sample carries identity {found}; the opened file has {opened}')
        found = {key: sample_taken.get(key) for key in digests(opened_bytes)}
        if found != digests(opened_bytes):
            problems.append(f'the sample carries {found}; the opened file holds {digests(opened_bytes)}')
        # What the path names now, read by name: another file, or nothing.
        if name == 'path_replaced_after_open':
            by_path = {'identity': identity(os.stat(target)), **digests(target.read_bytes())}
            assert by_path == {'identity': placed, **digests(placed_bytes)}, (name, by_path)
            assert by_path['identity'] != opened and all(
                by_path[key] != digests(opened_bytes)[key] for key in ('sha256', 'length', 'prefix_sha256')), name
        else:
            by_path = None
            assert not target.exists() and other.exists(), name
        records.append({'control': 'observer_' + name, 'opened': {'identity': opened, **digests(opened_bytes)},
                        'sample': sample_taken, 'path_afterwards': by_path, 'matched': not problems,
                        'problems': problems})
    # A path that names nothing supplies no sample, whatever opens it.
    absent = checker.observe_target(str(directory / 'absent'))
    assert absent['error'] and not absent['readable'] and not absent['regular_file'], absent
    return records


def member_of(record, *path):
    for key in path:
        record = record.get(key) if isinstance(record, dict) else None
    return record


def accepted_variants():
    """Alterations the checker must accept, each for a stated reason. Each is made in every form."""
    def short_target(view):
        # C shorter than the bound: the whole file is its bounded prefix.
        count = 10
        for sampled in (before, after):
            sampled(view, 'C').update(sample('C', sampled(view, 'C')['target']), length=count,
                                      sha256=hashlib.sha256(CONTENT['C'][:count]).hexdigest(),
                                      prefix_length=count, prefix_sha256=hashlib.sha256(CONTENT['C'][:count]).hexdigest())
            sampled(view, 'C')['stat']['st_size'] = count
        set_fresh(view, read_rc=count, content_hex=CONTENT['C'][:count].hex())
    return [
        # A descriptor is any nonnegative integer; zero is a successful open.
        ('fresh_open_returns_descriptor_0', lambda view: set_fresh(view, open_rc=0)),
        ('fresh_read_of_a_target_shorter_than_the_bound', short_target),
        # Steps 1 and 2 expect the same answer, so exchanging those two answers changes nothing
        # in the capture. This is the workload's stated blind spot, not a distinction it makes.
        ('answers_exchanged_1_2', lambda view: exchange_answers(view, 1, 2)),
    ]


def renamed():
    """Every label of the experiment changed consistently in each form's request and capture: names are labels."""
    state = build()

    def rename(value, mapping):
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, list):
            return [rename(item, mapping) for item in value]
        if isinstance(value, dict):
            return {key: rename(item, mapping) for key, item in value.items()}
        return value

    for form in FORMS:
        view = capture(state, form)
        document = document_of(view)
        mapping = {step['step_id']: f'renamed-{index}' for index, step in enumerate(checker.actions(document))}
        mapping.update({phase['phase_id']: f'renamed-phase-{index}' for index, phase in enumerate(document.get('phases', []))})
        mapping[ACTOR_LABEL] = 'renamed-reader'
        changed = rename(document, mapping)
        if form == 'emitted':
            set_document(state, lambda d: (d.clear(), d.update(changed)))
        else:
            set_input(view, lambda d: (d.clear(), d.update(changed)))
        view['run']['envelope'] = rename(view['run']['envelope'], mapping)
        for phase in reply_of(view)['phases']:
            for record in phase['validator_subprocess']['records']:
                record['raw_line'] = json.dumps(rename(json.loads(record['raw_line']), mapping), separators=(',', ':'))
        envelope_of(view)['data']['runner_client']['request_delivery']['bytes_written'] = len(submitted_of(view)) - 1
    state['refusals'] = {name: {'input': body, 'exit': 1, 'envelope': refusal_envelope(DEVELOPMENT, name), 'stderr': b''}
                         for name, body in checker.refusal_inputs(state['example-1']['stdout']).items()}
    return state


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
    _, report = evaluated(artifacts, 'uniform_answers', uniform)
    # The uniform capture is itself a reply the consumer reads cleanly; the present checker rejects
    # only step 3's own two expectations in it.
    assert not report['consumer_errors'], report['consumer_errors']
    assert checker.diagnostics(report) == triples('emitted', 'native.step3.prediction', 'native.step3.attempt'), \
        checker.diagnostics(report)
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


def shared_fault_controls(artifacts):
    """The same wrong answer in all three submissions fails each form's own expectation: no form vouches for another."""
    state = build()
    for form in FORMS:
        set_answer(capture(state, form), 3, ALLOW)
    _, report = evaluated(artifacts, 'shared_wrong_answer', state)
    wanted = set().union(*(triples(form, 'native.step3.prediction') for form in FORMS))
    assert checker.diagnostics(report) == wanted and not report['consumer_errors'], checker.render(report)
    assert all(row['status'] == 'pass' for row in report['assertions'] if row['id'] != 'native.step3.prediction')
    return [{'control': 'shared_wrong_answer', 'expected': sorted(map(list, wanted))}]


def table_controls(artifacts):
    """The workload's shape is the checker's one table: another table reads another partition, with no other change."""
    other = dict(checker.WORKLOAD, phases=(('step1',), ('step2', 'step3')))
    state = build(counts=(1, 2))
    for form in FORMS:
        recapture_host_reply(capture(state, form)['run']['envelope'])
    directory = artifacts / 'captures' / 'table_one_then_two'
    write(directory, state)
    inputs = checker.load(directory)
    under_other = checker.evaluate(inputs, authored_fixture=True, workload=other)
    assert under_other['status'] == 'pass' and not under_other['consumer_errors'] and \
        all(row['status'] == 'pass' for row in under_other['assertions']), checker.render(under_other)
    assert [(row['form'], row['id']) for row in under_other['assertions']] == \
        [(form, row[0]) for form in FORMS for row in checker.table(form, other)]
    # The same capture under the default table is another partition: its container refuses it and nothing is run.
    under_default = checker.evaluate(inputs, authored_fixture=True)
    problems, _ = judge(under_default, 'emitted', [CONTAINER],
                        conditions={CONTAINER: ['phase1.actions', 'phase2.actions']},
                        unevaluated=RUN_GROUPS + PREREQUISITES + ('passage.delivery_length',), rest_holds=True,
                        derivatives_withheld=True)
    assert not problems, problems
    # The committed contract snapshot holds the app's constant, as the drift suite requires. Standing in
    # for the emission, it passes the gate the live case runs before submitting, and `prepare` writes
    # derivatives of it that the transformation check accepts. Under the other table its container refuses it.
    snapshot = ROOT / 'docs/contract/public.json'
    request = next(row for row in json.loads(snapshot.read_text())['surfaces'] if row['id'] == 'request')
    example = next(node for node in request['public']['nodes'] if node['id'] == checker.EXAMPLE_NODE)['document']
    state = build()
    set_document(state, lambda d: (d.clear(), d.update(example, contract=DEVELOPMENT)))
    for key in ('run', 'property-list', 'contract-example', 'targets-before', 'targets-after'):
        state[key] = None
    state['refusals'], state['forms'] = {}, {}
    directory = artifacts / 'captures' / 'committed_snapshot_example'
    write(directory, state)
    app = artifacts / 'captures' / 'prepare-app'
    assert checker.prepare(directory, app, snapshot) == 0, 'the committed example is refused before submission'
    source = json.loads(state['example-1']['stdout'])
    for form in ('flat', 'actor'):
        derived = json.loads((directory / form / 'input.json').read_bytes())
        assert checker.transformation_problems(source, derived, form) == [], form
    refused = checker.evaluate(checker.load(directory), workload=other)
    assert checker.failed_conditions(refused) == {('emitted', CONTAINER): ('phase1.actions', 'phase2.actions')}, \
        checker.render(refused)
    return [{'control': 'table_one_then_two', 'passes_under': list(map(list, other['phases'])),
             'default_table_failed_conditions': ['phase1.actions', 'phase2.actions']},
            {'control': 'committed_snapshot_example', 'prepared': True,
             'steps': [step['step_id'] for step in checker.actions(example)]}]


def summary_controls(artifacts):
    """The diagnostic summary is made from a finished report and changes nothing in it."""
    inputs, report = evaluated(artifacts, 'summary_passing', build())
    assert 'diagnostic_summary' not in report
    kept = copy.deepcopy(report)
    summary = checker.diagnostic_summary(inputs, report)
    assert report == kept
    assert [entry['form'] for entry in summary] == list(FORMS) and all(len(entry['observations']) == 3 for entry in summary)
    # A form whose association is unestablished supplies no observations; the others still do.
    state = build()
    step_of(capture(state, 'flat'), 1).update(step_id='other-label')
    inputs, report = evaluated(artifacts, 'summary_flat_unassociated', state)
    kept = copy.deepcopy(report)
    summary = {entry['form']: entry for entry in checker.diagnostic_summary(inputs, report)}
    assert report == kept
    assert summary['flat']['observations'] is None and summary['flat']['withheld_reason']
    assert all(len(summary[form]['observations']) == 3 for form in ('emitted', 'actor'))
    return [{'control': 'summary_leaves_the_report_unchanged'}, {'control': 'summary_withheld_for_one_form'}]


def extension_policy_controls():
    # Distinct sources and opposite record orders expose a digest attributed to the wrong actor.
    sources = {'Alice': '(version 1)(allow default)', 'Bob': '(version 1)(deny default) ; café\n'}
    document = {'actors': []}
    dossiers, results = [], []
    for reader, source in sources.items():
        document['actors'].append({'actor_id': reader, 'sandbox': {'policy': {'sbpl_source': source}}})
        digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
        dossiers.append({'actor_id': reader, 'policy': {'augmentation': {
            'original_sha256': digest, 'applied_sha256': digest}}})
        results.append({'actor_id': reader, 'policy_sha256': digest, 'policy_received_sha256': digest})
    data = {'specimen': {'actors': dossiers}, 'runner_result': {'actors': results[::-1]}}
    assert reader_policy_mismatches(document, data) == {}
    data['specimen']['actors'] = dossiers[::-1]
    assert reader_policy_mismatches(document, data) == {}
    rejected = []
    for dossier, actor in zip(dossiers, results):
        reader = actor['actor_id']
        for record, field in ((dossier['policy']['augmentation'], 'original_sha256'),
                              (dossier['policy']['augmentation'], 'applied_sha256'),
                              (actor, 'policy_sha256'), (actor, 'policy_received_sha256')):
            expected = record[field]
            record[field] = '0' * 64
            key = f'{reader}.{field}'
            assert reader_policy_mismatches(document, data) == {
                key: {'submitted': expected, 'reported': record[field]}}
            record[field] = expected
            rejected.append(key)
    # All of Bob's reported digests can agree with one another and still describe Alice's source.
    dossiers[1]['policy'] = dossiers[0]['policy']
    for field in ('policy_sha256', 'policy_received_sha256'):
        results[1][field] = results[0][field]
    assert set(reader_policy_mismatches(document, data)) == {key for key in rejected if key.startswith('Bob.')}
    return {'single_field_mismatches': rejected, 'all_bob_digests_from_alice_rejected': True}


def main():
    artifacts = Path(sys.argv[1])
    if (artifacts / 'captures').exists():
        shutil.rmtree(artifacts / 'captures')
    # Qualify the complete authored actor envelope before its mutation controls.
    actor = bind_constructed_envelope(json.loads(ACTOR_FIXTURE.read_text()))
    errors = consumer.validate(actor, actor['build']['contract'], allow_fixture_json=True)
    assert not errors, errors
    from example_form_controls import controls as form_controls
    results = {'baselines': [], 'accepted_variants': [], 'controls': [], 'perturbations': perturbation_controls(),
               # `prepare` reads an app property list; the table control below uses the one written here.
               'prepare': prepare_controls(artifacts), 'observer': observer_controls(artifacts),
               'judgment': judgment_controls(artifacts),
               'uniform_answer_demonstration': uniform_answer_demonstration(artifacts),
               'table': table_controls(artifacts), 'summary': summary_controls(artifacts),
               'shared_fault': shared_fault_controls(artifacts), 'extension_policy': extension_policy_controls()}
    failures = [f'{record["control"]}: ' + '; '.join(record['problems'])
                for record in results['observer'] if not record['matched']]
    # Each form's table must carry the classification this case authors for each assertion.
    disagreeing = [f'{form} {ident}' for form in FORMS for ident, _, carried, _ in checker.table(form)
                   if carried != expected_classification(ident)]
    if disagreeing:
        failures.append('classification differs from this case\'s expectation: ' + ', '.join(disagreeing))
    # The selector controls below name every selection key the checker reads from the shape golden.
    if set(checker.RUNNER_SELECTION_KEYS) != {'runner', 'runner_id', 'runner_service', 'runner_mode'} or \
            checker.ENTITLEMENT_KEY not in checker.SELECTOR_FIELDS:
        failures.append('the controller selection keys changed; add a bounds control for each: ' +
                        ', '.join(checker.SELECTOR_FIELDS))

    def accepted(name, state):
        _, report = evaluated(artifacts, name, state)
        unsettled = [f'{row["form"]} {row["id"]}' for row in report['assertions'] if row['status'] != 'pass']
        if report['status'] != 'pass' or unsettled or report['consumer_errors']:
            failures.append(f'{name}: {checker.render(report)} {report["consumer_errors"]}')
        return report, {'status': report['status'], 'not_passing': unsettled, 'consumer_errors': report['consumer_errors']}

    required = None
    for identity in (DEVELOPMENT, RELEASE):
        report, record = accepted('baseline_' + identity.split(':')[0], build(identity))
        results['baselines'].append(dict(record, identity=identity))
        # What the live case reports: every row of the three-form report from the one `evaluate`.
        rows = [(row['form'], row['id']) for row in report['assertions']]
        assert required in (None, rows) and len(set(rows)) == len(rows)
        required = rows
    for name, change in accepted_variants():
        for form in FORMS:
            state = build()
            change(capture(state, form))
            results['accepted_variants'].append(dict(accepted(f'accepted_{form}_{name}', state)[1], variant=name, form=form))
    results['accepted_variants'].append(dict(accepted('accepted_consistent_renaming', renamed())[1],
                                             variant='consistent_renaming', form='all'))

    names = set()
    covered, conditions_covered = {}, {}
    for row in controls() + form_controls():
        assert row['name'] not in names, row['name']
        names.add(row['name'])
        assert row['targets'] and set(row['forms']) <= set(FORMS), row['name']
        for form in row['forms']:
            record = run_control(artifacts, row, form)
            results['controls'].append(record)
            if not record['matched']:
                failures.append(f'{form} {record["control"]}: ' + '; '.join(record['problems']))
            for ident in record['earned_coverage']:
                covered.setdefault((form, ident), []).append(record['control'])
            for ident, condition in record['earned_conditions']:
                conditions_covered.setdefault((form, ident, condition), []).append(record['control'])
    uncovered = [f'{form} {ident}' for form, ident in required if (form, ident) not in covered]
    declared = [(form, ident, condition) for form in FORMS for ident, names_ in checker.conditions(form).items()
                for condition in names_]
    unpinned = [f'{form} {ident} {condition}' for form, ident, condition in declared
                if (form, ident, condition) not in conditions_covered]
    undeclared = sorted(f'{form} {ident} {condition}' for form, ident, condition in conditions_covered
                        if (form, ident, condition) not in declared)
    results['coverage'] = {
        'rows': len(required),
        'covered': {f'{form} {ident}': covered[form, ident] for form, ident in required if (form, ident) in covered},
        'uncovered': uncovered,
        'conditions': len(declared),
        'conditions_covered': {f'{form} {ident} {condition}': conditions_covered[form, ident, condition]
                               for form, ident, condition in declared if (form, ident, condition) in conditions_covered},
        'conditions_unpinned': unpinned,
        'resting_on_other_evidence': [
            'Shape and record validity, ordering and the envelope-result relationship come from consumer.validate, '
            'whose rejected controls are blackbox_e2e/checker_controls; readers_consumer_propagation establishes '
            'only that a consumer error fails this case.',
            "That the app is validly signed and unchanged comes from the dispatcher's inspection and inventory, "
            'controlled in the dispatcher suite.'],
    }
    if uncovered:
        failures.append('rows without a matched rejected control in their form: ' + ', '.join(uncovered))
    if unpinned:
        failures.append('conditions without a matched control that fails them alone: ' + ', '.join(unpinned))
    if undeclared:
        failures.append('controls state conditions the checker does not declare: ' + ', '.join(undeclared))
    (artifacts / 'example-round-trip-controls.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'{len(results["controls"])} controls, {len(required) - len(uncovered)} of {len(required)} rows covered, '
          f'{len(declared) - len(unpinned)} of {len(declared)} conditions pinned', flush=True)
    if failures:
        raise SystemExit('\n'.join(failures))


if __name__ == '__main__':
    main()
