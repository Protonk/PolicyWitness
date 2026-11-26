# What can two individually acceptable runs conceal?

This investigation is part of the [0.4.0 Test Atlas](ATLAS-BUILD-PLAN.md#comparison-investigation-for-040). What incorrect or unsupported conclusion can our present tests admit when individually acceptable runs are interpreted together, and what evidence exposes the mistake?

PAWL interprets evidence across runs when comparing policies. Locating a mistaken inference might reduce the interpretation a PAWL caller has to supply. Whether the missing fact is observable by PW, checked by a test, or known only to the caller is itself a question for the investigation.

## Fixture account

The four original envelopes came from direct runs of the built-in runner on macOS 26.7.1 (25G241), development build 1634 at `e7937ecc`. Read the exact contract in each file's `build.contract` and `data.runner_result.producer.contract`. They predate the released request-file digest. Keep the files byte-for-byte with their producer identity. A replay on another build needs its own reviewed inputs, fixture account and observations.

The caller prepared a scratch tree containing `d/a` and varied the presence of `d/hole`. The original profile allowed by default and denied `file-read-data` under `d`. The second added an allow for that operation on the literal `d/hole`. Step `s0` attempted to open that path and `s1` attempted the neighboring `d/a`. The tree itself was temporary. Its preparation comes from the caller's account. A worker errno describes the later open.

| Caller fixture | Original policy | Added allow rule |
| --- | --- | --- |
| `d/hole` present | [Original, present](../../controller/compare-fixtures/orig_holepres.result.json) | [Added rule, present](../../controller/compare-fixtures/hole_holepres.result.json) |
| `d/hole` absent | [Original, absent](../../controller/compare-fixtures/orig_holeabs.result.json) | [Added rule, absent](../../controller/compare-fixtures/hole_holeabs.result.json) |

## Read the pairs

1. Give a reader the absent pair first. In `data.runner_result.steps`, locate `s0` on each side. Check the phase, requested action and path, the source of the result and the separate query operand and source. Both workers reported `ENOENT` and neither had a validator prediction for that path. Ask what that establishes about equivalence of the policies.
2. Add the present pair. For `s0` the worker's `EPERM` becomes a successful open. The neighboring `s1` open failed with `EPERM` in all four results. Reveal the fixture account and ask what justifies pairing these runs. Equal step IDs, errno values or outer outcomes alone cannot make one trial a control for another. Identify the conclusion warranted about the tested file and what evidence a claim about another application's open would require.
3. Find the assertion a maintainer would cite for that conclusion. Read the raw records and fixture preparation independently before consulting the checker. Identify exactly which relationship it tests, if any. Reapplying its reader to both results can give the same wrong answer twice.

## Challenge one credited relationship

Use the Atlas question about **when the host cleared its copy of an extension token**. The self-transfer assertion inspects a final flag. Both historical E6 runs ended with that flag true, although samples between phase boundaries showed different custody histories. Read the two timed samples and their fixture conditions before reading the assertion. Record which interval each observer can distinguish. [Custody question, samples and provenance](ATLAS-BUILD-PLAN.md#when-did-the-host-clear-its-copy-of-an-extension-token)

Test the outstanding inference on one controlled pair. Predict what the current assertion would say if clearance occurred only at teardown. In a disposable host trial keep the transfer and teardown, vary the last-use clear, and sample custody between last use and teardown independently of the final flag. Compare the actual assertion on both runs with those samples. Record the host/checker revisions, intervening phase and limits of the sampling hook. A constructed pair can test how a reader handles the records. Credit a difference in host behavior only for an observed host trial.

Return a short account for the relevant Atlas route. Give the proposed relationship, its independent justification, each original observation, the actual assertion and a contrary history. Locate any error precisely. PW may record or attribute a fact incorrectly. A checker may accept a false equivalence or difference, or lose evidence already acquired. The sampling may leave both histories possible. A causal reading may depend on a fixture condition or rationale only its author supplied. A demonstrated limit is a result even when PW and its checker both behave as promised.

Stop after the four opens and the harder pair. An offline script may serve the investigation and be discarded. Hand a demonstrated defect to the owner of `run`, `test` or the checker with its distinguishing case. The Atlas keeps enough evidence to challenge the conclusion, including after a repair makes the script redundant. Public dispatch, a permanent comparison format, support for historical inputs and porting PAWL's machinery are outside this investigation.
