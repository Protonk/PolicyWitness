"""Observe two shipped workers from outside at the existing hang seams.

This is an inventory, not an isolation oracle. Missing lsof/ps observations
fail; denied optional task inspection is retained as an observation boundary.
The ordinary contaminated_worker case supplies the positive inheritance control.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture


def command(out, name, argv, timeout=5):
    started = time.monotonic()
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout)
        stdout, stderr, rc = result.stdout, result.stderr, result.returncode
        expired = False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, rc = exc.stdout or b'', exc.stderr or b'', None
        expired = True
    (out / (name + '.stdout')).write_bytes(stdout)
    (out / (name + '.stderr')).write_bytes(stderr)
    record = dict(argv=argv, returncode=rc, timed_out=expired,
                  elapsed_seconds=time.monotonic() - started)
    (out / (name + '.json')).write_text(json.dumps(record, indent=2) + '\n')
    return record, stdout.decode(errors='replace')


def processes():
    result = subprocess.run(['/bin/ps', '-wwaxo', 'pid=,ppid=,comm=,args='],
                            capture_output=True, text=True, timeout=5, check=True)
    return result.stdout


def candidates(snapshot, flag):
    found = []
    for line in snapshot.splitlines():
        fields = line.strip().split(None, 3)
        if len(fields) == 4 and Path(fields[2]).name == 'pw-probe-runner' and flag in fields[3].split():
            found.append((int(fields[0]), int(fields[1])))
    return found


def observe(pw, out, boundary):
    pre = boundary == 'pre_ready'
    key = 'worker_pre_ready_hang_ms' if pre else 'worker_post_apply_hang_ms'
    flag = '--pre-ready-hang-ms' if pre else '--post-apply-hang-ms'
    # Both workers run the same empty allow-default plan. The seam is the
    # only difference; no wrapper replaces or instruments the signed worker.
    specimen = dict(schema_version=5, specimen_id='launch_inventory_' + boundary,
                    policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
                    probe_plan=[], _test_overrides={key: 20000})
    run = RunCapture(pw, out, specimen,
                     cli_args=['--timeout-ms', '45000'])
    initial = processes()
    (out / 'processes-before.txt').write_text(initial)
    existing = {pid for pid, _ in candidates(initial, flag)}
    pid = host = None
    observations = {}
    started = time.monotonic()
    with run:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and run.poll() is None:
            snapshot = processes()
            found = [(p, h) for p, h in candidates(snapshot, flag) if p not in existing]
            if len(found) == 1:
                pid, host = found[0]
                (out / 'processes-during.txt').write_text(snapshot)
                break
            assert len(found) <= 1, 'ambiguous worker identity; do not select by name alone'
            time.sleep(.05)
        assert pid is not None, 'worker not found; see CLI capture'
        # Allow startup to reach the selected sleep. Boundary attribution is
        # source + selected seam + timing, not a read of worker shared memory.
        time.sleep(.5)
        for name, argv in [
            ('identity', ['/bin/ps', '-ww', '-p', f'{pid},{host}', '-o',
                          'pid=,ppid=,uid=,gid=,lstart=,state=,wchan=,comm=,args=']),
            ('argv', ['/bin/ps', '-ww', '-p', str(pid), '-o', 'command=']),
            ('environment', ['/bin/ps', '-Eww', '-p', str(pid), '-o', 'command=']),
            ('descriptors', ['/usr/sbin/lsof', '-nP', '-p', str(pid)]),
            ('mappings', ['/usr/bin/vmmap', '-w', str(pid)]),
            ('ports', ['/usr/bin/lsmp', '-p', str(pid)]),
        ]:
            observations[name], _ = command(out, name, argv)
        observations['snapshot_elapsed_seconds'] = time.monotonic() - started
        # Wait for normal production cleanup even if an observation failed.
        rc = run.wait(timeout=35)
    envelope = run.load_json()
    runner = envelope['data']['runner_result']
    (out / 'observations.json').write_text(json.dumps(dict(
        boundary=boundary, worker_pid=pid, host_pid=host, observations=observations,
        boundary_basis='selected production sleep seam, source order and elapsed time; no shared-memory read',
    ), indent=2) + '\n')
    assert rc == 0 and runner['normalized_outcome'] == 'ok', runner
    worker = runner['runner_subprocess']
    assert worker['pid'] == pid and worker['exit_code'] == 0 and worker['reaped'], worker
    assert worker['done_observed'] and worker['collection_basis'] == 'after_confirmed_reap', worker
    assert worker['poll_stop_reason'] == 'done' and not worker['wait_errors'], worker
    assert worker['ready_byte_received'] is (not pre), worker
    readiness = worker['worker_evidence']['readiness']
    assert readiness['rc'] == (-1 if pre else 0), readiness
    if pre:
        assert worker['ready_wait']['stop'] == 'deadline' and readiness['errno'] == 32, worker
    assert runner['test_overrides'][key] == 20000, runner
    assert observations['snapshot_elapsed_seconds'] < 18, observations
    for name in ['identity', 'argv', 'environment', 'descriptors']:
        assert observations[name]['returncode'] == 0, (name, observations[name])
    # ps output must identify the requested seam; an empty result is no census.
    assert flag in (out / 'environment.stdout').read_text()
    rc_record, after = command(out, 'worker-after', ['/bin/ps', '-p', str(pid), '-o', 'pid='])
    assert rc_record['returncode'] == 1 and not after.strip(), 'worker still present after reported reap'
    print(f'{boundary}: observed worker {pid}, host {host}; clean worker exit; '
          f'mapping observer rc={observations["mappings"]["returncode"]}, '
          f'port observer rc={observations["ports"]["returncode"]}')


if __name__ == '__main__':
    pw, output = sys.argv[1:]
    for boundary in ['pre_ready', 'post_apply']:
        observe(pw, Path(output) / boundary, boundary)
