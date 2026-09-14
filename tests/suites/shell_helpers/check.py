"""Exercise the shell helper contract through subprocesses and durable artifacts."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

TESTS = Path(__file__).resolve().parents[2]
FIXTURE = TESTS / 'fixtures/shell_case/case.sh'
LIBRARY = TESTS / 'lib/case.sh'


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ('success', {}, ['build', 'check', 'later'], 'pass', ()),
        ('binary_override', {}, ['build', 'check', 'later'], 'pass', ()),
        ('missing_app', {}, [], 'fail', ('built policy-witness',)),
        ('nonexecutable_app', {}, [], 'fail', ('not executable',)),
        ('directory_app', {}, [], 'fail', ('not executable',)),
        ('failed_build', {'build_exit': 17}, ['build'], 'fail', ('fixture build failed', 'exit 17')),
        ('build_no_output', {'produce_output': False}, ['build'], 'fail', ('no executable file',)),
        ('build_nonexecutable', {'executable_output': False}, ['build'], 'fail', ('no executable file',)),
        ('failed_check', {'check_exit': 7}, ['build', 'check'], 'fail', ('controlled checker failed', 'exit 7')),
        ('checker_rc3', {'check_exit': 3}, ['build', 'check'], 'fail', ('controlled checker failed', 'exit 3')),
        ('missing_command', {}, ['build'], 'fail', ('missing command',)),
        ('missing_checker', {}, ['build'], 'fail', ('missing Python checker',)),
        ('log_open_failure', {}, ['build'], 'fail', ('controlled checker failed', 'missing-parent/assert.log')),
        ('optional_skip', {}, [], 'skip', ('PolicyWitness.app is missing',)),
    ]
    passed = []
    for name, changes, phases, status, diagnostics in cases:
        work = out / name
        work.mkdir()
        config = {'journal': str(work / 'journal.jsonl'), 'marker': secrets.token_hex(12), **changes}
        config_path = work / 'config.json'
        config_path.write_text(json.dumps(config, indent=2) + '\n')
        app = work / 'A custom app.app'
        pw = app / 'Contents/MacOS/policy-witness'
        if name == 'binary_override':
            pw = work / 'explicit binary'
        if name not in ('missing_app', 'optional_skip'):
            pw.parent.mkdir(parents=True, exist_ok=True)
            if name == 'directory_app':
                pw.mkdir()
            else:
                pw.write_text('#!/bin/sh\nexit 0\n')
                pw.chmod(0o644 if name == 'nonexecutable_app' else 0o755)

        suite = 'compatibility_alias' if name == 'binary_override' else 'controlled_suite'
        case_id = 'retained_case_id'
        child_out = work / 'out with spaces'
        canary = work / 'shell-evaluation-canary'
        literal = f'argument with spaces; $(touch "{canary}") "quotes"\nnext line'
        env = dict(os.environ)
        env.pop('PW_BIN', None)
        env.update(PW_APP_DIR=str(app), PW_TEST_OUT_DIR=str(child_out),
                   PW_TEST_EVENTS=str(child_out / 'events.jsonl'), PW_TEST_RUN_ID=f'control_{name}',
                   CONTROL_SUITE=suite, CONTROL_ID=case_id, CONTROL_MODE=name,
                   CONTROL_CONFIG=str(config_path), CONTROL_LITERAL=literal)
        if name in ('binary_override', 'optional_skip'):
            env['PW_BIN'] = str(pw)
        # Run from a different directory; the wrapper's root and every argument
        # must survive without relying on the parent's current working directory.
        result = subprocess.run(['bash', str(FIXTURE), str(LIBRARY)], env=env, cwd=work,
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
        (work / 'wrapper.stdout').write_bytes(result.stdout)
        (work / 'wrapper.stderr').write_bytes(result.stderr)
        (work / 'exit.json').write_text(json.dumps({'returncode': result.returncode}) + '\n')
        output = (result.stdout + result.stderr).decode()
        assert result.returncode == (1 if status == 'fail' else 0), (name, result.returncode, output)
        assert not canary.exists(), f'{name}: arguments were evaluated as shell code'
        records = [json.loads(line) for line in Path(config['journal']).read_text().splitlines()] if phases else []
        if not phases:
            assert not Path(config['journal']).exists(), f'{name}: a forbidden stage ran'
        assert [record['phase'] for record in records] == phases, (name, records)

        case_dir = child_out / 'suites' / suite / case_id
        artifacts = case_dir / 'artifacts'
        expected_args = {'build': [str(artifacts / 'helper')], 'check': [str(pw), literal], 'later': []}
        for record in records:
            assert record['argv'] == expected_args[record['phase']], (name, record)
        reports = list(child_out.glob('suites/*/*/report.json'))
        assert reports == [case_dir / 'report.json'], (name, reports)
        report = json.loads(reports[0].read_text())
        assert (report['suite'], report['test_id'], report['status']) == (suite, case_id, status), report
        assert report['artifacts_dir'] == str(artifacts), report
        assert all(note in report['message'] for note in diagnostics), (name, report)
        local_events = (case_dir / 'events.jsonl').read_bytes()
        assert local_events == (child_out / 'events.jsonl').read_bytes(), name
        events = [json.loads(line) for line in local_events.splitlines()]
        assert all(event['suite'] == suite and event['test_id'] == case_id for event in events), events
        assert [(event['status'], event['step']) for event in events if event['step'].startswith('test_')] == [
            ('start', 'test_start'), (status, 'test_end')], (name, events)

        logs = {'build': 'build.log', 'check': 'assert custom.log', 'later': 'later.log'}
        for phase in phases:
            log = artifacts / logs[phase]
            expected_bytes = f"{phase}: ok {config['marker']}\n{phase}: stderr {config['marker']}\n".encode()
            assert log.read_bytes() == expected_bytes, (name, phase, log.read_bytes())
            if config.get(f'{phase}_exit', 0):
                assert expected_bytes in result.stderr, (name, result.stderr)
                assert str(log) in report['message'], report
        if 'check' not in phases and name != 'log_open_failure':
            assert not (artifacts / logs['check']).exists(), name
        if 'later' not in phases:
            assert not (artifacts / logs['later']).exists(), name
        passed.append(name)
        print(f'{name}: ok', flush=True)
    (out / 'controls.json').write_text(json.dumps(passed, indent=2) + '\n')
    print(f'{len(passed)} shell helper controls passed')


if __name__ == '__main__':
    main()
