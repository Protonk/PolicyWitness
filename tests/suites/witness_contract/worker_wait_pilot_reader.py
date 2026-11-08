"""Worker-wait pilot reader: host and worker continuous-clock stamps per trial.

Reads the receipts check_worker_wait_pilot.py writes under <artifacts>/trials
and writes decomposition.json (one row per trial), summary.json (aggregates
per app, cell, regime, power source, low power mode and host flavour, and the
matched pairs of a comparison run) and summary.md. Every check appends a
named problem, so combined faults stay visible. Refused, incomplete, failed,
skipped and excluded trials stay in decomposition.json and are left out of
aggregates and pairs.

Interpretation rules, repeated in summary.json:
- Stamps are mach_continuous_time ticks. Each stamp converts to ns as
  floor(ticks * numer / denom), the footprint observer's conversion.
- A post-operation stamp is read after its store or load. A worker pass sample
  is read before the load it governs; loaded events carry that sample.
- A publication's endpoint bracket runs from the latest-read stamp the same
  process appended before it to its post-store stamp: for a worker arrival the
  same visit's ACTIVATION_STORED, APPLIED or the previous phase's last stamp;
  for a host release RELEASE_STORE_BEGIN, else the hook or collection end; for
  a host activation ACTIVATION_STORE_BEGIN, else the preceding event. A worker
  completion store has no stamp of its own: the next wait's first pass sample
  or TERMINAL_PUBLISHED follows it. A program-point stamp has no bracket.
- A polled host observation is located by its first positive sample. With an
  earlier negative sample the component keeps its name (arrival_detection,
  ack_observation, completion_detection, done_detection,
  inbound_ack_to_host_observed) and the negative-to-positive detection bracket
  is polling response under measurement, reported beside the latency and not
  counted as uncertainty. When the first check was already positive the
  component is *_first_check_positive: its latency includes whatever the host
  did before that check, and during_sleep_key names the host sleep containing
  the worker stamp. The two are never pooled.
- Sleep attribution takes the exact sleep from the HOST_SLEEP_BEGIN/END pairs
  (180/181, the first 64 sleeps of each key; scope event). Otherwise it uses a
  register's last pre/post pair: single_wait, last_pair_of_multi_count, or
  events_truncated for a key past 64 sleeps. With no containing sleep the
  scope is no_sleep_between when the host recorded no sleep between the
  publication and its observation, and unattributed otherwise.
- done_detection runs from the worker's TERMINAL_PUBLISHED to the host's first
  positive sample of the done flag (register 144, keyed by actor index). The
  ordinary host polls that flag; an actor-form trial reports it only for an
  actor whose 144 register exists, and its last visit's completion row
  otherwise ends at the same TERMINAL_PUBLISHED stamp.
- A release or activation wait's mean pass period is (accepting pass sample -
  first pass sample) / (passes - 1). An exchange wait has no first-pass stamp:
  its period is an upper bound, (answer - the preceding stamp) / passes.
- A custody recipient_wait is a host interval from TRANSFER_WAIT_START to
  TRANSFER_WAIT_END, not a detection, and bimodal by recipient state; the
  inbound acknowledgement rows split it into first-check-positive and detected
  cases. The summary shows its extremes only.
- Each endpoint term is that endpoint's bracket floored at the clock pair's
  busy-reader endpoint term and, for host endpoints, at twice the in-situ host
  stamp cost median. Uncertainty = both endpoint terms +, across processes,
  the alignment bound, from a clock-pair receipt that worker_wait_clock_pair
  accepts; without one it is not established. A value at or below its
  uncertainty is below_instrument_floor.
- Across processes a post-store stamp can follow the other side's observation
  stamp; such inversions are counted and widen the alignment term rather than
  being treated as clock faults. An inversion larger than ALIGNMENT_REFUSAL_NS
  refuses the trial.
- Components are chained or nested, not disjoint (spawn_to_* share the spawn
  end, eof_to_reap overlaps eof_to_decode and decode, held_total contains the
  release and acknowledgement components); never add them.
- Per actor, w<actor>.terminal_to_exit_request runs from the worker's
  TERMINAL_PUBLISHED to the host's EXIT_REQUESTED (146), w<actor>.exit_request_to_reap
  from 146 to the host's reaping sample WORKER_REAPED (147), and w<actor>.grace_wait
  from WORKER_GRACE_BEGIN (148) to WORKER_GRACE_FINISHED (157), with grace_stop_code
  157's aux (0 exhausted, 1 reaped, 2 wait_error). All are program-point intervals:
  each endpoint term is its floor, plus the alignment bound across processes. The
  worker's exit itself has no stamp. A trial whose 157 precedes its 148 is refused.
- Per trial, grace_timeouts, grace_notified and grace_unusable count how the worker
  grace waits between samples (sleep key 5) ended: a key-5 pair followed by
  WAIT_OUTCOME (182, phase = key, raw = the pair's end) is counted by its aux (0 timed
  out, 1 notified, 2 unusable); a key-5 pair without one is a plain sleep: requested
  at most 100 µs it is a settle sleep after a notification (grace_settle_sleeps),
  longer it is the timer poll and counts as a timeout, and so does every key-5
  wait past the 64 recorded pairs. grace_wait_record keeps that breakdown, with
  the plain sleeps by requested ns. A 182 whose aux is not 0, 1 or 2, or that does not immediately follow a
  181 of the same key and raw, refuses the trial.
- A trial whose driver exit-watch registration overlapped a held interval is
  excluded (observer_overlap) and kept as a diagnostic.
- A comparison run (schedule.json comparison) pairs a baseline and a candidate
  trial with the same cell, regime and repetition index when both are accepted
  under the same power source, low power mode and host flavour; any other
  trial is listed as unpaired. Per pair and component the difference is
  baseline minus candidate and its instrument uncertainty the sum of both
  sides'. A split observation is compared under one *_to_observation name,
  publication to the host's first positive sample, with each side's form kept.
  Worker release and activation passes are exact counts; whole request has no
  instrument uncertainty and only spread verdicts, and its direction counts the
  pairs where the candidate was faster (positive difference), slower or equal.
  The grace counts are paired as exact per-pair differences with each side's
  sum over the pairs, without verdicts. A side's spread of a
  quantity is max - min over its accepted trials in the group.
  improves_beyond_uncertainty_in_every_pair compares each difference with the
  instrument uncertainty; improves_beyond_spread_in_every_pair requires it to
  exceed the candidate's spread plus that uncertainty. Each is false once any
  established pair falls short and true only when all of the declared
  pairs_required pass. worsens_beyond_instrument_uncertainty and
  worsens_beyond_spread_in_any_pair (candidate minus baseline beyond the
  baseline's spread plus the instrument uncertainty) are true once any pair
  is worse and false only when all required pairs are established and none
  is; otherwise a verdict is withheld. For release_to_ack, activation_response
  and the custody rows' inbound_response (the host's transfer wait start,
  right after it commits the delivery, to the recipient's acknowledgement
  publication) the response bound is the candidate's largest accepted value
  minus the baseline's smallest, against 2 ms; it is credited only with their
  combined uncertainty at most 0.5 ms and the instrument gate credited. The
  two apps are never pooled.
- Per actor, scan carries the worker's inbound scan counters (passes, visits
  and loads per caller role, and zero_visit_passes, histogram bucket 0, over
  both roles) beside inbound_count, the deliveries the trial layout addresses
  to that actor, one inbound slot each, and the slots the page's
  INBOUND_ACKNOWLEDGED events name. inbound_observed is true when those events
  name each layout slot exactly once.
- A scan that visits from index 0 visits all n inbound slots on every pass
  except one that ends on acknowledging slot i, which visits i + 1, and
  acknowledges each slot once; each visit makes at least one load. Over P
  passes in one role it therefore makes at least n * P - n * (n - 1) / 2
  visits and as many loads: the full-scan floor. For such a scan visits per
  pass are n - n * (n - 1) / (2 * P) whenever every acknowledgement falls in
  that role, so a per-pass ratio alone follows the pass count and is lower
  for whichever side made fewer passes.
- A comparison pairs the counters as exact counts:
  w<actor>.scan_visits_per_pass_<role> and w<actor>.scan_loads_per_pass_<role>
  (role activation or exchange), with no uncertainty. A pair is lower when the
  baseline's count is at or above its full-scan floor, the candidate's is
  below its own, and the candidate's count / passes is strictly below the
  baseline's by integer cross-multiplication; a not_lower pair names the
  conditions it failed. A pair is no_passes when either side made no pass in
  that role, and refused when the actor's inbound_count differs between the
  sides (scan_inbound_count_mismatch) or either side's inbound_observed is
  false (scan_inbound_acknowledgement_mismatch); a refused pair names every
  problem it has. lower_in_every_pair is false once any established pair is
  not lower and true only when all of at least pairs_required pairs are
  established and lower; otherwise it is withheld.
  w<actor>.scan_zero_visit_passes is reported per side with each side's sum
  over the pairs, without a verdict. Groups carry each counter's sum and
  median per actor.
"""
import base64
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import sys

READER_VERSION = 9
HERE = Path(__file__).resolve().parent

# Worker stamp page; mirrors tests/fixtures/worker_wait/pww_stamp_page.h.
PAGE_OFFSET = 3293184
PAGE_BYTES = 32768
PAGE_MAGIC = 0x50575753
PAGE_VERSION = 1
EVENT_CAPACITY = 1000
STAGE_COUNT = 10
FLAG_CAPTURE_REFUSED, FLAG_EVENT_OVERFLOW, FLAG_INITIALIZED, FLAG_SCAN_ROLE_UNKNOWN = 1, 2, 4, 8
HEADER = struct.Struct('<IIIIQIIII')
STAGE = struct.Struct('<QQQ')
SCAN = struct.Struct('<71Q')
EVENT = struct.Struct('<IIIIQ')
LAYOUT = dict(header=0, header_size=HEADER.size, stages=HEADER.size, stage_size=STAGE.size,
              scan=HEADER.size + STAGE_COUNT * STAGE.size, scan_size=SCAN.size,
              events=HEADER.size + STAGE_COUNT * STAGE.size + SCAN.size, event_size=EVENT.size)
LAYOUT['size'] = LAYOUT['events'] + EVENT_CAPACITY * EVENT.size
assert LAYOUT['size'] <= PAGE_BYTES and LAYOUT['events'] % 8 == 0

STAGES = ('worker_start', 'proceed_start', 'proceed_observe', 'exec_admit', 'exec_observe', 'exec_reap',
          'activate_start', 'activate_observe', 'exchange_start', 'exchange_observe')
WORKER_EVENTS = {1: 'worker_start', 2: 'applied', 3: 'proceed_arrived', 4: 'proceed_ordinal_loaded',
                 5: 'proceed_acknowledged', 6: 'activation_loaded', 7: 'activation_stored',
                 8: 'exchange_answered', 9: 'inbound_observed', 10: 'inbound_acknowledged',
                 11: 'attempt_published', 12: 'terminal_published', 13: 'proceed_passes',
                 14: 'activation_passes', 15: 'exchange_passes'}
W = {name: code for code, name in WORKER_EVENTS.items()}
# Events whose raw is an earlier pass sample or the origin rather than a read at append.
WORKER_SAMPLED = {1, 4, 6, 9}
# Pass-count records follow their parent event with its phase and raw.
PASS_PARENTS = {13: 5, 14: 7, 15: 8}
HOST_EVENTS = {100: 'request_start', 101: 'worker_spawned', 102: 'ready_observed', 103: 'applied_observed',
               110: 'arrival_observed', 111: 'premature_check_done', 112: 'hook_mark',
               120: 'planning_start', 121: 'planning_end', 122: 'serialize_start', 123: 'serialize_end',
               124: 'pipes_ready', 125: 'spawn_start', 126: 'spawn_end', 127: 'first_write',
               128: 'stdin_closed', 129: 'first_read', 130: 'stdout_eof', 131: 'decode_start',
               132: 'decode_end', 133: 'grace_start', 134: 'validator_reaped', 135: 'grace_end',
               136: 'validator_terminate', 139: 'release_store_begin', 140: 'hook_end', 141: 'release_stored',
               142: 'ack_observed', 143: 'completion_observed', 144: 'done_observed', 145: 'death_check',
               146: 'exit_requested', 147: 'worker_reaped', 148: 'worker_grace_begin', 149: 'activation_store_begin',
               150: 'activation_stored', 151: 'collection_start', 152: 'collection_end', 153: 'custody_service_start',
               154: 'custody_service_end', 155: 'transfer_wait_start', 156: 'transfer_wait_end',
               157: 'worker_grace_finished', 160: 'setup_done', 161: 'schedule_done',
               170: 'stamp_page_copied', 171: 'flush_begin', 180: 'host_sleep_begin', 181: 'host_sleep_end',
               182: 'wait_outcome'}
H = {name: code for code, name in HOST_EVENTS.items()}
# Host events appended with a raw the caller read earlier (spawn return, custody pass start, sleep pre read).
HOST_PRESAMPLED = {101, 153, 180}
# Each host sleep appends 180 (raw = pre read) and 181 (raw = post read), phase = key, aux = requested ns,
# for the first 64 sleeps of its key; later sleeps update only the registers.
SLEEP_BEGIN, SLEEP_END, SLEEP_EVENTS_PER_KEY = 180, 181, 64
# A bounded exit wait's pair is followed by 182 (phase = key, aux = outcome, raw = the pair's end raw).
WAIT_OUTCOME = 182
WAIT_OUTCOMES = {0: 'timed_out', 1: 'notified', 2: 'unusable'}
GRACE_KEY = '5'
GRACE_COUNTS = ('grace_timeouts', 'grace_notified', 'grace_unusable', 'grace_settle_sleeps')
# A plain key-5 sleep requested at most this long is the settle sleep that follows a notification.
GRACE_SETTLE_NS = 100_000
SAMPLED_PERIOD = '(accepting pass sample - first pass sample) / (passes - 1)'
UPPER_PERIOD = 'upper bound: preceding stamp to answer / passes'
RECIPIENT_NOTE = 'host interval, not a detection; bimodal by recipient state; see the split sibling rows'
# A record read immediately before a host store, paired with the record after it.
STORE_BEGIN = {139: 141, 149: 150}
DROPPED_KINDS = ('events', 'register_samples', 'sleeps', 'custody_passes', 'worker_pages')
SLEEP_KEYS = {'0': 'ready_byte_wait', '1': 'ordinary_sentinel', '2': 'actor_setup', '3': 'actor_execution',
              '4': 'validator_grace', '5': 'worker_grace', '6': 'custody_recipient', '7': 'termination_gate'}
ALIGNMENT_REFUSAL_NS = 50_000
PAIR_APPS = ('baseline', 'candidate')
PAIRS_REQUIRED = 5
# Split observations compared under one name: publication to the host's first positive sample, either form.
OBSERVATION_FORMS = {'arrival_detection': 'arrival_to_observation', 'arrival_first_check_positive': 'arrival_to_observation',
                     'ack_observation': 'ack_to_observation', 'ack_first_check_positive': 'ack_to_observation',
                     'completion_detection': 'completion_to_observation',
                     'completion_first_check_positive': 'completion_to_observation',
                     'done_detection': 'done_to_observation', 'done_first_check_positive': 'done_to_observation',
                     'inbound_ack_to_host_observed': 'inbound_ack_to_observation',
                     'inbound_ack_first_check_positive': 'inbound_ack_to_observation'}
PAIRED_WAITS = ('release_wait', 'activation_wait')
RESPONSE_COMPONENTS = ('release_to_ack', 'activation_response', 'inbound_response')
RESPONSE_LIMIT_NS, RESPONSE_UNCERTAINTY_GATE_NS = 2_000_000, 500_000
# Inbound scan counters per actor; the paired ratios are count / passes of one caller role.
SCAN_ROLES, SCAN_MEASURES = ('activation', 'exchange'), ('visits', 'loads')
SCAN_COUNTERS = tuple(f'{kind}_{role}' for role in SCAN_ROLES for kind in ('passes',) + SCAN_MEASURES) + ('zero_visit_passes',)
SCAN_LOWER = 'lower_in_every_pair'
SCAN_REFUSAL = 'scan_inbound_count_mismatch'
SCAN_ACK_REFUSAL = 'scan_inbound_acknowledgement_mismatch'
SCAN_INBOUND_SOURCE = ('trial layout: deliveries addressed to the actor, one inbound slot each; checked against the slots '
                       "the actor's INBOUND_ACKNOWLEDGED events name")
