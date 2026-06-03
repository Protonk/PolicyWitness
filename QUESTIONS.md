# PolicyWitness — FAQ

The following questions are answered briefly with exhaustive detail remanded to the [user guide](PolicyWitness.md).

## When should I use PolicyWitness?

PolicyWitness is designed to observe differences between a system's userland sandbox-prediction API (`sandbox_check`) and that same kernel's sandbox enforcement. Use it when you're developing a sandbox policy and need to know whether `sandbox_check`'s prediction agrees with the kernel's enforcement for the operations and filters your policy uses. Alternatively, you could use it as a regression harness across macOS revisions to detect newly drifting `(operation, filter)` pairs, since Apple doesn't document drift surfaces and they shift between releases.

## Who needs to use PolicyWitness?

Almost no one. Folks authoring SBPL profiles can call `sandbox_check` and `sandbox-exec` directly and Apple's entitlements model plus their app's actual runtime behavior cover practical sandbox questions. A small wrapper script around `sandbox_check` plus `sandbox-exec` will get you most of what PolicyWitness produces.

## Why might I want to use PolicyWitness even if I don't need to?

Ergonomics. `sandbox_check` answers for a live PID, so asking it about a draft policy means standing up a process under that policy, querying it before it exits, and getting the answer out — work PolicyWitness does behind one JSON-in, JSON-out call.

## Beyond observing drift, what does PolicyWitness's attempt channel record?

PolicyWitness runs real syscalls inside the sandboxed worker for each probe step via four built-in attempt kinds: `file` (open/read/write/create/unlink/access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Each kind captures forensic detail in a uniform per-step envelope.

## Can PolicyWitness probe operations it doesn't natively support?

Yes — via the `exec` attempt kind plus the named-augment interface. Callers ship their own helper binary, opt into `exec_baseline` (a shipped SBPL fragment that satisfies `posix_spawn`'s allow-rule prerequisites under `(deny default)`), and probe the operation the helper exercises; PolicyWitness captures the bounded spawn-and-reap frame in the same envelope shape as the built-in attempt kinds. The per-operation authoring burden lives with the caller — PolicyWitness source intentionally doesn't carry an atlas of every sandboxable operation, and the augment system is the documented extension point for callers who need to test surfaces (network, iokit, ipc, signals, user_preference, etc.) PolicyWitness has no built-in attempt kind for.

## How does PolicyWitness handle uncertainty in its verdicts?

Each step in a run carries two verdicts the consumer reads: the validator's prediction at `sandbox_check.outcome` and the cross-channel comparison at `drift`. The prediction reports `prediction_unavailable` when the validator wasn't asked (an op+filter pair empirically known to drift, an unknown filter kind, or a path that doesn't resolve on the host) and `unsupported_operation` when libsandbox returned EINVAL on the operation name — both with `error` populated naming the trigger. The drift comparison reports `null` when no comparison is possible: when the prediction is unavailable; when the attempt didn't produce a verdict; or when the attempt's failure cause is ambiguous.

## What versions of SBPL are supported?

`(version 1)` is the officially supported SBPL profile prologue, but a small fraction of the profiles Apple ships under `/System/Library/Sandbox/Profiles/` open with `(version 2)` or `(version 3)` — the higher numbers are not documented in any public reference. PolicyWitness compiles whatever the host's `sandbox_compile_string` accepts, so all three work.

## How do I use imports with PolicyWitness?

PolicyWitness supports imports the same way `sandbox-exec` does — `(import "name.sb")` statements are resolved by libsandbox against the system search path (`/System/Library/Sandbox/Profiles/` first, then `/usr/share/sandbox/`).

## Is evidence from runs comparable across macOS versions?

No. The host's libsandbox, the imports closure, and the drift surface all vary by macOS release. In practice the vast majority of policy decisions are stable across versions, but PolicyWitness exists for the tiny fraction where they aren't.
