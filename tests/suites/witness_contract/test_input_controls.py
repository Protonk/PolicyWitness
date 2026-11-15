#!/usr/bin/env python3
"""Authored controls: exact diagnostics, coherent correspondence faults and real preflight."""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import sys

import check_test_input as checker
import test_input as driver
from blackbox import envelope_skeleton, recapture_host_reply
from file_observation import fresh_record

IDENTITY = 'development:' + '4' * 64
ROOT = Path(__file__).resolve().parents[3]
PATHS = dict(A='/private/tmp/constructed-test-input/A', B='/private/tmp/constructed-test-input/B')


def sample(target, payload, inode):
    return dict(target=target, resolved=target, regular_file=True, readable=True, error=None,
                stat=dict(st_dev=3, st_ino=inode, st_mode=33152, st_uid=501, st_gid=20,
                          st_size=len(payload), st_mtime_ns=100, st_ctime_ns=100),
                sha256=hashlib.sha256(payload).hexdigest(), length=len(payload),
                prefix_sha256=hashlib.sha256(payload[:checker.BOUND]).hexdigest(), prefix_length=len(payload[:checker.BOUND]))


def rewrite_line(record, **fields):
    """Change a validator record and the line it was parsed from together."""
    record.update(fields)
    raw = json.loads(record['raw_line'])
    raw.update(fields)
    record['raw_line'] = json.dumps(raw, separators=(',', ':'))


def reply_step(envelope, ident):
    return next(step for step in envelope['data']['runner_result']['steps'] if step['step_id'] == ident)


def set_answer(envelope, ident, denied):
    """One step's query answer, in the step and in its phase's collected record."""
    query = reply_step(envelope, ident)['sandbox_check']
    query.update(outcome='deny' if denied else 'allow', rc=int(denied), native_rc=int(denied), errno=0)
    record = next(record for phase in envelope['data']['runner_result']['phases']
                  for record in phase['validator_subprocess']['records'] if record['step_id'] == ident)
    rewrite_line(record, outcome=query['outcome'], rc=query['native_rc'], errno=0)


def set_query(envelope, denied, index=0):
    set_answer(envelope, envelope['data']['runner_result']['steps'][index]['step_id'], denied)


def refuse_read(envelope, ident):
    """A successful fresh read reported as the refused open, with its comparison record."""
    step = reply_step(envelope, ident)
    step['attempt'].update(rc=-1, errno=1, outcome='read_failed', fresh_read=dict(open_rc=-1, open_errno=1))
    step['comparison'].update(observation='permission_failure', observation_basis='permission_errno')


def fresh(envelope, ident):
    return reply_step(envelope, ident)['attempt']['fresh_read']


def replaced_before(state, name):
    """A's inode differs for one matrix passage; its samples and its reads agree with each other."""
    resample(state, [name], 44)
    mutate_capture(state, name, lambda e: [fresh(e, ident)['identity'].update(inode=44) for ident in ('read-aa', 'read-ba')])


def envelope(name, document, observed):
    if name == 'refusal':
        failure = dict(code='unknown_field', path=['policy', checker.UNKNOWN])
        result = envelope_skeleton(dict(normalized_outcome='bad_request', rc=1, error='constructed refusal',
                                        steps=[], phases=[], request_failure=failure))
        result['data']['request_failure'] = failure
        result['result']['error'] = 'constructed refusal'
    else:
        reply = json.loads((ROOT / 'tests/fixtures/contract/ordinary_phase_reply.json').read_text())
        reply.update(specimen_id='test-input', policy_sha256=hashlib.sha256(document['policy']['sbpl_source'].encode()).hexdigest())
        reply['steps'] = reply['steps'][:1]
        reply['phases'] = reply['phases'][:1]
        step, phase = reply['steps'][0], reply['phases'][0]
        target = document['probe_plan'][0]['attempt']['target']
        step.update(step_id='read-target', phase_id='main')
        step['sandbox_check'].update(filter_value=target)
        step['sandbox_check'].pop('path_diagnostics', None)
        attempt = step['attempt']
        attempt.update(requested_path=target)
        attempt['path_diagnostics'].update(input=target)
        phase.update(phase_id='main', action_ids=['read-target'])
        validator = phase['validator_subprocess']
        validator.update(phase_id='main', expected_step_ids=['read-target'])
        rewrite_line(validator['records'][0], step_id='read-target', filter_value=target)
        disposition = reply['runner_subprocess']['disposition']
        disposition['steps'] = disposition['steps'][:1]
        disposition['steps'][0].update(step_id='read-target', index=0)
        if name != 'denied_b':
            payload = checker.payload_for(name)
            fields = {key: observed['stat'][field] for key, field in checker.IDENTITY_FIELDS.items()}
            attempt.update(rc=0, errno=None, outcome='ok', fresh_read=fresh_record(payload, fields, bound=checker.BOUND))
            step['comparison'].update(observation='succeeded', observation_basis='completed_worker_status')
        result = envelope_skeleton(reply)
        set_query(result, name == 'denied_b')
        result['data']['specimen']['policy']['augmentation'].update(original_sha256=reply['policy_sha256'])
        result['data']['runner_sandbox_diagnostics'] = dict(process_disposition='clean_exit', termination_cause=None,
                stop_reason='done', disposition_integrity='valid', disposition_issues=[])
    result['build']['contract'] = IDENTITY
    result['data']['runner_result']['producer']['contract'] = IDENTITY
    result['data']['runner_client']['transport']['contract'] = IDENTITY
    return recapture_host_reply(result)


