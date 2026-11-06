# Plan: one bounded footprint reduction

## Result and boundary

Reduce avoidable controller allocation work while preserving the exact envelope
contract. Start from [LIMITS](LIMITS.md) and [FOOTPRINT](FOOTPRINT.md), especially fr8, and deliver one small
change with a matched before/after account. Do not combine it with worker wait,
shared-memory layout, authority custody, wire-version or generator refactoring.

The first candidate is [`sort_value`](../controller/src/json_contract.rs). It clones
each object's keys and subtrees into a temporary vector, recursively sorts those
copies, and replaces the old map. The input, old map, copied descendants and
later envelope representations overlap. Rebuilding from owned entries can remove
the subtree copies while keeping the same recursive traversal and final key
ordering. The inspected [Cargo configuration](../controller/Cargo.toml) enables no `serde_json`
`preserve_order` feature; its lockfile selects 1.0.147 without `indexmap`, and
the signed build supplies no feature override. The current map therefore uses
sorted `BTreeMap` storage. Keep explicit sorting for this first change rather
than coupling it to removal of the recursive traversal: take the old map with
`std::mem::take`, collect its owned entries, sort them and recursively rebuild
the map. This removes key/subtree cloning while preserving ordering even if
map features later change. Reconfirm the dependency configuration at execution.

The [deferred candidates](../records/FOOTPRINT-OUTFLOW.md) retain the wider
investigation. Only the first candidate is in this plan.

## Execution

1. Preserve a signed baseline and record its exact binaries, source and build
   provenance. Run the response footprint case with its dependencies. Preserve
   host bytes, client stdout, rendered envelope bytes, internal scalar receipt,
   verified sample intervals and observer cost. Use the same ordinary, phase-pair
   and actor workloads for the candidate.
2. Make only the ownership change in `sort_value`. Keep its public behavior,
   failure mapping, key ordering and all evidence fields unchanged. Retain the
   test-only scalar seam at the same boundaries; do not change the consumer to
   conceal a failing observation.
3. Establish exact rendering equivalence for nested objects and arrays, escaped
   strings and envelope-shaped inputs. `envelope_keys_are_sorted` covers one
   nested object; shape checks do not establish exact bytes or array ordering.
   Add a compact expected-byte check for a fixed nested Value containing arrays
   and escaping, passed through `sort_value` and the existing pretty serializer.
   Keep timestamps/build metadata fixed in that fixture; live envelope bytes
   cannot be equal across runs because their evidence and build stamps differ.
   Existing envelope tests still establish the public assembly path. Regenerate
   identity inputs only if covered inputs changed, and build the candidate
   through the signed pipeline.
4. Through `tests/run.sh` in fresh managed output, select `--suite unit`,
   `--suite integration`, `--case witness_contract/response_footprint` and
   `--suite source_drift`; the response case declares its observer, receipt,
   unit and ABI dependencies. Then run the default battery separately. This
   ownership-only change does not alter admission; broaden to coordinated
   admission/consumer verification if implementation crosses that boundary.
   Compare source-established eliminated copies and the actual native samples
   separately. Sampling does not locate an instantaneous peak or attribute a
   sample to sorting. Eliminated subtree copies are a source-established gain;
   no lower sampled maximum is required to establish that narrower result.
   Report unchanged/noisy native results honestly. If repeated matched samples
   suggest a material regression, investigate before accepting the change;
   retain negative results rather than expanding scope to obtain a win.
5. Update fr8 and its diagram to describe the resulting mechanism. Keep measured
   observations tied to the candidate and conditions. Commit the implementation,
   tests and documentation together; retain current default and complementary
   evidence within the normal retention policy, then retire this plan and its
   temporary acceptance records.

## Invariants and stop conditions

Preserve fresh processes, host/worker separation, prediction-before-attempt
ordering, exact witness evidence and honest attribution. This change must not
alter request admission, retention limits, malformed-output diagnostics,
authority transport or native call semantics. Stop for a correctness regression,
changed wire bytes outside established dynamic fields, missing required native
observations, unresolved cleanup or evidence that ownership changes require a
larger architectural change.

A later paced-worker-wait experiment may offer a larger reduction in sustained
CPU demand, but it crosses collection, activation, expiry, cancellation and
authority-service boundaries. It needs its own bounded change and the existing
barrier/activation/expiry controls. A held-worker CPU delta can still exceed a
sleeping control after pacing; that assertion is not a universal optimization
detector. Right-sized evidence regions and custody allocation changes remain
separate ABI/lifetime work.

## Coordination

One Sol implementer and one independent Astra reviewer are sufficient. The coordinator
serializes builds and native runs, limits compiler concurrency, and requests a
quiet interval only when the chosen comparison needs one. No scheduled approval
pause is required; unresolved blockers stop dependent work.
