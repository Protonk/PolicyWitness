> Deposited by the coordinator on 2026-11-10 for register row `R-14` in
> `records/contract/CONTRACT-LEDGER.md`. This is the return of a delegated
> pass that ran the candidates of `records/contract/validators/COMPARISON.md`
> in a disposable worktree, unchanged except for this note and Markdown
> links turned into literal text. The temporary test code it added is
> `records/contract/validators/RUN.patch`. The worktree and its raw output
> have been removed.

# Observed judgments of three readers on preparation-failure replies

Worktree commit (`git rev-parse HEAD`): `35226316beb3f2f2bbc326f92a51b136f5c5bc26`, plus the test-only changes in `r14-run.patch` (beside this file).

These are experiment runs made directly with the commands below. They are not runs of the catalog cases `runner_unit/pwrunner_core_unit_executable` or `unit/rust.unit` and establish nothing about the battery. No product source was changed; nothing was signed, packaged, committed or pushed.

## Commands

`W` is the worktree root. All three were run twice: once with 70 Swift-built replies, then again (after adding the D1c–D1e, N1 and N2 variants, the A0p variants and the envelope observation) with 85. The results below are from the second run; every exit status was 0 in both.

1. Swift (S, and the encoded replies). Same invocation as `tests/suites/runner_unit/run.sh:32`, with the experiment's output directory named so the test executable runs only the experiment and exits before the registered unit tests:

   ```sh
   PW_R14_EXPERIMENT_OUT="$W/.tmp/r14/out" /usr/bin/swift run -Xswiftc -DPW_UNIT_TEST_CONTEXT --jobs 2 \
     --scratch-path "$W/.tmp/r14/swift" --package-path "$W/runner" PWRunnerCoreTests
   ```

   Exit status 0. Last line: `r14 experiment: 85 replies written to …/.tmp/r14/out`. `PW_TEST_ARTIFACTS` and `PW_LIFECYCLE_WORKER_FIXTURE`, which the suite script sets, were not set; the experiment does not read them.

2. Rust (R). Same invocation as `tests/suites/runner_unit/run.sh:74-78`, naming the experiment test, with an isolated target directory and `cargo` from `/opt/homebrew/opt/rustup/bin`:

   ```sh
   CARGO_TARGET_DIR="$W/.tmp/r14/cargo-target" PW_R14_DIR="$W/.tmp/r14/out" cargo test --jobs 2 \
     --manifest-path "$W/controller/Cargo.toml" --bin policy-witness -- \
     --include-ignored --exact run_flow::tests::r14_preparation_failure_readers
   ```

   Exit status 0. `running 1 test … test result: ok. 1 passed; 0 failed`. The test asserts nothing about the judgments; it records them in `rust.json`.

3. Python (P), from the worktree root:

   ```sh
   env -u PYTHONOPTIMIZE tests/lib/python.sh tests/suites/runner_unit/r14_experiment.py "$W/.tmp/r14/out"
   ```

   Exit status 0. Output: `r14 experiment: 101 replies judged by the consumer`.

## How each reply reached each reader

- Each reply was built once. `runR14Experiment` (temporary, `runner/Tests/PWRunnerCoreTests/R14ExperimentTests.swift`) takes the three documents of `actorShapeDocuments()` that carry `preparation_failure` (indices 15, 17, 18 of 24: the `preparation`, `bindingRefusal` and `inventoryRefusal` fixtures), mutates the typed `PWRunnerRunResult`, calls `validateForReporting()` and records the outcome, then calls `pwPorcelainEncode` directly (no self-check) and writes `<id>.pwp`. Every reply encoded.
- `run_flow::tests::r14_preparation_failure_readers` (temporary) decodes each `.pwp` with `crate::porcelain::decode`, serializes the typed record to JSON, and judges `fixture_reply(json)` with `execution_diagnostics`, `admission_problem`, `reply_version` and `run_flow::admit_reply`, as `actor_driver_replies_cross_readers` does. It also renders the run envelope from that reply the way the existing tests do, to observe `data.runner_result`. It writes the JSON and the judgments to `rust.json`. Every reply decoded, from bytes and from JSON.
- `r14_experiment.py` (temporary) gives that same JSON to `consumer.validate_fixture(reply, expected_contract="test:policy-witness")`, the contract the existing cross-reader test passes. Difference from the existing test: the Python process is started through `tests/lib/python.sh` on the file the Rust test wrote, not as a `/usr/bin/python3` child of the Rust test.
- Changes the typed Swift record cannot hold (JSON null) were applied in the Rust test to the decoded JSON; S was not asked about those rows. For a JSON null the typed Rust record holds `None`, so R judged the record without the key while P judged the JSON with the null; those rows say so.
- D1 to D10 and D12, and the D13 starting points N1 and N2, were applied to each of the three baselines (B1, B2, B3): 31 replies per baseline, the control and 30 changes. Each of the 31 gave the same S outcome and diagnostic, the same R issues and the same P errors on all three baselines.
- For every one of the 101 replies: `admission_problem` returned `None`, `reply_version` was `supported`, `run_flow::admit_reply` was `Admitted`, and the rendered envelope carried `data.runner_result` non-null and equal to the typed reply. Every R objection observed appeared only as `disposition_issues` in `execution_diagnostics` (with `process_disposition: "withheld"`, `disposition_integrity: "invalid"`); none came from `admission_problem`.

