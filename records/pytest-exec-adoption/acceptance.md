# One-family adoption decision

Prepared by Codex, 2026-10-30. Scope: `runner_c_worker_harness/exec_control_states`
(F), on `adoption/pytest-exec-family` in
`/private/tmp/pw-pytest-exec-candidate-20261030`. The accepted checkout remains at
`77eb987554eef10ffa3371ffb21b235097562a78`; no merge or native production/oracle
change is part of this result. The authorization amendment was committed first
at `8fd2c825` in the planning worktree, before candidate implementation.

## Disposition

Recommend accepting this family after review of the committed candidate. Named
variants and explicit phases improve actual diagnosis; family logic is easier
to locate and the parallel mutation/expectation maps and shell test loop are
removed. The evidence supports this bounded change without a claim of fewer
lines, a productivity benchmark or eventual adoption of another family.

Pytest owns collection, item order, ordinary fixture lifecycle and phase reports.
PW still owns public whole-family selection, applicability, app integrity, checkout
claims, durable reconciliation, command ownership, recovery and retention. Its
supervisor interprets exported phase evidence and commands; it does not schedule
pytest items. The additional integration is substantial and remains a maintenance
obligation. This result does not change the earlier distinction between boundary
feasibility, maintenance benefit and the value of replacing the whole harness.

Implementation and acceptance are complete in the candidate, subject to the
specific verification identities below. The accepted route remains available
unchanged in its original checkout. No routine stage authorization remains pending.
The plan and associated records remain as the review package; retire them together
when this change is accepted or rejected under CONTRIBUTING.md. This leg does not
perform that later merge or delete evidence on the assumption of acceptance.

## Source and evidence boundaries

The test environment is Python 3.14.9 at the repository's pinned Homebrew path,
pytest 9.0.2, and the exact five wheels in `tests/requirements-pytest.lock`.
`tests/pytest.ini` uses fd capture/importlib mode; external plugin autoload, ambient
Python paths and cache writes are excluded. Packages are explicitly provisioned
into a verified isolated target. Collection does not install them.

`evidence-index.json` records full source commits, output paths, owner/run IDs,
pin declarations, key hashes and complete inventory digests. `native-comparison.json`
records equality of the accepted/candidate 58-attempt ledgers, C/header closure,
six mutation bodies and six designated rejection assertions. The native fixture,
golden, runner and application sources are unchanged. `walkthrough.json` records
the emitted phase outcomes, source-receipt checks and resolved report paths.
All raw runs are gitignored local evidence in the named worktrees; the committed
indexes and pins do not pretend to contain those raw bytes.

Comparison runs are explicitly exposed arrangements, not a blinded trial:

- `pytest-exec-current-normal-01`: accepted `77eb9875` native family through its
  old public path, preserved in the comparison worktree.
- `pytest-exec-current-formation-01`: `8136e63b`, one labelled comparison-only
  missing-anchor intervention in the old checker. Its parent reports only
  `exec evidence control regression`; details require the assertion log.
- Candidate diagnostic controls copy the real adopted test/helper and native
  closure, then apply one specified fault. Their small catalog omits app gates
  only to isolate these native/reporting controls. Real public F runs retain
  app/worker/clang admission and inspect the unchanged accepted application.

## Acceptance matrix

