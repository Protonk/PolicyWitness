1. Does step 4's chosen meaning of `drift` and `comparison` fulfill the plan's intended guarantees, or has it made acceptance easier by narrowing away an important promise?

   Before studying the classifier or the handoff's conclusions, reconstruct the intended guarantees from `tests/FAILURE-PROPAGATION-PLAN.md`, its observer principles and the original consumer questions C1–C6. Give that reconstruction in 150–200 words, then assess the implementation against it. The central design choice is to compare recorded outcomes within matching submitted scope while leaving synchronized state, runtime identity and causal attribution unestablished. Decide whether that is a useful and justified conclusion from the evidence PW actually has. Examine whether a concrete combination of query, attempt and enrichment records could support a stronger public claim than its observations justify, conceal a useful supported distinction, or satisfy the revised contract while missing the original purpose. Ground any criticism in a specific scenario and source or retained artifacts, and materially connect it to a guarantee identified in your reconstruction. Distinguish a demonstrated defect from an architectural limitation or an untested hypothesis. An explicit limitation is not automatically an adequate disposition, but neither additional fields nor mandatory certainty are automatically a remedy. Explain what evidence supports your conclusion and what could falsify it.

2. Is step 4's compatibility migration complete, and does the retained verification actually establish acceptance of the committed implementation across its affected consumers?

   Independently derive the affected emitters, readers, shared helpers, fixtures and runner contexts from commit `669cfb1` and the full test catalog before comparing that scope with `tests/FAILURE-PROPAGATION-INVENTORY.md` and `tests/out/failure-propagation-4/`. Check response-version handling, supported legacy replies, changed expectations and both built-in and BYOXPC paths. Reconcile required canonical case IDs with actual results, including the claimed 108 cases on the final build and 22 retained offline controls; verify why retained results still apply, inspect internal batch failures/skips, and match tested source and signed-build provenance to the commit. Account separately for later edits. Inspect raw envelopes and control evidence rather than treating the handoff, review script or passing totals as proof. Distinguish fixture-supplied verdicts, constructed interpretation tests and independently observed effects, including the evidence supporting live log candidates. Use focused reruns or counterexamples where needed to resolve a specific doubt. Report substantiated gaps and their consequences, with precise source/artifact references and bounded corrections where warranted. Keep step 5's pending consumer-recovery enforcement separate: this audit checks step 4's delivered contract and evidence without treating readable summary labels as proof that their meanings are justified.

## Results

### 1. Does step 4's `drift`/`comparison` fulfil the intended guarantees?

#### Reconstruction of the intended guarantees (199 words)

The plan treats a PolicyWitness run as testimony and asks that every claim in the
envelope be traceable to the observer that made it. Four things need separate
justification: that a record is valid, that it answers the request it is
associated with, that it is comparable to another observation, and that it
supports a causal conclusion. A shared step ID or envelope establishes none of
them. A summarizing layer may rank observations but must not rewrite them,
invent a value nobody returned, or assign a cause nobody saw. "I cannot tell"
must be sayable, and several known limits must coexist without one erasing
another.

C1–C6 turn that into an obligation owed to a reader: from a single envelope,
using the public contract alone, a consumer should see which steps report
established agreement and what comparison that covers, which observed failures
PW cannot attribute, what relation between query and attempt was established or
left open, why a comparison is missing, which resolutions were later host
observations, and which denial events are only candidates.

Fulfilling this makes a drift report auditable rather than something a reader
must trust. Withholding a conclusion is legitimate; withholding one the evidence
supports is not.

#### Verdict

**The central design choice is right, and one consequence of its implementation
is a demonstrated defect: the entire `exec` probe family can no longer produce a
comparison conclusion, for a reason that is an artifact of the representation
rather than of the evidence.**

#### Why the narrowing itself is justified

