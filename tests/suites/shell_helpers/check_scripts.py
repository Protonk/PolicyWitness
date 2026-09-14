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
                 expected=None, rc=0, errexit=1, early_failure=None, ordered=True):
        work = out / name
        repo = work / 'fixture repo'
        library = repo / 'tests/lib/scripts.sh'
        library.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'tests/lib/scripts.sh', library)
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
                                      if record['script'] == 'tools/pw' else []), (name, record)
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
                setup = record['script'] in children[:2]
                assert record['runner_mode'] == (None if setup else 'byoxpc'), (name, record)
                assert record['service'] == (None if setup else 'fixture.service'), (name, record)
                assert record['kind'] == (None if setup else 'byoxpc'), (name, record)
            assert records[0]['env_path'] is None, name
            assert records[1]['env_path'].endswith('/runner_install/artifacts/runner_env.json'), name
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

    opt_in = [f'tests/suites/opt_in/{name}.sh' for name in ('a', 'b', 'c')]
    exercise('opt_in_continues', opt_in, wrapper='opt_in',
             modes={opt_in[0]: 'skip', opt_in[1]: 'fail'}, rc=1)
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
        ('auth_failure', {byoxpc[0]: 'fail'}, byoxpc[:2], 1),
        ('install_failure', {byoxpc[1]: 'fail'}, byoxpc[:2], 1),
        ('install_skip', {byoxpc[1]: 'skip'}, byoxpc[:2], 0),
        ('run_failure', {byoxpc[3]: 'fail'}, byoxpc + ['tools/pw'], 1),
    ):
        exercise(f'byoxpc_{name}', byoxpc, wrapper='runner_byoxpc', modes=modes,
                 expected=expected, rc=rc)
    (out / 'controls.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'{len(inventory)} script-group controls passed')


if __name__ == '__main__':
    main()
