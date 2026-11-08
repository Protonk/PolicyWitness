# Release-stamped contracts

Status: proposed; investigation and implementation plan. No implementation
changes have been made for this plan. It replaces the de-schema plan this file
held before its rename; `git log --follow` reaches that text and its wider
inventory of build, test and publication counters.

## Basis

Source inspection of the checkout at `c60e90f2` and its working tree on
2026-11-08. No new signed build, live runner experiment or battery result is
claimed. Figures below come from `git log` over `docs/contract.json` and from
per-file inspection of two bump commits; recount before relying on them.

| Observation | Value |
| --- | --- |
| Commits that moved `docs/contract.json` between 2026-09-26 and 2026-11-06 | 29 |
| Releases tagged between 2026-10-14 and 2026-10-30 | 5 |
| Files in bump `cd3e8278` whose only change was a version number | 28 of 110 |
| Files in bump `7426fc09` whose only change was a version number | 11 of 54 |
| Generated copies of the four counters, and files holding them | 12 in 4 |
| Files the generator writes | 8 |
| Fixture and guide files carrying a literal request schema number | 10 |
| Test files that inject `contract.REQUEST_SCHEMA` programmatically | 22 |

The plan follows [planning guidance](CONTRIBUTING.md#planning-a-change).

## Problem

[docs/contract.json](docs/contract.json) owns four counters: request schema,
response schema, controller envelope and runner protocol.
[generate_contract.py](docs/generate_contract.py) copies them into Swift, Rust,
Python, a plist and four documents, and the build refuses a stale copy. Every
semantic reader requires exact equality, so the numbers never bought
compatibility. What they cost is a duty: between releases every change to a
reading rule needs a bump, a regeneration and edits to every fixture that
carries the number. A user who updates only on releases learns nothing from
"27 became 28" about which of their probe plans, profiles or installed runners
to revisit. Development builds report the nearest tag as `build.version`, so an
unreleased build can present a released interface.

## Intended result

The release is the public contract unit, and nothing a user holds needs to
track anything finer.

- **One emitted identity.** A clean build at an annotated release tag carries
  `release:vX.Y.Z`; every other build carries `development:<digest>` over the
  shipped sources. The identity is computed at build time and never committed.
- **One assertion per specimen.** A saved request names the contract it was
  written for. Admission is exact equality, before runner selection, augments,
  helpers or children. A missing or foreign assertion is a refusal with the
  expected value in the diagnostic. There is no implicit acceptance, adapter,
  negotiation or ignore switch.
- **Producer context on independently arriving output.** The controller
  envelope, the host reply and the client capture each carry the identity of
  the build that produced them. Readers admit by exact equality and keep
  unsupported bytes raw. Nested records inherit the admitted context.
- **No identity in any fixture.** The test harness asserts the candidate's
  identity at submission. Captured replies are read under the context they
  state. Nothing in `tests/fixtures` changes when the identity moves.
- **Derived surface stamps.** A generated table names each public surface a
  user can depend on and the release in which it last changed. The stamp is
  computed from the surface's shape golden and its normative definition across
  the release tags. Nobody asserts it, and nothing admits by it.
- **Installed runners exchange the same identity.** Install, verify and
  reservation compare it exactly. Recovery of an owned installation is
  unchanged.
- **The counters, their manifest, generator, copies and the bump classifier
  are deleted.**

No backwards compatibility, historical translation, capability exchange or
change history is added. The table says where to look; the current definition
says what the tool accepts.

## Out of scope

Internal and infrastructure counters stay as they are and may change on their
own schedule: registry `schema_version`, build provenance, toolchain stamp,
build session, release archive and acceptance records, retention index,
dispatcher and pytest records, rotation journal, shell and drift reports,
notarization and prune reports, `worker-equipment.json`, `Evidence/manifest.json`,
the validator NDJSON marker, repository manifests under `docs/*.json`, and the
investigative fixtures' receipt versions. The worker ABI identity and its
generator remain exactly as they are. The JSON representation experiment in
[JSON-AS-PORCELAIN-PLAN.md](JSON-AS-PORCELAIN-PLAN.md) is separate; any reader
or producer it generates inherits this identity rather than minting one, and
whichever of the two lands second adapts the reply root.

## Decisions

### D1. The identity is emitted, never tracked

Compute the identity in one helper shared with the worker identity's walker in
[generate_worker_identity.py](docs/generate_worker_identity.py), keeping its
symlink refusal. The scope is the shipped source and its build inputs:
`controller/src`, `controller/tools`, `runner/Sources`, `runner/Clients`,
`build.sh`, `meson.build`, `meson.options`, `runner/Package.swift`,
`controller/Cargo.toml` and `controller/Cargo.lock`. Hash every regular file
beneath the scope as it is on disk, sorted by path with length framing, so two
dirty trees at one HEAD differ and a documentation or test edit does not move
the identity. A code edit does, and a code edit is what can change meaning.

The release form requires `git describe --tags --exact-match --match 'v[0-9]*'`
to succeed and `git status --porcelain` to be empty. Everything else is
`development:<digest>`. The `build` object keeps `describe` and `commit` and
may carry `base_release` for orientation; nothing admits by it.

Plumbing uses the existing stamp path. [build.sh](build.sh) already derives
describe and commit once; it computes the identity there, under the checkout
lock, and passes `PW_BUILD_CONTRACT` the way [build.rs](controller/build.rs)
already forwards `PW_BUILD_*` with `rerun-if-env-changed`. Meson writes a
generated Swift source into the build directory and adds it to the core
target, since a new native source requires its Meson target. `stamp_info_plist`
adds `PWContract` to the app and service plists beside `PWBuildDescribe`.
`policy-witness --version` in [cli.rs](controller/src/cli.rs) prints the value.
A plain Cargo or SwiftPM build without the variable is `unbound`: it refuses
public requests and packaged peer checks, and its unit tests construct
identities explicitly. The build account in [docs/build.json](docs/build.json)
replaces the `check_contract` and `stale_contract` entries with the new step.

### D2. Specimens assert the contract; admission is exact and early

The request root gains a required string `contract` and loses `schema_version`.
[request_patch.rs](controller/src/request_patch.rs) checks presence and
equality before closed-key validation, selectors and augments, so an old
specimen is refused as missing `contract` with `expected_contract` populated,
not as an unknown key. [PWRunnerRequest.swift](runner/Sources/PWRunnerCore/PWRunnerRequest.swift)
repeats the check on direct XPC input before worker or validator creation.
Diagnostics rename `expected_schema` to `expected_contract` and
`unsupported_schema` to `unsupported_contract`; `bad_request`, bounded paths,
distinct missing and type failures and exit classification stay. Accepting an
old marker as an alternative authority is forbidden.

To run a saved specimen on another release its author reads the stamp table,
revisits the rows stamped after the specimen's release, and edits the
assertion. The tool never rewrites the specimen.

### D3. Independently arriving output carries producer context

- The controller envelope frame in [json_contract.rs](controller/src/json_contract.rs)
  drops `schema_version` and adds `contract` to `build`. `sbpl-check` shares
  the frame, so the helper envelope retained at `data.policy_check.envelope`
  carries its own producer; [policy_check.rs](controller/src/policy_check.rs)
  admits it by equality.
- The host reply in [PWRunnerReply.swift](runner/Sources/PWRunnerCore/PWRunnerReply.swift)
  drops `schema_version` and gains a `producer` object with `contract`,
  `describe` and `commit` from the compiled context. The degraded serialization
  in `PWRunnerService` carries the same object.
- The client capture in [PWRunnerTransport.swift](runner/Sources/PWRunnerCore/PWRunnerTransport.swift)
  and the reservation messages replace `protocol_version` with `contract`.
- The nested `compiled_profile.schema_version` is the one counter inside public
  output. [PWRunnerProfileCapture.swift](runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift),
  `compiled_profile_problem` in [run_flow.rs](controller/src/run_flow.rs) and
  [consumer.py](tests/lib/consumer.py) stop reading it; the receipt inherits the
  admitted reply context and keeps its nonce, worker and hash bindings.

Readers in `run_flow.rs`, `policy_check.rs`, the Swift codecs and `consumer.py`
admit the producer first and keep `unsupported_runner_response`,
`malformed_runner_response` and `unsupported` with raw retention and no
cascaded shape errors. A host reply from a foreign build is refused even when
the controller's own identity is current.

### D4. Installed runners exchange the same identity; recovery is unchanged

The service plist advertises `PWContract` in place of `PWRunnerProtocolVersion`.
[runner_commands.rs](controller/src/runner_commands.rs) admits it before signing
or launchd mutation and again after re-signing. New registry records in
[runner_manager.rs](controller/src/runner_manager.rs) gain a `contract` field;
`require_current_protocol` becomes an equality on it. Records without the field
are not executable and remain listable, reconcilable and removable through the
existing recovery behavior, including the retired kind aliases. The registry's
own `schema_version` is untouched. The reservation version exchange in
[PWRunnerService.swift](runner/Sources/PWRunnerCore/PWRunnerService.swift) and
[PWRunnerClientSession.swift](runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
compares the live peer's `contract`; a matching registry entry never excuses a
mismatched peer. A development build must reinstall its runner after any
shipped-source change. Easing that for BYOXPC development is a separate
decision, not part of this plan.

### D5. No identity lives in a fixture

Remove `schema_version` from the ten literal carriers under
`tests/fixtures/pw_runner`, `tests/fixtures/blackbox_e2e`,
`tests/fixtures/runner_smoke`, `tests/fixtures/request_contract/examples.json`
and the guide. One harness helper reads the candidate's identity from the app
bundle's plist, independently of the binary's own report, and inserts
`contract` at submission; the 22 suites that use `contract.REQUEST_SCHEMA`
switch to it, and [tests/lib/contract.py](tests/lib/contract.py) keeps only the
worker identity. Refusal controls use a fixed foreign value.

Captured reply and envelope fixtures keep their bytes forever. `consumer.py`
and the Rust readers take the expected producer as an explicit argument; tests
pass the fixture's own value, production callers pass the running build's. The
equality gate gets one positive and one negative control of its own. Shape
goldens drop their revision metadata and keep their shapes; a golden diff is
reviewed and the definition updated, which is what moves a stamp.

The smoke check in [pw_specimen_smoke.sh](tests/suites/smoke/pw_specimen_smoke.sh)
replaces its response and protocol comparisons with agreement among
`--version`, the plist, `build.contract`, the reply producer and the
harness-derived identity of the candidate, keeping its worker-identity
comparison.

### D6. Surface stamps are derived, never asserted

A manifest `docs/contract_surfaces.json` lists each public surface: an id, the
user artifact it governs, the golden files that fix its shape, and the id of a
delimited region `<!-- BEGIN CONTRACT <id> -->` in the guide or
[docs/CONTRACT.md](docs/CONTRACT.md) holding its normative definition and,
where the surface has behavior, a worked example the harness verifies. The
manifest is a scope definition like the worker identity's source list, not a
version registry.

A generator `docs/generate_contract_stamps.py` computes, for each surface, the
hash of its goldens as canonical JSON plus its region text with normalized
whitespace, at every annotated release tag from the first tag that carries the
manifest, using `git show`. The stamp is the latest tag whose hash differs from
the preceding tag's, or the first tag at which the surface exists. It renders
the table into a generated region of `docs/CONTRACT.md` and the guide; `--check`
verifies without writing. Run against the working tree it flags rows whose hash
differs from the last tag as `unreleased`, which a development build may print.
At release, `--release vX.Y.Z` renders those rows with the new tag before the
tag exists; afterwards `--check` with no arguments on the tagged tree must
reproduce the committed table exactly, and release preflight in
[release_preflight.py](tests/lib/release_preflight.py) requires that along with
no remaining `unreleased` rows. A removed surface keeps its row, stamped with
the removal release and marked removed.

Over-stamping is the safe error, so there is no suppression. A semantic change
that touches neither a golden nor a definition nor a verified example does not
move a stamp; in that case the tool holds no witness of its own contract for
that behavior, and the fix is a definition or example, not a hand-set stamp.

Initial surfaces, to be settled by the executor against the guide's section
structure, with ten to fifteen rows as the target: request root and runner
selection; policy, params, augments and imports; probe plan steps; phases and
actors; envelope frame and `build`; specimen dossier; reply steps and
comparison; disposition and lifecycle; actor evidence and equipment; compiled
profile receipt; transport and client capture; exit classification and
structured refusals; runner installation and reservation. Per-surface goldens
come from splitting [response_shape.json](tests/fixtures/contract/response_shape.json)
by surface, keeping [envelope_shape.json](tests/fixtures/contract/envelope_shape.json),
and adding a request shape golden collected from the closed `CodingKeys` and
the examples corpus.

### D7. Delete the superseded machinery

Remove `docs/contract.json`, `docs/generate_contract.py`, the generated regions
in `PWRunnerAPI.swift`, `json_contract.rs`, the service `Info.plist`,
`tests/lib/contract.py`, `docs/CONTRACT.md`, the guide and both implementation
READMEs, the `rerun-if-changed` on the manifest in `build.rs`, and `contract`
from the generator list in [fixture_inputs.py](tests/lib/fixture_inputs.py),
adding the stamp generator in its place. Delete `Verdict::NeedsBump` and its
branches in [shape.rs](controller/src/shape.rs) and `run_flow.rs`,
`classifyShapeChange` and its tests in
[ContractVersionTests.swift](runner/Tests/PWRunnerCoreTests/ContractVersionTests.swift),
and the version parts of [source_drift/contract.py](tests/suites/source_drift/contract.py),
keeping its worker-identity and architecture checks under a name that no longer
claims a version manifest. Rewrite `docs/CONTRACT.md` around the identity, the
assertion and the generated stamp table; its "when a number moves" rules become
"keep the definition and example current." Update
[docs/PolicyWitness.md](docs/PolicyWitness.md), `controller/README.md`,
`runner/README.md`, `controller/AGENTS.md`, `runner/AGENTS.md`, `tests/AGENTS.md`
and the root `AGENTS.md` maintenance checklist in the same change, and
regenerate the build account.

## Implementation sequence

Each stage is a reviewable change. The work must not be released between
stages 1 and 2, and no battery result from the hybrid state is evidence for
the final contract.

1. **Build context.** The shared helper, `build.sh`, `build.rs`, the generated
   Swift source, `PWContract` in both plists, `--version` and `build.contract`.
   Numbered admission stays authoritative; the identity is provenance only and
   is labeled so. Verify: clean build at a tag yields the release form; one
   commit after the tag, a dirty tree and a second dirty tree at the same HEAD
   yield three distinct development identities; a plain Cargo build is
   `unbound`; the plist, `--version` and envelope agree.
2. **Public cutover, one change.** D2 through D5 and D7 together: request
   admission in both languages, reply producer and degraded encoder, envelope
   frame, client capture and reservation, service plist and registry gate,
   compiled-profile counter, fixture carriers and harness injection, explicit
   reader context, smoke check, manifest and generator deletion, classifier
   deletion, documentation. New tests must not pass by accepting either marker.
3. **Surfaces and stamps.** D6: the manifest, per-surface goldens, guide
   regions and examples, the generator with `--check` and `--release`, the
   preflight requirements, and the rendered table. This stage may be prepared
   alongside stage 1 but lands after stage 2 so `docs/CONTRACT.md` is rewritten
   once. The first release after it carries every row stamped with that
   release, which is the truthful statement about the surfaces' first
   derivation.

## Verification

Use [tests/AGENTS.md](tests/AGENTS.md) and
[CHANGE-VERIFICATION.md](tests/CHANGE-VERIFICATION.md) for equipment, evidence
reuse and ownership. Build a signed candidate with `make build IDENTITY=…`,
mutate copies rather than the inspected app, and run everything through
`tests/run.sh` with a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` per evidence
set. Source inspection and Rust unit tests are not live XPC evidence.

| Proposition | Evidence |
| --- | --- |
| The identity is right in every build state | Stage 1 cases above, plus an out-of-checkout build with `PW_BUILD_*` overrides that cannot produce the release form. |
| The assertion protects intent before effects | Current assertion executes. Missing, malformed, old-marker-only and foreign assertions refuse before selectors, augments and client effects, with `expected_contract` in the diagnostic. Direct XPC repeats the refusal before children. Same-shape control: two instrumented builds share the `file/open_write` shape but one appends while the documented operation truncates; a specimen asserting the other build leaves the file unchanged with no client or worker launch, and a current assertion has the documented effect. |
| Producer context gates every reader | Foreign envelope, foreign host reply inside a current envelope, foreign helper envelope, malformed capture and detached compiled-profile receipt: bytes retained, no claims, no cascaded shape errors. Valid current nested data passes; wrong nonce, worker or hash binding still fails. |
| Installed runner mismatch refuses early | Registry entry without `contract`, foreign live peer behind a matching entry, foreign plist at install, current peer. No submission on mismatch, not merely an error envelope. Reservation timeout, lost grant and occupied host still never replay. |
| Recovery survives refusal | With a record lacking `contract`, a retired kind alias and absent helper metadata: list, status and reconcile work, run and verify refuse, owned removal succeeds only after observed absence, unknown raw metadata survives unrelated mutation. |
| Fixtures carry no identity | Grep for the removed markers across `tests/fixtures`, suites and the guide, classifying historical hits. Moving the identity, by editing a shipped source and rebuilding, changes no fixture and causes no fixture-only test failure. |
| Obsolete machinery is gone | No manifest, generator, copies, classifier or bump instruction remains in active source or prose. Changing an ordinary shape and reviewing its golden produces no missing-bump refusal; breaking a required field still fails substantive validation. |
| Stamps are deterministic | On a tagged tree, `--check` without arguments reproduces the committed table. Editing a golden, a region or a verified example flags its row `unreleased`; editing explanatory prose outside a region does not. `--release` renders the pending rows and the recomputation after tagging agrees. A removed surface keeps its row. |
| Worker boundary is untouched | `runner_abi_layout`, `runner_c_worker_harness`, `runner_live_worker_identity` and the worker-identity checks pass unchanged. |

Required suites for stage 2: `unit`, `failure_boundaries`, `runner_unit`,
`runner_outcome_bad_request`, `integration`, `blackbox_e2e`, `smoke`,
`source_drift`, `runner_byoxpc` with its registry-recovery and
reservation-control cases, and the `witness_contract` cases whose readers
change. Stage 3 adds `source_drift` and the `preflight` release checks. The
wait, release store and eligibility rule are not touched, so
`witness_contract/order_barrier_mutations` is not required unless a diff shows
otherwise. After targeted checks pass, run the final signed candidate through
the default `tests/run.sh` battery once. Preserve failed and interrupted
evidence and record candidate identity, selected cases and results with it.

## Reconsideration triggers

- A separately distributed consumer or producer actually needs admission
  independent of the release or development identity. Name its owner,
  distribution and decision; existing fields or tests are not evidence.
- The development identity proves too costly in practice. Measure the cost,
  then review the scope's inputs. Never exclude a directory that produces
  public output, and do not reintroduce per-surface counters as an
  optimization of this plan.
- An owned installation cannot be recovered under the new gate. Stop that
  subchange and design its recovery boundary; execution identity never becomes
  a cleanup prerequisite.
- A proposed surface cannot be given a deterministic golden or definition
  region. It is then not a contracted surface; say so rather than stamping it
  by hand.

Acceptance is complete when the diff shows the counters, copies, generator and
classifier gone; the identity, assertion, producer context and runner gate
make their stated refusals in live evidence; no fixture carries an identity;
and the stamp table reproduces from the tags.
