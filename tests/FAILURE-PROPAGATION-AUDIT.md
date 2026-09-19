1. Is step 3 of `tests/FAILURE-PROPAGATION-PLAN.md` actually complete, with its completion claims supported by the implementation and retained evidence? Review the seven requirements against the source, tests, failure contract, routing inventory and `tests/out/failure-propagation-3/closeout/`, rather than treating checked boxes or closeout prose as proof. Ground your conclusion in specific source and artifacts, including whether the tested implementation matches the committed work, whether the controls and mutations establish the claimed preservation, and whether fixture-supplied fields remain clearly distinguished from independently observed facts. Identify any unfinished obligation that belongs within step 3, keeping the interpretation work explicitly assigned to steps 4–5 separate.

2. What, if anything, should change in the planning of steps 4–5 before execution to prevent an agent from satisfying their written acceptance criteria while failing the plan’s intended outcome? Assess the route from evidence-join review and compatibility management through design acceptance and permanent consumer-recovery tests. Examine whether the plan adequately separates settling which distinctions are justified from enforcing that consumers can recover those distinctions, while preserving legitimate uncertainty. Develop one concrete planning weakness you can substantiate, showing how it could survive the existing gates and proposing a bounded correction. Tie the critique to the actual plan and repository dependencies; do not assume that more fields, tests or mandatory certainty would resolve it.

## Results

### 1. Is step 3 complete?

**Yes — substantively and verifiably, with one narrow unfinished obligation in the
closeout's own account of itself.** This is the best-evidenced batch in the
effort so far: the claims are qualified rather than inflated, and every one I
tried to falsify held up.

#### What I verified independently

| Check | Result |
| --- | --- |
| Closeout snapshot covers the repository | The 367-file snapshot is *exactly* the set of tracked non-`dist`/`target` files — 0 tracked files omitted, 0 extras |
| Snapshot still matches the tree | 366/367 hash-match; the only difference is this audit file |
| Signed build | 8/8 shipped executables and 51/51 recorded build sources hash-match `accepted-build.json` |
| Tested implementation vs committed work | Diffing the accepted-run snapshot against the closeout snapshot: **7 files changed, all Markdown** (`COVERAGE.md`, three plan/contract/inventory docs, two READMEs, this audit). No executable or test source moved between the tested state and the commit |
| No production behavior change | Every line the step-3 commit added to `controller/src/*.rs` and `main.swift` is inside `#[cfg(test)]`/test registration; `transport_diagnostics()` is `#[cfg(test)]` |
| Controls re-run on the committed tree | `witness_contract/unfamiliar_diagnostic_transport` **11/11 checks, 0 failures**; `runner_unit` **258/258 with 0 internal SKIP and 0 FAIL**; `unit/rust.unit` pass; `source_drift` pass; app inspection `valid_before: true, unchanged: true` |
| Mutations | All four retained mutation directories mutate the *exact* source now in the tree (`original_sha256 == current`) and restore it byte-for-byte (`restored == original`) |

#### The seven requirements

- **R1 (bounded arrangement).** Two genuinely distinct payloads:
  alpha uses an unfamiliar operation (239) *and* an unfamiliar `native_kind` (77);
  beta uses a **known** operation (8 = `sandbox_apply`) with an unfamiliar code.
  Alpha also pins `errno: 0` with `errno_present = 1`, exercising "zero remains a
  value." The producer literals (`tests/fixtures/diagnostic_transport/worker.h`)
  and the oracle (`cases.json`) are separate files, so a transport defect and a
  transcription slip both surface. Fixture built to `PW_TEST_ARTIFACTS`, outside
  the inspected app; the override is asserted mirrored in the reply.
- **R2 (carry each record through every boundary).** The CLI control drives C
  publication → Swift decode → runner JSON → XPC client → controller parse, and
  compares `evidence['failure']` to the oracle by whole-dict equality. Layers that
  are *not* reached by a real producer (helper/observer receivers) are stated as
  limits rather than implied.
- **R3 (unsuccessful stays unsuccessful; no inferred cause).** Every worker mode
  asserts `rc == 1`, `runner_failed`, `sandboxed_after_apply == False`, reaped
  exit 23, and an untouched independent file witness. The sharpest assertion is
  the pair: alpha requires `'sandbox_apply'` and `'sandbox_compile_string'` to be
  **absent** from the error, while beta requires `'sandbox_apply'` to be
  **present** — i.e. a known operation survives an unfamiliar code, and an
  unfamiliar operation is never promoted to a known one.
- **R4 (absent / unpublished / malformed / incompatible + truncation).** All four,
  plus `transport_bad_text` (declared length out of bounds → `invalid`) and
  `transport_beta_truncated` (real 4095-byte truncation), each asserting that the
  numeric record survives independently of text availability.
