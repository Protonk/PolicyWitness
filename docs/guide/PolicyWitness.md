# PolicyWitness

PolicyWitness (PW) runs a small experiment on a macOS sandbox policy. You supply a *specimen* describing the policy, the questions to ask and the operations to attempt. A fresh worker applies the policy. A separate validator can ask about that worker before the worker acts. PW returns their observations in one JSON file. Use it when you can name an operation that would help explain what happened in your application.

## Run your first specimen

On an Apple Silicon Mac running macOS 26, open Terminal. Set `PW` to the executable in your installed app. The following commands use a new directory so that the result and its inputs can travel together.

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
PW_WORK=$(mktemp -d /private/tmp/pw-read.XXXXXX) &&
"$PW" example > "$PW_WORK/example.json" &&
  "$PW" run "$PW_WORK/example.json" > "$PW_WORK/example-result.json"
```

Open the two files side by side. The example carries this build's `contract`. In the first phase, `read-hosts` both queries and opens `/etc/hosts`. The next step asks about *metadata* on `propernames` and reads *data* from `connectives`. In the second phase, the query and the open both concern data on `propernames`. Those differences are intentional. Paths, permissions and the contents of the local dictionary directory affect what you will observe.

For a read with a known answer, supply the file yourself. This example prints the bytes the worker read, in hexadecimal.

```sh
printf 'first\n' > "$PW_WORK/document" &&
  "$PW" test-input read --target "$PW_WORK/document" > "$PW_WORK/read.json" &&
  "$PW" run "$PW_WORK/read.json" > "$PW_WORK/result.json" &&
  /usr/bin/plutil -extract data.runner_result.steps.0.attempt.fresh_read.content_hex raw "$PW_WORK/result.json"
