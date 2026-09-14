"""Controlled builder/harness used only in disposable copies of the suite."""
import json
import os
from pathlib import Path
import shutil
import sys

config = json.loads(Path(os.environ['CONTROL_WORKER_CONFIG']).read_text())
building = sys.argv[1] == 'build.sh'
with Path(config['journal']).open('a') as stream:
    stream.write(json.dumps({'phase': 'build' if building else 'run', 'argv': sys.argv[2:]}) + '\n')
if building:
    print('controlled build stdout', flush=True)
    print('controlled build stderr', file=sys.stderr, flush=True)
    if config['mode'] == 'build_failure':
        raise SystemExit(17)
    if config['mode'] != 'missing_product':
        output = Path(sys.argv[2])
        shutil.copyfile(Path(__file__).with_suffix('.sh'), output)
        output.chmod(0o755)
    raise SystemExit(0)

scenario = sys.argv[3]
print(f'controlled harness stderr: {scenario}', file=sys.stderr, flush=True)
if config['mode'] == 'malformed_output':
    print('{broken', flush=True)
else:
    # Explicit transcripts for the first two cases; no imports from the suite.
    deny = scenario == 'bare_deny_default'
    result = {'ready_byte_received': config['mode'] != 'failed_observation',
              'applied': True, 'apply_rc': 0, 'done': True, 'sent_sigkill': False,
              'exit_code': 0, 'term_signal': None,
              'slots': [{'completed': 1, 'rc': 1 if deny else 0,
                         'errno': 1 if deny else 0, 'observed_path': '/private/etc/hosts'}]}
    print(json.dumps(result), flush=True)
raise SystemExit(23 if config['mode'] == 'harness_failure' or
                 (config['mode'] == 'later_failure' and scenario == 'bare_deny_default') else 0)
