"""Real process-loss windows in disposable copies; independent peers own the observations."""
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import time

import checkout_lock
import pytest_resources
from pytest_support import read, digest, write


def exercise(control):
    from pytest_integration import F, MODULE, require
    for mode in ('before-owner', 'before-release', 'before-start-publication', 'after-return'):
        root=control.fixture('window-'+mode)
        directory=Path('/private/tmp')/('pw-window-'+mode+'-'+str(os.getpid()));directory.mkdir()
        endpoint=str(directory/'peer')
        listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(endpoint);listener.listen(8);listener.settimeout(20)
        def mark(role, indent):
            return indent+"_observe=socket.socket(socket.AF_UNIX); _observe.connect("+repr(endpoint)+"); _observe.sendall("+repr(role.encode())+")\n"
        def patch(relative,before,after):
            p=root/relative;s=p.read_text();require(s.count(before)==1,mode+' fault anchor '+before);p.write_text(s.replace(before,after))
        # The engine's independent peer is established before any fixture work.
        patch('tests/lib/pytest_engine.py',"        send(PEER, dict(kind='started'))",mark('engine','        ').replace('_observe','self._observe')+"        send(PEER, dict(kind='started'))")
        native="import os,socket,sys,time,signal; s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1]); s.sendall(b'command'); s.recv(1); signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(60)"
        if mode=='after-return':
            native="import os,socket,sys,time,signal; child=os.fork(); s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1]); s.sendall(b'child' if child==0 else b'command'); s.recv(1); signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(60) if child==0 else None"
        setup="    import sys\n    pw_equipment.command([sys.executable,'-B','-S','-P','-c',"+repr(native)+","+repr(endpoint)+"], pw_equipment.artifacts/'window-command',60)\n    value = Observation(pw_equipment)"
        patch(MODULE,'    value = Observation(pw_equipment)',setup)
        if mode=='before-owner':
            needle='            self.process = subprocess.Popen('
            patch('tests/lib/pytest_resources.py',needle,mark('controller','            ')+'            time.sleep(60)\n'+needle)
            roles={'engine','controller'}
        elif mode=='before-release':
            needle="            transition(self.path, 'command_release_authorized')"
            patch('tests/lib/pytest_resources.py',needle,mark('controller','            ')+'            time.sleep(60)\n'+needle)
            patch('tests/lib/pytest_command_owner.py',"    gate.sendall(b'ready')",mark('owner','    ')+"    gate.sendall(b'ready')")
            roles={'engine','owner','controller'}
        elif mode=='before-start-publication':
            needle="            transition(path, 'command_started', command_pid=command.pid, command_pgid=command.pid)"
            patch('tests/lib/pytest_command_owner.py',needle,mark('owner','            ')+'            time.sleep(60)\n'+needle)
            roles={'engine','owner','command'}
        else:
            needle='            group_absent = checkout_lock.group_finished(command.pid, 1, command)'
            patch('tests/lib/pytest_command_owner.py',needle,mark('owner','            ')+'            time.sleep(60)\n'+needle)
            roles={'engine','owner','command','child'}
        env={k:v for k,v in os.environ.items() if not k.startswith(('PW_','PYTEST','PYTHON'))};env['PW_TEST_OUT_DIR']='tests/out/runs/window'
        log=(root.parent/'invocation.log').open('wb')
        process=subprocess.Popen(['bash','tests/run.sh'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        queue=select.kqueue();pids={};peers=[];exits=set()
        def collect(timeout):
            exits.update(e.ident for e in queue.control(None,max(1,len(pids)),timeout) if e.fflags & select.KQ_NOTE_EXIT)
        try:
            while set(pids)!=roles:
                peer,_=listener.accept();peers.append(peer);pid=peer.getsockopt(0,2);role=peer.recv(32).decode()
                require(role in roles and role not in pids,'unexpected independent peer')
                pids[role]=pid
                queue.control([select.kevent(pid,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD|select.KQ_EV_ONESHOT,fflags=select.KQ_NOTE_EXIT)],0,0)
                if role in ('command','child'):peer.sendall(b'g')
            out=root/'tests/out/runs/window';run_id=read(out/'owner.json')['run_id']
            paths=pytest_resources.record_paths(root,run_id);require(len(paths)==1,'window has other command obligations')
            before=read(paths[0])
            write(root.parent/'independent-starts.json',dict(pids=pids,record=str(paths[0]),state_before=before['state']))
            if mode in ('before-owner','before-release'):
                require(pids['controller']==process.pid,'controller marker not actual dispatcher')
                process.kill()
            else:
                require(before['state']==('command_release_authorized' if mode=='before-start-publication' else 'command_started'),'crash window not established')
                os.kill(pids['owner'],signal.SIGKILL)
            process.wait(timeout=20)
            if mode in ('before-start-publication','after-return'):
                run=read(out/'run.json')
                require(run['case_results'][1]['state']=='unrun' and 'pytest ownership' in run['case_results'][1]['reason'], 'unresolved ownership admitted queued legacy work inside the same run')
            if mode in ('before-start-publication','after-return'):
                live=pids['child'] if mode=='after-return' else pids['command']
                collect(0)
                require(live not in exits,'controlled live resource already exited')
                with checkout_lock.preview(root) as held:require(held,'surviving command/child lost inherited checkout hold')
                attempted=pytest_resources.recover(root,run_id,apply=True)
                require(attempted['unresolved'],'recovery invented settlement from missing or return-only evidence')
                # The external experiment owns this still-live authenticated peer
                # and registered its kernel exit observer before this signal.
                os.kill(live,signal.SIGKILL)
            deadline=time.monotonic()+20
            while exits!=set(pids.values()) and time.monotonic()<deadline:collect(1)
            require(exits==set(pids.values()),'not all independently observed actors exited')
            result=pytest_resources.recover(root,run_id,apply=True)
            if mode=='before-release':
                require(not result['unresolved'] and read(paths[0])['settlement']['never_launched'],'affirmative never-launch recovery failed')
            else:
                require(result['unresolved'] and read(paths[0])['state']!='closed','ambiguous launch/settlement was force-cleared')
            with checkout_lock.preview(root) as held:require(not held,'external controlled cleanup left a live lock holder')
            control.note('real crash window '+mode,output=str(out),pids=pids,kernel_exits=sorted(exits),
                record=str(paths[0]),state_before=before['state'],state_after=read(paths[0])['state'],
                source_sha256={p:digest(root/p) for p in (MODULE,'tests/lib/pytest_resources.py','tests/lib/pytest_command_owner.py')},
                disposition='closed with affirmative no-launch receipt' if mode=='before-release' else 'fixture checkout remains protected; recorded external exits do not manufacture an owner settlement')
        finally:
            if process.poll() is None:process.kill();process.wait()
            # On an unexpected failure, retain identities and avoid historical PID
            # cleanup. Normal paths above observe all exits before retiring peers.
            collect(0)
            write(root.parent/'independent-exits.json',dict(pids=pids,kernel_exits=sorted(exits),missing=sorted(set(pids.values())-exits)))
            queue.close();log.close()
            for peer in peers:peer.close()
            listener.close();(directory/'peer').unlink();directory.rmdir()
