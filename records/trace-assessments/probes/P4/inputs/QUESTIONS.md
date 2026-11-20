# P4 questions

Each file T1 to T6 in this directory is test or checker code from PolicyWitness, a tool that runs macOS sandbox experiments. These are excerpts; you will not see the product code they exercise or the documentation that describes them. For each file, answer from the code alone:

(a) What does this test establish? Distinguish what it asserts (and so would fail on) from what it only records or reports.
(b) Name concrete incorrect behaviours that would make it fail.
(c) Name a plausible claim someone might make about this test that it does not support, and why.

- T1.swift: one Swift test case, ending at an assertion about custody `erased` flags.
- T2.py: a checker for a three-actor "re-delegation" experiment, with a calibration and contrasts.
- T3.py: a checker for a run whose worker fails before policy application.
- T4.rs: one Rust test about compiled-profile receipts and run admission.
- T5.rs: helper functions, then one Rust test about the fallback policy compilation's input.
- T6.py: a checker for a run whose exec leader exits while a same-group descendant may remain.
