"""Constructed two-actor captures; these are reader controls, never native evidence."""
import copy
import hashlib
import json

import check_test_input as c
import test_input_controls as t
from blackbox import bind_constructed_envelope, recapture_host_reply

ACTORS = ('Left', 'Right')
PHASES = ('left-first', 'right-only', 'left-second')
# Each step under the phase the request declares for it.
PLACED = (('left-first', 'read-aa'), ('left-first', 'read-ab'), ('right-only', 'read-ba'),
          ('left-second', 'read-bb'), ('left-second', 'metadata-b'))


def replace(value, mapping):
    if isinstance(value, dict):
        return {k: replace(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [replace(v, mapping) for v in value]
    return mapping.get(value, value) if isinstance(value, (str, int)) else value


def envelope(document, observed):
    template = json.loads((t.ROOT / 'tests/fixtures/example_round_trip/constructed_actor_run.json').read_text())
    env = bind_constructed_envelope(template)
    env['build']['contract'] = env['data']['runner_client']['transport']['contract'] = t.IDENTITY
    reply = env['data']['runner_result']
    reply['producer']['contract'] = t.IDENTITY
    reply['specimen_id'] = document['specimen_id']
    planned = [s for p in document['phases'] for s in p['actions']]
    flat = dict(contract=t.IDENTITY, specimen_id='test-input', policy=document['actors'][0]['sandbox']['policy'], probe_plan=planned)
    ordinary = t.matrix_envelope(flat, observed)['data']['runner_result']
    reply['steps'] = ordinary['steps']
    actor_template = copy.deepcopy(reply['actors'][0])
    authority_template = copy.deepcopy(reply['authority_setup']['workers'][0])
    read_template = copy.deepcopy(reply['equipment_entitlements'][1])
    dossier_template = copy.deepcopy(env['data']['specimen']['actors'][0])
    diagnostic_template = copy.deepcopy(env['data']['runner_sandbox_diagnostics']['actors'][0])
    reply['actors'], reply['authority_setup']['workers'] = [], []
    reply['equipment_entitlements'] = reply['equipment_entitlements'][:1]
    env['data']['specimen']['actors'], env['data']['runner_sandbox_diagnostics']['actors'] = [], []
    for index, declaration in enumerate(document['actors']):
        name, pid = declaration['actor_id'], 51001 + index
        actor = replace(actor_template, {'constructed-reader': name, 51001: pid})
        digest = hashlib.sha256(declaration['sandbox']['policy']['sbpl_source'].encode()).hexdigest()
        actor.update(index=index, policy_sha256=digest, policy_received_sha256=digest,
                     visits=[i for i, p in enumerate(document['phases'], 1) if p['actor_id'] == name])
        actor['equipment']['execution']['entitlements_ref'] = index + 1
        actor['owned_reap']['capture_ordinal'] = 10 + index
        reply['actors'].append(actor)
        reply['authority_setup']['workers'].append(dict(authority_template, actor_id=name, actor_index=index))
        reply['equipment_entitlements'].append(dict(read_template, actor_id=name))
        dossier = copy.deepcopy(dossier_template)
        dossier['actor_id'] = name
        dossier['policy']['augmentation'].update(original_sha256=digest, applied_sha256=digest)
        env['data']['specimen']['actors'].append(dossier)
        env['data']['runner_sandbox_diagnostics']['actors'].append(dict(diagnostic_template, actor_id=name))
    records = {rec['step_id']: rec for rec in ordinary['phases'][0]['validator_subprocess']['records']}
    slots = {slot['step_id']: slot for slot in ordinary['runner_subprocess']['disposition']['steps']}
    reply['phases'] = []
    for ordinal, planned_phase in enumerate(document['phases'], 1):
        owner = next(a for a in reply['actors'] if a['actor_id'] == planned_phase['actor_id'])
        ids = [s['step_id'] for s in planned_phase['actions']]
        phase = copy.deepcopy(ordinary['phases'][0])
        phase.update(phase_id=planned_phase['phase_id'], actor_id=owner['actor_id'], ordinal=ordinal,
                     actor_visit=owner['visits'].index(ordinal) + 1, action_ids=ids)
        phase['validator_subprocess'].update(phase_id=phase['phase_id'], ordinal=ordinal, pid=51100 + ordinal,
                                             expected_step_ids=ids, records=[records[ident] for ident in ids])
        for step in reply['steps']:
            if step['step_id'] in ids:
                step.update(phase_id=phase['phase_id'], actor_id=owner['actor_id'])
                step['sandbox_check']['pid'] = owner['launch']['pid']
        reply['phases'].append(phase)
    assign_slots(reply, slots)
    return recapture_host_reply(env)


def assign_slots(reply, slots):
    """Each actor's worker carries the slots of its own steps, numbered in its own order."""
    for actor in reply['actors']:
        local = [s['step_id'] for s in reply['steps'] if s['actor_id'] == actor['actor_id']]
        actor['subprocess']['disposition']['steps'] = [dict(slots[ident], index=i) for i, ident in enumerate(local)]


def controls():
    """Yields (the consumer accepts it, name, change, exact diagnostics)."""
    failed = lambda *names: {(name, 'failed') for name in names}
    row = lambda ident: 'returning.' + dict((step, phase) for phase, step in PLACED)[ident] + '.' + ident
    unread = lambda *steps: {(row(step) + '.' + k, 'not_evaluated') for step in steps for k in ('identity', 'content')}
    form = lambda *steps: failed(*('distinction.crossed--returning.' + step for step in steps))
    result = lambda env: env['data']['runner_result']

    def mutate(s, change):
        t.mutate_capture(s, 'returning', change)

    def everywhere(s, mapping):
        def change(e):
            changed = replace(e, mapping)
            e.clear()
            e.update(changed)
        mutate(s, change)

    def rename(s):
        capture = s['passages']['returning']['capture']
        mapping = {name: 'renamed-' + name for name in ACTORS + PHASES + tuple(step for _, step in PLACED)}
        capture['input'] = c.encode(replace(json.loads(capture['input']), mapping))

        def change(e):
            changed = replace(e, mapping)
            e.clear()
            e.update(changed)
            for phase in result(e)['phases']:
                for record in phase['validator_subprocess']['records']:
                    record['raw_line'] = json.dumps(replace(json.loads(record['raw_line']), mapping), separators=(',', ':'))
            e['data']['runner_client']['request_delivery']['bytes_written'] = len(capture['input'].encode()) - 1
        mutate(s, change)
    yield True, 'actor_consistent_renaming', rename, set()

    # The request itself: each derivative fault is refused before submission by the same row.
    def derivative(s, change):
        capture = s['passages']['returning']['capture']
        document = json.loads(capture['input'])
        change(document)
        capture['input'] = c.encode(document)
        mutate(s, lambda e: e['data']['runner_client']['request_delivery'].update(bytes_written=len(capture['input'].encode()) - 1))

    def other_partition(document):
        document['phases'][1]['actions'].insert(0, document['phases'][0]['actions'].pop())

    def other_policy(document):
        document['actors'][1]['sandbox']['policy']['sbpl_source'] = c.ALLOW

    def other_operand(document):
        document['phases'][1]['actions'][0]['sandbox_check']['filter']['value'] = t.PATHS['A']
    for name, change, extra in (('partition', other_partition, set()), ('policy', other_policy, set()),
                                ('operand', other_operand, form('read-ba'))):
        yield True, 'actor_derivative_' + name, lambda s, change=change: derivative(s, change), failed('returning.transformation') | extra

    # Ownership. Faults the consumer's joins also catch are marked as not accepted by it.
    yield True, 'actor_exchanged', lambda s: everywhere(s, {'Left': 'Right', 'Right': 'Left'}), failed(
        'returning.association', 'returning.actor.Left.association', 'returning.actor.Right.association',
        *('returning.phase.' + phase + '.association' for phase in PHASES),
        *(row(step) + '.association' for _, step in PLACED)) | unread('read-aa', 'read-ba')
    for visit in (1, 3):
        yield False, 'actor_second_visit_' + str(visit), lambda s, visit=visit: mutate(s, lambda e: result(e)['phases'][2].update(
            actor_visit=visit)), failed('returning.consumer', 'returning.phase.left-second.association')
    yield False, 'actor_wrong_visits', lambda s: mutate(s, lambda e: result(e)['actors'][0].update(visits=[1, 2])), \
        failed('returning.consumer', 'returning.actor.Left.association')
    yield False, 'actor_wrong_validator_ids', lambda s: mutate(s, lambda e: result(e)['phases'][2]['validator_subprocess'].update(
        expected_step_ids=['read-ba'])), failed('returning.consumer', 'returning.phase.left-second.collections')
    yield True, 'actor_same_pid', lambda s: everywhere(s, {51002: 51001}), failed('returning.processes')
    yield False, 'actor_second_application', lambda s: mutate(s, lambda e: result(e)['actors'][0].update(application_count=2)), \
        failed('returning.consumer', 'returning.actor.Left.application')
    yield True, 'actor_equipment_default', lambda s: mutate(s, lambda e: result(e)['actors'][0]['equipment'].update(requested=None)), \
        failed('returning.actor.Left.equipment')

    def unreaped(s):
        def change(e):
            actor = result(e)['actors'][1]
            actor['subprocess']['reaped'] = False
            actor.pop('owned_reap')
        mutate(s, change)
        witnessed, reason = t.driver.cleanup_disposition(s['passages']['returning']['capture'], t.IDENTITY, authored_fixture=True)
        assert not witnessed, reason
    yield True, 'actor_unreaped', unreaped, failed('returning.actor.Right.worker')

    def wrong_phase(s):
        def change(e):
            reply = result(e)
            phases = reply['phases']
            steps = {x['step_id']: x for x in reply['steps']}
            records = {x['step_id']: x for p in phases for x in p['validator_subprocess']['records']}
            slots = {x['step_id']: x for a in reply['actors'] for x in a['subprocess']['disposition']['steps']}
            phases[0]['action_ids'], phases[2]['action_ids'] = phases[2]['action_ids'], phases[0]['action_ids']
            for phase in phases:
                phase['validator_subprocess'].update(expected_step_ids=phase['action_ids'],
                                                     records=[records[x] for x in phase['action_ids']])
                for ident in phase['action_ids']:
                    steps[ident]['phase_id'] = phase['phase_id']
            reply['steps'] = [steps[x] for phase in phases for x in phase['action_ids']]
            assign_slots(reply, slots)
        mutate(s, change)
    yield True, 'actor_steps_wrong_phase', wrong_phase, failed('returning.association',
        *('returning.phase.' + phase + '.' + k for phase in ('left-first', 'left-second') for k in ('association', 'collections')),
        *(row(step) + '.association' for phase, step in PLACED if phase != 'right-only')) | unread('read-aa')

    # The matrix's native expectations in this form, each beside correct ownership.
    yield True, 'actor_wrong_query', lambda s: mutate(s, lambda e: t.set_answer(e, 'read-ba', False)), \
        failed(row('read-ba') + '.query') | form('read-ba') | {(row('read-ba') + '.order', 'not_evaluated')}
    yield True, 'actor_wrong_attempt', lambda s: mutate(s, lambda e: t.refuse_read(e, 'read-ba')), \
        failed(row('read-ba') + '.attempt') | form('read-ba') | unread('read-ba')
    yield True, 'actor_equal_bytes_wrong_object', lambda s: mutate(s, lambda e: t.fresh(e, 'read-ba')['identity'].update(inode=42)), \
        failed(row('read-ba') + '.identity') | form('read-ba')
    yield True, 'actor_changed_returned_byte', lambda s: mutate(s, lambda e: t.fresh(e, 'read-aa').update(
        content_hex=(b'x' + c.PREFIX[1:]).hex())), failed(row('read-aa') + '.content') | form('read-aa')

    def unordered(s):
        def change(e):
            result(e)['phases'][1]['ordering']['worker_lifetime_established'] = False
            t.reply_step(e, 'read-ba')['comparison']['order'] = 'unestablished'
        mutate(s, change)
    yield True, 'actor_unestablished_order', unordered, failed('returning.phase.right-only.collections', row('read-ba') + '.order')
    yield True, 'actor_a_replaced_before', lambda s: t.replaced_before(s, 'returning'), \
        failed('returning.generation') | form('read-aa', 'read-ba')
