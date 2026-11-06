"""Public CLI boundary controls with token comparison only in transient memory."""
import ctypes
import hashlib
import json
import mmap
import os
import shutil
from pathlib import Path
import struct
import stat
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer
from lifecycle_oracle import check_record
from check_extensions import probe, intervention, specimen, lifecycle_events

SIZE, TOKEN_OFFSET, TOKEN_CAPACITY = 32768, 128, 16384
LIBC = ctypes.CDLL(None, use_errno=True)
# mode is variadic; declaring it fixed uses the wrong arm64 calling convention.
LIBC.shm_open.argtypes = [ctypes.c_char_p, ctypes.c_int]
LIBC.shm_open.restype = ctypes.c_int
LIBC.shm_unlink.argtypes = [ctypes.c_char_p]
LIBC.shm_unlink.restype = ctypes.c_int


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


# Each expected primary is one immutable independently published setup cell.
# Close after an earlier failure is cleanup, never a replacement primary.
SETUP_FAILURES = {
    107: (3, -1, 1), 108: (5, -1, 5), 109: (8, None, 19),
    110: (9, -1, 5), 111: (5, -1, 5), 112: (7, None, None),
    113: (10, None, None), 114: (10, None, None), 115: (10, None, None),
    118: (9, -1, 9),
}


def check_setup_failure(runner, mode):
    subject=next(a for a in runner['actors'] if a['actor_id']=='subject')
    setup=next(a for a in runner['authority_setup']['workers'] if a['actor_id']=='subject')
    primary,rc,error=SETUP_FAILURES[mode]
    assert setup['publication']=='observed' and setup['disposition']=='terminal_required_failure',setup
    assert setup['primary_operation']==primary,setup
    cells={c['slot']:c for c in setup['operations']}
    assert cells[primary].get('native_rc')==rc and cells[primary].get('errno')==error,cells
    assert subject['setup_status']=='authority_setup_failed' and subject['application_count']==0,subject
    assert subject['application']=={'state':'not_attempted','basis':'terminal_authority_setup_refusal'},subject
    assert not subject.get('applied') and subject['subprocess']['reaped'],subject
    if mode==111:
        assert cells[9]['role']=='cleanup' and cells[9]['native_rc']==-1 and cells[9]['errno']==9,cells
    if mode==118:
        assert cells[1]['state']=='unavailable' and cells[9]['role']=='setup',cells
    assert all(not e['result_published'] and not e['call_boundary_observed'] for e in lifecycle_events(runner))
    assert all(step['attempt']['result_source']=='synthetic' and step['comparison']['order']!='query_first' for step in runner['steps'])


def compile_fixture(out, channel, mode, issuer, executable_dir):
    path = executable_dir / ('issuer' if issuer else 'worker')
    command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra',
        '-Wno-deprecated-declarations', '-Wno-unused-function', f'-DPW_CONTROL_MODE={mode}',
        '-DPW_CONTROL_CHANNEL=' + json.dumps(channel), '-I', str(ROOT / 'controller/tools/pw_probe_runner')]
    command += [str(ROOT / 'tests/fixtures/extension_controls/control.c'), '-lsandbox', '-o', str(path)]
    write_json(out / (path.name + '-build-command.json'), command)
    result = subprocess.run(command, capture_output=True, timeout=30)
    (out / (path.name + '-build.log')).write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, f'{path.name} compile failed; see build log'
    subprocess.run(['/usr/bin/codesign','--force','--sign','-',str(path)],check=True,capture_output=True)
    shutil.copy2(path, out / path.name)
    return path


