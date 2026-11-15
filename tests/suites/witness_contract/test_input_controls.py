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
            payload = checker.SHORT_0 if name == 'initial_a' else checker.SHORT_1 if name == 'updated_a' else checker.LONG
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
        letter = 'A' if name in ('initial_a', 'updated_a', 'allowed_a') else 'B'
        payload = checker.SHORT_0 if name == 'initial_a' else checker.SHORT_1 if name == 'updated_a' else checker.LONG
        observed = sample(PATHS[letter], payload, 41 if letter == 'A' else 42)
        raw = checker.encode(documents[name])
        env = envelope(name, documents[name], observed)
        env['data']['runner_client']['request_delivery']['bytes_written'] = len(raw.encode()) - 1
        state['passages'][name] = dict(before=observed, after=copy.deepcopy(observed), capture=dict(input=raw,
            request_path='/constructed/input.json', run=dict(argv=['constructed', 'run', '/constructed/input.json'],
                stdout=checker.encode(env), stderr='', exit=1 if name == 'refusal' else 0)))
    return state


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
    yield 'exchanged_query_answers', exchanged, failed('denied_b.query', 'allowed_a.query')
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
        ('updated_a.stability', 'not_evaluated'), ('updated_a.identity', 'not_evaluated'), ('updated_a.content', 'not_evaluated')}
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
    for name, change, expected in controls():
        state = build()
        change(state)
        report = checker.evaluate(state, authored_fixture=True)
        dest = directory / name
        dest.mkdir()
        (dest / 'state.json').write_text(checker.encode(state))
        checker.write_report(dest, report)
        found = checker.diagnostics(report)
        assert found == expected, (name, sorted(expected), sorted(found))
        # All these mutations are coherent from the consumer's perspective.
        assert not any(ident.endswith('.consumer') for ident, _ in found), name
        records.append(dict(name=name, expected=sorted(expected), actual=sorted(found), consumer_accepted=True))
    preparation = directory / 'preparation'
    preparation.mkdir()
    records.extend(preparation_controls(preparation))
    records.extend(cleanup_controls(directory))
    (directory / 'controls.json').write_text(checker.encode(records))
    print(f'{len(records)} exact controls matched')


if __name__ == '__main__':
    main(sys.argv[1])
