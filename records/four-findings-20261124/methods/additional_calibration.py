"""Native allow-default controls and the stock driver's unusable-target gate."""
import json,os,signal,subprocess as sp,time
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'calibration'
root=out.parents[2];h=root/'tests/suites/witness_contract/harness';env=dict(os.environ,PW_PYTHON='/opt/homebrew/opt/python@3.14/bin/python3.14',PW_APP_DIR=str(root/'dist/PolicyWitness.app'))
for name,args,linger in [('platform-as-target',[h/'verify_filter_id.sh','iokit_open','iokit-registry-entry-class','IOPlatformExpertDevice','--allowed-value','IOPMrootDomain','--max-id','200'],False)]+[
 ('allow-default-'+value,[h/'enforcement_probe',kind,'(version 1)(allow default)',value],True)
 for kind,value in [('sysctl_read','kern.osrelease'),('iokit_open','IOSurfaceRoot'),('iokit_open','IOPlatformExpertDevice'),('iokit_open','IOPMrootDomain')]]:
    start=time.monotonic()
    with (out/(name+'.stdout')).open('wb') as so,(out/(name+'.stderr')).open('wb') as se:
        p=sp.Popen(args,env=env,stdout=so,stderr=se,start_new_session=True)
        stop=False
        try:
            if linger:
                while time.monotonic()-start<4 and p.poll() is None:
                    if b'attempt_outcome=' in (out/(name+'.stdout')).read_bytes():break
                    time.sleep(.015)
                if p.poll() is None:p.kill();stop=True
            p.wait(timeout=8)
        finally:
            if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=2)
    (out/(name+'.json')).write_text(json.dumps(dict(argv=list(map(str,args)),rc=p.returncode,elapsed_s=time.monotonic()-start,terminated_lingering_probe=stop),indent=2)+'\n')
