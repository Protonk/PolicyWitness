"""Fixture setup only: copy the public runner and supply an independent catalog."""
import json
from pathlib import Path
import shutil


def install_runner(source, destination, suites, *, signed_fixtures=False):
    for relative in ('tests/run.sh', 'tests/lib/test_cli.py', 'tests/lib/suite_run.py',
                     'tests/lib/testlib.sh', 'tests/lib/case.sh', 'tests/lib/artifact.py',
                     'tests/lib/retention.py', 'tests/RETAINED.json'):
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


def completed_output(path):
    """Independent minimal terminal fixture for replacement controls."""
    path.mkdir(parents=True, exist_ok=True)
    owner = dict(schema_version=1, run_id='prior', out_dir=str(path), started_at_unix_ms=1)
    (path / 'owner.json').write_text(json.dumps(owner))
    run = dict(schema_version=1, terminal=True, run_id='prior', started_at_unix_ms=1,
               finished_at_unix_ms=2, duration_ms=1, ok=True, configuration={'out_dir': str(path)},
               completion=dict(selected=1, completed=1, skipped=0, unrun=0), stale=True)
    run.update(plan={'cases': [{'id': 'prior/case'}], 'configuration': run['configuration']},
               case_results=[{'id': 'prior/case', 'state': 'completed'}])
    (path / 'run.json').write_text(json.dumps(run))