# Conditions of a lower scan pair; a not_lower pair names the ones it failed.
SCAN_UNMET = ('baseline_below_full_scan_floor', 'candidate_not_below_full_scan_floor', 'ratio_not_lower')
STATUS_ORDER = ('failed', 'skipped', 'incomplete', 'refused', 'excluded', 'accepted')
EXCLUSIONS = {'sleep_overlapped', 'pacing_out_of_range', 'power_transition', 'power_unobserved', 'observer_overlap'}
INCOMPLETE = {'stamps_missing', 'started_missing', 'validation_missing', 'conditions_missing',
              'conditions_malformed', 'host_exit_missing', 'worker_page_missing'}
STAGED_HOST = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner'
STAGED_WORKER = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
UNOBSERVED = {
    'per_pass_host_sleeps': 'The first 64 sleeps of each host sleep key are 180/181 event pairs; later sleeps of that key leave only the registers (count, sums, extremes and the last pre/post pair). Receipts without sleep events attribute through the registers alone.',
    'actor_done_observation': 'An actor-form trial reports done_detection only for an actor whose host 144 register exists; otherwise the host observation nearest the worker\'s end is the last visit\'s completion row, which ends at the same TERMINAL_PUBLISHED stamp.',
    'per_wait_worker_passes': 'Per-wait pass counts come from the PROCEED/ACTIVATION/EXCHANGE_PASSES records; receipts without them report per-wait passes as unavailable. An exchange wait has no first-pass stamp, so its period is an upper bound from the preceding stamp.',
    'host_observation_within_pass': 'A host poll reads the clock once, after its load; where in that pass the value became visible is covered only by the host endpoint floor.',
    'validator_internal': 'The validator process carries no stamps; spawn-to-first-read and EOF include its run time.',
    'ordinary_completion_publication': 'The ordinary host never waits for completion and no worker completion stamp exists.',
    'actor_completion_instant': 'The worker completion store has no stamp of its own; the next wait\'s first pass sample or TERMINAL_PUBLISHED follows it and the visit\'s last stamp precedes it.',
    'inbound_commit_instant': 'The host has no commit stamp; custody pass and transfer-wait stamps bracket it.',
    'inbound_observation_instant': 'INBOUND_OBSERVED carries the pass sample that precedes the observation, not a read at it.',
    'kernel_exit_times': 'Exit watches report kqueue collection brackets, not kernel exit times.',
    'worker_exit_instant': 'The worker\'s exit has no stamp: exit_request_to_reap ends at the host\'s reaping sample (147), which follows the exit by up to the wait between grace samples.',
    'neighbor_internal_intervals': 'The uninstrumented neighbor has no stamps; only whole-request latency and envelope millisecond fields exist.',
}


def ns(ticks, timebase):
    return ticks * timebase[0] // timebase[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- worker page ------------------------------------------------------------

def worker_order_problems(events, origin):
    """Fresh reads must not go backwards; a pass sample must precede the next fresh read."""
    problems = set()
    fresh = [e for e in events if e['event'] not in WORKER_SAMPLED]
    if any(b['raw'] < a['raw'] for a, b in zip(fresh, fresh[1:])):
        problems.add('worker_events_non_monotonic')
    for index, e in enumerate(events):
        if e['event'] in WORKER_SAMPLED:
            later = next((f for f in events[index + 1:] if f['event'] not in WORKER_SAMPLED), None)
            if later is not None and e['raw'] > later['raw']:
                problems.add('worker_events_non_monotonic')
    for code in WORKER_SAMPLED:
        same = [e['raw'] for e in events if e['event'] == code]
        if any(b < a for a, b in zip(same, same[1:])):
            problems.add('worker_events_non_monotonic')
    if any(e['raw'] < origin for e in events):
        problems.add('worker_event_before_origin')
    if any(e['event'] == W['worker_start'] and e['raw'] != origin for e in events):
        problems.add('worker_origin_mismatch')
    return problems


def pass_event_problems(events, stages):
    """Pass-count records follow their parents; once present, every parent has one and the sums meet the stage registers."""
    if not any(e['event'] in PASS_PARENTS for e in events):
        return set()
    problems = set()
    for index, e in enumerate(events):
        if e['event'] in PASS_PARENTS:
            parent = events[index - 1] if index else None
            if (parent is None or parent['event'] != PASS_PARENTS[e['event']] or parent['phase'] != e['phase']
                    or parent['raw'] != e['raw']):
                problems.add('worker_pass_event_unpaired')
        elif e['event'] in PASS_PARENTS.values():
            follower = events[index + 1] if index + 1 < len(events) else None
            if follower is None or PASS_PARENTS.get(follower['event']) != e['event']:
                problems.add('worker_pass_events_incomplete')
    for code, start, observe in ((13, 'proceed_start', 'proceed_observe'), (14, 'activate_start', 'activate_observe')):
        counts = [e['aux'] for e in events if e['event'] == code]
        if len(counts) != stages[start]['count'] or sum(counts) != stages[observe]['count'] or 0 in counts:
            problems.add('worker_pass_count_mismatch')
    # An exchange answered on its first load counts one pass without an observe sample.
    counts, observed = [e['aux'] for e in events if e['event'] == 15], stages['exchange_observe']['count']
    if len(counts) != stages['exchange_start']['count'] or not observed <= sum(counts) <= observed + len(counts) or 0 in counts:
        problems.add('worker_pass_count_mismatch')
    return problems


def decode_page(data):
    """(page, problems). A page with header problems is not interpreted further."""
    if len(data) < PAGE_BYTES:
        return None, ['worker_page_truncated']
    if len(data) > PAGE_BYTES:
        return None, ['worker_page_oversized']
    magic, version, numer, denom, origin, flags, pid, count, _ = HEADER.unpack_from(data, 0)
    if magic != PAGE_MAGIC:
        return None, ['worker_page_bad_magic']
    if version != PAGE_VERSION:
        return None, ['worker_page_wrong_version']
    problems = []
    if flags & FLAG_CAPTURE_REFUSED: problems.append('worker_page_capture_refused')
    if flags & FLAG_EVENT_OVERFLOW: problems.append('worker_page_event_overflow')
    if not flags & FLAG_INITIALIZED: problems.append('worker_page_uninitialized')
    if flags & ~(FLAG_CAPTURE_REFUSED | FLAG_EVENT_OVERFLOW | FLAG_INITIALIZED | FLAG_SCAN_ROLE_UNKNOWN):
        problems.append('worker_page_unknown_flags')
    if count > EVENT_CAPACITY: problems.append('worker_page_event_count_invalid')
    if not numer or not denom: problems.append('worker_timebase_invalid')
    if problems:
        return None, problems
    stages = {}
    for index, name in enumerate(STAGES):
        c, first_raw, last_raw = STAGE.unpack_from(data, LAYOUT['stages'] + index * STAGE.size)
        stages[name] = dict(count=c, first_raw=first_raw, last_raw=last_raw)
        if c and not origin <= first_raw <= last_raw:
            problems.append('worker_stage_register_invalid')
    values = SCAN.unpack_from(data, LAYOUT['scan'])
    scan = dict(passes_activation=values[0], passes_exchange=values[1], visits_activation=values[2],
                visits_exchange=values[3], loads_activation=values[4], loads_exchange=values[5],
                visits_histogram={str(i): v for i, v in enumerate(values[6:]) if v},
                role_unknown_passes_uncounted=bool(flags & FLAG_SCAN_ROLE_UNKNOWN))
    if not flags & FLAG_SCAN_ROLE_UNKNOWN and sum(values[6:]) != values[0] + values[1]:
        problems.append('worker_scan_histogram_mismatch')
    events = []
    for index in range(count):
        event, phase, aux, _, raw = EVENT.unpack_from(data, LAYOUT['events'] + index * EVENT.size)
        events.append(dict(event=event, name=WORKER_EVENTS.get(event), phase=phase, aux=aux, raw=raw))
    if any(e['name'] is None for e in events): problems.append('worker_event_unknown')
    problems.extend(worker_order_problems(events, origin))
    problems.extend(pass_event_problems(events, stages))
    page = dict(magic=magic, version=version, timebase=[numer, denom], origin_raw=origin, flags=flags, pid=pid,
                event_count=count, stages=stages, scan=scan, events=events)
    return page, sorted(set(problems))


def records(page):
    return [(e['event'], e['phase'], e['aux'], e['raw']) for e in page['events']]


# ---- host export --------------------------------------------------------------

def _int(value):
    return type(value) is int and value >= 0


def check_stamps(doc, trial):
    problems = []
    keys = {'version', 'host_pid', 'specimen_id', 'timebase', 'flavour', 'events', 'registers', 'sleeps', 'worker_pages', 'dropped'}
    if not isinstance(doc, dict) or not keys <= set(doc):
        return ['stamps_malformed']
    if doc['version'] != 1: problems.append('stamps_wrong_version')
    if doc['specimen_id'] != trial['specimen_id']: problems.append('stamps_specimen_mismatch')
    tb = doc['timebase']
    if not (isinstance(tb, dict) and _int(tb.get('numer')) and _int(tb.get('denom')) and tb['numer'] and tb['denom']):
        return problems + ['stamps_timebase_invalid']
    events = doc['events']
    if not isinstance(events, list) or not all(isinstance(e, list) and len(e) == 4 and all(map(_int, e)) for e in events):
        return problems + ['host_events_malformed']
    if any(e[0] not in HOST_EVENTS for e in events): problems.append('host_event_unknown')
    ordered = [e for e in events if e[0] not in HOST_PRESAMPLED]
    if any(b[3] < a[3] for a, b in zip(ordered, ordered[1:])): problems.append('host_events_non_monotonic')
    for index, e in enumerate(events):
        if e[0] in HOST_PRESAMPLED:
            later = next((f for f in events[index + 1:] if f[0] not in HOST_PRESAMPLED), None)
            if later is not None and e[3] > later[3]: problems.append('host_events_non_monotonic')
        if e[0] in STORE_BEGIN:
            following = events[index + 1] if index + 1 < len(events) else None
            if following is None or following[0] != STORE_BEGIN[e[0]] or following[1:3] != e[1:3]:
                problems.append('host_store_begin_unpaired')
    for begin, stored in STORE_BEGIN.items():
        if any(e[0] == begin for e in events) and any(
                e[0] == stored and (not index or events[index - 1][0] != begin) for index, e in enumerate(events)):
            problems.append('host_store_begin_incomplete')
    problems.extend(wait_outcome_problems(events))
    if 'stamp_cost' in doc:
        raws = doc['stamp_cost'].get('raws') if isinstance(doc['stamp_cost'], dict) else None
        if not isinstance(raws, list) or not all(map(_int, raws)) or any(b < a for a, b in zip(raws, raws[1:])):
            problems.append('host_stamp_cost_malformed')
    if not any(e[0] == H['request_start'] for e in events): problems.append('host_request_start_missing')
    dropped = doc['dropped'] if isinstance(doc['dropped'], dict) else {}
    problems += [f'host_dropped_{kind}' for kind in DROPPED_KINDS if dropped.get(kind) != 0]
    if (doc.get('started_marker') or {}).get('status') != 'written': problems.append('started_marker_not_written')
    if doc.get('page_within_capture') is not True: problems.append('host_page_outside_capture')
    for key, value in (doc['registers'] or {}).items():
        if not isinstance(value, dict): problems.append('host_register_malformed'); continue
        negative, positive = value.get('last_negative') or None, value.get('first_positive') or None
        if negative is not None and positive is not None and negative >= positive:
            problems.append('host_register_order')
        if 'negatives' in value and (not _int(value['negatives']) or (value['negatives'] == 0) != (negative is None)):
            problems.append('host_register_malformed')
    malformed = set()
    for key, value in (doc['sleeps'] or {}).items():
        observed = isinstance(value, dict) and _int(value.get('count')) and value['count'] > 0
        if (key not in SLEEP_KEYS or not isinstance(value, dict)
                or not all(_int(value.get(k)) for k in ('count', 'sum_ns', 'requested_sum_ns'))
                or (observed and not all(_int(value.get(k)) for k in ('max_ns', 'last_pre', 'last_post', 'min_ticks')))):
            problems.append('host_sleep_register_malformed'); malformed.add(key)
    problems.extend(sleep_event_problems(doc, malformed))
    expected_pages = len(trial['layout']['actors']) if trial.get('form') == 'actor' else 1
    if len(doc['worker_pages']) != expected_pages:
        problems.append('worker_page_missing')
    for entry in doc['worker_pages']:
        if entry.get('reaped') is not True: problems.append('worker_page_copied_before_reap')
        if entry.get('capture_requested') is not False: problems.append('worker_page_capture_requested')
    return sorted(set(problems))


def wait_outcome_problems(events):
    """A WAIT_OUTCOME carries 0, 1 or 2 and immediately follows its key's 181 with the same raw; a grace's 157
    follows its 148."""
    problems = set()
    for index, e in enumerate(events):
        if e[0] != WAIT_OUTCOME:
            continue
        if e[2] not in WAIT_OUTCOMES:
            problems.add('host_wait_outcome_invalid')
        end = events[index - 1] if index else None
        if end is None or end[0] != SLEEP_END or end[1] != e[1] or end[3] != e[3]:
            problems.add('host_wait_outcome_unpaired')
    for phase in sorted({e[1] for e in events if e[0] in (H['worker_grace_begin'], H['worker_grace_finished'])}):
        begin = index_of(events, H['worker_grace_begin'], phase=phase)
        finished = index_of(events, H['worker_grace_finished'], phase=phase)
        if begin is not None and finished is not None and (finished < begin or events[finished][3] < events[begin][3]):
            problems.add('host_grace_interval_reversed')
    return problems


def index_of(events, code, *, phase=None, aux=None, after=None, before=None):
    for index, e in enumerate(events):
        if e[0] != code: continue
        if phase is not None and e[1] != phase: continue
        if aux is not None and e[2] != aux: continue
        if after is not None and e[3] < after: continue
        if before is not None and e[3] >= before: continue
        return index
    return None


def first(events, code, **match):
    index = index_of(events, code, **match)
    return None if index is None else events[index]


def sleep_record(events):
    """Host sleep event pairs per key: a 180 immediately followed by its 181 with the same key and requested ns."""
    begins, pairs, unpaired = {}, {}, set()
    for index, e in enumerate(events):
        if e[0] == SLEEP_BEGIN:
            begins.setdefault(str(e[1]), []).append(e[2])
            end = events[index + 1] if index + 1 < len(events) else None
            if end is None or end[0] != SLEEP_END or list(end[1:3]) != list(e[1:3]) or end[3] < e[3]:
                unpaired.add(str(e[1]))
            else:
                pairs.setdefault(str(e[1]), []).append(dict(begin=e[3], end=end[3], requested_ns=e[2]))
        elif e[0] == SLEEP_END:
            begin = events[index - 1] if index else None
            if begin is None or begin[0] != SLEEP_BEGIN or list(begin[1:3]) != list(e[1:3]) or e[3] < begin[3]:
                unpaired.add(str(e[1]))
    return dict(present=any(e[0] in (SLEEP_BEGIN, SLEEP_END) for e in events), begins=begins, pairs=pairs, unpaired=unpaired)


EMPTY_SLEEP_RECORD = dict(present=False, begins={}, pairs={}, unpaired=set())


