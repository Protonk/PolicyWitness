"""Compare compiled C values with the inventory; exercise the native line cap."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# Mapping and subtraction rules belong to the test, not to the manifest.
ABI_LIMITS = {
    'policy_source': ('PW_SHM_POLICY_BYTES', 1),
    'probe_steps': ('PW_SHM_MAX_STEPS', 0),
    'policy_parameters': ('PW_SHM_MAX_PARAMS', 0),
    'step_id': ('PW_SHM_STEP_ID_MAX', 1),
    'attempt_target': ('PW_SHM_TARGET_MAX', 1),
    'exec_arguments': ('PW_SHM_MAX_ARGV', 1),
    'exec_argument': ('PW_SHM_ARGV_BYTES', 1),
    'parameter_key': ('PW_SHM_PARAM_KEY_MAX', 1),
    'parameter_value': ('PW_SHM_PARAM_VALUE_MAX', 1),
    'exec_stream': ('PW_SHM_CHILD_OUTPUT_BYTES', 1),
    'worker_diagnostic': ('PW_SHM_DIAGNOSTIC_BYTES', 1),
    'applied_profile': ('PW_SHM_CAPTURE_BYTES', 0),
    'observed_path': ('PW_SHM_OBSERVED_PATH_MAX', 1),
    'attempt_error': ('PW_SHM_ERROR_MAX', 1),
}
NATIVE_LIMITS = {'worker_proceed_wait', 'exec_child_wait', 'exec_step_descriptors', 'exec_descriptor_reserve', 'validator_query_payload'}


def values(text):
    return {key: int(value) for key, value in (line.split('=') for line in text.splitlines())}


def compare(limits, observed):
    owner = Path(__file__).relative_to(ROOT).as_posix()
    owned = {row['id']: row['value'] for row in limits
             if any(ref['path'] == owner and ref['kind'] == 'value' for ref in row['checks'])}
    assert owned == observed, f'compiled C limits disagree: documented={owned}, actual={observed}'


def query_boundary(validator):
    # Independent behavioral oracle. Manifest edits cannot change these inputs.
    probe = json.dumps({'step_id': 'boundary', 'operation': 'file-read-data',
                        'filter_type': 'NONE'}, separators=(',', ':')).encode()
    exact = probe + b' ' * (65534 - len(probe))
    over = exact + b' '
    result = subprocess.run([str(validator), '--batch', str(os.getpid())],
                            input=exact + b'\n' + over + b'\n' + probe + b'\n',
                            capture_output=True, timeout=10, check=True)
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(rows) == 3, rows
    assert rows[0]['step_id'] == 'boundary' and rows[0]['outcome'] != 'parse_error', rows
    assert rows[1]['step_id'] is None and rows[1]['outcome'] == 'parse_error', rows
    assert 'cap' in rows[1]['error'], rows
    assert rows[2]['step_id'] == 'boundary' and rows[2]['outcome'] != 'parse_error', rows


def control_character_round_trip(validator):
    # Foundation escapes every control character as \uXXXX and non-BMP text as a
    # surrogate pair; json.dumps with ensure_ascii does the same. The verdict must
    # decode as strict JSON with the submitted strings intact and no raw control
    # byte. Malformed escapes are per-probe parse errors that do not stop later
    # probes. The unsandboxed test process itself is the checked pid.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='pw-control-', dir='/private/tmp') as temp:
        path = Path(temp) / 'f\x01\x08\x1f\U0001F600\u2028'
        path.write_bytes(b'x')
        probes = [
            {'step_id': 'id\x01\x08\x0c\x1b', 'operation': 'file-read-data', 'filter_type': 'PATH', 'filter_value': str(path)},
            {'step_id': 'nul', 'operation': 'file-read-data', 'filter_type': 'PATH', 'filter_value': str(path)},
            {'step_id': 'lone', 'operation': 'file-read-data', 'filter_type': 'PATH', 'filter_value': str(path)},
            {'step_id': 'after', 'operation': 'file-read-data', 'filter_type': 'NONE'},
        ]
        lines = [json.dumps(probe, separators=(',', ':')).encode() for probe in probes]
        assert b'\\u0001' in lines[0] and b'\\ud83d' in lines[0].lower(), lines[0]
        lines[1] = lines[1].replace(b'"nul"', b'"n\\u0000l"')
        lines[2] = lines[2].replace(b'"lone"', b'"l\\ud83dne"')
        result = subprocess.run([str(validator), '--batch', str(os.getpid())],
                                input=b'\n'.join(lines) + b'\n', capture_output=True, timeout=10, check=True)
        raw = result.stdout.splitlines()
        assert len(raw) == 4, raw
        assert all(b < 0x20 for line in raw for b in []) or all(byte >= 0x20 for line in raw for byte in line), raw
        rows = [json.loads(line) for line in raw]
        assert rows[0]['step_id'] == probes[0]['step_id'] and rows[0]['filter_value'] == str(path), rows[0]
        assert rows[0]['outcome'] == 'allow', rows[0]
        assert rows[1]['step_id'] is None and rows[1]['outcome'] == 'parse_error', rows[1]
        assert rows[2]['step_id'] is None and rows[2]['outcome'] == 'parse_error', rows[2]
        assert rows[3]['step_id'] == 'after' and rows[3]['outcome'] == 'allow', rows[3]


def main():
    artifacts = Path(sys.argv[1])
    printer = values((artifacts / 'printer.out').read_text())
    observed = {ident: printer[key] - subtract for ident, (key, subtract) in ABI_LIMITS.items()}
    native = {}
    for binary in ('worker_limits', 'validator_limits'):
        native.update(values(subprocess.check_output([str(artifacts / binary)], text=True, timeout=10)))
    assert set(native) == NATIVE_LIMITS, native
    observed.update(native)
    limits = json.loads((ROOT / 'docs/limits.json').read_text())['limits']
    compare(limits, observed)
    # A self-consistent generated document must not hide a changed inventory.
    altered = json.loads(json.dumps(limits))
    next(row for row in altered if row['id'] == 'policy_source')['value'] += 1
    try:
        compare(altered, observed)
    except AssertionError:
        pass
    else:
        raise AssertionError('changed manifest value escaped compiled-value check')
    query_boundary(artifacts / 'validator_limits')
    control_character_round_trip(artifacts / 'validator_limits')
    print(f'ok: {len(observed)} compiled C limits; exact query boundary, drain/recovery and control-character round trip')


if __name__ == '__main__':
    main()
