"""Controls for the worker-wait pilot reader on constructed receipts: accepted first, then each fault refused.

Establishes the reader's decoding, arithmetic and refusal rules on constructed
inputs only; no stamp, timing or live trial is credited here. Comparison
controls pair constructed baseline and candidate rows and check each verdict
and response bound, and the stager's identity rules run on a constructed app
and source tree up to, never including, signing. A2 receipts with constructed
inbound scan counters check the per-actor scan pairs: lower in every pair, a
pair not lower, a ratio that only exact arithmetic separates, identical scans
on both sides whose pass counts differ (not lower although the ratio is), and
pairs refused for differing inbound counts or for acknowledged slots that
differ from the layout. `worker_wait_pilot_constructed.py` builds the receipts.
Expected values are written from the constructed microsecond times, not
computed with the reader's functions.

Each item's stable identity is `<Group>.<function>`, followed by a label where
the function runs once per input. An item ends by calling `established`, and the
family publishes `controls.json`: the names the items established as accepted,
the refused controls with the status and codes each reported, under
`not_established` every declared name whose item did not get that far, and
under `items` what each item declares and recorded.

Collection imports neither the reader, the clock pair nor the stager and
creates nothing: each loads in the first item that asks for it, a replaced
reader or stager function returns at the item's teardown, and every temporary
tree belongs to the item that makes it.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import pytest

from worker_wait_pilot_constructed import (ACTOR_EXITS, ACTOR_POLL_NS, ALIGN, CALIBRATION, COMPLETION_LAST,
    COMPLETION_NEXT, C_STAGES, FIRST_CHECK, FLAVOUR, GRACE_OUTCOMES, GRACE_POLL_NS, HOST_FLOOR, ISSUER_PASSES, NONE,
    OFFSETS, SENTINEL_NS, SUBJECT_PASSES, WORKER_FLOOR, actor_bundle, actor_done_observed, arrival_negative_free,
    done_absent, done_negative_free, drop_sleep_begin, drop_sleep_end, drop_sleep_pair, early_arrival,
    early_observation, edit_wait_outcome, edited, first_check_positive, header, late_release_stamp,
    move_grace_finished, move_wait_outcome, neighbor_bundle, ordinary_bundle, page_fault, phase_times, scan_passes,
    sleep_end_later, sleep_pair, sleep_requested_changed, swap_fresh, tk, watch_inside_held, write_bundle,
    write_calibration)

HERE = Path(__file__).resolve().parent
HOST_STAMPS = HERE.parents[2] / 'tests/fixtures/worker_wait/host_stamps.py'
PW_SOURCE_FILES = ('tests/suites/witness_contract/worker_wait_pilot_constructed.py',
                   'tests/suites/witness_contract/worker_wait_pilot_reader.py',
                   'tests/suites/witness_contract/worker_wait_clock_pair.py',
                   'tests/fixtures/worker_wait/host_stamps.py',
                   'tests/fixtures/caller_auth/bundle.py',
                   'tests/lib/artifact.py')

SCOPE = 'constructed reader sensitivity; no live stamps or timings credited'
# What each item establishes in controls.json, keyed by its identity. Filled while this module is imported.
CONTROLS = {}


def accepts(*names):
    """The item establishes these names as accepted."""
    return dict(accepted=list(names), rejected=[])


def rejects(*names):
    """The item establishes these controls as refused, and reports the status and codes it observed."""
    return dict(accepted=[], rejected=list(names))


def control(group, account=accepts(), commands='none'):
    """Give a function its identity, `group.function`, its controls.json names and its command scope."""
    def mark(function):
        identity = f'{group}.{function.__name__}'
        CONTROLS[identity] = account
        function = pytest.mark.pw_commands(commands)(function)
        return pytest.mark.pw_id(identity)(function)
    return mark


def inputs(group, names, rows, account=accepts(), commands='none'):
    """Run a function once per `(label, value...)` row; `group.function.label` identifies each run.

    account is what every row establishes, or a function from a row's label to what that row establishes."""
    def mark(function):
        identity = f'{group}.{function.__name__}'
        cases = []
        for label, *values in rows:
            CONTROLS[f'{identity}.{label}'] = account(label) if callable(account) else account
            cases.append(pytest.param(*values, id=label, marks=pytest.mark.pw_id(f'{identity}.{label}')))
        function = pytest.mark.pw_commands(commands)(function)
        return pytest.mark.parametrize(names, cases)(function)
    return mark


def controls_document(established):
    """The family's account of its controls.

    A name is accepted or rejected only when every item that declares it established it; otherwise it is
    listed under not_established with the items that did not. A name belongs to the group of its items:
    `origin_mismatch` is one refused control among the order rules and another among the constructed faults."""
    declaring = {}
    for identity, declared in CONTROLS.items():
        for kind in ('accepted', 'rejected'):
            for name in declared[kind]:
                declaring.setdefault((identity.split('.')[0], kind, name), []).append(identity)
    document = dict(scope=SCOPE, accepted=[], rejected=[], not_established=[])
    for (_, kind, name), identities in declaring.items():
        missing = [identity for identity in identities if identity not in established]
        if missing:
            document['not_established'].append(dict(name=name, declared_as=kind, items=missing))
        elif kind == 'accepted':
            document['accepted'].append(name)
        else:
            reports = {(established[identity]['status'], tuple(established[identity]['codes'])) for identity in identities}
            assert len(reports) == 1, f'{name}: its items report different refusals: {sorted(reports)}'
            (status, codes), = reports
            document['rejected'].append(dict(control=name, status=status, codes=list(codes)))
    document['items'] = {identity: dict(declared, established=identity in established, **established.get(identity, {}))
                         for identity, declared in CONTROLS.items()}
    return document


@pytest.fixture(scope='session')
def account(request, pw_equipment):
    """Collect what the items establish and publish controls.json after the last item, whatever failed.

    A failing item leaves its names under not_established. Pytest reports this teardown with the last item;
    it fails there only when no item failed and an item that started still did not record its control."""
    started, established = [], {}
    yield started, established
    pw_equipment.publish('controls.json', controls_document(established))
    silent = [identity for identity in started if identity not in established]
    if silent and not request.session.testsfailed:
        error = 'items passed without recording their controls: ' + ', '.join(silent)
        pw_equipment.publish('session-finalizer.json', dict(fixture='account', scope='all family items',
                                                            attached_to='last item teardown', kind='account', error=error))
        raise AssertionError(error)


@pytest.fixture
def established(request, account):
    """Record that this item's control held: called last, after the item's assertions.

    An item that declares a refused control passes the status and the codes it observed."""
    identity = request.node.get_closest_marker('pw_id').args[0]
    started, established = account
    started.append(identity)

    def record(status=None, codes=None):
        refused = bool(CONTROLS[identity]['rejected'])
        if refused != (status is not None and codes is not None):
            raise ValueError(f'{identity}: a refused control records its status and codes, any other control neither')
        established[identity] = dict(status=status, codes=codes) if refused else {}
    return record


@pytest.fixture(scope='session')
def reader():
    """The pilot reader under test, imported by the first item that asks for it."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import worker_wait_pilot_reader
    return worker_wait_pilot_reader


@pytest.fixture(scope='session')
def clock_pair(reader):
    """The clock-pair module, whose constructed calibration receipt the disk trees carry; it follows `reader` on the path."""
    import worker_wait_clock_pair
    return worker_wait_clock_pair


@pytest.fixture(scope='session')
def stamps():
    """The stager, loaded from the fixture's file."""
    spec = importlib.util.spec_from_file_location('worker_wait_host_stamps', HOST_STAMPS)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.fixture
def replace(monkeypatch):
    """Replace an attribute of the reader or the stager for this item only.

    The originals return at teardown whether the item passed or failed, and this fixture checks that they
    did, so a replacement cannot reach a later item."""
    originals = []

    def apply(owner, name, value):
        originals.append((owner, name, getattr(owner, name)))
        monkeypatch.setattr(owner, name, value)

    yield apply
    monkeypatch.undo()
    for owner, name, original in originals:
        assert getattr(owner, name) is original, f'{owner.__name__}.{name} was not restored'


@pytest.fixture
def temporary(pw_inputs):
    """Make temporary directories that this item owns.

    The caller registers a directory with `pw_inputs.track` once its starting content is in place and
    before changing it. Teardown captures every registered tree that still exists, then removes the
    directories, newest first. A capture or removal error fails the item's teardown."""
    owned = []

    def make(prefix):
        directory = tempfile.TemporaryDirectory(prefix=prefix)
        owned.append(directory)
        return Path(directory.name)

    yield make
    errors = []
    try:
        pw_inputs.capture_tracked('before cleanup')
    except Exception as error:
        errors.append(error)
    for directory in reversed(owned):
        try:
            directory.cleanup()
        except Exception as error:
            errors.append(error)
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise ExceptionGroup('temporary directories were not captured and removed', errors)


def codes(row):
    return set(row['problems']) | set(row['exclusions'])


def endpoint(process, stamp, bracket_from, bracket_ns):
    return dict(process=process, stamp=stamp, bracket_from=bracket_from, bracket_ns=bracket_ns)


# ---- layout and worker event order ----------------------------------------------------

@control('Layout')
def test_reader_offsets_are_the_c_layout(reader, established):
    assert {k: reader.LAYOUT[k] for k in OFFSETS} == OFFSETS, reader.LAYOUT
    established()


@control('Layout')
def test_reader_stages_follow_the_c_order(reader, established):
    assert list(reader.STAGES) == C_STAGES
    established()


def event(code, raw):
    return dict(event=code, phase=0, aux=0, raw=raw)


@control('OrderRules', accepts('sampled_inversion_accepted'))
def test_a_pass_sample_appended_after_a_later_read_is_accepted(reader, established):
    sampled_after_later_read = [event(1, 10), event(9, 50), event(10, 60), event(6, 50), event(6, 70), event(7, 71)]
    assert reader.worker_order_problems(sampled_after_later_read, 10) == set()
    established()


@inputs('OrderRules', 'name, events, expected', [(name, name, events, expected) for name, events, expected in (
        ('fresh_backwards', [event(1, 10), event(3, 60), event(10, 50)], {'worker_events_non_monotonic'}),
        ('sample_after_next_read', [event(1, 10), event(6, 80), event(7, 70)], {'worker_events_non_monotonic'}),
        ('sample_backwards', [event(1, 10), event(6, 70), event(6, 60), event(7, 90)], {'worker_events_non_monotonic'}),
        ('origin_mismatch', [event(1, 11), event(3, 20)], {'worker_origin_mismatch'}))], lambda label: rejects(label))
def test_a_fresh_read_out_of_order_or_off_its_origin_is_refused(reader, established, name, events, expected):
    assert reader.worker_order_problems(events, 10) == expected
    established(status='rejected', codes=[name])


# ---- complete receipts ----------------------------------------------------------------

def check_detection_total(reader, row):
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


def check_ordinary(reader, row):
    check_detection_total(reader, row)
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


def check_actor(reader, row):
    check_detection_total(reader, row)
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
        # The inbound-delivery response spans the wait start to the acknowledgement: the two parts above.
        assert t['inbound_response']['ns'] == 5_000 + 15_000, t['inbound_response']
        assert t['inbound_response']['endpoints'][0] == endpoint('host', 'inbound_committed', 'custody_service_start_to_wait_start', 10_000), t['inbound_response']
        assert t['inbound_response']['endpoints'][1]['stamp'] == 'inbound_acknowledged', t['inbound_response']
    assert transfers[0]['inbound_ack_to_host_observed']['detection_bracket_ns'] == 985_000 and 'inbound_ack_first_check_positive' not in transfers[0]
    observed = transfers[1]['inbound_ack_first_check_positive']
    assert (observed['during_sleep_key'], observed['during_sleep_scope'], observed['during_sleep_span']) == (
        '6', 'event', dict(ordinal=1, duration_ns=980_000, requested_ns=ACTOR_POLL_NS, stamp_after_begin_ns=4_000)), observed
    assert 'inbound_ack_to_host_observed' not in transfers[1]
    subject = row['worker_waits']['1']
    assert subject['release']['mean_pass_period_ns'] is None and subject['scan']['visits_per_pass_activation'] == 1.25
    assert subject['scan']['role_unknown_passes_uncounted'] is False
    assert row['clock_order']['inversions'] == 0


@control('Receipts', accepts('instrumented O1'))
def test_the_ordinary_receipt(reader, established):
    check_ordinary(reader, reader.evaluate_bundle(ordinary_bundle(), CALIBRATION))
    established()


@control('Receipts', accepts('instrumented A2'))
def test_the_actor_receipt(reader, established):
    check_actor(reader, reader.evaluate_bundle(actor_bundle(), CALIBRATION))
    established()


@control('Receipts', accepts('neighbor O1'))
def test_the_neighbor_receipt(reader, established):
    assert reader.evaluate_bundle(neighbor_bundle(), CALIBRATION)['status'] == 'accepted'
    established()


# ---- exit intervals and grace waits ---------------------------------------------------

def check_actor_intervals(reader, row, grace=None):
    """w0: TERMINAL_PUBLISHED (9.5 ms) to EXIT_REQUESTED (11.51 ms), that to WORKER_REAPED (11.6 ms), and the grace
    from 11.52 to 11.61 ms when stamped. Program points: worker floor 300, host max(300, 2 x 500), alignment 100."""
    (actor,) = row['actors']
    assert actor['actor'] == 0 and set(actor) == {'actor', 'terminal_to_exit_request', 'exit_request_to_reap', 'grace_wait',
                                                  'grace_stop_code', 'terminal_to_reap', 'terminal_to_teardown',
                                                  'spawn_to_teardown', 'spawn_to_ready_observed',
                                                  'ready_observed_to_applied_stamp',
                                                  'applied_stamp_to_first_arrival_stamp'}, actor
    assert actor['spawn_to_ready_observed']['ns'] == 2_000_000
    assert actor['ready_observed_to_applied_stamp']['ns'] == 800_000
    assert actor['applied_stamp_to_first_arrival_stamp']['ns'] == 1_200_000
    values = lambda name: (actor[name]['ns'], actor[name]['uncertainty_ns'], actor[name]['cross_process'])
    assert values('terminal_to_exit_request') == (2_010_000, WORKER_FLOOR + HOST_FLOOR + ALIGN, True), actor
    assert actor['terminal_to_exit_request']['endpoints'] == [endpoint('worker0', 'terminal_published', None, 0),
                                                              endpoint('host', 'exit_requested', None, 0)]
    assert values('exit_request_to_reap') == (90_000, 2 * HOST_FLOOR, False), actor
    assert values('terminal_to_reap') == (2_100_000, 100_000 + HOST_FLOOR + ALIGN, True), actor
    assert actor['terminal_to_teardown'] == dict(ns=None, unobserved='terminal_or_teardown_unobserved')
    assert actor['spawn_to_teardown'] == dict(ns=None, unobserved='spawn_or_teardown_unobserved')
    if grace is None:
        assert actor['grace_wait'] == dict(ns=None, unobserved='grace_not_stamped') and actor['grace_stop_code'] is None, actor
    else:
        assert values('grace_wait') == (90_000, 2 * HOST_FLOOR, False) and actor['grace_stop_code'] == 1, actor
        assert actor['grace_wait']['endpoints'] == [endpoint('host', 'worker_grace_begin', None, 0),
                                                    endpoint('host', 'worker_grace_finished', None, 0)]
    names = {name for name, _ in reader.component_values(row)}
    assert {'w0.terminal_to_exit_request', 'w0.exit_request_to_reap', 'w0.grace_wait'} <= names, names


