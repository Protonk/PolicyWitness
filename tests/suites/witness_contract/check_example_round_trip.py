#!/usr/bin/env python3
"""Check the passage of the app's own example from `example` through `run`.

The case supplies no specimen. The document is whatever the selected app
printed; this checker reads retained captures of the commands the case ran,
changes the printed bytes in one place for each refusal, observes every query
and attempt path itself, and reads the run envelope with the shared consumer.
Identity, digest and echo expectations are derived from the printed document
or another output of the same app. Shape, record, ordering and outcome-mapping
rules belong to the consumer and the controller; this file restates none of
them.

Two expectations are the case's own, and `WORKLOAD` below states both once.
The document must be that read-only workload, found by the relationships among
its submitted operands and never by a label or a path. Under observed
prerequisites the native results must then meet the answers and attempt
results pinned there to the present example, each answer before its attempt,
with a finished run whose process exits 0 and unchanged targets; a successful
fresh read must carry the descriptor identity, count and bytes this checker
observed for its target. The policy source is not read to decide any of this.
Each step's answer and attempt are separate assertions. Nothing here compares
an answer with its attempt, states that they agree or assigns a failure to the
policy.

The emitted document is submitted unchanged, and so are two derivatives this
case writes: a flat form and a single-actor form. Each submission is one form
with its own rows. A row has a form, a stable identifier, one group and one
classification; a failure prints all of them, and `report.json` holds every
row's result, with consistency apart from native observations. A row built
from several conditions names the ones that failed.

    prepare CAPTURE APP SNAPSHOT      gate the emission and write checked derivatives/refusals
    observe CAPTURE FORM before|after sample the selected submission
    evaluate CAPTURE                  read all three retained captures and report
"""
import argparse
import copy
import hashlib
import json
import os
import plistlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
import file_observation

CONSISTENCY = 'consistency'
EXECUTION_UNAVAILABLE = 'execution_unavailable'
PREREQUISITE_UNESTABLISHED = 'prerequisite_unestablished'
NATIVE_OBSERVATION = 'native_observation'

EXAMPLE_NODE = 'request.specimen.example'
PACKAGED_IDENTITY = re.compile(r'release:v[0-9]+\.[0-9]+\.[0-9]+|development:[0-9a-f]{64}')
READ_ONLY_FILE_ACTIONS = ('open_read', 'access', 'read_fresh')
# The most bytes one `read_fresh` reads, as the step-result surface documents it. Authored here.
FRESH_READ_BOUND = 64
EPERM = 1
# The one statement of this workload's shape. `phases` partitions the roles in
# emitted order. Each role names its query operation and its attempt action with
# the target each concerns, the answer pinned to the present example and the
# attempt result pinned to it. A target letter is a relationship among submitted
# paths: one letter is one path and two letters are two paths.
WORKLOAD = {
    'phases': (('step1', 'step2'), ('step3',)),
    'roles': {
        'step1': {'query': ('file-read-data', 'A'), 'attempt': ('open_read', 'A'),
                  'answer': {'outcome': 'allow', 'native_rc': 0}, 'result': {'outcome': 'ok', 'rc': 0}},
        'step2': {'query': ('file-read-metadata', 'B'), 'attempt': ('read_fresh', 'C'),
                  'answer': {'outcome': 'allow', 'native_rc': 0}, 'result': {'outcome': 'ok', 'rc': 0}},
        'step3': {'query': ('file-read-data', 'B'), 'attempt': ('open_read', 'B'),
                  'answer': {'outcome': 'deny', 'native_rc': 1, 'errno': 0},
                  'result': {'outcome': 'open_failed', 'errno': EPERM}},
    },
}
FORMS = ('emitted', 'flat', 'actor')
FRESH_ACTION = 'read_fresh'
# The controller's selection keys, from the request surface's shape golden (collected from `runner_select.rs`).
SELECTOR_FIELDS = tuple(json.loads((Path(__file__).resolve().parents[2] / 'fixtures/contract/surfaces/request.json')
                                   .read_text())['controller_keys']['SELECTOR_FIELDS'])
ENTITLEMENT_KEY = 'required_entitlements'
RUNNER_SELECTION_KEYS = tuple(key for key in SELECTOR_FIELDS if key != ENTITLEMENT_KEY)
UNKNOWN_MEMBER = 'example_round_trip_unknown_member'
STAT_FIELDS = file_observation.STAT_FIELDS

# Each refusal: the request-failure code and path `run` must report, whether
# the failure names the expected identity, and which component refuses.
REFUSALS = {
    'other_development': ('unsupported_contract', ['contract'], True, 'controller'),
    'other_release': ('unsupported_contract', ['contract'], True, 'controller'),
    'unbound': ('unsupported_contract', ['contract'], True, 'controller'),
    'absent_identity': ('missing_field', ['contract'], True, 'controller'),
    'truncated_document': ('invalid_json', [], False, 'controller'),
    'unknown_member': ('unknown_field', [UNKNOWN_MEMBER], False, 'host'),
}


def step_text(workload, role):
    """One role in words, from the table."""
    (operation, queried), (action, target) = workload['roles'][role]['query'], workload['roles'][role]['attempt']
    number = list(workload['roles']).index(role) + 1
    return f'step {number} (`{operation}` query on target {queried} beside `{action}` of target {target})'


def target_roles(workload):
    """The target letters in order of first use."""
    letters = []
    for spec in workload['roles'].values():
        for letter in (spec['query'][1], spec['attempt'][1]):
            if letter not in letters:
                letters.append(letter)
    return tuple(letters)


def target_text(workload, letter):
    uses = []
    for number, spec in enumerate(workload['roles'].values(), 1):
        if spec['query'][1] == letter:
            uses.append(f"step {number}'s `{spec['query'][0]}` query")
        if spec['attempt'][1] == letter:
            uses.append(f"step {number}'s `{spec['attempt'][0]}`")
    return 'the target of ' + ' and '.join(uses)


def fresh_roles(workload):
    """The roles whose attempt is a fresh read, with the target each reads."""
    return {role: spec['attempt'][1] for role, spec in workload['roles'].items() if spec['attempt'][0] == FRESH_ACTION}


def _spelled(expected):
    return ', '.join(f'`{key}` {json.dumps(value)}' for key, value in expected.items())


def _native_rows(workload):
    rows = [
        ('native.process_status', 'native', NATIVE_OBSERVATION,
         'the captured exit status of the `run` process is 0, whatever the envelope reports'),
        ('native.completion', 'native', NATIVE_OBSERVATION, "the reply's `normalized_outcome` is `finished`"),
    ]
    for role, spec in workload['roles'].items():
        rows.append((f'native.{role}.prediction', 'native', NATIVE_OBSERVATION,
                     f'{step_text(workload, role)}: the answer about {spec["query"][1]} is a validator answer with '
                     + _spelled(spec['answer'])))
    rows.append(('native.order', 'native', NATIVE_OBSERVATION,
                 'each step whose answer met its expectation records `order` `query_first`'))
    for role, spec in workload['roles'].items():
        rows.append((f'native.{role}.attempt', 'native', NATIVE_OBSERVATION,
                     f'{step_text(workload, role)}: the `{spec["attempt"][0]}` of {spec["attempt"][1]} is a worker '
                     'result with ' + _spelled(spec['result'])))
        if role in fresh_roles(workload):
            letter = spec['attempt'][1]
            rows.append((f'native.{role}.fresh_syscalls', 'native', NATIVE_OBSERVATION,
                         f'{step_text(workload, role)}: the open returned a descriptor, and the descriptor stat, '
                         'the bounded read and the close each succeeded'))
            rows.append((f'native.{role}.fresh_identity', 'native', NATIVE_OBSERVATION,
                         f"{step_text(workload, role)}: the descriptor's device and inode are those this checker "
                         f'observed for {letter}'))
            rows.append((f'native.{role}.fresh_content', 'native', NATIVE_OBSERVATION,
                         f"{step_text(workload, role)}: the read count and the bytes read are the length and digest "
                         f"of {letter}'s bounded prefix as this checker observed it"))
    rows.append(('native.targets_unchanged', 'native', NATIVE_OBSERVATION,
                 "each target's digest, length, bounded prefix and selected metadata are equal before and after the run"))
    return rows


def _publication_rows(workload):
    letters = ', '.join(target_roles(workload))
    rows = [
        ('emission.version_exit', 'emission', CONSISTENCY, '`--version` exits 0'),
        ('emission.example_exit', 'emission', CONSISTENCY, 'both `example` invocations exit 0'),
        ('emission.stderr_empty', 'emission', CONSISTENCY, 'both emissions leave stderr empty'),
        ('emission.json_object', 'emission', CONSISTENCY, 'each emission is one JSON object'),
        ('emission.framing_newline', 'emission', CONSISTENCY, 'each emission ends with exactly one LF'),
        ('passage.contract_matches_version', 'passage', CONSISTENCY,
         'the document asserts the identity `--version` reports under `build` and `data`'),
        ('passage.contract_matches_property_list', 'passage', CONSISTENCY,
         "the document asserts the app property list's `PWContract`"),
        ('passage.contract_packaged_form', 'passage', CONSISTENCY,
         'the identity has a packaged `release:` or `development:` form'),
        ('passage.emissions_identical', 'passage', CONSISTENCY, 'two emissions are byte-identical'),
        ('passage.contract_rendering', 'passage', CONSISTENCY,
         "the document without `contract` equals the contract snapshot's example"),
        ('bounds.ordinary_form', 'bounds', CONSISTENCY,
         'the document is ordinary phases with action counts ' +
         ' and '.join(str(len(phase)) for phase in workload['phases'])),
        ('bounds.workload_roles', 'bounds', CONSISTENCY,
         f'the document holds {len(workload["roles"])} steps: ' +
         '; '.join(step_text(workload, role) for role in workload['roles']) +
         f'; {letters} are different submitted paths'),
        ('bounds.read_only_attempts', 'bounds', CONSISTENCY, 'every attempt is a read-only file action'),
        ('bounds.no_test_overrides', 'bounds', CONSISTENCY, 'the document carries no `_test_overrides`'),
        ('bounds.no_runner_selection', 'bounds', CONSISTENCY, 'the document carries no runner selection field'),
        ('bounds.no_augments', 'bounds', CONSISTENCY, 'the policy names no augments'),
        ('bounds.no_entitlement_requirement', 'bounds', CONSISTENCY, 'the document requires no entitlement'),
    ]
    for name, (code, path, identity, component) in REFUSALS.items():
        prefix = 'refusal.' + name
        rows.append((prefix + '.one_change', 'refusals', CONSISTENCY,
                     'the submitted input is the document with this one change'))
        rows.append((prefix + '.refused', 'refusals', CONSISTENCY, '`run` exits 1 with `bad_request`'))
        rows.append((prefix + '.failure', 'refusals', CONSISTENCY,
                     f'`request_failure` has code `{code}` and path {json.dumps(path)}'))
        if identity:
            rows.append((prefix + '.expected_identity', 'refusals', CONSISTENCY,
                         "`request_failure.expected_contract` is the app's identity"))
        if component == 'controller':
            rows.append((prefix + '.no_delivery', 'refusals', CONSISTENCY,
                         'the refusal has no client capture and no runner reply'))
        else:
            rows.append((prefix + '.host_reply', 'refusals', CONSISTENCY,
                         'the host replies `bad_request` with no step results'))
    return rows


