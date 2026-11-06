#!/usr/bin/env python3
"""Record terminal BR4 evidence and close the already-reviewed case union."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NAME = 'extension-consolidation-build-refusals-04'
RUN = ROOT / 'tests/out/runs' / NAME


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    assert not path.exists(), f'receipt already exists: {path}'
    path.write_text(json.dumps(value, indent=2) + '\n')


def accepted(run, count):
    assert run['ok'] and run['terminal']
    assert run['completion'] == dict(completed=count, selected=count, skipped=0, unrun=0)
    assert run['case_outcome_counts'] == {'pass': count}
    assert not run['harness_errors']
    assert all(c['status'] == 'pass' and c['system_sleep_ms'] == 0 for c in run['case_results'])
    assert run['artifact_integrity']['valid_before'] and run['artifact_integrity']['unchanged']


def main():
    outer = read(RUN / 'run.json')
    accepted(outer, 1)
    assert outer['case_results'][0]['id'] == 'preflight/build_refusal_controls'
    artifacts = RUN / 'suites/preflight/build_refusal_controls/artifacts'
    nested_path = artifacts / 'release-battery/acceptance/tests/run.json'
    nested = read(nested_path)
    accepted(nested, 216)
    controls = read(artifacts / 'controls.json')
    mutations = read(artifacts / 'mutations.json')
    assert len(controls) == 88 and controls[-1]['refusal'] == 'release_battery'
    assert len(mutations) == 16
    assert all(m['self_checks']['control'] is not None and m['guard']['control'] is not None
               and not m['guard']['self_check_refused'] for m in mutations)
    manifest = read(HERE / 'evidence/candidate-11-final-source.json')
    changed = []
    for entry in manifest['files']:
        path = ROOT / entry['path']
        matches = (path.is_symlink() and str(path.readlink()) == entry['symlink']) if 'symlink' in entry else (
            path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'])
        if not matches:
            changed.append(entry['path'])
    assert not changed, changed
    write(HERE / 'build-refusals-04-source-integrity.json', dict(
        run_id=outer['run_id'], source_manifest='evidence/candidate-11-final-source.json',
        all_entries_match_after_run=True, entries=len(manifest['files']), changed=changed,
        scope='Hash/link equality for the recorded source scope before retention edits; excludes records/reports and build outputs. Dependency reachability is separately reviewed.'))
    write(HERE / 'build-refusals-04-result.json', dict(
        run=NAME, run_id=outer['run_id'], completion=outer['completion'],
        case_outcome_counts=outer['case_outcome_counts'], artifact_integrity=outer['artifact_integrity'],
        system_sleep_ms=sum(c['system_sleep_ms'] for c in outer['case_results']),
        controls=len(controls), mutations=len(mutations),
        nested=dict(run_id=nested['run_id'], completion=nested['completion'],
                    case_outcome_counts=nested['case_outcome_counts'], artifact_integrity=nested['artifact_integrity'],
                    system_sleep_ms=sum(c['system_sleep_ms'] for c in nested['case_results']),
                    original_run_record=str(nested_path.relative_to(ROOT))),
        scope='Whole dispatcher case passed, including restored original controls after both mutation stages. Only Apple notarization responses are controlled in the real isolated release battery; no publication or actual notarization is claimed. Raw evidence remains at its original owned main-checkout path; pinning is recorded separately in retention-change.json.'))
    coverage_path = HERE / 'verification-coverage.json'
    coverage = read(coverage_path)
    assert coverage['missing'] == ['preflight/build_refusal_controls']
    coverage['sources'].append(dict(run=NAME, run_id=outer['run_id'], ok=outer['ok'],
                                   case_outcome_counts=outer['case_outcome_counts'],
                                   artifact_integrity=outer['artifact_integrity']))
    row, = [c for c in coverage['cases'] if c['id'] == 'preflight/build_refusal_controls']
    row['credit'] = dict(run=NAME, run_id=outer['run_id'], case_status='pass', system_sleep_ms=0, run_ok=True)
    coverage['missing'] = [c['id'] for c in coverage['cases'] if not c['credit']]
    coverage['credited_case_count'] = len(coverage['cases']) - len(coverage['missing'])
    assert coverage['credited_case_count'] == coverage['distinct_union_count'] == 235 and not coverage['missing']
    coverage['status'] = 'complete'
    coverage_path.write_text(json.dumps(coverage, indent=2) + '\n')
    print(json.dumps(dict(run_id=outer['run_id'], nested_run_id=nested['run_id'],
                         controls=len(controls), mutations=len(mutations), credited_case_count=235)))


if __name__ == '__main__':
    main()
