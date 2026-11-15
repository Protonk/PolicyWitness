"""Returning-form submitted expectations; the consumer owns internal actor joins."""
import copy
import hashlib

import check_test_input as c


def expected(identity, paths, submitted=None):
    actors, phases, steps = ['Left', 'Right'], ['left-first', 'right-only', 'left-second'], [r[0] for r in c.MATRIX]
    if isinstance(submitted, dict):
        proposed = ([c.get(a, 'actor_id') for a in submitted.get('actors', [])],
                    [c.get(p, 'phase_id') for p in submitted.get('phases', [])],
                    [c.get(s, 'step_id') for p in submitted.get('phases', []) for s in p.get('actions', [])])
        if all(len(values) == count and all(isinstance(v, str) and 0 < len(v.encode()) <= 63 and '\0' not in v for v in values)
               and len(set(values)) == count for values, count in zip(proposed, (2, 3, 5))):
            actors, phases, steps = proposed
    rows = c.matrix_steps(paths)
    for row, name in zip(rows, steps):
        row['step_id'] = name
    policy = dict(format='sbpl', sbpl_source=c.policy_for(paths['B']))
    return dict(contract=identity, specimen_id='test-input',
        actors=[dict(actor_id=name, equipment='selected', sandbox=dict(mode='apply', policy=copy.deepcopy(policy))) for name in actors],
        phases=[dict(phase_id=name, actor_id=actors[owner], actions=rows[start:stop])
                for name, (owner, start, stop) in zip(phases, ((0, 0, 2), (1, 2, 3), (0, 3, 5)))])


def rows(r, passage, reply, envelope, document, *, available, stable):
    actors, phases = reply.get('actors') or [], reply.get('phases') or []
    submitted = [step for phase in document['phases'] for step in phase['actions']]
    r.check('returning.association', reply.get('specimen_id') == 'test-input' and reply.get('execution_form') == 'actors' and
            [a.get('actor_id') for a in actors] == [a['actor_id'] for a in document['actors']] and
            [s.get('step_id') for s in reply.get('steps', [])] == [s['step_id'] for s in submitted] and
            [p.get('phase_id') for p in phases] == [p['phase_id'] for p in document['phases']] and
            c.get(envelope, 'data', 'runner_client', 'request_delivery', 'bytes_written') == len(c.get(passage, 'capture', 'input').encode()) - 1,
            'submitted actors, phases, steps and delivery', available=available)
    pids = [c.get(a, 'launch', 'pid') for a in actors]
    r.check('returning.processes', len(pids) == 2 and all(type(pid) is int and pid > 0 for pid in pids) and len(set(pids)) == 2,
            'distinct concurrently live actor launches', available=available)
    for declaration in document['actors']:
        name = declaration['actor_id']
        matches = [a for a in actors if a.get('actor_id') == name]
        actor = matches[0] if len(matches) == 1 else {}
        label = 'returning.actor.' + name
        digest = hashlib.sha256(declaration['sandbox']['policy']['sbpl_source'].encode()).hexdigest()
        visits = [i for i, p in enumerate(document['phases'], 1) if p['actor_id'] == name]
        r.check(label + '.association', actor.get('visits') == visits and actor.get('policy_sha256') == digest,
                'submitted visits and policy digest; equal policies do not discriminate destinations', available=available)
        r.check(label + '.application', actor.get('mode') == 'apply' and actor.get('setup_status') == 'applied' and
                actor.get('applied') is True and c.exact(actor.get('application_count'), 1), 'one applied sandbox', available=available)
        r.check(label + '.equipment', c.get(actor, 'equipment', 'requested') == 'selected' and
                c.get(actor, 'equipment', 'resolved') == 'selected', 'explicit selected equipment', available=available)
        worker = c.mapping(actor.get('subprocess'))
        r.check(label + '.worker', all(worker.get(k) is True for k in ('reaped', 'ready_byte_received', 'done_observed')) and
                c.exact(worker.get('exit_code'), 0) and worker.get('term_signal') is None and
                worker.get('collection_basis') == 'after_confirmed_reap' and reply.get('normalized_outcome') == 'finished',
                'completed worker and confirmed reap', available=available)
    index, visits = 0, {}
    for ordinal, planned in enumerate(document['phases'], 1):
        owner, ident = planned['actor_id'], planned['phase_id']
        visits[owner] = visits.get(owner, 0) + 1
        matches = [p for p in phases if p.get('phase_id') == ident]
        phase = matches[0] if len(matches) == 1 else {}
        ids = [s['step_id'] for s in planned['actions']]
        label = 'returning.phase.' + ident
        r.check(label + '.association', phase.get('actor_id') == owner and c.exact(phase.get('ordinal'), ordinal) and
                c.exact(phase.get('actor_visit'), visits[owner]) and phase.get('action_ids') == ids,
                'submitted phase owner, ordinal, visit and exact step IDs', available=available)
        order = c.mapping(phase.get('ordering'))
        r.check(label + '.collections', phase.get('arrival_observed') is True and phase.get('completion_observed') is True and
                phase.get('collection_status') == 'collected' and c.get(phase, 'validator_subprocess', 'reaped') is True and
                c.get(phase, 'validator_subprocess', 'expected_step_ids') == ids and
                all(order.get(k) is True for k in ('collection_closed_before_proceed', 'proceed_set', 'proceed_observed', 'worker_lifetime_established')) and
                order.get('validator_disposition') == 'reaped' and order.get('protocol_violations') == [],
                'phase arrival, collection, release, acknowledgement and completion', available=available)
        for submitted in planned['actions']:
            matches = [s for s in reply.get('steps', []) if s.get('step_id') == submitted['step_id']]
            step = matches[0] if len(matches) == 1 else {}
            label = 'returning.' + ident + '.' + submitted['step_id']
            associated = step.get('phase_id') == ident and step.get('actor_id') == owner and c.operands_match(step, submitted)
            r.check(label + '.association', associated, 'submitted phase, actor and operands', available=available)
            _, _, _, _, denied, failed = c.MATRIX[index]
            c.step_rows(r, label, step, submitted, passage.get('before'), available=available and len(matches) == 1,
                        stable=stable and associated and len(matches) == 1, denied=denied, failed=failed)
            index += 1