def _execution_rows(workload):
    letters = target_roles(workload)
    fresh = sorted(set(fresh_roles(workload).values()))
    return [
        ('passage.delivery_length', 'passage', CONSISTENCY,
         "`request_delivery.bytes_written` is the submitted document's length without its framing newline"),
        ('admission.no_request_failure', 'admission', CONSISTENCY,
         'the run reports no `request_failure` and no `bad_request` outcome'),
        ('admission.dossier_policy_digest', 'admission', CONSISTENCY,
         "the dossier's original policy digest is the SHA-256 of the submitted policy source"),
        ('admission.reply_policy_digest', 'admission', CONSISTENCY,
         "the reply's `policy_sha256` is the SHA-256 of the submitted policy source"),
        ('identity.envelope_build', 'identity', CONSISTENCY, "the run envelope's `build.contract` is the document's"),
        ('identity.client_transport', 'identity', CONSISTENCY, "the client capture's `contract` is the document's"),
        ('identity.reply_producer', 'identity', CONSISTENCY, "the reply's `producer.contract` is the document's"),
        ('execution.admitted_reply', 'execution', EXECUTION_UNAVAILABLE, 'the run yields an admitted runner reply'),
        ('echo.specimen_id', 'echo', CONSISTENCY, "the reply echoes the document's `specimen_id`"),
        ('echo.step_ids', 'echo', CONSISTENCY, "the reply's step identifiers are the document's, in order"),
        ('echo.queries', 'echo', CONSISTENCY, 'each query echoes its submitted operation and filter'),
        ('echo.attempts', 'echo', CONSISTENCY, 'each attempt echoes its submitted kind, action and target'),
        ('reported.exit_code', 'reported', CONSISTENCY, 'the captured process exit status equals `result.exit_code`'),
        ('consumer_validation', 'readers', CONSISTENCY, 'the shared consumer reports no error'),
        ('readers.disposition_integrity', 'readers', CONSISTENCY, "the controller's `disposition_integrity` is `valid`"),
        ('readers.disposition_issues', 'readers', CONSISTENCY, 'the controller reports no `disposition_issues`'),
        ('prerequisite.targets_readable', 'native', PREREQUISITE_UNESTABLISHED,
         f'targets {", ".join(letters)} are each a regular file the test user opened and read before the run'),
        ('prerequisite.distinct_identities', 'native', PREREQUISITE_UNESTABLISHED,
         f'targets {", ".join(letters)} have {len(letters)} distinct device and inode identities'),
        ('prerequisite.distinguishing_prefixes', 'native', PREREQUISITE_UNESTABLISHED,
         "each target's bounded prefix is nonempty, and the prefix of " + ' and of '.join(fresh) +
         " differs from every other target's"),
    ] + _native_rows(workload)


def preparation_rows(workload=WORKLOAD):
    """Assertions established before observing targets or submitting any request."""
    return tuple(ident for ident, group, _, _ in _publication_rows(workload) if group != 'refusals')


STRUCTURE_ROWS = (
    ('structure.execution_form', 'structure', CONSISTENCY, 'the reply uses the submitted execution form'),
    ('structure.phase_membership', 'structure', CONSISTENCY,
     'reply phases retain the exact submitted phase/action partition and order'),
    ('structure.collections', 'structure', CONSISTENCY,
     'each submitted phase has its own complete collection and release chain'),
    ('structure.worker', 'structure', CONSISTENCY,
     'the submitted worker was applied, completed and reaped under its owned process record'),
)
ACTOR_ROWS = (
    ('structure.actor_ownership', 'structure', CONSISTENCY,
     'the submitted actor owns every visit, every step and its controller projections'),
    ('structure.actor_application', 'structure', CONSISTENCY,
     'the actor applied the submitted policy once and received its source digest'),
    ('structure.actor_equipment', 'structure', CONSISTENCY,
     'the actor used selected equipment matched to its launched worker'),
)
TRANSFORMATION_ROWS = {
    'flat': ('transformation', 'transformation', CONSISTENCY,
             'the flat derivative changes only phases into the ordered probe_plan'),
    'actor': ('transformation', 'transformation', CONSISTENCY,
              'the actor derivative relocates the entire policy to one applied selected actor and assigns every phase'),
}


def table(form, workload=WORKLOAD):
    """The rows of one form's report, in order: (identifier, group, classification, statement)."""
    if form == 'emitted':
        rows = _publication_rows(workload) + _execution_rows(workload)
    else:
        rows = [TRANSFORMATION_ROWS[form]] + _execution_rows(workload)
    return tuple(rows) + STRUCTURE_ROWS + (ACTOR_ROWS if form == 'actor' else ())


def _phase_names(count, *names):
    return tuple(f'phase{number}.{name}' for number in range(1, count + 1) for name in names)


def conditions(form, workload=WORKLOAD):
    """The named conditions of each conditioned row in one form. A failing row reports the names that failed."""
    phases = len(workload['phases'])
    replied = 1 if form == 'flat' else phases
    roles = tuple(workload['roles'])
    worker = ('pid', 'reaped', 'ready_byte_received', 'done_observed', 'exit_code', 'term_signal', 'collection_basis')
    declared = {
        'structure.execution_form': ('execution_form',),
        'structure.phase_membership': ('phase_count',) + _phase_names(replied, 'phase_id', 'ordinal', 'action_ids'),
        'structure.collections': _phase_names(
            replied, 'unique', 'arrival_observed', 'completion_observed', 'collection_status', 'validator_reaped',
            'collection_closed_before_proceed', 'proceed_set', 'proceed_observed', 'worker_lifetime_established',
            'validator_disposition', 'protocol_violations', 'expected_step_ids'),
        'structure.worker': (('applied', 'launch_pid', 'launch_parent_pid') if form == 'actor' else
                             ('applied', 'reply_pid')) + worker,
    }
    if form == 'emitted':
        declared['bounds.ordinary_form'] = ('phases',) + _phase_names(phases, 'members', 'phase_id', 'actions') + \
            ('distinct_phase_ids', 'no_probe_plan', 'no_actors')
    if form == 'flat':
        declared['transformation'] = ('members', 'preserved', 'actions') + tuple(f'action.{role}' for role in roles)
    if form == 'actor':
        declared['transformation'] = ('members', 'preserved', 'actors', 'actor.members', 'actor.actor_id',
                                      'actor.equipment', 'actor.sandbox.members', 'actor.sandbox.mode',
                                      'actor.sandbox.policy', 'phases') + \
            _phase_names(phases, 'members', 'actor_id', 'preserved')
        declared['structure.actor_ownership'] = ('reply_actors', 'diagnostics_actors', 'dossier_actors', 'visits') + \
            _phase_names(phases, 'actor_id', 'actor_visit', 'no_termination_gate') + \
            tuple(f'step.{role}.actor_id' for role in roles) + \
            ('unsubmitted_steps.actor_id', 'diagnostics.disposition_integrity', 'diagnostics.disposition_issues')
        declared['structure.actor_application'] = ('mode', 'setup_status', 'applied', 'application_count',
                                                   'application', 'policy_received_sha256')
        declared['structure.actor_equipment'] = ('requested', 'resolved', 'required_entitlements',
                                                 'requirements_status', 'execution.status', 'execution.eligible',
                                                 'execution.pid')
    return declared


def actions(document):
    """Submitted actions in order; never normalize a reply into another form."""
    if isinstance(document.get('probe_plan'), list):
        return document['probe_plan']
    phases = document.get('phases')
    return [step for phase in phases if isinstance(phase, dict) and isinstance(phase.get('actions'), list)
            for step in phase['actions']] if isinstance(phases, list) else []


def submitted_policy(document, form):
    if form == 'actor':
        actors = document.get('actors')
        return _get(actors[0], 'sandbox', 'policy') or {} if isinstance(actors, list) and len(actors) == 1 else {}
    return document.get('policy') or {}


# ---------------------------------------------------------------------------
# Retained captures
# ---------------------------------------------------------------------------

def _bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError:
        return None


def _exit(path):
    raw = _bytes(path)
    try:
        return int(raw.decode().strip()) if raw is not None else None
    except ValueError:
        return None


def _json(raw):
    """A parsed JSON value, or the reason it is unavailable."""
    if raw is None:
        return None, 'the capture is absent'
    try:
        return json.loads(raw.decode('utf-8')), None
    except (UnicodeDecodeError, ValueError) as error:
        return None, f'not JSON: {error}'


