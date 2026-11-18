# D-erasure-handles-ownership

Read-only assessment at HEAD `837296af` (branch `main`), 2026-11-17. No tracked
file was changed and nothing was built or run. Small in-memory reads of retained
JSON used `tests/lib/python.sh -I -c`. Every `file:line` below is the current
tree unless it names a record.

Entries assessed: authority identity/conventions and coverage/limits, DT-63,
DT-64, DT-66, DT-67, DT-68; observation-time identity/evidence classes, DT-124
to DT-128, the cross-anchor account and coverage/limits. Four coverage-map rows,
one subject each, plus a shared evidence base.

Classification codes: **CEC** contradicted explicit commitment; **CA**
consequential ambiguity; **UI** unsupported inference; **IMA** inaccurate
mechanism account; **OCC** overstated coverage credit; **AO** accurate
observation needing no change.

Evidence codes: **SRC** source/doc re-read now; **EX-A** executed by the
authority pass, capture absent; **EX-O** executed by the observation-time pass,
capture retained locally and re-read now; **LOCAL** retained default-battery
output at build `2f4d76e4`, read now.

## 0. Shared evidence base

| Evidence | State at HEAD | Use in this file |
| --- | --- | --- |
| `/private/tmp/pw-authority-trace-3QC3qQ/` (DT-59 to DT-68 captures, `issue_tail.c`, temporary Swift driver) | Absent | Original captures for DT-63's constructed exercise, DT-64's native return and DT-66's run cannot be re-read. Their claims are re-derived from source or from the rebuilt E-series. |
| `.tmp/contract-trio/observation-time/` (E1 to E7 CLI captures, E6 driver `main.swift`, `runs/e6/*.json`) | Present, gitignored, no retention guarantee; app build `8b5de2b2` | Re-read. Shows what that pass recorded, not current behavior. |
| `/private/tmp/pw-trio-ot-*` targets | Absent | Target identity cannot be reconstructed. |
| `tests/out/runs/trace-instrument-{before,after,after-corrected}/` (default batteries, build `2f4d76e4`, macOS 26.7.1) | Present; inactive development output, prunable | Read `extension_redelegation/artifacts/report.json` and `extension_boundaries/artifacts/{native,issue-2,issue-3,issue-16}`. Local observation only; not release evidence and not a case pass credited here. |
| Product source | `git diff 57d2375a HEAD -- controller runner` and the same from `cc55288d` change only the generated worker-identity bytes (`pw_probe_runner_abi.h`, `CWorker.swift`) | The review's product line numbers are off by 0 to 5 lines; content is the same. |
| Cited tests and docs | `git diff --stat 57d2375a HEAD` over the cited fixtures, checkers, suite READMEs, surfaces, `EXTENSIONS.md`, `WORKER.md`, `limits.json`, `footprint.json` is empty | The cited assertions are unchanged. |

Investigation-scope statements (identity, conventions, coverage, limits):

