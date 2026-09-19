1. After reading `tests/FAILURE-PROPAGATION-PLAN.md`, what does the plan intend to accomplish? Answer in your own words in **no more than 175 words**. Describe its high-level promises and what fulfilling them would mean for PolicyWitness, rather than summarizing its implementation steps.

2. After reviewing the repository changes against the plan, what is **one high-level case** where the implementation falls short of those promises? Explicitly connect the deficiency to an aspect you identified in your answer to question 1, explaining how the observed behavior fails to fulfill that promise. Ground the case in concrete repository evidence, and assess it against the plan’s intent rather than taking implementation choices or completion notes as the definition of success.

## Results

### 1. What the plan intends to accomplish (167 words)

PolicyWitness's output is testimony, and the plan's promise is to make it
admissible. Every statement in a run envelope should be traceable to the
component that actually observed it: the worker's published progress, the host's
supervisory actions, the validator's records, the controller's own capture. A
summarizing layer may rank those observations; it may not rewrite them, invent a
value nobody returned, or assign a cause nobody saw. Absence must stay visibly
absent, and "I cannot tell" must be a first-class, sayable result — including the
possibility that PolicyWitness's own instrumentation, rather than the sandbox, is
at fault. Correlation must stay separable from causation, every policy claim must
carry its own supporting observation, and evidence must travel without each
receiving layer having to understand it.

Fulfilling this changes what the tool is. A drift or denial report stops being a
label a reader has to trust and becomes an auditable account: who saw what, and
how far that evidence actually reaches. PolicyWitness's whole value rests on that
distinction.

### 2. Where the implementation falls short

**The case: `steps[].drift` — the one claim PolicyWitness exists to make — is the
only observation-derived statement in the envelope that this effort left with no
provenance and no way to say "I cannot tell". It still reports agreement from an
observation the code itself says cannot be attributed.**

This breaks the part of question 1 that matters most: *every policy claim must
carry its own supporting observation*, and *"I cannot tell" must be sayable*. The
plan states both directly — "Each policy claim needs its own supporting
observation" (`FAILURE-PROPAGATION-PLAN.md:99`), and, in the observer contract,
"Attempt completion alone does not make a permission failure a proven policy
denial. Missing observations do not establish agreement or disagreement"
(`:145-146`).

#### The behavior

`computeDrift` maps `(prediction=deny, observation=ambiguous permission failure)`
to `false` (`CWorkerOrchestrator.swift:659`), under a comment that concedes the
point: "small risk of crediting libsandbox for a DAC denial, accepted because the
signal is mostly right" (`:648-649`). `false` is defined publicly as "when they
agree" (`PolicyWitness.md:385`) — the identical value an observed allow/allow
agreement produces. Nothing in the step distinguishes the two.

`git diff 0670db1..HEAD` touches only comment lines in that function. Across
steps 0–3, the field is byte-for-byte the same decision it was before the effort
began.

#### The evidence, from the project's own control

`runner_exec_dac/deny_prediction_dac`, run here against the accepted step-3 build
(`out/failure-propagation-3/accepted-build.json`; all 8 executables and 366 of 367
recorded sources hash-match this tree — only this audit file differs):

```
policy:  (version 1)(allow default)
         (deny process-exec* (literal "/private/tmp/pw-exec-dac-.../denied-query"))
query:   process-exec*  /private/tmp/pw-exec-dac-.../denied-query   -> deny
attempt: exec spawn     /private/tmp/pw-exec-dac-.../helper         -> exec_failed,
                                                    errno 13, child_pid 0
envelope: normalized_outcome = ok,  steps[0].drift = false
step keys: [attempt, deny_signal, drift, sandbox_check, step_id]
```

The attempted helper is **allowed** by the policy; only a different path is
denied. The helper is mode 0644, and the suite records its own out-of-sandbox
control in the same artifact directory — `deny_prediction_dac.direct.json`:
`{"spawned": false, "errno": 13}`. So at the moment it publishes `drift=false`,
PolicyWitness holds, in one artifact set, (a) a prediction about a path nobody
attempted, (b) an attempt failure its own policy says the sandbox did not cause,
and (c) a direct control showing DAC caused it. It publishes "they agree."

#### Why this is high-level, not a detail

Every other claim in the envelope was given an explicit unknown state by this
effort. Predictions and attempts gained `result_source`, `native_rc` and
`missing_reason`; the corrections batch added `association_issues.kind=
"query_mismatch"` so a verdict answering the wrong query cannot supply a
prediction. Validator reception gained `decode_fault` and `expected_step_ids`.
Worker publication gained `failure_state` ∈ absent/incomplete/published/invalid.
The host gained `reaped`, `poll_stop_reason`, `wait_errors`. Log correlation —
the closest analogue — gained `association` ∈ `candidate`/`ambiguous`,
`correlation_status` ∈ `not_attempted`/`unavailable`/`no_match`/`pid_match`,
`window.pid_reuse_protection: false`, and `termination_cause: "unknown"`.

The termination question was taught to say "a PID match is a candidate, not a
cause." The drift question — the one the tool exists to answer — was not taught
to say "an EACCES is a candidate, not an agreement." `drift` remains `bool | null`
with no sibling field, and the routing inventory contains no row that *routes* it;
its single entry, "Directional drift" (`FAILURE-PROPAGATION-INVENTORY.md:153`),
records the behavior as accepted rather than as an owned observation.

The disambiguating evidence is collected and then not joined. Per-step denial
candidates exist (`match_step_denies`, with `process-exec` mapped from the
submitted attempt), but they live in the controller, while `drift` is computed in
the runner — before the controller captures any log — and the controller never
revisits it. PolicyWitness gathers what would resolve the ambiguity and leaves the
claim standing unresolved.

#### Why the completion notes do not settle it

The suite README calls this "agreement of outcomes, not evidence that the sandbox
caused the attempted helper's failure"; the contract says "False does not
establish that the sandbox caused the attempt failure"
(`FAILURE-PROPAGATION-CONTRACT.md:478-480`); `check.py:69` asserts
`denied["drift"] is False`. Those are prose and a pinned assertion — they state
the limitation everywhere *except* in the envelope a consumer actually reads.
That is precisely the pattern this plan set out to end: the whole point of
`missing_reason`, `failure_state` and `termination_cause` is that a limit which
exists only in documentation is not an observation. A test that asserts the
current value is a completion note, not a demonstration that the value is right.

The conservatism itself is defensible — leaning away from false drift positives
is a reasonable bias for this tool. The shortfall is that the bias is invisible
and unfilterable. A consumer aggregating `drift == false` as "libsandbox agreed
with kernel enforcement" silently absorbs every permission failure PolicyWitness
could not attribute, and cannot tell which rows those are. That is the specific
confusion the tool exists to prevent.

#### What would discharge the promise

No redesign, and no change to the classifier's bias: the plan's own vocabulary
already covers it. A per-step basis alongside the boolean — `drift_basis ∈
observed | directional_ambiguous`, exactly parallel to
`sandbox_check.result_source` and `step_denies[].association` — would let
`drift=false` keep its current value while stating which observation supports it.
Then a reader could do what question 1 says fulfilment means: see who saw what,
and how far the evidence actually reaches.
