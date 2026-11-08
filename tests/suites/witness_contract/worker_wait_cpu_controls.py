"""Independent controls for neutral held CPU evidence, including quiet workers."""
import copy
import json
from pathlib import Path
import sys
from check_held_phase_footprint import check_wait_measurement, check_measurement
from held_phase_footprint_controls import baseline


def main(out):
    busy=baseline(); check_wait_measurement(busy); check_measurement(busy)
    quiet=copy.deepcopy(busy)
    quiet['after']['samples'][0].update(user_ticks=0,user_ns=0)
    quiet['deltas_ns'][0]=0
    check_wait_measurement(quiet)
    try: check_measurement(quiet)
    except AssertionError: pass
    else: raise AssertionError('historical busy-worker meaning was weakened')
    mutations={
        'wrong_generation':lambda r:r['after']['samples'][0]['generation_after'].update(start_sec=999),
        'missing_effect':lambda r:r['effects'].pop(),
        'early_attempt':lambda r:r['effects'][0].update(target_unchanged=False),
        'release_before_endpoint':lambda r:r['release']['before'].update(begin_ns=1),
        'counter_error':lambda r:r['after']['samples'][0]['calls']['rusage'].update(rc=-1),
        'negative_counter':lambda r:r['before']['samples'][0].update(system_ns=1,system_ticks=1),
        'invented_delta':lambda r:r['deltas_ns'].__setitem__(0,123),
        'missing_worker':lambda r:r['after']['samples'].pop(0),
        'lost_sensitivity':lambda r:r['after']['samples'][3].update(user_ticks=0,user_ns=0),
        'short_interval':lambda r:r.update(requested_ns=1),
        'sampling_skew':lambda r:r['before'].update(end_ns=100_000_000),
        'sleep_overlap':lambda r:r['clock_after'].update(uptime_ns=1),
        'unbound_hold':lambda r:r['held_generations']['workers'][0]['generation_before'].update(start_sec=999),
    }
    rejected=[]
    for name,edit in mutations.items():
        bad=copy.deepcopy(quiet);edit(bad)
        if name=='lost_sensitivity': bad['deltas_ns'][3]=0
        try: check_wait_measurement(bad)
        except (AssertionError,KeyError,ValueError,TypeError,IndexError): rejected.append(name)
        else: raise AssertionError('bad quiet-worker receipt accepted: '+name)
    Path(out,'controls.json').write_text(json.dumps(dict(accepted=['busy','quiet'],rejected=rejected,
        scope='constructed evidence validity only; no live CPU benefit or production timing claim'),indent=2)+'\n')
    print(f'busy and quiet workers accepted; {len(rejected)} corrupt neutral CPU receipts refused; historical oracle preserved')


if __name__=='__main__': main(*sys.argv[1:])
