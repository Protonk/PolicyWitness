"""Plan the public test command before initializing any execution evidence."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import uuid

sys.dont_write_bytecode = True
from suite_run import execute, save


def catalog(root):
    data = json.loads((root / 'tests/catalog.json').read_text())
    cases, suites, report_paths = {}, {}, {}
    for suite, group in data['suites'].items():
        if not re.fullmatch(r'[a-z][a-z0-9_]*', suite):
            raise ValueError(f'invalid catalog suite: {suite}')
        suites[suite] = []
        for entry in group.get('cases', []):
            entry = {'id': entry} if isinstance(entry, str) else entry
            leaf = entry['id']
            if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', leaf):
                raise ValueError(f'invalid catalog case: {leaf}')
            key = f'{suite}/{leaf}'
            if key in cases:
                raise ValueError(f'duplicate catalog case: {key}')
            case = {name: group[name] for name in
                    ('command', 'requires', 'default', 'context', 'skip_reasons') if name in group}
            case.update(entry)
            case.update(id=key, suite=suite, test_id=leaf)
            case.setdefault('description', leaf.replace('_', ' '))
            case.setdefault('requires', [])
            case.setdefault('default', True)
            case.setdefault('context', 'standard')
            case.setdefault('skip_reasons', [])
            case.setdefault('depends_on', [])
            case.setdefault('report_suite', suite)
            if not isinstance(case['report_suite'], str) or not re.fullmatch(r'[a-z][a-z0-9_]*', case['report_suite']):
                raise ValueError(f'invalid report_suite: {key}')
            report_path = (case['report_suite'], leaf)
            if report_path in report_paths:
                raise ValueError(f'catalog report path {"/".join(report_path)} shared by {report_paths[report_path]} and {key}')
            report_paths[report_path] = key
            if not case.get('command') or not all(isinstance(x, str) and x for x in case['command']):
                raise ValueError(f'missing command: {key}')
            if not isinstance(case['default'], bool) or case['context'] not in ('standard', 'byoxpc'):
                raise ValueError(f'invalid default/context: {key}')
            for field in ('requires', 'skip_reasons', 'depends_on'):
                if not isinstance(case[field], list) or not all(isinstance(x, str) and x for x in case[field]):
                    raise ValueError(f'invalid {field}: {key}')
            unknown = set(case['requires']) - {'app', 'worker', 'cargo', 'swift', 'clang', 'gui', 'identity'}
            if unknown:
                raise ValueError(f'unknown prerequisites for {key}: {sorted(unknown)}')
            cases[key] = case
            suites[suite].append(key)
    for suite, group in data['suites'].items():
        suites[suite].extend(group.get('include', []))
        if not suites[suite] or any(key not in cases for key in suites[suite]):
            raise ValueError(f'empty suite or unknown included case: {suite}')
    for key, case in cases.items():
        if any(dep not in cases for dep in case['depends_on']):
            raise ValueError(f'unknown dependency: {key}')
    return cases, suites


def select(cases, suites, args):
    unknown = set(args.suite) - suites.keys()
    unknown_cases = set(args.case) - cases.keys()
    if unknown or unknown_cases:
        raise ValueError(f'unknown selection: suites={sorted(unknown)}, cases={sorted(unknown_cases)}; use --all --list')
    selected = set(args.case)
    for suite in args.suite:
        selected.update(suites[suite])
    if args.all:
        selected.update(cases)
    elif not args.suite and not args.case:
        selected.update(key for key, case in cases.items() if case['default'])
    requested = set(selected)
    ordered, visiting = [], set()

    def add(key):
        if key in visiting:
            raise ValueError(f'dependency cycle: {key}')
        if key in ordered:
            return
        visiting.add(key)
        for dep in cases[key]['depends_on']:
            add(dep)
        visiting.remove(key)
        ordered.append(key)

    for key in cases:
        if key in selected:
            add(key)
    if not ordered:
        raise ValueError('selection is empty')
    return [{**cases[key], 'selection': 'requested' if key in requested else 'dependency'} for key in ordered]


def resolve_config(root, env):
    def path(name, default=None, *, resolve=True):
        raw = env.get(name, default)
        if not raw:
            raise ValueError(f'{name} must not be empty')
        p = Path(raw)
        p = p if p.is_absolute() else root / p
        return p.resolve() if resolve else p

    internal = [key for key in env if key.startswith('PW_TEST_RUNNER_') or key in
                ('PW_TEST_SUITE_OVERRIDE', 'PW_TEST_CASES', 'PW_TEST_EVENTS')]
    if internal:
        raise ValueError(f'internal test settings cannot be supplied to tests/run.sh: {sorted(internal)}; select runner_byoxpc cases instead')
    # Infer each named bundle before following the executable's symlink. Whole
    # bundle aliases are fine; an executable must not redirect to another app.
    named_bins = [path(name, resolve=False) for name in ('PW_BIN', 'PW_BIN_PATH') if name in env]
    bin_apps = []
    for binary in named_bins:
        if binary.parts[-3:] != ('Contents', 'MacOS', 'policy-witness'):
            raise ValueError('controller override must identify Contents/MacOS/policy-witness in an app bundle')
        bin_apps.append(binary.parents[2].resolve())
    bins = [binary.resolve() for binary in named_bins]
    if len(set(bins)) > 1:
        raise ValueError('PW_BIN and PW_BIN_PATH identify different controllers')
    if 'PW_APP_DIR' in env:
        app = path('PW_APP_DIR')
    elif bins:
        app = bin_apps[0]
    else:
        app = (root / 'dist/PolicyWitness.app').resolve()
    binary = (app / 'Contents/MacOS/policy-witness').resolve()
    if app not in binary.parents:
        raise ValueError('controller must resolve inside the selected app bundle')
    if any(named_app != app for named_app in bin_apps) or (bins and bins[0] != binary):
        raise ValueError('PW_APP_DIR and controller override identify different artifacts')
    out = path('PW_TEST_OUT_DIR', 'tests/out')
    base = root / 'tests/out'
    if out != base and base not in out.parents:
        raise ValueError(f'PW_TEST_OUT_DIR must resolve within {base}; got {out}')
    if out.exists() and not out.is_dir():
        raise ValueError('PW_TEST_OUT_DIR must be a directory')
    if out == app or out in app.parents or app in out.parents:
        raise ValueError('test output must not overlap the tested app bundle')
    quiet = env.get('PW_TEST_QUIET', '0')
    if quiet not in ('', '0', '1'):
        raise ValueError('PW_TEST_QUIET must be 0 or 1')
    run_id = env.get('PW_TEST_RUN_ID', '')
    # The menagerie embeds this label in temporary paths and SBPL literals.
    if run_id and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', run_id):
        raise ValueError('PW_TEST_RUN_ID must start with a letter/digit and contain at most 128 letters, digits, dots, underscores, or hyphens')
    return {'app_dir': str(app), 'pw_bin': str(binary), 'out_dir': str(out), 'quiet': quiet == '1'}


def main():
    if not __debug__:
        raise SystemExit('ERROR: Python assertions are disabled; unset PYTHONOPTIMIZE before running tests')
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description='Run the default battery, or the union of explicit selectors.', allow_abbrev=False)
    parser.add_argument('--all', action='store_true', help='select every registered case, including opt-ins')
    parser.add_argument('--suite', action='append', default=[], metavar='NAME', help='select a suite (repeatable)')
    parser.add_argument('--case', action='append', default=[], metavar='SUITE/CASE', help='select an exact case ID (repeatable)')
    parser.add_argument('--list', action='store_true', help='print the selected plan as JSON without running or writing anything')
    parser.epilog = ('Configuration: PW_APP_DIR chooses the app; PW_BIN/PW_BIN_PATH are agreeing bundle-controller aliases. '
                     'PW_TEST_OUT_DIR (inside tests/out) is replaced on execution. PW_TEST_RUN_ID labels evidence. '
                     'PW_TEST_QUIET=1 suppresses routine case messages. Relative paths are repository-relative. '
                     'Use --all --list to discover cases, suites, prerequisites, and skip contracts.')
    args = parser.parse_args()
    try:
        cases, suites = catalog(root)
        selected = select(cases, suites, args)
        config = resolve_config(root, os.environ)
        for case in selected:
            command = case['command']
            if command[0] != 'bash' or len(command) < 2:
                raise ValueError(f'case command must start with bash and a repository script: {case["id"]}')
            script = (root / command[1]).resolve()
            if root not in script.parents or not script.is_file() or not os.access(script, os.X_OK):
                raise ValueError(f'missing or nonexecutable case runner: {script}')
        selected_ids = {c['id'] for c in selected}
        plan = {'schema_version': 1, 'configuration': config, 'cases': selected,
                'selection': {'mode': 'all' if args.all else 'explicit' if args.suite or args.case else 'default',
                              'suites': list(dict.fromkeys(args.suite)), 'cases': list(dict.fromkeys(args.case))},
                'containing_suites': {name: [key for key in keys if key in selected_ids]
                           for name, keys in suites.items() if selected_ids.intersection(keys)}}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    if args.list:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    out = Path(config['out_dir'])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    run_id = os.environ.get('PW_TEST_RUN_ID') or time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '_' + uuid.uuid4().hex[:8]
    started = time.time_ns() // 1_000_000
    save(out / 'plan.json', plan)
    return execute(root, out, run_id, started, plan, config)


if __name__ == '__main__':
    sys.exit(main())