def matrix_envelope(document, observed):
    steps, records, dispositions = [], [], []
    for index, submitted in enumerate(document['probe_plan']):
        single = dict(document, probe_plan=[submitted])
        env = envelope('denied_b' if index in (1, 3, 4) else 'b', single, observed)
        set_query(env, index in (2, 3))
        reply = env['data']['runner_result']
        step = reply['steps'][0]
        step['step_id'] = submitted['step_id']
        query = submitted['sandbox_check']
        step['sandbox_check'].update(operation=query['operation'], filter_value=query['filter']['value'])
        step['comparison'].update(operation_relation='different' if index == 4 else 'matched',
                                  target_relation='different_submitted' if index in (1, 2) else 'same_submitted')
        record = reply['phases'][0]['validator_subprocess']['records'][0]
        rewrite_line(record, step_id=step['step_id'], operation=query['operation'], filter_value=query['filter']['value'])
        disposition = reply['runner_subprocess']['disposition']['steps'][0]
        disposition.update(step_id=step['step_id'], index=index)
        steps.append(step)
        records.append(record)
        dispositions.append(disposition)
    reply['steps'] = steps
    reply['phases'][0]['action_ids'] = [s['step_id'] for s in steps]
    reply['phases'][0]['validator_subprocess'].update(expected_step_ids=reply['phases'][0]['action_ids'], records=records)
    reply['runner_subprocess']['disposition']['steps'] = dispositions
    return recapture_host_reply(env)


def build():
    version = dict(argv=['constructed', '--version'], exit=0, stderr='', stdout=checker.encode(dict(
        build=dict(contract=IDENTITY), data=dict(contract=IDENTITY))))
    targets = dict(a1=PATHS['A'], a2=PATHS['A'], b=PATHS['B'], literal=driver.LITERAL_TARGET)
    emissions = {name: dict(argv=['constructed', 'test-input', 'read', '--target', target],
        stdout=checker.encode(checker.expected_document(IDENTITY, target)), stderr='', exit=0) for name, target in targets.items()}
    public = dict(identity=IDENTITY, plist_contract=IDENTITY, version=version,
        snapshot={k: v for k, v in checker.expected_document(IDENTITY, '$EFFECT').items() if k != 'contract'},
        targets=targets, emissions=emissions)
    state = dict(paths=dict(PATHS), publication=public, passages={}, extended_a=sample(PATHS['A'], checker.LONG, 41))
    documents = checker.expected_inputs(state)
    for name in checker.PASSAGES:
        letter = 'A' if name in ('initial_a', 'updated_a', 'allowed_a', 'crossed', 'returning') + checker.REPLACEMENTS else 'B'
        payload = checker.payload_for(name)
        observed = sample(PATHS[letter], payload, 43 if name in checker.REPLACEMENTS else 41 if letter == 'A' else 42)
        raw = checker.encode(documents[name])
        state['passages'][name] = dict(before=observed, after=copy.deepcopy(observed), capture=dict(input=raw,
            request_path='/constructed/input.json', run=run_record(name, documents[name], observed, raw)))
        if name in ('crossed', 'returning'):
            state['passages'][name]['peer'] = {t: sample(PATHS['B'], checker.LONG, 42) for t in ('before', 'after')}
        if name in checker.REPLACEMENTS:
            for key, target, inode in (('parked', PATHS['A'] + '.previous', 41), ('bystander', PATHS['B'], 42)):
                state['passages'][name][key] = {t: sample(target, checker.LONG, inode) for t in ('before', 'after')}
    state['replacement'] = dict(original=sample(PATHS['A'], checker.LONG, 41),
        prepared=sample(PATHS['A'] + '.replacement', checker.LONG, 43),
        renames=[[PATHS['A'], PATHS['A'] + '.previous'], [PATHS['A'] + '.replacement', PATHS['A']]])
    return state


