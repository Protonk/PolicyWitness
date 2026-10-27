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
  commands on its UUID, platform, minimum, SDK and linker tools, with its
  architectures and container as the bytes carry them, and with
  `codesign -dvv`'s display of each nested signature it claims; a record for
  another build with the same inventory is refused.
- Requires the output target, from the bytes: every required executable,
  whatever the manifest claims, and every other Mach-O the bundle carries,
  found by header, must be a thin `arm64` Mach-O for macOS (`lipo -archs`
  naming exactly `arm64`, a thin header, the macOS platform in its load
  commands). dSYM companions are debug data and are not inspected as code,
  including fat containers whose every bounded, nonoverlapping slice has a
  complete matching `MH_DSYM` header. Mixed code/debug containers and malformed
  fat tables or slice headers remain subject to rejection.
  The fault is reported as `output_target`, independently of signature,
  manifest and record faults.
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
- Runs `nm -u` on the shipped `pw-probe-runner` and rejects an undefined
  `_clock_gettime`: the worker times release waits and exec attempts with
  continuous Mach time because libc's `CLOCK_MONOTONIC` path can fall back to a
  Unix syscall that a deny-default profile refuses. The raw import list and
  `nm` status are retained; a failed inspection is an error, never an empty
  import set. Like the host check this sees direct linked imports only, not
  dynamic lookups or library-internal calls, so it complements the
  [timing controls](../runner_c_worker_harness/README.md) rather than
  establishing usable time. Host and validator clocks are not inspected here.
- Artifact inspection never executes `policy-witness` or the runner.
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
  verifies, and requires exactly the codes each fault produces. For the output
  target it substitutes real x86_64 and universal Mach-O signed with the
  identity, with every signature verifying and every manifest and record hash
  consistent: an x86_64 helper whose record still claims the target must
  produce exactly `output_target` and `provenance_metadata`, the same helper
  described truthfully by its record exactly `output_target` and
  `provenance`, and an unlisted universal library exactly `output_target`. No copy is
  launched. A validly re-signed copy carrying a universal dSYM resource passes
  with no additional code in the inventory; cleanup removes only the temporary directory and checks the source
  inventory.
- `byoxpc_verification_controls` uses never-launched signed copies and isolated
  child registry/home directories. Corrupting a worker or issuer code page must
  fail recursive installation checks and subsequently identify both the bundle
  and changed helper during validation. Other helper signatures remain valid;
  removal verifies registry and plist cleanup.
- `build_provenance_controls` exercises the provenance and lock helpers with
  constructed inputs and disposable directories: SDK admission at shell and
  make entry points; plain and exec-restricted shim-probe profiles, successful
  permitted execution, rejected gate decisions and real nested-sandbox
  refusal; the combined profile with the fixed unreadable-arm64 rule, whose
  startup gate keeps the containment checks and requires the arm64 read to
  exit zero empty inside while the translation read prints 0, an arbitrary
  rule refused, and constructed missing, wrong, nonzero or incomplete sysctl
  observations stopping prepare and run before dispatch; claims admitted only by a
  live owner's handoff and refused when stale, closed, malformed, a separate
  open on the lock inode, a wrong nonce or another worktree's, with the real
  holder unchanged and an unheld descriptor never turned into a hold; an
  owner that exits or is killed during admission leaving no hold and no
  session; a hold that outlives a killed owner and wrapper while a protected
  grandchild runs, which a wrapper dropping the descriptor fails, and SIGINT,
  SIGTERM and SIGKILL at the launcher; exact environment witnesses captured
  by the shell front end, compared without restoration and recorded anew by
  nested front ends; missing or changed witnesses refused before writes;
  direct Python child environments compared byte for byte against the
  caller, with a shim negative control; stand-in developer directories
  refused under containment; session writes, fresh removal and stamp
  publication refused without a claim or with a missing, malformed or stale
  session nonce; symlinked, non-directory and foreign cache components and
  unsafe session destinations refused before any write, an owned missing
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
  It also checks unrelated-socket handoffs with copied public owner records,
  admission after the original owner exits while a nested scope survives,
  a full channel queue, complete large request replies, and cancellation of
  a command and descendant that ignore signals. Missing target directories
  remain absent after a refused session start. Typed Cargo profiles, Meson
  options, stamp projections and fresh-mode observations are checked, and
  archive load commands and signature claims are compared with the ZIP's
  executable bytes. Applying every opt-in mutation in memory checks its
  anchors in the default battery; the opt-in run establishes that the
  mutated guards actually fail their controls. The output target check is
  exercised on real fixtures linked with the selected SDK (thin arm64, x86_64
  and arm64e executables, a universal and a one-slice fat file, an arm64 Mac
  Catalyst executable, truncated, empty, text and fat-magic files) whose
  headers and load commands the control reads itself first; observations and
  decisions are compared separately, failed and inconsistent `lipo` reports
  refuse, the bundle scan finds renamed and unlisted code by header while a
  dSYM companion is skipped by file type and not by path, including universal,
  one-slice fat and fat64 debug containers while mixed code/debug or malformed
  containers remain subject to rejection. Both app-wide gates check every
  required path in full and partial builds even after text replacement, emptying,
  truncation of the magic or removal. The build gate
  records each stage and names only the departing output, and copies of the
  check with the container rule removed, the predicate reduced to arm64
  membership, names matched as substrings or the platform rule removed each
  accept a fixture the control refuses. Stamps carry the configured output
  target and refuse another or an older stamp before any probe; fresh removal
  replaces both Cargo release areas and keeps other profiles and triples;
  judgments bind to the output triple's release area; target rules are
  attributed to the output triple, not the compiler's host; a lower-precedence
  target default is recorded as overridden; records require the output target
  and are compared with the bytes, and a version 1 record is refused by the
  shape check and the archive reader alike.
