# Initial pytest-first counterfactual

Version C0.1, written before this workset changes implementation. The examined
repository is `bf7e97faab75754efe719b0bad20e83b67762c15`; the intake and
execution companion were committed as `4b18284`. This is an architectural
proposal and a set of expectations, not an implemented harness, benchmark,
or conclusion about whether PW should migrate. Freeze this account when C0
is sealed. Later corrections belong in attributable additions.

## Question and evidence basis

Suppose PW had used pytest from the outset to collect tests, acquire fixtures,
execute logical cases and report their outcomes. Which of its present testing
obligations would become ordinary framework work, and which would still need
specialized equipment? The comparison is with the present architecture at the
examined revision, not with a hypothetical minimal collection of Python tests.

The current public selection describes 238 catalog cases, 199 default, with
Rust, Swift, C, shell and Python execution beneath them. That selection command
was inspected; no battery was run for this account. The current
[dispatcher contract](../../tests/suites/dispatcher/README.md) and
[test guidance](../../tests/AGENTS.md) establish obligations for complete
accounting, artifact integrity, cancellation, equipment, evidence and cleanup.
The [worker account](../../docs/WORKER.md) and
[runner guidance](../../runner/AGENTS.md) explain why resource acquisition and
the position of native observations are part of the experiment.

Dated inputs, read as historical accounts:

- `records/tests/TEST-WORK-SURVEY-REPORT.md` and
  `records/tests/TEST-EXPECTATION-AUTHORITY-REPORT.md`, examined at `31b8195`.
  They distinguish execution paths, expected-answer authority, observation
  limits and source-shaped controls. Their old counts are not current counts.
- `records/archive/tests/PW-PYTEST-PATTERNS-REPORT.md`, which pins four upstream
  projects and PW `23db753`. Its useful patterns are explicit result handling,
  visible stateful sequences, independently authored malformed inputs, and
  synthetic tests of the harness. Its source inspection does not demonstrate
  a performance or maintenance benefit here.
- `records/archive/tests/PW-PYTEST-BASELINE-3ec96c1.md`, including its appended
  rejection, verification correction and limitations. The subordinate trial
  added a host beneath the existing dispatcher. Its stage-1 decision rejected
  the net machinery: 95 organizational lines removed versus about 426 added
  outside controls, with the checker itself 71 lines longer. Those measures
  characterize that trial, not a pytest-first arrangement. The later clean
  rerun at `e1db41a` also failed four drift cases because renamed test methods
  had citations in `docs/build.json`. The original narrower selection had not
  established the claimed verification. Performance timings were not an
  alternating comparison. F1–F4 were corrected later in unittest form.

No further upstream survey is needed to state this arrangement. Exact pytest
version and plugin API feasibility remain implementation assumptions; this
account does not claim compatibility with an uninspected current release.

## Proposed arrangement

Keep one public entry command, which could retain the spelling `tests/run.sh`.
It resolves the controlled execution environment and starts a small session
supervisor, then pytest as the primary test engine. It does not run the present
catalog dispatcher and then invoke pytest inside every catalog case.

There are three responsibility owners:

1. **Pytest** collects the logical cases, selects them, orders fixture setup and
   teardown, executes the case bodies, continues after ordinary independent
   failures, and emits setup/call/teardown outcomes and diagnostics.
2. **PW's pytest integration and domain adapters** declare case identity,
   equipment, default/opt-in membership and resource dependencies; enforce PW's
   outcome policy; invoke native/Rust/Swift equipment; retain specimen inputs,
   receipts and independently authored assertions. The integration translates
   framework reports into PW's durable run account without independently
   deciding that a failed pytest test passed.
3. **A session supervisor and resource owners** preserve the checkout hold,
   run ownership, cancellation and recovery outside the pytest process. They
   supervise commands and durable external resources whose lifetime cannot
   depend on a Python fixture finalizer. The supervisor does not collect test
   functions or reimplement ordinary fixture scheduling.

A normal execution would proceed as follows:

1. Admit arguments and output ownership without replacing protected evidence.
   Read-only selection does not acquire test resources. Test modules must keep
   collection free of native launches, signing and target acquisition.
2. Pytest collects and selects stable logical case IDs. It expands declared
   resource/dependency relationships through the PW integration. Publish the
   resulting selection before any case runs. A collection failure leaves a
   failed, incomplete session; it cannot be represented as zero passing cases.
