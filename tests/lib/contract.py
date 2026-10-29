"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 5
RESPONSE_SCHEMA = 24
CONTROLLER_ENVELOPE = 8
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094"
# END GENERATED WORKER IDENTITY
