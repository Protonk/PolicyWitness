"""Calibration pair control for the worker-wait pilot's timestamp instrument.

tests/fixtures/worker_wait/clock_pair.c forks a writer and a reader that share
one anonymous mapping (its header describes the protocol). This module builds
it, runs a matrix of reader pacings and injected delays one cell at a time,
retains each cell's raw output, and records what the pair shows on this
machine under the recorded conditions: clock read cost and tick, publication
to observation latency per reader pacing, writer-measured injected intervals,
a causal bound on cross-process clock offset, and whether the busy reader's
combined uncertainty is within 0.5 ms.

check_calibration() is the reader the pilot imports. It recomputes every
derived value, label, summary and the resolution section from the raw trial
records and rejects a receipt that disagrees. constructed_controls() shows it
accepting a constructed receipt and rejecting each fault, and shows the
resolution withholding credit under each condition that should withhold it.

The pair is not PolicyWitness: it applies no sandbox and runs neither the
host's nor the worker's loop. Its numbers are finite-run sensitivity facts,
not bounds on product response.

    worker_wait_clock_pair.py build BINARY LOG_DIR
    worker_wait_clock_pair.py run BINARY OUT_DIR [--modes busy,sleep2,sleep1]
        [--injects 0,1,2,3] [--trials N] [--read-overhead-samples N]
        [--inject-method nanosleep|mach_wait_until]
    worker_wait_clock_pair.py check CALIBRATION_JSON [--base OUT_DIR]
    worker_wait_clock_pair.py controls OUT_DIR
"""
import argparse
import ctypes
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'tests/fixtures/worker_wait/clock_pair.c'
COMPILE_FLAGS = ['-Wall', '-Wextra', '-Werror', '-O2', '-std=c11', '-arch', 'arm64', '-mmacosx-version-min=26.0']
KIND = 'worker_wait_clock_pair_calibration'
MODES = ('busy', 'sleep2', 'sleep1')
SLEEPING = ('sleep2', 'sleep1')
INJECTS = (0, 1, 2, 3)
METHODS = ('nanosleep', 'mach_wait_until')
SLEEP_PACING_NS = {'sleep2': 2_000_000, 'sleep1': 1_000_000}
HINTS_PER_PASS = 1000
HISTOGRAM_BUCKETS = 65
WATCHDOG_GRACE_S = 2
GATE_NS = 500_000
BOUNDARY_NS = 2_000_000
INJECTION_TOLERANCE_NS = 500_000
SLEEP_TOLERANCE_NS = 1_000_000
TIMEBASE_TOLERANCE = Fraction(1, 10_000)
HALF, P95 = Fraction(1, 2), Fraction(95, 100)

ROLES = {
    'busy': 'worker-like busy poller: one clock read, one acquire load and 1000 yield hints per pass',
    'sleep2': 'ordinary-host-like sleeping poller: one clock read, one acquire load and a 2 ms nanosleep per pass',
    'sleep1': 'actor-host-like sleeping poller: one clock read, one acquire load and a 1 ms nanosleep per pass',
}
INTERPRETATION = {
    'busy': ('Instrument resolution on the worker-like side: a busy poller locates an observation within one '
             'short pass, so this combined uncertainty is what the 0.5 ms gate is evaluated against.'),
    'sleeping': ('Host polling behavior, not instrument resolution: the bracket is the sleep the poller imposes '
                 'on itself. The pilot measures it as response. Exceeding 0.5 ms here is the expected '
                 'sensitivity result, not an instrument failure, and the gate does not apply to it.'),
}
DISTINCTION = (
    'The 0.5 ms gate applies to the timestamp instrument. The busy reader stands for the worker observing a host '
    'publication; its combined uncertainty is the instrument resolution and decides the gate. The sleeping '
    'readers stand for the ordinary host (2 ms) and actor host (1 ms) observing a worker publication; their '
    'brackets are dominated by their own sleeps, which the pilot must report as host response, so their gate '
    'result is expected to be "not met" and shows the computation can detect a wide bracket.')
FORMULA = (
    'combined_uncertainty_ns = endpoint term + pacing bracket + alignment bound. Endpoint term = max(2 x stamp_ns, '
    'widest measured endpoint bracket pair); stamp_ns = max(measured per-read cost, one tick). Pacing bracket = '
    'widest observation bracket among the mode\'s trials (gate basis: worst observed trial; p95 reported for '
    'information). Alignment bound = largest busy-cell bound on a constant offset between the processes\' clock '
    'reads, widened by one tick on each side for quantization.')
DEFINITIONS = {
    'R ready_raw': "reader's clock read immediately before it release-stores the trial's ready word",
    'A armed_raw': "writer's clock read immediately after the acquire load that first returned the trial's ready value",
    'P published_raw': ("writer's clock read after the injected sleep, immediately before the mailbox store and the "
                        'release store of the published word'),
    'Q post_store_raw': "writer's clock read immediately after that release store",
    'F first_pass_raw': "the reader's first pass sample for the trial",
    'N last_negative_raw': ("sample of the reader's last pass whose acquire load did not return the trial's value; "
                            'null when the first load returned it'),
    'S pass_sample_raw': ('sample taken at the start of the accepting pass, before its load: what the worker '
                          'seams PW_*_LOADED record'),
    'O observed_raw': "reader's clock read immediately after the acquire load that first returned the value",
    'latency_ns': 'O - P: includes the reader pacing delay (response), store visibility and both stamp reads',
    'actual_injected_ns': 'P - A on the writer clock alone; for inject 0 it spans two adjacent reads',
    'ready_hop_ns': 'A - R',
    'round_trip_ns': "ready_hop + latency: independent of any constant offset between the processes' clock reads",
    'response_ns': 'O - A: writer arm to reader observation across the two processes',
    'reader_interval_ns': "O - R on the reader's clock alone (includes the writer's ready detection)",
    'observation_bracket_ns': ('O - max(N, P): the value became visible to the reader within (max(N, P), O]; the '
                               'bracket implied by reader pacing'),
    'publication_store_bracket_ns': 'Q - P: the release store lies within [P, Q]',
    'observation_load_bracket_ns': 'O - S: the accepting load lies within [S, O]',
    'endpoint_brackets_ns': 'ns(Q - P + 1 tick) + ns(O - S + 1 tick): both endpoint brackets with one tick of quantization each',
    'pass_sample_before_publication': ('trials with S < P: a pass-sample stamp, as the worker seams record, precedes '
                                       'the publication stamp although that pass observed it'),
    'post_store_after_observation': ("trials with Q > O: a post-store stamp, as the worker seams record after a "
                                     "store, follows the other process's observation stamp"),
    'pass_interval': 'interval between consecutive pass samples; histogram bucket = bit length of the tick count',
    'causality': ('a value is observed no earlier than it was published and the writer arms no earlier than the '
                  'reader signals ready, so O >= P and A >= R in ticks. A cross-process hop can complete within '
                  'one tick, so equal ticks are accepted and counted; a strictly earlier raw is a violation.'),
    'statistics': ('nearest rank on integer ns: median = ceil(n/2)-th, p95 = ceil(0.95 n)-th smallest; '
                   'tick differences convert by floor(ticks x numer / denom)'),
}
NOT_OBSERVED = [
    'PolicyWitness: no host, worker, validator, sandbox, XPC or request path runs. The real host loop (checks '
    'between sleeps, HostWaitClock arithmetic, waitpid cadence) and worker loop (clock fault, cutoff and '
    'allowance tests, inbound service) are not reproduced.',
    'Core placement, cluster and frequency of each child: macOS offers no affinity and none was recorded.',
    'QoS class and timer leeway applied to the pacing and injected sleeps: inherited from the launcher, not set.',
    'Competing load other than the load averages recorded before and after the matrix.',
    'Individual pass intervals: only the per-trial maximum, per-trial mean and per-cell histogram are retained.',
    'When within the observation bracket the store became visible to the reader.',
    'Power transitions inside the matrix: pmset is read only before and after it.',
    'Process start and first execution of the fixture binary: they precede every stamp; no warm execution is '
    'excluded and trial 0 of every cell is retained.',
]


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ticks_ns(ticks, tb):
    return ticks * tb['numer'] // tb['denom']


