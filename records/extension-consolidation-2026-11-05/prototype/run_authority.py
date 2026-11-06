#!/usr/bin/env python3
"""Isolated authority experiment. Invoke only from an unsandboxed shell.

Builds/signs a derived native fixture; never changes the app or registry.
Output directory must not exist. This is investigation, not a catalog case.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]).resolve()
identity = sys.argv[2]
out.mkdir(parents=True, exist_ok=False)

def save(name, value):
    (out / name).write_text(json.dumps(value, indent=2) + '\n')

def command(name, argv, check=True):
    # The fixture owns and reaps its direct children; the group deadline is
    # only emergency containment and is recorded distinctly if reached.
    import signal
    p = subprocess.Popen([str(x) for x in argv], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = p.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(p.pid, signal.SIGKILL)
        stdout, stderr = p.communicate()
    (out / (name + '.stdout')).write_bytes(stdout)
    (out / (name + '.stderr')).write_bytes(stderr)
    save(name + '.command.json', dict(argv=[str(x) for x in argv], rc=p.returncode,
                                    deadline=timed_out, supervisor_pid=p.pid))
    if check:
        assert not timed_out and p.returncode == 0, name
    return stdout

source = ROOT / 'tests/fixtures/sandbox_extensions/native.c'
original = source.read_text()
(out / 'native.original.c').write_text(original)
s = original
def replace(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

replace('struct evidence {', '''struct evidence {
    char issuer_executable[PATH_MAX], worker_executable[PATH_MAX];
    int issuer_executable_rc, worker_executable_rc;
    struct access_result issuer_baseline;
''')
replace('    close(3); close(4);', '''    close(3); close(4);
    char *self_path = !strcmp(role, "--issuer") ? e->issuer_executable : e->worker_executable;
    uint32_t self_size = PATH_MAX;
    int self_rc = _NSGetExecutablePath(self_path, &self_size);
    if (!strcmp(role, "--issuer")) e->issuer_executable_rc = self_rc;
    else e->worker_executable_rc = self_rc;''')
replace('        issue_fn issue =', '''        access_file(e->target, &e->issuer_baseline, 0);
        issue_fn issue =''')
replace('    if (argc != 5)', '    if (argc != 8)')
replace('    int wspawn = spawn_role(executable, "--worker", efd, tfd, &worker);', '''    int parent_apply_rc = -999, parent_apply_errno = 0;
    if (!strcmp(argv[7], "restricted")) {
        if (strchr(e->target, '"') || strchr(e->target, '\\\\')) return 2;
        char profile[PATH_MAX + 128];
        snprintf(profile, sizeof(profile), "(version 1) (allow default) (deny file-read-data (literal \\\"%s\\\"))", e->target);
        compile_fn parent_compile = (compile_fn)dlsym(RTLD_DEFAULT, "sandbox_compile_string");
        apply_fn parent_apply = (apply_fn)dlsym(RTLD_DEFAULT, "sandbox_apply");
        char *error = NULL;
        void *compiled = parent_compile ? parent_compile(profile, NULL, &error) : NULL;
        if (!compiled || !parent_apply) return 90;
        errno = 0; parent_apply_rc = parent_apply(compiled); parent_apply_errno = errno;
        if (parent_apply_rc != 0) return 90;
    }
    int wspawn = spawn_role(argv[5], "--worker", efd, tfd, &worker);''')
replace('spawn_role(executable, "--issuer", efd, tfd, &issuer)', 'spawn_role(argv[6], "--issuer", efd, tfd, &issuer)')
replace('    fputs("{\\\"scenario\\\":", f);', '''    fprintf(f, "{\\\"parent_apply_rc\\\":%d,\\\"parent_apply_errno\\\":%d,", parent_apply_rc, parent_apply_errno);
    fputs("\\\"issuer_executable\\\":", f); string(f, e->issuer_executable);
    fputs(",\\\"worker_executable\\\":", f); string(f, e->worker_executable);
    fprintf(f, ",\\\"issuer_executable_rc\\\":%d,\\\"worker_executable_rc\\\":%d", e->issuer_executable_rc, e->worker_executable_rc);
    fputs(",\\\"issuer_baseline\\\":", f); json_access(f, &e->issuer_baseline);
    fputs(",\\\"scenario\\\":", f);''')
(out / 'native.c').write_text(s)
save('source.json', dict(source=str(source), sha256=hashlib.sha256(original.encode()).hexdigest(),
                         generated_sha256=hashlib.sha256(s.encode()).hexdigest(),
                         driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
command('os', ['/usr/bin/sw_vers'])
command('compiler', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '--version'])
command('build', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
                 '-O2', '-g', '-std=c11', '-fno-builtin-malloc', '-fno-builtin-free',
                 '-mmacosx-version-min=26.0', out / 'native.c', '-lsandbox', '-o', out / 'unsigned'])
plist = out / 'selected.plist'
plist.write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': True}))
for role in ('host', 'selected', 'unentitled'):
    binary = out / role
    shutil.copyfile(out / 'unsigned', binary)
    binary.chmod(0o755)
    args = ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp', '-s', identity]
    if role != 'unentitled':
        args += ['--entitlements', plist]
    command('sign-' + role, args + [binary])
    command('verify-' + role, ['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', binary])
    command('signature-' + role, ['/usr/bin/codesign', '-dvvv', binary])
    raw = command('entitlements-' + role, ['/usr/bin/codesign', '-d', '--entitlements', ':-', binary])
    observed = plistlib.loads(raw) if raw.strip() else {}
    assert observed == ({} if role == 'unentitled' else {'com.apple.security.cs.allow-jit': True}), observed
save('signed-hashes.json', {r: hashlib.sha256((out / r).read_bytes()).hexdigest()
                           for r in ('host', 'selected', 'unentitled')})
target = out / 'target'
target.write_bytes(b'PW authority variant prototype\n')
summary = {}
for mode, case in [('ordinary', 'lifecycle'), ('ordinary', 'issuer_exit'),
                   ('ordinary', 'no_consume'), ('ordinary', 'no_predicate'),
                   ('restricted', 'lifecycle')]:
    name = mode + '-' + case
    raw = command(name, [out / 'host', case, target, target, 'plain', out / 'selected',
                         out / 'unentitled', mode])
    row = json.loads(raw)
    assert row['worker_reaped'] == row['issuer_reaped'] == 1
    assert row['worker_wait_status'] == row['issuer_wait_status'] == 0
    assert row['token_guard_passed'] and row['worker_erased_channel']
    assert row['issuer_executable_rc'] == row['worker_executable_rc'] == 0
    assert Path(row['issuer_executable']).resolve() == out / 'unentitled'
    assert Path(row['worker_executable']).resolve() == out / 'selected'
    assert len({row['host_pid'], row['issuer_pid'], row['worker_pid']}) == 3
    assert target.read_bytes() == b'PW authority variant prototype\n'
    if mode == 'ordinary':
        assert row['issuer_baseline']['content_hex'] == target.read_bytes().hex()
        assert row['issue']['nonnull']
        if case == 'no_consume':
            assert not row['consume']['attempted']
        else:
            assert row['consume']['attempted'] and row['consume']['native_rc'] != -1
        access = row['boundaries'][2]['access']
        if case in ('lifecycle', 'issuer_exit'):
            assert access['content_hex'] == target.read_bytes().hex()
        else:
            assert access['open_rc'] < 0
    else:
        assert row['parent_apply_rc'] == 0
        assert row['issuer_baseline']['open_rc'] < 0
        assert row['boundaries'][0]['access']['open_rc'] < 0
    summary[name] = dict(host_pid=row['host_pid'], issuer_pid=row['issuer_pid'], worker_pid=row['worker_pid'],
                         parent_apply_rc=row['parent_apply_rc'], cleanup='both_direct_children_reaped')
save('summary.json', summary)
print(json.dumps(summary, indent=2))
