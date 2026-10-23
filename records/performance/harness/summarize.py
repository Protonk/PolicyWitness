#!/usr/bin/env python3
"""Verify a measurement directory, then export summaries outside the raw evidence."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import sys

MEASURES = ('W', 'C', 'R', 'S', 'X', 'G', 'L', 'L_inner', 'U',
            'client_residual_including_X', 'client_residual_without_X', 'controller_residual')


def read(path):
    return json.loads(path.read_text())


def get(value, *keys):
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def verify(directory):
    covered = set()
    checksum = directory / 'SHA256SUMS'
    if checksum.exists():
        for line in checksum.read_text().splitlines():
            expected, name = line.split('  ', 1)
            path = directory / name
            if name in covered or path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
                raise ValueError(f'unsafe or repeated checksum path: {name}')
            with path.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if len(expected) != 64 or actual != expected:
                raise ValueError(f'checksum mismatch: {name}')
            covered.add(name)
    all_files = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
                 if p.is_file() and p != checksum}
    return sorted(all_files - covered)


def measures(entry, status, envelope):
    values, unavailable = {}, {}
    def put(name, value, applicability=True, fault=False):
        if not applicability:
            unavailable[name] = 'inapplicable'
        elif fault:
            unavailable[name] = 'invalid'
        elif value is None:
            unavailable[name] = 'absent'
        elif not numeric(value) or value < 0:
            unavailable[name] = 'invalid'
        else:
            values[name] = value

    put('W', status.get('wall_ms'), fault=bool(status.get('sleep_clock_error')))
    usage = status.get('rusage')
    user, system = get(usage, 'ru_utime'), get(usage, 'ru_stime')
    put('U', (user + system) * 1000 if numeric(user) and numeric(system) else None)
    data = get(envelope, 'data')
    client = get(data, 'runner_client')
    runner = get(data, 'runner_result')
    subprocess = get(runner, 'runner_subprocess')
    is_run = entry['specimen'] is not None
    before, after = get(client, 'started_at_unix_ms'), get(client, 'ended_at_unix_ms')
    if numeric(before) and numeric(after):
        put('C', after - before, is_run)
    else:
        put('C', None, is_run, fault=(before is not None or after is not None))
    for letter, key in (('R', 'ready_wait'), ('G', 'exit_grace_wait')):
        wait = get(subprocess, key)
        applicable = is_run and not (letter == 'G' and get(subprocess, 'grace_end') == 'not_entered')
        put(letter, get(wait, 'elapsed_ms'), applicable, get(wait, 'clock_fault') is True)
    sentinel = get(subprocess, 'sentinel_wait')
    elapsed, excluded = get(sentinel, 'elapsed_ms'), get(sentinel, 'excluded_ms')
    fault = get(sentinel, 'clock_fault') is True
    put('X', excluded, is_run, fault)
    put('S', elapsed - excluded if numeric(elapsed) and numeric(excluded) else None, is_run,
        fault or (elapsed is not None and not numeric(elapsed))
        or (excluded is not None and not numeric(excluded)))
    capture = get(data, 'sandbox_log_capture')
    for letter, item in (('L', get(capture, 'supervision')),
                         ('L_inner', get(capture, 'observer', 'data', 'collection'))):
        put(letter, get(item, 'elapsed_ms'), is_run and entry['capture'],
            get(item, 'cutoff', 'reason') == 'clock_error')
    # These are mixed-clock arithmetic, never measured component durations.
    for name, terms in (('client_residual_including_X', ('C', 'R', 'S', 'G')),
                        ('client_residual_without_X', ('C', 'R', 'S', 'X', 'G')),
                        ('controller_residual', ('W', 'C', 'L'))):
        if not is_run:
            unavailable[name] = 'inapplicable'
            continue
        operands = dict(values)
        if unavailable.get('G') == 'inapplicable':
            operands['G'] = 0  # Grace was explicitly not entered, not merely missing.
        if not entry['capture']:
            operands['L'] = 0  # Disabled log capture has no supervised interval.
        if all(term in operands for term in terms):
            # Retain negative residuals as findings; do not silently discard them.
            values[name] = operands[terms[0]] - sum(operands[t] for t in terms[1:])
        else:
            unavailable[name] = 'invalid' if any(unavailable.get(t) == 'invalid' for t in terms) else 'absent'
    return values, unavailable


def strata(envelope, status):
    data = get(envelope, 'data')
    sub = get(data, 'runner_result', 'runner_subprocess')
    return {'exit_status': status.get('exit_status'), 'term_signal': status.get('term_signal'),
            'outcome': get(envelope, 'result', 'normalized_outcome'),
            'ready_stop': get(sub, 'ready_wait', 'stop'),
            'sentinel_stop': get(sub, 'sentinel_wait', 'stop'),
            'grace_stop': get(sub, 'exit_grace_wait', 'stop'),
            'capture_status': get(data, 'sandbox_log_capture', 'capture_status')}


def distribution(values):
    ordered = sorted(values)
    return {'n': len(ordered), 'minimum': ordered[0], 'median': statistics.median(ordered),
            'p90': ordered[math.ceil(.9 * len(ordered)) - 1], 'maximum': ordered[-1]}


def summarize(directory):
    directory = directory.resolve()
    unattested = verify(directory)
    run, manifest = read(directory / 'run.json'), read(directory / 'manifest.json')
    rows, excluded, groups = [], [], {}
    states, unreadable = collections.Counter(), {}
    listed = set()
    for entry in manifest['entries']:
        sequence = entry['sequence']
        if sequence in listed:
            raise ValueError(f'duplicate sequence: {sequence}')
        listed.add(sequence)
        invocation = directory / entry['directory']
        if not invocation.resolve().is_relative_to(directory):
            raise ValueError('invocation escapes run directory')
        status_path = invocation / 'status.json'
        status = read(status_path) if status_path.exists() else {'sequence': sequence, 'state': 'missing'}
        if status['sequence'] != sequence:
            raise ValueError(f'status sequence mismatch: {sequence}')
        state = status['state']
        states[state] += 1
        row = {'sequence': sequence, 'cell': entry['cell'], 'round': entry['round'], 'pair': entry.get('pair'),
               'warmup': entry['warmup'], 'state': state, 'system_sleep_ms': status.get('system_sleep_ms'),
               'deadline_source': status.get('deadline_source'),
               'effective_deadline_s': status.get('effective_deadline_s')}
        envelope = None
        if state != 'never_started' and (invocation / 'stdout.json').exists():
            try:
                envelope = read(invocation / 'stdout.json')
            except (ValueError, UnicodeError) as exc:
                row['envelope_error'] = str(exc)
        row['stratum'] = strata(envelope, status)
        row['envelope_stamp_unix_ms'] = get(envelope, 'generated_at_unix_ms')
        row['host_pid'] = get(envelope, 'data', 'runner_result', 'pid')
        row['worker_pid'] = get(envelope, 'data', 'runner_result', 'runner_subprocess', 'pid')
        row['error'] = get(envelope, 'result', 'error')
        row['measures_ms'], row['unreadable'] = measures(entry, status, envelope)
        reason = state if state != 'completed' else ('system_sleep' if status.get('sleep_detected') else
                                                    ('sleep_clock_error' if status.get('sleep_clock_error') else None))
        row['excluded_reason'] = reason
        rows.append(row)
        if reason:
            excluded.append({'sequence': sequence, 'state': state, 'reason': reason})
            continue
        cell = entry['cell']
        for measure, why in row['unreadable'].items():
            counter = unreadable.setdefault(cell, {}).setdefault(measure, collections.Counter())
            counter[why] += 1
        key = json.dumps([cell, entry['warmup'], row['stratum']], sort_keys=True)
        group = groups.setdefault(key, {'cell': cell, 'warmup': entry['warmup'], 'stratum': row['stratum'],
                                         'sequences': [], 'values': {}})
        group['sequences'].append(sequence)
        for name, value in row['measures_ms'].items():
            group['values'].setdefault(name, []).append(value)
    for group in groups.values():
        group['n'] = len(group['sequences'])
        group['measures_ms'] = {key: distribution(values) for key, values in group.pop('values').items()}
    expected = {e['directory'] + '/status.json' for e in manifest['entries']}
    actual = {p.relative_to(directory).as_posix() for p in (directory / 'invocations').glob('*/status.json')}
    return {'format_version': 1, 'run_id': run['run_id'], 'raw_directory': str(directory),
            'raw_evidence': 'gitignored; available only in the producing checkout',
            'config': manifest['config'], 'execution_context': manifest['execution_context'],
            'run': run, 'counts': dict(states), 'counts_match_run': dict(states) == run['counts'],
            'unexpected_statuses': sorted(actual - expected), 'missing_statuses': sorted(expected - actual),
            'unattested': unattested, 'excluded': excluded, 'unreadable_by_cell': unreadable,
            'groups': list(groups.values()), 'observations': rows,
            'quantile_method': 'nearest-rank p90; median averages middle two for even n',
            'definitions': {'S': 'sentinel elapsed minus excluded_ms', 'X': 'sentinel excluded_ms',
                            'L_inner': 'shared controller budget start through inner child collection finish',
                            'client_residual_including_X': 'C-R-S-G; includes phase collection X',
                            'client_residual_without_X': 'C-R-S-X-G',
                            'controller_residual': 'W-C-L; includes controller log parsing/correlation',
                            'U': 'wait4 user plus system CPU, milliseconds; controller and reaped descendants',
                            'E': 'envelope creation stamp only, retained per observation; no duration summary'}}


def markdown(summary):
    lines = [f'# Runtime summary: {summary["run_id"]}', '',
             f'Execution context: `{summary["execution_context"]}`. Raw evidence is gitignored and local-only.', '',
             f'Cleanup: `{summary["run"]["cleanup"]["state"]}`. Counts: `{json.dumps(summary["counts"], sort_keys=True)}`.',
             f'Unattested files: {len(summary["unattested"])}. Excluded observations: {len(summary["excluded"])}.', '',
             'Durations below are milliseconds. Each row has one outcome stratum; warm-ups remain separate.', '',
             '| Cell | Warm-up | Outcome / capture / stops / exit | n | W median | W p90 | C median | L median |',
             '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for group in summary['groups']:
        def stat(letter, name):
            value = get(group, 'measures_ms', letter, name)
            return f'{value:.3f}' if numeric(value) else '—'
        s = group['stratum']
        label = ' / '.join(str(s[k]) for k in ('outcome', 'capture_status', 'ready_stop', 'sentinel_stop', 'grace_stop', 'exit_status'))
        lines.append(f'| {group["cell"]} | {group["warmup"]} | {label} | {group["n"]} | '
                     f'{stat("W", "median")} | {stat("W", "p90")} | {stat("C", "median")} | {stat("L", "median")} |')
    lines += ['', 'All per-measure spreads, absent/invalid/inapplicable counts, exclusions, sequence numbers,',
              'and cleanup steps are retained in summary.json. Negative residuals remain observations.', '']
    return '\n'.join(lines)


def export(directory, output):
    if output.resolve().is_relative_to(directory.resolve()):
        raise ValueError('summary destination must be outside the immutable run directory')
    summary = summarize(directory)
    output.mkdir(parents=True, exist_ok=True)
    for name in ('manifest.json', 'conditions-start.json', 'conditions-end.json', 'owner.json', 'run.json', 'SHA256SUMS'):
        source = directory / name
        if source.exists():
            shutil.copyfile(source, output / name)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n')
    (output / 'summary.md').write_text(markdown(summary))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    summary = export(args.directory, args.out)
    print(json.dumps({'run_id': summary['run_id'], 'counts': summary['counts'],
                      'cleanup': summary['run']['cleanup']['state'], 'unattested': len(summary['unattested'])}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
