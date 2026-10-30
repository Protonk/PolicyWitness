# dispatcher

Offline contracts for public selection, configuration, execution, and evidence
reconciliation. Run `tests/run.sh --suite dispatcher`, or select `controls`,
`accounting_controls`, `cancellation_controls`, `artifact_controls`, `selection_controls`, or `retention_controls` by their full `dispatcher/<case>`
IDs. Each group runs once in its own invocation through the public command, so
a failure in reconciliation does not suppress the accounting group.

## Contract

`tests/run.sh` invokes `tests/lib/test_cli.py`. The CLI expands `tests/catalog.json`,
validates selectors and configuration, and produces a plan before writing output.
No selectors means default membership; explicit selectors form a deduplicated
union in catalog order. Dependencies appear in the plan. `--all` includes opt-ins;
`--list` is a read-only JSON description of exactly the selected plan. Relative
configuration paths resolve from the repository, even when invoked elsewhere.
`selection.suites` records requested suites; `containing_suites` lists membership
of the selected cases. Whole-app symlinks are accepted, but the controller must
resolve within the named bundle. Distinct catalog IDs cannot share a report path;
valid reporting aliases and suite inclusions remain supported.

Execution validates retention and output ownership, acquires `tests/.checkout.lock`,
revalidates, writes `owner.json` before `plan.json`, and delegates to `tests/lib/suite_run.py`. Each
ordinary case has a separate command invocation. BYOXPC specimen cases share a
single installation/cleanup lifecycle; the wrapper runs selected specimens in
separate child processes. Independent cases continue after a failing command.
Unavailable requirements or failed dependencies leave explicit unrun selections.
Ordinary commands run in their own process group. SIGINT while waiting for an
ordinary command forwards the interrupt, allows up to one second for its leader
to exit, then kills remaining group members and reaps the leader. Later cases
are not started. The summary retains completed and partial evidence and names
interruption as the reason for unfinished selections.

`dispatch.json` journals invocations and evidence. Each observed legacy case needs one
start followed by one terminal event, a readable report with matching identity,
and agreement between terminal event and report status. Reports must belong to
the selected plan. Suite inclusions reuse canonical IDs, while runner contexts
have distinct IDs. Repeating a selector executes once; actual reused evidence
still fails reconciliation.

`run.json` includes the original selectors, plan/configuration, case reports/counts, invocations,
harness errors, and one `case_results` entry per selection. `completion` counts
selected, completed, skipped, and unrun cases. Readable report counts remain
separate from missing-report failures. `ok` and process exit agree: no failed
reports and no harness errors. A case may skip only with a `skip_reason` declared
in its catalog contract. Required equipment missing is a run failure. Planning
errors exit 2 without replacing evidence.

Host and worker allowances count system sleep. For its whole execution the
executor holds an idle-sleep assertion through `/usr/bin/caffeinate -i -w` and
its own PID, launched with closed descriptors in its own session so it never
holds the checkout lock and a terminal interrupt does not end it early.
`run.json.idle_sleep_assertion` records whether it launched, whether it was
still running at the end, and any error; a failure to block sleep is printed as
a `SLEEP:` line and changes no result. Around each command the executor reads
`CLOCK_MONOTONIC_RAW`, which counts sleep, and `CLOCK_UPTIME_RAW`, which does
not, and records the gap between their advances in whole milliseconds as the
invocation's `system_sleep_ms`, copied to its `case_results`. A gap within a
millisecond either way is read skew. An unstarted invocation records null; a
failed read or a larger negative gap records null with `system_sleep_error`. An
invocation that slept gets a `SLEEP:` line naming its cases and statuses, and
a failure among them is marked not creditable product evidence. Sleep never
changes a status or `ok`.

## Independent controls

`check.py` exercises reconciliation against controlled reports/events: aliases,
crashes, silent exits, malformed or missing evidence, contradictory statuses,
rewritten events, reused paths, and removed reports. Failure scenarios generally
include a subsequent passing case. Missing/nonexecutable entrypoints instead
prove rejection happens before any execution or output replacement.

Scratch controls require ordinary finalization to remove populated scratch,
and independently require `build_tree_in_evidence` for a retained nested
`.build` and `scratch_retained` for scratch recreated after finalization.
Reported case statuses remain passing while either harness error fails the
run. Each scenario includes a later passing case and checks exact error codes.
The control records its stimulus paths and removes only those directories
after checking the child, including on assertion failure, so the parent scan
does not reject the deliberate fixtures. Child reports, events and logs remain.

