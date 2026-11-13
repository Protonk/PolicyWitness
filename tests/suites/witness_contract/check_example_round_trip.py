#!/usr/bin/env python3
"""Check the passage of the app's own example from `example` through `run`.

The case supplies no specimen. The document is whatever the selected app
printed; this checker reads retained captures of the commands the case ran,
changes the printed bytes in one place for each refusal, observes the attempt
targets itself, and reads the run envelope with the shared consumer. Identity,
digest and echo expectations are derived from the printed document or another
output of the same app. Shape, record, ordering and outcome-mapping rules
belong to the consumer and the controller; this file restates none of them.

Two expectations are the case's own. The document must hold at least one
paired, read-only probe, and under observed prerequisites the native results
must meet the expectations pinned to the present example: a validator `allow`
before a read that succeeds, with the targets unchanged. Nothing here states
that a prediction and an attempt agree.

Every assertion has a stable identifier, one group and one classification.
A failure prints its identifier and classification; `report.json` holds every
assertion's result, with consistency apart from native observations.

    prepare CAPTURE APP SNAPSHOT   gate the emission, observe, write refusal inputs
    observe-after CAPTURE          observe the targets again
    evaluate CAPTURE               read the retained captures and report
"""
import argparse
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
READ_ONLY_FILE_ACTIONS = ('open_read', 'access')
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
        ('bounds.ordinary_form', 'bounds', CONSISTENCY, 'the document is the ordinary form with a nonempty `probe_plan`'),
        ('bounds.paired_read_probe', 'bounds', CONSISTENCY,
         'at least one step pairs a `sandbox_check` with a read-only file attempt'),
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
         'each attempt target resolves to a regular file the test user can open and read'),
        ('native.completion', 'native', NATIVE_OBSERVATION, "the reply's `normalized_outcome` is `finished`"),
        ('native.prediction', 'native', NATIVE_OBSERVATION, 'each prediction is a validator `allow` with `native_rc` 0'),
        ('native.order', 'native', NATIVE_OBSERVATION, 'given that prediction, `order` is `query_first`'),
        ('native.attempt', 'native', NATIVE_OBSERVATION, 'each attempt has outcome `ok` and `rc` 0'),
        ('native.targets_unchanged', 'native', NATIVE_OBSERVATION,
         "each target's digest, length and selected metadata are equal before and after the run"),
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

def attempt_targets(document):
    targets = []
    for step in document.get('probe_plan') or []:
        attempt = step.get('attempt') if isinstance(step, dict) else None
        if isinstance(attempt, dict) and isinstance(attempt.get('target'), str) and attempt['target'] not in targets:
            targets.append(attempt['target'])
    return targets


def observe_target(target):
    record = {'target': target, 'resolved': None, 'regular_file': False, 'readable': False, 'error': None}
    try:
        resolved = os.path.realpath(target, strict=True)
        status = os.stat(resolved)
        record.update(resolved=resolved, regular_file=stat_module.S_ISREG(status.st_mode),
                      stat={field: getattr(status, field) for field in STAT_FIELDS})
        if record['regular_file']:
            data = Path(resolved).read_bytes()
            # A digest and length support the equality observation; the bytes are not retained.
            record.update(readable=True, sha256=hashlib.sha256(data).hexdigest(), length=len(data))
    except OSError as error:
        record['error'] = f'{type(error).__name__}: {error}'
    return record


def observe(directory, name, document):
    path = Path(directory) / (name + '.json')
    path.write_text(json.dumps({'targets': [observe_target(t) for t in attempt_targets(document)]}, indent=2) + '\n')


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class Results:
    def __init__(self):
        self.rows = {}

    def record(self, ident, problems, passed=None):
        """`problems` is a list of explanations; empty means the assertion holds."""
        assert ident in CLASSIFICATION and ident not in self.rows, ident
        problems = [problems] if isinstance(problems, str) else list(problems)
        self.rows[ident] = {'status': 'fail' if problems else 'pass', 'explanation': '; '.join(problems) or passed}

    def unevaluated(self, ident, reason):
        assert ident in CLASSIFICATION and ident not in self.rows, ident
        self.rows[ident] = {'status': 'not_evaluated', 'explanation': reason}

    def failed(self, *identifiers):
        return any(self.rows.get(ident, {}).get('status') == 'fail' for ident in identifiers)

    def rest(self, group_or_prefix, reason):
        for ident, group, _, _ in ASSERTIONS:
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