def check_actor_exits(reader, row, plain):
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
    exit_names = {f'w{a}.{n}' for a in ACTOR_EXITS for n in ('terminal_to_exit_request', 'exit_request_to_reap', 'grace_wait', 'terminal_to_reap')}
    others = lambda r: {name: record['ns'] for name, record in reader.component_values(r) if name not in exit_names}
    assert exit_names <= {name for name, _ in reader.component_values(row)}
    assert others(row) == others(plain), {k: (v, others(plain).get(k)) for k, v in others(row).items() if v != others(plain).get(k)}


def check_grace(reader, row, grace):
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
    check_actor_intervals(reader, row, grace)


@control('Grace', accepts('O1 per-actor exit intervals without grace stamps'))
def test_ordinary_exit_intervals_without_grace_stamps(reader, established):
    check_actor_intervals(reader, reader.evaluate_bundle(ordinary_bundle(), CALIBRATION))
    established()


@control('Grace')
def test_an_ordinary_receipt_without_grace_waits_counts_none(reader, established):
    assert tuple(reader.evaluate_bundle(ordinary_bundle(), CALIBRATION)[n] for n in reader.GRACE_COUNTS) == (0, 0, 0, 0)
    established()


@inputs('Grace', 'grace', [(grace, grace) for grace in GRACE_OUTCOMES],
        lambda label: accepts(f'O1 candidate-shaped grace wait: {label}'))
def test_one_grace_wait_is_counted_by_how_it_ended(reader, established, grace):
    check_grace(reader, reader.evaluate_bundle(ordinary_bundle(grace=grace), CALIBRATION), grace)
    established()


@control('Grace', accepts('grace counts summed per group'))
def test_grace_counts_are_summed_per_group(reader, established):
    graced = {grace: reader.evaluate_bundle(ordinary_bundle(grace=grace), CALIBRATION) for grace in ('notified', 'plain', 'unusable')}
    # Group sums over the accepted trials of one group.
    (group,) = reader.summarize([graced['notified'], graced['plain'], graced['unusable']])
    assert {name: (value['sum'], value['n'], value['max']) for name, value in group['grace_counts'].items()} == dict(
        grace_timeouts=(1, 3, 1), grace_notified=(1, 3, 1), grace_unusable=(1, 3, 1), grace_settle_sleeps=(0, 3, 0)), group['grace_counts']
    assert group['components']['w0.grace_wait']['n'] == 3 and group['components']['w0.exit_request_to_reap']['median'] == 90_000
    established()


@control('Grace', accepts('A2 without exit requests: per-actor intervals unobserved'))
def test_actor_exit_intervals_are_unobserved_without_exit_requests(reader, established):
    actor_row = reader.evaluate_bundle(actor_bundle(), CALIBRATION)
    assert [(a['actor'], a['terminal_to_exit_request']['unobserved'], a['exit_request_to_reap']['unobserved']) for a in actor_row['actors']] == [
        (0, 'terminal_or_exit_request_unobserved', 'exit_request_or_reap_unobserved'),
        (1, 'terminal_or_exit_request_unobserved', 'exit_request_or_reap_unobserved')], actor_row['actors']
    established()


@control('Grace', accepts('A2 candidate-shaped cleanup: each actor its own exit intervals, grace stop and one bounded wait'))
def test_each_actor_has_its_own_exit_intervals_stop_and_wait(reader, established):
    check_actor_exits(reader, reader.evaluate_bundle(actor_bundle(exits=True), CALIBRATION),
                      reader.evaluate_bundle(actor_bundle(), CALIBRATION))
    established()


def grace_export(waits, count):
    """A minimal host export: each wait is a key-5 sleep pair with the requested duration, followed by its outcome if any."""
    events, raw = [], 0
    for requested, outcome in waits:
        events += [[180, 5, requested, raw], [181, 5, requested, raw + 10]] + ([] if outcome is None else [[182, 5, outcome, raw + 10]])
        raw += 100
    return dict(events=events, sleeps={'5': dict(count=count)})


@control('Grace', accepts('grace waits past 64 recorded pairs counted as timeouts'))
def test_grace_waits_past_the_recorded_pairs_are_timeouts(reader, established):
    truncated = reader.grace_counts(grace_export([(GRACE_POLL_NS, 1)] * 64, 70))
    assert (truncated['grace_timeouts'], truncated['grace_notified'], truncated['grace_unusable']) == (6, 64, 0), truncated
    assert (truncated['grace_wait_record']['recorded_pairs'], truncated['grace_wait_record']['unrecorded']) == (64, 6), truncated
    established()


SETTLE_SLEEPS = 'settle and poll sleeps without an outcome counted as timeouts by requested ns'


@control('Grace', accepts(SETTLE_SLEEPS))
def test_settle_sleeps_are_counted_apart_from_timeouts(reader, established):
    # A notified wait, two 100 us settle sleeps and one 10 ms sleep: the settle sleeps are counted apart and only
    # the 10 ms plain sleep is a timeout; a plain sleep just over the settle bound is a timeout.
    settled = reader.grace_counts(grace_export([(GRACE_POLL_NS, 1), (100_000, None), (100_000, None), (GRACE_POLL_NS, None)], 4))
    assert (settled['grace_timeouts'], settled['grace_notified'], settled['grace_settle_sleeps']) == (1, 1, 2), settled
    assert settled['grace_wait_record']['plain_sleeps_by_requested_ns'] == {'100000': 2, '10000000': 1}, settled
    assert settled['grace_wait_record']['settle_sleeps'] == 2, settled
    established()


@control('Grace', accepts(SETTLE_SLEEPS))
def test_a_plain_sleep_just_over_the_settle_bound_is_a_timeout(reader, established):
    over = reader.grace_counts(grace_export([(100_001, None)], 1))
    assert (over['grace_timeouts'], over['grace_settle_sleeps']) == (1, 0), over
    established()


@control('Grace', accepts(SETTLE_SLEEPS))
def test_no_grace_wait_counts_no_timeout(reader, established):
    assert reader.grace_counts(grace_export([], 0))['grace_timeouts'] == 0
    established()


@inputs('Grace', 'events, expected', [
    ('outcome-after-its-pair', [[180, 5, 1, 0], [181, 5, 1, 10], [182, 5, 2, 10]], set()),
    ('outcome-code-3', [[180, 5, 1, 0], [181, 5, 1, 10], [182, 5, 3, 10]], {'host_wait_outcome_invalid'}),
    ('outcome-without-a-pair', [[182, 5, 1, 10]], {'host_wait_outcome_unpaired'}),
    ('grace-begin-then-finished', [[148, 1, 0, 10], [157, 1, 1, 10]], set()),
    ('grace-finished-before-begin', [[157, 1, 1, 10], [148, 1, 0, 10]], {'host_grace_interval_reversed'}),
], accepts('outcome and grace order rules on minimal exports'))
def test_wait_outcome_and_grace_order_rules(reader, established, events, expected):
    assert reader.wait_outcome_problems(events) == expected
    established()


# ---- final waits, teardown intervals and resampling -----------------------------------

FINAL_WAITS = 'final-only wait outcomes and zero waits distinguished from incomplete suffixes'


def final_waits():
    """Two ordinary phases: one sentinel sleep before each release, then four after the last release, one per
    way a wait can end, before the exit request."""
    layout = dict(form='ordinary', phases=[{}, {}])
    events = [[180, 1, 2000000, 10], [181, 1, 2000000, 20], [141, 0, 1, 30],
              [180, 1, 2000000, 40], [181, 1, 2000000, 50], [141, 1, 2, 60]]
    for i, outcome in enumerate((None, 0, 1, 2)):
        t = 70 + 20 * i
        events += [[180, 1, 2000000, t], [181, 1, 2000000, t + 10]]
        if outcome is not None:
            events.append([182, 1, outcome, t + 10])
    events.append([146, 0, 0, 200])
    doc = dict(events=events, sleeps={'1': dict(count=6)})
    return doc, layout


@control('FinalWait', accepts(FINAL_WAITS))
def test_final_waits_are_counted_by_how_they_ended(reader, established):
    doc, layout = final_waits()
    assert reader.final_wait_record(doc, layout) == dict(state='complete', waits=4, plain_sleep=1, timed_out=1, notified=1, unusable=1)
    established()


@control('FinalWait', accepts(FINAL_WAITS))
def test_no_wait_after_the_last_release_is_a_complete_zero(reader, established):
    doc, layout = final_waits()
    events = doc['events']
    before = dict(events=events[:6] + [[146, 0, 0, 200]], sleeps={'1': dict(count=2)})
    assert reader.final_wait_record(before, layout) == dict(state='complete', waits=0, plain_sleep=0, timed_out=0, notified=0, unusable=0)
    established()


@inputs('FinalWait', 'edit', [
    ('exit-request-missing', lambda missing: missing.update(events=[e for e in missing['events'] if e[0] != 146])),
    ('last-release-missing', lambda missing: missing.update(events=[e for e in missing['events'] if not (e[0] == 141 and e[1] == 1)])),
    ('sleep-pair-missing', lambda missing: missing['events'].__delitem__(slice(6, 8))),
    ('sleeps-past-the-recorded-pairs', lambda missing: missing['sleeps']['1'].update(count=65)),
    ('sleep-begins-before-the-last-release', lambda missing: missing['events'][6].__setitem__(3, 59)),
    ('outcome-code-3', lambda missing: next(e for e in missing['events'] if e[0] == 182).__setitem__(2, 3)),
], accepts(FINAL_WAITS))
def test_an_incomplete_final_suffix_is_unobserved(reader, established, edit):
    missing, layout = final_waits()
    edit(missing)
    assert reader.final_wait_record(missing, layout)['state'] == 'unobserved'
    established()


@control('FinalWait', accepts(FINAL_WAITS))
def test_an_actor_form_has_no_final_wait_record(reader, established):
    doc, layout = final_waits()
    assert reader.final_wait_record(doc, dict(form='actors')) == dict(state='not_applicable')
    established()


@control('FinalWait', accepts('terminal-to-reap and teardown intervals retain publication brackets and independent endpoints'))
def test_terminal_intervals_keep_the_publication_bracket(reader, established):
    # Direct terminal-to-reap carries the publication bracket, not the sum of other intervals.
    base = ordinary_bundle()
    end = [172, 0, 0, tk(10_000_000 + 11700)]
    at = next(i for i, e in enumerate(base['stamps']['events']) if e[3] > end[3])
    base['stamps']['events'].insert(at, end)
    row = reader.evaluate_bundle(base, CALIBRATION)
    assert row['status'] == 'accepted', row['problems']
    actor = row['actors'][0]
    assert (actor['terminal_to_teardown']['ns'], actor['terminal_to_teardown']['uncertainty_ns']) == (2_200_000, 101_100)
    spawn = next(e[3] for e in base['stamps']['events'] if e[0] == 101)
    assert actor['spawn_to_teardown']['ns'] == (end[3] - spawn) * 125 // 3
    assert actor['spawn_to_teardown']['uncertainty_ns'] == 2000
    established()


def resampling_export():
    """One resampling pair before a sentinel sleep and one after it."""
    doc = dict(resampling_measured=True, dropped=dict(events=0), events=[
        [183, 1, 0, 1000], [184, 1, 0, 3000],
        [180, 1, 2000, 3001], [181, 1, 2000, 6000],
        [183, 1, 0, 9000], [184, 1, 0, 9500]])
    return doc


@control('Resampling', accepts('initial_resampling_elapsed_not_sleep_or_cpu'))
def test_resampling_before_the_first_arrival_is_elapsed_time(reader, established):
    interval, doc = reader.Interval((1, 1), CALIBRATION, 0), resampling_export()
    result = reader.initial_resampling(doc, 7000, interval)
    assert result['count'] == 1 and result['ns'] == 2000 and result['uncertainty_ns'] == 600
    established()


@inputs('Resampling', 'export, arrival, expected', [
    ('measured-without-events', lambda doc: dict(resampling_measured=True, events=[], dropped=dict(events=0)), 7000, 0),
    ('not-measured', lambda doc: dict(events=[]), 7000, None),
    ('no-first-arrival', lambda doc: doc, None, None),
    ('first-arrival-before-the-pair-ends', lambda doc: doc, 2000, None),
    ('dropped-host-events', lambda doc: dict(doc, dropped=dict(events=1)), 7000, None),
], accepts('initial_resampling_missing_not_zero'))
def test_unobserved_resampling_is_not_zero(reader, established, export, arrival, expected):
    interval = reader.Interval((1, 1), CALIBRATION, 0)
    found = reader.initial_resampling(export(resampling_export()), arrival, interval)['ns']
    assert found == expected and (found is None) == (expected is None), found
    established()


MALFORMED_RESAMPLING = 'initial_resampling_malformed_pairs_rejected'