- **R5 (mutations must fail the controls).** Known-code-only worker decoding and
  known-outcome-only validator forwarding each fail `runner_unit` **and**
  `witness_contract/unfamiliar_diagnostic_transport`; shared-receiver detail
  removal fails `unit/rust.unit`. All restored.
- **R6 (acceptance review; fixture vs observed).** This is discharged unusually
  well. `FAILURE-PROPAGATION-CONTRACT.md:483-516`, the inventory's transport
  table, `COVERAGE.md` and both suite READMEs now say plainly that the transcript
  producer never calls `sandbox_check`, that even its `allow`/`rc=0` record is
  supplied test data, and that "a shared envelope does not establish a causal
  relationship between the retained records." The independently observed facts —
  host EPIPE, reaped exit 23, receiver UTF-8 fault, the real worker's file
  change — are named separately every time.
- **R7 (handoff).** Scope, limits, provenance and the doc-only closeout delta are
  all recorded and reproduce exactly.

#### The one unfinished obligation (inside step 3)

The closeout's account of the mutation experiment is incomplete, in two linked
ways.

`tests/out/failure-propagation-3/mutation-worker/` retains a run of the *same*
mutant (identical `mutant_sha256`) that did **not** fail the controls cleanly —
it aborted the Swift suite:

```
  FAIL unfamiliar operation code and kind retain signed result and zero errno ...   (4 clean failures)
  ...
[unfamiliar diagnostic transport]
PWRunnerCoreTests/DiagnosticTransportTests.swift:49: Fatal error: Unexpectedly
found nil while unwrapping an Optional value          rc=133, no summary line
```

The response was correct and is disclosed in
`out/failure-propagation-3/README.md:86-90`: the force-cast was replaced with a
normal `TestFailure` (the current line 49 is a `guard ... as? ... else { throw }`,
which cannot emit that message), `mutate.py` gained the assertion *"mutation must
fail normally, not crash"*, and the mutation was repeated as
`mutation-worker-confirmed`. That is exactly the right handling.

What is missing is at the closeout, which is the document the plan's status
paragraph points to as the handoff:

1. `closeout/README.md` opens with "**No production or test-code correction was
   needed.**" A test-code correction *was* made inside step 3 —
   `DiagnosticTransportTests.swift` was hardened, and the mutation driver was
   revised (`mutate.initial.py` → `mutate.py`). Requirement 7 asks for "an exact
   account of the source changes"; this sentence contradicts the step-3 README.
2. Requirement 6 says to review the claims "against the retained inputs, outputs
   and **mutation failures**." `closeout/review.py:93-110` iterates exactly three
   directories — `worker-confirmed`, `validator`, `controller` — and never reads
   `mutation-worker/`. The one retained mutation artifact whose outcome was a
   suite abort rather than a control failure is the one the review program skips.

This is bookkeeping, not coverage: the substance is disclosed elsewhere and the
confirmed re-run is sound. The bounded fix is two sentences in
`closeout/README.md` (state the mid-step test-equipment correction and why
`mutation-worker/` is superseded) and adding that directory to `review.py` as an
explicitly superseded entry. It is worth doing because it is the same class of
fragility flagged earlier in this document: a control that *crashes* the suite
prevents the remaining controls from running and leaves the log the handoff tells
the next agent to inspect truncated. `mutate.py` now guards future mutations
against that; nothing guards the ordinary suite, and the closeout is the natural
place to record that residual.

Nothing here belongs to steps 4–5. Drift meaning, query/attempt comparability,
temporal assumptions, host-enrichment provenance and log causation are correctly
excluded from step 3 and correctly assigned onward.

### 2. A planning weakness in steps 4–5

**The plan protects accepted *answers* from being bent to fit the
implementation, but leaves accepted *questions* free to be bent — and the
questions are written after the implementation is built, gated and committed.**

#### Where the seam is

The consumer-question table lives in step 5
(*Settle the design judgments and expected consumer answers*), and step 5 begins
"This step follows the step-4 commit and review." So the order is:

1. Step 4 writes the claim/evidence table, chooses the representation, passes the
   compatibility/dependency gate, updates every dependent assertion, and
   **commits**.
2. Step 5 then settles which distinctions are justified, and is told to use the
   six questions as "starting points, **refining their wording to the contract
   actually accepted**."
3. Step 5 writes the JSON-only recovery checks against those refined questions.

Step 5 guards step 2→3 well: "Do not derive expected answers from the emitted
summary labels or copy the classifier into the oracle," and "Changes to an
accepted answer require an explicit design reason; making a failing filter pass
is insufficient." Both of those protect the **answer**. Nothing protects the
**question**, and the question-refinement licence points the other way.

