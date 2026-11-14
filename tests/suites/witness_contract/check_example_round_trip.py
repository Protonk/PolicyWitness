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

Two expectations are the case's own. The document must be a read-only workload
of three steps over three targets, found by their relationships and never by a
label or a path:

    step 1   a `file-read-data` query on target A, and an `open_read` of A
    step 2   a `file-read-metadata` query on target B, and a `read_fresh` of target C
    step 3   a `file-read-data` query on B, and an `open_read` of B

Under observed prerequisites the native results must then meet the expectations
pinned to the present example: allow answers for steps 1 and 2 and a deny
answer for step 3, each before its attempt; a successful open of A; a
successful fresh read whose descriptor identity, count and bytes are those this
checker observed for C; a failed open of B with `EPERM`; a finished run whose
process exits 0; and unchanged targets. The policy source is not read to decide
any of this. Each step's answer and attempt are separate assertions. Nothing
here compares an answer with its attempt, states that they agree or assigns a
failure to the policy.

Every assertion has a stable identifier, one group and one classification.
A failure prints its identifier and classification; `report.json` holds every
assertion's result, with consistency apart from native observations.

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
import stat as stat_module
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer

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
STEPS = {
    'step1': 'step 1 (data-read query and open of target A)',
    'step2': 'step 2 (metadata query on target B beside a fresh read of target C)',
    'step3': 'step 3 (data-read query and open of target B)',
}
TARGETS = {
    'A': 'the target step 1 queries for data reads and opens',
    'B': 'the target step 2 queries for metadata reads and step 3 queries for data reads and opens',
    'C': 'the target step 2 reads through a fresh descriptor',
}
# The controller's selection keys, from the request surface's shape golden (collected from `runner_select.rs`).
SELECTOR_FIELDS = tuple(json.loads((Path(__file__).resolve().parents[2] / 'fixtures/contract/surfaces/request.json')
                                   .read_text())['controller_keys']['SELECTOR_FIELDS'])
ENTITLEMENT_KEY = 'required_entitlements'
RUNNER_SELECTION_KEYS = tuple(key for key in SELECTOR_FIELDS if key != ENTITLEMENT_KEY)
UNKNOWN_MEMBER = 'example_round_trip_unknown_member'
STAT_FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')

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


def _table():
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
        ('passage.delivery_length', 'passage', CONSISTENCY,
         "`request_delivery.bytes_written` is the document's length without its framing newline"),
        ('passage.contract_rendering', 'passage', CONSISTENCY,
         "the document without `contract` equals the contract snapshot's example"),
        ('bounds.ordinary_form', 'bounds', CONSISTENCY, 'the document has the required ordinary request container and action partition'),
        ('bounds.workload_roles', 'bounds', CONSISTENCY,
         'the plan is three steps: a `file-read-data` query and `open_read` of one target A; a `file-read-metadata` '
         'query on a second target B with a `read_fresh` of a third target C; a `file-read-data` query and '
         '`open_read` of B'),
        ('bounds.read_only_attempts', 'bounds', CONSISTENCY, 'every attempt is a read-only file action'),
        ('bounds.no_test_overrides', 'bounds', CONSISTENCY, 'the document carries no `_test_overrides`'),
        ('bounds.no_runner_selection', 'bounds', CONSISTENCY, 'the document carries no runner selection field'),
        ('bounds.no_augments', 'bounds', CONSISTENCY, 'the policy names no augments'),
        ('bounds.no_entitlement_requirement', 'bounds', CONSISTENCY, 'the document requires no entitlement'),
        ('admission.no_request_failure', 'admission', CONSISTENCY,
         'the run reports no `request_failure` and no `bad_request` outcome'),
        ('admission.dossier_policy_digest', 'admission', CONSISTENCY,
         "the dossier's original policy digest is the SHA-256 of the document's policy source"),
        ('admission.reply_policy_digest', 'admission', CONSISTENCY,
         "the reply's `policy_sha256` is the SHA-256 of the document's policy source"),
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
         'targets A, B and C are each a regular file the test user opened and read before the run'),
        ('prerequisite.distinct_identities', 'native', PREREQUISITE_UNESTABLISHED,
         'targets A, B and C have three distinct device and inode identities'),
        ('prerequisite.distinguishing_prefixes', 'native', PREREQUISITE_UNESTABLISHED,
         "each target's bounded prefix is nonempty, and C's differs from A's and from B's"),
        ('native.process_status', 'native', NATIVE_OBSERVATION,
         'the captured exit status of the `run` process is 0, whatever the envelope reports'),
        ('native.completion', 'native', NATIVE_OBSERVATION, "the reply's `normalized_outcome` is `finished`"),
        ('native.step1.prediction', 'native', NATIVE_OBSERVATION,
         STEPS['step1'] + ': the answer about A is a validator `allow` with `native_rc` 0'),
        ('native.step2.prediction', 'native', NATIVE_OBSERVATION,
         STEPS['step2'] + ': the answer about B is a validator `allow` with `native_rc` 0'),
        ('native.step3.prediction', 'native', NATIVE_OBSERVATION,
         STEPS['step3'] + ': the answer about B is a validator `deny` with `native_rc` 1 and a query `errno` of 0'),
        ('native.order', 'native', NATIVE_OBSERVATION,
         'each step whose answer met its expectation records `order` `query_first`'),
        ('native.step1.attempt', 'native', NATIVE_OBSERVATION,
         STEPS['step1'] + ': the open of A is a worker result with outcome `ok` and `rc` 0'),
        ('native.step2.attempt', 'native', NATIVE_OBSERVATION,
         STEPS['step2'] + ': the fresh read of C is a worker result with outcome `ok` and `rc` 0'),
        ('native.step2.fresh_syscalls', 'native', NATIVE_OBSERVATION,
         STEPS['step2'] + ': the open returned a descriptor, and the descriptor stat, the bounded read and the '
         'close each succeeded'),
        ('native.step2.fresh_identity', 'native', NATIVE_OBSERVATION,
         STEPS['step2'] + ": the descriptor's device and inode are those this checker observed for C"),
        ('native.step2.fresh_content', 'native', NATIVE_OBSERVATION,
         STEPS['step2'] + ": the read count and the bytes read are the length and digest of C's bounded prefix "
         'as this checker observed it'),
        ('native.step3.attempt', 'native', NATIVE_OBSERVATION,
         STEPS['step3'] + ': the open of B is a worker result with outcome `open_failed` and an attempt `errno` '
         'of exactly 1 (`EPERM`)'),
        ('native.targets_unchanged', 'native', NATIVE_OBSERVATION,
         "each target's digest, length, bounded prefix and selected metadata are equal before and after the run"),
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
    return tuple(rows)