@inputs('Resampling', 'events', [
    ('begin-without-end', [[183, 1, 0, 1000]]),
    ('end-without-begin', [[184, 1, 0, 3000]]),
    ('end-before-begin', [[183, 1, 0, 3000], [184, 1, 0, 1000]]),
    ('end-under-another-key', [[183, 1, 0, 1000], [184, 2, 0, 3000]]),
    ('two-begins', [[183, 1, 0, 1000], [183, 1, 0, 1100], [184, 1, 0, 3000]]),
    ('begin-with-an-aux', [[183, 1, 1, 1000], [184, 1, 0, 3000]]),
], accepts(MALFORMED_RESAMPLING))
def test_a_malformed_resampling_pair_is_refused(reader, established, events):
    interval = reader.Interval((1, 1), CALIBRATION, 0)
    bad = dict(resampling_export(), events=events)
    assert reader.resampling_pairs(bad)[1]
    assert reader.initial_resampling(bad, 7000, interval)['ns'] is None
    established()


@control('Resampling', accepts(MALFORMED_RESAMPLING))
def test_resampling_pairs_without_capture_are_named(reader, established):
    doc = resampling_export()
    assert reader.resampling_pairs(dict(doc, resampling_measured=False))[1] == ['resampling_without_capture']
    established()


@control('Resampling', accepts('startup_program_points_distinct'))
def test_startup_program_points_are_distinct(reader, established):
    interval = reader.Interval((1, 1), CALIBRATION, 0)
    # Startup fields name post-store program points, not an application instant.
    startup = reader.actor_intervals(dict(events=[[101, 0, 0, 1000], [102, 0, 0, 2000]]),
        {0: dict(timebase=(1, 1), events=[dict(event=2, phase=NONE, aux=0, raw=2500),
                                       dict(event=3, phase=0, aux=0, raw=2600)])}, interval)[0]
    assert startup['spawn_to_ready_observed']['ns'] == 1000
    assert startup['ready_observed_to_applied_stamp']['ns'] == 500
    assert startup['applied_stamp_to_first_arrival_stamp']['ns'] == 100
    established()


# ---- receipts without the later records -----------------------------------------------

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


def check_without_sleep_events(reader, row, full):
    """The dry-run-05 shape: no 180/181 pairs; every interval keeps its value and attribution uses the registers."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    assert row['host_sleep_events'] == dict(state='absent', attribution='sleep registers only')
    values = lambda r: {name: record['ns'] for name, record in reader.component_values(r)}
    assert values(row) == values(full), {k: (v, values(full).get(k)) for k, v in values(row).items() if v != values(full).get(k)}


@control('Historical', accepts('O1 without pass-count, store-begin, stamp-cost or sleep event records'))
def test_ordinary_without_pass_store_cost_or_sleep_records(reader, established):
    check_ordinary_without_new_records(reader.evaluate_bundle(ordinary_bundle(keep=False), CALIBRATION))
    established()


@control('Historical', accepts('A2 without pass-count, store-begin, stamp-cost or sleep event records'))
def test_actor_without_pass_store_cost_or_sleep_records(reader, established):
    check_actor_without_new_records(reader.evaluate_bundle(actor_bundle(keep=False), CALIBRATION))
    established()


@inputs('Historical', 'build', [('O1', ordinary_bundle), ('A2', actor_bundle)],
        lambda label: accepts({'O1': 'O1 without sleep event records', 'A2': 'A2 without sleep event records'}[label]))
def test_without_sleep_events_every_interval_keeps_its_value(reader, established, build):
    check_without_sleep_events(reader, reader.evaluate_bundle(build(sleep_events=False), CALIBRATION),
                               reader.evaluate_bundle(build(), CALIBRATION))
    established()


# ---- first checks already positive, done observations and a counted inversion ----------

def check_first_check_positive(reader, row, sleep_key, scope, span=None):
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


def check_actor_done(row):
    """An actor-form host that also samples the subject's done flag: done_detection for that worker only."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    (done,) = row['done']
    record = done['done_detection']
    assert done['actor'] == 1 and (record['ns'], record['detection_bracket_ns'], record['uncertainty_ns']) == (
        60_000, 110_000, 100_000 + HOST_FLOOR + ALIGN), done
    assert record['endpoints'][0] == endpoint('worker1', 'terminal_published', 'attempt_published', 100_000)


def check_inversion(row):
    """A 20 us release inversion is counted, kept, and widens the alignment of every cross-process interval."""
    assert row['status'] == 'accepted' and not row['problems'], row['problems']
    assert (row['clock_order']['inversions'], row['clock_order']['max_inversion_ns']) == (1, 20_000), row['clock_order']
    (phase,) = row['phases']
    assert phase['release_to_ack']['ns'] == -20_000 and phase['release_to_ack']['uncertainty_ns'] == 28_000 + 1000 + 20_000
    assert phase['release_to_ack']['uncertainty_basis'] == 'calibrated (alignment_widened_by_inversion)'
    assert phase['arrival_detection']['uncertainty_ns'] == 1_200_000 + HOST_FLOOR + 20_000
    assert phase['held_total']['uncertainty_ns'] == 1_200_000 + 1000 and phase['held_total']['uncertainty_basis'] == 'calibrated'


# Without sleep events, attribution falls back to the registers; a multi-count register retains only its last pair.
registers_only = lambda: ordinary_bundle(sleep_events=False)
FIRST_CHECKS = {
    'inside-a-single-sleep-register': 'O1 arrival first check positive inside a single sentinel sleep register',
    'register-spanning-two-waits': 'O1 arrival first check positive, containing sleep register spans two waits',
    'inside-a-sleep-event-pair': 'O1 arrival first check positive inside a sleep event pair',
}


@inputs('FirstCheck', 'build, edit, scope, span', [
    ('inside-a-single-sleep-register', registers_only, first_check_positive(1), 'single_wait', None),
    ('register-spanning-two-waits', registers_only, first_check_positive(2), 'last_pair_of_multi_count', None),
    # With sleep events, the exact sleep: the first sentinel sleep (4.31-6.46 ms) contains the arrival at 5.0 ms.
    ('inside-a-sleep-event-pair', ordinary_bundle, arrival_negative_free, 'event', (0, 2_150_000, SENTINEL_NS, 690_000)),
], lambda label: accepts(FIRST_CHECKS[label]))
def test_an_arrival_first_check_positive_is_attributed_to_its_sleep(reader, established, build, edit, scope, span):
    check_first_check_positive(reader, reader.evaluate_bundle(edited(build, edit), CALIBRATION), '1', scope, span)
    established()


@control('FirstCheck', accepts('O1 arrival first check positive before any sleep: unattributed'))
def test_an_arrival_before_any_sleep_is_unattributed(reader, established):
    check_unattributed(reader.evaluate_bundle(edited(lambda: ordinary_bundle(worker_edit=early_arrival), arrival_negative_free), CALIBRATION))
    established()


@control('FirstCheck', accepts('O1 done first check positive inside a sleep event pair'))
def test_a_done_first_check_positive_is_attributed_to_its_sleep(reader, established):
    check_done_first_check_positive(reader.evaluate_bundle(edited(ordinary_bundle, done_negative_free), CALIBRATION))
    established()


@control('FirstCheck', accepts('O1 done register absent: unobserved label'))
def test_an_absent_done_register_is_labelled_unobserved(reader, established):
    check_done_unobserved(reader.evaluate_bundle(edited(ordinary_bundle, done_absent), CALIBRATION))
    established()


@control('FirstCheck', accepts('A2 with a done register for the subject'))
def test_an_actor_done_register_belongs_to_its_worker(reader, established):
    check_actor_done(reader.evaluate_bundle(edited(actor_bundle, actor_done_observed), CALIBRATION))
    established()


@control('FirstCheck', accepts('O1 20 us release inversion widening alignment'))
def test_a_counted_release_inversion_widens_alignment(reader, established):
    check_inversion(reader.evaluate_bundle(edited(ordinary_bundle, late_release_stamp), CALIBRATION))
    established()


# ---- sleep pairing, register agreement and attribution on minimal host exports ---------

def sleep_export(pairs, registers):
    """A minimal host export at timebase 1/1 (ticks = ns): sleep event pairs and per-key registers."""
    events = []
    for key, begin, end in pairs:
        events += [[180, key, 1000, begin], [181, key, 1000, end]]
    return dict(events=events, timebase=dict(numer=1, denom=1),
                sleeps={str(k): dict(count=c, last_pre=pre, last_post=post, last_requested_ns=1000, requested_sum_ns=1000 * c,
                                     sum_ticks=ticks, sum_ns=ticks, max_ns=0, min_ticks=0)
                        for k, (c, pre, post, ticks) in registers.items()})


def attribute(reader, doc, raw, until):
    found = reader.sleep_attribution(doc, reader.sleep_record(doc['events']), raw, until)
    return found['during_sleep_key'], found['during_sleep_scope']


# Key 7 slept 70 times: 64 recorded pairs of 10 ns at 1000 ns spacing, then 6 sleeps ending with 70000-70010.
RECORDED = [(7, 1000 * i, 1000 * i + 10) for i in range(64)]
TRUNCATED = (RECORDED, {7: (70, 70_000, 70_010, 700)})
COMPLETE = ([(1, 100, 200), (1, 300, 400)], {1: (2, 300, 400, 200)})
REGISTERS = ([], {1: (1, 100, 200, 100), 2: (2, 150, 250, 150)})
TRUNCATED_EVENTS = 'sleep events truncated past 64 per key accepted and attributed'
EVENTS_BETWEEN = 'sleep events between publication and observation unattributed'
REGISTER_ONLY = 'register-only sleep attribution and no-sleep-between rule'
FORMATTING = 'tiny negative and attribution label formatting'
ATTRIBUTIONS = {
    TRUNCATED_EVENTS: [
        ('truncated-inside-a-recorded-pair', TRUNCATED, 5, 50, ('7', 'event')),
        ('truncated-inside-the-register-pair', TRUNCATED, 70_005, 70_100, ('7', 'events_truncated')),
        # Unrecorded sleeps may lie anywhere between the last pair and the register's last pre read.
        ('truncated-among-unrecorded-sleeps', TRUNCATED, 64_500, 64_600, (None, 'unattributed')),
        # With one unrecorded sleep the register pair is that sleep, so the window is known to hold none.
        ('truncated-by-one-sleep', (RECORDED, {7: (65, 70_000, 70_010, 650)}), 64_500, 64_600, (None, 'no_sleep_between')),
    ],
    # Complete pairs: a recorded sleep between publication and observation leaves it unattributed.
    EVENTS_BETWEEN: [
        ('complete-inside-a-pair', COMPLETE, 150, 450, ('1', 'event')),
        ('complete-sleep-between', COMPLETE, 250, 450, (None, 'unattributed')),
        ('complete-no-sleep-between', COMPLETE, 410, 450, (None, 'no_sleep_between')),
    ],
    # Registers alone: single-wait keys first, then a multi-count key's last pair; an earlier sleep of a
    # multi-count key could lie anywhere before its last pair.
    REGISTER_ONLY: [
        ('registers-single-wait', REGISTERS, 160, 300, ('1', 'single_wait')),
        ('registers-last-pair-of-a-multi-count-key', REGISTERS, 220, 300, ('2', 'last_pair_of_multi_count')),
        ('registers-single-wait-later', ([], {1: (1, 400, 500, 100)}), 250, 300, (None, 'no_sleep_between')),
        ('registers-multi-count-later', ([], {1: (2, 400, 500, 100)}), 250, 300, (None, 'unattributed')),
        ('registers-none', ([], {}), 250, 300, (None, 'no_sleep_between')),
    ],
}


@inputs('SleepRules', 'export, raw, until, expected', [row for rows in ATTRIBUTIONS.values() for row in rows],
        lambda label: accepts(next(name for name, rows in ATTRIBUTIONS.items() if any(row[0] == label for row in rows))))
def test_a_window_is_attributed_to_the_sleep_that_contains_it(reader, established, export, raw, until, expected):
    assert attribute(reader, sleep_export(*export), raw, until) == expected
    established()


@control('SleepRules', accepts(TRUNCATED_EVENTS))
def test_sleep_events_truncated_past_64_pairs_agree_with_their_register(reader, established):
    truncated = sleep_export(*TRUNCATED)
    assert reader.sleep_event_problems(truncated) == set()
    assert reader.sleep_event_state(truncated, reader.sleep_record(truncated['events']))['truncated_keys'] == ['7']
    established()


@control('SleepRules', accepts(TRUNCATED_EVENTS))
def test_a_recorded_pair_beyond_the_64_is_a_count_mismatch(reader, established):
    assert reader.sleep_event_problems(sleep_export(RECORDED + [(7, 64_000, 64_010)], {7: (70, 70_000, 70_010, 700)})) == {
        'host_sleep_event_count_mismatch'}
    established()


@control('SleepRules', accepts(EVENTS_BETWEEN))
def test_complete_sleep_events_agree_with_their_register(reader, established):
    complete = sleep_export(*COMPLETE)
    assert reader.sleep_event_problems(complete) == set()
    established()


@control('SleepRules', accepts(FORMATTING))
def test_microseconds_never_print_a_negative_zero(reader, established):
    # Summary formatting: no -0.0, and the attribution labels.
    assert [reader.us(v) for v in (None, -49, -1, 0, 49, -60, 1500)] == ['-', '0.0', '0.0', '0.0', '0.0', '-0.1', '1.5']
    established()


@control('SleepRules', accepts(FORMATTING))
def test_sleep_attribution_labels(reader, established):
    assert reader.sleeps({'unattributed': 1, 'none': 2, '1': 3}, {'event': 3}) == (
        'ordinary_sentinel 3, none (no host sleep between) 2, unattributed (no containing sleep) 1 [scope event 3]')
    established()


# ---- calibration and role limits -------------------------------------------------------

@control('Limits', accepts('uncalibrated O1'))
def test_without_a_calibration_the_uncertainty_is_absent(reader, established):
    uncalibrated = reader.evaluate_bundle(ordinary_bundle(), None)
    assert uncalibrated['status'] == 'accepted' and uncalibrated['phases'][0]['arrival_detection']['uncertainty_ns'] is None
    assert uncalibrated['phases'][0]['arrival_detection']['uncertainty_basis'] == 'calibration_absent'
    established()


@control('Limits', accepts('unbounded alignment O1'))
def test_an_unbounded_alignment_is_named(reader, established):
    unbounded = reader.evaluate_bundle(ordinary_bundle(), dict(CALIBRATION, alignment_ns=None))
    assert unbounded['phases'][0]['arrival_detection']['uncertainty_basis'] == 'alignment_unbounded'
    assert unbounded['phases'][0]['serialize']['uncertainty_ns'] == 2 * HOST_FLOOR
    established()


