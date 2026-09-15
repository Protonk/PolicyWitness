"""Public-command contracts checked against independent execution receipts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner

LITERAL = "literal spaces 'quoted' $(touch CANARY)"


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def snapshot(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    inventory = []
    all_ids = ['probe/first', 'probe/second', 'optional/limited', 'equipment/app', 'remote/install', 'remote/first']

    def exercise(name, args, expected=(), *, code=0, inspect=False, invalid=False, settings=None,
                 modes=None, codes=(), app=False, corrupt=None, skipped=0, unrun=0):
        work = out / name
        repo = work / 'fixture repo'
        suites = {
            'probe': {'command': ['bash', 'tests/suites/probe/run.sh', LITERAL], 'cases': ['first', 'second']},
            'optional': {'command': ['bash', 'tests/suites/optional/run.sh', LITERAL], 'default': False,
                         'cases': [{'id': 'limited', 'skip_reasons': ['fixture_unavailable']}]},
            'equipment': {'command': ['bash', 'tests/suites/equipment/run.sh', LITERAL], 'default': False,
                          'requires': ['app'], 'cases': ['app']},
            'remote': {'command': ['bash', 'tests/suites/remote/run.sh', LITERAL], 'default': False,
                       'context': 'byoxpc', 'cases': ['install', {'id': 'first', 'depends_on': ['remote/install']}]},
            'alias': {'include': ['probe/first']},
        }
        install_runner(ROOT, repo, suites)
        for suite in ('probe', 'optional', 'equipment', 'remote'):
            path = repo / f'tests/suites/{suite}/run.sh'
            path.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'tests/fixtures/dispatcher/selection.sh', path)
            path.chmod(0o755)
        fixture = repo / 'tests/fixtures/dispatcher/selection.py'
        fixture.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'tests/fixtures/dispatcher/selection.py', fixture)
        child_out = repo / 'tests/out'
        child_out.mkdir()
        (child_out / 'old.bin').write_bytes(b'prior evidence\x00\xff')
        (child_out / 'run.json').write_text('{"old":true}')
        app_dir = repo / 'An app.app'
        binary = app_dir / 'Contents/MacOS/policy-witness'
        if app:
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/bin/sh\nexit 0\n')
            binary.chmod(0o755)
        receipt = work / 'receipts.jsonl'
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
        # Deliberately let inspection try to create bytecode if it is careless.
        env.pop('PYTHONDONTWRITEBYTECODE', None)
        env.update(PW_TEST_RUN_ID=name, CONTROL_SELECTION_RECEIPTS=str(receipt),
                   CONTROL_SELECTION_MODES=json.dumps(modes or {}))
        if settings:
            env.update({k: v.replace('{repo}', str(repo)) for k, v in settings.items()})
        if app and not any(k in env for k in ('PW_APP_DIR', 'PW_BIN', 'PW_BIN_PATH')):
            env['PW_APP_DIR'] = str(app_dir)
        if corrupt:
            corrupt(repo)
        before = snapshot(repo)
        result = subprocess.run(['bash', str(repo / 'tests/run.sh'), *args], cwd=work,
                                env=env, capture_output=True, timeout=15)
        (work / 'stdout').write_bytes(result.stdout)
        (work / 'stderr').write_bytes(result.stderr)
        (work / 'exit.json').write_text(json.dumps({'argv': args, 'returncode': result.returncode}) + '\n')
        require(result.returncode == code, f'{name}: exit {result.returncode}, expected {code}: {result.stderr!r}')
        records = [json.loads(line) for line in receipt.read_text().splitlines()] if receipt.exists() else []
        if inspect or invalid:
            require(not records, f'{name}: inspection/invalid command executed work')
            require(snapshot(repo) == before, f'{name}: inspection/invalid command changed files')
            if inspect and '--list' in args:
                plan = json.loads(result.stdout)
                require([c['id'] for c in plan['cases']] == list(expected), f'{name}: wrong listed selection')
            inventory.append(name)
            return
        require([r['id'] for r in records] == list(expected), f'{name}: wrong execution receipts: {records}')
        summary = json.loads((child_out / 'run.json').read_text())
        plan = json.loads((child_out / 'plan.json').read_text())
        require(summary['plan'] == plan and summary['configuration'] == plan['configuration'], f'{name}: configuration/plan changed')
        require(summary['requested_suites'] == plan['selection']['suites']
                and summary['requested_cases'] == plan['selection']['cases'], f'{name}: original selectors lost')
        require(summary['ok'] is (code == 0), f'{name}: exit/summary disagree')
        require(set(codes) <= {e['code'] for e in summary['harness_errors']}, f'{name}: missing harness diagnostics')
        require(summary['completion'] == {'selected': len(plan['cases']), 'completed': len(plan['cases']) - skipped - unrun,
                                          'skipped': skipped, 'unrun': unrun}, f'{name}: wrong completion: {summary["completion"]}')
        require([r['id'] for r in summary['case_results']] == [c['id'] for c in plan['cases']], f'{name}: incomplete accounting')
        require(not (child_out / 'old.bin').exists(), f'{name}: stale evidence survived execution')
        config = summary['configuration']
        for record in records:
            require(record['argv'] == [LITERAL] and record['cwd'] == str(repo), f'{name}: argv/cwd drift')
            require(record['app'] == config['app_dir'] and record['bin'] == record['rust_bin'] == config['pw_bin'], f'{name}: artifact disagreement')
            require(record['quiet'] == ('1' if config['quiet'] else ''), f'{name}: quiet not normalized')
        require(not (repo / 'CANARY').exists(), f'{name}: shell interpolation')
        inventory.append(name)

    exercise('default', [], ['probe/first', 'probe/second'])
    exercise('one_case', ['--case', 'probe/second'], ['probe/second'])
    exercise('suite', ['--suite', 'probe'], ['probe/first', 'probe/second'])
    exercise('deduplicate', ['--suite', 'alias', '--case', 'probe/first', '--suite', 'probe', '--suite', 'probe'], ['probe/first', 'probe/second'])
    exercise('union', ['--case', 'optional/limited', '--suite', 'probe'], ['probe/first', 'probe/second', 'optional/limited'])
    exercise('reverse_union', ['--suite', 'probe', '--case', 'optional/limited'], ['probe/first', 'probe/second', 'optional/limited'])
    for name, args in [('all', ['--all']), ('all_first', ['--all', '--suite', 'probe']),
                       ('all_last', ['--suite', 'probe', '--all'])]:
        exercise(name, args, all_ids, app=True)
    exercise('contexts', ['--case', 'remote/first', '--case', 'probe/first'], ['probe/first', 'remote/install', 'remote/first'])
    exercise('dependency', ['--case', 'remote/first'], ['remote/install', 'remote/first'])
    for args, expected in [(['--list'], ['probe/first', 'probe/second']), (['--all', '--list'], all_ids),
                           (['--case', 'remote/first', '--list'], ['remote/install', 'remote/first'])]:
        exercise('list_' + str(len(inventory)), args, expected, inspect=True)
    exercise('help', ['--help'], inspect=True)
    for args in [['--describe'], ['--allow-skips'], ['--default'], ['--fail-fast'], ['--timeout', '4'],
                 ['--dry-run'], ['--sui', 'probe'], ['--suite'], ['--case'], ['--case', ''],
                 ['--all', '--suite', 'absent'], ['--case', 'first'], ['--case', 'probe/missing'],
                 ['--suite', '../probe'], ['--suite', 'probe', 'extra']]:
        exercise('invalid_' + str(len(inventory)), args, code=2, invalid=True)
    for key in ('PW_BIN', 'PW_BIN_PATH'):
        exercise('alias_' + key, ['--suite', 'equipment'], ['equipment/app'], app=True,
                 settings={key: 'An app.app/Contents/MacOS/policy-witness'})
    exercise('agreeing_aliases', ['--suite', 'equipment'], ['equipment/app'], app=True,
             settings={'PW_APP_DIR': 'An app.app', 'PW_BIN': '{repo}/An app.app/Contents/MacOS/policy-witness',
                       'PW_BIN_PATH': 'An app.app/Contents/MacOS/policy-witness'})
    for settings in [
        {'PW_BIN': '/a', 'PW_BIN_PATH': '/b'}, {'PW_BIN': '/standalone'},
        {'PW_APP_DIR': 'An app.app', 'PW_BIN': 'Other.app/Contents/MacOS/policy-witness'},
        {'PW_APP_DIR': ''}, {'PW_TEST_OUT_DIR': '../outside'}, {'PW_TEST_OUT_DIR': ''},
        {'PW_TEST_RUNNER_MODE': 'byoxpc'}, {'PW_TEST_RUNNER_SERVICE': 'ignored.service'},
        {'PW_TEST_SUITE_OVERRIDE': 'ignored'}, {'PW_TEST_CASES': 'ignored'},
        {'PW_TEST_EVENTS': '/tmp/ignored'}, {'PW_TEST_QUIET': 'false'},
        {'PW_APP_DIR': 'tests/out/Erased.app'},
        {'PW_TEST_RUN_ID': '../../escape'}, {'PW_TEST_RUN_ID': 'literal " quote'},
    ]:
        exercise('config_error_' + str(len(inventory)), ['--suite', 'probe'], code=2, invalid=True, settings=settings)
    exercise('symlink_escape', ['--suite', 'probe'], code=2, invalid=True,
             settings={'PW_TEST_OUT_DIR': 'tests/out/escape'},
             corrupt=lambda repo: (repo / 'tests/out/escape').symlink_to(repo.parent, target_is_directory=True))
    for value in ('0', '1'):
        exercise('quiet_' + value, ['--case', 'probe/first'], ['probe/first'], settings={'PW_TEST_QUIET': value})
    exercise('missing_equipment', ['--suite', 'equipment', '--suite', 'probe'], ['probe/first', 'probe/second'],
             code=1, codes=['not_run', 'unrun_case'], unrun=1)
    for mode, codes, unrun in [('fail', ['suite_exit'], 0), ('silent', ['empty_suite', 'unrun_case'], 1),
                             ('crash', ['suite_exit', 'unrun_case'], 1), ('wrong', ['unselected_case', 'unrun_case'], 1),
                             ('duplicate', ['case_start', 'case_end'], 0), ('skip_unknown', ['unexpected_skip'], 0)]:
        exercise('failure_' + mode, ['--suite', 'probe'], ['probe/first', 'probe/second'], code=1,
                 modes={'probe/first': mode}, codes=codes, unrun=unrun, skipped=1 if mode.startswith('skip') else 0)
    exercise('declared_skip', ['--suite', 'optional'], ['optional/limited'],
             modes={'optional/limited': 'skip_declared'}, skipped=1)
    exercise('skip_not_allowed_here', ['--case', 'probe/first'], ['probe/first'], code=1,
             modes={'probe/first': 'skip_declared'}, codes=['unexpected_skip'], skipped=1)
    # The catalog's declared runner must exist before any selected command runs.
    exercise('missing_entrypoint', ['--all'], code=2, invalid=True,
             corrupt=lambda repo: (repo / 'tests/suites/optional/run.sh').unlink())
    def dependent(repo):
        path = repo / 'tests/catalog.json'
        value = json.loads(path.read_text())
        value['suites']['optional']['cases'][0]['depends_on'] = ['probe/first']
        path.write_text(json.dumps(value))
    exercise('failed_dependency', ['--suite', 'optional', '--case', 'probe/second'],
             ['probe/second', 'probe/first'], code=1, codes=['not_run', 'unrun_case'], unrun=1,
             modes={'probe/first': 'fail'}, corrupt=dependent)
    # Real catalog integration pins the intended public relationships, not its
    # private representation or a generated expected copy of the catalog.
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
    def real_list(*args):
        result = subprocess.run(['bash', str(ROOT / 'tests/run.sh'), *args, '--list'],
                                env=clean_env, capture_output=True, timeout=10)
        require(result.returncode == 0, f'real catalog list failed: {result.stderr!r}')
        return json.loads(result.stdout)
    default_ids = {c['id'] for c in real_list()['cases']}
    require({'blackbox_menagerie/validation_controls', 'blackbox_e2e/checker_controls',
             'runner_filter_sysctl_name/checker_controls', 'witness_contract/happy_path_baseline'} <= default_ids,
            'ordinary controls/contracts missing from the real default battery')
    full = real_list('--all')['cases']
    opt = real_list('--suite', 'opt_in')['cases']
    require({c['id'] for c in opt} == {c['id'] for c in full if not c['default']},
            'opt_in group differs from non-default catalog membership')
    joined = real_list('--suite', 'witness_contract', '--suite', 'runner_validator_failure')['cases']
    for leaf in ('validator_decode_failure_reports_degraded', 'validator_unavailable_reports_degraded'):
        require([c['id'] for c in joined if c['test_id'] == leaf] == [f'runner_validator_failure/{leaf}'],
                f'{leaf}: shared suites duplicated the same contract case')
    inventory.append('real_catalog_relationships')
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} test command controls passed')


if __name__ == '__main__':
    main()
