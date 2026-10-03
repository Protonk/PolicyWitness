"""A plain run registers nothing.

The inventory covers what an install would create: the runner registry file,
the registry as `policy-witness runner list` reports it, and the launchd plist
directories. It is taken before and after one ordinary run and must be equal.
`launchctl list` labels naming PolicyWitness are retained as diagnostics only;
launchd's runtime job table is not an installation.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_capture import RunCapture  # noqa: E402
import effects  # noqa: E402

LABEL_MARKERS = ('policy-witness', 'policywitness', 'pwrunner')


def registry_path():
    override = os.environ.get('PW_RUNNER_REGISTRY')
    if override:
        return Path(override)
    return Path.home() / 'Library' / 'Application Support' / 'PolicyWitness' / 'runners.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def listing(directory):
    return sorted(entry.name for entry in directory.iterdir()) if directory.is_dir() else None


def inventory(pw):
    listed = subprocess.run([pw, 'runner', 'list'], capture_output=True, text=True, timeout=20)
    assert listed.returncode == 0, f'runner list failed: {listed.stderr}'
    reported = json.loads(listed.stdout)
    assert reported['kind'] == 'runner_registry', reported
    registry = registry_path()
    return {
        'registry_path': str(registry),
        'registry_sha256': digest(registry),
        'reported_registry': reported['data'],
        'user_launch_agents': listing(Path.home() / 'Library' / 'LaunchAgents'),
        'system_launch_agents': listing(Path('/Library/LaunchAgents')),
        'system_launch_daemons': listing(Path('/Library/LaunchDaemons')),
    }


def launchd_labels():
    try:
        listed = subprocess.run(['/bin/launchctl', 'list'], capture_output=True, text=True, timeout=20)
    except OSError as exc:
        return {'error': str(exc)}
    if listed.returncode != 0:
        return {'error': f'launchctl list exit {listed.returncode}', 'stderr': listed.stderr}
    labels = [line.split('\t')[-1] for line in listed.stdout.splitlines()[1:]]
    return {'labels': sorted(label for label in labels
                             if any(marker in label.lower() for marker in LABEL_MARKERS))}


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    before = inventory(pw)
    (out / 'inventory.before.json').write_text(json.dumps(before, indent=2) + '\n')
    (out / 'launchd_labels.before.json').write_text(json.dumps(launchd_labels(), indent=2) + '\n')

    spec = {
        'schema_version': 3,
        'specimen_id': 'run_effects_plain_run',
        'policy': {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'},
        'probe_plan': [{
            'step_id': secrets.token_hex(8),
            'sandbox_check': {'operation': 'file-read-data',
                              'filter': {'kind': 'path', 'value': '/etc/hosts'}},
            'attempt': {'kind': 'file', 'action': 'open_read', 'target': '/etc/hosts'},
        }],
    }
    with RunCapture(pw, out / 'run', spec, cli_args=['--no-log-capture']) as run:
        rc = run.wait(timeout=30)

    after = inventory(pw)
    (out / 'inventory.after.json').write_text(json.dumps(after, indent=2) + '\n')
    (out / 'launchd_labels.after.json').write_text(json.dumps(launchd_labels(), indent=2) + '\n')
    effects.expect_inventory_unchanged(before, after)

    assert rc == 0, f'PW exit={rc}; see {run.stdout_path}'
    envelope = run.load_json()
    assert envelope['result']['ok'] is True
    runner = envelope['data']['runner_result']
    assert runner['normalized_outcome'] == 'ok' and runner.get('test_overrides') is None, runner
    print('registry, reported registry, and launchd plist directories are unchanged by a plain run', flush=True)


if __name__ == '__main__':
    main()
