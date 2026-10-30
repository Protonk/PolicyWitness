# Responsibility and maintenance comparison

Prepared by Codex for the authorized maintenance leg, 2026-10-30. This is source
inspection and a re-examination of retained evidence, not a new execution trial.
The accepted subject is `77eb987554eef10ffa3371ffb21b235097562a78`; the candidate
and its completed assessment are frozen at
`9e46c7b94207c6baa28a1c62f4aa78defc6efb25`. Candidate paths below are relative to
`records/pytest-boundary/`; current-harness paths are relative to the repository.
The original counterfactual remains `0c22d256:records/workset/pytest-first.md`.

Three conclusions have different evidential requirements. The demonstration
establishes a **working boundary for its tested slice**. Actual edit paths and
diagnostics establish **some local maintenance benefits**. They do not establish
that **replacement is worthwhile**, which also depends on the omitted obligations,
integration work and continuing cost. Neither absence of demonstrated total
savings nor this decision to stop establishes that savings are impossible.

## Owners and potential displacement

“Disappear” below means that an adopted primary-pytest arrangement could remove
that responsibility's current implementation after the relevant cases move.
Nothing was removed from the accepted harness. Whole-file deletion does not
follow from replacing one function. Partial adoption can leave both interfaces
to maintain; that is not credited as a saving.

| Responsibility and current source owner | Demonstrated candidate owner | Maintenance disposition and limits |
| --- | --- | --- |
| Selection: `tests/lib/test_cli.py:catalog`, `select`; `tests/catalog.json`; shell `test_selected` in `tests/lib/testlib.sh` | Pytest collection/selectors; `engine.py:Journal.pytest_collection_finish`; supervisor validates and publishes received IDs | Ordinary collection, filtering and item ordering become framework behavior. The shell selection guard and catalog-to-command lookup can disappear for converted cases. Stable identities, selection metadata, defaults, dependency inclusion, requirement declarations and declared skip policy remain obligations. Most are absent from this slice, not removed by pytest. |
| Execution: `tests/lib/suite_run.py:execute`, `run_standard_command`; `tests/lib/case.sh`; per-suite `run.sh` | Pytest item/fixture execution in one engine; supervisor watches that engine and lease requests | The ordinary case invocation loop, shell start/pass/fail calls and a native variant loop disappear in the slice. Fixture setup/order/continuation become framework behavior. Native commands, raw capture, interpreter/environment checks and app invocation adapters remain. Current cases often have separate processes; a single pytest process is not equivalent isolation for arbitrary ambient state. Resource leases here last a session, not each fixture. |
| Phase reporting: `test_begin`, `_test_finish`, `write_report` in `tests/lib/testlib.sh`; `suite_run.py:reconcile`, `account`, `finish` | Pytest emits phases; `engine.py` durably appends them; `common.py:account`, `finish` validate completeness and project a summary | Shell-generated start/end channels and hand-built ordinary reports can disappear, with much of their cross-channel reconciliation. Separate body and teardown failures are naturally available. PW still owns missing/duplicate phase detection, selected-versus-started accounting, unexpected outcome policy, durable publication and terminal classification. This is a substantial move and contraction, not the elimination of result interpretation. |
| PW observations and expectations: `tests/lib/run_capture.py:RunCapture`; case readers, native fixtures and goldens; `check_exec_evidence.py:canonical_ledger`, `build_run`, `main` | Same native fixture/golden/parser; `native_adapter.py`; assertions and parameters in `test_native.py` | Actual input/output, effect witnesses, formation checks and independently authored expected values remain. Pytest improves assertion presentation and supplies iteration, not evidence semantics. `RunCapture`'s raw CLI capture and explicit timeout differ from pytest phase capture and remain useful. No savings are credited from omitting transport, admission, Swift/Rust or envelope checks. |
| Resource ownership: `tests/lib/checkout_lock.py:owned`, `Scope`, descriptor admission; `tests/fixtures/byoxpc/session.py:install`, `persist_state`, `cleanup` | Same checkout library; supervisor intent/gated launch; `resource_owner.py` cooperative owner | The checkout lock remains shared machinery. Pytest finalizers cannot replace ownership through pre-yield failure or engine death. The candidate adds an explicit engine/supervisor lease protocol. Production external-resource identity and cleanup checks remain with resource-specific adapters; the file-owning child is not a launchd/session implementation. |
| Interruption: `suite_run.py:run_standard_command`, checkout `Scope.supervise`, actual subject lifecycle equipment | Supervisor signal forwarding, grace period, engine wait; registered child exit observation; pytest phase handling | The per-item dispatch loop disappears, but stopping the engine and accounting for incomplete work move to supervision. Shared lock lifetime and subject process management remain. The candidate's one-second cancellation loop resembles existing code; `Scope.supervise` has different policy/grace periods, so reuse is not a semantics-free deletion. Escaped descendants and arbitrary compiler-tree death were not demonstrated. |
| Recovery: durable external-runner staging/session record, `session.py:cleanup`, `tests/lib/release_cleanup.py:cleanup_blocker` | `recover.py`, `supervisor.py:close_resource`, `common.py:finish`, `ExitObserver` | Restricted recovery is new candidate integration, not framework behavior. Live peer PID, nonce, transferred lock identity and independently watched exit support the demonstrated dual-death recovery. Production registry, service scope, bundle ownership and absence checks remain. A missing cooperative owner with missing exit evidence is unresolved, as the first retained failure illustrates. |
| Retention: `tests/lib/retention.py` path/owner validation, index, replacement/pruning; release cleanup guard | Same library; current-shaped `owner.json`, `plan.json`, `run.json`; investigation pins | Existing helpers and pins remain shared. Exact current JSON encoding is a compatibility choice, not an architectural requirement. Automatic protection of unresolved candidate leases is not implemented by copying the current terminal shape; see below. |
| Equipment and integrity: `test_cli.py:resolve_config`; `suite_run.py:requirements`, `execute`, sleep helpers; `tests/lib/artifact.py`; Python launch scripts | Explicit pinned venv, filtered environment, capture/configuration receipt; narrow helper/native command assertions | These checks have only a partial candidate counterpart. App provenance/signing and before/after integrity, equipment probes, dependency blocking, GUI/identity selection, sleep accounting and public CLI/configuration semantics cannot be counted as removed code. Much can be shared, but its admission/finalization hooks need an owner. |

