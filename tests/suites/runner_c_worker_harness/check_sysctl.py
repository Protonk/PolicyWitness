"""Observe the production sysctl call's capacity and reject a shortened input."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
ABI = ROOT / 'controller/tools/pw_probe_runner'
FIXTURE = ROOT / 'tests/fixtures/worker_lifecycle/sysctl_control.c'
OWNER = 'tests/suites/runner_c_worker_harness/check_sysctl.py'


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def build_and_run(directory, source):
    directory.mkdir()
    worker = directory / 'pw_probe_runner.c'
    worker.write_text(source)
    binary = directory / 'control'
    command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-O2',
               '-Wall', '-Wextra', '-Wno-deprecated-declarations', '-I', str(ABI),
               '-DPW_SYSCTL_WORKER_SOURCE=' + json.dumps(str(worker)),
               str(FIXTURE), '-lsandbox', '-o', str(binary)]
    save(directory / 'build-command.json', command)
    result = subprocess.run(command, capture_output=True, timeout=60)
    (directory / 'build.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, f'fixture build failed: {directory}/build.log'
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
    (directory / 'stdout.jsonl').write_text(result.stdout)
    (directory / 'stderr').write_text(result.stderr)
    save(directory / 'run.json', {'command': [str(binary)], 'returncode': result.returncode})
    assert result.returncode == 0, f'fixture failed: {directory}/stderr'
    return [json.loads(line) for line in result.stdout.splitlines()]


def check_capacity(receipts):
    assert len(receipts) == 2, receipts
    for row in receipts:
        assert row['incoming_length'] == 4096, 'actual sysctl read capacity is not 4096'


def check_call_and_result(receipts):
    assert [row['failure'] for row in receipts] == [0, 1], receipts
    for row in receipts:
        assert row['calls'] == 1, row
        assert row['target_matches'] == 1 and row['destination_nonnull'] == 1, row
        assert row['new_value_null'] == 1 and row['new_value_length'] == 0, row
        assert row['rc'] == row['failure'], row
        assert row['errno'] == (12 if row['failure'] else 0), row  # Darwin ENOMEM.
        assert row['error_label'] == row['failure'], row


def check_manifest(receipts):
    limits = json.loads((ROOT / 'docs/limits.json').read_text())['limits']
    owned = {row['id'] for row in limits if any(
        ref['path'] == OWNER and ref['kind'] == 'value' for ref in row['checks'])}
    assert owned == {'sysctl_read_bytes'}, f'unchecked sysctl limits ownership: {owned}'
    row = next(row for row in limits if row['id'] == 'sysctl_read_bytes')
    assert all(receipt['incoming_length'] == row['value'] for receipt in receipts), row


def main(out):
    inputs = [FIXTURE, Path(__file__), ROOT / 'docs/limits.json',
              *(path for path in ABI.iterdir() if path.suffix in {'.c', '.h'})]
    save(out / 'source-sha256.json', {str(path.relative_to(ROOT)):
         hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(inputs)})
    source = (ABI / 'pw_probe_runner.c').read_text()
    baseline = build_and_run(out / 'baseline', source)
    check_capacity(baseline)
    check_call_and_result(baseline)
    check_manifest(baseline)
    anchor = '''static void attempt_sysctl_read(pw_shm_slot_t *slot) {
    char buf[PW_SYSCTL_READ_BYTES];
    size_t len = sizeof(buf);'''
    assert source.count(anchor) == 1, 'sysctl capacity mutation anchor changed'
    shortened_source = source.replace(anchor, anchor.replace('sizeof(buf);', 'sizeof(buf) - 1;'))
    shortened = build_and_run(out / 'shortened', shortened_source)
    check_call_and_result(shortened)
    try:
        check_capacity(shortened)
    except AssertionError as error:
        assert str(error) == 'actual sysctl read capacity is not 4096', str(error)
        rejection = str(error)
    else:
        raise AssertionError('shortened supplied capacity escaped independent oracle')
    save(out / 'observations.json', {'baseline': baseline, 'shortened': shortened,
         'rejected_mutation': rejection})
    print('ok: one non-null 4096-byte read, unchanged PW status/errno and rejected shortened capacity')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
