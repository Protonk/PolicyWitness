"""Production exec controls: independent native ledger and rejected mutations.

The golden ledger was captured using the pre-refactor producer with exactly the
same equipment. Normalized descriptor identities remove incidental fd numbers;
every remaining call argument, result, errno, meaningful status and clock value
participates in the digest. This pins policy without interpreting new payloads.
"""
import collections
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / 'controller/tools/pw_probe_runner'
FIXTURE = ROOT / 'tests/fixtures/worker_lifecycle/exec_control.c'
GOLDEN = ROOT / 'tests/fixtures/worker_lifecycle/exec_call_policy.json'


def canonical_ledger(path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.startswith('{'):
            continue
        row = json.loads(line)
        fds = {}
        pipe_index = 0
        calls = []
        for original in row['calls']:
            call = list(original)
            if call[0] == 'pipe' and call[3] == 0:
                stream = ('stdout', 'stderr')[pipe_index]
                pipe_index += 1
                fds[call[1]], fds[call[2]] = stream + '_read', stream + '_write'
                call[1], call[2] = fds[call[1]], fds[call[2]]
            elif call[0] == 'close':
                call[1] = fds[call[1]]
            elif call[0] == 'revents':
                call[2] = fds[call[2]]
            calls.append(call)
        encoded = json.dumps(calls, separators=(',', ':')).encode()
        rows.append(dict(case=row['case'], attempt=row['attempt'],
                         count=len(calls), counts=dict(collections.Counter(c[0] for c in calls)),
                         sha256=hashlib.sha256(encoded).hexdigest()))
    assert len(rows) >= 55, f'incomplete native ledger: {len(rows)} attempts'
    return rows



if __name__ == '__main__':
    raise SystemExit('Use tests/run.sh --case runner_c_worker_harness/exec_control_states')