The useful generic deletion is concentrated: discover and run items once, let
the same framework produce their phases, then validate the durable record. In
the current arrangement, shell reports, global/local events and invocation
records require reconciliation against manually selected case identities.
`suite_run.py:reconcile` also checks interpreter identity and scratch leakage;
those checks do not disappear with its event protocol. Conversely, native
receipts and an outside lifecycle witness are independent evidence, not redundant
reports to remove. A result reader cannot certify the truth of its own inputs.

The fixed obligations are an unambiguous selected set before eligibility,
accounting for every selected item without turning missing evidence into success,
preserved PW observations/expectations, protected artifact/resource ownership,
and justified cleanup/retention through interruption. Existing CLI spellings,
aliases, catalog storage and JSON report layout are interface compatibility
choices, not intrinsic requirements of the architecture. The meanings of
defaults, prerequisites and permitted skips still need explicit treatment if
those production behaviors are to be preserved; renaming their fields would
not remove the policy.

Dependencies and requirement policy could be expressed in pytest fixtures or
collection metadata. That is a prospective design choice, not something the
demonstration already solved. Reimplementing catalog selection or dependency
scheduling inside the supervisor would forfeit part of the observed boundary.
Its duplicate-ID/publication checks are admission validation, not a second
selector: the tested supervisor does not decide which ordinary item runs next.

## What is behind 458 lines

These physical counts include comments and blanks. They locate owners and do
not measure equivalent functionality. The current CLI/executor's 757 lines
cover much more than the demonstrated 458.

