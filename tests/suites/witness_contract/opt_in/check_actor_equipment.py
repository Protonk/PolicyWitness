"""Mixed packaged worker authority with independent signing and live provenance.

The same-selected contrast deliberately succeeds natively. The independent
expected-equipment assertion must reject its claim to an unentitled issuer.
"""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parents[3] / 'lib')]
ROOT = HERE.parents[4]
from witness_capture import capture
import extension_actors as actors
from contract import REQUEST_SCHEMA
from runner_client_capture import host_reply
import consumer
sys.path[:0] = [str(ROOT / 'tests/fixtures/byoxpc'), str(ROOT / 'tests/fixtures/caller_auth')]
import session
from bundle import command, signature, save

KEY = 'com.apple.security.cs.allow-jit'
FALSE_KEY = 'com.apple.security.cs.allow-unsigned-executable-memory'
ABSENT_KEY = 'com.policywitness.test.required-absent'
pw, directory = sys.argv[1:]
out = Path(directory)
state = json.loads((out / 'session.json').read_text())
staging, bundle = session.owned_bundle(state)
receipts = out / 'equipment'
receipts.mkdir()
targets = staging / 'actor-targets'
targets.mkdir(exist_ok=True)
target = targets / 'mixed-equipment-target'
contents = b'PW mixed equipment witness\n'
target.write_bytes(contents)
assert target.read_bytes() == contents
expected_files = {'selected': bundle / 'Contents/MacOS/pw-probe-runner',
                  'unentitled': bundle / 'Contents/MacOS/pw-probe-runner-unentitled'}
readbacks = {role: session.entitlements(path, receipts, 'entitlements-' + role, command) or {}
             for role, path in expected_files.items()}
signatures = {role: signature(path, receipts / ('signature-' + role)) for role, path in expected_files.items()}
assert readbacks['selected'].get(KEY) is True and readbacks['unentitled'] == {}, readbacks
assert readbacks['selected'].get(FALSE_KEY) is False and ABSENT_KEY not in readbacks['selected'], readbacks
assert not (bundle / 'Contents/MacOS/pw-extension-issuer').exists(), 'retired helper remains installed'


def specimen(issuer='issuer', subject='subject', *, reversed_order=False, issuer_equipment='unentitled'):
    issuer_actor = dict(actors.unapplied_actor(issuer), equipment=issuer_equipment, required_entitlements=[])
    subject_actor = dict(actors.apply_actor(subject, actors.C_POLICY), equipment='selected', required_entitlements=[KEY])
    return {'schema_version': REQUEST_SCHEMA, 'specimen_id': 'mixed_worker_equipment',
            'actors': [subject_actor, issuer_actor] if reversed_order else [issuer_actor, subject_actor],
            'phases': [
                {'phase_id': 'baseline', 'actor_id': subject, 'actions': [actors.read_probe('before', target)]},
                {'phase_id': 'supply', 'actor_id': issuer, 'actions': [actors.issue('issue', 'token', target), actors.transfer('transfer', 'token', subject, 'delivery')]},
                {'phase_id': 'consume', 'actor_id': subject, 'actions': [actors.consume('consume', 'delivery', 'handle')]},
                {'phase_id': 'access', 'actor_id': subject, 'actions': [actors.read_probe('during', target)]},
                {'phase_id': 'release', 'actor_id': subject, 'actions': [actors.release('release', 'handle')]},
                {'phase_id': 'after', 'actor_id': subject, 'actions': [actors.read_probe('after', target)]}]}


def assert_equipment(runner, expected):
    by_binding = {b['binding_id']: b for b in runner['equipment_bindings']}
    by_read = {r['entitlements_id']: r for r in runner['equipment_entitlements']}
    assert runner['equipment_inventory']['status'] == 'verified'
    for actor in runner['actors']:
        role = expected[actor['actor_id']]
        equipment = actor['equipment']
        assert equipment['resolved'] == role and equipment['binding_ref'] == role, 'actor uses a different signed worker'
        binding, execution = by_binding[role], equipment['execution']
        assert binding['source'] == 'packaged' and binding['implementation_identity'] == 'inventory_verified'
        assert Path(binding['path']).samefile(expected_files[role])
        assert binding['sha256'] == hashlib.sha256(expected_files[role].read_bytes()).hexdigest()
        assert binding['cdhash'] == signatures[role]['CDHash']
        assert execution['status'] == 'matched' and execution['eligible'] is True
        assert execution['pid'] == actor['launch']['pid'] == actor['subprocess']['pid']
        assert Path(execution['path']).samefile(expected_files[role]) and execution['cdhash'] == signatures[role]['CDHash']
        assert binding['identifier'] == execution['identifier'] == signatures[role]['Identifier']
        expected_team = None if signatures[role]['TeamIdentifier'] == 'not set' else signatures[role]['TeamIdentifier']
        assert binding.get('team_id') == execution.get('team_id') == expected_team
        observed = by_read[execution['entitlements_ref']]
        assert observed['source'] == 'execution' and observed['actor_id'] == actor['actor_id'] and observed['binding_ref'] == role
        assert plistlib.loads(observed['raw_plist'].encode()) == readbacks[role]
        assert equipment['requirements_status'] == 'satisfied' and equipment['missing_requirements'] == []
    assert len({a['launch']['pid'] for a in runner['actors']}) == len(expected)
    assert all(a['subprocess']['reaped'] for a in runner['actors'])