Restricting `drift` to `observation == "succeeded"` is the correct reading of the
evidence, not an evasion. A completed *success* under a prediction is the only
attempt observation whose meaning is unambiguous: if the kernel had enforced a
deny the operation would have failed, and DAC can only add denials, never grant
them. So `drift=true` (deny predicted, operation succeeded) and `drift=false`
(allow predicted, operation succeeded) both rest on an observation that needs no
attribution argument. Correspondingly, retiring the old
`(allow, deniedStrongEvidence) → true` branch is right: its two members were a
sysctl catch-all (`.some(_) → deniedStrongEvidence`, which treated *any*
unrecognised errno as sandbox evidence) and `kr=1100`, neither of which
identifies the enforcing mechanism. The information is not lost — a consumer
recovers that population as `prediction=allow`, `observation=permission_failure`,
`observation_basis ∈ {permission_errno, bootstrap_permission_result}`, with
`sandbox_attribution_unestablished` — which is a better answer to C2 than
`drift=true` ever was. The previous round's directional-consistency complaint is
fully discharged: `runner_exec_dac`'s `deny_prediction_dac` now yields
`drift=null` with `conclusion=directional_consistency` available separately.

I looked for the opposite failure — a claim stronger than its observations — and
did not find one. `target_relation` is string equality of *submitted* values and
always carries `runtime_target_identity_unestablished`; `compound_attempt`,
`query_filter_scope_unestablished` and `local_name` namespace non-equivalence are
all handled; every comparison carries `query_attempt_order_unestablished` and
`state_stability_unestablished`.

#### The defect: exec can never reach a conclusion

`computeComparison` maps `("exec","spawn") → "process-exec"`
(`CWorkerOrchestrator.swift:695`), then sets `operation_relation = "unresolved"`
whenever `sandbox_check.operation.contains("*")` (`:705-706`). But libsandbox **rejects the
bare name**: `PolicyWitness.md:492-494` states that SBPL family operations "must
be passed to `sandbox_check` in their wildcard form — e.g. `process-exec*`, not
the bare `process-exec`", and `runner_use_c_worker/run.sh:747` records the same.
So the two spellings fail in complementary ways and there is no third.

Live, on the accepted build (`out/failure-propagation-4/accepted-build.json`;
8/8 executables and 51/51 production sources hash-match this tree):

```
step exec_star   query "process-exec*"   attempt exec/spawn /usr/bin/true (child 29359, exit 0)
  prediction allow | observation succeeded | observation_basis spawned_child
  target_relation same_submitted | operation_relation unresolved
  conclusion unavailable | drift null
  limitations [... broad_query_operation, operation:unresolved ...]

step exec_bare   query "process-exec"    same attempt
  sandbox_check.outcome unsupported_operation ("sandbox_check returned EINVAL ...")
  prediction unavailable | operation_relation matched | conclusion unavailable | drift null

step file_ok     query "file-read-data"  attempt file/open_read /etc/hosts
  prediction allow | observation succeeded | operation_relation matched
  conclusion agreement | drift false
```

`file_ok` and `exec_star` are the same epistemic situation — libsandbox predicted
allow, the gated operation demonstrably happened, the submitted target is
identical — and PW draws the conclusion for one and withholds it for the other
because of a `*` in a string.

