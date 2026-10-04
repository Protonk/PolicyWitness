# preflight

Read-only artifact inspection, with opt-in controls using real signatures.
Offline release controls also exercise the release procedure's decision points.

## Invariants

- Requires expected executables/resources, valid strict signatures for the app,
  service, and helpers, and matching hashes for every manifest entry. Required
  helper entries cannot silently disappear from the manifest.
- Runs `nm -u` on the shipped `PWRunner` executable and rejects any undefined
  `_sandbox_*` symbol. This sees linked imports; it does not detect dynamic
  symbol lookup. The [host-source check](../source_drift/README.md) covers
  literal lookup/load forms. Worker and validator native imports are expected.
- Never executes `policy-witness` or the runner.
- The shared `tests/lib/artifact.py` inspector also gates app-dependent selections
  in the public dispatcher. It never repairs a failed artifact.

## Success criteria

- `codesign.preflight` succeeds only when the inspector reports no errors.
- `signed_artifact_controls` copies the selected app to `/private/tmp`, checks a
  valid copy, removes a helper, damages a code page, and restores the helper.
  It then changes the copied runner's plist and re-signs inside-out with the
  matching Developer ID while retaining the old manifest. All signatures must
  verify, but inspection must reject the stale runner hash. No copy is launched;
  cleanup removes only the temporary directory and checks the source inventory.
- `release_controls` accepts a recognized Apple acceptance with extra fields and
  stops on agreement errors, unknown responses, pending/rejected/unknown status,
  wrong submission IDs, ambiguous duplicate fields, simulated timeouts, and changed input archives. Independent
  call receipts require exactly one submission and at most one bounded wait.
  Archive controls use real ZIPs and real layout/manifest/inventory checks, with
  simulated signature success and independent extraction/staple/execution tools.
  Their fake bundles carry a compiled XPC host stub because the inspector's
  `nm -u` check needs a real Mach-O, so these release controls need clang: the
  wrapper builds the stubs with `tests/fixtures/dispatcher/build.sh` into the
  case artifacts and names them in `PW_DISPATCHER_HOST_FIXTURE`.
  They cover missing helpers, stale evidence, missing staples, failed XPC runs,
  skipped cases, wrong runner provenance, mutation, and corrupt ZIPs, while a
  usable local source app remains untouched. Real signature semantics are covered
  separately by `signed_artifact_controls`.
  Evidence controls exercise custom distribution paths, shared named steps,
  archive identity, refusal of repeated submissions/commands, preservation of
  failed receipts, and links to the separate archive-acceptance output.
- `release_deadline_controls` runs the actual release command CLI against a
  parent/child fixture that flushes partial stdout and stderr, then waits on a
  test-owned socket. Each process configured to ignore SIGINT must survive a
  direct interrupt before the timeout case proceeds. A normal release must succeed; a hung tree must fail
  within the outer deadline. A third case lets the parent exit zero on the
  wrapper's SIGINT while its child remains stuck: the wrapper must still fail
  for timeout and stop the child. Independent invocation receipts require one
  launch, raw bytes must survive unchanged, and the shared exec observer requires
  kernel exit events for both peers before test cleanup. These deadline
  controls make no Apple requests and need no built app or signing identity;
  only the suite's compiler prerequisite applies. macOS socket/process
  observation may require escalation in an automation sandbox.

- `release_publish_controls` exercises the three release tools against a real
  temporary repository with a bare `origin`, fixture ZIPs, attempts and run
  records. The tag preflight must refuse an untagged or dirty tree, a
  lightweight tag, a remote holding a different tag, an unreachable remote and
  an existing archive, and must only warn under `--report`. Archiving must
  refuse a hash, acceptance, notarization, tag, guide, notes or battery
  mismatch without touching the distribution or the retention index, and on
  success must move the attempt, write the checksums and provenance record,
  pack and verify complete test evidence with portable summaries, and retain
  the acceptance and battery runs. Publication runs `git` for real
  against the bare remote and a GitHub stand-in: it pushes the tag once,
  creates the release once with the tag verified, downloads every asset back,
  and records origin only when digests and bytes match; a second run verifies
  without creating, and a mismatch leaves origin unrecorded.
- `release_rotation_controls` creates successive releases in real fixture
  repositories. It verifies compressed files and symlink targets independently,
  reads a detached archive after deleting its source runs, and observes that
  cleanup keeps the latest release plus the newest completed local output,
  including failed runs and completion-time ties. Older owned development,
  acceptance and abandoned output is removed. Explicit pins, active acceptance,
  newer unfinished work, pending resource cleanup, unknown output and scratch
  survive. The new archive must verify; old release entries can expire even
  without an older portable bundle. Corrupt new archives and symlink redirects
  stop unsafe cleanup. Names, filesystem timestamps and sizes do not choose newest.
  Abrupt child exits after rename, index replacement, partial deletion and
  completed deletion must resume from the journal without deleting a replacement
  at the original path. Competing processes must respect the stable checkout
  lock, and a failed atomic index replacement must preserve its prior bytes.

## Fixtures

- `tests/fixtures/caller_auth/bundle.py`: copying, signing, and command receipts.
- `dispatcher/artifact_controls`: offline real-file mutations with independent
  simulated codesign; verifies gating, case receipts, and final inventories.
- `tests/fixtures/dispatcher/fixture_bundle.py` and `build.sh`: fake bundles
  around a compiled XPC host stub, shared with the release controls here.
- `tests/fixtures/release/tools.py`: controlled external-tool boundary and receipts.
- `tests/fixtures/release/publish_tools.py`: GitHub stand-in for publication controls.
- `tests/fixtures/release/hanging_command.py`: real command processes; reuses
  `tests/fixtures/exec/control.py` for socket readiness and independent OS exits.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/preflight/codesign.preflight/artifacts/preflight.json`

Run:

```
./tests/run.sh --case preflight/codesign.preflight
./tests/run.sh --case preflight/signed_artifact_controls
./tests/run.sh --case preflight/release_controls
./tests/run.sh --case preflight/release_deadline_controls
./tests/run.sh --case preflight/release_publish_controls
./tests/run.sh --case preflight/release_rotation_controls
```
