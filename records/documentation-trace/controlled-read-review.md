# Controlled read: source and independent-observation trace

Initial source review on 2026-11-15, from starting commit
`2fcf9dbc9f08b1643426b4cf9b9b32e3782c86cc`, for exercise 3 of
[the documentation trace plan](../../DOCUMENTATION-TRACE-PLAN.md).
No live specimen, checker control or test suite was executed for this review.
Descriptions of controls below are check-reading evidence; they do not credit
historical observations as current executions. Final routed-document reading
and acceptance remain with the plan executor.

## Changed item and commitments to examine

A change to `attempt_file_read_fresh`, the shared-memory read projection, the
typed reader, the read publisher or the independent observer can require
review even when help and published request bytes stay identical. The relevant
commitments are:

| Identity | Complete-statement owner and scope | Intended reading home |
| --- | --- | --- |
| `request.specimen.emit_test_input` | [Request surface](../../docs/contract/10-request.surface.md): exact developer command, positional binding, complete publication and failure disposal; applies to CLI publication, not host admission. | REQUEST |
| `request.specimen.read_input` | Same source: separately authored identity-free request body, compared with publication independently of native effects. | REQUEST |
| `probes.step`, `probes.query`, `probes.attempt` | [Probe surface](../../docs/contract/12-probes.surface.md): query and attempt are separately admitted operands; `read_fresh` has its own operation meaning. | REQUEST |
| `steps.fresh_read` | [Step surface](../../docs/contract/31-steps.surface.md): open, descriptor stat, read, close, identity and bytes, with absent unreached observations. | RESPONSE |
| `steps.assessment.fresh` | Same source: acquisition during the released action and publication of reached operations on completed-slot publication. | RESPONSE |
| `steps.assessment.fresh_read_aggregate` | Same source: worker/host completed aggregate projection, for each phase and associated step, only for worker-sourced `file/read_fresh` with its fresh-read record present. | RESPONSE |
| `steps.assessment.assembly` and ordering conditions | Same source: independent provenance, unavailable channels and the bounded collection/release claim. | RESPONSE |
| `diagnostics.execution.reply_checks`, `.families`, `.outer_result` | [Diagnostics surface](../../docs/contract/41-diagnostics.surface.md): native observations have reply-wide validation scope in ordinary semantic replies; worker lifecycle validation and outer result selection are separate. | RESPONSE |

The aggregate rule inherits `bind.p: reply.phases`, `bind.s: reply.steps` and
`match.s: reply.steps[s].phase_id == reply.phases[p].phase_id` from
`steps.assessment`. Its ordered cases preserve open failure first, then stat,
read and close failure, each with and without nonzero errno; only the final
fallback reports `ok`, rc 0 and null errno. That applicability and order belong
beside the rule after routing. A successful aggregate does not establish the
identity or content correspondence supplied by the harness's independent
samples.

## Forward path: publication to observation

[`render_template`](../../controller/src/test_input.rs) accepts exactly
`read --target PATH`, requires a nonempty absolute UTF-8 path without NUL,
requires a bound identity, parses the embedded
[read body](../../controller/src/test_inputs/read.json), and checks all assigned
positions before mutation. There must be no preexisting `contract`, exactly
one probe, and `$EFFECT` at both target positions. It inserts the compiled
identity and assigns the literal caller string at those two positions. Other
members remain as embedded. `emit_template` requires all writes and flush to
succeed; a complete-looking object from a failed flush is unusable. The
identity gate here does not run host grammar admission or inspect the target.

The published request uses `file-read-data` with a path query and a separate
`file/read_fresh` attempt. The harness may deliberately cross those operands.
The query's answer does not identify the descriptor opened by the attempt.

