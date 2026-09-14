"""Run the actual C-worker suite with independently controlled test equipment."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'tests/fixtures/worker_harness'


def main():
    out = Path(sys.argv[1]).resolve()
    inventory = []
    for mode, phases, diagnostic in (
        ('build_failure', ['build'], 'fixture build failed'),
        ('missing_product', ['build'], 'no executable file'),
        ('harness_failure', ['build', 'run'], 'harness exited rc=23'),
        ('malformed_output', ['build', 'run'], 'Traceback'),
        ('failed_observation', ['build', 'run'], 'pre-apply ready byte not received'),
        ('later_failure', ['build', 'run', 'run'], 'harness exited rc=23'),
    ):
        work = out / mode
        repo = work / 'fixture repo'
        for relative in ('tests/suites/runner_c_worker_harness/run.sh',
                         'tests/lib/testlib.sh', 'tests/lib/case.sh'):
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        builder = repo / 'tests/fixtures/worker_harness/build.sh'
        builder.parent.mkdir(parents=True)
        shutil.copyfile(FIXTURE / 'control.sh', builder)
        abi = repo / 'controller/tools/pw_probe_runner/pw_probe_runner_abi.h'
        abi.parent.mkdir(parents=True)
        abi.touch()
        app = repo / 'A custom app.app'
        worker = app / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
        worker.parent.mkdir(parents=True)
        worker.write_text('#!/bin/sh\nexit 99\n')
        worker.chmod(0o755)
        child_out = repo / 'tests/out'
        child_out.mkdir()
        harness = child_out / 'harness.runner_c_worker'
        if mode == 'build_failure':
            # A failed rebuild must not execute an old binary left at its output.
            shutil.copyfile(FIXTURE / 'control.sh', harness)
            harness.chmod(0o755)
        config_path = work / 'config.json'
        journal = work / 'receipts.jsonl'
        config_path.write_text(json.dumps({'mode': mode, 'journal': str(journal)}) + '\n')
        env = {key: value for key, value in os.environ.items() if not key.startswith('PW_')}
        env.update(PW_APP_DIR=str(app), PW_TEST_OUT_DIR=str(child_out), PW_TEST_RUN_ID=mode,
                   CONTROL_WORKER_CONFIG=str(config_path), CONTROL_WORKER_DRIVER=str(FIXTURE / 'control.py'))
        result = subprocess.run(['bash', str(repo / 'tests/suites/runner_c_worker_harness/run.sh')],
                                env=env, cwd=work, capture_output=True, timeout=15)
        (work / 'stdout').write_bytes(result.stdout)
        (work / 'stderr').write_bytes(result.stderr)
        (work / 'exit.json').write_text(json.dumps({'returncode': result.returncode}) + '\n')
        assert result.returncode == 1, (mode, result.stdout, result.stderr)
        records = [json.loads(line) for line in journal.read_text().splitlines()]
        assert [record['phase'] for record in records] == phases, (mode, records)
        assert records[0]['argv'] == [str(harness)], (mode, records)
        expected_ids = ['happy_default_allow'] + (['bare_deny_default'] if mode == 'later_failure' else [])
        for record, scenario in zip(records[1:], expected_ids):
            assert record['argv'] == [str(worker), scenario], (mode, record)
        cases = child_out / 'suites/runner_c_worker_harness'
        reports = {path.parent.name: json.loads(path.read_text()) for path in cases.glob('*/report.json')}
        assert set(reports) == set(expected_ids), (mode, reports)
        for index, case_id in enumerate(expected_ids):
            status = 'fail' if index == len(expected_ids) - 1 else 'pass'
            report = reports[case_id]
            artifacts = cases / case_id / 'artifacts'
            assert (report['suite'], report['test_id'], report['status'], report['artifacts_dir']) == (
                'runner_c_worker_harness', case_id, status, str(artifacts)), (mode, report)
            if status == 'fail':
                assert diagnostic in report['message'], (mode, report)
                if mode not in ('malformed_output', 'failed_observation'):
                    assert not (artifacts / 'assert.log').exists(), 'assertions ran after equipment failure'
            local = [json.loads(line) for line in (cases / case_id / 'events.jsonl').read_text().splitlines()]
            assert [(e['step'], e['status']) for e in local if e['step'].startswith('test_')] == [
                ('test_start', 'start'), ('test_end', status)], (mode, local)
            if index < len(records) - 1:
                assert (artifacts / 'result.json').is_file(), (mode, artifacts)
                assert (artifacts / 'harness.stderr').read_text() == f'controlled harness stderr: {case_id}\n'
        build_log = cases / 'happy_default_allow/artifacts/build.log'
        assert build_log.read_bytes() == b'controlled build stdout\ncontrolled build stderr\n', mode
        inventory.append(mode)
        print(f'{mode}: ok', flush=True)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} worker setup controls passed')


if __name__ == '__main__':
    main()