def assert_lifecycle(runner):
    steps = {s['step_id']: s for s in runner['steps']}
    events = {e['step_id']: e for e in runner['extension_events']}
    assert steps['before']['attempt']['fresh_read']['open_rc'] == -1
    assert events['issue']['native_nonnull'] is True and events['issue']['status'] == 'returned'
    transfer, = runner['transfers']
    assert transfer['status'] == 'delivered' and transfer['equality'] == 'equal' and transfer['recipient_acknowledged'] and transfer['source_acknowledged']
    assert events['consume']['status'] == 'returned' and events['consume']['native_result'] != -1
    during = steps['during']['attempt']
    assert during['rc'] == 0 and during['fresh_read']['content_hex'] == contents.hex()
    identity = during['fresh_read']['identity']
    assert (identity['device'], identity['inode']) == (target.stat().st_dev, target.stat().st_ino)
    assert events['release']['status'] == 'returned' and events['release']['call_boundary_observed'] and events['release']['result_published']
    assert steps['after']['attempt']['result_source'] == 'worker' and steps['after']['attempt'].get('fresh_read') is not None
    assert target.read_bytes() == contents
    return dict(consume=events['consume']['native_result'], release=events['release']['native_result'],
                before=steps['before']['attempt']['rc'], during=during['rc'], after=steps['after']['attempt']['rc'])


results = []
for name, issuer, subject, reverse in [('mixed', 'issuer', 'subject', False), ('permuted', 'source', 'reader', True)]:
    _, runner = capture(pw, receipts, name, specimen(issuer, subject, reversed_order=reverse), session_state=state)
    lifecycle = assert_lifecycle(runner)
    assert_equipment(runner, {issuer: 'unentitled', subject: 'selected'})
    results.append(dict(case=name, equipment_credited=True, lifecycle=lifecycle))
_, runner = capture(pw, receipts, 'same-selected', specimen(issuer_equipment='selected'), session_state=state)
lifecycle = assert_lifecycle(runner)
assert_equipment(runner, {'issuer': 'selected', 'subject': 'selected'})
try:
    assert_equipment(runner, {'issuer': 'unentitled', 'subject': 'selected'})
except AssertionError as exc:
    assert 'different signed worker' in str(exc), exc
    results.append(dict(case='same-selected', equipment_credited=False, rejected_by=str(exc), lifecycle=lifecycle))
else:
    raise AssertionError('same-selected substitution satisfied the unentitled issuer assertion')
# The four equipment/application combinations and omitted selection have
# independent ordinary effects; they do not claim an extension caused access.
combination_actors, combination_phases, roles = [], [], {}
for role, mode in [('selected', 'apply'), ('selected', 'unapplied'),
                   ('unentitled', 'apply'), ('unentitled', 'unapplied'), (None, 'unapplied')]:
    actor_id = (role or 'default') + '_' + mode
    actor = actors.apply_actor(actor_id, '(version 1)(allow default)') if mode == 'apply' else actors.unapplied_actor(actor_id)
    if role is None:
        actor.pop('equipment')
    else:
        actor['equipment'] = role
    actor['required_entitlements'] = [KEY] if role != 'unentitled' else []
    combination_actors.append(actor)
    roles[actor_id] = role or 'selected'
    combination_phases.append(dict(phase_id=actor_id, actor_id=actor_id,
        actions=[actors.read_probe('read_' + actor_id, target)]))
_, combinations = capture(pw, receipts, 'mode-equipment-combinations',
    dict(schema_version=REQUEST_SCHEMA, specimen_id='mode_equipment_combinations',
         actors=combination_actors, phases=combination_phases), session_state=state)