def _invocation(directory, name):
    directory = Path(directory)
    return {'stdout': _bytes(directory / (name + '.stdout')), 'stderr': _bytes(directory / (name + '.stderr')),
            'exit': _exit(directory / (name + '.exit'))}


def load(directory):
    """Every retained input, absent ones as None. Nothing is interpreted here."""
    directory = Path(directory)
    inputs = {name: _invocation(directory, name) for name in ('version', 'example-1', 'example-2', 'run')}
    for name in ('property-list', 'contract-example', 'targets-before', 'targets-after'):
        inputs[name] = _json(_bytes(directory / (name + '.json')))[0]
    inputs['forms'] = {}
    for form in ('flat', 'actor'):
        base = directory / form
        inputs['forms'][form] = {'input': _bytes(base / 'input.json'), 'run': _invocation(base, 'run')}
        for name in ('targets-before', 'targets-after'):
            inputs['forms'][form][name] = _json(_bytes(base / (name + '.json')))[0]
    inputs['refusals'] = {}
    for name in REFUSALS:
        base = directory / 'refusals' / name
        inputs['refusals'][name] = dict(_invocation(base, 'run'), input=_bytes(base / 'input.json'))
    return inputs


# ---------------------------------------------------------------------------
# The produced bytes, changed in one place
# ---------------------------------------------------------------------------

def refusal_inputs(emitted):
    """Each refusal's input: the emitted bytes with exactly one change.

    Where the change can be made in the bytes it is: the identity's one
    encoded occurrence is replaced, a member is inserted before the closing
    brace, or the closing brace is removed. Removing the identity, or
    replacing one that does not occur exactly once, re-serializes the parsed
    document with that one member changed.
    """
    document = json.loads(emitted.decode('utf-8'))
    contract = document['contract']
    encoded = json.dumps(contract, ensure_ascii=False).encode('utf-8')
    body = emitted[:-1]
    assert emitted.endswith(b'\n') and body.rstrip() == body and body.endswith(b'}')

    def reserialized(change):
        changed = json.loads(emitted.decode('utf-8'))
        change(changed)
        return (json.dumps(changed, indent=2, ensure_ascii=False) + '\n').encode('utf-8')

    def with_contract(value):
        replacement = json.dumps(value, ensure_ascii=False).encode('utf-8')
        if emitted.count(encoded) == 1:
            return emitted.replace(encoded, replacement)
        return reserialized(lambda changed: changed.update(contract=value))

    if contract.startswith('development:') and re.fullmatch(r'[0-9a-f]{64}', contract[12:]):
        last = contract[-1]
        other = contract[:-1] + ('0' if last != '0' else '1')
    else:
        other = 'development:' + '0' * 64
    return {
        'other_development': with_contract(other),
        'other_release': with_contract('release:v0.0.0'),
        'unbound': with_contract('unbound'),
        'absent_identity': reserialized(lambda changed: changed.pop('contract')),
        'truncated_document': body[:-1] + b'\n',
        'unknown_member': body[:-1].rstrip() + b',\n  ' + json.dumps(UNKNOWN_MEMBER).encode() + b': true\n}\n',
    }


# ---------------------------------------------------------------------------
# Observations the case makes itself
# ---------------------------------------------------------------------------

def workload_roles(document, workload=WORKLOAD):
    """The step identifiers and targets of the table's roles, or the reasons the document is another workload.

    Roles are positions and relationships among submitted operands. No step
    identifier, path or policy text decides one.
    """
    roles = workload['roles']
    steps = actions(document)
    if len(steps) != len(roles) or any(not isinstance(step, dict) for step in steps):
        return None, [f'the document holds {len(steps)} step(s) where this workload has {len(roles)}']

    def half(step):
        query, attempt = step.get('sandbox_check'), step.get('attempt')
        path = _get(query, 'filter', 'value') if _get(query, 'filter', 'kind') == 'path' else None
        action = _get(attempt, 'action') if _get(attempt, 'kind') == 'file' else None
        target = _get(attempt, 'target')
        return (_get(query, 'operation'), path if isinstance(path, str) else None, action,
                target if isinstance(target, str) else None)

    found = [half(step) for step in steps]
    problems = []
    for number, (spec, (operation, path, action, target)) in enumerate(zip(roles.values(), found), 1):
        wanted_operation, wanted_action = spec['query'][0], spec['attempt'][0]
        if not (operation == wanted_operation and action == wanted_action and None not in (path, target)):
            problems.append(f'step {number} is not a `{wanted_operation}` path query with a `{wanted_action}` of a file')
    identifiers = [step.get('step_id') for step in steps]
    if any(not isinstance(ident, str) for ident in identifiers) or len(set(identifiers)) != len(roles):
        problems.append(f'the step identifiers are not {len(roles)} distinct strings')
    targets = {}
    if not problems:
        # One letter is one submitted path, and two letters are two, within a step and across steps.
        for number, (spec, (_, path, _, target)) in enumerate(zip(roles.values(), found), 1):
            for letter, submitted in ((spec['query'][1], path), (spec['attempt'][1], target)):
                if targets.setdefault(letter, submitted) != submitted:
                    problems.append(f'step {number} does not use the one path target {letter} names')
        for letter, submitted in targets.items():
            others = [other for other, value in targets.items() if other < letter and value == submitted]
            if others and not problems:
                problems.append(f'targets {others[0]} and {letter} are one submitted path')
    if problems:
        return None, problems
    return {'steps': dict(zip(roles, identifiers)), 'targets': {letter: targets[letter] for letter in target_roles(workload)}}, []


def observed_paths(document):
    """Every submitted query path and attempt target, each once, in order of appearance."""
    paths = []
    for step in actions(document):
        if not isinstance(step, dict):
            continue
        for path in (_get(step.get('sandbox_check'), 'filter', 'value'), _get(step.get('attempt'), 'target')):
            if isinstance(path, str) and path not in paths:
                paths.append(path)
    return paths


def observe_target(target, opener=os.open):
    return file_observation.observe_target(target, FRESH_READ_BOUND, opener=opener)


def observe(directory, name, document):
    path = Path(directory) / (name + '.json')
    path.write_text(json.dumps({'targets': [observe_target(t) for t in observed_paths(document)]}, indent=2) + '\n')


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class Results:
    """One form's rows. A conditioned row is recorded with the names of its failed conditions."""

    def __init__(self, form, workload):
        self.form = form
        self.table = table(form, workload)
        self.identifiers = {row[0] for row in self.table}
        self.declared = conditions(form, workload)
        self.rows = {}

    def record(self, ident, problems, passed=None):
        """`problems` is a list of explanations; empty means the assertion holds."""
        assert ident in self.identifiers and ident not in self.rows and ident not in self.declared, ident
        problems = [problems] if isinstance(problems, str) else list(problems)
        self.rows[ident] = {'status': 'fail' if problems else 'pass', 'explanation': '; '.join(problems) or passed}

    def conditions(self, ident, failed):
        """`failed` is a list of (condition name, explanation); empty means every condition holds."""
        assert ident in self.identifiers and ident not in self.rows, ident
        names = [name for name, _ in failed]
        assert set(names) <= set(self.declared[ident]) and len(set(names)) == len(names), (ident, names)
        self.rows[ident] = {'status': 'fail' if failed else 'pass', 'conditions': names,
                            'explanation': '; '.join(f'{name}: {text}' for name, text in failed) or None}

    def unevaluated(self, ident, reason):
        assert ident in self.identifiers and ident not in self.rows, ident
        self.rows[ident] = {'status': 'not_evaluated', 'explanation': reason}
        if ident in self.declared:
            self.rows[ident]['conditions'] = None

    def status(self, ident):
        return self.rows.get(ident, {}).get('status')

    def failed(self, *identifiers):
        return any(self.status(ident) == 'fail' for ident in identifiers)

    def rest(self, group_or_prefix, reason):
        for ident, group, _, _ in self.table:
            if ident not in self.rows and (group == group_or_prefix or ident.startswith(group_or_prefix)):
                self.unevaluated(ident, reason)

    def remaining(self, reason):
        for ident, _, _, _ in self.table:
            if ident not in self.rows:
                self.unevaluated(ident, reason)


class _Conditions:
    """Collects the failed conditions of one row."""

    def __init__(self):
        self.failed = []

    def require(self, name, holds, text):
        if not holds:
            self.failed.append((name, text))
        return holds


