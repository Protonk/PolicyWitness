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
        ('custom_build_log', {}, ['build', 'check', 'later'], 'pass', ()),
        ('custom_build_log_failure', {'build_exit': 17}, ['build'], 'fail', ('exit 17', 'another build.log')),
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
        env.update(PW_APP_DIR=str(app), PW_TEST_OUT_DIR=str(child_out), PW_TEST_CASES=case_id,
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
        if name.startswith('custom_build_log'):
            logs['build'] = 'another build.log'
            assert (artifacts / 'build.log').read_bytes() == b'prior build log\n', name
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
    passed += refusal_controls(out / 'refusal')
    (out / 'controls.json').write_text(json.dumps(passed, indent=2) + '\n')
    print(f'{len(passed)} shell helper controls passed')


ROOT = TESTS.parent
REFUSAL = 'not started by the test dispatcher'
# Real case scripts, one per library path: a shared suite command, an own
# script, the BYOXPC wrapper (each gated at test_selected) and a script that
# begins its case at once (gated at test_begin). None needs the app to refuse.
SCRIPTS = [('suite_command', 'tests/suites/unit/run.sh', True),
           ('own_script', 'tests/suites/blackbox_e2e/bbx_001.sh', True),
           ('byoxpc_wrapper', 'tests/suites/runner_byoxpc/run.sh', True),
           ('begins_at_once', 'tests/suites/sandbox_extensions_native/run.sh', False)]


def refusal_controls(out):
    """A case script refuses without the dispatcher's context and runs with it.

    Without PW_TEST_CASES, PW_TEST_EVENTS and PW_TEST_OUT_DIR a real script exits 2,
    names the canonical command, and writes nothing: no report, no event, no
    output directory, and never tests/out/runs/direct. With the context and a
    selection it does not own, the same script exits 0 without a refusal and
    without output, so the refusal is the gate and not a missing equipment."""
    out.mkdir()
    direct = ROOT / 'tests/out/runs/direct'
    direct_existed = direct.exists()
    passed = []
    for name, script, selectable in SCRIPTS:
        for mode in (('refused', 'with_context') if selectable else ('refused',)):
            label = f'refusal_{name}_{mode}'
            work = out / label
            work.mkdir()
            child_out = work / 'child out'
            env = {key: value for key, value in os.environ.items() if not key.startswith('PW_TEST_')}
            env['PW_APP_DIR'] = str(work / 'absent.app')
            if mode == 'with_context':
                env.update(PW_TEST_CASES='no_such_case', PW_TEST_EVENTS=str(child_out / 'events.jsonl'),
                           PW_TEST_OUT_DIR=str(child_out), PW_TEST_RUN_ID=label)
            before = sorted(p.name for p in work.iterdir())
            result = subprocess.run(['bash', str(ROOT / script)], env=env, cwd=work,
                                    stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
            (work / 'stdout').write_bytes(result.stdout)
            (work / 'stderr').write_bytes(result.stderr)
            (work / 'exit.json').write_text(json.dumps({'script': script, 'mode': mode, 'returncode': result.returncode}) + '\n')
            after = sorted(p.name for p in work.iterdir() if p.name not in ('stdout', 'stderr', 'exit.json'))
            assert direct.exists() == direct_existed, f'{label}: tests/out/runs/direct was created'
            if mode == 'refused':
                assert result.returncode == 2, (label, result.returncode, result.stderr)
                assert REFUSAL.encode() in result.stderr and b'tests/run.sh --case' in result.stderr, (label, result.stderr)
                assert script.encode() in result.stderr, (label, result.stderr)
                assert after == before, f'{label}: a refused start wrote {after}'
                assert not child_out.exists(), label
            else:
                assert result.returncode == 0, (label, result.returncode, result.stderr)
                assert REFUSAL.encode() not in result.stderr, (label, result.stderr)
                assert after == before, f'{label}: an unselected start wrote {after}'
                assert not child_out.exists() or not any(child_out.rglob('report.json')), label
            passed.append(label)
            print(f'{label}: ok', flush=True)
    return passed


if __name__ == '__main__':
    main()
