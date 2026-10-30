# Independent assessment of the completed PolicyWitness workset

Reviewed endpoint: `77eb987554eef10ffa3371ffb21b235097562a78`. Review date:
2026-10-30. Execution baseline: `bf7e97faab75754efe719b0bad20e83b67762c15`.

The completed workset merits acceptance within its stated bounds. It added a
supported extension capability, improved C and Swift ownership without evidence
of a remaining extraction defect, corrected documented checking weaknesses,
and implemented a separately authorized transport repair. The final 229-case
acceptance account reconciles with the available individual reports. Its reuse
judgments are defensible after examining the executable deltas; they are not
proved merely by the account's arithmetic or hashes. The original transport
failures remain unattributed, and the protected directory still lacks its
worker-exit witness. Those are real limits, not reasons to reinterpret the
earlier runs as passing.

The frozen pytest-first proposal survives this review as a credible division
of responsibilities. The work supplies strong examples supporting its warnings
about native observation, resource lifetime, source bindings and independent
expectations. It supplies much weaker evidence for its hoped-for reduction in
total machinery. I would leave the accepted implementation in place. A migration
decision would need a bounded demonstration of the proposed reporting and
supervision boundary, rather than another conversion of convenient assertions.

This is my source-and-evidence assessment, not a new acceptance battery. I read
the frozen `0c22d256:records/workset/pytest-first.md` before comparing the history;
recovered the retired records through git; inspected consequential production,
test and generator changes; read retained native observations and controls;
and independently checked case credits, inventories and selected historical
hashes. I ran read-only analysis scripts and public `runner list`/`runner
reconcile`, but no build, native experiment, test battery or pytest prototype.
No production code, existing expectation, permanent behavior document or old
evidence was changed. I did not independently audit every generated line,
every one of the Swift declarations, or every assertion beneath the 229 cases.

Historical references below use `commit:path`, recoverable with `git show`.
Unless stated otherwise, implementation paths describe the endpoint. Run paths
are beneath `tests/out/runs/`; their bytes are local and gitignored. Statements
about commands and errors read from those bytes are observations in this review.
Statements about earlier discussions are reports in committed records; the
private conversation is not independently available here. Architectural
judgments and suggested follow-ups are my inferences.

The history preserves the assigned experiment unusually well. The preparation
amendment at `3b585196:policywitness-omni-prompt-draft.md` explicitly separated
tested source from later acceptance, defined absent-child and persistence
observations, preserved old file-action meanings, broadened D2's bounded repair
authority, and made retention depend on evidence needs. `801f7d07` supplied
ordinary acceptance/retirement authority while reserving refactor omission and
behavioral-promise decisions for the user. Judging the completed work against
the first draft alone would miss these changes.

The graph contains the stated 69 commits after the baseline, including both
merge parents. C0 was sealed at `cf0136bb` before the native and D1 branches;
the final C0.2 bytes at `67fff425` exactly match `0c22d256` (SHA-256
`9c155b77a99870ed4519bcbe9ea0c3675d964bb129a9d90d7262bd0e99c8ec6c`). E2's
`29d1c797` seal precedes the C extraction and Swift stages. D1's chain through
`cd6adaaf` was merged at `0992fa28` and accepted at `7562d24a`; D2 starts from
that accepted state and reaches main through `bb92c213`. All twelve inherited
D1 files at `67fff425:records/checks-before-check/inherited/` match their
absorption manifest and original `7562d24a` bytes. Retirement at `63858221`
removed the packages, not their recoverability.

The records also preserve authority changes at the consequential boundaries:
F1 was explicitly deferred before its later correction; the F2 investigation
stopped with a repair direction before `60010034` specified the protocol; and
the F1 red candidate `55116788` precedes its fix. These are recoverable reports
of escalation and authorization, not independent proof of every user exchange.
Commit count and orderly prose establish neither effort nor oversight quality.