def diff_ns(later, earlier, tb):
    d = later - earlier
    return ticks_ns(d, tb) if d >= 0 else -ticks_ns(-d, tb)


def nearest_rank(ordered, q):
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def stats(values):
    ordered = sorted(values)
    if not ordered:
        return None
    return {'n': len(ordered), 'min': ordered[0], 'median': nearest_rank(ordered, HALF),
            'p95': nearest_rank(ordered, P95), 'max': ordered[-1]}


def watchdog_seconds(trials, inject_ms):
    return 5 + (trials * (inject_ms + 10) + 999) // 1000


def is_count(value):
    return type(value) is int and value >= 0


# Clock readings taken by this process, independent of the fixture's conversion.

_CONTINUOUS = []


def continuous_ticks():
    if not _CONTINUOUS:
        function = ctypes.CDLL(None).mach_continuous_time
        function.restype, function.argtypes = ctypes.c_uint64, []
        _CONTINUOUS.append(function)
    return _CONTINUOUS[0]()


def clock_reading():
    before = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    ticks = continuous_ticks()
    after = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    return {'monotonic_raw_before_ns': before, 'continuous_ticks': ticks, 'monotonic_raw_after_ns': after}


def sleep_clocks():
    return {'monotonic_raw_ns': time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW),
            'uptime_raw_ns': time.clock_gettime_ns(time.CLOCK_UPTIME_RAW)}


def timebase_agreement(check, tb):
    """Whether the declared timebase lies within the bracketed ratio of an independent ns clock to ticks."""
    before, after = check['before'], check['after']
    interval = after['continuous_ticks'] - before['continuous_ticks']
    if interval <= 0:
        return {'interval_ticks': interval, 'agrees': False, 'reason': 'continuous ticks did not advance'}
    low = Fraction(after['monotonic_raw_before_ns'] - before['monotonic_raw_after_ns'], interval)
    high = Fraction(after['monotonic_raw_after_ns'] - before['monotonic_raw_before_ns'], interval)
    declared = Fraction(tb['numer'], tb['denom'])
    return {'interval_ticks': interval, 'independent_clock': 'CLOCK_MONOTONIC_RAW',
            'ns_per_tick_low': float(low), 'ns_per_tick_high': float(high),
            'declared_ns_per_tick': float(declared), 'relative_tolerance': float(TIMEBASE_TOLERANCE),
            'agrees': low * (1 - TIMEBASE_TOLERANCE) <= declared <= high * (1 + TIMEBASE_TOLERANCE)}


def system_sleep_ns(before, after):
    return ((after['monotonic_raw_ns'] - before['monotonic_raw_ns']) -
            (after['uptime_raw_ns'] - before['uptime_raw_ns']))


def conditions_snapshot():
    snapshot = {'loadavg': list(os.getloadavg()), 'sleep_clocks': sleep_clocks()}
    for key, argv in (('pmset_batt', ['/usr/bin/pmset', '-g', 'batt']), ('pmset_settings', ['/usr/bin/pmset', '-g'])):
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
            snapshot[key] = {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout,
                             'stderr': result.stderr}
        except (OSError, subprocess.TimeoutExpired) as exc:
            snapshot[key] = {'argv': argv, 'error': repr(exc)}
    lines = [line.split() for line in snapshot['pmset_settings'].get('stdout', '').splitlines()]
    values = [words[1] for words in lines if len(words) == 2 and words[0] == 'lowpowermode']
    snapshot['lowpowermode'] = values[0] if len(values) == 1 else None
    return snapshot


# Pure functions of one cell's raw output.

def rederive(raw):
    """Recompute the fields clock_pair derives from raw ticks, the way it does."""
    tb = raw['timebase']
    for key in ('read_overhead', 'read_overhead_after'):
        overhead = raw[key]
        overhead['total_ns'] = ticks_ns(overhead['total_ticks'], tb)
        overhead['per_read_ns'] = round(overhead['total_ns'] / overhead['n'], 3)
    for t in raw['trials']:
        t['latency_ns'] = (diff_ns(t['observed_raw'], t['published_raw'], tb)
                           if t['writer_complete'] and t['reader_complete'] else None)
        t['actual_injected_ns'] = diff_ns(t['published_raw'], t['armed_raw'], tb) if t['writer_complete'] else None
    return raw


def complete_trials(raw):
    return [t for t in raw['trials'] if t['writer_complete'] and t['reader_complete']]


def trial_facts(t, tb, requested_ns):
    r, a, p, q = t['ready_raw'], t['armed_raw'], t['published_raw'], t['post_store_raw']
    f, n, s, o = t['first_pass_raw'], t['last_negative_raw'], t['pass_sample_raw'], t['observed_raw']
    latency, injected, hop = diff_ns(o, p, tb), diff_ns(p, a, tb), diff_ns(a, r, tb)
    passes = t['passes']
    return {
        'latency_ns': latency, 'actual_injected_ns': injected, 'injection_excess_ns': injected - requested_ns,
        'ready_hop_ns': hop, 'round_trip_ns': hop + latency, 'response_ns': diff_ns(o, a, tb),
        'reader_interval_ns': diff_ns(o, r, tb),
        'observation_bracket_ns': diff_ns(o, p if n is None else max(n, p), tb),
        'publication_store_bracket_ns': diff_ns(q, p, tb), 'observation_load_bracket_ns': diff_ns(o, s, tb),
        'endpoint_brackets_ns': ticks_ns(max(q - p + 1, 0), tb) + ticks_ns(max(o - s + 1, 0), tb),
        'mean_pass_interval_ns': ticks_ns(s - f, tb) // (passes - 1) if passes > 1 else None,
        'max_pass_interval_ns': ticks_ns(t['max_pass_interval_ticks'], tb),
        'pass_sample_before_publication': s < p, 'post_store_after_observation': q > o,
    }


def cell_facts(raw):
    return [trial_facts(t, raw['timebase'], raw['injected_requested_ns']) for t in complete_trials(raw)]


def histogram_upper_ns(counts, q, tb):
    total = sum(counts)
    if not total:
        return None
    target, seen = math.ceil(q * total), 0
    for bucket, count in enumerate(counts):
        seen += count
        if seen >= target:
            return ticks_ns((1 << bucket) - 1, tb) if bucket else 0
    return None


def cell_sleep_ns(raw):
    start, end = raw['clock_start'], raw['clock_end']
    gap = (end['continuous_raw'] - start['continuous_raw']) - (end['absolute_raw'] - start['absolute_raw'])
    return diff_ns(gap, 0, raw['timebase'])


def alignment(raw):
    """Bound a constant offset between the writer's and reader's clock reads from causal hops.

    A hop measured as m ticks spans less than m + 1 ticks, so each side widens by one tick."""
    trials, tb = complete_trials(raw), raw['timebase']
    if not trials:
        return None
    hop = [t['armed_raw'] - t['ready_raw'] for t in trials]
    seen = [t['observed_raw'] - t['published_raw'] for t in trials]
    lower, upper = diff_ns(-(min(seen) + 1), 0, tb), diff_ns(min(hop) + 1, 0, tb)
    return {'offset_interval_ns': [lower, upper], 'intersection_bound_ns': max(abs(lower), abs(upper)),
            'per_trial_bound_ns': stats([diff_ns(max(h, v) + 1, 0, tb) for h, v in zip(hop, seen)])}


