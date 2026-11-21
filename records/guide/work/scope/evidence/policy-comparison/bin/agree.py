import json, sys
# agree.py WRAP_TXT PW_RESULT : compare per-path query verdict and attempt errno
wrap, res = sys.argv[1:3]
q = []; a = []
for line in open(wrap):
    if line.startswith("#"): continue
    f = line.rstrip("\n").split("\t")
    if f[0] == "open_read": a.append(int(f[3].split("=")[1].split("(")[0]))
    else: q.append(f[4])
d = json.load(open(res))
steps = d["data"]["runner_result"]["steps"]
rows = 0; diffs = []
for i, st in enumerate(steps):
    pq = st["sandbox_check"]["outcome"]; pe = st["attempt"].get("errno") or 0
    rows += 1
    if pq != q[i] or pe != a[i]:
        diffs.append((st["step_id"], "wrap", q[i], a[i], "pw", pq, pe))
print(res.split("/")[-1], "rows", rows, "differences", diffs)