@control('Limits', accepts('O1 without an endpoint term'))
def test_a_calibration_without_an_endpoint_term_is_named(reader, established):
    no_term = reader.evaluate_bundle(ordinary_bundle(), dict(CALIBRATION, endpoint_term_ns=None))
    assert no_term['phases'][0]['serialize']['uncertainty_basis'] == 'calibration_endpoint_term_absent'
    established()


@control('Limits', accepts('scan role unknown A2'))
def test_scan_passes_of_an_unknown_role_are_flagged(reader, established):
    role_unknown = actor_bundle()
    page_fault(lambda d: scan_passes(401)(header('flags', 12)(d)), 1)(role_unknown)
    role_row = reader.evaluate_bundle(role_unknown, CALIBRATION)
    assert role_row['status'] == 'accepted' and role_row['worker_waits']['1']['scan']['role_unknown_passes_uncounted'] is True, role_row['problems']
    established()


# ---- pooling ---------------------------------------------------------------------------

def refused_as_pooled(reader, rows):
    try:
        reader.aggregate(rows)
    except AssertionError as error:
        assert 'pooled groups refused' in str(error), error
        return True
    return False


# Aggregation never pools apps, cells, regimes, power sources, low power modes or host flavours.
VARIANTS = dict(regime='idle', cell='O64', power_source='AC Power', lowpowermode='1', flavour=dict(FLAVOUR, swift='-O'))


@control('Pooling', rejects('neighbor_pooled_with_instrumented'))
def test_the_neighbor_is_not_pooled_with_the_instrumented_app(reader, established):
    base_row = reader.evaluate_bundle(ordinary_bundle(), CALIBRATION)
    neighbor_row = reader.evaluate_bundle(neighbor_bundle(), CALIBRATION)
    assert refused_as_pooled(reader, [base_row, neighbor_row]), 'pooled aggregate accepted: ' + 'neighbor_pooled_with_instrumented'
    established(status='refused', codes=['pooled'])


@inputs('Pooling', 'field, value', [(f'{field}_pooled', field, value) for field, value in VARIANTS.items()],
        lambda label: rejects(label))
def test_rows_that_differ_in_one_group_key_are_not_pooled(reader, established, field, value):
    base_row = reader.evaluate_bundle(ordinary_bundle(), CALIBRATION)
    assert refused_as_pooled(reader, [base_row, dict(copy.deepcopy(base_row), **{field: value})]), 'pooled aggregate accepted: ' + field
    established(status='refused', codes=['pooled'])


@control('Pooling')
def test_low_power_groups_each_keep_their_own_trial(reader, established):
    base_row = reader.evaluate_bundle(ordinary_bundle(), CALIBRATION)
    split = reader.summarize([base_row, dict(copy.deepcopy(base_row), lowpowermode='1')])
    assert [(g['lowpowermode'], g['counts']['accepted']) for g in split] == [('0', 1), ('1', 1)], split
    established()


# ---- constructed faults ----------------------------------------------------------------

FAULTS = []


def fault(name, expected, edit, build=ordinary_bundle):
    """One constructed fault: build makes a receipt, edit corrupts it, and expected is every problem and exclusion
    code the reader must report for it."""
    FAULTS.append((name, set(expected), edit, build))


unchanged = lambda r: None
fault('bad_magic', {'worker_page_bad_magic'}, page_fault(header('magic', 0x50575754)))
fault('wrong_version', {'worker_page_wrong_version'}, page_fault(header('version', 2)))
fault('capture_refused', {'worker_page_capture_refused'}, page_fault(header('flags', 5)))
fault('event_overflow', {'worker_page_event_overflow'}, page_fault(header('flags', 6)))
fault('uninitialized_page', {'worker_page_uninitialized'}, page_fault(header('flags', 0)))
fault('non_monotonic_worker_events', {'worker_events_non_monotonic'}, page_fault(swap_fresh))
fault('origin_mismatch', {'worker_origin_mismatch'}, page_fault(header('origin', tk(10_000_000 + 1400))))
fault('scan_histogram_mismatch', {'worker_scan_histogram_mismatch'}, page_fault(scan_passes(401), 1), actor_bundle)
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
fault('neighbor_with_stamps', {'neighbor_has_stamps'}, lambda r: r.update(stamps=ordinary_bundle()['stamps']), neighbor_bundle)
fault('actor_page_count_mismatch', {'stamp_page_count_mismatch'},
      lambda r: next(e for e in r['stamps']['events'] if e[0] == 170).__setitem__(2, 3), actor_bundle)
fault('stamps_for_other_specimen', {'stamps_specimen_mismatch'}, lambda r: r['stamps'].update(specimen_id='other'))
fault('page_from_other_worker', {'worker_page_pid_mismatch'}, lambda r: r['stamps']['worker_pages'][0].update(pid=1))
fault('timebase_mismatch', {'worker_timebase_mismatch'}, lambda r: r['stamps'].update(timebase=dict(numer=1, denom=1)))
fault('eligible_count_mismatch', {'eligible_count_mismatch'}, lambda r: r['trial']['layout']['phases'][0].update(eligible=2))
def reorder_host(r):
    events = r['stamps']['events']; events[2][3], events[3][3] = events[3][3], events[2][3]
fault('host_events_non_monotonic', {'host_events_non_monotonic'}, reorder_host)
def late_custody_start(r):
    next(e for e in r['stamps']['events'] if e[0] == 153 and e[2] == 1)[3] = tk(100_000_000 + phase_times(0)[1] + 1200)
fault('custody_start_after_pass_end', {'host_events_non_monotonic'}, late_custody_start, actor_bundle)
fault('started_after_spawn', {'started_after_spawn'}, lambda r: r['started'].update(raw=tk(10_000_000 + 2000)))
fault('started_host_pid_mismatch', {'started_mismatch'}, lambda r: r['started'].update(host_pid=4142))
fault('exit_watch_other_pid', {'host_exit_pid_mismatch'}, lambda r: r['host_exit']['registration']['generation'].update(pid=1))
fault('observer_overlap', {'observer_overlap'}, watch_inside_held)
fault('pass_event_unpaired', {'worker_pass_event_unpaired'}, unchanged,
      lambda: ordinary_bundle(worker_edit=lambda ev: [(e, p, a, t + 1) if e == 13 else (e, p, a, t) for e, p, a, t in ev]))
fault('pass_count_mismatch', {'worker_pass_count_mismatch'}, unchanged,
      lambda: ordinary_bundle(worker_edit=lambda ev: [(e, p, a - 1, t) if e == 13 else (e, p, a, t) for e, p, a, t in ev]))
fault('pass_events_incomplete', {'worker_pass_events_incomplete', 'worker_pass_count_mismatch'}, unchanged,
      lambda: actor_bundle(worker_edit=lambda actor, ev: [e for e in ev if not (actor == 1 and e[0] == 13 and e[1] == 1)]))
fault('exchange_pass_record_missing', {'worker_pass_events_incomplete', 'worker_pass_count_mismatch'}, unchanged,
      lambda: actor_bundle(worker_edit=lambda actor, ev: [e for e in ev if not (actor == 0 and e[0] == 15 and e[1] == 1)]))
fault('store_begin_unpaired', {'host_store_begin_unpaired'}, lambda r: next(e for e in r['stamps']['events'] if e[0] == 139).__setitem__(2, 2))
fault('store_begin_incomplete', {'host_store_begin_incomplete'}, unchanged,
      lambda: actor_bundle(host_edit=lambda events: [e for e in events if not (e[0] == 149 and e[1] == 0)]))
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
      lambda r: (lambda events, begin: events.__delitem__(slice(begin, begin + 2)))(*sleep_pair(r, 4)), actor_bundle)
graced = lambda: ordinary_bundle(grace='notified')
fault('wait_outcome_aux_3', {'host_wait_outcome_invalid'}, edit_wait_outcome(aux=lambda e: 3), graced)
fault('wait_outcome_without_pair', {'host_wait_outcome_unpaired'}, move_wait_outcome, graced)
fault('wait_outcome_other_key', {'host_wait_outcome_unpaired'}, edit_wait_outcome(phase=lambda e: 4), graced)
fault('wait_outcome_other_raw', {'host_wait_outcome_unpaired'}, edit_wait_outcome(raw=lambda e: e[3] + tk(1)), graced)
fault('grace_finished_before_begin', {'host_grace_interval_reversed'}, move_grace_finished(11515), graced)
fault('grace_finished_listed_before_begin', {'host_grace_interval_reversed'}, move_grace_finished(11520), graced)
fault('combined_magic_and_pacing', {'worker_page_bad_magic', 'pacing_out_of_range'},
      lambda r: (page_fault(header('magic', 0))(r), r['conditions']['pacing'].update(actual_gap_ns=None)))
fault('combined_alignment_and_sleep', {'clock_alignment_violation', 'sleep_overlapped'},
      lambda r: (early_observation(r), r['conditions'].update(sleep_overlapped=True)))


@inputs('Faults', 'expected, edit, build', FAULTS, lambda label: rejects(label))
def test_a_constructed_fault_is_refused_with_exactly_its_codes(reader, established, expected, edit, build):
    bad = build(); edit(bad)
    row = reader.evaluate_bundle(bad, CALIBRATION)
    assert row['status'] != 'accepted' and codes(row) == expected, (row['status'], codes(row))
    established(status=row['status'], codes=sorted(codes(row)))


# ---- replaced reader functions ---------------------------------------------------------

def old_uncertainty(self, start, end):
    """The pre-referee arithmetic: endpoint brackets + two calibration stamp costs + alignment."""
    cal, cross = self.calibration, start['process'] != end['process']
    if start['bracket_ns'] is None or end['bracket_ns'] is None:
        return dict(uncertainty_ns=None, uncertainty_basis='bracket_unobserved')
    alignment = max(cal['alignment_ns'], self.inversion_ns) if cross else 0
    return dict(uncertainty_ns=start['bracket_ns'] + end['bracket_ns'] + 2 * cal['stamp_ns'] + alignment, uncertainty_basis='calibrated')


def actor_blind_intervals(reader, stop_only):
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


# The pre-referee uncertainty arithmetic fails the expected values.
@inputs('ReplacedReader', 'build, check', [
    ('ordinary', ordinary_bundle, check_ordinary),
    ('actor', actor_bundle, check_actor),
    ('inversion', lambda: edited(ordinary_bundle, late_release_stamp), lambda reader, row: check_inversion(row)),
], rejects('old_uncertainty_formula'))
def test_the_superseded_uncertainty_formula_fails_the_expected_values(reader, replace, established, build, check):
    replace(reader.Interval, 'uncertainty', old_uncertainty)
    with pytest.raises(AssertionError):
        check(reader, reader.evaluate_bundle(build(), CALIBRATION))
    established(status='rejected', codes=['expected uncertainty mismatch'])


@inputs('ReplacedReader', 'stop_only', [('intervals', False), ('stop_code', True)],
        lambda label: rejects(f'actor_blind_{label}'))
def test_exit_lookups_that_ignore_the_actor_fail_the_per_actor_values(reader, replace, established, stop_only):
    plain = reader.evaluate_bundle(actor_bundle(), CALIBRATION)
    replace(reader, 'actor_intervals', actor_blind_intervals(reader, stop_only))
    with pytest.raises(AssertionError):
        check_actor_exits(reader, reader.evaluate_bundle(actor_bundle(exits=True), CALIBRATION), plain)
    established(status='rejected', codes=['expected per-actor interval mismatch'])


# ---- comparison runs -------------------------------------------------------------------

COMPARISON = dict(apps=['baseline', 'candidate'], pairing_rule='constructed: same cell, regime and repetition index')
VERDICTS = ('improves_beyond_uncertainty_in_every_pair', 'improves_beyond_spread_in_every_pair',
            'worsens_beyond_instrument_uncertainty', 'worsens_beyond_spread_in_any_pair',
            'worsens_beyond_spread_in_every_pair')


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


def pairs_of(reader, rows, required=3, gate=True):
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


@pytest.fixture
def base(reader):
    """The evaluated constructed O1 row that the baseline and candidate rows are made from."""
    return reader.evaluate_bundle(ordinary_bundle(), CALIBRATION)


def check_improvement(reader, base):
    (entry,) = pairs_of(reader, improving_rows(base))['entries']
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
        candidate_upper_ns=9100, baseline_lower_ns=2900, bound_ns=6200, limit_ns=2_000_000, within_limit=True, combined_uncertainty_ns=6200,
        uncertainty_at_most_0_5_ms=True, instrument_gate_credited=True, credited=True, coverage_complete=True,
        pairs_required=3, paired_trials=3, trials=dict(baseline=3, candidate=3))}, entry['response']
    assert entry['host_sleeps']['ready_byte_wait'] == [dict(index=i, baseline=dict(count=1, sum_ns=12_500_000),
                                                            candidate=dict(count=2, sum_ns=3_000_000)) for i in range(3)]
    assert entry['host_sleeps']['ordinary_sentinel'][0]['candidate'] == dict(count=2, sum_ns=4_350_000)
    assert [p['index'] for p in entry['pairs']] == [0, 1, 2] and pairs_of(reader, improving_rows(base))['unpaired'] == []


def check_one_pair_within_the_candidate_spread(reader, base):
    # One candidate arrival of 6.0 ms: 1.3 ms shorter than its baseline, beyond uncertainty but not beyond the 5.1 ms candidate spread.
    spread = {2: {'arrival_detection': (6_000_000, 1300)}}
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=spread))['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (True, False, False, False), arrival
    assert arrival['spread_ns']['candidate'] == dict(ns=5_100_000, trials=3)
    assert [(r['difference'], r['improve_threshold'], r['spread_outcome']) for r in arrival['pairs']] == [
        (6_200_000, 5_102_600, 'improved'), (6_300_000, 5_102_600, 'improved'), (1_300_000, 5_102_600, 'within_spread')], arrival['pairs']


def check_one_pair_worse_within_the_baseline_spread(reader, base):
    # 10 us worse in one pair: beyond the instrument uncertainty, within the 200 us baseline spread.
    worse = {2: {'held_total': (BASELINE_HELD + 200_000 + 10_000, 1300)}}
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=worse))['entries']
    held = entry['components']['p0.held_total']
    assert verdicts(held) == (False, False, True, False) and outcomes(held)[2] == (2, -10_000, 2600, 'worsened'), held
    assert (held['pairs'][2]['worsen_threshold'], held['pairs'][2]['spread_outcome']) == (202_600, 'within_spread'), held['pairs'][2]
    assert verdicts(entry['components']['p0.arrival_to_observation']) == (True, True, False, False)