| Question or obligation | Observed result and decisive evidence |
| --- | --- |
| Identify a variant and phase | Named F suffix, setup/call/teardown outcome, diagnostic and native directory are emitted for every item. Formation, accepted-mutation, wrong-rejection, setup-before-yield and simultaneous body/teardown controls inspect the actual reports. |
| Locate related logic | `test_exec_control_states.py` declares nine items and the shared baseline/finalizer; `exec_domain.py` owns the native recipe and paired literal expectations; `check_exec_evidence.py` retains only the canonical ledger parser. |
| One authoritative route | F's catalog declares one pytest module. The old shell block and executable checker loop are removed; direct old checker execution refuses with the public command. Public defaults, explicit family/suite selection and neighboring legacy paths pass. |
| Preserve native meanings | Production ledger has all 58 ordered attempts. Native input closure and unchanged mutation/oracle values compare equal to the old normal run. Incorrectly accepted mutations, wrong assertions and missing formation anchors are separately rejected. Missing-header controls still require their designated include refusal. |
| Timeout/cancellation | A command prints the expected assertion and then actually times out; the original candidate incorrectly credited it. The retained correction makes the bridge fail the phase after recording its receipt, even when matching rejection text exists. Ordinary cancellation uses the same refusal. |
| Preserve baseline applicability | A failed baseline records the production body failure and eight setup failures with no dependent call phases or mutant commands. The ordinary display groups the cause first; raw baseline/phase evidence remains. |
| Preserve finalizer scope and bodies | Both finalizer classes retain nine passing body reports and a failed last-item teardown. The summary prominently identifies all-family scope and distinguishes uncertain shared inputs from cleanup after completed observations. |
| Selection and collection | Syntax, duplicate IDs and empty collection refuse before replacement of protected output or command ownership. Read-only `--list` inventory agrees. Missing packages/app/clang show `not_started/unavailable` while independent work can continue. |
| Setup acquired before failed yield | Supervised setup command is registered and settled despite fixture failure; no dependence on post-yield cleanup. Later independent work runs. |
| Engine death / interruption | External peers and kernel exit observers distinguish completed, active and queued items. Completed evidence survives. Death reports `started/incomplete`; SIGINT cancels queued legacy work; independent continuation after engine-only death requires settled ownership. |
| Outer supervisor death / lock lifetime | The independent owner holds the actual lock while its command/child survives. Live authenticated and offline settled recovery work; active recovery refuses. Dropping the native descriptor, claiming closure without group absence, deleting both binding identities, and contradicting a recorded command with never-launched settlement are rejected. |
| Crash windows and admission | Pre-owner-launch, pre-release, started-before-PID-publication and direct-return-before-settlement are exercised with real process observations. Missing launch/settlement evidence never becomes proof of absence. Pending ownership blocks new builds/tests and already-selected later cases. |
| Recovery scope and retention | Public preview/apply remains usable when execution refuses. Reserved-but-unauthorized records can close; uncertain authorized records retain a checkout hold; proven quiescence with remaining cleanup holds only output. Repeated justified recovery is idempotent. Protected output refuses pruning; closed unpinned fixture output becomes eligible. |
| Missing/truncated publication | Valid earlier phases survive truncated/contradictory/missing session evidence. Missing family summary yields parent `started/incomplete`; missing start publication yields `unknown/incomplete`. None is an overall success or displayed merely as never started. |
| Portable completeness / historical compatibility | With expected source/selection fixed outside the subject before launch, deleting family declarations/references/all local hints, terminal receipts/roles or operation declarations still fails after transport hashes are repaired. Unknown producer sources cannot become historical by deleting schema/contract fields. Positively identified old neighbors remain readable. |
| Existing integration | Full 48-case C-worker suite and dispatcher selection/accounting/cancellation/retention/general controls pass. Source manifests, generated architecture/citations, generator contracts, direct Python startup and shell interpreter controls pass. Release acceptance/publication/rotation controls pass with independently supplied producer provenance. |
| Build integration | Existing broad build-refusal coverage is preserved as a failed prefix plus a separately identified continuation, including the real default-battery and mutation controls. It is not reported as one uninterrupted green run. The shared lock helpers and verified pytest equipment are explicitly supplied to disposable fixtures. |