#### How it survives every existing gate

Take the third question — *"What relationship between each query and attempt was
established, known to differ, or left unresolved?"*

- **Step 4's claim/evidence table** asks "What connects their operation, target
  and relevant conditions?" An honest, accurate row reads: *nothing in the
  envelope connects the operations; the runner deliberately accepts independently
  specified queries and attempts; the strongest supported conclusion is pair
  consistency, not comparability.* Requirement satisfied.
- **Step 4's "Implement bounded corrections"** then *endorses* changing nothing:
  "Continue accepting independently specified queries and attempts; admission or
  string equality alone cannot certify a meaningful comparison." And the step
  explicitly permits stopping there — "A useful result can leave interpretation
  unresolved."
- **The compatibility/dependency gate** is triggered by the *chosen
  representation*. If the representation does not touch the attempt object, the
  gate has nothing to inventory. Gate satisfied.
- **Step 4 acceptance** asks for "a deny query for A paired with successful
  allowed attempt B" and "Assert both retained evidence and the limited
  conclusion/derivation." A test asserting *no comparability claim is made*
  passes.
- **Step 5** refines question 3 to something the shipped envelope answers —
  e.g. "is the submitted query target recorded alongside the attempted target?" —
  records the expected answers, and the recovery checks pass.
- **Step 5's anti-degeneracy control** ("Include a case where blanket unknown
  would discard a conclusion the reviewed evidence supports") does not fire,
  because nothing was collapsed into unknown; the distinction was never put on
  the table.

Every box is checked. The intended outcome — a consumer can recover the accepted
distinctions from the envelope — quietly loses one, and the loss is invisible
because the record of it is a reworded question.

#### Why this is a real repository dependency, not a hypothetical

The envelope today cannot answer question 3 on the operation dimension, and the
plan already knows why. `tests/FAILURE-PROPAGATION-PLAN.md:398-402` records the
design: relevant operations are derived "from the submitted attempt's kind/action
… The current reply's attempt object omits kind/action; **the controller retains
the submitted request** and can use that provenance without adding duplicate
authoritative fields."

Confirmed against live CLI output from the accepted build:

```
steps[].attempt keys:  errno, exit_code, native_rc, normalized_path,
                       observed_path, outcome, rc, requested_path,
                       result_source, syscall_errno          # no kind, no action
envelope data keys:    ..., request_path, ...                # a path, not the request
"probe_plan" present in envelope: False
```

So the controller solved its own comparability problem by reading the request
**file** — precisely the input step 5 forbids the consumer test from using
("consulting … external artifacts to construct the consumer's answer is not
[allowed]"). A JSON-only consumer can compare `sandbox_check.filter_value` with
`attempt.requested_path`, but cannot see which syscall the attempt performed, and
therefore cannot tell a comparable pair from an intentionally divergent one —
the exact distinction the step-4 table row and the `runner_exec_dac`
deny-A/attempt-B scenario exist to protect. The same asymmetry applies to
question 6: `step_denies` is derived by the controller from the request, and a
consumer can read the conclusion but cannot recover what it rests on.

#### Why more fields, tests or certainty do not fix it

Adding `kind`/`action` to the attempt object would answer *this* question and
leave the mechanism untouched — the next representation choice would silently
reshape the next question. More recovery tests make the reworded question more
thoroughly enforced. Requiring a definitive answer is worse: "not established" is
the *correct* answer here, and the plan is right to allow it. The defect is not
in the contract's content but in the order of operations: the design judgment
that decides which distinctions matter runs *after* the implementation that
determines which distinctions are expressible.

#### Bounded correction

Move the consumer-question list out of step 5 and into step 4, immediately
**before** *"Choose a bounded public contract"*, and treat it as an input to the
design rather than an output of it. Then extend step 4's compatibility decision
with one column: for each frozen question, record exactly one disposition —

- **(a) answerable** from a single envelope under the chosen contract;
- **(b) deliberately not answerable**, with the design reason and the evidence or
  architectural limit that makes it so (question 3 would land here today, citing
  the kind/action decision at plan lines 398-402);
- **(c) answerable only with an added field or changed meaning** — which then
  enters the dependency inventory and the version decision.

Step 5 keeps its wording-refinement licence but inherits the protection the plan
already gives answers: a question may not be dropped, merged or have its
disposition changed without an explicit design reason, and a recovery check may
not be written against a question whose disposition changed to make it pass.

This adds no field, no certainty and no test. It costs one table in step 4 and
one sentence in step 5. What it buys is that outcome (b) — a perfectly acceptable
result — has to be *chosen and reviewed* rather than achieved by rewording, and
that the final ownership map in step 5 can show a reader which questions the
product answers, which it deliberately does not, and why.