ASSERTIONS = _table()
CLASSIFICATION = {ident: classification for ident, _, classification, _ in ASSERTIONS}

EXECUTION_ASSERTIONS = tuple(row for row in ASSERTIONS if row[1] not in ('emission', 'bounds', 'passage', 'refusals')
                             or row[0] == 'passage.delivery_length')


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

def workload_roles(document):
    """The step identifiers and targets of the three roles, or the reasons the document is another workload.

    Roles are positions and relationships among submitted operands. No step
    identifier, path or policy text decides one.
    """
    steps = actions(document)
    if len(steps) != 3 or any(not isinstance(step, dict) for step in steps):
        return None, [f'the document holds {len(steps)} step(s) where this workload has three']

    def half(step):
        query, attempt = step.get('sandbox_check'), step.get('attempt')
        path = _get(query, 'filter', 'value') if _get(query, 'filter', 'kind') == 'path' else None
        action = _get(attempt, 'action') if _get(attempt, 'kind') == 'file' else None
        target = _get(attempt, 'target')
        return (_get(query, 'operation'), path if isinstance(path, str) else None, action,
                target if isinstance(target, str) else None)

    def matched_open(found):
        operation, path, action, target = found
        return operation == 'file-read-data' and action == 'open_read' and path is not None and path == target

    first, second, third = (half(step) for step in steps)
    problems = []
    if not matched_open(first):
        problems.append('step 1 is not a `file-read-data` path query with an `open_read` of the same target')
    if not (second[0] == 'file-read-metadata' and second[2] == 'read_fresh' and None not in (second[1], second[3])
            and second[1] != second[3]):
        problems.append('step 2 is not a `file-read-metadata` path query with a `read_fresh` of another target')
    if not matched_open(third):
        problems.append('step 3 is not a `file-read-data` path query with an `open_read` of the same target')
    identifiers = [step.get('step_id') for step in steps]
    if any(not isinstance(ident, str) for ident in identifiers) or len(set(identifiers)) != 3:
        problems.append('the step identifiers are not three distinct strings')
    if not problems:
        if third[1] != second[1]:
            problems.append('step 3 does not query and open the target step 2 queries')
        if first[1] in (second[1], second[3]):
            problems.append("step 1's target is also a target of step 2")
    if problems:
        return None, problems
    return {'steps': dict(zip(STEPS, identifiers)),
            'targets': {'A': first[1], 'B': second[1], 'C': second[3]}}, []


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