def run_record(outcome, document, observed, raw):
    """A coherent run of `document` with the named passage's outcome, delivered as `raw`."""
    if outcome == 'returning':
        from test_input_actor_controls import envelope as actor_envelope
        env = actor_envelope(document, observed)
    else:
        env = matrix_envelope(document, observed) if outcome == 'crossed' else envelope(outcome, document, observed)
    env['data']['runner_client']['request_delivery']['bytes_written'] = len(raw.encode()) - 1
    return dict(argv=['constructed', 'run', '/constructed/input.json'], stdout=checker.encode(env), stderr='',
                exit=1 if outcome == 'refusal' else 0)


def other_outcome(state, name, outcome):
    """The passage's own request and delivery, reported with another passage's query and attempt results."""
    passage = state['passages'][name]
    raw = passage['capture']['input']
    passage['capture']['run'] = run_record(outcome, json.loads(raw), passage['before'], raw)
    mutate_capture(state, name, lambda e: set_query(e, name == 'denied_b'))


def resample(state, names, inode):
    for name in names:
        for moment in ('before', 'after'):
            state['passages'][name][moment]['stat']['st_ino'] = inode


def mutate_capture(state, name, change):
    run = state['passages'][name]['capture']['run']
    env = json.loads(run['stdout'])
    change(env)
    recapture_host_reply(env)
    run['stdout'] = checker.encode(env)


def attempt(env):
    return env['data']['runner_result']['steps'][0]['attempt']


