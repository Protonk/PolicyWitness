"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 4
RESPONSE_SCHEMA = 21
CONTROLLER_ENVELOPE = 7
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "b53c16f9dfb0e9b33d91fad40d6995ed58e7a612ff9b606d153814d1e04ecd87"
# END GENERATED WORKER IDENTITY
