"""Actor timing qualification on the signed candidate.

Finite, uninjected actor-form workloads run through the public CLI with the
actual polling implementation, every actor launched before the first phase,
and the host and validator doing their normal work: three matched rounds of
one-, three- and eight-actor specimens with the same aggregate query/file
workload distributed over the actors; a workload at the admitted aggregate
action and phase limits; and the principal re-delegation and positive
calibration shapes with five further live actors servicing ordinary phases.
Every run must complete without budget exhaustion with at least a quarter of
each effective actor-form allowance remaining at the largest charged interval,
each measured in its own accounting scope. The intervals are host scheduling
and publication measurements, never native call latency. Hardware, OS, power
and load are recorded; core counts alone do not establish capacity.
"""
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from witness_capture import capture  # noqa: E402
from contract import REQUEST_SCHEMA  # noqa: E402
import extension_actors  # noqa: E402
from worker_exit_witness import worker_exit_witness  # noqa: E402

pw, directory = sys.argv[1:]
out = Path(directory)
out.mkdir(parents=True, exist_ok=True)
LIMITS = {row['id']: row['value'] for row in json.loads((ROOT / 'docs/limits.json').read_text())['limits']}
MARGIN = 0.25
ALLOW_DEFAULT = '(version 1)(allow default)'
AGGREGATE_ACTIONS = 24


def sysctl(name):
    try:
        return subprocess.run(['/usr/sbin/sysctl', '-n', name], capture_output=True, text=True, timeout=10).stdout.strip() or None
    except OSError:
        return None


def environment():
    names = ['hw.ncpu', 'hw.physicalcpu', 'hw.logicalcpu', 'hw.nperflevels', 'hw.perflevel0.name', 'hw.perflevel0.physicalcpu',
             'hw.perflevel1.name', 'hw.perflevel1.physicalcpu', 'hw.memsize', 'machdep.cpu.brand_string', 'kern.osproductversion']
    power = None
    try:
        power = subprocess.run(['/usr/bin/pmset', '-g', 'batt'], capture_output=True, text=True, timeout=10).stdout.strip()
    except OSError:
        pass
    return {'macos': platform.mac_ver()[0], 'kernel': os.uname().release, 'machine': os.uname().machine,
            'sysctl': {name: sysctl(name) for name in names}, 'power': power, 'loadavg': os.getloadavg(),
            'euid': os.geteuid()}


def read(step_id, target):
    return extension_actors.read_probe(step_id, target)


