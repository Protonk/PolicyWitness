"""Outside replay observer; expectations come from the declared historical controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from observe import ROOT, HERE, PYTHON, require, read, rows, held, snapshot, base_env
import checkout_lock
import retention

ASSERTIONS = {
    'collection_from_final_reap':'slot->exec_leader_exit_observed == leader',
    'esrch_as_success':'slot->exec_group_rc == group->rc && slot->exec_group_errno == group->error',
    'fallback_from_group':'slot->exec_fallback_rc == fallback->rc && slot->exec_fallback_errno == fallback->error',
    'status_after_pending_wait':'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error',
    'revents_as_native_errno':'slot->exec_waitid_errno == wait_error && slot->exec_poll_errno == poll_failure',
    'local_deadline_as_native_errno':'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error',
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',required=True)
    parser.add_argument('--revision',required=True)
    parser.add_argument('--expect',choices=['old','stale','adapted'],required=True)
    args=parser.parse_args()
    out=ROOT/'tests/out/runs'/args.name
    start=time.time_ns()//1_000_000
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    with checkout_lock.owned(ROOT,env={}):
        retention.replacement_allowed(ROOT,out,retention.load_index(ROOT))
        require(not out.exists(),'fresh replay output required')
        out.mkdir(parents=True)
        retention.atomic_json(out/'owner.json',dict(schema_version=1,run_id=args.name,out_dir=str(out),started_at_unix_ms=start))
    (out/'source.json').write_text(json.dumps(dict(commit=source,files=snapshot(HERE)),indent=2)+'\n')
    candidate=out/'candidate'
    env=base_env(out,args.expect,'/nonexistent-unused-control-socket')
    env['BOUNDARY_REPLAY_REVISION']=args.revision
    command=[PYTHON,'-B','-I',str(HERE/'supervisor.py'),'--out',str(candidate),'--python',PYTHON,str(HERE/'test_native.py')]
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    observation=dict(expected=args.expect,revision=args.revision)
    ok=False
    try:
        with (out/'stdout').open('wb') as stdout,(out/'stderr').open('wb') as stderr:
            execution=subprocess.run(command,cwd=HERE,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,timeout=180)
        observation['returncode']=execution.returncode
        run=read(candidate/'run.json')
        phases=rows(candidate/'reports.jsonl')
        bodies=[p for p in phases if p.get('kind')=='report' and p.get('when')=='call']
        expected_names=['production',*ASSERTIONS]
        if args.expect=='adapted':expected_names+=['missing-pw_worker_timing.h','missing-pw_worker_exec.h']
        names=[p['nodeid'].split('[')[1].rstrip(']') for p in bodies]
        require(names==expected_names,'native selection differs from independent list')
        require((execution.returncode==0) is (args.expect!='stale'),'wrong replay exit')
        require(run['ok'] is (args.expect!='stale'),'wrong replay summary')
        require(bodies[0]['outcome']=='passed','production ledger did not pass')
        artifacts=candidate/'artifacts/native'
        golden=read(candidate/'native-inputs/exec_call_policy.json')['attempts']
        observed=read(artifacts/'observed-call-policy.json')
        require(len(observed)==58 and observed==golden,'native call policy changed')
        fixture=(candidate/'native-inputs/exec_control.c').read_bytes()
        original=subprocess.check_output(['git','show','f8f3c24f:tests/fixtures/worker_lifecycle/exec_control.c'],cwd=ROOT)
        require(fixture==original,'native assertion equipment changed')
        for index,(name,assertion) in enumerate(ASSERTIONS.items(),1):
            phase=bodies[index]
            if args.expect=='stale':
                require(phase['outcome']=='failed' and 'mutation was not formed' in phase['longrepr'],'stale anchor accepted or failed elsewhere')
                require(not (artifacts/name/'run.stdout').exists(),'stale mutation executed without formation')
            else:
                require(phase['outcome']=='passed','native rejection not accepted by its test')
                receipt=[r for r in rows(artifacts/name/'commands.jsonl') if r['event']=='returned' and r['name']=='run']
                require(len(receipt)==1 and receipt[0]['returncode']!=0,'native mutation was not rejected')
                error=(artifacts/name/'run.stderr').read_text()
                require('Assertion failed:' in error and assertion in error,'wrong native rejection reason')
        if args.expect=='adapted':
            for owner in ('pw_worker_timing.h','pw_worker_exec.h'):
                directory=artifacts/('missing-'+owner)
                receipt=[r for r in rows(directory/'commands.jsonl') if r['event']=='returned']
                require(len(receipt)==1 and receipt[0]['returncode']!=0,'missing owner compiled')
                require(f"'{owner}' file not found" in (directory/'build.stderr').read_text(),'wrong missing-owner diagnostic')
        require(not (candidate/'scratch').exists(),'build scratch retained')
        require(not held(),'native command retained lock')
        observation.update(ok=True,phase_outcomes=[p['outcome'] for p in bodies],native_attempts=len(observed),
                           fixture_sha256=hashlib.sha256(fixture).hexdigest())
        ok=True
    except BaseException as exc:
        observation['error']=repr(exc)
        print('REPLAY OBSERVATION FAILURE',repr(exc),flush=True)
    finally:
        (out/'observation.json').write_text(json.dumps(observation,indent=2)+'\n')
        end=time.time_ns()//1_000_000
        configuration=dict(out_dir=str(out))
        plan=dict(cases=[dict(id='native-replay')],configuration=configuration)
        run=dict(schema_version=1,terminal=True,run_id=args.name,started_at_unix_ms=start,finished_at_unix_ms=end,
                 duration_ms=end-start,configuration=configuration,plan=plan,ok=ok,
                 completion=dict(selected=1,completed=1,skipped=0,unrun=0),
                 case_results=[dict(id='native-replay',state='completed',status='pass' if ok else 'fail')])
        with checkout_lock.owned(ROOT,env={}):
            retention.atomic_json(out/'run.json',run)
            index=retention.read_object(ROOT/'tests/RETAINED.json')
            index['runs'].append(dict(path=str(out.relative_to(ROOT/'tests/out')),run_id=args.name,source=source,
                  app_inventory=None,reason='Exposed C extraction replay: '+args.expect+' adapter, native ledger and independent rejection observations.'))
            retention.write_index(ROOT,index)
    print(json.dumps(observation),flush=True)
    return 0 if ok else 1


if __name__=='__main__':
    raise SystemExit(main())
