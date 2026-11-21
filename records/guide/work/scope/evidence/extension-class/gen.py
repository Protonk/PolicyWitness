import json,sys
C="development:089e36a6b9f5327f9579b1ab165a5fe51e27e875d8ff32e74bbdf7f419c00d55"
W="/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/fbb806f1-8233-421a-8a54-c6b57c9469f0/scratchpad/scope/S3/w/"
def pol(cls=("read",), extra=""):
    preds=" ".join('(extension "com.apple.app-sandbox.%s")'%c for c in cls)
    s="(version 1) (allow default) (deny file-read-data) (deny file-write*)"
    if cls: s+=" (allow file-read-data %s)"%preds
    return s+extra
def rd(sid,t):
    return {"step_id":sid,"sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":t}},
            "attempt":{"kind":"file","action":"read_fresh","target":t}}
def ph(pid,a,acts): return {"phase_id":pid,"actor_id":a,"actions":acts}
def ext(sid,**k): return {"step_id":sid,"extension":k}
def spec(name,target,authority="read",policy=None,cons="Bob",release=True,after_release=True,issuer_unapplied=True):
    policy=policy or pol()
    acts=[{"actor_id":"issuer","equipment":"unentitled","sandbox":{"mode":"unapplied"}}]
    for n in ("Alice","Bob"):
        acts.append({"actor_id":n,"sandbox":{"mode":"apply","policy":{"format":"sbpl","sbpl_source":policy}}})
    p=[ph("a0","Alice",[rd("a_before",target)]),ph("b0","Bob",[rd("b_before",target)]),
       ph("sup","issuer",[ext("issue",operation="issue",family="file",authority=authority,target=target,token_ref="t"),
                          ext("xfer",operation="transfer",token_ref="t",recipient=cons,delivery_ref="d")]),
       ph("cons",cons,[ext("consume",operation="consume",delivery_ref="d",handle_ref="h")]),
       ph("a1","Alice",[rd("a_after",target)]),ph("b1","Bob",[rd("b_after",target)])]
    if release:
        p.append(ph("rel",cons,[ext("release",operation="release",handle_ref="h")]))
        if after_release:
            p.append(ph("a2","Alice",[rd("a_postrel",target)])); p.append(ph("b2","Bob",[rd("b_postrel",target)]))
    return {"contract":C,"specimen_id":name,"actors":acts,"phases":p}
T=W+"doc.txt"
S={}
S["base"]=spec("base",T)
S["rw_token_read_policy"]=spec("rw_token_read_policy",T,authority="read_write")
S["read_token_rw_policy"]=spec("read_token_rw_policy",T,policy=pol(("read-write",)))
S["no_predicate"]=spec("no_predicate",T,policy=pol(()))
S["other_target"]=None
x=spec("other_target",T); 
for a in x["phases"]:
    for ac in a["actions"]:
        if ac["step_id"]=="issue": ac["extension"]["target"]=W+"other.txt"
S["other_target"]=x
S["consume_by_issuer_self"]=None
for k,v in S.items():
    json.dump(v,open(k+".json","w"),indent=1)

def save(k,v): json.dump(v,open(k+".json","w"),indent=1)
# consumed by Alice
save("consume_alice",spec("consume_alice",T,cons="Alice"))
# directory token, read of file inside
D=W+"dir"; I=W+"dir/inner.txt"
x=spec("dir_token",I)
for p in x["phases"]:
    for ac in p["actions"]:
        if ac["step_id"]=="issue": ac["extension"]["target"]=D
save("dir_token",x)
# DAC: token for file mode 000
save("dac",spec("dac",W+"noperm.txt"))
# applied issuer under same restrictive policy
x=spec("applied_issuer",T)
x["actors"][0]={"actor_id":"issuer","equipment":"unentitled","sandbox":{"mode":"apply","policy":{"format":"sbpl","sbpl_source":pol(())}}}
save("applied_issuer",x)
# replace-on-save by recipient: allow write, unlink+create after consume then read
wpol=pol(("read",)," (allow file-write* (literal \"%s\"))"%T)
x=spec("replace",T,policy=wpol,after_release=False)
cons=[p for p in x["phases"] if p["phase_id"]=="b1"][0]
cons["actions"]=[rd("b_after",T),
  {"step_id":"unl","attempt":{"kind":"file","action":"unlink","target":T}},
  {"step_id":"cre","attempt":{"kind":"file","action":"create_fresh","target":T}},
  rd("b_replaced",T)]
save("replace",x)
x=spec("issuer_denied",T)
x["actors"][0]={"actor_id":"issuer","equipment":"unentitled","sandbox":{"mode":"apply","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default) (deny file-issue-extension)"}}}
save("issuer_denied",x)
