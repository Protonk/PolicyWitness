# Requirements and expectations

Which instructions could disappear if PolicyWitness were simpler? Start with a finding below and the decision its user has to make. Look for work PW could remove, information it already has, or an experiment a change would make harder to express. The [user guide plan](../../docs/guide/USER-GUIDE-PLAN.md#sources-and-constraints) locates the companion records, including the numbered responsibilities and their test consequences.

## What must we teach a user?

A user learning the following may never see `QUESTIONS.md`.

### Finding a lesson

Start with a sentence someone might say after reading a result. Find two steps or runs where the observation they noticed is the same. Would they make the same decision in both? Look for the fact that lets them decide, and ask where they could learn it. It might be in the next field, in an observation someone made during the run, or beyond what anyone recorded. Write the lesson so the reader can use it on a third case.

### Numbered findings

Teaching finding 1, on whether to keep a file for a second run, is in `GUIDE-STUDIES.md`. Teaching findings 2 and 3, on phase timing and a second reader as a control, are in `EXPERIMENTS-TO-PRESERVE.md`.

4. **Repeating a step gives you a result for the new attempt.** Suppose PW returns `runner_failed` halfway through a plan. The first step completed its `open_read`. The second, a create, says `started_without_result`. The third says `not_reached`. The host reaped the worker. Looking in the initially empty directory reveals a regular file at the create target. If you needed the file, it is already there. If you needed the return value of the call that created it, the worker died before publishing it. The synthetic `rc: -1` in that row supplies no native return value.

   Even a successful repeat leaves that first result unknown. In a timed-out run whose worker later created the file, we waited for its exit and resubmitted the identical specimen. The second worker reported `ok` for `create`. An open descriptor held across the repeat and an independent check of the path showed that the original file was still there. Plain `create` can open an existing file successfully. A retry starts at the first step, so earlier effects can recur. [File operations](../../docs/contract/12-probes.surface.md) · [Step result assembly](../../runner/Sources/PWRunnerCore/CWorkerStepResults.swift)

   **Evidence.** In `witness_contract/worker_killed_before_slot_publication`, the fixture stopped the worker after the native create returned. The checker inspected the file before decoding the envelope. The three step summaries above, reap and signal 9 are from run `20261121T201959Z_113ddef9`, under the gitignored `tests/out/runs/guide-retry-20261121/` and available only in this checkout. The repeat on the existing file is the separate `create_only` control in `work/evidence/retry/observations.json`. [Publication control](../../tests/suites/witness_contract/check_killed_before_publication.py)

5. **Read the question the validator answered alongside the operation the worker attempted.** Two steps each showed an `allow` prediction beside a failed fresh read of file B. Was either prediction about reading B's contents? One question asked about reading file A's contents. The other asked about reading file B's metadata. The worker tried to open B for data in both steps and got `EPERM` both times. To ask about the read you meant, change the query's path in the first case and its operation in the second. The step that asked about `file-read-data` on B received `deny`.

   **Evidence.** In the `crossed` capture of `witness_contract/test_input`, `read-ab` reported `matched` for the operation and `different_submitted` for the target. `metadata-b` reported `different` and `same_submitted`. `read-bb` reported `matched` and `same_submitted`. Run `20261121T201024Z_db418ae6` is available only in this checkout under the gitignored `tests/out/runs/guide-read-handoff-20261121/`. [Controlled reads](../../tests/suites/witness_contract/README.md#controlled-read-input) · [Comparison fields](../../docs/contract/31-steps.surface.md)

## What work can the user trust PW to do?

A user investigating a sandbox policy needs evidence they can use whichever way the experiment turns out. Without PW, what would they have to arrange for the experiment to answer their question, and what would they have to check before drawing a conclusion? Even if PW performs every operation in its published contract exactly as described, naming a computation can still leave the reader wondering which part of that work it takes off their hands. PW can do that part for them even when the result overturns their expectation.

An entry earns its place when a reader can cross one duty off their own procedure. State what they can omit, under what conditions they can rely on PW for it, and where their own effort or judgment resumes. If a reader could reasonably entrust one part to PW while retaining the next, draw the boundary there. A general description of PW gives the reader too little detail to make that choice.

Follow one ordinary use from the user guide into the shipped implementation. Note what the caller prepares, trace what the app takes over, and identify what the caller still has to establish after PW returns. Read the corresponding case in `tests/suites/` from fixture setup through its assertions. Ask who supplied the facts each assertion relies on. A passing test can credit the app with work the harness actually did. Where that division is unclear, try the same task locally with the shipped app and compare what it supplies with what the harness supplied. *If PW ceased doing this particular work, what would the user have to add to accomplish the same task?*

### Numbered findings

1. **Coordinate a query with the worker it concerns.** To obtain a prediction before an action, the user would otherwise have to keep the sandboxed process alive, identify it to a separate caller, and hold it until the query was collected. For an eligible query that PW reports as `query_first`, the user can leave that coordination to PW.

2. **Get an observation out without relaxing the policy to report it.** For a built-in attempt under `(deny default)`, the user can omit writing a reporting helper or granting the worker permission to write a results file. PW prepares shared memory before the policy takes effect, and its host collects what the worker publishes there. If the worker stops before publishing, the effect of the attempt may still need an independent check.

3. **Keep a later edit to the specimen from changing the request PW submits.** For a single invocation, the user can skip staging a private copy solely to prevent a later reopen. Once `policy-witness run` has parsed the JSON, the controller resolves and submits the request it already holds. This covers the SBPL text and parameter values in the JSON. A file named by an SBPL import is still a separate compiler input. If its contents matter, keep that file stable through compilation. A controller test replaces the specimen on disk, inspects the request handed to the client callback, and checks that the fallback compiler callback receives the same bytes. For a later invocation, outside-PW finding 2 gives a tested recipe for saving the request and the files it uses. [Held request and independent import reads](../../docs/contract/42-dossier.surface.md) · [File-replacement controls](../../controller/src/run_flow.rs)

4. **Study a bare `(deny default)` without adding what a program needs to start.** With `sandbox-exec`, a bare `(deny default)` stops the probe program before it runs. `/bin/cat` fails at `execvp`, and with exec allowed it still aborts at startup until the profile also allows reading `/`. Once started, it could read its file but not write to its standard output. Whatever the program needs to start and to report becomes part of the policy under study, and a difference between two profiles that lies in those rules, such as whether `/` can be read, cannot be observed this way. For a built-in attempt, the user can leave those rules out. PW's worker is already running when it applies the policy, and afterwards it makes the requested call directly. An `exec` attempt gives this up, because the helper has to start under the policy.

Trust findings 5 and 6, on token delivery and querying a newly created path, are in `EXPERIMENTS-TO-PRESERVE.md`.

7. **Repair a refused specimen without undoing its first step.** PW admits the whole request before it starts a worker or validator. A confirmed `bad_request` lets the user fix the reported defect and submit again without checking for effects from earlier steps. In an actor specimen the first step would create a file and the second had an empty ID. The client recorded `invoked`, the host refused the second step with `empty_step_id`, and the caller found the file absent. Giving the second step a nonempty ID made the run finish and the file appear. A refusal names one defect at a time. An admitted specimen can still encounter a missing directory and report a failed attempt in a `finished` run. If the client loses the host reply, responsibility finding 32 in `USER-RESPONSIBILITIES-AND-TESTS.md` gives the grounds for a retry.

   **Evidence.** The CLI refusal and its one-field repair are `actor-empty-step-cli` and `actor-nonempty-step-cli` in `runner_outcome_bad_request/accepted_input_contract`. Both recorded `invoked`. Only the repaired specimen launched an actor. Both file checks preceded envelope decoding in run `20261121T201959Z_113ddef9` (checkout-local, as in teaching finding 4). [Admission and repair controls](../../tests/suites/runner_outcome_bad_request/contract.py)

8. **Identify the object an attempt reached from the descriptor it opened.** A `stat` from the shell after a run describes whatever the path names by then. To learn which object a read or write reached, the user would otherwise write a helper that calls `fstat` on its own descriptor. For `read_fresh`, `write_fresh` and `create_fresh`, PW's worker does this before closing the descriptor and reports device and inode. One worker can then tell a replaced file from the original across phases: a read before an unlink and a read after recreating the same name reported different inodes. Comparing identities is still the user's work. Different numbers show different objects, but equal numbers don't rule out reuse. `open_read` and `create` report a path, not an identity.

9. **Stop a hung helper at its deadline, when the policy lets the worker signal it.** A helper that never exits would otherwise need the user's own timer, process group, kill and bounded wait. PW's worker gives each `exec` child 10 seconds, then sends SIGKILL to its process group and reaps it. Under `(allow default)`, the reply showed the signal succeeding and the child reaped with signal 9. The worker sends that signal from inside the sandbox, so the policy under study can refuse it. Under `(deny default)` with `exec_baseline`, the signal failed with EPERM and the reply recorded `group_request_failed`. The helper and its child were still running after `policy-witness` returned, reparented to launchd. When the reply records a failed cleanup, finding and stopping those processes is the user's job, as it is for any descendant that leaves the group.

## What must a user arrange outside of PW?

Sketch an experiment as a recipe a colleague could carry out at a terminal. Put each PW invocation on its own line and fill in the work around it. Which line would the colleague have to supply to make the experiment answer their question? Give that line enough detail to try by hand or turn into a script. Include any tradeoff that would change whether the colleague would use the recipe.

### Numbered findings

1. **Choose the second path after inspecting the first read.** One specimen can schedule two reads in successive phases of the same worker when both paths are known at submission. To let the first result determine the second path, the caller makes that choice between runs.

   ```sh
   policy-witness run first.json > first-result.json
   # Inspect the first read in first-result.json, choose the next path, and write second.json.
   policy-witness run second.json > second-result.json
   ```

   The person at the terminal can make that choice, or a script can apply their decision rule. The chosen path carries over in the second specimen. Its read takes place in a fresh worker, even if both specimens use the same policy.

2. **Give a colleague the inputs needed to repeat a read.** A colleague with the ordinary run envelope could see which path the worker read and check a candidate policy's source hash. The envelope carried neither the SBPL text nor the parameter map. In this experiment `read.json` supplied a directory as parameter `ROOT`. A local file named by an absolute SBPL import allowed reading `ROOT/document`. The question was whether the worker could read the known text in `left/document`.

   Run these commands from the private fixture directory containing those files. The colleague can use the same build and restore the fixture at its original paths.

   ```sh
   mkdir saved
   cp read.json local.sb left/document saved/
   policy-witness run saved/read.json > saved/first.json

   # Later, restore the two files that the saved request refers to.
   cp saved/local.sb local.sb
   cp saved/document left/document
   policy-witness run saved/read.json > saved/replay.json
   ```

   Changing only `ROOT` in the submitted JSON made the open fail with `EPERM` while the source and import-closure hashes stayed equal to the first run's. Restoring the request and changing only the imported rule also yielded `EPERM`. This time the closure hash changed. With the original request and rule back, changing only the document gave the worker `edition two\n`. Restoring its bytes gave it `edition one\n` again. We also ran the shell recipe with the original document moved aside before replay. The two workers read the same text from different inodes. That handoff reproduced the content observation. An experiment that depended on the original object would need to preserve it. The five controlled runs, the shell replay and the caller's file samples are under `repeat_a_read` in `work/evidence/file-repeats/observations.json`. [Policy parameters](../../docs/contract/11-policy.surface.md) · [Dossier hashes](../../docs/contract/42-dossier.surface.md)

3. **Observe a temporary file at the point where it matters.** A colleague wants to know whether the first run ever created a file before they repeat it. In three private directories, the target was absent at CLI return and the timeout envelope said `invoked`. We held the identified worker before its create, let it proceed after the timeout, and inspected the name again while the worker waited at its next step. The last inspection followed an independently registered worker exit event. The worker was the only writer to the target in each experiment.

   | Specimen and setup | At CLI return | After the create step | After worker exit |
   | --- | --- | --- | --- |
   | Create, parent directory present | Absent | Empty file | Same file |
   | Create, parent directory missing | Absent | Absent | Absent |
   | Create, then unlink | Absent | Empty file | Absent |

   If the aim is to leave a file at that path, the first row is already done. In the second row we supplied the missing parent and the retry created the file. If the aim is to create the file only once, the last two exit inspections look alike. Only the intermediate inspection caught the file that the third worker removed. Without an observation while it existed, those two endpoint checks leave its history unresolved.

   To make that inspection by hand in a new experiment, use a private directory and an allowing policy. Have the worker `create` the target, use `read_fresh` on a named pipe, then `unlink` the target. Set `target` and `gate` in both terminals to the absolute paths in the specimen. Start the run in the first terminal.

   ```sh
   mkfifo "$gate"
   policy-witness run specimen.json > result.json
   ```

   In the second terminal, open the writing end of the pipe. When the open returns, the worker has reached the pipe. Inspect the file while the reader waits, then send the byte.

   ```sh
   exec 3>"$gate"
   stat -f 'device=%d inode=%i size=%z' "$target"
   printf x >&3
   exec 3>&-
   ```

   The pause changes the timing and requires permission to open and read the pipe. Use it when the question tolerates both. Inspect within the worker's wait allowance. If it never reaches the pipe, the writer's open can block. The scripted timeout controls used a nonblocking open with a deadline. The signed runs, caller inspections, exit observations and retries are recorded in `work/evidence/retry/observations.json`. [Generation-qualified exit watch](../../tests/lib/footprint_observer.py)

## How much the user's real problem has to come into the specimen?

Start with a question someone is already trying to answer in their app. What observation would settle it? If the app or a short script can supply that observation, give the guide drafter that route. A reason to bring the problem into PW should be just as concrete. Say what the user gains by moving part of the experiment into a worker. Then try leaving out one detail at a time. The useful finding is the point where the smaller experiment starts answering a different question.

### Numbered findings

1. **How the app got its file descriptor can be part of the question.** An editor opens a document, applies a profile, then tries to read a word through the descriptor it kept open. If the author wants to know whether the editor can still read that word, the editor can perform the read and report it. Giving PW the same profile and path for a `read_fresh` attempt introduces a new open after the policy takes effect. That makes a useful companion experiment if the author also wants to know whether a worker under that profile can open the path afresh and read the word. The document parser can stay out of both experiments. The earlier open matters to the first one. [PW’s file operations](../../docs/contract/12-probes.surface.md)

   **Further instance.** An app reads a document the user chose, then stops accessing it. A native control in one process found a fresh open of the file denied after the extension was released, while a descriptor opened before release still read it. PW's `read_fresh` reports only the first, because no PW attempt keeps a descriptor across phases. Whether the app can still read what it already opened needs the app's own descriptor. The PW run answers whether a new open of the path still succeeds.

2. **A name that does not exist can't show how a profile treats it.** A rewritten profile is meant to treat a file the app creates later the way the original does. Each profile's answer for an object at that name settles it, and a short wrapper is enough: create the file outside the sandbox, call `sandbox_check` against a process started under each profile, and open the name from a process under each. Leaving out the file changes the question. For a path that did not exist, `sandbox_check` returned `rc 1, errno 0`, the value of a deny, under both profiles, under `(allow default)` and for an unsandboxed process. The open returned `ENOENT` whether or not the profile allowed the name. Two profiles that differed only at that name looked the same in both channels until the file existed, and then differed in both. PW reports such a query as `prediction_unavailable` instead of passing that value on; it does not recover the answer. When a rule tests the object itself, as `vnode-type` does, the kind of object created decides which part of the rule is tested.

3. **Can PW show when the spelling of a path matters to a comparison?** In the symlink experiment, the query returned the same prediction for two spellings, while the worker could open the canonical path and got `EPERM` through the directory link. PW records the resolved spelling in `path_diagnostics` but adds no comparison limitation. Could PW use the two recorded spellings to help a reader choose a comparison run without assigning a cause to the failed open? The application experiment and its controls are under scope finding 3 in `GUIDE-STUDIES.md`. [Path observations and comparison](work/scope/evidence/policy-comparison/pw/dorig.result.json)

4. **Compiling both profiles can settle every path at once, but only when the bytes match.** To ask whether a rewritten profile treats every path as the original does, the author can compile both with libsandbox and compare the bytes, without choosing any path. Rewrites that only changed whitespace, a trailing slash, rule order or a redundant rule, or that wrote a subpath as a regex, compiled to the original's bytes. PW's opt-in compiled-object receipt reported the same hash for the original and the regex rewrite. When the bytes differ, the compile says nothing about any one path: a profile with an added carve-out compiled differently and agreed with the original on every existing file. A compile also leaves out the process that holds the profile. A rule conditioned on a signing identifier answers for whichever process is checked. In PW, a rule naming `pw-probe-runner` denied the worker's read and a rule naming another program did not. A specimen whose profile tests the process answers for PW's worker, not for the app.

5. **Whether the helper starts is part of the question.** An app launches a small helper that reads its config file, and the author asks whether a candidate profile lets it. The helper can answer under `sandbox-exec` through its exit status and stderr. Giving PW the config path for a `read_fresh` attempt leaves out the helper's startup. Under a profile that allowed only reading the config, `read_fresh` succeeded, while the helper itself, with exec also allowed, aborted at startup with SIGABRT. An `exec` attempt keeps the startup in the experiment and records the spawn, the child's exit and its output separately. How the helper is launched matters too. `sandbox-exec` replaces itself with the helper, while PW's sandboxed worker spawns it as a child, which also needed `process-fork` and a read of `/dev/null`; an app that spawns its helper would presumably need them as well. The `exec_baseline` augment gets the helper started by allowing every read, so with it the experiment answers whether the helper starts, not whether it may read the config.

6. **Connecting by name is a different experiment from connecting to an address.** An app connects to a local service by host name, and the author asks whether a candidate profile allows it. A small client under `sandbox-exec` settles this, and PW adds little: it has no network attempt, so the client runs as an `exec` helper, and no `sandbox_check` filter names an address. A client that connects to a literal address leaves out the name lookup. Resolving `localhost` read `/etc/hosts`. With reads under `/private/etc` denied, the lookup failed before any connect, while a connect to `127.0.0.1` under the same profile succeeded. Under a narrow profile the lookup also needed `file-read-metadata`. Serving is a separate question again: binding needed `network-bind` and listening needed `network-inbound`, neither of which the outbound rule supplied. A refused connection to an allowed port returned `ECONNREFUSED`, and a port outside the rule returned EPERM.

Scope finding 7, on which process writes a preference and how to observe the save, is in `GUIDE-STUDIES.md`.

8. **The extension class and the profile's rule for it are part of the question.** A sandboxed app reads a document the user chose in an open panel. The app is the route for whether that read works, but the system chooses the extension class and issues the token, so the app cannot try another class or rule. PW can, with an unapplied actor issuing in place of the system. A read-write token did not satisfy a profile whose rule named only the read class, and a read token did not satisfy one that named only the read-write class. A token for another file did not cover the target, and a profile with no extension rule denied the read after a successful consume. A token for a directory covered a file inside it. A specimen that changes the class or drops the rule therefore answers a different question from the app's. What the system issues for a real selection stays outside the specimen.

9. **Keep the part of the file the app has to reach.** A text importer checks that its last record ends in a newline. If the question is whether the importer accepts a particular document, give it the document and observe its answer. If the question is whether a sandboxed reader can reach the terminator, a smaller probe can report the final byte. Under `(allow default)`, two 65-byte versions of a file had the same first 64 bytes. Each PW run made two `read_fresh` attempts. Both opened the file at the beginning and returned the same 64 bytes. The next step spawned `/usr/bin/tail -c 1` on the same file. Its one byte of stdout was a newline in one run and `!` in the other. A built-in read can answer a question about a short header. Repeating it cannot advance to a footer. The helper has to be able to start under the policy for its answer to be available.

   **Evidence.** The direct runs are recorded under `last_byte` in `work/evidence/file-repeats/observations.json`. The registered `witness_contract/test_input` case also removed byte 65 altogether. The worker returned identical `fresh_read` records for a file ending in `d`, the same file ending in `e`, and the file cut to 64 bytes. The harness's full-file samples distinguished all three. Run `20261121T201024Z_db418ae6` passed against build 1634. Its captures are under the gitignored `tests/out/runs/guide-read-handoff-20261121/`, available only in this checkout. [Worker read](../../controller/tools/pw_probe_runner/pw_probe_runner.c) · [Controlled read and independent samples](../../tests/suites/witness_contract/README.md#controlled-read-input)

## What can a colleague establish about a run they did not see?

Take one claim someone would put in a bug report and give the reader only the saved PW envelope. Which words can they defend? Ask them to name the field, who observed it and when. Then read the case in `tests/suites/` to find what the fixture knew or did outside PW. Hand over one observation at a time, tied to the same run and target. Which words can the reader add now? Try changing who performed an action while keeping the visible result the same. Record what distinguishes the two histories and which question remains open even with the operator present.

### Numbered findings

1. **Show how you know who created the file.** We tested the claim “my worker created an empty file before it died” against the interrupted create in teaching finding 4. Each addition to the handoff supported a different part of that sentence.

   | Evidence available to the colleague | What they can say about the original run |
   | --- | --- |
   | PW envelope alone | The worker reached the create step and the host reaped it with signal 9. The target failed to resolve at query planning. After orchestration the host resolved that same pathname (`realpath_resolved` appears in `same_as_input`). The create's native result went unpublished. |
   | Add the caller's `lstat` before submission | The target name was absent when the caller checked. This supplies the initial state that the failed planning lookup left uncertain. |
   | Add the caller's `lstat` after CLI return | An empty regular file was present at that name. The two samples establish the change. Who introduced the file is still open. |
   | Add the fixture's account of who acted | In this private fixture the worker's create was the only operation that could have introduced the file during the interval. That supports naming the worker as creator. Even the operator has no recorded numeric return from its `open`. |

   We checked the attribution with three workers given identical specimen bytes. Each paused on a pipe after query collection and stopped before publishing its create result. In A the caller created an empty file with an exclusive open before releasing the worker. In B the caller left the name absent for the worker. Both ended with an empty regular file. In A the caller held its descriptor across the worker's attempt and its device and inode still matched the final file. In C the caller made a directory at the same name. **All three envelopes contained identical `attempt` records for the create**, including the host's later path resolution. For a colleague asking “what was at that name afterward?”, the caller's final sample distinguishes a zero-byte regular file from the directory. For “did your worker create it?”, the caller's action changes the answer between A and B.

   **Evidence.** The original `witness_contract/worker_killed_before_slot_publication` envelope and `observations.json` belong to run `20261121T201959Z_113ddef9` in the gitignored `tests/out/runs/guide-retry-20261121/`, available only in this checkout. The three direct controls from build 1634 are checked in under `work/evidence/creator-handoff/`. Read `A.json`, `B.json` or `C.json` first, then the corresponding entry in `samples.json`, then `setup.json`. [Original fixture and sampling order](../../tests/suites/witness_contract/check_killed_before_publication.py) · [Host path observations](../../docs/contract/31-steps.surface.md) · [Worker create](../../controller/tools/pw_probe_runner/pw_probe_runner.c)

2. **The refusal can lose the fact that makes it a bug.** Did my script omit the specimen, or did PW discard the path I supplied? The fixes are different. On build 1634, `run` and `run -- example.json` each exited 2 with empty stderr and reported `missing <request.json>`. We compared the entire decoded envelopes. Removing only `generated_at_unix_ms` made them identical. Both establish that PW had no request path and invoked no runner client. Giving the recipient the specimen or the `help result` card still leaves both explanations open. The reporter's exact invocation distinguishes them. The argument parser had that distinction before it assembled the refusal. [Argument handling](../../controller/src/run_flow.rs) · [CLI refusal cases](../../controller/integration/interface_cases.json)

3. **A passing read under the default policy leaves the original failure open.** Suppose a colleague reads “`allow`, then `EPERM` on `propernames`” and wants to know what the validator allowed. We started from the shipped example's `metadata-propernames-read-connectives` step. In the next two runs we kept its policy, phases, step ID and other actions and changed one field at a time. In the table, both names are under `/usr/share/dict/`. Each row is a new worker, and all four outer outcomes were `finished`.

   | Specimen | Validator's question | Verdict | Worker's fresh read |
   | --- | --- | --- | --- |
   | Shipped `example` | Metadata of `propernames` | `allow` | Read 64 bytes from `connectives` |
   | Change only `attempt.target` to `propernames` | Metadata of `propernames` | `allow` | Open of `propernames` failed with `EPERM` |
   | Then change only `sandbox_check.operation` to `file-read-data` | Data of `propernames` | `deny` | Open of `propernames` failed with `EPERM` |
   | Separately emit `test-input read --target /usr/share/dict/propernames` | Data of `propernames` | `allow` | Read 64 bytes from `propernames` under `(allow default)` |

   The second envelope already contains the answer. In its step, `sandbox_check.operation` is `file-read-metadata`, `attempt.fresh_read.open_errno` is 1, and `comparison` reports `same_submitted` for the target and `different` for the operation. Changing only the query in the third run changed the verdict while the open still failed. That is enough to correct the question in the specimen. Assigning a cause to the failed open would take further evidence. The `help example` card names the attempts and omits their queries. The one-step publisher supplies a new allow-default policy. Its successful read makes a useful control for whether the file can be read under that policy. Substituting it for the failing run loses the very condition the colleague needs to investigate.

   **Evidence for findings 2 and 3.** The attachment contains the direct CLI inputs, envelopes, statuses, streams and help cards from build 1634 (`e7937ecc`) on macOS 25G241. Compare `no-operand.json` with `discarded-operand.json` for the refusal. For the read comparison, the four inputs and their `*-run.json` envelopes are named `example`, `same-file`, `same-file-data` and `read-default` in table order. [Captured controls](work/evidence/report-diagnosis.zip) · [Comparison fields](../../docs/contract/31-steps.surface.md) · [Published read input](../../controller/src/test_inputs/read.json)

4. **Which request goes with this compiled-profile receipt?** Suppose a colleague sends two requests and one captured receipt. For the nonce to distinguish the requests, each needs its own `capture_nonce`. The recipient can then compare the receipt’s `request_nonce` with the value in each saved request. If the caller reused the nonce, either request matches. The host checks the worker’s recorded nonce against the submitted one, but keeps no history of earlier nonces. [Request nonce requirements](../../docs/REQUEST.md#contract-policy-spec-capture_nonce) · [Receipt nonce](../../docs/RESPONSE.md#contract-profile-receipt-request_nonce)

   A controller test supplies a constructed `captured` receipt for a request that asked for no capture. It varies the nonce while keeping the labels valid, and the run still reports `finished`. While PW has both the request and the reply, could it tell the recipient whether capture was requested and whether the nonce matched? [Controller admission control](../../controller/src/run_flow.rs) · [Scope of the label check](../../docs/RESPONSE.md#contract-profile-receipt-labels)
