# P2 questions

Each file S1.md to S4.md in this directory is an excerpt from the PolicyWitness contract. Using only that excerpt, predict the outcome of each input below. For each prediction, quote the sentence or rule you relied on. If the excerpt does not decide the outcome, say "not decided by the text" and say what is missing.

## S1 (S1.md): validator association

Setup: an ordinary request has one step whose `step_id` is `café`, spelled with U+00E9. It queries `file-read-data` on a path. Each input is the validator record that comes back for that step (or, for I4, the request itself). Predict: does the record associate with the step; which association issues appear; the step's `order`; the run's normalized outcome and exit code.

- I1. The record's `step_id` is the same bytes as the request's.
- I2. The record's `step_id` is `cafe` followed by U+0301: canonically equivalent to the request's, but different bytes.
- I3. The record's `step_id` bytes are identical, but its filter value is a canonically equivalent spelling of the path with different bytes.
- I4. Instead, the request itself has two steps, one with `step_id` `café` spelled with U+00E9 and one spelled `cafe` followed by U+0301.

## S2 (S2.md): import inventory

Each input is a policy fragment given to the `sbpl-check` helper. `/d/marker.sb` is a readable file holding one rule. For each, predict: does the inventory record `/d/marker.sb`; the value of `unfollowed_imports`; and does the excerpt let you say whether the compiler evaluated the import.

- I1. `(import ; note` then a newline, then `"/d/marker.sb")`
- I2. `[import "/d/marker.sb"]`
- I3. `(import (string-append "/d" "/marker.sb"))`
- I4. `(if #f (import "/d/marker.sb"))`
- I5. `(define pw-alias import)` then a newline, then `(pw-alias "/d/marker.sb")`

## S3 (S3.md): registry loading

`PW_RUNNER_REGISTRY` names the registry path. For each input, predict what the command prints (envelope or not, and on which stream) and its exit code.

- I1. There is no entry at the path; its parent directory exists. Command: `runner list`.
- I2. The path is a symlink to a missing target. Command: `runner list`.
- I3. A directory is at the path. Command: `runner status --id x`.
- I4. The path's parent directory cannot be searched. Command: a `run` that selects an external runner. Also: is a runner client started?
- I5. `PW_RUNNER_REGISTRY` is set to the empty string. Command: `runner list`. Which registry path is used?

## S4 (S4.md): exec stream text and counts

Each input is a child process's entire stdout, written before it exits. Predict `bytes_received`, `bytes_retained`, `truncated`, `text_exact`, and how the reply's stdout text ends.

- I1. `x` followed by 2,000 copies of `é` (4,001 bytes).
- I2. `xx` followed by 2,000 copies of `é` (4,002 bytes).
- I3. `HEAD`, a NUL byte, then 2,048 `0` characters (2,053 bytes).
- I4. 17 bytes that are not valid UTF-8.
