"""Compile and apply the principal specimen's B policy through the shipped app.

Two narrow checks, not an experiment: the bundled `sbpl-check` helper compiles
the exact policy bytes, and the single-worker run path applies them and runs an
ordinary baseline access. An independent run under an ordinary allowance shows
the target is readable outside that policy. Retained: the source bytes and
hash, commands, helper envelope, run envelopes, equipment and environment.
A compile success alone establishes neither application nor issuance.
"""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from witness_capture import capture  # noqa: E402
from contract import REQUEST_SCHEMA  # noqa: E402
import extension_actors  # noqa: E402

pw, directory = sys.argv[1:]
out = Path(directory)
out.mkdir(parents=True, exist_ok=True)
helper = Path(pw).parent / 'sbpl-check'
assert helper.is_file(), helper

policy = extension_actors.B_POLICY
policy_sha256 = extension_actors.sha256_hex(policy)
(out / 'policy.sbpl').write_text(policy)
record = {
    'policy_sha256': policy_sha256, 'policy_bytes': len(policy.encode('utf-8')),
    'environment': {'macos': platform.mac_ver()[0], 'kernel': os.uname().release, 'machine': os.uname().machine,
                    'euid': os.geteuid()},
    'commands': [],
}


def request(specimen_id, source, target):
    return {'schema_version': REQUEST_SCHEMA, 'specimen_id': specimen_id,
            'policy': {'format': 'sbpl', 'sbpl_source': source},
            'probe_plan': [extension_actors.read_probe('baseline_read', target)]}


with tempfile.TemporaryDirectory(prefix='pw-policy-qualification-', dir='/private/tmp') as scratch:
    target = Path(scratch) / 'target'
    contents = b'PW policy qualification target\n'
    target.write_bytes(contents)
    # 1. Compile the exact bytes with the shipped helper.
    compile_request = out / 'compile-request.json'
    compile_request.write_text(json.dumps(request('extension_policy_qualification_compile', policy, target), indent=2) + '\n')
    argv = [str(helper), '--request', str(compile_request)]
    completed = subprocess.run(argv, capture_output=True, timeout=60)
    (out / 'sbpl-check.json').write_bytes(completed.stdout)
    (out / 'sbpl-check.stderr').write_bytes(completed.stderr)
    record['commands'].append({'argv': argv, 'returncode': completed.returncode})
    assert completed.returncode == 0, completed.stderr
    helper_envelope = json.loads(completed.stdout)
    assert helper_envelope['kind'] == 'sbpl_check', helper_envelope['kind']
    assert helper_envelope['result']['normalized_outcome'] == 'ok', helper_envelope['result']
    compile = helper_envelope['data']['compile']
    assert compile['ok'] is True and compile['stage'] == 'compile' and compile['error'] is None, compile
    assert helper_envelope['data']['policy_sha256'] == policy_sha256, helper_envelope['data']['policy_sha256']
    record['compile'] = compile
    record['helper_build'] = helper_envelope['build']

    # 2. Apply the exact bytes in a fresh worker and run a baseline fresh read.
    envelope, runner = capture(pw, out, 'apply', request('extension_policy_qualification', policy, target))
    record['commands'].append({'argv': [str(pw), 'run', str(out / 'apply' / 'specimen.json')], 'returncode': 0})
    assert runner['normalized_outcome'] == 'finished', runner
    assert runner['sandboxed_after_apply'] is True, runner.get('sandboxed_after_apply')
    assert runner['policy_sha256'] == policy_sha256, runner['policy_sha256']
    worker = runner['runner_subprocess']
    assert worker['reaped'] and worker['exit_code'] == 0, worker
    evidence = worker['worker_evidence']
    assert evidence['progress']['stage'] in ('finished', 'done', 'completed') or evidence['progress'], evidence['progress']
    step, = runner['steps']
    attempt = step['attempt']
    assert attempt['result_source'] == 'worker' and attempt['requested_action'] == 'read_fresh', attempt
    # The policy denies ordinary reads of the target; a completed failed open is
    # the application observation. Its errno is not a sandbox-cause claim.
    assert attempt['rc'] != 0 and attempt['fresh_read']['open_rc'] == -1, attempt
    assert step['sandbox_check']['outcome'] == 'deny' and step['sandbox_check']['pid'] == worker['pid'], step['sandbox_check']
    assert step['comparison']['order'] == 'query_first', step['comparison']
    record['apply'] = {'worker_pid': worker['pid'], 'attempt_rc': attempt['rc'], 'attempt_errno': attempt['errno'],
                       'open_errno': attempt['fresh_read']['open_errno'], 'prediction': step['sandbox_check']['outcome'],
                       'app_build': envelope['build']}

    # 3. The same target reads under an ordinary allowance: the file is readable.
    _, control = capture(pw, out, 'control', request('extension_policy_qualification_control',
                                                      extension_actors.CALIBRATION_POLICY, target))
    control_step, = control['steps']
    read = control_step['attempt']['fresh_read']
    assert control_step['attempt']['rc'] == 0 and bytes.fromhex(read['content_hex']) == contents, control_step['attempt']
    assert target.read_bytes() == contents
    record['control'] = {'worker_pid': control['runner_subprocess']['pid'], 'read_rc': read['read_rc']}

(out / 'qualification.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'B policy {policy_sha256[:12]} compiled by sbpl-check and applied once in worker {record["apply"]["worker_pid"]}; '
      f'baseline read denied under it (open errno {record["apply"]["open_errno"]}) and readable under the control policy.')
