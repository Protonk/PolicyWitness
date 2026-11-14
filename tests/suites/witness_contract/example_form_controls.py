"""Per-condition and ownership controls for the three example forms.

Each row here is a control of the same kind as the scalar rows and runs
through the same runner. A condition control changes one thing in one
submission's capture or request and states the one condition of its row that
must fail, with every other row it necessarily fails. The expected rows and
conditions are authored here; no checker output supplies one.
"""
import copy

import check_example_round_trip as checker
import example_round_trip_controls as scalar
from example_round_trip_controls import FORMS

ORDINARY = ('emitted', 'flat')
PHASED = ('emitted', 'actor')
ACTOR = ('actor',)
EXECUTION_FORM = 'structure.execution_form'
MEMBERSHIP = 'structure.phase_membership'
COLLECTIONS = scalar.COLLECTIONS
WORKER = 'structure.worker'
OWNERSHIP = 'structure.actor_ownership'
APPLICATION = 'structure.actor_application'
EQUIPMENT = 'structure.actor_equipment'
TRANSFORMATION = 'transformation'
# Everything read from a run: unevaluated when the derivative itself is refused.
BEHIND_TRANSFORMATION = ('passage.delivery_length', 'admission', 'identity', 'execution', 'echo', 'reported',
                         'readers', 'native', 'structure')
OTHER_ACTOR = 'another-reader'

reply = scalar.reply_of
phase = scalar.phase_of
actor = scalar.actor_of
worker = scalar.worker_of
step = scalar.step_of


def diagnostics(view):
    return scalar.envelope_of(view)['data']['runner_sandbox_diagnostics']


def dossiers(view):
    return scalar.envelope_of(view)['data']['specimen']['actors']


def with_phase(number):
    """The forms whose constructed reply has this phase."""
    return FORMS if number == 1 else PHASED


