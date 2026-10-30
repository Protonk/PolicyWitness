"""Native inputs and independent rejection expectations for exec_control_states."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil

from check_exec_evidence import canonical_ledger

FAMILY = 'runner_c_worker_harness/exec_control_states'
MARKER = '    slot->exec_valid = 1;'

@dataclass(frozen=True)
class Mutation:
    name: str
    statement: str
    expected: str

MUTATIONS = (
    Mutation('collection_from_final_reap', 'slot->exec_leader_exit_observed = reaped == child;', 'slot->exec_leader_exit_observed == leader'),
    Mutation('esrch_as_success', 'if (slot->exec_group_errno == ESRCH) { slot->exec_group_rc = 0; slot->exec_group_errno = 0; }', 'slot->exec_group_rc == group->rc && slot->exec_group_errno == group->error'),
    Mutation('fallback_from_group', 'if (slot->exec_fallback_present) { slot->exec_fallback_rc = slot->exec_group_rc; slot->exec_fallback_errno = slot->exec_group_errno; }', 'slot->exec_fallback_rc == fallback->rc && slot->exec_fallback_errno == fallback->error'),
    Mutation('status_after_pending_wait', 'if (reaped != child) { slot->exec_reap_wait_rc = child; slot->exec_reap_stop = PW_EXEC_REAP_REAPED; }', 'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error'),
    Mutation('revents_as_native_errno', 'if (slot->exec_stdout_poll_revents || slot->exec_stderr_poll_revents) slot->exec_poll_errno = EIO;', 'slot->exec_waitid_errno == wait_error && slot->exec_poll_errno == poll_failure'),
    Mutation('local_deadline_as_native_errno', 'if (slot->exec_reap_stop == PW_EXEC_REAP_DEADLINE) slot->exec_reap_wait_errno = ETIMEDOUT;', 'wait && slot->exec_reap_wait_rc == wait->rc && slot->exec_reap_wait_errno == wait->error'),
)
OWNERS = ('pw_worker_timing.h', 'pw_worker_exec.h')


def inventory(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.iterdir()) if p.suffix in ('.c', '.h', '.json')}


class Observation:
    def __init__(self, equipment):
        self.equipment = equipment
        self.inputs = equipment.artifacts / 'inputs'
        self.inputs.mkdir()
        native = equipment.root / 'controller/tools/pw_probe_runner'
        for source in [native / 'pw_probe_runner.c', *native.glob('*.h'),
                       equipment.root / 'tests/fixtures/worker_lifecycle/exec_control.c',
                       equipment.root / 'tests/fixtures/worker_lifecycle/exec_call_policy.json']:
            shutil.copy2(source, self.inputs / source.name)
        self.before = inventory(self.inputs)
        self.source = (self.inputs / 'pw_worker_exec.h').read_text()
        self.baseline_result = None
        equipment.publish('inputs.json', self.before)

    def prepare(self, name, mutation=None, missing=None):
        directory = self.equipment.artifacts / name
        directory.mkdir()
        for source in self.inputs.iterdir():
            shutil.copy2(source, directory / source.name)
        if mutation:
            self.equipment.publish(name + '/expectation.json', dict(kind='mutation', proposed=mutation.statement,
                                 expected=mutation.expected, formation='not yet established'))
            self.equipment.publish(name + '/sources-before-formation.json', inventory(directory))
            assert self.source.count(MARKER) == 1, f'{name}: exec assembly boundary changed; mutation not submitted'
            (directory / 'pw_worker_exec.h').write_text(self.source.replace(MARKER, '    ' + mutation.statement + '\n' + MARKER))
            self.equipment.publish(name + '/expectation.json', dict(kind='mutation', submitted=mutation.statement,
                                  expected=mutation.expected, formation='one exec assembly boundary'))
        if missing:
            self.equipment.publish(name + '/expectation.json', dict(kind='include', removed=missing,
                                    expected=f"'{missing}' file not found"))
            (directory / missing).unlink()
        self.equipment.publish(name + '/sources.json', inventory(directory))
        return directory

    def build_run(self, name, mutation=None, missing=None):
        directory = self.prepare(name, mutation, missing)
        output = directory / 'exec-control'
        argv = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
                '-O2', '-std=c11', '-I', str(directory), str(directory / 'exec_control.c'), '-lsandbox', '-o', str(output)]
        build = self.equipment.command(argv, directory / 'build', 60)
        diagnostic = (directory / 'build/stderr').read_text()
        if missing:
            expected = f"'{missing}' file not found"
            self.equipment.publish(name + '/observation.json', dict(returncode=build['returncode'], expected=expected, observed=diagnostic))
            assert build['returncode'] != 0, f'{missing}: missing production owner still compiled'
            assert expected in diagnostic, f'{missing}: failed outside the required include boundary: {diagnostic}'
            return directory, build['returncode']
        assert build['returncode'] == 0, f'{name}: compile failed: {diagnostic}'
        run = self.equipment.command([str(output)], directory / 'run', 20)
        return directory, run['returncode']

    def baseline(self):
        if self.baseline_result is None:
            initial = len(self.equipment.completed_operations)
            result = dict(ok=False, evidence='artifacts/production', error=None)
            try:
                directory, code = self.build_run('production')
                assert code == 0, 'production controls failed; see artifacts/production/run/stderr'
                observed = canonical_ledger(directory / 'run/stdout')
                self.equipment.publish('production/observed-call-policy.json', observed)
                expected = json.loads((self.inputs / 'exec_call_policy.json').read_text())
                assert expected['attempts'] == observed, 'native call order/count/value policy changed; compare retained expected and observed ledgers'
                result.update(ok=True, attempts=len(observed))
            except Exception as exc:
                # Any failure is the one shared result; a retry would re-enter production.
                result['error'] = str(exc) if isinstance(exc, AssertionError) else f'{type(exc).__name__}: {exc}'
            result['operations'] = self.equipment.completed_operations[initial:]
            self.baseline_result = result
            self.equipment.publish('baseline.json', result)
        self.equipment.observe(self.baseline_result['operations'])
        return self.baseline_result

    def mutation(self, mutation):
        directory, status = self.build_run(mutation.name, mutation=mutation)
        observed = (directory / 'run/stderr').read_text()
        self.equipment.publish(mutation.name + '/observation.json', dict(returncode=status, expected=mutation.expected, observed=observed))
        assert status != 0, f'unchanged native assertions accepted mutation {mutation.name}'
        assert 'Assertion failed:' in observed and mutation.expected in observed, f'{mutation.name} failed outside its designated oracle: {observed}'

    def finish(self):
        after = inventory(self.inputs)
        changed = {k:dict(before=self.before.get(k), after=after.get(k)) for k in self.before.keys() | after.keys() if self.before.get(k) != after.get(k)}
        self.equipment.publish('input-integrity.json', dict(ok=not changed, changed=changed,
            scope='all family items', applicability='retained per-variant source receipts remain individually inspectable'))
        assert not changed, f'shared input integrity uncertain: {changed}; see per-variant sources.json'
