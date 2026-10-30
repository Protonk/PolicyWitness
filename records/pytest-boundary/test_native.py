"""Exposed R1 replay: unchanged native oracle, pytest-owned variant reporting."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
from common import ROOT
from native_adapter import build_run, inventory

# Historical, independently authored expected assertions, not production enums
# or classifier results. These values are unchanged across the replay.
MUTATIONS = {
    'collection_from_final_reap': ('slot->exec_leader_exit_observed = reaped == child;',
                                 'slot->exec_leader_exit_observed == leader'),
    'esrch_as_success': ('if (slot->exec_group_errno == ESRCH) { slot->exec_group_rc = 0; slot->exec_group_errno = 0; }',
                        'slot->exec_group_rc == group->rc && slot->exec_group_errno == group->error'),
    'fallback_from_group': ('if (slot->exec_fallback_present) { slot->exec_fallback_rc = slot->exec_group_rc; slot->exec_fallback_errno = slot->exec_group_errno; }',
                           'slot->exec_fallback_rc == fallback->rc && slot->exec_fallback_errno == fallback->error'),
    'status_after_pending_wait': ('if (reaped != child) { slot->exec_reap_wait_rc = child; slot->exec_reap_stop = PW_EXEC_REAP_REAPED; }',
                                 'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error'),
    'revents_as_native_errno': ('if (slot->exec_stdout_poll_revents || slot->exec_stderr_poll_revents) slot->exec_poll_errno = EIO;',
                               'slot->exec_waitid_errno == wait_error && slot->exec_poll_errno == poll_failure'),
    'local_deadline_as_native_errno': ('if (slot->exec_reap_stop == PW_EXEC_REAP_DEADLINE) slot->exec_reap_wait_errno = ETIMEDOUT;',
                                      'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error'),
}


@pytest.fixture(scope='session')
def native_inputs(request):
    out = request.config.boundary.out
    inputs = out / 'native-inputs'
    inputs.mkdir()
    revision = os.environ['BOUNDARY_REPLAY_REVISION']
    native = 'controller/tools/pw_probe_runner/'
    paths = subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--',native],cwd=ROOT,text=True).splitlines()
    selected = [p for p in paths if p.endswith('.h') or p == native+'pw_probe_runner.c']
    selected += ['tests/fixtures/worker_lifecycle/exec_control.c','tests/fixtures/worker_lifecycle/exec_call_policy.json']
    for path in selected:
        (inputs/Path(path).name).write_bytes(subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT))
    before = inventory(inputs)
    (out / 'native-source.json').write_text(json.dumps(dict(revision=revision,files=before),indent=2)+'\n')
    scratch = out / 'scratch/native'
    scratch.mkdir(parents=True)
    yield inputs, out / 'artifacts/native', scratch
    assert inventory(inputs)==before, 'shared immutable native inputs changed'
    shutil.rmtree(scratch)
    scratch.parent.rmdir()


@pytest.mark.parametrize('variant', ['production', *MUTATIONS, 'missing-pw_worker_timing.h', 'missing-pw_worker_exec.h'])
def test_control(native_inputs, variant):
    inputs, artifacts, scratch = native_inputs
    if variant.startswith('missing-'):
        owner = variant.removeprefix('missing-')
        result = build_run(inputs, artifacts/variant, scratch/variant, missing_owner=owner)
        assert result.returncode != 0 and f"'{owner}' file not found" in result.stderr.decode(), (
            'missing owner compiled or failed outside its include boundary: '+result.stderr.decode())
        return
    mutation = MUTATIONS.get(variant)
    result = build_run(inputs, artifacts/variant, scratch/variant, mutation[0] if mutation else None)
    if variant == 'production':
        assert result.returncode == 0, result.stderr.decode()
        source = ROOT / 'tests/suites/runner_c_worker_harness/check_exec_evidence.py'
        spec = importlib.util.spec_from_file_location('native_policy_reader', source)
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        observed = reader.canonical_ledger(artifacts/variant/'run.stdout')
        (artifacts/'observed-call-policy.json').write_text(json.dumps(observed,indent=2)+'\n')
        assert observed == json.loads((inputs/'exec_call_policy.json').read_text())['attempts']
    else:
        assert result.returncode != 0, 'unchanged native assertions accepted mutation '+variant
        assert 'Assertion failed:' in result.stderr.decode() and mutation[1] in result.stderr.decode(), (
            'mutation failed outside its designated native assertion: '+result.stderr.decode())
