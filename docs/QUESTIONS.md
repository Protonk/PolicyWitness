# PolicyWitness — FAQ

The following questions are answered briefly with exhaustive detail remanded to the [user guide](PolicyWitness.md). The questions between the shared markers are copied into the guide's Questions section by `docs/generate_limits.py`; links into the guide are written as `PolicyWitness.md#anchor` and become internal links in the copy.

<!-- BEGIN SHARED QUESTIONS -->

## When should I use PolicyWitness?

Use PolicyWitness when you need to determine whether an observed result follows from the sandbox policy under test or from some unrelated part of the execution environment.

## Who needs to use PolicyWitness?

Almost no one. Folks authoring SBPL profiles can call `sandbox_check` and `sandbox-exec` directly and Apple's entitlements model plus their app's actual runtime behavior cover practical sandbox questions. A small wrapper script around `sandbox_check` plus `sandbox-exec` can obtain a prediction and an attempt result in the common case. 

## Can PolicyWitness attribute a failed attempt to sandbox denial?

No. PolicyWitness records the failed attempt and the evidence available around it, but a failure alone does not establish that the sandbox caused it.

## What does PolicyWitness's attempt channel record?

The sandboxed worker supports four built-in attempt kinds: `file` (open/read/write/create/unlink/access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Completed results carry operation-specific status and error observations in a uniform per-step envelope; those status fields are PolicyWitness attempt status, not raw syscall returns. Result provenance and missing reasons distinguish completed observations from missing or incomplete reports.

## Can PolicyWitness probe operations it doesn't natively support?

Yes — via the `exec` attempt kind plus the named-augment interface. Callers ship their own helper binary and, where needed, opt into `exec_baseline`, a shipped SBPL fragment supplying baseline allows for spawning under `(deny default)`. PolicyWitness records spawn observations, child disposition and bounded stdout/stderr in the same envelope shape as the built-in attempt kinds. The helper must supply evidence about its internal operation; PW does not turn that evidence into a record for that operation, and a successful spawn can coexist with a failed exec result. The per-operation authoring burden lives with the caller — PolicyWitness intentionally doesn't carry an atlas of every sandboxable operation, and the augment system is the documented extension point for callers who need to test surfaces (network, iokit, ipc, signals, user_preference, etc.) PolicyWitness has no built-in attempt kind for.

## What does a comparison record contain?

Each step's `comparison` has six fields: what the attempt channel observed (`observation`: `succeeded`, `permission_failure`, `other_failure` or `unavailable`) and the raw fields that observation rests on (`observation_basis`); whether the query named the same operation as the attempt (`operation_relation`) and the same submitted target (`target_relation`); whether an eligible query is known to precede the attempt batch (`order`); and a short list of `limitations` that name a planning exclusion or the attempt's lifecycle state. The query's own answer stays in `sandbox_check`. See the guide's [reading rules](PolicyWitness.md#reading-a-comparison-record).

## Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?

No. The envelope carries no evidence that a target's state was stable between the query and the attempt, or that a path named the same object both times, and a permission-shaped failure does not identify the sandbox as its cause. A deny prediction beside a successful attempt is therefore reported as those two facts with their relations and order, and nothing more. Readers who want an opinion form it from the record and the raw channels, under limits the record states.

## Can PolicyWitness run every profile that `libsandbox` accepts?

No. PolicyWitness has its own limits, documented in [the limits inventory](PolicyWitness.md#limits).

## What versions of SBPL are supported?

PolicyWitness passes the submitted SBPL source to the host's `libsandbox` compiler and supports whatever profile versions that compiler accepts. `(version 1)` is the documented profile version; some Apple-shipped profiles use higher version numbers.

## How do I use imports with PolicyWitness?

PolicyWitness supports imports the same way `sandbox-exec` does — `(import "name.sb")` statements are resolved by libsandbox against the system search path (`/System/Library/Sandbox/Profiles/` first, then `/usr/share/sandbox/`).

## Can PolicyWitness test sandbox-extension behavior?

No. PolicyWitness does not issue, consume, release, or otherwise track sandbox extensions, and it does not model changes in access caused by extension state. Policies containing extension predicates may compile and run, but PolicyWitness does not provide first-class probes or comparison semantics for extension lifecycle behavior.

## Which happens first, the prediction or the attempt?

A `query_first` comparison identifies an eligible native prediction collected before the worker acknowledged host release, which precedes every attempt. Missing or unusable predictions and death before acknowledgement remain `unestablished`. Query collection closes even when validator cleanup is unconfirmed; a surviving validator cannot add later records. The interval is not a common state snapshot, and earlier attempts can change what later attempts encounter.

## How do I read the denial log?

As optional, possibly incomplete evidence. The kernel's sandbox log intermittently omits denial lines for any sandboxed process, so a missing record never establishes that an operation was allowed. The validator queries `sandbox_check` with `SANDBOX_CHECK_NO_REPORT`, so a denial record naming the worker PID comes from an attempt, never from a prediction. A candidate association (`sandbox_log_capture.step_denies`) says that a record's PID, operation and path match a submitted attempt; it does not say the attempt produced that record, and it changes no comparison field.

## How long does a run take?

One runner client span plus, by default, one unified-log scan, plus the controller's own startup and output. Your reply records the first two: the runner's work is `data.runner_client.ended_at_unix_ms` minus `started_at_unix_ms`, and the scan is `data.sandbox_log_capture.supervision.elapsed_ms`.

## Can I evaluate specimens in parallel?

Yes and no. Each specimen is evaluated in its own runner and worker processes, but PolicyWitness does not guarantee relative scheduling between concurrent runs or complete denial-log evidence. If an experiment depends on timing or log availability, run the specimens separately. N.B. Runs through one installed [external runner](PolicyWitness.md#external-runners-byoxpc) are serial and queue behind launchd's respawn throttle, which the generated plist sets to one second.

<!-- END SHARED QUESTIONS -->
