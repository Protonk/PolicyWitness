"""Independent execution receipt and finite hold equipment for retention controls."""
import json
import os
from pathlib import Path
import sys
import time

out = Path(os.environ['PW_TEST_OUT_DIR'])
receipt = Path(os.environ['RETENTION_RECEIPT'])
grandchild = None
if os.environ.get('RETENTION_GRANDCHILD'):
    # A protected grandchild beyond this case process: it waits for its release file. 'pass' hands it the checkout
    # lock descriptors the claim names, as every protected launch must; 'drop' relies on Python's default, which closes them.
    import subprocess
    fds = []
    if os.environ['RETENTION_GRANDCHILD'] == 'pass':
        for name in ('PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_CHANNEL'):
            try:
                fd = int(os.environ.get(name, ''))
                os.fstat(fd)
            except (ValueError, OSError):
                continue
            fds.append(fd)
    waiter = ('import os, sys, time\n'
              'deadline = time.monotonic() + 30\n'
              'while not os.path.exists(sys.argv[1]) and time.monotonic() < deadline:\n'
              '    time.sleep(0.02)\n')
    grandchild = subprocess.Popen([sys.executable, '-B', '-c', waiter, os.environ['RETENTION_GRANDCHILD_RELEASE']],
                                  pass_fds=tuple(fds), start_new_session=True).pid
with receipt.open('a') as stream:
    stream.write(json.dumps(dict(pid=os.getpid(), out=str(out), run_id=os.environ['PW_TEST_RUN_ID'], grandchild=grandchild,
                                owner=json.loads((out / 'owner.json').read_text()))) + '\n')
if os.environ.get('RETENTION_HOLD'):
    release = Path(os.environ['RETENTION_HOLD'])
    deadline = time.monotonic() + 20
    while not release.exists():
        if time.monotonic() > deadline:
            raise SystemExit('fixture hold timed out')
        time.sleep(0.02)
status = os.environ.get('RETENTION_STATUS', 'pass')
case = out / 'suites/probe/witness'
case.mkdir(parents=True)
(case / 'report.json').write_text(json.dumps(dict(suite='probe', test_id='witness', status=status)))
with (out / 'events.jsonl').open('a') as stream:
    for step, value in [('test_start', 'start'), ('test_end', status)]:
        stream.write(json.dumps(dict(kind='test_event', run_id=os.environ['PW_TEST_RUN_ID'],
                                    suite='probe', test_id='witness', step=step, status=value)) + '\n')
raise SystemExit(1 if status == 'fail' else 0)
