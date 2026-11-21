import json, sys
# gen.py OUT SPECIMEN_ID SBPL_FILE OP ACTION PATH...
out, sid, sbfile, op, action = sys.argv[1:6]
paths = sys.argv[6:]
contract = "development:089e36a6b9f5327f9579b1ab165a5fe51e27e875d8ff32e74bbdf7f419c00d55"
src = open(sbfile).read()
steps = []
for i, p in enumerate(paths):
    steps.append({"step_id": f"s{i}",
                  "sandbox_check": {"operation": op, "filter": {"kind": "path", "value": p}},
                  "attempt": {"kind": "file", "action": action, "target": p}})
json.dump({"contract": contract, "specimen_id": sid,
           "policy": {"format": "sbpl", "sbpl_source": src},
           "probe_plan": steps}, open(out, "w"), indent=1)