| Component | Count / dependencies | Cost attributable to a possible adopted design |
| --- | --- | --- |
| `engine.py`, `common.py`, `supervisor.py`, `resource_owner.py`, `recover.py` | 65 + 97 + 167 + 79 + 50 = 458 | Engine hooks, journal/validator, eligibility and resource protocol, supervision and recovery require maintained integration. The 79-line child mixes a necessary ownership role with a synthetic file, external observer rendezvous and test-release protocol; neither keeping nor deleting it estimates a real resource adapter. |
| `checkout_lock.py`, `retention.py` | 631 + 348 = 979 shared lines | Direct imports, including durable JSON writing, path/pin validation and lock/descriptor handoff. These already exist and are neither new 979-line costs nor eliminated costs. Build/test mutual exclusion still needs the lock even after replacing test dispatch. |
| `tests/fixtures/exec/control.py:ExitObserver` | Kernel-exit primitive in a 150-line fixture module | Candidate supervision/recovery directly import it. `TreeControl` and `process_snapshot` are not needed by the candidate runtime merely because they share the module. Adoption would give the shared primitive an appropriate owner and preserve its verification. |
| Pytest 9.0.2 and pinned environment | Python 3.14.9; pluggy 1.7.0, iniconfig 2.3.1, packaging 26.3, pygments 2.21.0; installed hashes in frozen `equipment.json` | Framework implementation is maintained upstream, with local obligations for packaging, hook/report compatibility and upgrade checks. Disabling plugin autoload, explicit config, FD capture and child environments are part of this tested configuration. Standard library, macOS Unix sockets/SCM_RIGHTS, flock and kqueue remain substrate dependencies. |
| `native_adapter.py`, `test_native.py` | 55 + 76 = 131; imports existing native-ledger parser | Command receipts, source closure, mutation reach and expected assertions remain case work. Historical `git show` snapshot preparation belongs to this replay, not ordinary adopted test execution. Immutable input/variant separation remains useful. |
| `observe.py`, `observe_replay.py`, `test_subject.py` | 389 + 114 + 87 = 590 | Investigation driving, independent observation and synthetic stimuli; not adopted runtime. Fault-injection controls would still need maintained regression counterparts. The current comparison's snapshot script and prose are also investigation-only. |

No candidate file is silently exempted as “just a plugin.” The engine hook
protocol and `common.py` result policy are custom harness machinery even though
pytest supplies their phase inputs. The datagram-reset correction (`4211d48b`)
and valid-journal-prefix correction (`832e7717`) both repaired this integration.
Their retained failures establish concrete continuing obligations: reap before
resource finalization, and preserve completed evidence when a later frame is
malformed. They neither refute the corrected boundary nor become maintenance
work that pytest has absorbed.

## Inherited assumptions and omissions

The candidate copies the current terminal report's plan, count/state fields and
embedded phase reports mainly to reuse output tooling. A new encoding could
derive a compact terminal view from the journal. It would still need durable
selection and trustworthy completion/resource disposition; removing a summary
does not remove that responsibility. Its fresh-output-only rule also does not
need the existing helper's entire replacement policy, although bounded paths
and retained-overlap refusal do remain necessary. These are plausible local
contractions, not evidence for replacing the harness.

Recovery imports `close_resource` from the launcher module; putting shared
closure operations with their resource owner could reduce that coupling. The
engine uses existing lock environment names as library compatibility, not as an
intrinsic pytest requirement. Conversely, the supervisor's lease ownership and
the completeness check are not avoidable leftovers: demonstrated abrupt death
prevents relying on fixture finalizers or pytest's exit status alone.

One important adoption gap is **retention of unresolved resources**. Source
inspection shows `common.py:finish` marks an account terminal even when
`pending_resources` makes it unsuccessful. `retention.py:disposition` accepts
a structurally complete failed terminal account; `prune_rows` permits deletion
of an unpinned completed run. It does not interpret candidate `resources` or
`harness_errors`. The candidate stores its lease record and resource under that
run. Therefore its encoding is not by itself a protection against pruning an
unresolved lease. This is an unimplemented candidate integration obligation,
not a newly demonstrated defect in the accepted production harness, and no
deletion was attempted. The demonstration's pins protect its evidence/resources.
Production BYOXPC equipment keeps its durable session in owned staging as well
as a receipt in output; release cleanup has a layout-specific pending-session
guard. Adoption would need equivalent durable ownership outside disposable
output, or cleanup-aware retention integration. The existing release guard does
not automatically recognize `candidate/resources/*/record.json`.