def observe_target(target):
    """One sample: identity and content read from one descriptor this process opened, then closed."""
    record = {'target': target, 'resolved': None, 'regular_file': False, 'readable': False, 'error': None}
    try:
        record['resolved'] = os.path.realpath(target, strict=True)
        descriptor = os.open(target, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as error:
        record['error'] = f'{type(error).__name__}: {error}'
        return record
    try:
        status = os.fstat(descriptor)
        record.update(regular_file=stat_module.S_ISREG(status.st_mode),
                      stat={field: getattr(status, field) for field in STAT_FIELDS})
        if record['regular_file']:
            data = b''
            while chunk := os.read(descriptor, 1 << 20):
                data += chunk
            prefix = data[:FRESH_READ_BOUND]
            # Digests and lengths support the equality observations; the bytes are not retained.
            record.update(readable=True, sha256=hashlib.sha256(data).hexdigest(), length=len(data),
                          prefix_sha256=hashlib.sha256(prefix).hexdigest(), prefix_length=len(prefix))
    except OSError as error:
        record['error'] = f'{type(error).__name__}: {error}'
    finally:
        os.close(descriptor)
    return record


def observe(directory, name, document):
    path = Path(directory) / (name + '.json')
    path.write_text(json.dumps({'targets': [observe_target(t) for t in observed_paths(document)]}, indent=2) + '\n')


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class Results:
    def __init__(self, table=None):
        self.table = ASSERTIONS if table is None else table
        self.rows = {}

    def record(self, ident, problems, passed=None):
        """`problems` is a list of explanations; empty means the assertion holds."""
        assert ident in {row[0] for row in self.table} and ident not in self.rows, ident
        problems = [problems] if isinstance(problems, str) else list(problems)
        self.rows[ident] = {'status': 'fail' if problems else 'pass', 'explanation': '; '.join(problems) or passed}

    def unevaluated(self, ident, reason):
        assert ident in {row[0] for row in self.table} and ident not in self.rows, ident
        self.rows[ident] = {'status': 'not_evaluated', 'explanation': reason}

    def failed(self, *identifiers):
        return any(self.rows.get(ident, {}).get('status') == 'fail' for ident in identifiers)

    def rest(self, group_or_prefix, reason):
        for ident, group, _, _ in self.table:
            if ident not in self.rows and (group == group_or_prefix or ident.startswith(group_or_prefix)):
                self.unevaluated(ident, reason)


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


def _bounds(document, results, form='emitted'):
    ordinary = []
    if form == 'flat':
        plan = document.get('probe_plan')
        if not isinstance(plan, list) or not plan or any(not isinstance(step, dict) for step in plan):
            ordinary.append('`probe_plan` is not a nonempty array of objects')
        if 'phases' in document:
            ordinary.append('a flat document carries `phases`')
    else:
        phases = document.get('phases')
        if not isinstance(phases, list) or len(phases) != 2 or any(
                not isinstance(phase, dict) or set(phase) != {'phase_id', 'actions'} or
                not isinstance(phase.get('phase_id'), str) or not phase['phase_id'] or
                not isinstance(phase.get('actions'), list) or len(phase['actions']) != count
                for phase, count in zip(phases or [], (2, 1))):
            ordinary.append('emission must contain two ordinary phases with action counts 2 and 1')
        elif phases[0]['phase_id'] == phases[1]['phase_id']:
            ordinary.append('phase identifiers are not distinct')
        if 'probe_plan' in document:
            ordinary.append('the emitted document carries `probe_plan`')
    if document.get('actors') is not None:
        ordinary.append('the emitted document carries `actors`')
    results.record('bounds.ordinary_form', ordinary)
    steps = [step for step in actions(document) if isinstance(step, dict)]

    def read_only(attempt):
        return isinstance(attempt, dict) and attempt.get('kind') == 'file' and attempt.get('action') in READ_ONLY_FILE_ACTIONS

    roles, problems = workload_roles(document)
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
    """For each path read before the run, the ways its sample after the run differs."""
    after = _samples(inputs, 'targets-after') or {}
    changes = {}
    for target, earlier in (_samples(inputs, 'targets-before') or {}).items():
        if not (earlier.get('regular_file') and earlier.get('readable')):
            continue
        later = after.get(target)
        if later is None or not later.get('readable'):
            changes[target] = ['was not read after the run']
            continue
        differing = [field for field in STAT_FIELDS if _get(earlier, 'stat', field) != _get(later, 'stat', field)]
        if earlier.get('resolved') != later.get('resolved'):
            differing.insert(0, 'resolved path')
        for name, kind in (('prefix_sha256', str), ('prefix_length', int), ('sha256', str), ('length', int)):
            if type(earlier.get(name)) is not kind or earlier.get(name) != later.get(name):
                differing.insert(0, name)
        if differing:
            changes[target] = ['differs in ' + ', '.join(differing)]
    return changes


# The target each half of each step concerns. Its expectation was observed with that file present
# and readable, so it is read only when this checker read the file before the run.
CONCERNS = {('step1', 'query'): 'A', ('step1', 'attempt'): 'A', ('step2', 'query'): 'B', ('step2', 'attempt'): 'C',
            ('step3', 'query'): 'B', ('step3', 'attempt'): 'B'}


def _native(inputs, roles, reply, matched, echoed, ground, results):
    """Each pinned native expectation as its own assertion. No assertion reads an answer beside its attempt.

    An expectation that is read and not met fails whatever else is missing. One
    that is met passes only when every target prerequisite holds; `ground` says
    which targets were read and whether a pass is credited.
    """
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
            concerned = CONCERNS[role, half]
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

    def prediction(outcome, native_rc, errno=None):
        def problems(query):
            found = {key: query.get(key) for key in ('result_source', 'outcome', 'native_rc')}
            expected = {'result_source': 'validator', 'outcome': outcome, 'native_rc': native_rc}
            if errno is not None:
                found['errno'], expected['errno'] = query.get('errno'), errno
            if all(type(found[key]) is type(value) and found[key] == value for key, value in expected.items()):
                return []
            return [f'the answer is {_spell(found)}']
        return problems

    qualifying = [role for role, problems in (('step1', prediction('allow', 0)), ('step2', prediction('allow', 0)),
                                              ('step3', prediction('deny', 1, errno=0)))
                  if assertion(f'native.{role}.prediction', queries[role], problems)]
    if qualifying:
        orders = []
        for role in qualifying:
            order = _get(records[roles['steps'][role]][0], 'comparison', 'order')
            if order != 'query_first':
                orders.append(f'{STEPS[role]}: `order` is {_spell(order)}')
        settle('native.order', orders)
    else:
        results.unevaluated('native.order', 'no answer met its expectation')

    def succeeded(attempt):
        found = {key: attempt.get(key) for key in ('result_source', 'outcome', 'rc')}
        return [] if found['result_source'] == 'worker' and found['outcome'] == 'ok' and _exact_int(found['rc'], 0) \
            else [f'the attempt is {_spell(found)}']

    def refused(attempt):
        found = {key: attempt.get(key) for key in ('result_source', 'outcome', 'errno')}
        return [] if found['result_source'] == 'worker' and found['outcome'] == 'open_failed' \
            and _exact_int(found['errno'], EPERM) else [f'the attempt is {_spell(found)}']

    assertion('native.step1.attempt', attempts['step1'], succeeded)
    assertion('native.step2.attempt', attempts['step2'], succeeded)
    assertion('native.step3.attempt', attempts['step3'], refused)

    def fresh(read):
        return read.get('fresh_read') if isinstance(read.get('fresh_read'), dict) else {}

    def syscalls(attempt):
        read, problems = fresh(attempt), []
        # A successful open returns a descriptor, which is nonnegative and not zero by convention.
        if type(read.get('open_rc')) is not int or read['open_rc'] < 0:
            problems.append(f'`open_rc` is {_spell(read.get("open_rc"))}')
        for name in ('stat_rc', 'close_rc'):
            if not _exact_int(read.get(name), 0):
                problems.append(f'`{name}` is {_spell(read.get(name))}')
        if type(read.get('read_rc')) is not int or not 0 <= read['read_rc'] <= FRESH_READ_BOUND:
            problems.append(f'`read_rc` is {_spell(read.get("read_rc"))}')
        return problems
    assertion('native.step2.fresh_syscalls', attempts['step2'], syscalls)

    changes = _target_changes(inputs)
    settle('native.targets_unchanged', [f'{target} {change}' for target, found in changes.items() for change in found])

    # The correspondence with C needs one stable observation of C to compare against.
    target = roles['targets']['C']
    observed = (_samples(inputs, 'targets-before') or {}).get(target, {})
    source = attempts['step2'] if target not in changes else \
        (None, f'the samples of {target} before and after the run differ; no correspondence with it is claimed')
    expected = {'device': _get(observed, 'stat', 'st_dev'), 'inode': _get(observed, 'stat', 'st_ino')}

    def identity(attempt):
        found = {key: _get(fresh(attempt), 'identity', key) for key in ('device', 'inode')}
        return [] if all(type(found[key]) is int and found[key] == expected[key] for key in found) else \
            [f'the descriptor identity is {_spell(found)}; this checker observed {_spell(expected)} for {target}']

    def content(attempt):
        read, problems = fresh(attempt), []
        if not _exact_int(read.get('read_rc'), observed.get('prefix_length')):
            problems.append(f'`read_rc` is {_spell(read.get("read_rc"))}; this checker read a bounded prefix of '
                            f'{_spell(observed.get("prefix_length"))} bytes from {target}')
        try:
            digest = hashlib.sha256(bytes.fromhex(read.get('content_hex'))).hexdigest()
        except (TypeError, ValueError):
            digest = None
        if digest is None or digest != observed.get('prefix_sha256'):
            problems.append(f'the bytes read have SHA-256 {_spell(digest)}; the bounded prefix this checker read '
                            f'from {target} has {_spell(observed.get("prefix_sha256"))}')
        return problems

    def given(supplied, reason):
        """The fresh read's record, when the call that supplies this observation succeeded."""
        return source if source[0] is None or supplied(fresh(source[0])) else (None, reason)
    # A sample of C without a device and inode leaves nothing to compare an identity with. A sample
    # without a prefix differs from its later sample under the test above, which withholds both.
    identified = given(lambda read: _exact_int(read.get('stat_rc'), 0),
                       'the descriptor stat did not succeed; it supplies no identity')
    if identified[0] is not None and not all(type(value) is int for value in expected.values()):
        identified = (None, f'this checker\'s sample of {target} holds no device and inode to compare with')
    assertion('native.step2.fresh_identity', identified, identity)
    assertion('native.step2.fresh_content',
              given(lambda read: type(read.get('read_rc')) is int and read['read_rc'] >= 0,
                    'the bounded read did not succeed; it supplies no bytes'), content)


def _prerequisites(inputs, roles, results):
    """What this checker must have observed before a native expectation is credited.

    Returns the roles whose target it read before the run, and the reason no
    native pass is credited, which is None when every prerequisite holds.
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
    identities, prefixes = [], []
    for role in TARGETS:
        if any(type(part) is not int for part in identity(role)):
            identities.append(f'target {role} has no observed device and inode')
        if type(prefix(role)[0]) is not int or prefix(role)[0] < 1 or not isinstance(prefix(role)[1], str):
            prefixes.append(f'target {role} has no nonempty observed prefix')
    for first, second in (('A', 'B'), ('A', 'C'), ('B', 'C')):
        if not identities and identity(first) == identity(second):
            identities.append(f'targets {first} and {second} are one file: device and inode {_spell(list(identity(first)))}')
    for other in ('A', 'B'):
        if not prefixes and prefix(other) == prefix('C'):
            prefixes.append(f"target C's bounded prefix equals target {other}'s")
    results.record('prerequisite.distinct_identities', identities)
    results.record('prerequisite.distinguishing_prefixes', prefixes)
    return {'read': set(usable), 'uncredited': uncredited if identities or prefixes else None}


def _one_change(name, emitted, document, submitted):
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
        results.record(prefix + '.one_change', _one_change(name, emitted, document, capture['input']))
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


def evaluate_capture(inputs, *, authored_fixture=False, form='emitted', publication=True):
    """Every assertion's result from retained inputs.

    `authored_fixture` admits constructed JSON host bytes, for the offline
    controls only; a live capture is read as the controller retained it.
    """
    table = ASSERTIONS if publication else EXECUTION_ASSERTIONS
    results = Results(table)
    if publication:
        emitted, document = _emission(inputs, results)
        if document is not None:
            roles = _bounds(document, results, form)
            _passage(inputs, document, results)
        else:
            roles = None
        gate = [ident for ident, group, _, _ in table if group in ('emission', 'bounds')]
        if document is None or results.failed(*gate):
            for ident, _, _, _ in table:
                if ident not in results.rows:
                    results.unevaluated(ident, 'no run was attempted: the emission or its bounds did not hold')
            return _report(results, [], roles)
        _refusals(inputs, emitted, document, results)
    else:
        emitted = inputs.get('input')
        document, problem = _json(emitted)
        roles, problems = workload_roles(document) if isinstance(document, dict) else (None, ['no input'])
        if problem or problems:
            for ident, _, _, _ in table:
                results.unevaluated(ident, 'the derivative supplied no admitted workload')
            return _report(results, [], roles)
    ground = _prerequisites(inputs, roles, results)

    run = inputs['run']
    envelope, problem = _json(run['stdout'])
    if run['exit'] is None or problem or not isinstance(envelope, dict):
        results.record('execution.admitted_reply',
                       'the run was not captured' if run['exit'] is None else
                       'the run printed no envelope: stdout is ' + (problem or 'not an object'))
        for ident, _, _, _ in table:
            if ident not in results.rows:
                results.unevaluated(ident, 'the run supplied no envelope')
        return _report(results, [], roles)

    contract = document.get('contract')
    data = envelope.get('data') if isinstance(envelope.get('data'), dict) else {}
    client, carried = data.get('runner_client'), data.get('runner_result')
    written = _get(client, 'request_delivery', 'bytes_written')
    if client is None:
        results.unevaluated('passage.delivery_length', 'the envelope carries no client record')
    else:
        results.record('passage.delivery_length', [] if _exact_int(written, len(emitted) - 1) else
                       f'`request_delivery.bytes_written` is {_spell(written)}; the emitted document is '
                       f'{len(emitted) - 1} bytes without its framing newline')

    outcome = _get(envelope, 'result', 'normalized_outcome')
    refused = []
    if data.get('request_failure') is not None:
        refused.append('`data.request_failure` is ' + _spell(data['request_failure']))
    if outcome == 'bad_request':
        refused.append('`result.normalized_outcome` is "bad_request"')
    results.record('admission.no_request_failure', refused)
    policy = submitted_policy(document, form)
    digest = hashlib.sha256(policy['sbpl_source'].encode('utf-8')).hexdigest() if isinstance(policy.get('sbpl_source'), str) else None
    dossier = _get(data, 'specimen', 'policy', 'augmentation', 'original_sha256')
    if form == 'actor':
        wanted_actor = document['actors'][0]['actor_id']
        dossiers = [a for a in _get(data, 'specimen', 'actors') or [] if isinstance(a, dict) and a.get('actor_id') == wanted_actor]
        dossier = _get(dossiers[0], 'policy', 'augmentation', 'original_sha256') if len(dossiers) == 1 else None
    results.record('admission.dossier_policy_digest', [] if digest is not None and dossier == digest else
                   f'the dossier records {_spell(dossier)}; the document\'s policy source has SHA-256 {_spell(digest)}')

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
        return _report(results, errors, roles)
    reply = consumer.admitted_reply(envelope, contract, allow_fixture_json=authored_fixture)
    if reply is None:
        results.record('execution.admitted_reply', 'the envelope\'s evidence admits no runner reply '
                       f'(`result.normalized_outcome` is {_spell(outcome)})')
        for prefix in dependent:
            results.rest(prefix, 'no admitted reply: nothing is credited or faulted from it')
        return _report(results, errors, roles)
    results.record('execution.admitted_reply', [])

    policy_record = consumer.actor_record(reply, document['actors'][0]['actor_id']) if form == 'actor' else reply
    received = policy_record.get('policy_sha256')
    results.record('admission.reply_policy_digest', [] if digest is not None and received == digest else
                   f'the reply records {_spell(received)}; submitted policy SHA-256 is {_spell(digest)}')
    matched = _matched_steps(document, reply)
    echoed = _echo(document, reply, matched, results)
    diagnostics = data.get('runner_sandbox_diagnostics') if isinstance(data.get('runner_sandbox_diagnostics'), dict) else {}
    results.record('readers.disposition_integrity', [] if diagnostics.get('disposition_integrity') == 'valid' else
                   f'`disposition_integrity` is {_spell(diagnostics.get("disposition_integrity"))}')
    results.record('readers.disposition_issues', [] if diagnostics.get('disposition_issues') == [] else
                   f'`disposition_issues` is {_spell(diagnostics.get("disposition_issues"))}')
    _native(inputs, roles, reply, matched, echoed, ground, results)
    return _report(results, errors, roles)


def _report(results, consumer_errors, roles=None):
    missing = [ident for ident, _, _, _ in results.table if ident not in results.rows]
    assert not missing, missing
    assertions = [dict(id=ident, group=group, classification=classification, statement=statement, **results.rows[ident])
                  for ident, group, classification, statement in results.table]
    failures = [row for row in assertions if row['status'] == 'fail']
    counts = {}
    for row in assertions:
        bucket = counts.setdefault(row['classification'], {'pass': 0, 'fail': 0, 'not_evaluated': 0})
        bucket[row['status']] += 1
    # The roles let a reader of this file match each role-keyed statement to a submitted step and path.
    workload = None if roles is None else {
        'steps': {role: {'role': STEPS[role], 'step_id': ident} for role, ident in roles['steps'].items()},
        'targets': {role: {'role': TARGETS[role], 'path': path} for role, path in roles['targets'].items()}}
    return {'schema_version': 1, 'status': 'fail' if failures else 'pass', 'workload': workload,
            'classifications': sorted({row['classification'] for row in failures}),
            'counts_by_classification': counts,
            'failures': [{'id': row['id'], 'classification': row['classification'], 'explanation': row['explanation']}
                         for row in failures],
            'not_evaluated': [{'id': row['id'], 'reason': row['explanation']} for row in assertions
                              if row['status'] == 'not_evaluated'],
            'consumer_errors': list(consumer_errors), 'assertions': assertions}


# The example's request-to-evidence checks are separate from the general consumer.
STRUCTURE_ASSERTIONS = (
    ('structure.execution_form', 'structure', CONSISTENCY, 'the reply uses the submitted execution form'),
    ('structure.phase_membership', 'structure', CONSISTENCY, 'reply phases retain the exact submitted phase/action partition and order'),
    ('structure.collections', 'structure', CONSISTENCY, 'each submitted phase has its own complete collection and release chain'),
    ('structure.worker', 'structure', CONSISTENCY, 'the submitted worker was applied, completed and reaped under its owned process record'),
)
ACTOR_ASSERTIONS = (
    ('structure.actor_ownership', 'structure', CONSISTENCY, 'the submitted actor owns both visits, all steps and its controller projections'),
    ('structure.actor_application', 'structure', CONSISTENCY, 'the actor applied the submitted policy once and received its source digest'),
    ('structure.actor_equipment', 'structure', CONSISTENCY, 'the actor used selected equipment matched to its launched worker'),
)
TRANSFORM_STATEMENTS = {
    'flat': 'the flat derivative changes only phases into the ordered probe_plan',
    'actor': 'the actor derivative relocates the entire policy to one applied selected actor and assigns both phases',
}


def derivatives(document):
    """Construct the two test-owned request forms. Validation below is independent."""
    flat = copy.deepcopy(document)
    flat['probe_plan'] = [step for phase in flat.pop('phases') for step in phase['actions']]
    actor = copy.deepcopy(document)
    actor['actors'] = [{'actor_id': 'example-reader', 'equipment': 'selected',
                        'sandbox': {'mode': 'apply', 'policy': actor.pop('policy')}}]
    for phase in actor['phases']:
        phase['actor_id'] = 'example-reader'
    return {'flat': flat, 'actor': actor}


def transformation_problems(source, candidate, form):
    """Judge permitted fields and membership without calling the constructor."""
    if not isinstance(source, dict) or not isinstance(candidate, dict):
        return ['the source or derivative is not an object']
    problems = []
    if form == 'flat':
        if set(candidate) != (set(source) - {'phases'}) | {'probe_plan'}:
            problems.append('the flat member set differs')
        for key in source.keys() - {'phases'}:
            if candidate.get(key) != source[key]:
                problems.append(f'flat member {key} changed')
        steps = candidate.get('probe_plan')
        if not isinstance(steps, list) or len(steps) != 3:
            problems.append('flat does not hold exactly three actions')
        else:
            for index, (phase, action) in enumerate(((0, 0), (0, 1), (1, 0))):
                if steps[index] != source['phases'][phase]['actions'][action]:
                    problems.append(f'flat action {index} changed')
    else:
        if set(candidate) != (set(source) - {'policy'}) | {'actors'}:
            problems.append('the actor member set differs')
        for key in source.keys() - {'policy', 'phases'}:
            if candidate.get(key) != source[key]:
                problems.append(f'actor member {key} changed')
        actors = candidate.get('actors')
        actor = actors[0] if isinstance(actors, list) and len(actors) == 1 and isinstance(actors[0], dict) else {}
        actor_id = actor.get('actor_id')
        if set(actor) != {'actor_id', 'equipment', 'sandbox'} or not isinstance(actor_id, str) or not actor_id or \
                actor.get('equipment') != 'selected' or actor.get('sandbox') != {'mode': 'apply', 'policy': source.get('policy')}:
            problems.append('the sole applied selected actor does not preserve the entire policy')
        phases = candidate.get('phases')
        if not isinstance(phases, list) or len(phases) != 2:
            problems.append('actor does not hold two phases')
        else:
            for index, phase in enumerate(phases):
                if not isinstance(phase, dict) or set(phase) != set(source['phases'][index]) | {'actor_id'} or \
                        phase.get('actor_id') != actor_id or any(phase.get(k) != v for k, v in source['phases'][index].items()):
                    problems.append(f'actor phase {index} changed beyond its actor assignment')
    return problems


def _structure(inputs, document, form, base, *, authored_fixture):
    table = STRUCTURE_ASSERTIONS + (ACTOR_ASSERTIONS if form == 'actor' else ())
    results = Results(table)
    statuses = {r['id']: r['status'] for r in base['assertions']}
    if statuses.get('execution.admitted_reply') != 'pass':
        for ident, _, _, _ in table:
            results.unevaluated(ident, 'no identity-admitted reply')
        return _report(results, [])
    envelope = _json(inputs['run']['stdout'])[0]
    reply = consumer.admitted_reply(envelope, document['contract'], allow_fixture_json=authored_fixture)
    actor_form = form == 'actor'
    results.record('structure.execution_form', [] if consumer.actor_form(reply) == actor_form else 'the reply uses another execution form')
    expected = document['phases'] if form != 'flat' else [{'phase_id': 'main', 'actions': document['probe_plan']}]
    phases = reply.get('phases') if isinstance(reply.get('phases'), list) else []
    partition = [(p.get('phase_id'), p.get('ordinal'), p.get('action_ids')) if isinstance(p, dict) else None for p in phases]
    wanted = [(p['phase_id'], i, [s['step_id'] for s in p['actions']]) for i, p in enumerate(expected, 1)]
    results.record('structure.phase_membership', [] if partition == wanted else
                   f'reply partition {_spell(partition)} differs from submitted {_spell(wanted)}')
    collections = []
    for submitted in expected:
        matches = [p for p in phases if isinstance(p, dict) and p.get('phase_id') == submitted['phase_id']]
        if len(matches) != 1:
            collections.append(f'{submitted["phase_id"]}: no unique phase collection')
            continue
        phase = matches[0]
        validator = phase.get('validator_subprocess') or {}
        ordering = phase.get('ordering') or {}
        if any(phase.get(k) is not True for k in ('arrival_observed', 'completion_observed')) or \
                phase.get('collection_status') != 'collected' or validator.get('reaped') is not True or \
                any(ordering.get(k) is not True for k in ('collection_closed_before_proceed', 'proceed_set',
                                                         'proceed_observed', 'worker_lifetime_established')) or \
                ordering.get('validator_disposition') != 'reaped' or ordering.get('protocol_violations') != []:
            collections.append(f'{submitted["phase_id"]}: collection, completion or release is unestablished')
        # Internal ownership, query operand and PID joins belong to the full consumer.
        # Here an internally valid collection still has to name this submitted plan.
        if validator.get('expected_step_ids') != [s['step_id'] for s in submitted['actions']]:
            collections.append(f'{submitted["phase_id"]}: collection names another submitted query plan')
    results.record('structure.collections', collections)
    actor_id = document['actors'][0]['actor_id'] if actor_form else None
    actor = consumer.actor_record(reply, actor_id) if actor_form else {}
    worker = actor.get('subprocess') if actor_form else reply.get('runner_subprocess')
    worker = worker if isinstance(worker, dict) else {}
    pid = worker.get('pid')
    if actor_form:
        applied = actor.get('applied') is True and _get(actor, 'launch', 'pid') == pid and \
            _get(actor, 'launch', 'parent_pid') == reply.get('pid')
    else:
        applied = reply.get('sandboxed_after_apply') is True and reply.get('pid') == pid
    results.record('structure.worker', [] if applied and type(pid) is int and pid > 0 and
                   all(worker.get(k) is True for k in ('reaped', 'ready_byte_received', 'done_observed')) and
                   _exact_int(worker.get('exit_code'), 0) and worker.get('term_signal') is None and
                   worker.get('collection_basis') == 'after_confirmed_reap' else 'applied worker ownership, completion or reap is unestablished')
    if actor_form:
        data = envelope['data']
        actors = reply.get('actors') or []
        diagnostics = _get(data, 'runner_sandbox_diagnostics', 'actors') or []
        dossiers = _get(data, 'specimen', 'actors') or []
        ownership = []
        for label, records in (('reply', actors), ('diagnostics', diagnostics), ('dossier', dossiers)):
            if [a.get('actor_id') for a in records if isinstance(a, dict)] != [actor_id]:
                ownership.append(f'{label} does not name the sole submitted actor')
        if actor.get('visits') != [1, 2] or any(p.get('actor_id') != actor_id or p.get('actor_visit') != i
                                             for i, p in enumerate(phases, 1)) or \
                any(s.get('actor_id') != actor_id for s in reply.get('steps') or []):
            ownership.append('actor visit or step ownership differs')
        if any('termination_gate' in p for p in phases):
            ownership.append('a phase invents a termination dependency')
        for diagnostic in diagnostics:
            if diagnostic.get('disposition_integrity') != 'valid' or diagnostic.get('disposition_issues') != []:
                ownership.append('actor diagnostics do not establish valid disposition')
        results.record('structure.actor_ownership', ownership)
        digest = hashlib.sha256(submitted_policy(document, form)['sbpl_source'].encode()).hexdigest()
        results.record('structure.actor_application', [] if actor.get('mode') == 'apply' and
                       actor.get('setup_status') == 'applied' and actor.get('applied') is True and
                       _exact_int(actor.get('application_count'), 1) and
                       actor.get('application') == {'state': 'observed', 'basis': 'applied_publication'} and
                       actor.get('policy_received_sha256') == digest else 'single application or policy receipt differs')
        equipment = actor.get('equipment') or {}
        execution = equipment.get('execution') or {}
        results.record('structure.actor_equipment', [] if equipment.get('requested') == 'selected' and
                       equipment.get('resolved') == 'selected' and equipment.get('required_entitlements') == [] and
                       equipment.get('requirements_status') == 'satisfied' and execution.get('status') == 'matched' and
                       execution.get('eligible') is True and execution.get('pid') == pid else 'selected equipment is not matched to this actor worker')
    return _report(results, [])


def _diagnostic(inputs, document, form, rows):
    statuses = {r['id']: r['status'] for r in rows}
    required = ('identity.envelope_build', 'identity.client_transport', 'identity.reply_producer',
                'execution.admitted_reply', 'echo.specimen_id', 'echo.step_ids', 'echo.queries', 'echo.attempts',
                'structure.execution_form', 'structure.phase_membership') + (('structure.actor_ownership',) if form == 'actor' else ())
    record = {'form': form, 'samples': {key: inputs.get(key) for key in ('targets-before', 'targets-after')},
              'assertions': statuses, 'observations': None}
    if any(statuses.get(k) != 'pass' for k in required):
        record['withheld_reason'] = 'identity or submitted association is unestablished'
        return record
    reply = _json(inputs['run']['stdout'])[0]['data']['runner_result']
    roles = workload_roles(document)[0]
    observations = []
    for role, step_id in roles['steps'].items():
        step = next(s for s in reply['steps'] if s['step_id'] == step_id)
        query, attempt = step['sandbox_check'], step['attempt']
        fresh = attempt.get('fresh_read')
        observed = {'role': role, 'step_id': step_id, 'phase_id': step.get('phase_id'), 'actor_id': step.get('actor_id'),
                    'query': {k: query.get(k) for k in ('result_source', 'outcome', 'native_rc', 'errno')},
                    'attempt': {k: attempt.get(k) for k in ('result_source', 'outcome', 'rc', 'errno')}}
        if isinstance(fresh, dict):
            try:
                digest = hashlib.sha256(bytes.fromhex(fresh.get('content_hex'))).hexdigest()
            except (TypeError, ValueError):
                digest = None
            observed['fresh_read'] = {'identity': fresh.get('identity'), 'count': fresh.get('read_rc'), 'sha256': digest}
        observations.append(observed)
    record['observations'] = observations
    return record


def evaluate(inputs, *, authored_fixture=False):
    """One publication, three independent captures, no equality assertions."""
    emitted = evaluate_capture(inputs, authored_fixture=authored_fixture)
    source, _ = _json(inputs['example-1']['stdout'])
    prepared = all(r['status'] == 'pass' for r in emitted['assertions'] if r['group'] in ('emission', 'bounds'))
    forms, all_rows, summaries, errors = {}, [], [], []
    for form in ('emitted', 'flat', 'actor'):
        captured = inputs if form == 'emitted' else inputs['forms'][form]
        document = source if form == 'emitted' else _json(captured['input'])[0]
        transform = None if form == 'emitted' else transformation_problems(source, document, form) if prepared else ['emission is unestablished']
        if form != 'emitted':
            all_rows.append(dict(id=form + '.transformation', group='transformation', classification=CONSISTENCY,
                                 statement=TRANSFORM_STATEMENTS[form], status=('fail' if transform else 'pass') if prepared else 'not_evaluated',
                                 explanation='; '.join(transform) or None, form=form))
        if form == 'emitted':
            base = emitted
        elif prepared and not transform:
            base = evaluate_capture(captured, authored_fixture=authored_fixture, form=form, publication=False)
        else:
            withheld = Results(EXECUTION_ASSERTIONS)
            for ident, _, _, _ in withheld.table:
                withheld.unevaluated(ident, 'the emission or transformation is unestablished')
            base = _report(withheld, [])
        structure = _structure(captured, document, form, base, authored_fixture=authored_fixture)
        rows = base['assertions'] + structure['assertions']
        forms[form] = {'workload': base['workload'], 'consumer_errors': base['consumer_errors']}
        errors.extend(form + ': ' + error for error in base['consumer_errors'])
        summaries.append(_diagnostic(captured, document, form, rows))
        all_rows.extend(dict(row, id=(form + '.' if form != 'emitted' else '') + row['id'], form=form) for row in rows)
    results = Results(tuple((r['id'], r['group'], r['classification'], r['statement']) for r in all_rows))
    results.rows = {r['id']: {k: r[k] for k in ('status', 'explanation')} for r in all_rows}
    report = _report(results, errors)
    report['assertions'] = all_rows
    report.update(schema_version=2, forms=forms, diagnostic_summary=summaries)
    return report



def diagnostics(report):
    """The (assertion identifier, classification) pairs of a report's failures."""
    return {(row['id'], row['classification']) for row in report['failures']}


def render(report):
    lines = ['example round trip: ' + report['status'].upper() +
             (' (' + ', '.join(report['classifications']) + ')' if report['classifications'] else '')]
    for classification in (CONSISTENCY, EXECUTION_UNAVAILABLE, PREREQUISITE_UNESTABLISHED, NATIVE_OBSERVATION):
        counts = report['counts_by_classification'].get(classification)
        if counts:
            lines.append(f'  {classification}: {counts["pass"]} hold, {counts["fail"]} fail, '
                         f'{counts["not_evaluated"]} not evaluated')
    for row in report['failures']:
        lines.append(f'FAIL {row["id"]} [{row["classification"]}]: {row["explanation"]}')
    for row in report['not_evaluated']:
        lines.append(f'NOT EVALUATED {row["id"]}: {row["reason"]}')
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
    report = evaluate(load(directory))
    gate = [row for row in report['assertions'] if row['group'] in ('emission', 'bounds')]
    if any(row['status'] != 'pass' for row in gate):
        _write_report(directory, report)
        return 1
    emitted = (directory / 'example-1.stdout').read_bytes()
    source = json.loads(emitted)
    account = {}
    for form, document in derivatives(source).items():
        problems = transformation_problems(source, document, form)
        assert not problems, problems
        base = directory / form
        base.mkdir()
        (base / 'input.json').write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')
        account[form] = {'operation': TRANSFORM_STATEMENTS[form], 'problems': problems,
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
    command.add_argument('form', choices=('emitted', 'flat', 'actor'))
    command.add_argument('when', choices=('before', 'after'))
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        return prepare(args.capture, args.app, args.snapshot)
    if args.command == 'observe':
        base = Path(args.capture) if args.form == 'emitted' else Path(args.capture) / args.form
        path = base / ('example-1.stdout' if args.form == 'emitted' else 'input.json')
        observe(base, 'targets-' + args.when, json.loads(path.read_bytes()))
        return 0
    report = evaluate(load(args.capture))
    _write_report(args.capture, report)
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