def controls():
    failed = lambda *names: {(name, 'failed') for name in names}
    yield 'baseline', lambda s: None, set()
    yield 'descriptor_zero', lambda s: mutate_capture(s, 'b', lambda e: attempt(e)['fresh_read'].update(open_rc=0)), set()
    yield 'same_bytes_other_inode', lambda s: mutate_capture(s, 'b', lambda e: attempt(e)['fresh_read']['identity'].update(inode=41)), failed('b.identity')
    yield 'short_successful_read', lambda s: mutate_capture(s, 'b', lambda e: attempt(e)['fresh_read'].update(
        read_rc=checker.BOUND - 1, content_hex=checker.LONG[:checker.BOUND - 1].hex())), failed('b.content')
    for field, wrong in (('device', 4), ('mode', 33188), ('uid', 502), ('gid', 21)):
        yield 'wrong_identity_' + field, lambda s, field=field, wrong=wrong: mutate_capture(s, 'b',
            lambda e: attempt(e)['fresh_read']['identity'].update({field: wrong})), failed('b.identity')
    yield 'old_bytes_current_inode', lambda s: mutate_capture(s, 'updated_a', lambda e: attempt(e)['fresh_read'].update(content_hex=checker.SHORT_0.hex())), failed('updated_a.content')
    yield 'previous_whole_capture', lambda s: s['passages']['updated_a'].update(capture=copy.deepcopy(s['passages']['initial_a']['capture'])), failed('updated_a.content')
    yield 'missing_unknown_injection', lambda s: s['passages']['refusal'].update(capture=copy.deepcopy(s['passages']['b']['capture'])), failed('refusal.transformation', 'refusal.status', 'refusal.refusal')
    def exchanged(s):
        mutate_capture(s, 'denied_b', lambda e: set_query(e, False))
        mutate_capture(s, 'allowed_a', lambda e: set_query(e, True))
    yield 'exchanged_query_answers', exchanged, failed('denied_b.query', 'allowed_a.query') | {
        ('denied_b.order', 'not_evaluated'), ('allowed_a.order', 'not_evaluated'), ('distinction.allowed_a--replaced_a', 'failed')}
    yield 'observed_exit_not_published', lambda s: s['passages']['initial_a']['capture']['run'].update(exit=2), failed('initial_a.status')
    yield 'unreaped_worker', lambda s: mutate_capture(s, 'b', lambda e: e['data']['runner_result']['runner_subprocess'].update(reaped=False)), failed('b.worker')
    yield 'incomplete_phase', lambda s: mutate_capture(s, 'b', lambda e: e['data']['runner_result']['phases'][0].update(completion_observed=False)), failed('b.collections')
    def missing(s):
        s['passages']['updated_a']['before'] = None
    yield 'missing_observation', missing, failed('fixtures', 'updated_a.fixture') | {
        ('updated_a.stability', 'not_evaluated'), ('updated_a.identity', 'not_evaluated'), ('updated_a.content', 'not_evaluated')}
    def combined(s):
        missing(s)
        s['passages']['updated_a']['capture']['run']['exit'] = 2
        mutate_capture(s, 'denied_b', lambda e: set_query(e, False))
    yield 'missing_observation_independent_faults', combined, failed('fixtures', 'updated_a.fixture', 'updated_a.status', 'denied_b.query') | {
        ('updated_a.stability', 'not_evaluated'), ('updated_a.identity', 'not_evaluated'), ('updated_a.content', 'not_evaluated'),
        ('denied_b.order', 'not_evaluated')}
    def unstable(s):
        s['passages']['b']['after']['stat']['st_mtime_ns'] += 1
    yield 'unstable_target', unstable, failed('b.stability') | {('b.identity', 'not_evaluated'), ('b.content', 'not_evaluated')}
    yield 'missing_after', lambda s: s['passages']['b'].update(after=None), failed('b.stability', 'b.after_fixture') | {
        ('b.identity', 'not_evaluated'), ('b.content', 'not_evaluated')}
    yield 'invalid_after_sample', lambda s: s['passages']['b']['after'].update(regular_file=False, error='failed'), failed('b.after_fixture') | {
        ('b.identity', 'not_evaluated'), ('b.content', 'not_evaluated')}
    def publication_and_status(s):
        s['publication']['emissions']['a1']['stdout'] = '{invalid\n'
        s['passages']['b']['capture']['run']['exit'] = 2
    yield 'publication_independent_capture_fault', publication_and_status, failed('publication.a1.binding', 'publication.determinism',
            'initial_a.transformation', 'updated_a.transformation', 'b.status')
    unread = lambda name: {(name + '.identity', 'not_evaluated'), (name + '.content', 'not_evaluated')}
    # Another passage's coherent run: correct answers for its own request cannot stand in for this one.
    yield 'run_of_other_passage', lambda s: s['passages']['allowed_a']['capture'].update(
        run=copy.deepcopy(s['passages']['b']['capture']['run'])), failed('allowed_a.association') | unread('allowed_a')
    yield 'denied_read_reported_successful', lambda s: other_outcome(s, 'denied_b', 'b'), failed('denied_b.attempt')
    yield 'allowed_read_reported_refused', lambda s: other_outcome(s, 'allowed_a', 'denied_b'), failed('allowed_a.attempt', 'distinction.allowed_a--replaced_a') | unread('allowed_a')
    def unordered(s):
        def change(e):
            reply = e['data']['runner_result']
            reply['phases'][0]['ordering'].update(worker_lifetime_established=False)
            reply['steps'][0]['comparison'].update(order='unestablished')
        mutate_capture(s, 'b', change)
    yield 'unestablished_order', unordered, failed('b.collections', 'b.order')
    def wrong_answer_and_order(s):
        unordered(s)
        mutate_capture(s, 'b', lambda e: set_query(e, True))
    yield 'order_uncredited_beside_wrong_answer', wrong_answer_and_order, failed('b.collections', 'b.query') | {('b.order', 'not_evaluated')}
    # Fixture relationships the experiment depends on, with captures that agree with the earlier inodes.
    yield 'a_replaced_instead_of_updated', lambda s: resample(s, ['updated_a'], 43), failed('fixtures', 'updated_a.identity')
    yield 'b_shares_a_inode', lambda s: resample(s, ['b', 'refusal', 'repair', 'denied_b'], 41), failed('fixtures', 'b.identity', 'repair.identity', 'crossed.peer', 'returning.peer',
        *(name + '.bystander' for name in checker.REPLACEMENTS))
    def changed_b(s):
        resample(s, ['repair'], 44)
        mutate_capture(s, 'repair', lambda e: attempt(e)['fresh_read']['identity'].update(inode=44))
    yield 'b_changed_between_passages', changed_b, failed('repair.generation')
    def other_acquisition(s):
        s['publication']['targets']['b'] = PATHS['A']
    yield 'publication_recorded_for_other_target', other_acquisition, failed('publication.targets', 'publication.b.binding', 'publication.b.invocation')
    yield 'publication_second_newline', lambda s: s['publication']['emissions']['literal'].update(
        stdout=s['publication']['emissions']['literal']['stdout'] + '\n'), failed('publication.literal.framing')
    yield 'publication_other_command', lambda s: s['publication']['emissions']['literal']['argv'].__setitem__(1, 'example'), failed('publication.literal.invocation')


