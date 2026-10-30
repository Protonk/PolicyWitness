# C worker refactor design

R1 design examines fixed source `29d1c797f7e057dae507abf0a8b47ee6473d7b55`,
after E2's committed seal. `c_refactor` performed source inspection; no new
build, test or runtime observation is claimed by this design. The primary agent
reviews it before implementation. The governing acceptance criteria are in
`records/distribution/C-RUNNER-MODULARIZATION-PLAN.md`; this record and the workset
execution companion supply its concrete design and eventual adaptation account.

## Owners and lifetime map

The current worker is one translation unit. Its useful existing exec entry is
`attempt_exec_spawn(slot, timing, phase, index)`: the caller provides one result
destination and the worker's timing context, and never manages exec descriptors
or spawn handles. Preserve that interface and make its implementation owner
explicit. Do not introduce a worker-wide context or generic execution framework.

| State/resource | Current acquisition or initialization | Mutation/publication and ending lifetime | Intended owner |
| --- | --- | --- | --- |
| Argument/configuration values | `parse_args`, before the worker-origin sample | Immutable configuration after parse; no native authority in the struct | Lifecycle source |
| Continuous-clock origin/last sample and sticky fault | `pw_clock_start` samples exactly once before `map_region` | `pw_clock_sample` alone advances `last` or records the first rejected sample; later refusals do not read again | Timing component; lifecycle owns the stack instance |
| Timebase and converted allowances | `pw_timing_setup`, after header/extension preparation but before policy reads | One timebase query, ordered conversions, initial plan deadline; no attempt resource acquired | Timing component |
| Plan deadline | Initially `budget_ticks` after successful setup | Wait computes checked `old + sampled_wait` before release/cancel inspection, commits it exactly once immediately before acknowledgement; exec only reads it | Timing component defines arithmetic/storage; lifecycle owns the acknowledgement commit |
| Evidence mapping and borrowed slot/parameter pointers | `map_region` after clock origin; identity then prepared/header checks | Evidence helpers publish progress/failure; mappings last to process exit. No new descriptor closing/unmapping is introduced | Lifecycle source |
| Accepted extension channel, native function pointers and consume handle | `prepare_extension` before policy reads/application; entry-point resolution precedes local preparation; core limit precedes token mapping | Delivery publication, explicit consume/release actions and full token erasure retain current order; mapping persists to exit after acceptance, rejected mapping is erased/unmapped; ordinary departure never invents native release | Existing extension section in lifecycle source, unchanged |
| Policy buffer, parameter snapshot, native params and compiled profile | Static policy/consumed-parameter storage; params object only for a nonempty set; compile before ready/apply | EOF receipt precedes length/NUL rejection; free params after compile or earlier set failure; optional capture uses the exact profile before apply; existing profile/process lifetime remains unchanged | Lifecycle source |
| Exec pipe ends and spawn handles | `exec_resources_acquire`, reached inside a post-apply attempt only after budget admission | Partial setup unwinds current acquisitions; parent write ends close after spawn; remaining ends/handles release before `exec_valid` and before slot completion | Exec component; bookkeeping type private by convention to that implementation |
| Exec child identity, stream state, collection snapshot, cleanup request and reap facts | Local to `attempt_exec_spawn` after successful native spawn | Preserve WNOWAIT observation, collection freeze before cleanup/reap, group/fallback requests, nonblocking reap, actual status gating and legacy error precedence | Exec component; no state escapes except slot evidence and borrowed clock updates |
| Phase arrival/release acknowledgement, action completion, terminal publication | After successful apply | `wait_for_proceed`, `run_attempt` and `publish_done_and_exit` keep all atomic orders and token erasure visible; cancellation still exits without invented done/ack/failure | Lifecycle source |

The timing mutation boundary is deliberate. Timing owns sampling, conversions,
checked addition and sticky-fault rules. Main owns one zero-initialized
`pw_timing_t`, sets its three configuration durations, and calls origin/setup at
their current sites. Wait alone commits the checked exclusion when the numbered
release is accepted; this protocol decision remains visibly adjacent to the two
release stores. Exec borrows the same state, may advance/fault its clock through
the sampling API, and never extends the plan deadline. Tests may construct state
directly to reach overflow and prior-fault branches; production has no such knob.

