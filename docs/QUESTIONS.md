# PolicyWitness — FAQ

The following questions are answered briefly with exhaustive detail remanded to the [user guide](../PolicyWitness.md).

## When should I use PolicyWitness?

PolicyWitness compares `sandbox_check` predictions with the observed results of operations attempted under a sandbox policy. Use it when developing a policy or investigating disagreement for particular operations, filters and targets. A failed attempt does not by itself establish sandbox denial, and a reported disagreement does not by itself identify a libsandbox bug. You can also use it as a regression harness across macOS revisions, keeping the versions and observation conditions attached to the results.

## Who needs to use PolicyWitness?

Almost no one. Folks authoring SBPL profiles can call `sandbox_check` and `sandbox-exec` directly and Apple's entitlements model plus their app's actual runtime behavior cover practical sandbox questions. A small wrapper script around `sandbox_check` plus `sandbox-exec` can obtain a prediction and an attempt result in the common case. PolicyWitness also provides structured failure reporting across the worker, validator and transport boundaries.

## Why might I want to use PolicyWitness even if I don't need to?

Ergonomics. `sandbox_check` answers for a live PID, so asking it about a draft policy means standing up a process under that policy, querying it before it exits, and getting the answer out — work PolicyWitness does behind one JSON-in, JSON-out call.

## If a wrapper around `sandbox_check` and `sandbox-exec` can obtain a prediction and an attempt result, why does PolicyWitness have a controller, a runner, and a worker?

The separation keeps reporting outside the policy being tested, so a worker failure need not prevent a useful report. PolicyWitness can preserve that failure alongside the available predictions and attempt results, and describe what is missing. Its summaries make limited claims from those observations; failure alone is not treated as proof that the sandbox denied an operation.

## Beyond observing drift, what does PolicyWitness's attempt channel record?

The sandboxed worker supports four built-in attempt kinds: `file` (open/read/write/create/unlink/access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Completed results carry operation-specific status and error observations in a uniform per-step envelope; those status fields are not necessarily raw syscall returns. Result provenance and missing reasons distinguish completed observations from missing or incomplete reports. A missing result does not establish that the operation never started.

## Can PolicyWitness probe operations it doesn't natively support?

Yes — via the `exec` attempt kind plus the named-augment interface. Callers ship their own helper binary and, where needed, opt into `exec_baseline`, a shipped SBPL fragment supplying baseline allows for spawning under `(deny default)`. PolicyWitness records spawn observations, child disposition and bounded stdout/stderr in the same envelope shape as the built-in attempt kinds. The helper must supply evidence about its internal operation; PW does not automatically turn that evidence into a comparison for that operation. Successful spawning can coexist with a failed exec result. The per-operation authoring burden lives with the caller — PolicyWitness source intentionally doesn't carry an atlas of every sandboxable operation, and the augment system is the documented extension point for callers who need to test surfaces (network, iokit, ipc, signals, user_preference, etc.) PolicyWitness has no built-in attempt kind for.

## How does PolicyWitness handle uncertainty in its verdicts?

PolicyWitness keeps the prediction (`sandbox_check`) and attempt observations (`attempt`) separate from the comparison it derives. In response schema 7, `comparison` records the conclusion, its operation and target scope, and known limitations. `drift` is a compact summary: `false` for agreement, `true` for disagreement, and `null` for either directional consistency or an unavailable comparison.

For example, a deny prediction paired with a matching file-open attempt that fails with EPERM yields directional consistency and `drift: null`. The failure is consistent with the prediction, but does not establish that the sandbox caused it. Reading `comparison` lets a consumer distinguish that limited conclusion from a missing prediction or attempt result, while retaining the observations behind it.

## What versions of SBPL are supported?

`(version 1)` is the officially supported SBPL profile prologue, but a small fraction of the profiles Apple ships under `/System/Library/Sandbox/Profiles/` open with `(version 2)` or `(version 3)` — the higher numbers are not documented in any public reference. PolicyWitness compiles whatever the host's `sandbox_compile_string` accepts, so all three work.

## How do I use imports with PolicyWitness?

PolicyWitness supports imports the same way `sandbox-exec` does — `(import "name.sb")` statements are resolved by libsandbox against the system search path (`/System/Library/Sandbox/Profiles/` first, then `/usr/share/sandbox/`).

## Is evidence from runs comparable across macOS versions?

Yes, as observations tied to each macOS version: comparing them is useful for regression analysis. That does not establish equivalent behavior across releases, because libsandbox, the imported profiles and enforcement can differ. Keep the macOS version, policy/imports, probe inputs and response schema with the evidence. In particular, response 7's meaning of `drift` must not be applied to older stored replies.

## Can PolicyWitness test sandbox-extension behavior?

No. PolicyWitness does not issue, consume, release, or otherwise track sandbox extensions, and it does not model changes in access caused by extension state. Policies containing extension predicates may compile and run, but PolicyWitness does not provide first-class probes or comparison semantics for extension lifecycle behavior.
