"""Replay Swift reporting receipts through the independent binary reader.

These are constructed reporting/codec controls, not observations of native
execution or of a pipe interrupted by the kernel. Prefix controls establish
that an incomplete emitted frame cannot be read as a complete reply.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import porcelain


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def replay(artifacts):
    receipts = artifacts / 'porcelain-replies'
    decoded = {}
    results = []
    for name in ('normal', 'rich-failure', 'minimal-failure'):
        wire_path = receipts / (name + '.pwp')
        comparison_path = receipts / (name + '.comparison.json')
        wire = wire_path.read_bytes()
        expected = json.loads(comparison_path.read_text())
        actual = porcelain.decode(wire, 'reply')
        (receipts / (name + '.decoded.json')).write_text(
            json.dumps(actual, ensure_ascii=False, indent=2) + '\n')
        require(actual == expected, name + ': binary projection differs from JSON comparison receipt')
        decoded[name] = actual
        results.append(dict(name=name, bytes=len(wire),
                            sha256=hashlib.sha256(wire).hexdigest(),
                            comparison_sha256=hashlib.sha256(comparison_path.read_bytes()).hexdigest()))

        # Keep the complete positive receipt and exact interrupted prefixes.
        # Cuts include framing, fingerprint, root header/identity and the last
        # byte, independently of the generated record/field tables.
        cuts = sorted({0, 1, 4, 35, 36, 40, 41, 42, len(wire) // 2, len(wire) - 1})
        partials = receipts / 'interrupted'
        partials.mkdir(exist_ok=True)
        refusals = []
        for cut in cuts:
            require(0 <= cut < len(wire), name + ': missing complete positive receipt')
            prefix = wire[:cut]
            (partials / (name + '.' + str(cut) + '.partial')).write_bytes(prefix)
            try:
                porcelain.decode(prefix, 'reply')
            except ValueError as error:
                refusals.append(dict(retained_bytes=cut, error=str(error),
                                     sha256=hashlib.sha256(prefix).hexdigest()))
            else:
                raise AssertionError(name + ': interrupted prefix was accepted at ' + str(cut))
        results[-1]['interrupted_prefixes'] = refusals

    normal = decoded['normal']
    rich = decoded['rich-failure']
    minimal = decoded['minimal-failure']
    require('reporting_failure' not in normal, 'normal fixture unexpectedly degraded')
    require(len(normal['steps']) == 1 and normal['steps'][0]['comparison']['order'] == 'query_first',
            'normal positive comparison missing')
    require(normal['runner_subprocess']['reaped'] is False
            and normal['runner_subprocess'].get('exit_code') is None,
            'normal fixture no longer supplies the unconfirmed-reap control')
    require(normal['runner_subprocess']['disposition']['questions']['final_status']['state'] == 'unresolved',
            'unconfirmed reap acquired a final status')

    for name, reply, retained in [('rich-failure', rich, True), ('minimal-failure', minimal, False)]:
        failure = reply['reporting_failure']
        require(reply['normalized_outcome'] == 'runner_reporting_failed' and reply['rc'] == 1,
                name + ': reporting failure changed execution summary into success')
        require(isinstance(reply.get('error'), str) and reply['error'], name + ': absent failure diagnostic')
        require(failure['origin'] == 'runner_host' and failure['evidence_retained'] is retained,
                name + ': incorrect evidence retention claim')
        require(isinstance(failure.get('diagnostic'), str) and failure['diagnostic'],
                name + ': absent reporting diagnostic')
        for field in ('rc', 'normalized_outcome', 'error'):
            require(failure.get('original_' + field) == normal.get(field),
                    name + ': original summary changed at ' + field)
        require(all(step.get('comparison') is None for step in reply['steps']),
                name + ': unsupported comparison survived')

    expected_rich = copy.deepcopy(normal)
    expected_rich['steps'][0]['phase_id'] = 'missing'
    for step in expected_rich['steps']:
        step.pop('comparison')
    for field in ('rc', 'normalized_outcome', 'error', 'reporting_failure'):
        expected_rich[field] = rich[field]
    require(rich == expected_rich,
            'rich rejection changed facts beyond the injected association and withdrawn comparisons')

    identity = ('schema_version', 'specimen_id', 'run_kind', 'pid', 'bundle_id', 'policy_format', 'policy_sha256')
    for field in identity:
        require(minimal.get(field) == normal.get(field), 'minimal identity changed at ' + field)
    require(minimal['steps'] == [] and minimal['phases'] == [], 'minimal reply retained unreported observations')
    require(set(minimal) <= set(identity) | {'rc', 'normalized_outcome', 'error', 'steps', 'phases', 'reporting_failure'},
            'minimal reply retained rich evidence despite evidence_retained=false')
    require('evidence-preserving encoding also failed' in minimal['error'],
            'minimal reply omits the rich writer failure')

    report = dict(status='passed', scope='constructed Swift reporting receipts and interrupted-frame decoding',
                  limitations=['No native ending or XPC-copy observation.',
                               'Prefix rejection is not an actual interrupted-pipe emission trial.'],
                  receipts=results)
    (receipts / 'replay.json').write_text(json.dumps(report, indent=2) + '\n')
    print('normal, rich and minimal binary receipts match independent JSON projection; '
          'facts, failure retention and 30 interrupted prefixes checked')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: porcelain_replies.py ARTIFACTS')
    replay(Path(sys.argv[1]))
