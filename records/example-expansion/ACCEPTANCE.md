# Example expansion acceptance

The implementation is ready for review and retirement. The plan and this
material remain in place at the user's request; no retirement or pruning of
this acceptance run has been performed.

## Candidate and execution

- Source: `898f3ed119edde7b79e03c7c4a41987e098149da`, a clean checkout when
  the candidate was built and the combined selection executed.
- App: `dist/PolicyWitness.app`, version 0.3.7, build 1437,
  describe `v0.3.7-103-g898f3ed1`.
- Contract:
  `development:d40fb01587e7d251cad811767e6c615829e8005625ca3584fcf69eb949461070`.
- Host: macOS 26.7.1 (25G241), Darwin 25.6.0, arm64.
- Build: one `make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`.
  The build verified seven executables and two seals, Developer ID chain,
  hardened runtime and secure timestamps. No release or notarization claim.
- Dispatcher: `20261114T161752Z_f69e47e4`, output
  `tests/out/runs/example-expansion-acceptance`.
  All 20 selected cases completed and passed, with no skip, unrun case,
  harness error or recorded system sleep. The app passed inspection and its
  inventory was unchanged after the run.

The selection was inspected with `--list` before execution, then run outside
the automation sandbox for XPC and compiler discovery:

```sh
PW_TEST_OUT_DIR=tests/out/runs/example-expansion-acceptance tests/run.sh \
  --suite unit --suite integration --suite source_drift \
  --case witness_contract/example_round_trip \
  --case witness_contract/example_round_trip_controls \
  --case witness_contract/phases \
  --case witness_contract/actor_compositions \
  --case blackbox_e2e/checker_controls
```

The result includes all ten source-drift cases, all four unit cases,
`integration/cli.integration`, and the five explicit cases. The phase and actor
composition cases ran whole on the same candidate. No ordering wait, release,
eligibility, native runner, admission or transport implementation changed;
order-barrier mutation controls were therefore not required by this change.

## Native observations

The example case retained exactly twelve command records: version once,
example twice, three workload submissions and six refusal submissions. The
emitted phased stdout was submitted unchanged. Both derivatives passed the
independent transformation checks. Each submission had its own completed
before/after same-descriptor observations of all query and attempt paths.

| Form | Submitted phase/action partition | Query outcomes | Attempt outcomes |
| --- | --- | --- | --- |
| Emitted | `initial-reads`: 2; `restricted-read`: 1 | allow, allow, deny | ok, ok, open_failed / EPERM |
| Flat | implicit `main`: 3 | allow, allow, deny | ok, ok, open_failed / EPERM |
| Actor | same 2+1 partition, `example-reader`, visits 1 and 2 | allow, allow, deny | ok, ok, open_failed / EPERM |

Each process exited 0 and each reply finished. Each form passed all thirteen
native assertions, all three prerequisite assertions and its consumer check.
Every fresh read recorded 64 bytes whose digest, count and descriptor identity
matched its own independent sample of C; before/after contents and selected
metadata were unchanged. Every phase completed with its own collected query
records and release chain. The actor applied once, received the submitted
policy digest, matched selected equipment to its launched worker, and retained
observed worker completion/reap and per-actor controller records.

The complete live report passed all 158 assertions: 107 consistency, three
execution-availability, nine prerequisite and 39 native-observation assertions.
None was unevaluated. All six refusal inputs stopped at their specified
boundaries. The side-by-side summary has no equality assertion or acceptance
credit. No native difference required an exception to the planned pins.

## Constructed sensitivity and maintenance

The complete identity-free actor fixture passed the full consumer before its
mutation matrix, then passed the three-form case's independent assertions.
It is an authored hypothetical envelope, not a relabeled native capture.
The retained fixture account defines ownership and deliberate maintenance.

The final controls case passed 372 scalar controls and 426 form controls.
These include coherent foreign partitions/actor names, borrowed collections,
missing completion/acknowledgement, wrong live-worker binding, invented
singular actor evidence, policy receipt/equipment failures, altered derivative
members, consistent and one-sided renaming, dropped/duplicated/reordered
steps, and the same wrong answer in all three forms. The fresh-read,
missing-prerequisite and combined-fault matrix runs through every form;
independent faults remain visible and missing evidence earns no native pass.
The real-file replacement/unlink observer controls remain intact. Replacing
the diagnostic formatter does not change the assertion results.

The old scalar assertion identifiers retain their meanings apart from the
ordinary-container bound, which now describes the required form. The live
emission gate specifically requires two ordinary phases with counts 2 and 1;
its preparation controls reject flat emission, swapped/collapsed phases and a
lost action. Added identifiers carry flat/actor or structure prefixes. The
scalar matrix still qualifies its authored flat model; the additional matrix
qualifies the complete phased and actor captures.

No shared observation helper was extracted: `observe_target` and the scalar
fresh-read comparisons remain owned by the example checker and reused across
its forms. The pending controlled-input plan can extract those small helpers
when it adds its caller. The independent consumer, phase and actor readers
were reused without modification. The controller retains its exact emitted
preparation-to-client test and adds held-byte/policy coverage for both
transformations. Those controlled tests establish that boundary, not native
admission.

## Public content and evidence scope

The policy bytes and all three complete action objects were compared with
the prior constant and are unchanged. The published container is now phased.
The policy source SHA-256 is
`affa3413994bae450fef3f1913975e0c6608ee356fb993be1a86e9f428e463ff`.

The authored request surface explains both collection boundaries. The probes
extraction now selects `phases[0].actions[0]`; its extracted read-hosts object
is unchanged. Contract regeneration changed the request example and its
shared copies in probes, actors, extensions, refusals, reply, envelope and
installation snapshot payloads. Inspection traced those additional movements
only to the shared request example. No shape golden, runtime rule, CLI syntax,
lesson publication or worker identity was changed. The dependency account's
three paths and accepted local availability assumptions remain applicable.

The evidence does not establish general equivalence of execution forms,
isolation among multiple actors, different actor-local/global ordinal axes,
replanning after a filesystem effect, continuous target stability, the object
a native query consulted, or a sandbox cause for EPERM. Equal allow answers
remain interchangeable under coherent associations. Native worker/API and
consumer defects can be shared. Dictionary-file availability on other supported
macOS versions, including the 26.0 floor, remains unverified and accepted as a
local prerequisite.

## Availability and completion notes

The run directory contains raw requests, commands, stdout/stderr/status,
samples, the 158-assertion report, constructed control reports, companion-case
artifacts and dispatcher integrity/sleep accounting. It is gitignored local
development evidence, disposable under ordinary retention; this record does
not pin or copy it into protected release evidence. Temporary console logs
are `/private/tmp/pw-example-expansion-build.log` and
`/private/tmp/pw-example-expansion-acceptance.log` and may disappear.

Earlier offline development runs are not acceptance: controls-1, controls-2
and controls-4 found expected-diagnostic or coverage omissions in new controls;
these were corrected before the signed candidate. The combined selection
supplies the final credit. Only this account and the associated plan's status
are added after the accepted implementation; the executable, tests, fixtures,
public surfaces and generated outputs remain exactly the accepted revision.
The affected documentation/link check is rerun after that addition.
