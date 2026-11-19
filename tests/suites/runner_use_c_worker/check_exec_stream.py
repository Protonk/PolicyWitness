"""Exec stream text and stream counts beside the direct bytes of the same command.

Each contrast runs one argument array directly, with an empty environment and
stdin at /dev/null as the worker gives it, and through an exec/spawn attempt
under (allow default). The reply's text and its stream counts are compared
separately, each with the direct output. The retained count, the truncation
state and the exactness each contrast expects are authored in the table below;
none is taken from the reply. A direct run is a different process from the one
PolicyWitness spawned: the comparison relies on these commands being
deterministic.
"""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import build_context
import consumer
from run_capture import RunCapture

MARKER = '\n... [truncated]'
REPEATED_E_ACUTE = 'BEGIN {printf "%s";for(i=0;i<2000;i++)printf "é"}'
STREAMS = object()

# direct: the byte count the direct run must produce (an equipment check).
# retained: child bytes the text represents, marker excluded.
CONTRASTS = {
    'exec_stream_embedded_nul': dict(
        program='/usr/bin/printf', args=['HEAD\\000TAIL'],
        direct=9, retained=9, truncated=False, exact=True),
    'exec_stream_nul_before_overflow': dict(
        program='/usr/bin/printf', args=['HEAD\\000%02048d', '0'],
        direct=2053, retained=1007, truncated=True, exact=True),
    'exec_stream_split_utf8': dict(
        program='/usr/bin/awk', args=[REPEATED_E_ACUTE % 'xx'],
        direct=4002, retained=1006, truncated=True, exact=True),
    'exec_stream_aligned_utf8': dict(
        program='/usr/bin/awk', args=[REPEATED_E_ACUTE % 'x'],
        direct=4001, retained=1007, truncated=True, exact=True),
    'exec_stream_invalid_utf8': dict(
        program=STREAMS, args=['17', '0', '255'],
        direct=17, retained=17, truncated=False, exact=False),
    'exec_stream_exact_limit': dict(
        program=STREAMS, args=['1023', '0', '65'],
        direct=1023, retained=1023, truncated=False, exact=True),
}


def strictly_decodable(data):
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True