3. The supervisor takes the checkout lock and establishes durable run ownership
   before execution. The execution admission rechecks output eligibility and
   selection identity. An implementation may collect again in the execution
   process, but must detect changed selection before running it.
4. Fixtures prepare immutable equipment where sharing is appropriate and fresh
   mutable inputs per independent scenario. A fixture requiring the signed app
   performs the applicable gate; unrelated offline tests remain runnable if
   that gate fails. Case bodies contain the interventions under examination.
5. Adapters launch commands through a recorded, cancellable boundary. Each
   logical case retains its inputs and raw output before mutable scratch is
   cleaned. Pytest owns the case result; a test-specific external observation
   supplies evidence, not another scheduler.
6. Setup, body and teardown reports are recorded separately. A failed teardown
   fails the case even after a successful body. A missing required resource
   produces a failure and explicit unrun dependent work. Only a declared,
   evidence-qualified skip is permissible; unexpected skips/xfails are not
   interchangeable with a passed obligation.
7. Finalization joins the collected selection with actual reports and command
   observations. Missing cases, duplicate identities, collection errors,
   incomplete cleanup and artifact changes remain explicit. The supervisor can
   mark an interrupted session incomplete when pytest cannot finish reporting.
8. Artifact reinspection, process/resource cleanup observations and retention
   decisions remain available independently of the final terminal summary.

This arrangement has one source for ordinary collection and execution results.
It still has separate witnesses for what a command or native process did.
The durable account may retain current run/case shapes where useful, but their
exact JSON encoding is an implementation choice, not the reason for keeping
complete accounting. A missing terminal result must remain distinguishable
from a legitimately reported failure in any encoding.

## Responsibility map

| Obligation | Pytest supplies | PW-specific work that remains | Present machinery that disappears or changes |
| --- | --- | --- | --- |
| Discover, select and identify cases | Collection and parameter identities; selection interface. | Stable public IDs, default/opt-in policy, equipment metadata and exact requested/dependent selection. Read-only collection contract. | Catalog entries plus shell selection guards become one declaration/collection route; compatibility aliases, if desired, need an adapter. |
| Fixture lifetimes and isolation | Setup/teardown ordering, fixture scopes, per-case parameters. | Explicit immutable sharing boundary; mutable bundles and target directories isolated; durable resources registered before acquisition can leave cleanup obligations. | Repeated temporary-directory and ordinary cleanup boilerplate can shrink; native ownership and cleanup witnesses do not disappear. |
| Assertions and failure continuation | Test assertions, phase reports and continuation among independent tests. | Authored expectations, combined-failure preservation and legal skip policy. Stateful sequences stay a single logical experiment when later actions depend on earlier ones. | Shell start/pass/fail event construction and unittest loop bookkeeping can shrink. Domain assertions and continuation guarantees must be preserved, not counted by test-method totals. |
| Polyglot tests | Python case bodies/fixtures can invoke adapters. | Rust and Swift compilation, exact native selections, independent result readers, subprocess diagnostics and non-Python failure identities. | Shell wrappers can become thin Python adapters. Rust/Swift test engines and ABI fixtures remain, rather than being rewritten in Python. |
| Equipment and signed artifacts | Fixture dependencies and setup outcomes. | Toolchain/signing/GUI checks, app inventory before/after, unchanged inspected bytes, bounded refusal and unrun accounting. | Duplicated setup declarations may consolidate; equipment failure cannot become pytest's generic skip policy. |
| Lock and descendant lifetime | No assumption that fixture teardown survives a killed engine. | OS-held checkout lock, authenticated inherited ownership, command groups and independent exit/reap observations. | A session supervisor replaces the dispatcher's execution ownership role; the essential lock/process mechanisms remain. |
| External runners | Fixture dependency structure for an owned installation. | Private registry, installation receipts, launchd identity, confirmed removal and durable pending cleanup. | Batch shell installation/leaf orchestration can become resource fixtures plus cases, but durable cleanup is not a finalizer alone. |
| Native sandbox experiments | Parametrization between independent specimens and useful failure display. | Fresh once-sandboxed worker per specimen, explicit phase order, native observers, external effects and token confinement. | No replacement of native equipment or production ordering by Python fixture order. |
| Mutations and checker sensitivity | Named variants and fixture reuse. | Real production-source interception, exact mutation formation, valid baseline, expected rejection for the intended reason and restoration. | Scenario-loop boilerplate can shrink; source bindings, independent observers and compiled control variants remain. |
| Evidence and provenance | Structured outcome reports and fixture context. | Durable raw input/output, source/build identity, partial publication, retention index and applicability review. | Current shell events and some receipt outcome bookkeeping can use framework reports. Input snapshots and direct-command receipts still have their present limits. |
| Harness verification | Synthetic tests can exercise controlled pytest outcomes. | Independent consumers, OS interruption/exit controls, selection/publication checks and deliberately malformed reports. | Existing dispatcher controls need re-expression at the new boundary; their obligations cannot be inferred from pytest's own tests. |
| Documentation bindings | No semantic support for a claim merely from a test node ID. | Owning generator inputs, source membership, citation relocation, independent assertions and review of evidence applicability. | Citation adapters may recognize new test forms; this is maintenance work even if the test body becomes shorter. |