Reply identifiers: `B1`–`B3` baselines; `Bn-Dk…` candidate Dk applied to baseline n (letters distinguish ways of making the change); `Bn-D12-0` the degraded control for D12; `Bn-N1`, `Bn-N2` baselines with `preparation_failure` removed (tried as starting points for D13); `O0` the ordinary reply; `A0`, `AR` actor-form shape documents without `preparation_failure`; `A0p` A0 with attempt path diagnostics added in JSON.

## Judgments

S = `validateForReporting()`; R = `execution_diagnostics` and `admission_problem`; P = `consumer.validate_fixture` (it returned a list each time and never raised; a non-empty list is counted as an objection).
Predicted is the comparison's section D; "control" rows carry the expectation that every reader accepts.

| Reply | S | R | P | Predicted | Matches |
| --- | --- | --- | --- | --- | --- |
| B1 | accepts | accepts | accepts | control: all accept | yes |
| B1-D1a | objects | objects | objects | S objects / R objects / P accepts | not a clean observation: row not well-formed for R and P general setup check |
| B1-D1b | objects | objects | objects | S objects / R objects / P accepts | not a clean observation: row not well-formed for R and P general setup check |
| B1-D1c | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B1-D1d | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B1-D1e | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B1-D2a | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B1-D2b | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B1-D3 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D4a | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D4b | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D4c | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D5 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D5-jabsent | not asked | objects | objects | S accepts / R objects / P objects | yes; S not asked |
| B1-D5-jnull | not asked | objects | objects | S accepts / R objects / P objects | yes; S not asked |
| B1-D6a | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B1-D6b | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B1-D7 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D8 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D9a | accepts | objects | accepts | S accepts / R objects / P accepts | yes |
| B1-D9b | accepts | objects | accepts | S accepts / R objects / P accepts | yes |
| B1-D10a | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D10b | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B1-D12-0 | accepts | accepts | accepts | control: all accept | yes |
| B1-D12a | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B1-D12b | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B1-D12c | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B1-N1 | objects | objects | objects | none (starting point tried for D13) | n/a |
| B1-N1-D13 | not asked | objects | objects | S not expressible / R accepts / P objects | not a clean observation: starting reply not accepted by all readers |
| B1-N2 | accepts | accepts | accepts | none (starting point tried for D13) | n/a |
| B1-N2-D13 | not asked | accepts | objects | S not expressible / R accepts / P objects | yes |
| B2 | accepts | accepts | accepts | control: all accept | yes |
| B2-D1a | objects | objects | objects | S objects / R objects / P accepts | not a clean observation: row not well-formed for R and P general setup check |
| B2-D1b | objects | objects | objects | S objects / R objects / P accepts | not a clean observation: row not well-formed for R and P general setup check |
| B2-D1c | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B2-D1d | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B2-D1e | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B2-D2a | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B2-D2b | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B2-D3 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D4a | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D4b | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D4c | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D5 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D5-jabsent | not asked | objects | objects | S accepts / R objects / P objects | yes; S not asked |
| B2-D5-jnull | not asked | objects | objects | S accepts / R objects / P objects | yes; S not asked |
| B2-D6a | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B2-D6b | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B2-D7 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D8 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D9a | accepts | objects | accepts | S accepts / R objects / P accepts | yes |
| B2-D9b | accepts | objects | accepts | S accepts / R objects / P accepts | yes |
| B2-D10a | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D10b | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B2-D12-0 | accepts | accepts | accepts | control: all accept | yes |
| B2-D12a | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B2-D12b | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B2-D12c | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B2-N1 | objects | objects | objects | none (starting point tried for D13) | n/a |
| B2-N1-D13 | not asked | objects | objects | S not expressible / R accepts / P objects | not a clean observation: starting reply not accepted by all readers |
| B2-N2 | accepts | accepts | accepts | none (starting point tried for D13) | n/a |
| B2-N2-D13 | not asked | accepts | objects | S not expressible / R accepts / P objects | yes |
| B3 | accepts | accepts | accepts | control: all accept | yes |
| B3-D1a | objects | objects | objects | S objects / R objects / P accepts | not a clean observation: row not well-formed for R and P general setup check |
| B3-D1b | objects | objects | objects | S objects / R objects / P accepts | not a clean observation: row not well-formed for R and P general setup check |
| B3-D1c | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B3-D1d | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B3-D1e | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B3-D2a | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B3-D2b | objects | objects | accepts | S objects / R objects / P accepts | yes |
| B3-D3 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D4a | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D4b | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D4c | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D5 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D5-jabsent | not asked | objects | objects | S accepts / R objects / P objects | yes; S not asked |
| B3-D5-jnull | not asked | objects | objects | S accepts / R objects / P objects | yes; S not asked |
| B3-D6a | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B3-D6b | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B3-D7 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D8 | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D9a | accepts | objects | accepts | S accepts / R objects / P accepts | yes |
| B3-D9b | accepts | objects | accepts | S accepts / R objects / P accepts | yes |
| B3-D10a | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D10b | accepts | objects | objects | S accepts / R objects / P objects | yes |
| B3-D12-0 | accepts | accepts | accepts | control: all accept | yes |
| B3-D12a | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B3-D12b | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B3-D12c | accepts | accepts | objects | S accepts / R accepts / P objects | yes |
| B3-N1 | objects | objects | objects | none (starting point tried for D13) | n/a |
| B3-N1-D13 | not asked | objects | objects | S not expressible / R accepts / P objects | not a clean observation: starting reply not accepted by all readers |
| B3-N2 | accepts | accepts | accepts | none (starting point tried for D13) | n/a |
| B3-N2-D13 | not asked | accepts | objects | S not expressible / R accepts / P objects | yes |
| O0 | accepts | accepts | accepts | control: all accept | yes |
| O0-D11 | objects | objects | accepts | S objects / R objects / P accepts | yes |
| A0 | accepts | accepts | objects | none (starting point tried for D13) | n/a |
| A0p | not asked | accepts | accepts | control: all accept | yes |
| A0-D13 | not asked | accepts | objects | S not expressible / R accepts / P objects | not a clean observation: starting reply not accepted by all readers |
| A0p-D13 | not asked | accepts | objects | S not expressible / R accepts / P objects | yes |
| AR | accepts | objects | objects | none (starting point tried for D13) | n/a |
| AR-D13 | not asked | objects | objects | S not expressible / R accepts / P objects | not a clean observation: starting reply not accepted by all readers |