def check_one_pair_worse_beyond_the_baseline_spread(reader, base):
    # 500 us worse in one pair: beyond the baseline spread plus both uncertainties.
    worse_spread = {2: {'held_total': (BASELINE_HELD + 200_000 + 500_000, 1300)}}
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=worse_spread))['entries']
    held = entry['components']['p0.held_total']
    assert verdicts(held) == (False, False, True, True), held
    assert (held['pairs'][2]['difference'], held['pairs'][2]['worsen_threshold'], held['pairs'][2]['spread_outcome']) == (
        -500_000, 202_600, 'worsened'), held['pairs'][2]


@control('Comparison', accepts('candidate arrival and held total shorter beyond uncertainty and beyond its spread in every pair: improvement'))
def test_a_candidate_shorter_beyond_uncertainty_and_spread_in_every_pair_improves(reader, base, established):
    check_improvement(reader, base)
    established()


@control('Comparison', accepts('whole-request direction counts faster, equal and slower pairs by the sign of the difference'))
def test_whole_request_direction_counts_each_pair_by_sign(reader, base, established):
    # Whole request 50, 51, 52 ms against 44, 51, 60 ms: one pair each faster, equal and slower.
    mixed = [pair_row(base, app, i, whole_ms=ms) for i, pair in enumerate(((50, 44), (51, 51), (52, 60)))
             for app, ms in zip(reader.PAIR_APPS, pair)]
    (entry,) = pairs_of(reader, mixed)['entries']
    assert entry['whole_request']['direction'] == dict(faster=1, slower=1, equal=1, rule=DIRECTION_RULE), entry['whole_request']
    assert [r['difference'] for r in entry['whole_request']['pairs']] == [6_000_000, 0, -8_000_000]
    established()


@control('Comparison', accepts('grace counts paired as exact differences with per-side sums, an absent count kept as absent'))
def test_grace_counts_are_paired_as_exact_differences(reader, base, established):
    # Grace counts: one timeout per baseline trial, one notification per candidate trial, one candidate count absent.
    rows = [pair_row(base, app, i, **(dict(grace_timeouts=1) if app == 'baseline' else dict(grace_notified=1)))
            for i in range(3) for app in reader.PAIR_APPS]
    rows[5]['grace_unusable'] = None
    (entry,) = pairs_of(reader, rows)['entries']
    grace = entry['grace']
    assert set(grace) == set(reader.GRACE_COUNTS)
    assert [(r['baseline'], r['candidate'], r['difference']) for r in grace['grace_timeouts']['pairs']] == [(1, 0, 1)] * 3, grace
    assert grace['grace_timeouts']['sums'] == dict(baseline=3, candidate=0) and grace['grace_notified']['sums'] == dict(baseline=0, candidate=3)
    assert [r['difference'] for r in grace['grace_notified']['pairs']] == [-1] * 3
    assert grace['grace_unusable']['pairs'][2] == dict(index=2, absent_on=['candidate']) and grace['grace_unusable']['sums'] == dict(baseline=0, candidate=0)
    assert all('improves_beyond_uncertainty_in_every_pair' not in value for value in grace.values())
    established()


@control('Comparison', accepts('one pair within uncertainty: no improvement verdict'))
def test_one_pair_within_uncertainty_gives_no_improvement(reader, base, established):
    within = {1: {'arrival_detection': (BASELINE_ARRIVAL + 100_000 - 2000, 1300)}}
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=within))['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (False, False, False, False) and outcomes(arrival)[1] == (1, 2000, 2600, 'within_uncertainty'), arrival
    established()


@control('Comparison', accepts('improvement beyond uncertainty in every pair but within the candidate spread in one: no spread improvement verdict'))
def test_one_pair_within_the_candidate_spread_gives_no_spread_improvement(reader, base, established):
    check_one_pair_within_the_candidate_spread(reader, base)
    established()


@control('Comparison', accepts('one pair worse beyond uncertainty but within the baseline spread: instrument worsening only'))
def test_one_pair_worse_within_the_baseline_spread_is_an_instrument_worsening_only(reader, base, established):
    check_one_pair_worse_within_the_baseline_spread(reader, base)
    established()


@control('Comparison', accepts('one pair worse beyond the baseline spread: spread worsening'))
def test_one_pair_worse_beyond_the_baseline_spread_is_a_spread_worsening(reader, base, established):
    check_one_pair_worse_beyond_the_baseline_spread(reader, base)
    established()


@control('Comparison', accepts('fewer pairs than required: improvement withheld, refutation and worsening kept'))
def test_fewer_pairs_than_required_withhold_an_improvement_only(reader, base, established):
    worse = {2: {'held_total': (BASELINE_HELD + 200_000 + 10_000, 1300)}}
    # Fewer pairs than required: an improvement is withheld, a refutation or a worse pair is not.
    (entry,) = pairs_of(reader, improving_rows(base), required=5)['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (None, None, None, None) and arrival['withheld'] == '3 established of 5 required pairs', arrival
    assert verdicts(entry['components']['p0.serialize']) == (False, False, None, None)
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=worse), required=5)['entries']
    assert verdicts(entry['components']['p0.held_total']) == (False, False, True, None)
    established()


UNCREDITED_RESPONSE = 'response bound beyond 2 ms, or within it without the resolution or the gate: not credited'


@control('Comparison', accepts(UNCREDITED_RESPONSE))
def test_a_response_bound_beyond_2_ms_is_not_credited(reader, base, established):
    slow = {0: {'release_to_ack': (2_506_000, 3100)}}
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=slow))['entries']
    response = entry['response']['p0.release_to_ack']
    assert (response['bound_ns'], response['within_limit'], response['credited']) == (2_506_200, False, False), response
    established()


@control('Comparison', accepts(UNCREDITED_RESPONSE))
def test_a_response_bound_without_the_resolution_is_not_credited(reader, base, established):
    wide = {0: {'release_to_ack': (1_006_000, 600_000)}}
    (entry,) = pairs_of(reader, improving_rows(base, candidate_edits=wide))['entries']
    response = entry['response']['p0.release_to_ack']
    assert (response['bound_ns'], response['within_limit'], response['combined_uncertainty_ns'], response['uncertainty_at_most_0_5_ms'],
            response['credited']) == (1_603_100, True, 603_100, False, False), response
    established()


@control('Comparison', accepts(UNCREDITED_RESPONSE))
def test_a_response_bound_without_the_instrument_gate_is_not_credited(reader, base, established):
    (entry,) = pairs_of(reader, improving_rows(base), gate=False)['entries']
    response = entry['response']['p0.release_to_ack']
    assert (response['within_limit'], response['instrument_gate_credited'], response['credited']) == (True, False, False), response
    established()


@control('Comparison', accepts('unpaired trials (one side excluded, conditions differ) listed and never paired'))
def test_unpaired_trials_are_listed_and_never_paired(reader, base, established):
    rows = improving_rows(base) + [
        pair_row(base, 'baseline', 3, {'arrival_first_check_positive': (BASELINE_ARRIVAL, 1300)}, form='arrival_first_check_positive', whole_ms=51),
        pair_row(base, 'candidate', 3, {'arrival_detection': (CANDIDATE_ARRIVAL, 1300)}, status='excluded', exclusions=['observer_overlap']),
        pair_row(base, 'baseline', 4, whole_ms=51),
        pair_row(base, 'candidate', 4, power_source='AC Power')]
    found = pairs_of(reader, rows)
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
    assert mains['pairs'] == [] and mains['components'] == {}, mains
    assert mains['response']['p0.release_to_ack']['bound_ns'] is None and not mains['response']['p0.release_to_ack']['credited'], mains
    established()


IDENTICAL = 'identical receipts: no improvement or worsening verdict; uncalibrated: verdicts withheld; not a comparison: no pairs'


@control('Comparison', accepts(IDENTICAL))
def test_identical_receipts_neither_improve_nor_worsen(reader, base, established):
    # Identical receipts on both sides: every difference is zero, so no improvement and no worsening.
    same = [pair_row(base, app, i) for i in range(2) for app in reader.PAIR_APPS]
    (entry,) = pairs_of(reader, same, required=2)['entries']
    series = [*entry['components'].values(), *entry['waits'].values()]
    assert series and all(verdicts(v) == (False, False, False, False) for v in series), [
        (v, verdicts(v)) for v in series if verdicts(v) != (False, False, False, False)]
    assert verdicts(entry['whole_request']) == (None, False, None, False)
    assert entry['whole_request']['direction'] == dict(faster=0, slower=0, equal=2, rule=DIRECTION_RULE)
    established()


@control('Comparison', accepts(IDENTICAL))
def test_uncalibrated_receipts_withhold_their_verdicts(reader, established):
    uncalibrated = reader.evaluate_bundle(ordinary_bundle(), None)
    (entry,) = pairs_of(reader, [pair_row(uncalibrated, app, i) for i in range(2) for app in reader.PAIR_APPS], required=2)['entries']
    arrival = entry['components']['p0.arrival_to_observation']
    assert verdicts(arrival) == (None, None, None, None), arrival
    assert arrival['withheld'] == '0 established of 2 required pairs; absent or unestablished in 2', arrival
    assert verdicts(entry['waits']['p0.release_wait']) == (False, False, False, False)
    established()


@control('Comparison', accepts(IDENTICAL))
def test_a_schedule_without_a_comparison_has_no_pairs(reader, base, established):
    same = [pair_row(base, app, i) for i in range(2) for app in reader.PAIR_APPS]
    assert reader.matched_pairs(same, None, True) is None
    established()


@inputs('ReplacedReader', 'check', [
    ('improvement', check_improvement),
    ('within-the-candidate-spread', check_one_pair_within_the_candidate_spread),
    ('worse-within-the-baseline-spread', check_one_pair_worse_within_the_baseline_spread),
    ('worse-beyond-the-baseline-spread', check_one_pair_worse_beyond_the_baseline_spread),
], rejects('spread_term_ignored'))
def test_a_spread_term_replaced_by_zero_fails_the_spread_expectations(reader, base, replace, established, check):
    replace(reader, 'side_spread', lambda values: 0)
    with pytest.raises(AssertionError):
        check(reader, base)
    established(status='rejected', codes=['spread verdict mismatch'])


# ---- response bounds: boundary arithmetic, required coverage and publication brackets --

def release_response(reader, rows, required=3):
    return pairs_of(reader, rows, required=required)['entries'][0]['response']['p0.release_to_ack']


RESPONSE_EXTREMA = 'uncertainty-expanded response extrema and exact 2 ms boundary'
RESPONSE_UNCERTAINTY = 'response uncertainty on every trial, including non-extremal and unknown terms'
RESPONSE_COVERAGE = 'missing response endpoints and insufficient matched pairs withhold credit'
COMMIT_BRACKETS = 'version-2 commit brackets required; legacy service bracket remains conservative even with a later wait stamp'


@control('ResponseRepair', accepts(RESPONSE_EXTREMA))
def test_response_extrema_are_expanded_by_their_uncertainty(reader, base, established):
    rows = [pair_row(base, app, i, {'release_to_ack': (100_000 if app == 'baseline' else 2_000_000, 200_000)})
            for i in range(3) for app in ('baseline', 'candidate')]
    value = release_response(reader, rows)
    assert (value['candidate_upper_ns'], value['baseline_lower_ns'], value['bound_ns']) == (2_200_000, -100_000, 2_300_000)
    assert value['uncertainty_at_most_0_5_ms'] and not value['credited'], value
    established()


@inputs('ResponseRepair', 'delta, credited', [
    ('1-ns-inside-2-ms', -300_001, True),
    ('exactly-2-ms', -300_000, True),
    ('1-ns-beyond-2-ms', -299_999, False),
], accepts(RESPONSE_EXTREMA))
def test_the_response_bound_is_credited_up_to_exactly_2_ms(reader, base, established, delta, credited):
    boundary = [pair_row(base, app, i, {'release_to_ack': (100_000 if app == 'baseline' else 2_000_000, 200_000)})
                for i in range(3) for app in ('baseline', 'candidate')]
    for row in boundary:
        if row['app'] == 'candidate': row['phases'][0]['release_to_ack']['ns'] += delta
    value = release_response(reader, boundary)
    assert (value['bound_ns'], value['credited']) == (2_300_000 + delta, credited), value
    established()


def rows_with_one_candidate_response(base, ns, uncertainty):
    """Baseline responses of 0 and candidate responses of 2 ms, each with 10 us; one candidate trial differs."""
    rows = [pair_row(base, app, i, {'release_to_ack': ((0, 10_000) if app == 'baseline' else (2_000_000, 10_000))})
            for i in range(3) for app in ('baseline', 'candidate')]
    rows[3]['phases'][0]['release_to_ack'].update(ns=ns, uncertainty_ns=uncertainty)
    return rows


@control('ResponseRepair', accepts(RESPONSE_UNCERTAINTY))
def test_a_larger_uncertainty_on_a_non_extremal_trial_sets_the_upper_bound(reader, base, established):
    value = release_response(reader, rows_with_one_candidate_response(base, 1_900_000, 200_000))
    assert (value['candidate_upper_ns'], value['bound_ns']) == (2_100_000, 2_110_000), value
    established()


# The larger uncertainty may belong to neither nominal extreme. Unknown uncertainty cannot be dropped.
@control('ResponseRepair', accepts(RESPONSE_UNCERTAINTY))
def test_an_uncertainty_beyond_half_a_millisecond_on_any_trial_is_reported(reader, base, established):
    rows = rows_with_one_candidate_response(base, 1, 600_000)
    assert not release_response(reader, rows)['uncertainty_at_most_0_5_ms']
    established()


@control('ResponseRepair', accepts(RESPONSE_UNCERTAINTY))
def test_an_unknown_uncertainty_leaves_the_bound_unknown(reader, base, established):
    rows = rows_with_one_candidate_response(base, 1, None)
    assert release_response(reader, rows)['bound_ns'] is None and not release_response(reader, rows)['credited']
    established()


