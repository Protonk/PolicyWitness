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


def build_run(directory, source, baseline=False):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'pw_probe_runner.c').write_text(source)
    # Preserve the entire include closure rather than reading live source during
    # compilation. The fixture and every source remain beside build receipts.
    for header in NATIVE.glob('*.h'):
        shutil.copy2(header, directory / header.name)
    shutil.copy2(FIXTURE, directory / 'exec_control.c')
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in directory.iterdir() if p.suffix in ('.c', '.h')}
    (directory / 'source-sha256.json').write_text(json.dumps(sources, indent=2, sort_keys=True) + '\n')
    output = directory / 'exec-control'
    command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
               '-O2', '-std=c11', '-I', str(directory), str(directory / 'exec_control.c'),
               '-lsandbox', '-o', str(output)]
    if baseline:
        command.insert(5, '-DPW_EXEC_LEDGER_BASELINE=1')
    (directory / 'build-command.json').write_text(json.dumps(command, indent=2) + '\n')
    build = subprocess.run(command, capture_output=True, timeout=60)
    (directory / 'build.stdout').write_bytes(build.stdout)
    (directory / 'build.stderr').write_bytes(build.stderr)
    assert build.returncode == 0, f'{directory.name}: compile failed: {build.stderr.decode()}'
    with (directory / 'run.stdout').open('wb') as stdout, (directory / 'run.stderr').open('wb') as stderr:
        run = subprocess.run([str(output)], stdout=stdout, stderr=stderr, timeout=20)
    (directory / 'run.json').write_text(json.dumps(dict(command=[str(output)], returncode=run.returncode), indent=2) + '\n')
    return run.returncode


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = (NATIVE / 'pw_probe_runner.c').read_text()
    assert build_run(out / 'production', source) == 0, 'production controls failed'
    observed = canonical_ledger(out / 'production/run.stdout')
    (out / 'observed-call-policy.json').write_text(json.dumps(observed, indent=2) + '\n')
    expected = json.loads(GOLDEN.read_text())
    assert expected['attempts'] == observed, 'native call order/count/value policy changed; inspect observed-call-policy.json'

    # Faults affect only the disposable producer's assembled payload. All native
    # calls and unchanged assertions are the same as the production control.
    marker = '    slot->exec_valid = 1;'
    assert source.count(marker) == 1, 'exec assembly boundary changed'
    mutations = {
        'collection_from_final_reap': 'slot->exec_leader_exit_observed = reaped == child;',
        'esrch_as_success': 'if (slot->exec_group_errno == ESRCH) { slot->exec_group_rc = 0; slot->exec_group_errno = 0; }',
        'fallback_from_group': 'if (slot->exec_fallback_present) { slot->exec_fallback_rc = slot->exec_group_rc; slot->exec_fallback_errno = slot->exec_group_errno; }',
        'status_after_pending_wait': 'if (reaped != child) { slot->exec_reap_wait_rc = child; slot->exec_reap_stop = PW_EXEC_REAP_REAPED; }',
        'revents_as_native_errno': 'if (slot->exec_stdout_poll_revents || slot->exec_stderr_poll_revents) slot->exec_poll_errno = EIO;',
        'local_deadline_as_native_errno': 'if (slot->exec_reap_stop == PW_EXEC_REAP_DEADLINE) slot->exec_reap_wait_errno = ETIMEDOUT;',
    }
    expected_assertions = {
        'collection_from_final_reap': 'slot->exec_leader_exit_observed == leader',
        'esrch_as_success': 'slot->exec_group_rc == group->rc && slot->exec_group_errno == group->error',
        'fallback_from_group': 'slot->exec_fallback_rc == fallback->rc && slot->exec_fallback_errno == fallback->error',
        'status_after_pending_wait': 'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error',
        'revents_as_native_errno': 'slot->exec_waitid_errno == wait_error && slot->exec_poll_errno == poll_failure',
        'local_deadline_as_native_errno': 'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error',
    }
    results = []
    for name, change in mutations.items():
        code = source.replace(marker, '    ' + change + '\n' + marker)
        status = build_run(out / name, code)
        assert status != 0, f'unchanged native assertions accepted mutation {name}'
        error = (out / name / 'run.stderr').read_text()
        assert 'Assertion failed:' in error and expected_assertions[name] in error, f'{name} failed outside its designated oracle: {error}'
        results.append(dict(mutation=name, returncode=status, assertion=error.strip()))
    (out / 'rejected-mutations.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'ok: {len(observed)} attempts preserve native call policy; six wrong fact promotions rejected')


if __name__ == '__main__':
    main()