Other deliberate omissions have maintenance consequences. Skipped phases
currently fail the candidate; this is not the current catalog's declared-skip
policy. The native production and mutant items are independently parametrized;
the retained runs have a passing baseline, but general dependency blocking and
applicability when the baseline fails are not demonstrated. Full metadata,
resource-specific recovery and artifact admission/finalization could remain
shared domain code, but selecting their fixture scope and reporting failures is
new integration work. None is estimated as zero because the 458 lines omit it.

## What the real adaptation says about maintenance

The exposed C extraction replay changed source ownership and include closure,
not merely assertion syntax. Compare `0085bd54..fec0e181` for the candidate and
`341f9441` for the historical checker. Both had to copy the entry and complete
header closure, target the new `pw_worker_exec.h` owner, write mutations after
copying, and prove both implementation headers were reached. Pytest inferred
none of this. Candidate adapter/test edits were 17 added / 5 removed lines in
two files; the historical checker changed 21 / 3 in one. Different organization
and the exposed history prevent interpreting this as measured productivity.

The actual improvement is diagnostic and organizational. The retained stale
candidate ran a passing production control and reported six named
mutation-formation failures. Source inspection of the historical checker shows
a single pre-loop anchor assertion would stop its mutation loop on that absent
anchor; this leg did not run a new stale current-harness trial. Parameters
supplied execution and reporting without a handwritten
variant loop. Fixtures kept immutable common inputs apart from each variant.
The corrected replay retained 58 expected attempts, six designated native
assertion refusals and two specific missing-include refusals. The unchanged
513-line C fixture and golden ledger carried the consequential expectations.
The diagnostic benefit did not require weakening formation or exact-rejection
controls, and the outside observer did not import candidate result policy.

The benefit should not be exaggerated into avoided catalog edits. Today's
`runner_c_worker_harness/exec_control_states` is one catalog case and one shell
wrapper around `check_exec_evidence.py`; adding a mutation inside that script
does **not** add another catalog entry or shell case. The candidate has finer
item reporting, while the current harness already centralizes wrapper boilerplate
in `case.sh`/`testlib.sh`. Adding a genuinely new independently selected logical
case may benefit more from pytest collection; that broader saving is unmeasured.

There is one demonstrated reduction in duplicated declarations: candidate
`MUTATIONS` pairs each mutation with its expected assertion, while the current
checker maintains parallel `mutations` and `expected_assertions` maps keyed by
the same names. This is case-local organization, not an inherent pytest benefit.
The current checker could pair those independently authored values too. It
could also report all independently runnable variant failures after a valid
baseline, using named subtests or an explicit failure collection. The repository
already uses `unittest`/`subTest` in `tests/suites/source_drift/contract.py`.
That shows an available mechanism, not verified equivalent diagnostics for this
native case. Expected values must stay independent of production code; a shared
table must not derive the oracle from the implementation under test.

Those two current-harness improvements are reasonable at the next relevant
case edit, with existing baseline/formation/native rejection controls intact.
Neither requires a prototype now to make the architecture comparison fair.
No production edit or change to a behavioral promise is proposed in this leg.

## Decision about another experiment

The consequential uncertainty is whether the generic simplification outweighs
the integration and resource/equipment costs across the real catalog. Evidence
favoring replacement would include fewer authoritative edit locations under a
real cross-cutting change, unchanged independent failure detection, useful
diagnostics and explicit owners for all displaced obligations. Evidence against
would include the same declarations reproduced in pytest metadata/supervision,
equivalent domain edits plus protocol maintenance, or loss of a required witness.
A smaller source count or one more passing conversion alone would leave it
unresolved.

The existing C replay already resolves the narrower source-binding question:
semantic edits remain while iteration/reporting improve. Another native replay
would repeat it. Completing full selection/equipment policy or adapting a real
launchd resource would examine new responsibilities, but first implementing
their missing candidate contracts would exceed a small matched maintenance
change; the result would mix initial construction with maintenance. A compact
summary-format revision could reduce one inherited assumption without deciding
the broader cost question. None is necessary for the present decision to keep
the harness. **Zero further experiments were selected.** No new prototype,
current-harness improvement or additional historical replay was implemented.

The warranted next action is to leave the accepted arrangement in place and
consider the two local improvements when their case next changes. A future
replacement decision can revisit real selection/resource integration if a
concrete maintenance need justifies that larger investment. It is not an
unfinished prerequisite of this investigation.
