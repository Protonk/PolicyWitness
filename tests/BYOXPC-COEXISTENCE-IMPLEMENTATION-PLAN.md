# Absorb BYOXPC host contention and keep test runners off the shared registry

BYOXPC requests fail intermittently with `already_ran` when the host they reach
has already given its single claim to another request. The
[investigation](BYOXPC-BAD-NEIGHBOR-INVESTIGATION.md) reproduced three ways this
happens, without relying on chance:
- our own previous request's host is still inside its exit delay;
- another authorized client holds a running host;
- another client's connection queued ahead of ours during launchd's 1 s respawn
  throttle.

The other client learns our service name from the shared default registry,
where every test session installs. Test installs and cleanups are also refused
immediately whenever another process holds that registry's lock.

The intended result is that a request reaching an occupied host waits for that
host to exit and is then served by a fresh one, within the deadline it already
has, with each refused attempt recorded. Test sessions stop advertising
themselves in, and contending for, the shared registry. The default registry
location keeps one live case.

The host's single-claim semantics, its `already_ran` refusal, the launchd/XPC
transport and the ownership and cleanup rules stay as they are. Two things are
deliberately not attempted: relying on launchd to queue later connections for
the next host, and narrowing how long the production installer holds the
registry lock. The investigation's [design determinations](BYOXPC-BAD-NEIGHBOR-INVESTIGATION.md#design-determinations)
give the reasons.

## Changes, in order

