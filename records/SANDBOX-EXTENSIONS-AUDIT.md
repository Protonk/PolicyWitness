# Sandbox extensions out-of-band audits

This is the shared handoff document for the middle and final audits in
[the implementation plan](../SANDBOX-EXTENSIONS-PLAN.md#out-of-band-audit-handoffs).
The executing agent prepares each exchange at its waypoint, identifying the
reviewed source/build and documentation/evidence locations before writing the
questions. The auditor writes answers and additional findings in the same
section. Execution dispositions remain separate from the attributed audit text.

## A1 Middle audit — after M3

Status: complete. Original auditor answers and follow-up returned on 2026-10-13
(Claude Fable 5.1, out of band) remain attributed and unchanged. The executing
agent's corrections, review and final F10 verification are recorded below.
M3 remains valid; F10 is closed and F11 is explicitly assigned to M5.1. H1 is
prepared and awaiting the user's response; M4 has not started.

### A1 Handoff, questions and auditor answers

Prepared by the executing agent `/root` on 2026-10-13. Please attribute answers
and additional findings to the auditor, with source or retained-evidence
references and any access limitations. Answer beneath each question; the
executing agent's dispositions belong in the separate section below. The
questions identify areas requiring independent judgment, not presumed findings.

#### Candidate and evidence

| Item | Identity |
| --- | --- |
| Reviewed source | `fdbd89b215125b50fc6030e09bdc4a66b56e48f2` |
| Signed app source | `6744f3c0652fac983d2823dfcc9cb848efb105af`, clean stamp `v0.2.8-40-g6744f3c` |
| Local app | `dist/PolicyWitness.app`, version 0.2.8, build 560 |
| Signer | `Developer ID Application: Adam Hyland (42D369QV8E)`; certificate SHA-1 `1A6E85D06FC762993C8BD3E932556DED3985F030` |
| Host | macOS 26.7.1, build 25G241, arm64 |
| Wire versions | Request 4, runner response 17, envelope 7 |
| Worker identity | `12a5db4345b0801bd519224e65955eeb623f06664ed058c9a5c34ba7acbfc91d` |
| Embedded evidence manifest SHA-256 | `0df13c51fa78b5c3b6920c9b329adc9f94c5960e0334f13efdaf48e1410aabb4` |

The reviewed source differs from the signed source only in test code and its
documentation/metadata. Rust changes lie inside the existing `#[cfg(test)]`
module; preceding production bytes and other production inputs are unchanged.
The app's inspected inventories match across the two accepted runs. The commit
preparing this handoff changes only the plan, records and retention index; it
does not claim to be the source of the earlier build or test executions.

| Retained run under `tests/out/runs/` | Run ID and use |
| --- | --- |
| [extensions-m3-accepted-20261013](../tests/out/runs/extensions-m3-accepted-20261013/run.json) | `20261013T143650Z_763cbafa`; all 147 cases passed at clean `6744f3c` against build 560, with no skipped/unrun cases. Includes native/Swift/ABI, admission, independent readers, public CLI, order mutation, BYOXPC, preflight, source-drift, maximum reply and dispatcher coverage. |
| [extensions-m3-phase-logs-20261013](../tests/out/runs/extensions-m3-phase-logs-20261013/run.json) | `20261013T145127Z_5507dc70`; all 13 focused cases passed at clean `fdbd89b` against unchanged build 560. Replaces five unit, six source-drift, signature-preflight and termination/log-correlation credits. |

Each run records exact commands/configuration, canonical cases and artifact
inspection; its `checkpoint/` preserves console and source hashes. The first
also retains the signed-build log and cleanup verification. The second's
[credit manifest](../tests/out/runs/extensions-m3-phase-logs-20261013/checkpoint/acceptance-credits.json)
maps the final 147 credits to 13 replacement and 134 reused results. Its exact
test-only diff accompanies the source snapshot. Reuse includes a reviewed
exception: driver replay executes an unchanged filtered test; build guards copy
the changed test module and documentation but build production code without
`cfg(test)`, and their refusal paths/tool substitutions are unchanged. All unit,
changed live, and source/document checks were rerun. This is an applicability
judgment, separate from file-identity checks. Neither documentation baseline
changed from the M2 acceptance at `ac9c3b5`.

Standard and BYOXPC public CLI controls both observed a real consume handle
followed by release on that handle, with three phases of independent predictions
and fresh accesses in the same once-sandboxed worker. Fresh descriptor identity,
bytes, worker/issuer identity, signing and cleanup observations accompany native
results. Native success is not itself an effective-permission or revocation
claim. The ordinary unlink/unavailable-prediction and resolvable-later-query
controls and bounded lifecycle-placement controls are included in both paths.

The fresh read-only documentation reviewer was `/root/m3_rendered_review`
(`gpt-6-astra` requested; runtime identifier not independently exposed). Reports,
source snapshots, HTML, PDFs, inspected PNGs and manifests are retained in the
[correction run](../tests/out/runs/extensions-m3-review-corrections-20261013/reviews/)
and [final focused run](../tests/out/runs/extensions-m3-phase-logs-20261013/reviews/).
The renderer was Pandoc 3.12, WeasyPrint 70.0 and Poppler 26.10.0. F1–F5 were
corrected and rechecked: fresh-read return wording, issuer validation inventory,
BYOXPC signing/provenance labels, failure-matrix ownership and split guide
paragraphs. Collection-closure wording and the temporary test-helper location
were also corrected. The final three-document phase-log recheck found no issue.
The applicability manifest establishes current hashes for those three documents
and 14 unchanged previously reviewed documents; it does not enlarge the actual
page-inspection coverage. These reviews are separate from this external audit.

The source/test scripts and retention index are committed. The app, run output
and rendered artifacts are gitignored and **available only in this local
checkout**. They have not been published or packaged for another checkout.
HTML links can retain original `/private/tmp` preview paths; retained PDFs/PNGs
and source copies preserve inspected content. If these artifacts are unavailable
to the auditor, record that gap rather than treating the summaries as inspection.
The associated plan links the detailed investigative record and earlier runs.

#### Limitations and adjustments requiring attention

- The M1 allocation controls observed zero callbacks during the native windows,
  which cannot establish absence of private API allocations or other resources.
  The implemented invariant covers bounded, preallocated PW-owned reporting and
  coordination, with no explicit PW allocator use after application. Native API
  internals remain outside that guarantee. This is the plan-authorized,
  evidence-backed revision; no issuer authority was added.
- Native results apply to this host/library and exercised paths. A controlled
  entry/return seam establishes the test intervention and missing-publication
  behavior, not an observation inside Apple's private implementation. Missing
  publication remains unresolved even when the fixture knows a call returned.
- One earlier fixture run, `extensions-m3-native-boundaries3-20261012`
  (`20261013T005937Z_5456c6b2`), created 25 empty POSIX shared-memory objects
  before `fchmod` failed with EINVAL and before ownership names were recorded.
  No mapping, target, token or child was created. Names are unavailable and
  absence is unverified; no prefix-based cleanup was attempted. The fixture now
  records ownership first. All 26 recorded native channels and eight BYOXPC
  sessions in final consolidation have verified cleanup and absent recovery or
  staging paths. Later cleanup does not resolve the earlier unknown objects.
- The user observed and approved a Desktop-access TCC prompt during earlier
  testing. Subsequent phase/extension targets and executed fixture helpers use
  owned `/private/tmp` paths. Earlier stalls are retained without claiming a
  proven TCC cause; timeout controls now require an initial fixture record so a
  blocked launch cannot satisfy the intended intervention.
- Rendered inspection was bounded: unchanged release procedures, all duplicate
  limits pages, some unchanged architecture rows, browser compatibility and
  exhaustive link navigation were not inspected. Available live denial events
  are optional; controlled collector states establish the no-effect-on-execution
  and ambiguous-association rules independently of live retrieval completeness.

#### Questions and attributed auditor answers

**Q1 — Native evidence and independent readers.** Do the producer and readers
preserve the distinction among omitted actions, skipped dependencies, started
but unpublished calls and published native results, including failed consume
without a usable handle and failed release? Can any supported or malformed
record fabricate completion, a handle association or successful fresh access?
Inspect [the native worker](../controller/tools/pw_probe_runner/pw_probe_runner.c),
[Swift evidence tests](../runner/Tests/PWRunnerCoreTests/ExtensionEvidenceTests.swift),
[Rust reader](../controller/src/disposition.rs),
[independent Python reader](../tests/lib/extension_evidence.py) and the
[failure contract](../tests/FAILURE-PROPAGATION-CONTRACT.md). Please distinguish
an actual claim defect from additional combinations assigned to M4.

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): Yes. The producer and all three readers keep the four
states apart, and I found no supported or malformed record that fabricates
completion, a handle association or a successful fresh read. One handoff
citation is wrong and two labels are imprecise; neither is a claim defect.

