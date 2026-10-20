#!/usr/bin/env python3
"""Observe launch-descriptor ownership in copied production host sources.

Run through tests/run.sh. The signed worker is unchanged; native observer
challenges and source variants exist only in this case's owned artifacts.
"""
import copy
import hashlib
import json
import os
import signal
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/lib"))
from build_receipt import record_build

SWIFT = ['swift']
HERE = ROOT / "tests/fixtures/launch_descriptor"
FAILURES = ("spawn_failure", "truncate_failure", "mmap_nil", "mmap_failed", "pipe_1", "pipe_2", "nosigpipe", "get_flags", "nonblock", "pipe_cloexec", "extension_dup")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(out, label, argv, **kwargs):
    receipt = dict(argv=argv, cwd=str(kwargs.get('cwd', Path.cwd())), stage='prepared')
    command_path = out / (label + '.command.json')
    command_path.write_text(json.dumps(receipt, indent=2)+'\n')
    with (out / (label + '.log')).open('w') as stream:
        p = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True, **kwargs)
        receipt.update(process_pid=p.pid, stage='running')
        command_path.write_text(json.dumps(receipt, indent=2)+'\n')
        timed_out = False
        try: p.wait(timeout=240)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=10)
        receipt.update(returncode=p.returncode, timed_out=timed_out, stage='exited')
        command_path.write_text(json.dumps(receipt, indent=2)+'\n')
        # Post-reap group observations are read-only: a numeric PGID alone
        # no longer authorizes signaling once its owner has been reaped.
        # Any survivor retains this receipt and requires identity-checked
        # recovery by the coordinator. On timeout above, the leader remains
        # our unreaped child until the group signal and subsequent wait.
        scan = subprocess.check_output(['ps','-axo','pid=,pgid=,stat=,comm='], text=True)
        members = [line for line in scan.splitlines() if len(line.split()) >= 3 and line.split()[1] == str(p.pid)]
        cleanup = []
        (out / (label + '.ownership.json')).write_text(json.dumps(dict(process_group=p.pid,timed_out=timed_out,members_after_exit=members,members_after_cleanup=cleanup),indent=2)+'\n')
        assert not timed_out and not members and not cleanup, ('unexpected fixture cleanup', str(out))
    if p.returncode:
        raise AssertionError((label, p.returncode, str(out / (label + '.log'))))

