"""Bounded installed-bundle runs. Only identities for this bundle are persisted."""
import argparse, ctypes, errno, json, os, select, signal, subprocess as sp, tempfile, time
from pathlib import Path
base=Path(__file__).resolve().parents[1]
app=base.parents[1]/'dist/PolicyWitness.app'
pw=app/'Contents/MacOS/policy-witness'
native=app/'Contents/XPCServices/PWRunner.xpc/Contents/MacOS'
proc=ctypes.CDLL('/usr/lib/libproc.dylib')
def path(pid):
    buf=ctypes.create_string_buffer(4096)
    if proc.proc_pidpath(pid,buf,len(buf))>0: return os.fsdecode(buf.value)
    return None
def write(p,obj): p.write_text(json.dumps(obj,indent=2)+'\n')
def workers():
    rows={}
    listing=sp.check_output(['/bin/ps','-axo','pid=,ppid=,comm='],text=True,timeout=3)
    for row in listing.splitlines():
        cols=row.strip().split(None,2)
        if len(cols)!=3 or Path(cols[2]).name not in ('pw-probe-runner','pw-probe-runner-unentitled'): continue
        pid,host=map(int,cols[:2])
        name=path(pid)
        if name in map(str,[native/'pw-probe-runner',native/'pw-probe-runner-unentitled']) and path(host)==str(native/'PWRunner'):
            rows[pid]=(host,name)
    return rows
def ps(pid,opts,fields):
    args=['/bin/ps',opts,'-p',str(pid),'-o',fields]
    return sp.run(args,capture_output=True,timeout=3)
def env_snapshot(pid):
    plain=ps(pid,'-ww','command=')
    extra=ps(pid,'-Eww','command=')
    # Only the controlled worker argv is public; NEVER serialize unrelated environment strings.
    p,e=plain.stdout.strip(),extra.stdout.strip()
    return dict(pid=pid,argv=p.decode(),plain_rc=plain.returncode,environment_rc=extra.returncode,
                plain_nbytes=len(p),with_environment_nbytes=len(e),same_bytes=p==e,
                same_argv_prefix=e.startswith(p),controlled_marker_visible=b'PW_FINDINGS_CANARY=visible_1124' in e,
                stderr_plain=plain.stderr.decode(),stderr_env=extra.stderr.decode())
def observe(name,target,out):
    fifo='fifo' in name
    held=name=='env'
    ordinary=name=='fifo-ordinary'
    args=([str(pw),'run'] if ordinary else [str(pw),'test-input','run']+
          (['--worker-post-apply-hang-ms','20000'] if held else ['--worker-timeout-ms','3000']))
    spec=out/('fifo-specimen.json' if fifo else 'regular-specimen.json')
    with spec.open('wb') as so,(out/(name+'-generate.stderr')).open('wb') as se:
        sp.run([pw,'test-input','read','--target',target],stdout=so,stderr=se,check=True,timeout=5)
    args.append(str(spec))
    initial=workers()
    start=time.monotonic()
    deadline=145 if ordinary else (35 if held else 12)
    log=dict(argv=args,elapsed_s=None,watchdog_after_s=deadline,cli_pid=None,workers_before=initial,samples=[],events=[])
    def event(tag,**kwargs): log['events'].append(dict(seconds=time.monotonic()-start,event=tag,**kwargs))
    pid=host=None
    kq=select.kqueue()
    stdout=out/(name+'.json')
    try:
        with stdout.open('wb') as so,(out/(name+'.stderr')).open('wb') as se:
            p=sp.Popen(args,stdout=so,stderr=se,start_new_session=True)
            log['cli_pid']=p.pid
            try:
                while p.poll() is None and time.monotonic()-start<deadline:
                    if pid is None:
                        candidates=workers()
                        fresh=set(candidates)-set(initial)
                        if len(fresh)==1:
                            pid=fresh.pop(); host,worker_path=candidates[pid]
                            event('live-candidate',pid=pid,ppid=host,exe=worker_path,parent_exe=path(host))
                            try:
                                kq.control([select.kevent(pid,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD|select.KQ_EV_ONESHOT,fflags=select.KQ_NOTE_EXIT)],0,0)
                            except OSError as e: event('exit-monitor-registration-error',errno=e.errno)
                    t=time.monotonic()-start
                    if pid and t>0.65 and not log['samples']:
                        snap=ps(pid,'-ww','pid=,ppid=,lstart=,state=,wchan=,command=')
                        log['samples'].append(dict(seconds=t,rc=snap.returncode,line=snap.stdout.decode(),stderr=snap.stderr.decode()))
                        if held and snap.returncode==0:
                            write(out/'worker-ps-sanitized.json',env_snapshot(pid))
                    time.sleep(.025 if pid is None else .10)
                if p.poll() is None:
                    event('watchdog-fired')
                    if fifo: unblock(target,event)
                    try: p.wait(timeout=4)
                    except sp.TimeoutExpired:
                        os.killpg(p.pid,signal.SIGKILL); p.wait(timeout=3)
                        event('killed-owned-cli-process-group')
            finally:
                if p.poll() is None:
                    if fifo: unblock(target,event)
                    os.killpg(p.pid,signal.SIGKILL); p.wait(timeout=3)
            log.update(elapsed_s=time.monotonic()-start,rc=p.returncode)
        try:
            rr=json.loads(stdout.read_bytes())['data']['runner_result']
            sub=rr['runner_subprocess']
            rp=sub['pid']
            log.update(reported_worker=rp,live_matches_report=pid==rp,reported_worker_path_after=path(rp))
            gone=ps(rp,'-ww','pid=,ppid=,state=,comm=')
            event('ps-after',pid=rp,rc=gone.returncode,stdout=gone.stdout.decode(),stderr=gone.stderr.decode())
            if path(rp) is not None and fifo: unblock(target,event)
        except (KeyError,ValueError,TypeError) as e: event('report-unavailable',reason=str(e))
        if pid:
            kev=kq.control([],1,.1)
            event('registered-exit-event',events=[dict(pid=k.ident,fflags=k.fflags,exit=bool(k.fflags&select.KQ_NOTE_EXIT)) for k in kev])
            # The kqueue registration is tied to the original process. Recheck path and parent before fallback.
            if not kev and workers().get(pid)==(host,worker_path) and 'watchdog-fired' in [x['event'] for x in log['events']]:
                os.kill(pid,signal.SIGKILL); event('killed-owned-worker',pid=pid)
                event('fallback-exit',confirmed=bool(kq.control([],1,3)))
    finally:
        kq.close()
        write(out/(name+'-lifecycle.json'),log)
def unblock(fifo,event):
    # Private never-reused FIFO: supplies a writer AND a byte to release either kind of wait.
    try:
        fd=os.open(fifo,os.O_WRONLY|os.O_NONBLOCK)
        try: os.write(fd,b'x')
        finally: os.close(fd)
        event('watchdog-supplied-byte')
    except OSError as e: event('watchdog-open-or-write',errno=e.errno)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('group',choices=['blocking','environment']); g=parser.parse_args().group
    out=base/g
    with tempfile.TemporaryDirectory(prefix='pw-findings-',dir='/private/tmp') as d:
        d=Path(d); f=d/'regular'; f.write_bytes(b'ordinary control\n')
        if g=='blocking':
            fifo=d/'pipe'; os.mkfifo(fifo,0o600)
            for name,target in [('regular',f),('fifo-short',fifo),('fifo-ordinary',fifo)]: observe(name,target,out)
        else: observe('env',f,out)