*Producer.* In [`attempt_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
the worker release-stores `call_boundary` before the native call, writes
`native_result`, `native_errno` and `native_result_valid` after it returns, and
`run_attempt`'s caller stores the slot's `completed` flag last. The host reads
`native_result` only when `native_result_valid == 1`
([`CWorker.swift`](../runner/Sources/PWRunnerCore/CWorker.swift) slot decode),
and the orchestrator derives `unresolved` from an incomplete slot, `returned`
from a valid native result and `unavailable` from codes 1 to 4; any other
completed slot becomes `invalid`, which the encoder refuses. An omitted action
has no slot and no event. A failed consume leaves `extension_handle == -1`, so a
dependent release decides `handle_unavailable` without a call; API absence
decides `native_api_unavailable`. A call that started but was not published
keeps `call_boundary_observed: true`, `result_published: false`,
`status: unresolved` and no native fields. The boundary control's worker modes
101 to 103 and 201 to 203 establish this at the marker, during the call and
after return, and mode 203/103 shows the observer knowing the call returned
while the reply stays unresolved.

*Readers.* The Swift encoder (`extensionEvidenceProblem`,
[`PWRunnerAPI.swift`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)), the
Rust `extension_account_issues` in
[`disposition.rs`](../controller/src/disposition.rs) and the Python
[`extension_evidence.py`](../tests/lib/extension_evidence.py) with the lifecycle
oracle's D6/D8 rules implement the same closed rules. The handoff's citation of
[`evidence.rs`](../controller/src/evidence.rs) as the Rust reader is wrong: that
file holds the embedded-evidence manifest helpers and no extension rule.

*Fabrication probes.* Beyond the registered mutations (`blackbox_e2e`
extension controls, Swift and Rust refusal lists, the `phases` reader
rejections) I applied 25 mutations of my own to the retained `lifecycle`,
`ordinary` and `replacement` envelopes of
[`extensions-m3-accepted-20261013`](../tests/out/runs/extensions-m3-accepted-20261013/)
through both `consumer.validate` and `lifecycle_oracle.check_record`
(script and output retained under the audit run named in Q7). Rejected: consume
`returned` without delivery; release `returned` after a -1 consume; consume
`unavailable` with `handle_unavailable`; `returned` without the call marker;
published events with `proceed_observed: false` or `sandboxed_after_apply:
false`; `issued` beside a signalled issuer or a failed preparation; events
removed while `action_ids` still name them; attempt `rc: 0` beside a failed
fresh open; a lifecycle copy that disagrees with the disposition; swapped or
reordered consume/release identities; a release value outside 32 bits; a
negative errno; `delivered_bytes` differing from `token_length`; `query_first`
on an unavailable prediction; a record copied from another phase; arrival
without the previous completion; acknowledgement without release. Accepted, as
designed: fresh-read bytes altered to another string of the same length, and a
fresh-read identity copied from the declaration. Readers establish internal
consistency, not truth; the live `extensions` control compares bytes and inode
with the investigator's own file and retains them beside the reply.

*Items for later milestones, not claim defects.* (a) Both readers accept
`collection_status: collected` on a phase whose `ordering.validator_disposition`
is `not_needed` with no validator record. No claim can be built on it, since
`query_first` still needs an associated validator record, and production never
emits the combination, but the readers do not cross-check the two fields.
Reader hardening belongs in M5.1. (b) Worker delivery code 3 is reported as
`malformed_transport` but [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
also uses it for its own `setrlimit`, `fstat`, `mmap` and `close` failures, so a
reply cannot distinguish a malformed publication from a worker-local setup
failure. Delivery is withheld either way; a distinct code is an M4 or M5.1
vocabulary change across encoder, consumer and matrix.

**Q2 — Phase ordering and placement.** Does the public grammar enforce its
single-declaration and consume/release caps and reference order while retaining
all ordinary paired probes? Do phase-local query collection, progression,
unavailable predictions and lifecycle placement support exactly the stated
ordering claims? In particular, can repeated PID/target observations across
phases gain unjustified identity or log attribution? Entry points:
[grammar](../docs/REQUEST-GRAMMAR.md),
[orchestrator](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
[phase controls](../tests/suites/witness_contract/check_phases.py),
[extension controls](../tests/suites/witness_contract/check_extensions.py),
[collector tests](../controller/src/run_flow.rs) and
[live log controls](../tests/suites/witness_contract/check_termination_correlation.py).

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): Yes on all three points, with no unjustified identity
or attribution found.

*Grammar.* Admission enforces one declaration, one consume and one release
across the whole specimen (`PWExtensionLimits`, `extensionMeaningFailure`),
reference existence, distinctness and order (`unknown_token_reference`,
`unknown_handle_reference`, `duplicate_reference`, `release_before_consume`,
`inapplicable_field` for a token on release), closed fields at every object,
and exec exclusion. The corpus holds 36 phase and extension cases with separate
CLI and XPC expectations plus the exact/over byte-limit pairs;
`extension_paired_create` keeps an ordinary pair beside lifecycle actions,
`extension_mixed_action` refuses an action that is both, and
`phase_missing_sandbox_check` / `phase_missing_attempt` refuse query-only or
attempt-only ordinary entries.

*Ordering.* The driver ([`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift))
stores release ordinal `index + 1` only when the worker has applied, its
identity matches, `done == 0`, this phase has arrived and is neither
acknowledged nor completed, the previous phase is completed, no violation was
recorded and the child was still pending at the immediately preceding
`WNOHANG` wait; the `phaseBoundary` hook, which replans with
`planValidatorQueries` and runs the collection, returns before that store. The
worker ([`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c))
publishes `arrived`, waits for exactly its ordinal, treats a larger ordinal as
`PW_FAILURE_PHASE_RELEASE` and stops, sets the immutable `acknowledged` flag,
runs that phase's slots in order and then sets `completed`. The consumer's
`_ordering_chain` and `eligible_order` require all four ordering flags, no
protocol violations, application, arrival, a validator record for the same
step in the same phase and PID agreement before `query_first`. My mutations
confirm: `query_first` on the unavailable phase-2 query, a record borrowed from
another phase, and acknowledgement without release were all rejected. The
`order_barrier_mutations` control was credited at `6744f3c` and its governed
code is unchanged since.

*Unavailable predictions.* A path unresolvable at that phase's planning yields
`prediction_unavailable`, `query_plan:path_unresolved_at_planning` and
`order: unestablished` while the attempt still runs (ENOENT in the ordinary
control; the `preparation_failure` extension control). Later phases replan
independently (`unlink_recreate` control: a fresh `query_first` after the
recreate).

*Repeated PID and target.* The correlation control's three phased variants
require every recovered event to remain `ambiguous` with both step identities
as candidates. The readers never compare `fresh_read.identity` across phases or
with the declaration identity (my probe copying the declaration identity into
a later fresh read was accepted, by design), and the `replacement` control
retains the original and replacement inodes without a stability claim. Each
phase has its own validator with its own `expected_step_ids`, so a same-path
query in two phases is two records. Note only that the worker's
`repeated_action` reason and `consume_decided` / `release_decided` guards are
unreachable past admission; they are harmless duplication, see Q6.

**Q3 — Token channel, lifetime and interruption.** Are storage bounds, mapping
size, descriptor inheritance, issuer/worker ownership, buffer erasure and reap
conditions sufficient to support the documented confinement claims on both
success and failure? Does unknown cleanup correctly prevent delivery or later
claims? Assess what the native entry/return controls establish and where private
API behavior remains unobserved. Entry points:
[channel ABI](../controller/tools/pw_probe_runner/pw_extension_channel.h),
[issuer](../controller/tools/pw_probe_runner/pw_extension_issuer.c),
[host issuance](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift) and
[boundary controls](../tests/suites/witness_contract/check_extension_boundaries.py).

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): Yes for the documented claims. The seams establish PW's
behavior around the calls; libsandbox's internals stay unobserved, as the
account says.

*Bounds and mapping.* The channel is 17,472 bytes with a 16,384-byte token
array and a 1,024-byte path, fixed by static asserts in
[`pw_extension_channel.h`](../controller/tools/pw_probe_runner/pw_extension_channel.h)
and mirrored in `PWExtensionLayout`, which `runner_abi_layout` compares with the
compiled C offsets. The issuer refuses a native string of length 0 or at least
the capacity (status 3), the host refuses the same lengths as
`invalid_transport`, and the worker re-validates magic, `completed`, status,
length, the terminating NUL and the absence of interior NULs before mapping a
token; mode 16 delivers the full 16,383-byte payload end to end. The host
creates the object with mode 0600, unlinks the name immediately, truncates to
the channel size, and both children check `st_size` before `mmap`.

*Descriptors.* The host's descriptor is `FD_CLOEXEC`; the issuer receives a
high `F_DUPFD_CLOEXEC` duplicate moved to descriptor 3 under
`POSIX_SPAWN_CLOEXEC_DEFAULT` with stdio on `/dev/null` and a NULL
environment; the worker receives a separate high duplicate moved to 5; both
close the descriptor after mapping, and the boundary observer records
`issuer_channel_closed`, `worker_channel_closed`, `issuer_argv_clean`,
`issuer_env_clean` and `worker_argv_env_clean` from inside the children. Exec
attempts are refused beside a declaration (`extension_exec_unsupported`), so no
grandchild can inherit the descriptor or the mapping.

*Ownership, reap and delivery.* `deliveryDescriptor` exists only for
`issued`, which requires a published state 1, the channel's recorded PID equal
to the spawned PID, a call marker consistent with the state, a bounded length,
and a reap with exit code 0 inside the 5,000 millisecond wait. Any other outcome
clears the channel's `completed` word so a worker cannot consume it
([`ExtensionIssuer.swift`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)).
The Swift control with injected `waitpid` EIO and `kill` EPERM shows an
unconfirmed reap recorded as `issuer_wait_error` with `reaped: false` and no
delivery descriptor; issuer modes 4, 5, 7, 11 to 15 cover death before
publication, timeout and malformed headers.

*Erasure.* The issuer erases and frees the libsandbox buffer; the worker erases
its mapped token after its consume decision and again at normal completion; the
host erases after the worker driver returns, on capability refusal and in
`deinit`, and the Swift control verifies the physical mapping is zero and the
descriptor closed. Because host and worker map the same object, the host's
erase also clears the view of a dead or unreaped worker, so unknown worker
cleanup does not leave the token readable through PW's channel. The observer
confirms `issuer_token_erased` and `worker_token_erased` live, and the control
asserts the token appears in no retained artifact, argv, environment or
captured output.

*What the seams establish.* [`control.c`](../tests/fixtures/extension_controls/control.c)
compiles the production issuer and worker sources with `PW_EXTENSION_OBSERVE`
and overridden symbol lookup. It therefore establishes the source's behavior
under a clang `-O2` test build, not the shipped Meson-built bytes, and it never
observes inside `sandbox_extension_consume` or `_release`: whether the library
copies or retains the token, allocates, or what the kernel records. The
architecture's known gap says this; the test README could add the build
distinction. One label to refine in M4: an issuer that publishes and then exits
abnormally is reported as `issuer_result_missing` (delivery is still withheld);
`issuer death after publication` is a natural M4 combination and should carry
its own name.

**Q4 — Issuer authority and BYOXPC provenance.** Is issuance kept under its
separate, recorded ordinary authority, with the issuer signed without the
worker's entitlement plist? Do install, read-back, validate, reconcile and older
registry recovery preserve uncertainty when issuer evidence is absent, and
refuse a selected missing capability with the documented code? Review
[runner management](../controller/src/runner_manager.rs),
[bundle inspection](../controller/src/bundle.rs),
[provenance controls](../tests/suites/witness_contract/check_extension_provenance.py)
and the [external-runner account](../docs/PolicyWitness.md#external-runners-byoxpc).

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): Yes. Issuance stays under ordinary process authority with no
expansion, and the BYOXPC paths preserve unknown issuer evidence; two
documentation nuances and one missing live control are noted.

*Authority.* The shipped service, worker, validator and issuer all carry empty
entitlement sets in the embedded manifest (SHA-256 `0df13c51…`), so the issuer
is an ordinary unsandboxed process with the invoking user's IDs; the reply
records its `uid`, `euid`, `gid` and `egid`, and the live control compares
`euid` with the test's own. [`build.sh`](../build.sh) signs it with
`sign_macho` and no entitlements plist. For BYOXPC,
[`sign_install_tree`](../controller/src/runner_manager.rs) signs the worker with
the identity and the supplied plist, the validator and the issuer with the
identity alone, then the bundle, and refuses a copy missing any of the three
before any signing (unit test). The M1 decision gate was not exercised: no
entitlement, service or privilege was added.

*Read-back, validate, reconcile, older records.* `read_back` records
`issuer_signature` and `issuer_entitlements` only when the file exists or the
record already carries issuer evidence; older records therefore keep `None`,
which the docs and the record comment define as unknown rather than absent
authority, and a recorded issuer that disappears or cannot be read fails
validation (unit tests at the 1466 to 1507 region). Reconcile remains a
report; I did not find an issuer-specific reconcile branch, which is
consistent with the guide. [`check_extension_provenance.py`](../tests/suites/witness_contract/check_extension_provenance.py)
compares every BYOXPC envelope's `runner_provenance` with the independent
registry read-back and the dossier's issuer hash with the installed file.

*Capability refusal.* A missing executable makes `ExtensionSession` report
`issuer_unavailable` and the orchestrator returns `bad_request` with
`extension_issuer_unavailable` at `["extensions"]`, no worker and the
declaration retained; the `issuer_capability` control runs on both the standard
and the installed BYOXPC runner through the `issuer_executable_path` override,
and `extension_missing_issuer` records the admission/host difference.

*Gaps.* (1) The default-path case, a current runner copy whose
`pw-extension-issuer` file is absent, is established by code reading and the
override control, not by a live control that removes the file; cheap to add in
M4. (2) The guide's sentence that selecting an older bundle lacking the helper
refuses with `extension_issuer_unavailable` overstates: an older bundle also
runs an older `PWRunner` that predates request schema 4 and would refuse at the
version or unknown-field gate. The accurate claim is about a current copy whose
issuer file is missing; M5.5 wording. (3) Nothing asserts that the issuer's
entitlement set is empty; the read-back records whatever it has. Acceptable,
since the install path never supplies it a plist, but the provenance control
could pin `issuer_entitlements.granted == []` cheaply.

**Q5 — Contract, limits and integration.** Are request/response/envelope versions,
C/Swift layouts, admission corpus and independent readers coordinated for the
new actions and records? Does the 52,414,779-byte reply bound cover the actual
encoder and all relevant transport paths within the 152 MiB controller budget,
without hiding truncation or invalid ordering? Are any new build/capability
refusals missing behavioral controls? Start with
[contract owner](../docs/contract.json), [limits owner](../docs/limits.json),
[build owner](../docs/build.json),
[maximum-reply control](../tests/suites/witness_contract/check_max_target_reply.py)
and [coverage](../tests/COVERAGE.md).

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): Coordinated, with one scope note on the BYOXPC transport
and no missing behavioral control identified.

*Versions and layouts.* [`contract.json`](../docs/contract.json) states 4/17/7,
[`CONTRACT.md`](../docs/CONTRACT.md) agrees, the consumer gates on exactly
those values, the blackbox fixtures live under `response17`, the shape golden
carries `extension_events`, `fresh_read` and the declaration keys, and the ABI
golden records the new header fields (`phases` at 128, extension delivery at
100 to 112) and slot fields (`call_boundary` 5984, `native_result` 5992,
`access_bytes` 6072). `runner_abi_layout` and the regenerated worker identity
were credited at `6744f3c`. The corpus adds 36 phase/extension cases plus the
exact/over boundary pairs and the shared 256/257 total-action cases.

*Limits.* Rows exist with source and check owners for declarations, consumes,
releases, reference bytes, target bytes, token storage and payload, channel
size, issuer wait, fresh-read bytes, phase count, phase publications, the
cumulative collection allowance and the worker release wait.

*Reply bound.* `runner_reply_maximum` is informative; it is computed by
`maximalReplyEncodedSize()` in
[`ReplyMaximumTests.swift`](../runner/Tests/PWRunnerCoreTests/ReplyMaximumTests.swift)
from eight phases, 256 steps, the declaration, two events, a fresh-read payload
on every slot and the override echo, which is a superset of any reachable
reply. `controller_output` is three times that value rounded up to a 4 MiB
multiple, and
[`check_max_target_reply.py`](../tests/suites/witness_contract/check_max_target_reply.py)
asserts the live client's capture limit equals it and that oversize fields are
refused rather than truncated. The investigative record still quotes the
earlier 52,257,718-byte figure in its M2 section; the manifest and the control
use 52,414,779, and `limits_documentation` passed, so the record's older number
is history, not a current claim. The bound was exercised on the standard
runner; the BYOXPC path shares `pw-runner-client` and the same capture limit
but was not driven at maximum, which is M4/M5.6 work.

*Refusals and controls.* The new capability refusals have live controls
(`issuer_capability`, issuer mode 6 for `extension_api_unavailable`). The
issuer is a Meson output, a bundle copy, a signing step (`sig_issuer`) and an
inventory entry in `build.json`; the preflight verification control covers a
worker or issuer changed after sealing, and `build_guard_controls` was credited
at `6744f3c`. I did not identify a new build refusal lacking a control.

**Q6 — Account and necessary machinery.** Do the current
[architecture](../docs/ARCHITECTURE.md), [guide](../docs/PolicyWitness.md),
[runner account](../runner/README.md) and generated views describe the same
implemented boundaries? Is the revised PW-owned allocation claim supported
without an implied guarantee about private native calls? Identify unsupported
claims, missing generator ownership, or duplicated/generalized machinery whose
necessity should be examined in H1, citing the concrete path or invariant.

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): The accounts describe the same boundaries, the allocation
claim is supported without an implied guarantee, and I found no competing
models. Five mechanisms are worth H1's attention; none looks unnecessary.

*Agreement.* The root README's Flow and bundle inventory, the guide's
sandbox-extensions section and FAQ copy, the runner README's source map and
lifecycle, and the architecture's issuer node, T13/T14 channels, B14/B16
guards, X26 to X28 BYOXPC edges and timeline all state: issuance before worker
creation under ordinary authority, a fd 3 transient channel, delivery only
after a clean reap, consume/release in the once-applied worker, host erasure
before reply, no token bytes in evidence. `source_drift` established that every
citation resolves; I checked that the cited `run_targets`, `run_case` and
`runExtensionEvidenceTests` do establish the rows that cite them.

*Allocation claim.* The architecture states that PW introduces no post-apply
heap allocation for native lifecycle actions and names the private-call gap
twice. The C source supports the claim: `dlsym` and the channel `mmap` happen in
`prepare_extension` before `sandbox_apply`; the post-apply loop uses fixed slot
and evidence storage, atomics, the commpage clock, `open`/`fstat`/`read`/`close`
and the two native calls; exec attempts acquire pipes after apply by documented
design. It is scoped correctly.

*Unsupported or stale claims.* The guide's older-bundle sentence (Q4), the
`malformed_transport` label (Q1), the record's superseded reply figure (Q5), and
the handoff's `evidence.rs` citation, which is outside product documentation.

*Machinery for H1.* (1) Three parallel implementations of the extension rules
(Swift encoder, Rust disposition reader, Python reader) follow the existing
closed-vocabulary pattern and my mutations show them agreeing; the cost is
maintenance. (2) A fresh validator per phase is the simplest protocol and the
`phases` control shows distinct PIDs and reaps, but the plan asked to measure
its cost before considering a persistent validator and I found no recorded
per-phase launch cost in the investigative record; the retained run timings
can supply it before H1. (3) The compile-time `PW_EXTENSION_OBSERVE` seam with
`control.c` including the production sources is what makes the interruption
controls possible; its limit (a different build of the same source) should be
stated where the controls are described. (4) The worker's `repeated_action`
path and its vocabulary entry duplicate an admission rule and cannot be reached
through the public grammar; keeping or removing them is a judgment call.
(5) The all-action disposition index, with `phases[].action_ids` partitioning
`steps` and `extension_events`, costs readers a join but is what lets lifecycle
events exist without invented queries; it is justified.

**Q7 — Gate evidence and remaining limitations.** Does the accepted evidence,
including the 13 replacement credits and reviewed reuse of 134 earlier results,
establish the M3 gate for this exact candidate? Identify any unsound reuse,
missing discriminating control or inaccessible artifact that prevents that
conclusion. Does the unverified cleanup of 25 empty fixture objects change any
production or gate claim beyond the recorded limitation? Classify findings that
invalidate M3 or block H1/M4 separately from later work, and specify the smallest
correction or experiment needed.

Auditor answer (Claude Fable 5.1, out of band, 2026-10-13): The accepted evidence establishes the M3 gate as the gate is
written, and nothing I found invalidates M3. One coverage gap outside the gate's
letter needed a discriminating run, which I performed.

*Reuse soundness.* The retained `test-only-delta.diff` is byte-identical to
`git diff 6744f3c..fdbd89b`; its Rust hunks start at line 1195 of
`run_flow.rs`, after the `#[cfg(test)]` marker at line 940, so production Rust
is unchanged; the changed live checker, all unit cases and all source checks
were rerun in the 13-case run. Both runs' `artifact-integrity/before.json`
inventories are identical, and I re-hashed all 21 hashed entries against the
current `dist/PolicyWitness.app` with no mismatch. The reviewed exception for
the build guard and driver replay credits is reasonable; I did not rerun those
two because they need the signing keychain.

*Gate coverage.* Every control the M3 gate names is in the 147 credits:
`extensions`, `extensions_byoxpc`, `phases`, `extension_boundaries`,
`order_barrier_mutations`, the `runner_byoxpc` signing, provenance and
registry-recovery cases, `preflight`, the maximum-reply control,
`build_guard_controls`, `source_drift`, `failure_boundaries`, `runner_unit`,
`runner_abi_layout`, `runner_c_worker_harness`, `unit` and the blackbox checker.
However, 49 of the 174 default-battery cases have no result on any M2 or M3
build: the sixteen `runner_use_c_worker` cases, `runner_exec_lifecycle`,
`runner_exec_inheritance`, `runner_outcome_runner_timeout`,
`runner_outcome_worker_spawn_failed`, `runner_live_worker_identity`,
`runner_specimen_isolation`, `runner_mach_service_liveness`, the apply-isolation
and IOKit filter cases, `run_effects`, `smoke`, `shell_helpers`,
`validator_batch_mode`, `validator_bridge`, `exec_fixture`, `run_capture` and
`integration/cli.integration`. Their last executions were at the 0.2.8 release
source on 2026-10-11, before the phase protocol, the slot layout and response
17 changed the worker and its readers. The gate text lists specific suites, so
this is not a breach of its letter, but "affected validator and witness cases"
plausibly includes the worker-execution suites whose ABI changed.

*Discriminating run.* I ran the full default battery of 174 cases against the unchanged build 560 at the handoff commit `955e2272247af5070a441e01f2aa0e128c65b8fe` with a clean tree, which is production-identical to `fdbd89b`. The run is retained as [`a1-audit-default-20261013`](../tests/out/runs/a1-audit-default-20261013/run.json), run ID `20261013T162635Z_9a7839fb`, with no skipped or unrun cases and an unchanged app inventory: 172 passed and 2 failed. Both failures lie in the uncredited set and are stale test controls rather than product behavior (A1-F2): `shell_helpers/script_groups` expects every witness script to run through the wrapper, and M3 added the standalone `extension_boundaries.sh` with its own catalog command; `runner_specimen_isolation/overlapping_runs_keep_evidence_separate` expects a reversed `steps` array to add only the order diagnostic, and since M2 the consumer also reports that the reversed steps no longer match `phases[].action_ids`. The other 47 uncredited cases passed, including the sixteen `runner_use_c_worker` cases, the exec lifecycle and inheritance suites, the hung-worker timeout, worker identity, `run_effects`, `smoke` and the CLI integration case. My reader-mutation script and output and the console transcript are attached under that run's `audit/` directory, and I added a retention-index entry for the run; both the entry and this document are uncommitted.

*Unverified objects.* The host booted on 2026-10-07T01:47Z and has not rebooted
since the 2026-10-13T00:59Z fixture run, so the 25 objects were not cleared
by reboot. Their names were random `/pwext_` suffixes that were never recorded,
and macOS offers no enumeration of POSIX shared-memory names, so absence stays
unverifiable. They were created before truncation, so they are zero bytes, were
never mapped by a product process and hold no token; they change no production
or gate claim. Accept the recorded limitation; a reboot clears them.

*Access.* Every referenced artifact was available in this checkout; I verified
the presence and counts of the rendered review artifacts, not their content,
since the rendered assessment is a separate process.

*Classification.* Invalidating M3: none. Blocking H1: none. Before M4: repair
the two stale controls named above and rerun them, since M4 extends exactly
these control families and M5.6 requires the full battery. Later work: the
reader consistency gap and
`malformed_transport` label (M5.1), the post-publication issuer exit label and
the missing-issuer-file live control (M4), the BYOXPC maximum-reply path
(M4/M5.6), the older-bundle wording (M5.5), and the per-phase validator cost
note (before H1).

#### Additional auditor findings

Auditor (Claude Fable 5.1, out of band, 2026-10-13). Numbered for the
executing agent's dispositions; routes follow the plan's documentation /
implementation / investigation distinction.

- **A1-F1 (documentation, this document).** Q1 cites
  [`controller/src/evidence.rs`](../controller/src/evidence.rs) as the Rust
  reader; the extension rules live in `extension_account_issues` in
  [`controller/src/disposition.rs`](../controller/src/disposition.rs). Correct
  the citation.
- **A1-F2 (implementation, test controls; repair before M4).** 49
  default-battery cases, including the worker exec, timeout, identity and
  isolation suites, had no result on any M2/M3 build. My default-battery run
  against build 560 (Q7) passed 172 of 174 with no skips or unrun cases; the
  two failures are stale controls, not product behavior:
  `shell_helpers/script_groups` (`witness_continues`) expects every `*.sh` in
  `tests/suites/witness_contract/` to run through that wrapper, and M3 added
  the standalone `extension_boundaries.sh` there with its own catalog command;
  `runner_specimen_isolation/overlapping_runs_keep_evidence_separate`
  (`A_reordered_valid`) expects a reversed `steps` array to add only the order
  diagnostic, and since M2 the consumer also reports that the reversed steps
  no longer match `phases[].action_ids`, which is a legitimate rule. Route the
  standalone script through the wrapper or teach the control about standalone
  catalog commands; make the reorder mutation reverse `action_ids` too or add
  the partition diagnostic to the expected set. Rerun both, then index the
  evidence. Neither failure touches the M3 gate's named controls, but the gap
  that hid them is the reason the default battery belongs in each gate's
  evidence from here on.
- **A1-F3 (implementation, readers, M5.1).** `consumer.validate` and the
  lifecycle oracle accept `collection_status: collected` beside
  `ordering.validator_disposition: not_needed` with no validator record. No
  claim can be built on it; add the cross-check so the two fields cannot
  disagree. Production never emits the combination.
- **A1-F4 (documentation or vocabulary, M4/M5.1).** Worker delivery code 3
  (`malformed_transport`) also covers the worker's own `setrlimit`, `fstat`,
  `mmap` and `close` failures in `prepare_extension`. Either document the
  broader meaning or add a distinct code through encoder, consumer and matrix.
- **A1-F5 (vocabulary, M4).** An issuer that publishes and then exits
  abnormally is labeled `issuer_result_missing`; delivery is correctly
  withheld. Name the combination when M4 adds issuer death after publication.
- **A1-F6 (documentation, M5.5).** The guide's claim that selecting an older
  bundle lacking the helper returns `extension_issuer_unavailable` should say a
  current copy whose issuer file is missing; an older bundle's older `PWRunner`
  refuses earlier. A live control that removes the file from an owned copy
  would establish the default-path refusal (M4).
- **A1-F7 (documentation, M5.3/M5.4).** The interruption controls run the
  production sources under a clang `-O2` test build with `PW_EXTENSION_OBSERVE`;
  they establish the source's behavior, not the shipped bytes'. State this
  beside the controls' description.
- **A1-F8 (investigation note for H1).** The plan asked to measure the
  per-phase fresh-validator cost before considering a persistent validator;
  the record states the design but no measurement. Derive it from retained run
  timings or state that the measurement is not needed.
- **A1-F9 (documentation, record).** The M2 section of the investigative
  record quotes a 52,257,718-byte maximum; the manifest, guide and control use
  52,414,779. The record is history and may stand, but a one-line pointer to
  the superseding figure avoids a reader taking the old number as current.


### A1 Execution dispositions and follow-up

Executing agent `/root`, 2026-10-13. This is the requested review and briefing
of the returned audit, not completion of its corrective work. The auditor's
answers and original evidence index were preserved in commit `221f5ec` before
these dispositions. Their attributed text is unchanged. A1 remains open; H1
preparation and M4 have not started.

#### Assessment and verification

The audit supplies useful independent evidence and supports the principal M3
conclusion: the demonstrated lifecycle and phase ordering do not invent
effective permission, revocation or completion from native return codes. Its
scope is bounded source/evidence review plus new controls, not exhaustive proof
of every malformed record or another rendered-documentation assessment.

I verified the audit run's ownership, terminal state, run ID and counts:
172/174 passed, two failures, no skips or unrun cases. Its unchanged app
inventory matches the accepted M3 inventory, and I independently re-hashed all
21 hashed entries against the current app. Exactly 49 default cases were absent
from the final 147 M3 credits; 47 passed in the audit run and two failed. I did
not independently reconstruct the stronger historical statement that none ran
in any incremental M2/M3 diagnostic. The confirmed omission from final gate
credits is sufficient to accept the coverage criticism. My test selection was
too narrow for a change spanning worker ABI and response readers, even though
the plan's named gate controls were covered.

The failure logs and test source support the auditor's diagnoses. The wrapper
fixture glob includes the separately cataloged `extension_boundaries.sh`, which
the wrapper does not invoke. The isolation test first established distinct live
identities, effects and envelopes, then its mutation reversed `steps` without
reversing the phase action partition. The additional partition diagnostic is
legitimate. These are test-maintenance failures; neither is evidence that the
live isolation or native experiment failed. They nevertheless require repair.

I read the auditor's mutation script/output and independently reproduced F3 in
memory from the retained ordinary-phase envelope: both Python validation entry
points accept changing `not_needed` to `collected` while disposition stays
`not_needed` and no validator exists. This does not establish `query_first`, but
`collected` itself claims that the synchronous driver ran and returned under
the current failure contract. I therefore do not accept the unqualified phrase
“No claim can be built on it” as a reason to postpone this until M5.1.
The producer's empty-plan branch emits `not_needed`, so the observed production
baseline remains sound. Coordinated encoder/reader consistency controls should
be repaired during A1 follow-up, without equating `collected` with successful
spawn, complete output or clean reap.

No new live execution, signing or resource-sensitive experiment was needed for
this review. The existing allocation and unrecorded-empty-object limitations
remain; no attempt was made to clean objects by prefix.

#### Finding dispositions

| Finding | Lead disposition, owner and timing |
| --- | --- |
| A1-F1 | Accepted; corrected the executing agent's Q1 link to `disposition.rs` here. Auditor wording is preserved. |
| A1-F2 | Accepted. Repair both test controls and rerun them during A1 follow-up, before H1/M4. Prefer catalog-aware wrapper expectations; preserve both the pure order mutation and independent partition rejection rather than weakening the consumer. Include the default battery in subsequent milestones' acceptance evidence alongside opt-in gate controls, with explicit dependency-reviewed reuse where applicable. |
| A1-F3 | Accepted and moved earlier, to A1 follow-up. `collected` makes a bounded execution claim even without a usable prediction. Add compatible-state checks and positive/negative controls across affected encoder/readers; preserve valid collection failures. M5.1 will verify the resulting contract. |
| A1-F4 | Accepted. Document code 3's existing broader meaning, including local setup failure, during A1 follow-up so the current account does not infer malformed input from that label. M4 owns a distinct setup-failure code if its combined-fault controls require finer representation; any vocabulary change must update producer, readers and matrix together. |
| A1-F5 | Accepted as M4 vocabulary/combined-fault work. Published native evidence and abnormal issuer exit must both remain visible; delivery is already withheld. Add the post-publication-exit control and choose a status that does not imply the publication was absent. |
| A1-F6 | Accepted, with wording repair moved from M5.5 to A1 follow-up: the precise missing-helper refusal applies to a current runner copy. Older protocol binaries can refuse earlier. M4 owns the live default-path control on an owned copy with the helper removed; M5.5 rechecks the final account. |
| A1-F7 | Partly accepted as clarification, not missing foundational evidence. The fixture README already says that it compiles production sources outside the inspected app and identifies the instrumentation through overrides/provenance. Make the alternate-build limitation explicit beside the suite description during A1 follow-up; M5.3/M5.4 check its consistency. It does not prove the shipped bytes were interrupted internally. |
| A1-F8 | Accepted as an H1 design note, not an unmet unconditional measurement gate. The plan says to measure before considering a persistent validator; no such change is proposed. Recommend retaining the fresh validator and its existing bounded cleanup model. Retained aggregate/collection timings must not be called isolated process-launch cost. A persistent protocol would require the measurement first. |
| A1-F9 | Accepted as a history-navigation improvement. Added a pointer beside the M2 figure to the superseding M3 calculation; the original measured value is preserved. |

#### Additional lead finding and carried work

**A1-L1 — current capability-code documentation.** The guide at
`docs/PolicyWitness.md` near line 313 assigns `extension_issuer_unavailable` to
both a missing helper and a missing native issuance API. The orchestrator's
capability branch distinguishes `extension_api_unavailable`, and the retained
`extension_boundaries/artifacts/issuer-6/run.json` records that exact code. I
checked both source and retained output. Repair the owning guide and regenerate
its staged copy during A1 follow-up, alongside F6. This is a current
documentation error, not a proposed behavior change.

Q4's optional empty-issuer-entitlement assertion is accepted for M4 provenance
controls: compare the independent read-back to the expected empty grant set,
without changing how older unknown records are represented. Q5's BYOXPC
maximum-reply-path control is assigned to M4, with final acceptance at M5.6.
Shared transport code supports the present reuse argument but is not a live
maximum-size BYOXPC observation.

For H1, retain the fresh per-phase validator, separate issuer/token channel and
phase action partition. Their responsibilities and isolation boundaries are
established. Keep the encoder and independent readers separate despite their
maintenance cost. The worker's duplicate-action guards are small defensive
checks and do not justify a broader mechanism. This is a preliminary design
assessment for the requested audit briefing; the formal H1 briefing still
requires A1 corrections and closure.

Before A1 closes, commit the test/reader and current-account corrections,
affected checks, rendered rechecks and updated applicability evidence. Obtain
auditor follow-up where changes or disputed semantics require it. This review
does not relabel the 172/174 audit run as passing or replace its original output.

### A1 correction checkpoint — requested pause

Corrections are committed at `52bb1b96df168033ccd24bb0ec96dc1385d30ffc`;
current signed app is build 566 from `2f380d0`. The earlier full default run
passed 174/174. The final 196-case selection was stopped at the user's request:
[the terminal partial run](../tests/out/runs/a1-repair-accepted-20261013/run.json)
records 30 passed and 166 unrun, with an unchanged app inventory. It is not
acceptance. The final rendered recheck has no remaining findings; artifacts and
an explicitly unfinished handoff draft are retained under that run. The plan's
checkpoint contains exact resume instructions. The completed follow-up will
return to the original out-of-band auditor; no replacement auditor is being
commissioned. Original attributed answers remain unchanged. A1 stays open;
H1 and M4 have not started.

### A1 correction follow-up — handoff to the original auditor

Prepared by executing agent `/root` on 2026-10-13 for the original out-of-band
auditor, Claude Fable 5.1. The user requested this return to the same auditor.
This is a focused continuation of A1. The earlier attributed answers and
findings remain unchanged. A1 remains open; H1 and M4 have not started.
Please append your attributed follow-up answers below. This handoff records the
final implementation and evidence directly; reviewing commit history is optional.

#### Final candidate and acceptance

| Item | Identity |
| --- | --- |
| Reviewed source | `efb588b54fd01caf1d91683e9df6a1bff8e45bbd` (implementation unchanged from `52bb1b9`) |
| Signed app source | `2f380d02632ea4ae02fe47c78d389eaebb831dc2`, clean stamp `v0.2.8-46-g2f380d0` |
| Local app | `dist/PolicyWitness.app`, version 0.2.8, build 566 |
| Signer / host | Same Developer ID identity and certificate as above; macOS 26.7.1 / 25G241, arm64 |
| Wire versions | Request 4, response 17, envelope 7 |
| Worker identity | `d728670539b289721b4cfbc567df5c14ec76917c09311bba283e64a39ba36957` |
| Embedded manifest SHA-256 | `21d83af0bfd2e63197996038cd326e4b247f449ccdaa71e6c7fb72bf27839913` |

Production corrections are committed at `8707abc`; fixture corrections at
`2f380d0`; final Python oracle robustness and wording corrections at `52bb1b9`.
The reviewed source differs from the app source only in the plan, audit and
investigative records, retention index, handwritten failure-contract wording,
Python lifecycle oracle, and its blackbox controls. None is an app build input.
The handoff commit changes only the plan, records and retention index. It is not the source
of the earlier build or test execution.

**Final acceptance: 196/196 canonical cases have passing evidence**, covering
all 174 default cases plus the 22 required opt-ins. The resumed run
[`a1-repair-resume-20261013`](../tests/out/runs/a1-repair-resume-20261013/run.json),
ID `20261013T185935Z_3249b0bd`, passed 166/166 at clean `efb588b`, with no
skips, unrun cases or harness errors and unchanged app inventories. It includes
all 406 Swift checks plus Rust/Python driver replay, public phase/extension
controls, native boundaries, ordering mutations, BYOXPC and failure boundaries.
The other 30 completed passes are from
[`a1-repair-accepted-20261013`](../tests/out/runs/a1-repair-accepted-20261013/run.json),
ID `20261013T173617Z_a52124f2`, at clean `52bb1b9`. The user-requested pause
cancelled that run after those cases; its original unsuccessful terminal
accounting and 166 unrun selections are preserved.

The complete case-credit manifest is
[checkpoint/acceptance-credits.json](../tests/out/runs/a1-repair-resume-20261013/checkpoint/acceptance-credits.json).
It names every canonical case and its command/configuration, source and app.
Final credits combine 30 completed cases from the cancelled run with the
166 fresh results from the resumed run. The cancelled run remains `ok: false`;
none of its unrun cases is credited there. No result from the preceding oracle
revision or old build 560 receives final credit. Source hashes, selection and
command records, source applicability checks, cleanup observations and app
inventories are retained with the runs; the signed-build console is in the
cancelled run's checkpoint. The earlier
[174/174 default run](../tests/out/runs/a1-repair-default-20261013/run.json), ID
`20261013T171246Z_a9d472bc`, remains a separate passing historical run.

The [applicability review](../tests/out/runs/a1-repair-resume-20261013/checkpoint/source-applicability.json)
records the exact delta from `52bb1b9` to `efb588b`: the plan, two audit/investigation
records, and one appended retention-index entry. All implementation, test-code,
fixture, manifest and permanent-document bytes are unchanged. It separately
records execution-path judgments for the 30 reused cases. In particular,
dispatcher fixtures copy the index, while retention-specific controls replace
it with their independent index; the new retained path does not overlap their
controlled output paths. Build guards copy all tracked files, but the changed
metadata is not a build input. These are reviewed exceptions for copied bytes,
not claims that every fixture input is byte-identical or that hashes prove
complete dependency coverage. The handoff's final metadata-only delta is retained
alongside that review.

The diagnostic executions remain intact. The sandboxed first offline run left
one case unrun after signature inspection failed; the same selection outside
the automation sandbox passed 7/7 on unchanged build 560. The first signed
focused run passed 8/9, with a Swift test-only overlapping-access compile error.
Subsequent Swift runs passed 385/406 and 405/406 while incompatible legacy
fixtures were corrected. The accepted Swift correction then passed 406/406 and
Rust/Python driver replay. Full intermediate source snapshots were not captured
for those two failed Swift executions; their index sources remain null and they
receive no acceptance credit. The focused final malformed-input checker passed
before its commit, with exact working hashes/diff and null index source.
`tests/RETAINED.json` names all runs and their original provenance.

#### Corrections and carried findings

| Finding | Executed correction / disposition at this handoff |
| --- | --- |
| A1-F1 | The executing-agent Q1 citation now points to `controller/src/disposition.rs`. Attributed auditor wording is preserved. |
| A1-F2 | Wrapper expectations derive independently cataloged commands from `tests/catalog.json`, excluding those scripts from wrapper-only coverage while preserving all other siblings. The isolation controls separately reject step-only reversal as a broken phase partition, and reverse steps plus the sole phase's action IDs for the pure order mutation. The bad-attempt/order control retains its independent failure. Default and required opt-in coverage have explicit case credits above. |
| A1-F3 | The Swift ordinary encoder, Rust execution-diagnostics reader, and Python consumer/oracle reject incompatible collection status, disposition and native child/spawn observations. Positive controls preserve setup failure before spawn, failed spawn, unreaped child and clock/budget failure. Degraded reporting failures preserve raw conflict without restoring claims. See the source and control account below. |
| A1-F4 | The guide and failure contract explain that existing `malformed_transport` includes rejected publication or local setup failure; that label alone does not establish malformed input. No vocabulary change was made. M4 retains responsibility for a distinct setup-failure code if combined-fault observations need it. |
| A1-F5 | Still assigned to M4: an issuer publishing and then exiting abnormally must retain both observations and receive an appropriate status. Delivery is already withheld. No new claim of coverage for this combination is made. |
| A1-F6 | The guide limits the precise missing-helper refusal to a current runner copy and says older protocol binaries may refuse earlier. M4 still owns the live owned-copy control with the actual helper removed. |
| A1-F7 | Fixture and witness-suite accounts now explicitly identify the separate instrumented clang `-O2` build with `PW_EXTENSION_OBSERVE`; source-boundary controls do not interrupt shipped bytes or observe private API internals. |
| A1-F8 | Retained for H1. No persistent validator is proposed, so the plan's conditional isolated launch-cost measurement has not been performed. Aggregate/collection timings are not presented as isolated launch cost. |
| A1-F9 | The historical M2 reply-size figure points to the superseding M3 calculation; neither original measurement is rewritten. The current conservative bound remains unchanged by the fixture repair. |
| A1-L1 | Guide and regenerated staged copy distinguish `extension_api_unavailable` from `extension_issuer_unavailable`. |
| Additional phase-partition wording | The failure contract now states that phase action IDs partition ordinary steps and native events, preserving each array's order. |
| Rendered recheck F1 | The ordering table now says an observed native spawn failure is retained, while local setup can fail before such a record exists. The documentation reviewer rechecked the actual final page and closed this finding. |

The optional independent assertion that the issuer's grant set is empty and the
BYOXPC maximum-reply-path control remain M4 work, as dispositioned above.
The current run does not claim to supply either missing control. Issuer
privilege, extension classes, lifecycle limits and worker scheduling are unchanged.

#### Collection consistency and fixture review targets

[`collectionEvidenceConsistent`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
is enforced by the ordinary full-reply encoder.
[`phase_collection_issues`](../controller/src/disposition.rs) feeds execution
diagnostics and withholds disposition claims for contradictions.
[phase_evidence.py](../tests/lib/phase_evidence.py) is an independent Python
implementation used by the consumer and lifecycle oracle. The oracle also
returns diagnostics for malformed phase containers/entries instead of raising.
The handwritten [failure contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#phase-association-and-partial-publication)
records compatible combinations:

- `not_reached`: no disposition or `not_invoked`, with no child/spawn record.
- `not_needed`: `not_needed`, with no child/spawn record.
- `collected`: `not_spawned` with no child and an optional native spawn failure;
  or `reaped`/`unconfirmed` with the corresponding child/reap observation and
  no spawn-failure record.
- `budget_exhausted`: `not_spawned`, with no child/spawn record.
- `clock_unavailable`: `not_needed` before planning or `not_spawned` after a
  nonempty plan, with no child/spawn record.

Collection does not require successful spawning, complete output, zero child
exit or confirmed cleanup. The hand-reviewed
[phase fixture](../tests/fixtures/contract/phase_collection.json) contains nine
compatible and twelve contradictory states. Full Swift encoding, Rust
execution diagnostics and both Python entry points exercise those rows; public
phase controls mutate real capture states as well. Five additional malformed
container/entry controls exercise the Python diagnostics. None imports the
production classifier into the Python oracle.

Version values remain unchanged because this correction enforces existing
status meanings rather than changing a valid record's field type, vocabulary
or interpretation. The earlier accepted contradictory records were defects in
validation. This is the executing agent's application of the wire contract,
and is explicitly offered for your review. Worker identity was regenerated
because its conservative source inputs include the Swift encoder; the native
wait, release store, eligibility rule and ABI layout did not change.

The new consistency guard exposed an older field-complete Swift fixture that
placed both a validator child and a failed spawn in one phase. It now has
separate ordinary and failed-spawn shape documents; the committed response-shape
golden is unchanged. The missing-ordering-evidence control explicitly checks
ordinary encoding rejection and degraded preservation of the validator record,
with comparisons withheld. It does not remove the conflicting observation.
The maximum-reply test encodes a maximized typed spawn member separately and
adds its full insertion allowance per phase to the ordinary reply. The exact
conservative union remains **52,414,779 bytes**, under the **152 MiB** controller
budget. Splitting incompatible shapes does not lower the bound.

#### Documentation assessment and evidence limits

The existing `/root/m3_rendered_review` documentation reviewer performed a
focused recheck, separate from this external audit. The requested model was
gpt-6-astra; its runtime identifier is not independently exposed. It inspected
actual PNG derivatives of the changed architecture B4, public/staged guide,
failure contract, test/fixture indexes and affected suite READMEs, tracing the
changed claims to owners and controls. Its sole finding was the setup/spawn
wording above; the final rendered recheck has no remaining findings. The lead
also inspected the final ordering table. Prior M3 review applies only to
unchanged surfaces; the report states the pages inspected and omissions.

The [review report](../tests/out/runs/a1-repair-accepted-20261013/reviews/a1-rendered-recheck.txt),
immutable source/HTML/PDF/PNG snapshots, manifests, renderer scripts and current
source applicability record are retained under the cancelled run's `reviews/`.
Both documentation baselines are byte-identical to M2. These review artifacts
and test outputs are gitignored and **local-only**; the tracked record/index is
not a portable evidence archive. No publication or release is claimed.

The [cleanup verification](../tests/out/runs/a1-repair-resume-20261013/checkpoint/cleanup-verification.json)
records absence of all eight ordinary BYOXPC session fixtures and their staging
and plist paths, plus the seven exact registry-recovery service identities and
that isolated staging directory. These checks use owned receipts, exact
`launchctl` targets, registry/pending-cleanup observations and independent path
checks. All 26 native observer channels return ENOENT for their exact recorded
names; their recovery paths are absent. No build, test or render process remains
active. No cleanup warning from this correction pass remains unresolved.

The earlier M3 experiment's 25 empty POSIX shared-memory objects with unrecorded
random names remain an explicit cleanup limitation; their absence is unverified.
No prefix-based removal was attempted. The allocation claim remains limited to
PW-owned preallocated reporting/coordination and no explicit PW allocator use
after apply; private API internal resource behavior is unverified. Test targets
use owned `/private/tmp` paths to reduce TCC exposure. No new permission prompt
was reported during this correction pass; unattended prompt absence is not
independently established.

#### Questions for the original auditor

1. Does the coordinated collection-consistency repair reject the reported
   contradiction while preserving valid failed collection and degraded raw
   evidence? Is retaining wire versions 4/17/7 justified under the existing
   contract, or does a reading-rule change require a bump?
2. Do the wrapper and isolation corrections preserve their intended independent
   rejection controls? Do the Swift shape/degradation corrections and separate
   maximum-size spawn allowance preserve coverage and the conservative bound?
3. Does the combined final acceptance and its source/app provenance close
   the default-coverage gap? Identify any missing dependency, unsupported
   applicability claim or resource-cleanup issue.
4. Do the current documentation corrections address your findings, and are the
   explicitly carried M4/H1 items still appropriately deferred without
   invalidating M3 or blocking preparation of H1? Please identify any remaining
   blocker separately from later milestone work.

#### Original auditor follow-up answers

Auditor follow-up (Claude Fable 5.1, out of band, 2026-10-13). Reviewed at
`9a1f20b7e5517d67177e753996c19b3dbe0ae7df`, whose delta from the reviewed
source `efb588b` is the plan, two records and the retention index; the
implementation, test code and app inputs are those of `52bb1b9` and `2f380d0`.
The local app is build 566 with worker identity `d7286705…6957` embedded in
the runner binary, the worker header, the Swift layout and `tests/lib/contract.py`.
My own evidence is retained under
[a1-recheck-default-20261013](../tests/out/runs/a1-recheck-default-20261013/audit/):
33 reader probes replayed through the Python consumer, the lifecycle oracle and
the Rust `execution_diagnostics` entry point (the Rust replay used a scratch
copy of `controller/` at this commit with one appended test function that only
reads probe files; the production source is byte-identical and the diff is
retained), wrapper-control mutations, and the full default battery at this
commit against unchanged build 566 (run `20261013T193011Z_7e1b6661`: 174 of 174 passed, 0 failed, 0 skipped, 0 unrun). I did not
rerun the 22 credited opt-in cases: each requires the signing identity directly
or through its installation dependency, and the standing instruction is to pause
at keychain-dependent steps. Their evidence is accepted on the provenance checks
in answer 3, not on my own execution.

**Follow-up 1 — Collection consistency and wire versions.** Yes on both
parts. The repair rejects the A1-F3 contradiction, preserves every valid
failed-collection state, and leaves degraded replies holding the raw conflict
without claims. Retaining 4/17/7 is justified.

*The table is the producer's image.* In
[`CWorkerOrchestrator.swift`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
the phase boundary assigns exactly five statuses: `clock_unavailable` before
planning (plan stays empty, so `buildOrdering` yields `not_needed`) or after a
nonempty plan (`not_spawned`); `not_needed` for an empty plan; `budget_exhausted`
before any spawn (`not_spawned`); and `collected` once `runValidator` returns.
The disposition and `validator_subprocess.reaped` derive from the same
`ValidatorOutput`; a `validator_spawn_failure` record exists only for
`.spawnFailed`, whose partial output is nil; pre-spawn driver failures return
`.failure(_, nil)` with no record. Every compatible row in the failure contract's
table is therefore a reachable production state and every contradictory row is
unreachable, which is what the fixture's nine accepted and twelve rejected rows
encode.

*Three readers, one rule.* Swift
[`collectionEvidenceConsistent`](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift)
runs inside the ordinary branch of the reply encoder; the degraded branch
guarded by `reporting_failure` does not apply it, and the service's fallback
in `pwRunnerReplyData` strips comparisons and re-encodes under
`reporting_failure`, so a contradiction reaches the controller as evidence,
not as a claim. Rust `phase_collection_issues` returns nothing when
`reporting_failure` is an object and otherwise withholds the disposition; the
Python consumer skips `_validate_phases` for failed reporting and the oracle
skips its D6 phase check. My 33 probes on the live `phases/ordinary` and
`extensions/lifecycle` envelopes of the resumed run agree across all three
readers: the four unmodified baselines accepted, including the two build-560
envelopes from `extensions-m3-accepted-20261013` read by the repaired readers;
the F3 mutation and its three mirrors (`collected` child phase relabelled
`not_needed` or `not_reached`, the consume phase relabelled `not_needed`)
rejected by all three with the phase rule; eight valid failed or empty
collections accepted by all three (`budget_exhausted`, clock failure before
and after planning, an unconfirmed child, and appended `not_spawned` phases
with and without a spawn record, an unconfirmed child and `not_reached`); ten
contradictions beyond the fixture rows rejected by all three (reap flag against
disposition in both directions, child absent or present against disposition,
spawn failure beside a child or a `not_needed` phase, ordering removed, unknown
status, empty child object, string reap flag); and the degraded reply carrying
the F3 contradiction accepted by all three with no comparison claims. The only
divergences are on malformed types and are recorded as A1-F11.

*Versions.* The contract's rule in
[CONTRACT.md](../docs/CONTRACT.md#when-a-number-moves) moves a number when a
field is removed, its type or meaning changes, or a new requirement is placed
on readers. The repair removes no field, changes no type and changes no meaning:
`collected` and `not_needed` keep the meanings the contract already documented.
The new reader obligation applies only to combinations no conforming producer
emits, as the producer image shows, and the set of producer-emitted documents a
version-17 reader accepts is the same before and after the repair; the build-560
envelopes still validate. That is enforcement of version 17, not a new reading
rule, and I accept retaining 4/17/7 and regenerating the worker identity
without a layout change. Recommendation, not a finding: record this reading
in the contract's "When a number moves" section in one sentence, so the next
validation hardening does not reopen the question.

**Follow-up 2 — Test controls, Swift fixtures and the bound.** Partly. The
isolation controls, the Swift fixture split and the maximum-reply allowance
are preserved. The wrapper control is not; it now guards two scripts (A1-F10).

*Isolation.* [`check.py`](../tests/suites/runner_specimen_isolation/check.py)
now requires step-only reversal to report both the order error and the broken
partition, then reverses the sole phase's `action_ids` so the pure order
mutation and the bad-attempt variant must add exactly one order error with the
remaining diagnostic multiset unchanged; the `check` helper enforces
`len(order) == 1` and multiset equality. Both rejections stay independent and
the consumer is not weakened. It passes in my battery.

*Wrapper.* [`check_scripts.py`](../tests/suites/shell_helpers/check_scripts.py)
derives its exclusion from every `witness_contract` case command. Every case in
that suite has its own command, so 34 of the 36 siblings are excluded and the
expectation is three scripts: the baseline and the two scripts cataloged under
`runner_validator_failure`. I demonstrated the consequence on a scratch copy of
the tests tree: with `phases.sh` and `extensions.sh` deleted from the wrapper,
all 31 script-group controls pass; with
`validator_decode_failure_reports_degraded.sh` deleted, the control fails. The
README's sentence that "every other sibling script must still run through the
wrapper" is literally true of two scripts. See A1-F10.

*Swift fixtures.* The field-complete fixture no longer places a validator child
and a spawn failure in one phase; the spawn-failure keys reach the response
shape golden through the added `spawnFailed` shape document, and the committed
golden is unchanged since `955e227`. The `worker` and `collection`
missing-evidence cases in `OrderingTests` still assert `unestablished` order
first, then assert ordinary encoding refusal and degraded retention of the
contradictory validator record with comparisons withheld. `PhaseProtocolTests`
drives the 21 fixture rows through the full encoder. Coverage is preserved.

*Bound.* The spawn member is maximized separately and added once per phase
(eight phases) with one byte removed for the brace-to-comma substitution. The
union is 52,414,779 bytes before and after the split, so the separate accounting
reproduces the former in-fixture bytes exactly; the resumed run's Swift log
records `maximal reply: 52414779 bytes; budget 159383552`, and the 152 MiB
budget is unchanged. The union remains deliberately unreachable.

**Follow-up 3 — Coverage, provenance and cleanup.** Yes, the gap is closed,
and I found no missing dependency, unsupported applicability claim or cleanup
issue. Mechanical checks I repeated: the 196 credits are exactly the
dispatcher's 174 default cases plus 22 of the 25 opt-ins (the three not
credited are `runner_exec_inheritance/mutation_controls`,
`sandbox_extensions_native/feasibility` and `smoke/runner_caller_auth`, none
named by the M3 gate); the 30 credits from the cancelled run are exactly its
completed passes and the 166 resumed credits are exactly its remaining list
and the resumed run's completed passes; the resumed run's source snapshot
hashes all 644 tracked files and every hash equals the git tree at `efb588b`;
the `52bb1b9` to `efb588b` delta is the four metadata files the applicability
review names; the `2f380d0` to `52bb1b9` delta is six files of which none is a
build input, and the staged guide is byte-identical to its source; the 21
hashed app entries equal the current app. The labeled exceptions for the 30
reused results are judgments I agree with: dispatcher fixtures copy the index,
retention controls replace it, and build guards copy tracked metadata that
`build.sh` does not consume. Cleanup rechecked now: all 26 recorded observer
channels return ENOENT from `shm_open`, all 15 session and registry labels are
absent from the user launchd domain, all 16 staging and bundle paths are absent,
and no `pw-byoxpc-*` directory remains under `/private/tmp`. The 25 unnamed M3
objects remain unverifiable, as recorded. My discriminating run is the default
battery at this commit: `20261013T193011Z_7e1b6661`, 174 of 174 passed, 0 failed, 0 skipped, 0 unrun, with the app inventory
unchanged.

**Follow-up 4 — Documentation and deferrals.** Yes. A1-F1 is corrected. A1-F4's
guide and contract wording matches the worker: in
[`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
status 3 follows `setrlimit`, the descriptor size check, `mmap`, and a failed
close or rejected publication, and the text no longer implies malformed input.
A1-F6 limits the precise refusal to a current runner copy. A1-F7's wording
matches `compile_fixture` in `check_extension_boundaries.py` (clang `-O2`
against `control.c`, which defines `PW_EXTENSION_OBSERVE`) and claims nothing
about shipped bytes. A1-F9's pointer is beside the M2 figure. A1-L1 matches the
orchestrator's capability branch. The architecture account names the new
guard and its three checks, the generated copies agree, and `source_drift`
passes in my battery. The deferrals stand: A1-F5 and the two optional controls
to M4, A1-F8 as an H1 design note. Nothing here invalidates M3 or blocks H1
preparation. **No remaining blocker.** Two items belong to A1 rather than a later
milestone: A1-F10 is the unfinished half of A1-F2 and is small enough to finish
in this follow-up, and A1-F11 can be carried to M5.1 explicitly.

**A1-F10 — The repaired wrapper control guards two scripts (low; test
maintenance; complete within A1 follow-up or carry it explicitly).** Because the
catalog gives every `witness_contract` case its own command, the catalog-derived
exclusion in `check_scripts.py` removes 34 of 36 siblings from the
`witness_continues` expectation, and the control no longer fails when a sibling
is dropped from `tests/suites/witness_contract/run.sh` (demonstrated above and
retained under `audit/`). The default battery is unaffected because the
dispatcher runs cases from the catalog, not the wrapper, so this is not product
evidence. Smallest corrections: either add `extension_boundaries.sh` to the
wrapper and restore the sibling-complete expectation, or keep catalog awareness
but key the exclusion on an explicit attribute or a named exclusion list with a
stated reason; in both cases add the negative control that drops a sibling from
a wrapper copy and expects failure, which is the check that would have caught
this repair.

**A1-F11 — The Rust reader treats malformed phase containers and types as
absent (low; M5.1 reader hardening).** `phase_collection_issues` reads through
`as_array` and `as_str`, so `phases: 7` yields no issue and a `not_reached`
phase whose `validator_disposition` is the integer 7 is accepted; the Python
consumer and oracle reject both (probes 40 and 43). No claim depends on it: the
Rust projection owns the process disposition, phase claims are read by the
Python readers, and no producer emits these shapes. It belongs with the M5.1
reader-hardening work rather than with this follow-up.

#### Executing-agent disposition of follow-up

Reviewed by executing agent `/root` on 2026-10-13. Commit `682fda9` preserves
the returned follow-up and its retention entry before this disposition. The
original answers, findings and follow-up text are unchanged. This turn reviews
and records conclusions; it does not repair implementation or prepare H1.

**Conclusion:** the re-audit supports M3 and the substantive A1 corrections.
Collection-status consistency, valid failed collections, degraded evidence,
unchanged wire versions, Swift fixture coverage and the unchanged maximum-reply
bound are supported. The default-coverage gap is closed. I accept the auditor's
provenance judgments and current-account corrections, and the existing M4/H1
deferrals. The auditor found no blocker to H1 preparation. As a completion
choice, I will finish the small unfinished A1-F2/F10 test repair before closing
A1 instead of carrying that known regression forward. This does not reclassify
it as a product failure or invalidate the 196-case acceptance evidence.

I checked ownership and terminal accounting of `a1-recheck-default-20261013`
(`20261013T193011Z_7e1b6661`): all 174 default cases passed, with no skips,
unrun cases or artifact changes. All 21 current app-file hashes still match its
inventory. The auditor did not rerun the 22 opt-ins because of their separate
keychain restriction; they accepted the retained opt-in evidence after reviewing
source/app provenance. That restriction is an account of their audit scope, not
a new restriction on the authorized implementation workflow.

I inspected the retained probes, Rust replay output and test-only scratch diff,
and replayed all 33 documents through the current Python consumer/oracle with
identical results. Observe-only rows deliberately expose differences; matching
outputs do not establish universal shape-validation agreement. I did not rerun
the auditor's scratch Rust build. Its results for the two reported malformed
types follow directly from the current `as_array`/`as_str` paths. The lead's
[offline review evidence](../tests/out/runs/a1-recheck-default-20261013/lead-review-20261013/README.md)
retains the reproduction script, copied-input hashes, mutated wrappers and raw
outputs. These artifacts are local-only and do not add registered case credits.

| Item | Lead disposition |
| --- | --- |
| Follow-up 1: collection and versions | Accepted. No conforming producer shape changes meaning; the repaired checks enforce the existing status meanings and preserve raw degraded evidence. Keep versions 4/17/7. Carry the suggested concise clarification of the versioning rule to M5.1 contract review. |
| Follow-up 2: isolation, Swift fixtures and bound | Accepted. The independent order/partition checks, conflicting-evidence degradation checks, shape golden and 52,414,779-byte conservative union remain intact. F10 is the exception below. |
| Follow-up 3: acceptance and cleanup | Accepted. The 30 completed prior passes plus 166 resumed passes support the 196-case set, with explicitly reviewed copied-metadata exceptions. The independent 174/174 default run strengthens the result; the historical unnamed-shared-memory limitation remains unchanged. |
| Follow-up 4: current documentation and deferrals | Accepted. Current wording matches the bounded behavior. F5, actual missing-helper-file, empty issuer-grant assertion and BYOXPC maximum-reply controls remain M4 work; F8 remains an H1 design note. |
| A1-F10 | Accepted; repair within A1 before closure. My catalog-derived exclusion was too broad: it leaves the baseline and only two nonbaseline siblings in the expectation. Independent reproduction confirms that deleting both `phases.sh` and `extensions.sh` still passes all 31 controls, while deleting an unexcluded validator script fails. Restore complete sibling coverage by adding `extension_boundaries.sh` to the witness wrapper and removing the broad catalog exclusion, then add omission mutations that must fail. Update the account and run the affected controls; this is test coverage repair, not a change to the dispatcher's case coverage or product behavior. |
| A1-F11 | Accepted and explicitly assigned to M5.1. Present wrong-type containers/values must not collapse into valid absence. Harden the Rust phase reader with negative controls for `phases: 7` and integer validator disposition, preserving optional absence and degraded raw evidence. No native completion, fresh-access or ordering fabrication was demonstrated by these probes, and the typed producer cannot emit the malformed shapes. |

The adjacent probe with an empty spawn-failure object is also retained for
M5.1: the full Python consumer rejects its shape while the narrower oracle/Rust
checks do not. Review and document the boundaries of structural validation and
claim validation rather than implying that all readers perform identical work.
This is carried with F11's malformed-evidence review, not a new M3 defect.

A1 remains open for the bounded F10 repair and its verification. Once that work
is recorded, reevaluate closure and prepare H1 under the plan's existing human
review boundary. No new live, signed or TCC-sensitive test ran in this review;
no implementation or permanent-documentation source was changed.



### A1-F10 verification and closure

The authorized repair is committed at
`7bfbdcdcb30bbc55b74a28561eb2fd1ffeeeee89`. The witness wrapper now includes
`extension_boundaries.sh`. Its independent expectation again contains every
sibling script, baseline first, without a catalog exclusion. Both all-pass and
baseline-failure controls require all 37 child receipts. Three separate copied
wrapper mutations remove `phases.sh`, `extensions.sh`, or
`extension_boundaries.sh`; each is rejected by the same receipt check for exactly
its missing child, after checking exit status, streams and other observations.
An unrelated assertion or fixture failure cannot count as the expected rejection.

The registered run [a1-f10-20261013](../tests/out/runs/a1-f10-20261013/run.json),
ID `20261013T205716Z_b30e0bce`, passed 13/13 at clean `7bfbdcd`, with no skips,
unrun cases or harness errors: `shell_helpers/script_groups`, all six
`source_drift` cases and all six dispatcher cases. The script-group case passes
35 controls. Positive wrapper controls record 37 children each; each omission
records 36 and retains the exact rejection. Source/selection/command snapshots,
console, raw fixture outputs, and the
[wrapper observations](../tests/out/runs/a1-f10-20261013/checkpoint/wrapper-observations.json)
are retained. No live runner, signing, native boundary, or TCC-sensitive test ran.

The updated [196-case credit manifest](../tests/out/runs/a1-f10-20261013/checkpoint/acceptance-credits.json)
replaces 13 earlier credits and retains 183 after the recorded conservative
[source applicability review](../tests/out/runs/a1-f10-20261013/checkpoint/source-applicability.json).
Only the wrapper, its checker, README and bookkeeping changed. Registered witness
cases dispatch their explicit child commands; the wrapper does not execute on
those paths. Build-guard fixtures copy the changed files but neither changed
script is a build input or executed build-guard control. Copied retention metadata
uses the already reviewed isolated-fixture semantics. These are explicit
applicability judgments, not a claim that every copied input is identical.
All 21 current app content hashes match the accepted build-566 inventory.
No app rebuild or new signature verification is claimed; no production input,
protocol, worker identity, baseline, or layout changed.

The existing rendered reviewer `/root/m3_rendered_review` inspected the changed
shell-helper account on actual page 2 at this source, found no issue, and
recommended closing the documentation checkpoint. Its report records a
historical requested model of `gpt-6-astra`; runtime identity was not independently
exposed. The lead independently inspected the page and accepts the no-finding
assessment. The [retained review](../tests/out/runs/a1-f10-20261013/reviews/a1-f10-rendered-recheck.txt)
and immutable source/HTML/PDF/PNG/manifests are local-only. Source hashes for all
twelve final document surfaces match their applicable renders, substituting
this review for the previous shell-helper page. The bounded scope and prior
review omissions remain explicit.

**Disposition:** F10 and the remaining half of F2 are closed. A1 is complete:
the original auditor accepted the substantive correction and candidate evidence,
its remaining small test repair is now verified, and no current-gate blocker
remains. Attributed auditor answers are unchanged. F11 and the adjacent malformed
record scope remain explicitly assigned to M5.1. Existing M4 combined-fault,
actual missing-helper-file, issuer-grant and BYOXPC maximum-reply work remains
assigned there. F8 is incorporated into H1 as a conditional measurement note,
with no persistence change proposed. H1 is prepared and awaiting the user under
the plan's human review boundary; M4 has not started. Evidence is gitignored and
available only in this checkout. Prior cleanup observations and the limitation
concerning 25 unnamed empty objects are unchanged.

## A2 Final audit — after M5.6

Status: not prepared.

### A2 Handoff, questions and auditor answers

To be populated at the waypoint.

### A2 Execution dispositions and follow-up

Pending the returned audit.