## Difficult scenarios

### A. A failed subcase, a later case, and failed teardown

Independent malformed-record variants become separately named parameterized
items with a fresh mutable record. An immutable compiled fixture may be shared
only if its bytes and ambient use are unaffected by each case. One variant
fails its assertion, the next still runs, and cleanup can also fail. Pytest's
separate reports must retain both assertion and cleanup failures; the PW account
must remain failed and identify each affected item.

A publish/reuse/refuse/recover sequence remains one item when later actions
depend on the state established earlier. Splitting its phases into independent
parameters would change the experiment. A failed prerequisite can stop the
dependent sequence; that is distinct from silently suppressing independent
variants. This addresses the trial's failure-continuation concern without
assuming that matching method/parameter counts proves preservation.

### B. Cancellation with a command and descendant still alive

One case has completed; another has launched a helper whose descendant ignores
SIGINT; a third is selected but not started. The supervisor and command owner
record identities before launch completion, forward cancellation through the
owned boundary, apply bounded escalation, and observe exits. Pytest receives
interruption and stops starting cases. Its finalizers are useful on the ordinary
path but are not the sole owners of the lock or children.

If pytest dies before finishing reports, durable ownership and command receipts
allow the supervisor to retain the completed case, the interrupted case and
the unrun selection. If the supervisor also dies, protected descendants can
retain the OS lock and durable cleanup remains for recovery. Neither design
promises that arbitrary escaped descendants are contained. An observed signal
request is not an observed exit, and a released lock is not a complete run.

This work cannot be eliminated by using a familiar test framework. A thinner
supervisor may be possible, but giving it a second ordinary test scheduler
would reproduce a major cost of subordinate adoption.

### C. Extension intervention in one worker

A directory fixture creates controlled targets and records initial identities.
The test body asks native equipment to issue a token separately, apply one
worker policy and perform ordered before/consume/during/release/after actions.
One logical specimen remains one worker lifetime. Parametrization varies policy,
authority or target between fresh specimens, not individual phases of the same
worker. A fixture must not open the worker's target or consume authority as an
invisible convenience before the operation under examination.

The engine reports the test's authored assertions. Native calls, fresh
descriptors and external content observations establish the evidence behind
them. Unavailable path predictions stay unavailable. A future write capability
may require richer native write observations, but the initial architecture
does not assume the experiment will establish feasibility or revocation.
The framework cannot infer those facts from the token class or a successful
lifecycle return. Tokens remain in transient native channels, not fixture
parameters, logs or report attachments.

### D. A C or Swift extraction invalidates a control

An extracted production helper can leave a test that includes the old C file
outside the macros that intercepted native calls. Pytest would still collect
and report a passing test if its assertions no longer reached that helper.
The native control must therefore compile the intended extracted source with
explicit substitutions and prove sensitivity using the same independent
observer. A failure to form a mutation is an equipment/applicability failure,
not a detected behavior defect.

Similarly, a Swift type moved out of the shared API file changes client source
membership and source citations even if its codec is unchanged. Fixture reuse
may make building those variants easier, but cannot establish the production
source set or repair citations. The current repository's native-source, identity
and generator checks still have obligations. The previous pytest trial's stale
method citation is concrete evidence that test organization has this cost.

### E. Signed-app failure beside useful offline work

An app lacks a required helper or its signature/manifest inventory disagrees.
The shared app fixture refuses to supply valid equipment; dependent cases are
accounted as unrun with an equipment failure. Offline reader controls still run.
The session is failed regardless of their successes. The candidate app is
never repaired or re-signed by a fixture to satisfy its own gate. Mutated app
copies have separate ownership and are inspected as those copies.

