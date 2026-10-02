"""Check the live verification replies against the matrix rows they cover.
Run from the repository root; defaults to the replies beside this script."""
import json, os, re, sys
REMOVED={"state_stability_unestablished","runtime_target_identity_unestablished",
         "sandbox_attribution_unestablished","attempt_mutation_order_unestablished",
         "query_attempt_order_unestablished"}
TMAP={"same":"same_submitted","different":"different_submitted","unresolved":"unresolved"}
rows={}
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_matrix.md")):
    c=[x.strip() for x in line.strip().strip("|").split("|")]
    if len(c)<11: continue
    rid=c[0]
    if not re.fullmatch(r"(S\d\d|B\d|C1|T)",rid): continue
    obs=c[3]; observation,basis=(obs.split("/",1)+[""])[:2] if "/" in obs else (obs,"")
    rows[rid]=dict(pred=c[2],obs=observation.strip(),basis=basis.strip(),op=c[4],
        tgt=TMAP.get(c[5],c[5]),order=c[6],A=c[7],I=c[8],M=c[9],
        lim=set(re.findall(r"`([^`]+)`",c[10])))
# rows written as "as S01" are that row under a different attempt action
for _r in rows.values():
    if _r["pred"].startswith("as "):
        _r.update({k:v for k,v in rows[_r["pred"][3:]].items() if k!="pred"})
        _r["pred"]=rows[_r["pred"][3:]]["pred"]
SP=sys.argv[1] if len(sys.argv)>1 else "tests/fixtures/comparison/baseline_response12"
MAP={"s06":"S06","s10":"S10","s12":"S12","s18":"S18","s21":"S21","s22":"S22",
     "b1":"B1","b3":"B3","b5":"B5","b6":"B6","b7":"B7"}
for f in ("run_a.json","run_b.json"):
    d=json.load(open(SP+"/"+f))
    rr=d["data"].get("runner_result") or {}
    print("\n### %s  (run outcome: %s)"%(f,d["result"].get("normalized_outcome")))
    for s in rr.get("steps",[]):
        sid=s.get("step_id"); rid=MAP.get(sid)
        c=s.get("comparison") or {}
        got=dict(pred=c.get("prediction"),obs=c.get("observation"),basis=c.get("observation_basis"),
                 op=c.get("operation_relation"),tgt=c.get("target_relation"),order=c.get("order"),
                 lim=set(c.get("limitations") or [])-REMOVED)
        if not rid:
            print("  %-4s (no matrix row)  %s"%(sid,got)); continue
        want=rows[rid]
        diffs=[]
        for k in ("pred","obs","basis","op","tgt","order"):
            if want[k]!=got[k]: diffs.append("%s: plan=%r live=%r"%(k,want[k],got[k]))
        if want["lim"]!=got["lim"]:
            miss=sorted(want["lim"]-got["lim"]); extra=sorted(got["lim"]-want["lim"])
            if miss: diffs.append("lim missing live: %s"%miss)
            if extra: diffs.append("lim extra live: %s"%extra)
        status="MATCH" if not diffs else "DIFF"
        print("  %-4s %-4s %s"%(rid,sid,status))
        for x in diffs: print("        "+x)
        if diffs:
            print("        live full: %s/%s/%s %s %s %s lim=%s"%(got["pred"],got["obs"],got["basis"],
                  got["op"],got["tgt"],got["order"],sorted(got["lim"])))