def boundary_controls():
    failed = lambda *names: {(name, 'failed') for name in names}
    pair = lambda a, b: 'distinction.' + a + '--' + b
    first = pair('allowed_a', 'replaced_a')
    second = pair('replaced_a', 'suffix_a')
    third = pair('suffix_a', 'bound_a')
    fourth = pair('bound_a', 'empty_a')
    def read_from(s, dst, src):
        read = attempt(json.loads(s['passages'][src]['capture']['run']['stdout']))['fresh_read']
        mutate_capture(s, dst, lambda e: attempt(e).update(fresh_read=copy.deepcopy(read)))
    yield 'suffix_read_in_replaced', lambda s: read_from(s, 'replaced_a', 'suffix_a'), set()
    yield 'bound_read_in_suffix', lambda s: read_from(s, 'suffix_a', 'bound_a'), set()
    yield 'old_whole_allowed_capture', lambda s: s['passages']['replaced_a'].update(
        capture=copy.deepcopy(s['passages']['allowed_a']['capture'])), failed('replaced_a.identity', first, second)
    yield 'old_identity_current_content', lambda s: mutate_capture(s, 'replaced_a',
        lambda e: attempt(e)['fresh_read']['identity'].update(inode=41)), failed('replaced_a.identity', first, second)
    for inode in (41, 42):
        def shared(s, inode=inode):
            s['replacement']['prepared']['stat']['st_ino'] = inode
            resample(s, checker.REPLACEMENTS, inode)
            for name in checker.REPLACEMENTS:
                mutate_capture(s, name, lambda e: attempt(e)['fresh_read']['identity'].update(inode=inode))
        yield 'replacement_shared_' + str(inode), shared, failed('replacement', *([first] if inode == 41 else []))
    yield 'replacement_changed_in_generation', lambda s: resample(s, ['suffix_a'], 44), failed('suffix_a.generation', 'suffix_a.identity', second, third)
    for field, value in (('before', None), ('after', sample(PATHS['A'] + '.previous', b'x', 41))):
        yield 'parked_' + field, lambda s, field=field, value=value: s['passages']['replaced_a']['parked'].update({field: value}), failed('replaced_a.parked')
    yield 'empty_reported_unavailable', lambda s: other_outcome(s, 'empty_a', 'denied_b'), failed('empty_a.attempt', fourth) | {
        ('empty_a.identity', 'not_evaluated'), ('empty_a.content', 'not_evaluated')}
    # Counts and bytes remain mutually coherent so the consumer accepts them.
    for name, payload, distinctions in (('empty_a', b'x', []), ('updated_a', checker.SHORT_1[:-1], []),
                                        ('bound_a', checker.PREFIX[:-1], [third])):
        for mode in ('count', 'digest'):
            data = payload if mode == 'count' else (b'x' * len(checker.payload_for(name)[:checker.BOUND]) or b'x')
            def change(s, name=name, data=data):
                mutate_capture(s, name, lambda e: attempt(e)['fresh_read'].update(read_rc=len(data), content_hex=data.hex()))
            yield name + '_wrong_' + mode, change, failed(name + '.content', *distinctions)
    def stale(s):
        for t in ('before', 'after'):
            s['passages']['suffix_a'][t]['sha256'] = hashlib.sha256(checker.LONG).hexdigest()
    yield 'stale_full_sample', stale, failed('suffix_a.fixture', 'suffix_a.after_fixture', second) | {
        ('suffix_a.stability', 'not_evaluated'), ('suffix_a.identity', 'not_evaluated'), ('suffix_a.content', 'not_evaluated')}
    yield 'inside_prefix_change', lambda s: mutate_capture(s, 'suffix_a', lambda e: attempt(e)['fresh_read'].update(
        content_hex=(b'x' + checker.PREFIX[1:]).hex())), failed('suffix_a.content', second, third)
    def combined(s):
        mutate_capture(s, 'replaced_a', lambda e: set_query(e, True))
        mutate_capture(s, 'replaced_a', lambda e: attempt(e)['fresh_read']['identity'].update(inode=41))
        mutate_capture(s, 'replaced_a', lambda e: e['data']['runner_result']['runner_subprocess'].update(reaped=False))
        s['passages']['replaced_a']['parked']['before'] = None
    yield 'replacement_combined', combined, failed('replaced_a.query', 'replaced_a.identity', 'replaced_a.worker', 'replaced_a.parked', first, second) | {
        ('replaced_a.order', 'not_evaluated')}