The extension work establishes a narrow capability with appropriate witnesses.
The native arrangement uses separate issuer and once-sandboxed worker processes,
ordinary credentials, fresh descriptors and distinct child names at each
boundary. In `workset-native-crossed-01` / `20261029T213556Z_990dc5c9`, the eight
directory scenarios retain native JSON and independent final filesystem
observations. The raw positive row records absence at issuance and immediately
before creation, explicit truncation to zero, twenty bytes written and successful
close, followed by matching external contents after release and worker exit.
The file GID is 0 while the worker's primary GID is 20, a concrete reason the
earlier equality assumption was wrong.

| Consumed authority with matching target and predicates | Read known contents | Modify existing file | Create absent child |
| --- | --- | --- | --- |
| `com.apple.app-sandbox.read` | Observed | Write open failed | Exclusive write open failed |
| `com.apple.app-sandbox.read-write` | Observed | Native calls and external contents establish the effect | Absence, exclusive creation and external contents establish the effect |
| Either class, with no consumption, omitted predicates or a different directory | Read open failed | Write open failed | Exclusive write open failed |

All ordinary baselines succeeded. Fresh post-release opens failed in these
executions. The source and retained checker controls deliberately permit other
post-release outcomes; therefore the findings do not become a revocation
guarantee. Read-write authority enabled both tested directions; there was no
write-only class to compare symmetrically with read-only. Absent-child query
predictions remain unavailable. Neither permission-shaped failures nor matching
query/attempt outcomes acquire a stronger causal interpretation.

The correction at `b6cac0d7:tests/suites/sandbox_extensions_native/directory_check.py`
was justified. It removes the unsupported GID equality while retaining identity
comparison, and captures final filesystem observations in `finally` before
assertions and temporary-directory cleanup. Its retained controls reject eighteen
specific evidence defects and accept eight variations, including fresh access,
partial transfer and failed release after release-time observation. This is
better experimental equipment, not relaxation merely to obtain a pass. The
initial failed raw run is no longer present, so I independently confirm the
source correction and subsequent evidence, not the completeness of that lost
first execution. Recovery:
`67fff425:records/workset/directory-native.md` and `extension-follow-on.md`.

Public integration at `7426fc09` follows the observations coherently. Optional
`authority` selects bounded native classes; `write_fresh` and `create_fresh`
add separate open/truncate/write/close and metadata observations. In
`controller/tools/pw_probe_runner/pw_probe_runner.c:attempt_file_write_fresh`,
exclusive creation uses `O_CREAT|O_EXCL`; preopen `lstat` remains diagnostic;
close follows a successful open even after later failure; and a short transfer
does not invent an errno. The old `open_write` and `create` meanings remain.
The fifteen native substitution controls in
`tests/fixtures/extension_controls/write_control.c` reach the production body
under macros and independently specify call order and failure observations.

`tests/suites/witness_contract/check_extension_directory.py` records external
effects before interpretation and journals attempts before launching them. Its
cleanup requires a worker-exit witness, explaining the protected directory
discussed below. Coordinated readers, transport, ABI and live captures accompany
response schema 24; request 5 and then-envelope 8 remain. The enum mutation
anchor correction at `b565c1b0` follows new action values while retaining extra
value/gap rejection. The failed coordinated run remains failed, with replacement
source checks and a public BYOXPC witness at `workset-e2-final-01` /
`20261029T220413Z_2388f8c8`. I support E2's bounded acceptance; the native
experiment alone would not have established public integration.

The C refactor improves a real ownership boundary. Timing and exec bodies move
into private included implementation headers, while application, phase waits,
release acknowledgement and terminal publication stay visible in the worker
entry source. Exec borrows timing state and acquires its own resources inside
the attempt. Keeping one translation unit preserves existing interception
macros; separate compilation would have required additional test seams. This
choice is suitable for the bounded refactor, even though included implementation
headers do not provide link-level isolation.

