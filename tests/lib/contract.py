"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 4
RESPONSE_SCHEMA = 18
CONTROLLER_ENVELOPE = 7
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "5d5015722db1555ed399f3cac1890b11b41af7982986e717d77fbb9d96e87ff2"
# END GENERATED WORKER IDENTITY
