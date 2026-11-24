# PolicyWitness

PolicyWitness (PW) runs a small experiment on a macOS sandbox policy. You supply a *specimen* describing the policy, the questions to ask and the operations to attempt. A fresh worker applies the policy. A separate validator can ask about that worker before the worker acts. PW returns their observations in one JSON file. Use it when you can name an operation that would help explain what happened in your application.

## Run your first specimen

On an Apple Silicon Mac running macOS 26, open Terminal. Set `PW` to the executable in your installed app. The following commands use a new directory so that the result and its inputs can travel together. The later worked examples continue in the same Terminal window. Each starts from a specimen the app prints and edits it with `/usr/bin/jq`, which ships with macOS.

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
  /usr/bin/jq -r '.data.runner_result.steps[0].attempt.fresh_read.content_hex' "$PW_WORK/result.json"
```

For those six bytes the answer is `66697273740a`. To try your own policy, edit `policy.sbpl_source` in a copy of `read.json`, keep the fixture fixed, and save the second result separately, as the [failed-open example](#why-couldnt-my-app-open-this-file) does. Pass the path directly to `run`. For a filename beginning with a dash, use a spelling such as `./-sample.json`; this build ignores arguments following `--`. When changing the target, edit both the query's `filter.value` and the attempt's `target` if you intend them to refer to the same file. After changing builds, generate a new example and review your specimen against the new build before updating its contract.

## Read a result

| Question | Where to look |
| --- | --- |
| Did PW finish the experiment? | Read `result.normalized_outcome`. A `finished` run can contain a failed open. `policy-witness help result` lists the command outcomes and exit codes. |
| What did the worker do? | Find the `step_id` in `data.runner_result.steps`. Read `attempt.lifecycle`, `result_source`, `outcome` and the operation's own fields. A completed fresh read carries the bytes it sampled. A synthetic `no_completed_result` leaves the call's return unknown. |
| What did the validator answer? | Read that step's `sandbox_check` for the operation, filter, operand and source. Read `comparison` for their relationship to the attempt and the order PW could establish. A `query_first` answer can survive even when the worker never reached the step. |
| Which conclusion can I use? | Read the controller's `data.runner_sandbox_diagnostics` when present. Inspect its integrity findings before relying on a derived conclusion. For an effect outside the process, compare your own observations of the affected file, service or child. |

For a refusal, start with [repairing a specimen](#repairing-a-refused-specimen). For a lost reply, start with [deciding whether to repeat the run](#deciding-whether-to-repeat-a-run).

## Responsibilities

- **Describe the run you intend.** Write each field name once per JSON object and give each step a distinct, nonempty ID. To [reproduce a run](#handing-a-run-to-someone-else), save the command, specimen and result, along with any imported policies and fixture files it used.
- **Choose what to compare.** For a prediction about a particular read, query the read operation and the pathname you will open. To ask about a file after creating it, put the read in a later phase. PW collects eligible predictions before releasing the worker for that phase.
- **Observe the effect you care about.** To test a helper's write, give it a file with no other writer and compare its bytes before and after. To test an extension grant, compare the recipient's fresh reads before and after consumption. Use a control before attributing a permission error to the policy.
- **Decide when to retry.** Correct a confirmed input refusal and resubmit. After a client timeout, read `data.runner_client.submission`. With `not_invoked`, the client never called for execution. With `invoked` or `unknown`, effects may still occur. If an effect must happen only once, leave the run unresolved until you can establish what happened.

## Repairing a refused specimen

When PW refuses a specimen as `bad_request`, no step has run. PW checks the whole request before it starts a validator, worker or actor. `data.request_failure` names one defect. Fix that field and submit again. If the specimen has another defect, PW refuses it for that one, again without running a step.

To see a refusal leave a file untouched, put a create in front of a read. Copy the read step and turn the copy into a create: its query asks about `file-write-create` and its attempt is an exclusive `create_fresh` of the same path. The copy keeps the read's step ID.

```sh
"$PW" test-input read --target "$PW_WORK/notes" > "$PW_WORK/notes.json" &&
  /usr/bin/jq '.probe_plan = [.probe_plan[0]
      | .sandbox_check.operation = "file-write-create"
      | .attempt.action = "create_fresh"] + .probe_plan' \
    "$PW_WORK/notes.json" > "$PW_WORK/create.json" &&
  "$PW" run "$PW_WORK/create.json" > "$PW_WORK/create-refused.json"
/usr/bin/jq -c '[.result.normalized_outcome, .data.request_failure]' "$PW_WORK/create-refused.json"
ls "$PW_WORK/notes"
```

PW refuses the specimen with `duplicate_step_id` at the second step's `step_id`, and `notes` is absent. Give the create its own ID and submit again.

```sh
/usr/bin/jq '.probe_plan[0].step_id = "create-target"' "$PW_WORK/create.json" > "$PW_WORK/create-repaired.json" &&
  "$PW" run "$PW_WORK/create-repaired.json" > "$PW_WORK/create-result.json" &&
  ls -l "$PW_WORK/notes"
