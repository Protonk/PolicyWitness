"""Dispatcher-owned ARM first-use screen with a prepared gate and finite window."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def main(binary, primitive, output, gate):
    output, gate, binary = Path(output), Path(gate), Path(binary)
    assert primitive in ('wfe', 'wfet') and not gate.exists()
    token = uuid.uuid4().hex
    save(output/'prepared.json', dict(token=token, gate=str(gate), primitive=primitive,
                                     binary=str(binary), binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                                     profiles=['unapplied','allow_default','deny_default','file_read'],
                                     repetitions=3, trial_watchdog_s=8, cleanup_s=3, window_s=180))
    until = time.monotonic()+300
    while not gate.exists():
        assert time.monotonic()<until, 'prepared gate expired'
        time.sleep(.05)
    assert gate.read_text().strip()==token, 'gate token mismatch'
    started = time.monotonic(); deadline = started+180
    ownership = dict(version=1, scope='owned supervisor groups; child reaping remains in each native receipt',
                     cleanup_retained=False, trials=[])
    save(output/'ownership.json', ownership)
    for repeat in range(3):
        for policy in ('unapplied','allow_default','deny_default','file_read'):
            assert deadline-time.monotonic()>=11, 'window has no watchdog/cleanup reserve'
            prefix = output/f'{repeat}-{policy}'
            power_before = subprocess.run(['/usr/bin/pmset','-g','batt'],capture_output=True,text=True,check=True).stdout
            p = subprocess.Popen([str(binary), primitive, policy],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 text=True,start_new_session=True)
            own = dict(repetition=repeat,policy=policy,supervisor_pid=p.pid,group=p.pid,settled=False)
            ownership['trials'].append(own); ownership['cleanup_retained']=True
            save(output/'ownership.json',ownership)
            began = time.monotonic_ns()
            try:
                stdout, stderr = p.communicate(timeout=8)
            except BaseException:
                # The supervisor catches TERM and reaps its child; a forced group
                # kill is containment only and leaves cleanup evidence unresolved.
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    stdout, stderr = p.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL); stdout,stderr=p.communicate(timeout=3)
                prefix.with_suffix('.stdout').write_text(stdout)
                prefix.with_suffix('.stderr').write_text(stderr)
                own.update(returncode=p.returncode,contained=True)
                save(output/'ownership.json',ownership)
                raise
            prefix.with_suffix('.stdout').write_text(stdout); prefix.with_suffix('.stderr').write_text(stderr)
            row = json.loads(stdout)
            own.update(returncode=p.returncode,child_pid=row['pid'],child_reaped=row['reaped'],
                       settled=p.returncode==0 and row['reaped']==1)
            ownership['cleanup_retained']=not all(t['settled'] for t in ownership['trials'])
            save(output/'ownership.json',ownership)
            save(prefix.with_suffix('.conditions.json'),dict(primitive=primitive,policy=policy,repetition=repeat,
                 elapsed_ns=time.monotonic_ns()-began,power_before=power_before,
                 power_after=subprocess.run(['/usr/bin/pmset','-g','batt'],capture_output=True,text=True,check=True).stdout))
            with (output/'results.ndjson').open('a') as f: f.write(json.dumps(row)+'\n')
            assert own['settled'], 'unsettled supervisor/child; stop before another trial'
    save(output/'window.json',dict(declared_s=180,elapsed_s=time.monotonic()-started,complete=True))


if __name__ == '__main__': main(*sys.argv[1:])
