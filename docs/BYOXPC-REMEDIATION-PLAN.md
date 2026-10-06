# BYOXPC remediation plan

This plan makes the BYOXPC apparatus deliver what the README and the guide
say it delivers: a specimen policy applied under the entitlements the
installer supplied, selected on what the worker actually holds, verified to
the code that runs, and usable in sequence without a hidden wait. It is
grounded in the investigation records listed below, which stay as evidence
and are linked only from here. It is temporary: permanent documentation
never links it, and it is deleted when its gates have passed.

The architecture document states the three gaps this plan closes, in its
[BYOXPC section](ARCHITECTURE.md#byoxpc-as-a-variation-on-launch-and-selection)
and its [Known gaps](ARCHITECTURE.md#known-gaps) index: installed
entitlements reach the host executable only; installation's verification is
not recursive; selection by `required_entitlements` checks key presence in
the host's read-back. The user-facing account to correct is the guide's
[External runners](PolicyWitness.md#external-runners-byoxpc) section and the
README's [Entitlements + SBPL](../README.md#entitlements--sbpl) framing.

## Records this plan builds on

1. [Installation signature scope](../records/BYOXPC-SIGNATURE-SCOPE.md)
2. [Environment observability](../records/BYOXPC-ENVIRONMENT-OBSERVABILITY.md)
3. [Entitlement-conditioned behavior](../records/BYOXPC-ENTITLEMENT-BEHAVIOR.md)
4. [Ad-hoc behavior and a direct runtime control](../records/BYOXPC-ADHOC-BEHAVIOR.md)
5. [Verification boundaries and mixed authorities](../records/BYOXPC-VERIFICATION-BOUNDARIES.md)
6. [Respawn and retirement observations](../records/BYOXPC-RESPAWN-OBSERVATIONS.md)
7. [Three partial consumer workflows](../records/BYOXPC-CONSUMER-PROBES.md)

Their receipts are gitignored, local-only and pinned in `tests/RETAINED.json`
under `tests/out/runs/byoxpc-investigation-20261006/` and
`tests/out/runs/byoxpc-consumer-probes-20261006/`.

## Status

Planned; implementation has not started. Writing this plan credits no
implementation or acceptance test below.

- [x] Establish the regression baseline and record the starting failures.
- [ ] Group 1: sign the embedded helpers at install and read all three back.
- [ ] Group 2: verify recursively at install and in `runner validate`.
- [ ] Group 3: select on true-valued keys in the worker's read-back.
- [ ] Group 4: bound launchd's respawn wait in the generated plist.
- [ ] Group 5: correct the guide and the README.
- [ ] Reconcile the architecture document and the records; pass the final
  gates; retire this plan.

## Decisions, recorded up front

- **Installed entitlements reach the worker.** At install, the embedded
  worker is signed with the supplied identity and the supplied entitlements
  plist; the embedded validator is signed with the identity alone; then the
  enclosing bundle is signed as today. Record 3 shows the worker's
  entitlement is what the kernel consults for an SBPL predicate, and that the
  validator's `sandbox_check` for the worker's PID needed no entitlement of
  its own. Signing the validator with the identity removes the mixed
  authorities record 5 observed, without granting it capability it does not
  use.
- **Every binary's read-back is recorded.** The registry record and the
  dossier's runner provenance carry the host's, the worker's and the
  validator's entitlements and signatures separately, read back with
  `entitlements_from_codesign` and `codesign_metadata` after signing. Fields
  are added, not changed, so the registry loader stays additive and the
  envelope gains fields without a version bump; the shape golden learns them.
- **Verification is recursive.** `codesign_verify` uses `--deep --strict` at
  install and in `runner validate`. Record 5 shows the non-recursive check
  passing a copy whose worker code was altered.
- **Selection means a true-valued key on the worker.** `required_entitlements`
  is satisfied only by a key present with the boolean value `true` in the
  worker's read-back; the refusal names the process and the key. The host's
  entitlements remain recorded beside it and are not consulted for selection.
  Record 7 shows a `false`-valued host key admitting a runner today.
  Contract reading, decided here: the guide documents `required_entitlements`
  as enforcing that the runner holds the entitlements, so admitting a
  `false`-valued key is a defect against the documented meaning and the fix
  keeps the request contract value under CONTRACT.md's "fix an implementation
  defect to honor the documented request" row. The group quotes the guide's
  sentence in its execution notes when it starts; if the sentence does not
  bear that reading, the group bumps the request contract instead.
- **The generated plist sets a short `ThrottleInterval`.** Records 6 and 7
  show the guide's own verify-then-run sequence refused or delayed, and
  serial batches paying launchd's default wait. The value is chosen by
  measurement in Group 4, with the measurement retained.
- **Host-to-worker environment propagation stays unobserved.** Record 2 shows
  the worker spawns exec children with an empty environment, so no shipped
  path can read the worker's own environment back, and no route in this
  plan depends on it. Building a worker-side read-back is a product change
  this plan does not make; the architecture document keeps saying that
  `--env` configures the host's launch and that nothing records what the
  worker holds.
- **Project-location stalls are documented, not mitigated.** Records 2 and 3
  observed opens stalling against targets under the checkout's Desktop path
  with the same bytes completing from a temporary directory. The cause is
  unassigned; Group 5 advises owned temporary targets and leaves a diagnosis
  to its own investigation.

## Scope and retained limits

Changes are in the controller (install, validate, selection, plist
generation), the shared Python readers and goldens, the test fixtures and
the documentation. No runner source changes, so the worker identity does not
move and the order-barrier mutation control is not required; if a group
finds it must touch `runner/Sources/`, it regenerates the identity and runs
that control. No queue, automatic retry or cancellation is added; a
connection racing host retirement can still fail before a refusal, and a
timed-out request can still complete its effects. System scope, other
signing teams, other macOS versions and Gatekeeper distribution are outside
these gates.

Read [runner/AGENTS.md](../runner/AGENTS.md) before touching any runner test
machinery. Every installed runner in a test is test-owned through the session
helper in [tests/fixtures/byoxpc/session.py](../tests/fixtures/byoxpc/session.py)
and removed with its removal verified. Live steps need a GUI session and a
matching Developer ID; a refusal by the automation sandbox follows the
[sandboxed-harness procedure](../AGENTS.md#sandboxed-automation-harnesses).

## Baseline

Write each regression first and record its failure on the starting commit.
Rust reds use `#[ignore]` with this plan as the reason, selected by exact name
through a wrapper shaped like
[disposition_reds.sh](../tests/suites/unit/disposition_reds.sh) until the fix
promotes them; a live red is run once with its log retained.

- A Rust unit test that a selector requiring a key present with value
  `false` is refused. Red today in `entitlements_superset`.
- An offline verification control: copy the shipped XPC bundle to owned
  staging, sign it ad-hoc so no identity is needed, flip one byte of the
  worker's code after sealing, and require `codesign_verify` to fail. Red
  today, since the non-recursive check passes. The investigation's retained
  `signing_controls.py` has the exact procedure; port it as a test under a
  suite that requires only the built app.
- A live read-back after an owned install that requires the worker's
  entitlements to equal the supplied plist's. Red today: the worker's
  read-back is empty.
- A timing measurement, not an assertion: the wait a second request pays
  after a run, before and after Group 4, with the job listing's reported
  minimum runtime beside it.

## Group 1: install signing and read-backs

In [runner_commands.rs](../controller/src/runner_commands.rs) and
[runner_manager.rs](../controller/src/runner_manager.rs): before the bundle
is signed, sign `Contents/MacOS/pw-probe-runner` with the identity and the
entitlements plist, then `Contents/MacOS/sb_api_validator` with the identity
alone, each through `codesign_sign`; then sign the bundle as today. Nested
code must be signed before the enclosing seal, and the order is part of the
test. Keep the existing refusal of `--entitlements` without an identity or
`--allow-adhoc`, and apply it to the helpers too.

Read back all three binaries after signing. Extend the registry record with
per-binary signature and entitlement fields, additive, and the runner
provenance in [runner_select.rs](../controller/src/runner_select.rs) and the
dossier in [dossier.rs](../controller/src/dossier.rs) with the same. The
dossier's binary baselines already hash all three files; the new fields sit
beside those hashes.

Tests: the live read-back red above, promoted; the existing
`runner_byoxpc` cases and the opt-in `dossier_witness_byoxpc` case carrying
the new fields; a Rust unit test for the signing order with the codesign
call stubbed, so the sequence is pinned without an identity; the shape golden
updated through its candidate flow. The session helper's entitlement reader
is extended to read all three binaries, which the consumer probes already
did by hand.

## Group 2: recursive verification

`codesign_verify` adds `--deep --strict` and is used by install and by
`runner validate`. `runner validate` re-reads all three binaries, not the
host alone, and reports which failed. The offline verification red above is
promoted. The `runner_byoxpc` and registry-recovery cases must still pass,
since every bundle they install is now verified recursively.

## Group 3: selection on the worker's true-valued keys

`entitlements_from_codesign` keeps the raw plist and the keys; the selection
predicate changes from key membership to key present with value `true` in
the worker's read-back. `enforce_required_entitlements` reads the worker's
fields recorded by Group 1 and names the process and the key in its refusal.
A registry record written before Group 1, which has no worker read-back,
refuses any selector that requires entitlements, with a message that says to
reinstall; records without requirements select as before. The guide's
sentence on `required_entitlements` is quoted in the execution notes and the
contract reading above is confirmed or revised before the first code change.

Tests: the false-valued-key red, promoted; the existing selection unit tests
in [runner_select.rs](../controller/src/runner_select.rs) extended for true,
false, absent and pre-Group-1 records; the consumer-probe transfer matrix
reduced to a live case under `runner_byoxpc` that installs a host-only copy
and a host-plus-worker copy and requires the first to be refused and the
second to complete the entitlement-conditioned write, with the file bytes
read independently.

## Group 4: the respawn wait

`build_launchd_plist` writes a `ThrottleInterval`. Measure first with the
investigation's timing procedure, then choose the smallest value that makes
the verify-then-run sequence and a serial batch complete without a refusal or
a ten-second wait on this machine, and retain the measurement. The live
single-use case's fixed sleeps shrink to the measured value plus margin. The
guide's Questions note about the throttle is corrected by Group 5 to say what
the plist now sets.

## Group 5: the guide and the README

One group, after the code groups land, so every sentence describes shipped
behavior:

- The README's entitlement framing and the guide's install recipe say which
  processes the installed entitlements reach and what the registry records
  for each.
- `required_entitlements` is documented as true-valued keys on the worker.
- `runner verify` consumes a host; the recipe says what to expect from the
  next request and how long the wait is after Group 4.
- A timed-out request may still complete its effects, as the consumer probes
  observed; the run-output section says not to retry such a request blindly
  and to size the client budget to the specimen.
- A helper launched by an exec attempt sees three descriptors and no
  environment, and its own failure does not change the run summary.
- Targets under privacy-mediated folders can stall; the recipe recommends
  owned temporary targets.
- The architecture document's three BYOXPC Known gap paragraphs come out when
  their groups' gates pass, the figure's notes on `signing` and `selector`
  become descriptions of the mechanism, and the `verify` fact is updated for
  the throttle. The environment paragraph stays.

## Gates

1. Rust unit tests, Python checker controls and the shape-golden flow for
   every group, run after each group.
2. A signed build and the default battery.
3. The opt-in `runner_byoxpc` cases: BBX, `single_use`, `registry_recovery`,
   `runner_auth_external`, plus the new read-back and transfer cases, and the
   opt-in `dossier_witness_byoxpc` case.
4. Source drift, the generated contract, limits and architecture checks, and
   the anchor check by hand.
5. One final default battery against the completed signed artifact, with
   retained evidence paths and the source snapshot recorded below.

A blocked live gate is not a passing result. Every test-owned external
service is verified removed before its staging and recovery record are
deleted.

## Closeout

Update the seven records' status lines without replacing their evidence.
Remove the resolved Known gap paragraphs and index lines, regenerate the
figures, and run the architecture check. Record the final gate runs below,
then delete this plan. The records remain.

## Execution notes

### Baseline (2026-10-06, starting commit 2b9a207)

The four regressions exist and were recorded red before any product change:

- `unit/rust.byoxpc_reds` selects `false_valued_key_does_not_satisfy_a_requirement`
  (runner_manager) and `selection_refuses_a_false_valued_required_key`
  (runner_select) by exact name; both carry `#[ignore]` with this plan as the
  reason and failed with "a required key present with value false must be
  refused".
- `preflight/byoxpc_verification_controls` seals an owned ad-hoc copy, changes
  one worker code byte after sealing, and requires `runner install` to refuse
  it and `runner validate` to report a registered copy changed after
  installation. Red: the corrupted copy installed with exit 0 while
  `codesign --verify --deep --strict` and the worker's own verification
  rejected it. The run also showed `entitlements_from_codesign` recording
  `plutil failed` for a binary that carries no entitlements; Group 1 corrects
  that read-back since the validator never carries any.
- `runner_byoxpc/entitlement_readback` installs with a supplied plist
  (`com.apple.security.cs.allow-jit`) and reads all three binaries back.
  Red: the worker's read-back was empty.
- Timing, not an assertion, with the generated plist carrying no
  `ThrottleInterval` and launchd reporting `minimum runtime = 10`: a run 0.4 s
  after the install's own verify took 9.3 s; a run 0.4 s after a run took
  10.3 s; three serial runs with 0.4 s of consumer work between them took
  21.4 s of wall time.

Evidence: `tests/out/runs/byoxpc-remediation-baseline-reds` (dispatcher run
`20261006T183314Z_84233c0f`) and `tests/out/runs/byoxpc-remediation-baseline`
(`timing.py`, `before-group-4/`), both pinned in `tests/RETAINED.json`.
