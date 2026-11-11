# Initial stage-four guide workflow audit

The guide case failed at its first external-runner list-envelope assertion. The
actual `runner list` envelope has `kind: "runner_registry"`; the new harness
expected `runner_list`. The public producer is correct. The three corresponding
harness expectations need the private correction in `guide-list-kind.patch`.
The create, two refusal, positive capture and helper steps completed before this
failure. They supply the bounded observations below; the complete guide case
remains failed and needs a complete replacement run.

## Receipt and source scope

Canonical run `20261111T175904Z_4ee0cfa5`, local
`tests/out/runs/contract-stage-four-workflows-20261111`, is terminal with 16/16
completed, 12 pass and 4 fail. `witness_contract/guide_workflows` failed with zero
system sleep. App integrity reports valid before and unchanged. Root owns the
other failures and whole-run acceptance. The separate `runner_byoxpc/default_location`
report passes; this audit read that report only and grants it no substitute
credit for the unreached guide installation.

The executed guide snapshot is SHA256
`aa24c71c67019804cf2d6b34655d23cc4271939797b94788b8110aff0558b01f`.
The retained version identifies build 1337, commit
`5c1c63dc7bbcf07188f83924be1367423ea188b3`, describe
`v0.3.7-3-g5c1c63dc-dirty`, contract
`development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28`.
Worker evidence carries identity
`764ca292609245dd223fbc25791934cc24773e8db36fdc931b3c4c13042806a2`.
At audit time the current source and staged guides both have newer SHA256
`31944ef9cd04d131e1cf2314ba1bb3e0f67322a4f58a5a828bcb08136f3fa3a4`;
the observations here remain bound to the retained initial input. The workflow
asserted source/staged byte equality before its first command.

I read the full executed workflow and ownership-control sources, the relevant
session owner/adoption/cleanup, entitlement/equipment and registry helpers,
command capture helper and worker-exit witness. I read the guide's selected
sections and receiver/attempt explanation, owning suite account, selection
checklist, and all seven runner-management envelope constructors. The executed
workflow preimage is preserved privately as `guide_workflows.before.py`, SHA
`5765db308e8155f05249a010c841e07a5ecf79c43833511abfb97f7dc8238d8e`.
This is read-only review and standard-library receipt/hash inspection: no app
commands, tests, product-module imports, resource cleanup or shared edits by this
auditor. Source hashes alone do not claim every source line was reviewed.

## Exact displayed-command coverage

Eight fences were reached: two Quick start fences; four capture-refusal/repair
fences; the direct helper; and the initial external list/reconcile fence. Their
raw contents each occur exactly once in the retained guide and match their
recorded hashes. Joining their 17 source fragments reconstructs those fences,
with only the actual APP setup substitution. The eighteenth shell capture repeats
the create guard against the existing target. Every fragment returned zero with
no harness timeout. The two refused native invocations separately retained exit
1 in their PW_EXIT files; the successful compound recipe status does not erase
those refusals. Capture scripts retain the guide text plus the reviewed shell
state/umask bookkeeping. IDENTITY and ENT substitutions were not reached.

The complete target was 13 fences, 32 source fragments and one extra guard
execution. `request-hashes.json` and `workflow-result.json` were not reached.
The four submitted request hashes instead join the durable invocation entries
and retained `work-records.json`; all listed work-record hashes were checked.
The typo-to-correct-spelling and corrected-spelling-to-nonce JSON relations were
independently compared and change exactly those policy fields.

## Native observations that completed

| Step | Retained observation and consequence |
| --- | --- |
| Ordinary create | Target absent before submission; worker 70075 reports completed `file/create`, `rc: 0`, `outcome: ok`, applied policy and host-confirmed reap/exit 0. Independent target observation is a regular empty mode-0600 file, inode 198444628. Envelope and saved command exit are `finished`/0. |
| Existing-target guard | The repeated guard emitted its refusal text and preserved the result bytes, result/exit mtimes and target identity/content observation. No additional submitted request was recorded. |
| Misspelled flag | Exit 1 and `bad_request`; exact `unknown_field` path `["policy","capture_compiled_profiel"]`. Host report has no worker subprocess, steps or phases; target remains absent. |
| Corrected flag, absent nonce | Exit 1 and `bad_request`; exact `invalid_capture_nonce` path `["policy","capture_nonce"]`. Again no worker subprocess, steps or phases; target remains absent. |
| Positive capture | Worker 70117 reports completed create/application and host-confirmed reap/exit 0. Target becomes an independent regular empty mode-0600 file, inode 198444762. Receipt is `captured`, producer worker, stage before_apply, nonce `436767fc9f32159deb01a6feb13c1a7b`, source length 27 and source SHA `c3f48dc83eca4ac705acbf9094416e239dda782b96cab885e8f7151c653474b3`, parameter count 0. Decoded bytecode is 492 bytes with SHA `b2056ef25b6c4e72bcd45bb018452bde93d05afcbdb9813fee8698551cf397e0`; nonce, PID, source and payload identities were recomputed/joined. |
| Direct helper | `sbpl_check`, exit 0, compile `{stage: compile, ok: true, error: null}` and the same policy source hash. Both earlier files retain identical before/after file observations. This is compiler evidence for the direct helper request. |