| Id | Statement in the review | Holds at HEAD? | Disposition |
| --- | --- | --- | --- |
| S-1 | Authority pass: source at `57d2375a`, app `8b5de2b2`, product sources equal | yes; HEAD adds only regenerated identity bytes | AO. Keep as the inspected revision. |
| S-2 | Authority temporary material has no retention guarantee | yes; now absent | AO. Treat every EX-A claim as a retained description. |
| S-3 | Neither pass executed or credited a registered suite | yes for those passes | AO. Later LOCAL batteries exist but are development output. |
| S-4 | Sandboxed build and XPC failures in the passes are harness observations, not native authority outcomes | yes | AO. No product disposition. |
| S-5 | Authority trace scope and its narrower affirmative evidence (usable delivery after the issuer's owned reap; per-release fresh-read boundaries; interrupted issue withholds native fields) | yes as scope | AO. Affirmative items are scoped to the named specimens. |
| S-6 | Unexercised list (failed close/unmap, release failure, retained descriptors across release, abnormal native allocation); the oversized-return control does not characterize Apple's allocator or token maximum; the driver's custody print is not a public field | yes; still unexercised | AO. This pass adds no execution. |
| S-7 | Observation-time pass: source at `cc55288d`, app `8b5de2b2`, four evidence kinds | yes | AO. |
| S-8 | E-series artifacts under `.tmp`; targets under `/private/tmp` | artifacts present, targets absent | AO. |
| S-9 | Rebuilt specimens; published token length equals 171 plus the target path's byte length in three runs (208, 216, 226); no token content inspected | recorded so in `runs/e1a_issue_only`, `c7_len45`, `c7_len55` | AO. A correlation only. It bears on DT-64 only as the observed size range. |
| S-10 | Not executed: mutation of either last-use erase; not characterized: native release reference counting, revocation, cause of errno 1 | yes; unchanged by this pass | AO. Carried as limits in subjects 1 and 2. |

---

## 1. DT-63 / DT-64 / DT-124 / DT-125 / DT-128 — host last use and final teardown, native allocation prefix, worker observers, terminal byte extent

Rule carried from the coverage map: call counts, flags, scanned bytes and time
are four different observations and none substitutes for another.

### 1.1 Claims

| Id | Claim | Boundary (form, representation, observer, time) | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-63.a | The test comment says custody was erased "at the token's last declared transfer"; the assertion reads `outcome.custody[].erased` after `scheduler.run` returned | Live actor schedule; internal `CustodyObservation.erased`; Swift unit test; after host teardown | yes: `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift:467-468`; `runner/Sources/PWRunnerCore/ActorScheduler.swift:183-187` | SRC | OCC |
| DT-63.b | `finish()` runs before the outcome is built and sets every custody flag; the last-transfer `defer` also clears, including when the recipient is unavailable; the assertion cannot tell the sites apart | Host source | yes: `AuthorityCustody.swift:633-639`, `514-522`, `536-541` | SRC | AO |
| DT-63.c | Constructed host exercise: accepted, transfer never published gives `erased=false` before `finish()` and `erased=true`, `transfers=0` after | Synthetic payload, real host buffers, no native call; internal flag | yes by reading (`AuthorityCustody.swift:482-485` is not taken when `lastUseSlot != slot`; `:637` sets the flag) | EX-A; SRC; E6 V2 (EX-O) shows the same relation with real workers | AO |
| DT-63.d | Assertion and unconditional flag date to `c686a05f`; the handoff mutation list does not remove last-transfer retirement | History; mutation harness | yes: `c686a05f` (2026-11-03, contained in v0.3.5 to v0.3.7); `tests/suites/runner_unit/actor_handoff_mutations.py:86-89`, `116-119`, `134-169` | SRC, `git log -S` | AO |
| DT-63.e | Qualification: a support-scope finding, not evidence that production omits last-transfer clearing; the boolean is not a scan of memory | - | yes | - | AO; kept as a limit |
| DT-64.a | The ARCHITECTURE issue rule says "Erase the native allocation after copying"; WORKER and the inventory say inspected length | Public statements | yes: `docs/contract/14-extensions.surface.md:373` (rendered `docs/ARCHITECTURE.md:356`); `docs/WORKER.md:67`, `389-390`; `docs/architecture.json:9845` (rendered `WORKER.md:647`) | SRC | CEC for a native return longer than the inspected bound (constructed input only); IMA otherwise |
| DT-64.b | `strnlen` caps inspection at 16,384 bytes; the refusal branch erases that length and frees; a constructed 16,393-byte return left 8 nonzero bytes at the free boundary | Worker; native allocation; replaced issuer; at `free` | yes by reading: `controller/tools/pw_probe_runner/pw_probe_runner.c:859-865`; capture absent | EX-A (constructed); SRC | AO |
| DT-64.c | The issuer erasure observer scans only the erase length; the oversized mode builds exactly 16,384 nonzero bytes plus NUL, so it has no tail; the checker for that mode asserts nonnull, non-issued custody and unavailable dependents; the recipient-side observer is separate | Fixture and checker | yes: `tests/fixtures/extension_controls/control.c:117-124`, `160-165`; `tests/suites/witness_contract/check_extension_boundaries.py:326-332`. Also: the `issuer_token_erased` word is asserted only when the observer holds a native token (`:220-223`), so it is not asserted for issuer modes 2, 3 and 16 | SRC; LOCAL shows the unasserted word `true` for `issue-2` and `issue-16` | AO; the coverage statement at `architecture.json:9861` is accurate |
| DT-64.d | Limits: no claim that Apple's issuer returns oversized payloads or that the bytes were recovered; the bounded implementation predates 0.3.6; no layer selected | - | yes; observed real lengths are 208 to 226 (EX-O) and 220 (LOCAL `native`) | - | AO |
| DT-124.a | Seven clearing sites with extent, time and visibility | Host and worker source | yes: host outbound `AuthorityCustody.swift:490`; issue-only last use `:482-485`; last transfer `:514-522`; custody teardown `:311-322`, `:633-639`; region teardown `:225-242`; worker last consume `pw_probe_runner.c:937-940`; exit sweep `:579-590`, first call published once (`pw_authority_setup.h:39-40`) | SRC | AO |
| DT-124.b | The erase rule lists `report: runner_reply`; the reply carries only teardown and exit cells; no public field reports either last-use clearing | Public rule against the reply | yes: `14-extensions.surface.md:408-421`; token record has no erasure field (`ActorOrchestration.swift:462-474`); cells at `AuthorityCustody.swift:231`, `:315`, `pw_probe_runner.c:589` | SRC; EX-O E1a, E1b, E3 | CA |
| DT-124.c | E6 V1: private custody held 208 nonzero bytes through A's phase-2 arrival and 0 with the flag set at B's phase-3 arrival, before teardown | Internal driver, real workers and token; private buffer read by reflection; collection hooks | recorded so: `runs/e6/last_transfer.json` | EX-O (internal, not a public reply) | AO |
| DT-124.d | E6 V2 (issuer killed before the last transfer): still 208 and flag unset at the last hook; after `run()` the flag is true and the buffer unmapped; the final flag equals V1's; the capture does not isolate `finish()` | Same | recorded so: `runs/e6/issuer_killed.json` | EX-O | AO |
| DT-124.e | E6 V1: B's `d1` inbound slot is zero at phase 4 while `d2` is nonzero, so the last-consume clear precedes the exit sweep | Worker inbound slot read through the host mapping | recorded so | EX-O | AO |
| DT-124.f | E6 limits: no public reply, no equipment binding, validator or encoding; intervals bounded by hooks; B's consume returned native 0 (a candidate handle; the clear runs whatever the result) | - | yes: driver `main.swift`; `pw_probe_runner.c:933-940` | EX-O; SRC | AO |
| DT-124.g | Tests read only the final state: `:467-468` with a timing comment, `:307` without | Swift unit | yes | SRC | OCC for `:467`; AO for `:307` |
| DT-124.h | V2 is not an input on which `:468` fails; the point is what the comment credits | - | yes | - | AO |
| DT-124.i | The footprint snapshot reads `TokenCustody.erased == false` before the last transfer; flags only | Fixture | yes: `tests/fixtures/footprint/actor_snapshot.swift:43-49`; `tests/lib/footprint_workloads.py:118` | SRC | AO |
| DT-124.j | No existing observer covers the interval between the last transfer and teardown on the host side | Registered tests | yes: the only readers of either flag are `ActorAuthorityTests.swift:307`, `:468` and the snapshot | SRC | AO; accepted limit |
| DT-125.a | The boundary observer rewrites one word on every erase call over the observed inbound slot, scanning the full 16,384-byte field; it keeps a cumulative failure count only | Worker; fixture | yes: `control.c:125-129` | SRC | AO |
| DT-125.b | The checker reads only those words | Checker | yes: `check_extension_boundaries.py:273-274`, `336-338` | SRC | AO |
| DT-125.c | That observer would also pass if only the exit sweep ran | - | yes by reading | source-read, not executed | AO |
| DT-125.d | The terminal fixture counts erase calls and checks the full buffer after each; `consume` requires `erase_calls >= 3`; without the last-use erase the count would be 2 | Synthetic fixture compiled over the production worker source | yes by reading: `tests/fixtures/extension_controls/terminal_control.c:100-106`; `tests/suites/runner_c_worker_harness/check_terminal_erasure.py:90-91`; calls at `pw_probe_runner.c:938`, `:1673`, `:602` | source-read, not executed | AO |
| DT-125.e | That guard is synthetic and count-based, not a timing observation; no mutation was executed | - | partly. The same fixture's release callback asserts the full buffer is zero at the release call (`terminal_control.c:119-123`) in `explicit_release`, whose consume is marked last use (`:198`) and whose release must be counted (`check_terminal_erasure.py:41`). That is a byte-state observation between the last consume and the exit sweep. It is still synthetic and its sensitivity is still source-read | SRC | AO with this correction |
| DT-125.f | E6 V1 supplies the ordering observation internally; the host side has no equivalent guard | - | yes | EX-O; SRC | AO |
| DT-128.a | Worker cell 11's `value` counts bytes overwritten in settled inbound slots; it is 0 with `performed` when there is none | Public reply | yes: `pw_probe_runner.c:581-589`; E1a and E3 actor A | SRC; EX-O | CA (low consequence) |
| DT-128.b | E3 actor B reads 16,384 although its slot was cleared at the last consume; the count includes already-zero bytes | Public reply | yes by source; ordering shown by E6 V1 | SRC; EX-O | AO |
| DT-128.c | Host `shared_clear` under the same `shared_erasure` key covers every slot (16,384 in E1a, 32,768 in E2) | Public reply | yes: `AuthorityCustody.swift:231` | SRC; EX-O | AO |
| DT-128.d | `final_erase: performed` is recorded whenever the custody buffer exists | Public reply | yes: `AuthorityCustody.swift:311-316`; E1b has an `unresolved` token beside `performed` | SRC; EX-O | AO |
| DT-128.e | No statement gives `performed` a meaning that a value of 0 contradicts; RESPONSE lists the states without an extent | Public definitions | yes: `docs/contract/34-equipment.surface.md:870`, `:966`, `:992` | SRC | CA |
| X-1 | `issued` with `last_use_step_id` and `final_erase: performed` can be read as clearing at last use | Reply reader | yes; E1a shows the combination | EX-O | UI (no statement makes this inference) |
| X-2 | `shared_erasure: performed` can be read as "token bytes cleared at exit" | Reply reader | yes | EX-O | UI |
| X-3 | Teardown and exit records stand in for every clearing; the internal flag, the custody cell and cell 11 describe the last clearing, and last-use and teardown clearing are merged into teardown cells | Cross-anchor account | yes | SRC | AO |
| X-4 | E3 timeline steps 4 and 6 to 8: both last-use clears are internal; `consume_h2`'s clear "was not observed in E3" | Timeline | yes | EX-O | AO |

### 1.2 Comparison

**Obligation as stated.**

- Owner `docs/contract/14-extensions.surface.md:417` (`extensions.custody.erase`,
  rendered at `docs/ARCHITECTURE.md:375`): "Erase host-private custody at the
  last declared transfer (or after issue when never transferred) and at
  teardown. Erase worker-owned inbound payloads after their last declared
  consume and at normal exit once host settlement transfers ownership. At host
  teardown erase shared regions only for actors whose termination is
  established; otherwise detach the host mapping." Its header carries
  `report: ["runner_reply"]`. Its support is the subtree owner at `:440-448`,
  grade `source_read`.
- Owner `14-extensions.surface.md:373` (`extensions.custody.issue`): "Erase the
  native allocation after copying."
- Owner `docs/EXTENSIONS.md:81-84` (shared region): "The host erases private
  custody at the token's last declared transfer and at teardown. The worker
  erases settled inbound slots at last use and ordinary exit; the host clears
  remaining shared slots after confirmed process exit."
- Authored `docs/WORKER.md:389-390`: "It erases the native allocation to its
  inspected length and frees it before publishing the slot." Generated row a3
  (`docs/architecture.json:9845`): "Erase inspected length and free before
  outbound publication; oversized tail unobserved."
- Owner `docs/contract/34-equipment.surface.md:870`: "shared_erasure/
  private_erasure use not_present, performed, withheld_not_quiescent or
  unobserved." `:992`: "`value`: Operation-specific unsigned native observation
  when the cell marks a value present, such as object/page size."

**What the producer does (source, HEAD).**

- Host last use: `serviceTransfer`'s `defer` calls `tokens[...].erase()` and
  sets the observation flag when the serviced delivery's slot is the token's
  `lastUseSlot` (`AuthorityCustody.swift:514-522`). An issue with no declared
  transfer is cleared at acceptance (`:482-485`). `erase()` clears the whole
  16,384-byte buffer (`:304-309`).
- Host teardown: `ActorScheduler.finish()` stops and reaps every actor, then
  calls `custody.finish(quiescentActors:)` (`ActorScheduler.swift:557-583`).
  That clears and unmaps every custody buffer, records `final_erase`, sets
  every observation flag unconditionally, and clears shared regions only for
  quiescent owners (`AuthorityCustody.swift:633-639`, `311-322`, `225-242`).
- Worker issue: the native return is inspected with
  `strnlen(token, 16384)`. An in-range token is copied, then `length` bytes are
  cleared and the allocation freed (`pw_probe_runner.c:874-876`). An empty or
  longer return is cleared through `length` (0 or 16,384) and freed
  (`:860-865`). Bytes past the inspected length are never written.
- Worker inbound: the last declared consume clears the full slot field whatever
  the native result (`:937-940`). Every ordinary departure sweeps settled
  inbound slots (`:579-590`); the first sweep publishes cell 11 with the byte
  count overwritten, once (`pw_authority_setup.h:39-40`).
- Reply: the custody scope carries only `final_erase`; the region scope
  `shared_clear`; the worker scope `terminal_owned_inbound_clear`. The token
  record carries `last_use_step_id`, a declaration-derived name
  (`ActorOrchestration.swift:473`), and no erasure field.
  `CustodyObservation.erased` is read by no production code.

**What each reader or test asserts, by kind of observation.**

| Clearing site | Flag | Call count | Scanned bytes | Order or time |
| --- | --- | --- | --- | --- |
| Host outbound slot at acceptance | - | - | `ActorAuthorityTests.swift:144-149` scans the full token field (synthetic payload) | after `service` returns |
| Host private custody, issue-only last use | set at `:484`; read by no test before teardown | - | none | none |
| Host private custody, last transfer | set at `:519-520`; read only after teardown (`ActorAuthorityTests.swift:307`, `:468`); the footprint snapshot reads `false` before it | - | none registered; E6 by reflection (EX-O) | none registered; E6 hooks (EX-O) |
| Host private custody, teardown | `final_erase` cell and `private_erasure: performed` (public); internal flag | - | none (the buffer is unmapped in the same call) | by source, after reap |
| Host shared region, teardown | `shared_clear` cell with byte count; `shared_erasure` (public) | - | `ActorAuthorityTests.swift:182-205` through an independent mapping (synthetic, no worker) | after `finish(quiescentActors:)` |
| Worker native allocation after issue | `issuer_token_erased` word | - | scans the erase length only; asserted only for native-token modes (`check_extension_boundaries.py:220-223`) | at the erase call |
| Worker inbound, last consume | - | `erase_calls >= 3` (`check_terminal_erasure.py:91`) | full field after every erase call (`terminal_control.c:100-106`); full field at the release call in `explicit_release` (`:119-123`); cumulative word in the boundary control (`control.c:125-129`) | release-call ordering (synthetic); E6 V1 hook (EX-O) |
| Worker inbound, exit sweep | cell 11 and its value (public) | counted | `boundary_zero` at the `done` gate and `final_zero` after reap (`check_terminal_erasure.py:45-50`) | before `done`; the reversed-order mutation is rejected (`:133-142`) |

**Where support for last-use clearing is credited.** I searched every reference
to `ActorAuthorityTests`, "last use", "last declared", "erase" in `docs/`,
`tests/*.md`, suite READMEs, `tests/catalog.json`, `runner/README.md`.

- Host last use is stated as behavior in the erase rule, `EXTENSIONS.md:81-82`,
  the T17 note (`docs/architecture.json:1074`, rendered `ARCHITECTURE.md:239`),
  inventory row a4 (`architecture.json:9873-9874`), footprint fw7
  (`docs/footprint.json:334`) and the class comment at
  `AuthorityCustody.swift:247-249`. Every one is a mechanism statement with
  source support. The contract grade is `source_read`. Row a4's only check is
  `actor_handoff_mutations.py`, scoped to outbound aliasing and premature
  outbound erasure. fw7's `pins` for `runActorAuthorityTests` reads "Custody,
  delivery acknowledgement/equality and quiescence-qualified teardown". The
  authored sentence at `ARCHITECTURE.md:403-404` credits "copying, parked
  acknowledgement, settlement and quiescence dependencies". `tests/COVERAGE.md`
  does not mention host custody clearing.
- T17 lists `runActorAuthorityTests` in its check column beside a note that
  includes the last-use sentence. Topology-edge citations carry no assertion
  scope; the generator states that citation checks establish existence only.
  I read this as source support for the note, not test credit.
- The one place that credits an observation of host last-use clearing is the
  test comment at `ActorAuthorityTests.swift:467`.
- Worker last use is credited by footprint fw8's check `pins`
  (`docs/footprint.json:409`: "Terminal/last-use erasure controls distinguish
  authority publications from process storage") citing `terminal_erasure`.
  `tests/COVERAGE.md:206-207` and the harness README (`:525-538`) credit
  fixed-capacity and before-`done` erasure and name two rejected mutations;
  neither claims a last-use mutation.

**Observation and inference kept apart.** Observed (EX-O, internal driver,
build `8b5de2b2`): private custody was cleared between two hooks that bracket
the last transfer, before teardown, and was not cleared when that transfer never
ran. Inferred from source: the `defer` is the clearing site in V1 and
`finish()` in V2. Not observed anywhere: private custody clearing at teardown
by bytes (the buffer is unmapped in the same call); the unwritten tail of an
oversized native return at HEAD (EX-A capture absent; source re-read only).

### 1.3 Plausible treatments

| # | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| T1 | Assertion/coverage repair: make the comment at `:467` say what the read shows | `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift` | No (`runner/Tests`) | None for users. The test stops crediting last-transfer clearing. | None needed; the corrected sentence follows from `AuthorityCustody.swift:637`. |
| T2 | Correct the issue-rule account to inspected-length erasure | `docs/contract/14-extensions.surface.md:373`; regenerate with `tests/lib/python.sh docs/generate_contract_stamps.py` | No | Public meaning narrows to what WORKER already states. The `extensions` surface stamp changes in CONTRACT; the guide's table stays frozen. | The refusal or accept branch freeing without clearing the inspected length. |
| T3 | Assertion repair for T2: assert `issuer_token_erased` for the fixture-supplied oversized and maximum returns | `tests/suites/witness_contract/check_extension_boundaries.py` (near `:220-223` or in the `:279-283` and `:326-332` branches) | No | A default case gains one assertion that LOCAL output already satisfies. | `pw_probe_runner.c:862` removed: the word stays 0 for `issue-2`. |
| T4 | Reasoned retention with the limit stated at the erase rule | `14-extensions.surface.md:421` (prose under the rule) and `:447` (support `limits`); same generator | No | Readers learn that the reply reports teardown and exit clearing only. | None; no behavior changes. |
| T5 | State the extent and time meaning of `performed` and of erase-cell `value` | `docs/contract/34-equipment.surface.md:870`, `:992`; same generator. Shared with subject 4. | No | `equipment` surface stamp changes. | None; no behavior changes. |
| T6 | Host pre-teardown observer (see 1.4, "Observer decision") | `ActorAuthorityTests.swift`; optionally `tests/suites/runner_unit/actor_handoff_mutations.py`, `tests/catalog.json`, `tests/suites/runner_unit/README.md`, `docs/architecture.json` row a4 | No, if the buffer is read by reflection. Yes, if `TokenCustody.buffer` visibility is widened in `runner/Sources` (also regenerates worker identity) | A new unit assertion on an internal step. | `AuthorityCustody.swift:519` (with or without `:520`) removed while `finish()` is unchanged. |
| T7 | Execute the worker last-use sensitivity as a fourth mutation | `tests/suites/runner_c_worker_harness/check_terminal_erasure.py`, its README and catalog description | No | A default case grows by one disposable build. | `pw_probe_runner.c:937-940` removed: `consume` reports 2 erase calls and `explicit_release` aborts at the release callback. |
| T8 | Product change: publish a last-use clearing cell in the custody scope | `runner/Sources/PWRunnerCore/AuthorityCustody.swift`, `PWRunnerAuthoritySetup.swift:148`; `controller/src/porcelain_actor.rs:178`; `tests/lib/actor_evidence.py:36`; `34-equipment.surface.md:998-1003`; shape goldens | Yes (`runner/Sources`, `controller/src`); signed rebuild and worker-identity regeneration | A new public cell; three readers and fixtures change together. | A reply that reports last-use clearing when the last transfer never ran. |
| T9 | Product change: clear the whole oversized native return before freeing it | `controller/tools/pw_probe_runner/pw_probe_runner.c:860-865`; a new `control.c` mode with a nonzero tail and an extent-based scan; `WORKER.md:389-390`; `architecture.json:9845` | Yes (`controller/tools`); signed rebuild; `tests/lib/python.sh docs/generate_worker_identity.py` | The current issue-rule sentence becomes true as written. Requires either an unbounded `strlen` of a native return or `malloc_size`. | Prefix-only clearing that leaves nonzero bytes past 16,384. |

### 1.4 Recommended disposition per claim

**Observer decision (thread question 2 and 3).** No public statement credits a
check or an executed run for host last-use clearing. The behavior is stated
with source-read support everywhere it appears, and the only credit for an
observation is a test comment. Narrowing that comment (T1) leaves every stated
claim true, so an observer before teardown is not needed. I do not select T6.

If the decision is revisited, for example to keep the comment's original claim
or to give the host clause the kind of guard the worker clause has, the smallest
observer is:

- Storage: the token's private custody buffer (`TokenCustody`, 16,384 bytes),
  reached as `scheduler.custody!.tokens[0]`. Read two things and name them
  separately: the flag `TokenCustody.erased` (already readable through
  `@testable`), and the count of nonzero bytes in the mapped buffer. The
  pointer is `private`; the retained E6 driver reads it by `Mirror` reflection
  (`.tmp/contract-trio/observation-time/driver/runner/Tests/PWRunnerCoreTests/main.swift`,
  `privateBuffer`), which needs no `runner/Sources` edit.
- Where: the existing collection hook of the case "a parked recipient never
  consumes before its release..." (`ActorAuthorityTests.swift:439-444`), at
  `phase == 1`. A's phase-0 visit contains the issue and both transfers, and
  `a_to_b` is the token's `lastUseSlot` (`:433`). The host returns from
  `service` (and so from the `defer`) before it observes phase-0 completion, so
  the clear has run when B's phase-1 hook fires.
- Relative to teardown: the hook runs inside `walkSchedule`
  (`ActorScheduler.swift:411`), before `ActorScheduler.finish()` and therefore
  before `AuthorityCustody.finish()` clears, records `final_erase` and unmaps.
- Expected: nonzero count 0 and flag true at the hook. The already asserted
  `delivered` transfers (`:447`) establish that custody held the bytes when
  each transfer was serviced (`AuthorityCustody.swift:529`, `:583`).
- Mutation it must reject: remove `tokens[delivery.tokenIndex].erase()`
  (`AuthorityCustody.swift:519`, a unique anchor), with or without the flag
  line `:520`, leaving `finish()` intact. The hook then reads the token length
  in nonzero bytes and flag false, while the final flag and `final_erase` are
  unchanged. E6 V2 recorded exactly this pair of readings (208, flag unset,
  then final flag true) when the last transfer never ran.
- If the mutation is to be executed without the signed app, or a
  nonzero-before reading is wanted in the same run, use a synthetic control
  beside `runHandoffCopyBoundaryControl` (`:108-150`) instead: one token with
  `lastUseSlot` 1 and one self-delivery; publish a framed payload; `service`
  once (expect `equals` true, flag false, nonzero count equal to the length);
  store the transfer request; `service` again with `recipientUsable` false
  (answered `recipientUnavailable`, `defer` clears); expect count 0 and flags
  true while the buffer is still mapped; then `finish()`. Run the mutation as a
  further `swift_variant` in `actor_handoff_mutations.py:63-94`.
- Either form is a host observation. It adds nothing to worker coverage and
  must not be cited for it.

**Host coverage (kept separate from worker coverage).**

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-63.a, DT-124.g (`:467`) | T1, assertion/coverage repair | The comment is the only overstated credit. Suggested text: "Custody reads erased after the run; teardown sets this flag whether or not the last declared transfer ran." Keep the assertion as a final-state check: it requires one custody observation, marked erased, in the returned outcome. No further evidence would change this; `AuthorityCustody.swift:637` is unconditional. |
| DT-124.g (`:307`) | Retain unchanged | It carries no timing claim and also pins token index and `accepted`. |
| DT-63.b, .c, .d, .e; DT-124.c, .d, .f, .h, .i | Accurate; no change | E6 remains local evidence of the behavior at `8b5de2b2`, whose product source equals HEAD apart from identity bytes. It is not a registered result. |
| DT-124.a | Accurate; no change | Re-read row by row. |
| DT-124.b, X-1, X-3 | T4, retention with the limit stated | Accepted limit, to stand under the erase rule at `14-extensions.surface.md:421`: "The reply's `final_erase`, `shared_clear` and `terminal_owned_inbound_clear` cells record teardown and worker-exit clearing; last-use clearing has no reply field." A public last-use cell (T8) is a real alternative; I do not recommend it: no reader decision depends on it, teardown always clears, and it changes the wire shape and three readers. |
| DT-124.j | Retention with the limit stated | Accepted limit, for the custody support owner's `limits` at `14-extensions.surface.md:447`: "Host last-use custody clearing has no registered check; worker last-consume clearing is exercised by synthetic controls only." T6 would remove the first half of that sentence. |
| DT-128.c, .d | Accurate; covered by T5 | See worker table. |

**Worker coverage.**

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-64.a | T2, correct the account in its owner | The sentence promises more than the worker does for an empty or over-length return and names "the native allocation" where the worker clears the inspected string. Suggested `free.effect` sentence in place of "Erase the native allocation after copying.": "Erase the returned token through its inspected length and free the allocation, after copying a bounded token or on refusing an empty or longer one; bytes of a longer return beyond the inspected length are freed without being erased." It edits an existing free-text effect, so the free-text counts do not increase. T9 is the alternative that keeps the sentence. I do not recommend T9 now: every observed token is 208 to 226 bytes against a 16,383-byte bound, the unwritten bytes would lie in the heap of the actor that issued them, and WORKER and the inventory already document bounded inspection. |
| DT-64.b | Accurate; retained as the stated limit of T2 | Source establishes it. Re-executing the constructed return would not change a decision that narrows the statement to the source. |
| DT-64.c | T3, small assertion repair | Without it, a regression that drops the refusal-branch clear passes every registered case, and T2's "on refusing" clause has no asserting check. Existing case: `witness_contract/extension_boundaries` (`issue-2`, `issue-16`). `architecture.json:9845` may be aligned from "oversized tail unobserved" to "bytes beyond the inspected length not erased"; this is optional because the row is not false. |
| DT-64.d | Accurate; no change | See item (c) in the final message: whether the native issuer can exceed the bound is unknown. |
| DT-124.e, DT-125.f, X-4 | Accurate; no change | - |
| DT-125.a, .b, .c | Accurate; retain the boundary observer as it is | It establishes that every clear of the observed slot left the full field zero, at least once. It does not establish which call. No statement credits it for more. |
| DT-125.d, .e | Retain; record the correction | Worker last-consume clearing has two synthetic guards, a call count and a byte-state check at the release call. Both sensitivities are source-read. T7 would execute them; it is optional and I do not select it, because the footprint fw8 credit ("Terminal/last-use erasure controls") is true as worded. |
| DT-128.a, .b, .e, X-2 | T5, state the meaning | Accepted limit, to stand in the `ownership` definition (`34-equipment.surface.md:870`): "`performed` records that the scope's clearing operation ran over its assigned storage; it does not state that token bytes were present." And in `value` (`:992`), after "such as object/page size": "or the bytes a clearing operation overwrote, which can be zero". No behavior change is warranted: a zero-byte sweep is a true record of a sweep. |

### 1.5 Resulting user duties

- Do not conclude from `final_erase: performed`, `shared_erasure: performed`,
  a nonzero erase `value` or `last_use_step_id` that token bytes were cleared
  at the declared last use, or that bytes were present when the operation ran.
  Those cells record teardown and worker-exit operations.
- Nothing in a reply reports last-use clearing. A user who needs that fact
  cannot obtain it from the shipped app.
- No action is required of a user for DT-64. An over-length native return reads
  as `native_nonnull: true`, `token_length: 0`, token `issued_uncustodied`.

### 1.6 Implementation worklist

1. `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift:467`: replace the
   comment (T1). `runner/Tests` edit; no build-contract change.
2. `docs/contract/14-extensions.surface.md`: `:373` issue-rule sentence (T2);
   `:421` add the reply-visibility sentence (T4); `:447` extend `limits` (T4).
3. `docs/contract/34-equipment.surface.md`: `:870` and `:992` (T5; combine with
   subject 4's sentence in the same edit).
4. Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`, then
   `--check`. Review the changed `extensions` and `equipment` stamps in
   `docs/CONTRACT.md`; the guide's stamp table must remain byte-unchanged.
5. `tests/suites/witness_contract/check_extension_boundaries.py`: assert
   `observed['issuer_token_erased']` for issuer modes 2 and 16 (T3).
6. Optional: `docs/architecture.json:9845` wording, then
   `tests/lib/python.sh docs/generate_architecture.py` and `--check`.
7. Verification. Docs: `tests/run.sh --suite source_drift`. Swift test file:
   `tests/run.sh --case runner_unit/pwrunner_core_unit_executable` on the
   signed app (the file is also an input of the opt-in
   `runner_unit/actor_handoff_mutations`; rerun it before crediting it, per
   "Actor authority ownership and operation controls" in
   `tests/CHANGE-VERIFICATION.md`). Checker: `tests/run.sh --case
   witness_contract/extension_boundaries`. No signed rebuild is required by any
   selected edit.

---

## 2. DT-66 / DT-126 — equal raw handles and per-release access effects

Rule carried from the coverage map: equality of native return values does not
establish revocation.

### 2.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-66.a | REQUEST permits repeated consumption of one delivery under distinct handle references, one release per reference; the handle definition calls the value a candidate and says `raw_equal_handles` relates numbers; WORKER says handles persist apart from token bytes with no exit-time release | Public statements | yes: `docs/contract/14-extensions.surface.md:232-241`, `:930-948`; `docs/WORKER.md:414`, `:630` | SRC | AO |
| DT-66.b | Executed two-consume run: both consumes returned 1, both releases 0; fresh reads were denied at baseline, succeeded during and after the first release, and were denied after the second | Public CLI; applied B with the stated policy; worker fresh-read publications | original capture absent; the rebuilt run records the same pattern: `runs/e3_repeat/stdout.json` | EX-A; EX-O | AO |
| DT-66.c | All four queries read `deny` with `query_first`; the final phase's queries were collected before its consumes and releases, so they do not describe each later action's state | Validator queries at arrival | yes: collection precedes release (`ActorScheduler.swift:405-433`); E3 | SRC; EX-O | AO |
| DT-66.d | Both handle records still read `produced`, `release_attempted: true` in the final reply; they record production and call boundaries, not present validity | Public reply | yes: E3 | EX-O | AO |
| DT-66.e | The worker stores each candidate under its declared index, clears inbound bytes after the last declared consume, releases the stored number, and never invalidates the table entry; admission prevents a second release of one reference | Worker source | yes: `pw_probe_runner.c:933-940`, `:943-957` | SRC | AO |
| DT-66.f | The Swift test checks completed repeated consumes and release availability, not equality, release results or access between releases; the CLI lifecycle test permits either post-release result | Tests | yes: `ActorAuthorityTests.swift:453-462`; `tests/suites/witness_contract/check_extensions.py:105-107` | SRC | AO |
| DT-66.g | Limits: nothing here establishes the library's reference counting, universal revocation or the cause of errno 1 | - | yes | - | AO |
| DT-126.a | The rebuilt E3 run reproduces DT-66's pattern (reads: -1/1, 27 bytes, 27 bytes, -1/1; device and inode stable) | Public CLI | recorded so | EX-O | AO |
| DT-126.b | Producer and time of each handle field: `status` and `native_handle` from the consume slot; `raw_equal_handles` computed at assembly; `release_attempted` from the release slot's call-boundary marker, read at final collection even if the slot never completed | Assembly | yes: `ActorOrchestration.swift:489-506`; `ActorSession.swift:652`; `pw_probe_runner.c:948` | SRC | AO |
| DT-126.c | `release_attempted` means the worker reached the pre-call store; it is not evidence of entry into, return from or effect of the native call | Definition | yes: `14-extensions.surface.md:948`, `:540` | SRC | AO |
| DT-126.d | The worker never clears `handle_valid` after a release; no handle field changes on release, access loss or exit | Worker, reply | yes: `pw_probe_runner.c:943-957` | SRC | AO |
| DT-126.e | The two handle records and their two release events are identical apart from references, yet access after each release differs; only the `read_fresh` observations carry the boundary | Public reply | yes: E3 | EX-O | AO |
| X-5 | `produced`, `release_attempted: true` and a release result of 0 can be read as revocation | Reply reader | yes | EX-O | UI (no statement makes this inference) |
| X-6 | Handles are explicitly scoped by their definitions; worker `held` is not | Cross-anchor | yes; see subject 4 | SRC | AO |

### 2.2 Comparison

**Obligation as stated.**

- Owner `14-extensions.surface.md:429` (rendered `ARCHITECTURE.md:382`): "A
  release return records that native call; subsequent access is established by
  the corresponding access observation."
- Owner `:940`: "Equality relates raw numbers; declarations retain distinct
  reference identity." `:932`: "`produced` requires a completed native result
  other than -1". `:948`: "Whether the declared release action has an observed
  native call-boundary marker."
- Owner `docs/EXTENSIONS.md:106-107` (shared region): a consume result is "a
  candidate handle"; "`release` with `status: returned` | The native release
  call returned the recorded value. | Later fresh attempts and independently
  observed earlier effects." `:53-55`: "each handle is released at most once",
  in a paragraph whose subject is references.
- `docs/WORKER.md:414`: "Admission permits at most one release per handle;
  there is no public release retry or automatic exit-time native release."
  Row s37 (`:630`): "requested release is not proven revocation".

**What the producer does.** Per-reference bookkeeping only. Two references can
hold the same native number; each release passes that number to the native
call once. The reply records the consume result, a numeric equality relation,
the release marker and the release return. Nothing is derived from access.

**What readers and tests assert.** Swift, Rust and Python readers check that
handle records agree with their events (`PWRunnerReply.swift:621-631`). No
reader or test requires a post-release access result. The before/during/after
example schedules a `read_fresh` after the release for that purpose
(`14-extensions.surface.md:464-466`).

**Observation and inference kept apart.** Observed twice (EX-A, EX-O): with two
equal handles, access survived the first release and ended after the second.
Not established: why. A counting implementation in the private library is a
consistent explanation, not an observation.

### 2.3 Plausible treatments

| # | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| T1 | Reasoned retention; the limit is already stated | none | No | None | - |
| T2 | Product change: invalidate the table entry after release, or record a per-release access probe | `pw_probe_runner.c`, readers, surfaces | Yes | Would add an interpretation the worker cannot observe (the kernel state after release). Contrary to "witness over interpretation". | - |

### 2.4 Recommended disposition per claim

All fourteen claims: **reasoned retention, no edit** (T1). Each definition a
reader needs is already present and scoped: candidate handle, numeric equality,
call-boundary marker, and "subsequent access is established by the
corresponding access observation". The accepted limit is that sentence at
`14-extensions.surface.md:429`; it already stands beside the technical claim.

`EXTENSIONS.md:53-55` is not false: its paragraph defines references, and
admission enforces one release per `handle_ref`. In the observed run one native
number was passed to release twice, under two references. The shared region
may not gain explanation, and no false statement requires correction.

Further evidence would not change this. A discriminating observation already
exists as a schedule shape, not as an assertion: `read_fresh` after each
release (E3; the public before/during/after example). Enforcing either access
result would force a kernel answer.

### 2.5 Resulting user duties

- To learn whether access remains after a release, schedule a `read_fresh`
  after that release and read its own result.
- Do not infer revocation from a release result of 0, from
  `release_attempted: true`, or from `status: produced`.
- When `raw_equal_handles` is non-empty, do not assume the first release ends
  access; each reference's release is one native call on the same number.
- Queries collected at a phase's arrival describe that moment, not the state
  after later actions in the phase.

### 2.6 Implementation worklist

None.

---

## 3. DT-67 — redelegation contrasts: assertion authority and credited negative effects

### 3.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-67.a | The suite README says each of four contrasts "must not be credited"; the checker asserts that only for the two omitted-consume contrasts and records the result for the two weakened-policy contrasts | Suite account against checker | yes: `tests/suites/witness_contract/README.md:793-797`; `tests/suites/witness_contract/check_extension_redelegation.py:284-297` | SRC | OCC |
| DT-67.b | `chain()` does not credit reads alone; it requires both issues, issued custody, delivered and equal transfers, candidate results, known fresh bytes and failed baselines | Checker | yes: `check_extension_redelegation.py:150-158` | SRC | AO |
| DT-67.c | The principal case does not require principal credit to pass; it requires a successful native calibration and prints the credit or first break | Checker | yes: `:261-264`, `:300-303` | SRC | AO |
| DT-67.d | The authored executed support names one historical credited run; that observation cannot be recovered from a suite pass alone | Contract support | yes: `docs/contract/14-extensions.surface.md:483-494` | SRC | AO |
| DT-67.e | The branch distinction dates to `c686a05f` and v0.3.5; neither negative policy variant was newly executed; no unexpected native credit is alleged | History, limits | yes for the review's pass. LOCAL: three default batteries at `2f4d76e4` record `credited: false` for both weakened-policy contrasts (`remove_b_issuance_allowance`: B's issue returned NULL; `omit_c_extension_predicate`: C's consume returned 1 and its fresh read failed with errno 1) | SRC; LOCAL | AO |

### 3.2 Comparison

**Obligation as stated.** Owner `tests/suites/witness_contract/README.md:793-797`:
"The contrasts omit `B`'s consume, remove `B`'s issuance allowance, omit `C`'s
consume and omit `C`'s extension predicate; each must still publish its
remaining links and must not be credited, and their observations are retained
beside the principal run for comparison." The same section says at `:785-787`:
"The kernel's answers are recorded, not forced: a published NULL issue, a
failed consume or a denied read passes those assertions." The catalog
description (`tests/catalog.json:1958`) says "re-delegation credited only on
the complete chain", which is accurate.

**What the checker does (`check_extension_redelegation.py`).**

- Every contrast passes `apparatus_complete` (`:272`): exact policy hashes,
  distinct processes, phase order, every extension event published, reap.
- `complete` is true when all six link events are present (`:285`).
  `credited = complete and chain(...)['credited']` (`:286`).
- Omitted-consume contrasts: `assert not complete and not credited` (`:288-289`).
  Because `credited` is `complete and ...`, this assertion is satisfied by the
  absence of the omitted event alone. It is a statement about the submitted
  specimen's shape. It does not assert any native negative effect, such as C's
  read failing without a consume; that read is recorded.
- Weakened-policy contrasts: all six events are present, so `credited` is
  computed from native results. The branches at `:290-296` attach a comparison
  label and assert nothing about it.

**Whether the negative result is asserted or only recorded.**

| Contrast | Structural proposition | Native negative effect |
| --- | --- | --- |
| `omit_b_consume` | asserted (omitted event absent, so not complete) | recorded only |
| `omit_c_consume` | asserted | recorded only |
| `remove_b_issuance_allowance` | none | recorded only (`credited` saved to `report.json`) |
| `omit_c_extension_predicate` | none | recorded only |

So the README's "must not be credited" is enforced for two contrasts, and there
only by construction; for the other two it is not enforced. The module
docstring (`:9-11`) and the README's own "recorded, not forced" sentence state
the intended authority.

### 3.3 Plausible treatments

| # | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| T1 | Correct the suite account to the two authorities | `tests/suites/witness_contract/README.md:793-797`; comment at `check_extension_redelegation.py:266-267` | No | The credited claim matches the assertions. No verdict changes. | - |
| T2 | Assertion repair: add `assert not credited` to the two weakened-policy branches | `check_extension_redelegation.py:290-296` | No | A kernel answer becomes an enforced result of a default case and of `actors_byoxpc`. It passes on the LOCAL runs. It contradicts the suite's stated rule that kernel answers are recorded, and a different OS answer would fail the case without any product fault. | A credited chain under a policy missing the dependency. |
| T3 | Arrangement change: report the two weakened-policy credits as advisory judgments once the reporting capability carries them | checker, catalog, suite account | No | An unexpected credit becomes visible in terminal output without blocking. Not among the overhaul's selected conversions. | Same as T2, as a non-gating judgment. |

### 3.4 Recommended disposition per claim

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-67.a | T1, correction of the account in its owner | The suite's rule is that kernel answers are recorded, not forced, and the principal credit itself is not required. The contrasts qualify how the principal credit is read; they are not product assertions. Suggested text in place of the sentence at `:793-797`: "The contrasts omit `B`'s consume, remove `B`'s issuance allowance, omit `C`'s consume and omit `C`'s extension predicate; each must still publish its remaining links. The two omitted-consume contrasts must lack the omitted action's event, so their chain is incomplete and is not credited. The two weakened-policy contrasts publish all six links; whether their chain is credited is computed and recorded in `report.json` beside the principal run and is not asserted." Adjust the code comment at `:266-267` to match. Further evidence would not change this: the LOCAL reports agree with either treatment, and the choice concerns authority, not the observed value. |
| DT-67.b, .c | Accurate; no change | - |
| DT-67.d | Accurate; retain | The support entry is scoped by its `run`, `build` and `context` fields to one inspected run. A later pass adds nothing to it and is not claimed to. |
| DT-67.e | Accurate; no change | The LOCAL reports are development output; they are not cited in any permanent account. |

T3 is not recommended in this pass: the case is not among the selected
conversions and untouched cases keep their enforcement. It is the right vehicle
if a maintainer later wants an unexpected contrast credit surfaced.

### 3.5 Resulting user duties

None for users of the product. For a developer reading test evidence: a pass of
`witness_contract/extension_redelegation` does not establish that the
weakened-policy contrasts were uncredited, nor that the principal chain was
credited; read `contrasts.*.credited` and `principal.credited` in the case's
`report.json`.

### 3.6 Implementation worklist

1. `tests/suites/witness_contract/README.md:793-797`: replace the sentence (T1).
2. `tests/suites/witness_contract/check_extension_redelegation.py:266-267`:
   align the comment. Comment-only change to a default case's checker.
3. Verification: `tests/run.sh --suite source_drift` for the suite account.
   Rerun `tests/run.sh --case witness_contract/extension_redelegation` before
   crediting the case against the edited file, or record the comment-only delta
   as a reviewed exception under `tests/AGENTS.md`.

---

## 4. DT-68 / DT-127 — pre-exit worker publications beside host teardown observations

Rule carried from the coverage map: a historical `held` value does not
establish present ownership.

### 4.1 Claims

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-68.a | The equipment scope describes an "ownership state" with `held`; WORKER says the worker's authority mapping lasts through worker exit; these are different temporal scopes | Public statements | yes: `docs/contract/34-equipment.surface.md:824`, `:870`; `docs/WORKER.md:646` (row a2, "Mapping through worker exit") | SRC | CA |
| DT-68.b | In one final reply both worker scopes read `descriptor: released, mapping: held, shared_erasure: performed`, the host region scopes read mapping `released`, and both workers were reaped and absent | Public reply; worker cells beside host cells; after CLI return | original capture absent; E3 records the same combination | EX-A; EX-O | AO |
| DT-68.c | `mapping: held` is set from a successful slot 8; only slot 12 (rejected-mapping unmap) can replace it; the normal path publishes no unmap; the Python reader requires a cleanup cell for `released` and does not derive it from reap; the quiescence unit test does not inspect a worker's mapping | Source, readers, test | yes: `runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift:106-107`; `pw_probe_runner.c:715-717`, `:760-765`; `tests/lib/actor_evidence.py:100-113`; `ActorAuthorityTests.swift:182-205` | SRC | AO |
| DT-68.d | The combination cannot establish that a mapping remains accessible through a terminated worker, or that erasing a slot released its mapping; this is a temporal ambiguity, not a leak claim | - | yes | - | AO |
| DT-127.a | Worker values are decoded from the worker's evidence region during `collectOutput`, after reap: descriptor from cell 9, mapping from cell 8, `shared_erasure` from cell 11 published at the first exit sweep | Host decode of worker cells | yes: `ActorSession.swift:489`, `:625`, `:768`; `AuthoritySetupRuntime.swift:104-108`; `pw_probe_runner.c:589`, `:602`, `:820`, `:1673` | SRC | AO |
| DT-127.b | Host region and custody scopes are read after `custody.finish()`, which follows every actor's stop and reap | Host | yes: `ActorScheduler.swift:557-583`, `:184-193` | SRC | AO |
| DT-127.c | E1a, E1b and E3 show worker `mapping: held` beside a reaped actor and host `mapping: released`, for a clean exit, a SIGKILL before publication (`shared_erasure: not_present`) and a natural reap at the gate; E5 with no authority plan shows `not_required` and `not_acquired` | Public CLI | recorded so | EX-O | AO |
| DT-127.d | WORKER row a2 and the form table state the rationale | Docs | yes: `WORKER.md:646`, `:65-66` | SRC | AO |
| DT-127.e | Judgment: one field, `ownership`, documented without a time anchor, carries host values (outcome of the host's own last call) and worker values (last state the worker published before exit) | Definition | yes: `34-equipment.surface.md:870`. Neighbouring definitions give a partial anchor: "each worker's separately acquired setup publications" (`:786`), "worker setup scopes" (`:794`) | SRC | CA |
| DT-127.f | PW makes no later call on these resources; the deinitializers return at once; a host `released` stays accurate after the reply | Host source | yes: guards at `AuthorityCustody.swift:226`, `:312`, `:634` | SRC | AO |
| DT-127.g | `unresolved` records a failed call with the resource still held by the host process; `withheld_not_quiescent` records that the host did not erase | Host source | yes: `:213`, `:233`, `:238`, `:319` | SRC | AO |
| DT-127.h | WORKER explains the worker value but the ownership definition does not point to it; a reader must join `mapping: held` with `reaped`, the gate or `collection_basis` | Docs | yes | SRC | CA |
| DT-127.i | The cost is interpretive: no reader or classifier uses worker `held`; Python and Rust check that `released` and `performed` are backed by cells and do not constrain an erase cell's value | Readers | yes: `tests/lib/actor_evidence.py:100-113`; `controller/src/porcelain_actor.rs:312-358`. No test asserts worker `mapping == "held"` | SRC | AO |
| DT-127.j | Not a leak claim; process absence does not establish the disposition of other resources | - | yes | - | AO |
| X-7 | Worker `mapping: held` with `reaped` can be read as a present mapping | Reply reader | yes | EX-O | UI |
| X-8 | The present-tense risk sits where no time anchor is stated: worker `ownership` and `performed` (the cleanup-trigger wording belongs to the DT-46/120 row) | Cross-anchor | yes | SRC | AO |

### 4.2 Comparison

**Obligation as stated.** Owner `docs/contract/34-equipment.surface.md:870`
(rendered `docs/RESPONSE.md:2452`): "Named ownership states: object_name,
descriptor and mapping use not_acquired, held, released or unresolved;
shared_erasure/private_erasure use not_present, performed,
withheld_not_quiescent or unobserved." `:824`: "A scope retains operation
cells, its setup decision and ownership state." `docs/EXTENSIONS.md` makes no
statement about `ownership` values.

**What the producer does.** The host decodes each worker's published cells
after that worker has been stopped and reaped, and sets worker `mapping` to
`held` when the setup `mmap` cell succeeded. The worker keeps its mapping until
it exits and publishes no unmap on the ordinary path, so no cell can move the
value to `released`. Host scopes record the host's own `munmap`, `close`,
`shm_unlink`, `shared_clear` and `final_erase` calls, all made before assembly.

**What readers assert.** `released` requires a succeeded cleanup cell;
`performed` requires a performed erase cell; `held` is accepted as a vocabulary
member and used by no decision. This refusal to derive `released` from reap is
deliberate and correct: the host observed an exit, not an unmap.

**Observation and inference kept apart.** Observed (EX-O): the field
combination in three replies. Established by source: the time each value
describes. Not established by anything here: the state of any mapping after a
worker's exit.

### 4.3 Plausible treatments

| # | Treatment | Files | Build-contract input? | Consequence | Incorrect behavior a check must reject |
| --- | --- | --- | --- | --- | --- |
| T1 | Reasoned retention with the time anchor stated in the definition | `docs/contract/34-equipment.surface.md:870`; regenerate with `tests/lib/python.sh docs/generate_contract_stamps.py` | No | The public meaning gains a qualification; the `equipment` stamp changes. No reply changes. | None; no behavior changes. |
| T2 | Product change: rewrite worker `mapping` to `released` when the host observes the reap | `AuthoritySetupRuntime.swift`, `ActorScheduler.swift`, both readers, fixtures | Yes; signed rebuild | The reply would assert an unmap nobody observed. It also breaks the readers' rule that `released` needs a cleanup cell. | A `released` value without a cleanup observation. |
| T3 | Product change: a distinct worker value such as "held until exit" | Same, plus the vocabulary in the surface, Rust, Swift and Python | Yes | A new closed-vocabulary value for an interpretive gain only. | - |

### 4.4 Recommended disposition per claim

| Claim | Disposition | Reason and check |
| --- | --- | --- |
| DT-68.a, DT-127.e, .h, X-7, X-8 | T1, retention with the limit stated beside the claim | The producer is truthful about what each observer saw; only the definition lacks the time each value describes. Accepted limit, to follow the existing sentence at `34-equipment.surface.md:870`: "Each value records the last operation published for that resource in its scope, not an inventory at reply time. Host region and custody values come from the host's own setup and teardown calls. A worker scope's values come from cells that worker published before it exited, so worker `mapping: held` records a successful setup mapping with no published unmap, including for a worker the same reply reports reaped." Combine with subject 1's `performed` sentence in one edit. T2 would be an unsupported attribution; T3 adds vocabulary for no reader. |
| DT-68.b, .c, .d; DT-127.a, .b, .c, .d, .f, .g, .i, .j | Accurate; no change | Further evidence would not change the decision: the retained replies already show the combination for clean exit, SIGKILL and gate reap, and the timing is fixed by source. |

No discriminating check is needed for T1 because no behavior changes. If a
guard on the meaning is wanted, the existing rule is the right one and already
enforced by both independent readers: `released` without a succeeded cleanup
cell is refused.

### 4.5 Resulting user duties

- Do not read a worker scope's `mapping: held` as a mapping that exists after
  the run. Join it with that actor's `subprocess.reaped` and `owned_reap`.
- Read host `released` as the host's own completed call. Read host
  `unresolved` as a failed call that leaves the resource with the host
  process; a region scope's `cleanup_reference` then needs ownership-aware
  recovery.
- Read `withheld_not_quiescent` as "the host did not clear", not as a state of
  the region afterwards.

### 4.6 Implementation worklist

1. `docs/contract/34-equipment.surface.md:870`: append the accepted-limit
   sentences (one edit with subject 1's T5, including `:992`).
2. `tests/lib/python.sh docs/generate_contract_stamps.py`, then `--check`.
3. `tests/run.sh --suite source_drift`. No product or reader change; no signed
   rebuild.

---

## Outside the review

These are not findings of the review and are not added to it.

1. **`token_oversized` is named in the limits table and emitted by nothing.**
   `docs/limits.json:2850` (`extension_token_payload.effect`, rendered
   `docs/LIMITS.md:176` and copied into the frozen guide) says "Larger native
   results report `token_oversized`". No producer contains that string
   (`controller/src`, `controller/tools`, `runner/Sources`; zero occurrences in
   the three shipped executables at `dist/PolicyWitness.app`). `git log -S`
   shows the producer removed at `bc3abe2f`. LOCAL `issue-2` shows what an
   over-length return reads as: issue `status: returned`,
   `native_nonnull: true`, `token_length: 0`; token `issued_uncustodied`;
   transfer `custody_unavailable`. The worker's text "issued token length out
   of bounds" (`pw_probe_runner.c:861`) is absent from that envelope, and an
   empty return (`issue-3`) reads identically. This is a false statement in a
   generator input and may be corrected in its owner under the shared-region
   rule: edit `effect`, run `tests/lib/python.sh docs/generate_limits.py` and
   `--check`, then `tests/run.sh --case source_drift/limits_documentation`. The
   guide's copy stays frozen. Not a build-contract input.
2. **Low consequence.** `docs/EXTENSIONS.md:94` says a plan with no authority
   resources "records mapping as `not_required`". In the reply `not_required`
   is the worker scope's `disposition` and `ownership.mapping` reads
   `not_acquired` (EX-O E5). The sentence is loose, not false; I recommend no
   edit to the shared region.

## Consolidated worklist

Ordered; none of the selected edits touches `runner/Sources`, `controller/` or
any other build-contract input, so none forces a signed rebuild.

1. `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift:467` comment (1.6 item 1).
2. `docs/contract/14-extensions.surface.md:373`, `:421`, `:447` (1.6 item 2).
3. `docs/contract/34-equipment.surface.md:870`, `:992` (1.6 item 3; 4.6 item 1).
4. `tests/lib/python.sh docs/generate_contract_stamps.py`; `--check`.
5. `tests/suites/witness_contract/check_extension_boundaries.py` assertion for issuer modes 2 and 16 (1.6 item 5).
6. `tests/suites/witness_contract/README.md:793-797` and the checker comment (3.6).
7. If the outside-review item is accepted: `docs/limits.json:2850`; `tests/lib/python.sh docs/generate_limits.py`; `--check`.
8. Verification on the existing signed app: `tests/run.sh --suite source_drift`; `--case runner_unit/pwrunner_core_unit_executable`; `--case witness_contract/extension_boundaries`; `--case witness_contract/extension_redelegation` (or a recorded comment-only exception).

Not selected, with the condition that would select each: host pre-teardown
observer (1.3 T6) if the comment's original claim is to be kept or the host
clause is to have a guard; worker last-use mutation (1.3 T7) if executed
sensitivity is wanted; clearing the whole native return (1.3 T9) if the native
issuer is shown able to exceed 16,383 bytes; a public last-use cell (1.3 T8)
and advisory contrast credit (3.3 T3) if a reader comes to depend on them.

Claims assessed: 10 shared, 34 in subject 1, 14 in subject 2, 5 in subject 3,
16 in subject 4; 79 in total.
