"""Render the developer lesson's specimens; expectations live in the corpus."""
import argparse
import copy
import json
from pathlib import Path
import secrets

CORPUS = Path(__file__).resolve().parents[1] / 'fixtures/request_contract/examples.json'


def examples():
    return json.loads(CORPUS.read_text())


def materialize(example, effect, nonce):
    def substitute(value):
        if isinstance(value, dict):
            return {key: substitute(item) for key, item in value.items()}
        if isinstance(value, list):
            return [substitute(item) for item in value]
        if value == '$EFFECT':
            return str(effect)
        if value == '$NONCE':
            return nonce
        return value
    specimen = substitute(example['request'])
    if 'repeat_steps' in example:
        step = specimen['probe_plan'][0]
        specimen['probe_plan'] = [dict(copy.deepcopy(step), step_id=f's{i}')
                                 for i in range(example['repeat_steps'])]
    return specimen


if __name__ == '__main__':
    cases = {case['id']: case for case in examples()}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('example', choices=cases)
    parser.add_argument('--effect', required=True, help='absolute path to an absent file in an existing directory')
    args = parser.parse_args()
    case = cases[args.example]
    print(case['raw_request'] if 'raw_request' in case else
          json.dumps(materialize(case, args.effect, secrets.token_hex(16)), indent=2))
