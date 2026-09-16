"""Observe real wrapper processes with independent, harmless child scripts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'tests/fixtures/shell_case'


def main():
    out = Path(sys.argv[1]).resolve()
    inventory = []

    def exercise(name, children, *, wrapper=None, modes=None, missing=(),
                 expected=None, rc=0, errexit=1, early_failure=None, ordered=True, selected=None):
        work = out / name
        repo = work / 'fixture repo'
        library = repo / 'tests/lib/scripts.sh'
        library.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'tests/lib/scripts.sh', library)
        shutil.copyfile(ROOT / 'tests/lib/testlib.sh', library.with_name('testlib.sh'))
        if wrapper == 'runner_byoxpc':
            helper = repo / 'tests/fixtures/byoxpc/session.py'
            helper.parent.mkdir(parents=True)
            shutil.copyfile(FIXTURE / 'session_cleanup.py', helper)
        config = {'root': str(repo), 'journal': str(work / 'receipts.jsonl'), 'modes': modes or {}}
        config_path = work / 'config.json'
        config_path.write_text(json.dumps(config, indent=2) + '\n')
        for child in [*children, 'tools/pw']:
            if child in missing:
                continue
            path = repo / child
            path.parent.mkdir(parents=True, exist_ok=True)
            if child == early_failure:
                path.write_text('set -e\n/usr/bin/python3 "${CONTROL_SCRIPT_DRIVER}" "$0"\n'
                                'false\n/usr/bin/python3 "${CONTROL_SCRIPT_DRIVER}" "$0" forbidden\n')
            else:
                shutil.copyfile(FIXTURE / 'script_child.sh', path)
            path.chmod(0o755)
        env = {key: value for key, value in os.environ.items() if not key.startswith('PW_')}
        env.update(CONTROL_SCRIPT_CONFIG=str(config_path), CONTROL_ERREXIT=str(errexit),
                   CONTROL_SCRIPT_DRIVER=str(FIXTURE / 'script_child.py'),
                   PW_TEST_OUT_DIR=str(repo / 'tests/out'), PW_BIN=str(repo / 'tools/pw'))
        if selected is not None:
            env['PW_TEST_CASES'] = '\n'.join(selected)
        if wrapper:
            path = repo / f'tests/suites/{wrapper}/run.sh'
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path.relative_to(repo), path)
            argv = ['bash', str(path)]
        else:
            argv = ['bash', str(FIXTURE / 'script_group.sh'), str(library),
                    *(str(repo / child) for child in children)]
        result = subprocess.run(argv, cwd=work, env=env, capture_output=True, timeout=15)
        (work / 'stdout').write_bytes(result.stdout)
        (work / 'stderr').write_bytes(result.stderr)
        (work / 'exit.json').write_text(json.dumps({'returncode': result.returncode}) + '\n')
        assert result.returncode == rc, (name, result.returncode, result.stderr)
        journal = Path(config['journal'])
        records = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        expected = expected if expected is not None else [child for child in children if child not in missing]
        actual = [record['script'] for record in records]
        if ordered:
            assert actual == expected, (name, actual, expected)
        else:
            assert sorted(actual) == sorted(expected) and actual[0] == expected[0], (name, actual)
        for record in records:
            assert record['mode'] == config['modes'].get(record['script'], 'pass'), (name, record)
            assert record['argv'] == (['runner', 'remove', '--id', 'fixture-id']
                                      if record['script'] == 'tools/pw' else ['--suite', 'opt_in']
                                      if record['script'] == 'tests/run.sh' else []), (name, record)
        visible = [record for record in records if record['script'] != 'tools/pw']
        stdout = ''.join(f"{record['script']}: {record['mode']}\n" for record in visible).encode()
        assert result.stdout == stdout, (name, result.stdout, stdout)
        for record in visible:
            assert f"{record['script']}: stderr\n".encode() in result.stderr, (name, result.stderr)
        for child in missing:
            assert str(repo / child).encode() in result.stderr, (name, result.stderr)
        if not children:
            assert b'no child scripts supplied' in result.stderr, name
        assert not (work / 'CANARY').exists(), 'a script path was evaluated as shell code'
        if wrapper == 'runner_byoxpc':
            for record in records:
                assert record['alias'] == 'runner_byoxpc', (name, record)
                setup = record['script'].endswith(('/runner_auth_external.sh', '/runner_install.sh'))
                if record['script'] == 'tools/pw' and (modes or {}).get('tests/suites/runner_byoxpc/runner_install.sh') == 'partial_fail':
                    setup = True  # cleanup runs before runner-mode export
                assert record['runner_mode'] == (None if setup else 'byoxpc'), (name, record)
                assert record['service'] == (None if setup else 'fixture.service'), (name, record)
                assert record['kind'] == (None if setup else 'byoxpc'), (name, record)
                if record['script'].endswith('/runner_auth_external.sh'):
                    assert record['env_path'] is None, name
                if record['script'].endswith('/runner_install.sh'):
                    assert record['env_path'].endswith('/runner_install/artifacts/runner_env.json'), name
                if selected is not None and not setup and record['script'] != 'tools/pw':
                    assert record['selected_cases'] in selected and '\n' not in record['selected_cases'], (name, record)
        inventory.append(name)
        print(f'{name}: ok', flush=True)

    literal = "children/a $(touch CANARY) 'quoted'.sh"
    children = [literal, 'children/middle.sh', 'children/last.sh']
    for errexit in (0, 1):
        for mode in ('pass', 'skip', 'fail'):
            exercise(f'group_{mode}_errexit{errexit}', children, errexit=errexit,
                     modes={children[1]: mode}, rc=1 if mode == 'fail' else 0)
        exercise(f'group_missing_errexit{errexit}', children, errexit=errexit,
                 missing=[children[1]], rc=1)
        exercise(f'child_errexit{errexit}', children, errexit=errexit,
                 early_failure=children[1], rc=1)
        exercise(f'empty_errexit{errexit}', [], errexit=errexit, rc=1)

    bbx = ['tests/suites/blackbox_e2e/' + name for name in
           ('checker_controls.sh', 'bbx_001.sh', 'bbx_002.sh')]
    exercise('blackbox_skip', bbx, wrapper='blackbox_e2e', modes={bbx[0]: 'skip'})
    exercise('blackbox_failure', bbx, wrapper='blackbox_e2e', modes={bbx[1]: 'fail'}, rc=1)
    exercise('blackbox_missing', bbx, wrapper='blackbox_e2e', missing=[bbx[1]], rc=1)
    for wrapper, leaf in (('smoke', 'pw_specimen_smoke.sh'),
                          ('sbpl_allowdeny_consistency', 'sbpl_allowdeny_v1.sh')):
        child = f'tests/suites/{wrapper}/{leaf}'
        for mode in ('skip', 'fail'):
            exercise(f'{wrapper}_{mode}', [child], wrapper=wrapper, modes={child: mode},
                     rc=17 if mode == 'fail' else 0)

    exercise('opt_in_forward', ['tests/run.sh'], wrapper='opt_in')
    baseline = 'tests/suites/witness_contract/happy_path_baseline.sh'
    witness = [baseline] + sorted(str(path.relative_to(ROOT)) for path in
                                  (ROOT / 'tests/suites/witness_contract').glob('*.sh')
                                  if path.name not in ('run.sh', 'happy_path_baseline.sh'))
    exercise('witness_continues', witness, wrapper='witness_contract',
             modes={baseline: 'fail'}, rc=1, ordered=False)

    byoxpc = ['tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh',
              'tests/suites/runner_byoxpc/runner_install.sh',
              'tests/suites/smoke/pw_specimen_smoke.sh',
              'tests/suites/blackbox_menagerie/run.sh', 'tests/suites/blackbox_e2e/run.sh']
    for name, modes, expected, rc in (
        ('success', {}, byoxpc + ['tools/pw'], 0),
        ('auth_failure', {byoxpc[0]: 'fail'}, byoxpc + ['tools/pw'], 1),
        ('install_failure', {byoxpc[1]: 'fail'}, byoxpc[:2], 1),
        ('partial_install_failure', {byoxpc[1]: 'partial_fail'}, byoxpc[:2] + ['tools/pw'], 1),
        ('cleanup_failure', {'tools/pw': 'fail'}, byoxpc + ['tools/pw'], 1),
        ('install_skip', {byoxpc[1]: 'skip'}, byoxpc[:2], 0),
        ('run_failure', {byoxpc[3]: 'fail'}, byoxpc + ['tools/pw'], 1),
    ):
        exercise(f'byoxpc_{name}', byoxpc, wrapper='runner_byoxpc', modes=modes,
                 expected=expected, rc=rc)
    leaves = ['tests/suites/blackbox_e2e/bbx_001.sh', 'tests/suites/blackbox_e2e/bbx_002.sh']
    exercise('byoxpc_selected_leaf', byoxpc + leaves, wrapper='runner_byoxpc',
             selected=['runner_install', 'BBX-002'], expected=[byoxpc[1], leaves[1], 'tools/pw'])
    exercise('byoxpc_selected_failure_continues', byoxpc + leaves, wrapper='runner_byoxpc',
             selected=['runner_install', 'BBX-001', 'BBX-002'], modes={leaves[0]: 'fail'},
             expected=[byoxpc[1], *leaves, 'tools/pw'], rc=1)
    exercise('byoxpc_selected_install_failure', byoxpc + leaves, wrapper='runner_byoxpc',
             selected=['runner_install', 'BBX-002'], modes={byoxpc[1]: 'fail'}, expected=[byoxpc[1]], rc=1)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} script-group controls passed')


if __name__ == '__main__':
    main()
