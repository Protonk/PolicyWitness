# Pytest primary-engine boundary: bounded investigation

The architecture is feasible for the tested serial slice. Pytest owned selection,
fixture execution, continuation and phase reporting without a second ordinary
case scheduler in the supervisor. Durable publication, resource supervision,
recovery and result completeness still required substantial PW machinery. The
real C extraction replay preserved its native observations and rejection
controls, and produced useful individual diagnostics, but did not establish a
material reduction in adaptation work. Leave the accepted harness in place.

This is a prospective experiment after the completed workset review, followed
by one exposed historical replay. It does not replace or retrospectively improve
`0c22d256:records/workset/pytest-first.md`. The amendment and independent expected
observations were committed at `e9375310` before implementation. Accepted source
is `77eb987554eef10ffa3371ffb21b235097562a78`; all work is on
`investigation/pytest-boundary` in `/private/tmp/pw-pytest-boundary-20261030`.
The original checkout, accepted application and historical evidence remain in
place. No production harness integration, app build, CHECK work or migration
was performed.

The fixed environment is pytest 9.0.2, Python 3.14.9 on macOS arm64, with pinned
dependency versions and installed-file hashes. Execution is serial, external
plugin loading disabled, assertions enabled, explicit configuration, FD capture,
importlib imports and no pytest cache or bytecode writes. The actual helper
process uses the pinned Homebrew interpreter with `-I -S`, an explicitly checked
environment, argv, cwd, stdin and output pipes. This distinction mattered:
macOS supplied an encoding variable and Python reported a symlinked executable
path. Both were observed and made explicit rather than assumed away.

The existing dispatcher was a reference subject only. Its four unchanged
selection/accounting/cancellation/retention controls passed outside the automation
sandbox. The earlier sandboxed attempt remains failed, with socket-binding and
nested-sandbox refusals. Candidate execution never ran beneath that dispatcher
or an outer checkout hold. It directly reused `checkout_lock.py` and
`retention.py`; those responsibilities and their cost remain. Independent
observers reused the existing peer-PID rendezvous and kernel-exit primitive,
but obtained their own peer identities and exit events and never imported the
candidate's result interpreter.

The consequential ownership transitions are explicit:

| Transition | Owner and tested boundary |
| --- | --- |
| Selection becomes fixed | Pytest collects and applies its selectors in one engine. The integration sends the final node IDs and waits. Failed collection, an empty/duplicate selection and collect-only cannot enable test bodies. |
| Execution becomes eligible | The supervisor acquires its own checkout hold, validates fresh output and retention, durably publishes owner and plan, then hands over eligibility and held descriptors. Failed plan publication and refused output leave no body receipts. |
| Resource obligation is registered | A fixture requests a session lease. The supervisor publishes its intent before launch, starts a gated resource owner, registers exit observation and records the PID before allowing acquisition. |
| Acquisition occurs | The resource owner receives permission, creates its file and recovery channel, and records the already-published ownership in its raw acquisition receipt. An engine-side fixture finalizer is not its sole owner. |
| Reports become durable | Pytest hooks append and fsync separate start/setup/call/teardown/session records. Finalization joins these to the selected IDs; it does not rerun items or reinterpret a failed assertion as a pass. |
| Cleanup becomes justified | Normal supervision observes the child's kernel exit before removing its resource. After dual death, recovery checks the live socket peer, nonce, transferred lock descriptor and engine-exit observation, then independently watches the child's exit before deletion. It admits no new test session under the dead owner's claim. |

The supervisor's only execution loop watches one engine and resource requests.
Ordinary scheduling stays inside pytest. Its completeness validator is still a
second representation of the results: it checks phase structure, unexpected
items/outcomes, missing or duplicated evidence, engine completion and unresolved
leases. That is explicit integration work, not eliminated bookkeeping. Resource
leases last through this bounded session; this experiment does not demonstrate
that every production fixture should retain its resources that long.

The final demonstrator run at `832e7717` passed eighteen outside observation
groups, including eleven separately constructed accounting inputs. The underlying
candidate intentionally fails in several groups; an observer pass means the
declared failure was preserved, not that the candidate run passed.

- Pre-yield setup acquired its resource, then failed. There was no active-body
  receipt or post-yield finalizer receipt. The setup error survived, the later
  independent body ran, and the supervisor retained ownership through cleanup.
  Pytest's passing teardown-phase report did not invent execution of that
  fixture's post-yield code.
- Simultaneous body and teardown failures retained both distinct diagnostics.
  Later independent work continued despite a poisoned ambient `--maxfail=1`
  setting, which the engine launcher removed.
