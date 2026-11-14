"""Constructed request and ownership controls for the three example forms.

Expected diagnostics are authored here. The ordinary model and native fault
mutators come from the scalar controls; the actor envelope is its own complete,
identity-free fixture. No live reply supplies an expected result.
"""
import copy
import hashlib
import json
from pathlib import Path

import example_round_trip_controls as scalar
import check_example_round_trip as checker
from blackbox import bind_constructed_envelope, recapture_host_reply


def repartition(reply, partitions):
    """Author a coherent partition, including collection ownership and step echoes."""
    templates = copy.deepcopy(reply['phases'])
    records = {r['step_id']: r for p in templates for r in p['validator_subprocess']['records']}
    reply['phases'] = []
    for ordinal, (label, steps) in enumerate(partitions, 1):
        phase = copy.deepcopy(templates[0])
        ids = [step['step_id'] for step in steps]
        phase.update(phase_id=label, ordinal=ordinal, action_ids=ids)
        phase['validator_subprocess'].update(phase_id=label, ordinal=ordinal, pid=52000+ordinal,
                                             expected_step_ids=ids, records=[records[sid] for sid in ids])
        if reply.get('execution_form') == 'actors':
            phase.update(actor_id=reply['actors'][0]['actor_id'], actor_visit=ordinal)
        for step in steps:
            step['phase_id'] = label
        reply['phases'].append(phase)


def build():
    """Independently authored requests; the checker constructor is not their oracle."""
    state = scalar.build()
    flat_doc = scalar.document_of(state)
    emitted = copy.deepcopy(flat_doc)
    steps = emitted.pop('probe_plan')
    emitted['phases'] = [{'phase_id': 'constructed-initial', 'actions': steps[:2]},
                         {'phase_id': 'constructed-restricted', 'actions': steps[2:]}]
    reply = scalar.reply_of(state)
    repartition(reply, [(p['phase_id'], reply['steps'][start:stop])
                         for p, start, stop in zip(emitted['phases'], (0, 2), (2, 3))])
    scalar.set_document(state, lambda d: (d.clear(), d.update(emitted)))
    state['refusals'] = {name: dict(input=body, exit=1, envelope=scalar.refusal_envelope(scalar.DEVELOPMENT, name), stderr=b'')
                         for name, body in checker.refusal_inputs(state['example-1']['stdout']).items()}
    scalar.envelope_of(state)['data']['runner_client']['request_delivery']['bytes_written'] = len(state['example-1']['stdout'])-1
    recapture_host_reply(scalar.envelope_of(state))
    flat = scalar.build()
    actor_doc = copy.deepcopy(emitted)
    actor_doc.pop('policy')
    actor_doc['actors'] = [{'actor_id': 'constructed-reader', 'equipment': 'selected',
                            'sandbox': {'mode': 'apply', 'policy': copy.deepcopy(emitted['policy'])}}]
    for phase in actor_doc['phases']:
        phase['actor_id'] = 'constructed-reader'
    actor = bind_constructed_envelope(json.loads(scalar.ACTOR_FIXTURE.read_text()))
    actor['build']['contract'] = actor['data']['runner_client']['transport']['contract'] = scalar.DEVELOPMENT
    actor['data']['runner_result']['producer']['contract'] = scalar.DEVELOPMENT
    state['forms'] = {}
    for form, doc, envelope in (('flat', flat_doc, scalar.envelope_of(flat)), ('actor', actor_doc, actor)):
        raw = (json.dumps(doc, indent=2, sort_keys=True)+'\n').encode()
        envelope['data']['runner_client']['request_delivery']['bytes_written'] = len(raw)-1
        recapture_host_reply(envelope)
        state['forms'][form] = {'input': raw, 'run': {'exit': 0, 'envelope': envelope, 'stderr': b''},
                                'targets-before': copy.deepcopy(state['targets-before']),
                                'targets-after': copy.deepcopy(state['targets-after'])}
    return state


