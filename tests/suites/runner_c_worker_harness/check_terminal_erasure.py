"""Independent full-capacity and done-boundary cleanup oracles, with mutations."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
ABI = ROOT / 'controller/tools/pw_probe_runner'
FIXTURE = ROOT / 'tests/fixtures/extension_controls/terminal_control.c'


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def build(directory, source=None):
    directory.mkdir()
    command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra',
               '-Wno-deprecated-declarations', '-I', str(ABI)]
    if source is not None:
        path = directory / 'pw_probe_runner.c'
        path.write_text(source)
        command.append('-DPW_TERMINAL_WORKER_SOURCE=' + json.dumps(str(path)))
    command += [str(FIXTURE), '-lsandbox', '-o', str(directory / 'control')]
    save(directory / 'build-command.json', command)
    result = subprocess.run(command, capture_output=True, timeout=60)
    (directory / 'build.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, f'fixture build failed: {directory}/build.log'
    return directory / 'control'


def run(binary, scenario):
    result = subprocess.run([str(binary), scenario], capture_output=True, text=True, timeout=10)
    (binary.parent / (scenario + '.stdout')).write_text(result.stdout)
    (binary.parent / (scenario + '.stderr')).write_text(result.stderr)
    assert result.returncode == 0, f'control failed: {scenario}: rc={result.returncode}: {result.stderr}'
    value = json.loads(result.stdout)
    assert value['capacity'] == 16384 and value['tail_seeded'] == 1, value
    assert not value['cleanup_kill'], value
    assert value['outbound_preserved'] == value['unsettled_preserved'] == 1, value
    assert value['release_calls'] == (1 if scenario == 'explicit_release' else 0), value
    return value


def whole_buffer(value):
    assert value['final_zero'] == 1 and value['incomplete_erases'] == 0, 'full-capacity erasure failed'


def publication(value):
    assert value['boundary_zero'] == 1, 'erasure before done publication failed'


def rejected(check, value, expected):
    try:
        check(value)
    except AssertionError as error:
        assert str(error) == expected, str(error)
        return str(error)
    raise AssertionError('negative mutation escaped independent oracle')


def main(out):
    baseline = build(out / 'baseline')
    # Original codes and publication shapes on every reachable accepted-channel
    # ordinary early-return branch. The parameter-NUL defense is unreachable
    # after production's forced termination and is not fabricated here.
    early = {'param_capacity': (8, 5), 'length_expectation': (10, 12), 'clock_setup': (12, 1),
             'policy_read': (7, 3), 'policy_overflow': (7, 2), 'length_mismatch': (11, 13),
             'policy_nul': (9, 9)}
    results = {}
    for scenario, (code, failure) in early.items():
        v = results[scenario] = run(baseline, scenario)
        whole_buffer(v)
        assert v['exit_code'] == code and not v['signal'], v
        assert not any(v[key] for key in ('done', 'applied', 'ack', 'completed', 'consume_calls')), v
        assert v['failure'] == 1 and v['code'] == failure and v['boundary_zero'] == -1, v
        assert v['setup_disposition'] == 1 and v['exit_requested'] == 0, v
    terminal = ['normal', 'params_create', 'params_set', 'compile', 'apply', 'proceed_refusal',
                'future_release', 'consume', 'consume_failure', 'explicit_release', 'pre_hang']
    for scenario in terminal:
        v = results[scenario] = run(baseline, scenario)
        whole_buffer(v)
        publication(v)
        assert v['done'] == 1 and v['exit_code'] == 0 and not v['signal'] and v['exit_requested'] == 0, v
        if scenario in ('proceed_refusal', 'future_release'):
            assert v['applied'] == 1 and not v['ack'] and not v['consume_calls'] and not v['completed'], v
            assert v['failure'] == 1 and v['code'] == (8 if scenario == 'proceed_refusal' else 11), v
        if scenario in ('params_create', 'params_set', 'compile', 'apply'):
            assert not v['applied'] and not v['ack'] and not v['consume_calls'] and v['failure'] == 1, v
        if scenario in ('consume', 'consume_failure', 'explicit_release'):
            assert v['consume_calls'] == 1 and v['completed'] == 1 and v['erase_calls'] >= 3, v
        if scenario == 'pre_hang':
            assert v['sleep_observed'] == 1 and v['sleep_zero'] == 1, v
    v = results['cancel'] = run(baseline, 'cancel')
    whole_buffer(v)
    assert v['exit_code'] == 0 and v['exit_requested'] == 1 and v['applied'] == 1, v
    assert not any(v[key] for key in ('signal', 'done', 'failure', 'ack', 'completed', 'consume_calls')), v
    for scenario in ('fatal_consume', 'post_signal'):
        v = results[scenario] = run(baseline, scenario)
        assert v['signal'] == 9 and v['exit_code'] == -1 and not v['done'], v
        if scenario == 'fatal_consume':
            assert not v['final_zero'] and v['erase_calls'] == 0 and not v['completed'], v
        else:
            whole_buffer(v)  # normal-path erase happened before the fatal seam
    v = results['not_required'] = run(baseline, 'not_required')
    assert v['exit_code'] == 0 and v['done'] == 1 and v['erase_calls'] == 0 and not v['final_zero'], v

    v = results['rejected_channel'] = run(baseline, 'rejected_channel')
    assert v['setup_disposition'] == 3 and v['done'] == 1 and v['exit_code'] == 0, v
    assert not v['applied'] and not v['apply_calls'] and not v['compile_calls'], v
    assert v['final_zero'] == v['boundary_zero'] == 0, v  # Invalid mapping grants no payload access.

    setup_cases = {'setup_core': (4, -1, 1), 'setup_fstat_close': (6, -1, 5),
                   'setup_mmap_close': (9, 0, 19), 'setup_size': (8, 0, 0), 'setup_header_unmap': (11, 0, 0)}
    for scenario, primary in setup_cases.items():
        v = results[scenario] = run(baseline, scenario)
        assert v['setup_disposition'] == 3 and v['done'] == 1 and v['exit_code'] == 0, v
        assert not any(v[k] for k in ('apply_calls', 'compile_calls', 'read_calls', 'applied', 'ack', 'completed')), v
        assert (v['primary_slot'], v['primary_rc'], v['primary_errno']) == primary, v
        if scenario in ('setup_fstat_close', 'setup_mmap_close'):
            assert v['close_published'] == 1 and v['close_rc'] == -1 and v['close_errno'] == 9 and v['close_flags'] & 8, v
        if scenario == 'setup_header_unmap':
            assert v['unmap_published'] == 1 and v['unmap_rc'] == -1 and v['unmap_errno'] == 22, v
        assert v['final_zero'] == 0, v  # No validated owned payload was acquired.

    source = (ABI / 'pw_probe_runner.c').read_text()
    short_anchor = 'pw_extension_erase(slot->token, PW_EXTENSION_TOKEN_BYTES);'
    assert source.count(short_anchor) == 1, 'accepted erasure mutation anchor changed'
    shortened = source.replace(short_anchor, short_anchor.replace('PW_EXTENSION_TOKEN_BYTES', 'slot->token_length + 1'))
    short = run(build(out / 'shortened', shortened), 'proceed_refusal')
    short_error = rejected(whole_buffer, short, 'full-capacity erasure failed')

    order_anchor = '''    erase_accepted_token();
    atomic_store_explicit(&hdr->done, 1u, memory_order_release);
    PW_TERMINAL_PUBLISHED(hdr);'''
    assert source.count(order_anchor) == 1, 'publication order mutation anchor changed'
    reversed_source = source.replace(order_anchor, '''    atomic_store_explicit(&hdr->done, 1u, memory_order_release);
    PW_TERMINAL_PUBLISHED(hdr);
    erase_accepted_token();''')
    reverse = run(build(out / 'reversed', reversed_source), 'proceed_refusal')
    whole_buffer(reverse)  # post-reap check alone would miss this defect
    reverse_error = rejected(publication, reverse, 'erasure before done publication failed')
    terminal_anchor = '    if (required && primary!=UINT32_MAX) publish_done_and_exit(hdr);'
    assert source.count(terminal_anchor) == 1, 'terminal setup mutation anchor changed'
    continuing = source.replace(terminal_anchor, '    /* deliberate control: continue past required setup refusal */')
    refused = run(build(out / 'continuing', continuing), 'setup_core')
    def no_policy_calls(value):
        assert value['apply_calls'] == value['compile_calls'] == value['read_calls'] == 0, 'terminal setup reached policy processing'
    continuation_error = rejected(no_policy_calls, refused, 'terminal setup reached policy processing')
    save(out / 'observations.json', dict(baseline=results, shortened=short, reversed=reverse,
         rejected_mutations=dict(shortened=short_error, reversed=reverse_error, continuing=continuation_error), continuing=refused))
    print('ok: full-capacity erasure, erase-before-done, unchanged departures and three rejected mutations')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
