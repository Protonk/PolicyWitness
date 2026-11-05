# Documentation rerun passed

The user authorized rerunning the source-drift/documentation contracts and then
completing final reader preparation and responses. Root inspected the exact
selection and ran the three cases once, outside the automation sandbox:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-docs-02 tests/run.sh \
  --case source_drift/architecture_documentation \
  --case source_drift/limits_documentation \
  --case source_drift/generator_contract
```

Run `20261105T044221Z_f559a79b` completed all three cases with three passes,
zero skips/unrun cases and zero recorded sleep overlap, in 80,454 ms.
The corrected candidate patch SHA-256 matched before and after:
`1d9a77ef503eb5357cb2796fb7233550417c1909a51b063dd5c2489fe8b68b49`.
The prior failure remains a failed historical run; this rerun supplies new
credit for the corrected citations and the documentation contracts.

No Swift or product source changed. The 525/525 Swift tests and three downstream
reader replays retain their fresh credit from `doc-lookback-docs-01`, under the
existing applicability review. No distribution rebuild or F1 fixture execution
was needed or performed.

After terminal completion, `test-console.log` and `requested-selection.json`
were attached to the owned output under the checkout lock after checking
run/owner identity and resolved output path. Their SHA-256 values are:

- Console: `031f6060f05d07cfeaa8e67dcfab62361fefcd32f7b0946916314ab3f7b790f2`.
- Selection: `dc55da962f28c4b9aad3079b0f91a54371d25e047b0e2873995f942e852ab0be`.

`documentation/verification-02.json` retains the terminal accounting.
The validation gate is closed for final reading, without representing the
earlier broad battery as wholly passing or F1 as repaired. Final document
acceptance still depends on the reader-pair assessment and user decisions.
