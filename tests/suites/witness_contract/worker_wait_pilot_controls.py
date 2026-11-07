"""Constructed worker-wait pilot receipts: accepted first, then each fault rejected.

Establishes the reader's decoding, arithmetic and refusal rules on constructed
inputs only; no stamp, timing or live trial is credited here. Worker pages are
packed with offsets written from the C layout, in program order, including
loaded-record pairs, pass-count records and inbound pass samples appended after
later reads. Host exports carry each sleep as a 180/181 event pair beside its
register and a done register for the ordinary worker. Expected values are
written from the constructed microsecond times, not computed with the reader's
functions.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import worker_wait_pilot_reader as reader
import worker_wait_clock_pair as clock_pair

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


def ordinary_bundle(keep=True, worker_edit=None, index=0, sleep_events=True):
    """O1: one phase, one eligible query. Times are microseconds from a 10 s base.
    Sentinel pass 1 (4000-4300) observes application and samples arrival and done negative; sleep 1
    (4310-6460) contains the worker's arrival; pass 2 observes arrival and runs the hook; pass 3 after
    release samples acknowledgement and done negative; sleep 2 (9270-11470) contains TERMINAL_PUBLISHED;
    pass 4 observes both. keep=False drops the records the dry-run-04 receipts lack;
    sleep_events=False drops the 180/181 pairs the dry-run-05 receipts lack."""
    b = 10_000_000
    host = [(100, NONE, 0, 0), (101, 0, 4242, 1000), (102, 0, 0, 3000), (103, 0, 2, 4000),
            (180, 1, SENTINEL_NS, 4310), (181, 1, SENTINEL_NS, 6460), (110, 0, 1, 6500), (111, 0, 0, 6510),
            (112, 0, 0, 6520), (120, 0, 0, 6530), (121, 0, 1, 6600), (122, 0, 0, 6610), (123, 0, 120, 6640), (124, 0, 0, 6660),
            (125, 0, 0, 6670), (126, 0, 7777, 7670), (127, 0, 0, 7680), (128, 0, 0, 7690), (129, 0, 0, 9000), (130, 0, 0, 9100),
            (131, 0, 0, 9110), (132, 0, 1, 9150), (133, 0, 0, 9160), (134, 0, 0, 9170), (135, 0, 1, 9180), (140, 0, 0, 9200),
            (139, 0, 1, 9248), (141, 0, 1, 9250), (180, 1, SENTINEL_NS, 9270), (181, 1, SENTINEL_NS, 11470),
            (142, 0, 1, 11500), (144, 0, 3, 11500), (146, 0, 0, 11510), (147, 0, 0, 11600),
            (170, 0, 0, 11700), (171, NONE, 0, 60000)]
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
                        sleeps(**{'1': (2, SENTINEL_NS, 4_350_000, 2_200_000, 2_150_000, tk(b + 9270), tk(b + 11470))}),
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


def actor_bundle(keep=True, worker_edit=None, host_edit=None, sleep_events=True):
    """A2 lifecycle in program order. Phase g activates at 20 ms + 10 ms * g (microseconds from a 100 s base).
    An execution sleep (1048 us) lies between each bracketed arrival's negative and positive samples, and a
    recipient sleep (980 us) inside each transfer wait."""
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
    scan = {0: {}, 1: dict(passes_activation=400, visits_activation=500, loads_activation=520, histogram={0: 300, 1: 80, 2: 20})}
    origins = {0: 1500, 1: 1600}
    workers = {0: current(issuer, keep), 1: current(subject, keep)}
    if worker_edit:
        workers = {a: worker_edit(a, events) for a, events in workers.items()}
    packed = {a: pack_page([(e, p, x, tk(b + t)) for e, p, x, t in events], stages=stages[a].items(), scan=scan[a], pid=5000 + a,
                           origin=tk(b + origins[a])) for a, events in workers.items()}
    end = phase_times(4)[1] + 2000
    host += [(161, NONE, 0, end + 1000), (147, 0, 0, end + 1100), (147, 1, 0, end + 1110),
             (170, 0, len(workers[0]), end + 1200), (170, 1, len(workers[1]), end + 1201), (171, NONE, 0, end + 50000)]
    host = current(host, keep, sleep_events)
    if host_edit: host = host_edit(host)
    sid = 'A2-rapid-0-constructed'
    stamps = stamps_doc(sid, 5555, b, host, registers,
                        sleeps(**{'3': (4, ACTOR_POLL_NS, 4_192_000, 1_048_000, 1_048_000, tk(b + t4 + 51), tk(b + t4 + 1099)),
                                  '6': (2, ACTOR_POLL_NS, 1_960_000, 980_000, 980_000, tk(b + tc3 + 166), tk(b + tc3 + 1146))}),
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


def main(out):
    out = Path(out).resolve()
    assert {k: reader.LAYOUT[k] for k in OFFSETS} == OFFSETS, reader.LAYOUT
    assert list(reader.STAGES) == C_STAGES
    rule_controls = order_rule_controls()
    ordinary, actor, neighbor = ordinary_bundle(), actor_bundle(), neighbor_bundle()
    check_ordinary(reader.evaluate_bundle(copy.deepcopy(ordinary), CALIBRATION))
    check_actor(reader.evaluate_bundle(copy.deepcopy(actor), CALIBRATION))
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
                'uncalibrated O1', 'unbounded alignment O1', 'O1 without an endpoint term', 'scan role unknown A2'] + sleep_controls

    # The pre-referee uncertainty arithmetic fails the expected values.
    formula_rejected(old_uncertainty, [(ordinary_bundle, check_ordinary), (actor_bundle, check_actor),
                                       (lambda: edited(ordinary_bundle, late_release_stamp), check_inversion)])
    rejected = [dict(control='old_uncertainty_formula', status='rejected', codes=['expected uncertainty mismatch'])]

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
    assert decomposition['version'] == summary['version'] == 3
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
    (out / 'controls.json').write_text(json.dumps(dict(scope='constructed reader sensitivity; no live stamps or timings credited',
        accepted=accepted + rule_controls[:1], rejected=rejected), indent=2) + '\n')
    print(f'{len(rejected)} constructed worker-wait pilot faults rejected after {len(accepted) + 1} constructed receipts accepted')


if __name__ == '__main__':
    main(*sys.argv[1:])
