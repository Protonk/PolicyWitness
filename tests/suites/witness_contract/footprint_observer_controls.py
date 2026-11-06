"""Live sensitivity and independently corrupted observer receipt controls."""
import copy
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from footprint_observer import FootprintObserver, generation, require_sample, validate_batch
from control import ExitObserver


def rejected(value):
    try:
        validate_batch(value)
    except (AssertionError, KeyError, TypeError):
        return
    raise AssertionError('corrupt observer receipt accepted')


def self_cpu_ns(receipt):
    return sum(receipt[k + '_sec'] * 1_000_000_000 + receipt[k + '_usec'] * 1000
               for k in ('user', 'system'))


def check_cpu_agreement(external_delta, self_delta, outer_slack):
    # Timeval accounting is rounded to microseconds; allow 5ms accounting
    # variation, plus the observed outer scheduling brackets. This compares
    # independent APIs and would reject a raw24MHz counter labelled nanoseconds.
    assert self_delta >= 20_000_000, 'insufficient busy CPU for unit sensitivity'
    assert -5_000_000 <= external_delta - self_delta <= outer_slack + 5_000_000, (
        external_delta, self_delta, outer_slack)


def main(binary, output):
    output = Path(output)
    with FootprintObserver(binary, output / 'observer') as observer:
        initial_clock = observer.clock()
        with observer.spawn_control('allocation') as child:
            before = require_sample(observer.inspect(child.pid))
            identity = generation(before)
            exit_observer = ExitObserver()
            try:
                exit_observer.watch(child.pid)
                require_sample(observer.inspect(child.pid), identity)
                touched = child.touch(32 * 1024 * 1024)
                after = require_sample(observer.inspect(child.pid), identity)
                assert after['resident_bytes'] > before['resident_bytes'], (before, after)
                assert after['phys_footprint_bytes'] > before['phys_footprint_bytes'], (before, after)
            except BaseException:
                exit_observer.close()
                raise
        try:
            exit_observer.assert_stopped()
            absent = observer.inspect(child.pid)
            assert absent['status'] != 'ok' or generation(absent) != identity, absent
        finally:
            exit_observer.close()
        with observer.spawn_control('busy') as busy, observer.spawn_control('sleep') as sleeper:
            first = observer.sample([busy.pid, sleeper.pid])
            for s in first['samples']:
                require_sample(s)
            self_first = busy.cpu()
            time.sleep(0.35)
            self_second = busy.cpu()
            second = observer.sample([busy.pid, sleeper.pid])
            deltas = []
            for a, b in zip(first['samples'], second['samples']):
                require_sample(b, generation(a))
                delta = b['user_ns'] + b['system_ns'] - a['user_ns'] - a['system_ns']
                assert delta >= 0
                deltas.append(delta)
            assert deltas[0] > deltas[1], deltas
            self_delta = self_cpu_ns(self_second) - self_cpu_ns(self_first)
            outer_slack = ((self_first['end_ns'] - first['samples'][0]['begin_ns']) +
                           (second['samples'][0]['end_ns'] - self_second['begin_ns']))
            check_cpu_agreement(deltas[0], self_delta, outer_slack)
            raw_delta = sum(second['samples'][0][k + '_ticks'] - first['samples'][0][k + '_ticks']
                            for k in ('user', 'system'))
            # On a unit timebase raw and normalized values legitimately agree.
            conversion_control = first['samples'][0]['timebase_numer'] != first['samples'][0]['timebase_denom']
            if conversion_control:
                try:
                    check_cpu_agreement(raw_delta, self_delta, outer_slack)
                except AssertionError:
                    pass
                else:
                    raise AssertionError('raw-tick CPU unit error escaped independent calibration')
        final_clock = observer.clock()
        # Bracketing uncertainty bounds the apparent sleep difference.
        sleep_difference = ((final_clock['continuous_ns'] - initial_clock['continuous_ns']) -
                            (final_clock['uptime_ns'] - initial_clock['uptime_ns']))
        bracket_uncertainty = sum(c['end_ns'] - c['begin_ns'] for c in (initial_clock, final_clock))
        assert sleep_difference <= bracket_uncertainty + 1_000_000, sleep_difference
        validate_batch(second)
        faults = []
        bad = copy.deepcopy(second); bad['cpu_unit'] = 'ticks'; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['user_ns'] += 1; faults.append(bad)
        bad = copy.deepcopy(second); del bad['samples'][0]['user_ns']; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['generation_after']['start_usec'] += 1; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['end_ns'] = bad['samples'][0]['begin_ns'] - 1; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['calls']['rusage']['rc'] = -1; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['status'] = 'error'; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['pid'] += 1; faults.append(bad)
        bad = copy.deepcopy(second); bad['samples'][0]['begin_ns'] = True; faults.append(bad)
        for fault in faults:
            rejected(fault)
        receipt = {'version': 1, 'allocation': {'before': before, 'after': after, 'ack': touched,
                    'exited_generation': identity, 'post_exit_inspection': absent,
                    'independent_exit': 'EVFILT_PROC NOTE_EXIT'},
                   'cpu': {'first': first, 'second': second, 'busy_delta_ns': deltas[0],
                           'getrusage_first': self_first, 'getrusage_second': self_second,
                           'getrusage_delta_ns': self_delta, 'outer_slack_ns': outer_slack,
                           'raw_ticks_delta': raw_delta, 'conversion_control_applicable': conversion_control,
                           'sleep_delta_ns': deltas[1], 'requested_interval_s': 0.35},
                   'clock_start': initial_clock, 'clock_end': final_clock,
                   'sleep_difference_ns': sleep_difference, 'clock_bracket_uncertainty_ns': bracket_uncertainty,
                   'rejected_controls': len(faults),
                   'interpretation': 'Machine-specific sensitivity facts; no universal CPU quantum or memory threshold.'}
        (output / 'controls.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('observer live sensitivity and receipt rejection controls passed')


if __name__ == '__main__':
    main(*sys.argv[1:])
