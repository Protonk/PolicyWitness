"""Independent child receipts and controlled exits; imports no test machinery."""
import json
import os
from pathlib import Path
import sys

config = json.loads(Path(os.environ['CONTROL_SCRIPT_CONFIG']).read_text())
script = str(Path(sys.argv[1]).relative_to(config['root']))
mode = config['modes'].get(script, 'pass')
record = {
    'script': script, 'argv': sys.argv[2:], 'mode': mode,
    'alias': os.environ.get('PW_TEST_SUITE_OVERRIDE'),
    'runner_mode': os.environ.get('PW_TEST_RUNNER_MODE'),
    'service': os.environ.get('PW_TEST_RUNNER_SERVICE'),
    'kind': os.environ.get('PW_TEST_RUNNER_EXPECT_KIND'),
    'env_path': os.environ.get('PW_TEST_RUNNER_ENV_PATH'),
}
with Path(config['journal']).open('a') as stream:
    stream.write(json.dumps(record) + '\n')
if script.endswith('/runner_install.sh') and mode == 'pass':
    path = Path(os.environ['PW_TEST_RUNNER_ENV_PATH'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'runner_id': 'fixture-id', 'service_name': 'fixture.service'}))
print(f'{script}: {mode}', flush=True)
print(f'{script}: stderr', file=sys.stderr, flush=True)
raise SystemExit(17 if mode == 'fail' else 0)
