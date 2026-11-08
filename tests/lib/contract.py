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
WORKER_IDENTITY = "564477bc0b94cbaf0d99ae4f3cd82f2cd2ec20298c60218e4542c551b68298ee"
# END GENERATED WORKER IDENTITY