```

For those six bytes the answer is `66697273740a`. To try your own policy, edit `policy.sbpl_source` in a copy of `read.json`, keep the fixture fixed, and save the second result separately. Pass the path directly to `run`. For a filename beginning with a dash, use a spelling such as `./-sample.json`; this build ignores arguments following `--`. When changing the target, edit both the query's `filter.value` and the attempt's `target` if you intend them to refer to the same file. After changing builds, generate a new example and review your specimen against the new build before updating its contract.

## Read a result

| Question | Where to look |
| --- | --- |
| Did PW finish the experiment? | Read `result.normalized_outcome`. A `finished` run can contain a failed open. `policy-witness help result` lists the command outcomes and exit codes. |
| What did the worker do? | Find the `step_id` in `data.runner_result.steps`. Read `attempt.lifecycle`, `result_source`, `outcome` and the operation's own fields. A completed fresh read carries the bytes it sampled. A synthetic `no_completed_result` leaves the call's return unknown. |
| What did the validator answer? | Read that step's `sandbox_check` for the operation, filter, operand and source. Read `comparison` for their relationship to the attempt and the order PW could establish. A `query_first` answer can survive even when the worker never reached the step. |
| Which conclusion can I use? | Read the controller's `data.runner_sandbox_diagnostics` when present. Inspect its integrity findings before relying on a derived conclusion. For an effect outside the process, compare your own observations of the affected file, service or child. |

For a refusal, start with [repairing a specimen](#repairing-a-refused-specimen). For a lost reply, start with [deciding whether to repeat the run](#deciding-whether-to-repeat-a-run). For field definitions, see the [response reference](../RESPONSE.md#read-the-run-from-the-outside-in).

## Responsibilities

- **Describe the run you intend.** Write each field name once per JSON object and give each step a distinct, nonempty ID. To reproduce a run, save the command, specimen and result, along with any imported policies and fixture files it used.
- **Choose what to compare.** For a prediction about a particular read, query the read operation and the pathname you will open. To ask about a file after creating it, put the read in a later phase. PW collects eligible predictions before releasing the worker for that phase.
- **Observe the effect you care about.** To test a helper's write, give it a file with no other writer and compare its bytes before and after. To test an extension grant, compare the recipient's fresh reads before and after consumption. Use a control before attributing a permission error to the policy.
- **Decide when to retry.** Correct a confirmed input refusal and resubmit. After a client timeout, read `data.runner_client.submission`. With `not_invoked`, the client never called for execution. With `invoked` or `unknown`, effects may still occur. If an effect must happen only once, leave the run unresolved until you can establish what happened.

## Repairing a refused specimen

When PW refuses a specimen as `bad_request`, no step has run. PW checks the whole request before it starts a validator, worker or actor. `data.request_failure` names one defect. Fix that field and submit again. If the specimen has another defect, PW refuses it for that one, again without running a step.

The submission PW accepts starts execution from the beginning. Later setup or execution failures can interrupt it. In one actor specimen the first step would create a file and the second had an empty `step_id`. PW refused it, and the file stayed absent. Giving the second step an ID was the only change. The next submission finished, and its first step created the file.

`run` authorizes execution as soon as the specimen passes admission. If effects on the real targets must wait, try a copy whose effectful steps act on disposable fixtures. Review auxiliary inputs too, including any paths passed as helper arguments. A successful trial describes that copy. Restore the intended inputs only when ready to run them. The standalone compiler helper checks policy source; it cannot admit a whole specimen.

## Why couldn't my app open this file?

Start with what failed. In one saved run, step `s0` under `data.runner_result.steps` shows that the worker tried `open_read` on the intended pathname. Its published `attempt.errno` was 1 (`EPERM`). The validator had predicted `deny` for `file-read-data` on that path. From this envelope alone, the cause of the worker's error is still open. [Reading a step result](../RESPONSE.md#predictions-attempts-and-comparison)

The caller tried the same pathname under two Seatbelt policies, first with the file absent, then with it present. The second policy added one rule allowing reads of that file. Each cell describes a separate run.

| Fixture at the start | Original policy | With the added rule |
| --- | --- | --- |
| File absent | Worker open failed with `ENOENT`. No prediction. | Worker open failed with `ENOENT`. No prediction. |
| File present | Worker open failed with `EPERM`. Validator predicted `deny`. | Worker open succeeded. Validator predicted `allow`. |

With the file present, changing the rule changed the worker's ability to open it. With the rule in place, the open still needed the file to exist. If you received only an absent-file run, look at `comparison.limitations`. The entry `query_plan:path_unresolved_at_planning` explains why there was no prediction. That run leaves open what either policy would do once the file exists.

For the application, the next question is which call produced its error. Capture the pathname the app actually supplied and the result of its open. A sandbox denial naming that process, operation and path at the time of the failed call gives independent evidence that Seatbelt intervened. If the app chose an unexpected path, check how it formed that name. An app bug can send it to a path its policy restricts. If the open succeeded and the app later rejected the contents, compare those bytes with a document the app is known to accept.

## Handing a run to someone else

Send the specimen file and the result, with any imported policy and fixture files the run used. The recipient can tell which specimen goes with which result. `data.specimen.request_sha256` is the SHA-256 of the bytes PW read from the specimen file. Running `shasum -a 256` on each specimen file finds the one with the same digest, even after the files were renamed. [Specimen dossier](../RESPONSE.md#contract-dossier-specimen-request_sha256)

The digest identifies the specimen file, not the files it names. In one experiment the specimen set the parameter `ROOT`, and an imported policy file used `ROOT` to allow reading one document. Each row changed one thing from the first run and used a new worker.

| Changed from the first run | `request_sha256` | `policy.imports.closure_sha256` | Worker's read of the document |
| --- | --- | --- | --- |
| Nothing | `75b0…` | `e7ef…` | `edition one` |
| `ROOT` in the specimen | `8bd1…` | `e7ef…` | `EPERM` |
| The rule in the imported file | `75b0…` | `71ab…` | `EPERM` |
| The document's bytes | `75b0…` | `e7ef…` | `edition two` |

The policy's source hashes were the same in all four runs, because the source names the imported file without containing it. The closure hash covers the imported files PW's scan read. Only the worker's read showed the change to the document. For a colleague to repeat a read, send the bytes that were read.

For an incomplete scan, read each file's error in `records` and check `failure` for a problem in the submitted source. A file hash can accompany an error when the scanner read that file but could not follow something inside it. The standalone `sbpl-check --request` helper compiles the supplied source. If the request names an augment, `run` expands it before submission. Compare the effective sources or requested worker captures before drawing conclusions about compiled bytes.

The host looks up file and `exec` targets after orchestration. Its record in `attempt.path_diagnostics` names the observer and stage, even for a step the worker never reached. In three runs the worker stopped before publishing a create's result. Before releasing it, the caller had created an empty file, left the name absent, or made a directory there. The create's host lookup resolved to the same spelling in all three. An unreached open also carried the host's resolution of `/etc/hosts` to `/private/etc/hosts`. To establish what existed or who created it, send independent samples and their times. For an `exec` through a temporary symlink, the worker reported a successful child exit and had no descriptor path to return. The host resolved the submitted name to `/usr/bin/true`. That identifies where the name pointed at collection. For an open, the worker can also supply `attempt.observed_path` from the descriptor it actually acquired. [Attempt path observations](../RESPONSE.md#contract-steps-attempt-path_diagnostics)

If your colleague needs to identify a compiled object, enable `policy.capture_compiled_profile` and supply a fresh `policy.capture_nonce` of 32 lowercase hexadecimal characters. Save the request separately. For a captured receipt compare its `request_nonce` with that saved value. Two requests with the same nonce cannot be distinguished by this comparison. The host checks the worker's capture during collection. The controller admits the receipt's status and labels. The request-file digest identifies the input file even when capture is unavailable. Captured bytecode and input hashes may be sensitive when shared. [Compiled-profile receipts](../RESPONSE.md#read-compiled-profile-receipts)

## Choose the operation and the phase

Use `read_fresh` for a bounded sample and the identity of the descriptor that supplied it. Two documents can have the same first 64 bytes and different endings. If your question is whether your importer accepts either file, run the importer on both. Use `write_fresh` when you need the separate open, truncate and write results. The shorter `open_write` action opens with truncation and tries to write one byte. Give it a disposable copy. Even `open_read` tries to read one byte, which can consume data from a FIFO. [Probe operations](../REQUEST.md#paired-probes-and-attempted-operations)

Within a phase PW collects eligible queries before releasing the worker to perform the actions in order. Suppose you create a previously absent file and then open it. In one phase the planner sees the name while it is absent and can omit the path query. Put the open in a second phase to ask about the file after the create. The same worker keeps the same applied policy across both phases. A fresh *run* starts a new worker and leaves the fixture as the previous run left it. Restore the initial file state when it is part of your control. [Phase declarations](../REQUEST.md#divide-ordinary-actions-into-phases)

## Deciding whether to repeat a run

A lost reply and a refused request call for different decisions. On a client timeout, `data.runner_client.submission` can establish that the client never invoked execution (`not_invoked`). With `invoked`, it called for execution. With `unknown`, the evidence cannot settle whether it did. In both of the latter cases a worker could still act after CLI return. If the envelope itself could not be written, preserve stderr and inspect the affected resource before repeating an effect.

In one experiment, a caller checked the pathname at CLI timeout. It was absent in all three trials. Afterward one worker created and kept a file, one lacked its parent directory, and one created the file and later unlinked it. Sampling after worker exit distinguished only the surviving file. A caller sample between creation and unlink captured the transient effect. If an effect must occur only once and that observation is missing, leave its history unresolved. [Invocation and transport](../RESPONSE.md#read-invocation-and-transport)

## Compare two actors or two kinds of equipment

Use phases for multiple observations of one process. Use `actors` when your question requires different processes. Each actor has its own worker and either applies its own policy or declares an unapplied starting state. Name the actor on each phase. An ordinary step pairs a query and an attempt. Extension actions name issuance, transfer, consumption and release explicitly. [Actor requests](../REQUEST.md#give-each-actor-its-own-sandbox)

To test an extension, let Alice and Bob begin with the same worker equipment and policy. Establish each reader's baseline with a fresh read of known bytes. Transfer the grant to Alice, have her consume it, then repeat both reads. Repeat the trial with Bob as recipient. In the saved trials only the recipient read the word after consumption, and switching the recipient switched the successful read. The transfer's `delivered` and equality records establish delivery. A fresh open after release tests subsequent access. A descriptor acquired earlier can still refer to the file. [Extension coverage](../EXTENSIONS.md)

### Use an external runner

Use the built-in runner for the ordinary unentitled worker. If the experiment needs other signing entitlements, first inspect `runner list` and `runner reconcile`, including pending cleanup. For a user-scope service use a logged-in GUI session, a Developer ID Application identity from the app's team and your worker entitlements plist. Choose a new service label. In the following commands set `PW_APP` to the app containing `$PW`, `PW_SIGNER` to the identity, and `PW_ENT` to the absolute path to the plist.

```sh
PW_STAGE=$(mktemp -d "$PW_WORK/runner.XXXXXX") &&
  PW_BUNDLE="$PW_STAGE/Experiment.xpc" &&
  PW_SERVICE="com.policywitness.guide.$(id -u).$(basename "$PW_STAGE")" &&
  cp -R "$PW_APP/Contents/XPCServices/PWRunner.xpc" "$PW_BUNDLE" &&
  /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $PW_SERVICE" "$PW_BUNDLE/Contents/Info.plist" &&
  /usr/bin/codesign --force --options runtime --sign "$PW_SIGNER" "$PW_BUNDLE" &&
  "$PW" runner install --bundle "$PW_BUNDLE" --identity "$PW_SIGNER" --entitlements "$PW_ENT" --scope user > "$PW_WORK/install.json"
