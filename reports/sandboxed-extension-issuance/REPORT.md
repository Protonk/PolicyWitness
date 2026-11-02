# Sandboxed issuance pilot: Q1 and Q2

## Question status

| Question part | Status | Scope of the answer |
| --- | --- | --- |
| Q1(a): issuance | Answered within contrasts | C2 produced nonnull issuance; C3/C4/C5 returned null, in all three blocks on r1. |
| Q1(b): transfer | Answered within contrasts | Fifteen bounded publications were accepted with valid framing and transient equality; nine null-issue trials recorded dependent unavailability. |
| Q1(c): consumption | Answered within contrasts | Twelve calls returned `1`, errno `0`; three C6 decisions omitted consumption; nine calls were unavailable after null issuance. |
| Q1(d): fresh access | Answered within contrasts | All 24 first opens failed. C0/C1/C2 obtained 37 matching bytes on the second fresh read; C2/C6 and C2/C7 support the bounded findings below. |
| Q1(e): contrasts | Answered within contrasts | All five planned C2 contrasts are covered three times within r1, without coverage gaps. |
| Q2(a): observed queries | Answered within contrasts | Both forms returned `(0,0)` in C0/C1 and `(1,0)` in C2–C7, without variation across blocks. |
| Q2(b): representation | Answered within contrasts | The recorded flag/type arguments and validator source establish NONE versus path-only arguments, with no extension class alongside the path. |