My byte comparison finds the extracted timing and exec bodies once each in
the pre-refactor worker. My extraction normalization omits one trailing blank
line relative to the recorded hashes; this is a comparison convention, not a
body change. More substantively, `341f9441` changes the exec mutation recipe
to copy the full header closure and then mutate the copied exec owner. The
retained `workset-r1-01` / `20261029T223004Z_941f9f72` evidence has a 58-attempt
native ledger, six mutations rejected by the intended assertions, and two
specific missing-owner compiler refusals. The historical call-policy golden
did not change. The final F2 battery retains the same six rejection reasons.
These establish distinct things: membership, interception and selected behavior,
alongside the 204-case R1 run. Source equality alone establishes none of the
runtime claims. Recovery: `67fff425:records/workset/c-refactor.md`.

The Swift result also improves navigation and ownership: shared request and
evidence families retain their codecs and validators, host planning/result/
comparison/disposition helpers have named owners, and the run method retains
its orchestration sequence. Meson and `tests/lib/native_sources.py` explicitly
separate shared client membership from host-only processing. I compared both
run overloads and 85 bounded declaration slices against Stage 1; those slices
are exact. This is a narrower independent comparison than the implementer's
reported 91-chunk audit, and I do not substitute it for compilation or behavior.

The Stage 1 failure at `72165300` is instructive: moving `RequestKey` with
private visibility broke an existing phase-action decoder caller. Syntax
parsing and inverse body comparison missed an access boundary that compilation
found. `9af4d3d1` corrects visibility, followed by 87 passing preservation cases
in `20261029T225222Z_5ff4f3ef`. Stage 2 adapts the planner rule across all five
extracted orchestration owners, relocates the exec decoder mutation to
`PWRunnerAttemptEvidence.swift`, and preserves independent missing/shared and
host-only source membership controls. That preserves what the controls can
distinguish instead of merely making their paths resolve.

Stage 2's `workset-r2-final-01` / `20261029T231443Z_9c34b030` completed 207
cases with 205 passes. Its citation failure and BYOXPC failure remain real.
`81f5d260` repairs moved references and member-name citations; `590c5e42`
corrects a separate D2 identity-test citation already wrong before the refactor.
The nine source/build-entry replacements justify 206 distinct selected passes,
not a passing 207-case run. The later F2 repair supplies the final integrated
verification and changes product behavior. I support the extraction and its
combined acceptance, but would reject a description of the entire final delta
as a wire-preserving refactor. Recovery:
`67fff425:records/workset/swift-refactor.md`.

D1's useful contribution is its separation of represented-input currency from
semantic support. B1 would register selected claim/evidence relationships,
derive an index/census, and request applicability review when represented inputs
change. It explicitly excludes wrong attribution, missing assertions,
unregistered omissions and faithfully rendered false source material. Historical
registration and adoption reviews are supplied modeling assumptions. Thus
“no prediction failed” is evidence that the paper contract was applied
consistently to these examples, not proof that B1 discovers relationships,
detects semantic defects, or earns its maintenance cost.

The held-back history is recoverable and its limits are candid. The six-case
dataset seal matches, and my read-only verification matches all 33 recorded
historical file hashes. The correction at `58015254` makes H03 use the declared
whole-file selector and makes H04 assert removal of W50 as well as presence of
retained edges. Those were material evaluation gaps. Repeating exposed cases
with repaired equipment is development verification; it is not a second
independent held-back trial. H06 was already disclosed as delayed, and prior
repository familiarity could not be excluded. Recovery:
`58015254:records/check-support/replay/heldback.py`, `heldback-cases.json`, and
`67fff425:records/checks-before-check/inherited/heldback-review.md`.

D2's refusal to implement B1 is proportionate. The found problems justified
localized corrections, while B1 would add registrations and review state yet
leave the central semantic failures to review. The historical machine timings
do not measure adoption review cost or prove a new system would save time.
The existing need for applicability decisions survives the refusal; declining
the registry does not dispense with that obligation. A future repeated,
costly applicability failure could reopen the choice, but this workset does
not establish that need.

