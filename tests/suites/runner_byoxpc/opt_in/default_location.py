"""One live session using the production default registry and plist locations."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import contract
import build_context
from consumer import validate

pw, directory = sys.argv[1:]
out = Path(directory)
assert 'PW_RUNNER_REGISTRY' not in os.environ
state = json.loads((out / 'session.json').read_text())
assert state['registry_path'] is None
service = state['service_name']
verified = json.loads((out / 'verify-connection/stdout').read_text())
assert verified['kind'] == 'runner_verify' and verified['build']['contract'] == build_context.candidate_contract(), verified
assert verified['result']['ok'] is True and verified['result']['normalized_outcome'] == 'finished', verified['result']
assert verified['data']['normalized_outcome'] == 'finished', verified['data']
assert verified['data']['runner_result']['normalized_outcome'] == 'finished', verified['data']['runner_result']
listed = subprocess.run([pw, 'runner', 'list'], capture_output=True, timeout=30)
(out / 'default-list.json').write_bytes(listed.stdout)
assert listed.returncode == 0
records = json.loads(listed.stdout)['data']['runners']
record = next(r for r in records if r['service_name'] == service)
assert record['id'] == state['runner_id'] and record['bundle_path'] == state['bundle_path']
plist = Path.home() / 'Library/LaunchAgents' / (service + '.plist')
assert str(plist) == state['plist_path'] and plist.is_file()
assert plistlib.loads(plist.read_bytes())['Label'] == service
assert (Path.home() / 'Library/Application Support/PolicyWitness/runners.json').is_file()
effect = out / 'effect'
spec = dict(contract=build_context.candidate_contract(), specimen_id='default-location',
            runner=dict(mode='byoxpc', service=service),
            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
            probe_plan=[dict(step_id='create', sandbox_check=dict(operation='file-write-create',
                filter=dict(kind='path', value=str(effect))),
                attempt=dict(kind='file', action='create', target=str(effect)))])
path = out / 'specimen.json'
path.write_text(json.dumps(spec))
result = subprocess.run([pw, 'run', str(path)], capture_output=True, timeout=60)
(out / 'run.json').write_bytes(result.stdout)
(out / 'run.stderr').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr
doc = json.loads(result.stdout)
assert not validate(doc, build_context.candidate_contract()), validate(doc, build_context.candidate_contract())
assert doc['data']['runner_result']['normalized_outcome'] == 'finished' and effect.exists()
