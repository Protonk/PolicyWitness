"""Pre-extraction native adapter for the exposed historical replay."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from common import append, checkout_lock


def inventory(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file()}


def command(argv, artifact, name):
    append(artifact / 'commands.jsonl', dict(event='intent', command=argv, name=name))
    environment = {k:v for k,v in os.environ.items() if not k.startswith(('PYTEST','PYTHON'))}
    fds = checkout_lock.inherited_fds()
    assert len(fds) == 2, 'native command lacks protected descriptor handoff'
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=60,
                            env=environment, pass_fds=fds)
    (artifact / (name+'.stdout')).write_bytes(result.stdout)
    (artifact / (name+'.stderr')).write_bytes(result.stderr)
    append(artifact / 'commands.jsonl', dict(event='returned', command=argv, name=name,
           returncode=result.returncode, protected_fds=list(fds)))
    return result


def build_run(inputs, artifact, scratch, mutation=None):
    artifact.mkdir(parents=True)
    scratch.mkdir(parents=True)
    source = (inputs / 'pw_probe_runner.c').read_text()
    if mutation is not None:
        marker = '    slot->exec_valid = 1;'
        assert source.count(marker) == 1, 'exec assembly boundary changed: mutation was not formed'
        source = source.replace(marker, '    '+mutation+'\n'+marker)
    (artifact / 'pw_probe_runner.c').write_text(source)
    for header in inputs.glob('*.h'):
        shutil.copy2(header, artifact / header.name)
    shutil.copy2(inputs / 'exec_control.c', artifact / 'exec_control.c')
    (artifact / 'source-sha256.json').write_text(json.dumps(inventory(artifact),indent=2)+'\n')
    binary = scratch / 'exec-control'
    argv = ['/usr/bin/xcrun','--sdk','macosx','clang','-Wall','-Wextra','-Werror','-O2','-std=c11',
            '-I',str(artifact),str(artifact/'exec_control.c'),'-lsandbox','-o',str(binary)]
    build = command(argv,artifact,'build')
    assert build.returncode == 0, 'compile failed: '+build.stderr.decode()
    return command([str(binary)],artifact,'run')
