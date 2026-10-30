"""Two shipped clients, one owned host; file effects independently witness work."""
import json
import os
import re
from pathlib import Path
import plistlib
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import contract
from consumer import validate
from runner_client_capture import validate_capture
sys.path.insert(0, str(ROOT / "tests/fixtures/byoxpc"))
from neighbor_lab import process_identity, generation, generation_state

pw, directory = sys.argv[1:]
out = Path(directory)
service = json.loads((out / 'runner_env.json').read_text())['service_name']
state = json.loads(Path(json.loads((out / 'session.json').read_text())['state_path']).read_text())
# launchd respawns the job at most once per ThrottleInterval (its default is
# ten seconds when the plist sets none); wait that out plus a margin before
# a request that must reach a fresh host.
respawn_wait = plistlib.loads(Path(state['plist_path']).read_bytes()).get('ThrottleInterval', 10) + 1
processes = []
effects = Path(state['staging']) / 'effects'
effects.mkdir()

def launch(name, hang=0, direct=False, timeout=30000):
    effect = effects / name
    assert not effect.exists(), 'refusing reused effect path'
    spec = dict(schema_version=contract.REQUEST_SCHEMA, specimen_id=name,
        runner=dict(mode='byoxpc', service=service),
        policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
        probe_plan=[dict(step_id='create', sandbox_check=dict(operation='process-exec*',
            filter=dict(kind='path', value='/bin/sh')), attempt=dict(kind='exec', action='spawn', target='/bin/sh', args=['-c', 'printf x >> "$1"', 'effect', str(effect)]))])
    if direct: spec.pop('runner')
    if hang: spec['_test_overrides'] = dict(worker_post_apply_hang_ms=hang)
    path = out / (name + '.specimen.json'); path.write_text(json.dumps(spec, indent=2)+'\n')
    with (out/(name+'.json')).open('w') as stdout, (out/(name+'.stderr')).open('w') as stderr:
        argv = [str(Path(pw).parent / 'pw-runner-client'), 'run', '--timeout-ms', str(timeout), '--mach-service', service, str(path)] if direct else [pw, 'run', str(path), '--timeout-ms', str(timeout)]
        process = subprocess.Popen(argv,
            stdout=stdout, stderr=stderr, start_new_session=True)
    processes.append(process)
    return process, effect

def receive(process, name, code, direct=False):
    assert process.wait(timeout=40) == code, name
    doc = json.loads((out/(name+'.json')).read_text())
    problems = validate_capture(doc) if direct else validate(doc)
    assert not problems, problems
    return doc if direct else doc['data']['runner_result']

try:
    # Installation's verify call consumed a host. Wait beyond launchd's respawn
    # throttle before issuing this independent specimen; do not retry execution.
    time.sleep(respawn_wait)
    first, marker = launch('owner', 15000)
    deadline = time.monotonic() + 20
    while not marker.exists():
        assert first.poll() is None and time.monotonic() < deadline, 'owner never published file effect'
        time.sleep(.02)
    assert first.poll() is None, 'owner no longer held'
    target=f'gui/{os.getuid()}/{service}'
    launchd=subprocess.run(['/bin/launchctl','print',target],capture_output=True,text=True,timeout=5)
    (out/'held-host.launchctl.txt').write_text(launchd.stdout+launchd.stderr)
    assert launchd.returncode==0, 'owned host not in launchd'
    match=re.search(r'^\s*pid = (\d+)\s*$',launchd.stdout,re.M)
    assert match, 'launchd did not report held host PID'
    host_pid=int(match[1])
    children=subprocess.run(['/usr/bin/pgrep','-P',str(host_pid)],capture_output=True,text=True,timeout=5)
    assert children.returncode==0, 'held host has no child'
    child_pids=[int(p) for p in children.stdout.split()]
    receipts=subprocess.run(['/bin/ps','-o','pid=,ppid=,comm=','-p',','.join(map(str,child_pids))],
                            capture_output=True,text=True,timeout=5)
    (out/'held-children.txt').write_text(receipts.stdout+receipts.stderr)
    assert receipts.returncode==0
    worker_children=[int(row.split(None,2)[0]) for row in receipts.stdout.splitlines()
        if len(row.split(None,2))==3 and int(row.split(None,2)[1])==host_pid
        and Path(row.split(None,2)[2]).name=='pw-probe-runner']
    assert len(worker_children)==1, 'exactly one held worker required'

    owner_generation = process_identity(host_pid)
    assert owner_generation['observed']
    second, absent = launch('refused', direct=True, timeout=1000)
    refusal = receive(second, 'refused', 1, direct=True)
    assert first.poll() is None, 'refusal retired the active owner'
    assert refusal['terminal'] == 'xpc_timeout' and refusal['submission']['state'] == 'not_invoked', refusal
    assert refusal.get('runner_reply') is None, refusal
    assert any((a.get('control') or {}).get('host_pid') == host_pid and
               (a.get('control') or {}).get('status') == 'occupied' for a in refusal['attempts']), refusal
    assert not absent.exists(), 'refused request attempted file creation'
    waiting, waiting_effect = launch('reacquired')
    owner = receive(first, 'owner', 0)
    recovered = receive(waiting, 'reacquired', 0)
    envelope = json.loads((out / 'reacquired.json').read_text())
    transport = envelope['data']['runner_client']['transport']
    attempts = transport['attempts']
    assert any((a.get('control') or {}).get('host_pid') == host_pid and
               (a.get('control') or {}).get('status') == 'occupied' for a in attempts), attempts
    assert attempts[-1]['outcome'] == 'granted' and attempts[-1]['control']['host_pid'] != host_pid, attempts
    assert transport['submission']['state'] == 'invoked'
    assert transport['submission']['invoked_elapsed_ms'] >= attempts[-1]['ended_elapsed_ms']
    assert generation_state(generation(owner_generation)) == 'gone'
    assert recovered['runner_subprocess']['pid'] != owner['runner_subprocess']['pid']
    assert waiting_effect.read_bytes() == b'x'
    assert owner['normalized_outcome'] == 'ok' and owner['runner_subprocess']['reaped'] is True, owner
    assert owner['test_overrides']['worker_post_apply_hang_ms'] == 15000
    assert owner['runner_subprocess']['pid'] == worker_children[0], 'host/child receipts disagree with replies'
    assert marker.read_bytes() == b'x' and not absent.exists()
    pid = host_pid; deadline = time.monotonic()+5
    while True:
        try: os.kill(pid, 0)
        except ProcessLookupError: break
        assert time.monotonic() < deadline, 'owner host did not retire'
        time.sleep(.02)
    time.sleep(respawn_wait)
    third, marker = launch('fresh')
    fresh = receive(third, 'fresh', 0)
    assert fresh['normalized_outcome'] == 'ok' and marker.read_bytes() == b'x', fresh
    for name in ('owner', 'reacquired', 'fresh'):
        (out / (name + '.effect.bytes')).write_bytes((effects / name).read_bytes())
    (out/'receipts.json').write_text(json.dumps(dict(shared_host=pid, owner_worker=worker_children[0], fresh_worker=fresh['runner_subprocess']['pid'],
        owner_effect=True, refused_effect=False, owner_retired=True), indent=2)+'\n')
finally:
    # Watchdog intervention is failure, never evidence of a PW timeout. Session
    # cleanup in the wrapper owns the service and any surviving hosted children.
    for process in processes:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