- SIGINT preserved the completed item, incomplete active item and unstarted
  queued item. Pytest ran its available finalizer. A helper first demonstrated
  direct-SIGINT survival; candidate cleanup then produced independent exit events.
- Engine SIGKILL left one completed item, one active item and one queued item.
  Independent receipts established what started, and raw partial bytes survived.
  Missing phase reports remained incomplete.
- After supervisor and engine SIGKILL, the child remained responsive and held
  the same lock inode. A competing invocation collected but could not start a
  body. Recovery preserved the incomplete run, observed the child's exit and
  released the final hold. A deliberately dropped descriptor made the lock free
  while the child was still responsive; the outside lifetime control rejected it.
- Collection and publication failures, preexisting/retained output refusals,
  report-write failure and malformed accounting did not become success.
  Refused existing bytes were unchanged. Collect-only published no run.
  A truncated final journal frame preserves the earlier completed item's phase
  records, leaves later work incomplete and fails the run without rewriting raw bytes.
- FD capture caught deliberate inherited stdout/stderr writes. The explicitly
  piped helper had exactly the declared environment and inputs, no extra open
  descriptors, and the intended interpreter identity. The protected resource
  child held its explicit lock descriptor; a default close-on-exec assumption
  was insufficient, as the negative control demonstrated.

There were useful unsuccessful prototypes. `fa376979` mishandled a Unix datagram
reset during engine exit and bypassed resource finalization; the outside exit
observer caught the still-live child. The correction reaps the engine before
finalization. Subsequent failures exposed observer assumptions about interrupted
teardown, macOS environment additions and executable path spelling. All original
runs remain failed and pinned. The first failed run retains its acquired record,
resource file and empty recovery directory: the outside safety release was not
candidate cleanup, and its post-cleanup exit observation was not durably saved.
Later runs record exits before and after safety cleanup separately. That earlier
record has not been rewritten into a successful or closed lease.

Final source inspection found a second candidate defect: one malformed journal
line discarded previously decoded frames from the machine account. The independent
red control at `0d3af494` reproduced lost completed-item status. `832e7717` retains
the valid prefix while preserving the overall journal failure and incomplete
later work. The full demonstrator reran successfully after this correction.

The conditional replay was informative because it tested source binding after
the lifecycle boundary had passed. It used `f8f3c24f` before the C extraction
and `341f9441` after it. The old adapter is recoverable at `0085bd54`; the actual
adaptation is `fec0e181:records/pytest-boundary/{native_adapter.py,test_native.py}`.

| Replay | Candidate result | Outside native observation |
| --- | --- | --- |
| Old adapter, old source | Seven items passed | All 58 golden-ledger attempts matched; six mutants failed at the intended native assertions. |
| Same adapter, extracted source | One pass, six failures | The production ledger still matched, but every old mutation anchor was absent. No failed formation was credited as a detected behavior defect. Each variant received its own diagnostic. |
| Adapted owner/closure, extracted source | Nine items passed | The same ledger and six exact rejection reasons survived; removing either implementation header produced its specific include failure. |

The native C fixture's SHA-256 remained
`adc11fd2f3e1daf2638c752221b8da97a6a102aaab8fbcc1c42401a93ebb6da5`.
The mutation values, designated native assertions and golden expectation were
unchanged. A session fixture prepared immutable source inputs, each variant
got its own copies, and the fixture checked that shared inputs stayed unchanged.
Commands retained source hashes, arguments, raw stdout/stderr and statuses;
build intermediates were removed only after the commands returned. Compiler and
native children explicitly inherited the checkout claim. This replay did not
inject death during compilation or demonstrate general compiler-tree recovery.

The required edit remained semantic: copy the new entry and complete header
closure, write the mutation into the extracted owner after copying, and add the
missing-owner controls. Pytest did not discover that ownership change. The
candidate adaptation changed 17 added/5 removed physical lines across two files;
the corresponding historical checker change was 21 added/3 removed lines.
These small, differently organized diffs do not establish a productivity or
maintenance advantage. The demonstrated reporting benefit is narrower: the
stale replay exposed six named formation failures without a custom execution
loop, instead of stopping at the old script's single pre-loop anchor assertion.

The intended displacement and actual result are distinguishable:

| Responsibility | What changed in this slice |
| --- | --- |
| Ordinary selection, invocation order, fixture phases and continuation | Became pytest behavior. No candidate catalog or per-item command scheduler was added. |
| Shell start/end events and a single manually constructed case result | Replaced by pytest phase hooks, plus a durable phase journal. |
| Complete selected accounting and outcome policy | Moved into a 97-line join/validator; missing phases and unexpected skips still need PW policy. |
| Lock, output ownership and retention | Reused unchanged libraries, not removed. The candidate takes its own hold. |
| External resource lifetime and recovery | Added an explicit supervisor, gated resource adapter and restricted recovery protocol. These remain domain-specific machinery. |
| Native variant execution loop and report formatting | Became parametrized items and framework diagnostics; source copying, command receipts, native assertions, golden parsing and mutation reach remained. |
| Historical replay preparation and independent control driving | Investigation-only equipment. They are not proposed production harness components. |

Physical source lines, including blanks/comments, help locate costs: the five
candidate engine/account/supervision/resource/recovery files total **458**;
the native adapter and pytest slice add **131**, including historical snapshot
preparation. The outside observer, replay observer and synthetic subjects total
**590**. Shared lock and retention libraries total **979** unchanged lines, and
the existing OS exit observer and native-ledger reader remain dependencies.
The current CLI/executor total 757 lines but implement a much wider contract;
subtracting the candidate from that number would be misleading. Dependency
inventories, framework code and experimental audit/report material are excluded
from these source counts. No elapsed-agent-time or performance claim is made.

Recoverable evidence is under this worktree's gitignored `tests/out/runs/`.
Each candidate's own plan, reports and terminal account is separate from its
outside observer account. The committed retention index pins all twelve material
top-level runs, including failures and the stale replay, plus the retained-output
refusal stimuli. Repeated repository-pruner previews found no eligible disposable
run; no historical output was pruned or rewritten.

| Run directory / ID | Tested source | Role |
| --- | --- | --- |
| `pytest-boundary-reference-01` / `20261030T144802Z_0cf0ac62` | `e9375310` | Sandbox refusal reference; accounting and retention passed. |
| `pytest-boundary-reference-02` / `20261030T145251Z_0059d39d` | `e9375310` | Four unchanged reference groups passed outside the sandbox. Concurrent records-only additions did not enter those commands. |
| `pytest-boundary-demo-01` through `-04` (IDs equal directory names) | `fa376979`, `4211d48b`, `493309ed`, `5c4cd41d` | Preserved prototype/observer failures and preceding observations. |
| `pytest-boundary-demo-05` (same ID) | `cfbd753a` | Eighteen groups passed; ten accounting inputs; basis for proceeding to the replay. |
| `pytest-boundary-journal-red-01` (same ID) | `0d3af494` | Independent truncated-tail control rejected loss of an earlier completed item. |
| `pytest-boundary-demo-06` (same ID) | `832e7717` | Final eighteen groups passed; eleven accounting inputs including valid-prefix preservation. |
| `pytest-boundary-replay-old-01` and `-stale-01` (same IDs) | `0085bd54` | Seven passing old-source items, then the deliberately failed stale adapter. |
| `pytest-boundary-replay-adapted-01` (same ID) | `fec0e181` | Nine adapted items passed with the original native oracle. |

The final audit checked run/pin identities, source snapshots, the original
retention entries, protected-path existence and accepted-app paths/modes/hashes.
The app still matches inventory
`9529b7f22ca49559a3aee9200fd4ac9fe83268351576dc77d1c501e8f13cd4da`.
C0.2 still hashes to
`9c155b77a99870ed4519bcbe9ea0c3675d964bb129a9d90d7262bd0e99c8ec6c`.
The eight demonstrator dependency files are byte-identical to `832e7717`.
The post-replay reader correction changes retention of decoded frames when a
later JSON line fails; valid journals use the same per-line decoding and unchanged
accounting policy. The final reader reconciled all three retained native journals
to exactly their original case results and errors. The native adapter, assertions
and compiled inputs did not change. This supports reuse of the native execution
evidence without recompilation; it is an inspected applicability judgment, not a
claim that hashes discover all dependencies.

The result supports a credible boundary, not a replacement harness. Full catalog
defaults/dependencies, compatibility aliases, Rust/Swift adapters, signed-app
gates, artifact reinspection, sleep accounting, launchd recovery, and arbitrary
escaped descendants were not implemented. Recovery here needs the surviving
cooperative resource owner; an absent owner with incomplete exit evidence remains
unresolved. Fsync-backed process-death tests do not establish power-loss behavior.
None of these exclusions is credited as preserved production coverage.

The next decision can reasonably be to leave the current arrangement alone.
There is no newly demonstrated production defect and no basis for migration on
maintenance savings. If a future migration decision requires more evidence,
the useful next question is the incremental cost of one actual durable external
resource kind and full public selection metadata—not another conversion of easy
assertions or another repetition of these passing controls. That work is not
necessary to finish this bounded investigation and was not undertaken.