[`main`, `run_attempt` and `attempt_file_read_fresh`](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
place the attempt inside the phase loop after the release wait. In the ordinary
applied path this follows successful sandbox application; actor setup retains
its declared applied/unapplied distinction. The read action calls fresh
`open(O_RDONLY | O_CLOEXEC)`, `fstat`, one read bounded by
`PW_SHM_FRESH_READ_BYTES`, and one close. Failed open prevents subsequent calls.
After successful open, stat failure does not prevent read and close, and later
successful bytes remain recorded beside an earlier failure. The aggregate
preserves the first failure in that call order.

`run_attempt` release-publishes `slot.completed` only after the action returns.
[`ActorSession.collectOutput`](../../runner/Sources/PWRunnerCore/ActorSession.swift)
acquire-loads that marker and does not decode unpublished payload.
[`decodeFreshRead`](../../runner/Sources/PWRunnerCore/CWorker.swift) supplies
identity only after successful stat, content only for a valid nonnegative
bounded read, and no stat/read/close record after failed open.
[`buildAttemptResult` and `buildStepResults`](../../runner/Sources/PWRunnerCore/CWorkerStepResults.swift)
attach detailed records only for completed supported attempts, retain raw
aggregate rc, convert errno zero to null and identify the result as
worker-sourced. Missing or incomplete publication yields a synthetic
`no_completed_result`; it cannot establish whether a native operation occurred.

## Reverse path: returned record to its independent support

[`PWRunnerFreshRead`](../../runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift)
and the generated [porcelain writer](../../runner/Sources/PWRunnerCore/PWPorcelainRecords.swift)
carry the typed record. The controller's generated
[porcelain reader](../../controller/src/porcelain_records.rs) retains bytes and
projects content as hexadecimal.
[`fresh_read_problem`](../../controller/src/porcelain_native.rs), called by
[`admit_reply`](../../controller/src/porcelain_admission.rs), independently checks
applicable operation/provenance, native ranges and errno presence, absent
unreached fields, stat/identity agreement, read count/content length, and the
first-failure aggregate. This checks internal consistency without reopening the
path. Findings do not repair carried observations. The constructed
`typed_fresh_read_preserves_bytes_and_first_failure` and
`typed_missing_fresh_payload_is_invalid_and_exec_absence_remains_unknown`
controls pin parts of that distinction.

The external checker obtains different evidence:

- [`observe_target`](../../tests/lib/file_observation.py) opens its own
  descriptor, reads identity with `fstat`, reads full content through that same
  descriptor, and retains full and bounded-prefix lengths/digests. Its
  `target_changes` checks sampled identity, metadata and content differences.
- [`test_input.run_case`](../../tests/suites/witness_contract/test_input.py)
  owns creation, in-place changes, separately prepared replacement and saved
  request bytes. Publication preflight precedes sampling and derivatives.
- [`check_test_input.evaluate`, `step_rows` and `operands_match`](../../tests/suites/witness_contract/check_test_input.py)
  compare independently authored requests, recorded process and envelope exit,
  producer identity, worker/phase completion, exact query and attempt operands,
  native query answer, established order, syscall observations, descriptor
  identity and returned prefix. The identity/content comparisons require usable
  before/after samples and the intended association. Its independent bound is
  64; it is not loaded from the production limit.
- [`consumer`](../../tests/lib/consumer.py) independently decodes retained host
  bytes and validates their relationship to the controller projection;
  [`validate_fresh_read`](../../tests/lib/extension_evidence.py) owns internal
  native-record checks. A coherent reply describing the wrong fixture may pass
  those checks and still fail the separate correspondence rows.
- [`test_input_views.distinction_rows`](../../tests/suites/witness_contract/test_input_views.py)
  compares a fixed vocabulary of request, operand, query, attempt, descriptor,
  content, external sample and ownership facts against independently authored
  equal/different expectations. `write_report` saves this as
  `distinctions.json` beside a run's checker output. This review creates no such
  native run artifact.

## Three bounded differences

The maintained [controlled-read account](../../tests/suites/witness_contract/README.md#controlled-read-input)
and read checker provide these useful exercises. They describe the authored
workload and checks, not newly observed results here.

| Comparison | Independently expected difference | What the returned read cannot establish |
| --- | --- | --- |
| `allowed_a` to `replaced_a` | Saved request bytes stay identical; descriptor inode and sampled inode change, while bytes and selected metadata remain equal. The old object is parked and sampled separately. | A path string or content digest alone cannot distinguish the generations. |
| `replaced_a` to `suffix_a` | Same descriptor generation and returned 64-byte prefix; the independent full-file digest changes beyond that prefix. | The bounded read does not observe the changed suffix. |
| `suffix_a` to `bound_a` | Same returned prefix/count; independent full length and digest change as the suffix is removed. | A full bound of returned bytes does not establish EOF. |

The controls explicitly accept swapping indistinguishable read records in the
suffix/bound passages and reject stale whole captures, wrong generation, absent
parked samples, stale full-file samples and changed prefix/count evidence.
See `boundary_controls` in
[test_input_controls.py](../../tests/suites/witness_contract/test_input_controls.py).
Before/after equality establishes sampled stability, never continuous stability.
The observer's full-file sample does not imply that the worker read the whole
file.

The crossed `read-ba` row adds an independent limit: query B denies while the
attempt opens A successfully. Equal A/B content leaves the descriptor identity
as the observation distinguishing the opened object. The query records retain
their own operand and native answer. `query_first` states bounded temporal
ordering; it does not establish prediction/enforcement agreement or sandbox
cause. The returning-actor derivative uses its own samples and ownership checks;
equal policies do not establish policies reached distinguishable intended
actors, and these finite rows do not establish execution-form equivalence.

## Review outcome and navigation recommendations

The source and maintained checks support retaining the present meanings. A
change to acquisition timing, syscall order, publication eligibility, projection
or observer descriptor use would require review of these commitments even if
`test-input` output and help were unchanged. No new help association is needed.

The RESPONSE reading exercise should connect one saved request to replacement
and suffix observations and separate native record consistency from external
correspondence. It can state the independently expected difference table above
as a workload explanation without presenting invented captured output.

WORKER's `Acquisitions inside attempts` commitment list should include
`probes.attempt`, `steps.fresh_read`, `steps.assessment.fresh`, and
`steps.assessment.fresh_read_aggregate`. `Native observations and publications`
should link at least `steps.assessment.assembly` and
`steps.assessment.fresh`, alongside the existing lifecycle/publication account.
These links name what the sections explain; they do not confer test coverage.

The existing `steps.assessment.fresh` owner honestly says fresh-read sequencing
is source-supported there and its cited constructed controls concern fresh
writes. Preserve that limit; do not relabel it as executed fresh-read support.
The aggregate's owner is also `source_read`. The controlled-read suite supplies
additional finite correspondence checks, but a source/check index should name
that separate relationship and retain its workload scope. Final acceptance
must verify these routes through the actual generated commitment lists and
destinations; this initial review uses authored node identities so that it
survives relocation.
