"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 6
RESPONSE_SCHEMA = 27
CONTROLLER_ENVELOPE = 12
RUNNER_PROTOCOL = 3
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "6e8e46469c1ebf0677b799ad63adac5af20be68b20902e18450c5b6e70a8a9ba"
# END GENERATED WORKER IDENTITY
