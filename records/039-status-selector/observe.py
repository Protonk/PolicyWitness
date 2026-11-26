"""Run the two status lookup designs against one read-only registry fixture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(binary, design):
    registry = HERE / 'registry.json'
    env = dict(os.environ, PW_RUNNER_REGISTRY=str(registry))
    original = registry.read_bytes()
    first, second = json.loads(original)['runners']
    shared = first['id']
    assert shared == second['service_name']
    trials = []
    for field, value, intended in (
        ('service_name', first['service_name'], first),
        ('id', second['id'], second),
        ('id', shared, first),
        ('service_name', shared, second),
    ):
        args = ['runner', 'status']
        if design == 'released':
            args.append({'id': '--id', 'service_name': '--service-name'}[field])
        args.append(value)
        process = subprocess.run([binary, *args], env=env,
                                 capture_output=True, text=True, timeout=10)
        output = json.loads(process.stdout) if process.stdout else None
        if design == 'released' or value != shared:
            assert process.returncode == 0 and not process.stderr and output['result']['ok']
            assert all(output['data'][key] == intended[key] for key in ('id', 'service_name', 'bundle_path'))
        else:
            assert process.returncode == 2 and output is None
            assert process.stderr == f'ambiguous runner status key: {shared}\n'
        assert registry.read_bytes() == original and not registry.with_suffix('.json.lock').exists()
        trials.append(dict(intended_field=field, intended_bundle=intended['bundle_path'],
                           argv=args, exit_code=process.returncode, stdout=output, stderr=process.stderr))
    list_result = subprocess.run([binary, 'runner', 'list'], env=env, check=True, capture_output=True)
    listed = json.loads(list_result.stdout)['data']['runners']
    recovered = {field: [r['bundle_path'] for r in listed if r[field] == shared] for field in ('id', 'service_name')}
    assert recovered == {'id': [first['bundle_path']], 'service_name': [second['bundle_path']]}
    miss = ['runner', 'status'] + (['--id'] if design == 'released' else []) + ['missing-record']
    missing = subprocess.run([binary, *miss], env=env, capture_output=True, text=True)
    envelope = json.loads(missing.stdout)
    assert missing.returncode == 2 and not missing.stderr and envelope['result']['normalized_outcome'] == 'not_found'
    assert envelope['data'] == ({'requested_id': 'missing-record'} if design == 'released' else {})
    assert registry.read_bytes() == original
    version = json.loads(subprocess.check_output([binary, 'version']))
    return dict(version=version, binary_sha256=sha256(binary), registry_sha256=sha256(registry), trials=trials,
                listed=json.loads(list_result.stdout), recovered_by_column=recovered,
                missing=dict(argv=miss, exit_code=missing.returncode, stdout=envelope, stderr=missing.stderr))


if __name__ == '__main__':
    for design, binary in zip(('released', 'positional'), sys.argv[1:], strict=True):
        print(design)
        result = observe(Path(binary), design)
        (HERE / (design + '.json')).write_text(json.dumps(result, indent=2) + '\n')
