# Host path resolution and native path queries

Recorded 2026-10-14. Investigation requested against completed implementation
`2582f1e9aa0d2ca7bb867c4b3a22f9bb1b87e7e8`. Production source, contracts and the
signed app remain unchanged. Investigation equipment is committed separately;
the final native sweep uses `9aafcea`, and the explicit observer-child cleanup
recheck uses `88ba708`. This is empirical investigation, not a change to query
eligibility or another sandbox-extension acceptance gate.

## Conclusion and correction to the earlier briefing

Keep the current exclusion from ordinary usable predictions for now. Removing
it would expose native `rc=1, errno=0` as `deny` for unresolved paths even under
`(allow default)`. These returns did not discriminate the tested allow/deny
policies. Some paired operations still succeeded, with independent file effects.
Phases make the resolution dependency visible; they do not remove it.

The earlier briefing was too strong in calling the premise untested. Original
commit `9fff0f9972300151dbfdb193ceb17003cd5ac42c` describes an observed existing
versus absent path reproduction under a subpath allow rule. Its committed
regression checks the implemented exclusion; this investigation adds retained
direct native observations. The commit's explanation that absent paths always
fail with ENOENT before sandbox enforcement is too broad: creating an absent leaf
and unlinking a dangling symlink are counterexamples to that generalization.
The experiment does not establish which private API/internal layer produces the
resolution-sensitive native return.

The narrower supported account is: **on this host, unresolved path queries
returned the same denial-shaped native result across tested policy alternatives,
while actual operations had distinct, independently recorded outcomes.**
Host resolution is a conservative eligibility heuristic, not a native API
precondition, an existence guarantee at query time, or a proof about access.

## Method and equipment

macOS **26.7.1 (25G241)**, Darwin and compiler details retained with the runs;
UID/EUID 501. Targets and helpers used owned `/private/tmp` directories. No TCC
prompt was observed, no external runner was installed, and no target was placed
in Desktop/Documents/Downloads. The app remained version 0.2.8 build 597 from
`671d995`, signed with `Developer ID Application: Adam Hyland (42D369QV8E)`.
Before/after app inventories agree, and all recorded hashes still match the app.

1. **Direct native sweep.** A separately signed, empty-entitlement
   [native target](../tests/fixtures/path_query/target.c) compiles and applies one
   policy in each fresh process using the compile/apply entrypoints. The shipped
   `sb_api_validator` queries that PID with its normal PATH and NO_REPORT flags.
   After query collection has exited, the parent releases actual read, exclusive
   create, unlink or stat operations. A separate same-PID sequence removes and
   recreates paths under one fixed policy. This fixture is not the PW worker.
2. **Actual-worker confirmation.** The ordinary PW CLI runs three specimens
   with the unchanged production worker. A
   [validator observer](../tests/fixtures/path_query/validator_observer.py)
   forwards requested queries to an unchanged copy of the shipped validator and
   adds independent queries for the paths the host excluded. It saves the full
   native transcript but returns only originally requested records to PW.
   Existing anchor queries ensure every observed phase invokes a validator.
   PW therefore still reports `prediction_unavailable` for excluded queries.
   This changes collection timing; it is not an unchanged whole-system run.

Each boundary retains the submitted paths, host `realpath` result and errno,
stat/lstat identity and mode, raw native query records, actual syscall returns,
descriptor identity/content/close observations where available, and independent
before/after file state. Native results are never compared to an inferred policy
verdict to decide success. Existing-path controls calibrate predicate selection;
successful file operations require independently observed effects.

The calibrated sweep spans nine shapes: existing, absent leaf, absent parent,
dangling leaf symlink, dangling parent symlink, symlink loop, non-directory
component, non-searchable parent and mode-zero file. It pairs default-allow with
narrow-deny policies for literal, subpath and regex predicates across four file
operations. Denied/allowed existing anchors accompany every batch.

There are **219 native target processes, 231 boundaries, 924 queries and 462
attempts** in the calibrated sweep. The final actual-worker confirmation adds
three PW workers, six collections and 36 independently retained extra queries.

## Results

All **348 queries whose host path resolution failed** returned **`rc=1,
errno=0`**. That includes **168 queries under `(allow default)`**, with no deny
rules. The native result carried no error distinguishing resolution failure
from a policy denial. Existing-path controls correctly distinguished the
selected and sibling paths for all three calibrated predicate forms.

| Host resolution failure | Query count | Native query result |
| --- | ---: | --- |
| ENOENT (2), including absent leaves/parents and dangling symlinks | 204 | 1, errno 0 |
| ELOOP (62) | 48 | 1, errno 0 |
| ENOTDIR (20) | 48 | 1, errno 0 |
| EACCES (13), non-searchable parent | 48 | 1, errno 0 |

Decisive observations, retaining each channel's meaning:

| Controlled state | Native query | Operation and independent observation |
| --- | --- | --- |
| Absent leaf, allow-default policy, create query | 1 / errno 0 for both names | Both exclusive creates succeeded; each file contained the fixture's known byte. |
| Absent leaf, narrow create deny selecting one name | 1 / errno 0 for both names | Selected creation failed with EPERM; sibling creation succeeded and its byte was independently read back. |
| Dangling symlink, allow-default policy, unlink query | 1 / errno 0 for both names | Both unlink calls succeeded; both links were independently absent afterward. |
| Dangling symlink, narrow unlink deny selecting one name | 1 / errno 0 for both names | Selected unlink failed with EPERM and its link remained; sibling unlink succeeded and its link was absent. |
| Mode-zero existing file | Resolution succeeded; allow-default query returned 0 | Open failed with EACCES. Successful resolution and a native allow do not establish access. |

