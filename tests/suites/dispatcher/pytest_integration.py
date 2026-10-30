"""Isolated actual-family faults and independent expected observations."""
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner
import artifact
import execution_contract
import pytest_packages
import pytest_family
import release_accept
import release_runs
from pytest_support import read, write, digest, value_digest

F = 'runner_c_worker_harness/exec_control_states'
MODULE = 'tests/suites/runner_c_worker_harness/test_exec_control_states.py'
DOMAIN = 'tests/suites/runner_c_worker_harness/exec_domain.py'


def require(value, message):
    if not value:
        raise AssertionError(message)


class Integration:
    def __init__(self, out, note):
        self.out, self.note = out, note
        self.normal = None

    def fixture(self, name):
        root = self.out / name / 'repo'
        cases = {'runner_c_worker_harness':dict(cases=[dict(id='exec_control_states',engine='pytest',module=MODULE,requires=[])]),
                 'sentinel':dict(command=['bash','tests/suites/sentinel/run.sh'],cases=['later'])}
        install_runner(ROOT, root, cases)
        paths = [*['tests/lib/'+n for n in ('pytest_engine.py','pytest_command_owner.py')],
                 'tests/pytest.ini','tests/requirements-pytest.lock', MODULE, DOMAIN,
                 'tests/suites/runner_c_worker_harness/check_exec_evidence.py',
                 'tests/fixtures/worker_lifecycle/exec_control.c','tests/fixtures/worker_lifecycle/exec_call_policy.json']
        paths += [str(p.relative_to(ROOT)) for p in (ROOT/'controller/tools/pw_probe_runner').glob('*') if p.suffix in ('.h','.c')]
        for relative in paths:
            target = root / relative; target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
        target,_ = pytest_packages.target(ROOT)
        shutil.copytree(target,root/target.relative_to(ROOT))
        script = root/'tests/suites/sentinel/run.sh';script.parent.mkdir(parents=True)
        script.write_text('#!/bin/bash\nset -euo pipefail\nsource tests/lib/case.sh\ntest_begin sentinel later\nprintf observed > "$PW_TEST_ARTIFACTS/external-start"\ntest_pass "independent later case completed"\n');script.chmod(0o755)
        return root

    def run(self, root, name='run', args=(), expected=0, environment=None):
        env={k:v for k,v in os.environ.items() if not k.startswith(('PW_', 'PYTEST','PYTHON'))}
        env.update(PW_TEST_OUT_DIR='tests/out/runs/'+name)
        if environment: env.update(environment)
        result=subprocess.run(['bash','tests/run.sh',*args],cwd=root,env=env,capture_output=True,timeout=90)
        folder=root.parent/(name+'-invocation');folder.mkdir()
        (folder/'stdout').write_bytes(result.stdout);(folder/'stderr').write_bytes(result.stderr)
        write(folder/'command.json',dict(argv=list(args),returncode=result.returncode))
        require(result.returncode==expected,f'{root.parent.name}: expected {expected}, got {result.returncode}: {result.stderr.decode()[-2000:]}')
        out=root/'tests/out/runs'/name
        return out, read(out/'run.json') if (out/'run.json').exists() else None

    def fault(self, name, relative, before, after, expected=1):
        root=self.fixture(name);p=root/relative;s=p.read_text();require(s.count(before)==1,'fault anchor '+name);p.write_text(s.replace(before,after))
        out,run=self.run(root,expected=expected)
        require(run['case_results'][-1]['id']=='sentinel/later' and run['case_results'][-1]['status']=='pass','independent later work suppressed')
        require(run['ok'] is False,'fault was accepted')
        family=read(out/'suites'/F/'family.json')
        require(read(out/'suites'/F/'ownership.json')['closed'],'fault left command ownership unresolved')
        return root,out,run,family

    def native(self):
        root=self.fixture('integrated-normal')
        before=artifact.inventory(root)
        self.run(root,'list',args=('--list',))
        require(before==artifact.inventory(root),'--list changed fixture checkout')
        out,run=self.run(root)
        require(run['ok'] and len(run['case_results'])==2,'normal parent account')
        family=read(out/'suites'/F/'family.json')
        require(len(family['items'])==9 and all(i['outcome']=='passed' for i in family['items']),'nine ordinary items')
        require(len(read(out/'suites'/F/'artifacts/production/observed-call-policy.json'))==58,'native sequence lost')
        self.normal=(root,out,run,family)
        self.note('actual family normal and read-only collection', output=str(out))
        root,out,run,family=self.fault('formation',DOMAIN,"MARKER = '    slot->exec_valid = 1;'","MARKER = 'absent boundary'")
        require([i['outcome'] for i in family['items']]==['passed']+['failed']*6+['passed']*2,'formation outcomes')
        require(all('mutation not submitted' in i['phases']['call']['diagnostic'] for i in family['items'][1:7]),'formation diagnosis missing')
        self.note('formation fails distinctly from native rejection',output=str(out))
        root,out,run,family=self.fault('accepted-mutation',DOMAIN,"'slot->exec_leader_exit_observed = reaped == child;'","'(void)slot;'")
        require('accepted mutation' in family['items'][1]['phases']['call']['diagnostic'],'wrong acceptance concealed')
        self.note('accepted mutation refused by designated body expectation',output=str(out))
        root,out,run,family=self.fault('wrong-rejection',DOMAIN,"'slot->exec_leader_exit_observed = reaped == child;'","'slot->exec_group_rc = 42;'")
        require('outside its designated oracle' in family['items'][1]['phases']['call']['diagnostic'],'wrong rejection credited')
        self.note('wrong native rejection remains a failed control',output=str(out))
        root=self.fixture('baseline');golden=root/'tests/fixtures/worker_lifecycle/exec_call_policy.json';v=read(golden);v['attempts'][0]['sha256']='0'*64;write(golden,v)
        out,run=self.run(root,expected=1);family=read(out/'suites'/F/'family.json')
        require(family['items'][0]['phases']['call']['outcome']=='failed','baseline body failure missing')
        require(all(i['phases']['setup']['outcome']=='failed' and 'call' not in i['phases'] for i in family['items'][1:]),'baseline dependents ran')
        require(len(read(out/'suites'/F/'ownership.json')['commands'])==2,'mutant command started after bad baseline')
        require('SHARED BASELINE' in (out/'suites'/F/'summary.txt').read_text(),'shared baseline display absent')
        self.note('shared baseline cause retains observation and eight unattempted bodies',output=str(out))
        for kind,before,after in [
            ('input-finalizer',"        after = inventory(self.inputs)","        (self.inputs / 'pw_worker_exec.h').write_text('changed fixture input')\n        after = inventory(self.inputs)"),
            ('cleanup-finalizer',"        assert not changed,", "        raise RuntimeError('controlled ordinary fixture cleanup failure')\n        assert not changed,")]:
            root,out,run,family=self.fault(kind,DOMAIN,before,after)
            require(all(i['phases']['call']['outcome']=='passed' for i in family['items']),'finalizer erased body outcomes')
            require(family['items'][-1]['phases']['teardown']['outcome']=='failed','last teardown diagnosis absent')
            summary=(out/'suites'/F/'summary.txt').read_text()
            require('SHARED SESSION FINALIZER' in summary and 'all family items' in summary,'shared scope display absent')
            self.note(kind+' preserves body outcomes and explicitly displays scope',output=str(out))
        root,out,run,family=self.fault('body-and-teardown',MODULE,"    assert result['ok'], result['error']", "    assert False, 'controlled body failure'")
        # Separate source fixture: add function finalizer to that same body-failing item.
        # The first run is already sealed; use a new copied arrangement instead.
        root=self.fixture('both-phases')
        module=root/MODULE;s=module.read_text().replace("    assert result['ok'], result['error']","    assert False, 'controlled body failure'")
        s+='''\n@pytest.fixture(autouse=True)\ndef controlled_teardown(request):\n    yield\n    if request.node.get_closest_marker('pw_id').args[0] == 'production':\n        raise RuntimeError('controlled teardown failure')\n''';module.write_text(s)
        out,run=self.run(root,expected=1);family=read(out/'suites'/F/'family.json')
        require(family['items'][0]['phases']['call']['outcome']=='failed' and family['items'][0]['phases']['teardown']['outcome']=='failed','one failure overwrote another')
        self.note('same item body and teardown failures both survive',output=str(out))
        root,out,run,family=self.fault('setup-acquired',MODULE,'    value = Observation(pw_equipment)',"    pw_equipment.command(['/bin/echo','acquired'], pw_equipment.artifacts / 'acquired', 5)\n    raise RuntimeError('setup failed before yield')\n    value = Observation(pw_equipment)")
        require(all(i['phases']['setup']['outcome']=='failed' for i in family['items']),'setup failure obscured')
        self.note('setup command settles before failed yield; independent later work proceeds',output=str(out))

    def discovery(self):
        for name,before,after in [('syntax','import pytest','import )'),('duplicate',"pytest.mark.pw_id(m.name)","pytest.mark.pw_id('production')"),('empty',"import pytest","import pytest\npytest.skip('controlled empty module',allow_module_level=True)")]:
            root=self.fixture('collection-'+name);p=root/MODULE;p.write_text(p.read_text().replace(before,after));protected=root/'tests/out/runs/run';protected.mkdir(parents=True);(protected/'sentinel').write_text('preserve')
            before=artifact.inventory(root);out,run=self.run(root,expected=2)
            require(run is None and artifact.inventory(root)==before,'collection failed after protected-state mutation')
            require(not (root/'tests/out/pytest-owners').exists(),'collection acquired command equipment')
            self.note('collection '+name+' refuses before output replacement',output=str(root.parent))
        root=self.fixture('missing-packages');shutil.rmtree(root/'.tmp/pytest');out,run=self.run(root,expected=1)
        parent=run['case_results'][0];require(parent['execution_state']=='not_started' and parent['accounting_state']=='unavailable','missing equipment parent state')
        require(run['case_results'][1]['status']=='pass','missing engine suppressed legacy case')
        self.note('missing engine equipment visible as not_started/unavailable with legacy continuation',output=str(out))

    def accounting(self):
        root,out,run,family=self.normal;folder=out/'suites'/F
        manifest=read(folder/'selection.json');ownership=read(folder/'ownership.json');raw=(folder/'phases.jsonl').read_text();lines=raw.splitlines()
        for name,value in [('truncated', '\n'.join(lines[:-3])+'\n{"kind":'),('missing-finish','\n'.join(lines[:-1])+'\n'),('contradictory', raw+json.dumps(dict(kind='session_finish',exitstatus=0))+'\n')]:
            path=self.out/(name+'.jsonl');path.write_text(value)
            result=pytest_family.account(manifest,path,0,ownership,family['operations'])
            write(self.out/(name+'-subject.json'),result)
            require(not result['ok'] and result['accounting_state']=='incomplete','incomplete stream accepted '+name)
            require(all(i['outcome']=='passed' for i in result['items'][:8]),'valid earlier evidence discarded '+name)
        self.note('valid prefix survives truncated, absent and contradictory terminal evidence')

    def portable(self):
        root,out,run,family=self.normal
        expected=run['execution_contract'];anchor=value_digest(expected)
        acceptance=self.out/'portable-source';shutil.copytree(out,acceptance/'tests')
        write(acceptance/'acceptance.json',dict(schema_version=3,ok=True,execution_contract=expected))
        entry=dict(path='release-acceptance/fixture',run_id=run['run_id'],source='0'*40,app_inventory=None,reason='controlled portable family')
        valid=self.out/'portable-valid'
        release_runs.pack(valid,tag='v0.0.0',source='0'*40,runs={'acceptance':(acceptance,entry)},battery=('acceptance','tests/run.json'),expected_contract=expected)
        # Each altered archive is fully repacked and re-inventoried. The expected
        # contract stays outside its source tree and mutable checksum records.
        for name in ('engine-reference','all-hints','ownership-role','empty-operations','contract-copy'):
            source=self.out/('portable-source-'+name);shutil.copytree(acceptance,source)
            result=read(source/'tests/run.json');fpath=source/'tests/suites'/F
            if name=='engine-reference':
                del result['case_results'][0]['engine'];del result['case_results'][0]['family_report']
            elif name=='all-hints':
                result.pop('execution_contract');result['case_results']=result['case_results'][1:];shutil.rmtree(fpath)
            elif name=='ownership-role':
                (fpath/'ownership.json').unlink()
                result['case_results'][0].pop('ownership_report',None)
            elif name=='empty-operations':
                f=read(fpath/'family.json');f['operations']=[];write(fpath/'family.json',f)
                o=read(fpath/'ownership.json');o['commands']=[];write(fpath/'ownership.json',o)
            write(source/'tests/run.json',result)
            target=self.out/('portable-'+name);target.mkdir()
            with tarfile.open(target/'runs.tar.gz','w:gz',dereference=False) as archive:archive.add(source,arcname='acceptance')
            manifest=read(valid/'manifest.json');manifest['runs']['acceptance']['inventory']=artifact.inventory(source);manifest['sha256']=digest(target/'runs.tar.gz')
            for summary,origin in [('acceptance.json',source/'acceptance.json'),('battery.json',source/'tests/run.json')]:
                shutil.copyfile(origin,target/summary);manifest['summaries'][summary]=digest(target/summary)
            if name=='contract-copy':manifest.pop('execution_contract');manifest['schema_version']=2
            write(target/'manifest.json',manifest)
            try:release_runs.verify_bundle(target,expected_contract=expected)
            except (ValueError,KeyError) as exc:
                require('checksum' not in str(exc) and 'inventory' not in str(exc),'transport failed before semantic control')
                write(target/'rejection.json',dict(reason=str(exc),expected_identity=anchor))
            else:raise AssertionError('portable missing evidence accepted: '+name)
            require(value_digest(expected)==anchor,'independent expectation changed')
        # The valid portable family has no dependency on its local registry.
        release_runs.verify_bundle(valid,expected_contract=expected)
        self.note('portable semantic deletion controls reject after repaired transport hashes',expected_identity=anchor,output=str(valid))

    def recovery(self):
        import checkout_lock
        import pytest_resources as resources
        from repository import completed_output
        for state in ('reserved','owner_launch_authorized','owner_bound','command_release_authorized','command_started'):
            root=self.fixture('recovery-'+state);out=root/'tests/out/runs/pending';completed_output(out)
            with checkout_lock.owned(root,env={}) as scope:
                path=resources.reserve(root,out,state,F,F+'::production',['/bin/echo','never invoked'],out/'artifacts',5,scope,os.getpid())
                if state!='reserved':resources.transition(path,state,owner_pid=os.getpid(),command_pid=os.getpid())
            before=path.read_bytes()
            self.run(root,'preview',args=('--recover-ownership',state))
            require(path.read_bytes()==before,'recovery preview changed reservation')
            _,_=self.run(root,'recover',args=('--recover-ownership',state,'--apply'),expected=0 if state=='reserved' else 1)
            if state=='reserved':
                require(read(path)['state']=='closed','unlaunched reservation did not close')
            else:
                require(path.read_bytes()==before,'historical PID/ambiguous authorization altered')
                # This fixture never calls a launcher. The same refusal applies
                # to the live crash window where the missing publication is ambiguous.
                _,r=self.run(root,'admission',args=('--case','sentinel/later'),expected=2)
                require(r is None,'unknown ownership admitted an execution')
                self.run(root,'prune',args=('--prune','--apply'))
                require(out.exists(),'pruning removed an ambiguous ownership run')
            self.note('recovery disposition '+state,record=str(path),actual_launch=False)
        root=self.fixture('recovery-settled');out=root/'tests/out/runs/pending';completed_output(out)
        with checkout_lock.owned(root,env={}) as scope:
            command=resources.Command(root,out,'settled',F,F+'::production',['/bin/echo','completed'],out/'artifacts',5,scope,os.getpid())
            command.process.wait(timeout=10);command.gate.close()
            for log in command.logs:log.close()
        require(read(command.path)['state']=='quiescent_retained','missing durable settlement')
        self.run(root,'later',args=('--case','sentinel/later'))
        self.run(root,'prune-before',args=('--prune','--apply'))
        require(out.exists(),'quiescent held output was pruned')
        self.run(root,'recover',args=('--recover-ownership','settled','--apply'))
        self.run(root,'recover-again',args=('--recover-ownership','settled','--apply'))
        self.run(root,'prune-after',args=('--prune','--apply'))
        require(not out.exists(),'closed unpinned output not pruned')
        self.note('post-command pre-closure recovery admits independent work and protects output until closure')

    def deaths(self):
        import select
        import checkout_lock
        import pytest_resources as resources
        for mode in ('engine','interrupt','both'):
            root=self.fixture('death-'+mode)
            directory=Path('/private/tmp')/('pw-exec-observe-'+mode+'-'+str(os.getpid()));directory.mkdir()
            listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(directory/'peer'));listener.listen(4);listener.settimeout(20)
            native="import os,socket,sys,time,signal; child=os.fork(); s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1]); s.sendall(b'child' if child==0 else b'command'); signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(60)"
            injected="""    if mutation.name == 'collection_from_final_reap':
        import socket, sys
        peer=socket.socket(socket.AF_UNIX); peer.connect(ENDPOINT); peer.sendall(b'engine')
        baseline.equipment.command([sys.executable,'-B','-S','-P','-c',NATIVE,ENDPOINT],baseline.equipment.artifacts/'active-command',60)
""".replace('ENDPOINT',repr(str(directory/'peer'))).replace('NATIVE',repr(native))
            module=root/MODULE;module.write_text(module.read_text().replace('    baseline.mutation(mutation)',injected+'    baseline.mutation(mutation)'))
            env={k:v for k,v in os.environ.items() if not k.startswith(('PW_','PYTEST','PYTHON'))};env['PW_TEST_OUT_DIR']='tests/out/runs/death'
            log=(root.parent/'invocation.log').open('wb')
            process=subprocess.Popen(['bash','tests/run.sh'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            queue=select.kqueue();peers=[];pids={};exits=set()
            try:
                for _ in range(3):
                    peer,_=listener.accept();peers.append(peer);pid=peer.getsockopt(0,2);role=peer.recv(32).decode();pids[role]=pid
                    queue.control([select.kevent(pid,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD|select.KQ_EV_ONESHOT,fflags=select.KQ_NOTE_EXIT)],0,0)
                require(set(pids)=={'engine','command','child'},'independent start identities missing')
                out=root/'tests/out/runs/death';folder=out/'suites'/F
                events=[json.loads(line) for line in (folder/'phases.jsonl').read_text().splitlines()]
                require(sum(e['kind']=='item_finish' for e in events)==1,'completed/active/queued arrangement not established')
                if mode=='interrupt':process.send_signal(signal.SIGINT)
                else:
                    os.kill(pids['engine'],signal.SIGKILL)
                    if mode=='both':process.kill()
                with checkout_lock.preview(root) as held:require(held,'owned descendant lost lock before exit')
                process.wait(timeout=20)
                deadline=time.monotonic()+20
                while len(exits)<3 and time.monotonic()<deadline:
                    exits.update(e.ident for e in queue.control(None,3,1) if e.fflags & select.KQ_NOTE_EXIT)
                require(exits==set(pids.values()),'independent descendant/engine exit observation missing')
                if mode!='both':
                    run=read(out/'run.json');parent=run['case_results'][0]
                    require(parent['execution_state']=='started' and parent['accounting_state']=='incomplete' and not run['ok'],'death ordinary parent display conceals incomplete execution')
                    result=read(folder/'family.json')
                    require(result['items'][0]['outcome']=='passed' and not result['items'][2]['started'],'completed/queued evidence misclassified')
                    require(run['case_results'][1]['status']==('pass' if mode=='engine' else None),'independent continuation/cancellation changed')
                    require('execution=started accounting=incomplete' in (folder/'summary.txt').read_text(),'ordinary display missing started/incomplete')
                else:
                    require(not (out/'run.json').exists(),'killed supervisor published successful run')
                    run_id=read(out/'owner.json')['run_id']
                    result=resources.recover(root,run_id,apply=True)
                    require(not result['unresolved'],'dual-death recovery did not close observed quiescence')
                self.note('independent '+mode+' loss observations',pids=pids,kernel_exits=sorted(exits),output=str(out))
            finally:
                if process.poll() is None:process.kill();process.wait()
                queue.close();log.close()
                for peer in peers:peer.close()
                listener.close();(directory/'peer').unlink();directory.rmdir()

    def all(self):
        self.native();self.discovery();self.accounting();self.portable();self.recovery();self.deaths()