This connects directly to **C1** in my reconstruction: "which steps report
established agreement and what comparison that covers." For every exec probe the
answer is now permanently "none," even in the case with the *strongest* evidence
in the whole matrix. It is the third failure mode the question names — satisfying
the revised contract while missing the original purpose — because the contract's
generic rule ("Broad query names … retain unresolved scope, not inferred
equivalence") is individually reasonable and collectively voids a probe family.

#### Demonstrated defect, not an architectural limitation

PW has every observation it needs here; nothing about synchronization, identity
or causation is missing that is not equally missing from `file_ok`, which does
get `agreement`. The gap is representational: the contract's mapping table
(`FAILURE-PROPAGATION-CONTRACT.md:570`) writes `exec spawn → process-exec` while
the same repository documents that this spelling is unusable. Three independent
signs suggest it was not noticed rather than decided:

1. **A contract paragraph describing an unreachable case.** The contract devotes
   a passage to exec agreement — "An exec child that ran and then failed supplies
   spawn success independently of its later exit outcome … a useful spawn
   comparison cannot erase a failed exec result" — and
   `build.review-refinements.log` records a build superseded while tightening its
   wording. Through the CLI that comparison never exists: `spawned_child` requires
   `requested_kind == "exec"`, and exec never reaches `matched`.
2. **A unit oracle that production cannot produce.**
   `DriftClassifierTests.swift:122-127` reaches `drift == false` with
   `comparisonCheck(operation: "process-exec")` — a *bare*-name query carrying an
   `allow` verdict. My `exec_bare` run shows the real prediction channel returns
   `unsupported_operation` for that spelling, so no envelope can contain that
   pair. The plan permits constructed controls and the handoff credits them
   separately, so this is not a rule violation — but the only test exercising the
   spawn-agreement rule stands on an input the product cannot emit.
3. **Mechanically flipped assertions and no exec scenario.**
   `runner_exec_dac/check.py:80` changed `steps["executable"]["drift"] is False`
   to `is None` for the fully successful, unambiguous run, and
   `runner_use_c_worker/run.sh` gained `assert s.get("drift") is None  # broad
   process-exec* query`. The ten new CLI comparison scenarios
   (`comparison-expectations.json`) are **all file-based**; none is exec. The
   plan's own acceptance bullet warns that "a passing old or mechanically
   replaced assertion cannot settle a conflict with the meaning now promised."

#### What supports this and what would falsify it

Supporting: the two live runs above; the mapping in `computeComparison`; the
mandatory-wildcard statements in `PolicyWitness.md:492-494` and
`runner_use_c_worker/run.sh:747`; the absence of any exec CLI comparison
scenario; the absence of any exec-specific reasoning in the contract, inventory
or handoff (`grep process-exec` finds only the mapping line).

Falsifiable by: **(a)** a `sandbox_check` operation string that is accepted by
libsandbox *and* equals a mapped attempt operation for exec — I found none, and
the repository asserts none exists; **(b)** a recorded design reason stating that
exec comparison is deliberately withheld because `process-exec*` covers
`process-exec`, `process-fork` and related vectors, which would make this a
justified limitation rather than an oversight; or **(c)** evidence that
`process-exec*` genuinely gates more than the spawn the attempt performs, in
which case `unresolved` is correct and only the documentation is missing.

#### Bounded correction

No new field and no added certainty. Either:

- treat a query whose operation is the **accepted family spelling** of the mapped
  attempt operation as `matched`, and keep the breadth visible by replacing
  `broad_query_operation` with a specific limitation
  (e.g. `family_scope:process-exec*`) for that case — the comparison then behaves
  for exec exactly as it does for files, with the family breadth still reported;
  or
- if (b) above is the real judgment, record it: add the exec case explicitly to
  the C1/C3 dispositions and the `runner_exec_dac` README, so a reader learns
  that exec comparison is withheld by design rather than inferring it from a
  generic limitation shared with `file-read*`.

Either way, add one exec scenario to `check_comparison.py` so the chosen
behaviour is pinned by a CLI control rather than by two flipped assertions.

### 2. Is the compatibility migration complete and the verification sound?

**Substantially yes.** This is the most rigorous acceptance in the effort: it is
an all-catalog run, the dependency inventory was written before the edits, and
the review program reconciles IDs rather than trusting a selector. I found one
substantiated gap, in the justification for retained results — not in the results
themselves.

#### What I verified independently

| Check | Method | Result |
| --- | --- | --- |
| Required scope = whole catalog | Rebuilt case IDs from `tests/catalog.json`, diffed against `required-case-ids.txt` | 130 = 130, no ID in either set only |
| Signed build matches the commit | Hashed all entries of `accepted-build.json` | 8/8 executables, 51/51 production sources match |
| Tested source = committed source | `tested-source.json` vs `closeout-source.json` vs tree | differ in **5 files, all Markdown**; `closeout-source.json` (368 files = exactly the tracked non-`dist` set) matches the tree except this audit file |
| Candidate → final delta | Recomputed from `candidate-source.json` vs `tested-source.json` | 13 files, identical to `review.json`'s list |
| Final battery | `accepted/run.json` | 108/108 pass, 0 skip, app inspection valid and unchanged |
| First battery | `all-candidate/run.json` | 130 run, 127 pass, 3 fail (stale expectations), 0 skip — retained, not credited |
| Batch internals | `pwrunner_core_tests.log` in the accepted run | `262/262`, **0 internal SKIP, 0 FAIL**; Rust 110, CLI integration 10 |
| BYOXPC | Filtered `accepted/run.json` | all **13** BYOXPC cases ran on the final build and passed, including BBX-001/002 |
| Response version and legacy | `PWRunnerAPI.swift` (`comparison` is `decodeIfPresent`/`encodeIfPresent`; default 7) plus `EnvelopeInvariantTests` | stored versions 4–6 retain their own `drift` with `comparison`, `requested_kind`, `requested_action`, path `observer`/`phase` all nil; controller forwards the runner's version verbatim |
| Live log candidates (C6) | Raw `signal_capture/run.json`, `success_capture/run.json` | real captured events; 1 and 2 associations; each `association: "ambiguous"` over two repeated-attempt candidates, with per-candidate `operation_source: "submitted_attempt"` and `path_sources` — genuine observation, correctly not a unique occurrence |
| Focused rerun | `--case runner_validator_failure/transcript_controls --case runner_exec_dac/… --case witness_contract/drift_determination_via_validator_seam --suite unit --suite source_drift` | 5/5 pass on the current tree, integrity valid and unchanged |

Evidence provenance is also correctly stratified: the ten CLI comparison
scenarios use a **fixture-supplied** validator transcript (its verdicts are test
data, not native `sandbox_check` calls) with **real** worker attempts and file
effects; `runner_exec_dac` adds a direct out-of-band execution control;
`DriftClassifierTests` is constructed interpretation; the log candidates are
independently observed. The handoff says so in each case.

#### Substantiated gap: the retained-result basis is stated more broadly than it holds

`review.json` credits 22 of the 130 cases from the earlier `all-candidate`
battery under this basis:

> "all 22 retained cases are offline and their executable inputs/fixtures are
> unchanged."

That is not established for one of them. `review.py:36-38` implements the
retention rule as *"the case does not require `app`"* — it never checks whether a
retained case's own test code changed. And
`tests/suites/runner_validator_failure/check.py` **is** in the 13-file
candidate→final delta, and in `review.py:47-54`'s own `allowed_executable_delta`.
`runner_validator_failure/transcript_controls` is credited from the candidate
battery (`review.json` `case_credits`), and `runner_validator_failure/run.sh:12`
runs exactly that file (`check.py fixture`). So its credit comes from a run that
executed a different version of its own checker.

**Consequence: none, in fact.** I read the hunk — it is confined to `check_cli`
(lines 137-141: the drift/conclusion expectations for the two app-dependent
cases, both of which were rerun on the final build) — and `transcript_controls`
executes `check_fixture`, which is untouched. I then reran the case on the
current tree and it passes. So the accounting is imprecise, not wrong.

**Bounded correction**, in order of cost: rerun that one case (it needs no app
and takes seconds) and re-credit it; and tighten the rule in `review.py` from
"does not require `app`" to "no source reachable from the case's command changed
since the crediting battery," so the `retained_result_basis` sentence is
something the program actually checks. Absent that, narrow the sentence to name
the exception.

#### Smaller notes

- `review.py`'s `allowed_executable_delta` is a hand-maintained allowlist. It
  correctly caught the five executable-source changes here, but it is asserted
  against, not derived; a future delta is only as good as the list someone edits.
- The two claims I could not check from artifacts alone — that the tracked C
  convenience binary was restored to committed bytes, and that no mutation or
  fixture was installed into the inspected app — are consistent with the tree
  (`git status` is clean apart from this file) and with the unchanged app
  inspection, but rest on the handoff's statement.
- Nothing in step 4 pre-empts step 5: C1–C6 remain open dispositions, and the
  recovery filters are not yet written. The exec finding in part 1 is exactly the
  kind of thing step 5's C1 review should catch; it is reported here because the
  step-4 contract already promises the distinction that exec silently cannot
  deliver.
