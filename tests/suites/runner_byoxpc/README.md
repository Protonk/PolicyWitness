# runner_byoxpc

Runner suite for BYOXPC services. It installs a BYOXPC runner, runs the shared
smoke and blackbox scripts through `runner.mode=byoxpc`, and validates
`runner_kind` in the output.

## Invariants

- Requires launchd bootstrap from a logged-in GUI session.
- Installs a BYOXPC runner under the user scope and removes it after the suite.
- The team-matched path copies the complete runner to an owned `/private/tmp`
  directory and gives it a unique service identifier. Only that copy is signed;
  source signatures/entitlements and before/after file inventories are retained.
  The caller-auth settings must stay unchanged. The installer re-signs the
  embedded worker (with the supplied entitlements), validator and issuer (identity
  alone); their read-backs are checked after installation.
- Shared smoke and blackbox scripts receive `PW_TEST_RUNNER_MODE=byoxpc` and the
  installed service name.

## Opt-in tests

- `tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh`
- `tests/suites/runner_byoxpc/opt_in/registry_recovery.sh`
- `tests/suites/runner_byoxpc/opt_in/single_use.sh`
- `tests/suites/runner_byoxpc/opt_in/retirement_observations.sh`
- `tests/suites/runner_byoxpc/opt_in/default_location.sh`
- `tests/suites/runner_byoxpc/opt_in/entitlement_readback.sh`
- `tests/suites/runner_byoxpc/opt_in/entitlement_transfer.sh`
- `tests/suites/runner_byoxpc/opt_in/bad_neighbor_claims.sh`

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`.

- `<run>/suites/runner_byoxpc/<test_id>/artifacts/*`

Run:

```
./tests/run.sh --suite runner_byoxpc
```

The public catalog excludes these cases from the default battery. `--all` includes
them. `--case runner_byoxpc/BBX-001` selects just that specimen and its installation
dependency. Shared offline checker controls run once in their standard suites,
not again for each runner context. The external-auth case has its own invocation;
its failure does not suppress an otherwise usable team-matched runner.

The external-auth case uses the shared session helper and stages its disposable
ad-hoc runner with a unique `com.policywitness.test.*` service in a unique directory
under `/private/tmp`, so launching it does not depend on Desktop/Documents
privacy consent when the checkout or artifacts live there. Its modified plist,
signing output, and install/verify/remove results stay in the case artifacts.
Exit cleanup removes the service before deleting the temporary bundle; a failed
service removal retains the bundle and fails the case.

The wrapper installs once for selected specimen cases, continues independent
specimens after failures, and removes the runner on exit. Missing required GUI,
app, or signing equipment fails with explicit unrun selections in the public
summary. `PW_TEST_RUNNER_*` variables are private to this wrapper; select cases
instead of exporting those variables to `tests/run.sh`.

Cleanup ownership starts before installation, including failures before a runner
environment or successful install report exists. Removal warnings and lingering
registry/launchd/plist state fail the wrapper and retain staging for inspection.
A partial or uncertain installation with a pending registry record is recovered
through public removal. Uncertain installation without a record retains staging.
The durable session record stays beside the bundle; run-local receipts point to
it, so deleting output does not erase recovery state. The wrapper never pre-cleans the ordinary runner's
identifier. See `tests/fixtures/byoxpc/README.md` for the ownership contract and
`shell_helpers/byoxpc_setup` for offline failure controls.

Shared BBX file targets also use owned `/private/tmp` scratch, with before/after
artifacts and exit cleanup. Existing privacy-database entries are not modified.

`registry_recovery` runs actual CLI controls with registry and HOME paths supplied
only to child processes. It verifies pending/installed transitions, skip-bootstrap,
pending specimen rejection, filesystem write failures, ownership disagreement,
conflicts with pending cleanup, and concurrent modifying commands. Read-only
reconcile checks unregistered candidates and unknown inspection failures. A live
user-scope installation proves skipped bootout retains the running service after
plist removal and that recovery works without original diagnostic output.
Every uniquely owned service and plist must be absent before staging is deleted.

Rust unit controls separately exercise the production removal transaction with
supplied launchd observations: bootout/unlink failures, unknown/unowned state,
process loss after bootout, and failed retirement persistence. These controls
establish state transitions; the opt-in case supplies actual launchd evidence.

`single_use` retains the raw shipped-client refusal while an owner holds its
host. A concurrent public request records that same generation's refusal, waits
for observed retirement, then succeeds on a fresh generation. Append-only effects
establish one execution per successful request and none for the raw refusal.

`retirement_observations` is a bounded experiment, not a service reliability
acceptance control. It makes 48 public CLI requests with an ordinary allow-default
policy and empty probe plan: twelve each at predeclared minimum inter-call gaps
of 0, 10, 30 and 60 milliseconds, in that order. Each request has a 5000-millisecond
client timeout and a separate 15-second capture watchdog. The harness never
retries a request or waits for host retirement between calls; production
acquisition records remain in each envelope. Inputs are prepared before the
sequence and replies validated afterward. A blocking child wait avoids timeout
polling between calls; receipts retain actual start/completion times and gaps,
including capture and scheduling overhead.

The case requires GUI launchd and matching signing equipment and remains opt-in
because it observes live timing and Unified Logging. ProcessWatch is the only
full-process scanner. A separate observer queries sampled generations directly;
ESRCH or an observed different start time establishes the earlier generation's
absence. Unseen samples and missed short-lived processes do not establish exit.
A bounded post-sequence observation retains direct exits for every seen
generation before session cleanup. Missing exits, invalid envelopes, interrupted
logging or watchdog intervention make the experiment incomplete. Runner outcomes
are counted separately, including `ok`, `already_ran`, `xpc_error` and
`xpc_timeout`, without a required success ratio or causal interpretation.

`retirement/` retains every request and raw capture, per-request observations,
the selected app's provenance/inventory and case sources, generation samples and
direct exit receipts, the narrowly filtered unified-log stream, and a summary
even after an exception. Log attachment is asynchronous; no initial delay or
complete-event-coverage claim is made. A pass means the observation completed
with valid accounting and verified removal of the one owned session. It does
not establish BYOXPC reliability. Select a baseline or candidate with `PW_APP_DIR`
and use separate output directories to run the identical case against each app.

`bad_neighbor_claims` is the coexistence acceptance control. Schedule A spaces
requests and requires zero re-acquisitions. Public back-to-back (B), foreign-held
(D) and throttle-queued (E) requests must succeed with recorded re-acquisition;
every refusing generation is attributed from independent process samples and
owner requests. C retains the raw shipped-client observation. A bounded request
ends in `already_ran` without an effect while its neighbor continues holding.
The case checks that the default registry does not advertise its private session,
and keeps fixture registry-lock contention controls. A successful effect contains
exactly one appended byte. Artifacts include every attempt, generation, attribution
and the host's XPC log stream. Constructed controls reject PID reuse and unknown
holders before live scheduling.

`default_location` is the sole session using the shared default registry. It
checks the default list and real user plist, runs one specimen without
`PW_RUNNER_REGISTRY`, and verifies removal. Registry contention is a failure,
without retry. All other sessions use durable private registries; see the
[fixture recovery contract](../../fixtures/byoxpc/README.md).