C1–C5 address concrete facts: general prose-link checks belong to the generator
contract rather than the limits case; worker-identity controls have their own
owner; the build account should not carry a brittle handwritten table count;
repair hints should use the canonical Python wrapper; the old launch census
cannot promise absent raw pins; and release prose should name both existing
baseline gates. I inspected their source/diffs and the generator/dispatcher
routes. The later C1b citation correction qualifies the initial D2 acceptance;
it was not hidden as a refactor effect. Neither current citations nor faithful
generation establish that a cited assertion supports the prose. The documented
different discovery scopes remain legitimate bounded contracts. Recovery:
`67fff425:records/checks-before-check/{ownership,traces,implementation,acceptance}.md`.

F1 is a demonstrated checking defect with a sound repair. Before the repair,
the host-source guarantee included extension APIs while the implementation's
eight-symbol set omitted them; its own controls generated expectations from
that same set. `55116788` supplies a separately authored list. The retained red
run `20261030T024703Z_892e823d` has exactly 21 missed extension rejections.
`8ceb04ea` adds the three promised names and omission sensitivity. In the final
retirement run I inspected 14 accepted and 102 rejected snippets, eleven
single-symbol omissions losing exactly nine rejections each, and complete
restoration. Exact diagnostic keys prevent a parser failure from masquerading
as detection. Source-scope mutations cover Swift and the C shim.

That evidence supports the stated literal-form convention. It is not complete
Swift/C semantic analysis, and computed names remain outside the guarantee.
The separate artifact check's rejection of direct sandbox imports did not
repair the source promise. Conversely, the source-check defect never
established that production host code actually called an extension API. Pytest
would not have fixed the circular expectation authority; independently authored
cases were the decisive change.

Workset F2 deserves its own assessment because it changed execution transport.
The original two 4097 errors do not identify their cause. Forty-eight ordinary
requests on each of the Stage 1 and Stage 2 builds, and one passing original
workload on Stage 1, did not settle attribution. The later copied-source,
instrumented run did expose a particular lost refusal. I inspected the raw
trace for host generation `37509@1793319609.745637`: sequence 14 fires the prior
owner's exit timer, 15 receives `f2-observe-public-07`, 16 records failed
admission, and 17 invokes the prior owner's exit. The request has no reply
encoding event. That positive refusal observation is stronger than inferring
nonexecution from missing events. Instrumentation perturbs timing, so it does
not establish the same mechanism for the original failures.

Separate deliberate controls establish why generic retry is unsafe: 4097 can
accompany a refused request or a completed append effect whose reply was lost.
The proposed repair therefore moves retry before specimen submission, using
an effect-free reservation on the same authenticated connection. In
`PWRunnerReservation.swift`, one lock owns grant/expiry/submission transitions,
and abandoned or executed slots do not become free again. In
`PWRunnerClientSession.swift`, retry is restricted to acquisition; submission
is marked invoked before the RPC call; stale callbacks are associated with
attempt identities; and post-submission errors finish without reacquisition.
The controller invokes one helper. This is a coherent no-replay boundary,
without a promise of reliable replies or exactly-once delivery.

Protocol 2 and envelope 9 correctly distinguish client observations from host
results. Request 5 and host response 24 remain. Missing or rejected client
capture cannot establish noninvocation, and control refusals are not fabricated
host results. Old execution fallback is removed while old registry records
remain inspectable/removable. Compatibility evidence is bounded: a control
fixture represents the old protocol and a constructed old registry record
exercises current cleanup; a historical old service binary was not run.
That is sufficient for the specified refusal/cleanup boundary, not a broad
historical interoperability claim.

The nine reservation arrangements in the final run retain verified cleanup.
I examined the lost-execution and lost-helper-capture raw requests, traces and
effect observations: each selected specimen has one admission/worker entry and
one byte `78`, rather than duplicate append effects. The first envelope reports
`xpc_error` with submission `invoked` and null host result; the second reports
`missing_runner_client` with no recovered transport claim. Lost-grant evidence
shows absence before later successful acquisition and a single eventual byte.
These are strong selected controls alongside the normal signed workload, not
measurements of production loss frequency. Evidence:
`f2-controls-02` / `20261030T001949Z_1c855119` and
`f2-reservation-final-01` / `20261030T014533Z_3f5dbde2`, under their
`runner_byoxpc` case artifacts.

