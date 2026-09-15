"""Fixture setup only: copy the public runner and supply an independent catalog."""
import json
from pathlib import Path
import shutil


def install_runner(source, destination, suites):
    for relative in ('tests/run.sh', 'tests/lib/test_cli.py', 'tests/lib/suite_run.py',
                     'tests/lib/testlib.sh', 'tests/lib/case.sh'):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    (destination / 'tests/catalog.json').write_text(json.dumps({'schema_version': 1, 'suites': suites}) + '\n')