def capture(state, form):
    return state if form == 'emitted' else state['forms'][form]


def document(state, form):
    return scalar.document_of(state) if form == 'emitted' else json.loads(capture(state, form)['input'])


def set_input(state, form, change):
    if form == 'emitted':
        scalar.set_document(state, change)
    else:
        value = document(state, form)
        change(value)
        capture(state, form)['input'] = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def write(directory, state):
    scalar.write(directory, state)
    for form, entry in state.get('forms', {}).items():
        # Reuse the capture writer; no imaginary version/emission observations.
        child = dict(entry, refusals={})
        scalar.write(directory / form, child)
        (directory / form / 'input.json').write_bytes(entry['input'])


def evaluate(artifacts, name, state):
    for form in ('emitted', 'flat', 'actor'):
        entry = capture(state, form)
        if entry.get('run') is not None and 'envelope' in entry['run']:
            recapture_host_reply(entry['run']['envelope'])
    directory = artifacts / 'form-captures' / name
    write(directory, state)
    report = checker.evaluate(checker.load(directory), authored_fixture=True)
    (directory / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def run(artifacts):
    records = []
    baseline = evaluate(artifacts, 'passing', build())
    assert not baseline['consumer_errors'], baseline['consumer_errors']
    assert all(r['status'] == 'pass' for r in baseline['assertions']), checker.render(baseline)
    records.append({'control': 'complete_three_form_baseline', 'assertions': len(baseline['assertions'])})
    covered = set()

    def check(name, change, expected, *, clean=True, withheld=(), reader=None):
        state = build()
        change(state)
        report = evaluate(artifacts, name, state)
        actual = checker.diagnostics(report)
        wanted = {(ident, scalar.expected_classification(ident.split('.', 1)[1] if ident.startswith(('flat.', 'actor.')) else ident))
                  for ident in expected}
        if not clean:
            actual = {pair for pair in actual if not pair[0].endswith('consumer_validation')}
        assert actual == wanted, (name, actual, wanted, report['consumer_errors'])
        if clean:
            assert not report['consumer_errors'], (name, report['consumer_errors'])
        if reader:
            assert any(reader in error for error in report['consumer_errors']), (name, report['consumer_errors'])
        statuses = {r['id']: r['status'] for r in report['assertions']}
        assert all(statuses[i] == 'not_evaluated' for i in withheld), (name, statuses)
        covered.update(expected)
        records.append({'control': name, 'expected': sorted(wanted), 'consumer_errors': report['consumer_errors'],
                        'withheld': list(withheld)})
        return report

    # The same wrong answer must fail all three independent oracles.
    check('shared_wrong_answer', lambda s: [scalar.set_answer(capture(s, f), 3, scalar.ALLOW) for f in ('emitted','flat','actor')],
          ['native.step3.prediction','flat.native.step3.prediction','actor.native.step3.prediction'])
    for form in ('emitted', 'flat', 'actor'):
        prefix = '' if form == 'emitted' else form+'.'
        def reply(s):
            return scalar.reply_of(capture(s, form))
        check(form+'_wrong_execution_form', lambda s: reply(s).update(execution_form='ordinary' if form=='actor' else 'actors'),
              [prefix+'structure.execution_form'], clean=False)
        check(form+'_one_sided_step_rename', lambda s: reply(s)['steps'][0].update(step_id='other-label'),
              [prefix+'echo.step_ids'], clean=False,
              withheld=[prefix+'native.step1.prediction',prefix+'native.step1.attempt'])
        check(form+'_reordered_steps', lambda s: reply(s)['steps'].reverse(), [prefix+'echo.step_ids'], clean=False)
        check(form+'_dropped_step', lambda s: reply(s)['steps'].pop(1), [prefix+'echo.step_ids'], clean=False,
              withheld=[prefix+i for i in scalar.STEP_NATIVE[2]])
        check(form+'_duplicate_step', lambda s: reply(s)['steps'].append(copy.deepcopy(reply(s)['steps'][1])),
              [prefix+'echo.step_ids'], clean=False, withheld=[prefix+i for i in scalar.STEP_NATIVE[2]])
        if form == 'flat':
            check('flat_foreign_phase', lambda s: repartition(reply(s), [('foreign-phase', reply(s)['steps'])]),
                  ['flat.structure.phase_membership','flat.structure.collections'])
        if form != 'flat':
            check(form+'_wrong_partition', lambda s: repartition(reply(s), [
                (reply(s)['phases'][0]['phase_id'], reply(s)['steps'][:1]),
                (reply(s)['phases'][1]['phase_id'], reply(s)['steps'][1:])]),
                [prefix+'structure.phase_membership',prefix+'structure.collections'])
            check(form+'_borrowed_collection', lambda s: reply(s)['phases'][1].update(
                validator_subprocess=copy.deepcopy(reply(s)['phases'][0]['validator_subprocess'])),
                [prefix+'structure.collections'], clean=False, reader='validator collection names another phase')
        check(form+'_missing_completion', lambda s: reply(s)['phases'][-1].update(completion_observed=False),
              [prefix+'structure.collections'])
        check(form+'_missing_acknowledgement', lambda s: reply(s)['phases'][-1]['ordering'].update(proceed_observed=False),
              [prefix+'structure.collections'], clean=False, reader='phase completion lacks arrival or acknowledgement')
        check(form+'_worker_reap_absent', lambda s: (reply(s)['actors'][0]['subprocess'] if form=='actor' else reply(s)['runner_subprocess']).update(reaped=False),
              [prefix+'structure.worker'], clean=False)
        check(form+'_query_live_pid', lambda s: reply(s)['steps'][0]['sandbox_check'].update(pid=99999),
              [], clean=False, reader='query_first')
        # State the expected whole scalar diagnostic set independently; repeat the
        # reviewed fresh-read and missing-evidence distinctions through every form.
        selected = [row for row in scalar.controls() if row['name'].startswith(('fresh_', 'target_', 'targets_', 'prerequisite_'))]
        selected += [row for row in scalar.controls() if row['name'] in (
            'native_step1_deny_answer', 'native_step2_deny_answer', 'native_step3_eacces',
            'native_step3_allow_answer_with_successful_open', 'native_step1_eperm',
            'combined_prerequisite_and_consistency', 'combined_native_faults')]
        for row in selected:
            expected = [prefix+i for i,_ in row['expected']]
            if row['name'] in ('prerequisite_B_unreadable_and_order_unestablished', 'prerequisite_C_unreadable_and_validator_spawn_failed'):
                expected.append(prefix+'structure.collections')
            withheld = [prefix+i for i in row['unevaluated']]
            check(form+'_'+row['name'], lambda s, row=row: row['change'](capture(s, form)), expected,
                  clean=row['clean'], withheld=withheld)
    # The foreign actor remains coherent in every actor-owned account.
    def rename_actor(s, name, *, request=False):
        entry = capture(s, 'actor')
        def rename(value):
            if isinstance(value, dict):
                for k,v in value.items():
                    if k == 'actor_id': value[k] = name
                    else: rename(v)
            elif isinstance(value, list):
                for v in value: rename(v)
        rename(entry['run']['envelope']['data'])
        if request: set_input(s, 'actor', rename)
    check('foreign_actor', lambda s: rename_actor(s, 'another-reader'),
          ['actor.admission.dossier_policy_digest','actor.admission.reply_policy_digest','actor.structure.actor_ownership',
           'actor.structure.actor_application','actor.structure.actor_equipment','actor.structure.worker'])
    check('actor_wrong_received_digest', lambda s: scalar.reply_of(capture(s,'actor'))['actors'][0].update(policy_received_sha256='00'*32),
          ['actor.structure.actor_application'])
    check('actor_invented_singular_worker', lambda s: scalar.reply_of(capture(s,'actor')).update(
          runner_subprocess=copy.deepcopy(scalar.reply_of(capture(s,'actor'))['actors'][0]['subprocess'])),
          [], clean=False, reader='actor form carries singular runner_subprocess')
    check('actor_wrong_equipment', lambda s: scalar.reply_of(capture(s,'actor'))['actors'][0]['equipment']['execution'].update(status='unobserved',eligible=False),
          ['actor.structure.actor_equipment'])
    # Mutations to every preserved transformation dimension are caught before run.
    for form in ('flat','actor'):
        for label, change in [
            ('identity',lambda d:d.update(contract=scalar.RELEASE)),
            ('specimen',lambda d:d.update(specimen_id='different')),
            ('policy',lambda d:checker.submitted_policy(d,form).update(sbpl_source='changed byte')),
            ('operand',lambda d:checker.actions(d)[0]['attempt'].update(target='/different')),
            ('action',lambda d:checker.actions(d)[0]['attempt'].update(action='access')),
            ('extra',lambda d:d.update(extra=True)),
        ]:
            check(form+'_transform_'+label, lambda s, change=change:set_input(s,form,change), [form+'.transformation'])
        other='actor' if form=='flat' else 'flat'
        check(form+'_replaced_with_'+other, lambda s:capture(s,form).update(input=capture(s,other)['input']), [form+'.transformation'])
    # A renamed experiment changes all submitted labels and capture associations.
    state = build()
    rename_actor(state,'renamed-reader',request=True)
    for form in ('emitted','flat','actor'):
        entry=capture(state,form)
        mapping={s['step_id']:'renamed-'+str(i) for i,s in enumerate(checker.actions(document(state,form)))}
        if form!='flat':mapping.update({p['phase_id']:'renamed-phase-'+str(i) for i,p in enumerate(document(state,form)['phases'])})
        def renamed(value):
            if isinstance(value,str):return mapping.get(value,value)
            if isinstance(value,list):return [renamed(v) for v in value]
            if isinstance(value,dict):return {k:renamed(v) for k,v in value.items()}
            return value
        doc=renamed(document(state,form))
        set_input(state,form,lambda d:(d.clear(),d.update(doc)))
        entry['run']['envelope']=renamed(entry['run']['envelope'])
        for phase in scalar.reply_of(entry)['phases']:
            for row in phase['validator_subprocess']['records']:
                row['raw_line']=json.dumps(renamed(json.loads(row['raw_line'])),separators=(',',':'))
        raw=state['example-1']['stdout'] if form=='emitted' else entry['input']
        entry['run']['envelope']['data']['runner_client']['request_delivery']['bytes_written']=len(raw)-1
    state['refusals']={name:dict(input=body,exit=1,envelope=scalar.refusal_envelope(scalar.DEVELOPMENT,name),stderr=b'')
                       for name,body in checker.refusal_inputs(state['example-1']['stdout']).items()}
    report=evaluate(artifacts,'consistent_renaming',state)
    assert all(r['status']=='pass' for r in report['assertions']),checker.render(report)
    records.append({'control':'consistent_renaming','status':report['status']})
    original = checker._diagnostic
    try:
        checker._diagnostic = lambda *args: {'formatting': 'deliberately omitted'}
        reformatted = evaluate(artifacts, 'summary_format_independent', build())
        assert reformatted['assertions'] == baseline['assertions']
    finally:
        checker._diagnostic = original
    records.append({'control': 'summary_format_independent', 'assertions_unchanged': True})
    required = {('' if form=='emitted' else form+'.')+row[0]
                for form in ('emitted','flat','actor') for row in checker.STRUCTURE_ASSERTIONS}
    required.update('actor.'+row[0] for row in checker.ACTOR_ASSERTIONS)
    required.update(('flat.transformation','actor.transformation'))
    assert required <= covered, required-covered
    (artifacts/'example-form-controls.json').write_text(json.dumps({'controls':records,'covered':sorted(covered)},indent=2)+'\n')
    return records
