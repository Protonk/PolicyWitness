#!/usr/bin/env python3
"""Answers every probe except b3/b5, then stalls so the host's validator I/O
deadline expires with those two steps unanswered."""
import json, sys, time
OMIT = {"b3", "b5"}
DENY = {"b1"}
probes = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        probes.append(json.loads(line))
    except Exception:
        continue
    for p in probes[-1:]:
        sid = p.get("step_id")
        if sid in OMIT:
            continue
        outcome = "deny" if sid in DENY else "allow"
        print(json.dumps({
            "kind": "sb_api_validator_verdict", "schema_version": 1,
            "step_id": sid, "operation": p.get("operation"),
            "filter_type": p.get("filter_type"), "filter_type_id": 1,
            "filter_value": p.get("filter_value"),
            "rc": 0 if outcome == "allow" else 1, "errno": 0,
            "outcome": outcome,
        }))
        sys.stdout.flush()
time.sleep(30)
