#!/usr/bin/env python3
"""Exercise envelope comparison through its CLI using retained and mutated JSON.

All fixture slots contain copies of one validated live envelope; no app runs or
gitignored migration output are needed. Each control retains both inputs, the
comparison report, stdout and stderr, including the expected refusal path.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from blackbox import recapture_host_reply
BASE = ROOT / 'tests/fixtures/blackbox_e2e/checker/response24/valid_run.json'
COMPARER = ROOT / 'tests/lib/envelope_compare.py'


def set_field(document, path, value):
    parts = path.split('.')
    for key in parts[:-1]:
        document = document[key]
    document[parts[-1]] = value


def remove_field(document, path):
    parts = path.split('.')
    for key in parts[:-1]:
        document = document[key]
    del document[parts[-1]]


def main():
    out = Path(sys.argv[1])
    original = json.loads(BASE.read_text())
    names = sorted(p.name for p in (ROOT / 'tests/fixtures/pw_runner').glob('*.json'))
    assert names
    results = []

    def run(name, mutate=lambda d: None, *, baseline=original, rejected=None, options=()):
        directory = out / name
        candidate = copy.deepcopy(baseline)
        mutate(candidate)
        # These are authored comparison inputs. Encode the changed host
        # record explicitly; capture-failure controls live in checker_controls.
        recapture_host_reply(candidate)
        for side, document in [('candidate', candidate), ('baseline', baseline)]:
            target = directory / side
            target.mkdir(parents=True)
            for filename in names:
                (target / filename).write_text(json.dumps(document, indent=2) + '\n')
        report_path = directory / 'comparison.json'
        process = subprocess.run(
            [sys.executable, '-B', '-S', str(COMPARER), 'compare', str(directory / 'candidate'),
             str(directory / 'baseline'), '--out', str(report_path), *options],
            text=True, capture_output=True, timeout=30)
        (directory / 'stdout.txt').write_text(process.stdout)
        (directory / 'stderr.txt').write_text(process.stderr)
        report = json.loads(report_path.read_text())
        expected = 1 if rejected else 0
        assert process.returncode == expected and report['ok'] == (not rejected), (name, report)
        for fixture in report['fixtures'].values():
            # These controls must reach comparison, not merely trip schema validation.
            assert not any(fixture['validation'].values()), (name, fixture['validation'])
            if rejected:
                paths = [item['path'] for item in fixture['unexplained']]
                assert rejected in paths, (name, rejected, paths)
        results.append(dict(name=name, returncode=process.returncode, rejected_path=rejected))
        (out / 'controls.json').write_text(json.dumps(results, indent=2) + '\n')

    argv_path = 'data.runner_client.argv'
    def argv(document):
        return document['data']['runner_client']['argv']

    run('identical')
    def relocate(document):
        argv(document)[0] = '/private/tmp/candidate.app/Contents/MacOS/pw-runner-client'
        set_field(document, 'data.specimen.app_provenance.evidence_manifest_path',
                  '/private/tmp/candidate.app/Contents/Resources/Evidence/manifest.json')
    run('relocated_client', relocate)

    def rename_service(document):
        argv(document)[-1] = 'test.candidate.PWRunner'
        set_field(document, 'data.specimen.runner_provenance.runner_service_name', argv(document)[-1])
    run('renamed_service', rename_service)
    for flags in (['--mach-service'], ['--mach-service', '--privileged']):
        base = copy.deepcopy(original)
        argv(base)[6:6] = flags
        run('renamed_service_' + str(len(flags)), rename_service, baseline=base)

    run('absolute_deadline_varies', lambda d: argv(d).__setitem__(5, str(int(argv(d)[5]) + 1)))
    for label, index, value in [('command', 1, 'validate'), ('timeout_flag', 2, '--another-flag'),
                                ('timeout', 3, '1'), ('deadline_flag', 4, '--another-deadline'),
                                ('deadline_text', 5, 'not-a-tick'), ('deadline_negative', 5, '-1'),
                                ('deadline_overflow', 5, str(2**64)), ('request_flag', 6, '--different'),
                                ('request', 7, '/different.json'), ('service', 8, 'wrong.service'),
                                ('executable', 0, '/wrong/Contents/MacOS/pw-runner-client')]:
        run('changed_' + label, lambda d, i=index, v=value: argv(d).__setitem__(i, v),
            rejected=f'{argv_path}[{index}]')
    run('extra_argument', lambda d: argv(d).append('--unexpected'), rejected=argv_path)
    run('removed_argument', lambda d: argv(d).pop(), rejected=argv_path)
    run('replaced_command', lambda d: set_field(d, argv_path, ['entirely-different-command']),
        rejected=argv_path)
    run('reordered_arguments', lambda d: argv(d).__setitem__(slice(2, 4), list(reversed(argv(d)[2:4]))),
        rejected=argv_path + '[2]')

    issues = 'data.runner_result.runner_subprocess.disposition.issues'
    assert original['data']['runner_result']['runner_subprocess']['disposition']['issues'] == []
    run('removed_empty_array', lambda d: remove_field(d, issues), rejected=issues)
    timestamp = 'data.runner_client.started_at_unix_ms'
    run('changed_timestamp', lambda d: set_field(d, timestamp, 123456))
    run('removed_timestamp', lambda d: remove_field(d, timestamp), rejected=timestamp)
    run('null_timestamp', lambda d: set_field(d, timestamp, None), rejected=timestamp)
    run('changed_stamp', lambda d: set_field(d, 'build.commit', 'different'),
        options=('--across-builds',))
    run('removed_stamp', lambda d: remove_field(d, 'build.commit'), rejected='build.commit',
        options=('--across-builds',))

    # Refused helper JSON remains opaque to the consumer, but is still evidence
    # to compare. These paths also model future schema-admitted additions.
    opaque = copy.deepcopy(original)
    opaque['data']['policy_check'] = {'status': 'invalid_reply', 'envelope': {'retained': {}}}
    payload = 'data.policy_check.envelope'
    run('removed_empty_object', lambda d: remove_field(d, payload + '.retained'),
        baseline=opaque, rejected=payload + '.retained')
    run('empty_container_type', lambda d: set_field(d, payload + '.retained', []),
        baseline=opaque, rejected=payload + '.retained')
    run('added_field', lambda d: set_field(d, payload + '.new_field', 1),
        baseline=opaque, rejected=payload + '.new_field')
    opaque['data']['policy_check']['envelope']['retained'] = []
    run('added_empty_list_member', lambda d: set_field(d, payload + '.retained', [{}]),
        baseline=opaque, rejected=payload + '.retained')
    opaque['data']['policy_check']['envelope']['retained'] = 1
    run('boolean_is_not_number', lambda d: set_field(d, payload + '.retained', True),
        baseline=opaque, rejected=payload + '.retained')

    identity = 'data.runner_result.runner_subprocess.worker_evidence.abi_identity'
    run('expected_identity', lambda d: set_field(d, identity, 'a' * 64),
        options=('--expect-identity', 'a' * 64))
    run('removed_identity', lambda d: remove_field(d, identity), rejected=identity)
    print(f'{len(results)} envelope comparison controls passed')


if __name__ == '__main__':
    main()