- `build_guard_controls` runs the unchanged build script in a disposable
  checkout with real Cargo, Meson and signing tools. Tool wrappers replace the
  last checked Cargo or native output with a real Mach-O for a different macOS
  minimum, one or every shipped output with a Mach-O whose `LC_BUILD_VERSION`
  names another SDK version (linked with the selected SDK and stamped by the
  linker's `-platform_version`, a controlled metadata mismatch whose load
  commands the control reads before substituting it), sign `sbpl-check` ad hoc, or sign that helper, the service
  seal or the app seal with `--timestamp=none`. Both full and partial builds
  must refuse wrong minima and wrong SDKs before assembly while preserving
  previous distribution bytes. A Cargo output replaced by a thin x86_64 and a
  native output by a universal Mach-O, each with the plist's minimum and the
  selected SDK, must be refused by the output target check alone, naming the
  output, before assembly; the minimum and SDK faults must not reach it. The ad hoc and timestamp-less signatures must
  pass deep verification and then fail the signer check, naming the artifact,
  before the guide is staged or the ZIP is created; the control inspects each
  such signature independently before
  crediting the refusal. Successful siblings must package both variants. Raw
  command and tool receipts survive temporary-checkout cleanup. This case
  requires the full toolchain with one installed SDK and a Developer ID
  identity, and is opt-in. Actual selection changes between two toolchains
  belong to `build_toolchain_switch_controls`.
