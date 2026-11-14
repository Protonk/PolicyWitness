"""Inspect three example forms on an existing app; planning observations, not acceptance.

Run with the repository's pinned Python under its checkout lock. The output
directory must not exist. No fixture is refreshed and no expectation is learned
by a production checker. Raw commands and captures stay in the chosen output.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/suites/witness_contract'))
import consumer
from check_example_round_trip import observe_target


def main():
    app, output = map(lambda arg: Path(arg).resolve(), sys.argv[1:])
    output.mkdir()
    binary = app / 'Contents/MacOS/policy-witness'

    def invoke(name, *arguments):
        command = [str(binary), *map(str, arguments)]
        result = subprocess.run(command, capture_output=True)
        (output / (name + '.command.json')).write_text(json.dumps(command) + '\n')
        (output / (name + '.stdout')).write_bytes(result.stdout)
        (output / (name + '.stderr')).write_bytes(result.stderr)
        (output / (name + '.exit')).write_text(str(result.returncode) + '\n')
        return result

    version = invoke('version', '--version')
    emission = invoke('example', 'example')
    assert version.returncode == emission.returncode == 0
    original = json.loads(emission.stdout)
    assert len(original['probe_plan']) == 3 and 'actors' not in original and 'phases' not in original
    contract = json.loads(version.stdout)['build']['contract']
    assert original['contract'] == contract
    phased = copy.deepcopy(original)
    actions = phased.pop('probe_plan')
    phased['phases'] = [dict(phase_id='initial-reads', actions=actions[:2]),
                        dict(phase_id='restricted-read', actions=actions[2:])]
    actor = copy.deepcopy(phased)
    policy = actor.pop('policy')
    actor['actors'] = [dict(actor_id='example-reader', equipment='selected',
                            sandbox=dict(mode='apply', policy=policy))]
    for phase in actor['phases']:
        phase['actor_id'] = 'example-reader'
    assert [a for p in phased['phases'] for a in p['actions']] == original['probe_plan']
    assert [a for p in actor['phases'] for a in p['actions']] == original['probe_plan']
    assert policy == phased['policy'] == original['policy']
    paths = list(dict.fromkeys(path for step in original['probe_plan']
                              for path in (step['sandbox_check']['filter']['value'], step['attempt']['target'])))
    report = {'purpose': 'planning rehearsal; outside the dispatcher; no acceptance credit',
              'build': json.loads(version.stdout)['build'], 'forms': {}}
    for name, document in (('flat', original), ('phased', phased), ('actor', actor)):
        request = output / (name + '.json')
        request.write_bytes(emission.stdout if name == 'flat' else
                            (json.dumps(document, indent=2) + '\n').encode())
        before = [observe_target(path) for path in paths]
        result = invoke(name, 'run', request)
        after = [observe_target(path) for path in paths]
        (output / (name + '.samples.json')).write_text(json.dumps({'before': before, 'after': after}, indent=2) + '\n')
        envelope = json.loads(result.stdout)
        reply = envelope['data'].get('runner_result')
        entry = {'process_status': result.returncode, 'stderr_bytes': len(result.stderr),
                 'result': envelope['result'], 'consumer_errors': consumer.validate(envelope, contract),
                 'samples_equal': before == after, 'reply_keys': list(reply or {}),
                 'dossier_keys': list(envelope['data'].get('specimen') or {}),
                 'diagnostics': envelope['data'].get('runner_sandbox_diagnostics'),
                 'phases': [], 'steps': [], 'actors': []}
        for phase in (reply or {}).get('phases', []):
            entry['phases'].append({key: phase.get(key) for key in
                                   ('phase_id', 'ordinal', 'actor_id', 'actor_visit', 'action_ids',
                                    'arrival_observed', 'completion_observed', 'collection_status')})
        for step in (reply or {}).get('steps', []):
            entry['steps'].append({key: step.get(key) for key in
                                  ('step_id', 'phase_id', 'actor_id', 'sandbox_check', 'attempt', 'comparison')})
        for record in (reply or {}).get('actors', []):
            entry['actors'].append({key: record.get(key) for key in
                                   ('actor_id', 'index', 'mode', 'setup_status', 'applied', 'application_count',
                                    'application', 'launch', 'visits', 'equipment', 'subprocess',
                                    'policy_sha256', 'policy_received_sha256')})
        report['forms'][name] = entry
    (output / 'observations.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'build': report['build'],
                      'forms': {name: {'status': row['process_status'],
                                       'consumer_errors': row['consumer_errors'],
                                       'samples_equal': row['samples_equal'],
                                       'phases': row['phases'],
                                       'steps': [(s['step_id'], s['sandbox_check']['outcome'],
                                                  s['attempt']['outcome'], s['attempt'].get('errno'))
                                                 for s in row['steps']]}
                                for name, row in report['forms'].items()}}, indent=2))


if __name__ == '__main__':
    main()