```

The repaired specimen finishes, and its first step creates a one-byte file. The submission PW accepts starts execution from the beginning. Later setup or execution failures can interrupt it.

`run` authorizes execution as soon as the specimen passes admission. If effects on the real targets must wait, try a copy whose effectful steps act on disposable fixtures. Review auxiliary inputs too, including any paths passed as helper arguments. A successful trial describes that copy. Restore the intended inputs only when ready to run them. The standalone compiler helper checks policy source; it cannot admit a whole specimen.

## Why couldn't my app open this file?

Start with what failed. Find the step under `data.runner_result.steps` whose attempt matches the app's operation and pathname. Read its outcome and `attempt.errno` beside the validator's answer for the same operation and path. An `EPERM` beside a `deny` prediction still leaves the cause of the worker's error open.

A control settles it. Try the same pathname under two Seatbelt policies, first with the file absent, then with it present. The second policy adds one rule allowing reads of that file. `PW_WORK` is under `/private/tmp`, the resolved spelling of `/tmp`, so the rule's literal names the path the worker opens. Each result describes a separate run.

```sh
"$PW" test-input read --target "$PW_WORK/report" > "$PW_WORK/report.json" &&
  /usr/bin/jq '.policy.sbpl_source = "(version 1)\n(deny default)"' \
    "$PW_WORK/report.json" > "$PW_WORK/original.json" &&
  /usr/bin/jq --arg target "$PW_WORK/report" \
    '.policy.sbpl_source = "(version 1)\n(deny default)\n(allow file-read-data (literal \"" + $target + "\"))"' \
    "$PW_WORK/report.json" > "$PW_WORK/added.json" &&
  "$PW" run "$PW_WORK/original.json" > "$PW_WORK/original-absent.json" &&
  "$PW" run "$PW_WORK/added.json" > "$PW_WORK/added-absent.json" &&
  printf 'report\n' > "$PW_WORK/report" &&
  "$PW" run "$PW_WORK/original.json" > "$PW_WORK/original-present.json" &&
  "$PW" run "$PW_WORK/added.json" > "$PW_WORK/added-present.json" &&
  for result in original-absent added-absent original-present added-present; do
    /usr/bin/jq -c --arg run "$result" '.data.runner_result.steps[0]
      | [$run, .attempt.outcome, .attempt.errno, .sandbox_check.outcome, .comparison.limitations]' \
      "$PW_WORK/$result.json"
  done
```

| Fixture at the start | Original policy | With the added rule |
| --- | --- | --- |
| File absent | Worker read failed with `ENOENT` (errno 2). No prediction. | Worker read failed with `ENOENT`. No prediction. |
| File present | Worker read failed with `EPERM` (errno 1). Validator predicted `deny`. | Worker read succeeded. Validator predicted `allow`. |

With the file present, changing the rule changed the worker's ability to read it. With the rule in place, the read still needed the file to exist. In the absent-file runs, `comparison.limitations` holds `query_plan:path_unresolved_at_planning`, which explains why there was no prediction. Those runs leave open what either policy would do once the file exists.

For the application, the next question is which call produced its error. Capture the pathname the app actually supplied and the result of its open. A sandbox denial naming that process, operation and path at the time of the failed call gives independent evidence that Seatbelt intervened. If the app chose an unexpected path, check how it formed that name. An app bug can send it to a path its policy restricts. If the open succeeded and the app later rejected the contents, compare those bytes with a document the app is known to accept.

## Handing a run to someone else

Send the specimen file and the result, with any imported policy and fixture files the run used. The recipient can tell which specimen goes with which result. `data.specimen.request_sha256` is the SHA-256 of the bytes PW read from the specimen file. Running `shasum -a 256` on each specimen file finds the one with the same digest, even after the files were renamed.

The digest identifies the specimen file, not the files it names. Copy the first read's specimen under a new name, change the document, and run the copy.

```sh
cp "$PW_WORK/read.json" "$PW_WORK/handoff.json" &&
  printf 'second\n' > "$PW_WORK/document" &&
  "$PW" run "$PW_WORK/handoff.json" > "$PW_WORK/handoff-result.json" &&
  shasum -a 256 "$PW_WORK/read.json" "$PW_WORK/handoff.json" &&
  /usr/bin/jq -r '[.data.specimen.request_sha256, .data.runner_result.steps[0].attempt.fresh_read.content_hex] | @tsv' \
    "$PW_WORK/result.json" "$PW_WORK/handoff-result.json"