## Source arrangement and interfaces

Create two guarded private implementation headers beside the worker:

- `pw_worker_timing.h`: the deadline/budget constants, clock-stage enum,
  compile-time clock seams, timing types, clock/conversion/addition functions,
  bounded timing-diagnostic text helpers and `pw_timing_setup`. Include the
  proceed-wait default here as part of the same configuration family.
- `pw_worker_exec.h`: `pw_exec_resources_t`, acquisition/release helpers,
  setup failure, stream drain and `attempt_exec_spawn`. Only the entry function
  is called from the lifecycle source; callers do not use the bookkeeping type.

`pw_probe_runner.c` remains the single compiled worker unit and includes both
owners. Its public/static ABI is unchanged. Keep `main`, argument parsing,
preparation, ordinary/extension/file attempts, `run_attempt`, `wait_for_proceed`
and terminal cleanup/publication there. The reader can follow preparation,
compile, capture, ready, apply, phase waits, attempts and terminal exit without
reading the removed exec collection/reap implementation. These already-local
lifecycle decisions do not need a new abstraction to make the required sequence
visible. The exec owner depends on timing and the slot ABI, not on lifecycle
globals or extension state; timing depends on ABI/evidence helpers and native
clock types, not on exec resources.

Use ordinary private header dependencies and preserve static linkage. Keep the
existing function bodies and native expressions byte-for-byte where practical;
no helper split, renamed failure diagnostic, extra clock read, new initialization
or cleanup behavior is needed. Header guards must not bypass interception: the
fixture defines its native and semantic-stage macros before including the worker,
whose transitive include compiles exactly the same implementation under them.
There is no separately linked uninstrumented copy.

This arrangement follows the existing `pw_worker_evidence.h` and
`pw_profile_capture.h` model. Separate `.c` units were considered and rejected
for this bounded change: they would require another mechanism to substitute
native calls across units or duplicated implementation inclusion, while adding
no required ownership distinction. A broad shared worker context was rejected
because it exposes unrelated lifecycle/extension authority to exec. Moving all
attempts or the phase protocol was rejected because these required improvements
do not need that extra relocation. No public runtime component is introduced.

## Build and documentation adaptation

The Meson worker remains a single `.c` target. Update its source/dependency
account to name the two private included components; their actual dependency
edges are compiler-generated, as for the existing private headers. No new
translation unit is invented merely to alter the manifest's source count.
`native_sources.expected` therefore continues to expect the one worker entry
source. Its configured-build closure must show both headers among compiler
inputs and identity inputs. The identity generator already walks all `.h` files
under the worker directory, so regenerate its three owned copies and review the
new digest without changing ABI geometry or wire versions.

Relocate `docs/limits.json` citations for timing constants/functions to their
actual owner; retain `main`, wait and ordinary-operation citations at the worker
source. Relocate only affected exec/timing citations in `docs/architecture.json`,
review their assertions, and regenerate the owning architecture/limits outputs.
Update the runner source map and fixture/suite references that currently point
at the monolithic exec location. Preserve historical golden provenance as
historical: the exec call-policy golden is not regenerated or relabeled.

D2 may change the documents graph and generator hint controls concurrently in
its isolated worktree. Coordinate shared-file integration with the primary
agent; these source-citation relocations belong to R1, not D2. No F1 API-list
repair, CHECK writing, Swift-driver decomposition or external-helper refactor
belongs to R1.

## Control adaptation ledger

Each row is a required review during implementation. Record the implementing
commit and executed evidence below once known; this design does not anticipate
passing results.

