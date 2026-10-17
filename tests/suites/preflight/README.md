# preflight

Read-only artifact inspection, with opt-in controls using real signatures.
Offline release controls also exercise the release procedure's decision points.

## Invariants

- Requires expected executables/resources, valid strict signatures for the app,
  service, and helpers, and matching hashes for every manifest entry. Required
  helper entries cannot silently disappear from the manifest. The provenance
  record must be present and listed, have the documented shape (typed
  sections, no null required field, the variant's compilers and outputs,
  effective settings that agree with the outputs), name every shipped
  executable once with a valid path, carry no controller hash, agree with the
  manifest and the bytes on every other hash, with each executable's load
  commands on its UUID, platform, minimum, SDK and linker tools, and with
  `codesign -dvv`'s display of each nested signature it claims; a record for
  another build with the same inventory is refused.
- Runs `nm -u` on the shipped `PWRunner` executable and rejects any undefined
  `_sandbox_*` symbol. This sees linked imports; it does not detect dynamic
  symbol lookup. The [host-source check](../source_drift/README.md) covers
  literal lookup/load forms. Worker, validator and issuer native calls are
  expected; only the host must remain free of them. The issuer is required in
  the bundle inventory and has separate signature, signer and manifest-hash
  checks. This inspector does not compare entitlement contents. Independent
  issuer entitlement read-back belongs to the
  [BYOXPC controls](../runner_byoxpc/README.md) and
  [extension controls](../witness_contract/README.md#native-extension-boundaries).
- Never executes `policy-witness` or the runner.
- The shared `tests/lib/artifact.py` inspector also gates app-dependent selections
  in the public dispatcher. It never repairs a failed artifact.

## Success criteria

- `codesign.preflight` succeeds only when the inspector reports no errors.
- `signed_artifact_controls` copies the selected app to `/private/tmp`, checks a
  valid copy, removes a helper, damages a code page, and restores the helper.
  It then changes the copied runner's plist and re-signs inside-out with the
  matching Developer ID while retaining the old manifest. All signatures must
  verify, but inspection must reject the stale runner hash. It then writes
  semantically faulty records (a null or missing section, a wrong type, a null
  deployment target or required observation, a malformed request, a linker
  tool version alone, a signature claim, and the hash, inventory and SDK
  faults), refreshes the manifest and re-signs each copy so every signature
  verifies, and requires exactly the codes each fault produces. No copy is
  launched; cleanup removes only the temporary directory and checks the source
  inventory.
- `byoxpc_verification_controls` uses never-launched signed copies and isolated
  child registry/home directories. Corrupting a worker or issuer code page must
  fail recursive installation checks and subsequently identify both the bundle
  and changed helper during validation. Other helper signatures remain valid;
  removal verifies registry and plist cleanup.
- `build_provenance_controls` exercises the provenance and lock helpers with
  constructed inputs and disposable directories: claims admitted only by a
  live owner's handoff and refused when stale, closed, malformed, a separate
  open on the lock inode, a wrong nonce or another worktree's, with the real
  holder unchanged and an unheld descriptor never turned into a hold; an
  owner that exits or is killed during admission leaving no hold and no
  session; a hold that outlives a killed owner and wrapper while a protected
  grandchild runs, which a wrapper dropping the descriptor fails, and SIGINT,
  SIGTERM and SIGKILL at the launcher; requests captured by the shell front
  end, restored for the command, handed to nested owners and refused when
  absent or malformed; session writes, fresh removal and stamp publication
  refused without a claim or with a missing, malformed or stale session
  nonce; symlinked, non-directory and foreign cache components and unsafe
  session destinations refused before any write, an owned missing
  `controller/target/` created, and a path replaced between admission and use
  refused without writing or removing through it; stamps published, validated,
  extended and refused as missing, malformed, unsupported, foreign, changed
  or unobservable without ever rewriting one; bounded probes whose failure
  entries carry no tool output: stdout and stderr overflow while the tool would
  exit zero, both streams active at once, the exact limit, a nonzero exit,
  empty and malformed output, a timeout, a tool ignoring SIGTERM and an
  orphaned pipe writer, each completing within its bound with the fixture's
  processes observed gone; identities, commands and flag lists past their
  bounds failing rather than comparing equal after truncation, and failed
  required observations refusing compatibility, stamp publication and the
  record; fresh-mode removal admitting only owned real
  directories and refusing symlinked parents and failed removals; Cargo
  judgments bound to fingerprints through the uplifted executable with
  ambiguous, malformed and unsupported cases explicit; SDK versions
  normalized with unknowns never equal; Cargo configuration graphs read the
  way Cargo reads them (inline, dotted and table forms, invocation-directory
  discovery with ancestors and Cargo home, the extensionless name, includes in
  order with relative paths and the including file on top, bounds, cycles,
  missing or malformed files and type conflicts refused), the compiler and
  wrapper precedence with empty resets, `[env]` forced or not, inherited or
  not, relative and field-merged, conflicts with the build's inputs, and a
  summary carrying no PATH or unrelated values; Cargo judgments that are not
  literal booleans bound to the admitted executable refused in both modes, and
  requested flags attributed by precedence; signature displays establishing
  class, team and timestamp; and records refused for a swapped bundle,
  missing, duplicate or invalid outputs, a controller hash inside the seal,
  wrong hashes or wrong load-command metadata, every required section and
  representative nested fields missing, null or of the wrong type, a linker
  tool version alone, and a signature claim the display contradicts, by the
  inspector, by the producer before it writes and by the release-archive
  reader, which also binds each output's hash to the ZIP member, beside valid
  full and partial records and each permitted unknown. It needs clang for the Mach-O
  stand-ins and is in the default battery.
- `build_guard_controls` runs the unchanged build script in a disposable
  checkout with real Cargo, Meson and signing tools. Tool wrappers replace the
  last checked Cargo or native output with a real Mach-O for a different macOS
  minimum, one or every shipped output with a Mach-O whose `LC_BUILD_VERSION`
  names another SDK version (linked with the selected SDK and stamped by the
  linker's `-platform_version`, a controlled metadata mismatch whose load
  commands the control reads before substituting it), sign `sbpl-check` ad hoc, or sign that helper, the service
  seal or the app seal with `--timestamp=none`. Both full and partial builds
  must refuse wrong minima and wrong SDKs before assembly while preserving
  previous distribution bytes. The ad hoc and timestamp-less signatures must
  pass deep verification and then fail the signer check, naming the artifact,
  before the standalone observer is signed, the guide is staged or the ZIP is
  created; the control inspects each such signature independently before
  crediting the refusal. Successful siblings must package both variants. Raw
  command and tool receipts survive temporary-checkout cleanup. This case
  requires the full toolchain with one installed SDK and a Developer ID
  identity, and is opt-in. Actual selection changes between two toolchains
  belong to `build_toolchain_switch_controls`.
- `build_refusal_controls` runs the unchanged build script in a disposable
  checkout once per refusal the build manifest lists, in each variant the
  refusal applies to. A fault is arranged beside one boundary: a tracked input
  gone, a held lock, a claim without a live owner's handoff or an owner
  killed mid-build, a build launched by a Python owner without the caller's
  requests, an environment that cannot
  select the SDK or report its version, a stamp that is missing, malformed or
  foreign, a forwarding compiler wrapper relabelled after the stamp recorded
  it or failing its version probe, redirected or unobservable Cargo
  intermediates, a Cargo configuration that cannot be resolved or whose
  `[env]` forces another deployment target or SDK, a Cargo report whose
  judgment is not a literal boolean, a symlink at a cache path component or
  the session destination, a path replaced after an earlier helper's
  admission, a cache path fresh mode cannot remove, a Cargo
  output removed, made non-executable or moved under a target triple, a
  reused Cargo judgment in fresh mode, an old Ninja, a poisoned Meson
  directory, a source that does not compile, a worker reporting another
  identity, an input or output removed by a `cp`, `meson` or `codesign`
  wrapper after a named call, a truncated Mach-O at signing, the session gone
  before evidence, a tampered sealed resource or an edited record. Each
  control asserts the production diagnostic and status, the banners before
  and after the refusal, the tool calls that did not happen and the output
  left behind; the forwarding wrappers' receipts establish that compilations
  were forwarded and which flags they carried. The same case runs the
  fresh-mode state sequence with interruptions, the canary, replaced-output,
  lock-lifetime, Cargo oracle, Cargo selection and make-entrypoint controls
  described in the opt-in registry. Copies of the script with a guard removed or moved past its
  operation, and of the session helper with path admission disabled, must
  fail the matching control. Opt-in, with the same toolchain and identity requirements
  as the guard controls.
- `build_toolchain_switch_controls` builds under the selected developer
  directory and under the Command Line Tools through `DEVELOPER_DIR`, refusing
  reuse across the switch by a field its independent probes of both
  directories show to differ, and recovering fresh. It links a C and a Swift
  program under each directory first and names a linkable SDK through
  `SDKROOT` when xcrun's default does not link with that directory's tools,
  recording the probes. Opt-in; needs both developer directories with
  distinct compilers and a linkable SDK each, which is an equipment failure
  when absent.
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
- `tests/fixtures/build_guards/tools.py`: real-tool delegation with output
  replacements or a replaced codesign argument list at the selected boundary.
- `tests/fixtures/build_refusals/tools.py`: real-tool delegation with receipts
  and a stderr canary, passing the claim's lock descriptors to the real tool;
  configured hooks remove, move, copy, truncate, rewrite, replace with a
  symlink or change the mode of a file, edit Cargo's artifact report, kill or
  signal the build's shell, the lock owner or the wrapper itself, start a
  protected holder beyond the wrapper or record whether the lock is free
  beside one call, or answer a version query.
- `tests/fixtures/build_refusals/forward.py`: a forwarding compiler wrapper
  that runs the real compiler unchanged, records every invocation classified
  as compilation, probe or version query with the lock descriptor it holds,
  and can label, fail or hang a
  version query; `wrong_worker.c` is a worker stand-in reporting a foreign
  identity.
- The SDK refusal control gives real `xcrun` an unconfigured developer directory
  only for SDK selection. Its sandbox permits only that executable, denies Mach
  service lookups and limits writes to the fixture. A containment control runs
  first. Python/Git shims retain the actual developer environment; the fixture
  assumes no Xcode or Command Line Tools directory layout.
- `dispatcher/artifact_controls`: offline real-file mutations with independent
  simulated codesign; verifies gating, case receipts, and final inventories.
- `tests/fixtures/dispatcher/fixture_bundle.py` and `build.sh`: fake bundles
  around compiled Mach-O stubs with a complete full-build provenance record
  authored by the fixture (its own `otool` parse and the stubs' ad hoc
  linker signatures), shared with the release controls here. The release
  publish controls author a complete partial-build record whose helpers are
  members of their fixture ZIP.
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
./tests/run.sh --case preflight/build_provenance_controls
./tests/run.sh --case preflight/signed_artifact_controls
./tests/run.sh --case preflight/build_guard_controls
./tests/run.sh --case preflight/build_refusal_controls
./tests/run.sh --case preflight/build_toolchain_switch_controls
./tests/run.sh --case preflight/release_controls
./tests/run.sh --case preflight/release_deadline_controls
./tests/run.sh --case preflight/release_publish_controls
./tests/run.sh --case preflight/release_rotation_controls
```
