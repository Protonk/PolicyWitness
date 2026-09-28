"""Compare compiled C values with the inventory; exercise the native line cap."""
import json
import os
import subprocess
import sys
import tempfile
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
    # Independent JSON encoder supplies raw UTF-8 and escaped representations
    # of the same Unicode scalars. Decode the native output and require identity.
    scalars = ''.join(map(chr, range(1, 32))) + '\x7f\u0080\u07ff\u0800\ud7ff\ue000\uffff\U00010000\U0010ffff' + 'e\u0301é'
    probe = {'step_id': scalars, 'operation': 'file-read-data', 'filter_type': 'NONE'}
    lines = [json.dumps(probe, ensure_ascii=ascii_only, separators=(',', ':')).encode()
             for ascii_only in (False, True)]
    expected = [scalars, scalars]
    invalid = [b'"raw\x01"', b'"raw\t"', b'"raw\r"', b'"raw\x00"',
               b'"\xff"', b'"\xc0\xaf"', b'"\xe2\x82"', b'"\xed\xa0\x80"', b'"\xf4\x90\x80\x80"',
               br'"\u0000"', br'"\ud800"', br'"\udc00"', br'"\ud800\u0041"',
               br'"\ud800\u"', br'"\u12"', br'"\uXY00"', br'"\x01"']
    base = b'{"step_id":%s,"operation":"file-read-data","filter_type":"NONE"}'
    for index, literal in enumerate(invalid):
        lines.extend([base % literal, base % json.dumps(f'after-{index}').encode()])
        expected.extend([None, f'after-{index}'])
    # A raw NUL after otherwise valid JSON must not hide trailing bytes or make
    # an overlong physical line appear short. A following line remains usable.
    lines.extend([base % b'"prefix"' + b'\x00garbage',
                  base % b'"prefix"' + b'\x00' + b'x' * 65536, base % b'"last"'])
    expected.extend([None, None, 'last'])
    result = subprocess.run([str(validator), '--batch', str(os.getpid())],
                            input=b'\n'.join(lines) + b'\n', capture_output=True, timeout=10, check=True)
    raw = result.stdout.split(b'\n')
    assert raw.pop() == b'', 'missing final frame delimiter'
    assert len(raw) == len(expected), (len(raw), len(expected))
    assert all(byte >= 0x20 for line in raw for byte in line), 'raw control in emitted JSON'
    rows = [json.loads(line) for line in raw]
    for row, identity in zip(rows, expected):
        assert row['step_id'] == identity, row
        assert row['outcome'] == ('parse_error' if identity is None else 'allow'), row

    # Preserve the real native path control as well as the string-parser corpus.
    with tempfile.TemporaryDirectory(prefix='pw-control-', dir='/private/tmp') as temp:
        path = Path(temp) / 'f\x01\x08\x1f\U0001f600\u2028'
        path.write_bytes(b'x')
        probe = dict(step_id='path', operation='file-read-data', filter_type='PATH', filter_value=str(path))
        lines = [json.dumps(probe, ensure_ascii=escaped).encode() for escaped in (False, True)]
        result = subprocess.run([str(validator), '--batch', str(os.getpid())],
                                input=b'\n'.join(lines) + b'\n', capture_output=True, timeout=10, check=True)
        rows = [json.loads(line) for line in result.stdout.split(b'\n') if line]
        assert len(rows) == 2, rows
        assert all(row['outcome'] == 'allow' and row['filter_value'] == str(path) for row in rows), rows


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