def check(r, variant, mode):
    assert r['host_pid'] == r['driver_pid'], 'driver receipt identity'
    events = r['events']
    closes = [e for e in events if e['event'] == 'evidence_close']
    mapping = r['mapping']
    if mode in ('truncate_failure', 'mmap_nil', 'mmap_failed'):
        assert mapping == [0] * 11, 'unexpected mapping teardown before acquisition'
    else:
        assert mapping[0] == 1 and mapping[2] > 0 and mapping[3] >= mapping[2], 'owned mapping extent'
        assert mapping[4:6] == [1, mapping[3]], 'positive complete mapped range absent'
        assert mapping[6:10] == [0, 0, 1, 0], 'full mapped range not released'
        assert mapping[10] == mapping[2], 'owner unmap length differs from acquisition'
    injected = [e['point'] for e in events if e['event'] == 'injected']
    assert injected == ([mode] if mode in FAILURES and mode != 'spawn_failure' else []), 'failure injection'
    if mode in FAILURES:
        expected = {'spawn_failure': 'posix_spawn: ', 'truncate_failure': 'ftruncate:',
            'mmap_nil': 'mmap:', 'mmap_failed': 'mmap:', 'pipe_1': 'ready pipe:',
            'pipe_2': 'policy pipe:', 'nosigpipe': 'F_SETNOSIGPIPE:',
            'get_flags': 'policy O_NONBLOCK:', 'nonblock': 'policy O_NONBLOCK:',
            'pipe_cloexec': 'FD_CLOEXEC:', 'extension_dup': 'extension descriptor duplication failed'}
        assert expected[mode] in r['worker']['error'], 'wrong refusal boundary'
        assert 'pid' not in r['worker'] and not r['worker_receipt'] and not r['validator_receipt'] and not r['child_owner'], 'unexpected child'
        assert not r['readbacks'] and not r['validator']
        assert len(closes) == 1 and closes[0]['rc'] == 0, 'failure close ownership'
        assert not r['original_open_after_return'], 'failed setup retained descriptor'
        return
    w, v = r['worker'], r['validator']
    owner = r['child_owner']
    assert owner and owner['host_pid'] == r['host_pid'] == owner['process_group'], 'child ownership receipt'
    assert owner['worker_pid'] == w['pid'] == r['worker_receipt']['pid'] and r['worker_receipt']['ppid'] == r['host_pid'], 'worker receipt identity'
    assert w['independently_confirmed_host_reap'], 'host reap not independently confirmed'
    assert w['reaped'] and w['exit_code'] == 0 and w['applied'] and w['done'], 'worker did not complete'
    assert w['acknowledged'] and w['ownership'], 'ordinary release/ack lost'
    assert v['reaped'] and v['exit_code'] == 0, 'observer not reaped cleanly'
    assert v['pid'] == r['validator_receipt']['pid'] and r['validator_receipt']['ppid'] == r['host_pid'], 'validator receipt identity'
    host = [x for x in r['readbacks'] if x['same_host_object']]
    decoy = [x for x in r['readbacks'] if x['same_decoy_object']]
    assert len(decoy) == 1 and decoy[0]['fd'] == r['decoy_fd'], 'positive decoy challenge missing'
    assert not decoy[0]['same_host_object'] and decoy[0]['host_value'] == 0, 'decoy mistaken for evidence'
    assert all(x['token'] != 0 for x in r['readbacks']), 'challenge token absent'
    assert len(host) == (1 if variant == 'old_lifetime' else 0), 'same evidence reference inheritance'
    if host:
        assert host[0]['fd'] == r['original_fd'], 'wrong inherited reference'
        assert not host[0]['same_decoy_object'], 'host confused with decoy'
    observed = {x['fd']: x for x in r['validator_receipt']['fds']}
    for x in host + decoy:
        assert observed[x['fd']]['access_mode'] == 2 and observed[x['fd']]['mapped'] == 1, 'not writable mapping authority'
    if variant in ('candidate', 'stale_owner'):
        assert r['sentinel_fd'] == r['original_fd'], 'exact descriptor reuse not forced'
        assert r['sentinel_open_after_return'] == (variant == 'candidate'), 'close-once ownership'
        assert len(closes) == (1 if variant == 'candidate' else 2), 'unexpected close count'
    else:
        assert r['sentinel_fd'] == -1 and not r['original_open_after_return']
        assert len(closes) == 1 and closes[0]['rc'] == 0
    child = {x['fd']: x for x in r['worker_receipt']['fds']}
    assert child[3]['mapped'] == 1 and child[3]['access_mode'] == 2, 'worker evidence delivery lost'
    if mode == 'high':
        assert r['original_fd'] > 5 and child[r['original_fd']]['mapped'] == 1, 'worker original-number alias missing'
    if mode == 'self':
        assert r['original_fd'] == 3, 'self-dup was not exercised'
    if mode == 'extension_delivery':
        assert child[5]['access_mode'] == 0 and not child[5]['mapped'], 'extension fd5 not retained separately'


