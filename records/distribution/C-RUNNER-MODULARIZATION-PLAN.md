# C runner modularization: goals and acceptance

This draft defines the intended improvements, scope and acceptance criteria
for reorganizing the C worker. The next work is design preparation: establish
ownership and dependencies, examine the alternatives, and propose how the
criteria will be met. Source layout, interfaces, compilation arrangements,
test adaptations and implementation sequencing remain for that future work.

## Purpose and scope

[pw_probe_runner.c](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
contains worker preparation, policy compilation/application, timing, attempt
implementations, phase waiting and terminal publication. The intended result
is clearer ownership and narrower dependencies, with the ordering and resource
lifetimes that define the experiment remaining easy to inspect.

The implementation scope is the C worker and its private supporting code,
including existing headers where necessary. Build inventories, generated
identity, affected controls and source/documentation references are supporting
work. The validator, extension issuer, Swift driver and Rust controller are
outside the decomposition scope. Necessary generated metadata updates do not
expand that scope. New capabilities, behavioral repairs and performance changes
are separate work.

Acceptance requires both the structural improvements below and evidence that
behavior is preserved. Smaller files or passing existing tests alone do not
meet both requirements. There is no target file count or line limit, and a
component boundary here does not prescribe a separate compilation unit.

## Required improvements

| Improvement | Acceptance criterion |
| --- | --- |
| Cohesive exec-attempt machinery | Pipe setup, spawn configuration, stream collection, child observation and exec cleanup have an identifiable component owner. Resource bookkeeping is private to that responsibility. Callers supply explicit inputs and result destinations without managing its internal descriptors or spawn handles. |
| Cohesive timing responsibilities | Clock sampling, conversions, budget arithmetic and clock-fault state have a coherent owner. Phase waiting and exec attempts use those rules without duplicate implementations. The origin, mutation and use of timing state are traceable across the boundary. |
| A clearer worker lifecycle | A reviewer can follow preparation, policy application, phase waiting, attempt dispatch and terminal publication without reading exec implementation details. The ordering of consequential operations and their cleanup obligations remains visible. |

For each boundary, review must establish what state and resources it owns,
what it borrows or receives, what it can publish, and who ends each lifetime.
The proposed separation must reduce the unrelated implementation a reader
needs to inspect. Moving code behind a broad shared-state interface while
leaving callers responsible for its internals does not meet that criterion.

These are required outcomes. The future design may refine their boundaries,
but cannot silently replace them with file movement alone. If ownership or
behavioral constraints make an outcome unsuitable, revise the proposal with
the supporting evidence before treating a different outcome as sufficient.

## Behavior to preserve

The reorganization preserves:

- Preparation and native resource acquisition relative to policy application,
  including exec resources acquired within the attempted operation and their
  cleanup before the slot completes. Extraction introduces no hidden resource
  acquisition or initialization at an earlier stage.
- Semantically relevant native-call order, arguments, return/error capture,
  descriptor inheritance and lifetimes, child observation and cleanup behavior,
  including partial setup and interrupted execution.
- Clock sampling and budget semantics, including the shared timing state used
  by phase waiting and exec attempts. New boundaries do not add observations or
  reinterpret existing ones as an incidental consequence of extraction.
- Phase arrival, release acknowledgement, cancellation, progress and result
  publication, memory ordering, token erasure and terminal paths. Cleanup and
  publication retain their distinct meanings on failure as well as success.
- Shared-memory layout, accepted inputs, published evidence and its meanings.
  Missing observations remain missing; return codes and permission-shaped
  failures do not acquire stronger causal interpretations.

The [worker account](../../docs/WORKER.md),
[runner reference](../../runner/README.md) and
[wire contract](../../docs/CONTRACT.md) provide the existing boundaries and
meanings. Source relocation can change generated worker identity; preserving
that old identity is not a requirement. Preserving the runtime contract is.

## Evidence required for acceptance

Structural review must identify the resulting owners and show how each
required improvement was achieved. Behavioral evidence must exercise the
extracted production implementation, with any controlled substitutions made
explicit, and retain independent expectations about its observations.

The existing [exec controls](../../tests/suites/runner_c_worker_harness/check_exec_evidence.py)
compare native-call ledgers and reject altered evidence assembly. The
[phase-wait control](../../tests/fixtures/worker_lifecycle/proceed_control.c)
observes acknowledgement and action boundaries with controlled time. These
illustrate useful evidence and a constraint on design: controls currently
include worker source after defining interception macros. A passing control
is insufficient if extraction leaves the relevant implementation outside its
interceptions or exercises a duplicate implementation instead.

The eventual verification design must account for native-call observations,
controlled failures and rejected mutations, shared-layout agreement, source
coverage by the build/identity machinery, and integrated worker behavior.
Changes to test packaging must preserve what the checks can refute. Differences
from existing expectations require investigation; updating expectations to
match the reorganized implementation is not itself evidence of preservation.

Exact cases, baseline evidence and any additional controls remain to be
selected against the proposed boundaries. The selection follows
[tests/AGENTS.md](../../tests/AGENTS.md), including the ordering mutation control
when the worker wait, release store or eligibility rule changes. Compilation
and source-inventory checks cannot substitute for observations of execution.

## Design work before an execution plan

A future team needs to establish an ownership map covering mutable state,
acquisition and release sites, publication sites, and their position relative
to policy application. That map supplies the basis for deciding the following
questions; this draft does not choose their answers.

| Open question | Interaction with acceptance |
| --- | --- |
| How should source files, headers and compilation units be arranged? | The arrangement must provide useful boundaries while preserving production-source coverage and the reach of native-call interception in controls. |
| What interfaces and state representation should connect the components? | They must express ownership and result destinations without exposing internal bookkeeping or changing initialization, lifetime or timing behavior. |
| Where should lifecycle, cleanup and publication code remain together? | The result must make critical order and terminal obligations inspectable while delivering the required separation of exec details. |
| How should controls and build/source-identity checks adapt? | They must cover the actual extracted implementation and still detect the faults they claim to detect. Their current assumptions about a single worker source need explicit examination. |
| What sequence and verification checkpoints make the work reviewable? | Each proposed checkpoint needs a concrete structural outcome and applicable preservation evidence. Preparatory changes must support a named improvement. |

The next proposal should resolve consequential choices, identify the source
and evidence supporting them, and map every acceptance criterion to a review
or observation capable of rejecting a deficient result. Narrow experiments
may be needed to settle compilation or instrumentation questions. The output
of that preparation is an execution plan; this draft supplies its goals and
constraints.