SUMMARY_STATS = ('latency_ns', 'actual_injected_ns', 'injection_excess_ns', 'ready_hop_ns', 'round_trip_ns',
                 'response_ns', 'reader_interval_ns', 'observation_bracket_ns', 'publication_store_bracket_ns',
                 'observation_load_bracket_ns', 'endpoint_brackets_ns', 'mean_pass_interval_ns',
                 'max_pass_interval_ns')


def summarize_cell(raw):
    tb, facts, trials = raw['timebase'], cell_facts(raw), complete_trials(raw)
    summary = {'trials_requested': raw['trials_requested'], 'trials_complete': len(trials),
               'requested_injected_ns': raw['injected_requested_ns'], 'inject_method': raw['inject_method']}
    for key in SUMMARY_STATS:
        summary[key] = stats([f[key] for f in facts if f[key] is not None])
    passes = [t['passes'] for t in trials]
    summary.update(
        passes=stats(passes), first_load_observations=sum(p == 1 for p in passes),
        pass_interval_histogram_p95_upper_ns=histogram_upper_ns(raw['pass_histogram']['counts'], P95, tb),
        pass_sample_before_publication=sum(f['pass_sample_before_publication'] for f in facts),
        post_store_after_observation=sum(f['post_store_after_observation'] for f in facts),
        observation_before_publication=sum(t['observed_raw'] < t['published_raw'] for t in trials),
        observation_same_tick_as_publication=sum(t['observed_raw'] == t['published_raw'] for t in trials),
        arm_before_ready=sum(t['armed_raw'] < t['ready_raw'] for t in trials),
        arm_same_tick_as_ready=sum(t['armed_raw'] == t['ready_raw'] for t in trials),
        read_overhead_per_read_ns=max(raw[k]['total_ns'] / raw[k]['n'] for k in ('read_overhead', 'read_overhead_after')),
        alignment=alignment(raw), system_sleep_ns=cell_sleep_ns(raw))
    return summary


def labels_for(raw):
    """Trials and conditions that stay in the receipt but must carry a visible label."""
    labels, tb, requested = [], raw['timebase'], raw['injected_requested_ns']
    for t in raw['trials']:
        if not t['writer_complete']:
            continue
        actual = diff_ns(t['published_raw'], t['armed_raw'], tb)
        if actual < requested:
            labels.append({'trial': t['index'], 'label': 'injection_shorter_than_requested',
                           'requested_ns': requested, 'actual_ns': actual})
        elif actual - requested > INJECTION_TOLERANCE_NS:
            labels.append({'trial': t['index'], 'label': 'injection_overran_tolerance',
                           'requested_ns': requested, 'actual_ns': actual,
                           'tolerance_ns': INJECTION_TOLERANCE_NS})
    gap = cell_sleep_ns(raw)
    if gap > SLEEP_TOLERANCE_NS:
        labels.append({'trial': None, 'label': 'system_sleep_overlap', 'sleep_ns': gap})
    return labels


def cell_ok(cell):
    raw = cell.get('raw')
    return (cell.get('returncode') == 0 and not cell.get('harness_timeout') and cell.get('parse_error') is None
            and not cell.get('group_members_after_exit') and isinstance(raw, dict)
            and raw.get('status') == 'complete')


# The resolution section: a pure function of the cells and the run's clock facts.

def resolution(cells, timebase_agrees, conditions_sleep_ns):
    usable = [c for c in cells if isinstance(c.get('raw'), dict)]
    if not usable:
        return {'computed': False, 'instrument_gate': {'gate_ns': GATE_NS, 'credited': False,
                                                       'reasons': ['no_cell_output']}}
    tb = usable[0]['raw']['timebase']
    tick_ns = float(Fraction(tb['numer'], tb['denom']))
    read_ns = max(c['raw'][k]['total_ns'] / c['raw'][k]['n'] for c in usable
                  for k in ('read_overhead', 'read_overhead_after'))
    stamp_ns = max(read_ns, tick_ns)
    busy = [c for c in usable if c['mode'] == 'busy']
    per_cell = []
    for c in busy:
        a = alignment(c['raw'])
        if a:
            per_cell.append({'inject_ms': c['inject_ms'], 'offset_interval_ns': a['offset_interval_ns'],
                             'intersection_bound_ns': a['intersection_bound_ns']})
    alignment_bound = max((p['intersection_bound_ns'] for p in per_cell), default=None)
    readers, causality = {}, 0
    for mode in MODES:
        mine = [c for c in usable if c['mode'] == mode]
        if not mine:
            continue
        facts = [f for c in mine for f in cell_facts(c['raw'])]
        causality += sum(1 for c in mine for t in complete_trials(c['raw'])
                         if t['observed_raw'] < t['published_raw'] or t['armed_raw'] < t['ready_raw'])
        brackets = stats([f['observation_bracket_ns'] for f in facts])
        entry = {'role': ROLES[mode], 'injects_ms': [c['inject_ms'] for c in mine], 'trials': len(facts),
                 'pacing_bracket_ns': brackets, 'alignment_bound_ns': alignment_bound,
                 'latency_ns': stats([f['latency_ns'] for f in facts]),
                 'mean_pass_interval_ns': stats([f['mean_pass_interval_ns'] for f in facts
                                                 if f['mean_pass_interval_ns'] is not None]),
                 'gate_ns': GATE_NS, 'gate_basis': 'worst observed trial',
                 'interpretation': INTERPRETATION['busy' if mode == 'busy' else 'sleeping']}
        if brackets is None:
            entry.update(endpoint_term_ns=None, combined_uncertainty_ns=None, combined_uncertainty_p95_ns=None,
                         gate_met=False)
        else:
            endpoint = max(math.ceil(2 * stamp_ns), max(f['endpoint_brackets_ns'] for f in facts))
            offset = alignment_bound or 0
            entry.update(endpoint_term_ns=endpoint,
                         combined_uncertainty_ns=endpoint + brackets['max'] + offset,
                         combined_uncertainty_p95_ns=endpoint + brackets['p95'] + offset)
            entry['gate_met'] = entry['combined_uncertainty_ns'] <= GATE_NS
        if mode == 'busy':
            entry['boundary'] = boundary(mine, entry['combined_uncertainty_ns'])
        else:
            entry['sensitivity_shown'] = not entry['gate_met']
        readers[mode] = entry
    facts = [f for c in usable for f in cell_facts(c['raw'])]
    sleep_labels = any(cell_sleep_ns(c['raw']) > SLEEP_TOLERANCE_NS for c in usable)
    reasons = []
    if len(usable) != len(cells) or not all(cell_ok(c) for c in cells):
        reasons.append('incomplete_cells')
    if not {(m, i) for m in MODES for i in INJECTS} <= {(c['mode'], c['inject_ms']) for c in cells}:
        reasons.append('partial_matrix')
    if 'busy' not in readers:
        reasons.append('busy_cells_absent')
    else:
        b = readers['busy']
        if not b['gate_met']:
            reasons.append('busy_combined_uncertainty_exceeds_gate')
        if b['boundary']['disagreements']:
            reasons.append('boundary_disagreement')
        for side in ('below', 'above'):
            if not b['boundary'][side]:
                reasons.append('boundary_side_unobserved_' + side)
    sleeping = [m for m in SLEEPING if m in readers]
    if not sleeping:
        reasons.append('sleeping_cells_absent')
    reasons += ['sleeping_bracket_within_gate_' + m for m in sleeping if readers[m]['gate_met']]
    if causality:
        reasons.append('causality_violation')
    if not timebase_agrees:
        reasons.append('timebase_disagrees_with_independent_clock')
    if sleep_labels or conditions_sleep_ns is None or conditions_sleep_ns > SLEEP_TOLERANCE_NS:
        reasons.append('system_sleep_overlap')
    return {
        'computed': True, 'tick_ns': tick_ns, 'read_overhead_ns': read_ns, 'stamp_ns': stamp_ns,
        'alignment': {'bound_ns': alignment_bound, 'per_busy_cell': per_cell,
                      'assumption': ("one constant offset between the two processes' clock reads within a cell; "
                                     'the per-trial bounds in each cell summary hold without it')},
        'stamp_order': {'trials': len(facts),
                        'pass_sample_before_publication': sum(f['pass_sample_before_publication'] for f in facts),
                        'post_store_after_observation': sum(f['post_store_after_observation'] for f in facts),
                        'meaning': ('A pass-sample stamp can precede the other side\'s publication stamp and a '
                                    'post-store stamp can follow the other side\'s observation stamp. Neither '
                                    'ordering is a clock violation; a reader of such stamps must use brackets.')},
        'readers': readers,
        'instrument_gate': {'gate_ns': GATE_NS, 'credited': not reasons, 'reasons': reasons,
                            'scope': ('finite-run sensitivity of this pair on this machine under the recorded '
                                      'conditions; not a universal bound and not a PolicyWitness measurement')},
        'formula': FORMULA, 'distinction': DISTINCTION,
    }


