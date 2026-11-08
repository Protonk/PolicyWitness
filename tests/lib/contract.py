"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 6
RESPONSE_SCHEMA = 28
CONTROLLER_ENVELOPE = 13
RUNNER_PROTOCOL = 4
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "cad425b12377d1f1fe0f37f9dcc6ee546024afaf372d2a2b570cd97ce538c983"
# END GENERATED WORKER IDENTITY
