# Controller integration verification

## Scope and applicability

Integration candidate: `424f3c73a8a4f4f6cc3c147b40effb4ce3b79320`.
The maintainer accepted M01–M05 in DECISIONS. The implementation leaves
controller/runner runtime, shared consumer, fixtures, request grammar, wire
shape, field declarations, build pipeline, waits/releases, invocation and
cleanup mechanisms unchanged. The concrete changes are normative clarification,
explanatory integration, complete expected-error matching in one owning test,
and the controller tour's known-gap inventory/controls.

This is a reviewed dependency judgment, not a claim that shape or hash equality
proves runtime behavior. The initial eight-case evaluation remains applicable
to the unchanged controller/CLI/example paths: its actual entry scripts, unit
and integration sources, live case, example controls, imported readers and
fixtures did not change. Its old checker result remains historical evidence
of the narrower assertion. The changed result-control function must execute
again. No reader semantics or fixture coherence changed, so the complete
default battery triggered by such a change is inapplicable. No shipped input
changed, so no replacement signed build or new native comparison is required.
No wait/release/eligibility, protocol/layout, limit, selector, reservation or
cleanup change triggers their separate conditional native/mutation suites.
No release-form claim, tag or publication is part of this work.

The final documentation/control selection was inspected with the dispatcher's
`--list`: ten source-drift cases plus `blackbox_e2e/checker_controls`. They
cover generated ownership/freshness, authored tree/history/shape, independent
build/source controls, Markdown/prose/link handling, documentation copies and
the complete result diagnostics. Selection does not itself establish a pass.

## Structural checks and public accounting

Direct generator checks after the authored edits passed `--tree-check` and
`--check --require-history`. The tree retains 19 surfaces, 1,907 nodes and
1,004 fields with no uncovered record; free counts remain condition 51,
dependency 0, effect 78 and when 4. These are structural results, not runtime
observations. The first generation attempt refused two illegal definition
placements without writing outputs; the existing language was retained and
the nodes placed beside their reporting rules, as DECISIONS records.

A's normalized public comparison found unchanged existing rule/field contexts,
effects, applicability and actors. Three gap nodes become definitions in place;
two old gap IDs map to new sibling definitions with explicit references and
scoped prose. Local nodes change in the four intended authored surfaces;
their shared expansions also change the request, probes, actors, extensions,
refusals and installation public views. Surface artifacts, history and goldens
remain unchanged. The two
descriptive definitions' inherited context changes are expressly accounted
for in DECISIONS; no claim of identical context for every node is made.
Support changes remove stale references to undecided policies without adding
execution credit. Historical snapshots and shape goldens remain unchanged.

| Identity or artifact | Before / after |
| --- | --- |
| Public build contract | unchanged `development:6a333cf6f19aea6939fa843655b6ce2a90ec05837fb4bb6b8b9288b0ccc572f0` |
| Worker source identity | unchanged `52bbda618677886b6c59dcf5dd999e2b2a5021cbd2c8dc4f08aa0ba66ef2dd38` |
| Wire fingerprint | unchanged `80013e5b7342e84db61177804883655e3d60bc370bf0a4aa1bc61453a064e224` |
| `docs/porcelain.json` file SHA-256 | unchanged `538b3cf552fa8fa3578287e39a56594592799ff6062d35e5bfc7242ea4b009c2` |
| `controller/src/example.rs` SHA-256 | unchanged `31ae70312ee0d32bffc8a524a2b6c663237a0387bb621c335ecf75b3cd5536b6` |
| `docs/contract/public.json` SHA-256 | `36be1491309c8d204f005bafa3abdb1f643bacda3b09c961b3fd1b5ac13fc366` → `cd0e1175125ee3c76efaaa4285c1e20dac3d9208220fc5fa407bb6327a943397` |

The code-defined development identity excludes this contract prose and support;
the public snapshot reflects the clarified meanings. The selected signed app
remains the accepted clean `a5de0c63` build described in BASELINE. Recomputed
development and worker identities agree with it. Fresh selected-app signature
and byte inventory checks belong to each dispatcher receipt, not this digest
comparison.

