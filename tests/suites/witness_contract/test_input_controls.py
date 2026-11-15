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


def set_query(envelope, denied):
    reply = envelope['data']['runner_result']
    query = reply['steps'][0]['sandbox_check']
    query.update(outcome='deny' if denied else 'allow', rc=int(denied), native_rc=int(denied), errno=0)
    record = reply['phases'][0]['validator_subprocess']['records'][0]
    record.update(outcome=query['outcome'], rc=query['native_rc'], errno=0)
    raw = json.loads(record['raw_line'])
    raw.update(outcome=query['outcome'], rc=query['native_rc'], errno=0)
    record['raw_line'] = json.dumps(raw, separators=(',', ':'))


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
        record = validator['records'][0]
        record.update(step_id='read-target', filter_value=target)
        raw = json.loads(record['raw_line'])
        raw.update(step_id='read-target', filter_value=target)
        record['raw_line'] = json.dumps(raw, separators=(',', ':'))
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
        letter = 'A' if name in ('initial_a', 'updated_a', 'allowed_a') + checker.REPLACEMENTS else 'B'
        payload = checker.payload_for(name)
        observed = sample(PATHS[letter], payload, 43 if name in checker.REPLACEMENTS else 41 if letter == 'A' else 42)
        raw = checker.encode(documents[name])
        state['passages'][name] = dict(before=observed, after=copy.deepcopy(observed), capture=dict(input=raw,
            request_path='/constructed/input.json', run=run_record(name, documents[name], observed, raw)))
        if name in checker.REPLACEMENTS:
            for key, target, inode in (('parked', PATHS['A'] + '.previous', 41), ('bystander', PATHS['B'], 42)):
                state['passages'][name][key] = {t: sample(target, checker.LONG, inode) for t in ('before', 'after')}
    state['replacement'] = dict(original=sample(PATHS['A'], checker.LONG, 41),
        prepared=sample(PATHS['A'] + '.replacement', checker.LONG, 43),
        renames=[[PATHS['A'], PATHS['A'] + '.previous'], [PATHS['A'] + '.replacement', PATHS['A']]])
    return state


def run_record(outcome, document, observed, raw):
    """A coherent run of `document` with the named passage's outcome, delivered as `raw`."""
    env = envelope(outcome, document, observed)
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
    yield 'b_shares_a_inode', lambda s: resample(s, ['b', 'refusal', 'repair', 'denied_b'], 41), failed('fixtures', 'b.identity', 'repair.identity',
        *(name + '.bystander' for name in checker.REPLACEMENTS))
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


def unadmitted_controls():
    """Captures the consumer itself refuses: nothing under the reply is read or credited."""
    def other_build(s):
        def change(e):
            e['build']['contract'] = 'development:' + '5' * 64
        mutate_capture(s, 'b', change)
    yield 'envelope_of_other_build', other_build, {('b.build', 'failed'), ('b.consumer', 'failed'), ('b.reply', 'failed')} | {
        ('b.' + kind, 'not_evaluated') for kind in ('association', 'worker', 'collections', 'query', 'order', 'attempt', 'identity', 'content')}


def kind(ident):
    """A row's obligation without its passage or emission name."""
    parts = ident.split('.')
    if parts[0] == 'distinction':
        return 'distinction'
    if parts[0] in checker.PASSAGES:
        return parts[1]
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
    for coherent, group in ((True, controls()), (True, boundary_controls()), (False, unadmitted_controls())):
        for name, change, expected in group:
            state = build()
            change(state)
            report = checker.evaluate(state, authored_fixture=True)
            dest = directory / name
            dest.mkdir()
            (dest / 'state.json').write_text(checker.encode(state))
            checker.write_report(dest, report)
            found = checker.diagnostics(report)
            assert found == expected, (name, sorted(expected), sorted(found))
            # Correspondence controls are coherent to the consumer; only the unadmitted group is not.
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
    (directory / 'controls.json').write_text(checker.encode(records))
    print(f'{len(records)} exact controls matched')


if __name__ == '__main__':
    main(sys.argv[1])
