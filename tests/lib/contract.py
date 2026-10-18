"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 5
RESPONSE_SCHEMA = 23
CONTROLLER_ENVELOPE = 7
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "4cb19db043606894ace2e978434f8805edf4c79245f3588cc68a33b36deca9e8"
# END GENERATED WORKER IDENTITY