| Existing arrangement | Required adaptation or unchanged reach | Obligation preserved |
| --- | --- | --- |
| `check_exec_evidence.py` mutates `exec_valid` in worker `.c`, copies every native header into each variant, compiles the unchanged fixture | Read/mutate `pw_worker_exec.h`; copy the unchanged entry source and complete header closure first, then replace that variant's exec header. Keep per-variant sources/hashes/build/run receipts | Same 58-attempt native ledger and all six designated assertion failures; no golden refresh and no live-header fallback that discards the mutated owner |
| Inheritance mutation recipe rewrites empty environment and CLOEXEC flags in worker `.c` | Mutate exec owner, materialize worker plus full local header closure per variant, and compile that copied entry with its local includes | Baseline passes; environment/descriptor mutants fail the unchanged assertions with actual inherited environment/canary bytes |
| Clock, proceed, first-touch, apply/map/read/clock-failure and native-clock fixtures include worker after defining macros | Keep the same entry inclusion; review transitive headers remain inside macro scope and included once. Do not separately compile the moved bodies | Actual production calls still intercepted; existing ceiling/clock-stage/failure/publication expectations remain independent |
| Fresh-write fixture includes the worker by relative path after native-call macros | No fixture-source relocation is needed; new headers must compile through the same inclusion. Rerun its fifteen native controls | Production fresh-write calls and order remain intercepted; no duplicate action implementation or lost close/failure observation |
| Sysctl/terminal-erasure mutations copy only worker `.c` and find headers through the native include directory | Their actual mutation anchors stay in worker `.c`; review include resolution and retained input hashes/receipts include the new headers | Literal capacity and whole-buffer/before-done oracles keep their rejection power |
| Order-barrier worker mutation replaces the `wait_for_proceed` call in main; host mutation uses `CWorker.swift` | Main call and host owner stay put. Ensure rebuilt baseline/mutant worker includes new components and records their source identity | Independent early effects still reject wait/release bypass; do not treat a compilation/equipment error as a rejection |
| Compiled worker-limit probe includes worker `.c`; identity/closure checks know the native header tree | Transitive macros remain accessible; relocation tests verify changed header bytes change identity, and missing included owner refuses compilation | Compiled values, inventory, include closure, stale-copy refusal and source sensitivity survive extraction |

No new testing framework or reusable closure manager is proposed. Adapt the two
affected mutation recipes directly. Extend the existing worker-identity control
with one semantic edit in each extracted owner (and an independently specified
missing-owner build refusal if existing controls cannot establish that fact).
This demonstrates membership/sensitivity; it does not replace native ledgers or
live observations. No behavioral expectations are changed to fit the candidate.

## Execution and acceptance sequence

1. Primary review and commit this design before production edits. Confirm no
   concurrent main-checkout build/test or shared machinery mutation.
2. Extract timing and exec as one coherent candidate, adapt the two mutation
   recipes and affected references, regenerate through owners, and commit.
   Review the old/new bodies and native-call sites before running verification.
3. Build/sign the candidate through `make build` with the existing Developer ID.
   Review compiler closure for both headers, identity agreement and unchanged
   ABI layout. Do not use the old E2 app with a new worker identity.
4. Use fresh dispatcher output for the default battery, which includes source
   drift, C/Swift layout, core unit/native controls, live exec lifecycle,
   ordinary attempts, phase/publication/failure and independent consumer checks.
   Explicit additional controls are `runner_exec_inheritance/mutation_controls`,
   `runner_c_worker_harness/native_clock`, and
   `witness_contract/order_barrier_mutations`. The latter conservatively verifies
   the wait's moved timing dependency even though its protocol body stays put.
   Include applicable exec-reader/publication controls and the BYOXPC
   extension/phase witness in the primary agent's combined final selection.
5. Compare the preserved 58-attempt call policy and all rejected mutations,
   inspect native clock/proceed traces, and independently review the owners,
   lifetime/order map and actual source reach. A mismatch remains a failed
   candidate until explained; it is not permission to regenerate an expectation.
6. Record exact source, build and run identities, retained evidence, any
   applicability exceptions and adaptation commits. Accept R1 only when both
   structural improvements and preservation observations are established.
   The combined refactor seal additionally awaits the separate Swift effort.

E2's pinned coordinated run at `a7c1408` supplies the prior execution of the
unchanged exec-call controls and the other native baselines. Its later enum
fixture correction and records do not alter those dependencies, a source-review
applicability judgment rather than a new execution. R1 must establish its own
candidate behavior; the prior run is only the comparison baseline. All raw run
evidence stays local and gitignored under the repository retention contract.

