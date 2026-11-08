"""Constructed worker-wait pilot receipts: accepted first, then each fault rejected.

Establishes the reader's decoding, arithmetic and refusal rules on constructed
inputs only; no stamp, timing or live trial is credited here. Comparison
controls pair constructed baseline and candidate rows and check each verdict
and response bound, and the stager's identity rules run on a constructed app
and source tree up to, never including, signing. Worker pages are
packed with offsets written from the C layout, in program order, including
loaded-record pairs, pass-count records and inbound pass samples appended after
later reads. Host exports carry each sleep as a 180/181 event pair beside its
register and a done register for the ordinary worker. A candidate-shaped
ordinary receipt adds the worker grace program points and one bounded exit wait
whose pair is followed by its outcome event; a candidate-shaped A2 receipt gives
each actor its own exit request, reap, grace program points, bounded exit wait
and grace stop. A2 receipts with constructed inbound scan counters check the
per-actor scan pairs: lower in every pair, a pair not lower, a ratio that only
exact arithmetic separates, and a pair refused for differing inbound counts.
Expected values are written from
the constructed microsecond times, not computed with the reader's functions.
"""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import worker_wait_pilot_reader as reader
import worker_wait_clock_pair as clock_pair

HOST_STAMPS = HERE.parents[2] / 'tests/fixtures/worker_wait/host_stamps.py'

OFFSETS = dict(header=0, stages=40, scan=280, events=848, event_size=24, size=24848)
C_STAGES = ['worker_start', 'proceed_start', 'proceed_observe', 'exec_admit', 'exec_observe', 'exec_reap',
            'activate_start', 'activate_observe', 'exchange_start', 'exchange_observe']
NUMER, DENOM = 125, 3
NONE = 0xFFFFFFFF
FLAVOUR = {'swift': '-Onone -g', 'inspection': True, 'target': 'arm64-apple-macosx26.0', 'swift_jobs': 2}
CALIBRATION = dict(stamp_ns=50, read_overhead_ns=40.0, endpoint_term_ns=300, alignment_ns=100,
                   instrument_gate=dict(credited=True, reasons=[]))
# Host record-path cost burst in ticks between consecutive raws: median 12 ticks (500 ns).
COST_STEPS = [12] * 13 + [0, 48]
WORKER_FLOOR, HOST_FLOOR, ALIGN = 300, 1000, 100
# Events the dry-run-04 receipts lack: pass counts, store-begin records, host sleep pairs.
CURRENT_ONLY = {13, 14, 15, 139, 149, 180, 181}
# Host sleep event pairs, which the dry-run-05 receipts also lack.
SLEEP_EVENTS = {180, 181}
SENTINEL_NS, ACTOR_POLL_NS = 2_000_000, 1_000_000
GRACE_POLL_NS = 10_000_000
# The WAIT_OUTCOME aux of each constructed grace wait; 'plain' is a key-5 sleep without one.
GRACE_OUTCOMES = dict(timed_out=0, notified=1, unusable=2, plain=None)


def tk(us):
    """Ticks for a whole number of microseconds at the 125/3 timebase (exact)."""
    return us * 24


def pack_page(events, *, stages=(), scan=None, pid, origin, flags=4, magic=0x50575753, version=1):
    """Events stay in the given (program) order."""
    data = bytearray(32768)
    struct.pack_into('<IIIIQIIII', data, OFFSETS['header'], magic, version, NUMER, DENOM, origin, flags, pid, len(events), 0)
    registers = dict(stages)
    for index, name in enumerate(C_STAGES):
        struct.pack_into('<QQQ', data, OFFSETS['stages'] + 24 * index, *registers.get(name, (0, 0, 0)))
    scan = scan or {}
    histogram = [0] * 65
    for visits, count in scan.get('histogram', {}).items(): histogram[visits] = count
    struct.pack_into('<71Q', data, OFFSETS['scan'], *(scan.get(k, 0) for k in ('passes_activation', 'passes_exchange', 'visits_activation',
                     'visits_exchange', 'loads_activation', 'loads_exchange')), *histogram)
    for index, (event, phase, aux, raw) in enumerate(events):
        struct.pack_into('<IIIIQ', data, OFFSETS['events'] + 24 * index, event, phase, aux, 0, raw)
    return bytes(data)


def encode(page):
    return base64.b64encode(page).decode('ascii')


def sleeps(**observed):
    out = {}
    for key in map(str, range(8)):
        if key in observed:
            count, requested, total, longest, shortest, pre, post = observed[key]
            out[key] = dict(count=count, last_pre=pre, last_post=post, last_requested_ns=requested, requested_sum_ns=requested * count,
                            sum_ticks=total * 3 // 125, max_ticks=longest * 3 // 125, min_ticks=shortest * 3 // 125,
                            sum_ns=total, max_ns=longest)
        else:
            out[key] = dict(count=0, last_pre=None, last_post=None, last_requested_ns=None, requested_sum_ns=0,
                            sum_ticks=0, max_ticks=None, min_ticks=None, sum_ns=0, max_ns=None)
    return out


def current(events, keep, sleep_events=True):
    events = events if keep else [e for e in events if e[0] not in CURRENT_ONLY]
    return events if sleep_events else [e for e in events if e[0] not in SLEEP_EVENTS]


def stamps_doc(sid, host_pid, base, host, registers, sleep_rows, pages, cost=True):
    doc = dict(version=1, host_pid=host_pid, specimen_id=sid, file_stem=sid, stamp_dir='/private/tmp/pw-worker-wait-stamps/constructed',
               timebase=dict(numer=NUMER, denom=DENOM), flavour=dict(swift='-Onone -g', inspection=True),
               capacity=dict(events=4096, register_phases=64, custody_phases=64, page_actors=8),
               dropped=dict(events=0, register_samples=0, sleeps=0, custody_passes=0, worker_pages=0), page_within_capture=True,
               started_marker=dict(status='written', errno=None, begin_raw=tk(base), end_raw=tk(base + 5)),
               clock_pairs=[dict(stage='request_start', observed=True, continuous_before=tk(base), monotonic_ns=7_000_000_000, continuous_after=tk(base + 1)),
                            dict(stage='flush', observed=True, continuous_before=tk(base + 60000), monotonic_ns=7_060_000_001, continuous_after=tk(base + 60001))],
               events=[[e, p, a, tk(base + t)] for e, p, a, t in host], registers=registers, sleeps=sleep_rows, custody_passes={},
               worker_pages=[dict(actor=a, pid=pid, event_count_read=count, reaped=True, capture_requested=False, copied_raw=tk(base + 71100 + a),
                                  base64=encode(page)) for a, pid, count, page in pages])
    if cost:
        raws = [tk(base + 1)]
        for step in COST_STEPS: raws.append(raws[-1] + step)
        doc['stamp_cost'] = dict(raws=raws)
    return doc


def conditions(regime, gap_ns, eligible):
    power = dict(source='Battery Power', lowpowermode='0', batt=dict(stdout="Now drawing from 'Battery Power'\n"), settings=dict(stdout=' lowpowermode         0\n'))
    clock = lambda t: dict(begin_ns=t, end_ns=t + 10, continuous_ns=t + 10, uptime_ns=t + 10)
    return dict(version=1, power_before=power, power_after=copy.deepcopy(power), clock_before=clock(1000), clock_after=clock(90_000_000),
                sleep_difference_ns=0, sleep_tolerance_ns=1_000_020, sleep_overlapped=False, loadavg_before=[1, 1, 1], loadavg_after=[1, 1, 1],
                pacing=dict(regime=regime, requested_gap_ns=0 if regime == 'rapid' else 1_000_000_000, actual_gap_ns=gap_ns,
                            eligible_gap_ns=eligible, previous_cleanup_ns=500, previous_cleanup_how='host_exit_event'))


def trial(app, cell, regime, sid, layout, index=0):
    return dict(version=1, app=app, cell=cell, regime=regime, index=index, specimen_id=sid, form=layout['form'], layout=layout,
                flavour=FLAVOUR, dry_run=False, warm=False, status='completed',
                whole_request=dict(elapsed_ns=40_000_000, elapsed_source='constructed', observer_bracket_ns=41_000_000))


def host_exit(pid, begin_ns):
    generation = dict(pid=pid, start_sec=100, start_usec=1)
    return dict(state='registered', registration=dict(generation=generation, begin_ns=begin_ns, end_ns=begin_ns + 100_000),
                event=dict(generation=generation, collection_begin_ns=begin_ns + 70_000_000, collection_end_ns=begin_ns + 70_000_100),
                cleanup_observed_how='host_exit_event', cleanup_ns=begin_ns + 70_000_100, host_pid=pid)


def ordinary_bundle(keep=True, worker_edit=None, index=0, sleep_events=True, grace=None):
    """O1: one phase, one eligible query. Times are microseconds from a 10 s base.
    Sentinel pass 1 (4000-4300) observes application and samples arrival and done negative; sleep 1
    (4310-6460) contains the worker's arrival; pass 2 observes arrival and runs the hook; pass 3 after
    release samples acknowledgement and done negative; sleep 2 (9270-11470) contains TERMINAL_PUBLISHED;
    pass 4 observes both. keep=False drops the records the dry-run-04 receipts lack;
    sleep_events=False drops the 180/181 pairs the dry-run-05 receipts lack. grace names how one worker grace
    wait ends (GRACE_OUTCOMES): the grace begins at 11.52 ms after the exit request (11.51 ms), the wait runs
    11.53-11.58 ms, the reap follows at 11.6 ms and the grace finishes at 11.61 ms."""
    b = 10_000_000
    host = [(100, NONE, 0, 0), (101, 0, 4242, 1000), (102, 0, 0, 3000), (103, 0, 2, 4000),
            (180, 1, SENTINEL_NS, 4310), (181, 1, SENTINEL_NS, 6460), (110, 0, 1, 6500), (111, 0, 0, 6510),
            (112, 0, 0, 6520), (120, 0, 0, 6530), (121, 0, 1, 6600), (122, 0, 0, 6610), (123, 0, 120, 6640), (124, 0, 0, 6660),
            (125, 0, 0, 6670), (126, 0, 7777, 7670), (127, 0, 0, 7680), (128, 0, 0, 7690), (129, 0, 0, 9000), (130, 0, 0, 9100),
            (131, 0, 0, 9110), (132, 0, 1, 9150), (133, 0, 0, 9160), (134, 0, 0, 9170), (135, 0, 1, 9180), (140, 0, 0, 9200),
            (139, 0, 1, 9248), (141, 0, 1, 9250), (180, 1, SENTINEL_NS, 9270), (181, 1, SENTINEL_NS, 11470),
            (142, 0, 1, 11500), (144, 0, 3, 11500), (146, 0, 0, 11510), (147, 0, 0, 11600),
            (170, 0, 0, 11700), (171, NONE, 0, 60000)]
    grace_sleep = {}
    if grace is not None:
        at = next(i for i, e in enumerate(host) if e[0] == 146) + 1
        outcome = GRACE_OUTCOMES[grace]
        host[at:at] = [(148, 0, 0, 11520), (180, 5, GRACE_POLL_NS, 11530), (181, 5, GRACE_POLL_NS, 11580)] + (
            [] if outcome is None else [(182, 5, outcome, 11580)])
        host.insert(next(i for i, e in enumerate(host) if e[0] == 147) + 1, (157, 0, 1, 11610))
        grace_sleep = {'5': (1, GRACE_POLL_NS, 50_000, 50_000, 50_000, tk(b + 11530), tk(b + 11580))}
    worker = [(1, NONE, 0, 1500), (2, NONE, 0, 3800), (3, 0, 0, 5000), (4, 0, 0, 5002), (4, 0, 0, 9249), (4, 0, 1, 9255),
              (5, 0, 1, 9256), (13, 0, 3000, 9256), (11, 0, 0, 9400), (12, NONE, 0, 9500)]
    host, worker = current(host, keep, sleep_events), current(worker, keep)
    if worker_edit: worker = worker_edit(worker)
    host = [(e, p, len(worker), t) if e == 170 else (e, p, a, t) for e, p, a, t in host]
    stages = {'worker_start': (1, tk(b + 1500), tk(b + 1500)), 'proceed_start': (1, tk(b + 5001), tk(b + 5001)),
              'proceed_observe': (3000, tk(b + 5002), tk(b + 9255))}
    page = pack_page([(e, p, a, tk(b + t)) for e, p, a, t in worker], stages=stages.items(), pid=4242, origin=tk(b + 1500))
    sid = f'O1-rapid-{index}-constructed'
    registers = {'110:0': dict(last_negative=tk(b + 4300), first_positive=tk(b + 6500), negatives=1),
                 '142:0': dict(last_negative=tk(b + 9260), first_positive=tk(b + 11500), negatives=1),
                 '144:0': dict(last_negative=tk(b + 9261), first_positive=tk(b + 11500), negatives=3)}
    stamps = stamps_doc(sid, 4141, b, host, registers,
                        sleeps(**{'1': (2, SENTINEL_NS, 4_350_000, 2_200_000, 2_150_000, tk(b + 9270), tk(b + 11470))}, **grace_sleep),
                        [(0, 4242, len(worker), page)], cost=keep)
    return dict(dir=f'constructed/O1/{index}', trial=trial('instrumented', 'O1', 'rapid', sid, dict(form='ordinary', phases=[dict(eligible=1)]), index),
                conditions=conditions('rapid', 30_000_000, [0, 250_000_000]), started=dict(host_pid=4141, specimen_id=sid, raw=tk(b)),
                stamps=stamps, host_exit=host_exit(4141, b * 1000 + 2_000_000),
                validation=dict(problems=[], host_ms_fields={'runner_subprocess.sentinel_wait.excluded_ms': 2,
                                                             'phases.0.validator_subprocess.exit_grace_wait.elapsed_ms': 0}))


A2_LAYOUT = dict(form='actor', actors=['issuer', 'subject'],
                 phases=[dict(phase_id='issue', actor=0, visit=0, eligible=0), dict(phase_id='consume', actor=1, visit=0, eligible=0),
                         dict(phase_id='hold', actor=1, visit=1, eligible=2), dict(phase_id='latertransfer', actor=0, visit=1, eligible=0),
                         dict(phase_id='laterconsume', actor=1, visit=2, eligible=0)],
                 deliveries=[dict(delivery=0, source=0, recipient=1, slot=0), dict(delivery=1, source=0, recipient=1, slot=1)])
TRANSFER_PHASE = {0: 0, 3: 1}
# After each phase's collection end tc: the visit's last stamp before its completion store, and the stamp after it.
COMPLETION_LAST = {0: 1250, 1: 100, 2: 100, 3: 1250, 4: 100}
COMPLETION_NEXT = {0: 1260, 1: 101, 2: 101, 3: 1300, 4: 200}
# First-check-positive observations: arrival in phase 0, acknowledgement in phase 1, completion in phase 3, delivery 1.
FIRST_CHECK = dict(arrival=0, ack=1, completion=3)
ISSUER_PASSES = dict(release=(40, 60), activation=(30, 20), exchange=(10, 1, 20))
SUBJECT_PASSES = dict(release=(100, 100, 100), activation=(200, 100, 100))


def phase_times(g):
    t = 20000 + 10000 * g
    return t, t + (3100 if A2_LAYOUT['phases'][g]['eligible'] else 1160)


# Candidate-shaped A2 cleanup, microseconds after the schedule's end: per actor its exit request (146), grace
# begin (148), one bounded exit wait (key 5) with its outcome (182), the reaping sample (147) and the grace
# finish (157) with its stop. Actor 0's wait is notified and the next sample reaps it; actor 1's wait times out,
# its constructed allowance is spent and the reap follows termination.
ACTOR_EXITS = {0: dict(exit=1100, begin=1110, wait=(1120, 1320), outcome=1, reap=1330, finished=1340, stop=1),
               1: dict(exit=1400, begin=1410, wait=(1420, 11470), outcome=0, finished=11480, reap=11600, stop=0)}


