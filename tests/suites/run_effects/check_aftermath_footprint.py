"""Object-lifetime ledger for public CLI footprint runs.

Process exit is an independent NOTE_EXIT observation. Mapping disposal, byte
 erasure, native authority release and parent reap remain separate facts.
"""
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from footprint_observer import FootprintObserver, GenerationExitObserver, generation, sha256

STATES = {'present', 'absence_confirmed', 'unknown'}
CATEGORIES = {'baseline', 'specimen_effect', 'requested_output', 'apparatus', 'observer'}
BOUNDARIES = {'baseline', 'cli_return', 'resource_end'}


def expected_inventory_ids(r):
    count = 2 if r['configuration']['form'] == 'actor' else 1
    ids = {'host', 'validator', 'observer-process', 'installation', 'target', 'marker',
           'requested-envelope', 'requested-stderr', 'gate-socket', 'tree-socket', 'owned-staging',
           'exit-watchers', 'instrumentation-output'}
    for i in range(count):
        ids.add(f'worker-{i}')
        for kind in ('evidence_backing', 'launch_descriptor') + (('authority_backing', 'handle_table') if count == 2 else ()):
            ids.add(f'{kind}-{i}')
    if count == 2:
        ids |= {'private_custody', 'native_handle-H1', 'native_handle-H2', 'native_handle-H3'}
    return ids


def validate_actor_inventory(objects, held):
    backings = []
    for i in range(2):
        for kind in ('evidence_backing', 'authority_backing', 'launch_descriptor', 'handle_table'):
            obj = objects[f'{kind}-{i}']
            assert obj['actor_index'] == i and obj['worker_identity'] == objects[f'worker-{i}']['identity'], 'resource owner swap'
            if kind in ('evidence_backing', 'authority_backing'):
                assert obj['views'] == {'host': 'host', 'worker': f'worker-{i}'}
                backings.append(obj['backing_id'])
            if kind == 'authority_backing':
                assert obj['logical_capacity'] == next(x for x in held['regions'] if x['actor_index'] == i)
        assert objects[f'handle_table-{i}']['logical_capacity']['entries'] == 64
    assert len(backings) == len(set(backings)), 'duplicate backing identity'
    assert objects['private_custody']['references'] == {'token': 'T', 'actor_index': 0}
    for h, delivery in (('H1', 'D1'), ('H2', 'D1'), ('H3', 'D2')):
        assert objects['native_handle-'+h]['references'] == {'handle': h, 'delivery': delivery, 'token': 'T', 'actor_index': 1}


