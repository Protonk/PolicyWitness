"""Offline rejection controls; constructed scalars are not native observations."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from check_response_footprint import STAGES, check_internal, check_sizes, check_observation, actor_geometry, check_geometry, check_terminal_resolution


def rejected(check, value):
    try:
        check(value)
    except (AssertionError, ValueError, KeyError, TypeError):
        return
    raise AssertionError('mutated receipt accepted')


def fixture():
    # Independent bytes and counts, rather than values read back from a hook.
    host = b'{"marker":"independent controls"}'
    defaults = dict(raw_stdout=None, raw_stderr=None, retained_stdout=None, retained_stderr=None,
                    generic_base64=None, typed_base64=None, host_retained=None, decoded=None,
                    parsed_host=False, borrowed_input=False, envelope=False, rendered=None)
    rows = []
    for index, stage in enumerate(STAGES):
        row = dict(defaults, stage=stage)
        if index < 4: row.update(raw_stdout=[200,256],raw_stderr=[5,8])
        if 1 <= index <= 3: row['generic_base64'] = 4*((len(host)+2)//3)
        if index == 1: row.update(retained_stdout=[200,256],retained_stderr=[5,8])
        if 2 <= index <= 3: row.update(typed_base64=row['generic_base64'],host_retained=len(host),decoded=[len(host),64])
        if index == 3: row['parsed_host']=True
        if index >= 4: row.update(borrowed_input=True,envelope=True)
        if index == 5: row['rendered']=[300,512]
        rows.append(row)
    return dict(schema_version=1,case_id='response_footprint_success_boundaries',input_sha256=hashlib.sha256(host).hexdigest(),
                client_stdout_bytes=200,client_stderr_bytes=5,host_bytes=len(host),rendered_bytes=300,boundaries=rows)



def observation_fixture():
    identity=dict(pid=123,start_sec=12,start_usec=3)
    def sample(start):
        calls={name:dict(rc=0 if name=='rusage' else 1,errno=0,begin_ns=start+i,end_ns=start+i+1)
               for i,name in enumerate(['generation_before','rusage','path','generation_after'])}
        return dict(pid=123,begin_ns=start,end_ns=start+4,status='ok',generation_before=identity.copy(),
                    generation_after=identity.copy(),path='/independent/controller',calls=calls,
                    raw_cpu_unit='mach_absolute_time_ticks',timebase_numer=125,timebase_denom=3,
                    user_ticks=3,system_ticks=6,user_ns=125,system_ns=250,resident_bytes=100,phys_footprint_bytes=90)
    samples=[sample(30),sample(40)]
    registration=dict(source='EVFILT_PROC NOTE_EXIT registration',generation=identity.copy(),before=sample(10),after=sample(22),begin_ns=20,end_ns=21)
    controller=dict(pid=123,generation=identity,memory_unit='bytes',stage_attribution='unknown',
        launch_bracket_ns=[0,5],exit_bracket_ns=[44,60],verified_live_interval_ns=[30,44],
        exit_registration=registration,exit_inspection=dict(status='error',user_ns=None,system_ns=None,resident_bytes=None,phys_footprint_bytes=None),
        exit_events=[dict(generation=identity.copy(),event='exit',source='EVFILT_PROC NOTE_EXIT',
                          collection_begin_ns=50,collection_end_ns=51,actual_exit_time_ns=None)])
    return controller,samples


def observation_controls():
    valid=observation_fixture(); check_observation(*valid)
    faults=[]
    for metric in ['resident_bytes','phys_footprint_bytes']:
        bad=copy.deepcopy(valid); del bad[1][0][metric]; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['memory_unit']='pages'; faults.append(bad)
    bad=copy.deepcopy(valid); bad[1][0]['generation_after']['start_usec']+=1; faults.append(bad)
    for field,value in [('begin_ns',1),('end_ns',61),('end_ns',29)]:
        bad=copy.deepcopy(valid); bad[1][0][field]=value; faults.append(bad)
    bad=copy.deepcopy(valid); del bad[0]['launch_bracket_ns']; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_bracket_ns']=[60,44]; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_registration']['generation']['pid']+=1; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_events'][0]['generation']['pid']+=1; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_events'][0]['event']='alive'; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_events'][0]['collection_begin_ns']=30; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_events'][0]['actual_exit_time_ns']=50; faults.append(bad)
    bad=copy.deepcopy(valid); bad[1][0].update(status='error',resident_bytes=0,phys_footprint_bytes=0); faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_inspection']['resident_bytes']=0; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_registration']['after']['generation_after']['pid']+=1; faults.append(bad)
    bad=copy.deepcopy(valid); del bad[1][0]['begin_ns']; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_registration']['source']='pid presence'; faults.append(bad)
    bad=copy.deepcopy(valid); bad[0]['exit_events'][0]['source']='leader exit'; faults.append(bad)
    # Keep native sample framing valid while moving it outside the credited interval.
    bad=copy.deepcopy(valid)
    for key in ['begin_ns','end_ns']: bad[1][0][key]-=29
    for call in bad[1][0]['calls'].values():
        call['begin_ns']-=29; call['end_ns']-=29
    faults.append(bad)
    for bad in faults: rejected(lambda pair:check_observation(*pair),bad)
    return len(faults)


def terminal_controls():
    controller,_=observation_fixture()
    expected=controller['generation']
    sample=dict(pid=expected['pid'],begin_ns=45,end_ns=46,status='error',generation_before=None,generation_after=None,path=None,
                user_ns=None,system_ns=None,resident_bytes=None,phys_footprint_bytes=None,
                calls={key:dict(rc=0,errno=3) for key in ['generation_before','generation_after','path']})
    valid=dict(failed_sample=sample,exit_events=controller['exit_events'],wait_observed=True,returncode=0,
               classification='terminal generation exit; failed metrics excluded')
    check=lambda value:check_terminal_resolution(value,expected)
    check(valid)
    faults=[]
    bad=copy.deepcopy(valid); bad['exit_events']=[]; faults.append(bad)
    bad=copy.deepcopy(valid); bad['wait_observed']=False; faults.append(bad)
    bad=copy.deepcopy(valid); bad['exit_events'][0]['generation']['start_usec']+=1; faults.append(bad)
    bad=copy.deepcopy(valid); bad['failed_sample']['calls']['generation_before']['errno']=1; faults.append(bad)
    bad=copy.deepcopy(valid); bad['failed_sample']['resident_bytes']=0; faults.append(bad)
    bad=copy.deepcopy(valid); bad['failed_sample']['generation_before']=expected.copy(); faults.append(bad)
    for bad in faults: rejected(check,bad)
    return len(faults)


def geometry_fixture():
    issue=dict(operation='issue',token_ref='T')
    transfer=dict(operation='transfer',token_ref='T',recipient='reader',delivery_ref='D')
    consume=dict(operation='consume',delivery_ref='D',handle_ref='H')
    request=dict(actors=[dict(actor_id='issuer'),dict(actor_id='reader')],phases=[
        dict(actor_id='issuer',actions=[dict(extension=issue),dict(extension=transfer)]),
        dict(actor_id='reader',actions=[dict(extension=consume)])])
    def scope(owner,index):
        return dict(actor_id=owner,actor_index=index,operations=[dict(operation=name,state='succeeded',value=17600) for name in ['mmap','ftruncate']])
    def worker(owner,index):
        return dict(actor_id=owner,actor_index=index,operations=[
            dict(operation='fstat',state='succeeded',value=32768),
            dict(operation='object_size',state='accepted',value=32768),
            dict(operation='mmap',state='succeeded',value=32768),
            dict(operation='page_size',state='succeeded',native_rc=16384)])
    runner=dict(actors=[{},{}],phases=[{},{}],steps=[],extension_events=[{},{},{}],
        resources=dict(tokens=[dict(actor_id='issuer')],deliveries=[dict(recipient_actor_id='reader')],handles=[dict(actor_id='reader')]),
        authority_setup=dict(host=dict(regions=[scope('issuer',0),scope('reader',1)],custody=[dict(token_ref='T',token_index=0,operations=[dict(operation='mmap',state='succeeded',value=16384)])]),
                             workers=[worker('issuer',0),worker('reader',1)]))
    return request,runner


def geometry_controls():
    request,runner=geometry_fixture(); account=actor_geometry(request,runner,4096)
    check=lambda value:check_geometry(value,request,runner,4096)
    check(account)
    assert account['per_actor'][0]['authority']['logical_requested_bytes']==17600
    assert account['per_actor'][0]['authority']['observed_object_bytes']==32768
    assert account['per_actor'][0]['authority']['observed_padding_bytes']==15168
    faults=[]
    for field in ['shared_backing_objects','shared_backing_bytes','mapped_views','private_custody_bytes']:
        bad=copy.deepcopy(account); bad[field]*=2; faults.append(bad)
    bad=copy.deepcopy(account); bad['per_actor'][0]['actor_id']='reader'; faults.append(bad)
    bad=copy.deepcopy(account); bad['per_actor'][0]['issued_token_refs']=['OTHER']; faults.append(bad)
    bad=copy.deepcopy(account); bad['per_actor'][0]['observed']['outbound']+=1; faults.append(bad)
    bad=copy.deepcopy(account); bad['per_actor'][0]['authority']['backing_bytes']*=2; faults.append(bad)
    bad=copy.deepcopy(account); bad['capacity_is_reply_payload']=True; faults.append(bad)
    for bad in faults: rejected(check,bad)
    changed=copy.deepcopy(runner); changed['authority_setup']['host']['regions'][0]['actor_id']='reader'
    rejected(lambda r:actor_geometry(request,r,4096),changed)
    changed=copy.deepcopy(runner); changed['authority_setup']['host']['custody'][0]['token_ref']='OTHER'
    rejected(lambda r:actor_geometry(request,r,4096),changed)
    changed=copy.deepcopy(runner); changed['authority_setup']['host']['custody'][0]['token_index']=1
    rejected(lambda r:actor_geometry(request,r,4096),changed)
    # Host logical request and the page-padded worker view share one backing.
    for operation in ['fstat','object_size','mmap']:
        changed=copy.deepcopy(runner)
        next(op for op in changed['authority_setup']['workers'][0]['operations'] if op['operation']==operation)['value']=17600
        rejected(lambda r:actor_geometry(request,r,4096),changed)
    bad=copy.deepcopy(account); bad['shared_backing_bytes']+=32768
    rejected(check,bad)
    bad=copy.deepcopy(account); bad['per_actor'][0]['authority']['observed_padding_bytes']=0
    rejected(check,bad)
    return len(faults)+8


def main():
    terminal_rejections=terminal_controls()
    observation_rejections=observation_controls()
    geometry_rejections=geometry_controls()
    receipt=fixture(); check_internal(receipt)
    mutations=[]
    for index in range(6):
        value=copy.deepcopy(receipt); value['boundaries'].pop(index); mutations.append(value)
    value=copy.deepcopy(receipt); value['boundaries'][1:3]=reversed(value['boundaries'][1:3]); mutations.append(value)
    for field in ['client_stdout_bytes','client_stderr_bytes','host_bytes','rendered_bytes']:
        value=copy.deepcopy(receipt); value[field]+=1; mutations.append(value)
    value=copy.deepcopy(receipt); value['boundaries'][2]['decoded'][1]=0; mutations.append(value)
    for field in ['raw_stdout','raw_stderr','typed_base64','decoded','host_retained']:
        value=copy.deepcopy(receipt); value['boundaries'][5][field]=copy.deepcopy(receipt['boundaries'][2][field]); mutations.append(value)
    for value in mutations: rejected(check_internal,value)
    import base64
    host=b'{}'; envelope=b'{"outer":true}\n'; encoded=base64.b64encode(host).decode()
    reply=dict(data_base64=encoded,bytes_received=2,bytes_retained=2,truncated=False)
    client=dict(stdout_truncated=False,stderr_truncated=False,stdout_parse_error=None,stdout_capture_error=None,
                stdout_bytes_received=200,stdout_bytes_retained=200,stderr_bytes_received=5,stderr_bytes_retained=5,capture_limit_bytes=300)
    sizes=dict(host_received_bytes=2,host_retained_bytes=2,computed_transport_artifact_sha256=hashlib.sha256(host).hexdigest(),
               hash_scope='computed transport artifact; no producer hash supplied',synthesized_host_bound_bytes=100,
               base64_characters=len(encoded),client_stdout_received_bytes=200,client_stdout_retained_bytes=200,
               client_stderr_received_bytes=5,client_stderr_retained_bytes=5,client_allowance_bytes=300,
               final_envelope_bytes=len(envelope),authority_bytes_in_reply_payload=False)
    check=lambda value:check_sizes(value[0],value[1],client,host,envelope)
    check((sizes,reply))
    for field in ['host_received_bytes','host_retained_bytes','base64_characters','client_stdout_received_bytes',
                  'client_stderr_retained_bytes','final_envelope_bytes']:
        changed=copy.deepcopy(sizes); changed[field]+=1; rejected(check,(changed,reply))
    for field,wrong in [('computed_transport_artifact_sha256','0'*64),('authority_bytes_in_reply_payload',True),('host_received_bytes',200)]:
        changed=copy.deepcopy(sizes); changed[field]=wrong; rejected(check,(changed,reply))
    for field,wrong in [('data_base64','e31='),('bytes_retained',1),('truncated',True)]:
        changed=copy.deepcopy(reply); changed[field]=wrong; rejected(check,(sizes,changed))
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps(dict(schema_version=1,case_id='response_footprint_controls',constructed=True,
            accepted_valid=True,rejected_terminal=terminal_rejections,rejected_observation=observation_rejections,rejected_geometry=geometry_rejections,rejected_internal=len(mutations),rejected_transport=12),indent=2)+'\n')
    print('response footprint: valid independent receipts accepted; boundary and transport mutations rejected')

if __name__=='__main__': main()
