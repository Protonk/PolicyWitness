# Writing a PolicyWitness bug report

## Worked report

**Title.** `run -- example.json` reports `missing <request.json>` for a specimen that `run example.json` executes.

**What I expected.** I want to pass a user-supplied specimen path to PW from a shell script. I use `--` to end option parsing so a pathname beginning with a hyphen can be passed literally. I expected PW to take the next argument as the request path. The refusal reproduces even with the ordinary filename `example.json`.

**Where I saw it.** PolicyWitness 0.3.7, development build 1634 (`e7937ecc`), macOS 26.7.1 (25G241), arm64. I used the built-in runner.

**How to reproduce.** Set `PW` to the absolute path of the executable in your app. These commands use a fresh directory and the example emitted by that same executable.

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
cd "$(mktemp -d /private/tmp/pw-report.XXXXXXXX)" || exit 1
"$PW" example > example.json
"$PW" run -- example.json > example-refused.json 2> example-refused.stderr
printf 'with -- returned %s\n' "$?"
"$PW" run example.json > example-ordinary.json 2> example-ordinary.stderr
printf 'without -- returned %s\n' "$?"
```

The first invocation of `run` exited 2 with empty stderr. Its JSON on stdout gave `result.normalized_outcome = "tool_error"` and `result.error = "missing <request.json>"`. Both `data.specimen.request_path` and `data.runner_client` were null. The refusal happened before PW invoked a runner client.

Removing just `--` gave exit 0 and worker results for all three steps. I used `help result` to interpret the exit statuses. Its `tool_error false 2` and `finished true 0` rows describe the two invocations. Within the finished run, the `read-propernames` step reported `open_failed`.

**Smaller case.** I replaced the example's phases and dictionary paths with one read of five bytes I supplied. Run these in the same directory.

```sh
printf 'blue\n' > target.txt
"$PW" test-input read --target "$PWD/target.txt" > read.json
"$PW" run -- read.json > read-refused.json 2> read-refused.stderr
printf 'with -- returned %s\n' "$?"
"$PW" run read.json > read-ordinary.json 2> read-ordinary.stderr
printf 'without -- returned %s\n' "$?"
```

The first run gave the same exit 2 and missing-path message. The second exited 0. In the `read-target` step, `attempt.fresh_read.read_rc` was 5 and `content_hex` was `626c75650a`, the bytes I wrote. Both specimens work when I pass the path directly. I'd like PW to accept a single pathname after `--`.

**Attachments.** The two emitted specimens, target bytes, four complete envelopes, process exit statuses, stderr, version and help output are in [the report attachment](work/evidence/bug-report.zip). The read specimen contains my original absolute target path. The command above emits one for yours.

## Write yours

1. **Lead with the discrepancy.** Put the command or step and its surprising result in the title. Say what you were trying to do, what you expected, and why. Here the expectation comes from how the reporter passes filenames in a shell script. If yours comes from a PW help card or a documented promise, quote the relevant line.
2. **Give the recipient a starting point.** Save `"$PW" --version`, identify the macOS build and runner, and keep the specimen you actually submitted. The recipient can confirm that a specimen is the one the run read by comparing its SHA-256 with `data.specimen.request_sha256`. If `"$PW" example` shows the symptom, someone with the app can get that input without your project. Use `"$PW" help example` to locate the attempted operation of interest and read its query and policy in the emitted JSON.
3. **Show what makes the symptom appear.** Change one thing and give the command and observation on each side. For a file read, `"$PW" test-input read --target "$PWD/target.txt"` emits a single-step specimen under `(allow default)`. Supply the file yourself and run the specimen with `"$PW" run`. If the failure depends on your policy, keep that policy and change one field in the original specimen. A passing read under the default policy answers a different question.
4. **Point to the evidence that decides the claim.** Save stdout, stderr and the shell status separately. For an argument refusal, include the exact invocation. Someone who received only this report's refusal envelope could equally well conclude that the script passed no path at all. Use `"$PW" help result` to read the outer outcome. For a claim about a worker, name the step and its observation. For a claim about a file, include the relevant bytes or filesystem samples and say when you took them. Attach the inputs and full envelopes so the recipient can check your reading.
