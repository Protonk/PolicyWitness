"""Independent boundary stimuli and observations; candidate reports are subjects."""
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import checkout_lock
import execution_contract
import pytest_resources as resources
from pytest_support import read, write, value_digest


def require(value, message):
    if not value:
        raise AssertionError(message)


def busy(root):
    with checkout_lock.preview(root) as value:
        return value


def wait_for(predicate, description, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.02)
    raise AssertionError('timeout: ' + description)


class Controls:
    def __init__(self, out):
        self.out = out
        self.observed = []

    def note(self, name, **facts):
        self.observed.append(dict(name=name, **facts))
        write(self.out / 'observations.json', self.observed)
        print('ok:', name, flush=True)

    def fixture(self, name):
        root = self.out / name / 'repo'
        (root / 'tests').mkdir(parents=True)
        out = root / 'tests/out/runs/control'
        out.mkdir(parents=True)
        return root, out

    def ownership(self):
        root, out = self.fixture('ownership')
        with checkout_lock.owned(root, env={}) as scope:
            argv = [sys.executable, '-B', '-S', '-P', '-c',
                    'import os,sys; print("native stdout"); print("native stderr",file=sys.stderr); print(os.fstat(int(sys.argv[1])).st_ino)', str(scope.fd)]
            command = resources.Command(root, out, 'normal', 'fixture/family', 'fixture/family::one',
                                        argv, out / 'captured', 5, scope, os.getpid())
            held = os.fstat(scope.fd)
            receipt = command.finish()
            require(receipt['returncode'] == 0, 'normal command failed')
            require((out / 'captured/stdout').read_text() == f'native stdout\n{held.st_ino}\n', 'native fd capture/lock inheritance wrong')
            require((out / 'captured/stderr').read_text() == 'native stderr\n', 'native stderr capture lost')
            require(resources.snapshot(root, 'normal')['closed'], 'normal ownership not closed')
            self.note('native capture and actual lock inode inherited', inode=held.st_ino)
            # A reservation alone has no successful result. Deliberately unknown
            # authorization retains the checkout even when the lock is available.
            path = resources.reserve(root, out, 'ambiguous', 'fixture/family', 'fixture/family::two',
                                     ['/does-not-exist'], out / 'never', 5, scope, os.getpid())
            resources.transition(path, 'owner_launch_authorized')
        before = path.read_bytes()
        preview = resources.recover(root, 'ambiguous')
        require(path.read_bytes() == before and preview['before'][0]['blocking'] == 'checkout', 'preview changed unknown evidence')
        result = resources.recover(root, 'ambiguous', apply=True)
        require(result['unresolved'] and path.read_bytes() == before, 'ambiguous no-PID record improperly closed')
        self.note('ambiguous authorization refuses historical PID recovery', recovery=result)
        # Experimental controller has affirmative no-launch knowledge: store the
        # independent fixture observation. Production recovery is never given it.
        self.note('ambiguous fixture disposition', resource_started=False, reason='observer never invoked a launcher', path=str(path))

    def contract(self):
        family = 'fixture/family'
        selected = [dict(id=family, engine='pytest')]
        contract = dict(profile=execution_contract.PROFILE, source={'fixture':'independent expected producer'}, selected=selected, required_families=[family])
        contract['identity'] = value_digest(contract)
        selection = dict(items=[dict(id=family+'::one')])
        account = dict(manifest_digest=value_digest(selection), items=[dict(id=family+'::one', outcome='passed', phases={p:dict(outcome='passed',operations=['op']) for p in ('setup','call','teardown')})],
                       accounting_state='complete', ok=True, operations=['op'])
        command = dict(operation_id='op', state='closed', token='bound', command_pid=10,
                       settlement=dict(token='bound', authority_revoked=True, group_absent=True, command_pid=10, returncode=0))
        ownership = dict(closed=True, problems=[], commands=[command])
        parent = dict(id=family, engine='pytest', execution_state='started', accounting_state='complete', family_report='suites/'+family+'/family.json')
        run = dict(execution_contract=contract, case_results=[parent])
        files = {'suites/'+family+'/'+name+'.json':v for name,v in [('family',account),('selection',selection),('ownership',ownership)]}
        require(not execution_contract.problems(run, contract, files.__getitem__), 'valid family rejected')
        for field in ('engine', 'family_report', 'execution_state'):
            altered = json.loads(json.dumps(run)); del altered['case_results'][0][field]
            require(execution_contract.problems(altered, contract, files.__getitem__), 'missing '+field+' accepted')
        for role in ('family', 'ownership'):
            altered = dict(files); del altered['suites/'+family+'/'+role+'.json']
            require(execution_contract.problems(run, contract, altered.__getitem__), 'missing '+role+' accepted')
        altered = dict(run); altered.pop('execution_contract'); altered['case_results'] = []
        require(execution_contract.problems(altered, contract, {}.__getitem__), 'erasing all local family hints accepted')
        self.note('independent producer contract refuses missing family declarations and ownership roles')

    def detached(self, live=False):
        root, out = self.fixture('detached-live' if live else 'detached')
        # This is an external observation channel, not an engine report. Its peer
        # is the command itself. The fixture runs the actual command owner code.
        directory = Path('/private/tmp') / ('pw-control-' + str(os.getpid()))
        directory.mkdir()
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(directory / 'peer')); listener.listen(1); listener.settimeout(10)
        driver = out / 'driver.py'
        driver.write_text('''import os,sys,time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import checkout_lock
from pytest_resources import Command
root,out=map(Path,sys.argv[2:4])
with checkout_lock.owned(root,env={}) as scope:
    command=Command(root,out,'detached','fixture/family','fixture/family::one',
      [sys.executable,'-B','-S','-P','-c',"import socket,sys,time,signal; s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1]); s.sendall(b'started'); signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(60)",sys.argv[4]],out/'command',60,scope,os.getpid())
    (out/'owner-pid').write_text(str(command.process.pid))
    time.sleep(60)
''')
        env = {k:v for k,v in os.environ.items() if not k.startswith(('PW_CHECKOUT','PYTHON'))}
        log = (out / 'driver.log').open('wb')
        process = subprocess.Popen([sys.executable,'-B','-S',str(driver),str(ROOT/'tests/lib'),str(root),str(out),str(directory/'peer')], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        peer = None
        queue = select.kqueue()
        try:
            peer, _ = listener.accept()
            pid = peer.getsockopt(0, 2)
            require(peer.recv(16) == b'started', 'independent command start absent')
            owner = int(wait_for(lambda:(out/'owner-pid').read_text() if (out/'owner-pid').exists() else None,'owner PID'))
            for watched in (pid, owner):
                queue.control([select.kevent(watched,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD|select.KQ_EV_ONESHOT,fflags=select.KQ_NOTE_EXIT)],0,0)
            require(busy(root), 'owned command does not hold checkout')
            active = resources.recover(root, 'detached', apply=True)
            require(active['unresolved'], 'active session recovery accepted')
            process.kill(); process.wait(timeout=5)
            require(busy(root), 'lock released before owned command exits')
            live_result = None
            if live:
                live_result = resources.recover(root, 'detached', apply=True)
            exits=set()
            deadline=time.monotonic()+12
            while len(exits)<2 and time.monotonic()<deadline:
                exits.update(e.ident for e in queue.control(None,2,1) if e.fflags & select.KQ_NOTE_EXIT)
            require(exits == {pid,owner}, 'command/owner exits not independently observed')
            require(not busy(root), 'quiescent owner kept physical lock')
            self.note('external exit observations before disposition', command_pid=pid, owner_pid=owner, exit_events=sorted(exits), lock_busy=busy(root))
            state = resources.inspect(root,'detached')
            require(state[0]['blocking'] in (('output','closed') if live else ('output',)),'settled command still blocks checkout or lost output hold')
            result = resources.recover(root,'detached',apply=True)
            require(not result['unresolved'],'settled command recovery failed')
            require(not resources.recover(root,'detached',apply=True)['unresolved'],'recovery not idempotent')
            self.note('supervisor death preserves hold through command exit; recover closes settled output', command_pid=pid, owner_pid=owner, exit_events=sorted(exits), live_recovery=live_result)
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
            queue.close(); log.close()
            if peer: peer.close()
            listener.close(); (directory/'peer').unlink(); directory.rmdir()


if __name__ == '__main__':
    control = Controls(Path(sys.argv[1]).resolve())
    control.ownership()
    control.contract()
    control.detached()
    control.detached(live=True)
    from pytest_integration import Integration
    Integration(control.out, control.note).all()