def boundary(cells, band):
    """Classify each busy trial against the 2 ms acceptance boundary from the writer alone and across processes."""
    result = {'boundary_ns': BOUNDARY_NS, 'band_ns': band, 'below': 0, 'above': 0, 'within_band': 0,
              'disagreements': [],
              'basis': ('writer-only P - A against cross-process O - A; trials whose writer interval lies within '
                        'the band of the boundary are not classified')}
    if band is None:
        return result
    for c in cells:
        for t, f in zip(complete_trials(c['raw']), cell_facts(c['raw'])):
            writer, crossed = f['actual_injected_ns'], f['response_ns']
            if abs(writer - BOUNDARY_NS) <= band:
                result['within_band'] += 1
                continue
            above = writer > BOUNDARY_NS
            result['above' if above else 'below'] += 1
            if (crossed > BOUNDARY_NS) != above:
                result['disagreements'].append({'inject_ms': c['inject_ms'], 'trial': t['index'],
                                                'writer_interval_ns': writer, 'response_ns': crossed})
    return result


def assemble(requested, binary, cells, timebase_check, conditions):
    for cell in cells:
        raw = cell.get('raw')
        try:
            cell['labels'] = labels_for(raw) if isinstance(raw, dict) else []
            cell['summary'] = summarize_cell(raw) if isinstance(raw, dict) else None
            cell['summary_error'] = None
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            cell['labels'], cell['summary'], cell['summary_error'] = [], None, repr(exc)
    raws = [c['raw'] for c in cells if isinstance(c.get('raw'), dict)]
    timebase = raws[0]['timebase'] if raws else None
    agreement = timebase_agreement(timebase_check, timebase) if timebase else None
    timebase_check = dict(timebase_check, agreement=agreement)
    gap = system_sleep_ns(conditions['before']['sleep_clocks'], conditions['after']['sleep_clocks'])
    conditions = dict(conditions, system_sleep_ns=gap, sleep_overlap=gap > SLEEP_TOLERANCE_NS)
    expected = len(requested['modes']) * len(requested['injects'])
    return {
        'version': 1, 'kind': KIND,
        'scope': ('Independent two-process control of the pilot timestamp instrument: no sandbox, no '
                  'PolicyWitness host, worker or validator. It establishes finite-run clock and cross-process '
                  'publication sensitivity on this machine, not the host\'s or worker\'s real response.'),
        'binary': binary, 'requested': requested, 'timebase': timebase, 'timebase_check': timebase_check,
        'conditions': conditions, 'cells': cells,
        'complete': len(cells) == expected and all(cell_ok(c) for c in cells),
        'resolution': resolution(cells, bool(agreement and agreement['agrees']), gap),
        'definitions': DEFINITIONS, 'not_observed': NOT_OBSERVED,
    }


# Building and running the fixture.

def build(output, log_dir, source=SOURCE):
    output, log_dir = Path(output), Path(log_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    argv = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', *COMPILE_FLAGS, str(source), '-o', str(output)]
    version = subprocess.run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '--version'],
                             capture_output=True, text=True, timeout=60)
    result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    receipt = {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
               'compiler_version': version.stdout, 'source': str(source), 'source_sha256': sha256_file(source),
               'binary': str(output), 'binary_sha256': sha256_file(output) if result.returncode == 0 else None}
    save(log_dir / 'clock-pair-build.json', receipt)
    assert result.returncode == 0, f'clock_pair build failed: {result.stderr}'
    return receipt


def run_cell(binary, out, order, mode, inject_ms, trials, samples, method):
    directory = Path('cells') / f'{mode}-inject{inject_ms}'
    cell_dir = out / directory
    cell_dir.mkdir(parents=True, exist_ok=False)
    argv = [str(binary), '--mode', mode, '--inject', str(inject_ms), '--trials', str(trials),
            '--read-overhead-samples', str(samples), '--inject-method', method]
    meta = {'argv': argv, 'timeout_s': watchdog_seconds(trials, inject_ms) + WATCHDOG_GRACE_S + 10,
            'returncode': None, 'harness_timeout': False, 'group_killed': False,
            'clock_before': sleep_clocks()}
    with (cell_dir / 'stdout.json').open('wb') as stdout, (cell_dir / 'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            meta['returncode'] = process.wait(timeout=meta['timeout_s'])
        except subprocess.TimeoutExpired:
            meta['harness_timeout'] = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
                meta['group_killed'] = True
            except ProcessLookupError:
                pass
            meta['returncode'] = process.wait(timeout=10)
    meta['clock_after'] = sleep_clocks()
    # The fixture reaps both children before it exits; a surviving group member means it did not.
    try:
        os.killpg(process.pid, 0)
        meta['group_members_after_exit'] = True
    except ProcessLookupError:
        meta['group_members_after_exit'] = False
    save(cell_dir / 'command.json', meta)
    text = (cell_dir / 'stdout.json').read_bytes()
    raw, parse_error = None, None
    try:
        raw = json.loads(text)
    except ValueError as exc:
        parse_error = str(exc)
    return {'mode': mode, 'inject_ms': inject_ms, 'order': order, 'directory': str(directory),
            'stdout_sha256': hashlib.sha256(text).hexdigest(), 'returncode': meta['returncode'],
            'harness_timeout': meta['harness_timeout'], 'group_killed': meta['group_killed'],
            'group_members_after_exit': meta['group_members_after_exit'], 'parse_error': parse_error,
            'stderr': (cell_dir / 'stderr.txt').read_text(errors='replace'), 'raw': raw}


def run(binary, out_dir, modes=MODES, injects=INJECTS, trials=100, read_overhead_samples=100_000,
        inject_method='nanosleep'):
    """Run the matrix serially (one writer and one reader at a time) and write calibration.json."""
    modes, injects = list(modes), list(injects)
    assert modes and all(m in MODES for m in modes) and len(set(modes)) == len(modes), modes
    assert injects and all(i in INJECTS for i in injects) and len(set(injects)) == len(injects), injects
    assert type(trials) is int and 1 <= trials <= 5000, trials
    assert type(read_overhead_samples) is int and 1000 <= read_overhead_samples <= 50_000_000
    assert inject_method in METHODS, inject_method
    binary, out = Path(binary).resolve(), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / 'calibration.json').exists(), f'calibration already exists in {out}'
    requested = {'modes': modes, 'injects': injects, 'trials': trials,
                 'read_overhead_samples': read_overhead_samples, 'inject_method': inject_method}
    info = {'path': str(binary), 'sha256': sha256_file(binary), 'source': str(SOURCE),
            'source_sha256': sha256_file(SOURCE) if SOURCE.exists() else None}
    before = conditions_snapshot()
    first = clock_reading()
    cells = [run_cell(binary, out, order, mode, inject, trials, read_overhead_samples, inject_method)
             for order, (mode, inject) in enumerate((m, i) for m in modes for i in injects)]
    last = clock_reading()
    after = conditions_snapshot()
    calibration = assemble(requested, info, cells, {'before': first, 'after': last},
                           {'before': before, 'after': after})
    save(out / 'calibration.json', calibration)
    return json.loads((out / 'calibration.json').read_text())


