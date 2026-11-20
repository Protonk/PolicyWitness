# P3 ground truth: restatement comparison

Each reader sees one owner file and lists every claim it makes about one
named rule. The coordinator compares the lists with each other and with the
rule as the code implements it, given below. Owner files are chosen after
Pass 2 lands, with at most eight readers in all.

## Rule A: automatic policy compilation after a lost reply (fallback) and the presence of `policy_check`

- **Where it runs.** `controller/src/run_flow.rs:822-836`, on the branch
  with no admitted host reply. R11 (`b3c89046`) deleted the calls on the
  admitted-reply branch.
- **Eligibility.** `runner_client.rs:651-660`. All three must hold:
  transport admission `accepted`; no request-delivery error; client
  transport terminal `xpc_error`.
- **Request without an `actors` array.** The standalone helper compiles the
  held request serialization, and its capture goes in `data.policy_check`.
  If the capture is not eligible, there is no capture.
- **Request with an `actors` array.** Each actor carrying a resolved policy
  object is compiled separately (`{"policy": …}`), and the captures go in
  `actor_policy_checks` in request order. There is no whole-request
  compilation, so `policy_check` is null (R10).
- **Failures.** A helper launch or delivery failure records an `unavailable`
  capture. The runner reply is never changed.
- **Limits.**
  - Eligibility establishes neither worker progress nor the cause of the
    lost reply.
  - A fallback capture never shares an envelope with an admitted host
    reply.
  - The capture is an independent compilation, not evidence about the
    host's run.

## Rule B: derivation of `cleanup_trigger`

- **Where it is derived.** At final collection, from the poll stop reason,
  through `PWDisposition.triggerForStop` (`PWRunnerDisposition.swift:21-25`).
  It is a derivation, not a second observation.
- **Ordinary mappings.**

  | Poll stop reason | Trigger |
  | --- | --- |
  | `sentinel_deadline` | `deadline_expiry` |
  | `done` | `completion` |
  | `child_reaped` | `child_reaped` |
  | `wait_error` | `poll_wait_error` |
  | `policy_write_error` | `policy_transfer_error` |
  | `policy_transfer_deadline` | `policy_transfer_timeout` |

- **Actor additions** (R13): `schedule_complete`, `ended_before_arrival` and
  `ended_before_completion` all map to `completion`.
- **Other actor stop reasons pass through unchanged**
  (`ActorSession.swift:626`, `?? pollStopReason`). Examples: `setup_timeout`,
  `died_before_completion`, `authority_setup_failed`.
- **Termination cause of a host kill** follows from the trigger
  (`causeForTrigger`, `:34-36`):

  | Trigger | Termination cause |
  | --- | --- |
  | `deadline_expiry` | `host_sentinel_deadline` |
  | `completion` | `host_exit_grace_exhausted` |
  | `poll_wait_error` | `host_cleanup_after_wait_error` |
  | `policy_transfer_error` | `host_cleanup_after_transfer_error` |
  | `policy_transfer_timeout` | `host_cleanup_after_transfer_timeout` |

  Any other trigger has no mapped cause.
- **Where the ordinary mapping is confirmed.** In the observed envelopes: E1
  (`done` → `completion`) and E8 (`sentinel_deadline` → `deadline_expiry`).
  The source line that assigns the ordinary trigger was not pinned for this
  key.

## Rule C: what `order: query_first` establishes

`31-steps.surface.md` "Establish query order"; production
`eligibleOrderedStep`, `buildOrdering`. A step gets `query_first` only when
all of these hold:

1. **The phase's collection chain.** Collection was closed before proceed;
   proceed was set and observed; the worker's lifetime was established; and
   there were no protocol violations.
2. **Setup.**
   - Ordinary execution: successful application was observed.
   - Actor execution: the actor's declared applied or unapplied setup was
     established.
3. **A native answer.** The record came from the validator, with `native_rc`
   and `errno` present, `rc == native_rc`, and the outcome consistent with
   the native return.
4. **Unique association.** Exactly one validator record carries the step's
   identifier bytes, and its retained query identity matches.

Meaning: this eligible prediction was collected before the phase's attempt
batch was released. It does not mean prediction and enforcement agree, that
the prediction caused or explains the attempt, or that the prediction is
correct. Root `AGENTS.md` calls this "the limited meaning of `query_first`".

## Rule dropped: the `captured` receipt

Rule C was first the meaning of a `captured` receipt. Only
`35-profile.surface.md` states that rule (`RESPONSE.md` is rendered from it),
so there are no restatements to compare. That single ownership is itself a
result of this probe, and P1's E6 and E7 still test how readers take the
rule.

## Owners

Eight readers, one owner file each:

| Rule | Owner file |
| --- | --- |
| A | `docs/contract/11-policy.surface.md` |
| A | `docs/contract/40-envelope.surface.md` |
| A | `controller/README.md` |
| B | `docs/contract/32-lifecycle.surface.md` |
| B | `docs/contract/41-diagnostics.surface.md` |
| B | `tests/FAILURE-PROPAGATION-CONTRACT.md` |
| C | `docs/contract/31-steps.surface.md` |
| C | `docs/QUESTIONS.md` |