Verification is composed across fixed source commits, not presented as one final
all-suite invocation. The complete C-worker suite was observed at `9aa2d963`;
release-reader and rotation refinements have later dedicated observations; source/
startup checks were repeated at `74ef845f`. The final family matrix covers the
subsequent command-context and stopped-command corrections. The broad build
continuation uses `cecfdeef`, candidate-derived `39c04284` plus its labelled
selection wrapper, before the later stopped-command and settlement-validation
corrections. Those deltas are exercised by the final actual-family timeout/
baseline/closure controls and release-consumer regressions.
The final reader also checks the retained real battery using its separately
captured prelaunch contract; this is a reader verification, not a new execution
or app inspection. The evidence index preserves the full identity for each observation. The build
battery uses a freshly signed disposable app; notarization, staple validation and
Gatekeeper responses are explicitly controlled. It establishes no Apple acceptance
and publishes no release.

The final-source family/diagnostic run and regression identities are recorded in
the accompanying evidence index. Earlier decisive failures remain pinned, with
corrections distinguished in the implementation sequence: zombie-group EPERM,
missing fixture dependencies/producer provenance, observer socket lifetime,
premature mutation submission wording, publication fallback, per-invocation
ownership admission, shared-cause display, timed-out rejection text and absent closure identities. None was cured by weakening a native
oracle or changing the accepted app. The locale stimulus was rerun with inherited
`LC_ALL` absent; the accepted locale assertion was not changed.

## Emitted-report walkthrough

Start with the parent `run.json` and the displayed family report path. The
family `summary.txt` gives stable item IDs and phase outcomes; `family.json` and
`phases.jsonl` retain the full phase evidence, `pytest.txt` the framework output.
The summary links `artifacts/<suffix>/`, `operations.jsonl`, `ownership.json`
and `selection.json`. These paths were followed in the actual retained runs.

A passing `collection_from_final_reap` shows three passing phases. Its
`expectation.json` names the submitted statement
`slot->exec_leader_exit_observed = reaped == child;` and designated native
assertion `slot->exec_leader_exit_observed == leader`. The passing control retains
that assertion in stderr and native return status -6. `observation.json` gives actual return status and designated-assertion
presence; `run/stdout` and `run/stderr` retain the native observation. Source
inventory hashes match the retained copies. A deliberately accepted mutation
instead shows a **call failure**, `accepted mutation`, with the submitted no-op
and successful native exit retained. A wrong-rejection control shows **call
failure**, `outside its designated oracle`, with actual stderr preserving
`slot->exec_group_rc == group->rc && slot->exec_group_errno == group->error`
(return status -6). Nonzero status alone never credits the control. A separate timed-out-rejection
example retains matching assertion text and a stopped-command receipt; the body
fails explicitly for timeout instead of crediting that text.

The formation failure reports `mutation not submitted`; its expectation says
`proposed`/`not yet established`, with pre-formation sources retained. There is no
invented submitted mutation or native run. This is materially more direct than
the old broad shell failure. The change surfaced a misleading initial receipt
label during the walkthrough, which was corrected with the original run pinned.

For the bad baseline, the first scope line says `SHARED BASELINE`, gives the
native ledger mismatch and `artifacts/baseline.json`. The production item has a
failed call; eight named dependents say `setup blocked by shared baseline; body
not run`. No mutation rejection is credited. The baseline's expected/observed
ledgers remain available. The full repeated setup tracebacks remain behind the
summary in the raw reports, without obscuring the common cause.

For setup-before-yield, each item visibly fails setup and has no body. The summary
correctly says there is no native **variant** observation, and points to
`operations.jsonl` for the acquired setup command; its stdout and closed receipt
remain inspectable. For simultaneous production body and teardown failures, both
phases and their separate diagnostic text survive in the same item.

Both session-finalizer examples put `SHARED SESSION FINALIZER` before item rows,
name `observation`, and say `all family items`, attached to last-item teardown.
Input-integrity failure lists the changed shared header in `input-integrity.json`;
all per-variant source receipts still match their retained inputs. Thus the
recorded native assertions remain readable, while the family cannot pass its
shared-input integrity requirement. The cleanup example explicitly says cleanup
failed after observations: all body outcomes remain usable; command ownership
is separately closed in this example. Neither turns nine passing bodies into
family success. Any unresolved ownership is displayed separately and blocks
success regardless of those bodies.

