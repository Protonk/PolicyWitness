"""Build disposable worker variants and require specific contract failures."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[2]
sys.path.insert(0, str(SUITE))
from check import run_worker


def replace_once(source, old, new):
    assert source.count(old) == 1, f'mutation anchor changed: {old!r}; review this development recipe'
    return source.replace(old, new, 1)


def main():
    out, helper, harness = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    source_dir = ROOT / 'controller' / 'tools' / 'pw_probe_runner'
    source = (source_dir / 'pw_worker_exec.h').read_text()
    leak_env = replace_once(source, 'static char *empty_envp[] = { NULL };', 'extern char **environ;')
    leak_env = replace_once(leak_env, 'argv_local, empty_envp);', 'argv_local, environ);')
    leak_fds = replace_once(source, 'POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETPGROUP',
                           'POSIX_SPAWN_SETPGROUP')
    summaries = []
    for name, body, expected in [
            ('baseline', source, None),
            ('inherited_environment', leak_env, 'inherited environment:'),
            ('inherited_descriptors', leak_fds, 'inherited descriptors:')]:
        case = out / name
        case.mkdir(parents=True, exist_ok=True)
        # Compile a complete copied closure: the mutation must replace the
        # included exec owner, never leave production resolving a live header.
        for path in source_dir.glob('*.h'):
            shutil.copy2(path, case / path.name)
        candidate_source = case / 'pw_probe_runner.c'
        shutil.copy2(source_dir / candidate_source.name, candidate_source)
        (case / 'pw_worker_exec.h').write_text(body)
        sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in case.iterdir() if p.suffix in ('.c', '.h')}
        (case / 'source-sha256.json').write_text(json.dumps(sources, indent=2, sort_keys=True) + '\n')
        worker = case / 'worker'
        command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra',
                   '-Werror', '-O2', '-std=c11', '-I', str(case), '-lsandbox',
                   str(candidate_source), '-o', str(worker)]
        (case / 'build-command.json').write_text(json.dumps(command, indent=2) + '\n')
        with (case / 'build.log').open('wb') as log:
            subprocess.run(command,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
        try:
            run_worker(str(worker), helper, harness, case)
        except AssertionError as error:
            if expected is None or expected not in str(error):
                raise
            rejection = str(error)
            print(f'{name}: expected rejection: {rejection}', flush=True)
            observations = json.loads((case / 'observations.json').read_text())
            launch = json.loads((case / 'harness.jsonl').read_text().splitlines()[0])
            if name == 'inherited_environment':
                assert all(r['env_count'] == 1 and r['env_value'] == launch['env_value']
                           for r in observations)
            else:
                assert all(r['canary_rc'] == 32 and r['canary_errno'] == 0
                           and r['canary_hex'] == launch['canary_hex'] for r in observations)
            summaries.append({'variant': name, 'rejected': True, 'reason': rejection})
        else:
            assert expected is None, f'{name}: contract failed to detect deliberate leak'
            summaries.append({'variant': name, 'rejected': False})
    (out / 'mutations.json').write_text(json.dumps(summaries, indent=2) + '\n')


if __name__ == '__main__':
    main()
