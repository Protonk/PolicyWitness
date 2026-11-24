"""Writer rendezvous and queued-byte controls against each worktree's signed app."""
import argparse, errno, json, os, selectors, signal, subprocess as sp, sys, tempfile, time
from pathlib import Path
base=Path(__file__).resolve().parents[1]
def write(p,obj): p.write_text(json.dumps(obj,indent=2)+'\n')
def sample(fd):
    try: return dict(bytes_hex=os.read(fd,16).hex())
    except BlockingIOError as e: return dict(errno=e.errno,name=errno.errorcode[e.errno])
def announce(kind,**more):
    print(json.dumps(dict(event=kind,t=time.monotonic(),pid=os.getpid(),**more)),flush=True)
def writer(target,byte):
    announce('armed')
    w=os.open(target,os.O_WRONLY)
    announce('blocking_writer_open_returned',fd=w)
    if byte:
        # Open this observer only AFTER the rendezvous. It keeps the byte observable if the worker is very fast.
        r=os.open(target,os.O_RDONLY|os.O_NONBLOCK)
        announce('supplied',hex='7a',write_rc=os.write(w,b'z'))
    if sys.stdin.buffer.read(1)!=b'q': raise RuntimeError('lost supervisor')
    if byte:
        announce('post_run_sample',**sample(r)); os.close(r)
    os.close(w)
    announce('closed')
def event(p,log):
    # Unbuffered pipe, so every line consumed has its own readable event.
    with selectors.DefaultSelector() as sel:
        sel.register(p.stdout,selectors.EVENT_READ)
        if not sel.select(6): raise TimeoutError('writer event deadline')
        line=p.stdout.readline()
    if not line: raise RuntimeError('writer stopped before handshake')
    obj=json.loads(line);log.append(obj);return obj
def run(label,mode,num,out):
    case=out/(mode+'-'+str(num)); case.mkdir()
    root=Path('/private/tmp/pw-findings-b7113f57-'+label)
    pw=root/'dist/PolicyWitness.app/Contents/MacOS/policy-witness'
    with tempfile.TemporaryDirectory(dir='/private/tmp',prefix='pw-touch-') as temp:
        target=Path(temp)/'pipe'; os.mkfifo(target,0o600)
        st=target.stat()
        log=dict(build=label,mode=mode,fifo=str(target),device=st.st_dev,inode=st.st_ino,events=[])
        ev=log['events']
        raw=sp.run([pw,'test-input','read','--target',target],capture_output=True,timeout=6,check=True)
        (case/'generated.json').write_bytes(raw.stdout); (case/'generate.stderr').write_bytes(raw.stderr)
        req=json.loads(raw.stdout)
        assert req['probe_plan'][0]['attempt']['action']=='read_fresh'
        req['probe_plan'][0]['attempt']['action']='open_read'
        spec=case/'specimen.json'; write(spec,req)
        writerproc=p=None;r=w=None
        try:
            if mode in ('queued','two-bytes','native-open-close'):
                r=os.open(target,os.O_RDONLY|os.O_NONBLOCK)
                w=os.open(target,os.O_WRONLY|os.O_NONBLOCK)
                payload=b'zy' if mode=='two-bytes' else b'z'
                ev.append(dict(event='prequeued',hex=payload.hex(),write_rc=os.write(w,payload)))
            else:
                try:
                    fd=os.open(target,os.O_WRONLY|os.O_NONBLOCK); os.close(fd)
                    raise AssertionError('unexpected preexisting reader')
                except OSError as e:
                    if e.errno!=errno.ENXIO: raise
                    ev.append(dict(event='no_reader_before_launch',errno=e.errno))
                with (case/'writer.stderr').open('wb') as we:
                    writerproc=sp.Popen([sys.executable,'-B',__file__,'writer',str(target),mode],stdin=sp.PIPE,stdout=sp.PIPE,stderr=we,bufsize=0)
                assert event(writerproc,ev)['event']=='armed'
            if mode=='native-open-close':
                native_fd=os.open(target,os.O_RDONLY); os.close(native_fd)
                ev.append(dict(event='plain_open_and_close',fd=native_fd))
            else:
                args=[str(pw),'test-input','run','--worker-timeout-ms','3000',str(spec)]
                start=time.monotonic()
                with (case/'response.json').open('wb') as so,(case/'pw.stderr').open('wb') as se:
                    p=sp.Popen(args,stdout=so,stderr=se,start_new_session=True)
                    log.update(argv=args,cli_pid=p.pid,started=start)
                    if writerproc:
                        assert event(writerproc,ev)['event']=='blocking_writer_open_returned'
                        if mode=='connected-byte':
                            assert event(writerproc,ev)['event']=='supplied'
                        if mode=='connected-empty' and label=='original':
                            # Restrict descriptor inventory to this invocation's new, private FIFO.
                            snap=sp.run(['/usr/sbin/lsof','-nP','-FpcfaDin',str(target)],capture_output=True,timeout=3)
                            (case/'open-descriptors.stdout').write_bytes(snap.stdout)
                            (case/'open-descriptors.stderr').write_bytes(snap.stderr)
                            ev.append(dict(event='target_lsof',rc=snap.returncode,t=time.monotonic()))
                    p.wait(timeout=max(.1,10-time.monotonic()+start))
                    log.update(rc=p.returncode,elapsed_s=time.monotonic()-start)
                res=json.loads((case/'response.json').read_bytes())
                rr=res['data']['runner_result']; s=rr['steps'][0]['attempt']
                log.update(reported_worker=rr['runner_subprocess']['pid'],host=next(a['control']['host_pid'] for a in res['data']['runner_client']['transport']['attempts'] if a.get('control',{}).get('status')=='granted'),
                           reaped=rr['runner_subprocess']['reaped'],outcome=res['result']['normalized_outcome'],
                           attempt=s['outcome'],lifecycle=s['lifecycle']['summary'],request_contract=req['contract'],
                           response_contract=res['build']['contract'],producer=rr['producer'])
            if writerproc:
                writerproc.stdin.write(b'q')
                if mode=='connected-byte': assert event(writerproc,ev)['event']=='post_run_sample'
                assert event(writerproc,ev)['event']=='closed'
                log['writer_exit']=writerproc.wait(timeout=3)
            if r is not None: ev.append(dict(event='post_run_sample',**sample(r)))
        finally:
            if writerproc and writerproc.poll() is None:
                writerproc.kill();writerproc.wait(timeout=2)
            if r is not None: os.close(r)
            if w is not None: os.close(w)
            if p and p.poll() is None:
                # Release the private FIFO without assuming that the child still has a descriptor.
                rr=os.open(target,os.O_RDONLY|os.O_NONBLOCK)
                ww=os.open(target,os.O_WRONLY|os.O_NONBLOCK)
                os.write(ww,b'x'); os.close(ww); os.close(rr)
                try: p.wait(timeout=4)
                except sp.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
            write(case/'observations.json',log)
if __name__=='__main__':
    if sys.argv[1]=='writer': writer(sys.argv[2],sys.argv[3]=='connected-byte')
    else:
        builds=['clean-mutant'] if sys.argv[1:] == ['clean-mutant'] else ['original','mutant']
        for build in builds:
            out=base/'mutation'/(build+'-fifo');out.mkdir()
            for mode,count in [('native-open-close',1),('connected-empty',3),('connected-byte',3),('queued',5),('two-bytes',1)]:
                for idx in range(1,count+1):run(build,mode,idx,out)