```

Both specimen files and both results carry the same digest. Only the worker's reads differ: `66697273740a` before the change and `7365636f6e640a` after it. For a colleague to repeat a read, send the bytes that were read.

An imported policy file has its own identity. `data.specimen.policy.imports.closure_sha256` covers the submitted source and each imported file PW's scan read. Changing a parameter in the specimen changes the request digest and leaves the imported file's hash alone. Editing the imported file changes the closure digest and leaves the request digest alone. The source names the imported file without containing it, so the source's own hash stays the same in both cases. None of these digests covers the bytes of a file the worker reads.

For an incomplete scan, read each file's error in `records` and check `failure` for a problem in the submitted source. A file hash can accompany an error when the scanner read that file but could not follow something inside it. The standalone `sbpl-check --request` helper compiles the supplied source. If the request names an augment, `run` expands it before submission. Compare the effective sources or requested worker captures before drawing conclusions about compiled bytes.

The host looks up file and `exec` targets after orchestration. Its record in `attempt.path_diagnostics` names the observer and stage, even for a step the worker never reached. It resolves the name as it stands at that time, so it cannot say what existed when the worker acted or who created it. To establish that, send independent samples and their times. An `exec` returns no descriptor path, so for an `exec` through a symlink the host's lookup can be the only record of where the name pointed at collection. For an open, the worker can also supply `attempt.observed_path` from the descriptor it actually acquired.

If your colleague needs to identify a compiled object, enable `policy.capture_compiled_profile` and supply a fresh `policy.capture_nonce` of 32 lowercase hexadecimal characters. Save the request separately. For a captured receipt compare its `request_nonce` with that saved value. Two requests with the same nonce cannot be distinguished by this comparison. The host checks the worker's capture during collection. The controller admits the receipt's status and labels. The request-file digest identifies the input file even when capture is unavailable. Captured bytecode and input hashes may be sensitive when shared.

## Choose the operation and the phase

Use `read_fresh` for a bounded sample and the identity of the descriptor that supplied it. Two documents can have the same first <!-- span limits.fresh_read_bytes.value_unit -->64 bytes<!-- /span --> and different endings. If your question is whether your importer accepts either file, run the importer on both. Use `write_fresh` when you need the separate open, truncate and write results. The shorter `open_write` action opens with truncation and tries to write one byte. Give it a disposable copy.

When reading a FIFO, the worker can wait at open for a writer, then wait at read for data while the writer stays connected. Even `open_read` tries to consume one byte. If the worker times out while either call is blocked, the attempt can appear as `started_without_result`. For a read that should finish promptly, use a regular file or arrange for a writer to connect and supply data.

Within a phase PW collects eligible queries before releasing the worker to perform the actions in order. The repaired specimen above created `notes` and read it in one phase, so the planner saw the name while it was absent and omitted both queries. Put the read in a second phase to ask about the file after the create. Remove `notes` first to restore the starting state, then run the phased specimen twice.

```sh
rm "$PW_WORK/notes" &&
  /usr/bin/jq '{contract, specimen_id, policy, phases: [
      {phase_id: "create", actions: [.probe_plan[0]]},
      {phase_id: "read", actions: [.probe_plan[1]]}]}' \
    "$PW_WORK/create-repaired.json" > "$PW_WORK/phases.json" &&
  "$PW" run "$PW_WORK/phases.json" > "$PW_WORK/phases-1.json" &&
  "$PW" run "$PW_WORK/phases.json" > "$PW_WORK/phases-2.json" &&
  for result in create-result phases-1 phases-2; do
    /usr/bin/jq -c --arg run "$result" '.data.runner_result.steps[]
      | [$run, .step_id, .attempt.errno, .sandbox_check.outcome, .attempt.fresh_read.content_hex]' \
      "$PW_WORK/$result.json"
  done
```

In the first phased run the validator answers the read's query, because PW collected it after the create phase. The same worker keeps the same applied policy across both phases. The second run starts a new worker, and the file the first one created is still there. Its exclusive create fails with errno 17 (`EEXIST`) and its read returns the first worker's byte, `78` (`x`). Because the name now exists at planning, the create's query is answered too, with `allow`. That answer concerns the operation, not whether the file already exists. A fresh *run* leaves the fixture as the previous run left it. Restore the initial file state when it is part of your control.

## Deciding whether to repeat a run

A lost reply and a refused request call for different decisions. On a client timeout, `data.runner_client.submission` can establish that the client never invoked execution (`not_invoked`). With `invoked`, it called for execution. With `unknown`, the evidence cannot settle whether it did. In both of the latter cases a worker could still act after CLI return. If the envelope itself could not be written, preserve stderr and inspect the affected resource before repeating an effect.

To watch a worker act after CLI return, turn a read into a create and delay the worker. `test-input run` takes `run`'s arguments and passes test controls to the host. `--worker-pre-ready-hang-ms` holds the worker after it applies the policy and before it reports ready, standing in for a slow worker. `--timeout-ms` makes the client stop waiting first.

```sh
"$PW" test-input read --target "$PW_WORK/late" > "$PW_WORK/late-read.json" &&
  /usr/bin/jq '.probe_plan[0].step_id = "create-late"
      | .probe_plan[0].sandbox_check.operation = "file-write-create"
      | .probe_plan[0].attempt.action = "create_fresh"' \
    "$PW_WORK/late-read.json" > "$PW_WORK/late.json" &&
  "$PW" test-input run --worker-pre-ready-hang-ms 5000 --timeout-ms 1000 \
    "$PW_WORK/late.json" > "$PW_WORK/late-result.json"
