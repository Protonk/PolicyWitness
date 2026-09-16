"""Fixture setup only: copy the public runner and supply an independent catalog."""
import json
from pathlib import Path
import shutil


def install_runner(source, destination, suites, *, signed_fixtures=False):
    for relative in ('tests/run.sh', 'tests/lib/test_cli.py', 'tests/lib/suite_run.py',
                     'tests/lib/testlib.sh', 'tests/lib/case.sh', 'tests/lib/artifact.py'):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    (destination / 'tests/catalog.json').write_text(json.dumps({'schema_version': 1, 'suites': suites}) + '\n')
    if signed_fixtures:
        tool = destination / 'fixture-codesign'
        tool.write_text('#!/usr/bin/python3\n' + (source / 'tests/fixtures/dispatcher/artifacts.py').read_text())
        tool.chmod(0o755)
        inspector = destination / 'tests/lib/artifact.py'
        text = inspector.read_text()
        old = "CODESIGN = '/usr/bin/codesign'"
        if text.count(old) != 1:
            raise ValueError('cannot install isolated codesign equipment')
        inspector.write_text(text.replace(old, f'CODESIGN = {str(tool)!r}'))
