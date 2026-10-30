"""Wire contract versions for tests. Edit docs/contract.json and regenerate.

Semantic response and envelope readers accept exactly these versions. Request
admission and the worker ABI have separate contracts.
"""
# BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
REQUEST_SCHEMA = 5
RESPONSE_SCHEMA = 24
CONTROLLER_ENVELOPE = 9
RUNNER_PROTOCOL = 2
# END GENERATED CONTRACT VERSIONS

# BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
WORKER_IDENTITY = "86df53a3a899259bc529c8f819a54da08c33b90b679166770c43f6f5afed7d18"
# END GENERATED WORKER IDENTITY
