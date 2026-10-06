# Three partial BYOXPC consumer workflows

Investigation, 2026-10-06. These are exploratory observations using the shipped
CLI, copied runners and the existing exec fixture. No product code, native
probe implementation or registered test was changed. Remediation remains
separate.

## Scope and equipment

The three workflows were moving a specimen to BYOXPC, bringing an exec helper,
and repeated use of one installation. The project-location probe was deferred
at the user's request because it could require GUI responses to privacy
prompts. Every file-effect target and experimental helper executable here lived
in an owned `/private/tmp/pw-byoxpc-consumer-*` directory. No specimen targeted
Desktop, Documents or other user project locations; no privacy settings were
changed. The maintenance/reuse workflow was not run either.

macOS 14.8.9 (23J631), arm64, logged-in user scope, Developer ID Team
`42D369QV8E`. Checkout `e6ea44b`; the selected existing app reports build
`435`, `33ad847-dirty`. Its exact inventory and successful signature inspection
identify the artifact, rather than an assertion that its stamp proves a clean
build of this checkout. Live commands ran outside the automation sandbox.
No request used `_test_overrides`.

All linked output below is gitignored, local-only evidence, pinned in
`tests/RETAINED.json`, under
[byoxpc-consumer-probes-20261006](../tests/out/runs/byoxpc-consumer-probes-20261006/).
It includes the [probe driver](../tests/out/runs/byoxpc-consumer-probes-20261006/probes.py),
the copied ownership/signing driver it imports, exact specimens, command
streams, read-backs, independent file observations and checksums.

## 1. Moving a specimen to BYOXPC

### Procedure

One specimen queried and attempted three `file/open_write` operations:

1. A file permitted by the allow-default policy.
2. A file explicitly denied `file-write-data`.
3. A file denied that operation except when the process held
   `com.apple.security.cs.allow-jit`, tested using `require-entitlement`.

All three files were reset to the same known seed before each invocation.
The policy and probe plan stayed identical. The policy SHA-256 was
`c6fa82d45cda733be098eb1a82da74eb36c14e47182c1075d54f1f360f9c0670`.
This is a deliberate SBPL predicate experiment, not a test of JIT execution.

Run it once through standard mode and through four fresh external copies:
Developer ID host with entitlement true; Developer ID host with entitlement
false; Developer ID host and manually signed worker both with entitlement
true; and ad-hoc host with entitlement true and caller-auth keys removed.
Each external copy was selected once by registry ID and once by service name,
with an 11-second pause between successful invocations. The service-name
selection also required the entitlement key. Every configuration received a
negative control requiring a nonexistent key.

### Results

| Configuration | Ordinary allowed file | Explicitly denied file | Entitlement-conditioned file |
| --- | --- | --- | --- |
| Standard | query allow, write succeeded | query deny, seed preserved | query deny, seed preserved |
| Signed host, key true, unchanged worker | same | same | query deny, seed preserved |
| Signed host, key false, unchanged worker | same | same | query deny, seed preserved |
| Signed host and worker, key true | same | same | query allow, write succeeded |
| Ad-hoc host, key true, unchanged worker | same | same | query deny, seed preserved |

Successful writes independently read back as byte `0x78`; denied writes
returned `open_failed`/errno 1. All nine admitted invocations completed with
top-level `ok`. Selecting an external copy by ID or by service gave the same
effects. The response bundle ID and recorded provenance matched the selected
runner, including its registry ID and bundle path. These observations do not
turn pre-invocation binary hashes into runtime attestation.

The **false-valued host key satisfied `required_entitlements`**. The saved
signature read-back contains the boolean `false`, and the service-name request
requiring that key was admitted. This matches `entitlements_superset` in
[runner_manager.rs](../controller/src/runner_manager.rs), which tests key
membership. Admission therefore does not establish a true entitlement value,
worker possession, or the intended operation's capability.

All five missing-key controls were refused with CLI exit 2 and envelope
`tool_error`, no runner result, and unchanged target files. The external
diagnostic was `external runner does not satisfy required entitlements`.
There was no observed fallback execution.

Receipts: the `move-*` directories, particularly
[move-false](../tests/out/runs/byoxpc-consumer-probes-20261006/move-false/),
and the checked
[move matrix](../tests/out/runs/byoxpc-consumer-probes-20261006/final/move-matrix.json).
Each invocation has its specimen, raw envelope, before/after file snapshots,
summary and validation result. External copies also have per-binary signing
read-backs, registry records and verified cleanup receipts.

## 2. Bringing an exec helper

### Procedure

Build the existing [exec fixture](../tests/fixtures/exec/build.sh) and make
three copies: Developer ID with an empty entitlement dictionary; Developer ID
with the DYLD-environment exception; and ad-hoc with that same exception.
All use hardened runtime. Direct Python launches supply exactly a plain
canary and a `DYLD_LIBRARY_PATH` naming an absent owned directory, establishing
that the fixture can observe the input and the exception's effect.

