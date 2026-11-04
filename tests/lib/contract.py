"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 5
RESPONSE_SCHEMA = 25
CONTROLLER_ENVELOPE = 10
RUNNER_PROTOCOL = 2
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "076dd5b9d7734de33e1a6859ccb34de33e61ea058f075a688eaf34411a3c6c84"
# END GENERATED WORKER IDENTITY
