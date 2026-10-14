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
result = subprocess.run([config['validator'], *sys.argv[1:]], input=payload,
                        capture_output=True, timeout=8)
receipt = dict(pid=os.getpid(), target_pid=int(sys.argv[2]), requested=requested,
               extra=extra, start_ns=started, end_ns=time.monotonic_ns(),
               returncode=result.returncode, stdout=result.stdout.decode(),
               stderr=result.stderr.decode())
Path(config['receipts'], str(os.getpid()) + '.json').write_text(json.dumps(receipt, indent=2) + '\n')
assert result.returncode == 0
records = [json.loads(line) for line in result.stdout.splitlines()]
assert [v['step_id'] for v in records] == [q['step_id'] for q in queries]
for value in records[:len(requested)]:
    print(json.dumps(value), flush=True)