def main():
    pw, out_arg, name = sys.argv[1:]
    out = Path(out_arg).resolve()
    row = CONTRASTS[name]
    program = row['program']
    if program is STREAMS:
        program = str(out / 'streams')
        source = Path(__file__).resolve().parents[2] / 'fixtures/exec/streams.c'
        subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
                        '-std=c11', str(source), '-o', program], check=True, timeout=120)
    argv = [program, *row['args']]

    direct = subprocess.run(argv, env={}, stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
    (out / 'direct.stdout').write_bytes(direct.stdout)
    (out / 'direct.stderr').write_bytes(direct.stderr)
    assert direct.returncode == 0 and direct.stderr == b'', (direct.returncode, direct.stderr)
    assert len(direct.stdout) == row['direct'], (len(direct.stdout), row['direct'])
    kept = direct.stdout[:row['retained']]
    # The authored table must describe these bytes: a truncated row cuts at the
    # last scalar boundary within 1,007 bytes, and exactness is strict validity.
    assert row['truncated'] == (row['retained'] < row['direct'])
    assert strictly_decodable(kept) == row['exact'], name
    if row['truncated']:
        assert row['retained'] <= 1007 and (row['retained'] == 1007
            or not strictly_decodable(direct.stdout[:1007])), name
    expected_text = kept.decode('utf-8', errors='replace') + (MARKER if row['truncated'] else '')

    request = dict(
        contract=build_context.candidate_contract(), specimen_id=name,
        policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
        probe_plan=[dict(
            step_id='stream',
            sandbox_check=dict(operation='process-exec*', filter=dict(kind='path', value=program)),
            attempt=dict(kind='exec', action='spawn', target=program, args=row['args']))])
    with RunCapture(pw, out / 'pw', request) as run:
        code = run.wait(timeout=60)
        envelope = run.load_json()
    runner = envelope['data']['runner_result']
    attempt = runner['steps'][0]['attempt']
    observation = attempt.get('exec_observation') or {}
    collection = observation.get('collection') or {}
    stream = collection.get('stdout') or {}
    other = collection.get('stderr') or {}

    process, content, indications = [], [], []

    def check(group, condition, message):
        if not condition:
            group.append(message)

    # Process evidence beside the text.
    check(process, code == 0 and envelope['result']['ok'] is True
          and envelope['result']['normalized_outcome'] == 'finished', f'run result {envelope["result"]!r}')
    check(process, attempt.get('outcome') == 'ok' and attempt.get('rc') == 0, 'attempt outcome or rc')
    check(process, isinstance(attempt.get('child_pid'), int) and attempt['child_pid'] > 0, 'child_pid')
    check(process, attempt.get('child_exit_code') == 0 and attempt.get('child_term_signal') == 0, 'child status')
    check(process, collection.get('stop_reason') == 'leader_exit_and_eof'
          and collection.get('leader_exit_observed') is True, 'collection stop or leader exit')
    check(process, stream.get('eof') is True and other.get('eof') is True, 'stream EOF')
    check(process, (observation.get('cleanup') or {}) == {'state': 'not_requested'}, 'exec cleanup request')
    reap = observation.get('reap') or {}
    check(process, reap.get('stop_reason') == 'reaped'
          and (reap.get('last_wait') or {}).get('rc') == attempt.get('child_pid'), 'leader reap')
    check(process, (runner.get('runner_subprocess') or {}).get('termination_request') is None,
          'worker termination request')

    # Retained content, against the direct bytes.
    text = attempt.get('stdout')
    check(content, isinstance(text, str), f'stdout is {type(text).__name__}, not text')
    check(content, text == expected_text,
          f'stdout differs from the direct bytes: got {len(text or "")} characters {(text or "")[:24]!r}'
          f'...{(text or "")[-20:]!r}; expected {len(expected_text)} characters')
    check(content, 'stderr' not in attempt, f'stderr present for an empty stream: {attempt.get("stderr")!r}')
    if name == 'exec_stream_embedded_nul':
        check(content, text == 'HEAD\u0000TAIL', 'text is not HEAD, U+0000, TAIL')
    if name == 'exec_stream_nul_before_overflow':
        check(content, isinstance(text, str) and text.startswith('HEAD\u00000') and text.endswith(MARKER),
              'text does not begin HEAD, U+0000 and end with the marker')
    if name == 'exec_stream_split_utf8':
        check(content, isinstance(text, str) and '�' not in text
              and text == 'xx' + 'é' * 502 + MARKER, 'text is not xx, 502 e-acute and the marker')
    if name == 'exec_stream_aligned_utf8':
        check(content, isinstance(text, str) and len(text) == 520 and len(text.encode()) == 1023,
              'text is not 520 characters in 1,023 bytes')
    if name == 'exec_stream_invalid_utf8':
        check(content, text == '�' * 17, 'text is not 17 U+FFFD')
    if name == 'exec_stream_exact_limit':
        check(content, text == 'A' * 1023, 'text is not 1,023 A with no marker')

    # Loss indications, against the direct byte count and the authored row.
    observed = {key: stream.get(key) for key in ('bytes_received', 'bytes_retained', 'truncated', 'text_exact')}
    expected = dict(bytes_received=len(direct.stdout), bytes_retained=row['retained'],
                    truncated=row['truncated'], text_exact=row['exact'])
    for key, value in expected.items():
        check(indications, type(observed[key]) is type(value) and observed[key] == value,
              f'stdout {key} is {observed[key]!r}, expected {value!r}')
    empty = dict(bytes_received=0, bytes_retained=0, truncated=False, text_exact=True)
    for key, value in empty.items():
        check(indications, type(other.get(key)) is type(value) and other.get(key) == value,
              f'stderr {key} is {other.get(key)!r}, expected {value!r}')

    reader = consumer.validate(envelope, build_context.candidate_contract())
    receipt = dict(contrast=name, argv=argv, direct_bytes=len(direct.stdout),
                   expected=dict(text_utf8_bytes=len(expected_text.encode()), **expected),
                   observed=dict(stdout_present='stdout' in attempt,
                                 text_utf8_bytes=len(text.encode()) if isinstance(text, str) else None,
                                 text_equals_expected=text == expected_text, **observed),
                   failures=dict(process=process, content=content, indications=indications, reader=reader))
    (out / 'contrast.json').write_text(json.dumps(receipt, indent=2) + '\n')
    for group, failures in receipt['failures'].items():
        for failure in failures:
            print(f'{group}: {failure}')
    if any(receipt['failures'].values()):
        return 1
    print(f'ok: {name}: text equals the direct bytes; received {expected["bytes_received"]}, '
          f'retained {expected["bytes_retained"]}, truncated {expected["truncated"]}, exact {expected["text_exact"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