def sleep_event_problems(doc, malformed=()):
    """Once any sleep event is present, each key's begin records match its register: all of them while the
    key has at most 64 sleeps, a prefix of 64 beyond that. Counts are compared first; requested and
    duration sums only where the counts agree, and durations only over complete pairs."""
    record = sleep_record(doc['events'])
    if not record['present']:
        return set()
    problems = {'host_sleep_events_unpaired'} if record['unpaired'] else set()
    registers = doc['sleeps'] or {}
    if set(record['begins']) - set(registers):
        problems.add('host_sleep_event_count_mismatch')
    for key, value in registers.items():
        if key in malformed or not isinstance(value, dict):
            continue
        count, begins = value['count'], record['begins'].get(key, [])
        complete = count <= SLEEP_EVENTS_PER_KEY
        if len(begins) != min(count, SLEEP_EVENTS_PER_KEY):
            problems.add('host_sleep_event_count_mismatch'); continue
        if (sum(begins) != value['requested_sum_ns']) if complete else (sum(begins) > value['requested_sum_ns']):
            problems.add('host_sleep_event_requested_mismatch')
        pairs = record['pairs'].get(key, [])
        if key in record['unpaired'] or len(pairs) != len(begins):
            continue
        ticks = sum(p['end'] - p['begin'] for p in pairs)
        if _int(value.get('sum_ticks')) and ((ticks != value['sum_ticks']) if complete else (ticks > value['sum_ticks'])):
            problems.add('host_sleep_event_duration_mismatch')
        if complete and count and (pairs[-1]['begin'], pairs[-1]['end']) != (value['last_pre'], value['last_post']):
            problems.add('host_sleep_event_duration_mismatch')
    return problems


def sleep_event_state(doc, record):
    if not record['present']:
        return dict(state='absent', attribution='sleep registers only')
    truncated = sorted(key for key, value in (doc['sleeps'] or {}).items()
                       if isinstance(value, dict) and _int(value.get('count')) and value['count'] > SLEEP_EVENTS_PER_KEY)
    return dict(state='truncated' if truncated else 'complete', truncated_keys=truncated,
                pairs={key: len(value) for key, value in sorted(record['pairs'].items())})


def grace_counts(doc):
    """How the trial's worker grace waits (sleep key 5) ended: each recorded pair by the 182 that follows it, a
    pair without one as a plain sleep (a settle sleep when requested at most GRACE_SETTLE_NS, else a timeout), and
    every wait past the recorded pairs as a timeout."""
    register = (doc['sleeps'] or {}).get(GRACE_KEY) or dict(count=0)
    if not isinstance(register, dict) or not _int(register.get('count')):
        return None
    events, outcomes, plain, recorded = doc['events'], {code: 0 for code in WAIT_OUTCOMES}, {}, 0
    for index, e in enumerate(events):
        if e[0] != SLEEP_END or str(e[1]) != GRACE_KEY:
            continue
        recorded += 1
        follower = events[index + 1] if index + 1 < len(events) else None
        if follower is not None and follower[0] == WAIT_OUTCOME and follower[1] == e[1] and follower[2] in WAIT_OUTCOMES:
            outcomes[follower[2]] += 1
        else:
            plain[str(e[2])] = plain.get(str(e[2]), 0) + 1
    unrecorded = max(0, register['count'] - recorded)
    settle = sum(n for requested, n in plain.items() if int(requested) <= GRACE_SETTLE_NS)
    return dict(grace_timeouts=outcomes[0] + sum(plain.values()) - settle + unrecorded, grace_notified=outcomes[1],
                grace_unusable=outcomes[2], grace_settle_sleeps=settle,
                grace_wait_record=dict(waits=register['count'], recorded_pairs=recorded,
                                       outcome_events={WAIT_OUTCOMES[code]: n for code, n in outcomes.items()},
                                       plain_sleeps=sum(plain.values()), plain_sleeps_by_requested_ns=dict(sorted(plain.items())),
                                       settle_sleeps=settle, unrecorded=unrecorded))


def actor_intervals(doc, pages, interval):
    """Per actor: the worker's terminal publication to the host's exit request, that request to the host's reaping
    sample, and the grace wait between its program points (148, 157), all program-point intervals."""
    events, rows = doc['events'], []
    for actor in sorted(pages):
        terminal = first(records(pages[actor]), W['terminal_published'])
        at = lambda name: (lambda e: point(e and e[3], 'host', name))(first(events, H[name], phase=actor))
        finished = first(events, H['worker_grace_finished'], phase=actor)
        rows.append(dict(actor=actor,
                         terminal_to_exit_request=interval(point(terminal and terminal[3], f'worker{actor}', 'terminal_published'),
                                                           at('exit_requested'), missing='terminal_or_exit_request_unobserved'),
                         exit_request_to_reap=interval(at('exit_requested'), at('worker_reaped'), missing='exit_request_or_reap_unobserved'),
                         grace_wait=interval(at('worker_grace_begin'), at('worker_grace_finished'), missing='grace_not_stamped'),
                         grace_stop_code=finished and finished[2]))
    return rows


def host_stamp_cost(doc, tb):
    """Per-record cost of the host's own record path, from its request-start burst."""
    if 'stamp_cost' not in doc:
        return dict(median_ns=None, unobserved='stamp_cost absent from this export')
    raws = doc['stamp_cost']['raws']
    if len(raws) < 2:
        return dict(median_ns=None, unobserved='stamp_cost burst not recorded')
    costs = sorted(ns(b - a, tb) for a, b in zip(raws, raws[1:]))
    return dict(records=len(raws), min_ns=costs[0], median_ns=statistics.median(costs), max_ns=costs[-1],
                mean_ns=ns(raws[-1] - raws[0], tb) / (len(raws) - 1))


# ---- endpoints and intervals ----------------------------------------------------

def point(raw, process, stamp):
    """A program-point stamp: it has no bracket of its own."""
    return None if raw is None else dict(raw=raw, process=process, stamp=stamp, bracket_ns=0, bracket_from=None)


def preceding(events, index):
    """The latest-read record appended before index; pass-count records only repeat their parent's raw."""
    return max((e for e in reversed(events[:index]) if e[0] not in PASS_PARENTS), key=lambda e: e[3], default=None)


def published(events, index, process, names, tb, *, stamp=None, begin=None):
    """A post-store stamp bracketed back to the latest-read stamp appended before it by the same process."""
    if index is None:
        return None
    lower = preceding(events, index)
    raw = events[index][3]
    endpoint = dict(raw=raw, process=process, stamp=stamp or names[events[index][0]], lower_raw=lower and lower[3],
                    bracket_ns=None if lower is None else ns(raw, tb) - ns(lower[3], tb),
                    bracket_from=lower and names.get(lower[0], str(lower[0])))
    if begin is not None and (lower is None or lower[0] != begin):
        endpoint['fallback'] = names[begin] + '_absent'
    return endpoint


def raw_of(endpoint):
    return endpoint and endpoint['raw']


class Interval:
    """Interval records between endpoints, with explicit unobserved labels and uncertainty bases."""

    def __init__(self, timebase, calibration, host_cost_ns=None, inversion_ns=0, sleeps=None):
        self.tb, self.calibration, self.host_cost_ns, self.inversion_ns = timebase, calibration, host_cost_ns, inversion_ns
        # The trial's host sleep event pairs, for attributing first-check-positive observations.
        self.sleeps = sleeps or EMPTY_SLEEP_RECORD

    def __call__(self, start, end, *, missing='endpoint_unobserved', detection=None, worker_detection=None, **labels):
        if start is None or end is None:
            return dict(ns=None, unobserved=missing)
        record = dict(ns=ns(end['raw'], self.tb) - ns(start['raw'], self.tb), cross_process=start['process'] != end['process'])
        brackets = (start['bracket_ns'], end['bracket_ns'])
        record['bracket_ns'] = None if None in brackets else sum(brackets)
        record['endpoints'] = [{k: e[k] for k in ('process', 'stamp', 'bracket_from', 'bracket_ns')} for e in (start, end)]
        if detection is not None: record['detection_bracket_ns'] = detection
        if worker_detection is not None: record['worker_detection_bracket_ns'] = worker_detection
        record.update(self.uncertainty(start, end))
        if record['uncertainty_ns'] is not None:
            record['below_instrument_floor'] = record['ns'] <= record['uncertainty_ns']
        record.update(labels)
        return record

    def uncertainty(self, start, end):
        """Both endpoint terms, each its bracket floored per process, plus alignment across processes."""
        cal, cross = self.calibration, start['process'] != end['process']
        if start['bracket_ns'] is None or end['bracket_ns'] is None:
            return dict(uncertainty_ns=None, uncertainty_basis='bracket_unobserved')
        if cal is None:
            return dict(uncertainty_ns=None, uncertainty_basis='calibration_absent')
        if cal.get('endpoint_term_ns') is None:
            return dict(uncertainty_ns=None, uncertainty_basis='calibration_endpoint_term_absent')
        if cross and cal['alignment_ns'] is None:
            return dict(uncertainty_ns=None, uncertainty_basis='alignment_unbounded')
        labels, terms = set(), []
        for e in (start, end):
            floor = cal['endpoint_term_ns']
            if e['process'] == 'host':
                if self.host_cost_ns is None:
                    labels.add('host_stamp_cost_absent')
                else:
                    floor = max(floor, math.ceil(2 * self.host_cost_ns))
            if e.get('fallback'):
                labels.add(e['fallback'])
            terms.append(max(e['bracket_ns'], floor))
        alignment = 0
        if cross:
            alignment = max(cal['alignment_ns'], self.inversion_ns)
            if self.inversion_ns > cal['alignment_ns']:
                labels.add('alignment_widened_by_inversion')
        return dict(endpoint_terms_ns=terms, alignment_ns=alignment, uncertainty_ns=sum(terms) + alignment,
                    uncertainty_basis='calibrated' + (' (' + ', '.join(sorted(labels)) + ')' if labels else ''))

    def width(self, low, high):
        return None if low is None or high is None else ns(high, self.tb) - ns(low, self.tb)


def register_pair(value):
    return isinstance(value, dict) and _int(value.get('count')) and _int(value.get('last_pre')) and _int(value.get('last_post'))


def sleep_attribution(doc, record, raw, until):
    """The host sleep containing a worker stamp: an exact 180/181 pair first, else a register's last pair
    (single-wait registers before multi-count ones); without one, whether any host sleep lay between."""
    out = dict(during_sleep_key=None, during_sleep=None, during_sleep_scope=None)
    if raw is None:
        return out
    tb = (doc['timebase']['numer'], doc['timebase']['denom'])
    def found(key, scope, ordinal, begin, end, requested):
        return dict(during_sleep_key=key, during_sleep=SLEEP_KEYS.get(key), during_sleep_scope=scope,
                    during_sleep_span=dict(ordinal=ordinal, duration_ns=ns(end, tb) - ns(begin, tb), requested_ns=requested,
                                           stamp_after_begin_ns=ns(raw, tb) - ns(begin, tb)))
    for key in sorted(record['pairs']):
        for ordinal, pair in enumerate(record['pairs'][key]):
            if pair['begin'] <= raw <= pair['end']:
                return found(key, 'event', ordinal, pair['begin'], pair['end'], pair['requested_ns'])
    # Registers that slept; a malformed one (already a named problem) never attributes and never establishes 'none'.
    registers = sorted((key, value) for key, value in (doc['sleeps'] or {}).items()
                       if not isinstance(value, dict) or not _int(value.get('count')) or value['count'] > 0)
    for single in (True, False):
        for key, value in registers:
            if not register_pair(value):
                continue
            count, recorded = value['count'], len(record['pairs'].get(key, []))
            # A key whose every sleep is an event pair was searched above.
            if (count == 1) != single or recorded >= count or not value['last_pre'] <= raw <= value['last_post']:
                continue
            scope = ('events_truncated' if recorded and count > SLEEP_EVENTS_PER_KEY
                     else 'single_wait' if single else 'last_pair_of_multi_count')
            return found(key, scope, count - 1, value['last_pre'], value['last_post'], value.get('last_requested_ns'))
    out['during_sleep_scope'] = 'no_sleep_between' if no_sleep_between(record, registers, raw, until) else 'unattributed'
    return out


def no_sleep_between(record, registers, raw, until):
    """True only when every host sleep is known to lie outside (raw, until): each recorded pair, and for
    sleeps without a pair (past 64 per key, or receipts without sleep events), the register's last pair."""
    for key, value in registers:
        if not register_pair(value):
            return False
        pairs = record['pairs'].get(key, [])
        if any(pair['begin'] < until and pair['end'] > raw for pair in pairs):
            return False
        unrecorded = value['count'] - len(pairs)
        if unrecorded <= 0 or value['last_post'] <= raw:
            continue
        # Unrecorded sleeps of a key follow its recorded ones and end with the register's last pair.
        start = value['last_pre'] if unrecorded == 1 else pairs[-1]['end'] if pairs else None
        if start is None or start < until:
            return False
    return True


def polled(row, doc, interval, code, key, publication, names):
    """Adds one polled host observation of a worker publication, split by whether a negative sample preceded it."""
    value = (doc['registers'] or {}).get(f'{code}:{key}') or {}
    negative, positive = value.get('last_negative') or None, value.get('first_positive') or None
    if positive is None:
        row[names[0]] = dict(ns=None, unobserved='poll_register_absent')
        return None
    observation = point(positive, 'host', HOST_EVENTS[code])
    if negative is not None:
        row[names[0]] = interval(publication, observation, detection=interval.width(negative, positive))
    else:
        row[names[1]] = interval(publication, observation,
                                 **sleep_attribution(doc, interval.sleeps, raw_of(publication), positive))
    return positive


def loaded_samples(ev, code, visit, ordinal):
    """(accepting pass sample, the pass sample before it or None, the wait's first pass sample)."""
    matching = [e for e in ev if e[0] == code and e[1] == visit]
    for index, e in enumerate(matching):
        if e[2] == ordinal:
            previous = matching[index - 1] if index and matching[index - 1][2] != ordinal else None
            return e[3], previous and previous[3], matching[0][3]
    return None, None, None


