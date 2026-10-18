# Worker account: five documentation corrections

Associated plans: [worker redesign](../../WORKER-REDESIGN-PLAN.md) and
[worker documentation](../../docs/WORKER-INST-DOC-PLAN.md).
Base revision: `f85c7b094d75bf72931cd4856cb4ad086da20cbe`.
Status: all five corrections implemented and validated. Documentation register
rows 25 and 27 are closed at this scope; unrelated findings remain unchanged.

## Corrections and evidence

| Finding | Before | Corrected account and support |
| --- | --- | --- |
| Compiler outputs | S26a/S26b were acquired “Before compilation (compile boundary).” | Both now say “On compilation return, before apply.” The worker's main function receives the profile and error out-parameter from `sandbox_compile_string` before either capture or error reporting. This dates reference availability, not private allocation. |
| Implementation ownership | W24 cited the extension session, W30 the issuer, and W55 host comparison. | W24 cites host `runCWorker`; W30 cites worker `prepare_extension` and `attempt_extension`; W55 cites controller `attach_sandbox_logs` and `finish_sandbox_log_capture`. The related W49 drain citation also now names `attempt_exec_spawn` and `drain_one`. |
| Irrelevant checks | Row-wide mandatory citations included bare-deny for host arrays, optional parameters/capture and inherited-state facts, and an existing-file control for absent-file creation. | Explicit source-only rows are permitted. Relevant existing controls replace unrelated citations: parameter round trip, compiler failure, live capture, absent-target creation, host setup/descriptor controls and controller association. Each retained worker check names its assertion scope. No new runtime coverage is claimed. |
| Unidentified L | “Recorded production launch observation” supplied neither an execution identity nor a post-refactor applicability account. | A fresh launch-inventory execution is identified by run, source and app identities, inputs, observer commands, selected raw captures and artifact hashes in the durable [L receipt](../../docs/worker-launch-observation.json). The worker prose states both observations and applicability limits. |
| Mixed gating column | “Sandbox-gated” mixed placement, allocation internals, observed outcomes and old review notes. | The column is removed. “When” owns call-site placement; scoped assertions and identified L carry observed facts. Useful allocation/inspection limits and setup caveats remain in notes. Historical pass-status comments are removed from current behavior documentation. |

The architecture manifest is now documentation format 4. Empty check lists are
allowed only for worker-capability rows and render as “Source only; no assertion
cited.” Nonempty lists still require a test or rule; each worker check requires
nonempty scope text. Other graph and limit requirements are unchanged. New
controls exercise source-only acceptance, missing/blank scope rejection, and
rejection of a fixture-only list. Definition resolution remains mechanical;
assertion relevance and applicability remain reviewed judgments.

The generator was run after editing its inputs. It produced the worker table,
dot and SVG; no generated copy was edited directly. This correction changes no
runtime source, wire format, worker identity or cleanup behavior. It resolves
the reported citation/timing defects without selecting a broader holder/object
or resource-role model.

## Launch observation

Run `20261018T223601Z_85d8418b`, from
`tests/out/runs/worker-doc-launch-20261018`, passed the requested launch inventory
and its contaminated-worker dependency, 2/2 with no skips or unrun cases. The
signed app was valid and unchanged; its complete inventory equals that of the
accepted validator-default receipt rerun. Runtime sources at the base revision
match implementation `a458b28`; intervening changes under those directories are
plans only. The original build stamp is retained, not replaced by this review's
source revision.

The two separate workers used empty allow-default plans and the existing
pre-ready/post-apply sleep overrides. Both showed numeric descriptors 0–4,
read/write `/dev/null` stdout/stderr, cwd `/`, and matching plain/environment
`ps` captures. Both `vmmap` commands succeeded; both `lsmp` commands refused task
inspection. Final replies and subsequent process observations establish clean
exit, publication and reap. The pre-ready worker retained readiness `EPIPE`.
Those facts are extracted from the raw captures; the test's successful-command
assertions alone do not establish a particular descriptor or environment set.

The durable receipt preserves selected raw text, exact specimen/command and
worker evidence, source hashes and hashes of 59 original artifacts. Complete
raw output is gitignored and local to this checkout; the run is pinned in
`tests/RETAINED.json`. Its receipt explicitly excludes within-process change
measurement, mapping-object identification, a denied-policy gating experiment,
and signal/umask/resource-limit or extension-worker censuses. Reuse requires
review of behavior, configuration and identity, rather than an identity-only rule.

## Validation account

The first documentation run, `20261018T224032Z_78019c62`, passed
`limits_documentation` and failed `architecture_documentation` and
`generator_contract`. Assertion-scope edits made after generation left stale
copies during that development run. The new caption also said “definition
resolution” where the caption control requires “definitions.” The original
failed run is preserved without passing credit. Regeneration and corrected
caption wording precede the final run.

The first corrected run, `20261018T224517Z_38c3a586`, passed all three cases.
Final semantic review then removed the mapping-identification citation from W4
and the unrelated issuer-stdio citation from N4, replaced the session-descriptor
check with its cleanup control, and made the host setup assertion scopes more
precise. `pre-review-source.json` preserves that earlier passing snapshot.

The final run, `20261018T224844Z_c512fd20`, from
`tests/out/runs/worker-doc-corrections-reviewed-20261018`, passed all three cases:
`source_drift/limits_documentation`, `source_drift/architecture_documentation`
and `source_drift/generator_contract`, with no skips, unrun cases or harness
errors. It supplies all final documentation acceptance credit.
`validation-source.json` identifies the tested generator, manifest, generated
copies, observation receipt and changed check definitions. Their hashes still
match after testing. Later plan statuses, this report, run summaries and retention
entries are acceptance bookkeeping.

Scoped local-link/anchor and whitespace checks passed. Architecture, limits,
build and worker-identity generator checks passed. SVG comparison after removing
changed tooltip attributes found identical visible text and geometry; the other
four architecture graph definitions are unchanged. All 59 original L artifact
hashes and both worker-reported identities match its durable receipt. The final
inventory has 24 explicitly source-only rows and 141 scoped check citations.
Raw validation runs, including the original failures, are pinned for retention;
`validation-runs.json` retains their result accounting and artifact identities.

No app rebuild or full runtime battery is needed for these documentation and
generator changes. Existing check definitions were reviewed for assertion scope;
citing them does not claim they were all freshly executed.