def _bounds(document, results):
    plan = document.get('probe_plan')
    ordinary = []
    for key in ('actors', 'phases'):
        if document.get(key) is not None:
            ordinary.append(f'the document carries `{key}`')
    if not isinstance(plan, list) or not plan or any(not isinstance(step, dict) for step in plan):
        ordinary.append('`probe_plan` is not a nonempty array of objects')
    results.record('bounds.ordinary_form', ordinary)
    steps = [step for step in plan if isinstance(step, dict)] if isinstance(plan, list) else []

    def read_only(attempt):
        return isinstance(attempt, dict) and attempt.get('kind') == 'file' and attempt.get('action') in READ_ONLY_FILE_ACTIONS

    paired = [step for step in steps if isinstance(step.get('sandbox_check'), dict) and read_only(step.get('attempt'))]
    results.record('bounds.paired_read_probe', [] if paired else 'no step pairs a `sandbox_check` with a read-only file attempt')
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
    """(submitted step, first reply step with its identifier) for each submitted step that has one."""
    replied = [step for step in reply.get('steps') or [] if isinstance(step, dict)] if isinstance(reply.get('steps'), list) else []
    pairs = []
    for submitted in document['probe_plan']:
        match = next((step for step in replied if step.get('step_id') == submitted.get('step_id')), None)
        if match is not None:
            pairs.append((submitted, match))
    return pairs


def _echo(document, reply, pairs, results):
    results.record('echo.specimen_id', [] if reply.get('specimen_id') == document.get('specimen_id') else
                   f'the reply carries {_spell(reply.get("specimen_id"))}; the document carries {_spell(document.get("specimen_id"))}')
    submitted_ids = [step.get('step_id') for step in document['probe_plan']]
    replied_ids = [step.get('step_id') if isinstance(step, dict) else None for step in reply.get('steps') or []] \
        if isinstance(reply.get('steps'), list) else None
    results.record('echo.step_ids', [] if replied_ids == submitted_ids else
                   f'the reply lists {_spell(replied_ids)}; the document lists {_spell(submitted_ids)}')
    if not pairs:
        for ident in ('echo.queries', 'echo.attempts'):
            results.unevaluated(ident, 'no reply step carries a submitted step identifier')
        return
    queries, attempts = [], []
    for submitted, replied in pairs:
        label = _spell(submitted.get('step_id'))
        query = submitted.get('sandbox_check')
        if isinstance(query, dict):
            answer = replied.get('sandbox_check') if isinstance(replied.get('sandbox_check'), dict) else {}
            for name, sent, echoed in (('operation', query.get('operation'), answer.get('operation')),
                                       ('filter kind', _get(query, 'filter', 'kind'), answer.get('filter_kind')),
                                       ('filter value', _get(query, 'filter', 'value'), answer.get('filter_value'))):
                if sent != echoed:
                    queries.append(f'step {label} {name}: submitted {_spell(sent)}, echoed {_spell(echoed)}')
        attempt = submitted.get('attempt')
        if isinstance(attempt, dict):
            answer = replied.get('attempt') if isinstance(replied.get('attempt'), dict) else {}
            for name, sent, echoed in (('kind', attempt.get('kind'), answer.get('requested_kind')),
                                       ('action', attempt.get('action'), answer.get('requested_action')),
                                       ('target', attempt.get('target'), answer.get('requested_path'))):
                if sent != echoed:
                    attempts.append(f'step {label} {name}: submitted {_spell(sent)}, echoed {_spell(echoed)}')
    results.record('echo.queries', queries)
    results.record('echo.attempts', attempts)


def _exact_int(value, expected):
    return type(value) is int and value == expected


