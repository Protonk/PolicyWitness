#!/usr/bin/env python3
"""Run only in coordinator-granted execution window under checkout_lock.sh.

The output is a fresh investigation directory, outside the managed test-run
namespace. All source copies, exact transformations, commands and raw receipts
remain there. No app bytes, repository sources, or catalogue entries change.
"""
import copy
import hashlib
import json
import os
import signal
import time
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = '503156f0693dd8a22acf633efccdc93e300f2ebc'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(out, label, argv, **kwargs):
    with (out / (label + '.log')).open('w') as stream:
        p = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True, **kwargs)
        timed_out = False
        try: p.wait(timeout=240)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=10)
        # Every case has zero exec attempts. The worker and observer inherit
        # this fresh process group and never change it. Scan after the host
        # exits, then kill only this owned group if it retained a child.
        scan = subprocess.check_output(['ps','-axo','pid=,pgid=,stat=,comm='], text=True)
        members = [line for line in scan.splitlines() if len(line.split()) >= 3 and line.split()[1] == str(p.pid)]
        cleanup = []
        if members:
            try: os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            for _ in range(100):
                scan = subprocess.check_output(['ps','-axo','pid=,pgid=,stat=,comm='], text=True)
                cleanup = [line for line in scan.splitlines() if len(line.split()) >= 3 and line.split()[1] == str(p.pid)]
                if not cleanup: break
                time.sleep(.05)
        (out / (label + '.ownership.json')).write_text(json.dumps(dict(process_group=p.pid,timed_out=timed_out,members_after_exit=members,members_after_cleanup=cleanup),indent=2)+'\n')
        assert not timed_out and not members and not cleanup, ('unexpected fixture cleanup', str(out))
    (out / (label + '.command.json')).write_text(json.dumps(dict(argv=argv, returncode=p.returncode), indent=2)+'\n')
    if p.returncode:
        raise AssertionError((label, p.returncode, str(out / (label + '.log'))))

def check(r, variant, mode):
    events = r['events']
    closes = [e for e in events if e['event'] == 'evidence_close']
    if mode == 'spawn_failure':
        assert 'spawnFailed' in r['worker']['error']
        assert not r['readbacks'] and not r['validator']
        assert len(closes) == 1 and closes[0]['rc'] == 0
        assert not r['original_open_after_return']
        return
    if variant == 'noclear':
        assert r['original_fd'] == 3, 'self-dup not reached'
        assert r['worker']['reaped'] and r['worker']['independently_confirmed_host_reap'], 'characterized child not reaped'
        assert r['worker_receipt'], 'entry receipt absent'
        return
    w, v = r['worker'], r['validator']
    assert w['independently_confirmed_host_reap'], 'host reap not independently confirmed'
    assert w['reaped'] and w['exit_code'] == 0 and w['applied'] and w['done'], 'worker did not complete'
    assert w['acknowledged'] and w['ownership'], 'ordinary release/ack lost'
    assert v['reaped'] and v['exit_code'] == 0, 'observer not reaped cleanly'
    host = [x for x in r['readbacks'] if x['same_host_object']]
    decoy = [x for x in r['readbacks'] if x['same_decoy_object']]
    assert len(decoy) == 1 and decoy[0]['fd'] == r['decoy_fd'], 'positive decoy challenge missing'
    assert not decoy[0]['same_host_object'] and decoy[0]['host_value'] == 0, 'decoy mistaken for evidence'
    assert all(x['token'] != 0 for x in r['readbacks']), 'challenge token absent'
    assert len(host) == (1 if variant == 'baseline' else 0), 'same evidence reference inheritance'
    if host:
        assert host[0]['fd'] == r['original_fd'], 'wrong inherited reference'
        assert not host[0]['same_decoy_object'], 'host confused with decoy'
    observed = {x['fd']: x for x in r['validator_receipt']['fds']}
    for x in host + decoy:
        assert observed[x['fd']]['access_mode'] == 2 and observed[x['fd']]['mapped'] == 1, 'not writable mapping authority'
    if variant in ('close', 'naive'):
        assert r['sentinel_fd'] == r['original_fd'], 'exact descriptor reuse not forced'
        assert r['sentinel_open_after_return'] == (variant == 'close'), 'close-once ownership'
        assert len(closes) == (1 if variant == 'close' else 2), 'unexpected close count'
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