- `build_refusal_controls` runs the unchanged build script in a disposable
  checkout once per refusal the build manifest lists, in each variant the
  refusal applies to. A fault is arranged beside one boundary: an unreadable
  `hw.optional.arm64` under a sandbox profile, where the native builder
  refusal is the only output ahead of `--help`, an unknown argument, a bad
  knob, a missing tracked input, an invalid `SDKROOT` under the helper's
  combined containment and an independently held lock, with an empty receipt
  list and the session, caches and distribution unchanged (this exercises the
  empty value only; a value of `0` or a failed probe rests on the guard's
  code); a tracked input
  gone, a held lock, a claim without a live owner's handoff or an owner
  killed mid-build, a CLI owner or nested build with a missing or changed
  environment witness, an environment that cannot
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
  described in the [build-refusal account](../../CHANGE-VERIFICATION.md#build-refusal-controls). For the output target: outputs outside it
  substituted at each of the four checked boundaries (after Cargo, including
  a corrupted cached unit refused again on reuse; after the native compile,
  the worker before it is run; in the assembled bundle with an unlisted file,
  before any signature; before the ZIP); a stamp
  naming another target or predating the contract; an x86_64 Meson host
  through a cross file; Cargo's report naming another path; an x86_64 target
  default overridden; and the package guard on direct Cargo builds for other
  targets with its weakenings. Copies of the script with a guard removed or
  moved past its operation (the native builder check among them, removed or
  moved past Python and SDK setup or past the lock front end), and of the
  session helper with path admission disabled, must fail the matching
  control. Opt-in, with the same toolchain and identity requirements as the
  guard controls; it needs no Rosetta.
  A final release-battery sequence builds a fresh full ZIP and runs real
  acceptance with the real default battery against its extracted app. Only
  notarization, staple validation and Gatekeeper responses are controlled;
  extraction, signatures, case execution and the full inventory comparison
  remain real. The nested output is copied intact into the case's artifacts.
  It also runs the contained shim installation-request positive control and
  its empty-SDK neighbour, requiring a PID-attributed installation-service
  denial from the unified log. This is the only control deliberately making
  that request; its fixture retains the gate, outputs and raw log queries.
- `translated_build_refusal_controls` needs Rosetta and nothing else. In a
  disposable admission fixture with recording wrappers that would fail, a
  held lock, previous outputs, a session and caches, it runs the unchanged
  script under `arch -x86_64 /bin/bash` and `make build` under
  `arch -x86_64 /usr/bin/make`, in both variants, with `SDKROOT` unset or
  valid: each refuses naming `sysctl.proc_translated=1`, with no wrapped tool
  call, version probes included, and nothing changed. Under translation the
  builder refusal also wins over `--help`, an unknown argument, a bad knob, a
  missing tracked input and an invalid `SDKROOT`; make given an invalid
  `SDKROOT` refuses at parse time and never enters the script. Invalid SDK
  requests run under the ordinary shim-probe containment with `arch` inside
  it. Make's own launch and SDK check precede the script and are outside the
  receipt claim. Opt-in; missing Rosetta leaves the case unrun.
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
  skipped and unrun cases, a battery that is not the default selection, a
  battery that exceeds its fixed two-hour bound (acceptance fails and the nested
  output is retained), wrong runner provenance, mutation, and corrupt ZIPs,
  while a usable local source app remains untouched. The execution stand-in
  requires the one test interface with no selectors and the recorded bound.
  Real signature semantics are covered separately by `signed_artifact_controls`.
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
  records. Its ZIP members are real linker-signed Mach-O stand-ins whose
  load commands and signature facts the independent fixture writer records.
  The tag preflight must refuse an untagged or dirty tree, a
  lightweight tag, a remote holding a different tag, an unreachable remote and
  an existing archive, and must only warn under `--report`. Archiving must
  refuse a hash, acceptance, notarization, tag, guide, notes or battery
  mismatch without touching the distribution or the retention index, and on
  success must move the attempt, write the checksums and provenance record,
  pack and verify complete test evidence with portable summaries, and retain
  the acceptance run with the default battery nested inside it. The battery
  must be a passing default-selection run against the extracted app whose
  recorded inventory equals a fresh extraction of the ZIP in full: a changed
  file hash and a single changed mode bit are each refused by name, as are a
  failed, skipped, selected or mutated battery. Selection checks include the
  recorded plan mode: an all-case run has empty explicit selectors but is not
  a default run. Both archive formats reject that substitution. The generated schema-2 record carries the
  provenance writer's two sealed notes as independent literals, and both the
  ZIP's member and the archived copy keep them through verification; a release
  record without a provenance object and a version 1 record bound
  consistently through the ZIP, its checksums and the archived copy are
  refused. Publication runs `git` for real
  against the bare remote and a GitHub stand-in: it pushes the tag once,
  creates the release once with the tag verified, downloads every asset back,
  and records origin only when digests and bytes match; a second run verifies
  without creating, and a mismatch leaves origin unrecorded. An archive
  without portable test evidence is refused before any `git` or `gh` call.
  Branch-name controls run the actual `build.sh` stamp fragment and release
  preflight at the same commit and checkout path under `main`, `master`,
  `doc-rework` and newly created then renamed branches. Untagged, annotated-tag
  and dirty-tree decisions and stamps must agree across names; a retained
  comparison receipt distinguishes the source state from the branch label.
- `release_rotation_controls` creates successive releases in real fixture
  repositories. It verifies compressed files and symlink targets independently,
  reads a detached archive after deleting its source runs, and observes that
  cleanup keeps the latest release plus the newest completed local output,
  including failed runs and completion-time ties. Older owned development,
  acceptance and abandoned output is removed. Explicit pins, active acceptance,
  newer unfinished work, pending resource cleanup, unknown output (acceptance
  output without its owner record and lifetime lock among it) and scratch
  survive. The new archive must verify. Corrupt new archives and symlink redirects
  stop unsafe cleanup. Names, filesystem timestamps and sizes do not choose newest.
  Abrupt child exits after rename, index replacement, partial deletion and
  completed deletion must resume from the journal without deleting a replacement
  at the original path. Competing processes must respect the stable checkout
  lock, and a failed atomic index replacement must preserve its prior bytes.
  Current-format rotation retires older owned acceptance and separately retained
  battery output while leaving historical archive bytes unchanged. Unsupported
  evidence formats are refused by bundle/release verification and rotation
  before any index, journal or output change. The publication controls also
  require format refusal before any external command or archive change. These
  controls change a current fixture's format number and rebind its manifest hash;
  unchanged current-format evidence still verifies, publishes and recovers.

## Fixtures

- `tests/fixtures/caller_auth/bundle.py`: copying, signing, and command receipts.
- `tests/fixtures/build_guards/tools.py`: real-tool delegation with output
  replacements or a replaced codesign argument list at the selected boundary.
- `tests/fixtures/build_refusals/tools.py`: real-tool delegation with receipts
  and a stderr canary, passing the claim's lock descriptors to the real tool;
  configured hooks remove, move, copy over, replace with a new file carrying
  the current time, truncate,
  rewrite, replace with a symlink or change the mode of a file, append
  arguments to the real tool's command, edit Cargo's artifact report, kill or
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
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/preflight/codesign.preflight/artifacts/preflight.json`

Run:

```
./tests/run.sh --case preflight/codesign.preflight
./tests/run.sh --case preflight/build_provenance_controls
./tests/run.sh --case preflight/signed_artifact_controls
./tests/run.sh --case preflight/build_guard_controls
./tests/run.sh --case preflight/build_refusal_controls
./tests/run.sh --case preflight/translated_build_refusal_controls
./tests/run.sh --case preflight/build_toolchain_switch_controls
./tests/run.sh --case preflight/release_controls
./tests/run.sh --case preflight/release_deadline_controls
./tests/run.sh --case preflight/release_publish_controls
./tests/run.sh --case preflight/release_rotation_controls
```
