"""Run the real dispatcher in isolated fixture repositories; inspect its outputs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ('pass_and_skip', ['pass', 'skip'], True, ()),
        ('all_skip', ['skip'], True, ()),
        ('alias', ['wrapper'], True, ()),
        ('missing', ['absent', 'pass'], False, ('missing_runner',)),
        ('nonexecutable', ['nonexecutable', 'pass'], False, ('missing_runner',)),
        ('empty', ['silent', 'pass'], False, ('empty_suite',)),
        ('crash', ['crash', 'pass'], False, ('suite_exit', 'empty_suite')),
        ('pass_then_crash', ['pass_then_crash', 'pass'], False, ('suite_exit',)),
        ('failed_report_zero_exit', ['fail_then_zero', 'pass'], False, ()),
        ('malformed', ['malformed_report', 'pass'], False, ('invalid_report',)),
        ('list_report', ['report_list', 'pass'], False, ('invalid_report',)),
        ('invalid_status', ['invalid_status', 'pass'], False, ('invalid_report',)),
        ('wrong_identity', ['wrong_identity', 'pass'], False, ('invalid_report',)),
        ('missing_report', ['missing_report', 'pass'], False, ('missing_report',)),
        ('unfinished', ['unfinished', 'pass'], False, ('case_end', 'missing_report')),
        ('contradictory_status', ['status_mismatch', 'pass'], False, ('status_mismatch',)),
        ('no_events', ['no_events', 'pass'], False, ('case_start', 'case_end')),
        ('malformed_event', ['malformed_event', 'pass'], False, ('invalid_event',)),
        ('stale_events', ['stale_events', 'pass'], False, ('invalid_event',)),
        ('no_end', ['no_end', 'pass'], False, ('case_end',)),
        ('end_before_start', ['end_before_start', 'pass'], False, ('case_order',)),
        ('duplicate_end', ['duplicate_end', 'pass'], False, ('case_end',)),
        ('signal_exit', ['signal_exit', 'pass'], False, ('suite_exit', 'missing_report')),
        ('repeated_suite', ['pass', 'pass'], True, ()),
        ('reused_evidence', ['pass', 'reuse_previous'], False, ('reused_case', 'unselected_case')),
        ('rewritten_events', ['pass', 'no_events'], False, ('events_rewritten',)),
        ('unreadable_events', ['unreadable_events'], False, ('unreadable_events',)),
        ('removed_prior_report', ['pass', 'remove_prior'], False, ('report_removed',)),
    ]
    inventory = []
    for name, requested, expected_ok, codes in cases:
        work = out / name
        repo = work / 'fixture repo'
        fixture_suites = {suite: {'command': ['bash', f'tests/suites/{suite}/run.sh'],
                                  'cases': [{'id': 'fixture_case',
                                             'report_suite': 'reported_alias' if suite == 'wrapper' else suite,
                                             'skip_reasons': ['fixture_limitation'] if suite == 'skip' else []}]}
                          for suite in dict.fromkeys(requested)}
        install_runner(ROOT, repo, fixture_suites)
        for relative in ('tests/fixtures/dispatcher/alter.py',):
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        for suite in set(requested) | {'leaf'}:
            if suite == 'absent':
                continue
            script = repo / 'tests/suites' / suite / 'run.sh'
            script.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'tests/fixtures/dispatcher/run.sh', script)
            script.chmod(0o644 if suite == 'nonexecutable' else 0o755)
        child_out = repo / 'tests/out'
        child_out.mkdir(parents=True)
        # Old output must never be counted as evidence of this invocation.
        (child_out / 'run.json').write_text('{"ok": true, "stale": true}')
        env = {key: value for key, value in os.environ.items() if not key.startswith('PW_')}
        env.update(PW_TEST_OUT_DIR=str(child_out), PW_TEST_RUN_ID=f'control_{name}')
        argv = ['bash', str(repo / 'tests/run.sh')]
        for suite in requested:
            argv.extend(['--suite', suite])
        result = subprocess.run(argv, env=env, cwd=work, capture_output=True, timeout=20)
        (work / 'stdout').write_bytes(result.stdout)
        (work / 'stderr').write_bytes(result.stderr)
        (work / 'exit.json').write_text(json.dumps({'returncode': result.returncode}) + '\n')
        if name in ('missing', 'nonexecutable'):
            assert result.returncode == 2 and b'missing or nonexecutable case runner' in result.stderr, (name, result.stderr)
            assert (child_out / 'run.json').read_text() == '{"ok": true, "stale": true}', name
            assert not (child_out / 'dispatch.json').exists(), name
            inventory.append(name)
            print(f'{name}: ok', flush=True)
            continue
        requested = list(dict.fromkeys(requested))
        summary = json.loads((child_out / 'run.json').read_text())
        journal = json.loads((child_out / 'dispatch.json').read_text())
        assert result.returncode == (0 if expected_ok else 1), (name, result.returncode, result.stderr)
        assert summary['ok'] is expected_ok and 'stale' not in summary, (name, summary)
        assert summary['requested_suites'] == requested, (name, summary)
        invocations = summary['invocations']
        assert [item['requested_suite'] for item in invocations] == requested, name
        assert [item['index'] for item in invocations] == list(range(len(requested))), name
        assert journal['invocations'] == invocations, name
        actual_codes = {error['code'] for error in summary['harness_errors']}
        assert set(codes) <= actual_codes, (name, codes, summary['harness_errors'])
        if expected_ok:
            assert not summary['harness_errors'], summary
        for error in summary['harness_errors']:
            assert error['requested_suite'] == requested[error['invocation']], error
            assert error['code'].encode() in result.stderr, (name, error, result.stderr)
        reports = summary['reports']
        expected_counts = {status: sum(report['status'] == status for report in reports)
                           for status in ('pass', 'fail', 'skip')}
        assert summary['counts'] == {**expected_counts, 'total': len(reports)}, (name, summary)
        assert summary['ok'] is (expected_counts['fail'] == 0 and not summary['harness_errors']), name
        if requested[-1] == 'pass':
            assert invocations[-1]['state'] == 'exited' and invocations[-1]['returncode'] == 0, name
            assert any(report['suite'] == 'pass' and report['status'] == 'pass'
                       for report in invocations[-1]['reports']), 'failure suppressed the next requested suite'
        if name == 'alias':
            assert set(summary['suites']) == {'reported_alias'} and summary['counts']['pass'] == 1
            assert invocations[0]['report_paths'] == ['suites/reported_alias/fixture_case/report.json']
        if name == 'pass_and_skip':
            assert summary['counts'] == {'pass': 1, 'skip': 1, 'fail': 0, 'total': 2}
        if name == 'all_skip':
            assert summary['counts'] == {'pass': 0, 'skip': 1, 'fail': 0, 'total': 1}
        if name == 'pass_then_crash':
            assert invocations[0]['returncode'] == 19 and summary['counts']['pass'] == 2
        if name == 'failed_report_zero_exit':
            assert invocations[0]['returncode'] == 0 and summary['counts']['fail'] == 1
        inventory.append(name)
        print(f'{name}: ok', flush=True)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} dispatcher controls passed')


if __name__ == '__main__':
    main()
