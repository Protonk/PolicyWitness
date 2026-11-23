# PolicyWitness

## Responsibilities

- **Describe the run you intend.** Write each field name once per JSON object and give each step a distinct, nonempty ID. To reproduce a run, save the command, specimen and result, along with any imported policies and fixture files it used.
- **Choose what to compare.** For a prediction about a particular read, query the read operation and the pathname you will open. To ask about a file after creating it, put the read in a later phase. PW collects eligible predictions before releasing the worker for that phase.
- **Observe the effect you care about.** To test a helper's write, give it a file with no other writer and compare its bytes before and after. To test an extension grant, compare the recipient's fresh reads before and after consumption. Use a control before attributing a permission error to the policy.
- **Decide when to retry.** Correct a confirmed input refusal and resubmit. After a client timeout, read `data.runner_client.submission`. With `not_invoked`, the client never called for execution. With `invoked` or `unknown`, effects may still occur. If an effect must happen only once, leave the run unresolved until you can establish what happened.

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
