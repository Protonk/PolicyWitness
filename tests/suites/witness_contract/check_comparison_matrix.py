"""Run the comparison matrix's S, B and C specimens through the CLI and check
every step against its row in tests/fixtures/comparison/matrix.json.

Expectations come from the fixture, which was reviewed against the D1 matrix
and the independent controls recorded here: a direct EACCES open and spawn of
the mode-000 files, direct spawns of the helper copies, direct lookups of the
mach names, and file bytes compared before and after each run. Nothing here
derives an expectation from the reply.

Specimen B is steered through `_test_overrides.validator_executable_path`
(stub_validator.py beside the fixture) and ends in validator_no_reply; its
expectations come from the submitted scopes and the file controls, never from
the stub's transcript. B unlinks the files it queries, so every file is
recreated before each run, including after a failed one.
"""
import errno
import json
import re
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
from run_capture import RunCapture

FIXTURE_DIR = Path(__file__).resolve().parents[2] / 'fixtures/comparison'
FIXTURE = json.loads((FIXTURE_DIR / 'matrix.json').read_text())
STUB = FIXTURE_DIR / 'stub_validator.py'
WITNESS = b'independent witness\n'
CLI_ARGS = ['--no-log-capture']


def expand(value, root):
    if isinstance(value, str):
        return value.replace('{{SCEN_ROOT}}', str(root)).replace('{{STUB_VALIDATOR}}', str(STUB))
    if isinstance(value, list):
        return [expand(v, root) for v in value]
    if isinstance(value, dict):
        return {k: expand(v, root) for k, v in value.items()}
    return value


def compile_helper(path, exit_code):
    """A helper that exits with a fixed status. Compiled here rather than copied
    from the system volume: copies of some platform binaries are killed at launch."""
    source = path.with_suffix('.c')
    source.write_text(f'int main(void) {{ return {int(exit_code)}; }}\n')
    subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                    str(source), '-o', str(path)], check=True, capture_output=True, timeout=120)
    source.unlink()


def prepare_files(root):
    """Create every fixture file in its required pre-run state; return the bytes to compare later."""
    before = {}
    for name, spec in FIXTURE['files'].items():
        path = root / name
        if path.exists():
            path.chmod(0o600)
            path.unlink()
        if spec['state'] == 'absent':
            continue
        if spec['state'] == 'regular':
            path.write_bytes(spec['content'].encode())
        elif spec['state'] == 'compiled':
            compile_helper(path, spec['exit_code'])
        path.chmod(int(spec['mode'], 8))
        if spec['mode'] != '0000':
            before[name] = path.read_bytes()
    return before


def restore_modes(root):
    for name, spec in FIXTURE['files'].items():
        path = root / name
        if path.exists():
            path.chmod(0o600)


