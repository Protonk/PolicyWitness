# Release-stamped contracts: review checkpoint

The implementation and documentation reviews are complete. The full build-refusal
rehearsal passes, including its tagged default battery. The user authorized
preparation of v0.3.6 with supplied release notes, stopping before publication.
The actual release archive still requires its own notarization and acceptance.

## Documentation and test review corrections

All 28 findings from the documentation/test sweep were accepted. CLI help and
CLI structure were unchanged. Corrections cover quick-start contract binding;
producer admission and external-runner reinstall guidance; architecture wording;
content identity versus Git state; a single cutover commit containing stamps and
implementation; normative failure/reader accounts; test ownership citations;
corpus lessons, mutation types, labels and emitted evidence; and source comments.

The stamp collector now includes the complete binary decoder identity and the
reservation limits with their counting, effects and controls. Independent tag,
integer-width and limit mutations check the affected surface stamps. Uniform
generator controls repeat the unchanged command before their corruption control
and compare both bytes and modification times. The citation account explicitly
distinguishes suite ownership in the surface manifest from defined assertion
citations in the architecture/build/limits/footprint manifests.

The compiled-profile test now names its actual status/producer/stage validation;
it does not claim enclosing producer admission. The circular producer-constant
assertion was removed from the C-worker step test. Whole-reply producer admission
and independent binary-producer assertions remain in their owning tests.

Signed build 25 is the current candidate
([build log](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/signed-build-25.log)); the two corrected Rust source comments
change its digest because scoped files are hashed in full. The product behavior
and worker identity were not changed by this sweep.

- Contract: `development:e37abc6752da4ca3384fb3ccddec3b60844502440ece2b6cd8bc5407d1a4d7ef`.
- Controller SHA-256: `61ce919e1c82cb3b850ce72ef894f5629a2ffe5914d8543c96219763d9b08805`.
- Worker identity: `4be1acb4ec613d47ce43e8490eda14166a3e0ad550326124f46efa281f5127a1`.

Focused [run 26](../tests/out/runs/release-contracts-doc-review-26/run.json)
selected 24 cases: 23 passed and the generator-contract case failed when its
new helper import was loaded in isolation. The import now locates its helper
beside the generator; [run 27](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/run.json)
passes that complete case, including idempotence and isolated imports. The
original failure remains recorded. Across the two runs, all 24 distinct selected
cases have passing results, with no system sleep, skips or unrun cases.

Coverage comprises the full source-drift suite, all four Rust unit selections,
601/601 native core tests and independent binary/actor/lifecycle reader replays,
blackbox checks, sysctl checker controls, CLI/direct-XPC request corpus,
pre-apply evidence and reservation controls. The app passed artifact inspection
and remained unchanged. The [candidate receipt](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/candidate.json)
records source/plist/Swift-context/equipment/binary identity agreement. Final
runner list and reconcile receipts alongside it show no registrations, pending
cleanup, candidates or inspection errors; all ten reservation ownership receipts
record removal without cleanup errors.

The corrected isolated import affects documentation machinery only and leaves
the public source digest unchanged. Runs 26 and 27 selected no full battery;
the later full rehearsal is recorded under Review boundary below. Prior
build-22 runs supply no live result for this rebuilt candidate.

## Prior independent review and repair checkpoint

The independent review rejected readiness for the final battery. It found
missing-history stamp failures, incidental files in the digest, index-hidden
release edits, registry key collisions and metadata loss, incomplete surface
ownership, and test migration/control gaps. Runs 14 and 15 recorded that
review's failures; their terminal receipts are preserved in the current
checkpoint's superseded-receipt copies. Earlier live runs are not credited to
the new candidate.

The fixes now in the working tree:

- Source discovery uses declared language/resource suffixes and explicit build
  helpers, including the local Evidence imports. Actual scoped bytes and path
  membership must match the annotated tag for a release identity. Swift context
  generation compares its result with the identity exported by the build.
- Source copies and no-tags clones still check current inputs and table
  agreement, explicitly report incomplete derivation, and cannot erase stamped
  tables through regeneration. Release preflight requires history and the exact
  release contract before notarization.
