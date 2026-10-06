# BYOXPC investigation plan

This plan explores and investigates the BYOXPC apparatus: everything between
a user copying the shipped XPC bundle and a specimen running under the host
that copy provides. It makes no product change. It produces a map of the
apparatus as built, witnessed answers to the questions below, and the
decision inputs for whatever fix the entitlement gap turns out to need. The
fix itself belongs to a separate plan.

The starting point is the one Known gap left in
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
- [ ] Phase B: witness each question below, cheapest first
- [ ] Phase C: synthesize the findings and write the decision inputs

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
   `EnvironmentVariables` into the launchd plist, which reach the host. Whether
   a `DYLD_*` variable survives the hardened-runtime spawn into the worker is
   witnessable with an exec attempt that runs `/usr/bin/env` under an
   allow-all policy, since the exec channel captures the child's stdout.
   Receipt: the captured stdout in the envelope, with and without
   `com.apple.security.cs.allow-dyld-environment-variables` on the host.
   Expected: the variable does not reach the worker, which makes this route
   host-only as well.
3. **Entitlement-dependent behavior.** The README's premise is that the same
   policy yields different kernel behavior under different entitlements. Find
   one entitlement and one operation whose result changes with it, and
   witness the change with a worker signed by hand on a copy (both halves:
   host-only signing, then host-plus-worker signing) under the same specimen.
   Receipt: two envelopes whose attempt or prediction channel differs, with
   the read-backs from item 1. If no pair is found in reasonable time, record
   that as the finding; it bears on the README's framing.
4. **The ad-hoc path.** The guide's ad-hoc recipe assumes hardened-runtime
   exception entitlements are honored on an ad-hoc signature. Witness it with
   item 3's pair on an ad-hoc-signed copy. Receipt: the same pair of
   envelopes and read-backs.
5. **Mixed authorities.** After a signed-path install the bundle holds a host
   signed by the user's identity and helpers signed by the build's.
   `codesign_verify` accepts it and launchd starts it. Record what
   verification checks and does not check, because a fix that signs helpers
   at install changes that. Receipt: `codesign --verify --verbose` output on
   the installed copy and on a copy whose worker was re-signed by hand.
6. **The respawn throttle.** The generated plist sets no `ThrottleInterval`.
   Measure the wait a second run pays when issued within ten seconds of the
   previous launch and the failure an immediate run can see. Receipt: wall
   times and the `xpc_error` envelope. The guide does not mention the wait;
   whether it should is a Phase C question.

## Phase C: synthesis

- One record per finding, each citing its receipts, written so a reader can
  rerun the experiment.
- The decision inputs for the entitlement gap, stated without deciding: sign
  the embedded helpers with the supplied identity and entitlements at install
  and record every binary's read-back in the registry and the dossier; or
  state in the README and the guide that installed entitlements describe the
  host only, and say what that makes BYOXPC good for. Item 3 decides which
  is honest.
- Any new Known gap paragraph for the architecture document, and any
  correction the guide needs, listed for the plan that makes the fix.
- Candidate tests, listed with the receipt each would pin, for that plan.

## Records

None yet. Each Phase B item adds its record here when it has run.

## Execution notes

Phase A (2026-10-06): the figure and its tables were generated from the
manifest; every citation was verified by the generator. The two facts above
were read from `codesign_sign` in
[runner_manager.rs](../controller/src/runner_manager.rs), the install path in
[runner_commands.rs](../controller/src/runner_commands.rs), and `sign_macho`
in [build.sh](../build.sh); the signing read-back that first established the
gap is restated as Phase B item 1 so that it enters a record.