The engine-death display preserves a passed production item and marks active/
queued evidence incomplete. Its parent is `unrun` only in the legacy aggregation,
with accompanying `execution=started accounting=incomplete` displayed explicitly.
Missing equipment instead displays `not_started/unavailable`. These distinctions
were checked in the emitted parent and family reports, not reconstructed only
from raw process observations.

## Responsibility and maintenance account

| Responsibility | What changed; continuing owner |
| --- | --- |
| Public selection and applicability | Remain in PW catalog/dispatcher, at family granularity. One family adapter replaces the shell route. The parent records pytest's fixed collection; it does not carry a parallel variant selector. |
| Item order, variants and fixtures | Framework behavior through the suite-local pytest module. The handwritten mutation/include execution loops and shell family wrapper disappear. |
| Native witnesses and expectations | Remain domain code and independent native fixture/golden. A paired mutation/expected-rejection declaration replaces parallel maps. Complete native sequences are not split into independently runnable events. |
| Phase reports | Pytest supplies setup/call/teardown, assertion context and finalizer failures. The integration exports them durably and links observations. PW still maintains reconciliation, run-integrity and human summary semantics. |
| Baseline/finalizer scope | Pytest owns caching/finalization; the domain helper owns baseline validity and input receipts. A small summary adapter explains the shared meaning that pytest's last-item attachment does not itself explain. |
| Commands and recovery | New independent owner, socket protocol and durable registry outside pytest. PW maintains launch gates, process-group/descriptor evidence, recovery authentication and admission/disposal classifications. These are adopted integration costs, not omitted or credited to pytest. |
| Retention/release | Existing infrastructure remains, extended with the family/source contract, positive historical provenance and portable closure roles. Consumer schemas/count scopes are documented; no legacy item-report duplication is maintained for F. |
| Dependencies | Five pinned wheels, explicit installer/verifier and isolated import configuration are new obligations. Upgrades must preserve the phase bridge and controls; ambient plugins are not supported. |
| Investigation equipment | Copied comparison worktrees, frozen original demonstration, emitted-walkthrough/index scripts and build-continuation wrapper are review equipment. The registered `dispatcher/pytest_controls` and its independent observers are continuing regression controls. |

The standalone `tests/fixtures/worker_lifecycle/build_exec_control.sh` remains
manual fixture equipment, not a second family executor. Its compiler recipe and
the domain helper still share flag knowledge; a future recipe change must review
both. No removal of that duplication is credited here.

This improves ordinary editing and diagnosis while adding operational machinery.
The large shared integration is justified here by the explicitly chosen ownership
contract, not by a line-count claim. It could benefit later work, but no such
benefit is needed or credited in this decision.

## Limits and recovery disposition

The demonstrated resource kind is compiler/control process groups and their
files, on this macOS environment. It does not establish arbitrary escaping
process supervision or launchd installation recovery. The family has no skip
allowance, public item filter, parallel pytest scheduling or external plugins.
New-producer completeness assumes the independently retained source/release
identity remains trusted; repairing mutable archive hashes is within the controls,
replacing every trust anchor is outside them.

Actual candidate-family operations are closed. Intentionally ambiguous nested
control registries remain protected, including missing owner settlement after
externally observed exits and the earlier failed controls without a complete
persisted exit account. Their identities, endpoints, facts and missing closure
prerequisites are in the recovery index. They are isolated fixture checkout
holds, not hidden active claims against the candidate checkout. No historical PID
was signalled to make the index look clean. Prior protected resources and pins
retain their prior unresolved dispositions.

Unproven long-term savings remain unproven. The acceptance recommendation rests
on the observed diagnostic improvement, organization and preserved obligations
for this one family. Leaving every other family on the current harness is a
complete, supported endpoint.