def direct_controls(root, out):
    """Independent OS observations the rows cite; recorded beside the runs."""
    records = {}
    locked = root / 'locked'
    try:
        with locked.open('rb'):
            raise AssertionError('mode-000 file opened outside PW')
    except OSError as exc:
        assert exc.errno == errno.EACCES, exc
        records['locked_open'] = {'errno': exc.errno}
    helper_locked = root / 'helper_locked'
    try:
        subprocess.run([str(helper_locked)], capture_output=True, timeout=5)
        raise AssertionError('mode-000 helper spawned outside PW')
    except OSError as exc:
        assert exc.errno == errno.EACCES, exc
        records['helper_locked_spawn'] = {'errno': exc.errno}
    for name, expected in (('helper_true', 0), ('helper_false', 1)):
        result = subprocess.run([str(root / name)], capture_output=True, timeout=5)
        assert result.returncode == expected, (name, result.returncode)
        records[name + '_spawn'] = {'exit_code': result.returncode}
    for name in ('absent', 'absent_target', 'created'):
        assert not (root / name).exists(), name
    records['absent_before'] = ['absent', 'absent_target', 'created']
    (out / 'direct-controls.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def lookup(step, dotted):
    current = step
    for key in dotted.split('.'):
        if not isinstance(current, dict) or key not in current:
            return consumer.ABSENT
        current = current[key]
    return current


def check_assert(row, step, root, failures):
    for key, want in row['assert'].items():
        got = lookup(step, key)
        want = expand(want, root)
        if want == '>0':
            if not (isinstance(got, int) and got > 0):
                failures.append(f"{row['id']}: {key} expected a positive integer, got {got!r}")
        elif want is None:
            if got is not consumer.ABSENT and got is not None:
                failures.append(f"{row['id']}: {key} expected absent or null, got {got!r}")
        elif got != want:
            failures.append(f"{row['id']}: {key} expected {want!r}, got {got!r}")


def check_row(row, step, root, failures):
    want = expand(row['comparison'], root)
    got = step.get('comparison')
    if not isinstance(got, dict):
        failures.append(f"{row['id']}: missing comparison")
        return
    for key in consumer.COMPARISON_KEYS:
        if got.get(key) != want[key]:
            failures.append(f"{row['id']}: comparison.{key} expected {want[key]!r}, got {got.get(key)!r}")
    if consumer.query_column(step) != row['query']:
        failures.append(f"{row['id']}: query column expected {row['query']!r}, got {consumer.query_column(step)!r}")
    check_assert(row, step, root, failures)


def check_expected(label, envelope, expected, root, failures):
    runner = (envelope.get('data') or {}).get('runner_result') or {}
    for key, want in expected.items():
        if key == 'note':
            continue
        if key == 'steps.length':
            got = len(runner.get('steps') or [])
        elif key.startswith('result.'):
            got = lookup(envelope['result'], key[len('result.'):])
        elif key.startswith('runner_result.'):
            got = lookup(runner, key[len('runner_result.'):])
        else:
            got = lookup(runner, key)
        want = expand(want, root)
        if got != want and not (want is None and got is consumer.ABSENT):
            failures.append(f"{label}: {key} expected {want!r}, got {got!r}")


def check_effects(specimen_rows, before, root, failures):
    for row in specimen_rows:
        for name, state in (row.get('effects') or {}).items():
            path = root / name
            if state == 'absent' and path.exists():
                failures.append(f"{row['id']}: {name} still exists after the run")
            if state == 'present' and not path.exists():
                failures.append(f"{row['id']}: {name} was not created")
            size = re.fullmatch(r'present, (\d+) bytes?', state)
            if size and (not path.exists() or path.stat().st_size != int(size.group(1))):
                failures.append(f"{row['id']}: {name} expected {size.group(1)} bytes, "
                                f"got {path.stat().st_size if path.exists() else 'absent'}")
    for name, spec in FIXTURE['files'].items():
        if spec['effect'].startswith('unchanged bytes') and name in before:
            path = root / name
            if not path.exists() or path.read_bytes() != before[name]:
                failures.append(f"{name}: bytes changed although no row mutates it")


def run_specimen(pw, out, name, root):
    spec = FIXTURE['specimens'][name]
    request = {'schema_version': 1, 'specimen_id': spec['specimen_id'],
               'policy': {'format': 'sbpl', 'sbpl_source': expand(spec['policy'], root)},
               'probe_plan': expand(spec['probe_plan'], root)}
    if spec.get('test_overrides'):
        request['_test_overrides'] = expand(spec['test_overrides'], root)
    with RunCapture(pw, out / name, request, cli_args=CLI_ARGS) as run:
        rc = run.wait(timeout=90)
        envelope = run.load_json()
    return rc, envelope


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    out.mkdir(parents=True, exist_ok=True)
    failures = []
    summary = {}
    with tempfile.TemporaryDirectory(prefix='pw-matrix-', dir='/private/tmp') as work:
        root = Path(work)
        try:
            for name in ('S', 'B', 'C'):
                before = prepare_files(root)
                if name == 'S':
                    direct_controls(root, out)
                rc, envelope = run_specimen(pw, out, name, root)
                restore_modes(root)
                errors = consumer.validate(envelope)
                if errors:
                    failures.append(f'{name}: consumer validation: {errors}')
                    continue
                check_expected(name, envelope, FIXTURE['specimens'][name]['expected'], root, failures)
                rows = [r for r in FIXTURE['rows'] if r['specimen'] == name]
                steps = consumer.steps(envelope)
                by_id = {s.get('step_id'): s for s in steps}
                for row in rows:
                    step = by_id.get(row['step_id'])
                    if step is None:
                        failures.append(f"{row['id']}: step {row['step_id']} missing from the reply")
                        continue
                    check_row(row, step, root, failures)
                    # The same row selected by field, through the consumer.
                    chosen = consumer.select(steps, step_id=row['step_id'],
                                             observation=row['comparison']['observation'], order=row['comparison']['order'])
                    if len(chosen) != 1:
                        failures.append(f"{row['id']}: select by observation/order found {len(chosen)} steps")
                check_effects(rows, before, root, failures)
                summary[name] = {'exit_code': rc, 'normalized_outcome': envelope['result']['normalized_outcome'],
                                 'rows': [r['id'] for r in rows]}
        finally:
            restore_modes(root)
    (out / 'matrix-summary.json').write_text(json.dumps({'rows_checked': sum(len(v['rows']) for v in summary.values()),
                                                         'specimens': summary, 'failures': failures}, indent=2) + '\n')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f"{sum(len(v['rows']) for v in summary.values())} matrix rows matched their records, raw fields and file effects")


if __name__ == '__main__':
    main()