## Per reply

### B1

- Change: none (control): actorShapeDocuments()[15], resolved_plan/inconsistent_assignment, reason constructed assignment mismatch
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### B1-D1a

- Change: authority_setup.host.regions = [one row for actor A (index 0), disposition ready, as the `accounted` fixture builds it]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `actor_evidence`: released setup ownership lacks successful cleanup; `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'released setup ownership lacks successful cleanup'; 'released setup ownership lacks successful cleanup'
- Predicted: S objects / R objects / P accepts. Matches: not a clean observation: row not well-formed for R and P general setup check.

### B1-D1b

- Change: authority_setup.host.regions = [one row for actor A (index 0), disposition failed with cleanup_reference, as the `recovery` fixture builds it]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'released setup ownership lacks successful cleanup'
- Predicted: S objects / R objects / P accepts. Matches: not a clean observation: row not well-formed for R and P general setup check.

### B1-D1c

- Change: authority_setup.host.regions = [{actor_id A, actor_index 0, required true, disposition not_attempted, operations [], ownership {}}]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B1-D1d

- Change: authority_setup.host.regions = [the D1a ready row plus succeeded cleanup operations close_original_descriptor (slot 9) and munmap (slot 11)]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B1-D1e

- Change: authority_setup.host.regions = [the D1b failed row plus a succeeded cleanup operation close_original_descriptor (slot 9)]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B1-D2a

- Change: phases[0].arrival_observed false -> true (phase b_before, actor B)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B1-D2b

- Change: phases[2].arrival_observed false -> true (phase initial_supply, actor A; predecessor is actor C)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B1-D3

- Change: phases[0].ordering (was nil) = {collection_closed_before_proceed: false, proceed_set: true, proceed_observed: false, validator_disposition: not_invoked, worker_lifetime_established: false, protocol_violations: []}
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D4a

- Change: phases[0].action_ids[0] b_read_before -> 64 bytes of 'a'
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D4b

- Change: phases[0].action_ids[0] b_read_before -> empty string
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D4c

- Change: phases[0].action_ids[0] b_read_before -> "a\u0000b" (contains NUL)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D5

- Change: extension_events (was array of 0) = nil in the typed record
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Decoded JSON: `extension_events` key is absent
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D5-jabsent

- Change: decoded JSON of the baseline with the extension_events key removed
- Built by: change applied in Rust to the decoded JSON of B1; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes; S not asked.

### B1-D5-jnull

- Change: decoded JSON of the baseline with extension_events set to JSON null
- Built by: change applied in Rust to the decoded JSON of B1; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes; S not asked.

### B1-D6a

- Change: phases[0].phase_id b_before -> 64 bytes of 'p'
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'invalid phase_id'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B1-D6b

- Change: phases[0].phase_id b_before -> empty string
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'invalid phase_id'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B1-D7

- Change: phases[0].actor_visit 1 -> 2
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: phase actor_visit disagrees with that actor's visit order; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actor_visit disagrees with that actor's visit order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D8

- Change: actors[0].visits [3] -> []
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor visits disagree with its phases'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D9a

- Change: actors[0].visits [3] -> [3, 8] (8 is the ordinal of another actor's phase)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S accepts / R objects / P accepts. Matches: yes.

### B1-D9b

- Change: actors[0].visits [3] -> [3, 9] (9 exceeds the phase count 8)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S accepts / R objects / P accepts. Matches: yes.

### B1-D10a

- Change: actors[0].index 0 -> 1 (repeats actors[1].index)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor index or identity conflict; `actor_evidence`: phase actor is absent; `actor_evidence`: actor index or identity conflict; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D10b

- Change: actors[0].index 0 -> 3 (no actor has it; actor count 3)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor index or identity conflict; `actor_evidence`: phase actor is absent; `actor_evidence`: actor index or identity conflict; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B1-D12-0

- Change: degraded as the host re-issues it: rc 1, runner_reporting_failed, error, reporting_failure{evidence_retained: true}; no defect (control for D12)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### B1-D12a

- Change: degraded as D12-0, then actors = []
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'actor form requires a bounded actors list'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B1-D12b

- Change: degraded as D12-0, then actors[0].index 0 -> 1
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B1-D12c

- Change: degraded as D12-0, then phases[0].actor_visit 1 -> 2
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'phase actor_visit disagrees with that actor's visit order'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B1-N1

- Change: preparation_failure removed (nil); nothing else changed (candidate starting point for D13)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `phase identities and ordered actions must partition the reply`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `phase_collection`: phase actions do not partition reply; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'
- Predicted: none (starting point tried for D13). Matches: n/a.

### B1-N1-D13

- Change: decoded JSON of B1-N1 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of B1-N1; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `phase_collection`: phase actions do not partition reply; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: not a clean observation: starting reply not accepted by all readers.

### B1-N2

- Change: preparation_failure removed (nil) and every phase's action_ids emptied (candidate starting point for D13)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: none (starting point tried for D13). Matches: n/a.

### B1-N2-D13

- Change: decoded JSON of B1-N2 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of B1-N2; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: yes.

### B2

- Change: none (control): actorShapeDocuments()[17], equipment/equipment_binding_refused, reason entitlements_unreadable
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### B2-D1a

- Change: authority_setup.host.regions = [one row for actor A (index 0), disposition ready, as the `accounted` fixture builds it]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `actor_evidence`: released setup ownership lacks successful cleanup; `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'released setup ownership lacks successful cleanup'; 'released setup ownership lacks successful cleanup'
- Predicted: S objects / R objects / P accepts. Matches: not a clean observation: row not well-formed for R and P general setup check.

