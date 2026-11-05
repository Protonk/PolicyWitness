# Historical evidence preservation and applicability

This package preserves historical observations used by the lookback acceptance.
It does not issue fresh execution credit, change a historical result, retire a
record, move active ownership, or establish present process/resource settlement.
No tests, builds, generators, pins, pruning or managed-run writes were performed
by this evidence review. Original managed runs are gitignored local evidence;
the copies below are durable record artifacts.

## Package and identification

`historical-evidence/manifest.json` identifies every copied file
by original repository path, original run ID where applicable, SHA-256, byte
count, archive name and archive member (`copy_path`). Record/source copies
without one associated run use null and retain their own internal identities.
The two gzip tar archives contain exact bytes, not regenerated summaries.
Every unique archive member was read back and its size/hash checked after
creation. Inspect a receipt without extracting ownership-shaped directories:
`tar -xOf evidence.tar.gz 'copies/tests/out/runs/doc-lookback-repairs-01/run.json'`.
Run this example from `critique/historical-evidence/`.

- `historical-evidence/evidence.tar.gz`: 6,723 unique members,
  23,579,844 compressed bytes. Deduplicated input blobs are keyed by SHA-256;
  multiple original paths can name the same archive member. The manifest maps
  each original path, rather than pretending the old receipt's relative blob
  links resolve unchanged inside this package.
- `historical-evidence/older-complementary.tar.gz`:
  2,745 members, 2,805,402 compressed bytes. Preserves the five older
  nondefault case observations listed below, including inert session/removal
  and recovery receipts.
- `historical-evidence/source-comparison.json`:
  read-only comparisons of the historical per-case source manifests with the
  checkout during this review.
- `historical-evidence/f1-existing-copy-verification.json`:
  all 17 existing F1 copies match their original bytes and saved hashes.

The package includes all eleven existing lookback run directories: seven
`doc-lookback-repairs-01` through `-07`, three `doc-lookback-docs-01` through
`-03`, and Fable's `doc-lookback-audit-drift-01`. Audit is included in eleven,
not a twelfth run. For each, all available root files preserve run/owner/plan/
dispatch/events and console/selection receipts. Audit has no root console
transcript; none was invented. The full older two pin root records, before/
after app inventories, review records and dirty-source patches are also copied.
Their source commits remain null where originally unknown.

## Observation coverage

| Historical credit | Preserved support and limits |
| --- | --- |
| I1 public refusals | Full `accepted_input_contract` artifacts: request specimens, CLI captures/envelopes, direct-XPC replies, stderr, independent `effect.json` observations and case events/report. This includes the actor parameter cases and accepted boundary. |
| I1 internal / new diagnostic rows | Both repair and documentation Swift logs; docs-01's 525-test execution and raw replay inputs/envelopes/assertions, including `transfer-readers.log`, `clock-readers.log`, and actor reader controls. Earlier 524 tests do not establish the added diagnostic assertions. |
| I2 exact-cap capture | Native case events, capture compiler diagnostics, layout/limit outputs, report and the exact `capture.c` bytes matched to the prebuild hash. Capture assertions are silent on success: no per-assertion runtime trace existed. Preserved source assertions plus the case's capture step/result support constructed readable 1 MiB capture and cap-plus-one refusal, not compilation/application of a 1 MiB policy. |
| I3 six fallback scenarios | Original Cargo test output, case events/report, prepared source bytes, prebuild patch/hash record and fallback review. The test prints one aggregate test name, not six separate runtime traces; the six scenarios are established by the executed test source and passing test result. It remains a dependency-seam observation, not a live-helper observation. |
| Documentation fail/pass | Docs-01/02/03 and audit case reports, raw launch stdout/stderr, parent receipts and initial command source inventories/blobs. Citation failure stays a failure. Available earlier source records, documentation patches and final acceptance identity records are copied. |
| Build 1121 | Original build console, repair/docs app-integrity inventories, verification/prebuild identity records and saved patches. The archive retains the provenance in those records; it does not relabel the build as current HEAD or substitute a later build's embedded provenance. |
| Four nondefault controls | Raw baseline/mutation logs, result/command/build receipts, saved Swift/C inputs and mutation sources for exec/reaped/handoff controls; native-clock raw 27 observation rows, assertion log, platform/toolchain, installed-clock disassembly and deny-log output/status. |

F1's final two failed observations remain in the existing
`../implementation/setup-flake-evidence/manifest.json`
package, verified rather than duplicated. Root records for all seven repair
runs retain their historical pass/failure accounting. Intermediate F1 fixture
trees were not copied wholesale. No current F1 acceptance claim depends on
those intermediate trees replacing the retained final diagnostic observations.

