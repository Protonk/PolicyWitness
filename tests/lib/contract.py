"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 4
RESPONSE_SCHEMA = 15
CONTROLLER_ENVELOPE = 7
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "b92ab663b143748f81d4e4bf7994a33727eb19903d054dd0aa8097eed37cb802"
# END GENERATED WORKER IDENTITY