assert_equipment(combinations, roles)
for actual, submitted in zip(combinations['actors'], combination_actors):
    mode = submitted['sandbox']['mode']
    assert actual['equipment']['requested'] == submitted.get('equipment'), actual
    assert actual['application_count'] == (1 if mode == 'apply' else 0), actual
    assert actual['setup_status'] == ('applied' if mode == 'apply' else 'unapplied_declared'), actual
for step in combinations['steps']:
    assert step['attempt']['rc'] == 0 and step['attempt']['fresh_read']['content_hex'] == contents.hex(), step
assert target.read_bytes() == contents
results.append(dict(case='mode-equipment-combinations', modes=roles, equipment_credited=True))


def assert_requirement_refusal(reply, key, effect):
    assert reply['normalized_outcome'] == 'runner_failed', reply
    failure = reply['preparation_failure']
    assert failure['stage'] == 'equipment' and failure['code'] == 'equipment_binding_refused', failure
    assert failure['reason'] == 'requirements_unsatisfied' and failure['actor_id'] == 'requires', failure
    actual = {a['actor_id']: a for a in reply['actors']}
    assert actual['free']['equipment']['requirements_status'] == 'satisfied', actual
    assert actual['requires']['equipment']['requirements_status'] == 'unsatisfied', actual
    assert actual['requires']['equipment']['missing_requirements'] == [key], actual
    assert all(a.get('launch') is None and a.get('subprocess') is None for a in actual.values()), actual
    assert reply['steps'] == [] and not effect.exists(), (reply, effect)
    assert all(b['status'] == 'bound' for b in reply['equipment_bindings']), reply['equipment_bindings']
    errors = consumer.validate(reply)
    assert not errors, errors


# The controller's selected-worker preflight passes KEY. Actor-level false
# and absent keys must still be refused by the host, including direct XPC.
client = Path(pw).with_name('pw-runner-client')
for label, role, key in [('false', 'selected', FALSE_KEY), ('absent', 'selected', ABSENT_KEY),
                          ('unentitled-absent', 'unentitled', KEY)]:
    effect = targets / ('requirement-effect-' + label)
    assert not effect.exists()
    request = dict(schema_version=REQUEST_SCHEMA, specimen_id='actor_requirement_' + label,
        actors=[dict(actors.unapplied_actor('free'), equipment=role, required_entitlements=[]),
                dict(actors.unapplied_actor('requires'), equipment=role, required_entitlements=[key])],
        phases=[dict(phase_id='free', actor_id='free', actions=[]),
                dict(phase_id='requires', actor_id='requires', actions=[dict(step_id='effect',
                    sandbox_check=dict(operation='file-write-create', filter=dict(kind='path', value=str(effect))),
                    attempt=dict(kind='file', action='create', target=str(effect)))])])
    cli_request = copy.deepcopy(request)
    cli_request['runner'] = dict(mode='byoxpc', service=state['service_name'], required_entitlements=[KEY])
    _, refused = capture(pw, receipts, 'requirements-cli-' + label, cli_request, expected_rc=1)
    assert_requirement_refusal(refused, key, effect)
    direct = receipts / ('requirements-xpc-' + label)
    direct.mkdir()
    request_path = direct / 'request.json'
    request_path.write_text(json.dumps(request) + '\n')
    assert state['target'].startswith('gui/') and state['target'].endswith('/' + state['service_name']), state['target']
    result = command(direct / 'capture', [client, 'run', '--timeout-ms', '10000', '--mach-service',
                     state['service_name'], request_path], timeout=30, check=False)
    transport = json.loads((direct / 'capture/stdout').read_text())
    # A host runner_failed is still a successful transport (client exit 0).
    # Decode independently first: an acquisition/transport failure has no host
    # reply and must never satisfy the actor requirement-refusal assertion.
    direct_reply = host_reply(transport)
    assert result['returncode'] == 0 and not result['harness_timeout'], (result, transport)
    assert_requirement_refusal(direct_reply, key, effect)
    save(direct / 'host-reply.json', direct_reply)
    save(direct / 'effect.json', dict(path=str(effect), exists=effect.exists()))
    results.append(dict(case='required-' + label, key=key, role=role, cli_refused=True, direct_xpc_refused=True))

save(receipts / 'observations.json', dict(readbacks=readbacks, signatures=signatures, controls=results))
print('mixed and renamed/reordered packaged equipment observed; same-selected native success rejected by independent signing/actor assertion')
