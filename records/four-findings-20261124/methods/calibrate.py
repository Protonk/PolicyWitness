"""Run the stock paired scanner, then retain the stock probe's native controls."""
from pathlib import Path
import subprocess as sp
import os, signal, sys, time, json, shutil, tempfile
out = Path(__file__).resolve().parents[1] / 'calibration'
root = out.parents[2]
h = root / 'tests/suites/witness_contract/harness'
env = dict(os.environ, PW_PYTHON='/opt/homebrew/opt/python@3.14/bin/python3.14', PW_APP_DIR=str(root/'dist/PolicyWitness.app'))
scan = h / 'verify_filter_id.sh'
probe = h / 'enforcement_probe'
cases = [
 ('sysctl','sysctl_read','sysctl-read','sysctl-name','kern.osrelease','kern.osrelease',
  [('absent','kern.nonexistent.sibling', 'kern.nonexistent.sibling'), ('present','kern.ostype','kern.ostype')]),
 ('service','iokit_open','iokit-open-service','iokit-registry-entry-class','IOSurfaceRoot','IOSurfaceRoot',
  [('absent','SomeNonexistentService','SomeNonexistentService'),('platform','IOPlatformExpertDevice','IOPlatformExpertDevice'),('power','IOPMrootDomain','IOPMrootDomain')]),
 ('client','iokit_open_user_client','iokit-open-user-client','iokit-user-client-class','IOSurfaceRootUserClient','IOSurfaceRoot',
  [('absent','AnotherUserClient',None),('power','RootDomainUserClient','IOPMrootDomain')])]
def collect(name,args,linger=False):
    start=time.monotonic()
    with (out/(name+'.stdout')).open('wb') as so, (out/(name+'.stderr')).open('wb') as se:
        p=sp.Popen(args,stdout=so,stderr=se,env=env,start_new_session=True)
        stopped=False
        try:
            if linger:
                deadline=start+5
                while time.monotonic()<deadline and p.poll() is None:
                    if b'attempt_outcome=' in (out/(name+'.stdout')).read_bytes(): break
                    time.sleep(.015)
                if p.poll() is None:
                    p.kill(); stopped=True
            p.wait(timeout=150)
        finally:
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGKILL); p.wait()
    (out/(name+'.json')).write_text(json.dumps(dict(argv=list(map(str,args)),rc=p.returncode,
         elapsed_s=time.monotonic()-start,terminated_lingering_probe=stopped),indent=2)+'\n')
if sys.argv[1:] == ['first']:
    collect('sandbox-first',[scan,'sysctl_read','sysctl-name','kern.osrelease','--allowed-value','kern.nonexistent.sibling','--max-id','200'])
    sys.exit()
for name,kind,op,filt,target,service,siblings in cases:
    policy=f'(version 1)\n(allow default)\n(deny {op} ({filt} "{target}"))'
    for tag,sibling,_ in siblings:
        cmd=[scan,kind,filt,target]
        if kind=='iokit_open_user_client': cmd+=['--probe-target',service]
        collect(name+'-'+tag,cmd+['--allowed-value',sibling,'--max-id','200'])
    native='sysctl_read' if name=='sysctl' else 'iokit_open'
    for tag,sv in [('target',service)]+[(tag,sv) for tag,_,sv in siblings if sv]:
        collect(name+'-native-'+tag,[probe,native,policy,sv],True)
    if name=='client':
        collect('client-own-deny',['%s'%probe,native,policy.replace('IOSurfaceRootUserClient','RootDomainUserClient'),'IOPMrootDomain'],True)
for n in ['kern.osrelease','kern.ostype','kern.nonexistent.sibling']:
    collect(n,['/usr/sbin/sysctl',n])
