"""One-off investigation runner; use under tests/lib/checkout_lock.sh.

Usage: python3 records/safe-wait-time/run_probes.py /private/tmp/fresh-output [orders]
Writes raw commands, compiler diagnostics, observations, and native log capture.
The output directory must not already exist. No app or production source changes.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1]).resolve()
out.mkdir(exist_ok=False)
commands = []


def run(argv, name, timeout=30):
    start = time.time_ns()
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, cwd=root)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    record = dict(argv=[str(v) for v in argv], pid=proc.pid, returncode=proc.returncode,
                  timed_out=timed_out, started_unix_ns=start, ended_unix_ns=time.time_ns(),
                  reaped=True, stdout=name + '.stdout', stderr=name + '.stderr')
    (out / (name + '.stdout')).write_bytes(stdout)
    (out / (name + '.stderr')).write_bytes(stderr)
    commands.append(record)
    (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    if timed_out or proc.returncode:
        raise RuntimeError(record)
    return stdout


for name, argv in [('os', ['sw_vers']), ('kernel', ['uname', '-a']),
                   ('clang', ['xcrun', 'clang', '--version']),
                   ('sdk', ['xcrun', '--show-sdk-path']),
                   ('commit', ['git', 'rev-parse', 'HEAD'])]:
    run(argv, name)
flags = ['xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-O2', '-g', '-Wall', '-Wextra',
         '-Wno-deprecated-declarations', '-I', str(root / 'controller/tools/pw_probe_runner')]
for name in ['clock', 'order']:
    run(flags + [str(root / f'records/safe-wait-time/{name}_probe.c'), '-lsandbox',
                 '-o', str(out / (name + '-probe'))], 'build-' + name)
rows = []
for policy in (range(3) if len(sys.argv) == 2 else []):
    for kind in range(4):
        for warm in range(2):
            for repeat in range(3):
                name = f'clock-{policy}-{kind}-{warm}-{repeat}'
                raw = run([str(out / 'clock-probe'), str(kind), str(warm), str(policy), '5000000'], name)
                row = json.loads(raw)
                assert row['reaped'] and row['wait_status'] == 0 and row['finished'] == 1
                assert row['compile_ok'] == 1 and row['apply_rc'] == 0
                rows.append(dict(name=name, **row))
(out / 'clocks.json').write_text(json.dumps(rows, indent=2) + '\n')
orders = []
for mode in range(10):
    row = json.loads(run([str(out / 'order-probe'), str(mode)], f'order-{mode}'))
    assert row['reaped'] and row['status'] == 0 and row['killed'] == 0
    expected_code = {0: 1, 1: 1, 2: 8, 5: 8, 7: 11}.get(mode, 0)
    assert row['code'] == expected_code, row
    success = mode in [3, 6, 8, 9]
    assert all(bool(p['ack']) == success and bool(p['action_completed']) == success for p in row['phases']), row
    if success:
        assert all(p['action_rc'] == 0 for p in row['phases']), row
    if mode == 8:
        assert row['phases'][1]['observations'] == 2, row
    orders.append(row)
(out / 'ordering.json').write_text(json.dumps(orders, indent=2) + '\n')
run(['/usr/bin/log', 'show', '--last', '5m', '--style', 'json', '--predicate',
     'process == "kernel" AND eventMessage CONTAINS "clock-probe("'], 'deny-log', timeout=30)
files = [root / f'records/safe-wait-time/{name}' for name in ['clock_probe.c', 'order_probe.c', 'run_probes.py']]
files += list((root / 'controller/tools/pw_probe_runner').glob('*.[ch]'))
(out / 'source-hashes.json').write_text(json.dumps({str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                  for p in files}, indent=2) + '\n')
print(json.dumps(dict(clock_processes=len(rows), clock_reads=sum(r['count'] for r in rows),
                      clock_failures=sum(r['failures'] for r in rows), ordering_cases=len(orders))))
