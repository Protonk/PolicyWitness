"""Capture the user-space stack of two identified release workers waiting at different FIFO boundaries."""
from observe import base,pw,path,workers,write,unblock
from fifo_mutation import event
import json,os,signal,subprocess as sp,sys,tempfile,time
from pathlib import Path
for connected in (False,True):
    case = base / ('mutation/connected-stack' if connected else 'blocking/no-writer-stack')
    case.mkdir()
    with tempfile.TemporaryDirectory(dir='/private/tmp',prefix='pw-stack-') as tmp:
        fifo=Path(tmp)/'pipe';os.mkfifo(fifo,0o600)
        gen=sp.run([pw,'test-input','read','--target',fifo],capture_output=True,timeout=3,check=True)
        (case/'generated.json').write_bytes(gen.stdout)
        spec=json.loads(gen.stdout)
        if connected: spec['probe_plan'][0]['attempt']['action']='open_read'
        write(case/'specimen.json',spec)
        writer=p=None; ev=[]; report=dict(events=ev)
        before=workers();start=time.monotonic()
        try:
            if connected:
                with (case/'writer.stderr').open('wb') as se:
                    writer=sp.Popen([sys.executable,'-B',str(base/'methods/fifo_mutation.py'),'writer',str(fifo),'connected-empty'],stdin=sp.PIPE,stdout=sp.PIPE,stderr=se,bufsize=0)
                assert event(writer,ev)['event']=='armed'
            args=[str(pw),'test-input','run','--worker-timeout-ms','7000',str(case/'specimen.json')]
            with (case/'response.json').open('wb') as so,(case/'pw.stderr').open('wb') as se:
                p=sp.Popen(args,stdout=so,stderr=se,start_new_session=True)
                if writer: assert event(writer,ev)['event']=='blocking_writer_open_returned'
                while time.monotonic()-start<4:
                    current=workers()
                    fresh=set(current)-set(before)
                    if len(fresh)==1:
                        pid=fresh.pop();host,exe=current[pid];break
                    time.sleep(.025)
                else: raise RuntimeError('failed to identify bundle worker')
                report.update(pid=pid,parent=host,exe=exe,argv=args)
                for name,argv in [('sample',['/usr/bin/sample',str(pid),'1','5','-file',str(case/'sample.txt')]),
                                  ('lsof',['/usr/sbin/lsof','-nP','-p',str(pid)])]:
                    with (case/(name+'.stdout')).open('wb') as sn,(case/(name+'.stderr')).open('wb') as serr:
                        q=sp.run(argv,stdout=sn,stderr=serr,timeout=4)
                    ev.append(dict(command=argv,rc=q.returncode,t=time.monotonic()))
                p.wait(timeout=max(.2,15-time.monotonic()+start))
            if writer:
                writer.stdin.write(b'q');assert event(writer,ev)['event']=='closed';writer.wait(timeout=3)
            res=json.loads((case/'response.json').read_bytes()); rr=res['data']['runner_result']
            report.update(pid_matches_reply=pid==rr['runner_subprocess']['pid'],host_matches_grant=host in [a.get('control',{}).get('host_pid') for a in res['data']['runner_client']['transport']['attempts']],cli_rc=p.returncode,elapsed_s=time.monotonic()-start)
        finally:
            if writer and writer.poll() is None: writer.kill();writer.wait(timeout=3)
            if p and p.poll() is None:
                unblock(fifo,lambda what,**d:ev.append(dict(event=what,**d)))
                try:p.wait(timeout=4)
                except sp.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
            write(case/'observation.json',report)