# The independent reader.

def check_raw(cell, raw, cal, add):
    where = f"{cell['mode']}/inject{cell['inject_ms']}"
    requested = cal['requested']
    if raw.get('version') != 1 or raw.get('fixture') != 'worker_wait_clock_pair' or raw.get('clock') != 'mach_continuous_time':
        add('version', f'{where}: fixture identity {raw.get("fixture")!r} version {raw.get("version")!r}')
    if raw['status'] != 'complete' or raw['failure'] is not None:
        add('cell_failed', f'{where}: status {raw["status"]!r} failure {raw["failure"]!r}')
    if raw['mode'] != cell['mode'] or raw['injected_ms'] != cell['inject_ms']:
        add('matrix', f'{where}: raw reports {raw["mode"]}/inject{raw["injected_ms"]}')
    pacing = ({'kind': 'yield_hints', 'hints_per_pass': HINTS_PER_PASS} if raw['mode'] == 'busy' else
              {'kind': 'nanosleep', 'requested_ns': SLEEP_PACING_NS.get(raw['mode'])})
    if raw['pacing'] != pacing or raw['writer_pacing'] != {'kind': 'yield_hints', 'hints_per_pass': HINTS_PER_PASS}:
        add('shape', f'{where}: pacing {raw["pacing"]} writer {raw["writer_pacing"]}')
    if raw['injected_requested_ns'] != raw['injected_ms'] * 1_000_000:
        add('shape', f'{where}: requested ns {raw["injected_requested_ns"]}')
    method = 'none' if raw['injected_ms'] == 0 else requested['inject_method']
    if raw['inject_method'] != method:
        add('shape', f'{where}: inject method {raw["inject_method"]!r}, requested {method!r}')
    tb = raw['timebase']
    if not (is_count(tb['numer']) and tb['numer'] > 0 and is_count(tb['denom']) and tb['denom'] > 0):
        add('timebase', f'{where}: invalid timebase {tb}')
        return
    if tb != cal['timebase']:
        add('timebase', f'{where}: timebase {tb} differs from the calibration timebase {cal["timebase"]}')
    for role in ('writer', 'reader'):
        child = raw['children'][role]
        if (child['reaped'] is not True or child['exit_code'] != 0 or child['term_signal'] is not None
                or child['state'] != 'finished' or child['failure'] != 'none'):
            add('cell_failed', f'{where}: {role} {child}')
    if raw['watchdog']['stage'] != 0 or raw['watchdog']['sigkill_sent'] is not False:
        add('cell_failed', f'{where}: watchdog {raw["watchdog"]}')
    trials = raw['trials']
    if (raw['trials_requested'] != requested['trials'] or len(trials) != raw['trials_requested']
            or raw['trials_complete'] != len(complete_trials(raw))
            or [t['index'] for t in trials] != list(range(len(trials)))):
        add('missing_trials', f'{where}: {len(trials)} records, {raw["trials_complete"]} reported complete, '
                              f'{requested["trials"]} requested')
    fields = ('ready_raw', 'armed_raw', 'published_raw', 'post_store_raw', 'first_pass_raw', 'pass_sample_raw',
              'observed_raw', 'published_raw_seen', 'passes', 'max_pass_interval_ticks', 'writer_ready_passes')
    previous = None
    for t in trials:
        at = f'{where} trial {t["index"]}'
        if not (t['writer_complete'] is True and t['reader_complete'] is True):
            add('missing_trials', f'{at}: writer_complete {t["writer_complete"]} reader_complete {t["reader_complete"]}')
            previous = None
            continue
        if not all(is_count(t[k]) for k in fields) or not (t['last_negative_raw'] is None or is_count(t['last_negative_raw'])):
            add('shape', f'{at}: non-integer raw field')
            previous = None
            continue
        r, a, p, q = t['ready_raw'], t['armed_raw'], t['published_raw'], t['post_store_raw']
        f, n, s, o = t['first_pass_raw'], t['last_negative_raw'], t['pass_sample_raw'], t['observed_raw']
        passes, widest = t['passes'], t['max_pass_interval_ticks']
        order = [r <= f <= s <= o, a <= p <= q, passes >= 1, t['writer_ready_passes'] >= 1,
                 (n is None) == (passes == 1), n is None or f <= n < s,
                 (f == s and widest == 0) if passes == 1 else (widest <= s - f <= widest * (passes - 1))]
        if previous is not None:
            order += [previous['observed_raw'] <= r, previous['post_store_raw'] <= a]
        if not all(order):
            add('same_process_order', f'{at}: R={r} A={a} P={p} Q={q} F={f} N={n} S={s} O={o} passes={passes}')
        if o < p:
            add('observation_before_publication', f'{at}: observed {o} precedes published {p}')
        if a < r:
            add('arm_before_ready', f'{at}: armed {a} precedes ready {r}')
        if t['published_raw_seen'] != p:
            add('mailbox_mismatch', f'{at}: reader saw {t["published_raw_seen"]}, writer published {p}')
        if t['sleep_rc'] != 0 or t['sleep_errno'] != 0:
            add('sleep_failed', f'{at}: sleep rc {t["sleep_rc"]} errno {t["sleep_errno"]}')
        for key, later, earlier, code in (('latency_ns', o, p, 'negative_latency'),
                                          ('actual_injected_ns', p, a, 'negative_injection')):
            value = t[key]
            if type(value) is not int or value != diff_ns(later, earlier, tb):
                add('derived_mismatch', f'{at}: {key} {value!r}, recomputed {diff_ns(later, earlier, tb)}')
            if type(value) is int and value < 0:
                add(code, f'{at}: {key} {value}')
        previous = t
    counts = raw['pass_histogram']['counts']
    widest = [t['max_pass_interval_ticks'] for t in complete_trials(raw) if t['passes'] > 1]
    # An unfinished trial's passes are counted but its record is not, so only a full set is compared.
    every = raw['status'] == 'complete' and len(trials) == raw['trials_requested'] == len(complete_trials(raw))
    if every and (raw['pass_histogram'].get('unit') != 'ticks' or len(counts) != HISTOGRAM_BUCKETS
            or not all(is_count(x) for x in counts)
            or sum(counts) != sum(t['passes'] - 1 for t in complete_trials(raw))
            or any(counts[w.bit_length()] < 1 for w in widest)
            or (widest and max(i for i, x in enumerate(counts) if x) != max(widest).bit_length())):
        add('histogram', f'{where}: pass histogram disagrees with the trial records')
    for key in ('read_overhead', 'read_overhead_after'):
        o = raw[key]
        if (o['n'] != requested['read_overhead_samples'] or not is_count(o['total_ticks'])
                or not is_count(o['zero_delta_reads']) or o['zero_delta_reads'] > o['n']
                or not is_count(o['max_delta_ticks']) or o['max_delta_ticks'] > o['total_ticks']):
            add('shape', f'{where}: {key} {o}')
        elif o['total_ns'] != ticks_ns(o['total_ticks'], tb) or abs(o['per_read_ns'] - o['total_ns'] / o['n']) > 0.0006:
            add('derived_mismatch', f'{where}: {key} {o}')
    start, end = raw['clock_start'], raw['clock_end']
    if not (start['continuous_raw'] <= end['continuous_raw'] and start['absolute_raw'] <= end['absolute_raw']):
        add('same_process_order', f'{where}: clock_start {start} clock_end {end}')