`accounting_controls` runs `check_accounting.py`, which supplies independent
handoff records directly at the accounting/finalization boundary: ambiguous ownership must retain both
selections as unrun, and missing, duplicated, unexpected, or invalid result
records must never produce success. These controls bypass catalog validation
deliberately to check the executor's separate defense. A valid alias and reordered
complete results remain accepted. Inputs, summaries, diagnostics, and return
statuses are retained alongside the other controls. The same script supplies
constructed clock readings for the sleep record: equal advances and read skew
in either direction record zero, 1 ms and two seconds record exactly, and a
larger negative gap or a failed read records null with its reason. Failing
and passing invocations that slept keep their statuses and `ok`, and only the
failure's `SLEEP:` line is marked not creditable. An absent helper and one that
exits at once are recorded and reported without changing the run.

`cancellation_controls` runs the public command against three standard-context
fixture cases: one completes, one waits with a helper that ignores SIGINT, and
one remains queued. The helper must respond after a direct SIGINT before the
dispatcher is interrupted. A normal release must complete all three. Cancellation must
exit unsuccessfully within the wait deadline, preserve completed and partial
evidence, and account for the active and queued cases as unrun. Independent
execution receipts prove the queued case did not start. The existing exec
fixture's `TreeControl` and `ExitObserver` obtain peer PIDs from Unix sockets and
require kernel exit events for both active processes before test teardown can
release or kill them. This case needs macOS local sockets and process observation;
sandboxed automation may need escalation even though no PW app is launched.
Two additional scenarios guard a fixture app: normal release preserves it, and
cancellation after an independently applied mutation must retain the exact diff
and fail artifact integrity as well as execution. In every scenario, while the
active case waits, exactly one `caffeinate` names the dispatcher's PID, holds no
checkout lock descriptor and runs in its own session; it must be gone once the
dispatcher stops, and `run.json` must record it as launched and running at the
end, with zero sleep for every started invocation.

`check_selection.py` uses an independently authored tiny catalog and fixture
commands that import no test machinery. Their execution receipts record actual
case IDs, literal argv, working directory, and effective artifact configuration.
The observer uses explicit conditionals rather than Python assertions. It checks
union/order/deduplication, distinct contexts, dependencies, default/all membership,
read-only inspection, rejected flags/configuration, symlink output escapes,
artifact aliases, quiet values, required equipment, unexpected evidence, skip
contracts, and complete accounting after failures. Whole-tree byte snapshots
also catch accidental bytecode writes during inspection.
With a sandbox profile denying execution of `/usr/bin/arch`, the real Rosetta
probe fails to launch: the case requiring `rosetta` is unrun for missing
equipment with the probe's denial kept in `run.json`, while an independent
sibling runs and passes. The denial shows equipment-failure handling, not an
uninstalled Rosetta. The real catalog must keep `build_refusal_controls` free
of a `rosetta` requirement and of any dependency on the translated case.
Split bundles and colliding catalog report paths must be rejected without
execution or evidence replacement; whole-app and internal controller symlinks
must preserve the selected bundle in execution receipts.
Two runnable stub bundles also verify default and explicit app selection. The
selected controller records its own path, arguments, and bundle-local marker;
an ignored override must fail even when the fallback app is usable.

