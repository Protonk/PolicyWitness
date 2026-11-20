# P4 adjudication: test-only reading

**Run.** Workflow `wf_62eae7ce-94a`, 2026-11-20, at `2bcdfeb8`. Four readers
ran as `Explore` agents: three Sonnet and one Opus control. Every reader
reported opening only `inputs/`. Raw answers are in `answers.json`; the key
is in `KEY.md`.

## Result by test

**T1, custody assertion.** 4/4 found that the final `erased` assertion
cannot show erasure at the token's last declared transfer, which is the key's
reading (DT-63.a, DT-124.g; Pass 3 repairs the comment). 4/4 also found
something the key had wrong: the consume native results are never asserted.
A consume that returns -1 passes as long as its release reports code 2. The
key's "fails on" line overstated the test, and its correction is recorded
below.

One Sonnet reader noted that `bCompletedAtPhase0End` is read when phase 1
begins. The comment ("when its phase arrived") is accurate; the variable
name is not. That is a weak lead with no entry.

**T2, re-delegation checker.** 4/4 matched the key and the narrowed suite
account: apparatus and calibration are enforced, while the principal credit
and the two weakened-policy contrasts are recorded only. One Sonnet reader
added that the two omission contrasts assert the checker's own credit logic
over links removed by construction. That fits the account's "structural
assertions", so there is no action.

**T3, pre-apply failure checker.** The readers named limits around
application and compilation evidence, which the checker does not claim to
observe directly. None could see that the lifecycle oracle exists, so none
could name its absence. That is a constraint of the view, already covered by
DT-53.g in Pass 3.

**T4, the label-admission test, Pass 3 entry.** 4/4, including the Opus
control, read the test's name
(`compiled_profile_status_and_labels_alone_decide_run_admission`) and its
opening comment ("reads a receipt's status and its two labels and nothing
else") as claiming more than the test shows. A fixed nineteen-row corpus
never varies the other receipt fields while holding status and labels fixed.
It shows only that the one admitted `captured` row's unrelated nonce, source
and parameter fields were not compared.

The rule itself holds by source: `porcelain_admission.rs`
`admission_problem` reads `status`, `producer` and `capture_stage`. The unit
README's credit is accurate. The overclaim is in the test's own name and
comment.

Entry for Pass 3:
- Preferred: strengthen the test. Derive variants of the admitted
  `captured` row that change each non-label field, with status and labels
  fixed, and assert that each is still admitted. Keep a rejected neighbour
  with a changed label.
- Otherwise: narrow the name and comment to what the test shows. A rename
  must also update the check citation in `35-profile.surface.md` and
  regenerate.

**T5, held-request fallback test.** 4/4 matched the key: the client and
helper are stubs, and the test's own comment disclaims the shipped binaries.
The Opus control added a subtlety. The test detects a reread file only
because production calls the helper after the client returns, and it does
not assert that order. In production the order is structural, since
eligibility needs the client's result, so the credit "rejects a reread file"
holds. Weak lead; no entry.

**T6, survivor checker.** 4/4, including Opus, concluded that the checker
lets the case pass on an unfavorable `truthful_exec_account` or
`later_step_effect` judgment. At the checker level that is literally true:
it emits the judgments, and their enforced authority lives in the catalog's
`outcome_contract`, outside the view. Under that authority the dispatcher
fails the case; the overhaul plan's survivor controls showed this on a wrong
reply expectation. The suite README states the binding. The constraint
caused the reading; no account defect.

## Key correction

Recorded after the run; the key is otherwise unchanged. T1's "fails on"
should read: misbehaving transfers, deliveries, acceptance timing or
consume/release lifecycle codes, or custody not marked erased at all. A
consume's native result is not constrained.

## Destinations

- Pass 3 entry: T4.
- Weak, no entry: T1's variable name; T5's call order.
- Pass 4 entries: none.
- User-duty draft: none.
