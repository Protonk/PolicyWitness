from pathlib import Path
import json, os, subprocess as sp, signal, select, tempfile, time
from observe import env_snapshot,write
base=Path(__file__).resolve().parents[1]
out=base/'environment'
with tempfile.TemporaryDirectory(dir='/private/tmp',prefix='pw-env-control-') as temp:
    exe=Path(temp)/'control'
    with (out/'control-build.log').open('wb') as log:
        sp.run(['xcrun','clang','-Wall','-Wextra','-Wno-deprecated-declarations',base/'methods/env_control.c','-o',exe],stdout=log,stderr=log,check=True)
        sp.run(['/usr/bin/codesign','-s','-','-f','-o','runtime',exe],stdout=log,stderr=log,check=True)
        sp.run(['/usr/bin/codesign','-dvvv',exe],stdout=log,stderr=log,check=True)
    for mode in ['explicit','nil','empty','cleared']:
        with (out/(mode+'.stdout')).open('w+b',buffering=0) as so,(out/(mode+'.stderr')).open('wb') as se:
            p=sp.Popen([exe,'parent',mode],stdin=sp.PIPE,stdout=so,stderr=se,env={'PW_FINDINGS_CANARY':'visible_1124'},start_new_session=True)
            try:
                start=time.monotonic()
                while time.monotonic()-start<4 and p.poll() is None:
                    lines=(out/(mode+'.stdout')).read_text().splitlines()
                    if len(lines)==2: break
                    time.sleep(.01)
                assert len(lines)==2, mode
                worker=json.loads(lines[1])
                snap=env_snapshot(worker['pid'])
                p.communicate(input=b'x',timeout=3)
                write(out/(mode+'-ps.json'),dict(snapshot=snap,child_and_parent_exit=p.returncode,envp=mode))
            finally:
                if p.poll() is None: os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