@control('ResponseRepair', accepts(RESPONSE_COVERAGE))
def test_fewer_matched_pairs_than_required_withhold_response_credit(reader, base, established):
    rows = improving_rows(base)
    assert not release_response(reader, rows, required=5)['credited']
    established()


@control('ResponseRepair', accepts(RESPONSE_COVERAGE))
def test_a_trial_without_its_response_leaves_coverage_incomplete(reader, base, established):
    rows = improving_rows(base)
    missing = copy.deepcopy(rows)
    missing[1]['phases'][0].pop('release_to_ack')
    assert not release_response(reader, missing)['coverage_complete'] and not release_response(reader, missing)['credited']
    established()


@control('ResponseRepair', accepts(RESPONSE_COVERAGE))
def test_no_response_on_any_trial_leaves_the_bound_unknown(reader, base, established):
    rows = improving_rows(base)
    for row in rows: row['phases'][0].pop('release_to_ack')
    assert release_response(reader, rows)['bound_ns'] is None and not release_response(reader, rows)['credited']
    established()


@control('ResponseRepair', accepts('missing all inbound wait starts refuses the trial'))
def test_a_receipt_without_any_inbound_wait_start_is_refused(reader, established):
    # Missing all transfer starts used to silently remove every inbound response obligation.
    missing = actor_bundle()
    missing['stamps']['events'] = [e for e in missing['stamps']['events'] if e[0] != 155]
    value = reader.evaluate_bundle(missing, CALIBRATION)
    assert value['status'] == 'refused' and 'response_delivery_coverage' in value['problems'], value['problems']
    established()


def commit_bracketed_bundle():
    """A version-2 recorder brackets the commit separately from the later wait-start stamp."""
    bracketed = actor_bundle()
    bracketed['stamps']['version'] = 2
    events = []
    for e in bracketed['stamps']['events']:
        if e[0] == 155:
            events += [[158, e[1], e[2], e[3] - tk(6)], [159, e[1], e[2], e[3] - tk(4)]]
        events.append(e)
    bracketed['stamps']['events'] = events
    return bracketed


@control('ResponseRepair', accepts(COMMIT_BRACKETS))
def test_version_2_commit_brackets_bound_the_inbound_response(reader, established):
    bracketed = commit_bracketed_bundle()
    value = reader.evaluate_bundle(bracketed, CALIBRATION)
    assert value['status'] == 'accepted', value['problems']
    for p in value['phases']:
        for c in p['custody']:
            response_value = c['inbound_response']
            assert response_value['ns'] == 24_000 and response_value['uncertainty_ns'] == 17_100, response_value
            assert response_value['commit_bracket_source'] == 'commit_store'
    established()


@control('ResponseRepair', accepts(COMMIT_BRACKETS))
def test_a_version_2_receipt_without_commit_brackets_is_refused(reader, established):
    bracketed = commit_bracketed_bundle()
    missing = copy.deepcopy(bracketed)
    missing['stamps']['events'] = [e for e in missing['stamps']['events'] if e[0] not in (158, 159)]
    value = reader.evaluate_bundle(missing, CALIBRATION)
    assert value['status'] == 'refused' and any(p.startswith('response_endpoint_missing:') for p in value['problems']), value
    established()


@control('ResponseRepair', accepts(COMMIT_BRACKETS))
def test_a_legacy_receipt_keeps_the_whole_service_bracket(reader, established):
    # Old exports retain the whole pre-commit service to post-commit wait bracket, never a zero-width start.
    value = reader.evaluate_bundle(actor_bundle(), CALIBRATION)
    for p in value['phases']:
        for c in p['custody']:
            assert c['inbound_response']['uncertainty_ns'] == 25_100, c['inbound_response']
    established()


@control('ResponseRepair', accepts(COMMIT_BRACKETS))
def test_a_later_legacy_wait_stamp_widens_the_bracket(reader, established):
    delayed = actor_bundle()
    for e in delayed['stamps']['events']:
        if e[0] == 155: e[3] += tk(10)
    value = reader.evaluate_bundle(delayed, CALIBRATION)
    assert value['status'] == 'accepted', value['problems']
    for p in value['phases']:
        for c in p['custody']:
            v = c['inbound_response']
            assert (v['ns'], v['uncertainty_ns'], v['ns'] + v['uncertainty_ns']) == (10_000, 35_100, 45_100), v
    established()


@control('ResponseRepair', accepts(COMMIT_BRACKETS))
def test_a_legacy_receipt_without_the_service_start_is_refused(reader, established):
    missing = actor_bundle()
    missing['stamps']['events'] = [e for e in missing['stamps']['events'] if e[0] != 153]
    value = reader.evaluate_bundle(missing, CALIBRATION)
    assert value['status'] == 'refused' and any(p.startswith('response_endpoint_missing:') for p in value['problems']), value
    established()


# ---- per-actor scan pairs --------------------------------------------------------------

# Subject (two inbound slots) scan counters. The baseline scans from index 0: every pass visits both slots except
# the one acknowledging slot 0, so 2 * 400 - 1 visits, its full-scan floor. The candidate's passes visit two, one
# or no slots. The issuer has no inbound slot and makes 30 zero-visit passes on both sides.
ISSUER_SCAN = dict(passes_activation=30, histogram={0: 30})
BASELINE_SCAN = dict(passes_activation=400, visits_activation=799, loads_activation=840, histogram={1: 1, 2: 399})
CANDIDATE_SCAN = dict(passes_activation=400, visits_activation=140, loads_activation=160, histogram={0: 300, 1: 60, 2: 40})
# The baseline's scan in fewer passes: 599/300 is below 799/400 although both are full scans (floor 599).
BASELINE_FEWER_SCAN = dict(passes_activation=300, visits_activation=599, loads_activation=620, histogram={1: 1, 2: 299})
# The candidate's scan in fewer passes: 100/300 is below 140/400 although both are below their floors.
CANDIDATE_FEWER_SCAN = dict(passes_activation=300, visits_activation=100, loads_activation=115, histogram={0: 230, 1: 40, 2: 30})
# 5/3 (a full scan, floor 5) against 5 * 10**17 / (3 * 10**17 + 1) (floor 6 * 10**17 + 1): equal as floats, lower exactly.
THIRDS_SCAN = dict(passes_activation=3, visits_activation=5, loads_activation=5, histogram={1: 1, 2: 2})
NEAR_THIRDS_SCAN = dict(passes_activation=3 * 10**17 + 1, visits_activation=5 * 10**17, loads_activation=5 * 10**17,
                        histogram={0: 1, 1: 10**17, 2: 2 * 10**17})
SCAN_NAMES = [f'w{a}.scan_{m}_per_pass_{r}' for a in (0, 1) for r in ('activation', 'exchange') for m in ('visits', 'loads')]
SCAN_FLOOR = 'candidate_not_below_full_scan_floor'


def drop_subject_ack(slot):
    """A worker edit removing the subject page's INBOUND_ACKNOWLEDGED event for slot; the layout keeps the slot."""
    return lambda actor, events: [e for e in events if not (actor == 1 and e[0] == 10 and e[1] == slot)]


def scan_row(reader, app, index, subject, worker_edit=None):
    """An evaluated A2 row; a removed acknowledgement now refuses the complete trial."""
    bundle = actor_bundle(scan={0: ISSUER_SCAN, 1: subject}, worker_edit=worker_edit)
    bundle['trial'].update(app=app, index=index)
    row = reader.evaluate_bundle(bundle, CALIBRATION)
    if worker_edit:
        assert row['status'] == 'refused' and any(p.startswith('response_endpoint_missing:') for p in row['problems']), row['problems']
    else:
        assert row['status'] == 'accepted', row['problems']
    return dict(row, dir=f'constructed/{app}/A2/rapid/{index}')


def scan_rows(reader, candidates, baseline=BASELINE_SCAN, inbound=None, edits=None):
    """Constructed inputs to the scan comparison, including faults already refused by full-trial coverage checks.
    Mutate the decoded scan records here to independently exercise the comparison's own refusals."""
    rows = []
    for i, scan in enumerate(candidates):
        candidate = scan_row(reader, 'candidate', i, scan)
        if i in (inbound or {}):
            candidate['scan']['1'].update(inbound_count=inbound[i], inbound_observed=False)
        candidate['scan']['1'].update((edits or {}).get(i, {}))
        rows += [scan_row(reader, 'baseline', i, baseline), candidate]
    return rows


def scan_side(count, passes, floor):
    return dict(count=count, passes=passes, per_pass=count / passes, full_scan_floor=floor, below_full_scan_floor=count < floor)


def scan_outcomes(entry, name):
    return [r['outcome'] for r in entry['scan']['series'][name]['pairs']]


SCAN_RECORD = 'scan record: inbound_count from the layout, acknowledged slots from the page, observed only when they agree'
SCAN_LOWER_IN_EVERY_PAIR = 'candidate subject visits and loads per scan pass lower in every pair: lower_in_every_pair; zero-visit passes per side'
IDENTICAL_SCAN_NAME = 'identical scans whose pass counts differ, both full scans or both below their floors: lower ratio, not lower'
INBOUND_MISMATCH = 'a scan pair whose subject inbound_count differs between the sides: refused with the acknowledgement mismatch it implies'
# Identical scans on both sides whose pass counts differ: each per-pass ratio is lower on the side with fewer
# passes, and the pair is not lower because both sides are full scans or both are below their floors.
IDENTICAL_SCANS = [('both-full-scans', BASELINE_SCAN, BASELINE_FEWER_SCAN, [SCAN_FLOOR]),
                   ('both-below-their-floors', CANDIDATE_SCAN, CANDIDATE_FEWER_SCAN, ['baseline_below_full_scan_floor'])]


def check_identical_scans(reader, baseline, candidate, unmet):
    (entry,) = pairs_of(reader, scan_rows(reader, [candidate] * 3, baseline=baseline))['entries']
    for measure in ('visits', 'loads'):
        value = entry['scan']['series'][f'w1.scan_{measure}_per_pass_activation']
        (b, c), = {(r['baseline']['count'], r['candidate']['count']) for r in value['pairs']}
        assert c * baseline['passes_activation'] < b * candidate['passes_activation'], (measure, b, c)
        assert value[reader.SCAN_LOWER] is False and [(r['outcome'], r['unmet']) for r in value['pairs']] == [('not_lower', unmet)] * 3, value


def check_near_thirds(reader):
    (entry,) = pairs_of(reader, scan_rows(reader, [NEAR_THIRDS_SCAN] * 3, baseline=THIRDS_SCAN))['entries']
    visits = entry['scan']['series']['w1.scan_visits_per_pass_activation']
    assert visits['pairs'][0]['baseline']['per_pass'] == visits['pairs'][0]['candidate']['per_pass'], visits['pairs'][0]
    assert visits['pairs'][0]['baseline'] == scan_side(5, 3, 5) and visits['pairs'][0]['candidate']['full_scan_floor'] == 6 * 10**17 + 1
    assert visits[reader.SCAN_LOWER] is True and scan_outcomes(entry, 'w1.scan_visits_per_pass_activation') == ['lower'] * 3, visits


@control('Scan', accepts(SCAN_RECORD))
def test_a_scan_record_takes_its_inbound_count_from_the_layout(reader, established):
    row = scan_row(reader, 'baseline', 0, BASELINE_SCAN)
    assert row['scan'] == {
        '0': dict(passes_activation=30, visits_activation=0, loads_activation=0, passes_exchange=0, visits_exchange=0, loads_exchange=0,
                  zero_visit_passes=30, inbound_count=0, inbound_count_source=reader.SCAN_INBOUND_SOURCE, acknowledged_slots=[],
                  inbound_observed=True, role_unknown_passes_uncounted=False),
        '1': dict(passes_activation=400, visits_activation=799, loads_activation=840, passes_exchange=0, visits_exchange=0, loads_exchange=0,
                  zero_visit_passes=0, inbound_count=2, inbound_count_source=reader.SCAN_INBOUND_SOURCE, acknowledged_slots=[0, 1],
                  inbound_observed=True, role_unknown_passes_uncounted=False)}, row['scan']
    assert row['worker_waits']['1']['scan']['visits_per_pass_activation'] == 1.9975
    established()


@control('Scan', accepts(SCAN_RECORD))
def test_a_page_without_one_acknowledgement_is_not_observed(reader, established):
    dropped = scan_row(reader, 'candidate', 0, CANDIDATE_SCAN, worker_edit=drop_subject_ack(1))['scan']['1']
    assert dropped['inbound_count'] == 2 and dropped['acknowledged_slots'] == [0] and dropped['inbound_observed'] is False, dropped
    established()


@control('Scan', accepts(SCAN_LOWER_IN_EVERY_PAIR))
def test_subject_visits_and_loads_lower_in_every_pair(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3))['entries']
    scan = entry['scan']
    assert sorted(scan['series']) == sorted(SCAN_NAMES) and scan['refusals'] == [] and scan['problems'] == [], scan
    visits = scan['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is True and 'withheld' not in visits, visits
    assert visits['pairs'] == [dict(index=i, baseline=scan_side(799, 400, 799), candidate=scan_side(140, 400, 799),
                                    inbound_count=dict(baseline=2, candidate=2), outcome='lower') for i in range(3)], visits['pairs']
    loads = scan['series']['w1.scan_loads_per_pass_activation']
    assert loads[reader.SCAN_LOWER] is True and [(r['baseline'], r['candidate']) for r in loads['pairs']] == [
        (scan_side(840, 400, 799), scan_side(160, 400, 799))] * 3, loads['pairs']
    for name in ('w1.scan_visits_per_pass_exchange', 'w1.scan_loads_per_pass_exchange'):
        value = scan['series'][name]
        assert value[reader.SCAN_LOWER] is None and scan_outcomes(entry, name) == ['no_passes'] * 3, value
        assert value['withheld'] == '0 established of 3 required pairs; absent, without passes or refused in 3', value
        assert value['pairs'][0]['no_passes_on'] == ['baseline', 'candidate']
    issuer = scan['series']['w0.scan_visits_per_pass_activation']
    assert issuer[reader.SCAN_LOWER] is False and scan_outcomes(entry, 'w0.scan_visits_per_pass_activation') == ['not_lower'] * 3, issuer
    assert [r['unmet'] for r in issuer['pairs']] == [[SCAN_FLOOR, 'ratio_not_lower']] * 3, issuer['pairs']
    established()


@control('Scan', accepts(SCAN_LOWER_IN_EVERY_PAIR))
def test_zero_visit_passes_are_reported_per_side_without_a_verdict(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3))['entries']
    scan = entry['scan']
    zero = scan['zero_visit_passes']
    assert zero['w1.scan_zero_visit_passes'] == dict(pairs=[dict(index=i, baseline=0, candidate=300, difference=-300) for i in range(3)],
                                                     sums=dict(baseline=0, candidate=900)), zero
    assert zero['w0.scan_zero_visit_passes']['sums'] == dict(baseline=90, candidate=90)
    assert all(reader.SCAN_LOWER not in value for value in zero.values())
    established()


