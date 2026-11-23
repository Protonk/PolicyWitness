# What should `run` do with a pathname after `--`?

**Release target.** Conclude during the 0.3.8 guide work. Choose the release for any product change with the result.

**Decision goes to.** Responsibility finding 33 and handoff finding 2 under [what a colleague can establish](../../records/guide/REQUIREMENTS-AND-EXPECTATIONS.md#what-can-a-colleague-establish-about-a-run-they-did-not-see), and an entry in the [product-change ledger](../../records/guide/PRODUCT-CHANGES.md), whether or not the behavior changes. The [decision row](../../records/guide/USER-RESPONSIBILITIES-AND-TESTS.md#decisions-on-the-remaining-proposals) for findings 2, 21 and 33 already prefers a specific refusal.

**Draft 0 decision, 2026-11-23.** Keep the current invocation for 0.3.8. Prefer diagnosing a discarded suffix in later CLI work; accepting it as an operand can newly authorize execution.

`run` and `run -- example.json` both reported a missing request. The parser stops at the terminator, and the `run.terminator` fixture expects that result. Can the conventional end of options remove the ambiguity for a caller with exactly one specimen? [Parser](run_flow.rs) · [Interface cases](../integration/interface_cases.json) · [Captured invocations](../../records/guide/work/evidence/report-diagnosis.zip)

1. In a temporary directory, use a request containing malformed JSON so reaching the file produces an observable parse refusal before submission. Compare `run example.json` and `run -- example.json`. Repeat with a real filename beginning with a dash. Record argv, selected path, whether `data.specimen.request_sha256` shows a read, refusal stage, exit status and whether a runner client was invoked.
2. Compare the current parser with treating all tokens after `--` as operands. Cover no path, a path before a trailing terminator, and a second path on either side of the terminator. Check a flag-shaped pathname and a non-UTF-8 pathname. Follow the shared parser through `test-input run` with a control before the terminator. [Argument forms](interface/run_args.rs)

Return a small table of current and candidate outcomes, including any caller or fixture that relies on ignored suffixes. Identify the smallest parser or diagnostic change justified by the table.