- Cleanup entries nest the retained runner beside cleanup state. Historical
  flattened entries remain readable; their known top-level identity takes
  precedence over an opaque `runner` key. Unknown nested ownership, signature
  and entitlements metadata survives. Saves require a lossless read-back before
  atomic publication.
- Surface inputs distinguish policy, probes, actors, selectors, registry/command
  records and transport/reservation. They include delimited field definitions
  and examples in the guide. Refusal codes belong to the refusal region.
- Constructed readers require an explicit expected identity. Instrumented hosts
  carry an explicit candidate context. Removed markers, default-runner coverage,
  precise admission/producer assertions and the ABI comparator control are
  migrated or restored. Archive acceptance checks both the plist and the
  extracted binary's reported release identity.

Signed build 22 was the preceding candidate
([retained build log](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/prior-24/review-checkpoint/signed-build-22.log)):

- Contract: `development:73d1e3508c7c7ebfd31e8c50e5433b0c354562f0135bd7ef7703a9a66a4ae6c7`.
- Controller SHA-256: `54940cc658b91543b3429ced7c62e152be1d62b5411469bb3e24ec3c0986e372`.
- Worker identity: `4be1acb4ec613d47ce43e8490eda14166a3e0ad550326124f46efa281f5127a1`.

The comparison baseline is annotated `v0.3.5`, commit
`dcc843b8835ac9154151f9567543dc8b754c2407`. The intended first release of the
cutover is `v0.3.6`. All 13 surface stamps were `unreleased` at the development checkpoints; the
[release procedure](../docs/SIGNING.md#release-procedure) renders them for
v0.3.6 in the cutover commit and checks reproduction after tagging.
The candidate was built from the uncommitted working tree at
`e7a9d0d3b8ce358c05d696c5e8ffcaac7a6fa004`; that commit alone does not identify
these sources.

## Review map

- [Build identity](../docs/build_contract.py), [shared source walker](../docs/source_identity.py),
  [build plumbing](../build.sh), and [native configuration](../meson.build):
  clean annotated releases emit a release identity; other builds emit a source
  digest. The scope includes service plists, entitlements, augments and the two
  Python entrypoints and their local imports that create shipped inventory/evidence, because they affect
  shipped behavior or output. Standalone test and documentation files outside the declared scope do not
  enter the digest; embedded tests and comments inside scoped files do. A pre-signing recomputation refuses changed source inputs.
- [Request admission](../controller/src/request_patch.rs) and
  [direct-XPC decoding](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift):
  exact required `contract` before selectors, augments and descendants.
  Independently arriving envelopes, host replies and client captures each carry
  producer context. Unsupported received bytes remain raw.
- [Runner management](../controller/src/runner_manager.rs) and
  [reservation](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift):
  plist, registry and live peer checks use the same identity. Legacy records
  retain ownership and recovery paths without being executable.
- [Surface scope](../docs/contract_surfaces.json),
  [generator](../docs/generate_contract_stamps.py), and
  [normative definitions](../docs/CONTRACT.md): deterministic stamps derive from
  reviewed shape goldens, examples and delimited text. Request keys are collected
  from closed CodingKeys, including their JSON aliases. Unknown verification
  owners and stale collected goldens are refused.
- [Test context helper](../tests/lib/build_context.py): authored requests remain
  identity-free; submission reads the candidate plist independently. Constructed
  readers receive explicit test contexts. Historical captures remain unchanged.

The four public counters and nested compiled-profile counter, their manifest,
generator and bump classifier are removed. Internal registry, provenance,
validator and harness format counters remain. Worker layout, wait/release stores
and eligibility rules are unchanged; its source identity is regenerated.

## Prior targeted verification (build 22)

These prior targeted selections recorded 160 distinct passing case results,
not default-battery acceptance. Selected terminal, inventory, observation and
cleanup receipts survive as identified copies; the complete prior runs were
retired after the rebuilt candidate's focused verification. The copies are
historical evidence only. Current runs 26 and 27 are the two non-release pins.
Evidence under `tests/out/runs/` is gitignored and available only in this checkout.

| Run | Result and scope |
| --- | --- |
| [targeted-23](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/prior-23/run.json) | 145 selected: 140 passed, 4 failed, 1 unrun. The app passed inspection and remained unchanged. Prior native, admission, worker, witness and registry-recovery observations were recorded; the four failures and their dependent unrun case require the replacements below. |
| [controls-24](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/prior-24/run.json) | 23 selected: 22 passed, 1 failed, none unrun. All four run-23 failures and its dependent footprint case have passing replacements. Release controls, Rust unit selections, blackbox readers and sysctl reader controls pass. The build-refusal failure is detailed below. App inspection passed and the app remained unchanged. |

Run 23 passed the native core executable's 601 assertions and independent
binary, actor and lifecycle replays; all seven default runner-unit cases;
C/Swift ABI agreement; default C-worker harness cases; failure boundaries;
default runner selection and caller authentication; both default exec-inheritance
cases; and the affected witness selection apart from the footprint dependency.
The opt-in order-barrier mutation, BYOXPC dossier/actor, porcelain-output,
same-shape two-build admission/effect and registry-recovery cases also passed.
The registry control exercises opaque cleanup-key collisions and nested metadata
preservation, then verifies absence of owned services and plists. All ten
reservation-control ownership receipts record removal and no cleanup errors.

Run 23's failures remain failures in the original evidence:

| Case | Correction verified in run 24 |
| --- | --- |
| `source_drift/generator_contract` | The synthetic release repository now includes the full declared identity input set required by release preflight. |
| `runner_outcome_bad_request/accepted_input_contract` | Removed an assertion accidentally duplicated into the unrelated corpus loop; the direct-XPC control retains exact code, path and expected-contract checks. |
| `witness_contract/response_footprint_controls` | The constructed enclosing client receipt accounts for the larger producer-bearing host frame. The dependent `response_footprint` measurement is selected again. |
| `runner_byoxpc/reservation_controls` | Removed an inaccurate human-prose-prefix expectation; exact `unsupported_runner_response` classification, foreign raw producer, null semantic result and no-replay/effect assertions remain. |

The product inputs and signed app did not change after build 22. Subsequent
test changes are limited to those replacement cases, the constructed-versus-live
context choice in `unavailable_prediction.py`, and stricter release preflight
with its synthetic repository controls. Run 24 selects their affected owners.
The later build-refusal/rehearsal corrections below remain unverified by their
complete case. Passing run-23 observations are reused with that explicit dependency judgment;
a matching app identity alone would not establish test-helper applicability.

All seven generator `--check` commands pass, including
`generate_contract_stamps.py --check --require-history`. Direct source
recomputation agrees with build 22. The scoped input audit excludes the ignored
validator executable, an unused standalone build script and the augment README.
`git diff --check` is clean. The
[final candidate receipt](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/prior-24/review-checkpoint/candidate.json)
records the 105 scoped input hashes and agreement among recomputation, both
plists, generated Swift context, equipment inventory and `--version`. Final
`runner list` and `runner reconcile` receipts alongside it show an empty registry,
no pending cleanup, no candidates and no inspection errors.

## Earlier deferred build-refusal checkpoint

`preflight/build_refusal_controls` passed the full-build controls through output
architecture validation, then failed its stale-worker-identity assertion. Its
post-compile edit now triggers the earlier public-contract guard, correctly
refusing before signing. The test now changes the worker generator's own bytes,
outside the public identity scope, to reach the worker-specific guard.

Inspection also found two release-rehearsal migrations: the make-entrypoint
fixture needs the declared identity/stamp inputs and a prepared stamp table;
the real-archive rehearsal needs a clean annotated synthetic release and must
forward the extracted binary's new `--version` acceptance check. Those fixtures
are corrected and syntax checked. Their complete case has not been rerun.

That case includes a real full default battery inside `control_release_battery`.
It never reached that sequence in run 24. The user's requested pause before a
full battery therefore applies to this rerun too. No full battery, including a
nested rehearsal, ran during this repair checkpoint. This is an explicit
remaining validation item, not a passing control or release acceptance.

## Superseded evidence

The independent review's runs 14 and 15 rejected the earlier candidate.
Its contract `development:8930016ec238d1d832edf48bbac7e4b466fe7d28d210b5769fb8e789e900c67f`
included an ignored executable; agreement inside that checkout did not establish
clean-copy reproducibility. None of its live results is credited to build 22.
Earlier repair runs 16–21 established intermediate controls and are superseded
by the retained targeted selections. Build 19 failed at a Rust const-expression
compile check; build 20 succeeded but preceded the final registry ambiguity fix.

The failed run-09 plain-SwiftPM worktree was never executed and was removed
under the checkout lock, with an appended recovery receipt. Successful
same-shape runs removed their owned worktrees. Earlier reservation ownership
receipts record removal with no cleanup errors. Superseded completed output is
retired through the repository pruner after replacement evidence and selected
receipts were retained. Runs 23 and 24 were subsequently retired in favor of
current runs 26 and 27.
[Superseded receipt copies](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/prior-24/review-checkpoint/superseded-receipts.json)
preserve the older terminal identities, hashes and cleanup receipts.
[The latest retirement receipt](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/prior-27/review-checkpoint/retired-receipts.json)
identifies the selected run-23/24 copies. These copies do not
relocate ownership or supply missing observations. The v0.3.5 release pin is
unchanged.

## Review boundary

The user completed review and authorized v0.3.6 release preparation with supplied
release notes, stopping before `make publish`. The remaining rehearsal runs
before the single cutover commit and annotated tag. The actual released archive
then receives its own default battery through `make release`; development and
synthetic-release evidence do not replace that acceptance.

Run 28 passed both refusal variants but stopped in the fresh-build sequence:
three assertions still expected `meson configure` instead of
`meson setup --reconfigure`. Its unchanged toolchain stamp and command receipts
established a stale test expectation. The assertions now require the exact
reconfiguration invocation.

Run 29 passed both refusal variants and all eleven pre-battery sequences. Its
tagged `release:v0.0.0` rehearsal completed the default selection with 221 passing
cases, five failures, three cases without terminal reports, and no sleep overlap.
The extracted app was valid and unchanged. The failures exposed remaining test
migrations: a surface-manifest mutation fixture needed its own annotated history;
the opt-in group omitted the same-shape control; three inline readers omitted
the expected contract; the allow/deny template lacked assertion injection; and
mutations of live isolation captures used the generic constructed identity.
The worker-wait stager identity control also assumed its checkout was outside a
temporary root. That constructed control now isolates identity admission with
an explicit path-classification stand-in and still stops before worker
substitution or signing; it makes no staging-path admission claim.

Run 30 (`20261109T200421Z_53a8ab0a`) passed all ten replacement and shared-checker
cases with no skips, unrun cases, sleep overlap or app changes. These repairs
change tests only.

[Run 31](../tests/out/runs/release-contracts-release-preflight-31/run.json)
(`20261109T200553Z_d5eadc66`) passes the complete build-refusal case: 88
controls and sequences and all 16 guard-bypass demonstrations. Its
[tagged rehearsal battery](../tests/out/runs/release-contracts-release-preflight-31/suites/preflight/build_refusal_controls/artifacts/release-battery/acceptance/tests/run.json)
(`20261109T204452Z_37b840c0`) passes all 229 default cases, with no skips,
unrun cases, harness errors, sleep overlap or app changes. The rehearsal uses
`release:v0.0.0` and controlled Apple responses; it does not establish actual
notarization or acceptance of v0.3.6.

The retained pins are the complementary run 26 and complete rehearsal run 31.
Run 31's [receipt-copy manifest](../tests/out/runs/release-contracts-release-preflight-31/review-checkpoint/copied-receipts.json)
identifies original paths and hashes for the complete prior checkpoint, run 28,
run 30, selected run-29 failures and terminal summaries, and console transcripts.
The original failed outcomes remain unchanged. These copies do not relocate
active resource ownership or establish process settlement. Release-managed
retention is handled by the release archive's rotation transaction.
