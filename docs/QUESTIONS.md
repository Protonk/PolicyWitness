# PolicyWitness — FAQ

The following questions are answered briefly with exhaustive detail remanded to the [user guide](PolicyWitness.md). The questions between the shared markers are copied into the guide's Questions section by `docs/generate_limits.py`; links into the guide are written as `PolicyWitness.md#anchor` and become internal links in the copy.

<!-- BEGIN SHARED QUESTIONS -->

## When should I use PolicyWitness?

Use it for a repeatable experiment about a sandbox policy: prepare a saved request, collect a prediction where available, perform the requested actions and retain the observations. Start with the [quick start](PolicyWitness.md#quick-start), then read the [result account](PolicyWitness.md#reading-a-result) before comparing runs.

## Who needs to use PolicyWitness?

Developers investigating sandbox policy, native API behavior and process authority can use the same specimen and report to state exactly what they observed. A useful experiment identifies its target, its expected observation and an independent way to inspect the effect.

## What systems can run PolicyWitness?

The shipped app requires macOS 26 or later on Apple silicon (arm64).

## Can PolicyWitness attribute a failed attempt to sandbox denial?

A permission-shaped failure records a native result such as `EPERM`, `EACCES` or a bootstrap permission result. The report preserves that observation and the separately collected query answer. Establishing the cause requires evidence that distinguishes sandbox enforcement from the other reasons the native operation can fail.

## What does PolicyWitness's attempt channel record?

It records the requested operation's published result and the evidence that supports it. A completed failed operation is a result. A missing or incomplete publication stays unavailable, with lifecycle evidence showing whether the action boundary was reached. File, Mach lookup, sysctl and exec operations have [different observations](PolicyWitness.md#attempt-kinds-the-runner-implements).

## How does a worker report observations under `(deny default)`?

The host prepares shared evidence memory before the worker applies the policy. The worker publishes bounded observations there, and the host collects them after execution and cleanup. The host's reply path remains in its own unsandboxed process. Publication, collection and final process status each have their own records.

## Can PolicyWitness probe operations it doesn't natively support?

An `exec/spawn` attempt can run your helper and retain its bounded stdout, stderr and child-process observations. Arrange for the helper to report the native result and supporting effect you need. The [exec augment](PolicyWitness.md#augments) adds process permissions and an unconditional file-read allow; choose it only when those added permissions fit the experiment.

## What does a comparison record contain?

It records the attempt observation and its basis, the relationship between submitted operations and targets, query order and limitations. The prediction stays in `sandbox_check`. [Reading a comparison](PolicyWitness.md#reading-a-comparison-record) explains the six fields together. Reporting-failure replies omit comparisons while retaining the observations their fallback form can carry.

## Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?

The report supplies the query answer, attempt observation and the relationships it can establish. `query_first` establishes collection before the phase's actions; `same_submitted` compares submitted target bytes. Runtime object identity and changes between query and action require additional observations for an agreement or disagreement claim.

## Can PolicyWitness run every profile that `libsandbox` accepts?

PolicyWitness admits requests within its grammar, action relationships and [limits](PolicyWitness.md#limits). The worker then uses the host OS's native compiler and applies the resulting profile. Compilation, application and completion are separate observations, each with its own failure record.

## What versions of SBPL are supported?

SBPL is interpreted by the installed OS's `libsandbox`. Keep the recorded macOS build, selected source and parameters with the result when comparing compiler behavior. The [compiler helper](PolicyWitness.md#sbpl-check-sbpl-check) gives an independent host-side compilation diagnostic.

## How do I use imports with PolicyWitness?

Write native `(import "name.sb")` expressions in the policy. The controller separately inventories literal imports: absolute names are read as supplied; relative names are searched under `/System/Library/Sandbox/Profiles/` and then `/usr/share/sandbox/`. Preserve each inventory's errors, hashes and truncation status alongside the native compiler result. The [dossier](PolicyWitness.md#the-specimen-dossier) describes that inspection and the source selected for invocation.

## Can PolicyWitness test sandbox-extension behavior?

Use [actors and sandbox extensions](PolicyWitness.md#sandbox-extensions). Each actor selects equipment and either applies a policy or declares an unapplied path. Explicit issue, transfer, consume and release actions record native calls and host custody separately. Fresh file attempts before and after those actions observe access at those moments.

## Which happens first, the prediction or the attempt?

The host closes a phase's query collection before releasing its action batch. A qualifying native answer has `comparison.order: query_first` when the report carries the supporting release and acknowledgement chain. Actions run in declaration order; an earlier action can change the state a later action encounters. Use [ordered phases](PolicyWitness.md#ordered-phases) to collect again after earlier actions.

## Can PolicyWitness collect sandbox-denial logs?

The result records query, worker, transport and process-lifecycle evidence. If you collect unified logs separately, retain their collection conditions and correlate them with the saved run; a log entry's availability and attribution require their own evidence.

## How long does a run take?

The saved client start/end wall-clock milliseconds describe its observed span;
wall-clock adjustments can affect their difference. Client acquisition/reply allowance, host collection and cleanup, worker waits and exec observation have separate clocks and [budgets](PolicyWitness.md#execution-budgets). A client deadline can expire after execution was invoked. Inspect [submission state](PolicyWitness.md#receiver-evidence) before deciding whether a retry could repeat an effect.

## Can I evaluate specimens in parallel?

Each run acquires a fresh host and fresh specimen workers. Concurrent runs share machine resources and an installed service's launch pacing; acquisition can encounter an occupied host. Use independent request, result and target paths, retain each run's submission state and inspect its outcome. The [operating guidance](PolicyWitness.md#running-specimens-in-parallel) describes the separate process lifetimes.

## Are old versions of the app supported?

Use the guide shipped with the app and retain its exact `build.contract`. Each release preserves its contract and shape history for interpreting that release's reports. Review the [surface table](PolicyWitness.md#public-contract-surfaces) before updating an existing request for another build.

<!-- END SHARED QUESTIONS -->
