"""Independent experimental driver. Never imports candidate accounting code.

Selection expectations are literals; body/resource receipts and OS observations
are read separately from the candidate's terminal interpretation. The driver
holds no checkout lock across a candidate invocation.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PYTHON = '/private/tmp/pw-pytest-boundary-venv/bin/python'
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import TreeControl, ExitObserver
sys.path.insert(0, str(ROOT / 'tests/lib'))
import checkout_lock
import retention


def require(value, message):
    if not value:
        raise AssertionError(message)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines()] if Path(path).exists() else []


def wait_for(predicate, description, timeout=8):
    deadline = time.monotonic() + timeout
    while not predicate():
        require(time.monotonic() < deadline, 'timeout: ' + description)
        time.sleep(0.02)


def held():
    fd = os.open(ROOT / 'tests/.checkout.lock', os.O_RDWR)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)


def snapshot(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file()}


def base_env(witness, mode, control):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('PW_', 'PYTHON', 'PYTEST', 'BOUNDARY_'))}
    env.update(BOUNDARY_ROOT=str(ROOT), BOUNDARY_WITNESS=str(witness), BOUNDARY_MODE=mode,
               CONTROL_CANCEL_SOCKET=control, PYTEST_ADDOPTS='--maxfail=1', PYTHONPATH='/nonexistent-poison')
    return env


def invoke(equipment, out, witness, mode, control, options, logs):
    command = [PYTHON, '-B', '-I', str(equipment / 'supervisor.py'), '--out', str(out),
               '--python', PYTHON, str(HERE / 'test_subject.py')] + options
    (logs / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    return subprocess.Popen(command, cwd=HERE, env=base_env(witness, mode, control),
                            stdin=subprocess.DEVNULL, stdout=(logs / 'stdout').open('wb'),
                            stderr=(logs / 'stderr').open('wb'), start_new_session=True)


def mutant(root, name, filename, before, after):
    path = root / 'equipment' / name
    path.mkdir(parents=True)
    for p in HERE.iterdir():
        if p.suffix in ('.py', '.ini'):
            shutil.copy2(p, path / p.name)
    target = path / filename
    text = target.read_text()
    require(text.count(before) == 1, 'mutation anchor: ' + name)
    target.write_text(text.replace(before, after))
    return path


def exercise(root, name, mode=None, equipment=HERE):
    mode = mode or name
    work = root / 'observations' / name
    work.mkdir(parents=True)
    witness = work / 'witness'
    witness.mkdir()
    out = root / 'candidates' / name
    observation = dict(name=name, mode=mode, credited_cleanup=False)
    active = name in ('normal', 'setup_failure', 'double_failure', 'interrupt', 'engine_death',
                      'both_death', 'dropped_lock')
    options = ['-k', 'not environment']
    if name in ('selection', 'preview', 'existing', 'retained'):
        options = ['-k', 'completed or queued']
    if name == 'preview':
        options += ['--collect-only']
    if name == 'environment':
        options = ['-k', 'environment']
    if name == 'deselect':
        options += ['--deselect', 'test_subject.py::test_active']
    if name in ('existing', 'retained'):
        out.mkdir(parents=True)
        (out / 'preserve.bin').write_bytes(b'preserve exactly\x00\xff')
        before = snapshot(out)
        if name == 'retained':
            with checkout_lock.owned(ROOT, env={}):
                index = retention.read_object(ROOT / 'tests/RETAINED.json')
                index['runs'].append(dict(path=str(out.relative_to(ROOT / 'tests/out')), run_id=name,
                                         source=None, app_inventory=None, reason='Experimental retained-publication refusal stimulus.'))
                retention.write_index(ROOT, index)
    process, engine_observer = None, ExitObserver()
    socket_dir = tempfile.mkdtemp(prefix='pw-py-observe-', dir='/private/tmp')
    tree = TreeControl(Path(socket_dir) / 'gate')
    try:
        inode = (ROOT / 'tests/.checkout.lock').stat().st_ino
        process = invoke(equipment, out, witness, mode, tree.path, options, work)
        if active:
            peers = tree.accept(timeout=10)
            observation['peers'] = peers
            tree.assert_running()
            engine = read(out / 'engine.json')['pid']
            require(engine == peers['P'], 'body peer is not the engine')
            engine_observer.watch(engine)
            require(held(), 'candidate did not take checkout hold')
            resource = read(out / 'resources/0/record.json')
            require(Path(resource['resource']).read_bytes() == b'owned resource\n', 'resource not acquired')
            acquired = rows(witness / 'resource.jsonl')
            require(len(acquired) == 1 and acquired[0]['intent']['state'] == 'launched', 'no prior ownership at acquisition')
            require(acquired[0]['pid'] == peers['C'] and acquired[0]['lock_inode'] == inode, 'resource/lock identity mismatch')
            require(acquired[0]['stdin'] == '', 'resource inherited stdin')
            os.kill(peers['C'], signal.SIGINT)
            tree.assert_running()
            observation['helper_survived_direct_sigint'] = True
            if name in ('normal', 'setup_failure', 'double_failure'):
                tree.peers['P'].sendall(b'q')  # Only stimulus release, not child cleanup.
            elif name == 'interrupt':
                os.kill(process.pid, signal.SIGINT)
            elif name == 'engine_death':
                os.kill(engine, signal.SIGKILL)
            else:
                os.kill(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
                os.kill(engine, signal.SIGKILL)
                engine_observer.assert_stopped()
                tree.ping('C')
                observation['held_with_only_child'] = held()
                if name == 'dropped_lock':
                    require(not observation['held_with_only_child'], 'drop mutation did not expose free lock')
                    observation['lifetime_control_rejected'] = True
                    tree.peers['C'].sendall(b'q')
                    tree.observer.assert_stopped()
                    observation['outside_safety_cleanup'] = True
                    Path(resource['resource']).unlink()
                    Path(resource['socket_dir']).rmdir()
                else:
                    require(observation['held_with_only_child'], 'protected child lost checkout hold')
                    require(not (out / 'run.json').exists(), 'dead supervisor invented completion')
                    competitor = work / 'competitor'
                    competitor.mkdir()
                    other = invoke(HERE, root / 'candidates/competitor', competitor, 'selection', tree.path,
                                   ['-k', 'completed'], competitor)
                    require(other.wait(timeout=8) != 0, 'competing execution admitted')
                    require(not (competitor / 'starts.jsonl').exists(), 'competing body started')
                    wait_for(lambda: bool(rows(out / 'resources/0/observations.jsonl')), 'resource observes engine exit')
                    recovered = subprocess.run([PYTHON, '-B', '-I', str(HERE / 'recover.py'), str(out)],
                                               env=base_env(witness, mode, tree.path), capture_output=True, timeout=10)
                    (work / 'recovery.stdout').write_bytes(recovered.stdout)
                    (work / 'recovery.stderr').write_bytes(recovered.stderr)
                    require(recovered.returncode == 0, 'recovery failed: ' + recovered.stderr.decode())
                    tree.assert_stopped()
                    require(not Path(resource['resource']).exists(), 'recovery removed no resource')
                    observation['credited_cleanup'] = True
            if name != 'dropped_lock':
                code = process.wait(timeout=12)
                tree.assert_stopped()
                require(not Path(resource['resource']).exists(), 'resource remained after candidate cleanup')
                observation['credited_cleanup'] = True
        else:
            code = process.wait(timeout=12)
        observation['returncode'] = process.returncode
        require(not held(), 'checkout hold remains after owned processes exit')
        require((ROOT / 'tests/.checkout.lock').stat().st_ino == inode, 'lock inode replaced')
        starts = [r['stage'] for r in rows(witness / 'starts.jsonl')]
        observation['starts'] = starts
        if name in ('collection_error', 'duplicate', 'publication_failure', 'existing', 'retained', 'preview'):
            require(not starts, 'body or fixture started before eligibility')
            require(process.returncode == 0 if name == 'preview' else process.returncode != 0, 'wrong publication result')
            require(not (out / 'run.json').exists(), 'publication failure/preview invented terminal result')
            if name == 'preview':
                listing = (work / 'stdout').read_text()
                require('test_completed' in listing and 'test_queued' in listing and 'test_active' not in listing,
                        'preview did not describe pytest selection')
            if name in ('existing', 'retained'):
                require(snapshot(out) == before, 'refusal changed existing evidence')
        elif name == 'dropped_lock':
            require(starts == ['completed.body', 'active.setup', 'active.body'], 'drop stimulus starts')
        else:
            run = read(out / 'run.json')
            reports = rows(out / 'reports.jsonl')
            expected_ok = name in ('normal', 'selection', 'deselect', 'environment')
            require(run['ok'] is expected_ok, 'candidate summary contradicted declared expectation')
            require((process.returncode == 0) is expected_ok, 'candidate exit contradicted declared expectation')
            if name in ('selection', 'deselect'):
                require(starts == ['completed.body', 'queued.body'], 'pytest selection not applied')
            elif name == 'environment':
                require(starts == ['environment.body'], 'environment selection')
                helper = read(witness / 'helper.stdout')
                require(helper['env'] == {'LC_ALL':'C','LANG':'C','BOUNDARY_SENTINEL':'exact',
                                         '__CF_USER_TEXT_ENCODING':f'0x{os.getuid():X}:0x0:0x0'}, 'helper environment drift')
                require(Path(helper['executable']).resolve() == Path('/opt/homebrew/opt/python@3.14/bin/python3.14').resolve(),
                        'subject interpreter changed')
                configuration = read(out / 'engine_configuration.json')
                require(configuration['pytest']=='9.0.2' and configuration['capture']=='fd'
                        and configuration['optimize']==0 and configuration['external_plugins']==[], 'engine configuration drift')
                require(configuration['environment']=={'PYTEST_ADDOPTS':None,'PYTHONPATH':None,
                                                      'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'}, 'ambient engine options leaked')
                require(helper['fds'] == [] and helper['cwd'] == str(witness), 'helper descriptor/cwd drift')
                require(helper['argv'] == ['literal $() ; spaces'] and helper['stdin'] == b'literal\x00input'.hex(), 'helper input drift')
                require((witness / 'helper.stderr').read_bytes() == b'explicit stderr\n', 'helper stderr drift')
                body = [r for r in reports if r.get('when') == 'call'][0]
                require('implicit stdout' in body['stdout'] and 'implicit stderr' in body['stderr'], 'fd capture not observed')
            elif name == 'report_failure':
                require(starts == ['completed.body'], 'report failure continued work')
                require(run['harness_errors'], 'missing report accepted')
            else:
                expected = ['completed.body', 'active.setup']
                if name != 'setup_failure':
                    expected += ['active.body']
                if name in ('normal', 'double_failure', 'interrupt'):
                    expected += ['active.teardown']
                if name in ('normal', 'setup_failure', 'double_failure'):
                    expected += ['queued.body']
                require(starts == expected, 'independent start receipts differ: ' + repr(starts))
                cases = run['case_results']
                require(len(cases) == 3 and cases[0]['status'] == 'pass', 'completed obligation lost')
                require([c['id'].split('::')[-1] for c in cases] == ['test_completed','test_active','test_queued'],
                        'selection accounting identities differ')
                active_reports = [r for r in reports if r.get('nodeid','').endswith('::test_active') and r['kind']=='report']
                if name == 'setup_failure':
                    require([(r['when'],r['outcome']) for r in active_reports] == [('setup','failed'),('teardown','passed')], 'partial setup accounting')
                if name == 'double_failure':
                    failures = [r for r in active_reports if r['outcome']=='failed']
                    require([r['when'] for r in failures] == ['call','teardown'], 'combined phase failure lost')
                    require('distinct body failure' in failures[0]['longrepr'] and 'distinct teardown failure' in failures[1]['longrepr'], 'combined diagnostics lost')
                if name in ('interrupt','engine_death','both_death'):
                    require(cases[1]['status']=='fail' and cases[2]['state']=='unrun', 'incomplete/queued work promoted')
                    require((witness / 'partial.bin').read_bytes()==b'partial observation\x00\xff\n','partial bytes lost')
        observation['ok'] = True
    except BaseException as exc:
        observation['error'] = repr(exc)
        raise
    finally:
        observation['exited_before_safety_cleanup'] = sorted(tree.exits())
        (work / 'observation.json').write_text(json.dumps(observation, indent=2)+'\n')
        tree.close()
        observation['exited_after_safety_cleanup'] = sorted(tree.exited)
        (work / 'observation.json').write_text(json.dumps(observation, indent=2)+'\n')
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        engine_observer.close()
        Path(tree.path).unlink(missing_ok=True)
        Path(socket_dir).rmdir()
    return observation


def accounting(root):
    selected = ['independent/a', 'independent/b']
    events = []
    for node in selected:
        events += [dict(kind='start', nodeid=node)]
        events += [dict(kind='report', nodeid=node, when=phase, outcome='passed') for phase in ('setup','call','teardown')]
    events += [dict(kind='session_finish', exitstatus=0)]
    changes = dict(valid=lambda x:x, missing=lambda x:x[:2]+x[3:], duplicate=lambda x:x[:3]+[x[2]]+x[3:],
                   unexpected=lambda x:x+[dict(kind='start',nodeid='other/c')],
                   reordered=lambda x:x[4:8]+x[:4]+x[8:], missing_finish=lambda x:x[:-1],
                   invalid_outcome=lambda x:[dict(e,outcome='forgotten') if e.get('when')=='call' else e for e in x],
                   unexpected_skip=lambda x:[dict(e,outcome='skipped') if e.get('when')=='call' else e for e in x],
                   unknown_event=lambda x:x+[dict(kind='unrecognized')],
                   duplicated_selection=lambda x:x)
    for name, change in changes.items():
        work = root/'observations'/('accounting_'+name)
        work.mkdir(parents=True)
        data = dict(selection=selected, events=change(copy.deepcopy(events)), engine_code=0, resources=[])
        if name == 'duplicated_selection':
            data['selection'] = selected + [selected[0]]
        (work/'input.json').write_text(json.dumps(data,indent=2)+'\n')
        script = 'import json,sys;sys.path.insert(0,sys.argv[1]);from common import account;d=json.load(open(sys.argv[2]));r,e=account(**d);print(json.dumps(dict(results=r,errors=e,ok=not e and all(x["status"]=="pass" for x in r))))'
        result = subprocess.run([PYTHON,'-B','-I','-c',script,str(HERE),str(work/'input.json')],
                                env={'BOUNDARY_ROOT':str(ROOT)},capture_output=True,timeout=5)
        (work/'stdout').write_bytes(result.stdout)
        (work/'stderr').write_bytes(result.stderr)
        require(result.returncode==0,'accounting equipment failed')
        require(json.loads(result.stdout)['ok'] is (name in ('valid','reordered')), 'accounting accepted malformed evidence:'+name)
    # Constructed finalization input, not a claim about live publication/locking.
    work=root/'observations/accounting_truncated'
    work.mkdir(parents=True)
    retention.atomic_json(work/'owner.json',dict(schema_version=1,run_id='constructed',out_dir=str(work),started_at_unix_ms=1))
    retention.atomic_json(work/'plan.json',dict(cases=[dict(id=n) for n in selected],configuration=dict(out_dir=str(work))))
    (work/'resources').mkdir()
    raw=''.join(json.dumps(e)+'\n' for e in events[:5])+'{"kind":"report","nodeid":'
    (work/'reports.jsonl').write_text(raw)
    script='import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from common import finish;finish(Path(sys.argv[2]),None)'
    result=subprocess.run([PYTHON,'-B','-I','-c',script,str(HERE),str(work)],env={'BOUNDARY_ROOT':str(ROOT)},capture_output=True,timeout=5)
    (work/'stdout').write_bytes(result.stdout)
    (work/'stderr').write_bytes(result.stderr)
    require(result.returncode==0,'truncation finalization crashed')
    summary=read(work/'run.json')
    require(summary['ok'] is False,'truncated journal passed')
    require(summary['case_results'][0]['state']=='completed' and summary['case_results'][0]['status']=='pass',
            'truncated tail discarded a completed item')
    require(summary['case_results'][1]['state']=='unrun','truncated active item completed')
    require(any('journal' in e for e in summary['harness_errors']),'truncation lacks journal diagnostic')
    require((work/'reports.jsonl').read_text()==raw,'truncated raw evidence rewritten')
    return dict(name='accounting',ok=True,controls=[*changes,'truncated_tail'])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',required=True)
    parser.add_argument('--only',nargs='*')
    args=parser.parse_args()
    out=ROOT/'tests/out/runs'/args.name
    started=time.time_ns()//1_000_000
    names=args.only or ['normal','setup_failure','double_failure','interrupt','engine_death','both_death',
                       'selection','deselect','environment','preview','collection_error','duplicate',
                       'publication_failure','report_failure','existing','retained','dropped_lock','accounting']
    with checkout_lock.owned(ROOT,env={}):
        retention.replacement_allowed(ROOT,out,retention.load_index(ROOT))
        require(not out.exists(),'fresh investigation output required')
        out.mkdir(parents=True)
        retention.atomic_json(out/'owner.json',dict(schema_version=1,run_id=args.name,out_dir=str(out),started_at_unix_ms=started))
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (out/'source.json').write_text(json.dumps(dict(commit=source,files=snapshot(HERE)),indent=2)+'\n')
    configuration=dict(out_dir=str(out))
    plan=dict(cases=[dict(id=n) for n in names],configuration=configuration)
    retention.atomic_json(out/'plan.json',plan)
    mutations={
        'duplicate': ('engine.py','ids = [item.nodeid for item in session.items]', 'ids = [item.nodeid for item in session.items]; ids.append(ids[0])'),
        'publication_failure': ('common.py','retention.atomic_json(Path(path), value)', 'if Path(path).name == "plan.json": raise OSError("deliberate plan publication failure")\n    retention.atomic_json(Path(path), value)'),
        'report_failure': ('engine.py','def pytest_runtest_logreport(self, report):','def pytest_runtest_logreport(self, report):\n        if report.when == "call": raise OSError("deliberate report publication failure")'),
        'dropped_lock': ('resource_owner.py','gate.sendall(b\'a\')','os.close(fd)  # deliberate lifetime mutation\n    gate.sendall(b\'a\')')}
    results=[]
    try:
        for name in names:
            print('OBSERVE',name,flush=True)
            equipment=mutant(out,name,*mutations[name]) if name in mutations else HERE
            result=accounting(out) if name=='accounting' else exercise(out,name,equipment=equipment)
            results.append(dict(id=name,state='completed',status='pass',observation=result))
    except BaseException as exc:
        results.append(dict(id=names[len(results)],state='completed',status='fail',error=repr(exc)))
        print('OBSERVATION FAILURE',repr(exc),flush=True)
    finally:
        for name in names[len(results):]:
            results.append(dict(id=name,state='unrun',status=None))
        end=time.time_ns()//1_000_000
        ok=all(r['status']=='pass' for r in results)
        run=dict(schema_version=1,terminal=True,run_id=args.name,started_at_unix_ms=started,
                 finished_at_unix_ms=end,duration_ms=end-started,configuration=configuration,plan=plan,
                 case_results=results,ok=ok,completion=dict(selected=len(names),completed=sum(r['state']=='completed' for r in results),
                 skipped=0,unrun=sum(r['state']=='unrun' for r in results)))
        with checkout_lock.owned(ROOT,env={}):
            retention.atomic_json(out/'run.json',run)
            index=retention.read_object(ROOT/'tests/RETAINED.json')
            index['runs'].append(dict(path=str(out.relative_to(ROOT/'tests/out')),run_id=args.name,
                                     reason='Pytest primary-engine boundary experiment: independent observations, source snapshot and consequential outcomes.',
                                     source=source,app_inventory=None))
            retention.write_index(ROOT,index)
    print(json.dumps(dict(out=str(out),ok=ok,results=[(r['id'],r['status']) for r in results])),flush=True)
    return 0 if ok else 1


if __name__=='__main__':
    raise SystemExit(main())
