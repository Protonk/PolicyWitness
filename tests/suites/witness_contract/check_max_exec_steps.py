"""Every exec step of a maximum plan spawns.

256 exec steps of /usr/bin/true under an allow-all policy. Each exec step
holds four descriptors before the sandbox applies, so under launchd's default
soft limit of 256 only the first 62 could open their pipes and the rest failed
at pipe() with EMFILE. The worker now raises its soft limit to fit the plan
first, so every attempt must report a child that exited cleanly and no error.
"""
import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture

STEPS = 256
TARGET = '/usr/bin/true'


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory)
    ids = [f'e{i:03d}' for i in range(STEPS)]
    specimen = {
        'schema_version': 3, 'specimen_id': secrets.token_hex(12),
        'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
        'probe_plan': [{'step_id': step_id,
                        'sandbox_check': {'operation': 'process-exec*', 'filter': {'kind': 'path', 'value': TARGET}},
                        'attempt': {'kind': 'exec', 'action': 'spawn', 'target': TARGET}}
                       for step_id in ids],
    }
    run = RunCapture(pw, out / 'run', specimen, cli_args=['--timeout-ms', '120000', '--no-log-capture'])
    with run:
        rc = run.wait(timeout=150)
        envelope = run.load_json()
    assert rc == 0, rc
    data = envelope['data']
    client = data['runner_client']
    assert client['stdout_truncated'] is False and client['stdout_parse_error'] is None, client
    runner = data['runner_result']
    assert runner['normalized_outcome'] == 'ok', runner['normalized_outcome']
    assert runner['runner_subprocess']['exit_code'] == 0, runner['runner_subprocess']
    assert [step['step_id'] for step in runner['steps']] == ids, 'step identity or count lost'
    unspawned = []
    for step in runner['steps']:
        check, attempt = step['sandbox_check'], step['attempt']
        assert check['outcome'] == 'allow', check
        if not (attempt['outcome'] == 'ok' and attempt['rc'] == 0 and attempt['child_pid'] > 0
                and attempt['child_exit_code'] == 0 and attempt['child_term_signal'] == 0
                and attempt.get('error') is None):
            unspawned.append({'step_id': step['step_id'], 'attempt': attempt})
    (out / 'observations.json').write_text(json.dumps({
        'steps': STEPS, 'unspawned': unspawned,
        'runner_reply_bytes': client['stdout_bytes_received']}, indent=2) + '\n')
    assert not unspawned, f'{len(unspawned)} exec steps did not spawn a clean child; first: {unspawned[0]}'
    print(f'all {STEPS} exec steps spawned and exited cleanly; reply {client["stdout_bytes_received"]} bytes', flush=True)


if __name__ == '__main__':
    main()
