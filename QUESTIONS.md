# PolicyWitness — FAQ

## When should I use PolicyWitness?

PolicyWitness is designed to observe differences between a system's userland sandbox-prediction API (`sandbox_check`) and that same kernel's sandbox enforcement. Use it when you're developing a sandbox policy and need to know whether `sandbox_check`'s prediction agrees with the kernel's enforcement for the operations and filters your policy uses — i.e., whether the prediction tooling everyone else relies on would mislead you on this policy. You could use it as a regression harness across macOS revisions to detect newly drifting `(operation, filter)` pairs, since Apple doesn't document drift surfaces and they shift between releases.

## When would I not want to use PolicyWitness?

Nearly every case. Most macOS callers neither author SBPL profiles nor call `sandbox_check` directly, so the cross-channel comparison PW exists to produce isn't a question they need answered — Apple's entitlements model and their app's actual runtime behavior cover the practical sandbox question for them. Caveat: `sandbox_check` itself is technically deprecated, so the usual route of querying it for sandbox decisions doesn't have promised behavior — which is the gap PW is built to map.

## How does PolicyWitness compare to `sandbox-exec`?

`sandbox-exec` is the stock macOS CLI that applies a given SBPL profile to itself and then execs a target command, which runs under that profile. It compiles the profile through the same libsandbox machinery PolicyWitness uses, and a small wrapper script around `sandbox_check` plus `sandbox-exec` will get you most of what PolicyWitness produces. PolicyWitness exists because the judgment calls those scripts have to make — distinguishing DAC failures from sandbox failures, knowing which `sandbox_check` predictions are unreliable on the current macOS revision, handling unresolvable paths — are easier to maintain in one shared codebase than to rediscover per team.

## Beyond observing drift, what does PolicyWitness's attempt channel record?

PolicyWitness runs real syscalls inside the sandboxed worker for each probe step via four built-in attempt kinds: `file` (open/read/write/create/unlink/access), `mach_lookup` (`bootstrap_look_up`), `sysctl` (`sysctlbyname` read), and `exec` (`posix_spawn`). Each kind captures forensic detail in a uniform per-step envelope — the kernel's `F_GETPATH`-canonical `observed_path` for file ops; the bootstrap return code that distinguishes sandbox-deny (`kr=1100`) from service-missing (`kr=1102`) for mach lookups; errno bucketing for sysctl; and the full spawn-and-reap shape (child_pid, exit code, termination signal, captured stdout/stderr) for exec. That detail is what a real consumer would observe at runtime against the same policy, recorded once in machine-readable form.

## Can PolicyWitness probe operations it doesn't natively support?

Yes — via the `exec` attempt kind plus the named-augment interface. Callers ship their own helper binary, opt into `exec_baseline` (a shipped SBPL fragment that satisfies `posix_spawn`'s allow-rule prerequisites under `(deny default)`), and probe the operation the helper exercises; PolicyWitness captures the bounded spawn-and-reap frame in the same envelope shape as the built-in attempt kinds. The per-operation authoring burden lives with the caller — PolicyWitness source intentionally doesn't carry an atlas of every sandboxable operation, and the augment system is the documented extension point for callers who need to test surfaces (network, iokit, ipc, signals, user_preference, etc.) PolicyWitness has no built-in attempt kind for.

## How does PolicyWitness handle uncertainty in its verdicts?

PolicyWitness reports uncertainty as a distinct outcome with the reason populated, so a consumer can branch on it explicitly. Each step in a run carries two verdicts the consumer reads: the validator's prediction at `sandbox_check.outcome` and the cross-channel comparison at `drift`. The prediction reports `prediction_unavailable` when the validator wasn't asked (an op+filter pair empirically known to drift, an unknown filter kind, or a path that doesn't resolve on the host) and `unsupported_operation` when libsandbox returned EINVAL on the operation name — both with `error` populated naming the trigger. The drift comparison reports `null` when no comparison is possible — when the prediction is unavailable, when the attempt didn't produce a verdict, or when the attempt's failure is ambiguous between sandbox and DAC (file EPERM/EACCES, where the same errno could be a `chmod 000` rather than a sandbox deny).

## What versions of SBPL are supported?

`(version 1)` is the officially supported SBPL profile prologue, but a small fraction of the profiles Apple ships under `/System/Library/Sandbox/Profiles/` open with `(version 2)` or `(version 3)` — the higher numbers are not documented in any public reference. PolicyWitness compiles whatever the host's `sandbox_compile_string` accepts (the same surface `sandbox-exec` compiles against), so all three work.

## How do I use imports with PolicyWitness?

PolicyWitness supports imports the same way `sandbox-exec` does — `(import "name.sb")` statements are resolved by libsandbox against the system search path (`/System/Library/Sandbox/Profiles/` first, then `/usr/share/sandbox/`). What PolicyWitness adds is preflight-time provenance: every resolved import shows up in the envelope with its absolute path, sha256, size, and mtime, plus a `policy_closure_sha256` field covering the source bytes joined with the sorted set of resolved imports. The closure hash is reproducible iff every imported file is content-identical on the verifying host, so a hash match across two runs is evidence that the bytes that actually compiled were the same.

## Is evidence from runs comparable across macOS versions?

No. The host's libsandbox, the imports closure, and the drift surface all vary by macOS release — `policy_closure_sha256` covers file bytes that change between releases, the prediction-unavailable set was verified against specific builds, and the operations libsandbox accepts shift over time. In practice the vast majority of policy decisions are stable across versions, but PolicyWitness exists for the tiny fraction where they aren't.