def actor_bundle(keep=True, worker_edit=None, host_edit=None, sleep_events=True, exits=False, scan=None):
    """A2 lifecycle in program order. Phase g activates at 20 ms + 10 ms * g (microseconds from a 100 s base).
    An execution sleep (1048 us) lies between each bracketed arrival's negative and positive samples, and a
    recipient sleep (980 us) inside each transfer wait. exits=True replaces the two reaping samples with the
    per-actor cleanup of ACTOR_EXITS. scan replaces an actor's page scan counters."""
    b = 100_000_000
    host = [(100, NONE, 0, 0), (101, 0, 5000, 1000), (101, 1, 5001, 1100), (160, NONE, 0, 15000)]
    registers = {}
    for g, entry in enumerate(A2_LAYOUT['phases']):
        t, tc = phase_times(g)
        arrival = t + 5 if g == FIRST_CHECK['arrival'] else t + 1100
        completed = tc + COMPLETION_NEXT[g] + 40
        host += [(149, g, g + 1, t - 1), (150, g, g + 1, t)]
        if g != FIRST_CHECK['arrival']:
            host += [(180, 3, ACTOR_POLL_NS, t + 51), (181, 3, ACTOR_POLL_NS, t + 1099)]
        host += [(110, g, 5, arrival), (111, g, 0, t + 1105), (112, g, 0, t + 1108),
                 (151, g, 0, t + 1110), (120, g, 0, t + 1120), (121, g, entry['eligible'], t + 1150)]
        if entry['eligible']:
            host += [(122, g, 0, t + 1160), (123, g, 200, t + 1200), (124, g, 0, t + 1210), (125, g, 0, t + 1220), (126, g, 9, t + 2220),
                     (127, g, 0, t + 2230), (128, g, 0, t + 2240), (129, g, 0, t + 2900), (130, g, 0, t + 2950), (131, g, 0, t + 2960),
                     (132, g, 2, t + 2980), (133, g, 0, t + 2990), (134, g, 0, t + 2995), (135, g, 1, t + 3000)]
        host += [(140, g, 0, tc - 2), (152, g, 0, tc), (139, g, entry['visit'] + 1, tc + 48), (141, g, entry['visit'] + 1, tc + 50),
                 (142, g, 1, tc + 60)]
        if g == 0:
            host += [(153, g, 0, tc + 100), (154, g, 1, tc + 105)]
        if g in TRANSFER_PHASE:
            # Transfer-wait stamps precede the custody pass record, whose start raw is earlier.
            host += [(155, g, TRANSFER_PHASE[g], tc + 150), (180, 6, ACTOR_POLL_NS, tc + 166), (181, 6, ACTOR_POLL_NS, tc + 1146),
                     (156, g, 1, tc + 1150), (153, g, 1, tc + 140), (154, g, 2, tc + 1160)]
        host += [(143, g, 3, completed)]
        bracketed = lambda negative, positive, n: dict(last_negative=tk(b + negative), first_positive=tk(b + positive), negatives=n)
        positive = lambda raw: dict(last_negative=None, first_positive=tk(b + raw), negatives=0)
        registers[f'110:{g}'] = positive(arrival) if g == FIRST_CHECK['arrival'] else bracketed(t + 50, arrival, 5)
        registers[f'142:{g}'] = positive(tc + 60) if g == FIRST_CHECK['ack'] else bracketed(tc + 51, tc + 60, 1)
        registers[f'143:{g}'] = positive(completed) if g == FIRST_CHECK['completion'] else bracketed(tc + COMPLETION_LAST[g] - 5, completed, 3)
    tc0, tc3 = phase_times(0)[1], phase_times(3)[1]
    registers['156:0'] = dict(last_negative=tk(b + tc0 + 165), first_positive=tk(b + tc0 + 1150), negatives=1)
    registers['156:1'] = dict(last_negative=None, first_positive=tk(b + tc3 + 1150), negatives=0)
    (t0, tc0), (t3, tc3) = phase_times(0), phase_times(3)
    ip = ISSUER_PASSES
    issuer = [(1, NONE, 0, 1500), (6, 0, 0, 2000), (6, 0, 0, t0 - 1), (6, 0, 1, t0 + 1), (7, 0, 1, t0 + 2), (14, 0, ip['activation'][0], t0 + 2),
              (3, 0, 0, t0 + 3), (4, 0, 0, t0 + 4), (4, 0, 0, tc0 + 49), (4, 0, 1, tc0 + 52), (5, 0, 1, tc0 + 53), (13, 0, ip['release'][0], tc0 + 53),
              (8, 0, 1, tc0 + 110), (15, 0, ip['exchange'][0], tc0 + 110), (11, 0, 0, tc0 + 120),
              (8, 1, 1, tc0 + 1240), (15, 1, ip['exchange'][1], tc0 + 1240), (11, 1, 0, tc0 + 1250),
              (6, 1, 1, tc0 + 1260), (6, 1, 1, t3 - 1), (6, 1, 4, t3 + 1), (7, 1, 4, t3 + 2), (14, 1, ip['activation'][1], t3 + 2),
              (3, 1, 0, t3 + 3), (4, 1, 1, t3 + 4), (4, 1, 1, tc3 + 49), (4, 1, 2, tc3 + 52), (5, 1, 2, tc3 + 53), (13, 1, ip['release'][1], tc3 + 53),
              (8, 2, 1, tc3 + 1240), (15, 2, ip['exchange'][2], tc3 + 1240), (11, 2, 0, tc3 + 1250), (12, NONE, 0, tc3 + 1300)]
    subject = [(1, NONE, 0, 1600), (2, NONE, 0, 3900), (6, 0, 0, 4000), (9, 0, 7, tc0 + 155), (10, 0, 0, tc0 + 170)]
    for v, g in enumerate((1, 2, 4)):
        t, tc = phase_times(g)
        if v:
            subject += [(6, v, g, phase_times((1, 2, 4)[v - 1])[1] + 101)]
        if g == 4:
            subject += [(9, 1, 7, tc3 + 155), (10, 1, 0, tc3 + 170)]
        subject += [(6, v, 0 if v == 0 else g, t - 1), (6, v, g + 1, t + 1), (7, v, g + 1, t + 2), (14, v, SUBJECT_PASSES['activation'][v], t + 2),
                    (3, v, 0, t + 3), (4, v, v, t + 4), (4, v, v, tc + 49), (4, v, v + 1, tc + 52), (5, v, v + 1, tc + 53),
                    (13, v, SUBJECT_PASSES['release'][v], tc + 53), (11, v, 0, tc + 100)]
    subject += [(12, NONE, 0, phase_times(4)[1] + 200)]
    t1, t2, t4 = phase_times(1)[0], phase_times(2)[0], phase_times(4)[0]
    tc1, tc2, tc4 = phase_times(1)[1], phase_times(2)[1], phase_times(4)[1]
    stages = {0: {'proceed_start': (2, tk(b + t0 + 3), tk(b + t3 + 3)), 'proceed_observe': (100, tk(b + t0 + 4), tk(b + tc3 + 52)),
                  'activate_start': (2, tk(b + 1999), tk(b + tc0 + 1255)), 'activate_observe': (50, tk(b + 2000), tk(b + t3 + 1)),
                  'exchange_start': (3, tk(b + tc0 + 100), tk(b + tc3 + 1200)), 'exchange_observe': (30, tk(b + tc0 + 101), tk(b + tc3 + 1239))},
              1: {'proceed_start': (3, tk(b + t1 + 3), tk(b + t4 + 3)), 'proceed_observe': (300, tk(b + t1 + 4), tk(b + tc4 + 52)),
                  'activate_start': (3, tk(b + 3999), tk(b + tc2 + 100)), 'activate_observe': (400, tk(b + 4000), tk(b + t4 + 1))}}
    scan = {0: {}, 1: dict(passes_activation=400, visits_activation=500, loads_activation=520, histogram={0: 300, 1: 80, 2: 20}), **(scan or {})}
    origins = {0: 1500, 1: 1600}
    workers = {0: current(issuer, keep), 1: current(subject, keep)}
    if worker_edit:
        workers = {a: worker_edit(a, events) for a, events in workers.items()}
    packed = {a: pack_page([(e, p, x, tk(b + t)) for e, p, x, t in events], stages=stages[a].items(), scan=scan[a], pid=5000 + a,
                           origin=tk(b + origins[a])) for a, events in workers.items()}
    end = phase_times(4)[1] + 2000
    host += [(161, NONE, 0, end + 1000)]
    grace_sleep = {}
    if exits:
        for actor, x in ACTOR_EXITS.items():
            cleanup = [(146, actor, 0, x['exit']), (148, actor, 0, x['begin']), (180, 5, GRACE_POLL_NS, x['wait'][0]),
                       (181, 5, GRACE_POLL_NS, x['wait'][1]), (182, 5, x['outcome'], x['wait'][1]),
                       (147, actor, 0, x['reap']), (157, actor, x['stop'], x['finished'])]
            host += [(e, p, a, end + t) for e, p, a, t in sorted(cleanup, key=lambda e: e[3])]
        durations = [(x['wait'][1] - x['wait'][0]) * 1000 for x in ACTOR_EXITS.values()]
        grace_sleep = {'5': (2, GRACE_POLL_NS, sum(durations), max(durations), min(durations),
                             tk(b + end + ACTOR_EXITS[1]['wait'][0]), tk(b + end + ACTOR_EXITS[1]['wait'][1]))}
        copied = ACTOR_EXITS[1]['reap'] + 100
    else:
        host += [(147, 0, 0, end + 1100), (147, 1, 0, end + 1110)]
        copied = 1200
    host += [(170, 0, len(workers[0]), end + copied), (170, 1, len(workers[1]), end + copied + 1), (171, NONE, 0, end + 50000)]
    host = current(host, keep, sleep_events)
    if host_edit: host = host_edit(host)
    sid = 'A2-rapid-0-constructed'
    stamps = stamps_doc(sid, 5555, b, host, registers,
                        sleeps(**{'3': (4, ACTOR_POLL_NS, 4_192_000, 1_048_000, 1_048_000, tk(b + t4 + 51), tk(b + t4 + 1099)),
                                  '6': (2, ACTOR_POLL_NS, 1_960_000, 980_000, 980_000, tk(b + tc3 + 166), tk(b + tc3 + 1146))}, **grace_sleep),
                        [(0, 5000, len(workers[0]), packed[0]), (1, 5001, len(workers[1]), packed[1])], cost=keep)
    return dict(dir='constructed/A2', trial=trial('instrumented', 'A2', 'rapid', sid, A2_LAYOUT),
                conditions=conditions('rapid', 40_000_000, [0, 250_000_000]), started=dict(host_pid=5555, specimen_id=sid, raw=tk(b)),
                stamps=stamps, host_exit=host_exit(5555, b * 1000 + 500_000),
                validation=dict(problems=[], host_ms_fields={'phases.2.visit_timing.collection_ms': 1}))


def neighbor_bundle():
    return dict(dir='constructed/neighbor', trial=trial('neighbor', 'O1', 'idle', 'O1-idle-0-neighbor', dict(form='ordinary', phases=[dict(eligible=1)])),
                conditions=conditions('idle', 1_050_000_000, [1_000_000_000, 1_250_000_000]), started=None, stamps=None,
                host_exit=dict(state='not_attempted', event=None, cleanup_observed_how='cli_exit_plus_margin', cleanup_ns=1),
                validation=dict(problems=[], host_ms_fields={'runner_subprocess.sentinel_wait.excluded_ms': 2}))


def endpoint(process, stamp, bracket_from, bracket_ns):
    return dict(process=process, stamp=stamp, bracket_from=bracket_from, bracket_ns=bracket_ns)