Both successful create steps have `sandbox_check.result_source: synthetic`,
`outcome: prediction_unavailable`, `missing_reason: query_not_requested`,
`native_rc: null`, `rc: -1` and a host planning error naming the absent path.
Their comparisons carry `observation: succeeded`, basis
`completed_worker_status`, operation relation `unresolved`, target relation
`same_submitted`, order `unestablished`, and sole limitation
`query_plan:path_unresolved_at_planning`. Each main phase reports collection and
validator disposition `not_needed`; no validator subprocess was required. These
actual values support the guide's absent-path explanation at this boundary.

All four captures are admitted with one granted acquisition, submission
`invoked`, terminal `runner_reply`, client exit 0, complete retained host frames,
no capture/truncation/delivery error, and controller outcomes matching their
host replies. The refusal requests were invoked at the host interface before
host admission rejected them; `invoked` does not mean a worker was spawned.
Received/retained wire lengths and decoded hashes are recorded in observations.
Successful creates have `clean_exit` diagnostics with valid disposition and no
issues; refused requests have `no_worker` and no disposition issues.

## Failure boundary and cleanup

The real initial registry output is successful `runner_registry` with empty
`runners` and `pending_cleanup`. Reconcile independently returned successful
`runner_reconcile`, with empty records/candidates/inspection_errors and the
normal default registry path. The harness refused only the list kind before it
could evaluate the empty-registry prerequisite. No stage was adopted: outer
`session.external` is null; no install, verify, selected BYOXPC run, validation,
removal or equipment readback occurred.

The outer cleanup retains four disposition receipts: two confirmed worker reaps
and the two exact pre-worker host refusals. Its final receipt has
`cleanup_verified: true`, `removed: true`, no cleanup error and no uncertain
command. The recorded work path `/private/tmp/pw-guide.Pxx6ve` is absent at this
audit. Source-before and source-after inventories equal the durable source
inventory. This proves the exercised outer cleanup completed; nested external
cleanup awaits the replacement native workflow.

## Constructed controls

Both constructed-control completion files exist before the failed native step.
The ten ownership observation groups cover foreign/existing owners, dangling
auxiliary receipt refusal, immutable path/inode/default-registry checks,
durable-ahead uncertainty and recovery, a single simulated interrupted
submission with an independently written effect, injected consumer admission
followed by actual reap/refusal predicates, service/plist/registry absence,
incomplete install ownership, interrupted/final-receipt deletion recovery, and
foreign installed/pending rows. Six fake-command receipts retain 19 calls across
the absence variants. Those commands use the existing fake tool implementation;
the retained completion groups join source assertions that observe preserved
sentinels, zero unwanted calls, retained owners and successful neighbors.

These controls use real file operations with constructed OS/command inputs.
Disposition controls inject consumer admission explicitly. Their intentional
retained-error fixtures are disposed by fixture teardown after observation;
they establish control behavior, not a native lost reply, cancellation event or
live external-runner removal in this guide case.

## Narrow correction and remaining verification

| CLI command | Actual constructor kind | Harness expectation |
| --- | --- | --- |
| list (before/install/remove positions) | `runner_registry` | Correct all three `runner_list` literals. Actual initial output confirms this. |
| install | `runner_install` | Matches source; unreached here. |
| status | `runner_status` | Matches source; unreached here. |
| verify | `runner_verify` | Matches source; unreached here. |
| validate | `runner_validate` | Matches source; unreached here. |
| remove | `runner_remove` | Matches source; unreached here. |
| reconcile | `runner_reconcile` | Matches source and actual initial output. |

The shared fake OS tool emits deliberately partial `result`/`data` objects,
without a `kind` field. Existing helper controls consume that partial shape;
there is no contrary fake kind to change or whole-envelope fidelity claim.
`guide-list-kind.patch` changes the three owning literals only. It was AST-parsed
privately, not executed. Root should rerun the complete guide case against the
final source/staged guide and matching signed build, retaining this original
failure. Install/verify/run identity joins, entitlements, validate counts, service,
plist and both registry-collection absence, nested cleanup and all 13 fences
remain the replacement run's obligations.

`observations.json` and `source-artifact-manifest.json` are compact derived
receipts, not raw evidence archives. Original tests/out and /private/tmp paths
are local/gitignored and remain subject to ordinary retention. No retention
marker, raw-artifact copy or cleanup bypass was introduced.
