#!/usr/bin/python3
"""Forward only requested verdicts; retain extra native queries independently."""
import json
from pathlib import Path
import subprocess
import sys
import time
import os

config = json.loads(Path(__file__).with_suffix('.json').read_text())
requested = [json.loads(line) for line in sys.stdin.buffer if line.strip()]
extra = config['queries']
assert not {q['step_id'] for q in requested} & {q['step_id'] for q in extra}
queries = requested + extra
payload = ''.join(json.dumps(q) + '\n' for q in queries).encode()
started = time.monotonic_ns()
child = subprocess.Popen([config['validator'], *sys.argv[1:]], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
receipt_path = Path(config['receipts'], str(os.getpid()) + '.json')
receipt = dict(pid=os.getpid(), target_pid=int(sys.argv[2]), requested=requested,
               extra=extra, start_ns=started, native_validator_pid=child.pid,
               native_validator_reaped=False)
receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
try:
    stdout, stderr = child.communicate(payload, timeout=8)
except subprocess.TimeoutExpired:
    child.kill()
    stdout, stderr = child.communicate(timeout=5)
receipt.update(end_ns=time.monotonic_ns(), returncode=child.returncode,
               native_validator_reaped=True, stdout=stdout.decode(), stderr=stderr.decode())
receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
assert child.returncode == 0
records = [json.loads(line) for line in stdout.splitlines()]
assert [v['step_id'] for v in records] == [q['step_id'] for q in queries]
for value in records[:len(requested)]:
    print(json.dumps(value), flush=True)
