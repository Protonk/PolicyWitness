# Pin every example checker condition and state the workload once

Status: implemented in `c8f63bb2` and verified on signed build 1441 by
`20261114T194634Z_6b34bd1d`: all 18 selected cases passed. Review corrections in
`5e5200b5` passed the 13-case selection recorded below. Ready to begin the test
input plan's guide-design and acceptance review; this plan remains available
for retirement review. The implementation changed the
[example checker and its controls](../tests/suites/witness_contract/README.md#the-apps-own-example),
one contract-generator selector and one controller unit test. It added no
actor, action, native submission or product behavior. The
[result](#result) section holds the evidence for each criterion.

## Problem

The review of the three-form example (`898f3ed1`, build 1437) removed or
weakened one condition of the new checker code at a time, 91 times, outside
the dispatcher. 64 changes left every offline control passing. The live case
supplies only passing captures, so the controls are the only check on a
weakened condition. Four causes:

1. Each structure, actor, transformation and container assertion is one
   conjunction with one message. Its controls change several fields at once,
   so no control fails when a single condition is dropped, and a failure does
   not say which condition failed.
2. The coverage gate counts the 77-row scalar table and 17 added identifiers.
   The live report has 158 rows. 24 `flat.` and `actor.` rows have no rejected
   control in their form, and the 372 scalar controls evaluate a flat document
   through the publication path, a combination no live run uses.
3. The two-phase, 2+1 shape is restated in the container bound, the
   transformation check's indices, the role finder, the controls' builders, a
   controller unit test and the probes surface's positional member path.
4. The controls replace `checker._diagnostic`, patch `checker.os.open`, call
   `checker._one_change` and recover a row's form by parsing an identifier
   prefix.

## Changes

- **Conditions.** `bounds.ordinary_form`, both transformation rows and every
  `structure.*` row evaluate named conditions and report the names that
  failed. The checker declares the conditions of each such row for each form.
- **One evaluation, form-keyed rows.** `evaluate` is the only evaluation the
  controls and the live case call. Report rows carry `form` and an unprefixed
  `id`. The flat-with-publication path is removed. The controls' passing model
  is the phased emission with its flat and actor derivatives; a control that
  changes one capture runs in every form it applies to.
- **One workload table.** The checker states the phase partition, the role
  order, each role's query operation, attempt action, target relationships and
  native expectations once, and takes that table as a parameter. The container
  bound, role finder, transformation check, target concerns, native
  expectations and declared conditions read it.
- **Shape restatements outside the checker.** Remove the controller unit test
  that restates the constant's phases and step identifiers; the controls
  instead require the committed contract snapshot's example to satisfy the
  table offline. The contract generator's document member path accepts a
  one-member selector for an array element, and the probes surface selects the
  read-hosts action by `phase_id` and `step_id`.
- **Public seams.** The observer takes its opener as a parameter, the
  diagnostic summary is a separate public function applied after evaluation,
  and the one-change judgment is public.

The emitted document's bytes, the twelve CLI calls of the live case, every
existing assertion identifier and its meaning, and the reviewed prerequisite
and same-descriptor behavior do not change.

## Acceptance criteria

1. **Each condition has its own control.** For every form and every condition
   the checker declares there, one rejected control changes one thing and
   states the exact failing rows and, for each conditioned row, the exact
   failed conditions. The controls case fails when a declared condition has no
   matched control producing exactly that condition, and when a control names
   an undeclared one.
2. **The gate covers what the live case reports.** The required set is the
   `(form, id)` rows of the passing three-form baseline from `evaluate`. Each
   has a matched rejected control in that form. No control calls another
   evaluation entry.
3. **The shape is stated once.** A constructed 1+2 document, reply and
   derivatives pass under a 1+2 table passed to `evaluate` and fail the
   default table's container bound, with no other edit to the checker. The
   committed snapshot's example passes the bound and role finder offline. The
   removed unit test and the positional member path are gone, and the
   generator refuses a selector that matches no element or more than one.
4. **No private reach.** The controls name no underscore-prefixed checker
   attribute, replace no checker attribute and parse no identifier for its
   form.
5. **No distinction is lost.** Every prior scalar control remains under its
   name, apart from one whose name described the flat container. Each prior
   form control remains or is replaced by a stricter named control, and the
   replacements are listed in the implementing commit.
6. **The measured gap closes.** The review's 64 unnoticed changes,
   re-expressed against the new code, each fail the controls case. This is a
   scratch measurement outside the dispatcher, reported as such.
7. **The live case still passes** on one signed build made from the
   implementing commit, with twelve command records and a constant whose
   emitted bytes are unchanged.

## Verification

One signed candidate build, then one selection in a fresh `PW_TEST_OUT_DIR`:

```sh
tests/run.sh --suite unit --suite integration --suite source_drift \
  --case witness_contract/example_round_trip \
  --case witness_contract/example_round_trip_controls \
  --case blackbox_e2e/checker_controls
```

`witness_contract/phases` and `witness_contract/actor_compositions` are not
rerun unless a file they read changes; the change list in the implementing
commit supports that judgment. Regenerate the contract with
`tests/lib/python.sh docs/generate_contract_stamps.py` and review every moved
surface. A changed contract identity is a named cause for the build.

## Result

Candidate: `c8f63bb2`, `dist/PolicyWitness.app` build 1441, contract
`development:31acd293fb62d75f17231cd15b9179ea96de75a43331bbe80fedfaedd71d294e`,
signed with the Developer ID identity and a secure timestamp; no release or
notarization claim. Dispatcher run `20261114T194634Z_6b34bd1d` in
`tests/out/runs/example-controls-acceptance`: 18 of 18 cases passed (ten
`source_drift`, four `unit`, `integration/cli.integration`, both example
cases, `blackbox_e2e/checker_controls`), with no skip, unrun case, harness
error or recorded sleep, and an unchanged app inventory.

| Criterion | Evidence |
| --- | --- |
| 1. Each condition has its own control | The controls case reports 170 of 170 declared conditions pinned by a control that fails that condition alone, and fails otherwise. |
| 2. The gate covers what the live case reports | The required rows are the 158 `(form, id)` rows of the passing baseline from `evaluate`; all have a matched rejected control in their form, from 1045 control runs of 527 rows. The controls call `evaluate` and `prepare`. |
| 3. The shape is stated once | `table_one_then_two` passes a 1+2 capture under a 1+2 table and fails the default container; `committed_snapshot_example` passes `prepare`. The controller shape test is removed, the probes surface selects by `phase_id` and `step_id`, and the generator controls refuse a selector matching no element or two. |
| 4. No private reach | The two control files name no underscore-prefixed checker attribute, patch nothing and read each row's `form` member. |
| 5. No distinction is lost | 371 of 372 scalar controls keep their names; `c8f63bb2` lists the renamed one and each replaced form control. |
| 6. The measured gap closes | Outside the dispatcher, against the committed files: suppressing each of the 170 declared conditions, making each of the 158 rows unable to fail, and 48 source mutations of the remaining logic each fail the controls script. |
| 7. The live case still passes | The live report holds 158 passing rows with twelve command records; the emitted document equals the constant, whose bytes are those of `898f3ed1`. |

The contract regeneration moved no generated file. The build's development
identity did move, because it is computed from source bytes that include the
edited controller file; the commit message's statement that the identity is
unchanged is wrong on that point, and the build was required.

`witness_contract/phases` and `witness_contract/actor_compositions` were not
rerun, as a reviewed exception: the change touches the example checker, its
two control files, the contract tree reader and its controls, documentation
and one controller test module, none of which those cases read, and no
native, admission or transport source changed. Their last runs were on build
1437.

The run directories `tests/out/runs/example-controls-acceptance` and
`tests/out/runs/example-controls-rehearsal` are gitignored development output,
disposable under ordinary retention. The scratch measurement's harness and
logs were under `/private/tmp` and are not durable.

## Review corrections

The review found two preparation and control-accounting gaps. `prepare` checked
emission and workload bounds but could still write runnable derivatives after
an identity, snapshot or determinism failure. It now checks every publication
row before writing those inputs. The same `evaluate` entry has a preparation
mode that leaves run-dependent rows unevaluated; full capture evaluation keeps
independent run failures visible beside publication correspondence failures.
The controls include missing and mismatched identities, missing and changed
snapshot content, unreadable version output and differing emissions through
the actual preparation boundary.

The coverage accounting checked undeclared names only after a control earned
singleton coverage. The per-control judgment checked names only for expected,
declared rows, so conditions attached to other rows could be silently ignored.
Every stated condition now belongs to a declared row expected to fail in its
form, with no duplicates. Judgment controls require each refusal. Existing
ordinary-only worker conditions and actor-only diagnostic conditions now live
under their applicable forms instead of being silently ignored elsewhere.

The request example distinguishes an observed ordinary application from a
counted application, and the envelope example leaves operation-specific `rc`
values with their producer. The test input plan names the current three-form
baseline, concrete observer/comparison/control owners and the small extraction
still needed. It keeps its identical-content fixtures separate from example's
distinguishing-prefix prerequisites, and requires its own worker-reap and
phase-completion assertions and rejected controls. These repairs add no native
submission, action or product behavior.

### Review verification

Source `5e5200b5`, dispatcher run `20261114T234608Z_a6eb4923` in
`tests/out/runs/example-controls-review-acceptance`, against the unchanged
signed build 1441 and contract recorded above:

```sh
PW_TEST_OUT_DIR=tests/out/runs/example-controls-review-acceptance tests/run.sh \
  --suite source_drift --case blackbox_e2e/checker_controls \
  --case witness_contract/example_round_trip_controls \
  --case witness_contract/example_round_trip
```

All 13 selected cases passed: ten `source_drift` cases, the shared consumer
controls and both example cases. There were no skips, unrun cases, harness
errors or recorded sleep. The app passed inspection and its before/after
inventories are identical. The live report has 158 passing rows and twelve
command records. The controls retain 1045 matched runs covering all 158 rows
and all 170 conditions, plus 21 preparation scenarios and four judgment
controls. Preparation refuses each new correspondence fault before producing
runnable inputs; the combined-fault capture still reports every independent
failure.

No candidate rebuild was needed: the review changes no build-identity input,
and recomputing that identity gives build 1441's exact contract. The updated
checker and controls were rerun; this is not reuse of their earlier execution.
Contract regeneration changes only the two corrected examples and their
derived views; shape goldens, release history and the staged guide are
unchanged. The subsequent acceptance-note edits change only these plan
accounts, not executed code or fixtures.

The final run supersedes the two failing development rehearsals in
`example-controls-review-offline` and `example-controls-review-offline-2`:
their diagnostics exposed lost combined-fault reporting and condition lists
attached to inapplicable forms. Both are corrected; the third offline
rehearsal and final selection pass. These runs remain disposable development
output under ordinary retention, not retained release evidence.

Read-only equipment inspection on 2026-11-14 found a matching Developer ID
identity for the selected app's team, a logged-in GUI session, an empty
default runner registry with no pending cleanup, and no reconciliation
candidates or inspection errors. The source and staged guides are identical.
No external runner was installed. These mutable prerequisites must hold for
each execution of the
[full guide workflow](../tests/suites/witness_contract/README.md#guide-workflows).

## Limits

Constructed controls establish what the checker distinguishes, not what a
native producer does. The scratch measurement samples conditions chosen by
its author; the condition and row measurements are exhaustive over what the
checker declares and reports, and the 48 source mutations are not. The
consumer does not supply all of this workload's completion expectations:
example's structure rows reject an unreaped ordinary worker and an incomplete
final phase, and the
[test-input seam](../tests/suites/witness_contract/README.md#controlled-read-input)
owns those assertions for its passages. The shared consumer's scope is unchanged.
A second actor is a separate decision after this work.