These are separate query, syscall and file-state observations. EPERM alone is
not promoted into sandbox causation, and no general prediction/enforcement
agreement or disagreement verdict is assigned.

The fixed-policy same-PID transition was decisive in both fixtures and the
actual PW worker. A read deny selects one path; the sibling is not selected:

| State at collection | Selected path read query | Sibling read query |
| --- | --- | --- |
| Both exist | 1 / errno 0 | 0 / errno 0 |
| Both unlinked | 1 / errno 0 | 1 / errno 0 |
| Both recreated | 1 / errno 0 | 0 / errno 0 |

The policy and target PID stay fixed. While absent, both create queries also
returned 1, although both later creates succeeded in this read-deny experiment.
The actual-worker envelopes retain the current planner exclusions in the middle
phases and recover native read predictions after recreation. Separate actual-PW
create and dangling-unlink specimens reproduce the asymmetric operation effects
beside identical extra native query returns. Production consumer checks pass.

## Calibration, verification and retained evidence

All evidence below is gitignored and available only in this local checkout.
Each run has matching ownership and terminal records, source identities, raw
streams, exact commands, app inventories and cleanup observations. Checkpoints
include named source-input copies/hashes; those are not a complete dependency
proof. No failed historical run was rewritten.

| Run | Source | Result / credit |
| --- | --- | --- |
| [Initial native sweep](../tests/out/runs/path-query-investigation-20261014/) `20261014T141457Z_d0ba808a` | `ffa6935` | One exploratory case passed. The initial regex spelling did not select the intended existing target; its raw results are retained, but it is not credited as calibrated regex coverage. |
| [Initial actual-worker confirmation](../tests/out/runs/path-query-integrated-20261014/) `20261014T141821Z_4b10c3eb` | `4be8be2` | One case passed; three specimens, six collections. |
| [Calibrated sweep and supporting checks](../tests/out/runs/path-query-calibrated-20261014/) `20261014T141953Z_88eafbea` | `9aafcea` | Ten of ten passed: both investigations, all six source-drift cases, shell script grouping and dispatcher selection. No skips/unrun. |
| [Observer cleanup recheck](../tests/out/runs/path-query-observer-recheck-20261014/) `20261014T142317Z_b080924a` | `88ba708` | One case passed after adding explicit ownership/reap receipts for the observer's native-validator children. All three specimens repeated. |

The corrected regex covers both `/private/tmp` and Data-volume spellings and
adds explicit existing-path calibration. This identifies the initial control's
failure to select; it is not evidence isolating the internals of path rewriting.
The later observer change only strengthens fixture cleanup accounting. The
native sweep and eight supporting checks retain their original source identity;
no product source or permanent behavior documentation changed afterward.

The [derived findings](../tests/out/runs/path-query-calibrated-20261014/checkpoint/findings.json)
record the counts above. Exact observations establish all 219 calibrated native
targets reaped with exit 0, and the final three PW workers, six wrappers and six
native-validator children reaped. Owned temporary directories are absent. Earlier
investigation runs also retain successful cleanup. No execution or cleanup task
remains active. An initial selection typo was refused before execution; its
console is retained in the calibrated run's checkpoint.

Reproduce with a fresh output name, outside the automation sandbox:

```sh
PW_TEST_OUT_DIR=tests/out/runs/path-query-new \
IDENTITY='Developer ID Application: YOUR NAME (TEAMID)' \
tests/run.sh --case witness_contract/path_query_observations \
  --case witness_contract/path_query_integrated
```

## Recommendation and limits

Do not simply remove `pathFilterIsUnresolvable`. It currently prevents these
resolution-sensitive returns from becoming ordinary deny predictions and
potential spurious deny examples in PAWL. The evidence supports
that conservative purpose on the tested OS, including during phases.

The account should describe the observed limitation directly: host resolution
failed; the query is intentionally withheld because tested unresolved paths
yielded non-discriminating native returns. Avoid the stronger claims that the
API cannot be called, that every file operation must return ENOENT, or that the
private implementation's internal failure location has been identified.

If investigating the query mechanism itself is a product requirement, consider
a separately identified raw-query observation mode or channel. It should retain
the actual return and a contemporaneous resolution observation without silently
promoting them into the existing ordinary prediction semantics. That would need
an explicit reader/contract design. No such feature is implemented here.

This investigation covers one OS build, local filesystem, ordinary user and
signing configuration. It does not cover every predicate, filesystem, mount,
relative-path/cwd configuration, remote namespace, authority difference or race.
Host resolution before a validator query is not atomic with that query, and
successful resolution is not sufficient to certify prediction usefulness.
No native implementation disassembly or private-library instrumentation was
performed. WebKit's [SandboxSPI declaration](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/spi/darwin/SandboxSPI.h)
confirms the path-filter calling surface; it does not supply an absent-path
semantic guarantee. Conclusions above rest on retained local observations.

The separately requested issuance-timing deferral is recorded in
`records/ISSUANCE-TIMING-OUTFLOW.md`, with 0.3.1 as a possible destination. The
execution-versus-experimental-success decision remains settled and unchanged.
