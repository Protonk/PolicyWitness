# What should `run` do with a pathname after `--`?

`run` and `run -- example.json` both reported a missing request. The parser stops at the terminator, and the `run.terminator` fixture expects that result. Can the conventional end of options remove the ambiguity for a caller with exactly one specimen? [Parser](run_flow.rs) · [Interface cases](../integration/interface_cases.json) · [Captured invocations](../../records/guide/work/evidence/report-diagnosis.zip)

1. In a temporary directory, use a request containing malformed JSON so reaching the file produces an observable parse refusal before submission. Compare `run example.json` and `run -- example.json`. Repeat with a real filename beginning with a dash. Record argv, selected path, whether `data.specimen.request_sha256` shows a read, refusal stage, exit status and whether a runner client was invoked.
2. Compare the current parser with treating all tokens after `--` as operands. Cover no path, a path before a trailing terminator, and a second path on either side of the terminator. Check a flag-shaped pathname and a non-UTF-8 pathname. Follow the shared parser through `test-input run` with a control before the terminator. [Argument forms](interface/run_args.rs)

Return a small table of current and candidate outcomes, including any caller or fixture that relies on ignored suffixes. Identify the smallest parser or diagnostic change justified by the table.
