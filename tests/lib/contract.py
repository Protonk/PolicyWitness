"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 6
RESPONSE_SCHEMA = 29
CONTROLLER_ENVELOPE = 13
RUNNER_PROTOCOL = 4
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "7e0b4bd6f4e81629dc3451371b89a743d77a7570584512aa00ca292f72ffdc8e"
# END GENERATED WORKER IDENTITY
