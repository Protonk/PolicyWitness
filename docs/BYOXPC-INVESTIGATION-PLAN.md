# BYOXPC investigation plan

This plan explores and investigates the BYOXPC apparatus: everything between
a user copying the shipped XPC bundle and a specimen running under the host
that copy provides. It makes no product change. It produces a map of the
apparatus as built, witnessed answers to the questions below, and the
decision inputs for whatever fix the entitlement gap turns out to need. The
fix itself belongs to a separate plan.

The starting point is the host/worker entitlement Known gap in
[ARCHITECTURE.md](ARCHITECTURE.md#known-gaps): the installer embeds the
supplied entitlements in the host executable only, while the embedded worker,
the process the specimen policy is applied to, keeps the signature the build
gave it. That is a symptom. The question underneath it is what the apparatus
establishes about the process whose sandbox the user is studying, as opposed
to what it records.

The user-facing account is the guide's
[External runners](PolicyWitness.md#external-runners-byoxpc) section and the
README's [Entitlements + SBPL](../README.md#entitlements--sbpl) framing; the
command surface is the controller README's
[runner manager](../controller/README.md#runner-external-runner-manager)
section. This plan is temporary. Permanent documentation never links it, and
it is deleted when its questions have witnesses.

## Status

- [x] Phase A: map the apparatus from source, as a generated figure
  (2026-10-06)
- [x] Phase B: complete the six investigations and record their observation
  limits (2026-10-06). Host-to-worker environment propagation remains
  unobserved; the proposed exec-child witness cannot answer it.
- [x] Phase C: synthesize the findings and write the decision inputs
  (2026-10-06)

Paused for review before remediation. No product code or registered tests
changed. This plan remains on disk because not every original question has
a witness; completed investigation does not mean complete behavioral coverage.

## Rules

- Witness over interpretation. No claim enters a record or the architecture
  document without an observation that supports it: a `codesign` read-back,
  an envelope field, a captured stdout, a launchd listing.
- No product changes. Experiments use the shipped CLI, copies of the shipped
  bundle signed by hand, test-owned fixtures and specimens. If an experiment
  needs code that does not exist, the plan records the gap and stops there.
- Every installed runner is test-owned, installed through the session helper
  in [tests/fixtures/byoxpc/session.py](../tests/fixtures/byoxpc/session.py)
  or its equivalent, and removed with its removal verified before the plan
  moves on. Consecutive runs against one external runner pay launchd's
  default respawn throttle; space them or expect the wait.
- Live steps need a logged-in GUI session and a Developer ID whose Team ID
  matches the app. If the harness refuses them, follow the
  [sandboxed-harness procedure](../AGENTS.md#sandboxed-automation-harnesses)
  and rerun outside it.
- Findings are written as records under `records/`, linked only from this
  plan, each with its evidence paths. A finding that changes what the
  architecture document says is written there too, as a "Known gap"
  paragraph where the promise it limits is stated.

## Phase A: the map

The map is the fourth figure in the architecture document, "The BYOXPC
apparatus," generated from `docs/architecture.json` like the others, so
every node and edge cites the source symbol that implements it and the check
that exercises it. It traces: the copied bundle and the user's entitlements
plist; `runner install` and the codesign call it makes; the launchd plist
and the bootstrap; the host bound as a Mach service; the client's
connection and the caller-authorization gate; the request's runner selector
and its resolution through the registry; the provenance and binary baselines
the dossier records; the worker and validator the host spawns from its own
bundle; and the maintenance commands (`verify`, `validate`, `remove`,
`reconcile`).

Two facts the map makes explicit, because the investigation turns on them:

- Which process holds which signature after an install. The host carries
  the installed identity and entitlements; the worker and validator carry
  the build's, which hold no entitlements.
- Which fields describe which process. The registry's and provenance's
  `entitlements` are read back from the host executable. Nothing records the
  worker's.

## Phase B: the witnesses

Each item is one experiment with its receipts named. Order is by cost.

1. **Signature read-backs.** After an install on the signed path and on the
   ad-hoc path, read the entitlements and signing authority of all three
   binaries in the installed copy with `codesign -d --entitlements - --xml`
   and `codesign -dv`. Receipt: the six read-backs beside the registry
   record's `entitlements` field. This restates the gap as evidence and takes
   minutes.
2. **The environment route.** `runner install --env` writes
   `EnvironmentVariables` into the plist configuring the host's launch. Whether
   a `DYLD_*` variable survives into the worker needs a process observation.
   The proposed `/usr/bin/env` exec attempt cannot supply it: PW explicitly
   empties the exec child's environment. Receipt: the launchd configuration,
   captured exec result and the existing inspection fixture's explicit empty
   environment report, with and without
   `com.apple.security.cs.allow-dyld-environment-variables` on the host.
   Record the upstream observation gap without inferring a filtering cause.
3. **Entitlement-dependent behavior.** The README's premise is that the same
   policy yields different kernel behavior under different entitlements. Find
   one entitlement and one operation whose result changes with it, and
   witness the change with a worker signed by hand on a copy (both halves:
   host-only signing, then host-plus-worker signing) under the same specimen.
   Receipt: two envelopes whose attempt or prediction channel differs, with
   the read-backs from item 1. If no pair is found in reasonable time, record
   that as the finding; it bears on the README's framing.
4. **The ad-hoc path.** The guide's ad-hoc recipe assumes hardened-runtime
   exception entitlements are honored on an ad-hoc signature. Repeat item 3's
   pair on an ad-hoc-signed copy. Distinguish entitlement-conditioned SBPL
   behavior from a runtime-exception effect. Receipt: the same pair of
   envelopes and read-backs, plus any existing-fixture runtime control whose
   narrower scope is stated explicitly.
5. **Mixed authorities.** After a signed-path install the bundle holds a host
   signed by the user's identity and helpers signed by the build's.
   `codesign_verify` accepts it and launchd starts it. Record what
   verification checks and does not check, because a fix that signs helpers
   at install changes that. Receipt: `codesign --verify --verbose` output on
   the installed copy and on a copy whose worker was re-signed by hand.
6. **The respawn throttle.** The generated plist sets no `ThrottleInterval`.
   Measure the wait a second run pays when issued within ten seconds of the
   previous launch and the failure an immediate run can see. Receipt: wall
   times, job state and the envelopes actually observed, without prescribing
   an error class. The guide's Questions section mentions the throttle;
   whether it sufficiently explains the behavior is a Phase C question.

## Phase C: synthesis

- One record per finding, each citing its receipts, written so a reader can
  rerun the experiment.
- The decision inputs for the entitlement gap, stated without deciding: sign
  the embedded helpers with the supplied identity and entitlements at install
  and record every binary's read-back in the registry and the dossier; or
  state in the README and the guide that installed entitlements describe the
  host only, and say what that makes BYOXPC good for. Item 3 supplies one
  capability witness; it does not alone decide which processes should receive
  which entitlements or which product promise to make.
- Any new Known gap paragraph for the architecture document, and any
  correction the guide needs, listed for the plan that makes the fix.
- Candidate tests, listed with the receipt each would pin, for that plan.

## Records

1. [Installation signature scope](../records/BYOXPC-SIGNATURE-SCOPE.md).
2. [Environment observability](../records/BYOXPC-ENVIRONMENT-OBSERVABILITY.md).
3. [Entitlement-conditioned behavior](../records/BYOXPC-ENTITLEMENT-BEHAVIOR.md).
4. [Ad-hoc behavior and a direct runtime control](../records/BYOXPC-ADHOC-BEHAVIOR.md).
5. [Verification boundaries and mixed authorities](../records/BYOXPC-VERIFICATION-BOUNDARIES.md).
6. [Respawn and retirement observations](../records/BYOXPC-RESPAWN-OBSERVATIONS.md).
7. [Three partial consumer workflows](../records/BYOXPC-CONSUMER-PROBES.md):
   specimen transfer, an exec helper and repeated use of one installation.

## Decision inputs

- **There is an observable worker capability at stake.** With identical SBPL,
  changing the worker's entitlement changed a file-write query and attempt;
  independent before/after bytes confirmed the effect. Host-only and
  re-signed-empty-worker controls denied it. A host-only description would
  accurately limit the existing installation route, but would not provide
  that demonstrated capability. This does not decide whether to extend the
  route, or justify giving the validator the worker's entitlements.
- **Ad-hoc behavior has bounded positive evidence.** The SBPL pair worked
  with an ad-hoc worker. Separately, the existing fixture directly launched
  under an ad-hoc hardened signature retained a DYLD variable only when its
  exception entitlement was present. Neither witness establishes JIT or
  general exception support through the BYOXPC process chain.
- **Recorded metadata and executable checks answer different questions.**
  Host-only read-backs do not establish worker context. An ad-hoc worker
  beneath a Developer ID host passed verification and ran. Ordinary outer
  verification also accepted an offline copy with a corrupted worker code
  byte that recursive and individual checks rejected. Actual launch of that
  corrupted copy was deliberately not attempted.
- **Environment propagation remains open.** Plist contents and exec-child
  output cannot establish the host or worker's environment. No new product
  observation code was added to obtain an answer.
- **Repeated use needs investigation beyond one successful specimen.** The
  same installed runner produced immediate `already_ran`, a delayed `ok`,
  and `xpc_timeout` under a shorter client budget. These are measured cases,
  not a timing guarantee or evidence that retrying timed-out work is safe.
- **Location affected the experiments.** Re-signed workers stalled in an
  `open` against the checkout's Desktop target, including under allow-all;
  the corresponding temporary-target runs completed. An existing exec
  observer also failed from Desktop and worked from `/private/tmp`. The
  cause is unassigned. This is an input to consumer-like probes, not a
  diagnosed sandbox or signing failure.

Guide/README decisions for a separate turn: the scope of installed
entitlements and `required_entitlements`; the distinction between supported
worker operations and a separately signed exec helper; what `--env` is
observed to establish; signature verification's scope; and the practical
consequences of host retirement, respawn delay and client deadlines. The
architecture's host-only Known gap is confirmed, and a Known gap now states
the nested-code verification limit. No guide repair is made in this plan.

## Candidate probes and tests

These are inputs for a later turn, not new registered tests or selected fixes.

| Candidate | Receipt or observation to preserve | Limit |
| --- | --- | --- |
| Read back host, worker and validator for a small signing matrix | Item 1's signatures and registry side by side | Metadata possession is not an operation effect |
| Run a conditioned file write with an empty-worker control | Item 3's identical-policy pair and independent bytes | Deliberately chosen SBPL predicate, not general JIT support |
| Exercise an existing consumer helper through exec | Item 2's explicit process report, child exit and PID | Reports the child, not its parent |
| Check one actual runtime exception on an existing fixture | Item 4's direct two-variable control | Separate process and route from PW |
| Compare shallow, recursive and individual verification | Item 5's resealing and unlaunched corruption controls | Does not prove runtime acceptance of invalid code |
| Follow a successful run with another at different intervals and budgets | Item 6's envelope, job state and monotonic timing | Assert observation integrity; do not freeze one race outcome |
| Repeat a tiny workload from temporary and ordinary project locations | Initial Desktop failures and completed temporary controls | Collect the discrepancy before assigning a cause |

## Consumer probe status

The user authorized the first three proposed consumer workflows and deferred
the project-location probe because GUI responses to privacy prompts may not
be available. Specimen transfer, bringing a helper, and repeated use are
complete as manual exploratory runs; all file-effect targets and experimental
helper executables were in owned `/private/tmp` storage. The maintenance/reuse
workflow was not run. No registered tests or product code changed.

The report above records nine admitted transfer invocations and five
missing-key controls, four helper configurations with twelve process reports,
and six ordinary batch requests following `runner verify`. New observations
include admission of a false-valued required host key and a file effect first
observed after the creating request's CLI timeout. Their consumer implications
are recorded without selecting remediation. Permanent test registration
remains a separate decision.

Evidence is under `tests/out/runs/byoxpc-consumer-probes-20261006/`, gitignored,
local-only and pinned in `tests/RETAINED.json`. All 24 run envelopes validated;
the eight external copies were removed with absence verified; no owned
processes remained; and the source app inventory was unchanged. The checkout
was `e6ea44b`, using the same existing build 435 artifact on macOS 14.8.9
(23J631), arm64. Remediation remains paused for review.

## Execution notes

Phase A (2026-10-06): the figure and its tables were generated from the
manifest; every citation was verified by the generator. The two facts above
were read from `codesign_sign` in
[runner_manager.rs](../controller/src/runner_manager.rs), the install path in
[runner_commands.rs](../controller/src/runner_commands.rs), and `sign_macho`
in [build.sh](../build.sh); the signing read-back that first established the
gap is restated as Phase B item 1 so that it enters a record.

Phases B/C (2026-10-06): evidence is under
`tests/out/runs/byoxpc-investigation-20261006/`, gitignored and local-only,
pinned in `tests/RETAINED.json`. It includes orchestration scripts, specimens,
command streams, signing read-backs, effect bytes, a stack sample, raw
envelopes, source inventories and `SHA256.json`. No new native probe was
written. The existing session cleanup helper verified removal of all 19
installed copies; final registry/reconcile and owned-process observations
confirmed no remaining experiment service, plist, registration or process.
Fixture staging was also removed. All 24 envelopes validated, and the original
app inventory was unchanged. The 21 completed manual observation cases are
not a registered test-battery pass.

The checkout was `e2115cf` on macOS 14.8.9 (23J631), arm64. The selected
existing app reports `33ad847-dirty`, build 435; binary hashes identify the
tested artifact, rather than a claim that its stamp proves a clean build of
this checkout. Developer ID Team `42D369QV8E` matched the shipped client.
Sandboxed codesign inspection failed and its unchanged-byte unsandboxed
repeat passed. Live experiments ran outside the automation sandbox.

Scope corrections: item 2 closes with an explicit observation gap rather than
the originally proposed host-only inference. Item 4's SBPL pair and direct
DYLD control answer separate questions. Item 6 records observed outcomes and
recognizes the existing guide mention. Initial unsuccessful observations were
retained; completed temporary-location controls did not replace their receipts.