### B2-D1b

- Change: authority_setup.host.regions = [one row for actor A (index 0), disposition failed with cleanup_reference, as the `recovery` fixture builds it]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'released setup ownership lacks successful cleanup'
- Predicted: S objects / R objects / P accepts. Matches: not a clean observation: row not well-formed for R and P general setup check.

### B2-D1c

- Change: authority_setup.host.regions = [{actor_id A, actor_index 0, required true, disposition not_attempted, operations [], ownership {}}]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B2-D1d

- Change: authority_setup.host.regions = [the D1a ready row plus succeeded cleanup operations close_original_descriptor (slot 9) and munmap (slot 11)]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B2-D1e

- Change: authority_setup.host.regions = [the D1b failed row plus a succeeded cleanup operation close_original_descriptor (slot 9)]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B2-D2a

- Change: phases[0].arrival_observed false -> true (phase b_before, actor B)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B2-D2b

- Change: phases[2].arrival_observed false -> true (phase initial_supply, actor A; predecessor is actor C)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B2-D3

- Change: phases[0].ordering (was nil) = {collection_closed_before_proceed: false, proceed_set: true, proceed_observed: false, validator_disposition: not_invoked, worker_lifetime_established: false, protocol_violations: []}
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D4a

- Change: phases[0].action_ids[0] b_read_before -> 64 bytes of 'a'
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D4b