def controls():
    collected = scalar.Rows()
    add = collected.add

    def one(name, forms, change, row, condition, also=None, **requirements):
        """One change that fails one condition of one row. `also` names every other row it necessarily
        fails, with that row's failed conditions when it has them. The rest of the form holds."""
        also = also or {}
        add(name, change, [row], list(also), forms=forms, rest_holds=True,
            conditions={row: [condition], **{ident: names for ident, names in also.items() if names is not None}},
            **requirements)

    # The execution form.
    one('structure_other_execution_form', FORMS,
        lambda v: reply(v).update(execution_form='ordinary' if actor(v) else 'actors'), EXECUTION_FORM, 'execution_form')

    # Phase membership: the submitted partition, by position.
    one('membership_extra_phase', FORMS,
        lambda v: reply(v)['phases'].append(dict(copy.deepcopy(phase(v, 1)), phase_id='extra-phase',
                                                 ordinal=len(reply(v)['phases']) + 1, action_ids=[])),
        MEMBERSHIP, 'phase_count')
    one('membership_last_phase_dropped', FORMS, lambda v: reply(v)['phases'].pop(), MEMBERSHIP, 'phase_count',
        {COLLECTIONS: lambda form: [f'phase{scalar.phase_count(form)}.unique']})
    for number in (1, 2):
        forms = with_phase(number)
        one(f'membership_phase{number}_identifier', forms,
            lambda v, number=number: phase(v, number).update(phase_id='another-phase'),
            MEMBERSHIP, f'phase{number}.phase_id', {COLLECTIONS: [f'phase{number}.unique']})
        one(f'membership_phase{number}_ordinal', forms, lambda v, number=number: phase(v, number).update(ordinal=9),
            MEMBERSHIP, f'phase{number}.ordinal')
        one(f'membership_phase{number}_action_added', forms,
            lambda v, number=number: phase(v, number).update(action_ids=phase(v, number)['action_ids'] + ['another-step']),
            MEMBERSHIP, f'phase{number}.action_ids')
    one('membership_phase1_ordinal_boolean', FORMS, lambda v: phase(v, 1).update(ordinal=True), MEMBERSHIP, 'phase1.ordinal')
    one('membership_phase1_actions_reversed', PHASED, lambda v: phase(v, 1).update(action_ids=phase(v, 1)['action_ids'][::-1]),
        MEMBERSHIP, 'phase1.action_ids')

    # Collections: each submitted phase's own collection, completion and release chain.
    for number in (1, 2):
        forms = with_phase(number)

        def collection(name, change, condition, number=number, forms=forms, **requirements):
            one(f'collections_phase{number}_{name}', forms, lambda v: change(phase(v, number)), COLLECTIONS,
                f'phase{number}.{condition}', **requirements)
        one(f'collections_phase{number}_duplicated', forms,
            lambda v, number=number: reply(v)['phases'].append(copy.deepcopy(phase(v, number))),
            COLLECTIONS, f'phase{number}.unique', {MEMBERSHIP: ['phase_count']})
        collection('arrival_absent', lambda p: p.update(arrival_observed=False), 'arrival_observed')
        collection('completion_absent', lambda p: p.update(completion_observed=False), 'completion_observed')
        collection('not_collected', lambda p: p.update(collection_status='exhausted'), 'collection_status')
        collection('validator_not_reaped', lambda p: p['validator_subprocess'].update(reaped=False), 'validator_reaped')
        collection('collection_open_at_proceed', lambda p: p['ordering'].update(collection_closed_before_proceed=False),
                   'collection_closed_before_proceed')
        collection('proceed_not_set', lambda p: p['ordering'].update(proceed_set=False), 'proceed_set')
        collection('acknowledgement_absent', lambda p: p['ordering'].update(proceed_observed=False), 'proceed_observed',
                   consumer_reports='phase completion lacks arrival or acknowledgement')
        collection('worker_lifetime_unestablished', lambda p: p['ordering'].update(worker_lifetime_established=False),
                   'worker_lifetime_established')
        collection('validator_disposition', lambda p: p['ordering'].update(validator_disposition='killed'),
                   'validator_disposition')
        collection('protocol_violation', lambda p: p['ordering'].update(protocol_violations=['constructed violation']),
                   'protocol_violations')
        collection('another_query_plan', lambda p: p['validator_subprocess'].update(
            expected_step_ids=p['validator_subprocess']['expected_step_ids'] + ['another-step']),
                   'expected_step_ids')
        collection('acknowledgement_not_a_boolean', lambda p: p['ordering'].update(proceed_observed=1), 'proceed_observed')
    # A coherent reply to another partition, and to another phase label: the consumer reads both cleanly.
    add('wrong_partition',
        lambda v: scalar.repartition(reply(v), [(phase(v, 1)['phase_id'], reply(v)['steps'][:1]),
                                                (phase(v, 2)['phase_id'], reply(v)['steps'][1:])]),
        [MEMBERSHIP, COLLECTIONS], forms=PHASED, clean=True, rest_holds=True,
        conditions={MEMBERSHIP: ['phase1.action_ids', 'phase2.action_ids'],
                    COLLECTIONS: ['phase1.expected_step_ids', 'phase2.expected_step_ids']})
    add('foreign_phase',
        lambda v: scalar.repartition(reply(v), [('foreign-phase' if number == 1 else found['phase_id'],
                                                 [s for s in reply(v)['steps'] if s['step_id'] in found['action_ids']])
                                                for number, found in enumerate(reply(v)['phases'], 1)]),
        [MEMBERSHIP, COLLECTIONS], forms=FORMS, clean=True, rest_holds=True,
        conditions={MEMBERSHIP: ['phase1.phase_id'], COLLECTIONS: ['phase1.unique']})
    # The second phase carrying the first phase's collection: internally a reader rule, and here another plan.
    add('borrowed_collection',
        lambda v: phase(v, 2).update(validator_subprocess=copy.deepcopy(phase(v, 1)['validator_subprocess'])),
        [COLLECTIONS], forms=PHASED, rest_holds=True, conditions={COLLECTIONS: ['phase2.expected_step_ids']},
        consumer_reports='validator collection names another phase')

    # The worker: applied, owned by this reply, completed and reaped.
    one('worker_not_applied', ORDINARY, lambda v: reply(v).update(sandboxed_after_apply=False), WORKER, 'applied')
    one('worker_reply_names_another_process', ORDINARY, lambda v: reply(v).update(pid=4), WORKER, 'reply_pid')
    one('worker_process_identifier_zero', ORDINARY, lambda v: (reply(v).update(pid=0), worker(v).update(pid=0)),
        WORKER, 'pid')
    one('actor_worker_not_applied', ACTOR, lambda v: actor(v).update(applied=False), WORKER, 'applied',
        {APPLICATION: ['applied']})
    one('actor_launch_names_another_process', ACTOR, lambda v: actor(v)['launch'].update(pid=4), WORKER, 'launch_pid')
    one('actor_launch_names_another_parent', ACTOR, lambda v: actor(v)['launch'].update(parent_pid=4),
        WORKER, 'launch_parent_pid')
    one('actor_worker_process_identifier_zero', ACTOR,
        lambda v: (worker(v).update(pid=0), actor(v)['launch'].update(pid=0),
                   actor(v)['equipment']['execution'].update(pid=0)), WORKER, 'pid')
    for name, members, condition in (
            ('reap_absent', dict(reaped=False), 'reaped'),
            ('ready_byte_absent', dict(ready_byte_received=False), 'ready_byte_received'),
            ('completion_absent', dict(done_observed=False), 'done_observed'),
            ('exit_code_1', dict(exit_code=1), 'exit_code'),
            ('exit_code_boolean', dict(exit_code=False), 'exit_code'),
            ('terminated_by_signal', dict(term_signal=9), 'term_signal'),
            ('collected_before_reap', dict(collection_basis='at_deadline'), 'collection_basis')):
        one('worker_' + name, FORMS, lambda v, members=members: worker(v).update(members), WORKER, condition)

    # The actor's ownership of every projection of the run.
    one('ownership_second_reply_actor', ACTOR,
        lambda v: reply(v)['actors'].append(dict(copy.deepcopy(actor(v)), actor_id=OTHER_ACTOR)), OWNERSHIP, 'reply_actors')
    one('ownership_second_diagnostics_actor', ACTOR,
        lambda v: diagnostics(v)['actors'].append(dict(copy.deepcopy(diagnostics(v)['actors'][0]), actor_id=OTHER_ACTOR)),
        OWNERSHIP, 'diagnostics_actors')
    one('ownership_diagnostics_actor_renamed', ACTOR, lambda v: diagnostics(v)['actors'][0].update(actor_id=OTHER_ACTOR),
        OWNERSHIP, 'diagnostics_actors')
    one('ownership_second_dossier_actor', ACTOR,
        lambda v: dossiers(v).append(dict(copy.deepcopy(dossiers(v)[0]), actor_id=OTHER_ACTOR)), OWNERSHIP, 'dossier_actors')
    one('ownership_dossier_actor_renamed', ACTOR, lambda v: dossiers(v)[0].update(actor_id=OTHER_ACTOR),
        OWNERSHIP, 'dossier_actors', {'admission.dossier_policy_digest': None})
    one('ownership_one_visit', ACTOR, lambda v: actor(v).update(visits=[1]), OWNERSHIP, 'visits')
    for number in (1, 2):
        one(f'ownership_phase{number}_another_actor', ACTOR, lambda v, number=number: phase(v, number).update(actor_id=OTHER_ACTOR),
            OWNERSHIP, f'phase{number}.actor_id')
        one(f'ownership_phase{number}_another_visit', ACTOR, lambda v, number=number: phase(v, number).update(actor_visit=9),
            OWNERSHIP, f'phase{number}.actor_visit')
        one(f'ownership_phase{number}_termination_dependency', ACTOR,
            lambda v, number=number: phase(v, number).update(termination_gate={}), OWNERSHIP, f'phase{number}.no_termination_gate')
    for number in (1, 2, 3):
        one(f'ownership_step{number}_another_actor', ACTOR, lambda v, number=number: step(v, number).update(actor_id=OTHER_ACTOR),
            OWNERSHIP, f'step.step{number}.actor_id')
    one('ownership_unsubmitted_step_of_another_actor', ACTOR,
        lambda v: reply(v)['steps'].append(dict(copy.deepcopy(step(v, 1)), step_id='extra', actor_id=OTHER_ACTOR)),
        OWNERSHIP, 'unsubmitted_steps.actor_id', {'echo.step_ids': None})
    one('ownership_actor_disposition_invalid', ACTOR,
        lambda v: diagnostics(v)['actors'][0].update(disposition_integrity='invalid'), OWNERSHIP,
        'diagnostics.disposition_integrity')
    one('ownership_actor_disposition_issue', ACTOR,
        lambda v: diagnostics(v)['actors'][0].update(disposition_issues=[{'kind': 'constructed', 'detail': 'constructed issue'}]),
        OWNERSHIP, 'diagnostics.disposition_issues')

    # One application of the submitted policy.
    for name, members, condition in (
            ('unapplied_mode', dict(mode='none'), 'mode'),
            ('setup_timed_out', dict(setup_status='setup_timeout'), 'setup_status'),
            ('applied_twice', dict(application_count=2), 'application_count'),
            ('count_boolean', dict(application_count=True), 'application_count'),
            ('application_unobserved', dict(application={'state': 'unobserved', 'basis': 'applied_publication'}), 'application'),
            ('wrong_received_digest', dict(policy_received_sha256='00' * 32), 'policy_received_sha256')):
        one('application_' + name, ACTOR, lambda v, members=members: actor(v).update(members), APPLICATION, condition)

    # Selected equipment matched to the launched worker.
    for name, members, condition in (
            ('requested_other', dict(requested='entitled'), 'requested'),
            ('resolved_other', dict(resolved='entitled'), 'resolved'),
            ('entitlement_required', dict(required_entitlements=['com.example.entitlement']), 'required_entitlements'),
            ('requirements_unsatisfied', dict(requirements_status='unsatisfied'), 'requirements_status')):
        one('equipment_' + name, ACTOR, lambda v, members=members: actor(v)['equipment'].update(members), EQUIPMENT, condition)
    for name, members, condition in (
            ('execution_unobserved', dict(status='unobserved'), 'execution.status'),
            ('execution_ineligible', dict(eligible=False), 'execution.eligible'),
            ('execution_of_another_process', dict(pid=4), 'execution.pid')):
        one('equipment_' + name, ACTOR, lambda v, members=members: actor(v)['equipment']['execution'].update(members),
            EQUIPMENT, condition)
    add('actor_wrong_equipment', lambda v: actor(v)['equipment']['execution'].update(status='unobserved', eligible=False),
        [EQUIPMENT], forms=ACTOR, rest_holds=True, conditions={EQUIPMENT: ['execution.status', 'execution.eligible']})

    # An internally coherent capture for another actor name answers no part of the submitted request.
    def rename_actor(value):
        if isinstance(value, dict):
            for key, member in value.items():
                if key == 'actor_id':
                    value[key] = OTHER_ACTOR
                else:
                    rename_actor(member)
        elif isinstance(value, list):
            for member in value:
                rename_actor(member)
    add('foreign_actor', lambda v: rename_actor(scalar.envelope_of(v)['data']),
        [OWNERSHIP, APPLICATION, EQUIPMENT, WORKER, 'admission.dossier_policy_digest', 'admission.reply_policy_digest'],
        forms=ACTOR, clean=True, rest_holds=True,
        conditions={OWNERSHIP: ['reply_actors', 'diagnostics_actors', 'dossier_actors', 'visits', 'phase1.actor_id',
                                'phase2.actor_id', 'step.step1.actor_id', 'step.step2.actor_id', 'step.step3.actor_id'],
                    APPLICATION: ['mode', 'setup_status', 'applied', 'application_count', 'application',
                                  'policy_received_sha256'],
                    EQUIPMENT: ['requested', 'resolved', 'required_entitlements', 'requirements_status',
                                'execution.status', 'execution.eligible'],
                    WORKER: ['applied', 'launch_parent_pid', 'pid', 'reaped', 'ready_byte_received', 'done_observed',
                             'exit_code', 'collection_basis']})

    # Faults only the consumer's reader rules detect: its diagnostic alone, naming the rule.
    add('reader_query_live_process', lambda v: step(v, 1)['sandbox_check'].update(pid=99999), ['consumer_validation'],
        forms=FORMS, exactly_consumer=True, rest_holds=True, consumer_reports='query_first')
    add('reader_invented_singular_worker',
        lambda v: reply(v).update(runner_subprocess=copy.deepcopy(worker(v))), ['consumer_validation'],
        forms=ACTOR, exactly_consumer=True, rest_holds=True, consumer_reports='actor form carries singular runner_subprocess')

    # The derivatives: each permitted member, and each preserved one, judged before anything is run.
    def transform(name, form, change, *failed):
        add(f'{form}_transform_{name}', change, [TRANSFORMATION], forms=(form,), rest_holds=True,
            unevaluated=BEHIND_TRANSFORMATION, conditions={TRANSFORMATION: list(failed)})

    def document(change):
        return lambda v: scalar.set_input(v, change)

    def plan(d, number):
        return checker.actions(d)[number - 1]
    for form in ('flat', 'actor'):
        transform('extra', form, document(lambda d: d.update(extra=True)), 'members')
        transform('specimen_absent', form, document(lambda d: d.pop('specimen_id')), 'members')
        transform('identity', form, document(lambda d: d.update(contract=scalar.RELEASE)), 'preserved')
        transform('specimen', form, document(lambda d: d.update(specimen_id='different')), 'preserved')
        transform('not_an_object', form, lambda v: v.update(input=b'[]\n'), 'members')
        transform('not_retained', form, lambda v: v.update(input=None), 'members')
    # Another form's request in a derivative's place is not that derivative.
    for form, other in (('flat', 'actor'), ('actor', 'flat')):
        add(f'{form}_replaced_with_{other}',
            lambda state, form=form, other=other: state['forms'][form].update(input=state['forms'][other]['input']),
            [TRANSFORMATION], forms=(form,), rest_holds=True, unevaluated=BEHIND_TRANSFORMATION, whole_state=True,
            conditions={TRANSFORMATION: ['members']})
    transform('policy', 'flat', document(lambda d: d['policy'].update(sbpl_source='changed byte')), 'preserved')
    transform('phases_kept', 'flat', document(lambda d: d.update(phases=[])), 'members')
    transform('action_dropped', 'flat', document(lambda d: d['probe_plan'].pop()), 'actions')
    transform('plan_not_an_array', 'flat', document(lambda d: d.update(probe_plan={})), 'actions')
    for number in (1, 2, 3):
        transform(f'step{number}_operand', 'flat',
                  document(lambda d, number=number: plan(d, number)['attempt'].update(target='/different')),
                  f'action.step{number}')
    transform('operand', 'flat', document(lambda d: plan(d, 1)['sandbox_check']['filter'].update(value='/different')),
              'action.step1')
    transform('action', 'flat', document(lambda d: plan(d, 1)['attempt'].update(action='access')), 'action.step1')
    transform('actions_exchanged', 'flat', document(lambda d: d['probe_plan'].reverse()), 'action.step1', 'action.step3')

    def sole(d):
        return d['actors'][0]
    transform('policy', 'actor', document(lambda d: sole(d)['sandbox']['policy'].update(sbpl_source='changed byte')),
              'actor.sandbox.policy')
    transform('policy_kept', 'actor', document(lambda d: d.update(policy=copy.deepcopy(sole(d)['sandbox']['policy']))),
              'members')
    transform('no_actor', 'actor', document(lambda d: d.update(actors=[])), 'actors')
    transform('second_actor', 'actor', document(lambda d: d['actors'].append(dict(copy.deepcopy(sole(d)), actor_id='second'))),
              'actors')
    transform('actor_extra_member', 'actor', document(lambda d: sole(d).update(extensions=[])), 'actor.members')
    transform('actor_equipment_absent', 'actor', document(lambda d: sole(d).pop('equipment')), 'actor.members')
    transform('actor_identifier_empty', 'actor', document(lambda d: sole(d).update(actor_id='')), 'actor.actor_id')
    transform('actor_equipment', 'actor', document(lambda d: sole(d).update(equipment='entitled')), 'actor.equipment')
    transform('sandbox_extra_member', 'actor', document(lambda d: sole(d)['sandbox'].update(profile='x')),
              'actor.sandbox.members')
    transform('sandbox_not_an_object', 'actor', document(lambda d: sole(d).update(sandbox='apply')), 'actor.sandbox.members')
    transform('sandbox_unapplied', 'actor', document(lambda d: sole(d)['sandbox'].update(mode='none')), 'actor.sandbox.mode')
    transform('phase_dropped', 'actor', document(lambda d: d['phases'].pop()), 'phases')
    for number in (1, 2):
        transform(f'phase{number}_extra_member', 'actor',
                  document(lambda d, number=number: d['phases'][number - 1].update(note='x')), f'phase{number}.members')
        transform(f'phase{number}_unassigned', 'actor',
                  document(lambda d, number=number: d['phases'][number - 1].pop('actor_id')), f'phase{number}.members')
        transform(f'phase{number}_another_actor', 'actor',
                  document(lambda d, number=number: d['phases'][number - 1].update(actor_id=OTHER_ACTOR)),
                  f'phase{number}.actor_id')
        transform(f'phase{number}_relabeled', 'actor',
                  document(lambda d, number=number: d['phases'][number - 1].update(phase_id='relabeled')),
                  f'phase{number}.preserved')
        transform(f'phase{number}_operand', 'actor',
                  document(lambda d, number=number: d['phases'][number - 1]['actions'][0]['attempt'].update(target='/different')),
                  f'phase{number}.preserved')
    transform('operand', 'actor', document(lambda d: plan(d, 1)['sandbox_check']['filter'].update(value='/different')),
              'phase1.preserved')
    transform('action', 'actor', document(lambda d: plan(d, 1)['attempt'].update(action='access')), 'phase1.preserved')
    return collected.rows
