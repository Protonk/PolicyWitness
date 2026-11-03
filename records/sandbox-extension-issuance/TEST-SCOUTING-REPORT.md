# Test scouting for integrated sandbox-extension witnessing

Source review supporting the
[sandbox-extension witnessing plan](../../SANDBOX-EXTENSION-WITNESSING-PLAN.md).
This record identifies test dependencies and recommends equipment and controls
for the plan's acceptance requirements. It is not a coverage result or an
additional implementation plan.

- Examined revision: `51ee9e28827c0193bb9134eb7556eaf01f8386ee` ("Define
  extension plan integration boundary and actor timing qualification").
- Method: inspect the catalog, relevant suite implementations, shared readers,
  fixtures, source mutations and contract owners. The catalog declares 245
  cases; the shared request corpus contains 95 examples. These are inventory
  counts, not counts of passing tests or extension coverage.
- No builds, native operations or test cases were run for this review. The
  findings describe that revision; proposed controls are future work. Exact
  source anchors and dependencies must be reviewed against the candidate.

The plan already requires most of the behaviors below. The useful additions
are their test owners, equipment choices and limits of inference. Constructed
records test interpretation; they cannot establish that native operations ran.
Instrumented fixtures do not replace the principal and calibration cases
through the supported public interface.

## 1. Existing tests and contract owners affected

### 1.1 Source-anchored mutation controls

Five controls merit explicit review when factoring the worker driver:

| Case and source | Current mutation boundary | Applicability after factoring |
| --- | --- | --- |
| `witness_contract/order_barrier_mutations` ([mutations.py](../../tests/suites/witness_contract/opt_in/mutations.py)) | Host release store in `CWorker.swift`; worker `wait_for_proceed` call | Legacy barrier and new actor phase barriers |
| `runner_unit/launch_descriptor_controls` ([launch_descriptor_controls.py](../../tests/suites/runner_unit/launch_descriptor_controls.py)) | Descriptor ownership, lifetime and close-on-exec handling in `CWorker.swift` | Launch paths using the affected ownership code |
| `runner_unit/host_setup_oracle_sensitivity` ([host_setup_oracle_sensitivity.py](../../tests/suites/runner_unit/host_setup_oracle_sensitivity.py)) | Ready-pipe dup2 direction, shared-memory descriptor argument and unmap | Session setup and its independent observers |
| `runner_unit/exec_reader_mutations` ([exec_reader_mutations.py](../../tests/suites/runner_unit/opt_in/exec_reader_mutations.py)) | Completion/publication interpretation in `CWorker.swift` and `PWRunnerAttemptEvidence.swift` | Legacy exec and actor exec where admitted; extension-participating actors cannot exec |
| `runner_unit/reaped_ack_mutation` ([reaped_ack_mutation.py](../../tests/suites/runner_unit/opt_in/reaped_ack_mutation.py)) | Final acknowledgement reconciliation at confirmed reap | Sessions using that reconciliation |

These controls check expected anchor counts; the counts are not universally
one. `Probe.swift` in the launch-descriptor control is a copied fixture, not
another mutated production file. Do not assume all anchors move to one file
or all mutations apply identically to both forms. Preserve a passing baseline
and rejection of each applicable mutant, with source/build receipts. Exercise
both drivers where they reach the changed boundary.

The barrier control's
[driver_main.swift](../../tests/suites/witness_contract/opt_in/driver_main.swift)
uses the single-worker lifecycle fixture. It needs an actor driver for actor
scheduling edges; shared session code alone does not establish their coverage.

Review native source-copy recipes if the C implementation is split:
[exec inheritance mutations](../../tests/suites/runner_exec_inheritance/opt_in/mutations.py)
copy the worker and headers and mutate `pw_worker_exec.h`;
[exec_domain.py](../../tests/suites/runner_c_worker_harness/exec_domain.py),
[check_sysctl.py](../../tests/suites/runner_c_worker_harness/check_sysctl.py) and
[check_terminal_erasure.py](../../tests/suites/runner_c_worker_harness/check_terminal_erasure.py)
compile copied sources. Supply each fixture's actual include/link dependency
closure and receipts. Exec-domain compile controls establish source-domain
constraints, not native behavior. Choose the source split before updating
recipes, without assuming every recipe necessarily changes.

### 1.2 Actor barrier observations

Add controls for these scheduler faults:

- A parked actor performs a specimen action or native consume when delivery
  arrives, before its own phase release.
- The host releases a subsequent actor without the preceding phase's completion
  or the independently established quiescence permitting advancement after
  failure.
- The host substitutes timestamp order for that completion/quiescence evidence
  after an unresolved termination.

The held-effect pattern in
[check_ordering.py](../../tests/suites/witness_contract/check_ordering.py) is
useful, but its current reader and specimens are single-worker. Actor controls
need scoped observers and a native-call receipt where the forbidden operation
has no externally visible file effect. Missing publication is not proof that
consume never ran. Do not assume each fault is a one-line mutation.

### 1.3 Shared readers and cleanup ownership

- [extension_evidence.py](../../tests/lib/extension_evidence.py) correctly
  enforces the legacy declaration and consume/release limits. Dispatch on
  `execution_form`; preserve those rules while adding typed actor token,
  delivery and handle references. Do not loosen the legacy validator to accept
  both forms indiscriminately.
- [lifecycle_oracle.py](../../tests/lib/lifecycle_oracle.py) and
  [lifecycle_contract.py](../../tests/lib/lifecycle_contract.py) need scoped
  disposition and evidence-reference resolution. Aggregate failure must retain
  each actor's raw facts, including simultaneous faults.
- [worker_exit_witness.py](../../tests/lib/worker_exit_witness.py) currently
  accepts only a valid `runner_subprocess.pid` with `reaped == true` as positive
  exit evidence. Extend cleanup accounting before the first live actor case:
  require a complete ownership roster and positive exit evidence for every
  launched actor. Established never-launched actors do not require fictitious
  reaps; missing actors or replies do not establish absence. Validator,
  descendant and resource owners still need their applicable cleanup evidence.
  Unknown ownership/exit retains staging for recovery.
- [consumer.py](../../tests/lib/consumer.py) and
  [blackbox.py](../../tests/lib/blackbox.py) need actor-aware shape, policy-hash
  and apply checks. Replace singular assumptions with per-actor assertions;
  do not disable policy validation because the singular projection is null.
  Applied actors need their policy dossier and application evidence; unapplied
  actors must not acquire invented hashes or apply results.
- [phase_evidence.py](../../tests/lib/phase_evidence.py) needs actor/phase/visit
  joins and the correct query target. Validator PID uniqueness remains an
  invalid requirement; section 2.3 distinguishes target and validator PIDs.

### 1.4 Captures, goldens and constructed controls

These fixtures have different refresh procedures:

| Material | Treatment at the coordinated contract bump |
| --- | --- |
| Four live checker capture/specimen pairs under [blackbox_e2e/checker](../../tests/fixtures/blackbox_e2e/checker/README.md) | Capture new, unmodified envelopes from the final candidate into `responseNN/`; preserve historical captures |
| Live deadline/disposition pair under [disposition](../../tests/fixtures/disposition/README.md) | Refresh with the checker captures, retaining producer identity and managed run |
| `response_shape.json`, `envelope_shape.json` | Review encoded candidate shapes from their owning Swift/Rust tests |
| `phase_collection.json`, `evidence_types.json` | Extend hand-authored mutation/control cases and their consumers; these are not live shape goldens |
| `path_diagnostics.json`, generated [contract.py](../../tests/lib/contract.py) | Update deliberate version expectations and regenerate constants through their owners |

Follow the fixture READMEs and retain credited runs through `tests/RETAINED.json`.
Never edit a historical capture's version number to make it current.

Add real actor captures covering the principal specimen's actual outcome,
positive calibration through fresh access, and native refusal. Principal
refusal may cover the last category; principal success is not required.
Constructed mutations establish reader sensitivity, not missing native coverage.
Draft DTO tests in stages 1–2 are not public capture baselines. The public
version transition occurs on the stage 3 branch candidate, accepted in stage 4.

### 1.5 Limits and ABI owners

Current owners include `LimitsContractTests.swift`,
[limits.py](../../tests/suites/runner_abi_layout/limits.py) and the request
corpus. Preserve legacy counts and semantics. Add proposed actor counts,
aggregate storage and action limits with independent expectations and suitable
exact, plus-one, multibyte and cross-actor aggregate controls. The aggregate
budget must not become a per-actor multiplier. Use admission tests for syntactic
bounds and live controls for consequential execution bounds; not every
combination needs a separate live run.

[extension_layout.py](../../tests/suites/runner_abi_layout/extension_layout.py)
compares `PWExtensionLayout` in `ExtensionIssuer.swift` with a compiled header
printer. The main [abi_layout.txt](../../tests/fixtures/contract/abi_layout.txt)
has separate geometry coverage. Add printers/mirrors for actual new channel
layouts and update the main golden where affected, rather than assuming all
channel geometry belongs to it. Check widths, offsets, capacity arithmetic
and C/Swift agreement, including maximal encoded evidence.

### 1.6 Native worker harness

Release controls in
[harness.c](../../tests/suites/runner_c_worker_harness/harness.c) exercise one
worker wait. Reuse deterministic clock/polling controls where new waits share
code, while testing distinct activation, phase-release, delivery and custody
acknowledgement states. Activation before setup must refuse, not run a native
action. Concurrent actors and scheduling need host/live equipment beyond this
C harness.

Extend terminal-erasure controls to every owned delivery slot and outbound
scratch area, including unused/rejected capacity. Preserve accepted bytes until
their last scheduled use: another consume may reference the same delivery.
Distinguish full owned-capacity erasure from the extent of a native allocation,
and byte erasure from handle release. Process death must not invent cleanup.

Extend `clock_arithmetic`, `proceed_precedence` and `exec_control_states` for
applicable cutoffs, enclosing budgets, exact exhaustion and invalid clocks.
These checks precede, but cannot replace, signed timing qualification under
actual parked-actor load.

### 1.7 Admission corpus and test seams

The 95 shared [request examples](../../tests/fixtures/request_contract/examples.json)
feed CLI, direct-XPC and Swift admission tests. Add mixed-form, actor ownership,
forward-reference, self-transfer, repeated-consume, exec participation,
unapplied-policy and aggregate-bound cases. Distinct handle references may
arise from repeated consumption of one delivery; that is not illegal reuse of
a declaration ID.

[failure_boundaries/check.py](../../tests/suites/failure_boundaries/check.py)
has legacy extension-specific rewriting. Extend its matrix for new fields,
simultaneous violations and no-echo diagnostics for policy sources. Stage 1
tests draft forms without opening public admission; stage 3 wires both entry
points on the branch. `main` stays unchanged until stage 4 acceptance, with no
temporary `actor_unavailable` contract.

Scope worker interruption seams to actor/phase/action when needed under
[runner/AGENTS.md](../../runner/AGENTS.md). Specimen-wide budgets and aggregate
validator controls can remain global; not every `_test_overrides` key needs an
actor selector. Preserve legacy meanings and refuse invalid selectors before
children. Use controlled internal drivers for boundaries they can establish,
and public seams for reachable integrated behavior. An echoed seam request does
not prove the boundary occurred; retain an independent receipt. Do not add
result-fabricating native seams to production behavior.

### 1.8 Rust readers and legacy compatibility

`extension_account_issues` in `controller/src/disposition.rs`,
`unit/rust.disposition_reds`, shared constructed controls and dossier tests need
actor associations and failure propagation. Keep reader agreement without using
one reader's output as the other's oracle. Actor-local step names alone cannot
identify a global observation. Degraded replies and combined failures must
preserve uncertainty rather than invent singular projections.

Legacy extension, boundary, combination, directory, BYOXPC and blackbox cases
remain the adapter's battery. Behavioral expectations remain; version, shape
and fixture plumbing may need deliberate updates. Two equipment details:

- [check_extensions.py](../../tests/suites/witness_contract/check_extensions.py)
  locates a specific `$PW_EXTENSION_DIR/request.json` heredoc in the guide,
  not every example named `request.json`. If documentation moves or duplicates
  that marker, give the example an unambiguous owner/locator.
- [control.c](../../tests/fixtures/extension_controls/control.c) provides useful
  native substitutions and receipts. Reuse them where applicable, but do not
  force host custody/scheduling and all new C controls into one mode table.
  Shared build code is useful; independent behavioral oracles must survive.

## 2. Concrete controls and equipment to assign

These recommendations operationalize existing plan requirements. Proposed case
names are not present coverage: register actual equipment and managed evidence
before claiming acceptance credit.

### 2.1 Principal-policy qualification

Register the entry check, for example as proposed
`witness_contract/extension_policy_qualification`: compile the exact B policy
with `sbpl-check`, then apply it through the existing single-worker path. Tie
the qualified policy to the principal specimen by exact source identity. This
tests compile/application, not re-delegation.

Compile/apply failure blocks principal credit and requires the plan's explicit
reconsideration, not a bare/literal-path fallback. Issuance refusal can satisfy
the principal witnessing case only after the required policy has applied.
Positive calibration remains a separate mandatory gate. This check does not
require another standalone investigation.

### 2.2 Parked-actor quiescence

[launch_inventory.py](../../tests/suites/runner_exec_inheritance/launch_inventory.py)
observes two sequential specimens using process name/arguments and a baseline
inventory. It is not a concurrent actor ownership oracle. Join owned launch
receipts to actor IDs and independently observed PID/start identity and
parentage; a matching process name is insufficient.

In a controlled driver, hold the schedule in A's phase after its explicit
transfer to parked B. Witness B's delivery acknowledgement while no B consume
or specimen effect occurs during the held interval. Use a native-call receipt
as well as a file-effect observer. Then complete A's phase and release the same
B to observe its operation, ruling out a dead or never-started actor as the
reason for apparent quiescence. A disposable variant that consumes early without
publishing must make the independent observer fail, even if the ordinary reader
sees no inconsistent record. Do not issue a transfer during a collection hold
that forbids the sending actor's actions.

### 2.3 Query target identity and eligibility

`runner_use_c_worker/sandbox_check_pid_matches_worker` checks
`sandbox_check.pid` against `runner_subprocess.pid`. That field is the query
target, not `validator_subprocess.pid`: the validator is a different process.

Bind each phase's query target to its actor and visit. Reject a sibling target,
copied visit or conflicting reference; withhold `query_first` while retaining
raw evidence. Synthesized unavailable records still need the target association
but do not prove a validator ran. Do not invent a validator subprocess or
require globally unique PIDs across reaped processes.

### 2.4 Custody faults, host loss and cleanup

[host_setup_controls.py](../../tests/suites/runner_unit/host_setup_controls.py)
and [SetupControls.swift](../../tests/fixtures/host_setup/SetupControls.swift)
provide controlled production-source copies and adapters. They use real
process/descriptor boundaries; they are not kernel-free tests. Extend the
pattern to lost acknowledgements, wrong slot/generation/recipient and
interrupted custody copies, with receipts for which boundary occurred.

Modelled host failure tests deterministic state handling. Actual host-death
claims need a disposable owned host terminated at a recorded boundary, with
independent child-lifetime and cleanup observations. A killed host cannot be
expected to produce its final reply. Unknown exit/resource ownership retains
recovery state, not a claim of successful cleanup.

The [worker lifecycle fixture](../../tests/fixtures/worker_lifecycle/worker.c)
can gain actor protocol messages such as arrival and delivery acknowledgement.
These are test-double publications, not authority tokens or proof of native
consumption. Keep real native calls in public calibration and applicable
boundary controls.

### 2.5 Authority-byte confinement and lifetime

[check_extension_boundaries.py](../../tests/suites/witness_contract/check_extension_boundaries.py)
uses a transient observer copy of a real token to check output, request,
arguments, environment and artifacts. Extend it to every issuance result,
comparing bytes in memory before persisting captures. Cover ordinary/degraded
replies, stderr, dossiers and relevant encoded transport layers. Withhold
deliberately leaked output from artifacts; retain a byte-free sensitivity
result instead. Observe the explicitly requested calls; do not add issuance
calls solely to supply the detector.

The principal chain has two logical issuances, not a fixed number of copies or
necessarily two different byte strings. Inventory native allocations, actor
scratch, each host custody/delivery slot and observer copies with their owners
and lifetimes. Add serialization and shortened/early-erasure mutations with
receipts. Repeated consume must survive until last use; terminal erasure must
cover unused/rejected owned capacity as well as accepted bytes.

### 2.6 Fresh access, inherited descriptors and replacement

Adapt `contaminated_worker` equipment from
[runner_exec_inheritance](../../tests/suites/runner_exec_inheritance/run.sh)
to introduce a known target descriptor through a disposable launch path. The
independent checker must detect contaminated setup or a missing fresh open.
A general JSON reader cannot infer a hidden inherited descriptor from a
successful read, and should not rewrite a native result merely because this
control cannot credit delegation.

Adapt the replacement scenario in `check_extensions.py` to replace the path
between B's issuance and C's consumption. The current control keeps the old
inode open outside the worker, observes replacement independently and checks
new identity/content if the fresh open succeeds; it does not require success.
Preserve that distinction. Retain native failure or observed replacement access
without claiming original-resource continuity or a general revocation property.

### 2.7 Unapplied actors and inherited restrictions

`runner_byoxpc/entitlement_transfer` tests an applied SBPL `require-entitlement`
rule using a signing entitlement. It does not supply an existing App Sandbox
restriction that survives removing SBPL application. Its fixture therefore
cannot establish that an unapplied actor remains sandboxed.

Reuse its owned installation, signing/read-back and recovery helpers, but use
an actually restricted worker fixture for that claim: an App Sandbox signing
configuration with an independently observed baseline restriction on a
test-owned target outside its automatic allowance. Pair it with an appropriate
available-access control. Keep signing evidence and behavior distinct; an
entitlement key or permission-shaped errno alone does not prove cause. This
is additional acceptance equipment, not coverage the current case provides.

Reader controls separately reject invented application/hash evidence for an
unapplied actor, and eligibility for an apply actor with missing application.
They do not replace the native restriction case.

### 2.8 Process identity without exec

[runner_live_worker_identity](../../tests/suites/runner_live_worker_identity/README.md)
uses an exec helper's socket peer identity and kernel parent information to
identify the worker, then queries it independently. Extension actors cannot
use that exec rendezvous.

For the session gate, use a controlled boundary with owned launch receipts and
external kernel PID/start/parent observations. Query the parked actor's policy
using distinguishable allowed/refused operations while another actor owns the
schedule. Inventory any receipt channel before apply; do not add a post-apply
reporting dependency to the policy. Identify instrumented equipment separately
from ordinary public specimens. These queries establish policy/process
association, not issuance prediction.

### 2.9 Legacy helper dependency

Extend the owned missing-issuer BYOXPC wrapper, where applicable, to contrast
legacy refusal with actor execution that launches no issuer helper. It already
removes/restores the installed helper with recovery ownership. `runner validate`
must continue to report the mutated installation invalid and report it healthy
only after restoration/verification.

This is a controlled dependency test, not a promise to run arbitrary invalid
bundles. Do not weaken installation/signature validation to make it pass. If
platform validation prevents the live contrast, establish the dependency at
the owned host launch boundary and retain the mutated-bundle test's limitation.
Binary inventory may mention the helper; absence of a helper launch, rather
than absence of all issuer metadata, is the assertion.

### 2.10 Unsupported response without replay

Live equipment already exists in
[reservation_controls.py](../../tests/suites/runner_byoxpc/opt_in/reservation_controls.py):
owned instrumented hosts/clients, execution traces and controlled reply loss.
Its old-control case rejects an unsupported XPC protocol before submission.
That differs from an unsupported JSON response after execution.

Extend it to change only the outgoing response-schema marker to the previous
version after one real execution under the current XPC protocol. Require the
controller's unsupported-response result, retention of the opaque reply under
the existing contract, and independent traces/effects showing one execution
and no resubmission. The client transports data; the controller interprets the
semantic response version.

This tests the live boundary without retaining an old signed runner or creating
another service framework. It does not establish all interoperability with an
actual historical host. Preserve that limit and the constructed reader controls.

### 2.11 Execution-form and lifecycle associations

Assert `execution_form` against the submitted form, actor-form null singular
projections and preserved legacy projections. The discriminator establishes
reported shape, not which private driver ran. Common session code is allowed;
legacy issuer sequencing, lifetime and signing observations establish adapter
compatibility.

Assign the plan's multi-object controls to corpus, host/native and public cases:
repeated consumes with distinct handle references; self-transfer and fanout;
equal native handle values without reference deduplication; zero as a possible
handle and only `-1` as no handle; failed release without changing a sibling;
sender death before/after custody; and transfer publication before death.
Custody alone must not cause unrequested delivery. Wrong recipient, generation
or sibling-token associations need rejecting controls even when superficial
native return values look successful.

### 2.12 Existing integration and timing decisions

Do not reopen the integration choice: stages 1–3 stay on the branch, public
admission/version wiring occurs in stage 3, and `main` receives only the stage 4
accepted result. Missing calibration, principal-policy qualification or required
timing coverage holds acceptance and the FAQ change.

The plan already specifies matched one/three/eight-actor qualification, maximum
aggregate work, principal/calibration under parked load, timing observations
and 25-percent effective-budget headroom. Register those workloads with managed
evidence. External CPU observations are useful where available; the plan does
not require a particular `rusage` interface. Deterministic deadlines and
intentional timeouts remain separate from normal-load qualification. An honest
timeout can pass a failure-path test while failing timing acceptance.

## 3. Integration with the plan

The associated plan carries the concrete dependencies and acceptance gates;
this record retains the detailed test inventory. The stage mapping is:

| Point in the plan | Addition or clarification to carry forward |
| --- | --- |
| Implementation entry | Catalogued exact-policy compile/apply qualification, with no automatic fallback and no delegation credit from that check |
| Stage 1 | Scoped reader/dossier controls, draft admission corpus and complete cleanup ownership model; identify fixture owners without publishing new versions |
| Stage 2 | Review five source-mutation controls by applicability; independent actor identity and parked phase quiescence; cleanup helpers adapted before live actor tests |
| Stage 3 | Public authority chain plus independent native-call/fresh-access observations, parked delivery/consume controls, multi-object associations, custody faults and byte-confinement sensitivity; coordinated reader/ABI/version work |
| Stage 4 | New unmodified captures including calibration/refusal; actual inherited-restriction equipment; helper-dependency and live unsupported-response/no-replay controls; existing signed timing and compatibility gates |

The associated plan links to this report under [records guidance](../AGENTS.md).
Keep detailed source paths and equipment choices here until implementation
assigns them to suite accounts; permanent documentation and tests should not
link to this planning record. Do not duplicate the inventory in the plan or
expand deferred native families into obligations.

## 4. Retention and consolidation

Retire no tests now. The legacy battery remains necessary while its form is
supported. Native counterfactuals remain applicable when changed calls or
signatures need them; actor scheduling does not automatically require rerunning
every native family experiment.

Share build recipes, owned BYOXPC setup and suitable observers without weakening
receipts or recovery. Keep the C wait/clock harness, Swift scheduling controls,
native boundary controls and public live cases distinct: they establish
different facts. Neither one ordering driver nor one giant seam table replaces
those levels of evidence. The historical investigation remains unchanged and
is not a maintained test dependency merely because its equipment is useful.