- Change: phases[0].action_ids[0] b_read_before -> empty string
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D4c

- Change: phases[0].action_ids[0] b_read_before -> "a\u0000b" (contains NUL)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D5

- Change: extension_events (was array of 0) = nil in the typed record
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Decoded JSON: `extension_events` key is absent
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D5-jabsent

- Change: decoded JSON of the baseline with the extension_events key removed
- Built by: change applied in Rust to the decoded JSON of B2; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes; S not asked.

### B2-D5-jnull

- Change: decoded JSON of the baseline with extension_events set to JSON null
- Built by: change applied in Rust to the decoded JSON of B2; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes; S not asked.

### B2-D6a

- Change: phases[0].phase_id b_before -> 64 bytes of 'p'
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'invalid phase_id'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B2-D6b

- Change: phases[0].phase_id b_before -> empty string
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'invalid phase_id'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B2-D7

- Change: phases[0].actor_visit 1 -> 2
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: phase actor_visit disagrees with that actor's visit order; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actor_visit disagrees with that actor's visit order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D8

- Change: actors[0].visits [3] -> []
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor visits disagree with its phases'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D9a

- Change: actors[0].visits [3] -> [3, 8] (8 is the ordinal of another actor's phase)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S accepts / R objects / P accepts. Matches: yes.

### B2-D9b

- Change: actors[0].visits [3] -> [3, 9] (9 exceeds the phase count 8)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S accepts / R objects / P accepts. Matches: yes.

### B2-D10a

- Change: actors[0].index 0 -> 1 (repeats actors[1].index)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor index or identity conflict; `actor_evidence`: phase actor is absent; `actor_evidence`: actor index or identity conflict; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D10b

- Change: actors[0].index 0 -> 3 (no actor has it; actor count 3)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor index or identity conflict; `actor_evidence`: phase actor is absent; `actor_evidence`: actor index or identity conflict; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B2-D12-0

- Change: degraded as the host re-issues it: rc 1, runner_reporting_failed, error, reporting_failure{evidence_retained: true}; no defect (control for D12)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### B2-D12a

- Change: degraded as D12-0, then actors = []
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'actor form requires a bounded actors list'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B2-D12b

- Change: degraded as D12-0, then actors[0].index 0 -> 1
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B2-D12c

- Change: degraded as D12-0, then phases[0].actor_visit 1 -> 2
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'phase actor_visit disagrees with that actor's visit order'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B2-N1

- Change: preparation_failure removed (nil); nothing else changed (candidate starting point for D13)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `phase identities and ordered actions must partition the reply`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `phase_collection`: phase actions do not partition reply; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'
- Predicted: none (starting point tried for D13). Matches: n/a.

### B2-N1-D13

- Change: decoded JSON of B2-N1 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of B2-N1; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `phase_collection`: phase actions do not partition reply; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: not a clean observation: starting reply not accepted by all readers.

### B2-N2

- Change: preparation_failure removed (nil) and every phase's action_ids emptied (candidate starting point for D13)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: none (starting point tried for D13). Matches: n/a.

### B2-N2-D13

- Change: decoded JSON of B2-N2 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of B2-N2; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: yes.

### B3

- Change: none (control): actorShapeDocuments()[18], equipment/equipment_binding_refused, reason signature_invalid
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### B3-D1a

- Change: authority_setup.host.regions = [one row for actor A (index 0), disposition ready, as the `accounted` fixture builds it]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `actor_evidence`: released setup ownership lacks successful cleanup; `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'released setup ownership lacks successful cleanup'; 'released setup ownership lacks successful cleanup'
- Predicted: S objects / R objects / P accepts. Matches: not a clean observation: row not well-formed for R and P general setup check.

### B3-D1b

- Change: authority_setup.host.regions = [one row for actor A (index 0), disposition failed with cleanup_reference, as the `recovery` fixture builds it]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'released setup ownership lacks successful cleanup'
- Predicted: S objects / R objects / P accepts. Matches: not a clean observation: row not well-formed for R and P general setup check.

### B3-D1c

- Change: authority_setup.host.regions = [{actor_id A, actor_index 0, required true, disposition not_attempted, operations [], ownership {}}]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B3-D1d

- Change: authority_setup.host.regions = [the D1a ready row plus succeeded cleanup operations close_original_descriptor (slot 9) and munmap (slot 11)]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B3-D1e

- Change: authority_setup.host.regions = [the D1b failed row plus a succeeded cleanup operation close_original_descriptor (slot 9)]
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B3-D2a

- Change: phases[0].arrival_observed false -> true (phase b_before, actor B)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B3-D2b

- Change: phases[2].arrival_observed false -> true (phase initial_supply, actor A; predecessor is actor C)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `preparation refusal contains execution evidence`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### B3-D3

- Change: phases[0].ordering (was nil) = {collection_closed_before_proceed: false, proceed_set: true, proceed_observed: false, validator_disposition: not_invoked, worker_lifetime_established: false, protocol_violations: []}
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D4a

- Change: phases[0].action_ids[0] b_read_before -> 64 bytes of 'a'
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D4b

- Change: phases[0].action_ids[0] b_read_before -> empty string
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D4c

- Change: phases[0].action_ids[0] b_read_before -> "a\u0000b" (contains NUL)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D5

- Change: extension_events (was array of 0) = nil in the typed record
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Decoded JSON: `extension_events` key is absent
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D5-jabsent

- Change: decoded JSON of the baseline with the extension_events key removed
- Built by: change applied in Rust to the decoded JSON of B3; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes; S not asked.

### B3-D5-jnull

- Change: decoded JSON of the baseline with extension_events set to JSON null
- Built by: change applied in Rust to the decoded JSON of B3; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: invalid before-launch preparation failure; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S accepts / R objects / P objects. Matches: yes; S not asked.

### B3-D6a

- Change: phases[0].phase_id b_before -> 64 bytes of 'p'
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'invalid phase_id'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B3-D6b

- Change: phases[0].phase_id b_before -> empty string
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'invalid phase_id'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B3-D7

- Change: phases[0].actor_visit 1 -> 2
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: phase actor_visit disagrees with that actor's visit order; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actor_visit disagrees with that actor's visit order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D8

- Change: actors[0].visits [3] -> []
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor visits disagree with its phases'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D9a

- Change: actors[0].visits [3] -> [3, 8] (8 is the ordinal of another actor's phase)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S accepts / R objects / P accepts. Matches: yes.

### B3-D9b

- Change: actors[0].visits [3] -> [3, 9] (9 exceeds the phase count 8)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor visits disagree with schedule; `actor_evidence`: actor visits disagree with schedule; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S accepts / R objects / P accepts. Matches: yes.

### B3-D10a

- Change: actors[0].index 0 -> 1 (repeats actors[1].index)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor index or identity conflict; `actor_evidence`: phase actor is absent; `actor_evidence`: actor index or identity conflict; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D10b

- Change: actors[0].index 0 -> 3 (no actor has it; actor count 3)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: actor index or identity conflict; `actor_evidence`: phase actor is absent; `actor_evidence`: actor index or identity conflict; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R objects / P objects. Matches: yes.

### B3-D12-0

- Change: degraded as the host re-issues it: rc 1, runner_reporting_failed, error, reporting_failure{evidence_retained: true}; no defect (control for D12)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### B3-D12a

- Change: degraded as D12-0, then actors = []
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'actor form requires a bounded actors list'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B3-D12b

- Change: degraded as D12-0, then actors[0].index 0 -> 1
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'actor index disagrees with order'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B3-D12c

- Change: degraded as D12-0, then phases[0].actor_visit 1 -> 2
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_reporting_failed, exit code 1
- P: objects — 'phase actor_visit disagrees with that actor's visit order'
- Predicted: S accepts / R accepts / P objects. Matches: yes.

### B3-N1

- Change: preparation_failure removed (nil); nothing else changed (candidate starting point for D13)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `phase identities and ordered actions must partition the reply`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `phase_collection`: phase actions do not partition reply; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'phase actions do not partition the ordered steps'
- Predicted: none (starting point tried for D13). Matches: n/a.

### B3-N1-D13

- Change: decoded JSON of B3-N1 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of B3-N1; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `phase_collection`: phase actions do not partition reply; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'phase actions do not partition the ordered steps'; 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: not a clean observation: starting reply not accepted by all readers.

### B3-N2

- Change: preparation_failure removed (nil) and every phase's action_ids emptied (candidate starting point for D13)
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: none (starting point tried for D13). Matches: n/a.

### B3-N2-D13

- Change: decoded JSON of B3-N2 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of B3-N2; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: accepts — `process_disposition` no_worker, `disposition_integrity` null, issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: yes.

### O0

- Change: none (control): replyFixture(), the first ordinary shape document; execution_form nil
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` unconfirmed, `disposition_integrity` "valid", issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### O0-D11

- Change: preparation_failure = {resolved_plan, inconsistent_assignment, actor_id A, binding_ref 0, reason} added
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: objects — `actor evidence in ordinary reply`
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: ordinary reply carries actor authority evidence; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: accepts (empty list)
- Predicted: S objects / R objects / P accepts. Matches: yes.

### A0

- Change: none (control): actorShapeDocuments()[0]; preparation_failure nil
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: accepts — `process_disposition` per_actor, `disposition_integrity` "valid", issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` validator_unavailable, exit code 1
- P: objects — 'b_read_before: file/exec attempt without path diagnostics'; 'c_read_before: file/exec attempt without path diagnostics'; 'b_read_after: file/exec attempt without path diagnostics'; 'c_read_after: file/exec attempt without path diagnostics'
- Predicted: none (starting point tried for D13). Matches: n/a.

### A0p

- Change: decoded JSON of A0 with reply_fixtures::attempt_paths(requested_path) added as attempt.path_diagnostics on each file step (control for A0p-D13)
- Built by: change applied in Rust to the decoded JSON of A0; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: accepts — `process_disposition` per_actor, `disposition_integrity` "valid", issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` validator_unavailable, exit code 1
- P: accepts (empty list)
- Predicted: control: all accept. Matches: yes.

### A0-D13

- Change: decoded JSON of A0 (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of A0; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: accepts — `process_disposition` per_actor, `disposition_integrity` "valid", issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` validator_unavailable, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'b_read_before: file/exec attempt without path diagnostics'; 'c_read_before: file/exec attempt without path diagnostics'; 'b_read_after: file/exec attempt without path diagnostics'; 'c_read_after: file/exec attempt without path diagnostics'; 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: not a clean observation: starting reply not accepted by all readers.

### A0p-D13

- Change: A0p with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of A0p; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: accepts — `process_disposition` per_actor, `disposition_integrity` "valid", issues: none; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` validator_unavailable, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'invalid before-launch preparation failure'
- Predicted: S not expressible / R accepts / P objects. Matches: yes.

### AR

- Change: none (control): actorShapeDocuments()[14], the launch-refused reply the first baseline is derived from; preparation_failure nil
- Built by: typed Swift record, encoded to porcelain bytes, decoded in Rust
- S: accepts (no throw)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- P: objects — 'b_read_before: file/exec attempt without path diagnostics'; 'c_read_before: file/exec attempt without path diagnostics'; 'b_read_after: file/exec attempt without path diagnostics'; 'c_read_after: file/exec attempt without path diagnostics'; 'released setup ownership lacks successful cleanup'
- Predicted: none (starting point tried for D13). Matches: n/a.

### AR-D13

- Change: decoded JSON of AR (preparation_failure key absent) with "preparation_failure": null
- Built by: change applied in Rust to the decoded JSON of AR; S could not be asked
- S: not asked (the typed record cannot hold this change)
- R: objects — `process_disposition` withheld, `disposition_integrity` "invalid", issues: `actor_evidence`: released setup ownership lacks successful cleanup; `admission_problem`: null; `reply_version`: supported; `run_flow::admit_reply`: admitted
- R envelope (rendered as the existing tests do, `execution_envelope(complete_execution(execution_data(reply)))`): `data.runner_result` published, equal to the typed reply; `result.ok` false, `normalized_outcome` runner_failed, exit code 1
- Note: the typed Rust record re-serializes to JSON that differs from the JSON given to P (the null key is dropped), so R judged the record without the key and P judged the JSON with the null.
- P: objects — 'b_read_before: file/exec attempt without path diagnostics'; 'c_read_before: file/exec attempt without path diagnostics'; 'b_read_after: file/exec attempt without path diagnostics'; 'c_read_after: file/exec attempt without path diagnostics'; 'invalid before-launch preparation failure'; 'released setup ownership lacks successful cleanup'
- Predicted: S not expressible / R accepts / P objects. Matches: not a clean observation: starting reply not accepted by all readers.

## Could not be run

Every candidate D1 to D13 was run in at least one form. What was not observed, or not observed cleanly:

- **D13, S.** S was not asked: the typed Swift record cannot hold a JSON null, and no way was used to hand S JSON. The null was applied to decoded JSON for R and P only.
- **D13, starting point.** The two Swift shape documents first tried as "a valid actor-form reply" are not accepted by all three readers unmodified: `A0` (`actorShapeDocuments()[0]`) is accepted by S and R and refused by P (four `file/exec attempt without path diagnostics`); `AR` (`actorShapeDocuments()[14]`, the `recovery` fixture) is accepted by S and refused by R and P (`released setup ownership lacks successful cleanup`). `A0-D13` and `AR-D13` are therefore not clean. Two clean starting points were made instead: `Bn-N2` (a baseline with `preparation_failure` removed and every phase's `action_ids` emptied; accepted by S, R and P) and `A0p` (A0's JSON with attempt path diagnostics added; accepted by R and P, S not asked). `Bn-N2-D13` and `A0p-D13` are the clean observations.
- **D13 and `D5-jnull`, same content.** For a JSON null the Rust typed record holds `None` and re-serializes without the key, so R and P did not judge byte-identical content on those rows: P saw the null, R saw the record without it. That is the candidate itself for D13; it is recorded on each such row.
- **D5, S on the JSON forms.** S was asked only about the typed `extension_events = nil` form (`Bn-D5`), which the porcelain round trip delivers to R and P as an absent key. S was not asked about `Bn-D5-jnull` and `Bn-D5-jabsent`.
- **D1a, D1b.** The region rows copied from the Swift fixtures (`accounted`'s ready row, `recovery`'s failed row) are refused by R's and P's general setup check (`released setup ownership lacks successful cleanup`), so P's objection there is not about the preparation failure. The clean D1 observations are `Bn-D1c`, `Bn-D1d` and `Bn-D1e`, where R's only issue is the preparation-failure one and P returns no error.
- **D12, host path.** The degraded reply was made in test code by the same field assignments `pwRunnerReportData` makes (`PWRunnerService.swift:136-144`), on an unmodified baseline. The host's own re-issue path was not run.
- **Real driver replies.** The `actor-review-*.pwp` replies the existing cross-reader test uses need the signed app's worker; no app was built or signed, so none was used. Every reply here is a constructed shape document or a change to one.
- **The envelope.** `data.runner_result` was observed in an envelope rendered by the test helpers (`execution_data`, with the test client run), not in the output of a controller run. All replies here have a `normalized_outcome` other than `finished`, so an objected-to reply with `result.ok: true` was not observed.
- **Variants not tried.** D7 was run only as `phases[0].actor_visit` 1 → 2; D9 only by appending 8 or 9 to `actors[0].visits`; D10 only as index 1 or 3; D11 only on `replyFixture()`; D2 only on phases 0 and 2.

## Divergences observed

Replies on which the observed final judgments differ. `Bn` means the same result on B1, B2 and B3.

| Reply | S | R | P | Candidate |
| --- | --- | --- | --- | --- |
| Bn-D1c, Bn-D1d, Bn-D1e | objects | objects | accepts | D1 |
| Bn-D2a, Bn-D2b | objects | objects | accepts | D2 |
| Bn-D3 | accepts | objects | objects | D3 |
| Bn-D4a, Bn-D4b, Bn-D4c | accepts | objects | objects | D4 |
| Bn-D5 | accepts | objects | objects | D5 |
| Bn-D6a, Bn-D6b | accepts | accepts | objects | D6 |
| Bn-D7 | accepts | objects | objects | D7 |
| Bn-D8 | accepts | objects | objects | D8 |
| Bn-D9a, Bn-D9b | accepts | objects | accepts | D9 |
| Bn-D10a, Bn-D10b | accepts | objects | objects | D10 |
| O0-D11 | objects | objects | accepts | D11 |
| Bn-D12a, Bn-D12b, Bn-D12c | accepts | accepts | objects | D12 |
| Bn-N2-D13, A0p-D13 | not asked | accepts | objects | D13 |
| A0-D13 | not asked | accepts | objects | D13, starting reply already refused by P |
| A0 | accepts | accepts | objects | none: unmodified Swift shape document `actorShapeDocuments()[0]` |
| AR | accepts | objects | objects | none: unmodified Swift shape document `actorShapeDocuments()[14]` (`recovery`) |

No divergence on: B1, B2, B3 and Bn-D12-0 and Bn-N2 and O0 (all accept); Bn-D1a, Bn-D1b and Bn-N1 (all object); Bn-D5-jnull, Bn-D5-jabsent, Bn-N1-D13 and AR-D13 (R and P object, S not asked); A0p (R and P accept, S not asked).

Every clean observation agrees with the comparison's predicted judgment for its candidate. No observation contradicts a prediction.
