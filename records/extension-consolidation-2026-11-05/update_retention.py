#!/usr/bin/env python3
"""Apply the reviewed two-pin replacement after every required case passes."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tests/lib'))
import retention


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert sys.argv[1:] == ['--apply'], 'explicit --apply required'
    coverage = json.loads((HERE / 'verification-coverage.json').read_text())
    assert not coverage['missing'] and coverage['credited_case_count'] == coverage['distinct_union_count'] == 235
    assert (HERE / 'retention-review.md').is_file()
    archived = json.loads((HERE / 'evidence/extension-consolidation-actors-03-complete.json').read_text())
    with (HERE / 'evidence' / archived['archive']).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == archived['sha256']
    expected = {
        'runs/actor-passes-default-02': '20261104T180136Z_5ef8b568',
        'runs/actor-passes-final-controls-02': '20261104T201833Z_59c91237',
    }
    replacements = (
        ('extension-consolidation-battery-01',
         'Final consolidation default battery: 216/216 canonical cases, 551 Swift checks, no skips/unrun/harness errors/sleep, and unchanged signed build11. Exact dirty-source archive and review are in the associated consolidation records.'),
        ('extension-consolidation-build-refusals-04',
         'Complementary whole build-refusal family on final consolidation sources, including its real isolated default-battery rehearsal and designated guard mutations. Other required targeted evidence is preserved in hashed associated records; this run retains its original owned location.'),
    )
    before_path = HERE / 'retention-before.json'
    assert not before_path.exists() and not (HERE / 'retention-change.json').exists()
    with retention.checkout_lock(ROOT, purpose='execution'):
        retention.load_index(ROOT)
        path = ROOT / 'tests/RETAINED.json'
        before = path.read_bytes()
        old = json.loads(before)
        actual = {e['path']: e['run_id'] for e in old['runs'] if not e.get('release')}
        assert actual == expected, 'retention changed since review; preserve and reassess'
        releases = [e for e in old['runs'] if e.get('release')]
        added = []
        for name, reason in replacements:
            run_path = ROOT / 'tests/out/runs' / name
            owner = retention.valid_owner(run_path)
            run = retention.read_object(run_path / 'run.json')
            assert run['run_id'] == owner['run_id'] and run['ok']
            assert run['completion']['skipped'] == run['completion']['unrun'] == 0
            assert not run['harness_errors']
            assert all(c['status'] == 'pass' and c['system_sleep_ms'] == 0 for c in run['case_results'])
            assert run['artifact_integrity']['valid_before'] and run['artifact_integrity']['unchanged']
            assert (run_path / 'artifact-integrity/before.json').is_file()
            added.append(dict(path='runs/' + name, run_id=run['run_id'], reason=reason,
                              source=None, app_inventory='artifact-integrity/before.json'))
        new = dict(schema_version=1, runs=releases + added)
        before_path.write_bytes(before)
        retention.write_index(ROOT, new)
        after = path.read_bytes()
        receipt = dict(before_sha256=sha(before), after_sha256=sha(after),
                       removed_nonrelease=expected, added_nonrelease=added,
                       release_entries_unchanged=releases,
                       writer='tests.lib.retention.write_index under its existing checkout_lock',
                       source_note='Null source means no committed candidate is claimed; exact dirty sources are archived.',
                       cleanup='This replaces pins only. Supported pruner preview/apply is a separate operation.')
        retention.atomic_json(HERE / 'retention-change.json', receipt)
    print(json.dumps(dict(nonrelease_pins=len(added), release_entries_preserved=len(releases))))


if __name__ == '__main__':
    main()