def _spell(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _get(value, *path):
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _emission(inputs, results):
    """Emission requirements; returns the first emission's bytes and document when usable."""
    results.record('emission.version_exit',
                   [] if inputs['version']['exit'] == 0 else f'`--version` exit status is {_spell(inputs["version"]["exit"])}')
    exits, stderr, objects, framing, documents = [], [], [], [], {}
    for name in ('example-1', 'example-2'):
        invocation = inputs[name]
        if invocation['exit'] != 0:
            exits.append(f'{name} exit status is {_spell(invocation["exit"])}')
        if invocation['stderr'] != b'':
            stderr.append(f'{name} stderr is ' + ('absent' if invocation['stderr'] is None else
                                                    f'{len(invocation["stderr"])} bytes'))
        value, problem = _json(invocation['stdout'])
        if problem or not isinstance(value, dict):
            objects.append(f'{name} stdout is ' + (problem or f'a JSON {type(value).__name__}, not an object'))
        else:
            documents[name] = value
        raw = invocation['stdout'] or b''
        if not raw.endswith(b'\n') or raw[:-1] != raw[:-1].rstrip():
            framing.append(f'{name} stdout ends with {raw[-2:]!r}')
    results.record('emission.example_exit', exits)
    results.record('emission.stderr_empty', stderr)
    results.record('emission.json_object', objects)
    results.record('emission.framing_newline', framing)
    return inputs['example-1']['stdout'], documents.get('example-1')


def _bounds(document, results, workload):
    counts = [len(phase) for phase in workload['phases']]
    form = _Conditions()
    phases = document.get('phases')
    listed = phases if isinstance(phases, list) else []
    form.require('phases', isinstance(phases, list) and len(phases) == len(counts),
                 f'`phases` is not an array of {len(counts)} phases')
    for number, (phase, count) in enumerate(zip(listed, counts), 1):
        if not form.require(f'phase{number}.members', isinstance(phase, dict) and set(phase) == {'phase_id', 'actions'},
                            'the phase is not an object with exactly `phase_id` and `actions`'):
            continue
        form.require(f'phase{number}.phase_id', isinstance(phase['phase_id'], str) and bool(phase['phase_id']),
                     f'`phase_id` is {_spell(phase["phase_id"])}')
        form.require(f'phase{number}.actions', isinstance(phase['actions'], list) and len(phase['actions']) == count,
                     f'`actions` does not hold {count} action(s)')
    named = [phase.get('phase_id') for phase in listed if isinstance(phase, dict)]
    if len(named) == len(listed) and all(isinstance(ident, str) for ident in named):
        form.require('distinct_phase_ids', len(set(named)) == len(named), 'two phases share an identifier')
    form.require('no_probe_plan', 'probe_plan' not in document, 'the document carries `probe_plan`')
    form.require('no_actors', document.get('actors') is None, 'the document carries `actors`')
    results.conditions('bounds.ordinary_form', form.failed)
    steps = [step for step in actions(document) if isinstance(step, dict)]

    def read_only(attempt):
        return isinstance(attempt, dict) and attempt.get('kind') == 'file' and attempt.get('action') in READ_ONLY_FILE_ACTIONS

    roles, problems = workload_roles(document, workload)
    results.record('bounds.workload_roles', problems)
    results.record('bounds.read_only_attempts',
                   [f'step {_spell(step.get("step_id"))} attempts {_spell(step.get("attempt"))}'
                    for step in steps if 'attempt' in step and not read_only(step['attempt'])])
    results.record('bounds.no_test_overrides', ['`_test_overrides` is present'] if '_test_overrides' in document else [])
    results.record('bounds.no_runner_selection', [f'`{key}` is present' for key in RUNNER_SELECTION_KEYS if key in document])
    policy = document.get('policy')
    results.record('bounds.no_augments',
                   ['`policy.augments` is ' + _spell(policy['augments'])] if isinstance(policy, dict) and policy.get('augments') else [])
    entitlement = []
    if ENTITLEMENT_KEY in document:
        entitlement.append(f'`{ENTITLEMENT_KEY}` is present')
    if isinstance(document.get('runner'), dict) and ENTITLEMENT_KEY in document['runner']:
        entitlement.append(f'`runner.{ENTITLEMENT_KEY}` is present')
    results.record('bounds.no_entitlement_requirement', entitlement)
    return roles


def _passage(inputs, document, results):
    contract = document.get('contract')
    version, problem = _json(inputs['version']['stdout'])
    problems = []
    if problem or not isinstance(version, dict):
        problems.append('the version envelope is ' + (problem or 'not an object'))
    else:
        for path in (('build', 'contract'), ('data', 'contract')):
            if _get(version, *path) != contract or not isinstance(contract, str):
                problems.append(f'version `{".".join(path)}` is {_spell(_get(version, *path))}; the document asserts {_spell(contract)}')
    results.record('passage.contract_matches_version', problems)
    listed = _get(inputs['property-list'], 'PWContract')
    results.record('passage.contract_matches_property_list',
                   [] if isinstance(contract, str) and listed == contract else
                   f'the property list holds {_spell(listed)}; the document asserts {_spell(contract)}')
    results.record('passage.contract_packaged_form',
                   [] if isinstance(contract, str) and PACKAGED_IDENTITY.fullmatch(contract) else
                   f'{_spell(contract)} is neither `release:vX.Y.Z` nor `development:<sha256>`')
    first, second = inputs['example-1']['stdout'], inputs['example-2']['stdout']
    results.record('passage.emissions_identical',
                   [] if first is not None and first == second else 'the two emissions differ in their bytes')
    rendered = _get(inputs['contract-example'], 'document')
    without = {key: value for key, value in document.items() if key != 'contract'}
    if not isinstance(rendered, dict):
        results.record('passage.contract_rendering', "the contract snapshot's example was not retained")
    else:
        differing = sorted(key for key in without.keys() | rendered.keys() if without.get(key, None) != rendered.get(key, None)
                           or (key in without) != (key in rendered))
        results.record('passage.contract_rendering',
                       [f'member `{key}` differs from the contract snapshot' for key in differing])


def _matched_steps(document, reply):
    """(submitted step, every reply step carrying its identifier), in submitted order.

    Reply steps are found by identifier, never by position, and two steps with
    one identifier are both kept.
    """
    replied = [step for step in reply.get('steps') or [] if isinstance(step, dict)] if isinstance(reply.get('steps'), list) else []
    return [(submitted, [step for step in replied if step.get('step_id') == submitted.get('step_id')])
            for submitted in actions(document)]


def _echo(document, reply, matched, results):
    """Echo assertions; returns, per submitted step identifier, which halves every carrying record echoes."""
    results.record('echo.specimen_id', [] if reply.get('specimen_id') == document.get('specimen_id') else
                   f'the reply carries {_spell(reply.get("specimen_id"))}; the document carries {_spell(document.get("specimen_id"))}')
    submitted_ids = [step.get('step_id') for step in actions(document)]
    replied_ids = [step.get('step_id') if isinstance(step, dict) else None for step in reply.get('steps') or []] \
        if isinstance(reply.get('steps'), list) else None
    results.record('echo.step_ids', [] if replied_ids == submitted_ids else
                   f'the reply lists {_spell(replied_ids)}; the document lists {_spell(submitted_ids)}')
    echoed = {}
    if not any(records for _, records in matched):
        for ident in ('echo.queries', 'echo.attempts'):
            results.unevaluated(ident, 'no reply step carries a submitted step identifier')
        return echoed
    queries, attempts = [], []
    for submitted, records in matched:
        label = _spell(submitted.get('step_id'))
        halves = echoed.setdefault(submitted.get('step_id'), {'query': True, 'attempt': True})
        for replied in records:
            query = submitted.get('sandbox_check')
            if isinstance(query, dict):
                answer = replied.get('sandbox_check') if isinstance(replied.get('sandbox_check'), dict) else {}
                for name, sent, found in (('operation', query.get('operation'), answer.get('operation')),
                                          ('filter kind', _get(query, 'filter', 'kind'), answer.get('filter_kind')),
                                          ('filter value', _get(query, 'filter', 'value'), answer.get('filter_value'))):
                    if sent != found:
                        halves['query'] = False
                        queries.append(f'step {label} {name}: submitted {_spell(sent)}, echoed {_spell(found)}')
            attempt = submitted.get('attempt')
            if isinstance(attempt, dict):
                answer = replied.get('attempt') if isinstance(replied.get('attempt'), dict) else {}
                for name, sent, found in (('kind', attempt.get('kind'), answer.get('requested_kind')),
                                          ('action', attempt.get('action'), answer.get('requested_action')),
                                          ('target', attempt.get('target'), answer.get('requested_path'))):
                    if sent != found:
                        halves['attempt'] = False
                        attempts.append(f'step {label} {name}: submitted {_spell(sent)}, echoed {_spell(found)}')
    results.record('echo.queries', queries)
    results.record('echo.attempts', attempts)
    return echoed


def _exact_int(value, expected):
    return type(value) is int and value == expected


def _samples(inputs, name):
    """This checker's observations from one sampling, by submitted path."""
    observed = _get(inputs[name], 'targets')
    if not isinstance(observed, list):
        return None
    return {record.get('target'): record for record in observed if isinstance(record, dict)}


def _target_changes(inputs):
    return file_observation.target_changes(_samples(inputs, 'targets-before'), _samples(inputs, 'targets-after'))


def _native(inputs, roles, reply, matched, echoed, ground, results, workload):
    """Each pinned native expectation as its own assertion. No assertion reads an answer beside its attempt.

    An expectation that is read and not met fails whatever else is missing. One
    that is met passes only when every target prerequisite holds; `ground` says
    which targets were read and whether a pass is credited. The target each
    half of a step concerns is the one the table names for it: its expectation
    was observed with that file present and readable, so it is read only when
    this checker read the file before the run.
    """
    specs = workload['roles']

    def settle(ident, problems):
        if problems or ground['uncredited'] is None:
            results.record(ident, problems)
        else:
            results.unevaluated(ident, ground['uncredited'])

    run = inputs['run']
    settle('native.process_status', [] if _exact_int(run['exit'], 0) else
           [f'the `run` process exited {_spell(run["exit"])}'])
    settle('native.completion', [] if reply.get('normalized_outcome') == 'finished' else
           [f'the reply\'s `normalized_outcome` is {_spell(reply.get("normalized_outcome"))}'])

    # One reply record per step, read only for the half that echoes what was submitted.
    records = {submitted.get('step_id'): found for submitted, found in matched}
    queries, attempts = {}, {}
    for role, ident in roles['steps'].items():
        found = records.get(ident, [])
        unusable = None if len(found) == 1 else f'the reply carries {len(found)} steps with identifier {_spell(ident)}'
        for half, member, store in (('query', 'sandbox_check', queries), ('attempt', 'attempt', attempts)):
            concerned = specs[role][half][1]
            if concerned not in ground['read']:
                store[role] = (None, f'target {concerned} ({roles["targets"][concerned]}) was not read before the '
                               f'run; nothing about it is credited or faulted')
            elif unusable is None and not echoed[ident][half]:
                store[role] = (None, f'the reply\'s {half} record for {_spell(ident)} does not echo the submitted '
                               f'{half}; nothing is read from it')
            elif unusable is None:
                store[role] = (found[0].get(member) if isinstance(found[0].get(member), dict) else {}, None)
            else:
                store[role] = (None, unusable)

    def assertion(ident, source, problems):
        record, withheld = source
        if record is None:
            results.unevaluated(ident, withheld)
            return False
        problems = problems(record)
        settle(ident, problems)
        return not problems

    def pinned(noun, producer, expectation):
        """The record comes from `producer` and carries each pinned member with its exact type and value."""
        expected = dict(result_source=producer, **expectation)

        def problems(record):
            found = {key: record.get(key) for key in expected}
            if all(type(found[key]) is type(value) and found[key] == value for key, value in expected.items()):
                return []
            return [f'the {noun} is {_spell(found)}']
        return problems

    qualifying = [role for role in specs
                  if assertion(f'native.{role}.prediction', queries[role], pinned('answer', 'validator', specs[role]['answer']))]
    if qualifying:
        orders = []
        for role in qualifying:
            order = _get(records[roles['steps'][role]][0], 'comparison', 'order')
            if order != 'query_first':
                orders.append(f'{step_text(workload, role)}: `order` is {_spell(order)}')
        settle('native.order', orders)
    else:
        results.unevaluated('native.order', 'no answer met its expectation')

    for role in specs:
        assertion(f'native.{role}.attempt', attempts[role], pinned('attempt', 'worker', specs[role]['result']))

    changes = _target_changes(inputs)
    settle('native.targets_unchanged', [f'{target} {change}' for target, found in changes.items() for change in found])

    def fresh(read):
        return read.get('fresh_read') if isinstance(read.get('fresh_read'), dict) else {}

    def syscalls(attempt):
        return file_observation.fresh_syscalls(attempt, FRESH_READ_BOUND)

    for role, letter in fresh_roles(workload).items():
        assertion(f'native.{role}.fresh_syscalls', attempts[role], syscalls)

        # The correspondence needs one stable observation of the target to compare against.
        target = roles['targets'][letter]
        observed = (_samples(inputs, 'targets-before') or {}).get(target, {})
        source = attempts[role] if target not in changes else \
            (None, f'the samples of {target} before and after the run differ; no correspondence with it is claimed')
        expected = {'device': _get(observed, 'stat', 'st_dev'), 'inode': _get(observed, 'stat', 'st_ino')}

        def identity(attempt, expected=expected, target=target):
            return file_observation.fresh_identity(attempt, expected, target)

        def content(attempt, observed=observed, target=target):
            return file_observation.fresh_content(attempt, observed, target)

        def given(supplied, reason, source=source):
            """The fresh read's record, when the call that supplies this observation succeeded."""
            return source if source[0] is None or supplied(fresh(source[0])) else (None, reason)
        # A sample without a device and inode leaves nothing to compare an identity with. A sample
        # without a prefix differs from its later sample under the test above, which withholds both.
        identified = given(lambda read: _exact_int(read.get('stat_rc'), 0),
                           'the descriptor stat did not succeed; it supplies no identity')
        if identified[0] is not None and not all(type(value) is int for value in expected.values()):
            identified = (None, f'this checker\'s sample of {target} holds no device and inode to compare with')
        assertion(f'native.{role}.fresh_identity', identified, identity)
        assertion(f'native.{role}.fresh_content',
                  given(lambda read: type(read.get('read_rc')) is int and read['read_rc'] >= 0,
                        'the bounded read did not succeed; it supplies no bytes'), content)


def _prerequisites(inputs, roles, results, workload):
    """What this checker must have observed before a native expectation is credited.

    Returns the targets it read before the run, and the reason no native pass
    is credited, which is None when every prerequisite holds.
    """
    uncredited = 'no failure was found; no native pass is credited while a target prerequisite is unestablished'
    samples = _samples(inputs, 'targets-before')
    problems, usable = [], {}
    if samples is None:
        problems.append('the targets were not observed before the run')
    else:
        for role, target in roles['targets'].items():
            record = samples.get(target)
            if record is None:
                problems.append(f'target {role} ({target}) was not observed')
            elif not record.get('regular_file') or not record.get('readable'):
                problems.append(f'target {role} ({target}) is not a readable regular file' +
                                (f' ({record["error"]})' if record.get('error') else ''))
            else:
                usable[role] = record
    results.record('prerequisite.targets_readable', problems)
    if problems:
        for ident in ('prerequisite.distinct_identities', 'prerequisite.distinguishing_prefixes'):
            results.unevaluated(ident, 'a target was not read before the run')
        return {'read': set(usable), 'uncredited': uncredited}

    def identity(role):
        return _get(usable[role], 'stat', 'st_dev'), _get(usable[role], 'stat', 'st_ino')

    def prefix(role):
        return usable[role].get('prefix_length'), usable[role].get('prefix_sha256')
    letters = target_roles(workload)
    identities, prefixes = [], []
    for role in letters:
        if any(type(part) is not int for part in identity(role)):
            identities.append(f'target {role} has no observed device and inode')
        if type(prefix(role)[0]) is not int or prefix(role)[0] < 1 or not isinstance(prefix(role)[1], str):
            prefixes.append(f'target {role} has no nonempty observed prefix')
    for index, first in enumerate(letters):
        for second in letters[index + 1:]:
            if not identities and identity(first) == identity(second):
                identities.append(f'targets {first} and {second} are one file: device and inode {_spell(list(identity(first)))}')
    for read in sorted(set(fresh_roles(workload).values())):
        for other in letters:
            if other != read and not prefixes and prefix(other) == prefix(read):
                prefixes.append(f"target {read}'s bounded prefix equals target {other}'s")
    results.record('prerequisite.distinct_identities', identities)
    results.record('prerequisite.distinguishing_prefixes', prefixes)
    return {'read': set(usable), 'uncredited': uncredited if identities or prefixes else None}


def one_change_problems(name, emitted, document, submitted):
    """Whether a submitted input is the emitted document with its one stated change.

    The input is judged against the emitted bytes and the stated change, not
    against the function that wrote it.
    """
    if submitted is None:
        return ['the input was not retained']
    if name == 'truncated_document':
        return [] if emitted.endswith(b'}\n') and submitted == emitted[:-2] + b'\n' else \
            ['the input is not the emitted bytes without their closing brace']
    value, problem = _json(submitted)
    if problem or not isinstance(value, dict):
        return ['the input is ' + (problem or 'not a JSON object')]
    contract = document.get('contract')

    def others(members):
        return {key: member for key, member in members.items() if key != 'contract'}

    if name == 'absent_identity':
        return [] if value == others(document) else ['the input is not the document without `contract`']
    if name == 'unknown_member':
        return [] if value == dict(document, **{UNKNOWN_MEMBER: True}) else \
            ['the input is not the document with one unknown member']
    asserted = value.get('contract')
    if others(value) != others(document) or not isinstance(asserted, str) or asserted == contract:
        return ['the input differs from the document outside `contract`, or asserts the same identity']
    if name == 'other_release':
        return [] if asserted == 'release:v0.0.0' else [f'the input asserts {_spell(asserted)}']
    if name == 'unbound':
        return [] if asserted == 'unbound' else [f'the input asserts {_spell(asserted)}']
    development = re.compile(r'development:[0-9a-f]{64}')
    if not development.fullmatch(asserted):
        return [f'the input asserts {_spell(asserted)}, which is not a development identity']
    if isinstance(contract, str) and development.fullmatch(contract) and \
            sum(a != b for a, b in zip(asserted, contract)) != 1:
        return [f'the input asserts {_spell(asserted)}, which is not one digit from the document\'s identity']
    return []


def _refusals(inputs, emitted, document, results):
    for name, (code, path, identity, component) in REFUSALS.items():
        prefix = 'refusal.' + name
        capture = inputs['refusals'][name]
        results.record(prefix + '.one_change', one_change_problems(name, emitted, document, capture['input']))
        envelope, problem = _json(capture['stdout'])
        refused = []
        if capture['exit'] != 1:
            refused.append(f'exit status is {_spell(capture["exit"])}')
        if problem or not isinstance(envelope, dict):
            refused.append('stdout is ' + (problem or 'not an object'))
        elif _get(envelope, 'result', 'normalized_outcome') != 'bad_request':
            refused.append(f'`result.normalized_outcome` is {_spell(_get(envelope, "result", "normalized_outcome"))}')
        results.record(prefix + '.refused', refused)
        if not isinstance(envelope, dict):
            results.rest(prefix + '.', 'the refusal produced no envelope')
            continue
        failure = _get(envelope, 'data', 'request_failure')
        found = (_get(failure, 'code'), _get(failure, 'path'))
        results.record(prefix + '.failure', [] if found == (code, path) else
                       f'`request_failure` has code {_spell(found[0])} and path {_spell(found[1])}')
        if identity:
            results.record(prefix + '.expected_identity',
                           [] if _get(failure, 'expected_contract') == document.get('contract') else
                           f'`expected_contract` is {_spell(_get(failure, "expected_contract"))}; '
                           f'the app\'s identity is {_spell(document.get("contract"))}')
        data = envelope.get('data') if isinstance(envelope.get('data'), dict) else {}
        if component == 'controller':
            results.record(prefix + '.no_delivery',
                           [f'`data.{key}` is present' for key in ('runner_client', 'runner_result') if data.get(key) is not None])
        else:
            reply = data.get('runner_result')
            host = []
            if data.get('runner_client') is None or not isinstance(reply, dict):
                host.append('the refusal carries no client capture and runner reply')
            else:
                if reply.get('normalized_outcome') != 'bad_request':
                    host.append(f'the reply\'s `normalized_outcome` is {_spell(reply.get("normalized_outcome"))}')
                if reply.get('steps') != []:
                    host.append('the reply carries step results')
            results.record(prefix + '.host_reply', host)


def _publication(inputs, results, workload):
    """Emission, bounds and passage, without reading any run captures.

    Returns the emitted bytes with their document when it may, and the roles
    the bounds found either way.
    """
    emitted, document = _emission(inputs, results)
    roles = None
    if document is not None:
        roles = _bounds(document, results, workload)
        _passage(inputs, document, results)
    gate = [ident for ident, group, _, _ in results.table if group in ('emission', 'bounds')]
    if document is None or results.failed(*gate):
        results.remaining('no run was attempted: the emission or its bounds did not hold')
        return None, roles
    return (emitted, document), roles


def _execution(capture, submitted, document, form, roles, results, workload, authored_fixture):
    """Every row read from one submission's run. Returns the consumer's errors.

    `authored_fixture` admits constructed JSON host bytes, for the offline
    controls only; a live capture is read as the controller retained it.
    """
    ground = _prerequisites(capture, roles, results, workload)

    run = capture['run']
    envelope, problem = _json(run['stdout'])
    if run['exit'] is None or problem or not isinstance(envelope, dict):
        results.record('execution.admitted_reply',
                       'the run was not captured' if run['exit'] is None else
                       'the run printed no envelope: stdout is ' + (problem or 'not an object'))
        results.remaining('the run supplied no envelope')
        return []

    contract = document.get('contract')
    data = envelope.get('data') if isinstance(envelope.get('data'), dict) else {}
    client, carried = data.get('runner_client'), data.get('runner_result')
    written = _get(client, 'request_delivery', 'bytes_written')
    if client is None:
        results.unevaluated('passage.delivery_length', 'the envelope carries no client record')
    else:
        results.record('passage.delivery_length', [] if _exact_int(written, len(submitted) - 1) else
                       f'`request_delivery.bytes_written` is {_spell(written)}; the submitted document is '
                       f'{len(submitted) - 1} bytes without its framing newline')

    outcome = _get(envelope, 'result', 'normalized_outcome')
    refused = []
    if data.get('request_failure') is not None:
        refused.append('`data.request_failure` is ' + _spell(data['request_failure']))
    if outcome == 'bad_request':
        refused.append('`result.normalized_outcome` is "bad_request"')
    results.record('admission.no_request_failure', refused)
    policy = submitted_policy(document, form)
    digest = hashlib.sha256(policy['sbpl_source'].encode('utf-8')).hexdigest() if isinstance(policy.get('sbpl_source'), str) else None
    actor_id = document['actors'][0]['actor_id'] if form == 'actor' else None
    if form == 'actor':
        dossiers = [entry for entry in _get(data, 'specimen', 'actors') or []
                    if isinstance(entry, dict) and entry.get('actor_id') == actor_id]
        dossier = _get(dossiers[0], 'policy', 'augmentation', 'original_sha256') if len(dossiers) == 1 else None
    else:
        dossier = _get(data, 'specimen', 'policy', 'augmentation', 'original_sha256')
    results.record('admission.dossier_policy_digest', [] if digest is not None and dossier == digest else
                   f'the dossier records {_spell(dossier)}; the submitted policy source has SHA-256 {_spell(digest)}')

    # Producer identity is compared before any reply is read.
    results.record('identity.envelope_build', [] if _get(envelope, 'build', 'contract') == contract else
                   f'`build.contract` is {_spell(_get(envelope, "build", "contract"))}')
    if client is None:
        results.unevaluated('identity.client_transport', 'the envelope carries no client record')
    else:
        results.record('identity.client_transport', [] if _get(client, 'transport', 'contract') == contract else
                       f'the capture\'s `contract` is {_spell(_get(client, "transport", "contract"))}')
    if carried is None:
        results.unevaluated('identity.reply_producer', 'the envelope carries no runner reply')
    else:
        results.record('identity.reply_producer', [] if _get(carried, 'producer', 'contract') == contract else
                       f'`producer.contract` is {_spell(_get(carried, "producer", "contract"))}')

    reported = _get(envelope, 'result', 'exit_code')
    results.record('reported.exit_code', [] if _exact_int(reported, run['exit']) else
                   f'the process exited {run["exit"]}; `result.exit_code` is {_spell(reported)}')
    errors = consumer.validate(envelope, contract, allow_fixture_json=authored_fixture)
    results.record('consumer_validation', [f'{len(errors)} consumer error(s): ' + '; '.join(errors)] if errors else [])

    dependent = ('admission.reply_policy_digest', 'echo.', 'readers.', 'native.')
    if results.failed('identity.envelope_build', 'identity.client_transport', 'identity.reply_producer'):
        results.unevaluated('execution.admitted_reply', 'an identity differs; no reply is read under another identity')
        for prefix in dependent:
            results.rest(prefix, 'an identity differs; no reply is read under another identity')
        return errors
    reply = consumer.admitted_reply(envelope, contract, allow_fixture_json=authored_fixture)
    if reply is None:
        results.record('execution.admitted_reply', 'the envelope\'s evidence admits no runner reply '
                       f'(`result.normalized_outcome` is {_spell(outcome)})')
        for prefix in dependent:
            results.rest(prefix, 'no admitted reply: nothing is credited or faulted from it')
        return errors
    results.record('execution.admitted_reply', [])

    received = (consumer.actor_record(reply, actor_id) if form == 'actor' else reply).get('policy_sha256')
    results.record('admission.reply_policy_digest', [] if digest is not None and received == digest else
                   f'the reply records {_spell(received)}; the submitted policy source has SHA-256 {_spell(digest)}')
    matched = _matched_steps(document, reply)
    echoed = _echo(document, reply, matched, results)
    diagnostics = data.get('runner_sandbox_diagnostics') if isinstance(data.get('runner_sandbox_diagnostics'), dict) else {}
    results.record('readers.disposition_integrity', [] if diagnostics.get('disposition_integrity') == 'valid' else
                   f'`disposition_integrity` is {_spell(diagnostics.get("disposition_integrity"))}')
    results.record('readers.disposition_issues', [] if diagnostics.get('disposition_issues') == [] else
                   f'`disposition_issues` is {_spell(diagnostics.get("disposition_issues"))}')
    _native(capture, roles, reply, matched, echoed, ground, results, workload)
    return errors


def derivatives(document):
    """Construct the two test-owned request forms. `transformation_problems` judges them independently."""
    flat = copy.deepcopy(document)
    flat['probe_plan'] = [step for phase in flat.pop('phases') for step in phase['actions']]
    actor = copy.deepcopy(document)
    actor['actors'] = [{'actor_id': 'example-reader', 'equipment': 'selected',
                        'sandbox': {'mode': 'apply', 'policy': actor.pop('policy')}}]
    for phase in actor['phases']:
        phase['actor_id'] = 'example-reader'
    return {'flat': flat, 'actor': actor}


def transformation_problems(source, candidate, form, workload=WORKLOAD):
    """The failed conditions of one derivative, as (name, explanation).

    The derivative is judged by its members against the emitted document and
    the table, without calling the constructor. A member that is absent fails
    the member set alone; one that is present and changed fails its own
    condition.
    """
    check = _Conditions()
    if not check.require('members', isinstance(candidate, dict), 'the derivative is not a JSON object'):
        return check.failed
    roles = workload['roles']
    if form == 'flat':
        check.require('members', set(candidate) == (set(source) - {'phases'}) | {'probe_plan'},
                      f'the members are {_spell(sorted(candidate))}')
        changed = sorted(key for key in (source.keys() - {'phases'}) & candidate.keys() if candidate[key] != source[key])
        check.require('preserved', not changed, f'member(s) {_spell(changed)} changed')
        steps = candidate.get('probe_plan')
        if 'probe_plan' in candidate and check.require('actions', isinstance(steps, list) and len(steps) == len(roles),
                                                       f'`probe_plan` does not hold {len(roles)} actions'):
            position = iter(steps)
            for index, phase in enumerate(workload['phases']):
                for offset, role in enumerate(phase):
                    check.require(f'action.{role}', next(position) == source['phases'][index]['actions'][offset],
                                  f'the action is not phase {index + 1} action {offset + 1} of the emitted document')
        return check.failed
    check.require('members', set(candidate) == (set(source) - {'policy'}) | {'actors'},
                  f'the members are {_spell(sorted(candidate))}')
    changed = sorted(key for key in (source.keys() - {'policy', 'phases'}) & candidate.keys() if candidate[key] != source[key])
    check.require('preserved', not changed, f'member(s) {_spell(changed)} changed')
    actors = candidate.get('actors')
    actor_id = None
    if 'actors' in candidate and check.require('actors', isinstance(actors, list) and len(actors) == 1 and
                                               isinstance(actors[0], dict), '`actors` is not one actor object'):
        actor = actors[0]
        check.require('actor.members', set(actor) == {'actor_id', 'equipment', 'sandbox'},
                      f'the actor\'s members are {_spell(sorted(actor))}')
        if 'actor_id' in actor and check.require('actor.actor_id', isinstance(actor['actor_id'], str) and bool(actor['actor_id']),
                                                 f'`actor_id` is {_spell(actor["actor_id"])}'):
            actor_id = actor['actor_id']
        if 'equipment' in actor:
            check.require('actor.equipment', actor['equipment'] == 'selected', f'`equipment` is {_spell(actor["equipment"])}')
        if 'sandbox' in actor:
            sandbox = actor['sandbox']
            if check.require('actor.sandbox.members', isinstance(sandbox, dict) and set(sandbox) == {'mode', 'policy'},
                             'the sandbox is not an object with exactly `mode` and `policy`'):
                check.require('actor.sandbox.mode', sandbox['mode'] == 'apply', f'`mode` is {_spell(sandbox["mode"])}')
                check.require('actor.sandbox.policy', sandbox['policy'] == source.get('policy'),
                              'the policy is not the emitted document\'s whole policy')
    phases = candidate.get('phases')
    if 'phases' in candidate and check.require('phases', isinstance(phases, list) and len(phases) == len(source['phases']),
                                               f'`phases` does not hold {len(source["phases"])} phases'):
        for number, (phase, original) in enumerate(zip(phases, source['phases']), 1):
            if not check.require(f'phase{number}.members', isinstance(phase, dict) and set(phase) == set(original) | {'actor_id'},
                                 'the phase does not add exactly `actor_id` to the emitted phase\'s members'):
                continue
            if actor_id is not None:
                check.require(f'phase{number}.actor_id', phase['actor_id'] == actor_id,
                              f'`actor_id` is {_spell(phase["actor_id"])}; the actor is {_spell(actor_id)}')
            check.require(f'phase{number}.preserved', all(phase[key] == value for key, value in original.items()),
                          'an emitted phase member changed')
    return check.failed


def _structure(capture, document, form, roles, results, authored_fixture):
    """Correspondence between one submitted document and the ownership records of its reply.

    Internal ownership, query operand and process-identifier joins belong to
    the consumer. Here an internally valid reply still has to be the reply to
    this submitted partition, worker and actor.
    """
    if results.status('execution.admitted_reply') != 'pass':
        results.rest('structure', 'no identity-admitted reply')
        return
    envelope = _json(capture['run']['stdout'])[0]
    reply = consumer.admitted_reply(envelope, document['contract'], allow_fixture_json=authored_fixture)
    actor_form = form == 'actor'

    check = _Conditions()
    check.require('execution_form', consumer.actor_form(reply) == actor_form, 'the reply uses another execution form')
    results.conditions('structure.execution_form', check.failed)

    expected = [{'phase_id': 'main', 'actions': document['probe_plan']}] if form == 'flat' else document['phases']
    phases = [phase if isinstance(phase, dict) else {} for phase in reply['phases']] \
        if isinstance(reply.get('phases'), list) else []
    membership = _Conditions()
    membership.require('phase_count', len(phases) == len(expected),
                       f'the reply holds {len(phases)} phase(s); {len(expected)} were submitted')
    for number, (submitted, replied) in enumerate(zip(expected, phases), 1):
        wanted = [step['step_id'] for step in submitted['actions']]
        for name, found, sent in (('phase_id', replied.get('phase_id'), submitted['phase_id']),
                                  ('action_ids', replied.get('action_ids'), wanted)):
            membership.require(f'phase{number}.{name}', found == sent, f'the reply carries {_spell(found)}; submitted {_spell(sent)}')
        membership.require(f'phase{number}.ordinal', _exact_int(replied.get('ordinal'), number),
                           f'the reply carries {_spell(replied.get("ordinal"))}')
    results.conditions('structure.phase_membership', membership.failed)

    collections = _Conditions()
    for number, submitted in enumerate(expected, 1):
        matches = [phase for phase in phases if phase.get('phase_id') == submitted['phase_id']]
        if not collections.require(f'phase{number}.unique', len(matches) == 1,
                                   f'{len(matches)} reply phases carry {_spell(submitted["phase_id"])}'):
            continue
        phase = matches[0]
        validator = phase.get('validator_subprocess') if isinstance(phase.get('validator_subprocess'), dict) else {}
        ordering = phase.get('ordering') if isinstance(phase.get('ordering'), dict) else {}
        wanted = [step['step_id'] for step in submitted['actions']]
        for name, found, sent in (
                ('arrival_observed', phase.get('arrival_observed'), True),
                ('completion_observed', phase.get('completion_observed'), True),
                ('collection_status', phase.get('collection_status'), 'collected'),
                ('validator_reaped', validator.get('reaped'), True),
                ('collection_closed_before_proceed', ordering.get('collection_closed_before_proceed'), True),
                ('proceed_set', ordering.get('proceed_set'), True),
                ('proceed_observed', ordering.get('proceed_observed'), True),
                ('worker_lifetime_established', ordering.get('worker_lifetime_established'), True),
                ('validator_disposition', ordering.get('validator_disposition'), 'reaped'),
                ('protocol_violations', ordering.get('protocol_violations'), []),
                ('expected_step_ids', validator.get('expected_step_ids'), wanted)):
            collections.require(f'phase{number}.{name}', type(found) is type(sent) and found == sent,
                                f'the phase carries {_spell(found)}')
    results.conditions('structure.collections', collections.failed)

    actor_id = document['actors'][0]['actor_id'] if actor_form else None
    actor = consumer.actor_record(reply, actor_id) if actor_form else {}
    worker = actor.get('subprocess') if actor_form else reply.get('runner_subprocess')
    worker = worker if isinstance(worker, dict) else {}
    pid = worker.get('pid')
    owned = _Conditions()
    if actor_form:
        owned.require('applied', actor.get('applied') is True, f'the actor\'s `applied` is {_spell(actor.get("applied"))}')
        owned.require('launch_pid', _get(actor, 'launch', 'pid') == pid,
                      f'the launch names process {_spell(_get(actor, "launch", "pid"))}; the worker is {_spell(pid)}')
        owned.require('launch_parent_pid', _get(actor, 'launch', 'parent_pid') == reply.get('pid'),
                      f'the launch names parent {_spell(_get(actor, "launch", "parent_pid"))}; the reply\'s process is '
                      f'{_spell(reply.get("pid"))}')
    else:
        owned.require('applied', reply.get('sandboxed_after_apply') is True,
                      f'`sandboxed_after_apply` is {_spell(reply.get("sandboxed_after_apply"))}')
        owned.require('reply_pid', reply.get('pid') == pid,
                      f'the reply\'s process is {_spell(reply.get("pid"))}; the worker is {_spell(pid)}')
    owned.require('pid', type(pid) is int and pid > 0, f'the worker\'s `pid` is {_spell(pid)}')
    for name in ('reaped', 'ready_byte_received', 'done_observed'):
        owned.require(name, worker.get(name) is True, f'`{name}` is {_spell(worker.get(name))}')
    owned.require('exit_code', _exact_int(worker.get('exit_code'), 0), f'`exit_code` is {_spell(worker.get("exit_code"))}')
    owned.require('term_signal', worker.get('term_signal') is None, f'`term_signal` is {_spell(worker.get("term_signal"))}')
    owned.require('collection_basis', worker.get('collection_basis') == 'after_confirmed_reap',
                  f'`collection_basis` is {_spell(worker.get("collection_basis"))}')
    results.conditions('structure.worker', owned.failed)
    if not actor_form:
        return

    data = envelope['data']
    ownership = _Conditions()
    diagnostics = _get(data, 'runner_sandbox_diagnostics', 'actors')
    for label, records in (('reply', reply.get('actors')), ('diagnostics', diagnostics),
                           ('dossier', _get(data, 'specimen', 'actors'))):
        named = [entry.get('actor_id') if isinstance(entry, dict) else None for entry in records] \
            if isinstance(records, list) else None
        ownership.require(f'{label}_actors', named == [actor_id], f'the {label} names actors {_spell(named)}')
    visits = list(range(1, len(expected) + 1))
    ownership.require('visits', actor.get('visits') == visits, f'the actor\'s visits are {_spell(actor.get("visits"))}')
    for number, replied in enumerate(phases[:len(expected)], 1):
        ownership.require(f'phase{number}.actor_id', replied.get('actor_id') == actor_id,
                          f'the phase names actor {_spell(replied.get("actor_id"))}')
        ownership.require(f'phase{number}.actor_visit', _exact_int(replied.get('actor_visit'), number),
                          f'the phase is visit {_spell(replied.get("actor_visit"))}')
        ownership.require(f'phase{number}.no_termination_gate', 'termination_gate' not in replied,
                          'the phase carries a termination dependency')
    steps = [step for step in reply['steps'] if isinstance(step, dict)] if isinstance(reply.get('steps'), list) else []
    for role, ident in roles['steps'].items():
        owners = [step.get('actor_id') for step in steps if step.get('step_id') == ident]
        ownership.require(f'step.{role}.actor_id', all(owner == actor_id for owner in owners),
                          f'the step names actor(s) {_spell(owners)}')
    others = [step.get('actor_id') for step in steps if step.get('step_id') not in roles['steps'].values()]
    ownership.require('unsubmitted_steps.actor_id', all(owner == actor_id for owner in others),
                      f'step(s) that were not submitted name actor(s) {_spell(others)}')
    entries = [entry for entry in diagnostics if isinstance(entry, dict)] if isinstance(diagnostics, list) else []
    for name, wanted in (('disposition_integrity', 'valid'), ('disposition_issues', [])):
        found = [entry.get(name) for entry in entries]
        ownership.require(f'diagnostics.{name}', all(type(value) is type(wanted) and value == wanted for value in found),
                          f'the actor diagnostics carry {_spell(found)}')
    results.conditions('structure.actor_ownership', ownership.failed)

    digest = hashlib.sha256(submitted_policy(document, form)['sbpl_source'].encode('utf-8')).hexdigest()
    application = _Conditions()
    for name, wanted in (('mode', 'apply'), ('setup_status', 'applied'), ('applied', True), ('application_count', 1),
                         ('application', {'state': 'observed', 'basis': 'applied_publication'}),
                         ('policy_received_sha256', digest)):
        found = actor.get(name)
        application.require(name, type(found) is type(wanted) and found == wanted, f'the actor carries {_spell(found)}')
    results.conditions('structure.actor_application', application.failed)

    equipment = actor.get('equipment') if isinstance(actor.get('equipment'), dict) else {}
    execution = equipment.get('execution') if isinstance(equipment.get('execution'), dict) else {}
    matched = _Conditions()
    for name, found, wanted in (('requested', equipment.get('requested'), 'selected'),
                                ('resolved', equipment.get('resolved'), 'selected'),
                                ('required_entitlements', equipment.get('required_entitlements'), []),
                                ('requirements_status', equipment.get('requirements_status'), 'satisfied'),
                                ('execution.status', execution.get('status'), 'matched'),
                                ('execution.eligible', execution.get('eligible'), True)):
        matched.require(name, type(found) is type(wanted) and found == wanted, f'the equipment carries {_spell(found)}')
    matched.require('execution.pid', execution.get('pid') == pid,
                    f'the equipment observation names process {_spell(execution.get("pid"))}; the worker is {_spell(pid)}')
    results.conditions('structure.actor_equipment', matched.failed)


def _described(roles, workload):
    """The roles in words, so a reader of the report can match each statement to a submitted step and path."""
    if roles is None:
        return None
    return {'steps': {role: {'role': step_text(workload, role), 'step_id': ident} for role, ident in roles['steps'].items()},
            'targets': {letter: {'role': target_text(workload, letter), 'path': submitted}
                        for letter, submitted in roles['targets'].items()}}


def _report(by_form, forms):
    assertions = []
    for form, results in by_form.items():
        missing = [ident for ident, _, _, _ in results.table if ident not in results.rows]
        assert not missing, (form, missing)
        assertions.extend(dict(form=form, id=ident, group=group, classification=classification, statement=statement,
                               **results.rows[ident]) for ident, group, classification, statement in results.table)
    failures = [row for row in assertions if row['status'] == 'fail']
    counts = {}
    for row in assertions:
        bucket = counts.setdefault(row['classification'], {'pass': 0, 'fail': 0, 'not_evaluated': 0})
        bucket[row['status']] += 1
    return {'schema_version': 3, 'status': 'fail' if failures else 'pass',
            'classifications': sorted({row['classification'] for row in failures}),
            'counts_by_classification': counts,
            'failures': [{key: row[key] for key in ('form', 'id', 'classification', 'explanation', 'conditions') if key in row}
                         for row in failures],
            'not_evaluated': [{'form': row['form'], 'id': row['id'], 'reason': row['explanation']} for row in assertions
                              if row['status'] == 'not_evaluated'],
            'consumer_errors': [f'{form}: {error}' for form in forms for error in forms[form]['consumer_errors']],
            'forms': forms, 'assertions': assertions}


def evaluate(inputs, *, authored_fixture=False, workload=WORKLOAD, preparation_only=False):
    """One publication and three submissions, each judged on its own rows. No row compares two forms.

    Preparation evaluates only the publication rows, before any observations
    or submissions exist. Evaluation of retained captures preserves independent
    run failures even beside a publication correspondence failure.
    """
    by_form = {form: Results(form, workload) for form in FORMS}
    forms = {form: {'workload': None, 'consumer_errors': []} for form in FORMS}
    publication, roles = _publication(inputs, by_form['emitted'], workload)
    forms['emitted']['workload'] = _described(roles, workload)
    if preparation_only:
        for results in by_form.values():
            results.remaining('preparation has not observed targets or submitted any request')
        return _report(by_form, forms)
    if publication is not None:
        _refusals(inputs, *publication, by_form['emitted'])
    for form in FORMS:
        results = by_form[form]
        if publication is None:
            if form != 'emitted':
                results.remaining('the emission is unestablished')
            continue
        emitted, source = publication
        if form == 'emitted':
            capture, submitted, document = inputs, emitted, source
        else:
            capture = inputs['forms'][form]
            submitted = capture['input']
            document = _json(submitted)[0]
            failed = transformation_problems(source, document, form, workload)
            results.conditions('transformation', failed)
            if failed:
                results.remaining('the transformation is unestablished')
                continue
            roles, problems = workload_roles(document, workload)
            if problems:
                results.remaining('the derivative supplied no admitted workload')
                continue
            forms[form]['workload'] = _described(roles, workload)
        forms[form]['consumer_errors'] = _execution(capture, submitted, document, form, roles, results, workload,
                                                    authored_fixture)
        _structure(capture, document, form, roles, results, authored_fixture)
    return _report(by_form, forms)


SUMMARY_REQUIRES = ('identity.envelope_build', 'identity.client_transport', 'identity.reply_producer',
                    'execution.admitted_reply', 'echo.specimen_id', 'echo.step_ids', 'echo.queries', 'echo.attempts',
                    'structure.execution_form', 'structure.phase_membership')


def diagnostic_summary(inputs, report):
    """Each form's observations side by side, for a reader. It is built from a finished report and judges nothing.

    Query and attempt stay separate values. A form whose producer identity or
    submitted association is unestablished supplies no observations.
    """
    summaries = []
    for form in FORMS:
        capture = inputs if form == 'emitted' else inputs['forms'][form]
        statuses = {row['id']: row['status'] for row in report['assertions'] if row['form'] == form}
        record = {'form': form, 'samples': {key: capture.get(key) for key in ('targets-before', 'targets-after')},
                  'assertions': statuses, 'observations': None}
        summaries.append(record)
        described = report['forms'][form]['workload']
        required = SUMMARY_REQUIRES + (('structure.actor_ownership',) if form == 'actor' else ())
        if described is None or any(statuses.get(ident) != 'pass' for ident in required):
            record['withheld_reason'] = 'identity or submitted association is unestablished'
            continue
        reply = _json(capture['run']['stdout'])[0]['data']['runner_result']
        record['observations'] = []
        for role, entry in described['steps'].items():
            step = next(found for found in reply['steps'] if found['step_id'] == entry['step_id'])
            query, attempt = step['sandbox_check'], step['attempt']
            observed = {'role': role, 'step_id': entry['step_id'], 'phase_id': step.get('phase_id'),
                        'actor_id': step.get('actor_id'),
                        'query': {key: query.get(key) for key in ('result_source', 'outcome', 'native_rc', 'errno')},
                        'attempt': {key: attempt.get(key) for key in ('result_source', 'outcome', 'rc', 'errno')}}
            fresh = attempt.get('fresh_read')
            if isinstance(fresh, dict):
                try:
                    digest = hashlib.sha256(bytes.fromhex(fresh.get('content_hex'))).hexdigest()
                except (TypeError, ValueError):
                    digest = None
                observed['fresh_read'] = {'identity': fresh.get('identity'), 'count': fresh.get('read_rc'), 'sha256': digest}
            record['observations'].append(observed)
    return summaries


def diagnostics(report):
    """The (form, assertion identifier, classification) triples of a report's failures."""
    return {(row['form'], row['id'], row['classification']) for row in report['failures']}


def failed_conditions(report):
    """The failed condition names of each conditioned row that failed, by (form, assertion identifier)."""
    return {(row['form'], row['id']): tuple(row['conditions']) for row in report['failures'] if 'conditions' in row}


def render(report):
    lines = ['example round trip: ' + report['status'].upper() +
             (' (' + ', '.join(report['classifications']) + ')' if report['classifications'] else '')]
    for classification in (CONSISTENCY, EXECUTION_UNAVAILABLE, PREREQUISITE_UNESTABLISHED, NATIVE_OBSERVATION):
        counts = report['counts_by_classification'].get(classification)
        if counts:
            lines.append(f'  {classification}: {counts["pass"]} hold, {counts["fail"]} fail, '
                         f'{counts["not_evaluated"]} not evaluated')
    for row in report['failures']:
        lines.append(f'FAIL {row["form"]} {row["id"]} [{row["classification"]}]: {row["explanation"]}')
    for row in report['not_evaluated']:
        lines.append(f'NOT EVALUATED {row["form"]} {row["id"]}: {row["reason"]}')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _write_report(directory, report):
    (Path(directory) / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(render(report), flush=True)


def prepare(directory, app, snapshot):
    directory = Path(directory)
    listed = {'path': str(Path(app) / 'Contents/Info.plist'), 'PWContract': None, 'error': None}
    try:
        listed['PWContract'] = plistlib.loads(Path(listed['path']).read_bytes()).get('PWContract')
    except (OSError, plistlib.InvalidFileException, ValueError) as error:
        listed['error'] = f'{type(error).__name__}: {error}'
    (directory / 'property-list.json').write_text(json.dumps(listed, indent=2) + '\n')
    rendered = {'snapshot': str(snapshot), 'node': EXAMPLE_NODE, 'document': None}
    request = next(row for row in json.loads(Path(snapshot).read_text())['surfaces'] if row['id'] == 'request')
    node = next((node for node in request['public']['nodes'] if node['id'] == EXAMPLE_NODE), None)
    rendered['document'] = node.get('document') if node else None
    (directory / 'contract-example.json').write_text(json.dumps(rendered, indent=2) + '\n')

    # The same checker decides whether the emitted bytes may be run.
    report = evaluate(load(directory), preparation_only=True)
    gate = [row for row in report['assertions'] if row['form'] == 'emitted' and row['id'] in preparation_rows()]
    if any(row['status'] != 'pass' for row in gate):
        _write_report(directory, report)
        return 1
    emitted = (directory / 'example-1.stdout').read_bytes()
    source = json.loads(emitted)
    account = {}
    for form, document in derivatives(source).items():
        problems = [f'{name}: {text}' for name, text in transformation_problems(source, document, form)]
        assert not problems, problems
        base = directory / form
        base.mkdir()
        (base / 'input.json').write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')
        account[form] = {'operation': TRANSFORMATION_ROWS[form][3], 'problems': problems,
                         'removed': ['phases'] if form == 'flat' else ['policy'],
                         'added': ['probe_plan'] if form == 'flat' else ['actors', 'phases[].actor_id'],
                         'relocated': 'phases[].actions -> probe_plan' if form == 'flat' else 'policy -> actors[0].sandbox.policy',
                         'preserved': 'all other members, ordered action objects and policy bytes'}
    (directory / 'transformations.json').write_text(json.dumps(account, indent=2) + '\n')
    for name, body in refusal_inputs(emitted).items():
        base = directory / 'refusals' / name
        base.mkdir(parents=True)
        (base / 'input.json').write_bytes(body)
    print('prepared: the emitted document is within the bounds this case runs', flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('prepare')
    command.add_argument('capture')
    command.add_argument('app')
    command.add_argument('snapshot')
    commands.add_parser('evaluate').add_argument('capture')
    command = commands.add_parser('observe')
    command.add_argument('capture')
    command.add_argument('form', choices=FORMS)
    command.add_argument('when', choices=('before', 'after'))
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        return prepare(args.capture, args.app, args.snapshot)
    if args.command == 'observe':
        base = Path(args.capture) if args.form == 'emitted' else Path(args.capture) / args.form
        path = base / ('example-1.stdout' if args.form == 'emitted' else 'input.json')
        observe(base, 'targets-' + args.when, json.loads(path.read_bytes()))
        return 0
    inputs = load(args.capture)
    report = evaluate(inputs)
    # The summary is added to a finished report: no row is computed after it or from it.
    report['diagnostic_summary'] = diagnostic_summary(inputs, report)
    _write_report(args.capture, report)
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