def matrix_controls():
    failed = lambda *names: {(name, 'failed') for name in names}
    unread = lambda *steps: {('crossed.' + step + '.' + k, 'not_evaluated') for step in steps for k in ('identity', 'content')}
    # A changed crossed step also changes its comparison with the same step in the returning form.
    form = lambda *steps: failed(*('distinction.crossed--returning.' + step for step in steps))
    first = 'distinction.crossed.read-aa--read-ba'
    second = 'distinction.crossed.read-aa--read-ab'
    third = 'distinction.crossed.read-bb--metadata-b'
    steps = [row[0] for row in checker.MATRIX]

    def input_change(s, change):
        capture = s['passages']['crossed']['capture']
        document = json.loads(capture['input'])
        change(document['probe_plan'])
        capture['input'] = checker.encode(document)
        mutate_capture(s, 'crossed', lambda e: e['data']['runner_client']['request_delivery'].update(
            bytes_written=len(capture['input'].encode()) - 1))
    for label, change, extra in (
            ('query_operand', lambda rows: rows[2]['sandbox_check']['filter'].update(value=PATHS['A']), failed(first) | form('read-ba')),
            ('attempt_operand', lambda rows: rows[1]['attempt'].update(target=PATHS['A']), failed(second) | form('read-ab')),
            ('query_operation', lambda rows: rows[4]['sandbox_check'].update(operation='file-read-data'), failed(third) | form('metadata-b')),
            ('omitted', lambda rows: rows.pop(), {(third, 'not_evaluated'), ('distinction.crossed--returning.metadata-b', 'not_evaluated')}),
            ('duplicated', lambda rows: rows.append(copy.deepcopy(rows[0])), set()),
            ('reordered', lambda rows: rows.reverse(), set())):
        yield 'matrix_' + label, lambda s, change=change: input_change(s, change), failed('crossed.transformation') | extra
    yield 'matrix_wrong_query', lambda s: mutate_capture(s, 'crossed', lambda e: set_answer(e, 'read-ba', False)), \
        failed('crossed.read-ba.query', first) | form('read-ba') | {('crossed.read-ba.order', 'not_evaluated')}
    yield 'matrix_wrong_attempt', lambda s: mutate_capture(s, 'crossed', lambda e: refuse_read(e, 'read-ba')), \
        failed('crossed.read-ba.attempt', first) | form('read-ba') | unread('read-ba')
    yield 'matrix_equal_bytes_wrong_object', lambda s: mutate_capture(s, 'crossed', lambda e: fresh(e, 'read-ba')['identity'].update(inode=42)), \
        failed('crossed.read-ba.identity', first) | form('read-ba')
    yield 'matrix_changed_returned_byte', lambda s: mutate_capture(s, 'crossed', lambda e: fresh(e, 'read-aa').update(
        content_hex=(b'x' + checker.PREFIX[1:]).hex())), failed('crossed.read-aa.content', first) | form('read-aa')

    def swapped(s):
        def change(e):
            reply = e['data']['runner_result']
            records = reply['phases'][0]['validator_subprocess']['records']
            reply['steps'][0], reply['steps'][2] = reply['steps'][2], reply['steps'][0]
            records[0], records[2] = records[2], records[0]
            for index in (0, 2):
                reply['steps'][index]['step_id'] = steps[index]
                rewrite_line(records[index], step_id=steps[index])
        mutate_capture(s, 'crossed', change)
    yield 'matrix_other_step_under_id', swapped, failed('crossed.read-aa.association', 'crossed.read-ba.association',
        'crossed.read-aa.query', 'crossed.read-ba.query', second) | form('read-aa', 'read-ba') | unread('read-aa', 'read-ba') | {
        ('crossed.' + step + '.order', 'not_evaluated') for step in ('read-aa', 'read-ba')}

    # A wrong relation stays consumer-valid only when the submitted echo changes with it.
    def relation(s):
        def change(e):
            step = reply_step(e, 'read-ba')
            step['sandbox_check']['filter_value'] = PATHS['A']
            step['comparison']['target_relation'] = 'same_submitted'
            rewrite_line(e['data']['runner_result']['phases'][0]['validator_subprocess']['records'][2], filter_value=PATHS['A'])
        mutate_capture(s, 'crossed', change)
    yield 'matrix_wrong_relation', relation, failed('crossed.read-ba.association') | unread('read-ba')

    def unordered(s):
        def change(e):
            reply = e['data']['runner_result']
            reply['phases'][0]['ordering']['worker_lifetime_established'] = False
            for step in reply['steps']:
                step['comparison']['order'] = 'unestablished'
        mutate_capture(s, 'crossed', change)
    yield 'matrix_unestablished_order', unordered, failed('crossed.collections', *('crossed.' + step + '.order' for step in steps))

    # Every record of the reply reversed together: each step is still found by its identifier.
    def reversed_reply(s):
        def change(e):
            reply = e['data']['runner_result']
            phase, slots = reply['phases'][0], reply['runner_subprocess']['disposition']
            reply['steps'].reverse()
            phase['action_ids'].reverse()
            phase['validator_subprocess']['expected_step_ids'] = list(phase['action_ids'])
            phase['validator_subprocess']['records'].reverse()
            slots['steps'] = [dict(slot, index=index) for index, slot in enumerate(reversed(slots['steps']))]
        mutate_capture(s, 'crossed', change)
    yield 'matrix_reply_reordered', reversed_reply, failed('crossed.association', 'crossed.collections')
    yield 'matrix_peer_sample_missing', lambda s: s['passages']['crossed']['peer'].update(after=None), failed('crossed.peer')
    yield 'matrix_a_replaced_before', lambda s: replaced_before(s, 'crossed'), failed('crossed.generation') | form('read-aa', 'read-ba')


