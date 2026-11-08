"""Independent controls for neutral held CPU evidence, including quiet workers."""
import copy
import json
from pathlib import Path
import sys
from check_held_phase_footprint import check_wait_measurement, check_measurement
from held_phase_footprint_controls import baseline
from worker_wait_cost import compare, source_variant


def main(out):
    busy=baseline(); check_wait_measurement(busy); check_measurement(busy)
    quiet=copy.deepcopy(busy)
    quiet['after']['samples'][0].update(user_ticks=0,user_ns=0)
    quiet['deltas_ns'][0]=0
    check_wait_measurement(quiet)
    fifth=copy.deepcopy(quiet); fifth['repetition']=4; check_wait_measurement(fifth)
    try: check_measurement(fifth)
    except AssertionError: pass
    else: raise AssertionError('historical repetition contract was weakened')
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
    rows=[]
    for regime in ('rapid','idle'):
        for repetition in range(5):
            for side,receipt in (('baseline',busy),('candidate',quiet)):
                r=copy.deepcopy(receipt);r['repetition']=repetition
                r['conditions'].update(regime=regime,side=side)
                rows.append(dict(regime=regime,repetition=repetition,side=side,measurement=r,
                                 eligible=True,power=dict(source='AC Power',lowpowermode='0')))
    assert compare(rows,'release',.1)['worthwhile_in_every_pair']
    noop=copy.deepcopy(rows)
    for r in noop:
        r['measurement']=copy.deepcopy(busy)
        r['measurement']['repetition']=r['repetition']
        r['measurement']['conditions'].update(regime=r['regime'],side=r['side'])
    assert not compare(noop,'release',.1)['worthwhile_in_every_pair'], 'no-op credited'
    contrary=copy.deepcopy(noop)
    for i in range(len(rows)-1): contrary[i]=copy.deepcopy(rows[i])
    assert not compare(contrary,'release',.1)['worthwhile_in_every_pair'], 'contrary pair concealed'
    for name,edit in {
        'missing_pair':lambda r:r.pop(),
        'duplicate_side':lambda r:r[-1].update(side='baseline'),
        'pacing_exclusion':lambda r:r[-1].update(eligible=False),
        'power_mismatch':lambda r:r[-1]['power'].update(source='Battery Power'),
        'relabelled_repetition':lambda r:r[-1]['measurement'].update(repetition=0),
        'relabelled_regime':lambda r:r[-1]['measurement']['conditions'].update(regime='rapid'),
        'combined_pair_faults':lambda r:(r[-1].update(eligible=False),r[0]['measurement'].update(actual_min_ns=1)),
    }.items():
        bad=copy.deepcopy(rows);edit(bad)
        try:compare(bad,'release',.1)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('bad comparison accepted: '+name)
    source=(Path(__file__).resolve().parents[3]/'controller/tools/pw_probe_runner/pw_probe_runner.c').read_text()
    for role in ('release','activation'):
        assert source_variant(source,role,'baseline')==source
        hint=source_variant(source,role,'hint10000')
        assert hint.count('i < 10000u')==1 and hint.count('i < 1000u')==2
        timed=source_variant(source,role,'wfet')
        assert timed.count('        cost_wait(timing, now,')==1 and timed.count('i < 1000u')==2
        assert timed.count('    cost_setup();')==1
    Path(out,'controls.json').write_text(json.dumps(dict(accepted=['busy','quiet','five_pair_gain','noop_not_credited','contrary_pair_not_concealed'],rejected=rejected,
        scope='constructed evidence validity only; no live CPU benefit or production timing claim'),indent=2)+'\n')
    print(f'busy and quiet workers accepted; {len(rejected)} corrupt neutral CPU receipts refused; historical oracle preserved')


if __name__=='__main__': main(*sys.argv[1:])