def run(out, scratch):
    assert not out.exists(), 'fresh output required'
    base = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    out.mkdir(parents=True)
    package = out / 'runner'
    shutil.copytree(ROOT / 'runner/Sources', package / 'Sources')
    shutil.copyfile(ROOT / 'runner/Package.swift', package / 'Package.swift')
    snapshots = out / 'source'; snapshots.mkdir()
    for source in HERE.iterdir():
        if source.is_file(): shutil.copyfile(source, snapshots / source.name)
    shutil.copyfile(__file__, snapshots / Path(__file__).name)
    source_manifest = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/'runner/Sources').rglob('*')) if p.is_file()}
    source_manifest['runner/Package.swift'] = digest(ROOT/'runner/Package.swift')
    source_manifest.update({str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/'controller/tools/pw_probe_runner').glob('*.h'))})
    source_manifest.update({str(p.relative_to(ROOT)): digest(p) for p in sorted(HERE.iterdir()) if p.is_file()})
    source_manifest[str(Path(__file__).relative_to(ROOT))] = digest(Path(__file__))
    (out/'source-manifest.json').write_text(json.dumps(dict(base_commit=base, inputs=source_manifest), indent=2)+'\n')
    path = package/'Sources/PWRunnerCore/CWorker.swift'
    original = path.read_text(); (snapshots/'CWorker.original.swift').write_text(original)
    transformations = []
    def replace(old,new,count=1):
        nonlocal original
        assert original.count(old) == count, (old, original.count(old), count)
        original = original.replace(old,new)
        transformations.append(dict(old=old,new=new,count=count))
    replace('return pw_cworker_shm_open_create(cName, 0o600)', 'return probeShm(cName, 0o600)')
    replace('close(shmFD)', '_ = probeClose(shmFD)', 5)
    replace('if ftruncate(shmFD,', 'if probeTruncate(shmFD,')
    replace('guard let base = mmap(', 'guard let base = probeMap(')
    replace('_ = munmap(base, PWShmLayout.regionBytes)', '_ = descriptorUnmap(base, PWShmLayout.regionBytes)')
    replace('if pipe(&', 'if probePipe(&', 2)
    replace('fcntl(', 'probeFcntl(', 8)
    replace('    _ = probeFcntl(shmFD, F_SETFD, 0)', '    if probeVariant != "no_clear" { _ = probeFcntl(shmFD, F_SETFD, 0) }')
    replace('    storeRelease(rawBase, offset: PWShmLayout.preparedOffset, 1)',
            '    storeRelease(rawBase, offset: PWShmLayout.preparedOffset, 1)\n    probePrepared(base)')
    replace('    ownsShmFD = false\n    _ = probeClose(shmFD)', """    probeChildSpawned(pid)
    // Deliberate defects affect only this copied executable. Candidate executes
    // the production ownership operations without substitutions.
    if probeVariant != "old_lifetime" {
        if probeVariant != "stale_owner" { ownsShmFD = false }
        _ = probeClose(shmFD)
    }
    probeAfterSpawn(ownsShmFD)""")
    path.write_text(original); (snapshots/'CWorker.instrumented.swift').write_text(original)
    (out/'transformations.json').write_text(json.dumps(transformations,indent=2)+'\n')
    shutil.copyfile(HERE/'Probe.swift', package/'Sources/PWRunnerCore/Probe.swift')
    shutil.copyfile(HERE/'mapping.c', package/'Sources/PWCWorkerShim/descriptor_mapping.c')
    main=package/'Tests/PWRunnerCoreTests/main.swift'; main.parent.mkdir(parents=True)
    main.write_text('import Foundation\n@testable import PWRunnerCore\ntry runProbe(CommandLine.arguments[1], CommandLine.arguments[2], CommandLine.arguments[3])\n')
    app=Path(os.environ.get('PW_APP_DIR', str(ROOT/'dist/PolicyWitness.app')))
    worker=app/'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
    observer=out/'observer'
    command(out,'observer-build',['clang','-Wall','-Wextra','-Werror','-I'+str(ROOT/'controller/tools/pw_probe_runner'),'-DREAL_WORKER="'+str(worker)+'"',str(HERE/'observer.c'),'-o',str(observer)])
    command(out,'core-build',[*SWIFT,'build','--package-path',str(package),'--scratch-path',str(scratch),'--product','PWRunnerCoreTests'])
    binary = record_build(package, out, scratch, 'PWRunnerCoreTests', swift_command=SWIFT)
    (out/'equipment.json').write_text(json.dumps(dict(worker=str(worker),worker_sha256=digest(worker),observer_sha256=digest(observer),host_sha256=digest(binary),uname=subprocess.check_output(['uname','-a'],text=True).strip()),indent=2)+'\n')
    results=[]; receipts={}
    cases=[(v,m) for v in ('candidate','old_lifetime') for m in ('high','self','extension_delivery')]
    cases += [('candidate', mode) for mode in FAILURES]
    cases += [('stale_owner','high'),('no_clear','self')]
    for variant,mode in cases:
        label=variant+'-'+mode; case=out/label; case.mkdir()
        command(case,'run',[str(binary),str(observer),variant,mode],cwd=case)
        r=json.loads((case/'receipt.json').read_text())
        r['driver_pid']=json.loads((case/'run.command.json').read_text())['process_pid']
        owner=case/'child-owner.json'
        r['child_owner']=json.loads(owner.read_text()) if owner.exists() else None
        for role in ('worker','validator'):
            f=case/(role+'.json')
            r[role+'_receipt']=json.loads(f.read_text()) if f.exists() else None
        (case/'joined.json').write_text(json.dumps(r,indent=2)+'\n')
        if variant == 'no_clear':
            # Completion failure alone is ambiguous. Establish the specific
            # self-dup endpoint loss at child entry and its native disposition.
            assert r['original_fd'] == 3, 'no-clear control did not reach self-dup'
            assert all(fd['fd'] != 3 for fd in r['worker_receipt']['fds']), 'no-clear control retained fd3'
            w = r['worker']
            assert w['exit_code'] == 3 and not w['applied'] and not w['done'], 'no-clear control changed refusal boundary'
            assert w['reaped'] and w['independently_confirmed_host_reap'], 'no-clear child reap not established'
        # Test the deliberately restored defects with candidate requirements.
        # Their designated rejected assertion must remain independently fixed.
        expected_failure = {'old_lifetime': 'same evidence reference inheritance',
                            'stale_owner': 'close-once ownership',
                            'no_clear': 'worker did not complete'}.get(variant)
        try:
            check(r, 'candidate', mode)
        except AssertionError as error:
            assert expected_failure and str(error) == expected_failure, (label, str(error), expected_failure)
            results.append(dict(rejected_source_control=label, reason=str(error)))
        else:
            assert expected_failure is None, (label, 'source defect escaped candidate oracle')
            results.append(dict(case=label,passed=True,host_references=sum(x['same_host_object'] for x in r['readbacks']),sentinel_survived=r['sentinel_open_after_return']))
        if variant == 'old_lifetime': check(r, variant, mode)
        receipts[label]=r
    mutations=[
        ('old_lifetime-high','missing positive decoy',lambda r:r.update(readbacks=[x for x in r['readbacks'] if not x['same_decoy_object']])),
        ('candidate-high','decoy mislabeled same object',lambda r:r['readbacks'][0].update(same_host_object=True)),
        ('old_lifetime-high','removed native write authority',lambda r:[x.update(access_mode=0) for x in r['validator_receipt']['fds']] ),
        ('candidate-high','reuse sentinel closed',lambda r:r.update(sentinel_open_after_return=False)),
        ('candidate-high','reuse not established',lambda r:r.update(sentinel_fd=-1)),
        ('old_lifetime-high','worker delivery missing',lambda r:[x.update(mapped=0) for x in r['worker_receipt']['fds'] if x['fd']==3]),
        ('candidate-high','surviving mapping suffix',lambda r:r['mapping'].__setitem__(9, 16384)),
    ]
    for name,label,mutate in mutations:
        r=copy.deepcopy(receipts[name]);mutate(r)
        try:check(r,*name.split('-'))
        except AssertionError as e:results.append(dict(rejected_control=label,reason=str(e)))
        else:raise AssertionError((label,'counterexample accepted'))
    (out/'snapshot-hashes.json').write_text(json.dumps({str(p.relative_to(out)):digest(p) for p in sorted(snapshots.rglob('*')) if p.is_file()},indent=2)+'\n')
    assert digest(worker)==json.loads((out/'equipment.json').read_text())['worker_sha256']
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__': run(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
