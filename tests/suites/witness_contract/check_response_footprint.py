"""Response accounting and external controller samples; no decoder-stage inference."""
import base64
import copy
import errno
import hashlib
import json
import os
import platform
import resource
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from footprint_observer import FootprintObserver, GenerationExitObserver, generation, require_sample, sha256
from run_capture import RunCapture
import check_max_target_reply as maximum

STAGES = ['full_client_collection', 'capture_parsing', 'typed_capture_validation_base64_decoding',
          'host_parsing', 'envelope_construction_sorting', 'final_rendering']


def strict_decode(text):
    data = base64.b64decode(text, validate=True)
    assert base64.b64encode(data).decode('ascii') == text, 'noncanonical base64'
    return data


def check_internal(receipt):
    assert receipt['schema_version'] == 1
    assert receipt['case_id'] == 'response_footprint_success_boundaries'
    assert len(receipt['input_sha256']) == 64 and all(c in '0123456789abcdef' for c in receipt['input_sha256'])
    rows = receipt['boundaries']
    assert [r['stage'] for r in rows] == STAGES
    for index, row in enumerate(rows):
        for field in ['raw_stdout', 'raw_stderr', 'retained_stdout', 'retained_stderr', 'decoded', 'rendered']:
            pair = row[field]
            if pair is not None:
                assert len(pair) == 2 and all(type(x) is int and x >= 0 for x in pair)
                assert pair[1] >= pair[0], field
        if index < 4:
            assert row['raw_stdout'][0] == receipt['client_stdout_bytes']
            assert row['raw_stderr'][0] == receipt['client_stderr_bytes']
        else:
            assert row['raw_stdout'] is None and row['raw_stderr'] is None
            assert row['typed_base64'] is None and row['decoded'] is None and row['host_retained'] is None
            assert row['borrowed_input'] and row['envelope']
        if 1 <= index <= 3:
            assert row['generic_base64'] == 4 * ((receipt['host_bytes'] + 2) // 3)
        if 2 <= index <= 3:
            assert row['typed_base64'] == row['generic_base64']
            assert row['host_retained'] == receipt['host_bytes'] == row['decoded'][0]
    assert rows[1]['retained_stdout'][0] == receipt['client_stdout_bytes']
    assert rows[1]['retained_stderr'][0] == receipt['client_stderr_bytes']
    assert rows[3]['parsed_host'] is True
    assert rows[5]['rendered'][0] == receipt['rendered_bytes']


def check_sizes(sizes, reply, client, host_artifact, envelope_artifact):
    decoded = strict_decode(reply['data_base64'])
    assert decoded == host_artifact
    assert sizes['computed_transport_artifact_sha256'] == hashlib.sha256(host_artifact).hexdigest()
    assert sizes['hash_scope'] == 'computed transport artifact; no producer hash supplied'
    assert reply['truncated'] is False
    assert sizes['host_received_bytes'] == reply['bytes_received'] == reply['bytes_retained'] == sizes['host_retained_bytes'] == len(decoded)
    assert sizes['host_received_bytes'] <= sizes['synthesized_host_bound_bytes']
    assert sizes['base64_characters'] == len(reply['data_base64'])
    assert client['stdout_truncated'] is False and client['stderr_truncated'] is False
    assert client['stdout_parse_error'] is None and client['stdout_capture_error'] is None
    for stream in ['stdout', 'stderr']:
        assert sizes[f'client_{stream}_received_bytes'] == client[f'{stream}_bytes_received'] == client[f'{stream}_bytes_retained'] == sizes[f'client_{stream}_retained_bytes']
        assert sizes[f'client_{stream}_received_bytes'] <= sizes['client_allowance_bytes'] == client['capture_limit_bytes']
    assert sizes['host_received_bytes'] < sizes['client_stdout_received_bytes']
    assert sizes['final_envelope_bytes'] == len(envelope_artifact)
    assert sizes['authority_bytes_in_reply_payload'] is False


def check_terminal_resolution(resolution, expected):
    """An ESRCH inspection ends sampling only with the registered exit and wait."""
    sample = resolution['failed_sample']
    assert sample['pid'] == expected['pid'] and sample['status'] == 'error'
    assert sample['generation_before'] is None and sample['generation_after'] is None and sample['path'] is None
    assert all(sample[key] is None for key in ['user_ns','system_ns','resident_bytes','phys_footprint_bytes'])
    assert type(sample['begin_ns']) is int and 0 <= sample['begin_ns'] <= sample['end_ns']
    for name in ['generation_before','generation_after','path']:
        call = sample['calls'][name]
        assert call['rc'] == 0 and call['errno'] == errno.ESRCH
    events = resolution['exit_events']
    assert len(events)==1
    event = events[0]
    assert event['generation']==expected and event['source']=='EVFILT_PROC NOTE_EXIT' and event['event']=='exit'
    assert sample['end_ns'] <= event['collection_begin_ns'] <= event['collection_end_ns']
    assert event['actual_exit_time_ns'] is None
    assert resolution['wait_observed'] is True and type(resolution['returncode']) is int
    assert resolution['classification']=='terminal generation exit; failed metrics excluded'


def check_observation(controller, samples):
    assert len(samples) >= 2
    assert controller['memory_unit'] == 'bytes'
    assert controller['stage_attribution'] == 'unknown'
    before, after = controller['launch_bracket_ns'], controller['exit_bracket_ns']
    assert len(before) == len(after) == 2
    assert all(type(t) is int for t in before+after)
    assert before[0] <= before[1] <= after[0] <= after[1]
    registration = controller['exit_registration']
    assert registration['generation'] == controller['generation']
    assert registration['source'] == 'EVFILT_PROC NOTE_EXIT registration'
    assert before[1] <= registration['begin_ns'] <= registration['end_ns'] <= samples[0]['begin_ns']
    require_sample(registration['before'], controller['generation'])
    require_sample(registration['after'], controller['generation'])
    assert registration['before']['end_ns'] <= registration['begin_ns']
    assert registration['end_ns'] <= registration['after']['begin_ns'] <= registration['after']['end_ns'] <= samples[0]['begin_ns']
    previous = registration['after']['end_ns']
    for sample in samples:
        require_sample(sample, controller['generation'])
        assert controller['pid'] == sample['pid']
        assert previous <= sample['begin_ns'] <= sample['end_ns'] <= after[0]
        previous = sample['end_ns']
    assert samples[-1]['end_ns'] == after[0], 'last verified-live sample defines coverage end'
    assert controller['verified_live_interval_ns'] == [samples[0]['begin_ns'], samples[-1]['end_ns']]
    inspection = controller['exit_inspection']
    assert inspection['status'] != 'ok' or generation(inspection) != controller['generation']
    if inspection['status'] != 'ok':
        assert all(inspection[k] is None for k in ['user_ns','system_ns','resident_bytes','phys_footprint_bytes'])
    assert len(controller['exit_events']) == 1
    event = controller['exit_events'][0]
    assert event['generation'] == controller['generation']
    assert event['event'] == 'exit' and event['source'] == 'EVFILT_PROC NOTE_EXIT'
    assert after[0] <= event['collection_begin_ns'] <= event['collection_end_ns'] <= after[1]
    assert event['actual_exit_time_ns'] is None
    terminal = controller.get('terminal_resolution')
    if terminal is not None:
        check_terminal_resolution(terminal, controller['generation'])
        assert after[0] <= terminal['failed_sample']['begin_ns']
        assert terminal['exit_events'] == controller['exit_events']


def setup_bytes(scope, operation):
    rows = [r for r in scope['operations'] if r['operation'] == operation]
    assert len(rows) == 1 and rows[0]['state'] == 'succeeded'
    assert type(rows[0]['value']) is int and rows[0]['value'] > 0
    return rows[0]['value']


def actor_geometry(request, runner, evidence_bytes):
    """Logical capacities and shared views, derived from plan references and setup."""
    actors = [a['actor_id'] for a in request['actors']]
    assert len(set(actors)) == len(actors)
    operations = [(phase['actor_id'], action['extension']) for phase in request['phases']
                  for action in phase['actions'] if 'extension' in action]
    issues = [(owner,op['token_ref']) for owner,op in operations if op['operation']=='issue']
    deliveries = [(owner,op['recipient'],op['delivery_ref'],op['token_ref']) for owner,op in operations if op['operation']=='transfer']
    consumes = [(owner,op['handle_ref'],op['delivery_ref']) for owner,op in operations if op['operation']=='consume']
    token_owner = {ref:owner for owner,ref in issues}
    assert len(token_owner)==len(issues)
    assert all(token_owner[token]==owner and recipient in actors for owner,recipient,ref,token in deliveries)
    setup = runner['authority_setup']
    regions = {row['actor_id']:row for row in setup['host']['regions']}
    workers = {row['actor_id']:row for row in setup['workers']}
    custody = {row['token_ref']:row for row in setup['host']['custody']}
    assert len(regions)==len(setup['host']['regions']) and set(regions)==set(actors)
    assert len(workers)==len(setup['workers']) and set(workers)==set(actors)
    assert len(custody)==len(setup['host']['custody']) and set(custody)==set(token_owner)
    for index,(_,ref) in enumerate(issues): assert custody[ref]['token_index']==index
    rows=[]
    for index,owner in enumerate(actors):
        assert regions[owner]['actor_index']==workers[owner]['actor_index']==index
        outbound=[ref for who,ref in issues if who==owner]
        inbound=[ref for source,recipient,ref,token in deliveries if recipient==owner]
        handles=[ref for who,ref,delivery in consumes if who==owner]
        authority=1152+(len(outbound)+len(inbound))*16448
        assert setup_bytes(regions[owner],'mmap') == setup_bytes(regions[owner],'ftruncate') == authority
        worker = workers[owner]
        observed_object = setup_bytes(worker,'fstat')
        accepted_size = [op for op in worker['operations'] if op['operation']=='object_size']
        assert len(accepted_size)==1 and accepted_size[0]['state']=='accepted' and accepted_size[0]['value']==observed_object
        page_records = [op for op in worker['operations'] if op['operation']=='page_size']
        assert len(page_records)==1 and page_records[0]['state']=='succeeded'
        page = page_records[0]['native_rc']
        assert type(page) is int and page > 0
        source_maximum = 1152+(32+64)*16448
        maximum_rounded = ((source_maximum+page-1)//page)*page
        logical_rounded = ((authority+page-1)//page)*page
        assert authority <= observed_object <= maximum_rounded
        assert setup_bytes(worker,'mmap') == observed_object
        custody_bytes=0
        for ref in outbound:
            custody_bytes += setup_bytes(custody[ref],'mmap')
            assert setup_bytes(custody[ref],'mmap')==16384
        rows.append(dict(actor_id=owner,actor_index=index,issued_token_refs=outbound,inbound_delivery_refs=inbound,
            candidate_handle_refs=handles,planned=dict(outbound=len(outbound),inbound=len(inbound),handles=len(handles)),
            observed=dict(outbound=sum(r['actor_id']==owner for r in runner['resources']['tokens']),
                          inbound=sum(r['recipient_actor_id']==owner for r in runner['resources']['deliveries']),
                          handles=sum(r['actor_id']==owner for r in runner['resources']['handles'])),
            evidence=dict(backing_id='evidence:'+owner,backing_bytes=evidence_bytes,views=['host','worker:'+owner]),
            authority=dict(backing_id='authority:'+owner,backing_bytes=authority,
                backing_bytes_scope='requested logical capacity; counted once, not physical backing measurement',
                logical_requested_bytes=authority,host_mapping_requested_bytes=authority,
                observed_object_bytes=observed_object,worker_mapping_requested_bytes=observed_object,
                observed_padding_bytes=observed_object-authority,page_size=page,
                logical_page_rounded_bytes=logical_rounded,observed_matches_logical_page_rounding=observed_object==logical_rounded,
                source_accepted_maximum_bytes=maximum_rounded,views=['host','worker:'+owner]),
            private_custody=dict(owner='host',token_refs=outbound,logical_bytes=custody_bytes),
            handle_table=dict(owner=owner,logical_value_bytes=64*8,scope='fixed C values; not kernel memory')))
    for row in rows: assert row['planned']==row['observed']
    return dict(per_actor=rows,planned=dict(actors=len(actors),phases=len(request['phases']),
        actions=sum(len(p['actions']) for p in request['phases']),tokens=len(issues),deliveries=len(deliveries),handles=len(consumes)),
        observed=dict(actors=len(runner['actors']),phases=len(runner['phases']),
            actions=len(runner['steps'])+len(runner['extension_events']),tokens=len(runner['resources']['tokens']),
            deliveries=len(runner['resources']['deliveries']),handles=len(runner['resources']['handles'])),
        shared_backing_objects=2*len(actors),shared_backing_bytes=sum(r[k]['backing_bytes'] for r in rows for k in ['evidence','authority']),
        mapped_views=4*len(actors),private_custody_bytes=sum(r['private_custody']['logical_bytes'] for r in rows),
        capacity_is_reply_payload=False,evidence_region_bytes_per_backing=evidence_bytes,
        shared_backing_bytes_scope='logical capacity counted once per backing; padded worker views excluded from sum',
        scope='source-derived logical capacity and observed mapping requests; not residency or kernel memory')


def check_geometry(account, request, runner, evidence_bytes):
    assert account == actor_geometry(request,runner,evidence_bytes)
    assert account['planned']==account['observed']


def profiles(runner):
    result = []
    for owner, profile in [('ordinary', runner.get('compiled_profile'))] + [(a['actor_id'], a.get('compiled_profile')) for a in runner.get('actors', [])]:
        if profile and profile.get('status') == 'captured':
            # Existing consumer validates receipt structure and hashes. Count its actual decoded bytes separately.
            encoded = profile['bytecode_b64']
            decoded = strict_decode(encoded)
            assert len(decoded) == profile['bytecode_length']
            assert hashlib.sha256(decoded).hexdigest() == profile['bytecode_sha256']
            result.append(dict(owner=owner, bytecode_length=profile['bytecode_length'],
                               base64_characters=len(encoded), decoded_bytes=len(decoded)))
    return result



def check_workload(runner, request, expectations):
    maximum.check_reply(runner, request, **expectations)
    if request.get('actors'):
        setup = runner['authority_setup']
        assert len(setup['workers']) == len(request['actors'])
        assert len(setup['host']['regions']) == len(request['actors'])
        assert len(setup['host']['custody']) == 32


def check_workload_rejections(runner, request, expectations):
    """Accept the real reply before removing evidence in reversible checker controls."""
    check_workload(runner, request, expectations)
    checks = [(runner, 'steps')]
    if request.get('actors'):
        checks += [(runner, field) for field in ['actors','phases','extension_events','transfers','resources','authority_setup']]
        checks += [(runner['actors'][0], 'equipment'), (runner['actors'][1], 'compiled_profile')]
    if any(step['attempt']['kind']=='exec' for step in maximum.request_steps(request)):
        checks.append((runner['steps'][0]['attempt'], 'stdout'))
    rejected = []
    for owner, field in checks:
        original = owner.pop(field)
        try:
            try:
                check_workload(runner, request, expectations)
            except (AssertionError, KeyError, TypeError, ValueError):
                rejected.append(field)
            else:
                raise AssertionError(('missing workload evidence accepted',field))
        finally:
            owner[field] = original
    return rejected


def collect(pw, observer, out, name, request, internal, **expectations):
    directory = out / name
    baseline_hash = sha256(pw)
    expected_path = str(Path(pw).resolve())
    python_before = require_sample(observer.inspect(os.getpid()))
    python_cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    run = RunCapture(pw, directory, request, cli_args=['--timeout-ms', '120000'])
    start_clock = observer.clock()
    launch_begin = start_clock['continuous_ns']
    run.start()
    launch_end = observer.clock()['continuous_ns']
    pid = run.pid
    exits = GenerationExitObserver(observer)
    try:
        registration = exits.watch(pid)
    except BaseException:
        exits.close()
        run.close()
        raise
    samples = []
    terminal_resolution = None
    cadence_ns = 1_000_000
    deadline = time.monotonic() + 150
    last_alive = launch_end
    try:
        while run.poll() is None:
            assert time.monotonic() < deadline, 'response observation harness deadline'
            batch = observer.sample([pid])
            sample = batch['samples'][0]
            if sample['status'] == 'ok':
                require_sample(sample, generation(samples[0]) if samples else None)
                assert sample['path'] == expected_path, 'sampled executable path mismatch'
                samples.append(sample)
                last_alive = sample['end_ns']
            else:
                # Keep the failed sample before attempting bounded independent resolution.
                terminal_resolution = dict(failed_sample=sample,exit_events=[],wait_observed=False,returncode=None,
                    classification='unresolved inspection failure')
                terminal_path=directory/'terminal-inspection.json'
                terminal_path.write_text(json.dumps(terminal_resolution,indent=2)+'\n')
                # Live permission/error failures cannot become terminal merely because exit follows later.
                assert sample['status']=='error' and sample['generation_before'] is None and sample['generation_after'] is None
                assert all(sample['calls'][key]['rc']==0 and sample['calls'][key]['errno']==errno.ESRCH
                           for key in ['generation_before','generation_after','path']), sample
                terminal_resolution['exit_events']=exits.read_exit_events(timeout=1)
                terminal_path.write_text(json.dumps(terminal_resolution,indent=2)+'\n')
                assert terminal_resolution['exit_events'], ('terminal absence lacks independent generation exit',sample)
                terminal_resolution['returncode']=run.wait(timeout=5)
                terminal_resolution['wait_observed']=True
                terminal_resolution['classification']='terminal generation exit; failed metrics excluded'
                terminal_path.write_text(json.dumps(terminal_resolution,indent=2)+'\n')
                check_terminal_resolution(terminal_resolution,registration['generation'])
                break
            time.sleep(cadence_ns / 1e9)
        exit_events = exits.read_exit_events(timeout=1)
        assert len(exit_events) == 1 and exit_events[0]['generation'] == generation(samples[0])
        assert sha256(pw) == baseline_hash, 'controller bytes changed during observation'
        python_cpu_after = resource.getrusage(resource.RUSAGE_SELF)
        python_after = require_sample(observer.inspect(os.getpid()), generation(python_before))
        end_clock = observer.clock()
        exit_end = end_clock['continuous_ns']
        sleep_difference = (end_clock['continuous_ns']-start_clock['continuous_ns'])-(end_clock['uptime_ns']-start_clock['uptime_ns'])
        uncertainty = sum(c['end_ns']-c['begin_ns'] for c in [start_clock,end_clock])
        assert sleep_difference <= uncertainty+1_000_000, 'system sleep overlapped response observation'
        assert run.wait(timeout=5) == 0
        envelope = run.load_json()
        client = envelope['data']['runner_client']
        runner = envelope['data']['runner_result']
        rejected_evidence = check_workload_rejections(runner, request, expectations)
        if request.get('policy',{}).get('capture_compiled_profile'):
            assert runner['compiled_profile']['status']=='captured'
        reply = client['transport']['runner_reply']
        decoded = strict_decode(reply['data_base64'])
        artifact = directory / 'host-reply.json'
        artifact.write_bytes(decoded)
        assert json.loads(decoded) == runner, 'transported host bytes must be exact admitted reply'
        sizes = dict(host_received_bytes=reply['bytes_received'], host_retained_bytes=reply['bytes_retained'],
                     base64_characters=len(reply['data_base64']),
                     computed_transport_artifact_sha256=hashlib.sha256(decoded).hexdigest(),
                     hash_scope='computed transport artifact; no producer hash supplied',
                     synthesized_host_bound_bytes=maximum.documented_limit('runner_reply_maximum'),
                     client_allowance_bytes=client['capture_limit_bytes'],
                     final_envelope_bytes=run.stdout_path.stat().st_size,
                     authority_bytes_in_reply_payload=False, compiled_profiles=profiles(runner))
        for stream in ['stdout', 'stderr']:
            for count in ['received', 'retained']:
                sizes[f'client_{stream}_{count}_bytes'] = client[f'{stream}_bytes_{count}']
        assert sizes['client_allowance_bytes'] == maximum.documented_limit('controller_output')
        check_sizes(sizes, reply, client, artifact.read_bytes(), run.stdout_path.read_bytes())
        controller = dict(pid=pid, generation=generation(samples[0]) if samples else None,
                          executable_sha256=baseline_hash, launch_bracket_ns=[launch_begin, launch_end],
                          exit_bracket_ns=[last_alive, exit_end],
                          verified_live_interval_ns=[samples[0]['begin_ns'],last_alive], exit_inspection=observer.inspect(pid),
                          memory_unit='bytes', stage_attribution='unknown', terminal_resolution=terminal_resolution, exit_events=exit_events, exit_registration=registration)
        check_observation(controller, samples)
        receipt = dict(schema_version=1, case_id='witness_contract/response_footprint', workload=name,
                       run_id=sha256(run.request_path)[:16]+'-'+str(pid), workload_id=name, repetition=0, repetition_count=1,
                       request_sha256=sha256(run.request_path),
                       app_evidence={name:sha256(Path(pw).parents[1]/'Resources/Evidence'/name) for name in ['manifest.json','provenance.json']},
                       source_identity={str(path.relative_to(Path(__file__).resolve().parents[3])):sha256(path) for path in [Path(__file__),Path(maximum.__file__),Path(__file__).resolve().parents[2]/'lib/run_capture.py',Path(__file__).resolve().parents[2]/'lib/footprint_observer.py']},
                       sizes=sizes, controller=controller, samples=samples, rejected_evidence_controls=rejected_evidence,
                       internal_assertions=internal,
                       conditions=dict(os=platform.platform(),hardware=platform.machine(),
                                       python_driver=dict(cpu_source='getrusage RUSAGE_SELF seconds converted to ns',generation=generation(python_before),executable=sys.executable,executable_sha256=sha256(sys.executable),
                                           before=python_before,after=python_after,
                                           user_cpu_ns=int((python_cpu_after.ru_utime-python_cpu_before.ru_utime)*1e9),
                                           system_cpu_ns=int((python_cpu_after.ru_stime-python_cpu_before.ru_stime)*1e9),
                                           scope='Python launch/watch/sample interval including raw-receipt writes and final binary verification; native child reported separately'),
                                       requested_cadence_ns=cadence_ns, observer=observer.provenance,
                                       power_observation=subprocess.run(['/usr/bin/pmset','-g','batt'],capture_output=True,text=True,check=True).stdout,
                                       clock_start=start_clock,clock_end=end_clock,sleep_difference_ns=sleep_difference,
                                       native_observer_sample_scope='native observer child only; Python driver separately identified',
                                       observer_sample=require_sample(observer.inspect(observer.process.pid)),
                                       actual_start_intervals_ns=[b['begin_ns']-a['begin_ns'] for a,b in zip(samples,samples[1:])]),
                       summary=dict(coverage_interval_ns=controller['verified_live_interval_ns'],metrics={metric: dict(sampled_min=min(s[metric] for s in samples), sampled_max=max(s[metric] for s in samples)) for metric in ['resident_bytes','phys_footprint_bytes']}))
        if request.get('actors'):
            golden=Path(__file__).resolve().parents[3]/'tests/fixtures/contract/abi_layout.txt'
            evidence_bytes=int(dict(line.split('=',1) for line in golden.read_text().splitlines() if '=' in line)['PW_SHM_REGION_BYTES'])
            receipt['actor_workload']=actor_geometry(request,runner,evidence_bytes)
            check_geometry(receipt['actor_workload'],request,runner,evidence_bytes)
            receipt['actor_workload_source']=dict(abi_layout_golden_sha256=sha256(golden),
                authority_source_sha256=sha256(Path(__file__).resolve().parents[3]/'runner/Sources/PWRunnerCore/AuthorityCustody.swift'),
                worker_authority_source_sha256=sha256(Path(__file__).resolve().parents[3]/'controller/tools/pw_probe_runner/pw_probe_runner.c'))
        assert receipt['run_id'] and receipt['workload_id'] and receipt['request_sha256']==sha256(run.request_path)
        assert receipt['repetition_count']==1 and receipt['repetition']==0
        assert receipt['conditions']['os'] and receipt['conditions']['hardware'] and receipt['source_identity']
        (directory / 'response-footprint.json').write_text(json.dumps(receipt, indent=2)+'\n')
        return receipt
    finally:
        exits.close()
        run.close()


def main():
    pw, out, binary, unit_receipt = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    internal = json.loads(unit_receipt.read_text()); check_internal(internal)
    input_artifact = unit_receipt.with_suffix('.input.json')
    assert sha256(input_artifact) == internal['input_sha256']
    assert len(input_artifact.read_bytes()) == internal['host_bytes']
    repo = Path(__file__).resolve().parents[3]
    for name, digest in internal['sources_sha256'].items(): assert sha256(repo/name) == digest
    (out/'internal-input.json').write_bytes(input_artifact.read_bytes())
    (out/'internal-assertions.json').write_text(json.dumps(internal,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='pw-response-', dir='/private/tmp') as temporary, FootprintObserver(binary, out/'observer') as observer:
        root = Path(temporary)
        plain = maximum.targets_under(root/'plain'); escaped = maximum.targets_under(root/'escaped', escaped=True)
        ordinary = maximum.specimen(plain, escaped)
        phased = copy.deepcopy(ordinary); actions=phased.pop('probe_plan')
        phased['phases']=[dict(phase_id=f'p{i}',actions=actions[i*32:(i+1)*32]) for i in range(8)]
        small = copy.deepcopy(ordinary); small['probe_plan']=small['probe_plan'][:1]
        small['probe_plan'][0]['attempt']['action']='read_fresh'
        receipts = [collect(pw, observer, out, 'ordinary_small', small, internal)]
        receipts.append(collect(pw, observer, out, 'independent_query', ordinary, internal))
        receipts.append(collect(pw, observer, out, 'eight_phase_maximum', phased, internal))
        fresh=copy.deepcopy(phased)
        for target in plain: Path(target).write_bytes(bytes(range(65)))
        for step in maximum.request_steps(fresh): step['attempt']['action']='read_fresh'
        receipts.append(collect(pw, observer, out, 'actor_maximum', maximum.actor_maximum(fresh), internal))
        control=maximum.targets_under(root/'control', control=True); helper=Path(control[0])
        repo=Path(__file__).resolve().parents[3]
        subprocess.run(['/usr/bin/xcrun','--sdk','macosx','clang','-Wall','-Wextra','-Werror','-std=c11',str(repo/'tests/fixtures/exec/streams.c'),'-o',str(helper)],check=True)
        for byte in [0,1,34,92,255]:
            direct=subprocess.run([str(helper),'1023','17',str(byte)],capture_output=True,check=True,timeout=5)
            assert direct.stdout==bytes([byte])*1023 and direct.stderr==bytes([byte])*17
        args=['1023','1023','1']; large=maximum.specimen([str(helper)]*maximum.STEPS,control,exec_args=args)
        large['specimen_id']='\x01'*255; large['run_kind']='\x01'*63
        large['policy'].update(capture_compiled_profile=True,capture_nonce='f'*32)
        for i,step in enumerate(large['probe_plan']): step['step_id']='\x01'*59+f'{i:04d}'
        receipts.append(collect(pw,observer,out,'control_character_exec',large,internal,exec_args=args,exec_output=('\x01'*1023,'\x01'*1023)))
        (out/'response-footprint.json').write_text(json.dumps(dict(schema_version=1,case_id='witness_contract/response_footprint',workloads=receipts),indent=2)+'\n')

if __name__ == '__main__': main()