def validate_receipt(r):
    assert r['schema_version'] == 1 and r['case_id'] == 'run_effects/aftermath_footprint'
    for key in ('run_id', 'workload_id', 'request_sha256', 'source_identity',
                'inspected_binaries', 'conditions', 'observer', 'configuration'):
        assert r[key], key
    assert r['clock'] == 'mach_continuous_time_ns'
    assert r['configuration']['completion_repetitions'] == 3
    assert r['configuration']['form'] in ('ordinary', 'actor')
    assert r['configuration']['path'] in ('completion', 'timeout')
    inventory = r['inventory']
    ids = [o['id'] for o in inventory]
    assert ids and len(ids) == len(set(ids)), 'duplicate inventory identity'
    objects = {o['id']: o for o in inventory}
    required = {o['id'] for o in inventory if o.get('required_process')}
    assert required == {f'worker-{i}' for i in range(2 if r['configuration']['form'] == 'actor' else 1)}, 'missing/incorrect required workers'
    for o in inventory:
        assert o['category'] in CATEGORIES and o['owner'] and o['ownership_basis']
        assert o['creation_evidence'] and o['expected_end']
        assert o['category'] != 'baseline' or o['creation_evidence']['pre_existing'] is True
        if o['type'] == 'process':
            assert set(o['identity']) == {'pid', 'start_sec', 'start_usec'}
        if o.get('surface') in ('mapping', 'custody', 'handle_table'):
            assert o['expected_end'] not in ('native_release', 'byte_erasure'), 'conflated resource ending'
    snapshots = r['snapshots']
    assert [s['boundary'] for s in snapshots] == ['baseline', 'cli_return', 'resource_end'], 'missing/reordered/duplicate boundary'
    assert all(a['end_ns'] <= b['begin_ns'] for a, b in zip(snapshots, snapshots[1:])), 'snapshot order'
    for snap in snapshots:
        assert snap['cli_relative_ns'] == snap['end_ns'] - r['cli_return_ns'], 'wrong CLI-relative time'
    assert snapshots[2]['assisted'] == (r['configuration']['path'] == 'timeout'), 'wrong assistance status'
    primary = [s for s in snapshots if s['boundary'] == 'cli_return']
    assert len(primary) == 1 and primary[0]['assisted'] is False
    for snap in snapshots:
        assert type(snap['begin_ns']) is int and type(snap['end_ns']) is int and 0 <= snap['begin_ns'] <= snap['end_ns']
        assert type(snap['cli_relative_ns']) is int
        entries = snap['objects']
        assert len(entries) == len(ids) and {e['id'] for e in entries} == set(ids), 'omitted/duplicate object state'
        for e in entries:
            obj = objects[e['id']]
            assert e['state'] in STATES and e['evidence'] and 'native_error' in e
            assert e['ending_status'] in ('observed', 'pending', 'unestablished')
            if e['state'] == 'present' and obj['type'] == 'process':
                if 'sample' in e['evidence']:
                    assert generation(e['evidence']['sample']) == obj['identity'], 'present identity swap'
                else:
                    assert e['evidence']['identity'] == obj['identity'], 'present identity swap'
            if e['state'] == 'unknown':
                assert e['reason'], 'unknown needs reason'
            if e['state'] == 'absence_confirmed':
                assert e['native_error'] is None, 'inspection error is not absence'
                assert e['evidence']['identity'] == obj['identity'], 'identity swap'
                assert e['evidence']['source'] in ('EVFILT_PROC NOTE_EXIT', 'pathname binding inspection', 'not_created_yet')
                if obj['type'] == 'pathname_binding' and e['evidence']['source'] != 'not_created_yet':
                    assert e['evidence']['scope'] == 'name binding only; inode lifetime unestablished'
                assert not e['evidence'].get('leader_exit'), 'leader exit does not establish descendant exit'
                assert obj.get('surface') not in ('mapping', 'custody', 'handle_table'), 'process exit alone is not direct mapping inspection'
            if snap['boundary'] != 'baseline' and e['id'] in required:
                assert e['state'] != 'unknown', 'required worker observation unknown'
            if snap['boundary'] == 'baseline' and obj['category'] == 'baseline':
                assert e['state'] == 'present', 'baseline registration relabeled'
    for intervention in r['interventions']:
        assert primary[0]['end_ns'] <= intervention['begin_ns'] <= intervention['end_ns'], 'intervention precedes primary snapshot'
        for key in ('action', 'target_identity', 'ownership', 'reason', 'native_result', 'native_error', 'later_observation'):
            assert key in intervention, key
        assert intervention['native_error'] is None and intervention['native_result'] == 'returned'
        if intervention['action'] == 'gate release':
            assert intervention['target_identity']['generation'] == objects['validator']['identity']
            assert intervention['later_observation']['boundary'] == 'resource_end'
            assert intervention['end_ns'] <= snapshots[-1]['begin_ns']
        elif intervention['action'] == 'fixture finish':
            assert intervention['target_identity']['identity'] == objects['owned-staging']['identity']
            later = intervention['later_observation']
            assert later['begin_ns'] >= intervention['begin_ns'] and later['end_ns'] <= intervention['end_ns']
            assert later['staging_binding_absent'] is True and later['all_registered_ends'] is True
    by_boundary = {s['boundary']: {e['id']: e for e in s['objects']} for s in snapshots}
    end_events = r['end_events']
    for event in end_events:
        assert event['identity'] == objects[event['object_id']]['identity'] == event['generation']
        assert type(event['collection_begin_ns']) is int and type(event['collection_end_ns']) is int
        assert 0 <= event['collection_begin_ns'] <= event['collection_end_ns'] <= snapshots[-1]['end_ns'], 'invalid event time'
        for snap in snapshots:
            if snap['begin_ns'] >= event['collection_end_ns']:
                entry = next(e for e in snap['objects'] if e['id'] == event['object_id'])
                assert entry['state'] == 'absence_confirmed', 'established exit cannot be replaced by inspectable process record'
        assert any(w['generation'] == event['generation'] and w['end_ns'] <= event['collection_begin_ns'] for w in r['exit_registrations']), 'unregistered exit'
    effects = r['invocation']['effects']
    assert effects['target_unchanged'] is True and effects['marker_unchanged'] is True and effects['exec_connected'] is False, 'early requested effect'
    assert effects['gate']['event'] == 'held'
    assert any(e['event'] == 'ready' for e in r['invocation']['gate']), 'missing gate readiness'
    assert effects['gate'] in r['invocation']['gate'], 'missing acknowledged hold event'
    ready = r['invocation']['ready']
    assert ready['event'] == 'ready' and ready in r['invocation']['gate'], 'missing exact ready event'
    assert ready['target_pid'] in {objects[oid]['identity']['pid'] for oid in required}, 'held target is not a required worker'
    assert r['invocation']['established_before_timeout'] is True
    assert expected_inventory_ids(r) <= set(ids), 'omitted required inventory row'
    assert set(r['expected_inventory_ids']) == expected_inventory_ids(r), 'inventory expectation changed'
    assert all(o['id'] in expected_inventory_ids(r) or o.get('optional_surface') is True for o in inventory), 'unexpected inventory row'
    for oid in required:
        obj = objects[oid]
        assert any(w['generation'] == obj['identity'] for w in r['exit_registrations']), 'missing exit watch'
        if r['configuration']['path'] == 'timeout':
            assert r['invocation']['established_before_timeout'] is True
            assert by_boundary['cli_return'][oid]['state'] == 'present', 'timeout worker must remain observed'
        else:
            assert any(e['object_id'] == oid and e['source'] == 'EVFILT_PROC NOTE_EXIT'
                       and e['identity'] == obj['identity'] for e in end_events), 'missing independent worker exit'
    for oid in ('host', 'validator'):
        assert any(e['object_id'] == oid and e['identity'] == objects[oid]['identity']
                   and e['source'] == 'EVFILT_PROC NOTE_EXIT' for e in end_events), 'missing apparatus process exit'
    if r['configuration']['path'] == 'timeout':
        terminal = r['invocation']['terminal_capture']
        assert terminal['terminal'] == 'xpc_timeout' and terminal['submission']['state'] == 'invoked', 'timeout lacks invoked terminal capture'
    if r['configuration']['form'] == 'actor':
        from footprint_workloads import check_snapshot, check_held_binding
        check_held_binding(r['held_state']['snapshot'], r['invocation']['ready'], r['held_state']['generations'])
        held = check_snapshot(r['held_state']['snapshot'], lifecycle=True)
        assert len(required) == 2
        assert [objects[f'worker-{i}']['identity']['pid'] for i in range(2)] == [a['pid'] for a in held['actors']], 'actor generation association'
        validate_actor_inventory(objects, held)
        for surface in ('evidence_backing', 'authority_backing', 'launch_descriptor', 'private_custody', 'handle_table', 'native_handle'):
            assert any(o.get('resource_kind') == surface for o in inventory), surface
    assert r['cleanup']['status'] in ('complete', 'retained')
    if r['cleanup']['status'] == 'retained':
        assert r['cleanup']['recovery_record'], 'cleanup ownership missing'
    return r