def run(out):
    assert not out.exists(), 'fresh output required'
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASE
    out.mkdir(parents=True)
    package = out / 'runner'
    shutil.copytree(ROOT / 'runner/Sources', package / 'Sources')
    shutil.copyfile(ROOT / 'runner/Package.swift', package / 'Package.swift')
    snapshots = out / 'source'; snapshots.mkdir()
    for source in HERE.iterdir():
        if source.is_file(): shutil.copyfile(source, snapshots / source.name)
    source_manifest = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/'runner/Sources').rglob('*')) if p.is_file()}
    source_manifest['runner/Package.swift'] = digest(ROOT/'runner/Package.swift')
    source_manifest.update({str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/'controller/tools/pw_probe_runner').glob('*.h'))})
    (out/'source-manifest.json').write_text(json.dumps(dict(base_commit=BASE, inputs=source_manifest), indent=2)+'\n')
    path = package/'Sources/PWRunnerCore/CWorker.swift'
    original = path.read_text(); (snapshots/'CWorker.original.swift').write_text(original)
    transformations = []
    def replace(old,new,count=1):
        nonlocal original
        assert original.count(old) == count, (old, original.count(old), count)
        original = original.replace(old,new)
        transformations.append(dict(old=old,new=new,count=count))
    replace('let shmFD = shmName.withCString', 'var shmFD = shmName.withCString')
    replace('return pw_cworker_shm_open_create(cName, 0o600)', 'return probeShm(cName, 0o600)')
    replace('close(shmFD)', '_ = probeClose(shmFD)', 4)
    replace('        _ = probeClose(shmFD)\n    }\n\n    // Zero the region.', '        if shmFD >= 0 { _ = probeClose(shmFD) }\n    }\n\n    // Zero the region.')
    replace('    _ = fcntl(shmFD, F_SETFD, 0)', '    if probeVariant != "noclear" { _ = fcntl(shmFD, F_SETFD, 0) }')
    replace('    storeRelease(rawBase, offset: PWShmLayout.preparedOffset, 1)', '    storeRelease(rawBase, offset: PWShmLayout.preparedOffset, 1)\n    probePrepared(base)')
    replace('    // The transfer calls (clock, write, poll) are one injection point:', '''    // Disposable ownership prototypes, selected only in this test executable.
    probeChildSpawned(pid)
    if probeVariant == "close" || probeVariant == "naive" {
        _ = probeClose(shmFD)
        if probeVariant == "close" { shmFD = -1 }
    } else if probeVariant == "cloexec" {
        precondition(fcntl(shmFD, F_SETFD, FD_CLOEXEC) == 0)
    }
    probeAfterSpawn(shmFD)
    // The transfer calls (clock, write, poll) are one injection point:''')
    path.write_text(original); (snapshots/'CWorker.instrumented.swift').write_text(original)
    (out/'transformations.json').write_text(json.dumps(transformations,indent=2)+'\n')
    controls = (HERE/'Probe.swift').read_text()
    controls = controls.replace('var originalFD: Int32', 'var probeVariant = ""\nvar originalFD: Int32')
    controls = controls.replace('func runProbe(_ observer: String, _ mode: String) throws {', 'func runProbe(_ observer: String, _ variant: String, _ mode: String) throws {\n    probeVariant = variant')
    (package/'Sources/PWRunnerCore/Probe.swift').write_text(controls)
    main=package/'Tests/PWRunnerCoreTests/main.swift'; main.parent.mkdir(parents=True)
    main.write_text('import Foundation\n@testable import PWRunnerCore\ntry runProbe(CommandLine.arguments[1], CommandLine.arguments[2], CommandLine.arguments[3])\n')
    worker=ROOT/'dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
    observer=out/'observer'
    command(out,'observer-build',['clang','-Wall','-Wextra','-Werror','-I'+str(ROOT/'controller/tools/pw_probe_runner'),'-DREAL_WORKER="'+str(worker)+'"',str(HERE/'observer.c'),'-o',str(observer)])
    command(out,'core-build',['swift','build','--package-path',str(package),'--product','PWRunnerCoreTests'])
    binary=Path(subprocess.check_output(['swift','build','--package-path',str(package),'--show-bin-path'],text=True).strip())/'PWRunnerCoreTests'
    (out/'equipment.json').write_text(json.dumps(dict(worker=str(worker),worker_sha256=digest(worker),observer_sha256=digest(observer),host_sha256=digest(binary),uname=subprocess.check_output(['uname','-a'],text=True).strip()),indent=2)+'\n')
    results=[]; receipts={}
    cases=[(v,m) for v in ('baseline','close','cloexec') for m in ('high','self','extension_delivery','spawn_failure')]
    cases += [('naive','high'),('noclear','self')]
    for variant,mode in cases:
        label=variant+'-'+mode; case=out/label; case.mkdir()
        command(case,'run',[str(binary),str(observer),variant,mode],cwd=case)
        r=json.loads((case/'receipt.json').read_text())
        for role in ('worker','validator'):
            f=case/(role+'.json')
            r[role+'_receipt']=json.loads(f.read_text()) if f.exists() else None
        (case/'joined.json').write_text(json.dumps(r,indent=2)+'\n')
        check(r,variant,mode); receipts[label]=r
        results.append(dict(case=label,passed=True,host_references=sum(x['same_host_object'] for x in r['readbacks']),sentinel_survived=r['sentinel_open_after_return']))
    mutations=[
        ('baseline-high','missing positive decoy',lambda r:r.update(readbacks=[x for x in r['readbacks'] if not x['same_decoy_object']])),
        ('close-high','decoy mislabeled same object',lambda r:r['readbacks'][0].update(same_host_object=True)),
        ('baseline-high','removed native write authority',lambda r:[x.update(access_mode=0) for x in r['validator_receipt']['fds']] ),
        ('close-high','reuse sentinel closed',lambda r:r.update(sentinel_open_after_return=False)),
        ('close-high','reuse not established',lambda r:r.update(sentinel_fd=-1)),
        ('baseline-high','worker delivery missing',lambda r:[x.update(mapped=0) for x in r['worker_receipt']['fds'] if x['fd']==3]),
    ]
    for name,label,mutate in mutations:
        r=copy.deepcopy(receipts[name]);mutate(r)
        try:check(r,*name.split('-'))
        except AssertionError as e:results.append(dict(rejected_control=label,reason=str(e)))
        else:raise AssertionError((label,'counterexample accepted'))
    assert digest(worker)==json.loads((out/'equipment.json').read_text())['worker_sha256']
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__': run(Path(sys.argv[1]).resolve())