def wait_passes(ev, parent, code, first_sample, accepting, tb):
    """Passes in one wait from the pass-count record after its parent, and the mean period between its first and accepting samples."""
    if parent is None or parent + 1 >= len(ev) or ev[parent + 1][0] != code:
        return dict(passes=None, unobserved='per-wait pass record absent')
    passes = ev[parent + 1][2]
    span = None if first_sample is None or accepting is None else ns(accepting, tb) - ns(first_sample, tb)
    return dict(passes=passes, sampled_span_ns=span,
                mean_pass_period_ns=span // (passes - 1) if span is not None and passes >= 2 else None)


def exchange_wait(ev, index, tb):
    """One exchange wait: passes from its pass-count record; it has no first-pass stamp, so its mean pass
    period is an upper bound from the preceding stamp to the answer."""
    passes = wait_passes(ev, index, 15, None, None, tb)['passes']
    lower = preceding(ev, index)
    span = None if lower is None else ns(ev[index][3], tb) - ns(lower[3], tb)
    return dict(slot=ev[index][1], passes=passes, span_upper_ns=span, span_from=lower and WORKER_EVENTS.get(lower[0]),
                upper_mean_pass_period_ns=span // passes if span is not None and passes else None)


def per_wait(page):
    """Each wait's passes from the pass-count records; None when the page has none."""
    ev, tb = records(page), tuple(page['timebase'])
    if not any(e[0] in PASS_PARENTS for e in ev):
        return None
    out = dict(release=[], activation=[], exchange=[])
    for index, e in enumerate(ev):
        if e[0] == W['proceed_acknowledged']:
            accepting, _, start = loaded_samples(ev, W['proceed_ordinal_loaded'], e[1], e[2])
            out['release'].append(dict(visit=e[1], **wait_passes(ev, index, 13, start, accepting, tb)))
        elif e[0] == W['activation_stored']:
            accepting, _, start = loaded_samples(ev, W['activation_loaded'], e[1], e[2])
            out['activation'].append(dict(visit=e[1], **wait_passes(ev, index, 14, start, accepting, tb)))
        elif e[0] == W['exchange_answered']:
            out['exchange'].append(exchange_wait(ev, index, tb))
    return out


def worker_wait_registers(page):
    out = {}
    for wait, start, observe in (('release', 'proceed_start', 'proceed_observe'),
                                 ('activation', 'activate_start', 'activate_observe'),
                                 ('exchange', 'exchange_start', 'exchange_observe')):
        waits, reg = page['stages'][start]['count'], page['stages'][observe]
        row = dict(waits=waits, passes=reg['count'])
        if waits == 1 and reg['count'] >= 2:
            row['mean_pass_period_ns'] = (ns(reg['last_raw'], page['timebase']) - ns(reg['first_raw'], page['timebase'])) // (reg['count'] - 1)
        else:
            row['mean_pass_period_ns'] = None
            row['unobserved'] = 'no wait' if waits == 0 else 'fewer than two passes' if waits == 1 else f'registers span {waits} waits'
        out[wait] = row
    scan = page['scan']
    out['scan'] = dict(scan, visits_per_pass_activation=(scan['visits_activation'] / scan['passes_activation'] if scan['passes_activation'] else None),
                       visits_per_pass_exchange=(scan['visits_exchange'] / scan['passes_exchange'] if scan['passes_exchange'] else None))
    waits = per_wait(page)
    out['per_wait'] = waits if waits is not None else dict(unavailable='no pass-count records on this page')
    return out


def worker_phase(page, actor, visit, ordinal):
    """Worker endpoints for one local visit (the phase index in the ordinary form)."""
    ev, tb, process = records(page), tuple(page['timebase']), f'worker{actor}'
    acked = index_of(ev, W['proceed_acknowledged'], phase=visit, aux=ordinal)
    loaded, previous, start = loaded_samples(ev, W['proceed_ordinal_loaded'], visit, ordinal)
    return dict(arrived=published(ev, index_of(ev, W['proceed_arrived'], phase=visit), process, WORKER_EVENTS, tb),
                acknowledged=published(ev, acked, process, WORKER_EVENTS, tb), acknowledged_index=acked,
                ordinal_sample=point(loaded, process, 'proceed_ordinal_loaded'),
                worker_detection_bracket_ns=None if previous is None or loaded is None else ns(loaded, tb) - ns(previous, tb),
                release_wait=wait_passes(ev, acked, 13, start, loaded, tb))


def completion_index(ev, acked):
    """The record that follows a visit's completion store: the next wait's first pass sample or TERMINAL_PUBLISHED."""
    if acked is None:
        return None
    visit = ev[acked][1]
    for index in range(acked + 1, len(ev)):
        e = ev[index]
        if (e[0] == W['activation_loaded'] and e[1] != visit) or e[0] == W['terminal_published']:
            return index
    return None


def completion_endpoint(page, actor, acked):
    ev = records(page)
    index = completion_index(ev, acked)
    return None if index is None else published(ev, index, f'worker{actor}', WORKER_EVENTS, tuple(page['timebase']))


def done_rows(doc, pages, interval, pairs, actors):
    """The host's observation of each listed worker's done flag (register 144 keyed by actor index) after its
    TERMINAL_PUBLISHED stamp, split like every polled observation."""
    rows = []
    for actor in actors:
        ev = records(pages[actor])
        terminal = published(ev, index_of(ev, W['terminal_published']), f'worker{actor}', WORKER_EVENTS, tuple(pages[actor]['timebase']))
        row = dict(actor=actor)
        observed = polled(row, doc, interval, H['done_observed'], actor, terminal, ('done_detection', 'done_first_check_positive'))
        inversion(pairs, f'w{actor}:done', raw_of(terminal), observed)
        rows.append(row)
    return rows


def inversion(pairs, name, publication, observation):
    if publication is None or observation is None:
        return
    pairs.append(dict(pair=name, publication_raw=publication, observation_raw=observation,
                      inverted_ticks=max(0, publication - observation)))


def ordinary_phases(doc, page, trial, interval, pairs):
    events, tb = doc['events'], interval.tb
    phases = []
    for p, expected in enumerate(trial['layout']['phases']):
        w = worker_phase(page, 0, p, p + 1)
        start = first(events, H['planning_start'], phase=p)
        hook_end = first(events, H['hook_end'], phase=p)
        lo = start and start[3]; hi = hook_end and hook_end[3]
        row = dict(phase=p, expected_eligible=expected['eligible'])
        mark = first(events, H['hook_mark'], phase=p)
        planning_end = first(events, H['planning_end'], phase=p)
        row['eligible_planned'] = planning_end[2] if planning_end else None
        release = published(events, index_of(events, H['release_stored'], phase=p), 'host', HOST_EVENTS, tb,
                            begin=H['release_store_begin'])
        row.update(collection_components(events, interval, lo, hi, planning_end, 'hook_end'))
        observed = polled(row, doc, interval, H['arrival_observed'], p, w['arrived'],
                          ('arrival_detection', 'arrival_first_check_positive'))
        row['arrival_bookkeeping'] = interval(point(observed, 'host', 'arrival_observed'), point(mark and mark[3], 'host', 'hook_mark'))
        row['collection'] = interval(point(mark and mark[3], 'host', 'hook_mark'), point(hi, 'host', 'hook_end'))
        row['closure_to_release'] = interval(point(hi, 'host', 'hook_end'), release)
        row['release_to_ordinal_sample'] = interval(release, w['ordinal_sample'])
        row['release_to_ack'] = interval(release, w['acknowledged'], worker_detection=w['worker_detection_bracket_ns'])
        ack_observed = polled(row, doc, interval, H['ack_observed'], p, w['acknowledged'],
                              ('ack_observation', 'ack_first_check_positive'))
        row['held_total'] = interval(w['arrived'], w['acknowledged'])
        row['release_wait'] = w['release_wait']
        inversion(pairs, f'p{p}:arrival', raw_of(w['arrived']), observed)
        inversion(pairs, f'p{p}:release', raw_of(release), raw_of(w['acknowledged']))
        inversion(pairs, f'p{p}:ack', raw_of(w['acknowledged']), ack_observed)
        row['held_interval_ns'] = ([ns(w['arrived']['raw'], tb), ns(w['acknowledged']['raw'], tb)]
                                   if w['arrived'] and w['acknowledged'] else None)
        phases.append(row)
    return phases


def collection_components(events, interval, lo, hi, planning_end, hi_name):
    """Validator path stamps between a phase's planning start and its collection end."""
    if lo is None or hi is None:
        return dict(planning=dict(ns=None, unobserved='collection_bounds_unobserved'))
    def at(name):
        e = first(events, H[name], after=lo, before=hi + 1)
        return point(e and e[3], 'host', name)
    planned = point(planning_end and planning_end[3], 'host', 'planning_end')
    planning = interval(point(lo, 'host', 'planning_start'), planned)
    if planning_end and planning_end[2] == 0:
        return dict(planning=planning, validator='not_needed')
    serialize_end = first(events, H['serialize_end'], after=lo, before=hi + 1)
    decode_end = first(events, H['decode_end'], after=lo, before=hi + 1)
    grace_end = first(events, H['grace_end'], after=lo, before=hi + 1)
    return dict(
        planning=planning,
        planning_to_serialize=interval(planned, at('serialize_start')),
        serialize=interval(at('serialize_start'), at('serialize_end')),
        pipes=interval(at('serialize_end'), at('pipes_ready')),
        spawn=interval(at('spawn_start'), at('spawn_end')),
        spawn_to_first_write=interval(at('spawn_end'), at('first_write')),
        spawn_to_stdin_closed=interval(at('spawn_end'), at('stdin_closed')),
        spawn_to_first_read=interval(at('spawn_end'), at('first_read')),
        spawn_to_eof=interval(at('spawn_end'), at('stdout_eof')),
        eof_to_decode=interval(at('stdout_eof'), at('decode_start')),
        decode=interval(at('decode_start'), at('decode_end')),
        eof_to_reap=interval(at('stdout_eof'), at('validator_reaped'), missing='reap_unobserved'),
        grace=interval(at('grace_start'), at('grace_end')),
        grace_to_collection_end=interval(at('grace_end'), point(hi, 'host', hi_name)),
        validator_terminate_called=at('validator_terminate') is not None,
        payload_bytes=serialize_end and serialize_end[2], decoded_verdicts=decode_end and decode_end[2],
        grace_stop_code=grace_end and grace_end[2])


def actor_phases(doc, pages, trial, interval, pairs):
    events, tb = doc['events'], interval.tb
    layout = trial['layout']
    activations = [index_of(events, H['activation_stored'], aux=g + 1) for g in range(len(layout['phases']))]
    bounds = [None if i is None else events[i][3] for i in activations]
    phases = []
    for g, entry in enumerate(layout['phases']):
        actor, visit = entry['actor'], entry['visit']
        page = pages.get(actor)
        lo = bounds[g]; hi = next((b for b in bounds[g + 1:] if b is not None), None)
        row = dict(phase=g, actor=actor, visit=visit, expected_eligible=entry['eligible'])
        if page is None or lo is None:
            row['unobserved'] = 'worker_page_or_activation_missing'
            phases.append(row); continue
        process, ev = f'worker{actor}', records(page)
        w = worker_phase(page, actor, visit, visit + 1)
        a_loaded, a_previous, a_start = loaded_samples(ev, W['activation_loaded'], visit, g + 1)
        stored_index = index_of(ev, W['activation_stored'], phase=visit, aux=g + 1)
        a_stored = published(ev, stored_index, process, WORKER_EVENTS, tb)
        activation = published(events, activations[g], 'host', HOST_EVENTS, tb, begin=H['activation_store_begin'])
        seg = lambda name: first(events, H[name], after=lo, before=hi)
        cstart, cend = seg('collection_start'), seg('collection_end')
        planning_start, planning_end = seg('planning_start'), seg('planning_end')
        release = published(events, index_of(events, H['release_stored'], after=lo, before=hi), 'host', HOST_EVENTS, tb,
                            begin=H['release_store_begin'])
        row['eligible_planned'] = planning_end[2] if planning_end else None
        row['activation_sample'] = interval(activation, point(a_loaded, process, 'activation_loaded'))
        row['activation_response'] = interval(activation, a_stored, worker_detection=interval.width(a_previous, a_loaded))
        row['activation_to_arrival'] = interval(a_stored, w['arrived'])
        positive = polled(row, doc, interval, H['arrival_observed'], g, w['arrived'],
                          ('arrival_detection', 'arrival_first_check_positive'))
        if cstart and cend:
            row.update(collection_components(events, interval, planning_start and planning_start[3], cend[3], planning_end, 'collection_end'))
        row['collection'] = interval(point(cstart and cstart[3], 'host', 'collection_start'), point(cend and cend[3], 'host', 'collection_end'))
        row['closure_to_release'] = interval(point(cend and cend[3], 'host', 'collection_end'), release)
        row['release_to_ordinal_sample'] = interval(release, w['ordinal_sample'])
        row['release_to_ack'] = interval(release, w['acknowledged'], worker_detection=w['worker_detection_bracket_ns'])
        ack_positive = polled(row, doc, interval, H['ack_observed'], g, w['acknowledged'],
                              ('ack_observation', 'ack_first_check_positive'))
        completion = completion_endpoint(page, actor, w['acknowledged_index'])
        completed = polled(row, doc, interval, H['completion_observed'], g, completion,
                           ('completion_detection', 'completion_first_check_positive'))
        # Exchange waits between this visit's acknowledgement and its completion, keyed by slot.
        acked, end = w['acknowledged_index'], completion_index(ev, w['acknowledged_index'])
        row['exchange_waits'] = ([] if acked is None else
                                 [exchange_wait(ev, i, tuple(page['timebase'])) for i in range(acked + 1, len(ev) if end is None else end)
                                  if ev[i][0] == W['exchange_answered']])
        row['held_total'] = interval(w['arrived'], w['acknowledged'])
        row['held_interval_ns'] = ([ns(w['arrived']['raw'], tb), ns(w['acknowledged']['raw'], tb)]
                                   if w['arrived'] and w['acknowledged'] else None)
        row['activation_wait'] = wait_passes(ev, stored_index, 14, a_start, a_loaded, tb)
        row['release_wait'] = w['release_wait']
        inversion(pairs, f'g{g}:activation', lo, raw_of(a_stored))
        inversion(pairs, f'g{g}:arrival', raw_of(w['arrived']), positive)
        inversion(pairs, f'g{g}:release', raw_of(release), raw_of(w['acknowledged']))
        inversion(pairs, f'g{g}:ack', raw_of(w['acknowledged']), ack_positive)
        # The completion stamp follows the store; the stamp before it must precede the observation.
        inversion(pairs, f'g{g}:completion', completion and completion['lower_raw'], completed)
        row['custody'] = custody(doc, pages, layout, interval, lo, hi, pairs, g)
        phases.append(row)
    return phases


def custody(doc, pages, layout, interval, lo, hi, pairs, g):
    """Transfers serviced in this phase, associated with recipient slots in delivery order."""
    events, tb = doc['events'], interval.tb
    rows = []
    starts = [e for e in events if e[0] == H['transfer_wait_start'] and lo <= e[3] < (hi if hi is not None else float('inf'))]
    for start in starts:
        delivery = start[2]
        end = first(events, H['transfer_wait_end'], after=start[3])
        target = next((d for d in layout.get('deliveries', []) if d['delivery'] == delivery), None)
        row = dict(delivery=delivery, ack=end and end[2], association='layout delivery order to recipient inbound slot')
        service = [e for e in events if e[0] == H['custody_service_start'] and e[3] <= start[3]]
        waiting = point(start[3], 'host', 'transfer_wait_start')
        ended = point(end and end[3], 'host', 'transfer_wait_end')
        row['service_to_wait_start'] = interval(point(max((e[3] for e in service), default=None), 'host', 'custody_service_start'),
                                                waiting, missing='custody_service_start_unobserved')
        row['recipient_wait'] = interval(waiting, ended)
        if target is None or target['recipient'] not in pages:
            row['inbound'] = dict(unobserved='recipient page or delivery layout missing'); rows.append(row); continue
        process, ev = f"worker{target['recipient']}", records(pages[target['recipient']])
        sample = first(ev, W['inbound_observed'], phase=target['slot'])
        sample = point(sample and sample[3], process, 'inbound_observed')
        acked = published(ev, index_of(ev, W['inbound_acknowledged'], phase=target['slot']), process, WORKER_EVENTS, tb)
        row['wait_start_to_inbound_pass_sample'] = interval(waiting, sample)
        row['inbound_pass_sample_to_ack'] = interval(sample, acked)
        # The inbound-delivery response: the host's wait start follows its commit store; the worker's
        # acknowledgement publication ends it. Bounded like release_to_ack and activation_response.
        row['inbound_response'] = interval(waiting, acked)
        observed = polled(row, doc, interval, H['transfer_wait_end'], delivery, acked,
                          ('inbound_ack_to_host_observed', 'inbound_ack_first_check_positive'))
        inversion(pairs, f'g{g}:d{delivery}:inbound_ack', raw_of(acked), observed)
        source = pages.get(target['source'])
        if source is not None:
            answered = first(records(source), W['exchange_answered'], after=end[3]) if end else None
            row['host_wait_end_to_exchange_answered'] = interval(
                ended, point(answered and answered[3], f"worker{target['source']}", 'exchange_answered'),
                missing='exchange_answer_unobserved')
        rows.append(row)
    return rows


def host_sleeps(doc, record=EMPTY_SLEEP_RECORD):
    out = {}
    tb = (doc['timebase']['numer'], doc['timebase']['denom'])
    for key, value in sorted((doc['sleeps'] or {}).items()):
        count = value['count']
        row = dict(key=key, wait=SLEEP_KEYS[key], count=count, sum_ns=value['sum_ns'], requested_sum_ns=value['requested_sum_ns'])
        if count:
            row.update(mean_ns=value['sum_ns'] // count, mean_requested_ns=value['requested_sum_ns'] // count,
                       mean_overshoot_ns=(value['sum_ns'] - value['requested_sum_ns']) // count,
                       max_ns=value['max_ns'], min_ns=ns(value['min_ticks'], tb),
                       last_ns=ns(value['last_post'], tb) - ns(value['last_pre'], tb),
                       last_requested_ns=value.get('last_requested_ns'))
        pairs = record['pairs'].get(key)
        if pairs is not None:
            row.update(event_pairs=len(pairs), event_durations_ns=[ns(p['end'], tb) - ns(p['begin'], tb) for p in pairs])
        out[SLEEP_KEYS[key]] = row
    return out


def host_clock_pairs(doc):
    """Host CLOCK_MONOTONIC minus continuous time at request start and flush, for envelope cross-checks."""
    tb = (doc['timebase']['numer'], doc['timebase']['denom'])
    out = {}
    for pair in doc.get('clock_pairs') or []:
        if pair.get('observed') and pair.get('monotonic_ns') is not None:
            before, after = ns(pair['continuous_before'], tb), ns(pair['continuous_after'], tb)
            out[pair['stage']] = dict(monotonic_minus_continuous_ns=pair['monotonic_ns'] - (before + after) // 2,
                                      bracket_ns=after - before)
        else:
            out[pair.get('stage')] = dict(unobserved='clock pair not recorded')
    return out


def request_timeline(events, tb):
    start = first(events, H['request_start'])
    if start is None:
        return {}
    out = {}
    for name in ('worker_spawned', 'ready_observed', 'applied_observed', 'setup_done', 'done_observed', 'schedule_done',
                 'exit_requested', 'worker_reaped', 'flush_begin'):
        e = first(events, H[name])
        out[name + '_offset_ns'] = ns(e[3], tb) - ns(start[3], tb) if e else None
    out['death_checks'] = sum(1 for e in events if e[0] == H['death_check'])
    out['stamp_pages_copied'] = [e[2] for e in events if e[0] == H['stamp_page_copied']]
    return out


def cross_checks(row, fields):
    """Envelope millisecond fields beside stamped ns (different clocks and read points)."""
    out = {}
    def pair(name, path, stamped):
        value = fields.get(path)
        out[name] = dict(envelope_path=path, envelope_ms=value, stamped_ns=stamped,
                         difference_ms=(value - stamped / 1e6) if value is not None and stamped is not None else None)
    phases = row.get('phases') or []
    if row['form'] == 'ordinary':
        collected = [p['collection']['ns'] for p in phases if isinstance(p.get('collection'), dict)]
        pair('sentinel_excluded', 'runner_subprocess.sentinel_wait.excluded_ms',
             sum(collected) if collected and None not in collected else None)
    for p in phases:
        index = p['phase']
        if isinstance(p.get('grace'), dict):
            pair(f'p{index}_validator_grace', f'phases.{index}.validator_subprocess.exit_grace_wait.elapsed_ms', p['grace']['ns'])
        if row['form'] == 'actor' and isinstance(p.get('collection'), dict):
            pair(f'p{index}_collection', f'phases.{index}.visit_timing.collection_ms', p['collection']['ns'])
    return out


def calibration_terms(artifacts):
    """Stamp cost, busy-reader endpoint term and alignment bound from a clock-pair receipt that its own checker accepts."""
    path = Path(artifacts) / 'clock-pair' / 'calibration.json'
    if not path.exists():
        return None, 'not_established: clock-pair/calibration.json absent'
    sys.path.insert(0, str(HERE))
    try:
        import worker_wait_clock_pair
        resolution = worker_wait_clock_pair.resolution_numbers(json.loads(path.read_text()), base=path.parent)
        stamp = math.ceil(resolution['stamp_ns'])
        alignment = resolution['alignment']['bound_ns']
        busy = resolution['readers'].get('busy') or {}
    except (ImportError, ValueError, KeyError, TypeError, AssertionError) as exc:
        return None, f'not_established: clock-pair receipt rejected ({str(exc)[:300]})'
    return dict(stamp_ns=stamp, read_overhead_ns=resolution['read_overhead_ns'], endpoint_term_ns=busy.get('endpoint_term_ns'),
                busy_combined_uncertainty_ns=busy.get('combined_uncertainty_ns'), alignment_ns=alignment,
                instrument_gate=resolution['instrument_gate'], source=str(path), sha256=sha256(path)), 'established'


# ---- trial evaluation -----------------------------------------------------------

def load_json(path):
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


def load_bundle(trial_dir):
    trial_dir = Path(trial_dir)
    return dict(dir=str(trial_dir), trial=load_json(trial_dir / 'trial.json'), conditions=load_json(trial_dir / 'conditions.json'),
                started=load_json(trial_dir / 'started.json'), stamps=load_json(trial_dir / 'stamps.json'),
                exported=load_json(trial_dir / 'exported.json'),
                host_exit=load_json(trial_dir / 'host-exit.json'), validation=load_json(trial_dir / 'validation.json'))


def check_conditions(conditions):
    if conditions is None:
        return ['conditions_missing']
    out = []
    try:
        if conditions['sleep_overlapped'] or abs(conditions['sleep_difference_ns']) > conditions['sleep_tolerance_ns']:
            out.append('sleep_overlapped')
        before, after = conditions['power_before'], conditions['power_after']
        if before['source'] is None or after['source'] is None or before['lowpowermode'] is None or after['lowpowermode'] is None:
            out.append('power_unobserved')
        elif before['source'] != after['source'] or before['lowpowermode'] != after['lowpowermode']:
            out.append('power_transition')
        pacing = conditions['pacing']
        low, high = pacing['eligible_gap_ns']
        if pacing['actual_gap_ns'] is None or not low <= pacing['actual_gap_ns'] <= high:
            out.append('pacing_out_of_range')
    except (KeyError, TypeError, ValueError):
        out.append('conditions_malformed')
    return out


def evaluate_bundle(bundle, calibration=None):
    """One decomposition row. Problems accumulate; status follows STATUS_ORDER."""
    trial = bundle['trial']
    row = dict(dir=bundle['dir'], problems=[], exclusions=[])
    if trial is None:
        row.update(status='incomplete', problems=['trial_receipt_missing']); return row
    for key in ('app', 'cell', 'regime', 'index', 'specimen_id', 'form', 'dry_run', 'flavour'):
        row[key] = trial.get(key)
    problems = row['problems']
    if trial['status'] in ('skipped_window', 'not_run_after_stop'):
        row['status'] = 'skipped'; problems.append(trial['status']); return row
    completed = trial['status'] == 'completed'
    if not completed:
        problems.append('driver_' + trial['status'])
    row['whole_request'] = trial.get('whole_request')
    row['pacing'] = (bundle['conditions'] or {}).get('pacing')
    power = (bundle['conditions'] or {}).get('power_before') or {}
    row['power_source'], row['lowpowermode'] = power.get('source'), power.get('lowpowermode')
    if completed or bundle['conditions'] is not None:
        for code in check_conditions(bundle['conditions']):
            (row['exclusions'] if code in EXCLUSIONS else problems).append(code)
    validation = bundle['validation']
    if validation is None and completed:
        problems.append('validation_missing')
    elif validation is not None:
        problems.extend('validation:' + p for p in validation['problems'])
    if bundle['host_exit'] is None and completed:
        problems.append('host_exit_missing')
    row['envelope_ms_fields'] = (validation or {}).get('cross_check_fields') or (validation or {}).get('host_ms_fields') or {}
    if trial['app'] == 'neighbor':
        if bundle['stamps'] is not None or bundle['started'] is not None:
            problems.append('neighbor_has_stamps')
        row['host_ms_fields'] = (validation or {}).get('host_ms_fields')
    elif completed:
        evaluate_stamps(bundle, row, calibration)
        row['export'] = export_duration(bundle.get('exported'), bundle.get('stamps'))
    row['problems'] = sorted(set(problems)); row['exclusions'] = sorted(set(row['exclusions']))
    codes = row['problems']
    if any(c.startswith('validation:') or c.startswith('driver_') for c in codes):
        row['status'] = 'failed'
    elif any(c in INCOMPLETE for c in codes):
        row['status'] = 'incomplete'
    elif codes:
        row['status'] = 'refused'
    elif row['exclusions']:
        row['status'] = 'excluded'
    else:
        row['status'] = 'accepted'
    return row


def evaluate_stamps(bundle, row, calibration):
    trial, doc, problems = bundle['trial'], bundle['stamps'], row['problems']
    if bundle['started'] is None:
        problems.append('started_missing')
    if doc is None:
        problems.append('stamps_missing'); return
    found = check_stamps(doc, trial)
    problems.extend(found)
    if any(p in ('stamps_malformed', 'stamps_timebase_invalid', 'host_events_malformed') for p in found):
        return
    tb = (doc['timebase']['numer'], doc['timebase']['denom'])
    events = doc['events']
    started = bundle['started']
    if started is not None:
        if started.get('host_pid') != doc['host_pid'] or started.get('specimen_id') != trial['specimen_id']:
            problems.append('started_mismatch')
        spawned = first(events, H['worker_spawned'])
        if spawned and type(started.get('raw')) is int and started['raw'] > spawned[3]:
            problems.append('started_after_spawn')
    watch = (bundle['host_exit'] or {}).get('registration')
    if watch and watch['generation']['pid'] != doc['host_pid']:
        problems.append('host_exit_pid_mismatch')
    pages = {}
    copied = sorted(e[2] for e in events if e[0] == H['stamp_page_copied'])
    counts = []
    for entry in doc['worker_pages']:
        try:
            data = base64.b64decode(entry['base64'], validate=True)
        except (ValueError, KeyError, TypeError):
            problems.append('worker_page_encoding'); continue
        page, page_problems = decode_page(data)
        problems.extend(page_problems)
        if page is None: continue
        if page['pid'] != entry.get('pid'): problems.append('worker_page_pid_mismatch')
        if tuple(page['timebase']) != tb: problems.append('worker_timebase_mismatch')
        if entry.get('event_count_read') != page['event_count']: problems.append('stamp_page_count_mismatch')
        counts.append(page['event_count'])
        pages[entry.get('actor') or 0] = page
    if counts and len(counts) == len(doc['worker_pages']) and sorted(counts) != copied:
        problems.append('stamp_page_count_mismatch')
    row['request'] = request_timeline(events, tb)
    sleeps = sleep_record(events)
    row['host_sleep_events'] = sleep_event_state(doc, sleeps)
    row['host_sleeps'] = host_sleeps(doc, sleeps) if 'host_sleep_register_malformed' not in problems else None
    row['host_clock_pairs'] = host_clock_pairs(doc)
    row['host_stamp_cost'] = (host_stamp_cost(doc, tb) if 'host_stamp_cost_malformed' not in problems
                              else dict(median_ns=None, unobserved='stamp_cost malformed'))
    row['custody_passes'] = doc.get('custody_passes')
    counts = grace_counts(doc) if 'host_sleep_register_malformed' not in problems else None
    row.update(counts or {name: None for name in GRACE_COUNTS})
    if counts is None:
        row['grace_wait_record'] = dict(unobserved='worker grace sleep register malformed')
    row['worker_waits'] = {str(actor): worker_wait_registers(page) for actor, page in pages.items()}
    row['scan'] = scan_record(trial['layout'], pages)
    row['host_flavour'] = doc['flavour']
    if len(pages) != len(doc['worker_pages']) or not pages:
        return
    registers = doc['registers'] or {}
    # The ordinary host polls worker 0's done flag; an actor-form trial only where a 144 register exists.
    watched = [0] if trial['form'] == 'ordinary' else [a for a in sorted(pages) if f"{H['done_observed']}:{a}" in registers]
    def build(interval, pairs):
        phases = (ordinary_phases(doc, pages[0], trial, interval, pairs) if trial['form'] == 'ordinary'
                  else actor_phases(doc, pages, trial, interval, pairs))
        return phases, done_rows(doc, pages, interval, pairs, watched), actor_intervals(doc, pages, interval)
    cost = row['host_stamp_cost']['median_ns']
    pairs = []
    row['phases'], row['done'], row['actors'] = build(Interval(tb, calibration, cost, sleeps=sleeps), pairs)
    for pair in pairs:
        pair['inverted_ns'] = ns(pair['publication_raw'], tb) - ns(pair['observation_raw'], tb) if pair['inverted_ticks'] else 0
    inverted = [p['inverted_ns'] for p in pairs if p['inverted_ns'] > 0]
    row['clock_order'] = dict(pairs=pairs, inversions=len(inverted), max_inversion_ns=max(inverted, default=0),
                              refusal_threshold_ns=ALIGNMENT_REFUSAL_NS)
    if any(v > ALIGNMENT_REFUSAL_NS for v in inverted):
        problems.append('clock_alignment_violation')
    if inverted:
        # Counted inversions widen the alignment term of every cross-process interval.
        row['phases'], row['done'], row['actors'] = build(Interval(tb, calibration, cost, max(inverted), sleeps=sleeps), [])
    for p in row['phases']:
        if p.get('eligible_planned') is not None and p['eligible_planned'] != p['expected_eligible']:
            problems.append('eligible_count_mismatch')
    row['detection_total'] = detection_total(row)
    if row['detection_total'].get('ns') is not None and row['detection_total'].get('uncertainty_ns') is not None:
        row['detection_total']['below_instrument_floor'] = row['detection_total']['ns'] <= row['detection_total']['uncertainty_ns']
    row['host_ms_cross_checks'] = cross_checks(row, (bundle['validation'] or {}).get('host_ms_fields') or {})
    row['observer_overlap'] = observer_overlap(bundle['host_exit'], row['phases'])
    if row['observer_overlap'].get('overlaps_held'):
        row['exclusions'].append('observer_overlap')


def inbound_slots(layout):
    """Inbound slot indices per actor index: the deliveries the layout addresses to it (none in the ordinary form)."""
    slots = {}
    for delivery in layout.get('deliveries') or []:
        slots.setdefault(delivery['recipient'], []).append(delivery['slot'])
    return slots


def scan_record(layout, pages):
    """Per actor: the page's scan counters, the actor's inbound_count from the layout and the slots the page's
    INBOUND_ACKNOWLEDGED events name; inbound_observed when they name each layout slot exactly once."""
    slots, out = inbound_slots(layout), {}
    for actor, page in sorted(pages.items()):
        scan, declared = page['scan'], sorted(slots.get(actor, []))
        acknowledged = sorted(e['phase'] for e in page['events'] if e['event'] == W['inbound_acknowledged'])
        out[str(actor)] = dict({name: scan[name] for name in SCAN_COUNTERS[:-1]}, zero_visit_passes=scan['visits_histogram'].get('0', 0),
                               inbound_count=len(declared), inbound_count_source=SCAN_INBOUND_SOURCE,
                               acknowledged_slots=acknowledged, inbound_observed=acknowledged == declared,
                               role_unknown_passes_uncounted=scan['role_unknown_passes_uncounted'])
    return out


def export_duration(exported, stamps):
    """The host's own export span from the .exported marker; the neighbor has none and a missing marker is labeled."""
    if not isinstance(exported, dict) or stamps is None:
        return dict(duration_ns=None, unobserved='exported marker absent')
    begin, end = exported.get('begin_raw'), exported.get('end_raw')
    if type(begin) is not int or type(end) is not int or end < begin or exported.get('host_pid') != stamps.get('host_pid'):
        return dict(duration_ns=None, unobserved='exported marker malformed or from another host')
    tb = (stamps['timebase']['numer'], stamps['timebase']['denom'])
    return dict(duration_ns=ns(end - begin, tb), bytes=exported.get('bytes'))


def observer_overlap(host_exit, phases):
    """Whether the driver's exit-watch registration ran inside a held interval."""
    registration = (host_exit or {}).get('registration')
    if not registration:
        return dict(registration=None)
    activity = (host_exit or {}).get('activity_ns')
    if isinstance(activity, list) and len(activity) == 2 and all(type(v) is int for v in activity):
        begin, end, span = activity[0], activity[1], 'activity_ns'
    else:
        begin, end, span = registration['begin_ns'], registration['end_ns'], 'registration'
    held = [p['held_interval_ns'] for p in phases if p.get('held_interval_ns')]
    return dict(registration=[registration['begin_ns'], registration['end_ns']], span=[begin, end], span_source=span,
                overlaps_held=any(begin < b and a < end for a, b in held),
                held_intervals=held, clock='driver and observer mach_continuous_time ns; stamps converted with the same floor')


# ---- aggregation ----------------------------------------------------------------

def group_key(row):
    return (row['app'], row['cell'], row['regime'], row.get('power_source'), row.get('lowpowermode'),
            json.dumps(row.get('flavour'), sort_keys=True))


DETECTION_LEAVES = ('arrival_detection', 'arrival_first_check_positive', 'completion_detection',
                    'completion_first_check_positive', 'inbound_ack_to_host_observed', 'inbound_ack_first_check_positive')


def detection_total(row):
    """The per-trial sum of the host's post-publication detection latencies: arrival after an activation or a
    release (every actor visit; ordinary phases after the first, whose arrival follows readiness), completion after
    a release, and the recipient acknowledgement after an inbound commit. Uncertainty is the sum of the parts'.
    The worker's terminal publication follows no host publication and is excluded."""
    parts = []
    for name, record in component_values(row):
        if record.get('ns') is None or name == 'detection_total':
            continue
        prefix, _, leaf = name.rpartition('.')
        if leaf not in DETECTION_LEAVES:
            continue
        if row.get('form') == 'ordinary' and leaf.startswith('arrival') and prefix == 'p0':
            continue
        parts.append((name, record))
    if not parts:
        return dict(ns=None, unobserved='no post-publication detection in this form', components=[])
    uncertainties = [r.get('uncertainty_ns') for _, r in parts]
    return dict(ns=sum(r['ns'] for _, r in parts), components=[n for n, _ in parts],
                uncertainty_ns=None if None in uncertainties else sum(uncertainties),
                uncertainty_basis='sum of the parts' if None not in uncertainties else 'a part is not established',
                cross_process=True, below_instrument_floor=None)


def component_values(row):
    """(name, record) for every interval record in a row, including custody rows and the detection total."""
    if isinstance(row.get('detection_total'), dict) and 'ns' in row['detection_total']:
        yield 'detection_total', row['detection_total']
    for p in row.get('phases') or []:
        prefix = f"p{p['phase']}."
        for name, value in p.items():
            if isinstance(value, dict) and 'ns' in value:
                yield prefix + name, value
        for c, transfer in enumerate(p.get('custody') or []):
            for name, value in transfer.items():
                if isinstance(value, dict) and 'ns' in value:
                    yield f'{prefix}custody{c}.{name}', value
    for done in row.get('done') or []:
        for name, value in done.items():
            if isinstance(value, dict) and 'ns' in value:
                yield f"w{done['actor']}.{name}", value
    for actor in row.get('actors') or []:
        for name, value in actor.items():
            if isinstance(value, dict) and 'ns' in value:
                yield f"w{actor['actor']}.{name}", value


def wait_values(row):
    """(name, passes, mean pass period, period definition) for each worker wait in a row."""
    for p in row.get('phases') or []:
        for kind in ('activation_wait', 'release_wait'):
            if isinstance(p.get(kind), dict):
                yield f"p{p['phase']}.{kind}", p[kind].get('passes'), p[kind].get('mean_pass_period_ns'), SAMPLED_PERIOD
        for wait in p.get('exchange_waits') or []:
            yield f"p{p['phase']}.exchange_wait.slot{wait['slot']}", wait['passes'], wait['upper_mean_pass_period_ns'], UPPER_PERIOD


def stats(values):
    return dict(n=len(values), median=statistics.median(values), min=min(values), max=max(values)) if values else dict(n=0)


def aggregate(rows):
    """Aggregates for one homogeneous group; mixing apps, cells, regimes, power, low power mode or flavour is refused."""
    keys = {group_key(r) for r in rows}
    assert len(keys) == 1, f'pooled groups refused: {sorted(keys)}'
    assert all(r['status'] == 'accepted' for r in rows), 'aggregates take accepted trials only'
    components = {}
    for row in rows:
        for name, record in component_values(row):
            entry = components.setdefault(name, dict(values=[], unobserved={}, uncertainty=[], detection=[], worker=[],
                                                     basis=set(), below=0, sleeps={}, scopes={}))
            if record['ns'] is None:
                entry['unobserved'][record['unobserved']] = entry['unobserved'].get(record['unobserved'], 0) + 1
                continue
            entry['values'].append(record['ns'])
            entry['uncertainty'].append(record.get('uncertainty_ns')); entry['basis'].add(record.get('uncertainty_basis'))
            entry['below'] += bool(record.get('below_instrument_floor'))
            if record.get('detection_bracket_ns') is not None: entry['detection'].append(record['detection_bracket_ns'])
            if record.get('worker_detection_bracket_ns') is not None: entry['worker'].append(record['worker_detection_bracket_ns'])
            if 'during_sleep_scope' in record:
                scope = record['during_sleep_scope']
                key = record['during_sleep_key'] or ('none' if scope == 'no_sleep_between' else 'unattributed')
                entry['sleeps'][key] = entry['sleeps'].get(key, 0) + 1
                entry['scopes'][scope] = entry['scopes'].get(scope, 0) + 1
    out = {}
    for name, entry in sorted(components.items()):
        established = entry['uncertainty'] and None not in entry['uncertainty']
        out[name] = dict(stats(entry['values']), unobserved=entry['unobserved'],
                         max_uncertainty_ns=max(entry['uncertainty']) if established else None,
                         uncertainty_basis=sorted(entry['basis']),
                         detection_bracket=stats(entry['detection']), worker_detection_bracket=stats(entry['worker']))
        if established:
            out[name]['pairwise_comparison_uncertainty_ns'] = 2 * out[name]['max_uncertainty_ns']
            # Resolved in every trial when each value exceeds that trial's own uncertainty.
            out[name]['above_uncertainty_in_every_trial'] = all(v > u for v, u in zip(entry['values'], entry['uncertainty']))
            out[name]['below_instrument_floor'] = entry['below']
        if entry['sleeps']:
            out[name]['during_sleep_key'] = entry['sleeps']
            out[name]['during_sleep_scope'] = entry['scopes']
        if name.endswith('.recipient_wait'):
            out[name]['note'] = RECIPIENT_NOTE
    waits = {}
    for row in rows:
        for name, passes, period, definition in wait_values(row):
            entry = waits.setdefault(name, dict(passes=[], periods=[], unavailable=0, definitions=set()))
            entry['definitions'].add(definition)
            if passes is None:
                entry['unavailable'] += 1
                continue
            entry['passes'].append(passes)
            if period is not None: entry['periods'].append(period)
    whole = [r['whole_request']['elapsed_ns'] for r in rows if (r.get('whole_request') or {}).get('elapsed_ns') is not None]
    sleeps = {}
    for row in rows:
        for name, value in (row.get('host_sleeps') or {}).items():
            if value['count']:
                sleeps.setdefault(name, []).append(value['mean_overshoot_ns'])
    order = [r['clock_order'] for r in rows if r.get('clock_order')]
    grace = {}
    for name in GRACE_COUNTS:
        values = [r[name] for r in rows if r.get(name) is not None]
        grace[name] = dict(stats(values), sum=sum(values), unavailable=len(rows) - len(values))
    exports = [r['export']['duration_ns'] for r in rows if (r.get('export') or {}).get('duration_ns') is not None]
    envelope = {}
    for row in rows:
        for path, value in (row.get('envelope_ms_fields') or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                envelope.setdefault(path, []).append(value)
    scan = {}
    for row in rows:
        for actor, record in (row.get('scan') or {}).items():
            entry = scan.setdefault(actor, dict(inbound_count=set(), **{name: [] for name in SCAN_COUNTERS}))
            entry['inbound_count'].add(record['inbound_count'])
            for name in SCAN_COUNTERS:
                entry[name].append(record[name])
    scan = {actor: dict(inbound_count=sorted(entry.pop('inbound_count')),
                        **{name: dict(stats(values), sum=sum(values)) for name, values in entry.items()})
            for actor, entry in sorted(scan.items(), key=lambda item: int(item[0]))}
    return dict(components=out, whole_request_ns=stats(whole), export_duration_ns=stats(exports), scan=scan,
                envelope_ms={k: stats(v) for k, v in sorted(envelope.items())},
                waits={k: dict(passes=stats(v['passes']), mean_pass_period_ns=stats(v['periods']), unavailable=v['unavailable'],
                               period_definition=sorted(v['definitions']))
                       for k, v in sorted(waits.items())},
                host_sleep_mean_overshoot_ns={k: stats(v) for k, v in sleeps.items()}, grace_counts=grace,
                clock_order=dict(trials=len(order), inversions=sum(a['inversions'] for a in order),
                                 max_inversion_ns=max((a['max_inversion_ns'] for a in order), default=0)))


def summarize(rows, required=None):
    groups = {}
    for row in rows:
        if row.get('app') is None: continue
        groups.setdefault(group_key(row), []).append(row)
    out = []
    for key, members in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
        app, cell, regime, power, lowpower, flavour = key
        counts = {s: sum(1 for r in members if r['status'] == s) for s in STATUS_ORDER}
        accepted = [r for r in members if r['status'] == 'accepted']
        entry = dict(app=app, cell=cell, regime=regime, power_source=power, lowpowermode=lowpower, flavour=json.loads(flavour),
                     counts=counts, dry_run=any(r.get('dry_run') for r in members),
                     non_accepted=[dict(dir=r['dir'], status=r['status'], problems=r['problems'], exclusions=r['exclusions'])
                                   for r in members if r['status'] != 'accepted'])
        if required is not None:
            entry['required'] = required.get(f'{app}/{cell}/{regime}')
            entry['coverage'] = 'complete' if entry['required'] is not None and counts['accepted'] >= entry['required'] else 'incomplete'
        entry.update(aggregate(accepted) if accepted else dict(components={}, whole_request_ns=dict(n=0), waits={}))
        out.append(entry)
    return out


# ---- matched pairs (comparison runs) ----------------------------------------------

def pair_key(row):
    """The group a pair belongs to: every grouping key except the app."""
    return group_key(row)[1:]


def pair_components(row):
    """name -> (value, uncertainty, form) for each observed interval; split observations under one *_to_observation name."""
    out = {}
    for name, record in component_values(row):
        if record['ns'] is None:
            continue
        prefix, _, leaf = name.rpartition('.')
        out[f'{prefix}.{OBSERVATION_FORMS[leaf]}' if leaf in OBSERVATION_FORMS else name] = (
            record['ns'], record.get('uncertainty_ns'), leaf if leaf in OBSERVATION_FORMS else None)
    return out


def pair_waits(row):
    """Release and activation pass counts; exact counts, so their uncertainty is zero."""
    return {name: (passes, 0, None) for name, passes, _, _ in wait_values(row)
            if name.rpartition('.')[2] in PAIRED_WAITS and passes is not None}


IMPROVES, IMPROVES_SPREAD = 'improves_beyond_uncertainty_in_every_pair', 'improves_beyond_spread_in_every_pair'
WORSENS, WORSENS_SPREAD = 'worsens_beyond_instrument_uncertainty', 'worsens_beyond_spread_in_any_pair'
WORSENS_SPREAD_EVERY = 'worsens_beyond_spread_in_every_pair'


def side_spread(values):
    """One side's spread of one quantity: max - min over its accepted trials in the group."""
    return max(values) - min(values)


def settle(outcomes, required, within):
    """(improves in every pair, worsens in any pair) from per-pair outcomes; outcomes other than
    improved, worsened and `within` are not established."""
    established = [o for o in outcomes if o in ('improved', 'worsened', within)]
    complete = len(established) == len(outcomes) >= required
    return (False if any(o != 'improved' for o in established) else True if complete else None,
            True if 'worsened' in outcomes else False if complete else None)


def settle_every_worse(outcomes, required, within):
    """Worsening in every pair: refuted by any established pair that is not worse, established only when all
    required pairs are established and worse; a resolved regression rather than one noisy pair."""
    established = [o for o in outcomes if o in ('improved', 'worsened', within)]
    complete = len(established) == len(outcomes) >= required
    return False if any(o != 'worsened' for o in established) else True if complete else None


def pair_series(pairs, values, required, accepted, instrument=True):
    """Per pair baseline minus candidate, judged against the instrument uncertainty (the sum of both sides')
    and against each side's spread plus that uncertainty, with the four verdicts.

    values(row) maps a name to (value, uncertainty, form); accepted maps each app to its accepted rows in the
    group, the spread's population. Improvement is refuted by any established pair that falls short and
    established only when all required pairs pass; worsening is established by any pair and refuted only when
    all required pairs are established and none is worse. Without instrument uncertainty (whole request) only
    the spread verdicts are given."""
    measured = [(index, values(b), values(c)) for index, b, c in pairs]
    population = {app: [values(r) for r in accepted.get(app, [])] for app in PAIR_APPS}
    out = {}
    for name in sorted({n for _, vb, vc in measured for n in set(vb) | set(vc)}):
        spread = {}
        for app in PAIR_APPS:
            seen = [v[name][0] for v in population[app] if name in v]
            spread[app] = dict(ns=side_spread(seen) if seen else None, trials=len(seen))
        rows = []
        for index, vb, vc in measured:
            if name not in vb or name not in vc:
                absent = [app for app, v in zip(PAIR_APPS, (vb, vc)) if name not in v]
                rows.append(dict(index=index, outcome='absent', spread_outcome='absent', absent_on=absent))
                continue
            (b, ub, fb), (c, uc, fc) = vb[name], vc[name]
            combined = None if ub is None or uc is None else ub + uc
            outcome = ('uncertainty_not_established' if combined is None else 'improved' if b - c > combined
                       else 'worsened' if c - b > combined else 'within_uncertainty')
            better = None if combined is None or spread['candidate']['ns'] is None else spread['candidate']['ns'] + combined
            worse = None if combined is None or spread['baseline']['ns'] is None else spread['baseline']['ns'] + combined
            spread_outcome = ('not_established' if better is None or worse is None else 'improved' if b - c > better
                              else 'worsened' if c - b > worse else 'within_spread')
            row = dict(index=index, baseline=b, candidate=c, difference=b - c, combined_uncertainty=combined,
                       outcome=outcome if instrument else 'not_applicable', improve_threshold=better, worsen_threshold=worse,
                       spread_outcome=spread_outcome)
            if fb or fc:
                row['forms'] = dict(baseline=fb, candidate=fc)
            rows.append(row)
        improves, worsens = settle([r['outcome'] for r in rows], required, 'within_uncertainty')
        improves_spread, worsens_spread = settle([r['spread_outcome'] for r in rows], required, 'within_spread')
        worsens_spread_every = settle_every_worse([r['spread_outcome'] for r in rows], required, 'within_spread')
        entry = {'pairs': rows, 'spread_ns': spread, IMPROVES: improves if instrument else None, IMPROVES_SPREAD: improves_spread,
                 WORSENS: worsens if instrument else None, WORSENS_SPREAD: worsens_spread, WORSENS_SPREAD_EVERY: worsens_spread_every}
        if not instrument:
            entry['instrument_verdicts'] = 'not applicable: no instrument uncertainty; see the spread verdicts'
        if None in (improves_spread, worsens_spread) or (instrument and None in (improves, worsens)):
            established = sum(r['spread_outcome'] in ('improved', 'worsened', 'within_spread') for r in rows)
            entry['withheld'] = (f'{established} established of {required} required pairs'
                                 + (f'; absent or unestablished in {len(rows) - established}' if established < len(rows) else ''))
        out[name] = entry
    return out


def response_bounds(accepted, gate_credited):
    """Candidate upper bound minus baseline lower bound per response component, over each side's accepted trials."""
    sides = {app: [pair_components(r) for r in accepted.get(app, [])] for app in PAIR_APPS}
    present = lambda app: {n for values in sides[app] for n in values if n.rpartition('.')[2] in RESPONSE_COMPONENTS}
    out = {}
    for name in sorted(present('candidate') & present('baseline')):
        upper = max((v[name] for v in sides['candidate'] if name in v), key=lambda item: item[0])
        lower = min((v[name] for v in sides['baseline'] if name in v), key=lambda item: item[0])
        bound = upper[0] - lower[0]
        combined = None if upper[1] is None or lower[1] is None else upper[1] + lower[1]
        resolved = combined is not None and combined <= RESPONSE_UNCERTAINTY_GATE_NS
        out[name] = dict(candidate_upper_ns=upper[0], baseline_lower_ns=lower[0], bound_ns=bound, limit_ns=RESPONSE_LIMIT_NS,
                         within_limit=bound <= RESPONSE_LIMIT_NS, combined_uncertainty_ns=combined,
                         uncertainty_at_most_0_5_ms=resolved, instrument_gate_credited=gate_credited,
                         credited=bound <= RESPONSE_LIMIT_NS and resolved and gate_credited,
                         trials={app: sum(name in v for v in sides[app]) for app in PAIR_APPS})
    return out


def host_sleep_pairs(pairs):
    """Per pair, each host sleep or bounded wait key with a sleep on either side: count and total duration."""
    out = {}
    for index, b, c in pairs:
        both = [r.get('host_sleeps') or {} for r in (b, c)]
        for wait in sorted(set(both[0]) | set(both[1])):
            sides = [side.get(wait) or dict(count=0, sum_ns=0) for side in both]
            if any(side['count'] for side in sides):
                out.setdefault(wait, []).append(dict(index=index, **{app: dict(count=side['count'], sum_ns=side['sum_ns'])
                                                                     for app, side in zip(PAIR_APPS, sides)}))
    return out


def grace_pairs(pairs):
    """Per grace count: each pair's exact baseline minus candidate difference and each side's sum over the pairs."""
    out = {}
    for name in GRACE_COUNTS:
        rows = []
        for index, b, c in pairs:
            if b.get(name) is None or c.get(name) is None:
                rows.append(dict(index=index, absent_on=[app for app, r in zip(PAIR_APPS, (b, c)) if r.get(name) is None]))
                continue
            rows.append(dict(index=index, baseline=b[name], candidate=c[name], difference=b[name] - c[name]))
        out[name] = dict(pairs=rows, sums={app: sum(r[app] for r in rows if app in r) for app in PAIR_APPS},
                         note='exact counts; baseline minus candidate; no verdicts')
    return out


def scan_lower(baseline_count, baseline_passes, candidate_count, candidate_passes):
    """Whether candidate_count / candidate_passes < baseline_count / baseline_passes, exactly (both passes positive)."""
    return candidate_count * baseline_passes < baseline_count * candidate_passes


def scan_floor(passes, inbound):
    """The fewest visits, and so loads, a scan from index 0 over inbound slots makes in passes passes: each pass
    visits every slot except one ending on acknowledging slot i, which visits i + 1, and each slot is acknowledged
    once."""
    return inbound * passes - inbound * (inbound - 1) // 2


def scan_side(record, measure, role):
    count, passes = record[f'{measure}_{role}'], record[f'passes_{role}']
    floor = scan_floor(passes, record['inbound_count'])
    return dict(count=count, passes=passes, per_pass=count / passes if passes else None,
                full_scan_floor=floor, below_full_scan_floor=count < floor)


def scan_unmet(vb, vc):
    """The conditions of a lower pair (SCAN_UNMET) that this pair fails; empty when it is lower."""
    failed = (vb['below_full_scan_floor'], not vc['below_full_scan_floor'],
              not scan_lower(vb['count'], vb['passes'], vc['count'], vc['passes']))
    return [name for name, fails in zip(SCAN_UNMET, failed) if fails]


def scan_pairs(pairs, required):
    """Per actor and caller role, visits and loads per scan pass as exact counts against the full-scan floor with
    lower_in_every_pair, and the zero-visit passes per side. A pair whose inbound_count differs between the sides, or
    whose acknowledged slots differ from the layout on either side, is refused."""
    series, zero, refusals = {}, {}, []
    actors = sorted({a for _, b, c in pairs for r in (b, c) for a in (r.get('scan') or {})}, key=int)
    for actor in actors:
        named = {f'w{actor}.scan_{measure}_per_pass_{role}': (measure, role) for role in SCAN_ROLES for measure in SCAN_MEASURES}
        rows = {name: [] for name in named}
        zero_rows = []
        for index, b, c in pairs:
            sides = [(r.get('scan') or {}).get(actor) for r in (b, c)]
            if None in sides:
                absent = [app for app, side in zip(PAIR_APPS, sides) if side is None]
                for name in named:
                    rows[name].append(dict(index=index, outcome='absent', absent_on=absent))
                zero_rows.append(dict(index=index, absent_on=absent))
                continue
            sb, sc = sides
            inbound = dict(baseline=sb['inbound_count'], candidate=sc['inbound_count'])
            acknowledged = dict(baseline=sb['acknowledged_slots'], candidate=sc['acknowledged_slots'])
            refused = ([SCAN_REFUSAL] if sb['inbound_count'] != sc['inbound_count'] else []) + (
                [SCAN_ACK_REFUSAL] if not (sb['inbound_observed'] and sc['inbound_observed']) else [])
            if refused:
                refusals.append(dict(index=index, actor=int(actor), problems=refused, inbound_count=inbound, acknowledged_slots=acknowledged))
            zero_rows.append(dict(index=index, baseline=sb['zero_visit_passes'], candidate=sc['zero_visit_passes'],
                                  difference=sb['zero_visit_passes'] - sc['zero_visit_passes'], **({'problems': refused} if refused else {})))
            for name, (measure, role) in named.items():
                vb, vc = scan_side(sb, measure, role), scan_side(sc, measure, role)
                row = dict(index=index, baseline=vb, candidate=vc, inbound_count=inbound)
                if refused:
                    row.update(outcome='refused', problems=refused)
                elif not vb['passes'] or not vc['passes']:
                    row.update(outcome='no_passes', no_passes_on=[app for app, v in zip(PAIR_APPS, (vb, vc)) if not v['passes']])
                else:
                    unmet = scan_unmet(vb, vc)
                    row['outcome'] = 'not_lower' if unmet else 'lower'
                    if unmet:
                        row['unmet'] = unmet
                rows[name].append(row)
        for name, found in rows.items():
            outcomes = [r['outcome'] for r in found]
            established = [o for o in outcomes if o in ('lower', 'not_lower')]
            complete = len(established) == len(outcomes) >= required
            entry = {'pairs': found, SCAN_LOWER: False if 'not_lower' in established else True if complete else None}
            if entry[SCAN_LOWER] is None:
                entry['withheld'] = (f'{len(established)} established of {required} required pairs'
                                     + (f'; absent, without passes or refused in {len(found) - len(established)}' if len(established) < len(found) else ''))
            series[name] = entry
        zero[f'w{actor}.scan_zero_visit_passes'] = dict(pairs=zero_rows, sums={app: sum(r[app] for r in zero_rows if app in r) for app in PAIR_APPS})
    return dict(series=series, zero_visit_passes=zero, refusals=refusals, problems=sorted({p for r in refusals for p in r['problems']}),
                rule='per pair: the baseline count at or above its full-scan floor n * passes - n * (n - 1) / 2, the candidate count below '
                     'its own, and the candidate count / passes strictly below the baseline by integer cross-multiplication; exact counts, '
                     'no uncertainty; a pair whose inbound_count differs between the sides, or whose acknowledged slots differ from the '
                     'layout on either side, is refused',
                zero_visit_rule='histogram bucket 0 (passes that visited no slot, both roles) per side; no verdict')


def direction(series):
    """Pairs where the candidate was faster (baseline minus candidate positive), slower or equal."""
    differences = [r['difference'] for r in series.get('pairs', []) if 'difference' in r]
    return dict(faster=sum(d > 0 for d in differences), slower=sum(d < 0 for d in differences),
                equal=sum(d == 0 for d in differences), rule='sign of baseline minus candidate per pair')


def whole_request(row):
    """Whole-request latency, which carries no instrument uncertainty: only its spread verdicts apply."""
    elapsed = (row.get('whole_request') or {}).get('elapsed_ns')
    return {} if elapsed is None else {'whole_request': (elapsed, 0, None)}


def matched_pairs(rows, comparison, gate_credited):
    """Matched baseline/candidate pairs per cell, regime and conditions; None outside a comparison run."""
    if not comparison:
        return None
    required = comparison.get('pairs_required', PAIRS_REQUIRED)
    trials, accepted, groups, unpaired = {}, {}, {}, []
    for row in rows:
        if row.get('app') in PAIR_APPS and row.get('index') is not None:
            trials.setdefault((row['cell'], row['regime'], row['index']), {})[row['app']] = row
            if row['status'] == 'accepted':
                accepted.setdefault(pair_key(row), {}).setdefault(row['app'], []).append(row)
    for (cell, regime, index), sides in sorted(trials.items(), key=lambda item: tuple(map(str, item[0]))):
        b, c = sides.get('baseline'), sides.get('candidate')
        reason = ('the other app has no receipt' if b is None or c is None
                  else 'not accepted on both sides' if (b['status'], c['status']) != ('accepted', 'accepted')
                  else 'conditions differ (power source, low power mode or host flavour)' if pair_key(b) != pair_key(c) else None)
        if reason is None:
            groups.setdefault(pair_key(b), []).append((index, b, c))
            continue
        for app, row in sorted(sides.items()):
            other = sides.get(PAIR_APPS[1 - PAIR_APPS.index(app)])
            unpaired.append(dict(app=app, cell=cell, regime=regime, index=index, dir=row['dir'], status=row['status'],
                                 problems=row['problems'], exclusions=row['exclusions'], reason=reason,
                                 other_status=other and other['status']))
    entries = []
    for key in sorted(set(groups) | set(accepted), key=lambda k: tuple(map(str, k))):
        cell, regime, power, lowpower, flavour = key
        pairs, members = groups.get(key, []), accepted.get(key, {})
        whole = pair_series(pairs, whole_request, required, members, instrument=False).get('whole_request') or dict(pairs=[])
        whole['direction'] = direction(whole)
        entries.append(dict(cell=cell, regime=regime, power_source=power, lowpowermode=lowpower, flavour=json.loads(flavour),
                            pairs_required=required, pairs=[dict(index=i, baseline=b['dir'], candidate=c['dir']) for i, b, c in pairs],
                            components=pair_series(pairs, pair_components, required, members),
                            waits=pair_series(pairs, pair_waits, required, members),
                            whole_request=whole, grace=grace_pairs(pairs), scan=scan_pairs(pairs, required),
                            response=response_bounds(members, gate_credited), host_sleeps=host_sleep_pairs(pairs)))
    return dict(rule=comparison.get('pairing_rule'), pairs_required=required, difference='baseline minus candidate',
                entries=entries, unpaired=unpaired)


def fixture_identity(artifacts):
    """Hashes of the fixture builds a run measured, from its build and staging receipts."""
    out, absent = {}, []
    staged = load_json(artifacts / 'staged-identity-before.json')
    if staged:
        for app, value in sorted(staged.items()):
            executables = value.get('executables') or {}
            out[app] = dict(host=(executables.get(STAGED_HOST) or {}).get('sha256'),
                            worker=(executables.get(STAGED_WORKER) or {}).get('sha256'))
    else:
        absent.append('staged-identity-before.json')
    pair = load_json(artifacts / 'clock-pair-build' / 'clock-pair-build.json')
    if pair:
        out['clock_pair'] = dict(binary=pair.get('binary_sha256'), source=pair.get('source_sha256'))
    else:
        absent.append('clock-pair-build/clock-pair-build.json')
    hosts = {path.parent.name[len('host-'):]: load_json(path) for path in sorted(artifacts.glob('host-*/host-build.json'))}
    stamped = {kind: host for kind, host in hosts.items() if host.get('kind') == 'instrumented'}
    if stamped:
        sources = {(host.get('stamp_source') or {}).get('fixture_sha256') for host in stamped.values()}
        out['host_stamps_source'] = sources.pop() if len(sources) == 1 else 'differs between hosts'
        out['host_patches_skipped'] = {kind: [entry['index'] for entry in host.get('patches_skipped', [])] for kind, host in stamped.items()}
    else:
        absent.append('host-<app>/host-build.json for a stamped host')
    return dict(executables=out, receipts_absent=absent,
                note='Fixture builds and staged copies, not production bytes: the hosts are disposable -Onone builds and the workers are recipe builds.')


def overlap_rows(rows):
    return [dict(dir=r['dir'], app=r['app'], cell=r['cell'], regime=r['regime'], index=r['index'], status=r['status'],
                 overlaps_held=(r.get('observer_overlap') or {}).get('overlaps_held'))
            for r in rows if r.get('app') != 'neighbor' and 'observer_overlap' in r]


def read_artifacts(artifacts, *, write=True):
    artifacts = Path(artifacts).resolve()
    calibration, calibration_status = calibration_terms(artifacts)
    rows = [evaluate_bundle(load_bundle(path.parent), calibration)
            for path in sorted((artifacts / 'trials').glob('*/*/*/*/trial.json'))]
    warm = []
    for path in sorted((artifacts / 'warm').glob('*/*/warm.json')):
        value = json.loads(path.read_text())
        warm.append(dict(dir=str(path.parent), app=value.get('app'), cell=value.get('cell'), status=value.get('status'),
                         whole_request=value.get('whole_request'), excluded='first execution of the staged executables'))
    schedule = load_json(artifacts / 'schedule.json') or {}
    decomposition = dict(version=READER_VERSION, reader=dict(path=str(Path(__file__).resolve()), sha256=sha256(__file__)),
                         calibration=calibration, calibration_status=calibration_status, rows=rows)
    summary = dict(version=READER_VERSION, reader=decomposition['reader'], fixture_identity=fixture_identity(artifacts),
                   calibration_status=calibration_status, instrument_gate=(calibration or {}).get('instrument_gate'),
                   endpoint_term_ns=(calibration or {}).get('endpoint_term_ns'), alignment_ns=(calibration or {}).get('alignment_ns'),
                   busy_combined_uncertainty_ns=(calibration or {}).get('busy_combined_uncertainty_ns'),
                   period_definitions=dict(release_activation=SAMPLED_PERIOD, exchange=UPPER_PERIOD),
                   interpretation=__doc__, unobserved_intervals=UNOBSERVED, alignment_refusal_ns=ALIGNMENT_REFUSAL_NS,
                   counts={s: sum(1 for r in rows if r['status'] == s) for s in STATUS_ORDER},
                   observer_overlap=overlap_rows(rows),
                   excluded=[dict(dir=r['dir'], exclusions=r['exclusions']) for r in rows if r['status'] == 'excluded'],
                   groups=summarize(rows, schedule.get('required')), warm=warm,
                   pairs=matched_pairs(rows, schedule.get('comparison'), bool(((calibration or {}).get('instrument_gate') or {}).get('credited'))))
    if write:
        (artifacts / 'decomposition.json').write_text(json.dumps(decomposition, indent=2) + '\n')
        (artifacts / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        (artifacts / 'summary.md').write_text(markdown(summary))
    return decomposition, summary


def us(value):
    """Microseconds to 0.1; a magnitude under 50 ns prints 0.0, never -0.0 (JSON keeps the raw value)."""
    if value is None:
        return '-'
    return '0.0' if abs(value) < 50 else f'{value / 1000:.1f}'


def short(value):
    return (value or 'absent')[:12]


SLEEP_NONE = {'unattributed': 'unattributed (no containing sleep)', 'none': 'none (no host sleep between)'}


def sleeps(counts, scopes=None):
    text = ', '.join(f"{SLEEP_NONE.get(key) or SLEEP_KEYS.get(key, key)} {n}" for key, n in sorted((counts or {}).items()))
    found = ', '.join(f'{scope} {n}' for scope, n in sorted((scopes or {}).items()) if scope not in ('unattributed', 'no_sleep_between'))
    return text + (f' [scope {found}]' if found else '')


def format_stats(value):
    return 'none' if not value.get('n') else f"n {value['n']}, median {us(value['median'])}, min {us(value['min'])}, max {us(value['max'])}"


def verdict(value):
    return {True: 'yes', False: 'no'}.get(value, 'withheld')


def verdicts(entry, improves):
    """'instrument / spread' for the improvement verdicts, 'instrument / spread any / spread every' for the worsening
    verdicts of one series."""
    keys = (IMPROVES, IMPROVES_SPREAD) if improves else (WORSENS, WORSENS_SPREAD, WORSENS_SPREAD_EVERY)
    instrument = 'n/a' if entry.get('instrument_verdicts') else verdict(entry[keys[0]])
    return f'{instrument} / ' + ' / '.join(verdict(entry[k]) for k in keys[1:])


def per_pair(entry, fmt):
    """'r<index> difference ± combined uncertainty' per pair, with each side's observation form where it has one."""
    form = lambda leaf: 'first check' if leaf and leaf.endswith('first_check_positive') else 'detected'
    parts = []
    for r in entry['pairs']:
        if r['outcome'] == 'absent':
            parts.append(f"r{r['index']} absent on {'/'.join(r['absent_on'])}")
            continue
        bound = 'not established' if r['combined_uncertainty'] is None else fmt(r['combined_uncertainty'])
        bound = '' if r['outcome'] == 'not_applicable' else f' ± {bound}'
        forms = r.get('forms')
        parts.append(f"r{r['index']} {fmt(r['difference'])}{bound}" + (f" ({form(forms['baseline'])}/{form(forms['candidate'])})" if forms else ''))
    return ('; '.join(parts) or 'none') + (f" [withheld: {entry['withheld']}]" if entry.get('withheld') else '')


def spreads(entry, fmt):
    return ' / '.join('-' if entry['spread_ns'][app]['ns'] is None else fmt(entry['spread_ns'][app]['ns']) for app in PAIR_APPS)


def pairs_markdown(pairs):
    ms = lambda value: f'{value / 1e6:.2f} ms'
    lines = ['## Matched pairs', '',
             f"Pairing: {pairs['rule']}. Each per-pair value is baseline minus candidate (positive: the candidate is shorter or "
             'made fewer passes) ± the sum of both sides\' instrument uncertainties; components are microseconds. Each verdict '
             'cell reads instrument / spread. Instrument verdicts compare each difference with that uncertainty. Spread verdicts '
             'also add a side\'s spread (max - min over its accepted trials in this group): an improvement must exceed the '
             'candidate\'s spread plus the uncertainty, a worsening the baseline\'s. An improvement verdict is no once any '
             f"established pair falls short and yes only when all {pairs['pairs_required']} required pairs pass; a worsening "
             'verdict is yes once any pair is worse and no only when all required pairs are established and none is; the third '
             'worsening cell, spread in every pair, is yes only when every required pair is worse beyond the spread, which is a '
             'resolved regression rather than one noisy pair; otherwise '
             'it is withheld. *_to_observation rows run from publication to the host\'s first positive sample in either form, '
             'shown per pair as baseline/candidate (first check or detected). Worker passes are exact counts. Whole request has '
             'no instrument uncertainty (n/a) and only spread verdicts. A response bound is the candidate\'s largest value minus the '
             'baseline\'s smallest, credited only within 2 ms with combined uncertainty at most 0.5 ms and the instrument gate '
             'credited. The apps are never pooled.', '']
    for entry in pairs['entries']:
        unpaired = [u for u in pairs['unpaired'] if (u['cell'], u['regime']) == (entry['cell'], entry['regime'])]
        lines += [f"### {entry['cell']} {entry['regime']} ({entry['power_source']}, lowpowermode {entry['lowpowermode']})", '',
                  f"Pairs: {len(entry['pairs'])} of {entry['pairs_required']} required (repetitions "
                  f"{', '.join(str(p['index']) for p in entry['pairs']) or 'none'}). Unpaired: "
                  + ('; '.join(f"{u['app']} r{u['index']} {u['status']} ({u['reason']}) {u['problems'] + u['exclusions']}" for u in unpaired)
                     or 'none') + '.', '']
        for title, series, fmt in (('Component', entry['components'], us), ('Worker wait passes', entry['waits'], str)):
            if not series:
                continue
            lines += [f'| {title} | improves in every pair | worsens in any pair | spread baseline / candidate | per pair |',
                      '| --- | --- | --- | --- | --- |']
            for name, value in series.items():
                lines.append(f"| {name} | {verdicts(value, True)} | {verdicts(value, False)} | {spreads(value, fmt)} | {per_pair(value, fmt)} |")
            lines.append('')
        whole = entry['whole_request']
        if whole.get('pairs'):
            way = whole['direction']
            lines += [f"Whole request (spread baseline / candidate {spreads(whole, ms)}): improves {verdicts(whole, True)}; "
                      f"worsens {verdicts(whole, False)}; {per_pair(whole, ms)}. Candidate faster in {way['faster']}, "
                      f"slower in {way['slower']}, equal in {way['equal']} pairs.", '']
        if entry.get('pairs'):
            lines += ['| Grace waits (key 5) | sum baseline / candidate | per pair: baseline -> candidate |', '| --- | --- | --- |']
            for name, value in entry['grace'].items():
                lines.append(f"| {name} | {value['sums']['baseline']} / {value['sums']['candidate']} | " + '; '.join(
                    f"r{r['index']} absent on {'/'.join(r['absent_on'])}" if 'absent_on' in r else f"r{r['index']} {r['baseline']} -> {r['candidate']}"
                    for r in value['pairs']) + ' |')
            lines.append('')
        scan = entry.get('scan') or {}
        if scan.get('series'):
            ratio = lambda side: f"{side['count']}/{side['passes']}"
            lines += ['Inbound scan rows are exact counts per actor and caller role, count/passes per pair: lower when the baseline\'s '
                      'count is at or above its full-scan floor (n * passes - n * (n - 1) / 2), the candidate\'s is below its own and the '
                      'candidate\'s ratio is strictly below the baseline\'s; a not_lower pair names the conditions it failed. A pair whose '
                      'inbound_count differs between the sides, or whose acknowledged slots differ from the layout, is refused.', '',
                      '| Inbound scan (exact counts) | lower in every pair | per pair: baseline -> candidate (count/passes) |', '| --- | --- | --- |']
            for name, value in scan['series'].items():
                lines.append(f"| {name} | {verdict(value[SCAN_LOWER])} | " + '; '.join(
                    f"r{r['index']} absent on {'/'.join(r['absent_on'])}" if r['outcome'] == 'absent'
                    else f"r{r['index']} {ratio(r['baseline'])} -> {ratio(r['candidate'])}" + (
                        '' if r['outcome'] == 'lower' else f" ({', '.join(r['unmet'])})" if r['outcome'] == 'not_lower' else f" ({r['outcome']})")
                    for r in value['pairs']) + (f" [withheld: {value['withheld']}]" if value.get('withheld') else '') + ' |')
            for name, value in scan['zero_visit_passes'].items():
                lines.append(f"| {name} (sum baseline / candidate {value['sums']['baseline']} / {value['sums']['candidate']}) | no verdict | " + '; '.join(
                    f"r{r['index']} absent on {'/'.join(r['absent_on'])}" if 'absent_on' in r else f"r{r['index']} {r['baseline']} -> {r['candidate']}"
                    for r in value['pairs']) + ' |')
            lines.append('')
            if scan['refusals']:
                lines += ['Refused scan pairs: ' + '; '.join(
                    f"r{r['index']} w{r['actor']} {', '.join(r['problems'])} (inbound_count {r['inbound_count']['baseline']} / "
                    f"{r['inbound_count']['candidate']}; acknowledged slots {len(r['acknowledged_slots']['baseline'])} / "
                    f"{len(r['acknowledged_slots']['candidate'])})" for r in scan['refusals']) + '.', '']
        if entry['response']:
            lines += ['| Response | candidate upper | baseline lower | bound | within 2 ms | combined uncertainty | credited |',
                      '| --- | --- | --- | --- | --- | --- | --- |']
            for name, value in entry['response'].items():
                lines.append(f"| {name} | {us(value['candidate_upper_ns'])} | {us(value['baseline_lower_ns'])} | {us(value['bound_ns'])} "
                             f"| {'yes' if value['within_limit'] else 'no'} | {us(value['combined_uncertainty_ns'])} "
                             f"| {'yes' if value['credited'] else 'no'} |")
            lines.append('')
        if entry['host_sleeps']:
            lines += ['| Host sleep or bounded wait | per pair: baseline count, total -> candidate count, total |', '| --- | --- |']
            for wait, rows in entry['host_sleeps'].items():
                lines.append(f'| {wait} | ' + '; '.join(
                    f"r{r['index']} {r['baseline']['count']}, {ms(r['baseline']['sum_ns'])} -> {r['candidate']['count']}, {ms(r['candidate']['sum_ns'])}"
                    for r in rows) + ' |')
            lines.append('')
    return lines


def markdown(summary):
    gate, identity = summary['instrument_gate'], summary['fixture_identity']
    builds = '; '.join(f"{app} host {short(v['host'])}, worker {short(v['worker'])}" for app, v in identity['executables'].items()
                       if isinstance(v, dict) and 'host' in v)
    pair = identity['executables'].get('clock_pair') or {}
    lines = ['# Worker-wait pilot summary', '',
             f"Not production bytes: every measured executable is a fixture build. Reader {short(summary['reader']['sha256'])}; "
             f"staged {builds or 'identities absent'}; clock pair {short(pair.get('binary'))}; "
             f"HostStamps.swift {short(identity['executables'].get('host_stamps_source'))}"
             + (f"; receipts absent: {', '.join(identity['receipts_absent'])}" if identity['receipts_absent'] else '') + '.', '',
             f"Calibration {summary['calibration_status']}"
             + (f"; 0.5 ms instrument gate {'credited' if gate['credited'] else 'not credited ' + str(gate['reasons'])}"
                f" (busy combined uncertainty {summary.get('busy_combined_uncertainty_ns')} ns)" if gate else '')
             + f"; endpoint term {summary['endpoint_term_ns']} ns, alignment bound {summary['alignment_ns']} ns.",
             'Values are microseconds. Aggregates use accepted trials of one app, cell, regime, power source, low power mode and host flavour.',
             'Components are chained or nested, not disjoint (spawn_to_* share the spawn end; eof_to_reap overlaps eof_to_decode and decode; '
             'held_total contains the release and acknowledgement components): never add them.',
             'Uncertainty is both endpoint terms (bracket floored at the endpoint term, host endpoints also at twice the in-situ stamp cost) '
             'plus the alignment bound across processes; "below floor" counts values at or below it.',
             'Detection brackets are polling response, reported beside latencies; they are not instrument uncertainty. '
             '*_first_check_positive rows had no negative host sample, so they carry no detection bracket and are not polling response; '
             '"during sleep" counts the host sleep containing the worker stamp, taken from the 180/181 sleep event pairs (scope event) '
             'or else from a sleep register\'s last pair (single_wait, last_pair_of_multi_count, events_truncated past 64 sleeps per key); '
             '"unattributed (no containing sleep)" when none contains it, and "none" only when the host recorded no sleep between '
             'the publication and its observation.',
             'w<actor>.done_detection runs from the worker\'s TERMINAL_PUBLISHED to the host\'s first positive done sample (register 144).',
             'w<actor>.terminal_to_exit_request (TERMINAL_PUBLISHED to EXIT_REQUESTED), w<actor>.exit_request_to_reap (to the host\'s '
             'reaping sample) and w<actor>.grace_wait (WORKER_GRACE_BEGIN to WORKER_GRACE_FINISHED) are program-point intervals. '
             'Grace waits count how the worker grace waits between samples (key 5) ended: timeouts include plain sleeps and '
             'waits past the 64 recorded pairs.',
             f'A release or activation wait\'s mean pass period is {SAMPLED_PERIOD}. Exchange wait rows (pN.exchange_wait.slotS) '
             f'have no first-pass stamp: their period is an {UPPER_PERIOD}.',
             f'custody recipient_wait rows show min and max only: {RECIPIENT_NOTE}.', '',
             'Trial counts: ' + ', '.join(f'{k} {v}' for k, v in summary['counts'].items()), '']
    skipped = identity['executables'].get('host_patches_skipped')
    if skipped is not None:
        lines += ['Optional host patches skipped (patch index): ' + '; '.join(f'{app} {v or "none"}' for app, v in skipped.items()) + '.', '']
    if summary.get('pairs'):
        lines += pairs_markdown(summary['pairs'])
    for group in summary['groups']:
        lines += [f"## {group['app']} {group['cell']} {group['regime']} ({group['power_source']}, lowpowermode {group['lowpowermode']})", '',
                  f"Counts: {group['counts']}; coverage {group.get('coverage', 'not declared')}"
                  + ('; dry run, not creditable' if group['dry_run'] else ''), '',
                  f"Whole request (RunCapture): {format_stats(group['whole_request_ns'])}; "
                  f"host export span: {format_stats(group.get('export_duration_ns') or dict(n=0))}", '']
        if group.get('grace_counts'):
            lines += ['Grace waits (key 5), sum over accepted trials: ' + ', '.join(
                f"{name} {value['sum']} (max per trial {value.get('max', '-')}"
                + (f", unavailable {value['unavailable']}" if value['unavailable'] else '') + ')'
                for name, value in group['grace_counts'].items()) + '.', '']
        if group.get('scan'):
            lines += ['Inbound scan per actor, sum (median) over accepted trials: ' + '; '.join(
                f"w{actor} inbound_count {'/'.join(map(str, value['inbound_count']))}: " + ', '.join(
                    f"{name} {value[name]['sum']} ({value[name]['median']})" for name in SCAN_COUNTERS)
                for actor, value in group['scan'].items()) + '.', '']
        if group.get('envelope_ms'):
            lines += ['| Envelope field (integer ms, host clock) | n | median | min | max |', '| --- | --- | --- | --- | --- |']
            for path, value in group['envelope_ms'].items():
                lines.append(f"| {path} | {value['n']} | {value['median']} | {value['min']} | {value['max']} |")
            lines.append('')
        if group['components']:
            lines += ['| Component | n | median | min | max | max uncertainty | below floor | detection bracket max | during sleep | unobserved |',
                      '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
            for name, value in group['components'].items():
                uncertainty = us(value['max_uncertainty_ns']) if value['max_uncertainty_ns'] is not None else 'not established: ' + '/'.join(value['uncertainty_basis'])
                detection = value['detection_bracket'].get('max', value['worker_detection_bracket'].get('max'))
                label, median = name, us(value.get('median'))
                if value.get('note'):
                    label, median = f"{name} ({value['note']})", 'not reported'
                lines.append(f"| {label} | {value['n']} | {median} | {us(value.get('min'))} | {us(value.get('max'))} "
                             f"| {uncertainty} | {value.get('below_instrument_floor', '-')} | {us(detection)} "
                             f"| {sleeps(value.get('during_sleep_key'), value.get('during_sleep_scope'))} | {value['unobserved'] or ''} |")
            lines.append('')
        if group.get('waits'):
            lines += ['| Wait | passes | mean pass period | period definition | unavailable |', '| --- | --- | --- | --- | --- |']
            for name, value in group['waits'].items():
                passes = value['passes']
                count = f"n {passes['n']}, median {passes['median']}" if passes['n'] else 'none'
                definition = '; '.join('sampled' if d == SAMPLED_PERIOD else d for d in value.get('period_definition') or [])
                lines.append(f"| {name} | {count} | {format_stats(value['mean_pass_period_ns'])} | {definition} | {value['unavailable']} |")
            lines.append('')
        for row in group['non_accepted']:
            lines.append(f"- {row['status']}: {row['dir']} {row['problems'] + row['exclusions']}")
        lines.append('')
    if summary['observer_overlap']:
        lines += ['## Observer overlap per trial', ''] + [
            f"- {r['app']} {r['cell']} {r['regime']} {r['index']}: overlaps held interval {r['overlaps_held']}; {r['status']}"
            for r in summary['observer_overlap']] + ['']
    lines += ['## Excluded trials', ''] + ([f"- {r['dir']}: {r['exclusions']}" for r in summary['excluded']] or ['- none']) + ['']
    lines += ['## Not observed by this instrument', ''] + [f'- `{k}`: {v}' for k, v in summary['unobserved_intervals'].items()]
    if summary['warm']:
        lines += ['', '## Excluded first executions', ''] + [
            f"- {w['app']} {w['cell']}: {w['status']}, whole request {us((w['whole_request'] or {}).get('elapsed_ns'))}" for w in summary['warm']]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    _, summary = read_artifacts(sys.argv[1])
    print(f"worker-wait pilot reader: {summary['counts']}; calibration {summary['calibration_status']}")