F2 also exposed failures in its own changes. Runtime relocation after refused
Desktop-access prompts requires a new run; it does not explain every earlier
failure. The unchanged caller-auth requirement then caught loss of native
NSError details when generic interruption callbacks won the race. Removing
those callbacks retained the RPC's error owner; the next failure showed that
`localizedDescription` still omitted route detail. `4407d0ae` retains a bounded
debug description with fallback and explicit truncation. The separate
`f2-native-route-04` / `20261030T014440Z_1028993a` result is therefore valuable
regression evidence, not redundant success. Recovery:
`67fff425:records/workset/f2-investigation.md` and `f2-reservation-design.md`.

The acceptance account withstands the mechanical checks I performed:

| Credited source of results | Distinct required cases | Review observation |
| --- | ---: | --- |
| `f2-reservation-final-01`, `20261030T014533Z_3f5dbde2`, source `4407d0ae` | 212 | Selected retained passes from a run that actually completed 225 pass / 4 fail |
| `f2-reservation-replacements-01`, `20261030T020912Z_f6e7fb69`, source `8500baff` | 15 | Selected replacements from its 17 passes; two source checks are superseded below |
| `workset-final-retirement-01`, `20261030T025834Z_b1b498cd`, source `63858221` | 2 | Current source/structure and generator/prose-link replacements, including F1 |
| Total required | 229 | No duplicate IDs; exact match to the full run's selected plan |
| `f2-native-route-04`, `20261030T014440Z_1028993a` | Separate caller-auth | Completed pass, excluded from the 229 total |

Every credited row matches a completed passing individual report and a
successful invocation with no invocation harness error or recorded sleep.
The full run's four suite errors remain associated with its four failed
owners. The three app-using acceptance runs have byte-identical before/after
inventories, SHA-256
`9529b7f22ca49559a3aee9200fd4ac9fe83268351576dc77d1c501e8f13cd4da`.
The current app has the same path set, modes and file hashes. I did not perform
a new signature verification; identical bytes and retained signing observations
are the basis for this review's identity statement.

Selection changes are explicable. The baseline catalog had 238 cases, 199
default. E2 adds native directory, fresh-write native controls and public
directory coverage, reaching 241/201. F2 adds retirement observations,
reservation controls and client-session controls, reaching 244/202. The final
required selection is 202 defaults, 21 BYOXPC cases and six explicit native/
refactor witnesses. Counts measure selection/accounting, not the number or
independence of assertions: the Swift executable alone reports 488 tests,
and the native directory case contains eight scenarios.

The reuse judgment depends on a small, inspectable executable delta. Between
`4407d0ae` and `8500baff`, the only Rust change is embedded Python under
`#[cfg(test)]`; the production prefix is identical. Three suite-local Python
owners recapture deliberately authored host variants so their envelope-9
carrier matches, while preserving original live envelopes and malformed outer
controls. Reader admission was not weakened. Registry recovery adds public
invalid-marker and old-record cleanup controls. All changed owners reran,
together with Rust and source checks. Shared readers, fixtures, native/build
inputs and the app remain unchanged.

For the later F1/retirement delta, I also checked less obvious dependencies.
`witness_contract/attempt_outcome_matrix_enforced.sh` reads the changed
`check.py`, but only its unchanged `AttemptOutcome` membership text; it does
not execute the modified host-symbol rule. The Markdown reader scans Python
imports, but these edits add no parser import; direct-Python checks inspect
unchanged shell entry points. The rule owner and generator reader reran.
Thus “unchanged files” would be too broad a justification, while unaffected
executed paths is defensible here. The ledger is not an automatically complete
dependency proof; this review does not convert it into one.