`artifact_controls` runs real file damage through the public command: missing
helper, broken signature, validly resealed stale manifest, omitted/duplicate
entries, malformed manifest, a helper escaping the app through a symlink, and
an intact bundle whose XPC host executable imports `_sandbox_check` (the host
invariance check, through `nm -u` on a compiled control binary; the valid
bundle's host is a compiled binary with no such import). For the output
target, with every signature, manifest hash and record hash consistent: an
x86_64 helper the record describes truthfully must produce exactly the
inspector's `output_target` error and the record's own `provenance` refusal;
a one-slice fat container of the same arm64 stub, whose load commands match
while the record still claims a thin file, exactly `output_target` and
`provenance_metadata`; unlisted universal code under `Contents/Resources`,
found by its header, exactly `output_target`; and the dSYM companion of an
x86_64 executable beside a helper leaves the bundle valid, since debug data is
not code.
App and worker cases must remain unrun while the independent offline case runs.
Mutations during passing, failing, and crashing commands must produce precise
final diffs covering bytes, modes, additions, deletions, and symlinks.

`tests/fixtures/dispatcher/repository.py` copies equipment and writes the
caller-supplied catalog; it contains no expected selections or result oracle.
For app controls only, it copies `seal_tool.py` into the disposable repository
as the inspector's codesign executable. That independent file-seal model
imports nothing but the standard library and knows no bundle layout; manifest
parsing, hashing, and inventories still use the real inspector. Production has
no bypass setting. Apple's signature semantics are checked separately by
`preflight/signed_artifact_controls`. `fixture_bundle.py` lays out the fake
bundles, pure Python, with a complete full-build provenance record the fixture
authors itself (nominal toolchain values, its own `otool` reading of the
stubs, and the ad hoc signature facts their linker signatures carry, which
the inspector compares with `codesign -dvv`), around a compiled XPC host stub: the suite wrapper builds
the clean stub and the control stubs once per run with
`tests/fixtures/dispatcher/build.sh` into the case artifacts and names them in
`PW_DISPATCHER_HOST_FIXTURE` (`<name>`, `<name>.imports-sandbox`, the worker
stubs `<name>.imports-clock` and `<name>.continuous-clock`, and the stand-ins
outside the output target `<name>.x86_64`, `<name>.universal`,
`<name>.one-slice-fat` and `<name>.x86_64.dSYM`); only `check_artifacts.py`
uses the control stubs. Every stub is compiled for its architecture
explicitly, the non-arm64 ones signed ad hoc as the linker signs arm64
output, so the fixture record's signature facts hold for each. Its worker clock scenarios lay a
real `clock_gettime` import at the worker path only, which inspection must
reject while the bundle stays sealed; a permitted `mach_continuous_time`
import, which must pass with that symbol in the retained import list; and
unreadable worker bytes, whose failed `nm` must be an error rather than an
empty import set. A missing stub is an equipment error, so the suite requires
clang.
Fixtures, receipts, raw stdout/stderr, exit status, plans, journals, summaries,
and `controls.json` remain in artifacts for inspection.

## Retention controls

`retention_controls` uses independent fixture checkouts and execution receipts.
It reuses `artifact.inventory` to compare retained files, modes, symlink targets
and empty directories. It checks retained siblings and overlap in all directions,
absent local retained directories, invalid/unreadable indexes, redirected paths,
completed failed runs, interrupted and ambiguous replacement refusals, and
read-only help/list/invalid requests. A case receipt observes that `owner.json`
already exists when execution starts.

Held executions prove competing operations fail even for another output path,
independent checkouts can execute, and a killed dispatcher's case keeps the OS
lock it was passed until the case is stopped, after which the lock is free and
no run completion is invented. A second scenario kills the dispatcher and then
the case process while the case's grandchild runs: the lock stays held until
the grandchild exits, and the same scenario with a case that drops the
descriptor (Python's default for its children) observes a free lock, which
the control must reject. Tests inspect the stable lock inode and retain
raw command output and receipts. The lock file must never be unlinked, including
by cleanup: otherwise a second inode could admit a competing operation.

See [the output contract](../../README.md#retention-ownership-and-execution-locking)
for the committed index fields, terminal ownership checks, default
`tests/out/runs/default`, direct-script fallback and release-acceptance output.

Pruning uses these same retention and ownership checks. `--prune` previews a
read-only snapshot; `--prune --apply` revalidates and deletes eligible completed
runs under the lock. `--prune --apply --unfinished <name>` is the deliberate
cleanup path for one interrupted/ambiguous managed run after inspection.
Selection/prune combinations and unfinished removal of retained, completed or
unmanaged output are rejected. `make prune` delegates to preview; `make prune APPLY=1` delegates to apply.
Every other supplied `APPLY` value refuses, and there is no `clean` target.

Preview briefly probes the same nonblocking lock before classification. A
simultaneous execution can receive checkout-busy from that probe and must be
retried after preview finishes. This safe contention window is intentional;
preview's busy observation is a snapshot, not a reservation or readiness promise.

Controls retain independent execution receipts and verify preview/apply changes,
completed failed runs, all keep dispositions, preview under a held lock,
`--unfinished` against each disposition, invalid indexes, retained ancestors and
descendants, symlink redirects, lock contention, and Makefile preview/apply preservation and refusal before delegation.
An actual directory-permission restriction forces unlink failure; the test
checks a nonzero apply exit, the reported error and the remaining inventory.
Standalone files and release acceptance output survive every cleanup operation.

`pytest_controls` is an opt-in control of the exec-family integration. Its external
native peer, kernel exit observations and lock inode checks are independent of
candidate summary interpretation. Deliberately unresolved fixture records are
retained inside its artifacts and are never mistaken for live checkout ownership.
Receipt controls launch a missing executable, a command whose registered context
differs from the owner's, an owner that cannot start and an owner slower than its
readiness wait; each must settle as never launched without a checkout hold, and a
sentinel legacy case must still run after the integrated failure. A same-group
child that outlives an ordinary leader exit is identified by its own socket peer
and kernel exit event; its forced exit must be recorded and, with the real native
ledger, refused. A producer close of an uncreated descriptor must leave one cached
baseline failure naming the ledger error. Availability controls move the package
target between plan collection and the prerequisite check in each direction; the
run must still finish with a named `not_started/unavailable` family, a running
legacy sentinel and a free checkout.