## Review and implementation status

Design prepared by `c_refactor`; accepted by primary-agent source review after
independent reading of timing, exec, phase and main lifecycle sites. The reviewed design keeps phase exclusion commits adjacent to acknowledgement,
exec resources private to the attempt, and native interception transitive.
At design acceptance, no production source, build/test fixture or generator
input had been changed for R1. D2 integration and its main verification precede the implementation
so shared documentation/check changes remain distinct. No existing
behavioral promise is newly disputed by this inspection. F1 remains deferred
as directed by the user. Implementation/adaptation commits and verification
results will be added here after they exist.

## Candidate implementation

Implementation starts from clean `f8f3c24f29a3ae1a3af3802daa575ca684be751f`,
after D2 integration/acceptance and D1 retirement. The candidate commit containing
this section owns the two extractions, control adaptations and source-reference
updates together. No signed build or dispatcher execution was performed during
preparation; the old E2 app is not credited against this new identity.

Exact comparison against that source established:

| Extracted body | Bytes | SHA-256 of unchanged body |
| --- | --- | --- |
| Timing constants/types/helpers/setup | 10,268 | `c2bdd497bf5e2835dce82de454e0f5bb4acde70eae370096a16e77ff94b2e13f` |
| Exec bookkeeping/setup/collection/cleanup | 24,122 | `893dd99a561b53ba1d689627eda643b54b851a45d9a52632308ec258afef8a36` |

Both bodies are byte-for-byte extractions with header guards, declared includes
and owner comments around them. Replacing the two include directives with those
bodies reconstructs the old worker after removing only four system includes now
owned by the private headers (`mach_time`, `poll`, `spawn`, `wait`). Main,
phase wait, deadline commitment, ordinary/file/extension attempts and publication
function bodies are unchanged. The historical exec-call golden is unchanged.
These are source-comparison facts, not behavioral equivalence established by a
runtime execution.

`check_exec_evidence.py` now mutates the copied exec owner after copying the
unchanged entry and full header closure. The original ledger and six mutation
oracles remain unchanged. Two additional compile controls remove the actual
timing or exec owner and require its specific missing-include refusal; they
retain sources, hashes, command and diagnostic rather than treating any failed
compile as detection. The inheritance recipe likewise copies the complete
closure, mutates only exec and records source hashes/compiler command; its
environment and descriptor leak oracles are unchanged.

The existing identity case now applies an independently specified semantic edit
to each private owner, requires changed identity/stale-copy refusal, regenerates,
and requires currency. This is additional source-sensitivity coverage; the
native controls establish actual intercepted calls. Ordinary source membership
still expects one worker translation unit. Meson's target account names its
private dependencies; the signed-build closure check remains required to prove
what the compiler consumed.

The source-reference audit relocated five limits citations and twenty-four
architecture citations to their actual timing/exec owners, retaining lifecycle
citations and D2's documents-graph corrections. Owning generators regenerated
limits/architecture accounts and identity copies. Runner and fixture/suite
accounts describe the included owners and the mutation recipes. The new worker
identity is `b307fc295883bbcdf4bdd2b2855ce8d6fe969eb93d104e54c7e775075bad6b0f`;
wire versions and ABI geometry were not changed.

Local preparation checks passed: Python AST parsing for the three changed
scripts; `clang -fsyntax-only` for the worker, exec, clock, proceed, fresh-write,
terminal-erasure, compiled-limit and native-clock translation units; all five
generator `--check` commands; and `git diff --check`. Preprocessing the exec,
clock, proceed and fresh-write fixtures confirmed both actual owners are included
once and production call expressions use their fixture substitutions. The
fresh-write audit's first by-hand matcher expected a nonexistent local-variable
spelling; inspection corrected that matcher to the unchanged `out->truncate_rc`
assignment. It was not a compiler or product failure.