def check_cell(cell, cal, add, base):
    where = f"{cell.get('mode')}/inject{cell.get('inject_ms')}"
    if (cell['returncode'] != 0 or cell['harness_timeout'] or cell['parse_error'] is not None
            or cell['group_members_after_exit'] is not False):
        add('cell_failed', f'{where}: returncode {cell["returncode"]} harness_timeout {cell["harness_timeout"]} '
                           f'parse_error {cell["parse_error"]!r} survivors {cell["group_members_after_exit"]}')
    raw = cell['raw']
    if not isinstance(raw, dict):
        add('cell_failed', f'{where}: no raw output')
        return
    check_raw(cell, raw, cal, add)
    expected = labels_for(raw)
    for label in expected:
        if label not in cell['labels']:
            add('unlabeled_injection_outlier' if label['label'].startswith('injection') else 'unlabeled_condition',
                f'{where}: {label}')
    for label in cell['labels']:
        if label not in expected:
            add('spurious_label', f'{where}: {label}')
    summary = summarize_cell(raw)
    if cell['summary'] != summary:
        keys = sorted(k for k in summary if (cell['summary'] or {}).get(k) != summary[k])
        add('summary_mismatch', f'{where}: stored summary differs at {keys}')
    if base is not None:
        path = Path(base) / cell['directory'] / 'stdout.json'
        if not path.exists() or sha256_file(path) != cell['stdout_sha256'] or json.loads(path.read_text()) != raw:
            add('raw_file', f'{where}: {path} is missing or differs from the embedded raw output')


def calibration_problems(cal, base=None):
    problems = []

    def add(code, detail):
        problems.append({'code': code, 'detail': str(detail)[:600]})

    try:
        if cal['version'] != 1 or cal['kind'] != KIND:
            add('version', f'{cal["kind"]!r} version {cal["version"]!r}')
        requested = cal['requested']
        modes, injects = requested['modes'], requested['injects']
        if (not modes or not injects or len(set(modes)) != len(modes) or len(set(injects)) != len(injects)
                or not all(m in MODES for m in modes) or not all(i in INJECTS for i in injects)
                or requested['inject_method'] not in METHODS or not (is_count(requested['trials']) and requested['trials'] > 0)):
            add('matrix', f'requested {requested}')
        seen = [(c['mode'], c['inject_ms']) for c in cal['cells']]
        if sorted(seen) != sorted((m, i) for m in modes for i in injects) or len(set(seen)) != len(seen):
            add('matrix', f'cells {seen} do not cover {modes} x {injects} exactly once')
        if [c['order'] for c in cal['cells']] != list(range(len(cal['cells']))):
            add('matrix', 'cell order is not the execution sequence')
        for cell in cal['cells']:
            try:
                check_cell(cell, cal, add, base)
            except (KeyError, TypeError, ValueError, AttributeError, IndexError, ZeroDivisionError) as exc:
                add('shape', f"{cell.get('mode')}/inject{cell.get('inject_ms')}: {exc!r}")
        tb = cal['timebase']
        agreement = timebase_agreement(cal['timebase_check'], tb)
        if not agreement['agrees']:
            add('timebase', f'declared {tb} outside the independent clock bracket {agreement}')
        if cal['timebase_check']['agreement'] != agreement:
            add('timebase', 'stored timebase agreement differs from the recomputed one')
        conditions = cal['conditions']
        gap = system_sleep_ns(conditions['before']['sleep_clocks'], conditions['after']['sleep_clocks'])
        if conditions['system_sleep_ns'] != gap or conditions['sleep_overlap'] != (gap > SLEEP_TOLERANCE_NS):
            add('conditions', f'stored sleep {conditions["system_sleep_ns"]}, recomputed {gap}')
        expected = len(modes) * len(injects)
        if cal['complete'] != (len(cal['cells']) == expected and all(cell_ok(c) for c in cal['cells'])):
            add('summary_mismatch', f'complete flag {cal["complete"]!r}')
        recomputed = resolution(cal['cells'], agreement['agrees'], gap)
        if cal['resolution'] != recomputed:
            keys = sorted(k for k in recomputed if cal['resolution'].get(k) != recomputed[k])
            add('resolution_mismatch', f'stored resolution differs at {keys}')
        if cal['definitions'] != DEFINITIONS or cal['not_observed'] != NOT_OBSERVED:
            add('shape', 'definitions or not-observed list differ from this reader')
    except (KeyError, TypeError, ValueError, AttributeError, IndexError, ZeroDivisionError) as exc:
        add('shape', repr(exc))
    return problems


def check_calibration(cal, base=None):
    """Validate a calibration receipt; return it, or raise AssertionError naming every problem."""
    problems = calibration_problems(cal, base)
    if problems:
        raise AssertionError('calibration receipt rejected:\n' +
                             '\n'.join(f'  {p["code"]}: {p["detail"]}' for p in problems))
    return cal


def resolution_numbers(cal, base=None):
    """The checked resolution section, for the pilot reader."""
    return check_calibration(cal, base)['resolution']


# Constructed receipts and controls.

CONSTRUCTED_TB = {'numer': 125, 'denom': 3}


def to_ticks(ns, tb=CONSTRUCTED_TB):
    return ns * tb['denom'] // tb['numer']


