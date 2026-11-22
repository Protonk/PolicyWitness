# Guide studies

What would a reader need to observe in their own application for this lesson to hold? A study can supply a worked example, identify a limit on what it shows, or leave a question for another run.

## When should I keep the file for the second run?

### Teaching finding 1

**What starts fresh in a PW run is the process.** Suppose you want to know whether two profiles let a worker create a file. Give each worker a `create_fresh` followed by a `read_fresh` on the same path. Starting with the name absent, profile A's worker created the file and read back `x`. Profile B's create returned `EEXIST`, and its read returned the `x` the first worker had written. We moved the file aside and ran the profiles in reverse order. B created the file and A got `EEXIST`. To test each profile's ability to create a missing file, move the first trial's file aside before starting the second invocation. To test whether a second worker can read what the first one wrote, leave it there.

**Evidence.** A used `(allow default)`. B added a rule denying unlink. The four direct runs reported four distinct worker PIDs. Within each pair, both workers' reads and the caller's intervening file sample recorded the same device, inode and byte. The selected observations and envelope timestamps from signed build 1634 on macOS 25G241 are checked in at `work/evidence/file-repeats/observations.json` under `create_and_read`. The full envelopes were collected in temporary storage. [Worker lifetime](../../runner/README.md#run-lifecycle) · [File operations](../../docs/contract/12-probes.surface.md)

## Which pathname answers the application's question?

### Scope finding 3

**Following a link in the app's spelling is checked only by the attempt.** An app opens a file as `/tmp/…` or through a symlink, and the author asks whether a rewritten profile still lets it. `sandbox_check` answers for the object the spelling resolves to: the canonical path, the `/tmp` spelling and paths through a link to the file or to its directory all got the same prediction. The open also has to read each link it follows. Under `(deny default)` with reads allowed in the target's directory, reads through `/tmp` and through the directory link were predicted `allow` and failed with EPERM. Allowing `file-read-metadata` on `/tmp` let the `/tmp` read succeed, and `system.sb` grants exactly that for `/etc`, `/tmp` and `/var`. Two profiles that differ only in such a rule, or only by importing `system.sb`, agree in every query and differ in the attempt. A query-only comparison, a companion attempt on another file, or the canonical spelling in place of the app's answers how each profile treats the resolved object, not whether the app's open succeeds.

For a worked example, compare opening the same file through the app's spelling and through its resolved spelling. Which result helps the reader predict whether their app can open the document the way it actually does? The paired policy runs and the native controls are described under scope finding 3 in `work/scope/README.md`. [Original profile run](work/scope/evidence/policy-comparison/pw/dorig.result.json) · [Rewritten profile run](work/scope/evidence/policy-comparison/pw/drewr.result.json)

## What would show that a preference survived the process that wrote it?

### Scope finding 7

**Which process writes the settings file can be part of the question.** An app saves its settings with `CFPreferencesSetValue` and `CFPreferencesSynchronize`, and the author asks whether a candidate profile lets it save. The app can answer under `sandbox-exec` with what synchronize returned and the plist checked on disk. PW cannot, because its worker cannot call the preferences API, and a PW write to the plist covers only one route. For a domain named by a file path, the app's own process wrote the plist: with writes to its directory denied, synchronize failed and the kernel attributed the denial to the app, while denying every `cfprefsd` lookup left the save working. For a named domain, a read succeeded when either the daemon or the file was reachable and failed only when both were denied. A value read back in the same process was the new one even when the save failed, so the file on disk is the observation. Other work a daemon does on an app's behalf may have the same shape; only preferences were tried.

The path-domain experiment compared the writer's readback with the plist. The named-domain experiment examined reads. A question for a further study is what a second process could observe after a writer to a named domain exits. The run conditions and limits are recorded under scope finding 7 in `work/scope/README.md`. [Path-domain writer](work/scope/evidence/settings/setpref.c) · [Named-domain reader](work/scope/evidence/settings/rd.c)

## What can a saved run tell me about a failed open?

Read just step `s0` in the original-policy, file-present envelope. The worker published `open_failed` with errno 1. The comparison gives `permission_errno` as its basis, and the validator answered `deny` for the submitted path and operation. This establishes the failed worker open. Attributing it to the policy takes a control. [First envelope](work/scope/evidence/policy-comparison/pw/orig_holepres.result.json)

Now read `s0` with the added allow rule. The open succeeded. The open of the neighboring file in `s1` still failed with errno 1 in both runs. Repeat the comparison with the named file absent and both `s0` opens fail with errno 2. The fixture account identifies the name the caller varied between trials. For an app reporting a similar symptom, the next useful evidence would be the pathname that app supplied and the result of its call. [Added rule, file present](work/scope/evidence/policy-comparison/pw/hole_holepres.result.json) · [Original policy, file absent](work/scope/evidence/policy-comparison/pw/orig_holeabs.result.json) · [Added rule, file absent](work/scope/evidence/policy-comparison/pw/hole_holeabs.result.json) · [Fixture account](work/scope/README.md#2-absent-names)

**Where the reading stalls.** “Why is there no prediction?” already has an answer in `comparison.limitations` and `sandbox_check.error`. “Which error did the host's path lookup return at planning time?” has none. The planner keeps whether `realpath` resolved the name. The recorded `ENOENT` came from the worker's later open. Would retaining the host's own errno distinguish two cases a reader would handle differently? Try a missing component and an intermediate component that is a regular file. Check whether the worker's evidence already makes the distinction the reader needs before proposing another field. [Query planner](../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift) · [Path lookup](../../runner/Sources/PWRunnerCore/PathUtils.swift)