1. **Controller: re-acquire a host after a proven pre-admission refusal.** This
   applies to `policy-witness run` against an external runner and to
   `runner verify`. Re-acquire only when every one of these holds:
   - the reply is admitted under the current response schema;
   - its outcome is `already_ran`, with empty `steps` and no `runner_subprocess`;
   - its `pid` names a live process whose executable path (`proc_pidpath`)
     equals the selected record's `executable_path`;
   - the controller has captured that process's start time (`proc_pidinfo`) at
     the same observation.

   Those facts are what make the refusal pre-admission and tie it to the
   selected runner: the host sets `pid` from `getpid()` before its claim check.
   Any other reply is handled exactly as today. Then:
   - Wait until that generation is gone: ESRCH, or the PID now has a different
     start time. Any other observation failure ends acquisition with the refusal
     as the result; an unknown observation is never retirement.
   - Then start a new client process.
   - The request's existing timeout bounds all attempts together. Add no new
     constant or attempt count; when the deadline passes, the result is the last
     refusal.
   - The admitted attempt remains the `runner_client` capture and the runner
     result, and alone defines the deny-log window and every downstream
     observation. This matters because a neighbor's specimen may run in a host
     that refused us.
   - Retain refused attempts in a new additive envelope record, each with:
     - its client capture;
     - the refusal;
     - the refusing generation's PID, start time and executable;
     - the observed exit.

   Implement this around the injectable `client` in `RunDependencies`
   (`controller/src/run_flow.rs`) and the client call in `cmd_runner_verify`
   (`controller/src/runner_commands.rs`). Pass the process observer in as well,
   so Rust unit tests can drive every branch without live processes. `libc` is
   already a dependency.

   An added field needs no version bump under
   [When a number moves](../docs/CONTRACT.md#when-a-number-moves); if you
   choose to carry one anyway, record it in `contract.json` as that section
   describes. Update, through their
   owning generators where they have one:
   - the user guide's external-runner section, explaining that a qualifying
     `already_ran` triggers re-acquisition within the existing deadline. The
     last refusal is returned when that deadline expires. A refusal can also
     reach the caller earlier if it does not meet the re-acquisition conditions
     or if a process observation fails before retirement is established;
   - the controller README's run lifecycle and its run inventory, which gains
     process reads;
   - affected shape goldens.

   The Swift runner and client do not change.

2. **Test sessions use a durable per-session registry.** In
   `tests/fixtures/byoxpc/session.py`, for both the team and no-auth variants:
   - Put the registry at
     `~/Library/Application Support/PolicyWitness/test-sessions/<service>/runners.json`,
     and record that path in the durable `session.json` before any registry
     access.
   - Pass `PW_RUNNER_REGISTRY` to every helper CLI call. Add it to
     `runner_env.json` and export it in every wrapper that runs specimens against
     the session: `runner_byoxpc/run.sh`, the `runner_byoxpc` opt-in wrappers, and
     `witness_contract/opt_in/{extensions,dossier_witness}_byoxpc.sh`.
   - Keep `HOME` real. Developer ID signing cannot find the identity under a
     redirected `HOME`, so plists stay in `~/Library/LaunchAgents`.
   - The registry lives outside staging so that a crash followed by a reboot
     still leaves an ownership record for the plist that loads at the next login.
   - Cleanup deletes the session's registry directory only after verified
     removal leaves that registry empty.
   - Document recovery in `tests/fixtures/byoxpc/README.md`: a `runner reconcile`
     candidate's label names its registry directory. Ownership still comes from
     the record inside it, never from the label.

   In the same change:
   - Remove `retire_host` and its receipt. After step 1 the first specimen no
     longer depends on it, and its treatment of a failed `launchctl print` as
     retirement goes with it. Update the fake tools in
     `tests/fixtures/byoxpc/tools.py` and the `shell_helpers/byoxpc_setup`
     controls to match.
   - Delete the uncalled `cleanup_runner_service` from `tests/lib/testlib.sh`.
     It boots out by name and ignores errors.

3. **Keep the default location live.** Add the opt-in case
   `runner_byoxpc/default_location`, using a default-location variant of the
   session helper with no override. It:
   - installs;
   - checks that the record appears in the default `runner list` and the plist at
     `~/Library/LaunchAgents/<service>.plist`;
   - runs one specimen through `policy-witness run` without
     `PW_RUNNER_REGISTRY`;
   - removes the runner with verified absence.

   This becomes the only test that holds the shared lock or advertises in the
   shared registry. A `registry busy` refusal there is a real contention report:
   let it fail, don't retry it.

4. **Revise the controls.**
   - **`single_use`:** keep the host-level observation through the shipped client
     (a second client is refused with no effect while the owner holds). Add a
     `policy-witness run` during the hold whose envelope records one refused
     attempt naming the owner's host, then an admitted attempt on a fresh
     generation after the owner's observed exit, with its effect produced once.
   - **`bad_neighbor_claims`** becomes the coexistence control:
     - Its neighbor uses the service name directly; the case also asserts that
       the default `runner list` no longer shows the session's service.
     - Schedules B, D and E through `policy-witness run` must show no
       caller-visible `already_ran`, at least one recorded re-acquire, the case's
       own attribution of each refusing generation to the session or the
       neighbor, and each request's effect exactly once.
     - Schedule A must record zero re-acquires.
     - Schedule C stays as the raw shipped-client observation.
     - Add a bound schedule: the neighbor holds past the session request's
       timeout, and the request ends in `already_ran` with its attempt record and
       no effect.
   - **Rust unit controls:** each non-qualifying reply returns without
     re-acquiring. That covers another outcome, steps present, a worker present,
     an unsupported schema, a PID running another executable, and an observation
     failure. Also cover: PID reuse counts as gone; deadline exhaustion returns
     the last refusal; the log window comes from the admitted attempt only.
   - **Registrations:** register the new and changed cases in `catalog.json`,
     the suite and fixture READMEs, `OPT_IN_TESTS.md` and `COVERAGE.md`.

## Verification

Build a signed app with `make build IDENTITY=...`. This replaces the 0.3.1 app
in `dist/`; the release evidence remains retained separately. Then run, each
with a fresh `PW_TEST_OUT_DIR`:
- the default battery, which exercises envelope consumers and shape goldens;
- `tests/run.sh --suite runner_byoxpc`, which includes
  `runner_byoxpc/bad_neighbor_claims`, `single_use` and `default_location`;
- `shell_helpers/byoxpc_setup`;
- `witness_contract/extensions_byoxpc` and
  `witness_contract/dossier_witness_byoxpc`;
- `source_drift`.

A passing battery on a quiet machine proves nothing about re-acquisition. The
acceptance evidence is the coexistence control's recorded attempts and
attributions, together with schedule A's zero.

Stop and reconsider if any of these appears:
- a live refusal whose PID does not run the selected executable;
- a re-acquired request served by a generation that had already refused it;
- a `registry busy` refusal from any session install other than
  `default_location`.

System-scope runners were not exercised. If their hosts cannot be observed
from the controller, the trigger conditions are not met and they keep today's
refusal.