def unadmitted_controls():
    """Captures the consumer itself refuses: nothing under the reply is read or credited."""
    def other_build(s):
        def change(e):
            e['build']['contract'] = 'development:' + '5' * 64
        mutate_capture(s, 'b', change)
    yield 'envelope_of_other_build', other_build, {('b.build', 'failed'), ('b.consumer', 'failed'), ('b.reply', 'failed')} | {
        ('b.' + kind, 'not_evaluated') for kind in ('association', 'worker', 'collections', 'query', 'order', 'attempt', 'identity', 'content')}


# Rows every passage computes the same way, whatever its form.
UNIFORM = ('status', 'build', 'consumer', 'reply', 'worker', 'fixture', 'after_fixture', 'stability')


def kind(ident):
    """A row's obligation, without the names that only select among rows evaluated alike.

    An emission, a one-step passage, and a form's step, actor or phase are such
    names. A form keeps its own name on everything but the uniform rows, so its
    matrix, ownership and derivative rows each need a control in that form. Each
    distinction pair is its own obligation; the five across the forms are one.
    """
    parts = ident.split('.')
    if parts[0] == 'distinction':
        return 'distinction.crossed--returning' if parts[1] == 'crossed--returning' else ident
    if parts[0] in ('crossed', 'returning') and not (len(parts) == 2 and parts[1] in UNIFORM):
        family = () if len(parts) == 2 else (parts[1],) if parts[1] in ('actor', 'phase') else ('step',)
        return '.'.join((parts[0],) + family + (parts[-1],))
    if parts[0] in checker.PASSAGES:
        return parts[-1]
    return ident if len(parts) < 3 else parts[0] + '.' + parts[2]


def preparation_controls(directory):
    rows = []
    for name in ('accepted', 'wrong_target', 'ignored_emitter', 'wrong_plist', 'missing_snapshot', 'bad_version', 'failed_emission'):
        dest = directory / name
        dest.mkdir()
        app = dest / 'App/Contents'
        app.mkdir(parents=True)
        (app / 'Info.plist').write_bytes(plistlib.dumps(dict(PWContract='development:' + '5' * 64 if name == 'wrong_plist' else IDENTITY)))
        body = {k: v for k, v in checker.expected_document(IDENTITY, '$EFFECT').items() if k != 'contract'}
        snapshot = dict(surfaces=[dict(public=dict(nodes=[dict(id='request.specimen.read_input',
            prose='```json\n' + json.dumps(body) + '\n```')]))])
        snapshot_path = dest / 'snapshot.json'
        snapshot_path.write_text(json.dumps({} if name == 'missing_snapshot' else snapshot))
        good, wrong = dest / 'publisher', dest / 'wrong-publisher'
        source = '''#!{python}
import json, sys
identity={identity!r}
if sys.argv[1:] == ['--version']:
 print(json.dumps(dict(build=dict(contract=identity),data=dict(contract=identity))))
 sys.exit({version_exit})
v={body!r}
v['contract']=identity
target=sys.argv[-1]
{wrong}
v['probe_plan'][0]['sandbox_check']['filter']['value']=target
v['probe_plan'][0]['attempt']['target']=target
print(json.dumps(v,ensure_ascii=False,indent=2))
sys.exit({emit_exit})
'''
        for script, changed in ((good, False), (wrong, True)):
            script.write_text(source.format(python=sys.executable, identity=IDENTITY, body=body,
                version_exit=2 if name == 'bad_version' else 0, emit_exit=2 if name == 'failed_emission' else 0,
                wrong='target=' + repr(PATHS['B']) if changed else ''))
            script.chmod(0o700)
        observed = []
        def observer(target, bound):
            observed.append(target)
            return sample(target, checker.SHORT_0, 41)
        supplied = wrong if name in ('wrong_target', 'ignored_emitter') else good
        rejected = False
        try:
            # The bypass is a deliberate driver mutation: the scenario's oracle
            # must detect that its supplied emitter was ignored.
            driver.start(dest, good, app.parent, snapshot_path, PATHS,
                         emitter=good if name == 'ignored_emitter' else supplied, observer=observer)
        except ValueError as error:
            rejected = True
            (dest / 'rejection.txt').write_text(str(error))
        invoked = all(json.loads((dest / (part + '.command.json')).read_text())[0] == str(supplied)
                      for part in ('a1', 'a2', 'literal'))
        expected_diagnostics = {
            'accepted': set(), 'ignored_emitter': set(),
            'wrong_target': {(f'publication.{part}.binding', 'failed') for part in ('a1', 'a2', 'literal')},
            'wrong_plist': {('publication.identity', 'failed')},
            'missing_snapshot': {('publication.snapshot', 'failed')},
            'bad_version': {('publication.identity', 'failed')},
            'failed_emission': {(f'publication.{part}.status', 'failed') for part in ('a1', 'a2', 'literal')},
        }[name]
        actual_diagnostics = checker.diagnostics(json.loads((dest / 'preparation-report.json').read_text()))
        assert actual_diagnostics == expected_diagnostics, (name, actual_diagnostics, expected_diagnostics)
        caught_wrong = rejected and not observed and invoked
        if name == 'ignored_emitter':
            assert not caught_wrong and not invoked and observed, (name, rejected, observed, invoked)
        elif name == 'accepted':
            assert not rejected and observed == [PATHS['A']] and invoked, name
        else:
            assert caught_wrong, (name, rejected, observed, invoked)
            assert not (dest / 'initial-before.json').exists()
            assert not list(dest.rglob('input.json')) and not list(dest.rglob('run.stdout'))
        rows.append(dict(name=name, rejected=rejected, observer_calls=observed, supplied_emitter_invoked=invoked,
                         bypass_detected=name == 'ignored_emitter', diagnostics=sorted(actual_diagnostics)))
    return rows