```

Omit `XPC_SERVICE_PATH` or supply the canonical bundle path. Save the installed ID, service name, scope, bundle path and plist path. Run `"$PW" runner verify --service-name "$PW_SERVICE"`. Select the same service with `runner.mode` set to `byoxpc` and `runner.service` set to its label in the specimen. Name the required worker entitlement keys in `runner.required_entitlements`. Check the selected worker's readback before attributing a difference to its equipment. [Runner commands](../../controller/README.md#runner-external-runner-manager)

When finished, run `"$PW" runner remove --service-name "$PW_SERVICE"`. Inspect `cleanup_retained`, warnings and the retained record. Keep the staging bundle and ownership information while cleanup is pending, including after a partial installation. List and reconcile again. Use the recorded selector to continue removal and verify the owned service and plist are absent before discarding staging. [Runner recovery](../../controller/README.md#registry-ownership-and-recovery)

## Where to look for a specific field or limit

The [request reference](../REQUEST.md#request-reference) covers supported actions, actor forms, policy inputs and admission. The [response reference](../RESPONSE.md#read-the-envelope-reference) identifies who observed each field and when. [Limits](../LIMITS.md) describes what can be bounded, truncated or withheld. Use the [responsibilities table](../REQUIREMENTS.md) for the evidence to retain when preparing a comparison or bug report.