def observations(mapping):
    return dict(issuer_pid=struct.unpack_from('I', mapping, 4)[0], worker_pid=struct.unpack_from('I', mapping, 8)[0],
        stage=struct.unpack_from('I', mapping, 12)[0], operation=struct.unpack_from('I', mapping, 16)[0],
        actual_returned=bool(struct.unpack_from('I', mapping, 20)[0]), actual_result=struct.unpack_from('q', mapping, 24)[0],
        issuer_core_disabled=bool(struct.unpack_from('I', mapping, 32)[0]),
        worker_core_disabled=bool(struct.unpack_from('I', mapping, 36)[0]),
        issuer_channel_closed=bool(struct.unpack_from('I', mapping, 40)[0]),
        worker_channel_closed=bool(struct.unpack_from('I', mapping, 44)[0]),
        token_length=struct.unpack_from('I', mapping, 48)[0],
        issuer_argv_clean=bool(struct.unpack_from('I', mapping, 52)[0]),
        issuer_env_clean=bool(struct.unpack_from('I', mapping, 56)[0]),
        worker_argv_env_clean=bool(struct.unpack_from('I', mapping, 60)[0]),
        worker_token_erased=bool(struct.unpack_from('I', mapping, 64)[0]),
        issuer_token_erased=bool(struct.unpack_from('I', mapping, 68)[0]),
        control_value=struct.unpack_from('I', mapping, 72)[0],
        prefix_valid=bool(struct.unpack_from('I', mapping, 76)[0]),
        worker_tail_seeded=bool(struct.unpack_from('I', mapping, 80)[0]),
        worker_erase_capacity=struct.unpack_from('I', mapping, 84)[0],
        worker_erase_failures=struct.unpack_from('I', mapping, 88)[0],
        source_done_before_exit=bool(struct.unpack_from('I',mapping,92)[0]),
        source_final_completed_before_exit=bool(struct.unpack_from('I',mapping,96)[0]))