def constructed_raw(mode, inject_ms, trials=6, pace=None, overrun=None, visibility_delay=None, sleep_gap_ticks=0,
                    arm_same_tick=(), observe_same_tick=(), store_delay=None):
    """A consistent clock_pair record. Per trial index: overrun adds writer sleep,
    visibility_delay holds the value invisible past the store and store_delay delays the
    writer's post-store read (ticks); arm_same_tick and observe_same_tick put A on R's tick
    and O on P's tick, observed by the pass sampled before P."""
    pace = pace or {'busy': 10, 'sleep2': to_ticks(2_250_000), 'sleep1': to_ticks(1_150_000)}[mode]
    requested = inject_ms * 1_000_000
    counts, rows, t = [0] * HISTOGRAM_BUCKETS, [], 9_000_100
    for i in range(trials):
        r, f = t, t + 1
        a = r if i in arm_same_tick else r + 3
        p = a + to_ticks(requested) + (to_ticks(120_000) if inject_ms else 1) + (overrun or {}).get(i, 0)
        q = p + 1 + (store_delay or {}).get(i, 0)
        if i in observe_same_tick:
            j = (p - f) // pace
            s, o = f + j * pace, p
        else:
            j = (max(p, q + (visibility_delay or {}).get(i, 0) - 1) - f) // pace + 1
            s, o = f + j * pace, f + j * pace + 1
        counts[pace.bit_length()] += j
        rows.append({'index': i, 'writer_complete': True, 'reader_complete': True, 'ready_raw': r,
                     'armed_raw': a, 'published_raw': p, 'post_store_raw': q, 'first_pass_raw': f,
                     'last_negative_raw': s - pace if j else None, 'pass_sample_raw': s, 'observed_raw': o,
                     'published_raw_seen': p, 'passes': j + 1, 'max_pass_interval_ticks': pace if j else 0,
                     'writer_ready_passes': 2, 'sleep_rc': 0, 'sleep_errno': 0})
        t = o + 2
    overhead = {'n': 1000, 'total_ticks': 114, 'zero_delta_reads': 886, 'max_delta_ticks': 1}
    raw = {'version': 1, 'fixture': 'worker_wait_clock_pair', 'status': 'complete', 'failure': None,
           'clock': 'mach_continuous_time', 'timebase': dict(CONSTRUCTED_TB), 'mode': mode,
           'pacing': ({'kind': 'yield_hints', 'hints_per_pass': HINTS_PER_PASS} if mode == 'busy' else
                      {'kind': 'nanosleep', 'requested_ns': SLEEP_PACING_NS[mode]}),
           'writer_pacing': {'kind': 'yield_hints', 'hints_per_pass': HINTS_PER_PASS},
           'injected_ms': inject_ms, 'injected_requested_ns': requested,
           'inject_method': 'none' if inject_ms == 0 else 'nanosleep', 'trials_requested': trials,
           'trials_complete': trials, 'read_overhead_samples': 1000, 'child_wait_limit_ns': 2_000_000_000,
           'watchdog': {'seconds': watchdog_seconds(trials, inject_ms), 'grace_seconds': WATCHDOG_GRACE_S,
                        'stage': 0, 'sigkill_sent': False},
           'parent_pid': 100,
           'children': {role: {'pid': pid, 'reaped': True, 'exit_code': 0, 'term_signal': None,
                               'state': 'finished', 'failure': 'none', 'failure_trial': None,
                               'failure_value': None} for role, pid in (('writer', 101), ('reader', 102))},
           'clock_start': {'continuous_raw': 9_000_000, 'absolute_raw': 4_000_000},
           'clock_end': {'continuous_raw': t + 50 + sleep_gap_ticks, 'absolute_raw': t + 50 - 5_000_000},
           'read_overhead': dict(overhead, when='before_fork'),
           'read_overhead_after': dict(overhead, when='after_reap'),
           'pass_histogram': {'unit': 'ticks', 'bucket': 'bit_length', 'counts': counts}, 'trials': rows}
    return rederive(raw)


def constructed_receipt(injects=INJECTS, raw_options=None, modify_raws=None):
    """A calibration assembled by the production assembler from constructed cells. The accepted
    receipt carries one injected sleep that overran the tolerance (a labeled outlier), an arm on
    the ready tick and an observation on the publication tick by a pass sampled before it."""
    options = {('busy', 1): {'overrun': {2: to_ticks(800_000)}},
               ('busy', 0): {'arm_same_tick': {4}, 'observe_same_tick': {5}}}
    options.update(raw_options or {})
    raws = [constructed_raw(m, i, **options.get((m, i), {})) for m in MODES for i in injects]
    if modify_raws:
        modify_raws(raws)
    cells = [{'mode': raw['mode'], 'inject_ms': raw['injected_ms'], 'order': k, 'directory': None,
              'stdout_sha256': None, 'returncode': 0, 'harness_timeout': False, 'group_killed': False,
              'group_members_after_exit': False, 'parse_error': None, 'stderr': '', 'raw': raw}
             for k, raw in enumerate(raws)]
    requested = {'modes': list(MODES), 'injects': list(injects), 'trials': 6, 'read_overhead_samples': 1000,
                 'inject_method': 'nanosleep'}
    check = {'before': {'monotonic_raw_before_ns': 333_333_000, 'continuous_ticks': 8_000_000,
                        'monotonic_raw_after_ns': 333_334_000},
             'after': {'monotonic_raw_before_ns': 3_333_333_000, 'continuous_ticks': 80_000_000,
                       'monotonic_raw_after_ns': 3_333_334_000}}
    snapshot = lambda t: {'loadavg': [0.5, 0.5, 0.5], 'sleep_clocks': {'monotonic_raw_ns': t, 'uptime_raw_ns': t - 10},
                          'pmset_batt': {'constructed': True}, 'pmset_settings': {'constructed': True},
                          'lowpowermode': '0'}
    binary = {'path': 'constructed', 'sha256': None, 'source': str(SOURCE), 'source_sha256': None}
    return json.loads(json.dumps(assemble(requested, binary, cells, check,
                                          {'before': snapshot(1_000_000_000), 'after': snapshot(4_000_000_000)})))


def cell_of(cal_or_raws, mode, inject_ms):
    for item in cal_or_raws:
        raw = item.get('raw', item)
        if raw['mode'] == mode and raw['injected_ms'] == inject_ms:
            return item
    raise KeyError((mode, inject_ms))


def reassembled(modify_raws, **kwargs):
    return constructed_receipt(modify_raws=modify_raws, **kwargs)


def edited(edit):
    cal = constructed_receipt()
    edit(cal)
    return cal


def _trial(raws, mode, inject_ms, index):
    return cell_of(raws, mode, inject_ms)['trials'][index]


def _set(raws, mode, inject_ms, index, **values):
    _trial(raws, mode, inject_ms, index).update(values)
    rederive(cell_of(raws, mode, inject_ms))


def _all_timebases(raws, tb):
    for raw in raws:
        raw['timebase'] = dict(tb)
        rederive(raw)


def _drop_last(raws):
    cell_of(raws, 'busy', 3)['trials'].pop()


def _incomplete(raws):
    raw = cell_of(raws, 'sleep1', 0)
    last = raw['trials'][-1]
    for key in ('ready_raw', 'first_pass_raw', 'last_negative_raw', 'pass_sample_raw', 'observed_raw',
                'published_raw_seen', 'passes', 'max_pass_interval_ticks'):
        last[key] = None
    last['reader_complete'], last['latency_ns'] = False, None
    raw.update(status='failed', failure='a child did not finish', trials_complete=len(raw['trials']) - 1)
    raw['children']['reader'].update(exit_code=11, state='failed', failure='wait_timeout', failure_trial=5,
                                     failure_value=5)


def _child_failed(raws):
    cell_of(raws, 'sleep2', 3)['children']['writer'].update(exit_code=10, state='failed', failure='inject_sleep_failed',
                                                            failure_trial=0, failure_value=1)


