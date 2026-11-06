"""Independent operation counts, delivery identity and actual fresh-open control.

The fixture uses synthetic extension callbacks, not native sandbox authority.
Mutation success requires the designated assertion after successful compilation;
compiler errors, signals and timeouts never count as detected behavior.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
NATIVE = Path('controller/tools/pw_probe_runner')
FIXTURE = Path('tests/fixtures/extension_controls/operation_control.c')
MUTATIONS = {
    'skip_issue': ('char *token = extension_issue(extension_class, slot->ext_target, 0);',
                   '(void)extension_class; char *token = NULL;', 'issue native call executed exactly once'),
    'skip_consume': ('int64_t result = extension_consume(in->token);',
                     'int64_t result = 202;', 'consume native call executed exactly once'),
    'skip_release': ('int64_t result = (int64_t)extension_release(handle_table[slot->ext_handle_index]);',
                     'int64_t result = 0;', 'release native call executed exactly once'),
    'wrong_delivery': ('if (candidate->resource_index != slot->ext_delivery_index) continue;',
                       '/* control: take the first available delivery */', 'consume selects the named delivery'),
    'inherited_read': ('int fd = open(slot->target, O_RDONLY | O_CLOEXEC);',
                       'int fd = dup(inherited_fd);', 'fresh read executes its own open'),
    'skip_dispatch_issue': ('case PW_ATTEMPT_EXTENSION_ISSUE: attempt_extension_issue(slot, timing, index); break;',
        'case PW_ATTEMPT_EXTENSION_ISSUE: break;', 'dispatch issue calls only its native issue boundary'),
    'skip_dispatch_consume': ('if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_consume_actor(slot);',
        'if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) { /* omitted dispatch */ }',
        'dispatch consume calls only its native consume boundary'),
    'skip_dispatch_release': ('if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_release_actor(slot);',
        'if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) { /* omitted dispatch */ }',
        'dispatch release calls only its native release boundary'),
    'misroute_dispatch_consume': ('if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_consume_actor(slot);',
        'if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_release_actor(slot);',
        'dispatch consume calls only its native consume boundary'),
    'misroute_dispatch_release': ('if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_release_actor(slot);',
        'if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_consume_actor(slot);',
        'dispatch release calls only its native release boundary'),
    'crossed_dispatch_handle': ('if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) attempt_extension_release_actor(slot);',
        'if (g_hdr->actor_mode != PW_ACTOR_MODE_LEGACY) { slot->ext_handle_index = 9; attempt_extension_release_actor(slot); }',
        'dispatch release receives its own distinct handle'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(out, scratch):
    out.mkdir(parents=True, exist_ok=True); scratch.mkdir(parents=True, exist_ok=True)
    results = []
    for name in ['baseline', *MUTATIONS]:
        directory = out / name; source = directory / 'source'
        shutil.copytree(ROOT / NATIVE, source / NATIVE)
        (source / FIXTURE).parent.mkdir(parents=True)
        shutil.copyfile(ROOT / FIXTURE, source / FIXTURE)
        worker = source / NATIVE / 'pw_probe_runner.c'
        mutation = None
        if name in MUTATIONS:
            before, after, expected = MUTATIONS[name]
            content = worker.read_text()
            assert content.count(before) == 1, (name, 'source anchor changed; review this mutation')
            mutation = dict(before=before, after=after, expected=expected, original_sha256=digest(worker))
            worker.write_text(content.replace(before, after, 1))
        inventory = {str(p.relative_to(source)): digest(p) for p in sorted(source.rglob('*')) if p.is_file()}
        (directory / 'source.json').write_text(json.dumps(dict(mutation=mutation, sha256=inventory), indent=2) + '\n')
        product = scratch / name
        command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
                   '-Wno-deprecated-declarations', '-O2', '-std=c11', str(source / FIXTURE), '-lsandbox', '-o', str(product)]
        with (directory / 'build.log').open('w') as log:
            compiled = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90)
        (directory / 'build.json').write_text(json.dumps(dict(command=command, returncode=compiled.returncode,
            product=str(product), product_sha256=digest(product) if product.is_file() else None), indent=2) + '\n')
        assert compiled.returncode == 0, (name, 'build failure is not mutation detection')
        observed = subprocess.run([str(product)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15, text=True)
        (directory / 'run.log').write_text(observed.stdout)
        row = dict(variant=name, returncode=observed.returncode, expected_rejection=MUTATIONS[name][2] if name in MUTATIONS else None)
        results.append(row)
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        if name == 'baseline':
            assert observed.returncode == 0 and 'fresh descriptor ownership observed' in observed.stdout, (name, observed.stdout)
        else:
            assert observed.returncode == 73 and 'CONTROL_REJECTED: ' + MUTATIONS[name][2] in observed.stdout, (name, observed.stdout)
    print(f'baseline and {len(MUTATIONS)} targeted body/dispatch counterexamples classified by independent call, handle and descriptor observations')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