def run_case(pw, out, name, issuer_mode=0, worker_mode=None, row=None):
    out = out / name
    out.mkdir()
    channel = '/pwext_' + uuid.uuid4().hex[:20]
    fd = LIBC.shm_open(channel.encode(), os.O_RDWR | os.O_CREAT | os.O_EXCL, ctypes.c_uint(0o600))
    assert fd >= 0, f'create transient observer failed: errno {ctypes.get_errno()}'
    owner = dict(channel=channel, creator_pid=os.getpid(), exclusive_creation=True, bytes=SIZE,
                 token_bytes_retained=False, cleanup_retained=True, recovery_state='unresolved_manual',
                 recovery='Do not unlink from this recorded name alone after owner exit; verify retained object identity or recover manually.')
    recovery = Path(tempfile.mkdtemp(prefix='pw-extension-control-', dir='/private/tmp')) / 'owner.json'
    owner.update(recovery_path=str(recovery), case_directory=str(out))
    def save_owner():
        write_json(out / 'channel-owner.json', owner)
        write_json(recovery, owner)
    def retire_owner():
        if not owner['cleanup_retained']:
            (recovery.parent / 'target').unlink(missing_ok=True)
            for name in ('issuer', 'worker'):
                (recovery.parent / name).unlink(missing_ok=True)
            recovery.unlink()
            recovery.parent.rmdir()
    try:
        save_owner()
        metadata = os.fstat(fd)
        owner.update(mode=stat.S_IMODE(metadata.st_mode), uid=metadata.st_uid)
        assert stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_uid == os.getuid(), owner
        os.ftruncate(fd, SIZE)
        mapping = mmap.mmap(fd, SIZE, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    except BaseException:
        owner['cleanup_retained'] = LIBC.shm_unlink(channel.encode()) != 0
        save_owner()
        retire_owner()
        os.close(fd)
        raise
    mapping[:] = b'\0' * SIZE
    struct.pack_into('I', mapping, 0, 0x43545845)
    save_owner()
    launched, cleanup_known = False, False
    try:
        issuer = compile_fixture(out, channel, issuer_mode, True, recovery.parent)
        worker = compile_fixture(out, channel, worker_mode or 0, False, recovery.parent)
        target = recovery.parent / 'target'
        owner['target_path'] = str(target)
        save_owner()
        contents = b'PW boundary witness\n'
        target.write_bytes(contents)
        spec = specimen(target, [[probe('before', target)], [intervention('consume', 'consume')],
                                 [probe('during', target), intervention('release', 'release')],
                                 [probe('after', target)]],terminate_issuer=issuer_mode in (18,19,20))
        if row is not None:
            spec = specimen(target, [[intervention(action, action) if action in ('consume', 'release')
                else probe(action, target) for action in phase] for phase in row['actions']])
            spec['specimen_id'] = row['id']
            if row['id']=='M07': spec['phases'][0:2]=reversed(spec['phases'][0:2])
        spec['_test_overrides'] = dict(actor_equipment_executable_paths={'unentitled':str(issuer),'selected':str(worker)})
        request = out / 'specimen.json'
        write_json(request, spec)
        command = [pw, 'run', str(request), '--timeout-ms', '60000']
        # Unlike ordinary RunCapture, keep output in memory until comparison
        # with the authority-bearing bytes; a product leak must fail without
        # persisting the leaked token in the failure artifact.
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        launched = True
        try:
            stdout, stderr = child.communicate(timeout=40)
        except subprocess.TimeoutExpired:
            child.kill(); child.communicate(timeout=5)
            raise AssertionError('CLI timeout; observer ownership retained pending child inspection')
        envelope = json.loads(stdout)
        runner = envelope['data']['runner_result']
        actors={a['actor_id']:a for a in runner['actors']}
        issuer_record=actors['issuer'].get('subprocess') or {}
        worker_record=actors['subject'].get('subprocess') or {}
        cleanup_known=all(not a.get('launch',{}).get('pid') or a.get('subprocess',{}).get('reaped') is True for a in actors.values())
        observed = observations(mapping)
        length = observed['token_length']
        assert 0 <= length < TOKEN_CAPACITY, 'invalid observer token length'
        token = bytes(mapping[TOKEN_OFFSET:TOKEN_OFFSET + length])
        leaked = bool(token) and (token in stdout or token in stderr or token in request.read_bytes()
            or any(token in os.fsencode(arg) for arg in command)
            or any(token in os.fsencode(value) for value in os.environ.values()))
        observed['captured_output_excludes_token'] = not leaked
        # Pin the detector's sensitivity using this real token in memory only.
        observed['confinement_detector_control'] = bool(token) and token in b'prefix' + token + b'suffix'
        write_json(out / 'observations.json', observed)
        assert not leaked, 'token confinement failure; raw CLI output withheld'
        (out / 'run.json').write_bytes(stdout)
        (out / 'stderr.txt').write_bytes(stderr)
        write_json(out / 'capture.json', dict(argv=command, cli_pid=child.pid, returncode=child.returncode))
        assert cleanup_known, 'unconfirmed native child cleanup; observer ownership retained'
        assert target.read_bytes() == contents, 'independent target bytes changed'
        assert runner['test_overrides']['actor_equipment_executable_paths']==spec['_test_overrides']['actor_equipment_executable_paths']
        assert consumer.validate(envelope)==[],consumer.validate(envelope)
        assert check_record(envelope)==[],check_record(envelope)
        for role,path,actor_id,pid_key in (('unentitled',issuer,'issuer','issuer_pid'),
                                           ('selected',worker,'subject','worker_pid')):
            binding=next(b for b in runner['equipment_bindings'] if b['binding_id']=='override-'+role)
            assert binding['source']=='test_override' and binding['implementation_identity']=='unverified_fixture',binding
            assert binding['status']=='bound' and binding['signature_osstatus']==0,binding
            # Security may report /tmp for an executable submitted under
            # /private/tmp. Require the same live filesystem object, not a
            # string prefix or a path with merely matching content.
            assert Path(binding['path']).samefile(path),binding
            assert binding['sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),binding
            actor=actors[actor_id]
            equipment=actor['equipment']
            execution=equipment['execution']
            assert equipment['binding_ref']==binding['binding_id'] and equipment['resolved']==role,equipment
            if execution['status']=='matched':
                assert execution['eligible'] and Path(execution['path']).samefile(path),execution
                assert execution['pid']==actor['launch']['pid'] and execution['parent_pid']==actor['launch']['parent_pid'],execution
                assert all(execution[key]==binding[key] for key in ('cdhash','identifier','team_id')),execution
            else:
                assert actor['setup_status']=='authority_setup_failed',actor
                assert execution['status']=='unobserved' and execution['reason']=='setup_unavailable' and not execution['eligible'],execution
            if observed[pid_key]:
                assert observed[pid_key]==actor['launch']['pid'],(actor_id,observed[pid_key],actor['launch'])
        if length:
            assert observed['issuer_argv_clean'] and observed['issuer_env_clean']
            assert observed['issuer_core_disabled'] and observed['issuer_channel_closed']
            assert observed['issuer_token_erased']
            for path in out.rglob('*'):
                if path.is_file():
                    assert token not in path.read_bytes(), 'token found in retained artifact'
        events=lifecycle_events(runner)
        issue=next(e for e in runner['extension_events'] if e['operation']=='issue')
        token_record=runner['resources']['tokens'][0]
        if row is not None:
            from check_extension_combinations import check_row
            check_row(row,runner,observed)
        elif worker_mode in SETUP_FAILURES:
            check_setup_failure(runner,worker_mode)
        elif worker_mode in (101,102,103,201,202,203):
            which=0 if worker_mode<200 else 1
            event=events[which]
            assert runner['normalized_outcome']=='runner_failed'
            assert worker_record['term_signal']==9 and worker_record['reaped']
            assert observed['operation']==which+1 and observed['stage']=={1:1,2:3,3:2}[worker_mode%100]
            assert observed['actual_returned']==(worker_mode%100==3)
            assert event['call_boundary_observed'] and not event['result_published']
            assert event['status']=='unresolved' and event.get('native_result') is None and event.get('errno') is None
            assert observed['worker_core_disabled'] and observed['worker_channel_closed']
            assert runner['steps'][0]['attempt']['result_source']=='worker'
            if which:
                assert events[0]['status']=='returned' and events[0]['native_result']!=-1
                assert runner['steps'][1]['attempt']['result_source']=='worker'
        elif worker_mode==106:
            assert worker_record['term_signal']==9 and worker_record['reaped']
            assert observed['stage']==4 and observed['control_value']>0 and observed['prefix_valid']
            assert not events[0]['result_published'] and not events[0]['call_boundary_observed']
            assert runner['steps'][0]['attempt']['result_source']=='worker'
        elif worker_mode in (116,117):
            transfer=runner['transfers'][0]
            # Rejection acknowledges the malformed framing; it grants neither
            # successful delivery nor permission to compare or consume bytes.
            assert transfer['status']=='recipient_rejected',transfer
            assert transfer['custody_status']=='held' and transfer['copy_status']=='copied',transfer
            assert transfer['equality']=='not_compared',transfer
            assert transfer['request_published'] and transfer['recipient_acknowledged'] and transfer['source_acknowledged'],transfer
            assert transfer['recipient_wait']['stop']=='acknowledged',transfer
            delivery=runner['resources']['deliveries'][0]
            assert delivery['status']=='recipient_rejected' and delivery['equality']=='not_compared',delivery
            assert delivery.get('delivered_length') is None,delivery
            for event,reason in zip(events,('delivery_unavailable','handle_unavailable')):
                assert event['status']=='unavailable' and event['unavailable_reason']==reason,event
                assert event['result_published'] and not event['call_boundary_observed'],event
                assert event.get('native_result') is None and event.get('errno') is None,event
            assert len(events)==2
            assert issue['result_published'] and issue['native_nonnull'] and token_record['status']=='issued',issue
            assert observed['worker_pid']==0 and observed['stage']==0 and observed['operation']==0 and not observed['actual_returned'],observed
            assert observed['worker_tail_seeded'] and observed['worker_erase_capacity']==TOKEN_CAPACITY,observed
            assert observed['worker_token_erased'] and observed['worker_erase_failures']==0,observed
            setup=next(a for a in runner['authority_setup']['workers'] if a['actor_id']=='subject')
            assert setup['disposition']=='ready' and setup['ownership']['shared_erasure']=='performed',setup
            assert worker_record['reaped'] and worker_record['exit_code']==0,worker_record
            assert all(c['ownership']['private_erasure']=='performed' for c in runner['authority_setup']['host']['custody'])
        elif worker_mode==104 or issuer_mode in (10,16):
            assert events[0]['status']=='returned' and events[0]['native_result']==-1
            assert events[1]['status']=='unavailable' and events[1]['unavailable_reason']=='handle_unavailable'
            if issuer_mode==16:
                assert issue['token_length']==16383 and runner['transfers'][0]['status']=='delivered'
        elif worker_mode==204:
            assert events[0]['native_result']!=-1
            assert events[1]['status']=='returned' and events[1]['native_result']==-1 and events[1]['errno']==5
        elif worker_mode==105:
            assert events[0]['status']=='unavailable' and events[0]['unavailable_reason']=='native_api_unavailable'
            assert events[1]['status']=='unavailable' and events[1]['unavailable_reason']=='handle_unavailable'
            setup=next(a for a in runner['authority_setup']['workers'] if a['actor_id']=='subject')
            cells={c['slot']:c for c in setup['operations']}
            assert setup['disposition']=='ready' and cells[1]['state']=='unavailable' and cells[2]['state']=='available'
        elif worker_mode==205:
            assert events[0]['status']=='returned' and events[0]['native_result']!=-1
            assert events[1]['status']=='unavailable' and events[1]['unavailable_reason']=='native_api_unavailable'
        elif issuer_mode==6:
            assert issue['status']=='unavailable' and issue['unavailable_reason']=='native_api_unavailable'
            assert not issue['call_boundary_observed'] and issue['result_published']
            assert events[0]['status']=='unavailable' and events[0]['unavailable_reason']=='delivery_unavailable'
        elif issuer_mode in (18,19,20):
            gate=next(p['termination_gate'] for p in runner['phases'] if p.get('termination_gate'))
            assert observed['source_done_before_exit'] and observed['source_final_completed_before_exit']
            if issuer_mode==19:
                assert gate['outcome']=='timed_out' and not gate['activation_eligible']
                assert not events[0]['call_boundary_observed'] and not events[0]['result_published']
                assert issuer_record['reaped'] and actors['issuer']['owned_reap']['capture_ordinal']>gate['capture_ordinal']
            else:
                reap=actors['issuer']['owned_reap']
                activation=next(p['activation_observation'] for p in runner['phases'] if p['phase_id']=='issuer_final')
                assert gate['outcome']=='satisfied' and gate['activation_eligible']
                assert gate['observation']=={'capture_ordinal':reap['capture_ordinal']}
                assert activation['capture_ordinal']<reap['capture_ordinal']<gate['capture_ordinal']
                assert reap['observed_ns']>=activation['observed_ns'] and not reap['departure_requested']
                assert events[0]['native_result']!=-1 and events[1]['native_result']==0
                if issuer_mode==18: assert gate['wait']['elapsed_ms']>=250
                else: assert issuer_record['exit_code']==87
        elif issuer_mode in (4,5,13,17):
            assert runner['normalized_outcome']=='runner_failed'
            assert issuer_record['reaped']
            if issuer_mode==5: assert not events[0]['call_boundary_observed']
            else: assert events[0]['status']=='unavailable' and events[0]['unavailable_reason']=='delivery_unavailable'
            assert issue['result_published']==(issuer_mode==17)
            if issuer_mode==17:
                assert observed['control_value']==1 and issue['native_nonnull'] is True and issuer_record['exit_code']==87
            if issuer_mode==13: assert observed['control_value']==0
        elif issuer_mode in (1,2,3,7,8,9,11,12,14,15):
            assert issue['status']=='returned' and issue['call_boundary_observed'] and issue['result_published']
            assert issue['native_nonnull']==(issuer_mode!=1)
            if issuer_mode==1: assert issue['errno']==13
            assert token_record['status']!='issued',token_record
            assert events[0]['status']=='unavailable' and events[0]['unavailable_reason']=='delivery_unavailable'
            assert events[1]['unavailable_reason']=='handle_unavailable'
        else:
            assert runner['transfers'][0]['status']=='delivered'
            assert events[0]['native_result']!=-1 and events[1]['native_result']==0
            assert observed['worker_argv_env_clean'] and observed['worker_token_erased']
            assert observed['worker_tail_seeded'] and observed['worker_erase_capacity']==TOKEN_CAPACITY
            assert observed['worker_erase_failures']==0
        assert all(r['ownership']['shared_erasure']=='performed' for r in runner['authority_setup']['host']['regions'])
        return dict(case=name, ok=True, issuer_mode=issuer_mode, worker_mode=worker_mode)
    finally:
        mapping[:] = b'\0' * SIZE
        mapping.close()
        if not launched or cleanup_known:
            current=LIBC.shm_open(channel.encode(),os.O_RDONLY)
            assert current>=0, 'observer identity lookup failed'
            try:
                held,named=os.fstat(fd),os.fstat(current)
                assert (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino), 'observer name changed objects; retain for manual recovery'
                assert LIBC.shm_unlink(channel.encode())==0, 'observer unlink failed'
            finally: os.close(current)
            owner['cleanup_retained'] = False
        os.close(fd)
        save_owner()
        retire_owner()


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory).resolve()
    results = []
    cases=[('native',0,0)]+[(f'issue-{mode}',mode,0) for mode in range(1,21)] \
        +[(f'worker-{mode}',0,mode) for mode in (101,102,103,104,105,106,116,117,201,202,203,204,205)] \
        +[(f'setup-{mode}',0,mode) for mode in SETUP_FAILURES]
    for name, issuer, worker in cases:
        try:
            results.append(run_case(pw, out, name, issuer, worker))
        except Exception as exc:
            results.append(dict(case=name, ok=False, error=str(exc)))
        write_json(out / 'results.json', results)
    failed = [r['case'] + ': ' + r.get('error', '') for r in results if not r['ok']]
    assert not failed, '\n'.join(failed)
    print(f'{len(results)} native boundary and token-confinement controls passed.')


if __name__ == '__main__':
    main()