def _native(inputs, document, reply, pairs, results):
    results.record('native.completion', [] if reply.get('normalized_outcome') == 'finished' else
                   f'the reply\'s `normalized_outcome` is {_spell(reply.get("normalized_outcome"))}')
    if not pairs:
        for ident in ('native.prediction', 'native.order', 'native.attempt'):
            results.unevaluated(ident, 'no reply step carries a submitted step identifier')
    else:
        predictions, orders, attempts, predicted = [], [], [], 0
        for submitted, replied in pairs:
            label = _spell(submitted.get('step_id'))
            if isinstance(submitted.get('sandbox_check'), dict):
                query = replied.get('sandbox_check') if isinstance(replied.get('sandbox_check'), dict) else {}
                found = {key: query.get(key) for key in ('result_source', 'outcome', 'native_rc')}
                if found['result_source'] == 'validator' and found['outcome'] == 'allow' and _exact_int(found['native_rc'], 0):
                    predicted += 1
                    order = _get(replied, 'comparison', 'order')
                    if order != 'query_first':
                        orders.append(f'step {label} `order` is {_spell(order)}')
                else:
                    predictions.append(f'step {label} prediction is {_spell(found)}')
            if isinstance(submitted.get('attempt'), dict):
                attempt = replied.get('attempt') if isinstance(replied.get('attempt'), dict) else {}
                if attempt.get('outcome') != 'ok' or not _exact_int(attempt.get('rc'), 0):
                    attempts.append(f'step {label} attempt has outcome {_spell(attempt.get("outcome"))} and rc {_spell(attempt.get("rc"))}')
        results.record('native.prediction', predictions)
        if predicted:
            results.record('native.order', orders)
        else:
            results.unevaluated('native.order', 'no prediction met its expectation')
        results.record('native.attempt', attempts)
    before = {record['target']: record for record in _get(inputs['targets-before'], 'targets') or []}
    after = {record.get('target'): record for record in _get(inputs['targets-after'], 'targets') or []
             if isinstance(record, dict)}
    changed = []
    for target, earlier in before.items():
        later = after.get(target)
        if later is None or not later.get('readable'):
            changed.append(f'{target} was not read after the run')
            continue
        differing = [field for field in STAT_FIELDS if _get(earlier, 'stat', field) != _get(later, 'stat', field)]
        if earlier.get('resolved') != later.get('resolved'):
            differing.insert(0, 'resolved path')
        if not isinstance(earlier.get('sha256'), str) or earlier.get('sha256') != later.get('sha256'):
            differing.insert(0, 'digest')
        if type(earlier.get('length')) is not int or earlier.get('length') != later.get('length'):
            differing.insert(0, 'length')
        if differing:
            changed.append(f'{target} differs in ' + ', '.join(differing))
    results.record('native.targets_unchanged', changed)


def _prerequisites(inputs, document, results):
    observed = _get(inputs['targets-before'], 'targets')
    problems = []
    if not isinstance(observed, list) or any(not isinstance(record, dict) for record in observed):
        problems.append('the targets were not observed before the run')
    else:
        records = {record.get('target'): record for record in observed}
        for target in attempt_targets(document):
            record = records.get(target)
            if record is None:
                problems.append(f'{target} was not observed')
            elif not record.get('regular_file') or not record.get('readable'):
                problems.append(f'{target} is not a readable regular file' + (f' ({record["error"]})' if record.get('error') else ''))
    results.record('prerequisite.targets_readable', problems)
    return not problems


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