REJECTED = [
    ('negative_latency', 'negative_latency', lambda: edited(lambda c: cell_of(c['cells'], 'busy', 0)['raw']['trials'][0].update(latency_ns=-125))),
    ('observation_before_publication', 'observation_before_publication',
     lambda: reassembled(lambda r: _set(r, 'busy', 0, 1, observed_raw=_trial(r, 'busy', 0, 1)['published_raw'] - 1))),
    ('arm_before_ready', 'arm_before_ready',
     lambda: reassembled(lambda r: _set(r, 'busy', 2, 0, armed_raw=_trial(r, 'busy', 2, 0)['ready_raw'] - 1))),
    ('wrong_timebase_in_one_cell', 'timebase',
     lambda: reassembled(lambda r: (cell_of(r, 'sleep2', 1).update(timebase={'numer': 1, 'denom': 1}),
                                    rederive(cell_of(r, 'sleep2', 1))))),
    ('consistently_wrong_timebase', 'timebase', lambda: reassembled(lambda r: _all_timebases(r, {'numer': 1, 'denom': 1}))),
    ('missing_trial', 'missing_trials', lambda: reassembled(_drop_last)),
    ('incomplete_trial', 'missing_trials', lambda: reassembled(_incomplete)),
    ('unlabeled_injection_outlier', 'unlabeled_injection_outlier',
     lambda: edited(lambda c: cell_of(c['cells'], 'busy', 1)['labels'].clear())),
    ('spurious_label', 'spurious_label',
     lambda: edited(lambda c: cell_of(c['cells'], 'busy', 2)['labels'].append(
         {'trial': 0, 'label': 'injection_overran_tolerance', 'requested_ns': 2_000_000, 'actual_ns': 2_120_000,
          'tolerance_ns': INJECTION_TOLERANCE_NS}))),
    ('mailbox_mismatch', 'mailbox_mismatch',
     lambda: reassembled(lambda r: _set(r, 'sleep2', 0, 2, published_raw_seen=_trial(r, 'sleep2', 0, 2)['published_raw'] + 1))),
    ('child_failed', 'cell_failed', lambda: reassembled(_child_failed)),
    ('summary_tampered', 'summary_mismatch',
     lambda: edited(lambda c: cell_of(c['cells'], 'busy', 0)['summary']['latency_ns'].update(max=1))),
    ('resolution_tampered', 'resolution_mismatch',
     lambda: edited(lambda c: c['resolution']['readers']['busy'].update(gate_met=False))),
    ('matrix_missing_cell', 'matrix', lambda: edited(lambda c: c['cells'].pop())),
]

NOT_CREDITED = [
    ('system_sleep_overlap', 'system_sleep_overlap',
     lambda: constructed_receipt(raw_options={('busy', 0): {'sleep_gap_ticks': to_ticks(3_000_000_000)}})),
    ('sleeping_pacing_ineffective', 'sleeping_bracket_within_gate_sleep2',
     lambda: constructed_receipt(raw_options={('sleep2', i): {'pace': 10} for i in INJECTS})),
    ('boundary_disagreement', 'boundary_disagreement',
     lambda: constructed_receipt(raw_options={('busy', 1): {'visibility_delay': {3: to_ticks(1_200_000)}}})),
    ('boundary_side_unobserved', 'boundary_side_unobserved_above', lambda: constructed_receipt(injects=(0, 1))),
    ('busy_gate_exceeded', 'busy_combined_uncertainty_exceeds_gate',
     lambda: constructed_receipt(raw_options={('busy', 0): {'pace': to_ticks(600_000)}})),
    # One slow post-store read widens the endpoint term past the gate although every pacing bracket stays short.
    ('endpoint_bracket_outlier', 'busy_combined_uncertainty_exceeds_gate',
     lambda: constructed_receipt(raw_options={('busy', 0): {'store_delay': {2: to_ticks(600_000)}}})),
]


def constructed_controls(out=None):
    good = constructed_receipt()
    check_calibration(good)
    gate = good['resolution']['instrument_gate']
    assert gate['credited'] is True and gate['reasons'] == [], gate
    readers = good['resolution']['readers']
    assert readers['busy']['gate_met'] and not readers['sleep2']['gate_met'] and not readers['sleep1']['gate_met'], readers
    labels = cell_of(good['cells'], 'busy', 1)['labels']
    assert [x['label'] for x in labels] == ['injection_overran_tolerance'], labels
    same = cell_of(good['cells'], 'busy', 0)['summary']
    assert same['arm_same_tick_as_ready'] == 1 and same['observation_same_tick_as_publication'] == 1, same
    assert same['pass_sample_before_publication'] == 1 and same['first_load_observations'] == 1, same
    record = {'version': 1, 'accepted': {'credited': True, 'labels': labels,
                                         'busy_combined_uncertainty_ns': readers['busy']['combined_uncertainty_ns']},
              'rejected': [], 'not_credited': []}
    for name, code, build_fault in REJECTED:
        codes = [p['code'] for p in calibration_problems(build_fault())]
        assert code in codes, f'{name}: expected {code}, got {codes}'
        record['rejected'].append({'name': name, 'expected': code, 'codes': codes})
    for name, reason, build_condition in NOT_CREDITED:
        cal = build_condition()
        check_calibration(cal)
        gate = cal['resolution']['instrument_gate']
        assert gate['credited'] is False and reason in gate['reasons'], f'{name}: {gate}'
        record['not_credited'].append({'name': name, 'expected_reason': reason, 'reasons': gate['reasons']})
        if name == 'endpoint_bracket_outlier':
            busy = cal['resolution']['readers']['busy']
            assert busy['endpoint_term_ns'] > GATE_NS > busy['pacing_bracket_ns']['max'] + busy['alignment_bound_ns'], busy
            assert busy['endpoint_term_ns'] >= max(f['endpoint_brackets_ns'] for f in cell_facts(cell_of(cal['cells'], 'busy', 0)['raw']))
    if out is not None:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        save(out / 'clock-pair-controls.json', record)
    return record


def report(cal):
    res = cal['resolution']
    lines = [f'complete: {cal["complete"]}; timebase {cal["timebase"]}; '
             f'stamp {res["stamp_ns"]:.2f} ns (read {res["read_overhead_ns"]:.2f} ns, tick {res["tick_ns"]:.2f} ns); '
             f'alignment bound {res["alignment"]["bound_ns"]} ns']
    for cell in cal['cells']:
        s = cell['summary'] or {}
        lat, inj = s.get('latency_ns') or {}, s.get('actual_injected_ns') or {}
        lines.append(f'  {cell["mode"]:>6} inject {cell["inject_ms"]} ms: latency ns min {lat.get("min")} median '
                     f'{lat.get("median")} p95 {lat.get("p95")} max {lat.get("max")}; injected actual ns median '
                     f'{inj.get("median")} max {inj.get("max")}; passes {(s.get("passes") or {}).get("median")}; '
                     f'labels {[x["label"] for x in cell["labels"]]}')
    for mode, entry in res.get('readers', {}).items():
        lines.append(f'  {mode}: combined {entry["combined_uncertainty_ns"]} ns (p95 basis '
                     f'{entry["combined_uncertainty_p95_ns"]} ns), gate met {entry["gate_met"]}')
    gate = res['instrument_gate']
    lines.append(f'instrument gate credited: {gate["credited"]} {gate["reasons"]}')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build')
    b.add_argument('binary')
    b.add_argument('log_dir')
    r = sub.add_parser('run')
    r.add_argument('binary')
    r.add_argument('out_dir')
    r.add_argument('--modes', default=','.join(MODES))
    r.add_argument('--injects', default=','.join(map(str, INJECTS)))
    r.add_argument('--trials', type=int, default=100)
    r.add_argument('--read-overhead-samples', type=int, default=100_000)
    r.add_argument('--inject-method', default='nanosleep', choices=METHODS)
    c = sub.add_parser('check')
    c.add_argument('calibration')
    c.add_argument('--base')
    k = sub.add_parser('controls')
    k.add_argument('out_dir')
    args = parser.parse_args(argv)
    if args.command == 'build':
        print(json.dumps(build(args.binary, args.log_dir), indent=2))
    elif args.command == 'run':
        cal = run(args.binary, args.out_dir, args.modes.split(','), [int(x) for x in args.injects.split(',')],
                  args.trials, args.read_overhead_samples, args.inject_method)
        check_calibration(cal, base=args.out_dir)
        print(report(cal))
    elif args.command == 'check':
        cal = json.loads(Path(args.calibration).read_text())
        check_calibration(cal, base=args.base)
        print(report(cal))
    else:
        record = constructed_controls(args.out_dir)
        print(f'clock pair controls passed: accepted 1, rejected {len(record["rejected"])}, '
              f'not credited {len(record["not_credited"])}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