Run a five-step specimen through standard mode and three external copies:
signed host without the DYLD exception, signed host with it, and ad-hoc host
with it. Each external installation supplies the same plain and DYLD canaries
through `--env`; the workers retain their build signatures. The specimen runs
each helper's `--inspect` mode, then asks the Developer ID helper to create an
allowed file and a file whose creation the specimen policy denies.

### Results

All twelve inspection reports were complete and matched their reported exec
child PIDs. Each child exited zero and reported:

- Empty environment, including no plain canary.
- Only descriptors 0, 1 and 2; descriptor 200 was unavailable.
- EOF on stdin.

The direct Developer ID control without the DYLD exception reported one
environment entry. The Developer ID and ad-hoc controls with the exception
reported both supplied entries.
Thus the empty PW reports were not a failure of the fixture to observe a
supplied environment. They agree with the worker's explicit empty exec
environment. They still do not measure the host or worker's own environment.

In all four runner configurations, the helper's allowed write created a file
containing `exec_fixture: wrote by helper\n`. Its denied write produced
`exec_failed`, child exit 3, and stderr naming `Operation not permitted`;
the denied file remained absent. The `process-exec*` query allowed launching
that child. All four top-level runs were `ok`, even though each included the
failed child operation. The query, run summary and helper's internal operation
answer distinct questions.

Receipts: the direct controls under
[baseline](../tests/out/runs/byoxpc-consumer-probes-20261006/baseline/),
the `helper-*` directories, and the checked
[helper reports](../tests/out/runs/byoxpc-consumer-probes-20261006/final/helper-matrix.json).
The reports include actual environment counts, descriptor observations and
child PIDs, not an interpretation of missing stdout.

## 3. Repeated use of one installation

### Procedure

One fresh Developer ID installation receives `runner verify`, an immediate
file-creation specimen, another request after host retirement with a short
client budget, and three serial specimens with 0.4 seconds of consumer
processing time between them. Each request owns a unique initially absent
file, so an effect cannot be mistaken for another request's work.

After an 11-second pause, send an ordinary two-step specimen: exec
`/bin/sleep 3`, then create its unique file. Give the CLI a 700 ms client
deadline. Observe the file after the CLI returns without retrying the request.
No override extends the worker lifetime. Save exact owned launchd job listings
and monotonic elapsed times; watch files at approximately 100 ms intervals.

### Results

| Invocation | CLI wall time | Runner outcome | Independent effect |
| --- | --- | --- | --- |
| Immediately after successful `runner verify` | 0.020 s | `already_ran` | No file |
| After retirement, 1,500 ms client budget | 1.577 s | `xpc_timeout` | No file during the 12.1 s follow-up watch or at final observation |
| Serial specimen 0 | 0.201 s | `ok` | File created |
| Serial specimen 1 | 6.215 s | `ok` | File created |
| Serial specimen 2 | 10.244 s | `ok` | File created |
| Sleep then create, 700 ms client budget | 0.793 s | `xpc_timeout` | Absent at return; present later |

Before the short-budget request, launchd reported the previous host not
running with exit code zero. Immediately after the in-flight timeout it
reported a running host. The final listing reported that host retired with
exit code zero. The job listings report `minimum runtime = 10`; measured
waiting depends on launch history and is not a fixed interval from the prior
CLI's return.

The in-flight file first appeared **2.557 seconds into the post-timeout
watch**, which began after the timeout envelope and a job-state snapshot.
It had been absent in the snapshot taken immediately after CLI return. No
retry occurred. This establishes that work from this request continued after
the client's timeout. The timeout envelope itself contains no completed-step
reply, and the later file is separate observation, not a reconstructed reply.

The earlier queued timeout's absent file establishes only the observation
window's lack of an effect. It does not establish cancellation as a general
property. The successful serial specimens demonstrate the route can support
a batch with sufficient client budgets, while immediate use after verification
can still reach the retiring host's terminal admission state.

Receipts: the [batch directory](../tests/out/runs/byoxpc-consumer-probes-20261006/batch/)
and [watch summary](../tests/out/runs/byoxpc-consumer-probes-20261006/final/batch-watches.json).
Raw watches retain every file observation, and each command records its exact
argv, exit status and elapsed time. No outer harness timeout occurred.

## Completion and limits

The three workflows comprised ten manual configurations, 24 `run` envelopes
and one management `verify` invocation. All 24 run envelopes passed the
independent consumer validator. The check also compared the common transfer
policy hash, response/provenance identities, independent effect bytes and
explicit helper reports. These counts describe completed observations, not
24 successful operations or new registered test coverage.

Eight external installations were removed through the existing session
cleanup helper, with service, plist and registry absence verified. The final
registry matched the initial registry, no experiment-owned processes remained,
and the source app inventory was unchanged. Fixture files were copied into
the local evidence before their owned temporary directory was removed.

These probes establish behavior on one machine and artifact, with one
Developer ID team plus ad-hoc signing. They do not cover system scope,
other teams, other macOS versions, project-location/privacy behavior, arbitrary
consumer helpers, or the deferred maintenance/reuse workflow. Their useful
feedback is the separation between selection and capability, successful
launch and helper effect, and client timeout and continued execution. No
repair is selected by this report.