def evaluate(inputs, *, authored_fixture=False):
    """Every assertion's result from retained inputs.

    `authored_fixture` admits constructed JSON host bytes, for the offline
    controls only; a live capture is read as the controller retained it.
    """
    results = Results()
    emitted, document = _emission(inputs, results)
    if document is None:
        for ident, group, _, _ in ASSERTIONS:
            if ident not in results.rows:
                results.unevaluated(ident, 'the first emission supplied no document')
        return _report(results, [])
    _bounds(document, results)
    _passage(inputs, document, results)
    gate = [ident for ident, group, _, _ in ASSERTIONS if group in ('emission', 'bounds')]
    if results.failed(*gate):
        for ident, group, _, _ in ASSERTIONS:
            if ident not in results.rows:
                results.unevaluated(ident, 'no run was attempted: the emission or its bounds did not hold')
        return _report(results, [])

    prerequisites = _prerequisites(inputs, document, results)
    _refusals(inputs, emitted, document, results)

    run = inputs['run']
    envelope, problem = _json(run['stdout'])
    if run['exit'] is None or problem or not isinstance(envelope, dict):
        results.record('execution.admitted_reply',
                       'the run was not captured' if run['exit'] is None else
                       'the run printed no envelope: stdout is ' + (problem or 'not an object'))
        for ident, _, _, _ in ASSERTIONS:
            if ident not in results.rows:
                results.unevaluated(ident, 'the run supplied no envelope')
        return _report(results, [])

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
    digest = hashlib.sha256(_get(document, 'policy', 'sbpl_source').encode('utf-8')).hexdigest() \
        if isinstance(_get(document, 'policy', 'sbpl_source'), str) else None
    dossier = _get(data, 'specimen', 'policy', 'augmentation', 'original_sha256')
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
        return _report(results, errors)
    reply = consumer.admitted_reply(envelope, contract, allow_fixture_json=authored_fixture)
    if reply is None:
        results.record('execution.admitted_reply', 'the envelope\'s evidence admits no runner reply '
                       f'(`result.normalized_outcome` is {_spell(outcome)})')
        for prefix in dependent:
            results.rest(prefix, 'no admitted reply: nothing is credited or faulted from it')
        return _report(results, errors)
    results.record('execution.admitted_reply', [])

    results.record('admission.reply_policy_digest', [] if digest is not None and reply.get('policy_sha256') == digest else
                   f'the reply records {_spell(reply.get("policy_sha256"))}; the document\'s policy source has SHA-256 {_spell(digest)}')
    pairs = _matched_steps(document, reply)
    _echo(document, reply, pairs, results)
    diagnostics = data.get('runner_sandbox_diagnostics') if isinstance(data.get('runner_sandbox_diagnostics'), dict) else {}
    results.record('readers.disposition_integrity', [] if diagnostics.get('disposition_integrity') == 'valid' else
                   f'`disposition_integrity` is {_spell(diagnostics.get("disposition_integrity"))}')
    results.record('readers.disposition_issues', [] if diagnostics.get('disposition_issues') == [] else
                   f'`disposition_issues` is {_spell(diagnostics.get("disposition_issues"))}')
    if prerequisites:
        _native(inputs, document, reply, pairs, results)
    else:
        results.rest('native.', 'a target prerequisite was not observed')
    return _report(results, errors)


def _report(results, consumer_errors):
    missing = [ident for ident, _, _, _ in ASSERTIONS if ident not in results.rows]
    assert not missing, missing
    assertions = [dict(id=ident, group=group, classification=classification, statement=statement, **results.rows[ident])
                  for ident, group, classification, statement in ASSERTIONS]
    failures = [row for row in assertions if row['status'] == 'fail']
    counts = {}
    for row in assertions:
        bucket = counts.setdefault(row['classification'], {'pass': 0, 'fail': 0, 'not_evaluated': 0})
        bucket[row['status']] += 1
    return {'schema_version': 1, 'status': 'fail' if failures else 'pass',
            'classifications': sorted({row['classification'] for row in failures}),
            'counts_by_classification': counts,
            'failures': [{'id': row['id'], 'classification': row['classification'], 'explanation': row['explanation']}
                         for row in failures],
            'not_evaluated': [{'id': row['id'], 'reason': row['explanation']} for row in assertions
                              if row['status'] == 'not_evaluated'],
            'consumer_errors': list(consumer_errors), 'assertions': assertions}


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
    observe(directory, 'targets-before', json.loads(emitted.decode('utf-8')))
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
    for name in ('observe-after', 'evaluate'):
        commands.add_parser(name).add_argument('capture')
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        return prepare(args.capture, args.app, args.snapshot)
    if args.command == 'observe-after':
        emitted = (Path(args.capture) / 'example-1.stdout').read_bytes()
        observe(args.capture, 'targets-after', json.loads(emitted.decode('utf-8')))
        return 0
    report = evaluate(load(args.capture))
    _write_report(args.capture, report)
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