The frozen counterfactual should be judged against these obligations rather
than the final file count. Its three owners—pytest, PW adapters, and external
supervision/resource owners—still make sense. The comparison below states
what the work actually adds to that assessment.

| Adaptation or failure | Plausible pytest-first change | Responsibility that remains or moves |
| --- | --- | --- |
| Native directory scenario loop and ordinary temporary preparation | Named parameters, function-scoped inputs and normal fixture teardown can replace loop/report boilerplate | Correct authority controls, absence before issuance, native effects, token confinement, and capture before destructive cleanup |
| C header extraction and Swift family moves | Shared build fixtures and parameterized mutation names may simplify preparation | Exact copied source closure, interception, explicit client membership and intended rejection reasons |
| F1's omitted symbols | Independently declared examples can become individually reported cases | Independent expectation authority and omission sensitivity; collection cannot discover an omitted promise |
| D1/D2 citation and applicability work | Framework node identities can replace some names and outcome formatting | Discovery scope, assertion adequacy, input identity and applicability review; moving test names itself creates citation maintenance |
| F2 native loss controls | Ordinary command fixtures and per-arrangement reports may consolidate setup | Production reservation semantics, independent effects, unknown execution, no replay, launchd ownership and durable cleanup |
| Envelope-9 fixture failures | Parameters and fixture builders can centralize coherent constructed carriers | Distinguishing authored host variants from transport-corruption tests and preserving original live bytes |
| 229-case replacement credit | Framework phase reports can replace generic start/end bookkeeping | Stable logical identities across Rust/Swift/native adapters, source/equipment binding, historical failures and reviewed reuse |

C0.2 scenarios C, D, F and G receive substantial support: extension phases
remain one worker experiment; moved native owners require real interception;
external resources survive missing terminal evidence; and generated/cited
agreement does not establish semantic truth. Scenario A's proposed independent
case identities and phase reports remain plausible advantages, but the work
does not demonstrate an implemented pytest boundary preserving all of PW's
reporting semantics. Scenario E's independent offline work remains a sensible
design requirement; this workset is not a direct experiment comparing it across
engines. Scenario B's survival obligations have concrete analogues in lost
helper/worker evidence, but F2's product-helper loss is not an executed test of
a killed pytest session supervisor. I would not silently count it as one.