## Source applicability and recommendation

The historical sources are not inferred from today's HEAD. Preparation hashes,
existing snapshots/patches and saved per-case sources are the identity basis.
The changed prepared source files matched their old hashes when copied; later
parallel Rust test edits are new work, not changes to these copied bytes.
Documentation applicability exceptions from the acceptance record remain
historical judgments. New Rust assertions need new execution.

| Nondefault case | Comparison and recommendation |
| --- | --- |
| `runner_unit/exec_reader_mutations` | 88 saved source entries compared with repository paths mapped from fixture/native copy locations. All match except the deliberately generated `main.swift` and `LimitsContractTests.swift`. The generated main calls exec observations; the changed Limits test body is compiled but not called by that main. This is a narrowly reviewed changed-input exception for the observation, not a proof that all harness dependencies are unchanged. Historical wrapper/shared-helper identity is not completely recorded. Rerun for unqualified current credit. |
| `runner_unit/reaped_ack_mutation` | 49 saved entries match after path mapping except deliberately generated `main.swift`, whose retained text calls the reaped-acknowledgment controls. Historical wrapper/shared-helper identity is not completely recorded. Rerun for unqualified current credit. |
| `runner_unit/actor_handoff_mutations` | All 51 manifest entries match current source, including the case Python/shell and selected fixture/native/Swift inputs. This is the strongest identity basis, but the manifest is not an exhaustive record of shared dispatcher/equipment dependencies. Its raw baseline/three designated mutation observations are preserved. A fresh complementary run is reasonable alongside the other three. |
| `runner_c_worker_harness/native_clock` | Raw machine-specific observations are preserved, including 36,000,000 usable continuous-clock samples, 27 fresh processes, observed old-clock failures, and available deny records. No complete historical source hash set for shell/C/shared helpers was retained in this case itself. Rerun for current credit; do not generalize either historical or new results to all machines/OS builds. |

These recommendations distinguish missing dependency provenance from an observed
implementation failure. Hash equality on the covered files does not establish
complete dependency coverage or reachability.

## Older pins and pruning dependence

`actor-passes-default-02` records 215/216 passes and the old limits-owner-list
failure; `actor-passes-final-controls-02` records ten passes including its
replacement credit. Their retained review/source records preserve the dirty
build-1116 provenance and selected red/protocol-fixture observations. A fresh
216-case default battery can replace current default-case credit only when it
has completed and been reviewed; the planned count alone is not replacement.

Six final-controls cases are outside the present default catalog:
`runner_unit/actor_handoff_mutations`, `witness_contract/order_barrier_mutations`,
`witness_contract/extensions_byoxpc`, `witness_contract/actors_byoxpc`,
`runner_byoxpc/reservation_controls`, and `runner_byoxpc/registry_recovery`.
A four-case new complementary run replaces only the first of these six.
The other five now have their available raw text observations, independent
assertions, inventories, commands and session/cleanup receipts copied in
`older-complementary.tar.gz`. Current lookback credit can therefore cite these
inert observations without depending on those raw receipts remaining in a
prunable managed directory, subject to an explicit applicability judgment if
current credit is claimed. Copies do not resolve any outstanding active cleanup
ownership; original records remain authoritative for that purpose.

No pin was removed. Retiring either older pin still requires the coordinator's
explicit accounting of replacement credit, any remaining source/applicability
uncertainty and live recovery obligations. This package is not permission to
prune and is not a complete portable replay of every historical default case.

## Omitted inputs and remaining limits

The manifest lists omitted files with original identities/hashes/size when
available. Compiled fixture executables, staged app bundles and binary equipment
are omitted: raw observations, source snapshots and inventories are retained.
They would require rebuilding/reinstalling from an established source/toolchain
for replay; no claim is made that binary hashes alone reconstruct them.
Repeated later per-command input inventories and mutation-input blobs from
source-drift runs are omitted after retaining initial inventories/source blobs,
raw launch output and parent receipts. Consequently some historical receipt
links intentionally resolve only in the original managed tree. The archive
manifest identifies the preserved subset; it is not a self-contained runnable
fixture worktree. All copied bytes and omissions are identified rather than
silently presenting a partial tree as complete.

Build-console and inventory evidence do not fill gaps in a historical exact
source snapshot. No source identity was assigned from the commit that happened
to add a retention entry. I2 and I3 have the runtime granularity limits stated
above. Fresh default/complementary verification is the coordinator's separate
work and must be preserved/credited separately.
