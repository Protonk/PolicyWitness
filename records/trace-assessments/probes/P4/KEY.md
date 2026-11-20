# P4 answer key: test-only reading

Readers see only the named test or checker code. They do not see the product
code or the account that credits the test. For each target they say what the
test establishes, which incorrect behaviour would make it fail, and which
plausible claim it does not support. The coordinator wrote this key by
reading each test before any reader ran. The credited claim each test's
account makes is quoted under "Credited" once Pass 2's review fixes land.

## T1 `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift`, the self-transfer test ending at the custody assertion (~`:467-468`)

**Establishes:**
- the transfers, deliveries and consumes in that schedule, including that
  B accepted while parked and A consumed its self-transfer in a later visit;
- after the run, including teardown, every custody entry reports `erased`.

**Fails on:** a schedule whose transfers or consumes misbehave, or a run
after which custody is not marked erased at all.

**Does not support:** that custody was erased at the token's last declared
transfer. `AuthorityCustody.finish()` sets `erased` on every entry
unconditionally (`AuthorityCustody.swift:637`), so last-use clearing and
teardown cannot be told apart. The comment above the assertion claims
otherwise; this is DT-63.a and DT-124.g.

## T2 `tests/suites/witness_contract/check_extension_redelegation.py`

**Establishes (enforced):**
- apparatus integrity on every run: distinct fresh processes, equipment,
  application, publications, `query_first`, `finished`;
- a positive calibration on this host: A's issue is non-null, the transfer
  is delivered and equal, B's consume returns, and B's read fails before and
  succeeds after with matching bytes;
- for the two omission contrasts, that the chain is incomplete and not
  credited.

**Recorded, not enforced:** whether the principal chain is credited, and the
results of the two weakened-policy contrasts.

**Fails on:** missing issuance, transfer, consume or access capability;
apparatus defects; an omitted link that is nonetheless credited.

**Does not support:**
- that re-delegation works, since the principal credit is not asserted;
- that the weakened policies prevent re-delegation, since those results are
  only recorded.

## T3 `tests/suites/witness_contract/check_pre_apply_failure.py`

**Establishes:**
- the consumer validates each envelope;
- the expected step observations are selected;
- no library result or cause claim appears for the pre-apply failure;
- raw lifecycle observations;
- the effects.

**Fails on:** a consumer-invalid envelope, a cause claim, missing raw
lifecycle facts, or wrong effects.

**Does not support:** that the envelope's lifecycle claims are correct. The
lifecycle oracle is never invoked, so a withheld or contradictory claim that
the consumer accepts would pass (DT-53.g).

## T4 `controller/src/run_flow.rs` `compiled_profile_status_and_labels_alone_decide_run_admission`

**Establishes:**
- reply admission decides a receipt row on its status and two labels only:
  two rows admitted, nine refused at admission with the decoded reply kept,
  and eight refused first by the test's typed reader;
- an admitted `captured` row whose nonce, source and parameter fields match
  nothing submitted is still admitted.

**Fails on:** admission that ignores status or labels, drops the decoded
reply on refusal, or compares fields beyond the labels.

**Does not support:**
- that a captured receipt is authentic;
- that a captured receipt is associated with its request;
- anything about live host behaviour, because the client result is supplied.

## T5 `controller/src/run_flow.rs` `ordinary_fallback_receives_the_held_request_after_the_file_is_replaced`

**Establishes:** through production orchestration with client and helper
callbacks, after the request file is replaced inside the client callback:
- the client received the expected resolved request;
- every helper input equals the client input byte for byte;
- the envelope's capture is the one returned for that input.

**Fails on:** rereading the file for the helper, re-serializing the request,
or handing the helper anything but the held bytes.

**Does not support:** that the shipped client reaches this capture, or that
the shipped helper compiles this input. The callbacks stand in for both, as
the test's comment says.

## T6 `tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py`

**Establishes:**
- a same-group descendant's lifetime is classified as an informational
  observation;
- the reply truthfully accounts for the exec, an enforced judgment: finished,
  worker facts, the `leader_exit_and_eof` stop with cleanup `not_requested`,
  the leader's status, and envelope validity;
- the later step's file effect, also an enforced judgment.

**Fails on:**
- a reply whose reported facts disagree with the independent observations,
  including a different stop or cleanup claim;
- a missing later effect;
- unresolved lifetime evidence;
- lost cleanup observation.

**Does not support:**
- that the product keeps descendants alive;
- that a product which ended the descendant at completion would pass. It
  would not: the `leader_exit_and_eof` with `not_requested` relation stays
  enforced at controller admission.

## Credited claims, at `24ea8ada`

- **T1.** The test's own comment at `ActorAuthorityTests.swift:467` reads
  "Custody was erased at the token's last declared transfer."
- **T2.** `tests/suites/witness_contract/README.md:949-962`:
  - the witnessing assertions concern the apparatus;
  - "The kernel's answers are recorded, not forced";
  - "Re-delegation is credited in the report only when …"

  This matches the key: the principal credit is reported, not enforced.
- **T3.** `tests/FAILURE-PROPAGATION-CONTRACT.md:723` credits "Independent
  attribution, raw lifecycle-observation and consumer-validation groups". It
  makes no lifecycle-claim credit.
- **T4.** `tests/suites/unit/README.md:85-95`: two rows admitted and
  seventeen refused. Nine are refused by reply admission with the decoded
  reply kept, and eight by the typed reader. The captured row's fields are
  unrelated to the request.
- **T5.** `controller/README.md:210` and the `11-policy` limits text: the
  callbacks compare the helper's inputs with the client's. No execution is
  credited.
- **T6.** `tests/suites/runner_exec_lifecycle/README.md:68-84`: the
  descendant's lifetime is recorded without a verdict, and the judgments are
  declared in `outcome_contract`.

Expected readings: T1 and T3 should disagree with or narrow their credits,
and T2, T4, T5 and T6 should agree. A reader who credits T2 with showing that
re-delegation works, or T5 with exercising the shipped helper, has over-read
the test.
