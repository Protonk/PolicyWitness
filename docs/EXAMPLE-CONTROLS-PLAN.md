# Pin every example checker condition and state the workload once

Status: accepted for implementation by the maintainer on 2026-11-14; not yet
implemented. It changes the
[example checker and its controls](../tests/suites/witness_contract/README.md#the-apps-own-example),
one contract-generator selector and one controller unit test. It adds no
actor, action, native submission or product behavior.

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
- **Public seams.** The observer takes an after-open callback, the diagnostic
  summary is a separate public function applied after evaluation, and the
  one-change judgment is public.

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
   name. Each prior form control remains or is replaced by a stricter named
   control, and the replacement is listed in the implementing commit.
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

## Limits

Constructed controls establish what the checker distinguishes, not what a
native producer does. The scratch measurement samples conditions chosen by
its author. The consumer's acceptance of an unreaped ordinary worker and of
an incomplete final phase, the request surface's "applied once" sentence and
the envelope surface's failed-open `rc` stay as the review reported them. A
second actor is a separate decision after this work.