This report closes the [plan](PLAN.md) after
**24 planned trials on one apparatus revision, r1**. There were no diagnostic
native reruns, correction cycles, unrun positions or pending cleanup. The
[closed state](evidence/state.json) retains the accounting. Questions are defined
in [TRACES.md](TRACES.md#questions); Q3–Q18 receive no answers from this pilot.

## Equipment and preparation

The [r1 equipment record](evidence/equipment/r1/equipment.json) retains source
snapshots/hashes, command arguments/results, signing read-backs and host facts.
Its source commit is `6ea196363dd5007f3d98d72424e0ffd044524ddb`. The ignore rule
was committed first, in `d528e236`, before any build.

| Equipment fact | Recorded value |
| --- | --- |
| Host | macOS 26.7.1, build 25G241; Darwin 25.6.0; arm64 |
| Compiler/SDK | Apple clang 21.0.0 (`clang-2100.4.1.1`); macOS SDK 27.2; deployment target 26.0 |
| Signing identity | `Developer ID Application: Adam Hyland (42D369QV8E)` |
| Signature | Strict verification passed; selected authority, runtime flag and secure timestamp read back |
| Entitlements | Absent |
| Executable SHA-256 | `67cef267c01dae2002a333ab2a5ddfbeff9f4574e8bc7bd52c3055404b0d017c` |
| Images | Linked libsandbox and libSystem; all roles reported the same 47 loaded images, with no application frameworks |
| Native environment | Exactly `PATH=/usr/bin:/bin` and `LC_ALL=C`, observed in all roles |

Products in `local/r1/` are gitignored and available only in the local checkout.
The report is readable without them. Retained read-backs include
[verification](evidence/equipment/r1/verify.stderr.txt),
[signature](evidence/equipment/r1/signature.stderr.txt),
[entitlements](evidence/equipment/r1/entitlements.stdout.txt), and
[linked images](evidence/equipment/r1/linked-images.stdout.txt).

The independent equipment comprises [pilot.c](pilot.c), [run.sh](run.sh),
[driver.py](driver.py), the [event protocol](NATIVE-PROTOCOL.md),
[read.py](read.py), and [reader_controls.py](reader_controls.py). Production PW,
the registered fixture, suite checkers and test catalog were not changed.

The [source review](REVIEW.md) accounts for acquisitions and cleanup. The
supervisor created A/B, recorded canonical paths, identities and fresh-read
baselines, then closed target descriptors before child launch. Children mapped
explicit apparatus channels, closed mapping descriptors, disabled core dumps,
resolved native functions and compiled their exact policies before application.
Neither child inspected A/B or warmed an extension before that boundary.
All 48 compilations returned nonnull, errno 0. All 24 recipient applications and
21 sandboxed issuer applications returned `(0,0)`; three C0 issuer applications
were explicitly omitted after compilation.

All 168 prescribed descriptor snapshots completed without inspection failures
or target matches. Entry snapshots contained `0–4,32–34`; later snapshots
contained `0–2,32–34`. Source inspection accounts for intervening acquisitions.
Shared-memory separation is grounded in distinct exclusive creations and
explicit descriptor associations; stat metadata is not assumed to uniquely
identify those objects. This is not a census of transient resources, Mach
rights or private library initialization.

## Coverage, schedules and trial identities

Each sequence was retained before its block began. C0/C1 were first only in
block one, for the mandatory connection checkpoint. Later blocks varied their
positions and positive/negative-control adjacencies without changing the matrix.

| Block | Recorded sequence | Schedule |
| --- | --- | --- |
| 1 | C0, C1, C4, C2, C6, C3, C7, C5 | [block 1](evidence/schedules/block-1.json) |
| 2 | C7, C3, C0, C5, C2, C1, C4, C6 | [block 2](evidence/schedules/block-2.json) |
| 3 | C6, C4, C1, C5, C7, C2, C3, C0 | [block 3](evidence/schedules/block-3.json) |

Each ID links its raw record. Each trial directory also retains original
NDJSON and ownership evidence. `evidence/checks/read-<trial-id>/` retains the
corresponding reader command and result.

| Arrangement | Block 1 | Block 2 | Block 3 |
| --- | --- | --- | --- |
| C0 | [b1-p1-C0-r1](evidence/trials/b1-p1-C0-r1/trial.json) | [b2-p3-C0-r1](evidence/trials/b2-p3-C0-r1/trial.json) | [b3-p8-C0-r1](evidence/trials/b3-p8-C0-r1/trial.json) |
| C1 | [b1-p2-C1-r1](evidence/trials/b1-p2-C1-r1/trial.json) | [b2-p6-C1-r1](evidence/trials/b2-p6-C1-r1/trial.json) | [b3-p3-C1-r1](evidence/trials/b3-p3-C1-r1/trial.json) |
| C2 | [b1-p4-C2-r1](evidence/trials/b1-p4-C2-r1/trial.json) | [b2-p5-C2-r1](evidence/trials/b2-p5-C2-r1/trial.json) | [b3-p6-C2-r1](evidence/trials/b3-p6-C2-r1/trial.json) |
| C3 | [b1-p6-C3-r1](evidence/trials/b1-p6-C3-r1/trial.json) | [b2-p2-C3-r1](evidence/trials/b2-p2-C3-r1/trial.json) | [b3-p7-C3-r1](evidence/trials/b3-p7-C3-r1/trial.json) |
| C4 | [b1-p3-C4-r1](evidence/trials/b1-p3-C4-r1/trial.json) | [b2-p7-C4-r1](evidence/trials/b2-p7-C4-r1/trial.json) | [b3-p2-C4-r1](evidence/trials/b3-p2-C4-r1/trial.json) |
| C5 | [b1-p8-C5-r1](evidence/trials/b1-p8-C5-r1/trial.json) | [b2-p4-C5-r1](evidence/trials/b2-p4-C5-r1/trial.json) | [b3-p4-C5-r1](evidence/trials/b3-p4-C5-r1/trial.json) |
| C6 | [b1-p5-C6-r1](evidence/trials/b1-p5-C6-r1/trial.json) | [b2-p8-C6-r1](evidence/trials/b2-p8-C6-r1/trial.json) | [b3-p1-C6-r1](evidence/trials/b3-p1-C6-r1/trial.json) |
| C7 | [b1-p7-C7-r1](evidence/trials/b1-p7-C7-r1/trial.json) | [b2-p1-C7-r1](evidence/trials/b2-p1-C7-r1/trial.json) | [b3-p5-C7-r1](evidence/trials/b3-p5-C7-r1/trial.json) |

The following patterns were identical across each arrangement's three
repetitions. Pairs are raw `(return, errno)`; issuance records nonnullness,
never a pointer address. **Every first recipient open returned `(-1,1)`**;
its fstat/read/close were explicitly unavailable because opening failed. Each
successful second read recorded fresh open `(3,0)`, fstat `(0,0)` with matching
identity, read `(37,0)` and close `(0,0)`. Known A bytes were
`PolicyWitness browser pilot target A\n`.

| Row | Issue / errno | Transfer | Consume / errno | Second fresh access | NONE | PATH(A) |
| --- | --- | --- | --- | --- | --- | --- |
| C0 | nonnull / 0 | accepted, equal | `(1,0)` | 37 matching bytes | `(0,0)` | `(0,0)` |
| C1 | nonnull / 0 | accepted, equal | `(1,0)` | 37 matching bytes | `(0,0)` | `(0,0)` |
| C2 | nonnull / 0 | accepted, equal | `(1,0)` | 37 matching bytes | `(1,0)` | `(1,0)` |
| C3 | null / 1 | unavailable | unavailable | open `(-1,1)` | `(1,0)` | `(1,0)` |
| C4 | null / 1 | unavailable | unavailable | open `(-1,1)` | `(1,0)` | `(1,0)` |
| C5 | null / 1 | unavailable | unavailable | open `(-1,1)` | `(1,0)` | `(1,0)` |
| C6 | nonnull / 0 | accepted, equal | omitted by design | open `(-1,1)` | `(1,0)` | `(1,0)` |
| C7 | nonnull / 0 | accepted, equal | `(1,0)` | open `(-1,1)` | `(1,0)` | `(1,0)` |

Totals: 15 nonnull and nine null issue results; 15 accepted 211-byte transfers
with valid framing and transient equality; 12 native consumes, three designed
omissions and nine unavailable consumption records. All 24 second reads were
attempted: nine obtained known bytes and 15 failed at open. Native refusal is
a published result. Dependency unavailability is explicit rather than missing
or filled with invented returns.

## Q1 answers and decision-table limits

These answers use the [plan's decision table](PLAN.md#fixed-contrasts-and-positive-controls).
Supported and withheld wording is reproduced verbatim. The first-block examples
below have the same values in the two other repetitions linked above.

### Q1(a): issuance

[C2 b1-p4](evidence/trials/b1-p4-C2-r1/trial.json) recorded nonnull issuance,
errno 0. [C3 b1-p6](evidence/trials/b1-p6-C3-r1/trial.json),
[C4 b1-p3](evidence/trials/b1-p3-C4-r1/trial.json), and
[C5 b1-p8](evidence/trials/b1-p8-C5-r1/trial.json) each recorded null issuance,
errno 1. Both queries in each trial returned `(1,0)`. These values repeat in
all blocks. C0/C1 also produced nonnull issuance, errno 0.

Decision-table condition: **“C2 nonnull; C3, C4 or C5 null”**. The changed rule
is respectively the absent allowance, its class string, or its literal path;
the native call still requests the read class for A.

Supported: **“A finding scoped to that row's single changed rule and the recorded environment”**.
Withheld: **“An errno-based claim about kernel cause”**.

The C0-nonnull/C1-null and C1-nonnull/C2-null conditions did not occur; their
negative findings are not invoked.

### Q1(b): transfer

The indexed C0/C1/C2/C6/C7 trials each record length 211, valid framing,
recipient acceptance and transient equality. C3/C4/C5 record unavailability
after null/errno-1 issuance. For example,
[C7 b1-p7](evidence/trials/b1-p7-C7-r1/trial.json) records nonnull/errno-0
issuance, accepted/equal transfer and consume `(1,0)`, while its second open
returns `(-1,1)`; both issuer queries are `(1,0)`.

Decision-table condition: **“Issuance nonnull; delivery, consumption or fresh access fails”**,
here satisfied by C7's fresh access.
Supported: **“Each stage's own observation, reported separately”**.
Withheld: **“Collapsing the later stages into issuance refusal”**.

### Q1(c): consumption

The indexed C0/C1/C2/C7 trials contain all 12 native consumes, each `(1,0)`.
C6 records three omissions; C3/C4/C5 record nine unavailable calls.
[C7 b1-p7](evidence/trials/b1-p7-C7-r1/trial.json) preserves consume `(1,0)`
beside second open `(-1,1)` and both query pairs `(1,0)`, as do its other two
repetitions. The return is a candidate handle under the pilot's `-1` sentinel
convention, not proof of access.

Decision-table condition: **“Issuance nonnull; delivery, consumption or fresh access fails”**.
Supported: **“Each stage's own observation, reported separately”**.
Withheld: **“Collapsing the later stages into issuance refusal”**.

### Q1(d): fresh access

[C2 b1-p4](evidence/trials/b1-p4-C2-r1/trial.json) and
[C6 b1-p5](evidence/trials/b1-p5-C6-r1/trial.json) both accepted transfer, and
both first opens were `(-1,1)`. C2 consumed `(1,0)` then read `(37,0)` with
matching identity/bytes; C6 omitted consumption and its second open was
`(-1,1)`. Both query pairs were `(1,0)` in both arrangements. This repeats in
each block.

Decision-table condition: **“C2 and C6 both accepted; both pre-consume reads fail; C2 reads known bytes after a consume return other than `-1`; C6's second read fails”**.
Supported: **“Consumption-dependent delegation in this setup; delivery alone produced no access in C6”**.
Withheld: **“A general consumption claim beyond this apparatus”**.

[C2 b1-p4](evidence/trials/b1-p4-C2-r1/trial.json) and
[C7 b1-p7](evidence/trials/b1-p7-C7-r1/trial.json) both accepted transfer, both
first opens were `(-1,1)`, and both consumes were `(1,0)`. C2 then read 37
matching bytes; C7's second open was `(-1,1)`. Both query pairs were `(1,0)`.
This also repeats in each block.

Decision-table condition: **“C2 and C7 both accepted; both pre-consume reads fail; both consume returns other than `-1`; C2 reads known bytes; C7's second read fails”**.
Supported: **“A role for the recipient's extension predicate; the consume return alone does not establish access”**.
Withheld: **“A general predicate claim beyond this apparatus”**.

### Q1(e): contrasts

Within each r1 block, C2's nonnull/errno-0 issue contrasts with C3/C4/C5's
null/errno-1 issues. C2's accepted transfer, consume `(1,0)` and matching
37-byte read contrast with C6's accepted transfer, omitted consumption and
second open `(-1,1)`, and C7's accepted transfer, consume `(1,0)` and second
open `(-1,1)`. All first opens are `(-1,1)`; both queries are `(1,0)` in these
six arrangements. First-block IDs are `b1-p4-C2-r1`, `b1-p6-C3-r1`,
`b1-p3-C4-r1`, `b1-p8-C5-r1`, `b1-p5-C6-r1` and `b1-p7-C7-r1`, linked above.
The other blocks supply the same five comparisons. No contrasts cross revisions.

| Decision-table condition | Supported finding | Withheld |
| --- | --- | --- |
| C2 nonnull; C3, C4 or C5 null | A finding scoped to that row's single changed rule and the recorded environment | An errno-based claim about kernel cause |
| C2/C6 accepted, first reads fail, C2 gains known bytes after consume while C6's second read fails | Consumption-dependent delegation in this setup; delivery alone produced no access in C6 | A general consumption claim beyond this apparatus |
| C2/C7 accepted, first reads fail, both consume returns other than -1, C2 gains known bytes while C7's second read fails | A role for the recipient's extension predicate; the consume return alone does not establish access | A general predicate claim beyond this apparatus |

## Q2 answers and query limits

### Q2(a): observed queries

The trial index and outcome table give all 48 query results. For example,
[C0 b1-p1](evidence/trials/b1-p1-C0-r1/trial.json) and
[C1 b1-p2](evidence/trials/b1-p2-C1-r1/trial.json) have `(0,0)` for each filter;
[C2 b1-p4](evidence/trials/b1-p4-C2-r1/trial.json) and C3–C7 have `(1,0)` for
each. Across three blocks there are 12 `(0,0)` pairs and 36 `(1,0)` pairs, with
no errors, unclassified pairs or unavailable queries.

The Q1 decision table has no Q2 row. This answer follows the
[query protocol](PLAN.md#ordering-and-query-protocol).
Its convention labels these pairs allow and deny respectively. The `(1,0)`
pattern occurred both where issuance was nonnull (C2/C6/C7) and where it was
null (C3/C4/C5); it did not distinguish those results in these records. This
is not a calibrated native contract or a claim of agreement or disagreement
between prediction and enforcement.

### Q2(b): representation

Every `query_capability` records successful API/flag lookup, both resolving to
`/usr/lib/system/libsystem_sandbox.dylib`. The exported integer was
`1073741824` (`0x40000000`). NONE's complete type argument was `1073741824`,
with no filter value; PATH used `1073741825`, with canonical A as its sole
filter value. Recorded caller/target PIDs identify the supervisor and its live
waiting issuer. Collection and release markers precede the issuer's call.

These observations, [retained native source](evidence/equipment/r1/source/records/browser-trace-investigations/pilot.c)
and [validator source](pw-context/controller/tools/sb_api_validator/sb_api_validator.c)
show PID, operation, type and either no additional argument or one path. Neither
representation carries the extension class alongside the path. The native issue
call instead receives class, path and flags 0. This is an argument-representation
answer, not a result inferred by treating query labels as issuance predictions.

The Q1 table has no representation row. Both Q2 parts withhold Q2's listed
claims: **“usable issuance, a class-specific issuance prediction,
prediction/enforcement agreement, a need for a new query API, or a production
comparison.”** No recipient queries, filter-ID search, alternate API experiment
or unified-log collection was performed. No-report suppression and verdict
invariance were not verified. This ordering is not PW's
`comparison.order=query_first`.

## Controls and equipment checkpoints

All [26 final constructed controls](evidence/controls/constructed-02/summary.json)
passed; their source snapshots, commands, inputs and read-backs are retained.
The earlier [24-control run](evidence/controls/constructed-01/summary.json)
also remains. The final run adds shared-memory identity controls described in
[REVIEW.md](REVIEW.md). These interpretation controls added zero native trials.
They accept honest native refusal, failed consumption and unavailable queries,
and reject unsupported execution-chain and known-byte claims.

The required real-record control uses
[b1-p1-C0-r1](evidence/trials/b1-p1-C0-r1/trial.json). The
[mutation manifest](evidence/controls/derived-from-b1-p1-C0-r1/mutation.json)
records exactly one deletion, `/events/56`: issuer `issue_result`, sequence 57.
The original remained byte-for-byte unchanged. The copy retains accepted
transfer, consume `(1,0)` and the 37-byte read, but the
[reader result](evidence/controls/derived-from-b1-p1-C0-r1/mutated-reader.stdout)
returns 1 and withholds complete-sequence acceptance because the issuance link
is missing. This added no native trial.

All 24 actual reader results accept complete connected evidence; nine accept
a complete delegation sequence. None has errors, inspection limits or integrity
findings. The checkpoints are [initial C0/C1](evidence/checkpoints/01-block-1-initial.json),
[block 1](evidence/checkpoints/02-block-1-complete.json),
[block 2](evidence/checkpoints/03-block-2-complete.json), and
[block 3](evidence/checkpoints/04-block-3-complete.json).
They use actual call/result records and record functional process control,
evidence collection and cleanup. No control failed and no equipment fault was
diagnosed during native execution.

## Completion, cleanup and retention

The 2,112 events match original NDJSON. There are 72 distinct process/start
identities. All 48 children published ordinary exit and were independently
reaped with status 0. Every supervisor returned 0; every driver independently
established process-group absence. All 24 owned directories were checked by
identity/receipt and removed after final observations; none remains. No signal
or deadline was reached, and no native channel cleanup remains pending.

All 15 nonnull native strings have inspected-prefix erasure observations. Both
children and the supervisor report zero read-backs after erasing their channel
views. Retained fields contain no raw tokens or token hashes; native stderr is
empty. These observations cover owned storage, not private library copies,
OS swap or privileged inspection. No release call was made; neither revocation
nor exit-time revocation is established.

The [closed state](evidence/state.json) records zero correction cycles, zero
cumulative troubleshooting seconds and zero diagnostic reruns. Source and
executable hashes remain r1's. The evidence tree is approximately 6.6 MB in
aggregate because it retains original NDJSON, assembled records, equipment/source
snapshots, reader outputs, constructed inputs and the real-record mutation.
No individual record exceeds 82 KB. This duplication preserves original
observations and independently inspectable read-backs.

## Prior evidence and applicability

The retained [v0.3.4 acceptance](../../tests/out/release-acceptance/run-3ab7e31af74345dfa87d1948c56ecb27)
at `0289d9ae8a78be59f9727e6fc2118b3c9b24bcc1` passed 201 cases, including
the four production extension cases cited by the plan. It did not run the
opt-in native suite. Retained [native feasibility artifacts](../../tests/out/runs/workset-native-crossed-01/suites/sandbox_extensions_native/feasibility/artifacts)
include `lifecycle-plain`: nonnull issue/errno 0, consume `(1,0)`, failed
pre-consume opening, then 33 known bytes with matching identity. Its fixture
and suite sources at `8aa74027e78f0b7ab4c859c1ffa85f2b41a8a288` are identical
to those at the release tag.

Both contexts record macOS 26.7.1, build 25G241, arm64 and the pilot's signing
identity; [release signing provenance](../../dist/archive/v0.3.4/evidence/provenance.json)
also records it. These paths are gitignored, available only in the local
checkout, and retain their existing managed ownership. They remain historical
context; this pilot's C0 records supply its baseline.

## Incidental observations and recommendations

Under Q5 only: all 12 native consumes returned `1`. No zero was observed; there
was no repeated consume. This does not resolve the wrapper disagreement or
establish zero's absence in general. No other inventory question is answered
or pursued.

Recommend retaining this report for maintainer review. The prepared sandboxed
issuer and separately sandboxed recipient exhibited the bounded consumption
and predicate contrasts stated above. This establishes neither a production
multi-process capability nor browser runtime behavior. Any maintained fixture,
production issuance action, grammar change, tighter issuer-access policy,
framework-loading comparison or Q3–Q18 experiment needs a separately reviewed
scope. No such follow-up was undertaken.