def distributed(name, actor_count, target, actions=AGGREGATE_ACTIONS, phase_count=None):
    """The constant aggregate workload split over `actor_count` apply actors:
    `actions` fresh reads in `phase_count` phases, visiting the actors in turn."""
    phase_count = phase_count or min(LIMITS['actor_phases'], max(actor_count, 3))
    actors = [extension_actors.apply_actor(f'w{i}', ALLOW_DEFAULT) for i in range(actor_count)]
    per_phase = [actions // phase_count + (1 if i < actions % phase_count else 0) for i in range(phase_count)]
    phases, step = [], 0
    for index, count in enumerate(per_phase):
        actor = actors[index % actor_count]['actor_id']
        phases.append({'phase_id': f'p{index}', 'actor_id': actor,
                       'actions': [read(f's{step + k}', target) for k in range(count)]})
        step += count
    return {'schema_version': REQUEST_SCHEMA, 'specimen_id': name, 'actors': actors, 'phases': phases}


def with_bystanders(spec, count, target):
    """Add `count` live apply actors, each servicing one bounded ordinary phase
    placed between the specimen's own phases."""
    bystanders = [extension_actors.apply_actor(f'x{i}', ALLOW_DEFAULT) for i in range(count)]
    bystander_phase = lambda index: {'phase_id': f'bystander_{index}', 'actor_id': bystanders[index]['actor_id'],
                                     'actions': [read(f'bystander_read_{index}', target)]}
    phases = []
    for index, phase in enumerate(spec['phases']):
        phases.append(phase)
        if index < count:
            phases.append(bystander_phase(index))
    # Every bystander services one phase even when the specimen has fewer
    # phases than bystanders.
    phases += [bystander_phase(index) for index in range(len(spec['phases']), count)]
    spec = dict(spec, actors=spec['actors'] + bystanders, phases=phases)
    assert len(spec['actors']) <= LIMITS['actors'] and len(phases) <= LIMITS['actor_phases'], (len(spec['actors']), len(phases))
    return spec


def charged(wait):
    """Milliseconds charged to a host wait: elapsed minus its excluded interval."""
    if not isinstance(wait, dict) or type(wait.get('elapsed_ms')) is not int:
        return None
    return wait['elapsed_ms'] - (wait.get('excluded_ms') or 0)


def intervals(runner):
    schedule = runner['schedule']
    phases = runner['phases']
    timing = [p.get('visit_timing') or {} for p in phases]
    collection = [t.get('collection_ms') for t in timing if t.get('collection_ms') is not None]
    release = [t.get('arrival_to_release_ms') for t in timing if t.get('arrival_to_release_ms') is not None]
    arrival = [t.get('activation_to_arrival_ms') for t in timing if t.get('activation_to_arrival_ms') is not None]
    completion = [t.get('release_to_completion_ms') for t in timing if t.get('release_to_completion_ms') is not None]
    exchange = [t['recipient_wait']['elapsed_ms'] for t in runner.get('transfers') or []
                if isinstance(t.get('recipient_wait'), dict) and type(t['recipient_wait'].get('elapsed_ms')) is int]
    setup = schedule.get('setup_wait') or {}
    execution = schedule.get('execution_wait') or {}
    return {
        'setup_ms': setup.get('elapsed_ms'), 'execution_charged_ms': charged(execution),
        'execution_elapsed_ms': execution.get('elapsed_ms'), 'collection_total_ms': sum(collection),
        'collection_max_ms': max(collection, default=0), 'arrival_max_ms': max(arrival, default=0),
        'release_wait_max_ms': max(release, default=0), 'completion_max_ms': max(completion, default=0),
        'exchange_max_ms': max(exchange, default=0),
        'total_ms': (setup.get('elapsed_ms') or 0) + (execution.get('elapsed_ms') or 0),
        'phases': len(phases), 'actors': len(runner['actors']),
    }


def margins(measured):
    """Each measurement against its own allowance: the fraction remaining."""
    scopes = {
        'setup_ms': LIMITS['actor_setup_allowance'], 'execution_charged_ms': LIMITS['actor_execution_allowance'],
        'collection_total_ms': LIMITS['actor_collection_allowance'], 'release_wait_max_ms': LIMITS['actor_release_wait'],
        'exchange_max_ms': LIMITS['actor_exchange_allowance'], 'total_ms': LIMITS['actor_lifetime_cutoff'],
    }
    return {name: {'observed_ms': measured[name], 'allowance_ms': allowance,
                   'remaining': None if measured[name] is None else round(1 - measured[name] / allowance, 4)}
            for name, allowance in scopes.items()}


def completed_without_exhaustion(envelope, runner, spec):
    assert runner['execution_form'] == 'actors' and runner['normalized_outcome'] == 'finished', (runner['normalized_outcome'], runner.get('error'))
    witnessed, reason = worker_exit_witness(envelope)
    assert witnessed, reason
    assert runner['schedule'].get('cancelled') is None, runner['schedule']
    assert len(runner['actors']) == len(spec['actors']), (len(runner['actors']), len(spec['actors']))
    for actor in runner['actors']:
        assert actor['setup_status'] in ('applied', 'unapplied_declared'), actor
        assert actor['subprocess']['reaped'] and actor['subprocess']['exit_code'] == 0, actor['actor_id']
    for phase in runner['phases']:
        assert phase['arrival_observed'] and phase['completion_observed'], phase['phase_id']
        assert phase['collection_status'] not in ('budget_exhausted', 'clock_unavailable'), phase
        assert phase['ordering']['protocol_violations'] == [], phase
    for step in runner['steps']:
        assert step['attempt']['result_source'] == 'worker', step['step_id']


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def run(name, spec, target_bytes=None):
    # The harness's reaped children are the controller and its client helper;
    # the host and actors are launchd's descendants and are not in this figure.
    cpu_before, load_before = children_cpu(), os.getloadavg()
    envelope, runner = capture(pw, out, name, spec)
    completed_without_exhaustion(envelope, runner, spec)
    measured = intervals(runner)
    result = {'specimen_id': spec['specimen_id'], 'actors': len(spec['actors']), 'phases': len(spec['phases']),
              'actions': sum(len(p['actions']) for p in spec['phases']), 'measured': measured, 'margins': margins(measured),
              'pids': [a['launch']['pid'] for a in runner['actors']], 'app_build': envelope['build'],
              'harness_children_cpu_s': round(children_cpu() - cpu_before, 4), 'loadavg_before': load_before,
              'loadavg_after': os.getloadavg(), 'runner_kind': envelope['data'].get('runner_kind')}
    short = [k for k, m in result['margins'].items() if m['remaining'] is not None and m['remaining'] < MARGIN]
    result['margin_shortfalls'] = short
    return result, runner


report = {'environment': environment(), 'allowances': {k: LIMITS[k] for k in (
    'actor_setup_allowance', 'actor_execution_allowance', 'actor_collection_allowance', 'actor_release_wait',
    'actor_exchange_allowance', 'actor_lifetime_cutoff')}, 'margin': MARGIN, 'rounds': [], 'limits_workload': None,
    'redelegation_eight': None, 'calibration_eight': None}
shortfalls = []

with tempfile.TemporaryDirectory(prefix='pw-actor-timing-', dir='/private/tmp') as scratch:
    target = Path(scratch) / 'target'
    target.write_bytes(b'PW actor timing target\n')

    # ---- Three matched rounds of one, three and eight actors.
    for round_index in range(3):
        for count in (1, 3, 8):
            name = f'round{round_index}_actors{count}'
            result, _ = run(name, distributed(name, count, target))
            result['round'] = round_index
            report['rounds'].append(result)
            shortfalls += [(name, s) for s in result['margin_shortfalls']]

    # ---- The admitted aggregate action and phase limits over eight actors.
    limits_spec = distributed('limits_workload', 8, target, actions=256, phase_count=LIMITS['actor_phases'])
    assert sum(len(p['actions']) for p in limits_spec['phases']) == 256 and len(limits_spec['phases']) == LIMITS['actor_phases']
    result, _ = run('limits_workload', limits_spec)
    report['limits_workload'] = result
    shortfalls += [('limits_workload', s) for s in result['margin_shortfalls']]

    # ---- The principal shape and the calibration with five further live actors.
    principal = with_bystanders(extension_actors.redelegation_specimen(target, schema_version=REQUEST_SCHEMA,
                                                                       specimen_id='redelegation_eight'), 5, target)
    result, runner = run('redelegation_eight', principal)
    events = {e['step_id']: e for e in runner['extension_events']}
    transfers = {t['delivery_ref']: t for t in runner['transfers']}
    result['chain'] = {'a_issue': events['a_issue'].get('native_nonnull'), 'db': transfers['db']['status'],
                       'b_consume': events['b_consume_first'].get('native_result'), 'b_issue': events['b_issue'].get('native_nonnull'),
                       'dc': transfers['dc']['status'], 'c_consume': events['c_consume_second'].get('native_result')}
    # The same authority-chain assertions as the acceptance case's calibration:
    # every link published and bound to its actor; eight live actors do not
    # change the chain's associations.
    assert all(e['result_published'] for e in runner['extension_events']), events
    assert transfers['dc']['token_ref'] == 'tb' and events['b_issue']['actor_id'] == 'B', transfers['dc']
    report['redelegation_eight'] = result
    shortfalls += [('redelegation_eight', s) for s in result['margin_shortfalls']]

    calibration = {
        'schema_version': REQUEST_SCHEMA, 'specimen_id': 'calibration_eight',
        'actors': [extension_actors.unapplied_actor('A'), extension_actors.apply_actor('B', extension_actors.C_POLICY)],
        'phases': [
            {'phase_id': 'b_before', 'actor_id': 'B', 'actions': [read('b_read_before', target)]},
            {'phase_id': 'supply', 'actor_id': 'A', 'actions': [extension_actors.issue('a_issue', 'ta', target),
                                                                 extension_actors.transfer('a_to_b', 'ta', 'B', 'db')]},
            {'phase_id': 'b_use', 'actor_id': 'B', 'actions': [extension_actors.consume('b_consume', 'db', 'hb'),
                                                                read('b_read_after', target), extension_actors.release('b_release', 'hb')]},
        ]}
    calibration = with_bystanders(calibration, 6, target)
    result, runner = run('calibration_eight', calibration)
    a_issue, consume = next(e for e in runner['extension_events'] if e['step_id'] == 'a_issue'), next(e for e in runner['extension_events'] if e['step_id'] == 'b_consume')
    after = next(s for s in runner['steps'] if s['step_id'] == 'b_read_after')['attempt']
    result['positive'] = {'a_issue': a_issue.get('native_nonnull'), 'transfer': runner['transfers'][0]['status'],
                          'b_consume': consume.get('native_result'), 'b_read_after_rc': after['rc']}
    assert a_issue.get('native_nonnull') is True and runner['transfers'][0]['status'] == 'delivered', result['positive']
    assert consume['status'] == 'returned' and consume['native_result'] != -1 and after['rc'] == 0, result['positive']
    report['calibration_eight'] = result
    shortfalls += [('calibration_eight', s) for s in result['margin_shortfalls']]

report['margin_shortfalls'] = shortfalls
report['qualified'] = not shortfalls
(out / 'report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
largest = {}
for result in report['rounds'] + [report['limits_workload'], report['redelegation_eight'], report['calibration_eight']]:
    for name, margin in result['margins'].items():
        if margin['observed_ms'] is not None and margin['observed_ms'] >= largest.get(name, (0, ''))[0]:
            largest[name] = (margin['observed_ms'], result['specimen_id'])
assert not shortfalls, ('actor timing qualification failed: allowance margins below the required quarter', shortfalls)
print('actor profile qualified on this equipment: largest charged intervals '
      + ', '.join(f'{name} {ms} ms ({who})' for name, (ms, who) in sorted(largest.items())))
