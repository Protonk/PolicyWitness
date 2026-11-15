#!/usr/bin/env python3
"""Independent expectations for the developer read publisher and seven passages.

Publication, observed process status, internal validity and external correspondence
are separate obligations. Samples and fixture transitions live outside replaceable
run captures. Constructed controls are not evidence of native occurrence.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
from file_observation import fresh_content, fresh_identity, fresh_syscalls, target_changes

BOUND = 64  # Independently authored from the documented read_fresh bound.
SHORT_0 = b'a' * (BOUND - 1)
SHORT_1 = b'b' * (BOUND - 1)
LONG = SHORT_1 + b'cd'
PASSAGES = ('initial_a', 'updated_a', 'b', 'refusal', 'repair', 'denied_b', 'allowed_a')
UNKNOWN = 'test_input_unknown_field'
ALLOW = '(version 1)\n(allow default)'
PACKAGED = re.compile(r'(?:release:v[0-9]+\.[0-9]+\.[0-9]+|development:[0-9a-f]{64})')
IDENTITY_FIELDS = dict(device='st_dev', inode='st_ino', mode='st_mode', uid='st_uid', gid='st_gid')


def get(value, *path):
    for key in path:
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and isinstance(key, int) and 0 <= key < len(value):
            value = value[key]
        else:
            return None
    return value


def mapping(value):
    return value if isinstance(value, dict) else {}


def parsed(raw):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def exact(found, wanted):
    return type(found) is type(wanted) and found == wanted


def expected_document(identity, target):
    # Authored here, never loaded from the product's embedded template.
    return dict(contract=identity, specimen_id='test-input', policy=dict(format='sbpl', sbpl_source=ALLOW),
                probe_plan=[dict(step_id='read-target',
                    sandbox_check=dict(operation='file-read-data', filter=dict(kind='path', value=target)),
                    attempt=dict(kind='file', action='read_fresh', target=target))])


def policy_for(target):
    # JSON string escaping is also SBPL string escaping for these owned paths.
    return ALLOW + '\n(deny file-read-data (literal ' + json.dumps(target) + ') (with no-report))'


class Results:
    def __init__(self):
        self.rows = []

    def check(self, ident, ok, detail='', *, available=True):
        assert not any(row['id'] == ident for row in self.rows), ident
        self.rows.append(dict(id=ident, status=('passed' if ok else 'failed') if available else 'not_evaluated',
                              detail=detail))

    def report(self):
        return dict(ok=all(row['status'] == 'passed' for row in self.rows), rows=self.rows)


def diagnostics(report):
    return {(row['id'], row['status']) for row in report['rows'] if row['status'] != 'passed'}


def publication(publication):
    r = Results()
    identity = publication.get('identity')
    version = publication.get('version') or {}
    envelope = parsed(version.get('stdout'))
    r.check('publication.identity', isinstance(identity, str) and bool(PACKAGED.fullmatch(identity)) and
            publication.get('plist_contract') == identity and get(envelope, 'build', 'contract') == identity and get(envelope, 'data', 'contract') == identity and
            exact(version.get('exit'), 0) and version.get('stderr') == '', 'version, plist and packaged identity')
    snapshot = publication.get('snapshot')
    r.check('publication.snapshot', snapshot == {k: v for k, v in expected_document(identity, '$EFFECT').items()
                                               if k != 'contract'}, 'independent stamped read_input example')
    emissions = publication.get('emissions') or {}
    for name in ('a1', 'a2', 'literal') + (('b',) if 'b' in emissions else ()):
        emission = emissions.get(name) or {}
        raw = emission.get('stdout')
        r.check('publication.' + name + '.status', exact(emission.get('exit'), 0) and emission.get('stderr') == '',
                'publication must succeed with empty stderr')
        r.check('publication.' + name + '.framing', isinstance(raw, str) and raw.endswith('\n') and
                raw[:-1] == raw[:-1].rstrip(), 'one framing newline')
        r.check('publication.' + name + '.binding', parsed(raw) == expected_document(identity, get(publication, 'targets', name)),
                'exact independently authored body and caller target')
        r.check('publication.' + name + '.invocation', get(emission, 'argv', 1) == 'test-input' and
                emission.get('argv', [])[2:] == ['read', '--target', get(publication, 'targets', name)],
                'recorded invocation uses the independently requested target')
    r.check('publication.determinism', get(emissions, 'a1', 'stdout') is not None and
            get(emissions, 'a1', 'stdout') == get(emissions, 'a2', 'stdout'), 'repeated A bytes')
    return r.report()


def sample_ok(sample, target, payload):
    return isinstance(sample, dict) and sample.get('target') == target and sample.get('resolved') == target and \
        sample.get('regular_file') is True and sample.get('readable') is True and sample.get('error') is None and \
        exact(sample.get('length'), len(payload)) and sample.get('sha256') == hashlib.sha256(payload).hexdigest() and \
        exact(sample.get('prefix_length'), len(payload[:BOUND])) and \
        sample.get('prefix_sha256') == hashlib.sha256(payload[:BOUND]).hexdigest() and \
        all(type(get(sample, 'stat', field)) is int for field in IDENTITY_FIELDS.values()) and \
        exact(get(sample, 'stat', 'st_size'), len(payload))


def expected_inputs(state):
    a = expected_document(state['publication']['identity'], state['paths']['A'])
    b = expected_document(state['publication']['identity'], state['paths']['B'])
    refusal = copy.deepcopy(b)
    refusal['policy'][UNKNOWN] = True
    denied = copy.deepcopy(b)
    denied['policy']['sbpl_source'] = policy_for(state['paths']['B'])
    allowed = copy.deepcopy(a)
    allowed['policy'] = copy.deepcopy(denied['policy'])
    return dict(initial_a=a, updated_a=a, b=b, refusal=refusal, repair=b, denied_b=denied, allowed_a=allowed)


def evaluate(state, *, authored_fixture=False):
    r = Results()
    r.rows.extend(publication(state['publication'])['rows'])
    r.check('publication.targets', get(state, 'publication', 'targets', 'a1') == get(state, 'paths', 'A') and
            get(state, 'publication', 'targets', 'a2') == get(state, 'paths', 'A') and
            get(state, 'publication', 'targets', 'b') == get(state, 'paths', 'B'), 'acquisition targets bound to fixture paths')
    paths = state['paths']
    passages = state['passages']
    identity = state['publication']['identity']
    expected = expected_inputs(state)
    # The recipe and relationships belong to the experiment, outside any run capture.
    initial = get(passages, 'initial_a', 'before')
    updated = get(passages, 'updated_a', 'before')
    extended = state.get('extended_a')
    b_sample = get(passages, 'b', 'before')
    last_a = get(passages, 'allowed_a', 'before')
    samples = ((initial, paths['A'], SHORT_0), (updated, paths['A'], SHORT_1), (extended, paths['A'], LONG),
               (last_a, paths['A'], LONG), (b_sample, paths['B'], LONG))
    usable = all(sample_ok(*row) for row in samples)
    a_ids = [(get(sample, 'stat', 'st_dev'), get(sample, 'stat', 'st_ino'))
             for sample in (initial, updated, extended, last_a)]
    equal_fields = ('st_dev', 'st_mode', 'st_uid', 'st_gid', 'st_size')
    r.check('fixtures', BOUND > 1 and usable and len(set(a_ids)) == 1 and
            all(get(extended, 'stat', f) == get(b_sample, 'stat', f) for f in equal_fields) and
            get(extended, 'stat', 'st_ino') != get(b_sample, 'stat', 'st_ino'),
            'exact payload transitions, retained A identity, matched A/B metadata and distinct inodes')
    for name in PASSAGES:
        p = passages.get(name) or {}
        capture = p.get('capture') or {}
        document = parsed(capture.get('input'))
        raw_expected = get(state, 'publication', 'emissions', 'a1' if name in ('initial_a', 'updated_a') else 'b', 'stdout')
        same_bytes = name not in ('initial_a', 'updated_a', 'b') or capture.get('input') == raw_expected
        r.check(name + '.transformation', document == expected[name] and same_bytes, 'declared derivative or exact emitted bytes')
        target = paths['A' if name in ('initial_a', 'updated_a', 'allowed_a') else 'B']
        payload = SHORT_0 if name == 'initial_a' else SHORT_1 if name == 'updated_a' else LONG
        before, after = p.get('before'), p.get('after')
        readable = sample_ok(before, target, payload)
        readable_after = sample_ok(after, target, payload)
        changes = target_changes({target: before} if isinstance(before, dict) else {},
                                 {target: after} if isinstance(after, dict) else {})
        r.check(name + '.stability', not changes and isinstance(after, dict), str(changes), available=readable)
        r.check(name + '.after_fixture', readable_after, 'resolved regular file and exact bytes after passage')
        r.check(name + '.fixture', readable, 'resolved regular file and exact independently prepared bytes')
        run = capture.get('run') or {}
        envelope = parsed(run.get('stdout'))
        wanted_exit = 1 if name == 'refusal' else 0
        r.check(name + '.status', exact(run.get('exit'), wanted_exit) and
                exact(get(envelope, 'result', 'exit_code'), wanted_exit) and
                exact(get(envelope, 'result', 'ok'), name != 'refusal'), 'observed and published status independently pinned')
        identified = get(envelope, 'build', 'contract') == identity
        r.check(name + '.build', identified, 'envelope identity before reply interpretation')
        errors = consumer.validate(envelope, identity, allow_fixture_json=authored_fixture) if isinstance(envelope, dict) else ['no envelope']
        r.check(name + '.consumer', not errors, errors)
        reply = consumer.admitted_reply(envelope, identity, allow_fixture_json=authored_fixture) if identified else None
        if name == 'refusal':
            failure = dict(code='unknown_field', path=['policy', UNKNOWN])
            r.check(name + '.refusal', get(envelope, 'result', 'normalized_outcome') == 'bad_request' and
                    all(get(envelope, 'data', 'request_failure', k) == v for k, v in failure.items()) and
                    isinstance(reply, dict) and all(get(reply, 'request_failure', k) == v for k, v in failure.items()) and
                    reply.get('normalized_outcome') == 'bad_request' and reply.get('steps') == [] and
                    reply.get('runner_subprocess') is None and reply.get('validator_subprocess') is None and
                    not reply.get('phases'), 'exact host refusal and reported absence of execution records')
            continue
        available = isinstance(reply, dict)
        r.check(name + '.reply', available, 'identity-admitted ordinary reply')
        reply = mapping(reply)
        step = mapping(get(reply, 'steps', 0))
        digest = hashlib.sha256(expected[name]['policy']['sbpl_source'].encode()).hexdigest()
        association = reply.get('specimen_id') == 'test-input' and reply.get('policy_sha256') == digest and \
            get(envelope, 'data', 'specimen', 'policy', 'augmentation', 'original_sha256') == digest and \
            isinstance(reply.get('steps'), list) and len(reply['steps']) == 1 and step.get('step_id') == 'read-target' and \
            step.get('phase_id') == 'main' and get(step, 'sandbox_check', 'operation') == 'file-read-data' and \
            get(step, 'sandbox_check', 'filter_kind') == 'path' and get(step, 'sandbox_check', 'filter_value') == target and \
            get(step, 'attempt', 'requested_kind') == 'file' and get(step, 'attempt', 'requested_action') == 'read_fresh' and \
            get(step, 'attempt', 'requested_path') == target and not reply.get('actors') and \
            get(envelope, 'data', 'runner_client', 'request_delivery', 'bytes_written') == len(capture.get('input', '').encode()) - 1
        r.check(name + '.association', association, 'submitted IDs, policy digest, operands and delivery', available=available)
        worker = mapping(reply.get('runner_subprocess'))
        pid = worker.get('pid')
        worker_ok = type(pid) is int and pid > 0 and exact(reply.get('pid'), pid) and \
            reply.get('sandboxed_after_apply') is True and all(worker.get(k) is True for k in ('reaped', 'ready_byte_received', 'done_observed')) and \
            exact(worker.get('exit_code'), 0) and worker.get('term_signal') is None and \
            worker.get('collection_basis') == 'after_confirmed_reap' and reply.get('normalized_outcome') == 'finished'
        r.check(name + '.worker', worker_ok, 'applied, ready, completed and confirmed reap', available=available)
        phase = mapping(get(reply, 'phases', 0))
        order = mapping(phase.get('ordering'))
        collections_ok = isinstance(reply.get('phases'), list) and len(reply['phases']) == 1 and \
            phase.get('phase_id') == 'main' and exact(phase.get('ordinal'), 1) and phase.get('action_ids') == ['read-target'] and \
            phase.get('arrival_observed') is True and phase.get('completion_observed') is True and \
            phase.get('collection_status') == 'collected' and get(phase, 'validator_subprocess', 'reaped') is True and \
            get(phase, 'validator_subprocess', 'expected_step_ids') == ['read-target'] and \
            all(order.get(k) is True for k in ('collection_closed_before_proceed', 'proceed_set', 'proceed_observed', 'worker_lifetime_established')) and \
            order.get('validator_disposition') == 'reaped' and order.get('protocol_violations') == []
        r.check(name + '.collections', collections_ok, 'phase arrival/completion and collection/release chain', available=available)
        denied = name == 'denied_b'
        query = mapping(step.get('sandbox_check'))
        answered = query.get('result_source') == 'validator' and query.get('outcome') == ('deny' if denied else 'allow') and \
            exact(query.get('native_rc'), 1 if denied else 0) and exact(query.get('errno'), 0)
        r.check(name + '.query', answered, 'independent query result', available=available)
        # Order is credited only beside the expected answer, and never changes that answer's row.
        r.check(name + '.order', get(step, 'comparison', 'order') == 'query_first', 'query placed before the attempt',
                available=available and answered)
        attempt = mapping(step.get('attempt'))
        r.check(name + '.attempt', attempt.get('result_source') == 'worker' and
                exact(attempt.get('rc'), -1 if denied else 0) and exact(attempt.get('errno'), 1 if denied else None) and
                attempt.get('outcome') == ('read_failed' if denied else 'ok') and
                (get(attempt, 'fresh_read', 'open_rc') == -1 and get(attempt, 'fresh_read', 'open_errno') == 1 if denied else
                 not fresh_syscalls(attempt, BOUND)), 'independent syscall and aggregate results', available=available)
        if not denied:
            stable = available and readable and readable_after and not changes and association
            expected_identity = {key: get(before, 'stat', field) for key, field in IDENTITY_FIELDS.items()}
            r.check(name + '.identity', not fresh_identity(attempt, expected_identity, target), 'descriptor identity versus independent sample',
                    available=stable and exact(get(attempt, 'fresh_read', 'stat_rc'), 0))
            r.check(name + '.content', not fresh_content(attempt, before or {}, target), 'current bounded count and bytes versus independent sample',
                    available=stable and type(get(attempt, 'fresh_read', 'read_rc')) is int and get(attempt, 'fresh_read', 'read_rc') >= 0)
    return r.report()


def write_report(directory, report):
    (Path(directory) / 'report.json').write_text(encode(report))
    for row in report['rows']:
        if row['status'] != 'passed':
            print(row['id'], row['status'], row['detail'])