@control('Scan', accepts(SCAN_LOWER_IN_EVERY_PAIR))
def test_scan_pairs_in_markdown(reader, established):
    text = '\n'.join(reader.pairs_markdown(pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3))))
    for needle in ('| w1.scan_visits_per_pass_activation | yes | r0 799/400 -> 140/400; r1 799/400 -> 140/400; r2 799/400 -> 140/400 |',
                   f'| w0.scan_visits_per_pass_activation | no | r0 0/30 -> 0/30 ({SCAN_FLOOR}, ratio_not_lower);',
                   '| w1.scan_zero_visit_passes (sum baseline / candidate 0 / 900) | no verdict | r0 0 -> 300; r1 0 -> 300; r2 0 -> 300 |'):
        assert needle in text, needle
    established()


@control('Scan', accepts('scan pairs lower in all three of five required pairs: withheld'))
def test_scan_pairs_lower_in_three_of_five_required_pairs_are_withheld(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3), required=5)['entries']
    visits = entry['scan']['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is None and visits['withheld'] == '3 established of 5 required pairs', visits
    established()


@control('Scan', accepts('one scan pair equal to its baseline: not lower in every pair'))
def test_one_scan_pair_equal_to_its_baseline_is_not_lower_in_every_pair(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN, BASELINE_SCAN, CANDIDATE_SCAN]))['entries']
    assert scan_outcomes(entry, 'w1.scan_visits_per_pass_activation') == ['lower', 'not_lower', 'lower']
    visits = entry['scan']['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is False and visits['pairs'][1]['unmet'] == [SCAN_FLOOR, 'ratio_not_lower'], visits['pairs'][1]
    established()


@inputs('Scan', 'baseline, candidate, unmet', IDENTICAL_SCANS, accepts(IDENTICAL_SCAN_NAME))
def test_identical_scans_with_fewer_passes_are_not_lower(reader, established, baseline, candidate, unmet):
    check_identical_scans(reader, baseline, candidate, unmet)
    established()


@control('Scan', accepts(IDENTICAL_SCAN_NAME))
def test_a_scan_with_fewer_passes_has_the_floor_of_its_own_pass_count(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_FEWER_SCAN] * 3, baseline=CANDIDATE_SCAN))['entries']
    assert [r['candidate']['full_scan_floor'] for r in entry['scan']['series']['w1.scan_loads_per_pass_activation']['pairs']] == [599] * 3
    established()


@control('Scan', accepts(IDENTICAL_SCAN_NAME))
def test_identical_full_scans_in_markdown(reader, established):
    text = '\n'.join(reader.pairs_markdown(pairs_of(reader, scan_rows(reader, [BASELINE_FEWER_SCAN] * 3))))
    assert f'| w1.scan_visits_per_pass_activation | no | r0 799/400 -> 599/300 ({SCAN_FLOOR});' in text, text
    established()


@control('Scan', accepts('a candidate ratio below the baseline that floats round to equal: lower by exact arithmetic'))
def test_a_ratio_that_floats_round_to_equal_is_lower_by_exact_arithmetic(reader, established):
    check_near_thirds(reader)
    established()


@control('Scan', accepts(INBOUND_MISMATCH))
def test_a_pair_with_differing_inbound_counts_is_refused(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3, inbound={2: 3}))['entries']
    scan = entry['scan']
    both = [reader.SCAN_REFUSAL, reader.SCAN_ACK_REFUSAL]
    assert scan['refusals'] == [dict(index=2, actor=1, problems=both, inbound_count=dict(baseline=2, candidate=3),
                                     acknowledged_slots=dict(baseline=[0, 1], candidate=[0, 1]))], scan['refusals']
    assert scan['problems'] == sorted(both)
    for name in SCAN_NAMES[4:]:
        assert scan_outcomes(entry, name)[2] == 'refused' and scan['series'][name]['pairs'][2]['problems'] == both, name
    visits = scan['series']['w1.scan_visits_per_pass_activation']
    assert visits[reader.SCAN_LOWER] is None and visits['withheld'] == '2 established of 3 required pairs; absent, without passes or refused in 1', visits
    assert scan['zero_visit_passes']['w1.scan_zero_visit_passes']['pairs'][2]['problems'] == both
    assert scan_outcomes(entry, 'w0.scan_visits_per_pass_activation') == ['not_lower'] * 3
    established()


@control('Scan', accepts(INBOUND_MISMATCH))
def test_a_refused_pair_does_not_hide_a_pair_that_is_not_lower(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN, BASELINE_SCAN, CANDIDATE_SCAN], inbound={2: 3}))['entries']
    assert entry['scan']['series']['w1.scan_visits_per_pass_activation'][reader.SCAN_LOWER] is False
    established()


@control('Scan', accepts(INBOUND_MISMATCH))
def test_a_refused_scan_pair_in_markdown(reader, established):
    text = '\n'.join(reader.pairs_markdown(pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3, inbound={2: 3}))))
    assert ('Refused scan pairs: r2 w1 scan_inbound_count_mismatch, scan_inbound_acknowledgement_mismatch '
            '(inbound_count 2 / 3; acknowledged slots 2 / 2).') in text and 'r2 799/400 -> 140/400 (refused)' in text, text
    established()


@control('Scan', accepts('a scan pair whose candidate page acknowledges fewer slots than the layout addresses: refused, verdict withheld'))
def test_a_pair_whose_page_acknowledges_fewer_slots_is_refused(reader, established):
    (entry,) = pairs_of(reader, scan_rows(reader, [CANDIDATE_SCAN] * 3, edits={1: dict(acknowledged_slots=[0], inbound_observed=False)}))['entries']
    scan = entry['scan']
    assert scan['refusals'] == [dict(index=1, actor=1, problems=[reader.SCAN_ACK_REFUSAL], inbound_count=dict(baseline=2, candidate=2),
                                     acknowledged_slots=dict(baseline=[0, 1], candidate=[0]))], scan['refusals']
    assert scan_outcomes(entry, 'w1.scan_visits_per_pass_activation') == ['lower', 'refused', 'lower']
    assert scan['series']['w1.scan_visits_per_pass_activation'][reader.SCAN_LOWER] is None
    assert scan_outcomes(entry, 'w0.scan_visits_per_pass_activation') == ['not_lower'] * 3
    established()


@control('Scan', accepts('scan counters summed with medians per actor in a group'))
def test_scan_counters_are_summed_with_medians_per_actor(reader, established):
    (group,) = reader.summarize([scan_row(reader, 'candidate', i, CANDIDATE_SCAN) for i in range(3)])
    stat = lambda value, n=3: dict(n=n, median=value, min=value, max=value, sum=n * value)
    assert group['scan']['1'] == dict(inbound_count=[2], passes_activation=stat(400), visits_activation=stat(140), loads_activation=stat(160),
                                      passes_exchange=stat(0), visits_exchange=stat(0), loads_exchange=stat(0), zero_visit_passes=stat(300)), group['scan']
    assert group['scan']['0']['zero_visit_passes'] == stat(30) and group['scan']['0']['inbound_count'] == [0]
    established()


@control('ReplacedReader', rejects('scan_ratio_float_comparison'))
def test_a_float_ratio_comparison_fails_the_exact_arithmetic_control(reader, replace, established):
    replace(reader, 'scan_lower', lambda bc, bp, cc, cp: cc / cp < bc / bp)
    with pytest.raises(AssertionError):
        check_near_thirds(reader)
    established(status='rejected', codes=['scan outcome mismatch'])


@inputs('ReplacedReader', 'baseline, candidate, unmet', IDENTICAL_SCANS, rejects('scan_full_scan_floor_ignored'))
def test_a_lower_ratio_credited_without_the_floor_conditions_fails(reader, replace, established, baseline, candidate, unmet):
    kept = reader.scan_unmet
    replace(reader, 'scan_unmet', lambda vb, vc: [name for name in kept(vb, vc) if name == 'ratio_not_lower'])
    with pytest.raises(AssertionError):
        check_identical_scans(reader, baseline, candidate, unmet)
    established(status='rejected', codes=['scan outcome mismatch'])


# ---- receipts on disk: the loader, the clock pair's checker and the writers ------------

def write_identity(reader, root):
    """Constructed staging and clock-pair build receipts for the summary header."""
    executables = lambda host, worker: {'executables': {reader.STAGED_HOST: dict(sha256=host), reader.STAGED_WORKER: dict(sha256=worker)}}
    (root / 'staged-identity-before.json').write_text(json.dumps(dict(instrumented=executables('a1' * 32, 'b2' * 32),
                                                                      neighbor=executables('c3' * 32, 'd4' * 32))))
    (root / 'clock-pair-build').mkdir()
    (root / 'clock-pair-build' / 'clock-pair-build.json').write_text(json.dumps(dict(binary_sha256='e5' * 32, source_sha256='f6' * 32)))


@pytest.fixture
def constructed_tree(temporary, pw_inputs, reader, clock_pair):
    """Write the disk round trip's receipts into a tree of this item's own and return it with the clock pair's resolution.

    Three ordinary trials (one whose exit watch overlaps the held interval, one whose first arrival check is
    unattributed), the actor trial and the neighbor, with the schedule, the staging and clock-pair build
    identities and the clock pair's constructed calibration. The tree is registered, and so captured as
    constructed, before the item reads or changes it."""
    def build(name='constructed'):
        root = temporary('pw-pilot-') / name
        overlapped = edited(lambda: ordinary_bundle(index=1), watch_inside_held)
        unattributed = edited(lambda: ordinary_bundle(index=2, worker_edit=early_arrival), arrival_negative_free)
        for bundle in (ordinary_bundle(), overlapped, unattributed, actor_bundle(), neighbor_bundle()):
            write_bundle(root, bundle)
        (root / 'schedule.json').write_text(json.dumps(dict(required={'instrumented/O1/rapid': 1, 'instrumented/A2/rapid': 1, 'neighbor/O1/idle': 1})))
        write_identity(reader, root)
        resolution = write_calibration(clock_pair, root)
        pw_inputs.track(root)
        return root, resolution
    return build


