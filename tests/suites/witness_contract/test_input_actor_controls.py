"""Constructed two-actor captures; these are reader controls, never native evidence."""
import copy
import hashlib
import json

import check_test_input as c
import test_input_controls as t
from blackbox import bind_constructed_envelope, recapture_host_reply


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
                     actor_visit=owner['visits'].index(ordinal)+1, action_ids=ids)
        phase['validator_subprocess'].update(phase_id=phase['phase_id'], ordinal=ordinal, pid=51100+ordinal,
                                            expected_step_ids=ids, records=[records[ident] for ident in ids])
        for step in reply['steps']:
            if step['step_id'] in ids:
                step.update(phase_id=phase['phase_id'], actor_id=owner['actor_id'])
                step['sandbox_check']['pid'] = owner['launch']['pid']
        reply['phases'].append(phase)
    for actor in reply['actors']:
        local = [s['step_id'] for s in reply['steps'] if s['actor_id'] == actor['actor_id']]
        actor['subprocess']['disposition']['steps'] = [dict(slots[ident], index=i) for i, ident in enumerate(local)]
    return recapture_host_reply(env)


def controls():
    failed = lambda *names: {(name, 'failed') for name in names}
    def mutate(s, change):
        t.mutate_capture(s, 'returning', change)
    def rename(s):
        p=s['passages']['returning'];capture=p['capture']
        mapping={name: 'renamed-'+name for name in ('Left','Right','left-first','right-only','left-second','read-aa','read-ab','read-ba','read-bb','metadata-b')}
        capture['input']=c.encode(replace(json.loads(capture['input']),mapping))
        def change(e):
            changed=replace(e,mapping);e.clear();e.update(changed)
            for phase in e['data']['runner_result']['phases']:
                for record in phase['validator_subprocess']['records']:
                    record['raw_line']=json.dumps(replace(json.loads(record['raw_line']),mapping),separators=(',', ':'))
            e['data']['runner_client']['request_delivery']['bytes_written']=len(capture['input'].encode())-1
        mutate(s,change)
    yield True, 'actor_consistent_renaming', rename, set()
    def exchange(s):
        def change(e):
            changed=replace(e,{'Left':'Right','Right':'Left'});e.clear();e.update(changed)
        mutate(s,change)
    affected = [('left-first','read-aa'),('left-first','read-ab'),('right-only','read-ba'),('left-second','read-bb'),('left-second','metadata-b')]
    yield True, 'actor_exchanged', exchange, failed('returning.association','returning.actor.Left.association','returning.actor.Right.association',
        *('returning.phase.'+p+'.association' for p in ('left-first','right-only','left-second')),
        *('returning.'+p+'.'+s+'.association' for p,s in affected)) | {
        ('returning.'+p+'.'+s+'.'+k,'not_evaluated') for p,s in affected if s in ('read-aa','read-ba') for k in ('identity','content')}
    for visit in (1,3):
        yield False, 'actor_second_visit_'+str(visit), lambda s, visit=visit: mutate(s,lambda e:
            e['data']['runner_result']['phases'][2].update(actor_visit=visit)), failed('returning.consumer','returning.phase.left-second.association')
    yield False, 'actor_wrong_visits', lambda s: mutate(s,lambda e:e['data']['runner_result']['actors'][0].update(visits=[1,2])), failed('returning.consumer','returning.actor.Left.association')
    yield False, 'actor_wrong_validator_ids', lambda s: mutate(s,lambda e:e['data']['runner_result']['phases'][2]['validator_subprocess'].update(expected_step_ids=['read-ba'])), failed('returning.consumer','returning.phase.left-second.collections')
    def same_pid(s):
        def change(e):
            changed=replace(e,{51002:51001});e.clear();e.update(changed)
        mutate(s,change)
    yield True, 'actor_same_pid', same_pid, failed('returning.processes')
    yield False, 'actor_second_application', lambda s: mutate(s,lambda e:e['data']['runner_result']['actors'][0].update(application_count=2)), failed('returning.consumer','returning.actor.Left.application')
    yield True, 'actor_equipment_default', lambda s: mutate(s,lambda e:e['data']['runner_result']['actors'][0]['equipment'].update(requested=None)), failed('returning.actor.Left.equipment')
    def unreaped(s):
        def change(e):
            actor=e['data']['runner_result']['actors'][1]
            actor['subprocess']['reaped']=False
            actor.pop('owned_reap')
        mutate(s,change)
        witnessed,reason=t.driver.cleanup_disposition(s['passages']['returning']['capture'],t.IDENTITY,authored_fixture=True)
        assert not witnessed, reason
    yield True, 'actor_unreaped', unreaped, failed('returning.actor.Right.worker')
    def wrong_phase(s):
        def change(e):
            r=e['data']['runner_result'];phases=r['phases'];steps={x['step_id']:x for x in r['steps']}
            records={x['step_id']:x for p in phases for x in p['validator_subprocess']['records']}
            slots={x['step_id']:x for a in r['actors'] for x in a['subprocess']['disposition']['steps']}
            phases[0]['action_ids'],phases[2]['action_ids']=phases[2]['action_ids'],phases[0]['action_ids']
            for p in phases:
                p['validator_subprocess'].update(expected_step_ids=p['action_ids'],records=[records[x] for x in p['action_ids']])
                for ident in p['action_ids']:steps[ident]['phase_id']=p['phase_id']
            r['steps']=[steps[x] for p in phases for x in p['action_ids']]
            for a in r['actors']:
                local=[x['step_id'] for x in r['steps'] if x['actor_id']==a['actor_id']]
                a['subprocess']['disposition']['steps']=[dict(slots[x],index=i) for i,x in enumerate(local)]
        mutate(s,change)
    yield True, 'actor_steps_wrong_phase', wrong_phase, failed('returning.association',
        *('returning.phase.'+p+'.'+k for p in ('left-first','left-second') for k in ('association','collections')),
        *('returning.'+p+'.'+s+'.association' for p,s in affected if p!='right-only')) | {
        ('returning.left-first.read-aa.'+k,'not_evaluated') for k in ('identity','content')}