The architecture manifest changes only the existing source-drift node's Guards
text to include the controller tour. Its generator regenerated the table, DOT
tooltip and SVG tooltip/stamp. Review of the generated diff confirms unchanged
visible labels, geometry, nodes, edges and layout; only the tooltip content and
its DOT digest change. D's new control diagram is authored Mermaid, reviewed
against its named routes and not registered as a generated destination. The
known-gap checker explicitly registers the tour and extends the existing
unindexed/indexed/missing-heading/spurious-entry/restoration controls.

## Consolidated execution

```sh
env PYTHONDONTWRITEBYTECODE=1 PW_TEST_OUT_DIR=tests/out/runs/controller-authority-verification PW_TEST_QUIET=1 tests/run.sh --suite source_drift --case blackbox_e2e/checker_controls
```

Run `20261113T155111Z_8ba29955` completed outside the automation sandbox under
the repository checkout lock: all 11 selected cases passed, with no skip,
unrun case, harness error or recorded system sleep. Selected-app integrity was
valid before execution and unchanged afterward. Duration was 428,073 ms.
No build, test or artifact mutation was performed by a principal agent;
returning review notes did not change the executed inputs.

The 134 real consumer-input controls retain 189 actual diagnostics. Every
complete expected/actual multiset matches with empty missing/unexpected lists.
The five separate oracle controls traverse the actual control path: baseline
and restoration accept; the unrelated sentinel is the only unexpected extra;
removing the comparison produces exactly that missing message; duplication
produces exactly one unexpected copy. Their scope is matcher sensitivity,
distinct from the real validator calls. Raw receipts are
`suites/blackbox_e2e/checker_controls/artifacts/result-consistency-controls.json`
and `result-oracle-controls.json` under the run directory.

The planner receipt at
`suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/controls.json`
records all five new controller gap cases with no problems: unindexed and
spurious entries produce exactly `known_gaps.index_order`; a missing final
heading produces `known_gaps.final_section`; indexed and restored inputs pass.
These are evaluated controls, not blocked rules or generic rejection credit.
Generator controls passed complete link/anchor/prose, ownership, freshness,
history and shape checks; no free-text or prose baseline was raised.

### Final prose correction and reviewed reuse

After execution, BR01 replaces “carried actor labels, phase IDs and action IDs”
with “carried actor labels and each matching phase's action IDs” in one prose
sentence. The changed sentence now matches the inspected production selector.
It changes no heading, link, code/span/fence structure, known-gap paragraph,
quantity, generated region, contract, test or implementation. A/B/C agree with
the correction, and D accepted it in the integration response.

The coordinator reuses this run's structural results for that exact delta under
the reviewed-exception rule in tests/AGENTS. The predicates exercised by the
link/anchor/gap/prose checks are unchanged by removing the falsely named join;
semantic accuracy is established by source review, not those structural checks.
The real consumer and comparator inputs are unchanged. This is explicitly
reviewed applicability, not a claim that the final sentence's bytes were present
during the run. `git diff --check` passes. No third test run is needed solely
for this sentence, and no new execution credit is inferred from its review.

## Review and retention

Frozen A/B/C original hashes were recomputed and equal INITIAL-FREEZE. All
56 original obligation families occur once in INTEGRATION, with original scope
cells preserved and final disposition, sources, assertions and limits attached.
The reviewer roles remain distinct. C's bounded oracle review found no required
source correction, with execution explicitly pending.

`git worktree list --porcelain` shows only the original checkout. This plan
created no worktree and no minor-agent assignments. Disposable outputs remain
in their dispatcher-owned locations until receipt inspection and final review;
ordinary pruning will retire them after their dispositions are recorded.

All three returning reviews now accept the final result, including receipt
inspection and the exact BR01 reuse exception. D's response accepts that
correction without another product choice. The normal prune preview passed
outside the automation sandbox after the sandboxed signature diagnostic;
the same release artifacts were unchanged between attempts.
`make prune APPLY=1` removed both completed disposable run directories with
no blockers/failures/unmanaged output and preserved protected release evidence.
Raw development receipts are now unavailable; EVIDENCE records the complete
retention disposition. There is no pending verification or cleanup action.