@control('DiskRoundTrip')
def test_four_trials_are_accepted_one_is_excluded_and_three_files_are_written(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    assert summary['calibration_status'] == 'established' and summary['counts']['accepted'] == 4 and summary['counts']['excluded'] == 1, (
        summary['calibration_status'], summary['counts'])
    assert decomposition['version'] == summary['version'] == 12
    assert all((root / name).exists() for name in ('decomposition.json', 'summary.json', 'summary.md'))
    established()


@control('DiskRoundTrip')
def test_the_calibration_terms_are_the_clock_pairs_resolution(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    calibration = decomposition['calibration']
    term = resolution['readers']['busy']['endpoint_term_ns']
    assert calibration['stamp_ns'] == -(-resolution['stamp_ns'] // 1) and calibration['alignment_ns'] == resolution['alignment']['bound_ns']
    assert calibration['endpoint_term_ns'] == term and summary['endpoint_term_ns'] == term
    assert summary['busy_combined_uncertainty_ns'] == resolution['readers']['busy']['combined_uncertainty_ns'] is not None
    established()


@control('DiskRoundTrip')
def test_each_app_cell_and_regime_is_its_own_complete_group(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    assert [(g['app'], g['cell'], g['regime'], g['lowpowermode'], g['coverage']) for g in summary['groups']] == [
        ('instrumented', 'A2', 'rapid', '0', 'complete'), ('instrumented', 'O1', 'rapid', '0', 'complete'), ('neighbor', 'O1', 'idle', '0', 'complete')]
    established()


@control('DiskRoundTrip')
def test_the_ordinary_group_keeps_its_excluded_trial_out_of_its_aggregates(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    term = resolution['readers']['busy']['endpoint_term_ns']
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
    established()


@control('DiskRoundTrip')
def test_the_actor_group_reports_first_checks_custody_and_exchange_waits(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
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
    established()


@control('DiskRoundTrip')
def test_the_overlapped_trial_is_listed_and_excluded(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    assert [(r['index'], r['overlaps_held'], r['status']) for r in summary['observer_overlap'] if r['cell'] == 'O1'] == [
        (0, False, 'accepted'), (1, True, 'excluded'), (2, False, 'accepted')]
    assert [Path(r['dir']).name for r in summary['excluded']] == ['1']
    established()


@control('DiskRoundTrip')
def test_the_markdown_summary_carries_its_identities_and_explanations(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    text = (root / 'summary.md').read_text()
    for needle in ('Not production bytes', summary['reader']['sha256'][:12], 'a1a1a1a1a1a1', 'd4d4d4d4d4d4', 'e5e5e5e5e5e5',
                   'chained or nested, not disjoint', '## Excluded trials', 'O1 rapid 1: overlaps held interval True; excluded',
                   'custody_recipient 1 [scope event 1]', 'lowpowermode 0', f"busy combined uncertainty {summary['busy_combined_uncertainty_ns']} ns",
                   reader.SAMPLED_PERIOD, '| p0.exchange_wait.slot0 |', reader.UPPER_PERIOD, 'unattributed (no containing sleep) 1',
                   'none (no host sleep between) 1', '| w0.done_detection |'):
        assert needle in text, needle
    established()


@control('DiskRoundTrip')
def test_the_markdown_summary_does_not_report_a_recipient_wait_duration(reader, constructed_tree, established):
    root, resolution = constructed_tree()
    decomposition, summary = reader.read_artifacts(root)
    text = (root / 'summary.md').read_text()
    recipient = [line for line in text.splitlines() if line.startswith('| p0.custody0.recipient_wait (')]
    assert len(recipient) == 1 and reader.RECIPIENT_NOTE in recipient[0] and recipient[0].split(' | ')[2] == 'not reported', recipient
    established()


@control('CalibrationContrasts')
def test_a_tampered_calibration_is_not_established_and_trial_facts_survive(reader, constructed_tree, established):
    tampered, _ = constructed_tree('constructed-tampered-calibration')
    value = json.loads((tampered / 'clock-pair/calibration.json').read_text()); value['resolution']['read_overhead_ns'] += 1
    (tampered / 'clock-pair/calibration.json').write_text(json.dumps(value))
    rows, plain = reader.read_artifacts(tampered, write=False)
    assert plain['calibration_status'].startswith('not_established') and plain['counts']['accepted'] == 4
    assert next(r for r in rows['rows'] if r['cell'] == 'O1' and r['app'] == 'instrumented')['phases'][0]['serialize']['uncertainty_basis'] == 'calibration_absent'
    established()


# A calibration whose busy endpoint term exceeds the gate: established, not credited, and carried into every endpoint.
@control('CalibrationContrasts', rejects('calibration_endpoint_outlier'))
def test_an_endpoint_outlier_is_established_and_not_credited(reader, clock_pair, constructed_tree, established):
    outlier, _ = constructed_tree('constructed-endpoint-outlier')
    wide = write_calibration(clock_pair, outlier, clock_pair.constructed_receipt(
        raw_options={('busy', 0): {'store_delay': {2: clock_pair.to_ticks(600_000)}}}))
    rows, plain = reader.read_artifacts(outlier)
    wide_term = wide['readers']['busy']['endpoint_term_ns']
    assert plain['calibration_status'] == 'established' and wide_term > clock_pair.GATE_NS
    assert plain['instrument_gate']['credited'] is False and 'busy_combined_uncertainty_exceeds_gate' in plain['instrument_gate']['reasons']
    wide_row = next(r for r in rows['rows'] if r['cell'] == 'O1' and r['app'] == 'instrumented' and r['index'] == 0)
    assert wide_row['phases'][0]['release_to_ack']['uncertainty_ns'] == 2 * wide_term + wide['alignment']['bound_ns']
    assert 'gate not credited' in (outlier / 'summary.md').read_text()
    established(status='not_credited', codes=plain['instrument_gate']['reasons'])


# Missing files go through the disk loader.
@inputs('MissingFiles', 'name, removed, extra', [(name, name, removed, extra) for name, removed, extra in (
        ('missing_stamps', 'stamps.json', None), ('missing_started', 'started.json', None),
        ('combined_missing_stamps_and_sleep', 'stamps.json', 'sleep'))], lambda label: rejects(label))
def test_a_trial_with_a_missing_file_is_incomplete(reader, constructed_tree, established, name, removed, extra):
    copy_root, _ = constructed_tree('fault-' + name)
    directory = copy_root / 'trials/instrumented/O1/rapid/0'
    (directory / removed).unlink()
    expected = {removed.replace('.json', '') + '_missing'}
    if extra:
        value = json.loads((directory / 'conditions.json').read_text()); value['sleep_difference_ns'] = 9_000_000
        (directory / 'conditions.json').write_text(json.dumps(value)); expected.add('sleep_overlapped')
    rows, _ = reader.read_artifacts(copy_root, write=False)
    row = next(r for r in rows['rows'] if r['cell'] == 'O1' and r['app'] == 'instrumented' and r['index'] == 0)
    assert row['status'] == 'incomplete' and codes(row) == expected, (name, row['status'], codes(row))
    established(status=row['status'], codes=sorted(codes(row)))


@pytest.fixture
def comparison_tree(temporary, pw_inputs, reader, clock_pair):
    """Write a comparison run's receipts into a tree of this item's own: three baseline and three candidate
    ordinary trials, the last candidate's exit watch overlapping its held interval, two pairs required. The
    tree is registered, and so captured as constructed, before the item reads it."""
    root = temporary('pw-pilot-') / 'constructed-comparison'
    for index in range(3):
        for app in reader.PAIR_APPS:
            bundle = ordinary_bundle(index=index)
            bundle['trial']['app'] = app
            if (app, index) == ('candidate', 2):
                watch_inside_held(bundle)
            write_bundle(root, bundle)
    (root / 'schedule.json').write_text(json.dumps(dict(required={f'{app}/O1/rapid': 2 for app in reader.PAIR_APPS},
                                                        comparison=dict(COMPARISON, pairs_required=2))))
    write_calibration(clock_pair, root)
    pw_inputs.track(root)
    return root


ROUND_TRIP = 'comparison receipts through the loader: separate app groups, two pairs, the excluded trial unpaired, matched-pair section'


@control('ComparisonRoundTrip', accepts(ROUND_TRIP))
def test_baseline_and_candidate_stay_separate_groups_with_two_pairs(reader, comparison_tree, established):
    root = comparison_tree
    decomposition, summary = reader.read_artifacts(root)
    assert [(g['app'], g['counts']['accepted']) for g in summary['groups']] == [('baseline', 3), ('candidate', 2)], summary['groups']
    (entry,) = summary['pairs']['entries']
    assert [p['index'] for p in entry['pairs']] == [0, 1] and len(summary['pairs']['unpaired']) == 2
    assert all(verdicts(v) == (False, False, False, False) for v in (*entry['components'].values(), *entry['waits'].values()))
    assert verdicts(entry['whole_request']) == (None, False, None, False)
    assert [r['app'] for r in summary['observer_overlap']] == ['baseline'] * 3 + ['candidate'] * 3
    established()


@control('ComparisonRoundTrip', accepts(ROUND_TRIP))
def test_each_pairs_uncertainty_is_the_sum_of_its_two_trials(reader, comparison_tree, established):
    root = comparison_tree
    decomposition, summary = reader.read_artifacts(root)
    (entry,) = summary['pairs']['entries']
    # Each pair's uncertainty is the sum of its two trials' own uncertainties.
    side = {(r['app'], r['index']): r['phases'][0]['arrival_detection']['uncertainty_ns'] for r in decomposition['rows']}
    combined = [side[('baseline', i)] + side[('candidate', i)] for i in range(2)]
    assert [r['combined_uncertainty'] for r in entry['components']['p0.arrival_to_observation']['pairs']] == combined
    established()


@control('ComparisonRoundTrip', accepts(ROUND_TRIP))
def test_the_markdown_summary_has_the_matched_pairs_section(reader, comparison_tree, established):
    root = comparison_tree
    decomposition, summary = reader.read_artifacts(root)
    (entry,) = summary['pairs']['entries']
    side = {(r['app'], r['index']): r['phases'][0]['arrival_detection']['uncertainty_ns'] for r in decomposition['rows']}
    combined = [side[('baseline', i)] + side[('candidate', i)] for i in range(2)]
    text = (root / 'summary.md').read_text()
    for needle in ('## Matched pairs', '### O1 rapid (Battery Power, lowpowermode 0)', 'Pairs: 2 of 2 required (repetitions 0, 1)',
                   "candidate r2 excluded (not accepted on both sides) ['observer_overlap']",
                   f'| p0.arrival_to_observation | no / no | no / no / no | 0.0 / 0.0 | r0 0.0 ± {combined[0] / 1000:.1f} (detected/detected); '
                   f'r1 0.0 ± {combined[1] / 1000:.1f} (detected/detected) |',
                   '| p0.release_wait | no / no | no / no / no | 0 / 0 | r0 0 ± 0; r1 0 ± 0 |', 'Whole request (spread baseline / candidate 0.00 ms / 0.00 ms): improves n/a / no; worsens n/a / no / no; r0 0.00 ms; r1 0.00 ms.', '| p0.release_to_ack | 9.4 | 2.6 | 6.8 | yes |',
                   'Candidate faster in 0, slower in 0, equal in 2 pairs.', '| grace_timeouts | 0 / 0 | r0 0 -> 0; r1 0 -> 0 |',
                   'Grace waits (key 5), sum over accepted trials: grace_timeouts 0 (max per trial 0)',
                   '| w0.terminal_to_exit_request | no / no | no / no / no |',
                   '| w0.scan_visits_per_pass_activation | withheld | r0 0/0 -> 0/0 (no_passes); r1 0/0 -> 0/0 (no_passes) '
                   '[withheld: 0 established of 2 required pairs; absent, without passes or refused in 2] |',
                   '| w0.scan_zero_visit_passes (sum baseline / candidate 0 / 0) | no verdict | r0 0 -> 0; r1 0 -> 0 |',
                   'w0 inbound_count 0: passes_activation 0 (0)',
                   '| ordinary_sentinel | r0 2, 4.35 ms -> 2, 4.35 ms; r1 2, 4.35 ms -> 2, 4.35 ms |', '## baseline O1 rapid', '## candidate O1 rapid'):
        assert needle in text, needle
    established()


# ---- the stager's identity rules, stopped before worker substitution or signing ---------

class Reached(Exception):
    """The stager passed both identity checks and reached the source-tree record."""


DECLARED, OTHER = 'ab' * 32, 'cd' * 32
IDENTITY_TEXT = "stager identity read from a tree's contract.py text; malformed, missing or duplicated constants refused"


@pytest.fixture
def candidate_tree(temporary, pw_inputs):
    """A constructed source tree of this item's own that declares DECLARED; returns the tree and its contract.py."""
    tree = temporary('pw-pilot-stager-') / 'candidate-tree'
    (tree / 'tests/lib').mkdir(parents=True)
    contract = tree / 'tests/lib/contract.py'
    contract.write_text(f'WORKER_IDENTITY = "{DECLARED}"\n')
    pw_inputs.track(tree)
    return tree, contract


@control('Stager', accepts(IDENTITY_TEXT))
def test_the_identity_is_read_from_the_trees_contract_text(stamps, candidate_tree, established):
    tree, _ = candidate_tree
    assert stamps.tree_worker_identity(tree) == DECLARED
    established()


@inputs('Stager', 'text', [
    ('missing', ''),
    ('duplicated', f'WORKER_IDENTITY = "{DECLARED}"\nWORKER_IDENTITY = "{OTHER}"\n'),
    ('single-quoted', f"WORKER_IDENTITY = '{DECLARED}'\n"),
    ('one-digit-short', f'WORKER_IDENTITY = "{DECLARED[:-1]}"\n'),
], accepts(IDENTITY_TEXT))
def test_a_missing_malformed_or_duplicated_identity_is_refused(stamps, candidate_tree, established, text):
    tree, contract = candidate_tree
    contract.write_text(text)
    with pytest.raises(AssertionError, match='worker identities'):
        stamps.tree_worker_identity(tree)
    established()


@pytest.fixture
def stage(request, pw_equipment, pw_inputs, stamps, replace):
    """Stage a constructed candidate app from a constructed source tree, host and stand-in worker.

    The inputs and the staged copy stay under this item's `artifacts/stager/<identity>/`. The stager's two
    commands, the `ditto` copy and the stand-in worker's `--version`, are real: its command helper is
    replaced by one that launches them at the engine's supervised boundary with the stager's own receipt
    directory as the command's artifact directory, so the stager reads back the output the command's owner
    wrote. `tree_commit` raises `Reached`, which ends the attempt before worker substitution or signing.

    These identity controls never install or sign a runner. Their owned output is classified as durable so
    that a temporary source checkout reaches the same identity boundary; this does not exercise
    staging-path admission."""
    base = (pw_equipment.artifacts / 'stager' / request.node.get_closest_marker('pw_id').args[0]).resolve()
    tree = base / 'candidate-tree'
    (tree / 'tests/lib').mkdir(parents=True)
    (tree / 'tests/lib/contract.py').write_text(f'WORKER_IDENTITY = "{DECLARED}"\n')
    app = base / 'source/PolicyWitness.app'
    (app / stamps.EQUIPMENT).parent.mkdir(parents=True)
    host = base / 'host/PWRunner'
    host.parent.mkdir()
    host.write_bytes(b'constructed host\n')
    host.with_name('host-build.json').write_text(json.dumps(dict(kind='instrumented', output=dict(sha256=hashlib.sha256(b'constructed host\n').hexdigest()))))
    worker = base / 'worker/pw-probe-runner-stamps'
    worker.parent.mkdir()

    def supervised(out, argv, *, timeout=30, check=True, env=None):
        out.mkdir(parents=True)
        pw_inputs.capture_tracked('before command')
        receipt = pw_equipment.command(argv, out, timeout, env=env)
        if check and receipt['returncode'] != 0:
            raise AssertionError(f'command failed: {out}: {(out / "stderr").read_text()}')
        return dict(argv=list(map(str, argv)), returncode=receipt['returncode'], harness_timeout=False)

    def reached(tree, receipts):
        raise Reached()

    def attempt(name, equipment, reported):
        (app / stamps.EQUIPMENT).write_text(json.dumps(dict(worker_identity=equipment)))
        worker.write_text(f'#!/bin/sh\necho "pw-probe-runner abi_identity={reported}"\n'); worker.chmod(0o755)
        pw_inputs.track(base)
        try:
            stamps.stage(app, base / name / 'staging/candidate', 'constructed identity', host, worker, worker, True, tree)
        except Reached:
            return 'reached'
        except AssertionError as error:
            return str(error)
        raise AssertionError('stage completed on constructed inputs')

    replace(stamps, 'command', supervised)
    replace(stamps, 'tree_commit', reached)
    replace(stamps, '_volatile', lambda path: not path.is_relative_to(base))
    return attempt


@control('Stager', accepts("candidate stager refuses an app whose equipment identity differs from its tree's"), commands='recorded')
def test_an_app_whose_equipment_identity_differs_is_refused(stage, established):
    refused = stage('equipment-mismatch', OTHER, DECLARED)
    assert refused.startswith(f'app equipment identity {OTHER} is not') and DECLARED in refused, refused
    established()


@control('Stager', accepts('candidate stager refuses a stamp worker reporting another identity'), commands='recorded')
def test_a_stamp_worker_reporting_another_identity_is_refused(stage, established):
    refused = stage('worker-mismatch', DECLARED, OTHER)
    assert f'abi_identity={OTHER}' in refused and f'declared {DECLARED}' in refused, refused
    established()


@control('Stager', accepts('agreeing identities reach the source-tree record; staging-path classification is constructed'), commands='recorded')
def test_agreeing_identities_reach_the_source_tree_record(stage, established):
    assert stage('agreeing', DECLARED, DECLARED) == 'reached'
    established()
