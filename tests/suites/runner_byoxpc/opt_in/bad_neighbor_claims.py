"""Occupied-claim explanations against one installed BYOXPC service.

Investigation equipment, not a specimen test. The session's requests and a
foreign authorized client's requests reach one owned service. Process
observations attribute each refusal to the host generation that issued it and
to the request that held that host's claim; the already_ran string alone never
does. Outcomes of the unheld schedules are recorded, not asserted.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import contract
from consumer import validate
from neighbor_lab import ProcessWatch, generation_state, save, wait_for

pw, directory = sys.argv[1:3]
out = Path(directory)
client = Path(pw).parent / 'pw-runner-client'
service = json.loads((out / 'runner_env.json').read_text())['service_name']
state = json.loads(Path(json.loads((out / 'session.json').read_text())['state_path']).read_text())
macos = Path(state['bundle_path']) / 'Contents/MacOS'
HOST, WORKER = str(macos / 'PWRunner'), str(macos / 'pw-probe-runner')
work = out / 'claims'
work.mkdir()
requests, children = [], []


def overlaps(record, start, end):
    unseen = record['unseen_after_ns']
    return record['first_seen_ns'] <= end and (unseen is None or unseen >= start)


def served_host(request, hosts, workers):
    """The host generation that served a request, and how it was identified."""
    worker = request.get('worker_pid')
    if worker is not None:
        seen = [w for w in workers if w['pid'] == worker and overlaps(w, request['start_ns'], request['end_ns'])]
        if len(seen) == 1:
            parents = [h for h in hosts if h['pid'] == seen[0]['ppid'] and overlaps(h, request['start_ns'], request['end_ns'])]
            if len(parents) == 1:
                return parents[0]['generation'], 'worker_parent'
    alive = [h for h in hosts if overlaps(h, request['start_ns'], request['end_ns'])]
    return (alive[0]['generation'], 'only_host_in_window') if len(alive) == 1 else (None, 'unidentified')


def attribute(refusal, hosts, owners):
    """Which observed generation refused, and whose served request held its claim."""
    matches = [h for h in hosts if h['pid'] == refusal['reply_pid'] and overlaps(h, refusal['start_ns'], refusal['end_ns'])]
    if len(matches) != 1:
        return dict(host=None, cause='unobserved_host', candidates=len(matches))
    host = matches[0]['generation']
    holders = [r for r in owners if r['host'] == host]
    if not holders:
        return dict(host=host, cause='unattributed_claim')
    if len(holders) > 1:
        return dict(host=host, cause='ambiguous_claim', holders=[r['name'] for r in holders])
    return dict(host=host, cause=holders[0]['actor'] + '_claim', holder=holders[0]['name'])


def checker_controls():
    # Constructed observations: a matching PID outside the window (reuse), and
    # a generation that served nobody known, must not be attributed to anyone.
    hosts = [dict(generation='10@1.000000', pid=10, ppid=1, first_seen_ns=0, unseen_after_ns=50),
             dict(generation='10@2.000000', pid=10, ppid=1, first_seen_ns=100, unseen_after_ns=200),
             dict(generation='11@3.000000', pid=11, ppid=1, first_seen_ns=300, unseen_after_ns=None)]
    owners = [dict(name='own', actor='session', host='10@1.000000'),
              dict(name='theirs', actor='neighbor', host='10@2.000000')]
    cases = {'own': (dict(reply_pid=10, start_ns=40, end_ns=60), 'session_claim'),
             'neighbor': (dict(reply_pid=10, start_ns=150, end_ns=160), 'neighbor_claim'),
             'reused_pid': (dict(reply_pid=10, start_ns=250, end_ns=260), 'unobserved_host'),
             'unknown_holder': (dict(reply_pid=11, start_ns=310, end_ns=320), 'unattributed_claim'),
             'unseen_pid': (dict(reply_pid=12, start_ns=0, end_ns=400), 'unobserved_host')}
    results = {name: attribute(refusal, hosts, owners)['cause'] for name, (refusal, _) in cases.items()}
    save(work / 'checker-controls.json', results)
    assert results == {name: cause for name, (_, cause) in cases.items()}, results
    workers = [dict(pid=20, ppid=10, first_seen_ns=110, unseen_after_ns=120)]
    assert served_host(dict(worker_pid=20, start_ns=105, end_ns=190), hosts, workers) == ('10@2.000000', 'worker_parent')
    assert served_host(dict(worker_pid=21, start_ns=0, end_ns=400), hosts, []) == (None, 'unidentified')


def specimen(name, effect, hang, runner):
    spec = dict(schema_version=contract.REQUEST_SCHEMA, specimen_id=name,
        policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
        probe_plan=[dict(step_id='create', sandbox_check=dict(operation='file-write-create',
            filter=dict(kind='path', value=str(effect))), attempt=dict(kind='file', action='create', target=str(effect)))])
    if runner:
        spec['runner'] = dict(mode='byoxpc', service=service)
    if hang:
        spec['_test_overrides'] = dict(worker_post_apply_hang_ms=hang)
    return spec


def launch(name, actor, *, hang=0, direct=False):
    """Start one request through the public CLI or the shipped client directly."""
    folder = work / f'{len(requests):02d}-{name}'
    folder.mkdir()
    effect = folder / 'effect'
    spec = specimen(name, effect, hang, runner=not direct)
    (folder / 'specimen.json').write_text(json.dumps(spec, indent=2) + '\n')
    if direct:
        argv = [str(client), 'run', '--timeout-ms', '30000', '--mach-service', '--request', '-', service]
    else:
        argv = [pw, 'run', str(folder / 'specimen.json'), '--no-log-capture', '--timeout-ms', '30000']
    record = dict(name=name, actor=actor, direct=direct, argv=argv, folder=str(folder), effect=str(effect),
                  host_states_at_start={h['generation']: generation_state(h['generation'])
                                        for h in watch.snapshot('host') if h['unseen_after_ns'] is None})
    with (folder / 'stdout').open('w') as stdout, (folder / 'stderr').open('w') as stderr:
        record['start_ns'] = time.monotonic_ns()
        process = subprocess.Popen(argv, stdin=subprocess.PIPE if direct else subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
    if direct:
        process.stdin.write(json.dumps(spec).encode())
        process.stdin.close()
    children.append(process)
    requests.append(record)
    return process, record


def finish(process, record):
    record['returncode'] = process.wait(timeout=45)
    record['end_ns'] = time.monotonic_ns()
    folder = Path(record['folder'])
    raw = json.loads((folder / 'stdout').read_text())
    if record['direct']:
        reply = raw
    else:
        assert not validate(raw), validate(raw)
        reply = raw['data']['runner_result']
    subprocess_record = reply.get('runner_subprocess') or {}
    record.update(outcome=reply['normalized_outcome'], reply_pid=reply.get('pid'),
                  worker_pid=subprocess_record.get('pid'), steps=len(reply.get('steps') or []),
                  effect_exists=Path(record['effect']).exists())
    save(folder / 'record.json', record)
    return record


def run(name, actor, **options):
    return finish(*launch(name, actor, **options))


def wait_retired(reason):
    """Every observed host generation is gone by direct observation."""
    def retired():
        states = {h['generation']: generation_state(h['generation']) for h in watch.snapshot('host')}
        assert 'unknown' not in states.values(), ('host observation failed', states)
        return all(value == 'gone' for value in states.values())
    wait_for(retired, 'host retirement before ' + reason, timeout=10)


checker_controls()
log = subprocess.Popen(['/usr/bin/log', 'stream', '--style', 'ndjson', '--level', 'debug', '--predicate',
                        f'process == "PWRunner" OR process == "pw-runner-client" OR eventMessage CONTAINS "{service}"'],
                       stdout=(work / 'unified-log.ndjson').open('w'), stderr=(work / 'unified-log.stderr').open('w'))
watch = ProcessWatch({HOST: 'host', WORKER: 'worker'}).start()
schedules = {}
try:
    time.sleep(1)  # log stream attaches asynchronously; its gap is a limitation, not evidence
    wait_retired('the first schedule')

    # A. No neighbor, explicit retirement handoff: the positive control.
    spaced = []
    for index in range(3):
        wait_retired(f'spaced request {index}')
        spaced.append(run(f'spaced-{index}', 'session'))
    schedules['spaced'] = [r['name'] for r in spaced]

    # B. No neighbor, no handoff: each public request starts when the last exits.
    wait_retired('back-to-back requests')
    schedules['public_back_to_back'] = [run(f'public-{index}', 'session')['name'] for index in range(6)]

    # C. No neighbor: the shipped client again as soon as a served reply returns,
    # inside the owner's scheduled exit delay when the host is still alive.
    schedules['direct_after_reply'] = []
    for index in range(3):
        wait_retired(f'direct pair {index}')
        first = run(f'direct-owner-{index}', 'session', direct=True)
        second = run(f'direct-next-{index}', 'session', direct=True)
        schedules['direct_after_reply'].append([first['name'], second['name']])

    # D. A foreign authorized client discovers the service in the shared registry
    # and holds a fresh host's claim; the session then requests that service.
    wait_retired('foreign held claim')
    listing = subprocess.run([pw, 'runner', 'list'], capture_output=True, text=True, timeout=30)
    (work / 'neighbor-runner-list.json').write_text(listing.stdout)
    discovered = [r['service_name'] for r in json.loads(listing.stdout)['data']['runners']]
    assert service in discovered, ('neighbor could not discover the session service', discovered)
    neighbor, held = launch('neighbor-held', 'neighbor', hang=6000)
    wait_for(lambda: Path(held['effect']).exists() or neighbor.poll() is not None, 'neighbor effect', timeout=20)
    assert neighbor.poll() is None and Path(held['effect']).exists(), 'neighbor never held the claim'
    held_hosts = [h['generation'] for h in watch.snapshot('host') if generation_state(h['generation']) == 'alive']
    assert len(held_hosts) == 1, ('one live host expected while the neighbor holds it', held_hosts)
    refused = run('session-during-neighbor', 'session')
    assert neighbor.poll() is None, 'neighbor finished before the session request completed'
    finish(neighbor, held)
    wait_retired('continuation after the neighbor')
    after = run('session-after-neighbor', 'session')
    schedules['foreign_held'] = dict(neighbor=held['name'], refused=refused['name'], after=after['name'],
                                     held_host=held_hosts[0])

    # E. Two authorized clients queue while launchd throttles the next spawn
    # (ThrottleInterval 1 s after the primer's spawn): the neighbor first.
    queued = []
    for index in range(2):
        wait_retired(f'throttle primer {index}')
        primer = run(f'throttle-primer-{index}', 'session', direct=True)
        wait_retired(f'throttle window {index}')
        spawned = max(h['first_seen_ns'] for h in watch.snapshot('host'))
        neighbor, first = launch(f'neighbor-queued-{index}', 'neighbor', direct=True)
        time.sleep(.1)
        session_process, second = launch(f'session-queued-{index}', 'session', direct=True)
        first['since_last_spawn_ms'] = (first['start_ns'] - spawned) / 1e6
        second['since_last_spawn_ms'] = (second['start_ns'] - spawned) / 1e6
        finish(neighbor, first)
        finish(session_process, second)
        queued.append(dict(primer=primer['name'], neighbor=first['name'], session=second['name']))
    schedules['throttle_queue'] = queued

    # F. Registry lock contention on a fixture-owned registry: removal of an
    # absent service is refused while another process holds the lock.
    import fcntl
    fixture = work / 'fixture-registry' / 'runners.json'
    fixture.parent.mkdir()
    holder = (fixture.parent / 'runners.json.lock').open('a+')
    fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
    absent = 'com.policywitness.test.byoxpc.s' + 'absent' * 4
    env = dict(os.environ, PW_RUNNER_REGISTRY=str(fixture))
    contended = subprocess.run([pw, 'runner', 'remove', '--service-name', absent], env=env,
                               capture_output=True, text=True, timeout=30)
    fcntl.flock(holder, fcntl.LOCK_UN)
    holder.close()
    uncontended = subprocess.run([pw, 'runner', 'remove', '--service-name', absent], env=env,
                                 capture_output=True, text=True, timeout=30)
    schedules['registry_lock'] = dict(
        contended=dict(returncode=contended.returncode, stdout=contended.stdout, stderr=contended.stderr),
        uncontended=dict(returncode=uncontended.returncode, stdout=uncontended.stdout, stderr=uncontended.stderr))
finally:
    for process in children:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    time.sleep(1)
    watch.stop()
    log.send_signal(signal.SIGINT)
    try:
        log.wait(timeout=5)
    except subprocess.TimeoutExpired:
        log.kill()
    hosts, workers = watch.snapshot('host'), watch.snapshot('worker')
    save(work / 'processes.json', dict(hosts=hosts, workers=workers, sampler=watch.summary(),
                                       paths=dict(host=HOST, worker=WORKER)))
    save(work / 'requests.json', requests)

served = []
for record in requests:
    if record.get('outcome') == 'ok':
        record['host'], record['host_basis'] = served_host(record, hosts, workers)
        served.append(record)
attributions = {}
for record in requests:
    if record.get('outcome') == 'already_ran':
        record['attribution'] = attribute(record, hosts, served)
        attributions[record['name']] = record['attribution']
save(work / 'requests.json', requests)
by_name = {r['name']: r for r in requests}
summary = dict(service=service, schedules=schedules, attributions=attributions,
               outcomes={r['name']: r['outcome'] for r in requests},
               hosts={r['name']: r.get('host') for r in requests})
save(work / 'summary.json', summary)

# Positive control: with a retirement handoff and no neighbor, each request
# reached its own fresh host and produced its own effect.
spaced = [by_name[n] for n in schedules['spaced']]
assert all(r['outcome'] == 'ok' and r['effect_exists'] for r in spaced), [r['outcome'] for r in spaced]
assert len({r['host'] for r in spaced}) == 3 and None not in {r['host'] for r in spaced}, [r['host'] for r in spaced]
# Every refusal is pre-effect, whatever held the claim.
for record in requests:
    if record.get('outcome') == 'already_ran':
        assert record['steps'] == 0 and record['worker_pid'] is None and not record['effect_exists'], record
# Controlled interference: the refusal came from the host the neighbor held.
foreign = schedules['foreign_held']
refusal = by_name[foreign['refused']]
assert refusal['outcome'] == 'already_ran', refusal
assert refusal['attribution'] == dict(host=foreign['held_host'], cause='neighbor_claim', holder='neighbor-held'), refusal['attribution']
assert by_name['neighbor-held']['outcome'] == 'ok' and by_name['neighbor-held']['effect_exists']
assert by_name['session-after-neighbor']['outcome'] == 'ok' and by_name['session-after-neighbor']['effect_exists']
lock = schedules['registry_lock']
assert lock['contended']['returncode'] != 0 and 'busy' in lock['contended']['stdout'] + lock['contended']['stderr'], lock
assert 'busy' not in lock['uncontended']['stdout'] + lock['uncontended']['stderr'], lock
print(json.dumps(dict(outcomes=summary['outcomes'], attributions=attributions), indent=2))
