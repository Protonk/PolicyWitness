"""Bounded, gated CPU screen on actual held workers; never an adoption oracle.

Uses the historical held workload, neutral CPU oracle and substitution signer.
The candidate changes only the selected unsuccessful tail in a retained copy of
the worker translation unit. No source app or production source is modified.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from check_held_phase_footprint import calibrate, measure, check_wait_measurement
from check_worker_wait_pilot import capture_power, staged_identity
from footprint_observer import FootprintObserver, sha256
from footprint_workloads import ActorHostFixture

TAIL = '        for (uint32_t i = 0; i < 1000u; i++) cpu_relax();'
ROLES = {'release': 'wait_for_proceed', 'activation': 'wait_for_activation'}

# Test-only, machine-qualified prototype. No production deployment gate is
# claimed. Frequency is read before application; each count deadline is local,
# checked, and limited by the last valid continuous-clock remaining allowance.
WFET = r'''
static uint64_t cost_frequency;
static void cost_setup(void) {
    __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(cost_frequency));
}
static void cost_wait(pw_timing_t *timing, uint64_t now, uint64_t remaining) {
    if (timing->cutoff_ticks) {
        if (now >= timing->cutoff_ticks) return;
        if (timing->cutoff_ticks - now < remaining) remaining = timing->cutoff_ticks - now;
    }
    __uint128_t ns = (__uint128_t)remaining * timing->clock.numer / timing->clock.denom;
    if (ns > 100000) ns = 100000;
    if (!ns || !cost_frequency) return;
    __uint128_t ticks = (ns * cost_frequency + 999999999) / 1000000000;
    uint64_t counter, deadline;
    __asm__ volatile("isb\n\tmrs %0, cntvct_el0" : "=r"(counter) :: "memory");
    if (ticks > UINT64_MAX || pw_ticks_add(counter, (uint64_t)ticks, &deadline)) return;
    register uint64_t until __asm__("x17") = deadline;
    __asm__ volatile(".inst 0xd5031011" :: "r"(until) : "memory");
}
'''


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def source_variant(source, role, candidate):
    assert role in ROLES and candidate in ('baseline', 'wfet', 'hint10000')
    if candidate == 'baseline': return source
    begin = source.index('static void ' + ROLES[role] + '(')
    end = source.index('\n/* ---- main', begin) if role == 'release' else source.index('\n/* No allocation', begin)
    body = source[begin:end]
    assert body.count(TAIL) == 1
    if candidate == 'hint10000':
        replacement = TAIL.replace('1000u', '10000u')
    else:
        remaining = 'timing->proceed_ticks - (now - start)' if role == 'release' else 'UINT64_MAX'
        replacement = '        cost_wait(timing, now, ' + remaining + ');'
    source = source[:begin] + body.replace(TAIL, replacement) + source[end:]
    if candidate == 'wfet':
        anchor = 'static void wait_for_activation('
        assert source.count(anchor) == 1
        source = source.replace(anchor, WFET + '\n' + anchor)
        anchor = '    if (pw_timing_setup(&timing, evidence) != 0) { erase_accepted_token(); return 12; }'
        assert source.count(anchor) == 1
        source = source.replace(anchor, anchor + '\n    cost_setup(); /* test-only, pre-apply configuration */')
    return source


def rate_interval(row, role):
    """Counter and elapsed bounds, not a universal statistical confidence interval."""
    check_wait_measurement(row)
    index = 0
    assert row['name'] == ('ordinary' if role == 'release' else 'actor_lifecycle')
    # In the lifecycle cell the issuer (worker 0) is parked, with the subject
    # holding the queried phase. The snapshot independently establishes this.
    count = row['deltas_ns'][index]
    q = row['quantum_ns']
    shortest = row['after']['begin_ns'] - row['before']['end_ns']
    longest = row['after']['end_ns'] - row['before']['begin_ns']
    # Two independently sampled endpoints: allow one declared quantum per end.
    return dict(lower=max(0, count - 2*q)/longest,
                upper=(count + 2*q)/shortest, observed=count/shortest,
                count_ns=count, shortest_ns=shortest, longest_ns=longest,
                endpoint_allowance_ns=2*q,
                other_roles=dict(zip(row['roles'][1:], row['deltas_ns'][1:])))


def compare(rows, role, minimum):
    assert len(rows) == 20 and 0 < minimum < 1
    pairs = []
    for regime in ('rapid', 'idle'):
        for repetition in range(5):
            pair = [r for r in rows if r['regime'] == regime and r['repetition'] == repetition]
            assert len(pair) == 2 and {r['side'] for r in pair} == {'baseline', 'candidate'}
            b, c = [next(r for r in pair if r['side'] == side) for side in ('baseline', 'candidate')]
            assert b['eligible'] and c['eligible'], 'missing eligible pair; no automatic replacement'
            assert b['power'] == c['power'], 'unmatched power'
            bi, ci = [rate_interval(r['measurement'], role) for r in (b, c)]
            gain = bi['lower'] - ci['upper']
            pairs.append(dict(regime=regime, repetition=repetition, baseline=bi, candidate=ci,
                              conservative_gain=gain,
                              worthwhile=gain >= minimum * bi['upper']))
    return dict(pairs=pairs, minimum_fraction=minimum,
                worthwhile_in_every_pair=all(p['worthwhile'] for p in pairs),
                interpretation='Held CPU rate screen only. Positive result requires remaining protocol, '
                'response, whole-request cost and deployment qualification. No energy/capacity inference.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('app', type=Path); p.add_argument('out', type=Path); p.add_argument('identity')
    p.add_argument('observer', type=Path); p.add_argument('bridge', type=Path); p.add_argument('helper', type=Path)
    p.add_argument('--role', choices=ROLES, required=True)
    p.add_argument('--candidate', choices=('baseline', 'wfet', 'hint10000'), required=True)
    p.add_argument('--gate', type=Path, required=True)
    p.add_argument('--minimum', type=float, default=.1)
    p.add_argument('--window', type=int, default=300)
    a = p.parse_args()
    assert not a.gate.exists()
    a.out = a.out.resolve(); a.app = a.app.resolve()
    mut = module('wait_cost_substitution', HERE / 'opt_in/mutations.py')
    source_path = ROOT / 'controller/tools/pw_probe_runner/pw_probe_runner.c'
    source = source_path.read_text()
    shutil.copytree(source_path.parent, a.out / 'worker-source')
    for path in (Path(__file__), HERE / 'check_held_phase_footprint.py', ROOT / 'tests/lib/footprint_workloads.py'):
        shutil.copy2(path, a.out / path.name)
    actor_host = None
    source_app = a.app
    if a.role == 'activation':
        actor_host = ActorHostFixture(a.app, a.out / 'actor-host', a.identity).build()
        source_app = actor_host.app
    sides = ('baseline',) if a.candidate == 'baseline' else ('baseline', 'candidate')
    apps = {}
    for side in sides:
        candidate = 'baseline' if side == 'baseline' else a.candidate
        out = a.out / 'build' / side; out.mkdir(parents=True)
        body = source_variant(source, a.role, candidate)
        (out / 'worker.c').write_text(body)
        worker = out / 'worker'
        mut.command(out / 'compile', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
            '-O2', '-std=c11', '-arch', 'arm64', '-mmacosx-version-min=26.0',
            '-I', source_path.parent, out / 'worker.c', '-lsandbox', '-o', worker], timeout=60)
        mut.command(out / 'disassemble', ['/usr/bin/xcrun', 'otool', '-tvV', worker])
        staging = a.out / 'staging' / side
        apps[side] = mut.signed_copy(source_app, staging, out, a.identity, worker)
    identities = {side: staged_identity(app) for side, app in apps.items()}
    prepared = dict(version=1, role=a.role, candidate=a.candidate, identities=identities,
                    minimum_fraction=a.minimum, window_seconds=a.window, cpu_only=True,
                    source_sha256=sha256(source_path), reader_sha256=sha256(Path(__file__)),
                    neutral_reader_sha256=sha256(HERE / 'check_held_phase_footprint.py'),
                    source_app_unchanged=True,
                    gate=str(a.gate), gate_value='begin',
                    phases='one excluded first request per exact staged app, calibration, then fixed schedule')
    save(a.out / 'prepared.json', prepared)
    start = time.monotonic()
    while not a.gate.exists():
        assert time.monotonic() - start < 600, 'identity gate timeout; no native trial ran'
        time.sleep(.2)
    assert a.gate.read_text().strip() == 'begin'
    window_start = time.monotonic(); rows = []; previous_cleanup = None
    name = 'ordinary' if a.role == 'release' else 'actor_lifecycle'
    with FootprintObserver(a.observer, a.out / 'observer') as observer:
        quantum = calibrate(observer, a.out)
        assert quantum <= 20_000_000, 'unplanned hold size; arrange another bounded window'
        for side in sides:
            app = apps[side]
            host = SimpleNamespace(pw=app / 'Contents/MacOS/policy-witness', snapshot=actor_host.snapshot) if actor_host else None
            assert time.monotonic() - window_start + 80 < a.window
            measure(app / 'Contents/MacOS/policy-witness', a.out / 'warm' / side, a.bridge, a.helper,
                    observer, host, name, quantum, 0, 1,
                    dict(calibration=str(a.out / 'calibration.json'), phase='excluded_first_request'),
                    checker=check_wait_measurement)
        previous_cleanup = time.time_ns()
        schedule = [(regime, repetition, side) for regime in ('rapid', 'idle')
                    for repetition in range(1 if a.candidate == 'baseline' else 5)
                    for side in (sides if repetition % 2 == 0 else tuple(reversed(sides)))]
        for index, (regime, repetition, side) in enumerate(schedule):
            assert time.monotonic() - window_start + 80 < a.window, 'insufficient watchdog/cleanup reserve'
            power_before = capture_power()
            if regime == 'idle': time.sleep(1)
            directory = a.out / f'trial-{index:02d}-{regime}-{side}'
            app = apps[side]
            host = SimpleNamespace(pw=app / 'Contents/MacOS/policy-witness', snapshot=actor_host.snapshot) if actor_host else None
            measurement = measure(app / 'Contents/MacOS/policy-witness', directory, a.bridge, a.helper,
                                  observer, host, name, quantum, repetition, 1,
                                  dict(calibration=str(a.out / 'calibration.json'), regime=regime, side=side),
                                  checker=check_wait_measurement)
            cleanup = time.time_ns()
            launch = json.loads((directory / 'run/capture.json').read_text())['started_at_unix_ns']
            gap = launch - previous_cleanup
            power_after = capture_power()
            power = lambda item: {key: item[key] for key in ('source', 'lowpowermode')}
            stable = power(power_before) == power(power_after) and all(power(power_before).values())
            # The next launch includes fixed input preparation and power observation.
            low, high = (0, 100_000_000) if regime == 'rapid' else (1_000_000_000, 1_250_000_000)
            row = dict(regime=regime, repetition=repetition, side=side, directory=str(directory),
                       actual_gap_ns=gap, eligible_gap_ns=[low,high], eligible=bool(stable and low <= gap <= high),
                       power=power(power_before), power_before=power_before, power_after=power_after,
                       measurement=measurement)
            rows.append(row); save(a.out / 'trials.json', rows)
            previous_cleanup = cleanup
    assert {side: staged_identity(app) for side, app in apps.items()} == identities, 'staged executable changed'
    result = (dict(baseline=[dict(regime=r['regime'], eligible=r['eligible'],
                                 rate=rate_interval(r['measurement'], a.role)) for r in rows])
              if a.candidate == 'baseline' else compare(rows, a.role, a.minimum))
    result.update(window_elapsed_seconds=time.monotonic()-window_start, source_changes=False)
    save(a.out / 'result.json', result)
    print(json.dumps(result))


if __name__ == '__main__': main()