Artifact reinspection must still happen after a failing body or ordinary
interruption. If forced termination prevents it, the account explicitly lacks
that observation. Neither a successful pytest exit nor a complete set of
Python reports alone establishes app integrity, notarization or the identity
of the source that produced the binary.

### F. BYOXPC installation survives an interrupted session

An installation fixture registers durable ownership before exposing a runner
to dependent tests. It records service name, scope, bundle path and signing
read-back. Several cases may use the owned installation, while every specimen
still gets fresh host/worker state under the production lifecycle.

On teardown the fixture requests removal and independently verifies absence.
A warning or unknown inspection keeps its staging and cleanup record. Recovery
uses that ownership record even if pytest's finalizer never ran. A later
session must not adopt or delete a service based on its name prefix. Sharing
the fixture can reduce installation repetition, but global state still limits
safe parallelism; separate worktrees alone do not isolate launchd resources.

### G. Limits, documentation and a passing checker

A generated table agrees with its manifest; a compiled value comparison agrees
as well. Those are distinct from a live observation of timeout or capacity
behavior. Parameterizing these checks under pytest does not make their oracle
independent when they share the same input. A current source citation can still
point to a function that no longer asserts the prose claim.

The durable account distinguishes source inspection, constructed inputs,
compiled comparisons and live paths. A historical receipt remains historical
when code moves or changes; reuse needs the same applicability judgment as
today. Framework-generated outcome records can simplify bookkeeping but do
not form a new semantic proof layer over documentation.

## Assumptions and expected consequences

The pytest host has pinned, explicit dependencies and controlled plugin loading.
Tested helpers retain their intended direct interpreter/import/environment
boundary. Tests of that boundary run the actual helper process with explicit
inputs; they do not substitute the pytest host's environment or assume that
its `sys.executable` and imports are the subject. Isolation may require
additional child execution, and its complexity/cost belongs in the comparison.

The initial arrangement is serial for one managed checkout. Independent
worktrees and separately owned resources could permit concurrency, but no
parallel-execution benefit is assumed. Signing, GUI services, timestamps,
kernel behavior and machine sleep remain external conditions. Dependency
failure must be distinguished from a test's ordinary assertion failure.

Expected advantages, not measured results:

- Fewer separate declarations and custom transitions for collection, ordinary
  fixture lifetimes and report phases; familiar case/parameter identities.
- Clearer isolation of independent malformed inputs and more direct display of
  setup/body/teardown failures, while explicit stateful sequences remain visible.
- Shared immutable preparation may reduce repeated compilation without sharing
  mutable records, provided the sharing boundary is actually established.
- More of the generic Python testing behavior has a standard engine owner;
  PW can concentrate its custom code on the experiment and its evidence.

Expected liabilities and surviving costs:

- The supervisor, native adapters, durable resource journals, artifact checks,
  outcome policy and evidence retention remain substantial custom machinery.
- Framework defaults for skips, capture, imports, fixture scopes and plugin
  loading can change the subject's conditions unless their boundaries are explicit.
- Finer parametrization can multiply setup work or conceal a stateful sequence;
  broader fixtures can introduce mutation coupling and forced-exit cleanup gaps.
- Polyglot execution still needs exact selection/result adapters. A second
  reporting representation can grow instead of replace current bookkeeping.
- Source-shaped controls and documentation bindings still require adaptations
  after production or test reorganization. Pytest does not reduce their semantic
  verification obligation merely by changing syntax.

No net reduction, speedup, migration suitability or superiority is claimed.
The expected benefit depends on replacing ordinary dispatch/report machinery
while keeping the specialized observer boundaries inspectable. A design that
retains the old dispatcher intact and adds a general pytest bridge would be
a materially different arrangement from this one.

## Questions subsequent work may illuminate

- How much refactor adaptation concerns generic setup/reporting, and how much
  concerns actual source membership, native interception or independent oracles?
- Which expensive preparations have a defensible immutable sharing boundary,
  and which apparent repetition preserves independence or observable timing?
- How much of a richer native effect's work is public evidence design and
  independent observation, rather than test-engine organization?
- Where can framework phase reports replace present outcome bookkeeping, and
  where must durable observations survive a dead engine or failed finalizer?
- Which documentation complications arise from test organization, and which
  remain questions of claim support and applicability regardless of framework?

These are frozen questions and expectations. This engagement records the
authorized work and its adaptations; it does not later score this account,
implement a pytest trial, or prescribe another investigator's experimental
program. C0 completion is the concrete arrangement and its inspectable limits.