/usr/bin/jq -c '[.result.normalized_outcome, .data.runner_client.submission]' "$PW_WORK/late-result.json"
ls "$PW_WORK/late"
```

The result is `xpc_timeout` with submission `invoked`, and `late` is absent. Wait for the held worker, then look again.

```sh
sleep 8; ls -l "$PW_WORK/late"
```

The file is now there. The CLI's answer and the first sample describe the moment the client stopped waiting. Repeating the run then would have submitted a second create. A sample after the worker exits can still miss an effect that was later undone: a file created and then unlinked leaves nothing to find. If an effect must occur only once and no observation covers its whole window, leave its history unresolved.

## Compare two actors or two kinds of equipment

Use phases for multiple observations of one process. Use `actors` when your question requires different processes. Each actor has its own worker and either applies its own policy or declares an unapplied starting state. Name the actor on each phase. An ordinary step pairs a query and an attempt. Extension actions name issuance, transfer, consumption and release explicitly.

To test an extension, let Alice and Bob begin with the same worker equipment and policy. Establish each reader's baseline with a fresh read of known bytes. Transfer the grant to Alice, have her consume it, then repeat both reads. Repeat the trial with Bob as recipient. If only the recipient's read changes, and switching the recipient switches which read changes, the consumed grant accounts for the difference. The transfer's `delivered` and equality records establish delivery. A fresh open after release tests subsequent access. A descriptor acquired earlier can still refer to the file.

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

Omit `XPC_SERVICE_PATH` or supply the canonical bundle path. Save the installed ID, service name, scope, bundle path and plist path. Run `"$PW" runner verify --service-name "$PW_SERVICE"`. Select the same service with `runner.mode` set to `byoxpc` and `runner.service` set to its label in the specimen. Name the required worker entitlement keys in `runner.required_entitlements`. Check the selected worker's readback before attributing a difference to its equipment.

When finished, run `"$PW" runner remove --service-name "$PW_SERVICE"` and read `data.cleanup_retained` even if the command exits 0. If it is true, keep the staged bundle and the ownership record. Read `data.warnings` and `data.retained_record` to see what still needs attention.

If cleanup is pending, including after a partial install, or removal reports a warning, use `"$PW" runner list` to find the record and `"$PW" runner reconcile` to inspect the service and plist. Use the recorded ID or service name when retrying removal. Discard staging only after confirming that the owned service and plist are both absent and cleanup is complete.

## Public contract surfaces

The table gives the release that last changed each part of the public contract.

<!-- BEGIN GENERATED CONTRACT STAMPS -->
| Surface | User artifact | Last changed |
| --- | --- | --- |
| `actor_evidence` | Actor and phase evidence | v0.3.8 |
| `actors` | Actors and phases | v0.3.8 |
| `diagnostics` | Controller findings and assessments | v0.3.8 |
| `dossier` | Specimen dossier | v0.3.8 |
| `envelope` | The controller envelope | v0.3.8 |
| `equipment` | Equipment and authority setup | v0.3.8 |
| `extensions` | Extension actions and authority custody | v0.3.8 |
| `identity` | The contract identity | v0.3.8 |
| `installation` | Managing runners | v0.3.8 |
| `lifecycle` | Process and operation observations | v0.3.8 |
| `policy` | Policy source, parameters and compilation | v0.3.8 |
| `probes` | Paired probes and attempted operations | v0.3.8 |
| `profile` | Compiled-profile receipts | v0.3.8 |
| `refusals` | Request refusals and retained evidence | v0.3.8 |
| `reply` | The host report | v0.3.8 |
| `request` | Saved specimens and runner selection | v0.3.8 |
| `steps` | Predictions, attempts and comparison | v0.3.8 |
| `transport` | Reservation, invocation and client capture | v0.3.8 |
| `wire` | Binary response primitives and validator record transport | v0.3.8 |
<!-- END GENERATED CONTRACT STAMPS -->
