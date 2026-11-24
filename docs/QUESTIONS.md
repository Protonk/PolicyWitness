# PolicyWitness — FAQ

For instructions and worked examples, see the [user guide](PolicyWitness.md).

<!-- BEGIN SHARED QUESTIONS -->

## When should I use PolicyWitness?

Use PolicyWitness when you’re investigating whether an observed result follows from the sandbox policy under test or from some other part of the execution environment.

## Who needs to use PolicyWitness?

Almost no one. Folks authoring SBPL profiles can call `sandbox_check` and `sandbox-exec` directly and Apple's entitlements model plus their app's actual runtime behavior cover practical sandbox questions. A small wrapper script around `sandbox_check` plus `sandbox-exec` can obtain a prediction and an attempt result in the common case.

## What systems can run PolicyWitness?

The shipped app requires Apple silicon and has a minimum macOS version of 26.0. Its executables are arm64-only.

## Can PolicyWitness attribute a failed attempt to sandbox denial?

No. PolicyWitness records the failed attempt and the evidence available around it, but a failure alone does not establish that the sandbox caused it.

## What does PolicyWitness's attempt channel record?

It records what happened when the worker tried the requested operation. The four built-in kinds are `file` (open, read, write, create, unlink or check access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Each completed attempt has a PolicyWitness status and operation-specific results or errors. A failed operation counts as a completed result. If the worker could not report a result, the step records what is known about how far it got.

## How does a worker report observations under `(deny default)`?

The host prepares and pre-touches a shared-memory region before spawning the worker. The worker publishes observations there after applying its policy, and the unsandboxed host reads them to assemble the response.

## Can PolicyWitness probe operations it doesn't natively support?

Yes. Supply a helper binary and run it with an `exec` attempt. PolicyWitness records whether the helper spawned, what happened to the child, and bounded stdout and stderr. The helper must supply evidence about the operation it performed. A helper can spawn successfully and still fail at that operation.

If the helper needs permission to spawn under `(deny default)`, the optional `exec_baseline` augment grants it. The augment also grants `(allow file-read*)` unconditionally, which matters if you’re trying to observe a denied file read.

## What does a comparison record contain?

A step’s `comparison` has six fields. `observation` describes what the attempt channel saw, and `observation_basis` identifies the evidence for it. `operation_relation` and `target_relation` say whether the query and attempt name the same operation and submitted target. `order` says whether an eligible query is known to precede the phase’s attempts. `limitations` lists relevant planning exclusions or gaps in the attempt record. The query’s own answer is in `sandbox_check`. Reporting-failure replies omit comparisons, even when they retain steps.

## Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?

No. A deny prediction beside a successful attempt is reported as those two observations. A path can name a different object by the time the worker acts, and an operation can fail for reasons unrelated to the sandbox. The comparison records what PW knows about the operation, the submitted target and the order of events.

## Can PolicyWitness run every profile that `libsandbox` accepts?

No. PolicyWitness has its own limits, documented in the [limits inventory](LIMITS.md).

## What versions of SBPL are supported?

PolicyWitness passes the SBPL source to the host’s `libsandbox` compiler and supports whatever profile versions that compiler accepts. `(version 1)` is the documented profile version. Some Apple-shipped profiles use higher version numbers.

## How do I use imports with PolicyWitness?

Write `(import "name.sb")` in the SBPL source. The host OS’s `libsandbox` resolves imports during compilation. PolicyWitness also inventories literal imports for the specimen dossier. Its scanner reads absolute paths as supplied and searches for relative names in `/System/Library/Sandbox/Profiles/` first, then `/usr/share/sandbox/`. The inventory records the files the scanner found.

## Can PolicyWitness test sandbox-extension behavior?

Yes. Each actor runs in its own worker. One actor can issue a token and transfer it to another. Fresh file attempts before consumption, after consumption and after release show what the receiving actor could do at each point. See [sandbox extensions](EXTENSIONS.md) for the supported operations and authority types.

## Which happens first, the prediction or the attempt?

The host closes query collection before releasing the worker to perform that phase’s actions. A comparison marked `query_first` means PW can establish that the prediction preceded the action batch. If that order cannot be established, PW reports `unestablished`. Earlier actions in the batch can change what a later one encounters. Start a new phase if you want a prediction after such a change.

## Can PolicyWitness collect sandbox-denial logs?

No. Earlier versions included a best-effort unified-log observer. The observer and its former PolicyWitness integration are archived at [Protonk/Observer](https://github.com/Protonk/Observer). The archive is unmaintained.

## How long does a run take?

It depends on the specimen. Subtract `data.runner_client.started_at_unix_ms` from `data.runner_client.ended_at_unix_ms` to get the runner client’s elapsed wall-clock time in milliseconds. Clock adjustments can affect that difference. The whole command also includes the controller’s startup, preparation and output.

## Can I evaluate specimens in parallel?

Yes. Each specimen gets a fresh host and its own workers. Concurrent runs share machine resources, so run specimens separately if timing matters. With one installed external runner, a client can find the host occupied and run out of time before it submits the specimen. The service’s launchd throttle sets the pace at which fresh hosts can start.

## Are old versions of the app supported?

In general, no. Correlating changes across release versions is a research problem for the user.

<!-- END SHARED QUESTIONS -->
