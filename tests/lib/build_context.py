"""Candidate assertions and explicit contexts for constructed test records."""
from copy import deepcopy
import os
from pathlib import Path
import plistlib

ROOT = Path(__file__).resolve().parents[2]
TEST_CONTRACT = 'test:fixture'


def candidate_contract(app=None):
    app = Path(app or os.environ.get('PW_APP_DIR', ROOT / 'dist/PolicyWitness.app'))
    value = plistlib.loads((app / 'Contents/Info.plist').read_bytes()).get('PWContract')
    if not isinstance(value, str) or not value or value == 'unbound':
        raise ValueError(f'{app}: no bound PWContract in the candidate plist')
    return value


def asserted_request(template, app=None):
    """Copy an identity-free request template and assert the inspected candidate."""
    result = deepcopy(template)
    if 'schema_version' in result or 'contract' in result:
        raise ValueError('request template carries a contract marker')
    result['contract'] = candidate_contract(app)
    return result


def producer(identity=TEST_CONTRACT):
    return dict(contract=identity, describe='constructed', commit='constructed')


def write_swift_context(path, identity=TEST_CONTRACT):
    """Explicit context for an instrumented or constructed native test product."""
    import json
    Path(path).write_text('enum PWBuildContext {\n    static let contract = ' + json.dumps(identity) +
                         '\n    static let describe = "test fixture"\n    static let commit = "test fixture"\n}\n')
    return Path(path)
