"""Match every matrix row in plan_matrix.md (the plan's matrix as verified) against the comparison
tuples in retained run output. Run from the repository root."""
import json, os, re, collections

REMOVED={"state_stability_unestablished","runtime_target_identity_unestablished",
         "sandbox_attribution_unestablished","attempt_mutation_order_unestablished",
         "query_attempt_order_unestablished"}

# ---- parse the matrix from the plan ----
rows={}
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_matrix.md")):
    if not line.startswith("| S") and not line.startswith("| B") and not line.startswith("| C1") and not line.startswith("| T "):
        continue
    c=[x.strip() for x in line.strip().strip("|").split("|")]
    if len(c)<11: continue
    rid=c[0]
    if not re.fullmatch(r"(S\d\d|B\d|C1|T)",rid): continue
    obs=c[3]
    if "/" in obs:
        observation,basis=[x.strip() for x in obs.split("/",1)]
    else:
        observation,basis=obs,""
    lims=set()
    for m in re.finditer(r"`([^`]+)`",c[10]): lims.add(m.group(1))
    rows[rid]=dict(scenario=c[1],prediction=c[2],observation=observation,observation_basis=basis,
                   operation_relation=c[4],target_relation=c[5],order=c[6],
                   A=c[7],I=c[8],M=c[9],limitations=lims,raw=line.rstrip())

# "as S01" rows
for rid,r in rows.items():
    if r["prediction"].startswith("as "):
        r["alias"]=r["prediction"][3:]

# ---- collect live tuples ----
live=collections.defaultdict(list)
for ROOT in ("tests/out/runs/release-0.2.4-default","tests/out/runs/default","tests/out/runs/best-effort-log-final-review-default"):
    for dp,dn,fn in os.walk(ROOT):
        for f in fn:
            if not f.endswith(".json"): continue
            p=os.path.join(dp,f)
            try:
                if os.path.getsize(p)>40_000_000: continue
                d=json.load(open(p))
            except Exception: continue
            stack=[d]
            while stack:
                o=stack.pop()
                if isinstance(o,dict):
                    st=o.get("steps")
                    if isinstance(st,list) and o.get("schema_version") and "specimen_id" in o:
                        for s in st:
                            if not isinstance(s,dict): continue
                            c=s.get("comparison")
                            if not isinstance(c,dict): continue
                            lim=frozenset(c.get("limitations") or [])-REMOVED
                            key=(c.get("prediction"),c.get("observation"),c.get("observation_basis"),
                                 c.get("operation_relation"),c.get("target_relation"),c.get("order"),lim)
                            loc=p.split("/suites/")[-1].split("/artifacts/")[0]
                            live[key].append((loc,s.get("step_id")))
                    for v in o.values(): stack.append(v)
                elif isinstance(o,list): stack.extend(o)

TMAP={"same":"same_submitted","different":"different_submitted","unresolved":"unresolved"}
def norm(r):
    return (r["prediction"],r["observation"],r["observation_basis"],r["operation_relation"],
            TMAP.get(r["target_relation"],r["target_relation"]),r["order"],frozenset(r["limitations"]))

print("live distinct tuples:",len(live))
print()
ok=[];bad=[];alias=[]
for rid in sorted(rows,key=lambda x:(x[0],x[1:].zfill(2))):
    r=rows[rid]
    if "alias" in r: alias.append((rid,r["alias"])); continue
    k=norm(r)
    if k in live:
        ok.append((rid,live[k][0]))
    else:
        # nearest live tuple: same first six, limitations differ
        near=[(kk,v) for kk,v in live.items() if kk[:6]==k[:6]]
        bad.append((rid,r,near))

print("EXACT LIVE MATCH (%d):"%len(ok))
for rid,ex in ok: print("  %-4s %s  (%s / step %s)"%(rid,rows[rid]["scenario"][:44],ex[0],ex[1]))
print("\nALIAS ROWS (%d): %s"%(len(alias),", ".join("%s->%s"%a for a in alias)))
print("\nNO EXACT LIVE MATCH (%d):"%len(bad))
for rid,r,near in bad:
    print("\n  %-4s %s"%(rid,r["scenario"]))
    print("       plan: %s/%s/%s %s %s %s  lim=%s"%(r["prediction"],r["observation"],r["observation_basis"],
          r["operation_relation"],r["target_relation"],r["order"],sorted(r["limitations"])))
    if not near: print("       no live tuple with those six fields")
    for kk,v in near[:3]:
        print("       live: same six, lim=%s   (%s / %s)"%(sorted(kk[6]),v[0][0],v[0][1]))
