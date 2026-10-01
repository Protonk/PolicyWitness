#!/usr/bin/env python3
"""Steered validator for matrix specimen B (tests/fixtures/comparison/matrix.json).

Reads the host's NDJSON probes and answers each one by step ID with a fixed
record: deny for b1, allow for b6 and b7, a diagnostic error record for b4,
and nothing for b2, b3 and b5. After the last probe it flushes stdout and holds
it open until the host's validator I/O deadline expires, so the run ends in
validator_no_reply while every emitted record is retained and associated.

This is input-steering through _test_overrides.validator_executable_path, not
result-faking: the real worker performs the attempts and the real host joins
the channels. Its output is stub output, not a native sandbox_check result.
Expectations for specimen B come from the submitted scopes and the independent
file controls, never from this transcript.

The transcript is in the host's validator record vocabulary: allow/deny records
carry rc/errno and the probe's operation and filter metadata; the diagnostic
record carries outcome "error" and a string error and omits native results.
"""
import json
import sys
import time

DENY = {"b1"}
ALLOW = {"b6", "b7"}
ERROR = {"b4"}
OMIT = {"b2", "b3", "b5"}

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        probe = json.loads(line)
    except ValueError:
        continue
    step_id = probe.get("step_id")
    base = {"kind": "sb_api_validator_verdict", "schema_version": 1, "step_id": step_id,
            "operation": probe.get("operation"), "filter_type": probe.get("filter_type"),
            "filter_value": probe.get("filter_value")}
    if step_id in DENY or step_id in ALLOW:
        outcome = "deny" if step_id in DENY else "allow"
        record = dict(base, filter_type_id=1, rc=0 if outcome == "allow" else 1, errno=0, outcome=outcome)
    elif step_id in ERROR:
        record = dict(base, outcome="error", error="stub diagnostic: no native query was made for this step")
    else:
        continue
    sys.stdout.write(json.dumps(record) + "\n")
    sys.stdout.flush()
# Hold stdout open past validator_io_timeout_ms; the host kills the stub.
time.sleep(60)
