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
WORKER_IDENTITY = "b5f3b8c929c2efdf801f8e4cbb45d5fe5123de47c1761809eb0acb4bc685f6e6"
# END GENERATED WORKER IDENTITY