For framework feasibility I checked the versioned pytest 9.0.x documentation
(identifying 9.0.2), rather than assuming current APIs. Collection modification
and completion hooks expose the selected items, and the runtest protocol emits
setup/call/teardown reports, with call conditional on successful setup. Those
are real primitives for the proposal; they do not implement PW's durable
selection handshake or failure policy. [pytest API reference](https://docs.pytest.org/en/9.0.x/reference/reference.html#collection-hooks)
and [runtest protocol](https://docs.pytest.org/en/9.0.x/reference/reference.html#pytest.hookspec.pytest_runtest_protocol).

There is a concrete boundary worth making more explicit than C0.2 does. Yield
fixture teardown is not entered if setup raises before yielding; the documented
alternative is explicit finalizer registration, with care around partial
acquisition. The native experiment's lost read-back and BYOXPC's unknown worker
make this consequential: durable resource ownership and evidence capture must
precede the operation that can leave an obligation, and cleanup must wait for
the appropriate exit/effect evidence. This refines the proposed adapter/supervisor
contract; it does not refute C0.2, which already requires durable ownership
before acquisition. [pytest fixture teardown guidance](https://docs.pytest.org/en/9.0.x/how-to/fixtures.html#handling-errors-for-yield-fixture).

Another implementation obligation is environmental isolation. Pytest's default
capture replaces low-level stdout/stderr handling and supplies null stdin.
That cannot be assumed harmless for PW's descriptor-sensitive equipment.
Explicit subprocess launch contracts can isolate the subject, while still
using framework reporting for the Python case. This is a cost and control
requirement already anticipated by C0.2, not evidence that pytest cannot host
the work. [pytest capture behavior](https://docs.pytest.org/en/9.0.x/how-to/capture-stdout-stderr.html#default-stdout-stderr-stdin-capturing-behaviour).

My correction to the frozen account is one of emphasis, not a retrospective
rewrite of its predictions: replacing ordinary report bookkeeping leaves a
two-way contract to design. The supervisor must receive stable selection and
resource ownership early enough to recover an interrupted run, while the
integration must preserve framework failures, missing call phases, teardown
failures and unavailable observations without inventing successful obligations.
F2's carrier adaptations show how even valid assertions can become inapplicable
when that surrounding representation changes. This cost belongs to the proposed
arrangement even if placed in a small plugin or supervisor.

The work does not show that this boundary would become as large as the current
dispatcher. Some current duplicated events, selection guards and ordinary
fixture setup really could disappear. Nor does it show net savings, a speedup,
or simpler maintenance in operation. The earlier subordinate trial's reported
95 organizational lines removed versus roughly 426 added outside controls
measures that different integration, not this architecture. Its corrected
verification and signal-handling departures remain useful warnings about
independent consumer tests and exact integration behavior. The historical D1
timings and case counts likewise cannot become a performance benchmark for an
unimplemented replacement.

Evidence preservation is adequate for the current acceptance assessment, with
explicit limits. All 36 retention entries have local directories; the 35
dispatcher run IDs match `run.json`, and the separate release acceptance ID
matches its owner record. This includes pre-existing release evidence and three
historical D1 cost inputs, not 36 new workset batteries. I confirmed the dirty
D1 cost run remains labeled with null clean source, with its source/diff account
retained. The missing older launch runs cannot supply a new census or current
coverage. The early native baseline/failed directory and E2 shape-harvest raw
runs are also absent, so their exact initial diagnostics/harvest execution are
limited to committed accounts and subsequent retained evidence. No final
credited run is missing.

The retained failures are useful: they preserve the native-control and source
adaptation history, the F2 attribution limits, the introduced native-error
regression and the F1 independent red case. Multiple source-retirement runs
carry narrower deletion evidence. The initial rough retention expectation was
not a quota and was removed in the preparation amendment. This larger set is
justified by discoveries and replacements, although record volume itself is
not rigor. Recoverability comes from fixed commits, the final checkpoint and
case-credit accounts. Repeated design/status prose makes reading slower; that
is an organization cost, not grounds to prune it during this review.

Current read-only `runner list` and `runner reconcile` return empty records,
pending cleanup, candidates and inspection errors. The protected
`/private/tmp/pw-extension-directory-uge3532e/ownership.json` still identifies
the `no_predicate-baseline` request with no runner-subprocess record and unknown
worker spawn/exit. I have no new exit witness and leave the directory protected.
Service absence and elapsed time do not resolve it. The F2 baseline worktree
at `/private/tmp/pw-f2-stage1` remains at `2de5b1c7`, and the unrelated pytest
evidence worktree remains at `6304fef5`; neither was changed. Controlled-prep
staging also remains untouched.

The matters deserving attention are therefore bounded. Preserve the unresolved
worker ownership until a suitable witness supports recovery. Keep F2's unknown
execution/no-replay and compatibility limits visible in future transport work.
Treat source conventions and generated references as scoped checks, retaining
independent omission controls when promises grow. I found no new production
defect requiring a repair or reason to reopen E2, either refactor, C1–C5, F1 or
the reservation design on the evidence inspected.

If a pytest decision becomes worthwhile, the highest-value next experiment is
a small primary-engine/supervisor boundary exercise: publish a fixed selection,
run one completed item, one item that leaves an owned child/resource while the
engine dies, and one not started item; independently verify durable accounting,
lock lifetime and cleanup evidence. Pair it with an ordinary setup failure,
later independent success and simultaneous call/teardown failures to check
report translation. Its question is whether generic scheduling/reporting can
actually be removed without recreating it in the supervisor. This is a bounded
architectural experiment, not a migration recommendation or a replay of the
subordinate trial. No such experiment was needed to settle the acceptance
claims reviewed here, and none was performed.
