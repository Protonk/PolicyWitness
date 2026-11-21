import json, sys
# summ.py RESULT [STRIP_PREFIX]
d = json.load(open(sys.argv[1]))
strip = sys.argv[2:] 
def s(x):
    if not isinstance(x, str): return x
    for p in strip: x = x.replace(p, p.split("/")[-1] if False else "T")
    return x
rr = d["data"].get("runner_result") or {}
print("#", d["result"]["normalized_outcome"], "exit", d["result"]["exit_code"], "worker pid", rr.get("pid"), "sandboxed_after_apply", rr.get("sandboxed_after_apply"))
for st in rr.get("steps", []):
    q = st["sandbox_check"]; a = st["attempt"]; c = st.get("comparison", {})
    print("\t".join(str(v) for v in [st["step_id"], q["operation"], s(q["filter_value"]), q["outcome"], "native_rc=%s" % q.get("native_rc"), a["requested_action"], a["outcome"], "errno=%s" % a.get("errno"), c.get("order"), ",".join(c.get("limitations", [])), "obs_path=%s" % s(a.get("observed_path"))]))
