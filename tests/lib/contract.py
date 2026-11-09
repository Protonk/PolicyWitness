"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 6
RESPONSE_SCHEMA = 30
CONTROLLER_ENVELOPE = 14
RUNNER_PROTOCOL = 4
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "3b174d7b067b50015615c21c21819b1a500e1a83f0d938e987d338cee9db2173"
# END GENERATED WORKER IDENTITY
