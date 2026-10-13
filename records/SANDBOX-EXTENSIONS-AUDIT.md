# Sandbox extensions out-of-band audits

This is the shared handoff document for the middle and final audits in
[the implementation plan](../SANDBOX-EXTENSIONS-PLAN.md#out-of-band-audit-handoffs).
The executing agent prepares each exchange at its waypoint, identifying the
reviewed source/build and documentation/evidence locations before writing the
questions. The auditor writes answers and additional findings in the same
section. Execution dispositions remain separate from the attributed audit text.

## A1 Middle audit — after M3

Status: auditor answers returned on 2026-10-13 (Claude Fable 5.1, out of band);
executing-agent review recorded below; corrective follow-up pending. M3 implementation and its
rendered-documentation assessment are complete. This exchange is not A1
closure; execution is standing by before H1 and M4.

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

## A2 Final audit — after M5.6

Status: not prepared.

### A2 Handoff, questions and auditor answers

To be populated at the waypoint.

### A2 Execution dispositions and follow-up

Pending the returned audit.