Other controls retain their original direct inclusion: sysctl snapshots already
discover all native `.c`/`.h` inputs; terminal-erasure and order-barrier variants
resolve their unmodified private headers from the fixed candidate checkout,
while their changed anchors remain in the copied entry source. Their evidence
therefore depends on the committed candidate's header bytes, not merely a
standalone mutated `.c` file. No unrelated fixture architecture was introduced.

Primary verification and structural review remain pending. In particular, the
204-case selection (201 defaults plus the three planned opt-in controls), signed
compiler closure, native ledger equality and rejected mutations have not yet
run against this candidate. F1 remains unresolved and untouched.

## R1 acceptance

Tested source is `341f9441bc96d147a1bc68b4c1df47e1f5464cb7`; this later
acceptance account is not that source. Primary review independently expanded
both private includes and reconstructed the original worker exactly after
removing the four relocated system includes. Read-only reviewer
`review_public_extension` independently confirmed that comparison, required
owners, lifecycle/state mutation boundaries, unchanged goldens/oracles and
actual fixture interception. It found no substantive defect or acceptance gap.

`make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`
built and signed version 0.3.3 build 994, `v0.3.3-141-g341f9441`, from the clean
candidate. Worker identity is the candidate digest above. Compiler dependency
output contains both new headers; the configured source/identity closure check
passed. All seven executables and two seals verified with the intended Developer
ID/team, hardened runtime and secure timestamps. This was not a public release.

Run `workset-r1-01`, `20261029T223004Z_941f9f72`, passed **204/204** cases at
the unchanged clean candidate and matching app, with no skips, unrun cases,
harness errors, observed sleep or app mutation. The dispatcher selection was
constructed from all 201 current default IDs reported by `tests/run.sh --all
--list`, plus native_clock, inheritance mutation_controls and
order_barrier_mutations; the completed ID set was checked against that catalog.
Elapsed dispatcher time was 756.539 seconds. The run and app inventory are pinned;
raw output remains local/gitignored.

The production exec control matched all 58 historical native-call rows, rejected
all six evidence mutations at their designated unchanged assertions, and refused
both missing-owner variants at the exact include boundary. Inheritance accepted
the baseline and rejected environment/descriptor leaks. The order control
accepted the baseline and rejected both worker/host bypasses through component
gates and independent CLI effects. Native clock recorded 36 million usable
continuous samples at timebase 125/3; its old-clock comparator remained a separate
observation (six failures among nine runs), not a new guarantee or repair.
Clock arithmetic, proceed precedence, fresh-write substitutions, C/Swift layout,
all 480 Swift tests and integrated partial/failure/extension cases passed.

The three structural improvements are accepted: exec bookkeeping is local to
its component; timing rules/state origins and mutations are explicit; the
lifecycle sequence can be followed without exec collection/cleanup internals.
No behavior, wire version, ABI geometry or native oracle was changed to obtain
these results. Adaptations belong to candidate `341f9441`, distinct from the
prior D2 apparatus corrections. Final combined-source verification remains
required after R2; the full refactor-stage seal awaits Swift completion. F1
remains unresolved and was not altered or established by this passing run.

## Continued applicability and plan retirement

The final combined implementation `fd90eee` / signed build 1000 passed the
R1 native-call, timing, proceed, ABI, inheritance mutation, identity/source
membership and order-barrier controls in workset-r2-final-01. Its two failures
were the separately corrected Swift contract citation and unresolved BYOXPC
transport failure. These do not reverse the independently established R1
acceptance at 96d0328e. The C modularization plan may retire now; the associated
workset still owns this design/adaptation/acceptance record, which remains until
that workset can close. The combined refactor seal remains withheld for F2.

F2's authorized reservation repair now passes combined verification on signed
build 1016, production source `4407d0ae` and test source `8500baff`. The
229-case acceptance reconciles 212 unchanged full-run passes with 17 replacement
passes, as recorded in f2-reservation-design.md and swift-refactor.md. It includes
R1's native-clock, inheritance, ABI, source/identity and order-barrier controls.
The combined C/Swift refactor stage is accepted; F1 and whole-workset disposition
remain separate. The C acceptance and protected historical evidence are unchanged.