def check_ordinary(row):
    check_detection_total(row)
    assert row['status'] == 'accepted' and not row['problems'] and not row['exclusions'], row
    (phase,) = row['phases']
    value = lambda name: phase[name]['ns']
    expected = dict(arrival_detection=1_500_000, arrival_bookkeeping=20_000, planning=70_000, serialize=30_000, pipes=20_000,
                    spawn=1_000_000, spawn_to_first_read=1_330_000, spawn_to_eof=1_430_000, decode=40_000, eof_to_reap=70_000,
                    grace=20_000, collection=2_680_000, closure_to_release=50_000, release_to_ordinal_sample=5_000,
                    release_to_ack=6_000, ack_observation=2_244_000, held_total=4_256_000)
    assert {k: value(k) for k in expected} == expected, {k: value(k) for k in expected}
    assert 'arrival_first_check_positive' not in phase and 'ack_first_check_positive' not in phase
    # Endpoint brackets: arrival back to APPLIED (1.2 ms), release back to RELEASE_STORE_BEGIN (2 us), the
    # acknowledgement back to its accepting sample (1 us). Floors: worker 300, host max(300, 2 x 500).
    uncertainty = dict(arrival_detection=1_200_000 + HOST_FLOOR + ALIGN, arrival_bookkeeping=2 * HOST_FLOOR, serialize=2 * HOST_FLOOR,
                       closure_to_release=HOST_FLOOR + 2000, release_to_ordinal_sample=2000 + WORKER_FLOOR + ALIGN,
                       release_to_ack=2000 + 1000 + ALIGN, ack_observation=1000 + HOST_FLOOR + ALIGN, held_total=1_200_000 + 1000)
    assert {k: phase[k]['uncertainty_ns'] for k in uncertainty} == uncertainty, {k: phase[k]['uncertainty_ns'] for k in uncertainty}
    assert {phase[k]['uncertainty_basis'] for k in uncertainty} == {'calibrated'}
    assert not any(phase[k]['below_instrument_floor'] for k in uncertainty)
    assert phase['release_to_ack']['endpoints'] == [endpoint('host', 'release_stored', 'release_store_begin', 2000),
                                                    endpoint('worker0', 'proceed_acknowledged', 'proceed_ordinal_loaded', 1000)]
    assert phase['arrival_detection']['endpoints'] == [endpoint('worker0', 'proceed_arrived', 'applied', 1_200_000),
                                                       endpoint('host', 'arrival_observed', None, 0)]
    assert phase['arrival_detection']['detection_bracket_ns'] == 2_200_000 and phase['ack_observation']['detection_bracket_ns'] == 2_240_000
    # The host's done observation (11.5 ms) after TERMINAL_PUBLISHED (9.5 ms), bracketed back to ATTEMPT_PUBLISHED (9.4 ms).
    (done,) = row['done']
    assert set(done) == {'actor', 'done_detection'} and done['actor'] == 0, done
    assert (done['done_detection']['ns'], done['done_detection']['uncertainty_ns'], done['done_detection']['detection_bracket_ns']) == (
        2_000_000, 100_000 + HOST_FLOOR + ALIGN, 2_239_000), done
    assert done['done_detection']['endpoints'] == [endpoint('worker0', 'terminal_published', 'attempt_published', 100_000),
                                                   endpoint('host', 'done_observed', None, 0)]
    assert row['host_sleep_events'] == dict(state='complete', truncated_keys=[], pairs={'1': 2}), row['host_sleep_events']
    assert row['host_sleeps']['ordinary_sentinel']['event_durations_ns'] == [2_150_000, 2_200_000]
    assert row['request']['done_observed_offset_ns'] == 11_500_000
    assert phase['release_to_ack']['worker_detection_bracket_ns'] == 6000
    assert phase['eligible_planned'] == 1 and phase['payload_bytes'] == 120 and phase['grace_stop_code'] == 1
    assert phase['release_wait'] == dict(passes=3000, sampled_span_ns=4_253_000, mean_pass_period_ns=4_253_000 // 2999)
    assert row['worker_waits']['0']['per_wait'] == dict(release=[dict(visit=0, passes=3000, sampled_span_ns=4_253_000,
                                                                      mean_pass_period_ns=4_253_000 // 2999)], activation=[], exchange=[])
    assert row['worker_waits']['0']['release'] == dict(waits=1, passes=3000, mean_pass_period_ns=4_253_000 // 2999)
    cost = row['host_stamp_cost']
    assert (cost['records'], cost['min_ns'], cost['median_ns'], cost['max_ns']) == (16, 0, 500, 2000), cost
    sleep = row['host_sleeps']['ordinary_sentinel']
    assert (sleep['mean_ns'], sleep['mean_overshoot_ns'], sleep['min_ns'], sleep['last_ns']) == (2_175_000, 175_000, 2_150_000, 2_200_000), sleep
    assert row['host_sleeps']['ready_byte_wait']['count'] == 0 and 'mean_ns' not in row['host_sleeps']['ready_byte_wait']
    assert row['host_clock_pairs']['flush']['monotonic_minus_continuous_ns'] == 7_060_000_001 - 10_060_000_500
    assert row['clock_order']['inversions'] == 0 and [p['pair'] for p in row['clock_order']['pairs']] == ['p0:arrival', 'p0:release', 'p0:ack', 'w0:done']
    assert row['observer_overlap']['overlaps_held'] is False
    assert row['request']['applied_observed_offset_ns'] == 4_000_000 and row['request']['stamp_pages_copied'] == [10]
    assert row['host_ms_cross_checks']['sentinel_excluded']['stamped_ns'] == 2_680_000


def check_actor_intervals(row, grace=None):
    """w0: TERMINAL_PUBLISHED (9.5 ms) to EXIT_REQUESTED (11.51 ms), that to WORKER_REAPED (11.6 ms), and the grace
    from 11.52 to 11.61 ms when stamped. Program points: worker floor 300, host max(300, 2 x 500), alignment 100."""
    (actor,) = row['actors']
    assert actor['actor'] == 0 and set(actor) == {'actor', 'terminal_to_exit_request', 'exit_request_to_reap', 'grace_wait',
                                                  'grace_stop_code'}, actor
    values = lambda name: (actor[name]['ns'], actor[name]['uncertainty_ns'], actor[name]['cross_process'])
    assert values('terminal_to_exit_request') == (2_010_000, WORKER_FLOOR + HOST_FLOOR + ALIGN, True), actor
    assert actor['terminal_to_exit_request']['endpoints'] == [endpoint('worker0', 'terminal_published', None, 0),
                                                              endpoint('host', 'exit_requested', None, 0)]
    assert values('exit_request_to_reap') == (90_000, 2 * HOST_FLOOR, False), actor
    if grace is None:
        assert actor['grace_wait'] == dict(ns=None, unobserved='grace_not_stamped') and actor['grace_stop_code'] is None, actor
    else:
        assert values('grace_wait') == (90_000, 2 * HOST_FLOOR, False) and actor['grace_stop_code'] == 1, actor
        assert actor['grace_wait']['endpoints'] == [endpoint('host', 'worker_grace_begin', None, 0),
                                                    endpoint('host', 'worker_grace_finished', None, 0)]
    names = {name for name, _ in reader.component_values(row)}
    assert {'w0.terminal_to_exit_request', 'w0.exit_request_to_reap', 'w0.grace_wait'} <= names, names


def check_actor_exits(row, plain):
    """Each actor's cleanup from its own events (ACTOR_EXITS, after the schedule's end at 63.16 ms): issuer
    TERMINAL_PUBLISHED at 52.46 ms, subject at 61.36 ms. Every other interval keeps the plain A2 value."""
    assert row['status'] == 'accepted' and not row['problems'] and not row['exclusions'], row['problems']
    end = phase_times(4)[1] + 2000
    terminal = {0: phase_times(3)[1] + 1300, 1: phase_times(4)[1] + 200}
    values = lambda a, name: (a[name]['ns'], a[name]['uncertainty_ns'], a[name]['cross_process'])
    got = {a['actor']: a for a in row['actors']}
    assert sorted(got) == [0, 1], row['actors']
    for actor, x in ACTOR_EXITS.items():
        a = got[actor]
        assert values(a, 'terminal_to_exit_request') == ((end + x['exit'] - terminal[actor]) * 1000, WORKER_FLOOR + HOST_FLOOR + ALIGN, True), a
        assert a['terminal_to_exit_request']['endpoints'] == [endpoint(f'worker{actor}', 'terminal_published', None, 0),
                                                              endpoint('host', 'exit_requested', None, 0)], a
        assert values(a, 'exit_request_to_reap') == ((x['reap'] - x['exit']) * 1000, 2 * HOST_FLOOR, False), a
        assert values(a, 'grace_wait') == ((x['finished'] - x['begin']) * 1000, 2 * HOST_FLOOR, False), a
        assert a['grace_stop_code'] == x['stop'], a
    # The expected values differ between the actors, so a reader that took one actor's events for both fails here.
    assert got[0]['grace_stop_code'] != got[1]['grace_stop_code']
    assert all(got[0][name]['ns'] != got[1][name]['ns'] for name in ('terminal_to_exit_request', 'exit_request_to_reap', 'grace_wait'))
    assert tuple(row[name] for name in reader.GRACE_COUNTS) == (1, 1, 0, 0), [row[n] for n in reader.GRACE_COUNTS]
    assert row['grace_wait_record'] == dict(waits=2, recorded_pairs=2, outcome_events=dict(timed_out=1, notified=1, unusable=0),
                                            plain_sleeps=0, plain_sleeps_by_requested_ns={}, settle_sleeps=0, unrecorded=0), row['grace_wait_record']
    assert row['host_sleep_events'] == dict(state='complete', truncated_keys=[], pairs={'3': 4, '5': 2, '6': 2}), row['host_sleep_events']
    assert row['host_sleeps']['worker_grace']['event_durations_ns'] == [200_000, 10_050_000], row['host_sleeps']['worker_grace']
    exit_names = {f'w{a}.{n}' for a in ACTOR_EXITS for n in ('terminal_to_exit_request', 'exit_request_to_reap', 'grace_wait')}
    others = lambda r: {name: record['ns'] for name, record in reader.component_values(r) if name not in exit_names}
    assert exit_names <= {name for name, _ in reader.component_values(row)}
    assert others(row) == others(plain), {k: (v, others(plain).get(k)) for k, v in others(row).items() if v != others(plain).get(k)}


def actor_blind_intervals(stop_only):
    """The reader's per-actor intervals with the host lookups not matched by actor: every actor gets the first
    146, 147, 148 and 157, or (stop_only) only the stop code ignores the actor."""
    def intervals(doc, pages, interval):
        events, rows = doc['events'], []
        for actor in sorted(pages):
            terminal = reader.first(reader.records(pages[actor]), reader.W['terminal_published'])
            match = {} if not stop_only else dict(phase=actor)
            at = lambda name: (lambda e: reader.point(e and e[3], 'host', name))(reader.first(events, reader.H[name], **match))
            finished = reader.first(events, reader.H['worker_grace_finished'])
            rows.append(dict(actor=actor,
                             terminal_to_exit_request=interval(reader.point(terminal and terminal[3], f'worker{actor}', 'terminal_published'),
                                                               at('exit_requested'), missing='terminal_or_exit_request_unobserved'),
                             exit_request_to_reap=interval(at('exit_requested'), at('worker_reaped'), missing='exit_request_or_reap_unobserved'),
                             grace_wait=interval(at('worker_grace_begin'), at('worker_grace_finished'), missing='grace_not_stamped'),
                             grace_stop_code=finished and finished[2]))
        return rows
    return intervals


def actor_blind_rejected(plain):
    """check_actor_exits fails when the reader's per-actor lookups ignore the actor, wholly or for the stop code."""
    kept = reader.actor_intervals
    try:
        for stop_only in (False, True):
            reader.actor_intervals = actor_blind_intervals(stop_only)
            try:
                check_actor_exits(reader.evaluate_bundle(actor_bundle(exits=True), CALIBRATION), plain)
            except AssertionError:
                continue
            raise AssertionError(f'check_actor_exits accepted actor-blind intervals (stop_only={stop_only})')
    finally:
        reader.actor_intervals = kept
    return [dict(control=f'actor_blind_{which}', status='rejected', codes=['expected per-actor interval mismatch'])
            for which in ('intervals', 'stop_code')]


def check_grace(row, grace):
    """One key-5 wait counted by its outcome event; a 10 ms key-5 sleep without one is a timeout."""
    assert row['status'] == 'accepted' and not row['problems'] and not row['exclusions'], (grace, row['problems'])
    expected = dict(timed_out=(1, 0, 0, 0), notified=(0, 1, 0, 0), unusable=(0, 0, 1, 0), plain=(1, 0, 0, 0))[grace]
    assert tuple(row[name] for name in reader.GRACE_COUNTS) == expected, (grace, [row[n] for n in reader.GRACE_COUNTS])
    outcome = GRACE_OUTCOMES[grace]
    events = {name: int(code == outcome) for code, name in enumerate(('timed_out', 'notified', 'unusable'))}
    assert row['grace_wait_record'] == dict(waits=1, recorded_pairs=1, outcome_events=events, plain_sleeps=int(outcome is None),
                                            plain_sleeps_by_requested_ns={str(GRACE_POLL_NS): 1} if outcome is None else {},
                                            settle_sleeps=0, unrecorded=0), row['grace_wait_record']
    assert row['host_sleep_events'] == dict(state='complete', truncated_keys=[], pairs={'1': 2, '5': 1}), row['host_sleep_events']
    assert row['host_sleeps']['worker_grace']['event_durations_ns'] == [50_000]
    check_actor_intervals(row, grace)


def grace_rule_controls():
    """Grace counts on minimal host exports: waits past the 64 recorded pairs and 10 ms plain sleeps are timeouts;
    plain sleeps requested at most 100 us are settle sleeps."""
    def export(waits, count):
        events, raw = [], 0
        for requested, outcome in waits:
            events += [[180, 5, requested, raw], [181, 5, requested, raw + 10]] + ([] if outcome is None else [[182, 5, outcome, raw + 10]])
            raw += 100
        return dict(events=events, sleeps={'5': dict(count=count)})
    truncated = reader.grace_counts(export([(GRACE_POLL_NS, 1)] * 64, 70))
    assert (truncated['grace_timeouts'], truncated['grace_notified'], truncated['grace_unusable']) == (6, 64, 0), truncated
    assert (truncated['grace_wait_record']['recorded_pairs'], truncated['grace_wait_record']['unrecorded']) == (64, 6), truncated
    # A notified wait, two 100 us settle sleeps and one 10 ms sleep: the settle sleeps are counted apart and only
    # the 10 ms plain sleep is a timeout; a plain sleep just over the settle bound is a timeout.
    settled = reader.grace_counts(export([(GRACE_POLL_NS, 1), (100_000, None), (100_000, None), (GRACE_POLL_NS, None)], 4))
    assert (settled['grace_timeouts'], settled['grace_notified'], settled['grace_settle_sleeps']) == (1, 1, 2), settled
    assert settled['grace_wait_record']['plain_sleeps_by_requested_ns'] == {'100000': 2, '10000000': 1}, settled
    assert settled['grace_wait_record']['settle_sleeps'] == 2, settled
    over = reader.grace_counts(export([(100_001, None)], 1))
    assert (over['grace_timeouts'], over['grace_settle_sleeps']) == (1, 0), over
    assert reader.grace_counts(export([], 0))['grace_timeouts'] == 0
    assert reader.wait_outcome_problems([[180, 5, 1, 0], [181, 5, 1, 10], [182, 5, 2, 10]]) == set()
    assert reader.wait_outcome_problems([[180, 5, 1, 0], [181, 5, 1, 10], [182, 5, 3, 10]]) == {'host_wait_outcome_invalid'}
    assert reader.wait_outcome_problems([[182, 5, 1, 10]]) == {'host_wait_outcome_unpaired'}
    assert reader.wait_outcome_problems([[148, 1, 0, 10], [157, 1, 1, 10]]) == set()
    assert reader.wait_outcome_problems([[157, 1, 1, 10], [148, 1, 0, 10]]) == {'host_grace_interval_reversed'}
    return ['grace waits past 64 recorded pairs counted as timeouts', 'settle and poll sleeps without an outcome counted as timeouts by requested ns',
            'outcome and grace order rules on minimal exports']


def move_grace_finished(raw_us):
    """WORKER_GRACE_FINISHED moved before WORKER_GRACE_BEGIN, at raw_us."""
    def edit(bundle):
        events = bundle['stamps']['events']
        finished = next(e for e in events if e[0] == 157)
        events.remove(finished)
        finished[3] = tk(10_000_000 + raw_us)
        events.insert(next(i for i, e in enumerate(events) if e[0] == 148), finished)
    return edit


def move_wait_outcome(bundle):
    """The WAIT_OUTCOME moved from after its pair to just after WORKER_GRACE_BEGIN."""
    events = bundle['stamps']['events']
    outcome = next(e for e in events if e[0] == 182)
    events.remove(outcome)
    outcome[3] = tk(10_000_000 + 11525)
    events.insert(next(i for i, e in enumerate(events) if e[0] == 148) + 1, outcome)


def edit_wait_outcome(**fields):
    def edit(bundle):
        outcome = next(e for e in bundle['stamps']['events'] if e[0] == 182)
        for index, value in fields.items():
            outcome[dict(phase=1, aux=2, raw=3)[index]] = value(outcome)
    return edit


def check_ordinary_without_new_records(row):
    """The dry-run-04 shape: brackets fall back to the preceding host event and the host floor to the calibration term."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    (phase,) = row['phases']
    floor = CALIBRATION['endpoint_term_ns']
    assert phase['release_to_ack']['endpoints'][0] == endpoint('host', 'release_stored', 'hook_end', 50_000)
    assert phase['release_to_ack']['uncertainty_ns'] == 50_000 + 1000 + ALIGN
    assert phase['release_to_ack']['uncertainty_basis'] == 'calibrated (host_stamp_cost_absent, release_store_begin_absent)'
    assert phase['release_to_ack']['below_instrument_floor'] is True
    assert phase['closure_to_release']['uncertainty_ns'] == floor + 50_000 and phase['closure_to_release']['below_instrument_floor'] is True
    assert phase['serialize']['uncertainty_ns'] == 2 * floor and phase['serialize']['uncertainty_basis'] == 'calibrated (host_stamp_cost_absent)'
    assert phase['held_total']['uncertainty_ns'] == 1_200_000 + 1000 and phase['held_total']['uncertainty_basis'] == 'calibrated'
    assert phase['release_wait'] == dict(passes=None, unobserved='per-wait pass record absent')
    assert row['worker_waits']['0']['per_wait'] == dict(unavailable='no pass-count records on this page')
    assert row['host_stamp_cost'] == dict(median_ns=None, unobserved='stamp_cost absent from this export')


def check_first_check_positive(row, sleep_key, scope, span=None):
    """Arrival 5.0 ms, first (positive) host check 6.5 ms; span names the containing sleep's ordinal, duration,
    requested duration and the arrival's offset into it."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    (phase,) = row['phases']
    assert 'arrival_detection' not in phase and 'ack_observation' in phase
    record = phase['arrival_first_check_positive']
    assert (record['ns'], record['uncertainty_ns'], record['during_sleep_key']) == (1_500_000, 1_200_000 + HOST_FLOOR + ALIGN, sleep_key), record
    assert record['during_sleep'] == reader.SLEEP_KEYS.get(sleep_key) and 'detection_bracket_ns' not in record
    assert record['during_sleep_scope'] == scope, record
    if span is not None:
        assert record['during_sleep_span'] == dict(zip(('ordinal', 'duration_ns', 'requested_ns', 'stamp_after_begin_ns'), span)), record


def check_unattributed(row):
    """The worker arrives at 4.305 ms, before sleep 1 begins at 4.310 ms; the host's first check at 6.5 ms is positive."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    (phase,) = row['phases']
    record = phase['arrival_first_check_positive']
    assert (record['ns'], record['uncertainty_ns']) == (2_195_000, 505_000 + HOST_FLOOR + ALIGN), record
    assert (record['during_sleep_key'], record['during_sleep_scope']) == (None, 'unattributed') and 'during_sleep_span' not in record


def check_done_first_check_positive(row):
    """No negative done sample: TERMINAL_PUBLISHED (9.5 ms) lies in the second sentinel sleep (9.27-11.47 ms)."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    (done,) = row['done']
    record = done['done_first_check_positive']
    assert 'done_detection' not in done and record['ns'] == 2_000_000 and 'detection_bracket_ns' not in record, done
    assert (record['during_sleep_key'], record['during_sleep_scope'], record['during_sleep_span']) == (
        '1', 'event', dict(ordinal=1, duration_ns=2_200_000, requested_ns=SENTINEL_NS, stamp_after_begin_ns=230_000)), record


def check_done_unobserved(row):
    """A host export without the done register or event: labeled unobserved, not refused."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    assert row['done'] == [dict(actor=0, done_detection=dict(ns=None, unobserved='poll_register_absent'))], row['done']
    assert row['request']['done_observed_offset_ns'] is None


def check_inversion(row):
    """A 20 us release inversion is counted, kept, and widens the alignment of every cross-process interval."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    assert (row['clock_order']['inversions'], row['clock_order']['max_inversion_ns']) == (1, 20_000), row['clock_order']
    (phase,) = row['phases']
    assert phase['release_to_ack']['ns'] == -20_000 and phase['release_to_ack']['uncertainty_ns'] == 28_000 + 1000 + 20_000
    assert phase['release_to_ack']['uncertainty_basis'] == 'calibrated (alignment_widened_by_inversion)'
    assert phase['arrival_detection']['uncertainty_ns'] == 1_200_000 + HOST_FLOOR + 20_000
    assert phase['held_total']['uncertainty_ns'] == 1_200_000 + 1000 and phase['held_total']['uncertainty_basis'] == 'calibrated'


def per_wait_expected():
    """Each wait's passes and periods from the constructed microsecond times."""
    (t0, tc0), (t1, tc1), (t2, tc2), (t3, tc3), (t4, tc4) = map(phase_times, range(5))
    wait = lambda visit, passes, first, accepting: dict(visit=visit, passes=passes, sampled_span_ns=(accepting - first) * 1000,
                                                       mean_pass_period_ns=(accepting - first) * 1000 // (passes - 1))
    exchange = lambda slot, passes, lower, answered, name: dict(slot=slot, passes=passes, span_upper_ns=(answered - lower) * 1000,
                                                               span_from=name, upper_mean_pass_period_ns=(answered - lower) * 1000 // passes)
    ip, sp = ISSUER_PASSES, SUBJECT_PASSES
    return {'0': dict(release=[wait(0, ip['release'][0], t0 + 4, tc0 + 52), wait(1, ip['release'][1], t3 + 4, tc3 + 52)],
                      activation=[wait(0, ip['activation'][0], 2000, t0 + 1), wait(1, ip['activation'][1], tc0 + 1260, t3 + 1)],
                      exchange=[exchange(0, ip['exchange'][0], tc0 + 53, tc0 + 110, 'proceed_acknowledged'),
                                exchange(1, ip['exchange'][1], tc0 + 120, tc0 + 1240, 'attempt_published'),
                                exchange(2, ip['exchange'][2], tc3 + 53, tc3 + 1240, 'proceed_acknowledged')]),
            '1': dict(release=[wait(0, sp['release'][0], t1 + 4, tc1 + 52), wait(1, sp['release'][1], t2 + 4, tc2 + 52),
                               wait(2, sp['release'][2], t4 + 4, tc4 + 52)],
                      activation=[wait(0, sp['activation'][0], 4000, t1 + 1), wait(1, sp['activation'][1], tc1 + 101, t2 + 1),
                                  wait(2, sp['activation'][2], tc2 + 101, t4 + 1)],
                      exchange=[])}


def check_actor(row):
    check_detection_total(row)
    assert row['status'] == 'accepted' and not row['problems'] and not row['exclusions'], row
    phases = row['phases']
    assert [p['eligible_planned'] for p in phases] == [0, 0, 2, 0, 0]
    names = lambda base, g, which: base if g != FIRST_CHECK[which] else None
    for p in phases:
        g = p['phase']; t, tc = phase_times(g)
        arrival = 'arrival_first_check_positive' if g == FIRST_CHECK['arrival'] else 'arrival_detection'
        ack = 'ack_first_check_positive' if g == FIRST_CHECK['ack'] else 'ack_observation'
        completion = 'completion_first_check_positive' if g == FIRST_CHECK['completion'] else 'completion_detection'
        other = {'arrival_detection', 'arrival_first_check_positive', 'ack_observation', 'ack_first_check_positive',
                 'completion_detection', 'completion_first_check_positive'} - {arrival, ack, completion}
        assert not other & set(p), (g, other & set(p))
        completion_bracket = (COMPLETION_NEXT[g] - COMPLETION_LAST[g]) * 1000
        values = dict(activation_sample=(1000, HOST_FLOOR + WORKER_FLOOR + ALIGN), activation_response=(2000, 1000 + 1000 + ALIGN),
                      activation_to_arrival=(1000, 2000), closure_to_release=(50_000, HOST_FLOOR + 2000),
                      release_to_ordinal_sample=(2000, 2000 + WORKER_FLOOR + ALIGN), release_to_ack=(3000, 2000 + 1000 + ALIGN),
                      held_total=(((tc + 53) - (t + 3)) * 1000, 2000),
                      **{arrival: (2000 if g == FIRST_CHECK['arrival'] else 1_097_000, 1000 + HOST_FLOOR + ALIGN),
                         ack: (7000, 1000 + HOST_FLOOR + ALIGN),
                         completion: (40_000, max(completion_bracket, WORKER_FLOOR) + HOST_FLOOR + ALIGN)})
        got = {k: (p[k]['ns'], p[k]['uncertainty_ns']) for k in values}
        assert got == values, (g, got, values)
        assert {p[k]['uncertainty_basis'] for k in values} == {'calibrated'}, g
        assert p['activation_sample']['endpoints'][0] == endpoint('host', 'activation_stored', 'activation_store_begin', 1000)
        # Every visit, including the middle one (A2 phase 2), brackets its arrival back to its own ACTIVATION_STORED.
        assert p[arrival]['endpoints'][0] == endpoint(f"worker{p['actor']}", 'proceed_arrived', 'activation_stored', 1000), (g, p[arrival])
        assert p['activation_response']['worker_detection_bracket_ns'] == 2000 and p['release_to_ack']['worker_detection_bracket_ns'] == 3000
        assert p[completion]['endpoints'][0]['stamp'] == ('terminal_published' if g in (3, 4) else 'activation_loaded')
        assert p[completion]['endpoints'][0]['bracket_from'] == 'attempt_published'
        if g == FIRST_CHECK['arrival']:
            # No execution sleep lies between the arrival (t + 3 us) and its first check (t + 5 us).
            assert p[arrival]['during_sleep_key'] is None and p[arrival]['below_instrument_floor'] is True
            assert p[arrival]['during_sleep_scope'] == 'no_sleep_between', p[arrival]
        else:
            assert p[arrival]['detection_bracket_ns'] == 1_050_000
        for first_check in {ack, completion} & {'ack_first_check_positive', 'completion_first_check_positive'}:
            assert (p[first_check]['during_sleep_key'], p[first_check]['during_sleep_scope']) == (None, 'no_sleep_between'), (g, p[first_check])
        if g != FIRST_CHECK['ack']:
            assert p[ack]['detection_bracket_ns'] == 9000
        if g != FIRST_CHECK['completion']:
            assert p[completion]['detection_bracket_ns'] == (COMPLETION_NEXT[g] + 40 - COMPLETION_LAST[g] + 5) * 1000
        assert (p['release_to_ack']['below_instrument_floor'], p['held_total']['below_instrument_floor']) == (True, False)
    expected = per_wait_expected()
    for actor in ('0', '1'):
        assert row['worker_waits'][actor]['per_wait'] == expected[actor], (actor, row['worker_waits'][actor]['per_wait'])
    # Exchange waits belong to the visit whose acknowledgement precedes them: issuer slots 0 and 1 in phase 0, slot 2 in phase 3.
    exchanges = expected['0']['exchange']
    assert [p['exchange_waits'] for p in phases] == [exchanges[:2], [], [], exchanges[2:], []], [p['exchange_waits'] for p in phases]
    assert row['done'] == [] and row['host_sleep_events'] == dict(state='complete', truncated_keys=[], pairs={'3': 4, '6': 2})
    by_phase = {(p['actor'], p['visit']): p for p in phases}
    for actor, waits in expected.items():
        for kind in ('release', 'activation'):
            for w in waits[kind]:
                assert by_phase[(int(actor), w['visit'])][kind + '_wait'] == {k: w[k] for k in ('passes', 'sampled_span_ns', 'mean_pass_period_ns')}
    assert phases[2]['serialize']['ns'] == 40_000 and phases[2]['collection']['ns'] == 1_990_000
    transfers = phases[0]['custody'] + phases[3]['custody']
    assert [t['delivery'] for t in transfers] == [0, 1]
    for t in transfers:
        observed = 'inbound_ack_to_host_observed' if t['delivery'] == 0 else 'inbound_ack_first_check_positive'
        assert (t['service_to_wait_start']['ns'], t['wait_start_to_inbound_pass_sample']['ns'], t['inbound_pass_sample_to_ack']['ns'],
                t[observed]['ns'], t['host_wait_end_to_exchange_answered']['ns'], t['recipient_wait']['ns']) == (
                    10_000, 5_000, 15_000, 980_000, 90_000, 1_000_000), t
        assert t[observed]['uncertainty_ns'] == 15_000 + HOST_FLOOR + ALIGN
        assert t['inbound_pass_sample_to_ack']['below_instrument_floor'] is True
    assert transfers[0]['inbound_ack_to_host_observed']['detection_bracket_ns'] == 985_000 and 'inbound_ack_first_check_positive' not in transfers[0]
    observed = transfers[1]['inbound_ack_first_check_positive']
    assert (observed['during_sleep_key'], observed['during_sleep_scope'], observed['during_sleep_span']) == (
        '6', 'event', dict(ordinal=1, duration_ns=980_000, requested_ns=ACTOR_POLL_NS, stamp_after_begin_ns=4_000)), observed
    assert 'inbound_ack_to_host_observed' not in transfers[1]
    subject = row['worker_waits']['1']
    assert subject['release']['mean_pass_period_ns'] is None and subject['scan']['visits_per_pass_activation'] == 1.25
    assert subject['scan']['role_unknown_passes_uncounted'] is False
    assert row['clock_order']['inversions'] == 0


def check_actor_done(row):
    """An actor-form host that also samples the subject's done flag: done_detection for that worker only."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    (done,) = row['done']
    record = done['done_detection']
    assert done['actor'] == 1 and (record['ns'], record['detection_bracket_ns'], record['uncertainty_ns']) == (
        60_000, 110_000, 100_000 + HOST_FLOOR + ALIGN), done
    assert record['endpoints'][0] == endpoint('worker1', 'terminal_published', 'attempt_published', 100_000)


def check_without_sleep_events(row, full):
    """The dry-run-05 shape: no 180/181 pairs; every interval keeps its value and attribution uses the registers."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    assert row['host_sleep_events'] == dict(state='absent', attribution='sleep registers only')
    values = lambda r: {name: record['ns'] for name, record in reader.component_values(r)}
    assert values(row) == values(full), {k: (v, values(full).get(k)) for k, v in values(row).items() if v != values(full).get(k)}


def check_actor_without_new_records(row):
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    phases = row['phases']
    floor = CALIBRATION['endpoint_term_ns']
    first_activation = phases[0]['activation_sample']
    assert first_activation['endpoints'][0] == endpoint('host', 'activation_stored', 'setup_done', 5_000_000)
    assert first_activation['uncertainty_ns'] == 5_000_000 + floor + ALIGN
    assert first_activation['uncertainty_basis'] == 'calibrated (activation_store_begin_absent, host_stamp_cost_absent)'
    previous_completion = phase_times(0)[1] + COMPLETION_NEXT[0] + 40
    assert phases[1]['activation_sample']['endpoints'][0] == endpoint('host', 'activation_stored', 'completion_observed',
                                                                      (phase_times(1)[0] - previous_completion) * 1000)
    assert phases[2]['release_to_ack']['endpoints'][0] == endpoint('host', 'release_stored', 'collection_end', 50_000)
    assert phases[2]['arrival_detection']['endpoints'][0]['bracket_from'] == 'activation_stored'
    assert all(p['release_wait']['passes'] is None and p['activation_wait']['passes'] is None for p in phases)
    assert all(w['per_wait'] == dict(unavailable='no pass-count records on this page') for w in row['worker_waits'].values())


def old_uncertainty(self, start, end):
    """The pre-referee arithmetic: endpoint brackets + two calibration stamp costs + alignment."""
    cal, cross = self.calibration, start['process'] != end['process']
    if start['bracket_ns'] is None or end['bracket_ns'] is None:
        return dict(uncertainty_ns=None, uncertainty_basis='bracket_unobserved')
    alignment = max(cal['alignment_ns'], self.inversion_ns) if cross else 0
    return dict(uncertainty_ns=start['bracket_ns'] + end['bracket_ns'] + 2 * cal['stamp_ns'] + alignment, uncertainty_basis='calibrated')


def formula_rejected(formula, checks):
    """Each check fails when the reader's uncertainty arithmetic is replaced by formula."""
    kept = reader.Interval.uncertainty
    reader.Interval.uncertainty = formula
    try:
        for build, check in checks:
            try:
                check(reader.evaluate_bundle(build(), CALIBRATION))
            except AssertionError:
                continue
            raise AssertionError(f'{check.__name__} accepted the replaced uncertainty formula')
    finally:
        reader.Interval.uncertainty = kept


def write_bundle(root, bundle):
    t = bundle['trial']
    directory = root / 'trials' / t['app'] / t['cell'] / t['regime'] / str(t['index'])
    directory.mkdir(parents=True)
    for key, name in (('trial', 'trial.json'), ('conditions', 'conditions.json'), ('started', 'started.json'), ('stamps', 'stamps.json'),
                      ('host_exit', 'host-exit.json'), ('validation', 'validation.json')):
        if bundle[key] is not None:
            (directory / name).write_text(json.dumps(bundle[key]) + '\n')
    return directory


def write_calibration(root, calibration=None):
    """The clock pair's own constructed receipt, with its raw cell outputs on disk."""
    calibration = calibration or clock_pair.constructed_receipt()
    base = root / 'clock-pair'
    shutil.rmtree(base, ignore_errors=True)
    for cell in calibration['cells']:
        directory = Path('cells') / f"{cell['mode']}-inject{cell['inject_ms']}"
        (base / directory).mkdir(parents=True)
        text = json.dumps(cell['raw']).encode()
        (base / directory / 'stdout.json').write_bytes(text)
        cell['directory'], cell['stdout_sha256'] = str(directory), hashlib.sha256(text).hexdigest()
    (base / 'calibration.json').write_text(json.dumps(calibration))
    return clock_pair.resolution_numbers(calibration, base=base)


def write_identity(root):
    """Constructed staging and clock-pair build receipts for the summary header."""
    executables = lambda host, worker: {'executables': {reader.STAGED_HOST: dict(sha256=host), reader.STAGED_WORKER: dict(sha256=worker)}}
    (root / 'staged-identity-before.json').write_text(json.dumps(dict(instrumented=executables('a1' * 32, 'b2' * 32),
                                                                      neighbor=executables('c3' * 32, 'd4' * 32))))
    (root / 'clock-pair-build').mkdir()
    (root / 'clock-pair-build' / 'clock-pair-build.json').write_text(json.dumps(dict(binary_sha256='e5' * 32, source_sha256='f6' * 32)))


def page_fault(edit, index=0):
    def apply(bundle):
        entry = bundle['stamps']['worker_pages'][index]
        entry['base64'] = encode(edit(bytearray(base64.b64decode(entry['base64']))))
    return apply


def header(field, value):
    index = ['magic', 'version', 'numer', 'denom', 'origin', 'flags', 'pid', 'count'].index(field)
    def edit(data):
        values = list(struct.unpack_from('<IIIIQIIII', data, 0)); values[index] = value
        struct.pack_into('<IIIIQIIII', data, 0, *values); return data
    return edit


def scan_passes(value):
    def edit(data):
        struct.pack_into('<Q', data, OFFSETS['scan'], value); return data
    return edit


def swap_fresh(data):
    """Swap the raws of APPLIED and PROCEED_ARRIVED, two reads taken at append."""
    first = struct.unpack_from('<IIIIQ', data, OFFSETS['events'] + 24)
    second = struct.unpack_from('<IIIIQ', data, OFFSETS['events'] + 48)
    struct.pack_into('<IIIIQ', data, OFFSETS['events'] + 24, *first[:4], second[4])
    struct.pack_into('<IIIIQ', data, OFFSETS['events'] + 48, *second[:4], first[4])
    return data


def early_observation(bundle):
    """Host arrival observation 900 us before the worker's arrival stamp, appended before the first sentinel sleep."""
    b, stamps = 10_000_000, bundle['stamps']
    stamps['registers']['110:0'] = dict(last_negative=tk(b + 4050), first_positive=tk(b + 4100), negatives=1)
    events = stamps['events']
    observed = next(e for e in events if e[0] == 110)
    events.remove(observed)
    observed[3] = tk(b + 4100)
    events.insert(next(i for i, e in enumerate(events) if e[0] == 103) + 1, observed)


def arrival_negative_free(bundle):
    """The host's first arrival check (6.5 ms) is already positive."""
    stamps = bundle['stamps']
    stamps['registers']['110:0'] = dict(last_negative=None, first_positive=tk(10_000_000 + 6500), negatives=0)
    next(e for e in stamps['events'] if e[0] == 110)[2] = 0


def early_arrival(events):
    """The worker arrives at 4.305 ms, its first pass sample at 4.306 ms: before the first sentinel sleep begins."""
    return [(e, p, a, 4305 if e == 3 else 4306 if (e, t) == (4, 5002) else t) for e, p, a, t in events]


def done_negative_free(bundle):
    """The host's first done check (11.5 ms) is already positive."""
    stamps = bundle['stamps']
    stamps['registers']['144:0'] = dict(last_negative=None, first_positive=tk(10_000_000 + 11500), negatives=0)
    next(e for e in stamps['events'] if e[0] == 144)[2] = 0


def done_absent(bundle):
    """A host export with no done register or DONE_OBSERVED event while the worker's TERMINAL_PUBLISHED is present."""
    stamps = bundle['stamps']
    del stamps['registers']['144:0']
    stamps['events'] = [e for e in stamps['events'] if e[0] != 144]


def actor_done_observed(bundle):
    """The actor host also samples the subject's done flag: negative 150 us and positive 260 us after the last collection end."""
    b, tc4, stamps = 100_000_000, phase_times(4)[1], bundle['stamps']
    stamps['registers']['144:1'] = dict(last_negative=tk(b + tc4 + 150), first_positive=tk(b + tc4 + 260), negatives=2)
    events = stamps['events']
    events.insert(next(i for i, e in enumerate(events) if e[0] == 161), [144, 1, 2, tk(b + tc4 + 260)])


def sleep_pair(bundle, ordinal):
    """The host events and the index of the ordinal-th HOST_SLEEP_BEGIN."""
    events = bundle['stamps']['events']
    return events, [i for i, e in enumerate(events) if e[0] == 180][ordinal]


def drop_sleep_end(bundle):
    events, begin = sleep_pair(bundle, 1); del events[begin + 1]


def drop_sleep_begin(bundle):
    events, begin = sleep_pair(bundle, 0); del events[begin]


def drop_sleep_pair(bundle):
    events, begin = sleep_pair(bundle, 0); del events[begin:begin + 2]


def sleep_requested_changed(bundle):
    events, begin = sleep_pair(bundle, 0); events[begin][2] = events[begin + 1][2] = 2_500_000


def sleep_end_later(bundle):
    """The first sleep's end record 10 us later than the register's tick sum allows (still before the next event)."""
    events, begin = sleep_pair(bundle, 0); events[begin + 1][3] += tk(10)


def first_check_positive(count):
    """The host's first arrival check is positive; one sentinel sleep register spans the worker's arrival."""
    def edit(bundle):
        b, stamps = 10_000_000, bundle['stamps']
        stamps['registers']['110:0'] = dict(last_negative=None, first_positive=tk(b + 6500), negatives=0)
        stamps['sleeps']['1'].update(count=count, last_pre=tk(b + 4100), last_post=tk(b + 6490))
    return edit


def late_release_stamp(bundle):
    """The host's post-store release stamp follows the worker's acknowledgement by 20 us."""
    next(e for e in bundle['stamps']['events'] if e[0] == 141)[3] = tk(10_000_000 + 9276)


def watch_inside_held(bundle):
    """The driver's exit-watch registration runs 1 ms after the worker's arrival, inside the held interval."""
    bundle['host_exit']['registration'].update(begin_ns=10_006_000_000, end_ns=10_006_100_000)


def edited(build, edit):
    bundle = build(); edit(bundle); return bundle


def codes(row):
    return set(row['problems']) | set(row['exclusions'])


def order_rule_controls():
    """A pass sample appended after a later read is accepted; a fresh read going backwards is not."""
    event = lambda code, raw: dict(event=code, phase=0, aux=0, raw=raw)
    sampled_after_later_read = [event(1, 10), event(9, 50), event(10, 60), event(6, 50), event(6, 70), event(7, 71)]
    assert reader.worker_order_problems(sampled_after_later_read, 10) == set()
    assert reader.worker_order_problems([event(1, 10), event(3, 60), event(10, 50)], 10) == {'worker_events_non_monotonic'}
    assert reader.worker_order_problems([event(1, 10), event(6, 80), event(7, 70)], 10) == {'worker_events_non_monotonic'}
    assert reader.worker_order_problems([event(1, 10), event(6, 70), event(6, 60), event(7, 90)], 10) == {'worker_events_non_monotonic'}
    assert reader.worker_order_problems([event(1, 11), event(3, 20)], 10) == {'worker_origin_mismatch'}
    return ['sampled_inversion_accepted', 'fresh_backwards', 'sample_after_next_read', 'sample_backwards', 'origin_mismatch']


def sleep_rule_controls():
    """Sleep pairing, register agreement and attribution on minimal host exports (timebase 1/1, ticks = ns)."""
    def export(pairs, registers):
        events = []
        for key, begin, end in pairs:
            events += [[180, key, 1000, begin], [181, key, 1000, end]]
        return dict(events=events, timebase=dict(numer=1, denom=1),
                    sleeps={str(k): dict(count=c, last_pre=pre, last_post=post, last_requested_ns=1000, requested_sum_ns=1000 * c,
                                         sum_ticks=ticks, sum_ns=ticks, max_ns=0, min_ticks=0)
                            for k, (c, pre, post, ticks) in registers.items()})
    def attribute(doc, raw, until):
        found = reader.sleep_attribution(doc, reader.sleep_record(doc['events']), raw, until)
        return found['during_sleep_key'], found['during_sleep_scope']
    # Key 7 slept 70 times: 64 recorded pairs of 10 ns at 1000 ns spacing, then 6 sleeps ending with 70000-70010.
    recorded = [(7, 1000 * i, 1000 * i + 10) for i in range(64)]
    truncated = export(recorded, {7: (70, 70_000, 70_010, 700)})
    assert reader.sleep_event_problems(truncated) == set()
    assert reader.sleep_event_state(truncated, reader.sleep_record(truncated['events']))['truncated_keys'] == ['7']
    assert attribute(truncated, 5, 50) == ('7', 'event')
    assert attribute(truncated, 70_005, 70_100) == ('7', 'events_truncated')
    # Unrecorded sleeps may lie anywhere between the last pair and the register's last pre read.
    assert attribute(truncated, 64_500, 64_600) == (None, 'unattributed')
    # With one unrecorded sleep the register pair is that sleep, so the window is known to hold none.
    assert attribute(export(recorded, {7: (65, 70_000, 70_010, 650)}), 64_500, 64_600) == (None, 'no_sleep_between')
    assert reader.sleep_event_problems(export(recorded + [(7, 64_000, 64_010)], {7: (70, 70_000, 70_010, 700)})) == {
        'host_sleep_event_count_mismatch'}
    # Complete pairs: a recorded sleep between publication and observation leaves it unattributed.
    complete = export([(1, 100, 200), (1, 300, 400)], {1: (2, 300, 400, 200)})
    assert reader.sleep_event_problems(complete) == set()
    assert attribute(complete, 150, 450) == ('1', 'event')
    assert attribute(complete, 250, 450) == (None, 'unattributed') and attribute(complete, 410, 450) == (None, 'no_sleep_between')
    # Registers alone: single-wait keys first, then a multi-count key's last pair; an earlier sleep of a
    # multi-count key could lie anywhere before its last pair.
    registers = export([], {1: (1, 100, 200, 100), 2: (2, 150, 250, 150)})
    assert attribute(registers, 160, 300) == ('1', 'single_wait') and attribute(registers, 220, 300) == ('2', 'last_pair_of_multi_count')
    assert attribute(export([], {1: (1, 400, 500, 100)}), 250, 300) == (None, 'no_sleep_between')
    assert attribute(export([], {1: (2, 400, 500, 100)}), 250, 300) == (None, 'unattributed')
    assert attribute(export([], {}), 250, 300) == (None, 'no_sleep_between')
    # Summary formatting: no -0.0, and the attribution labels.
    assert [reader.us(v) for v in (None, -49, -1, 0, 49, -60, 1500)] == ['-', '0.0', '0.0', '0.0', '0.0', '-0.1', '1.5']
    assert reader.sleeps({'unattributed': 1, 'none': 2, '1': 3}, {'event': 3}) == (
        'ordinary_sentinel 3, none (no host sleep between) 2, unattributed (no containing sleep) 1 [scope event 3]')
    return ['sleep events truncated past 64 per key accepted and attributed', 'sleep events between publication and observation unattributed',
            'register-only sleep attribution and no-sleep-between rule', 'tiny negative and attribution label formatting']


def refused_as_pooled(rows):
    try:
        reader.aggregate(rows)
    except AssertionError as error:
        assert 'pooled groups refused' in str(error), error
        return True
    return False


# ---- comparison runs ---------------------------------------------------------------

COMPARISON = dict(apps=['baseline', 'candidate'], pairing_rule='constructed: same cell, regime and repetition index')
VERDICTS = ('improves_beyond_uncertainty_in_every_pair', 'improves_beyond_spread_in_every_pair',
            'worsens_beyond_instrument_uncertainty', 'worsens_beyond_spread_in_any_pair',
            'worsens_beyond_spread_in_every_pair')


def check_detection_total(row):
    """detection_total is the sum of the row's post-publication detection records, excluding the first ordinary
    phase's arrival, with the parts' uncertainties summed."""
    total = row['detection_total']
    parts = [(n, r) for n, r in reader.component_values(row) if n != 'detection_total' and r.get('ns') is not None
             and n.rpartition('.')[2] in reader.DETECTION_LEAVES
             and not (row.get('form') == 'ordinary' and n.startswith('p0.arrival'))]
    if not parts:
        assert total['ns'] is None and total['components'] == [], total
        return 0
    assert total['ns'] == sum(r['ns'] for _, r in parts) and total['components'] == [n for n, _ in parts], total
    assert total['uncertainty_ns'] == sum(r['uncertainty_ns'] for _, r in parts), total
    assert ('detection_total', total) in list(reader.component_values(row))
    return len(parts)


def check_every_pair_worsening(pairs, required):
    """The every-pair worsening verdict follows its definition on every series: refuted by an established pair
    that is not worse, established only when all required pairs are established and worse, else withheld."""
    checked = 0
    for entry in pairs.get('entries', []):
        for section in ('components', 'waits', 'whole_request'):
            series = entry.get(section) or {}
            series = series if 'pairs' not in series else {'whole_request': series}
            for name, value in series.items():
                if not isinstance(value, dict) or 'pairs' not in value or 'improves_beyond_spread_in_every_pair' not in value:
                    continue
                outcomes = [r['spread_outcome'] for r in value['pairs']]
                established = [o for o in outcomes if o in ('improved', 'worsened', 'within_spread')]
                complete = len(established) == len(outcomes) >= required
                expected = False if any(o != 'worsened' for o in established) else True if complete else None
                assert value['worsens_beyond_spread_in_every_pair'] is expected, (entry.get('cell'), name, outcomes, value['worsens_beyond_spread_in_every_pair'])
                checked += 1
    assert checked > 0, 'no paired series were checked'
    return checked
BASELINE_ARRIVAL, BASELINE_HELD, CANDIDATE_ARRIVAL, CANDIDATE_HELD = 7_100_000, 8_900_000, 900_000, 2_700_000
DIRECTION_RULE = 'sign of baseline minus candidate per pair'


def pair_row(base, app, index, values=(), *, form=None, passes=3000, whole_ms=50, ready=(1, 12_500_000), status='accepted', **fields):
    """A baseline or candidate row from the evaluated constructed O1 row. values maps a phase-0 component to
    (ns, uncertainty ns); form renames the constructed arrival_detection record."""
    row = copy.deepcopy(base)
    row.update(app=app, index=index, status=status, dir=f'constructed/{app}/O1/rapid/{index}', **fields)
    phase = row['phases'][0]
    if form:
        phase[form] = phase.pop('arrival_detection')
    for name, (value, uncertainty) in dict(values).items():
        phase[name].update(ns=value, uncertainty_ns=uncertainty)
    phase['release_wait']['passes'] = passes
    row['whole_request'] = dict(elapsed_ns=whole_ms * 1_000_000)
    row['host_sleeps']['ready_byte_wait'].update(count=ready[0], sum_ns=ready[1])
    return row


def improving_rows(base, count=3, candidate_edits=None):
    """The candidate's arrival and held total are shorter by 6.2 to 6.4 ms in every pair, with 1.3 us per side.
    candidate_edits maps an index to replacement (ns, uncertainty) values."""
    rows = []
    for i in range(count):
        step = 100_000 * i
        rows.append(pair_row(base, 'baseline', i, {'arrival_first_check_positive': (BASELINE_ARRIVAL + step, 1300),
                                                   'held_total': (BASELINE_HELD + step, 1300)},
                             form='arrival_first_check_positive', passes=3000 + 10 * i, whole_ms=50 + i))
        values = {'arrival_detection': (CANDIDATE_ARRIVAL, 1300), 'held_total': (CANDIDATE_HELD, 1300)}
        values.update((candidate_edits or {}).get(i, {}))
        rows.append(pair_row(base, 'candidate', i, values, passes=1000, whole_ms=44 + i, ready=(2, 3_000_000)))
    return rows


def pairs_of(rows, required=3, gate=True):
    pairs = reader.matched_pairs(rows, dict(COMPARISON, pairs_required=required), gate)
    if pairs is not None:
        check_every_pair_worsening(pairs, required)
    return pairs


def outcomes(series):
    return [(r['index'], r['difference'], r['combined_uncertainty'], r['outcome']) for r in series['pairs']]


def verdicts(series):
    """(improves: instrument, spread; worsens: instrument, spread any). The every-pair worsening verdict is
    checked against its definition on every series by check_every_pair_worsening."""
    return tuple(series[v] for v in VERDICTS[:4])


def comparison_controls(base):
    """Matched-pair verdicts, spreads and response bounds on constructed baseline and candidate rows."""
    names = []
    (entry,) = pairs_of(improving_rows(base))['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (True, True, False, False) and 'withheld' not in arrival, arrival
    assert outcomes(arrival) == [(i, 6_200_000 + 100_000 * i, 2600, 'improved') for i in range(3)], arrival
    assert all(r['forms'] == dict(baseline='arrival_first_check_positive', candidate='arrival_detection') for r in arrival['pairs'])
    # Baseline arrivals 7.1 to 7.3 ms, candidate arrivals all 0.9 ms.
    assert arrival['spread_ns'] == dict(baseline=dict(ns=200_000, trials=3), candidate=dict(ns=0, trials=3)), arrival['spread_ns']
    assert [(r['improve_threshold'], r['worsen_threshold'], r['spread_outcome']) for r in arrival['pairs']] == [(2600, 202_600, 'improved')] * 3
    held = entry['components']['p0.held_total']
    assert verdicts(held) == (True, True, False, False) and outcomes(held) == [(i, 6_200_000 + 100_000 * i, 2600, 'improved') for i in range(3)], held
    # Components left equal differ by zero, within their uncertainty and spread: not improved, not worse.
    serialize = entry['components']['p0.serialize']
    assert verdicts(serialize) == (False, False, False, False) and [o[3] for o in outcomes(serialize)] == ['within_uncertainty'] * 3, serialize
    passes = entry['waits']['p0.release_wait']
    assert verdicts(passes) == (True, True, False, False) and outcomes(passes) == [(i, 2000 + 10 * i, 0, 'improved') for i in range(3)], passes
    assert passes['spread_ns'] == dict(baseline=dict(ns=20, trials=3), candidate=dict(ns=0, trials=3)), passes['spread_ns']
    # Whole request: no instrument uncertainty, so spread verdicts only; 6 ms shorter against a 2 ms candidate spread.
    whole = entry['whole_request']
    assert whole['spread_ns'] == dict(baseline=dict(ns=2_000_000, trials=3), candidate=dict(ns=2_000_000, trials=3)), whole
    assert verdicts(whole) == (None, True, None, False) and 'instrument_verdicts' in whole and 'withheld' not in whole, whole
    assert outcomes(whole) == [(i, 6_000_000, 0, 'not_applicable') for i in range(3)], whole
    assert whole['direction'] == dict(faster=3, slower=0, equal=0, rule=DIRECTION_RULE), whole['direction']
    assert entry['response'] == {'p0.release_to_ack': dict(
        candidate_upper_ns=6000, baseline_lower_ns=6000, bound_ns=0, limit_ns=2_000_000, within_limit=True, combined_uncertainty_ns=6200,
        uncertainty_at_most_0_5_ms=True, instrument_gate_credited=True, credited=True, trials=dict(baseline=3, candidate=3))}, entry['response']
    assert entry['host_sleeps']['ready_byte_wait'] == [dict(index=i, baseline=dict(count=1, sum_ns=12_500_000),
                                                            candidate=dict(count=2, sum_ns=3_000_000)) for i in range(3)]
    assert entry['host_sleeps']['ordinary_sentinel'][0]['candidate'] == dict(count=2, sum_ns=4_350_000)
    assert [p['index'] for p in entry['pairs']] == [0, 1, 2] and pairs_of(improving_rows(base))['unpaired'] == []
    names.append('candidate arrival and held total shorter beyond uncertainty and beyond its spread in every pair: improvement')

    # Whole request 50, 51, 52 ms against 44, 51, 60 ms: one pair each faster, equal and slower.
    mixed = [pair_row(base, app, i, whole_ms=ms) for i, pair in enumerate(((50, 44), (51, 51), (52, 60)))
             for app, ms in zip(reader.PAIR_APPS, pair)]
    (entry,) = pairs_of(mixed)['entries']
    assert entry['whole_request']['direction'] == dict(faster=1, slower=1, equal=1, rule=DIRECTION_RULE), entry['whole_request']
    assert [r['difference'] for r in entry['whole_request']['pairs']] == [6_000_000, 0, -8_000_000]
    names.append('whole-request direction counts faster, equal and slower pairs by the sign of the difference')

    # Grace counts: one timeout per baseline trial, one notification per candidate trial, one candidate count absent.
    rows = [pair_row(base, app, i, **(dict(grace_timeouts=1) if app == 'baseline' else dict(grace_notified=1)))
            for i in range(3) for app in reader.PAIR_APPS]
    rows[5]['grace_unusable'] = None
    (entry,) = pairs_of(rows)['entries']
    grace = entry['grace']
    assert set(grace) == set(reader.GRACE_COUNTS)
    assert [(r['baseline'], r['candidate'], r['difference']) for r in grace['grace_timeouts']['pairs']] == [(1, 0, 1)] * 3, grace
    assert grace['grace_timeouts']['sums'] == dict(baseline=3, candidate=0) and grace['grace_notified']['sums'] == dict(baseline=0, candidate=3)
    assert [r['difference'] for r in grace['grace_notified']['pairs']] == [-1] * 3
    assert grace['grace_unusable']['pairs'][2] == dict(index=2, absent_on=['candidate']) and grace['grace_unusable']['sums'] == dict(baseline=0, candidate=0)
    assert all('improves_beyond_uncertainty_in_every_pair' not in value for value in grace.values())
    names.append('grace counts paired as exact differences with per-side sums, an absent count kept as absent')

    within = {1: {'arrival_detection': (BASELINE_ARRIVAL + 100_000 - 2000, 1300)}}
    (entry,) = pairs_of(improving_rows(base, candidate_edits=within))['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (False, False, False, False) and outcomes(arrival)[1] == (1, 2000, 2600, 'within_uncertainty'), arrival
    names.append('one pair within uncertainty: no improvement verdict')

    # One candidate arrival of 6.0 ms: 1.3 ms shorter than its baseline, beyond uncertainty but not beyond the 5.1 ms candidate spread.
    spread = {2: {'arrival_detection': (6_000_000, 1300)}}
    (entry,) = pairs_of(improving_rows(base, candidate_edits=spread))['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (True, False, False, False), arrival
    assert arrival['spread_ns']['candidate'] == dict(ns=5_100_000, trials=3)
    assert [(r['difference'], r['improve_threshold'], r['spread_outcome']) for r in arrival['pairs']] == [
        (6_200_000, 5_102_600, 'improved'), (6_300_000, 5_102_600, 'improved'), (1_300_000, 5_102_600, 'within_spread')], arrival['pairs']
    names.append('improvement beyond uncertainty in every pair but within the candidate spread in one: no spread improvement verdict')

    # 10 us worse in one pair: beyond the instrument uncertainty, within the 200 us baseline spread.
    worse = {2: {'held_total': (BASELINE_HELD + 200_000 + 10_000, 1300)}}
    (entry,) = pairs_of(improving_rows(base, candidate_edits=worse))['entries']
    held = entry['components']['p0.held_total']
    assert verdicts(held) == (False, False, True, False) and outcomes(held)[2] == (2, -10_000, 2600, 'worsened'), held
    assert (held['pairs'][2]['worsen_threshold'], held['pairs'][2]['spread_outcome']) == (202_600, 'within_spread'), held['pairs'][2]
    assert verdicts(entry['components']['p0.arrival_to_observation']) == (True, True, False, False)
    names.append('one pair worse beyond uncertainty but within the baseline spread: instrument worsening only')

    # 500 us worse in one pair: beyond the baseline spread plus both uncertainties.
    worse_spread = {2: {'held_total': (BASELINE_HELD + 200_000 + 500_000, 1300)}}
    (entry,) = pairs_of(improving_rows(base, candidate_edits=worse_spread))['entries']
    held = entry['components']['p0.held_total']
    assert verdicts(held) == (False, False, True, True), held
    assert (held['pairs'][2]['difference'], held['pairs'][2]['worsen_threshold'], held['pairs'][2]['spread_outcome']) == (
        -500_000, 202_600, 'worsened'), held['pairs'][2]
    names.append('one pair worse beyond the baseline spread: spread worsening')

    # Fewer pairs than required: an improvement is withheld, a refutation or a worse pair is not.
    (entry,) = pairs_of(improving_rows(base), required=5)['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (None, None, None, None) and arrival['withheld'] == '3 established of 5 required pairs', arrival
    assert verdicts(entry['components']['p0.serialize']) == (False, False, None, None)
    (entry,) = pairs_of(improving_rows(base, candidate_edits=worse), required=5)['entries']
    assert verdicts(entry['components']['p0.held_total']) == (False, False, True, None)
    names.append('fewer pairs than required: improvement withheld, refutation and worsening kept')

    slow = {0: {'release_to_ack': (2_506_000, 3100)}}
    (entry,) = pairs_of(improving_rows(base, candidate_edits=slow))['entries']
    response = entry['response']['p0.release_to_ack']
    assert (response['bound_ns'], response['within_limit'], response['credited']) == (2_500_000, False, False), response
    wide = {0: {'release_to_ack': (1_006_000, 600_000)}}
    (entry,) = pairs_of(improving_rows(base, candidate_edits=wide))['entries']
    response = entry['response']['p0.release_to_ack']
    assert (response['bound_ns'], response['within_limit'], response['combined_uncertainty_ns'], response['uncertainty_at_most_0_5_ms'],
            response['credited']) == (1_000_000, True, 603_100, False, False), response
    (entry,) = pairs_of(improving_rows(base), gate=False)['entries']
    response = entry['response']['p0.release_to_ack']
    assert (response['within_limit'], response['instrument_gate_credited'], response['credited']) == (True, False, False), response
    names.append('response bound beyond 2 ms, or within it without the resolution or the gate: not credited')

    rows = improving_rows(base) + [
        pair_row(base, 'baseline', 3, {'arrival_first_check_positive': (BASELINE_ARRIVAL, 1300)}, form='arrival_first_check_positive', whole_ms=51),
        pair_row(base, 'candidate', 3, {'arrival_detection': (CANDIDATE_ARRIVAL, 1300)}, status='excluded', exclusions=['observer_overlap']),
        pair_row(base, 'baseline', 4, whole_ms=51),
        pair_row(base, 'candidate', 4, power_source='AC Power')]
    found = pairs_of(rows)
    battery = next(e for e in found['entries'] if e['power_source'] == 'Battery Power')
    assert [p['index'] for p in battery['pairs']] == [0, 1, 2], battery['pairs']
    assert verdicts(battery['components']['p0.arrival_to_observation']) == (True, True, False, False)
    assert [(u['app'], u['index'], u['status'], u['reason'], u['other_status']) for u in found['unpaired']] == [
        ('baseline', 3, 'accepted', 'not accepted on both sides', 'excluded'),
        ('candidate', 3, 'excluded', 'not accepted on both sides', 'accepted'),
        ('baseline', 4, 'accepted', 'conditions differ (power source, low power mode or host flavour)', 'accepted'),
        ('candidate', 4, 'accepted', 'conditions differ (power source, low power mode or host flavour)', 'accepted')], found['unpaired']
    # Unpaired accepted trials still count in their own side's spreads and response bounds, never as pairs.
    assert battery['response']['p0.release_to_ack']['trials'] == dict(baseline=5, candidate=3)
    assert battery['whole_request']['spread_ns'] == dict(baseline=dict(ns=2_000_000, trials=5), candidate=dict(ns=2_000_000, trials=3))
    mains = next(e for e in found['entries'] if e['power_source'] == 'AC Power')
    assert mains['pairs'] == [] and mains['components'] == {} and mains['response'] == {}, mains
    names.append('unpaired trials (one side excluded, conditions differ) listed and never paired')

    # Identical receipts on both sides: every difference is zero, so no improvement and no worsening.
    same = [pair_row(base, app, i) for i in range(2) for app in reader.PAIR_APPS]
    (entry,) = pairs_of(same, required=2)['entries']
    series = [*entry['components'].values(), *entry['waits'].values()]
    assert series and all(verdicts(v) == (False, False, False, False) for v in series), [
        (v, verdicts(v)) for v in series if verdicts(v) != (False, False, False, False)]
    assert verdicts(entry['whole_request']) == (None, False, None, False)
    assert entry['whole_request']['direction'] == dict(faster=0, slower=0, equal=2, rule=DIRECTION_RULE)
    uncalibrated = reader.evaluate_bundle(ordinary_bundle(), None)
    (entry,) = pairs_of([pair_row(uncalibrated, app, i) for i in range(2) for app in reader.PAIR_APPS], required=2)['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (None, None, None, None), arrival
    assert arrival['withheld'] == '0 established of 2 required pairs; absent or unestablished in 2', arrival
    assert verdicts(entry['waits']['p0.release_wait']) == (False, False, False, False)
    assert reader.matched_pairs(same, None, True) is None
    names.append('identical receipts: no improvement or worsening verdict; uncalibrated: verdicts withheld; not a comparison: no pairs')
    return names


# Subject (two inbound slots) scan counters: the baseline visits both slots on every pass; the candidate's
# passes visit two, one or no slots. The issuer has no inbound slot and makes 30 zero-visit passes on both sides.
ISSUER_SCAN = dict(passes_activation=30, histogram={0: 30})
BASELINE_SCAN = dict(passes_activation=400, visits_activation=800, loads_activation=840, histogram={2: 400})
CANDIDATE_SCAN = dict(passes_activation=400, visits_activation=140, loads_activation=160, histogram={0: 300, 1: 60, 2: 40})
# 1/3 against 10**17 / (3 * 10**17 + 1): equal as floats, lower exactly.
THIRD_SCAN = dict(passes_activation=3, visits_activation=1, loads_activation=1, histogram={0: 2, 1: 1})
NEAR_THIRD_SCAN = dict(passes_activation=3 * 10**17 + 1, visits_activation=10**17, loads_activation=10**17,
                       histogram={0: 2 * 10**17 + 1, 1: 10**17})
SCAN_NAMES = [f'w{a}.scan_{m}_per_pass_{r}' for a in (0, 1) for r in ('activation', 'exchange') for m in ('visits', 'loads')]


def scan_row(app, index, subject, inbound=2):
    """An evaluated A2 row with the given subject scan counters; inbound changes the subject's layout deliveries."""
    bundle = actor_bundle(scan={0: ISSUER_SCAN, 1: subject})
    bundle['trial'].update(app=app, index=index)
    bundle['trial']['layout']['deliveries'] = [dict(delivery=d, source=0, recipient=1, slot=d) for d in range(inbound)]
    row = reader.evaluate_bundle(bundle, CALIBRATION)
    assert row['status'] == 'accepted', row['problems']
    return dict(row, dir=f'constructed/{app}/A2/rapid/{index}')


def scan_rows(candidates, baseline=BASELINE_SCAN, inbound=None):
    """Baseline and candidate rows per index; candidates lists each index's candidate subject counters."""
    return [row for i, scan in enumerate(candidates)
            for row in (scan_row('baseline', i, baseline), scan_row('candidate', i, scan, (inbound or {}).get(i, 2)))]


def scan_outcomes(entry, name):
    return [r['outcome'] for r in entry['scan']['series'][name]['pairs']]


def scan_controls():
    """Per-actor scan pairs on constructed A2 receipts: exact counts, lower_in_every_pair and the inbound refusal."""
    names = []
    row = scan_row('baseline', 0, BASELINE_SCAN)
    assert row['scan'] == {
        '0': dict(passes_activation=30, visits_activation=0, loads_activation=0, passes_exchange=0, visits_exchange=0, loads_exchange=0,
                  zero_visit_passes=30, inbound_count=0, inbound_count_source=reader.SCAN_INBOUND_SOURCE, role_unknown_passes_uncounted=False),
        '1': dict(passes_activation=400, visits_activation=800, loads_activation=840, passes_exchange=0, visits_exchange=0, loads_exchange=0,
                  zero_visit_passes=0, inbound_count=2, inbound_count_source=reader.SCAN_INBOUND_SOURCE, role_unknown_passes_uncounted=False)}, row['scan']
    assert row['worker_waits']['1']['scan']['visits_per_pass_activation'] == 2.0

    (entry,) = pairs_of(scan_rows([CANDIDATE_SCAN] * 3))['entries']
    scan = entry['scan']
    assert sorted(scan['series']) == sorted(SCAN_NAMES) and scan['refusals'] == [] and scan['problems'] == [], scan
    visits = scan['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is True and 'withheld' not in visits, visits
    assert visits['pairs'] == [dict(index=i, baseline=dict(count=800, passes=400, per_pass=2.0), candidate=dict(count=140, passes=400, per_pass=0.35),
                                    inbound_count=dict(baseline=2, candidate=2), outcome='lower') for i in range(3)], visits['pairs']
    loads = scan['series']['w1.scan_loads_per_pass_activation']
    assert loads[reader.SCAN_LOWER] is True and [(r['baseline']['count'], r['candidate']['count']) for r in loads['pairs']] == [(840, 160)] * 3
    for name in ('w1.scan_visits_per_pass_exchange', 'w1.scan_loads_per_pass_exchange'):
        value = scan['series'][name]
        assert value[reader.SCAN_LOWER] is None and scan_outcomes(entry, name) == ['no_passes'] * 3, value
        assert value['withheld'] == '0 established of 3 required pairs; absent, without passes or refused in 3', value
        assert value['pairs'][0]['no_passes_on'] == ['baseline', 'candidate']
    issuer = scan['series']['w0.scan_visits_per_pass_activation']
    assert issuer[reader.SCAN_LOWER] is False and scan_outcomes(entry, 'w0.scan_visits_per_pass_activation') == ['not_lower'] * 3, issuer
    zero = scan['zero_visit_passes']
    assert zero['w1.scan_zero_visit_passes'] == dict(pairs=[dict(index=i, baseline=0, candidate=300, difference=-300) for i in range(3)],
                                                     sums=dict(baseline=0, candidate=900)), zero
    assert zero['w0.scan_zero_visit_passes']['sums'] == dict(baseline=90, candidate=90)
    assert all(reader.SCAN_LOWER not in value for value in zero.values())
    text = '\n'.join(reader.pairs_markdown(pairs_of(scan_rows([CANDIDATE_SCAN] * 3))))
    for needle in ('| w1.scan_visits_per_pass_activation | yes | r0 800/400 -> 140/400; r1 800/400 -> 140/400; r2 800/400 -> 140/400 |',
                   '| w0.scan_visits_per_pass_activation | no | r0 0/30 -> 0/30;',
                   '| w1.scan_zero_visit_passes (sum baseline / candidate 0 / 900) | no verdict | r0 0 -> 300; r1 0 -> 300; r2 0 -> 300 |'):
        assert needle in text, needle
    names.append('candidate subject visits and loads per scan pass lower in every pair: lower_in_every_pair; zero-visit passes per side')

    (entry,) = pairs_of(scan_rows([CANDIDATE_SCAN] * 3), required=5)['entries']
    visits = entry['scan']['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is None and visits['withheld'] == '3 established of 5 required pairs', visits
    names.append('scan pairs lower in all three of five required pairs: withheld')

    (entry,) = pairs_of(scan_rows([CANDIDATE_SCAN, BASELINE_SCAN, CANDIDATE_SCAN]))['entries']
    assert scan_outcomes(entry, 'w1.scan_visits_per_pass_activation') == ['lower', 'not_lower', 'lower']
    assert entry['scan']['series']['w1.scan_visits_per_pass_activation'][reader.SCAN_LOWER] is False
    names.append('one scan pair equal to its baseline: not lower in every pair')

    (entry,) = pairs_of(scan_rows([NEAR_THIRD_SCAN] * 3, baseline=THIRD_SCAN))['entries']
    visits = entry['scan']['series']['w1.scan_visits_per_pass_activation']
    assert visits['pairs'][0]['baseline']['per_pass'] == visits['pairs'][0]['candidate']['per_pass'], visits['pairs'][0]
    assert visits[reader.SCAN_LOWER] is True and scan_outcomes(entry, 'w1.scan_visits_per_pass_activation') == ['lower'] * 3, visits
    names.append('a candidate ratio below the baseline that floats round to equal: lower by exact arithmetic')

    (entry,) = pairs_of(scan_rows([CANDIDATE_SCAN] * 3, inbound={2: 3}))['entries']
    scan = entry['scan']
    assert scan['refusals'] == [dict(index=2, actor=1, problem=reader.SCAN_REFUSAL, inbound_count=dict(baseline=2, candidate=3))], scan['refusals']
    assert scan['problems'] == [reader.SCAN_REFUSAL]
    for name in SCAN_NAMES[4:]:
        assert scan_outcomes(entry, name)[2] == 'refused' and scan['series'][name]['pairs'][2]['problem'] == reader.SCAN_REFUSAL, name
    visits = scan['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is None and visits['withheld'] == '2 established of 3 required pairs; absent, without passes or refused in 1', visits
    assert scan['zero_visit_passes']['w1.scan_zero_visit_passes']['pairs'][2]['problem'] == reader.SCAN_REFUSAL
    assert scan_outcomes(entry, 'w0.scan_visits_per_pass_activation') == ['not_lower'] * 3
    (entry,) = pairs_of(scan_rows([CANDIDATE_SCAN, BASELINE_SCAN, CANDIDATE_SCAN], inbound={2: 3}))['entries']
    assert entry['scan']['series']['w1.scan_visits_per_pass_activation'][reader.SCAN_LOWER] is False
    text = '\n'.join(reader.pairs_markdown(pairs_of(scan_rows([CANDIDATE_SCAN] * 3, inbound={2: 3}))))
    assert 'Refused scan pairs: r2 w1 scan_inbound_count_mismatch (inbound_count 2 / 3).' in text and 'r2 800/400 -> 140/400 (refused)' in text, text
    names.append('a scan pair whose subject inbound_count differs between the sides: refused, verdict withheld or refuted by the rest')

    (group,) = reader.summarize([scan_row('candidate', i, CANDIDATE_SCAN) for i in range(3)])
    stat = lambda value, n=3: dict(n=n, median=value, min=value, max=value, sum=n * value)
    assert group['scan']['1'] == dict(inbound_count=[2], passes_activation=stat(400), visits_activation=stat(140), loads_activation=stat(160),
                                      passes_exchange=stat(0), visits_exchange=stat(0), loads_exchange=stat(0), zero_visit_passes=stat(300)), group['scan']
    assert group['scan']['0']['zero_visit_passes'] == stat(30) and group['scan']['0']['inbound_count'] == [0]
    names.append('scan counters summed with medians per actor in a group')
    return names


def scan_float_rejected():
    """The exact-arithmetic scan control fails when the reader compares per-pass ratios as floats."""
    kept = reader.scan_lower
    reader.scan_lower = lambda bc, bp, cc, cp: cc / cp < bc / bp
    try:
        scan_controls()
    except AssertionError:
        return dict(control='scan_ratio_float_comparison', status='rejected', codes=['scan outcome mismatch'])
    finally:
        reader.scan_lower = kept
    raise AssertionError('the scan controls accepted a reader that compares per-pass ratios as floats')


def spread_ignored_rejected(base):
    """The matched-pair controls fail when the reader's spread term is replaced by zero."""
    kept = reader.side_spread
    reader.side_spread = lambda values: 0
    try:
        comparison_controls(base)
    except AssertionError:
        return dict(control='spread_term_ignored', status='rejected', codes=['spread verdict mismatch'])
    finally:
        reader.side_spread = kept
    raise AssertionError('the comparison controls accepted a reader that ignores the spread term')


def comparison_round_trip(out):
    """A comparison run's receipts through the loader and writers: baseline and candidate stay separate groups."""
    root = out / 'constructed-comparison'
    shutil.rmtree(root, ignore_errors=True)
    for index in range(3):
        for app in reader.PAIR_APPS:
            bundle = ordinary_bundle(index=index)
            bundle['trial']['app'] = app
            if (app, index) == ('candidate', 2):
                watch_inside_held(bundle)
            write_bundle(root, bundle)
    (root / 'schedule.json').write_text(json.dumps(dict(required={f'{app}/O1/rapid': 2 for app in reader.PAIR_APPS},
                                                        comparison=dict(COMPARISON, pairs_required=2))))
    write_calibration(root)
    decomposition, summary = reader.read_artifacts(root)
    assert [(g['app'], g['counts']['accepted']) for g in summary['groups']] == [('baseline', 3), ('candidate', 2)], summary['groups']
    (entry,) = summary['pairs']['entries']
    assert [p['index'] for p in entry['pairs']] == [0, 1] and len(summary['pairs']['unpaired']) == 2
    assert all(verdicts(v) == (False, False, False, False) for v in (*entry['components'].values(), *entry['waits'].values()))
    assert verdicts(entry['whole_request']) == (None, False, None, False)
    # Each pair's uncertainty is the sum of its two trials' own uncertainties.
    side = {(r['app'], r['index']): r['phases'][0]['arrival_detection']['uncertainty_ns'] for r in decomposition['rows']}
    combined = [side[('baseline', i)] + side[('candidate', i)] for i in range(2)]
    assert [r['combined_uncertainty'] for r in entry['components']['p0.arrival_to_observation']['pairs']] == combined
    assert [r['app'] for r in summary['observer_overlap']] == ['baseline'] * 3 + ['candidate'] * 3
    text = (root / 'summary.md').read_text()
    for needle in ('## Matched pairs', '### O1 rapid (Battery Power, lowpowermode 0)', 'Pairs: 2 of 2 required (repetitions 0, 1)',
                   "candidate r2 excluded (not accepted on both sides) ['observer_overlap']",
                   f'| p0.arrival_to_observation | no / no | no / no / no | 0.0 / 0.0 | r0 0.0 ± {combined[0] / 1000:.1f} (detected/detected); '
                   f'r1 0.0 ± {combined[1] / 1000:.1f} (detected/detected) |',
                   '| p0.release_wait | no / no | no / no / no | 0 / 0 | r0 0 ± 0; r1 0 ± 0 |', 'Whole request (spread baseline / candidate 0.00 ms / 0.00 ms): improves n/a / no; worsens n/a / no / no; r0 0.00 ms; r1 0.00 ms.', '| p0.release_to_ack | 6.0 | 6.0 | 0.0 | yes |',
                   'Candidate faster in 0, slower in 0, equal in 2 pairs.', '| grace_timeouts | 0 / 0 | r0 0 -> 0; r1 0 -> 0 |',
                   'Grace waits (key 5), sum over accepted trials: grace_timeouts 0 (max per trial 0)',
                   '| w0.terminal_to_exit_request | no / no | no / no / no |',
                   '| w0.scan_visits_per_pass_activation | withheld | r0 0/0 -> 0/0 (no_passes); r1 0/0 -> 0/0 (no_passes) '
                   '[withheld: 0 established of 2 required pairs; absent, without passes or refused in 2] |',
                   '| w0.scan_zero_visit_passes (sum baseline / candidate 0 / 0) | no verdict | r0 0 -> 0; r1 0 -> 0 |',
                   'w0 inbound_count 0: passes_activation 0 (0)',
                   '| ordinary_sentinel | r0 2, 4.35 ms -> 2, 4.35 ms; r1 2, 4.35 ms -> 2, 4.35 ms |', '## baseline O1 rapid', '## candidate O1 rapid'):
        assert needle in text, needle
    shutil.rmtree(root)
    return ['comparison receipts through the loader: separate app groups, two pairs, the excluded trial unpaired, matched-pair section']


class Reached(Exception):
    """The stager passed both identity checks and reached the source-tree record."""


def stager_identity_controls(out):
    """The stager's identity rules on a constructed candidate app and source tree, stopped before any copy or signature."""
    spec = importlib.util.spec_from_file_location('worker_wait_host_stamps', HOST_STAMPS)
    stamps = importlib.util.module_from_spec(spec); spec.loader.exec_module(stamps)
    base = out / 'constructed-stager'
    shutil.rmtree(base, ignore_errors=True)
    tree = base / 'candidate-tree'
    (tree / 'tests/lib').mkdir(parents=True)
    contract = tree / 'tests/lib/contract.py'
    declared, other = 'ab' * 32, 'cd' * 32
    contract.write_text(f'RUNNER_PROTOCOL = 1\nWORKER_IDENTITY = "{declared}"\n')
    assert stamps.tree_worker_identity(tree) == declared
    for text in ('', f'WORKER_IDENTITY = "{declared}"\nWORKER_IDENTITY = "{other}"\n', f"WORKER_IDENTITY = '{declared}'\n",
                 f'WORKER_IDENTITY = "{declared[:-1]}"\n'):
        contract.write_text(text)
        try:
            stamps.tree_worker_identity(tree)
        except AssertionError as error:
            assert 'worker identities' in str(error), error
            continue
        raise AssertionError(f'identity read from {text!r}')
    contract.write_text(f'WORKER_IDENTITY = "{declared}"\n')
    app = base / 'source/PolicyWitness.app'
    (app / stamps.EQUIPMENT).parent.mkdir(parents=True)
    host = base / 'host/PWRunner'
    host.parent.mkdir()
    host.write_bytes(b'constructed host\n')
    host.with_name('host-build.json').write_text(json.dumps(dict(kind='instrumented', output=dict(sha256=hashlib.sha256(b'constructed host\n').hexdigest()))))
    worker = base / 'worker/pw-probe-runner-stamps'
    worker.parent.mkdir()
    def attempt(name, equipment, reported):
        (app / stamps.EQUIPMENT).write_text(json.dumps(dict(worker_identity=equipment)))
        worker.write_text(f'#!/bin/sh\necho "pw-probe-runner abi_identity={reported}"\n'); worker.chmod(0o755)
        try:
            stamps.stage(app, base / name / 'staging/candidate', 'constructed identity', host, worker, worker, True, tree)
        except Reached:
            return 'reached'
        except AssertionError as error:
            return str(error)
        raise AssertionError('stage completed on constructed inputs')
    def reached(tree, receipts):
        raise Reached()
    kept, stamps.tree_commit = stamps.tree_commit, reached
    try:
        refused = attempt('equipment-mismatch', other, declared)
        assert refused.startswith(f'app equipment identity {other} is not') and declared in refused, refused
        refused = attempt('worker-mismatch', declared, other)
        assert f'abi_identity={other}' in refused and f'declared {declared}' in refused, refused
        assert attempt('agreeing', declared, declared) == 'reached'
    finally:
        stamps.tree_commit = kept
    shutil.rmtree(base)
    return ['stager identity read from a tree\'s contract.py text; malformed, missing or duplicated constants refused',
            'candidate stager refuses an app whose equipment identity differs from its tree\'s',
            'candidate stager refuses a stamp worker reporting another identity', 'agreeing identities reach the source-tree record']


def main(out):
    out = Path(out).resolve()
    assert {k: reader.LAYOUT[k] for k in OFFSETS} == OFFSETS, reader.LAYOUT
    assert list(reader.STAGES) == C_STAGES
    rule_controls = order_rule_controls()
    ordinary, actor, neighbor = ordinary_bundle(), actor_bundle(), neighbor_bundle()
    check_ordinary(reader.evaluate_bundle(copy.deepcopy(ordinary), CALIBRATION))
    check_actor_intervals(reader.evaluate_bundle(copy.deepcopy(ordinary), CALIBRATION))
    assert tuple(reader.evaluate_bundle(copy.deepcopy(ordinary), CALIBRATION)[n] for n in reader.GRACE_COUNTS) == (0, 0, 0, 0)
    graced = {grace: reader.evaluate_bundle(ordinary_bundle(grace=grace), CALIBRATION) for grace in GRACE_OUTCOMES}
    for grace, row in graced.items():
        check_grace(row, grace)
    # Group sums over the accepted trials of one group.
    (group,) = reader.summarize([graced['notified'], graced['plain'], graced['unusable']])
    assert {name: (value['sum'], value['n'], value['max']) for name, value in group['grace_counts'].items()} == dict(
        grace_timeouts=(1, 3, 1), grace_notified=(1, 3, 1), grace_unusable=(1, 3, 1), grace_settle_sleeps=(0, 3, 0)), group['grace_counts']
    assert group['components']['w0.grace_wait']['n'] == 3 and group['components']['w0.exit_request_to_reap']['median'] == 90_000
    actor_row = reader.evaluate_bundle(copy.deepcopy(actor), CALIBRATION)
    assert [(a['actor'], a['terminal_to_exit_request']['unobserved'], a['exit_request_to_reap']['unobserved']) for a in actor_row['actors']] == [
        (0, 'terminal_or_exit_request_unobserved', 'exit_request_or_reap_unobserved'),
        (1, 'terminal_or_exit_request_unobserved', 'exit_request_or_reap_unobserved')], actor_row['actors']
    grace_controls = grace_rule_controls()
    check_actor(reader.evaluate_bundle(copy.deepcopy(actor), CALIBRATION))
    check_actor_exits(reader.evaluate_bundle(actor_bundle(exits=True), CALIBRATION), actor_row)
    assert reader.evaluate_bundle(copy.deepcopy(neighbor), CALIBRATION)['status'] == 'accepted'
    check_ordinary_without_new_records(reader.evaluate_bundle(ordinary_bundle(keep=False), CALIBRATION))
    check_actor_without_new_records(reader.evaluate_bundle(actor_bundle(keep=False), CALIBRATION))
    full_ordinary = reader.evaluate_bundle(copy.deepcopy(ordinary), CALIBRATION)
    check_without_sleep_events(reader.evaluate_bundle(ordinary_bundle(sleep_events=False), CALIBRATION), full_ordinary)
    check_without_sleep_events(reader.evaluate_bundle(actor_bundle(sleep_events=False), CALIBRATION),
                               reader.evaluate_bundle(copy.deepcopy(actor), CALIBRATION))
    # Without sleep events, attribution falls back to the registers; a multi-count register retains only its last pair.
    registers_only = lambda: ordinary_bundle(sleep_events=False)
    check_first_check_positive(reader.evaluate_bundle(edited(registers_only, first_check_positive(1)), CALIBRATION), '1', 'single_wait')
    check_first_check_positive(reader.evaluate_bundle(edited(registers_only, first_check_positive(2)), CALIBRATION), '1', 'last_pair_of_multi_count')
    # With sleep events, the exact sleep: the first sentinel sleep (4.31-6.46 ms) contains the arrival at 5.0 ms.
    check_first_check_positive(reader.evaluate_bundle(edited(ordinary_bundle, arrival_negative_free), CALIBRATION), '1', 'event',
                               (0, 2_150_000, SENTINEL_NS, 690_000))
    check_unattributed(reader.evaluate_bundle(edited(lambda: ordinary_bundle(worker_edit=early_arrival), arrival_negative_free), CALIBRATION))
    check_done_first_check_positive(reader.evaluate_bundle(edited(ordinary_bundle, done_negative_free), CALIBRATION))
    check_done_unobserved(reader.evaluate_bundle(edited(ordinary_bundle, done_absent), CALIBRATION))
    check_actor_done(reader.evaluate_bundle(edited(actor_bundle, actor_done_observed), CALIBRATION))
    sleep_controls = sleep_rule_controls()
    check_inversion(reader.evaluate_bundle(edited(ordinary_bundle, late_release_stamp), CALIBRATION))
    uncalibrated = reader.evaluate_bundle(copy.deepcopy(ordinary), None)
    assert uncalibrated['status'] == 'accepted' and uncalibrated['phases'][0]['arrival_detection']['uncertainty_ns'] is None
    assert uncalibrated['phases'][0]['arrival_detection']['uncertainty_basis'] == 'calibration_absent'
    unbounded = reader.evaluate_bundle(copy.deepcopy(ordinary), dict(CALIBRATION, alignment_ns=None))
    assert unbounded['phases'][0]['arrival_detection']['uncertainty_basis'] == 'alignment_unbounded'
    assert unbounded['phases'][0]['serialize']['uncertainty_ns'] == 2 * HOST_FLOOR
    no_term = reader.evaluate_bundle(copy.deepcopy(ordinary), dict(CALIBRATION, endpoint_term_ns=None))
    assert no_term['phases'][0]['serialize']['uncertainty_basis'] == 'calibration_endpoint_term_absent'
    role_unknown = copy.deepcopy(actor)
    page_fault(lambda d: scan_passes(401)(header('flags', 12)(d)), 1)(role_unknown)
    role_row = reader.evaluate_bundle(role_unknown, CALIBRATION)
    assert role_row['status'] == 'accepted' and role_row['worker_waits']['1']['scan']['role_unknown_passes_uncounted'] is True, role_row['problems']
    accepted = ['instrumented O1', 'instrumented A2', 'neighbor O1', 'O1 without pass-count, store-begin, stamp-cost or sleep event records',
                'A2 without pass-count, store-begin, stamp-cost or sleep event records', 'O1 without sleep event records',
                'A2 without sleep event records', 'O1 arrival first check positive inside a single sentinel sleep register',
                'O1 arrival first check positive, containing sleep register spans two waits',
                'O1 arrival first check positive inside a sleep event pair', 'O1 arrival first check positive before any sleep: unattributed',
                'O1 done first check positive inside a sleep event pair', 'O1 done register absent: unobserved label',
                'A2 with a done register for the subject', 'O1 20 us release inversion widening alignment',
                'uncalibrated O1', 'unbounded alignment O1', 'O1 without an endpoint term', 'scan role unknown A2',
                'O1 per-actor exit intervals without grace stamps', 'A2 without exit requests: per-actor intervals unobserved',
                'A2 candidate-shaped cleanup: each actor its own exit intervals, grace stop and one bounded wait'] + [
                f'O1 candidate-shaped grace wait: {grace}' for grace in GRACE_OUTCOMES] + [
                'grace counts summed per group'] + sleep_controls + grace_controls

    # The pre-referee uncertainty arithmetic fails the expected values.
    formula_rejected(old_uncertainty, [(ordinary_bundle, check_ordinary), (actor_bundle, check_actor),
                                       (lambda: edited(ordinary_bundle, late_release_stamp), check_inversion)])
    rejected = [dict(control='old_uncertainty_formula', status='rejected', codes=['expected uncertainty mismatch'])]
    rejected += actor_blind_rejected(actor_row)

    # Disk round trip through the loader, the clock pair's checker and the writers.
    root = out / 'constructed'
    shutil.rmtree(root, ignore_errors=True)
    overlapped = edited(lambda: ordinary_bundle(index=1), watch_inside_held)
    unattributed = edited(lambda: ordinary_bundle(index=2, worker_edit=early_arrival), arrival_negative_free)
    for bundle in (ordinary, overlapped, unattributed, actor, neighbor):
        write_bundle(root, bundle)
    (root / 'schedule.json').write_text(json.dumps(dict(required={'instrumented/O1/rapid': 1, 'instrumented/A2/rapid': 1, 'neighbor/O1/idle': 1})))
    write_identity(root)
    resolution = write_calibration(root)
    decomposition, summary = reader.read_artifacts(root)
    assert summary['calibration_status'] == 'established' and summary['counts']['accepted'] == 4 and summary['counts']['excluded'] == 1, (
        summary['calibration_status'], summary['counts'])
    assert decomposition['version'] == summary['version'] == 8
    calibration = decomposition['calibration']
    term = resolution['readers']['busy']['endpoint_term_ns']
    assert calibration['stamp_ns'] == -(-resolution['stamp_ns'] // 1) and calibration['alignment_ns'] == resolution['alignment']['bound_ns']
    assert calibration['endpoint_term_ns'] == term and summary['endpoint_term_ns'] == term
    assert summary['busy_combined_uncertainty_ns'] == resolution['readers']['busy']['combined_uncertainty_ns'] is not None
    assert all((root / name).exists() for name in ('decomposition.json', 'summary.json', 'summary.md'))
    assert [(g['app'], g['cell'], g['regime'], g['lowpowermode'], g['coverage']) for g in summary['groups']] == [
        ('instrumented', 'A2', 'rapid', '0', 'complete'), ('instrumented', 'O1', 'rapid', '0', 'complete'), ('neighbor', 'O1', 'idle', '0', 'complete')]
    o1 = next(g for g in summary['groups'] if g['cell'] == 'O1' and g['app'] == 'instrumented')
    host_floor = max(term, 2 * 500)
    assert o1['counts']['excluded'] == 1 and o1['non_accepted'][0]['exclusions'] == ['observer_overlap']
    assert o1['components']['p0.serialize'] == dict(n=2, median=30_000, min=30_000, max=30_000, unobserved={}, max_uncertainty_ns=2 * host_floor,
                                                     uncertainty_basis=['calibrated'], detection_bracket=dict(n=0), worker_detection_bracket=dict(n=0),
                                                     pairwise_comparison_uncertainty_ns=4 * host_floor, above_uncertainty_in_every_trial=30_000 > 2 * host_floor,
                                                     below_instrument_floor=2 * int(30_000 <= 2 * host_floor)), o1['components']['p0.serialize']
    # Trial 2's first pass sample is at 4.306 ms rather than 5.002 ms; both accept at 9.255 ms after 3000 passes.
    periods = sorted((9255 - first) * 1000 // 2999 for first in (5002, 4306))
    assert o1['waits']['p0.release_wait'] == dict(passes=dict(n=2, median=3000, min=3000, max=3000), unavailable=0,
                                                  mean_pass_period_ns=dict(n=2, median=sum(periods) / 2, min=periods[0], max=periods[1]),
                                                  period_definition=[reader.SAMPLED_PERIOD]), o1['waits']['p0.release_wait']
    # The split rows keep their own n; the unattributed first check comes from trial 2.
    assert (o1['components']['p0.arrival_detection']['n'], o1['components']['p0.arrival_first_check_positive']['n']) == (1, 1)
    assert o1['components']['p0.arrival_first_check_positive']['during_sleep_key'] == {'unattributed': 1}
    assert o1['components']['w0.done_detection']['n'] == 2 and o1['components']['w0.done_detection']['median'] == 2_000_000
    a2 = next(g for g in summary['groups'] if g['cell'] == 'A2')
    assert a2['components']['p0.arrival_first_check_positive']['n'] == 1 and 'p0.arrival_detection' not in a2['components']
    assert (a2['components']['p0.arrival_first_check_positive']['during_sleep_key'],
            a2['components']['p0.arrival_first_check_positive']['during_sleep_scope']) == ({'none': 1}, {'no_sleep_between': 1})
    assert a2['components']['p3.custody0.inbound_ack_first_check_positive']['during_sleep_key'] == {'6': 1}
    assert a2['components']['p3.custody0.inbound_ack_first_check_positive']['during_sleep_scope'] == {'event': 1}
    assert all(a2['components'][f'p{g}.custody0.recipient_wait']['note'] == reader.RECIPIENT_NOTE for g in (0, 3))
    (t0, tc0), (t3, tc3) = phase_times(0), phase_times(3)
    upper = lambda passes, span_us: dict(passes=dict(n=1, median=passes, min=passes, max=passes), unavailable=0,
                                         mean_pass_period_ns=dict(n=1, median=span_us * 1000 // passes, min=span_us * 1000 // passes,
                                                                  max=span_us * 1000 // passes), period_definition=[reader.UPPER_PERIOD])
    assert {k: v for k, v in a2['waits'].items() if '.exchange_wait.' in k} == {
        'p0.exchange_wait.slot0': upper(ISSUER_PASSES['exchange'][0], 110 - 53), 'p0.exchange_wait.slot1': upper(ISSUER_PASSES['exchange'][1], 1240 - 120),
        'p3.exchange_wait.slot2': upper(ISSUER_PASSES['exchange'][2], 1240 - 53)}, a2['waits']
    assert [(r['index'], r['overlaps_held'], r['status']) for r in summary['observer_overlap'] if r['cell'] == 'O1'] == [
        (0, False, 'accepted'), (1, True, 'excluded'), (2, False, 'accepted')]
    assert [Path(r['dir']).name for r in summary['excluded']] == ['1']
    text = (root / 'summary.md').read_text()
    for needle in ('Not production bytes', summary['reader']['sha256'][:12], 'a1a1a1a1a1a1', 'd4d4d4d4d4d4', 'e5e5e5e5e5e5',
                   'chained or nested, not disjoint', '## Excluded trials', 'O1 rapid 1: overlaps held interval True; excluded',
                   'custody_recipient 1 [scope event 1]', 'lowpowermode 0', f"busy combined uncertainty {summary['busy_combined_uncertainty_ns']} ns",
                   reader.SAMPLED_PERIOD, '| p0.exchange_wait.slot0 |', reader.UPPER_PERIOD, 'unattributed (no containing sleep) 1',
                   'none (no host sleep between) 1', '| w0.done_detection |'):
        assert needle in text, needle
    recipient = [line for line in text.splitlines() if line.startswith('| p0.custody0.recipient_wait (')]
    assert len(recipient) == 1 and reader.RECIPIENT_NOTE in recipient[0] and recipient[0].split(' | ')[2] == 'not reported', recipient
    tampered = out / 'constructed-tampered-calibration'
    shutil.rmtree(tampered, ignore_errors=True); shutil.copytree(root, tampered)
    value = json.loads((tampered / 'clock-pair/calibration.json').read_text()); value['resolution']['read_overhead_ns'] += 1
    (tampered / 'clock-pair/calibration.json').write_text(json.dumps(value))
    rows, plain = reader.read_artifacts(tampered, write=False)
    assert plain['calibration_status'].startswith('not_established') and plain['counts']['accepted'] == 4
    assert next(r for r in rows['rows'] if r['cell'] == 'O1' and r['app'] == 'instrumented')['phases'][0]['serialize']['uncertainty_basis'] == 'calibration_absent'
    shutil.rmtree(tampered)

    # A calibration whose busy endpoint term exceeds the gate: established, not credited, and carried into every endpoint.
    outlier = out / 'constructed-endpoint-outlier'
    shutil.rmtree(outlier, ignore_errors=True); shutil.copytree(root, outlier)
    wide = write_calibration(outlier, clock_pair.constructed_receipt(
        raw_options={('busy', 0): {'store_delay': {2: clock_pair.to_ticks(600_000)}}}))
    rows, plain = reader.read_artifacts(outlier)
    wide_term = wide['readers']['busy']['endpoint_term_ns']
    assert plain['calibration_status'] == 'established' and wide_term > clock_pair.GATE_NS
    assert plain['instrument_gate']['credited'] is False and 'busy_combined_uncertainty_exceeds_gate' in plain['instrument_gate']['reasons']
    wide_row = next(r for r in rows['rows'] if r['cell'] == 'O1' and r['app'] == 'instrumented' and r['index'] == 0)
    assert wide_row['phases'][0]['release_to_ack']['uncertainty_ns'] == 2 * wide_term + wide['alignment']['bound_ns']
    assert 'gate not credited' in (outlier / 'summary.md').read_text()
    rejected.append(dict(control='calibration_endpoint_outlier', status='not_credited', codes=plain['instrument_gate']['reasons']))
    shutil.rmtree(outlier)

    faults = []
    def fault(name, expected, edit, base=ordinary):
        bad = copy.deepcopy(base); edit(bad); faults.append((name, set(expected), bad))
    unchanged = lambda r: None
    fault('bad_magic', {'worker_page_bad_magic'}, page_fault(header('magic', 0x50575754)))
    fault('wrong_version', {'worker_page_wrong_version'}, page_fault(header('version', 2)))
    fault('capture_refused', {'worker_page_capture_refused'}, page_fault(header('flags', 5)))
    fault('event_overflow', {'worker_page_event_overflow'}, page_fault(header('flags', 6)))
    fault('uninitialized_page', {'worker_page_uninitialized'}, page_fault(header('flags', 0)))
    fault('non_monotonic_worker_events', {'worker_events_non_monotonic'}, page_fault(swap_fresh))
    fault('origin_mismatch', {'worker_origin_mismatch'}, page_fault(header('origin', tk(10_000_000 + 1400))))
    fault('scan_histogram_mismatch', {'worker_scan_histogram_mismatch'}, page_fault(scan_passes(401), 1), actor)
    fault('observation_before_publication', {'clock_alignment_violation'}, early_observation)
    fault('truncated_page', {'worker_page_truncated'}, page_fault(lambda data: data[:-16]))
    fault('page_copied_before_reap', {'worker_page_copied_before_reap'}, lambda r: r['stamps']['worker_pages'][0].update(reaped=False))
    fault('capture_requested', {'worker_page_capture_requested'}, lambda r: r['stamps']['worker_pages'][0].update(capture_requested=True))
    fault('page_count_read_mismatch', {'stamp_page_count_mismatch'}, lambda r: r['stamps']['worker_pages'][0].update(event_count_read=3))
    fault('host_dropped_events', {'host_dropped_events'}, lambda r: r['stamps']['dropped'].update(events=2))
    fault('host_dropped_pages', {'host_dropped_worker_pages'}, lambda r: r['stamps']['dropped'].update(worker_pages=1))
    fault('started_marker_not_written', {'started_marker_not_written'}, lambda r: r['stamps']['started_marker'].update(status='directory_missing'))
    fault('sleep_register_malformed', {'host_sleep_register_malformed'}, lambda r: r['stamps']['sleeps']['1'].update(max_ns=None))
    fault('sleep_overlapped', {'sleep_overlapped'}, lambda r: r['conditions'].update(sleep_difference_ns=5_000_000))
    fault('pacing_out_of_range', {'pacing_out_of_range'}, lambda r: r['conditions']['pacing'].update(actual_gap_ns=400_000_000))
    fault('power_transition', {'power_transition'}, lambda r: r['conditions']['power_after'].update(source='AC Power'))
    fault('lowpowermode_transition', {'power_transition'}, lambda r: r['conditions']['power_after'].update(lowpowermode='1'))
    fault('neighbor_with_stamps', {'neighbor_has_stamps'}, lambda r: r.update(stamps=copy.deepcopy(ordinary['stamps'])), neighbor)
    fault('actor_page_count_mismatch', {'stamp_page_count_mismatch'},
          lambda r: next(e for e in r['stamps']['events'] if e[0] == 170).__setitem__(2, 3), actor)
    fault('stamps_for_other_specimen', {'stamps_specimen_mismatch'}, lambda r: r['stamps'].update(specimen_id='other'))
    fault('page_from_other_worker', {'worker_page_pid_mismatch'}, lambda r: r['stamps']['worker_pages'][0].update(pid=1))
    fault('timebase_mismatch', {'worker_timebase_mismatch'}, lambda r: r['stamps'].update(timebase=dict(numer=1, denom=1)))
    fault('eligible_count_mismatch', {'eligible_count_mismatch'}, lambda r: r['trial']['layout']['phases'][0].update(eligible=2))
    def reorder_host(r):
        events = r['stamps']['events']; events[2][3], events[3][3] = events[3][3], events[2][3]
    fault('host_events_non_monotonic', {'host_events_non_monotonic'}, reorder_host)
    def late_custody_start(r):
        next(e for e in r['stamps']['events'] if e[0] == 153 and e[2] == 1)[3] = tk(100_000_000 + phase_times(0)[1] + 1200)
    fault('custody_start_after_pass_end', {'host_events_non_monotonic'}, late_custody_start, actor)
    fault('started_after_spawn', {'started_after_spawn'}, lambda r: r['started'].update(raw=tk(10_000_000 + 2000)))
    fault('started_host_pid_mismatch', {'started_mismatch'}, lambda r: r['started'].update(host_pid=4142))
    fault('exit_watch_other_pid', {'host_exit_pid_mismatch'}, lambda r: r['host_exit']['registration']['generation'].update(pid=1))
    fault('observer_overlap', {'observer_overlap'}, watch_inside_held)
    fault('pass_event_unpaired', {'worker_pass_event_unpaired'}, unchanged,
          ordinary_bundle(worker_edit=lambda ev: [(e, p, a, t + 1) if e == 13 else (e, p, a, t) for e, p, a, t in ev]))
    fault('pass_count_mismatch', {'worker_pass_count_mismatch'}, unchanged,
          ordinary_bundle(worker_edit=lambda ev: [(e, p, a - 1, t) if e == 13 else (e, p, a, t) for e, p, a, t in ev]))
    fault('pass_events_incomplete', {'worker_pass_events_incomplete', 'worker_pass_count_mismatch'}, unchanged,
          actor_bundle(worker_edit=lambda actor, ev: [e for e in ev if not (actor == 1 and e[0] == 13 and e[1] == 1)]))
    fault('exchange_pass_record_missing', {'worker_pass_events_incomplete', 'worker_pass_count_mismatch'}, unchanged,
          actor_bundle(worker_edit=lambda actor, ev: [e for e in ev if not (actor == 0 and e[0] == 15 and e[1] == 1)]))
    fault('store_begin_unpaired', {'host_store_begin_unpaired'}, lambda r: next(e for e in r['stamps']['events'] if e[0] == 139).__setitem__(2, 2))
    fault('store_begin_incomplete', {'host_store_begin_incomplete'}, unchanged,
          actor_bundle(host_edit=lambda events: [e for e in events if not (e[0] == 149 and e[1] == 0)]))
    fault('stamp_cost_malformed', {'host_stamp_cost_malformed'}, lambda r: r['stamps']['stamp_cost']['raws'].reverse())
    fault('register_negatives_inconsistent', {'host_register_malformed'}, lambda r: r['stamps']['registers']['110:0'].update(negatives=0))
    # A sleep register without its last pre read, on a first-check-positive arrival that the reader must attribute.
    fault('sleep_register_pair_missing', {'host_sleep_register_malformed'},
          lambda r: (arrival_negative_free(r), r['stamps']['sleeps']['1'].update(last_pre=None)))
    fault('sleep_end_missing', {'host_sleep_events_unpaired'}, drop_sleep_end)
    fault('sleep_end_without_begin', {'host_sleep_events_unpaired', 'host_sleep_event_count_mismatch'}, drop_sleep_begin)
    fault('sleep_pair_missing', {'host_sleep_event_count_mismatch'}, drop_sleep_pair)
    fault('sleep_requested_mismatch', {'host_sleep_event_requested_mismatch'}, sleep_requested_changed)
    fault('sleep_duration_mismatch', {'host_sleep_event_duration_mismatch'}, sleep_end_later)
    fault('actor_sleep_pair_missing', {'host_sleep_event_count_mismatch'},
          lambda r: (lambda events, begin: events.__delitem__(slice(begin, begin + 2)))(*sleep_pair(r, 4)), actor)
    graced = lambda: ordinary_bundle(grace='notified')
    fault('wait_outcome_aux_3', {'host_wait_outcome_invalid'}, edit_wait_outcome(aux=lambda e: 3), graced())
    fault('wait_outcome_without_pair', {'host_wait_outcome_unpaired'}, move_wait_outcome, graced())
    fault('wait_outcome_other_key', {'host_wait_outcome_unpaired'}, edit_wait_outcome(phase=lambda e: 4), graced())
    fault('wait_outcome_other_raw', {'host_wait_outcome_unpaired'}, edit_wait_outcome(raw=lambda e: e[3] + tk(1)), graced())
    fault('grace_finished_before_begin', {'host_grace_interval_reversed'}, move_grace_finished(11515), graced())
    fault('grace_finished_listed_before_begin', {'host_grace_interval_reversed'}, move_grace_finished(11520), graced())
    fault('combined_magic_and_pacing', {'worker_page_bad_magic', 'pacing_out_of_range'},
          lambda r: (page_fault(header('magic', 0))(r), r['conditions']['pacing'].update(actual_gap_ns=None)))
    fault('combined_alignment_and_sleep', {'clock_alignment_violation', 'sleep_overlapped'},
          lambda r: (early_observation(r), r['conditions'].update(sleep_overlapped=True)))
    rejected += [dict(control=name, status='rejected', codes=[name]) for name in rule_controls[1:]]
    for name, expected, bad in faults:
        row = reader.evaluate_bundle(bad, CALIBRATION)
        assert row['status'] != 'accepted' and codes(row) == expected, (name, row['status'], codes(row))
        rejected.append(dict(control=name, status=row['status'], codes=sorted(codes(row))))

    # Missing files go through the disk loader.
    for name, removed, extra in (('missing_stamps', 'stamps.json', None), ('missing_started', 'started.json', None),
                                 ('combined_missing_stamps_and_sleep', 'stamps.json', 'sleep')):
        copy_root = out / ('fault-' + name)
        shutil.rmtree(copy_root, ignore_errors=True); shutil.copytree(root, copy_root)
        directory = copy_root / 'trials/instrumented/O1/rapid/0'
        (directory / removed).unlink()
        expected = {removed.replace('.json', '') + '_missing'}
        if extra:
            value = json.loads((directory / 'conditions.json').read_text()); value['sleep_difference_ns'] = 9_000_000
            (directory / 'conditions.json').write_text(json.dumps(value)); expected.add('sleep_overlapped')
        rows, _ = reader.read_artifacts(copy_root, write=False)
        row = next(r for r in rows['rows'] if r['cell'] == 'O1' and r['app'] == 'instrumented' and r['index'] == 0)
        assert row['status'] == 'incomplete' and codes(row) == expected, (name, row['status'], codes(row))
        rejected.append(dict(control=name, status=row['status'], codes=sorted(codes(row))))
        shutil.rmtree(copy_root)

    # Aggregation never pools apps, cells, regimes, power sources, low power modes or host flavours.
    base_row = next(r for r in decomposition['rows'] if r['app'] == 'instrumented' and r['cell'] == 'O1' and r['index'] == 0)
    neighbor_row = next(r for r in decomposition['rows'] if r['app'] == 'neighbor')
    variants = dict(regime='idle', cell='O64', power_source='AC Power', lowpowermode='1', flavour=dict(FLAVOUR, swift='-O'))
    mixed = {'neighbor_pooled_with_instrumented': [base_row, neighbor_row]}
    mixed.update({f'{field}_pooled': [base_row, dict(copy.deepcopy(base_row), **{field: value})] for field, value in variants.items()})
    for name, rows in mixed.items():
        assert refused_as_pooled(rows), 'pooled aggregate accepted: ' + name
        rejected.append(dict(control=name, status='refused', codes=['pooled']))
    split = reader.summarize([base_row, dict(copy.deepcopy(base_row), lowpowermode='1')])
    assert [(g['lowpowermode'], g['counts']['accepted']) for g in split] == [('0', 1), ('1', 1)], split
    accepted += comparison_controls(reader.evaluate_bundle(ordinary_bundle(), CALIBRATION))
    rejected.append(spread_ignored_rejected(reader.evaluate_bundle(ordinary_bundle(), CALIBRATION)))
    accepted += scan_controls()
    rejected.append(scan_float_rejected())
    accepted += comparison_round_trip(out)
    accepted += stager_identity_controls(out)
    (out / 'controls.json').write_text(json.dumps(dict(scope='constructed reader sensitivity; no live stamps or timings credited',
        accepted=accepted + rule_controls[:1], rejected=rejected), indent=2) + '\n')
    print(f'{len(rejected)} constructed worker-wait pilot faults rejected after {len(accepted) + 1} constructed receipts accepted')


if __name__ == '__main__':
    main(*sys.argv[1:])
