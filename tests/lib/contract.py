"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 5
RESPONSE_SCHEMA = 25
CONTROLLER_ENVELOPE = 10
RUNNER_PROTOCOL = 3
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "c1f66cc04bf60846bcddcee5d765e965d75c1e6a8d682d116f14439dc9b93bf7"
# END GENERATED WORKER IDENTITY
