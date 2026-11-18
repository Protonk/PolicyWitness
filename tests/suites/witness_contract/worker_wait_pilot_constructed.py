"""Constructed worker-wait pilot receipts, the edits that corrupt them and their writers.

Inputs only: nothing here reads a receipt, and importing this module loads
neither the pilot reader nor the clock pair. The pilot controls
(`test_worker_wait_pilot_controls.py`) and the dispatcher's constructed
comparison (`tests/fixtures/dispatcher/pilot_unfavorable.py`) build their
receipts here.

Worker pages are packed with offsets written from the C layout, in program
order, including loaded-record pairs, pass-count records and inbound pass
samples appended after later reads. Host exports carry each sleep as a 180/181
event pair beside its register and a done register for the ordinary worker. A
candidate-shaped ordinary receipt adds the worker grace program points and one
bounded exit wait whose pair is followed by its outcome event; a
candidate-shaped A2 receipt gives each actor its own exit request, reap, grace
program points, bounded exit wait and grace stop. An A2 receipt takes
constructed inbound scan counters for either actor's page. Times are whole
constructed microseconds.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct

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


def write_bundle(root, bundle):
    t = bundle['trial']
    directory = root / 'trials' / t['app'] / t['cell'] / t['regime'] / str(t['index'])
    directory.mkdir(parents=True)
    for key, name in (('trial', 'trial.json'), ('conditions', 'conditions.json'), ('started', 'started.json'), ('stamps', 'stamps.json'),
                      ('host_exit', 'host-exit.json'), ('validation', 'validation.json')):
        if bundle[key] is not None:
            (directory / name).write_text(json.dumps(bundle[key]) + '\n')
    return directory


def write_calibration(clock_pair, root, calibration=None):
    """The clock pair's own constructed receipt, with its raw cell outputs on disk.

    clock_pair is the clock-pair module; the caller passes it so that this module imports no reader."""
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