def cleanup_controls(directory):
    state = build()
    records = []
    for name, passage, expected in [('reaped', 'b', True), ('refusal', 'refusal', True),
                                   ('missing_run', 'b', False), ('wrong_identity', 'b', False),
                                   ('unreaped', 'b', False), ('wrong_refusal', 'refusal', False)]:
        capture = copy.deepcopy(state['passages'][passage]['capture'])
        if name == 'missing_run':
            capture.pop('run')
        elif name in ('wrong_identity', 'unreaped', 'wrong_refusal'):
            env = json.loads(capture['run']['stdout'])
            if name == 'wrong_identity':
                env['build']['contract'] = 'development:' + '5' * 64
            elif name == 'unreaped':
                env['data']['runner_result']['runner_subprocess']['reaped'] = False
            else:
                env['data']['runner_result']['request_failure']['path'] = ['policy', 'another_field']
                env['data']['request_failure']['path'] = ['policy', 'another_field']
            recapture_host_reply(env)
            capture['run']['stdout'] = checker.encode(env)
        witnessed, reason = driver.cleanup_disposition(capture, IDENTITY, refusal=passage == 'refusal', authored_fixture=True)
        assert witnessed is expected, (name, witnessed, reason)
        records.append(dict(name=name, expected=expected, witnessed=witnessed, reason=reason))
    (directory / 'cleanup-controls.json').write_text(checker.encode(records))
    return records


def main(directory):
    directory = Path(directory)
    records = []
    rejected = set()
    from test_input_actor_controls import controls as actor_controls
    groups = [(coherent, name, change, expected)
              for coherent, group in ((True, controls()), (True, boundary_controls()), (True, matrix_controls()), (False, unadmitted_controls()))
              for name, change, expected in group] + list(actor_controls())
    for coherent, name, change, expected in groups:
        state = build()
        change(state)
        report = checker.evaluate(state, authored_fixture=True)
        dest = directory / name
        dest.mkdir()
        (dest / 'state.json').write_text(checker.encode(state))
        checker.write_report(dest, report)
        found = checker.diagnostics(report)
        assert found == expected, (name, sorted(expected), sorted(found))
        # A coherent control is one the consumer accepts, so only the seam's own rows reject it.
        assert coherent is not any(ident.endswith('.consumer') for ident, _ in found), name
        rejected |= {kind(ident) for ident, status in found if status == 'failed'}
        records.append(dict(name=name, expected=sorted(expected), actual=sorted(found), consumer_accepted=coherent))
    preparation = directory / 'preparation'
    preparation.mkdir()
    prepared = preparation_controls(preparation)
    rejected |= {kind(ident) for row in prepared for ident, status in row['diagnostics'] if status == 'failed'}
    # Every obligation the checker reports has a control that fails it; a row no control can fail earns nothing.
    obligations = {kind(row['id']) for row in checker.evaluate(build(), authored_fixture=True)['rows']}
    assert obligations == rejected, (sorted(obligations - rejected), sorted(rejected - obligations))
    records.extend(prepared)
    records.extend(cleanup_controls(directory))
    # Exercise the actual acquisition gate before allowing the actor derivative.
    for name, changed in (('matrix_gate_accepted', False), ('matrix_gate_wrong_query', True)):
        state = build()
        if changed:
            mutate_capture(state, 'crossed', lambda e: set_query(e, False, 2))
        dest = directory / name
        dest.mkdir()
        reached_derivative = False
        try:
            driver.crossed_gate(dest, state, authored_fixture=True)
            reached_derivative = True
        except ValueError:
            pass
        assert reached_derivative is not changed, name
        records.append(dict(name=name, reached_derivative=reached_derivative))
    (directory / 'controls.json').write_text(checker.encode(records))
    print(f'{len(records)} exact controls matched')


if __name__ == '__main__':
    main(sys.argv[1])