def checker_controls():
    """Independent ledger inputs, including a real premature unlink intervention."""
    g = {'pid': 123, 'start_sec': 20, 'start_usec': 1}
    obj = {'id': 'worker-0', 'type': 'process', 'identity': g, 'owner': 'host',
           'ownership_basis': 'registered generation', 'category': 'apparatus',
           'creation_evidence': {'launch': True}, 'expected_end': 'exit', 'required_process': True}
    def state(boundary):
        absent = boundary != 'cli_return'
        return {'id': 'worker-0', 'state': 'absence_confirmed' if absent else 'present',
                'evidence': {'identity': g, 'source': 'not_created_yet' if boundary == 'baseline' else 'EVFILT_PROC NOTE_EXIT'},
                'native_error': None, 'ending_status': 'observed' if absent else 'pending'}
    valid = {'schema_version': 1, 'case_id': 'run_effects/aftermath_footprint',
             'clock': 'mach_continuous_time_ns', 'configuration': {'completion_repetitions': 3, 'path': 'completion', 'form': 'ordinary'},
             'inventory': [obj], 'snapshots': [{'boundary': b, 'begin_ns': i*10, 'end_ns': i*10+1,
                'cli_relative_ns': i*10-10, 'assisted': False, 'objects': [state(b)]}
                for i, b in enumerate(('baseline', 'cli_return', 'resource_end'))],
             'cli_return_ns': 11, 'interventions': [], 'exit_registrations': [{'generation': g, 'begin_ns': 1, 'end_ns': 2}],
             'end_events': [{'object_id': 'worker-0', 'identity': g, 'generation': g, 'source': 'EVFILT_PROC NOTE_EXIT', 'collection_begin_ns': 18, 'collection_end_ns': 19}],
             'cleanup': {'status': 'complete'}, 'invocation': {'established_before_timeout': True,
                 'ready': {'event': 'ready', 'target_pid': 123},
                 'gate': [{'event': 'ready', 'target_pid': 123}, {'event': 'held'}],
                 'effects': {'target_unchanged': True, 'marker_unchanged': True, 'exec_connected': False, 'gate': {'event': 'held'}}}}
    for key in ('run_id', 'workload_id', 'request_sha256', 'source_identity', 'inspected_binaries', 'conditions', 'observer'):
        valid[key] = {'fixture': True}
    # Complete ordinary inventory independently populated for interpretation controls.
    for oid in sorted(expected_inventory_ids(valid)-{'worker-0'}):
        identity = dict(g, pid=124 if oid == 'host' else 125) if oid in ('host','validator') else {'fixture_object': oid}
        obj2 = dict(id=oid,type='process' if oid in ('host','validator') else 'observer_resource',identity=identity,
                    owner='fixture',ownership_basis='independent control',category='observer',
                    creation_evidence={'pre_existing': True},expected_end='control teardown')
        valid['inventory'].append(obj2)
        for snap in valid['snapshots']:
            snap['objects'].append(dict(id=oid,state='absence_confirmed' if oid in ('host','validator') and snap['boundary']=='resource_end' else 'present',
                evidence={'identity':identity,'source':'EVFILT_PROC NOTE_EXIT'},native_error=None,ending_status='pending'))
        if oid in ('host','validator'):
            valid['exit_registrations'].append(dict(generation=identity,begin_ns=1,end_ns=2))
            valid['end_events'].append(dict(object_id=oid,identity=identity,generation=identity,source='EVFILT_PROC NOTE_EXIT',collection_begin_ns=18,collection_end_ns=19))
    valid['expected_inventory_ids'] = sorted(expected_inventory_ids(valid))
    validate_receipt(valid)
    optional = copy.deepcopy(valid)
    optional['inventory'].append({'id': 'optional_mapping', 'type': 'logical_resource', 'identity': {'mapping': 'fixture'},
        'owner': 'host', 'ownership_basis': 'component', 'category': 'apparatus', 'optional_surface': True,
        'creation_evidence': {'source': True}, 'expected_end': 'unmap', 'surface': 'mapping'})
    for snap in optional['snapshots']:
        snap['objects'].append({'id': 'optional_mapping', 'state': 'unknown', 'evidence': {'inspection': 'unsupported'},
            'native_error': 1, 'reason': 'optional live mapping inspection unavailable', 'ending_status': 'unestablished'})
    validate_receipt(optional)
    baseline_control = copy.deepcopy(valid)
    baseline_control['inventory'].append({'id': 'registration', 'type': 'registry', 'identity': {'baseline': 'owned'},
        'owner': 'user', 'ownership_basis': 'pre-run inventory', 'category': 'baseline', 'optional_surface': True,
        'creation_evidence': {'pre_existing': True}, 'expected_end': 'retained'})
    for snap in baseline_control['snapshots']:
        snap['objects'].append({'id': 'registration', 'state': 'present', 'evidence': {'identity': {'baseline': 'owned'}},
                               'native_error': None, 'ending_status': 'pending'})
    validate_receipt(baseline_control)
    baseline_control['inventory'][-1]['creation_evidence']['pre_existing'] = False
    try:
        validate_receipt(baseline_control)
    except AssertionError:
        pass
    else:
        raise AssertionError('accepted baseline registration as run-created')
    mutations = [
        ('omitted inventory and states', lambda r: (r['inventory'].pop(), [s['objects'].pop() for s in r['snapshots']])),
        ('omitted state', lambda r: r['snapshots'][1]['objects'].clear()),
        ('missing baseline', lambda r: r['snapshots'].pop(0)),
        ('unsupported absence', lambda r: r['snapshots'][2]['objects'][0].update(native_error=3)),
        ('identity swap', lambda r: r['snapshots'][2]['objects'][0].update(evidence={'identity': dict(g, start_usec=2), 'source': 'EVFILT_PROC NOTE_EXIT'})),
        ('descendant from leader', lambda r: r['snapshots'][2]['objects'][0]['evidence'].update(leader_exit=True)),
        ('required unknown', lambda r: r['snapshots'][1]['objects'][0].update(state='unknown', reason='refused')),
        ('premature intervention', lambda r: r['interventions'].append({'begin_ns': 0, 'end_ns': 1})),
        ('exited record mislabeled executing', lambda r: r['snapshots'][2]['objects'][0].update(state='present')),
        ('missing exit', lambda r: r['end_events'].clear()),
        ('missing event timestamp', lambda r: r['end_events'][0].pop('collection_begin_ns')),
        ('reversed event timestamp', lambda r: r['end_events'][0].update(collection_begin_ns=20, collection_end_ns=19)),
        ('shifted primary', lambda r: r['snapshots'][1].update(cli_relative_ns=999)),
        ('assistance mislabeled', lambda r: r['snapshots'][2].update(assisted=True)),
        ('missing effects', lambda r: r['invocation'].pop('effects')),
        ('missing hold acknowledgement', lambda r: r['invocation']['gate'].pop()),
        ('missing ready evidence', lambda r: r['invocation'].pop('ready')),
        ('unknown form', lambda r: r['configuration'].update(form='unknown')),
        ('unknown path', lambda r: r['configuration'].update(path='unknown')),
        ('missing required worker marker', lambda r: r['inventory'][0].pop('required_process')),
        ('early effect', lambda r: r['invocation'].update(effects={'target_unchanged': False, 'marker_unchanged': True, 'exec_connected': False})),
    ]
    results = [{'control': 'baseline registration relabeled run-created', 'rejected': True}]
    for name, mutate in mutations:
        bad = copy.deepcopy(valid)
        mutate(bad)
        try:
            validate_receipt(bad)
        except (AssertionError, KeyError) as exc:
            results.append({'control': name, 'rejected': True, 'diagnostic': str(exc)})
        else:
            raise AssertionError(f'accepted {name}')
    # Metadata-only lifecycle fixture independently constructed from publication
    # meanings. No live bearer bytes are read or reproduced by these controls.
    from footprint_workloads import check_snapshot
    sys.path.insert(0, str(Path(__file__).parents[1] / 'witness_contract'))
    from held_phase_footprint_controls import actor_snapshot
    held = actor_snapshot()
    check_snapshot(held, lifecycle=True)
    actor_objects = {}
    for i, actor in enumerate(held['actors']):
        identity = dict(g, pid=actor['pid'])
        actor_objects[f'worker-{i}'] = {'identity': identity}
        for kind in ('evidence_backing','authority_backing','launch_descriptor','handle_table'):
            actor_objects[f'{kind}-{i}'] = dict(actor_index=i,worker_identity=identity,
                views={'host':'host','worker':f'worker-{i}'},backing_id=f'{kind}-{i}',
                logical_capacity=held['regions'][i] if kind=='authority_backing' else {'entries':64})
    actor_objects['private_custody'] = {'references': {'token':'T','actor_index':0}}
    for h,d in (('H1','D1'),('H2','D1'),('H3','D2')):
        actor_objects['native_handle-'+h] = {'references': {'handle':h,'delivery':d,'token':'T','actor_index':1}}
    validate_actor_inventory(actor_objects, held)
    for name,mutate in (
        ('omitted actor evidence object',lambda x:x.pop('evidence_backing-1')),
        ('swapped resource owner',lambda x:x['authority_backing-1'].update(actor_index=0)),
        ('duplicate backing',lambda x:x['authority_backing-1'].update(backing_id=x['authority_backing-0']['backing_id']))):
        bad=copy.deepcopy(actor_objects); mutate(bad)
        try:
            validate_actor_inventory(bad,held)
        except (AssertionError,KeyError) as exc:
            results.append({'control':name,'rejected':True,'diagnostic':str(exc)})
        else:
            raise AssertionError('accepted '+name)
    for name, mutate in (
        ('pre-consume actor', lambda x: x['actors'][1]['slots'][0].update(completed=0)),
        ('swapped delivery references', lambda x: x['deliveries'][0].update(recipient_actor=0)),
        ('erased custody', lambda x: x['tokens'][0].update(erased=True)),
        ('withdrawn delivery', lambda x: x['deliveries'][0].update(settled=0)),
        ('already attempted release', lambda x: x['actors'][1]['slots'][4].update(call_boundary=1))):
        bad = copy.deepcopy(held); mutate(bad)
        try:
            check_snapshot(bad, lifecycle=True)
        except AssertionError as exc:
            results.append({'control': name, 'rejected': True, 'diagnostic': str(exc)})
        else:
            raise AssertionError('accepted '+name)
    # Real reversible premature cleanup, not merely a changed receipt field.
    import tempfile
    import time
    with tempfile.TemporaryDirectory(prefix='pw-aftermath-control-') as directory:
        marker = Path(directory) / 'owned'
        marker.write_bytes(b'owned fixture')
        original_inode = marker.stat().st_ino
        renamed = marker.with_name('renamed')
        marker.rename(renamed)
        assert not marker.exists() and renamed.stat().st_ino == original_inode
        rename_bad = copy.deepcopy(valid)
        binding = {'id': 'renamed-binding', 'type': 'pathname_binding', 'identity': {'path': str(marker), 'ino': original_inode},
            'owner': 'fixture', 'ownership_basis': 'owned file', 'category': 'observer', 'optional_surface': True,
            'creation_evidence': {'pre_existing': True}, 'expected_end': 'pathname removal'}
        rename_bad['inventory'].append(binding)
        for snap in rename_bad['snapshots']:
            snap['objects'].append({'id': binding['id'], 'state': 'absence_confirmed',
                'evidence': {'identity': binding['identity'], 'source': 'pathname binding inspection', 'scope': 'inode disposed'},
                'native_error': None, 'ending_status': 'observed'})
        try:
            validate_receipt(rename_bad)
        except AssertionError:
            results.append({'control': 'rename cannot establish inode disposal', 'rejected': True})
        else:
            raise AssertionError('accepted pathname absence as inode disposal')
        renamed.rename(marker)
        cleanup_begin = time.monotonic_ns()
        marker.unlink()
        cleanup_end = time.monotonic_ns()
        snapshot_end = time.monotonic_ns()
        assert cleanup_begin <= cleanup_end <= snapshot_end
        assert not marker.exists()
        bad = copy.deepcopy(valid)
        bad['snapshots'][1].update(begin_ns=snapshot_end, end_ns=snapshot_end, cli_relative_ns=snapshot_end-bad['cli_return_ns'])
        bad['snapshots'][2].update(begin_ns=snapshot_end+10, end_ns=snapshot_end+11, cli_relative_ns=snapshot_end+11-bad['cli_return_ns'])
        bad['interventions'] = [{'begin_ns': cleanup_begin, 'end_ns': cleanup_end}]
        try:
            validate_receipt(bad)
        except AssertionError:
            results.append({'control': 'actual premature cleanup', 'rejected': True})
        else:
            raise AssertionError('accepted actual premature cleanup')
    return results


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def observe_case(pw, out, bridge, helper, observer, *, lifecycle, timeout, actor_host):
    import platform
    import subprocess
    import time
    from footprint_workloads import HeldWorkload
    from check_installs_nothing import inventory as installation_inventory
    out.mkdir(parents=True, exist_ok=True)
    installation = installation_inventory(pw)
    power = subprocess.run(['/usr/bin/pmset', '-g', 'batt'], capture_output=True, text=True, timeout=10)
    assert power.returncode == 0, power.stderr
    condition_start = observer.clock()
    workload = HeldWorkload(pw, out / 'workload', bridge, helper, observer,
                            lifecycle=lifecycle, actor_host=actor_host, ordinary_small=not lifecycle,
                            timeout_ms=8000 if timeout else 60000)
    r = {'schema_version': 1, 'case_id': 'run_effects/aftermath_footprint',
         'run_id': out.name, 'workload_id': 'actor_lifecycle' if lifecycle else 'ordinary_small',
         'clock': 'mach_continuous_time_ns', 'source_identity': {'checker_sha256': sha256(__file__)},
         'inspected_binaries': {'pw': {'path': str(pw), 'sha256': sha256(pw)},
                                'observer': observer.provenance},
         'conditions': {'os': platform.platform(), 'hardware': platform.machine(),
                        'power_source': {'stdout': power.stdout, 'stderr': power.stderr, 'returncode': power.returncode},
                        'clock_start': condition_start, 'sleep_crosscheck': 'continuous minus uptime delta; dispatcher run.json supplies independent case sleep accounting'},
         'observer': observer.provenance, 'configuration': {'completion_repetitions': 3,
             'form': 'actor' if lifecycle else 'ordinary', 'path': 'timeout' if timeout else 'completion',
             'exit_observation_budget_seconds': 30},
         'inventory': [], 'snapshots': [], 'end_events': [], 'interventions': [],
         'exit_registrations': [], 'invocation': {}, 'held_state': None,
         'cleanup': {'status': 'retained', 'recovery_record': str(out / 'recovery.json')}}
    prepared_files = {}
    for name in ('target', 'marker'):
        path = Path(getattr(workload, name))
        st = path.stat()
        prepared_files[name] = {'path': str(path), 'dev': st.st_dev, 'ino': st.st_ino, 'sha256': sha256(path)}
    prepared_outputs = {}
    for path in (workload.run.stdout_path, workload.run.stderr_path):
        st = path.stat()
        prepared_outputs[str(path)] = {'dev': st.st_dev, 'ino': st.st_ino, 'size': st.st_size}
    baseline_clock = observer.clock()
    exits = GenerationExitObserver(observer)
    primary_done = False
    def persist():
        write(out / 'aftermath.json', r)
    def snapshot(boundary, assisted=False):
        begin = observer.clock()['begin_ns']
        exits.read_exit_events()
        states = []
        for obj in r['inventory']:
            ev, error, reason = {}, None, None
            if obj['type'] == 'process':
                sample = observer.inspect(obj['identity']['pid'])
                if sample['status'] != 'ok':
                    exits.read_exit_events()
                if obj['identity']['pid'] in exits.events:
                    state, ev = 'absence_confirmed', {'identity': obj['identity'], 'source': 'EVFILT_PROC NOTE_EXIT',
                        'event': exits.events[obj['identity']['pid']], 'process_record_sample': sample,
                        'scope': 'execution ended; process-record disposal and reap unestablished'}
                elif sample['status'] == 'ok' and generation(sample) == obj['identity']:
                    state, ev = 'present', {'sample': sample}
                else:
                    state, ev, error, reason = 'unknown', {'sample': sample}, sample.get('calls'), 'no generation-qualified exit event'
            elif obj['category'] == 'baseline':
                current = installation_inventory(pw)
                assert current == installation, 'installation inventory changed'
                state, ev = 'present', {'inventory': current}
            elif obj['type'] == 'pathname_binding':
                path = Path(obj['identity']['path'])
                try:
                    st = path.stat()
                    assert (st.st_dev, st.st_ino) == (obj['identity']['dev'], obj['identity']['ino']), 'file identity changed'
                    state, ev = 'present', {'identity': obj['identity'], 'size': st.st_size, 'sha256': sha256(path),
                                           'scope': 'pathname binding matches prepared inode; backing disposal unestablished'}
                except FileNotFoundError:
                    state, ev = 'absence_confirmed', {'identity': obj['identity'], 'source': 'pathname binding inspection',
                        'scope': 'name binding only; inode lifetime unestablished'}
                except OSError as exc:
                    state, ev, error, reason = 'unknown', {'inspection': 'stat/read failed'}, {'errno': exc.errno, 'message': str(exc)}, 'pathname inspection failed'
            elif obj['type'] == 'observer_resource':
                state, ev = 'present', {'identity': obj['identity'], 'scope': 'test-owned resource retained through primary/resource-end; cleanup separately observed'}
            else:
                state, ev, reason = 'unknown', {'scope': 'source/component mapping; not live inspection'}, 'public process inspection does not establish mapping, erasure or native handle disposal'
            states.append({'id': obj['id'], 'state': state, 'evidence': ev, 'native_error': error,
                           'reason': reason, 'ending_status': 'observed' if state == 'absence_confirmed' else 'pending' if state == 'present' else 'unestablished'})
        end = observer.clock()['end_ns']
        r['snapshots'].append({'boundary': boundary, 'begin_ns': begin, 'end_ns': end,
                              'cli_relative_ns': end-r.get('cli_return_ns', end),
                              'assisted': assisted, 'objects': states})
        persist()
    def intervene(action, operation):
        entry = {'action': action, 'target_identity': {'generation': next(o['identity'] for o in r['inventory'] if o['id'] == 'validator')} if action == 'gate release' else {'object_id': 'owned-staging', 'identity': {'path': str(workload.work)}}, 'ownership': 'test-owned fixture',
                 'reason': 'release held collection' if action == 'gate release' else 'fixture cleanup',
                 'begin_ns': observer.clock()['begin_ns'], 'native_result': None, 'native_error': None,
                 'later_observation': {'boundary': 'resource_end'} if action == 'gate release' else {'artifact': str(out / 'workload/cleanup-end-observations.json'), 'ownership_artifact': str(out / 'workload/ownership.json')}}
        r['interventions'].append(entry)
        persist()
        try:
            operation()
            entry['native_result'] = 'returned'
            if action == 'fixture finish':
                actual = json.loads((out / 'workload/cleanup-end-observations.json').read_text())
                entry['later_observation'].update(begin_ns=entry['begin_ns'], end_ns=observer.clock()['end_ns'],
                    all_registered_ends=actual['all_registered_ends'], staging_binding_absent=not workload.work.exists(),
                    scope='owned staging name removed after confirmed process exits; no general inode erasure claim')
        except BaseException as exc:
            entry['native_error'] = repr(exc)
            raise
        finally:
            entry['end_ns'] = observer.clock()['end_ns']
            persist()
    try:
        launch_begin = observer.clock()
        workload.start()
        launch_end = observer.clock()
        r['launch_provenance'] = {'begin': launch_begin, 'end': launch_end, 'capture_metadata': str(workload.run.metadata_path),
            'scope': 'run-created generation absence before invocation is inferred from launch ownership, not prior PID inspection'}
        assert workload.run.poll() is None, 'CLI returned before exit watchers installed'
        for i, sample in enumerate(workload.workers):
            g = generation(sample)
            exits.watch(g['pid'], g)
            r['inventory'].append({'id': f'worker-{i}', 'type': 'process', 'identity': g,
                'owner': 'host', 'ownership_basis': 'held worker generation registered before release',
                'category': 'apparatus', 'creation_evidence': {'gate': True}, 'expected_end': 'exit', 'required_process': True})
        for oid, pid, owner, preexisting in (('validator', workload.gate.pid, 'host', False),
                                                  ('observer-process', observer.process.pid, 'test', True)):
            sample = observer.inspect(pid)
            assert sample['status'] == 'ok', sample
            g = generation(sample)
            if not preexisting:
                exits.watch(pid, g)
            r['inventory'].append({'id': oid, 'type': 'process', 'identity': g, 'owner': owner,
                'ownership_basis': 'native generation sample', 'category': 'observer' if preexisting else 'apparatus',
                'creation_evidence': {'pre_existing': preexisting}, 'expected_end': 'exit'})
        if workload.host:
            sample = workload.host
            g = generation(sample)
            exits.watch(g['pid'], g)
            r['inventory'].append({'id': 'host', 'type': 'process', 'identity': g, 'owner': 'launchd',
                'ownership_basis': 'worker parent generation', 'category': 'apparatus',
                'creation_evidence': {'parent_observation': True}, 'expected_end': 'exit'})
        r['inventory'].append({'id': 'installation', 'type': 'installation_inventory', 'identity': {'baseline': installation},
            'owner': 'user/system', 'ownership_basis': 'pre-run registry and plist inventory', 'category': 'baseline',
            'creation_evidence': {'pre_existing': True}, 'expected_end': 'retained'})
        for name in ('target', 'marker'):
            path = Path(getattr(workload, name))
            st = path.stat()
            r['inventory'].append({'id': name, 'type': 'pathname_binding', 'identity': {'path': str(path), 'dev': st.st_dev, 'ino': st.st_ino},
                'owner': 'specimen', 'ownership_basis': 'owned fixture', 'category': 'specimen_effect',
                'creation_evidence': {'prepared_before_invocation': prepared_files[name]}, 'expected_end': 'test fixture removal'})
        for name, path in (('requested-envelope', workload.run.stdout_path), ('requested-stderr', workload.run.stderr_path)):
            st = path.stat()
            r['inventory'].append({'id': name, 'type': 'pathname_binding', 'identity': {'path': str(path), 'dev': st.st_dev, 'ino': st.st_ino},
                'owner': 'caller', 'ownership_basis': 'RunCapture redirected output', 'category': 'requested_output',
                'creation_evidence': {'creation_boundary': 'RunCapture.__init__ touch before declared post-preparation baseline', 'prepared_before_invocation': prepared_outputs[str(path)]}, 'expected_end': 'caller disposal'})
        for i in range(len(workload.workers)):
            kinds = ['evidence_backing', 'launch_descriptor'] + (['authority_backing', 'handle_table'] if lifecycle else [])
            for kind in kinds:
                r['inventory'].append({'id': f'{kind}-{i}', 'type': 'logical_resource', 'identity': {'worker': f'worker-{i}', 'kind': kind},
                    'owner': f'worker-{i}/host', 'ownership_basis': 'source allocation path; live disposal uninspected',
                    'category': 'apparatus', 'creation_evidence': {'source_supported': True}, 'expected_end': 'close' if kind == 'launch_descriptor' else 'unmap/process exit',
                    'surface': 'handle_table' if kind == 'handle_table' else 'descriptor' if kind == 'launch_descriptor' else 'mapping', 'resource_kind': kind,
                    'actor_index': i, 'worker_identity': r['inventory'][i]['identity'],
                    'backing_id': f'{out.name}:{kind}:{i}', 'views': {'host': 'host', 'worker': f'worker-{i}'}})
        if lifecycle:
            for kind in ('private_custody', 'native_handle-H1', 'native_handle-H2', 'native_handle-H3'):
                r['inventory'].append({'id': kind, 'type': 'logical_resource', 'identity': {'lifecycle': kind},
                    'owner': 'host' if kind == 'private_custody' else 'subject', 'ownership_basis': 'metadata-only held snapshot',
                    'category': 'apparatus' if kind == 'private_custody' else 'specimen_effect',
                    'creation_evidence': {'snapshot': True}, 'expected_end': 'unmap' if kind == 'private_custody' else 'native_release/process exit',
                    'resource_kind': 'private_custody' if kind == 'private_custody' else 'native_handle',
                    'references': {'token': 'T', 'actor_index': 0} if kind == 'private_custody' else {'handle': kind.rsplit('-', 1)[1], 'delivery': 'D2' if kind.endswith('H3') else 'D1', 'token': 'T', 'actor_index': 1},
                    'surface': 'custody' if kind == 'private_custody' else 'native_handle'})
            for obj in r['inventory']:
                if obj.get('resource_kind') == 'handle_table':
                    obj['logical_capacity'] = {'entries': 64, 'handle_value_bytes': 512, 'validity_bytes': 64,
                        'derivation': 'PW_AUTHORITY_MAX_HANDLES; int64_t handle_table and uint8_t handle_valid; not measured kernel storage'}
                if obj.get('resource_kind') == 'authority_backing':
                    index = int(obj['id'].rsplit('-', 1)[1])
                    obj['logical_capacity'] = workload.snapshot['regions'][index]
                if obj.get('resource_kind') == 'private_custody':
                    obj['logical_capacity'] = {'bytes': 16384, 'derivation': 'TokenCustody fixed capacity; live token length separate'}
            assert workload.snapshot, 'missing held actor metadata'
            r['held_state'] = {'snapshot': workload.snapshot, 'generations': workload.held_generations}
        for name, identity, ending in (('gate-socket', {'path': workload.gate.path}, 'socket close'),
             ('tree-socket', {'path': workload.tree.path}, 'socket close'),
             ('owned-staging', {'path': str(workload.work)}, 'owned directory removal'),
             ('exit-watchers', {'owner_pid': __import__('os').getpid(), 'owners': ['gate.observer', 'tree.observer', 'HeldWorkload.exits', 'aftermath.exits']}, 'kqueue close'),
             ('instrumentation-output', {'path': str(actor_host.snapshots) if lifecycle else str(out / 'workload/held-snapshot.json')}, 'retained evidence disposal')):
            r['inventory'].append({'id': name, 'type': 'observer_resource', 'identity': identity, 'owner': 'test harness',
                'ownership_basis': 'exclusive fixture preparation', 'category': 'observer',
                'creation_evidence': {'pre_existing': name != 'instrumentation-output' or lifecycle}, 'expected_end': ending})
        r['expected_inventory_ids'] = sorted(expected_inventory_ids(r))
        r['configuration']['repetition_conditions'] = 'serial runs; each prior run reaches registered exits and fixture cleanup before next invocation; no overlap/accumulation measurement'
        r['request_sha256'] = sha256(workload.run.request_path)
        r['inspected_binaries']['actual_cli'] = {'path': str(workload.run.argv[0]), 'sha256': sha256(workload.run.argv[0])}
        for label, sample in [('host', workload.host)] + [(f'worker-{i}', sample) for i, sample in enumerate(workload.workers)]:
            if sample:
                r['inspected_binaries'][label] = {'path': sample['path'], 'sha256': sha256(sample['path'])}
        r['source_identity']['dependencies'] = {str(path): sha256(path) for path in (
            Path(__file__), Path(__file__).parents[2] / 'lib/footprint_workloads.py',
            Path(__file__).parents[2] / 'lib/run_capture.py', Path(__file__).parents[2] / 'lib/footprint_observer.py',
            Path(__file__).parent / 'check_installs_nothing.py')}
        r['artifact_hashes'] = {'request': r['request_sha256']}
        r['assertion_outcomes'] = {'required_worker_generations_registered': True, 'primary_before_cleanup': None}
        r['exit_registrations'] = exits.registrations
        r['invocation'] = {'established_before_timeout': True, 'gate': workload.gate.events, 'ready': workload.ready,
                           'effects': workload.effects()}
        # Baseline process nonexistence is registration provenance, not inspection
        # of an unknown PID. Prepared fixture files and installation preexist.
        baseline = []
        for obj in r['inventory']:
            if obj['type'] == 'process' and obj['creation_evidence'].get('pre_existing'):
                state, evidence = 'present', {'identity': obj['identity'], 'source': 'observer launched before baseline'}
            elif obj['type'] == 'process' or (obj['type'] == 'observer_resource' and not obj['creation_evidence']['pre_existing']):
                state, evidence = 'absence_confirmed', {'identity': obj['identity'], 'source': 'not_created_yet',
                    'launch_provenance': r['launch_provenance'], 'scope': 'launch-owned generation/name not yet created; not backing-object disposal'}
            elif obj['type'] == 'logical_resource':
                state, evidence = 'unknown', {'source': 'not inspected before invocation'}
            else:
                state, evidence = 'present', {'identity': obj['identity'], 'pre_run_inventory': installation if obj['category'] == 'baseline' else 'prepared fixture'}
            baseline.append({'id': obj['id'], 'state': state, 'evidence': evidence, 'native_error': None,
                             'reason': 'logical capacity source account only' if state == 'unknown' else None,
                             'ending_status': 'unestablished'})
        r['snapshots'].append({'boundary': 'baseline', 'begin_ns': baseline_clock['begin_ns'], 'end_ns': baseline_clock['end_ns'],
                               'cli_relative_ns': 0, 'assisted': False, 'objects': baseline})
        if not timeout:
            # This release precedes CLI return and is not a post-return intervention.
            workload.release()
        rc = workload.run.wait(timeout=40)
        r['cli_return_ns'] = observer.clock()['continuous_ns']
        r['cli_return_code'] = rc
        for snap in r['snapshots']:
            snap['cli_relative_ns'] = snap['end_ns'] - r['cli_return_ns']
        snapshot('cli_return')
        primary_done = True
        r['assertion_outcomes']['primary_before_cleanup'] = True
        value = workload.run.load_json()
        client = value.get('data', {}).get('runner_client') or {}
        transport = client.get('transport') or {}
        r['sizes'] = {'host_reply_bytes': (transport.get('runner_reply') or {}).get('bytes_received'),
                      'client_stdout_bytes': client.get('stdout_bytes_received'),
                      'unavailable_reason': 'timeout may prevent terminal reply metadata' if timeout else None}
        r['artifact_hashes']['envelope'] = sha256(workload.run.stdout_path)
        if timeout:
            assert rc != 0
            envelope = workload.run.load_json()
            assert transport['terminal'] == 'xpc_timeout', transport
            assert transport['submission']['state'] == 'invoked', transport
            assert client['submission'] == 'invoked', client
            assert envelope['data']['runner_result'] is None, envelope
            r['invocation']['terminal_capture'] = {'terminal': transport['terminal'], 'submission': transport['submission']}
            r['timeout_envelope'] = envelope
            intervene('gate release', workload.release)
        else:
            assert rc == 0
            workload.complete()
        deadline = time.monotonic()+30
        required_pids = set(exits.registered)
        while not required_pids <= set(exits.events) and time.monotonic() < deadline:
            exits.read_exit_events(timeout=0.2)
        assert required_pids <= set(exits.events), 'registered worker/host/validator exits not independently observed'
        for obj in r['inventory']:
            if obj['type'] == 'process' and obj['identity']['pid'] in exits.events:
                r['end_events'].append({'object_id': obj['id'], 'identity': obj['identity'],
                    **exits.events[obj['identity']['pid']]})
        snapshot('resource_end', assisted=timeout)
        r['host_resource_end'] = {'identity': next(o['identity'] for o in r['inventory'] if o['id'] == 'host'),
            'event': exits.events[next(o['identity']['pid'] for o in r['inventory'] if o['id'] == 'host')],
            'scope': 'independent host exit; does not directly observe mapping disposal or parent reap'}
        r['conditions']['clock_end'] = observer.clock()
        clock_end = r['conditions']['clock_end']
        r['conditions']['sleep_delta_ns'] = ((clock_end['continuous_ns']-condition_start['continuous_ns'])
            - (clock_end['uptime_ns']-condition_start['uptime_ns']))
        write(out / 'recovery.json', {'status': 'cleanup pending', 'inventory': r['inventory'],
                                     'primary_snapshot_complete': True, 'staging': str(out / 'workload')})
        intervene('fixture finish', workload.finish)
        assert workload.cleanup_confirmed, 'shared fixture did not independently confirm process ends and staging removal'
        ownership_record = out / 'workload' / 'ownership.json'
        ownership = json.loads(ownership_record.read_text())
        assert ownership['cleanup_retained'] is False and not Path(ownership['staging']).exists(), ownership
        r['cleanup'] = {'status': 'complete', 'recovery_record': None, 'ownership_record': str(ownership_record),
                        'scope': 'confirmed owned staging removal after generation-qualified host/worker/validator exits',
                        'fixture_interventions': workload.interventions}
        write(out / 'recovery.json', {'status': 'complete', 'ownership_record': str(ownership_record)})
        validate_receipt(r)
        persist()
        return r
    except BaseException as exc:
        r['primary_error'] = repr(exc)
        write(out / 'recovery.json', {'status': 'retained', 'inventory': r['inventory'],
                                     'primary_snapshot_complete': primary_done, 'staging': str(out / 'workload'),
                                     'reason': repr(exc)})
        persist()
        # No unledgered release/finalizer is allowed to replace the primary state.
        raise
    finally:
        exits.close()


def main():
    from footprint_workloads import ActorHostFixture
    pw, output, bridge, helper, binary, identity = sys.argv[1:]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    out = Path(output).resolve()
    with FootprintObserver(binary, out / 'observer') as observer:
        fixture = ActorHostFixture(Path(pw).resolve().parents[2], out / 'actor-host', identity)
        fixture.build()
        receipts = []
        for lifecycle in (False, True):
            for repetition in range(3):
                receipts.append(observe_case(pw, out / f'{"actor" if lifecycle else "ordinary"}-completion-{repetition}',
                    bridge, helper, observer, lifecycle=lifecycle, timeout=False, actor_host=fixture if lifecycle else None))
            receipts.append(observe_case(pw, out / f'{"actor" if lifecycle else "ordinary"}-timeout',
                bridge, helper, observer, lifecycle=lifecycle, timeout=True, actor_host=fixture if lifecycle else None))
        write(out / 'repetitions.json', {'declared_completion_N': 3, 'runs': [
            {'run_id': r['run_id'], 'objects': len(r['inventory']), 'boundaries': len(r['snapshots'])} for r in receipts]})


if __name__ == '__main__':
    main()
