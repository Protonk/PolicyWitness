# Pilot evidence reader

`read.py` reads one driver `trial.json`. It imports no PolicyWitness classifier,
native fixture checker or producer module. It checks the retained event chain
against the fixed C0–C7 matrix and reports observations separately from a
complete delegation sequence. [NATIVE-PROTOCOL.md](NATIVE-PROTOCOL.md) describes
the raw publications; the driver adds launch ownership and cleanup observations.

Run it under the investigation driver, which retains the command and output:

```sh
tests/lib/checkout_lock.sh -- /bin/sh records/browser-trace-investigations/run.sh \
  check --name reader-TRIAL --script read.py -- \
  records/browser-trace-investigations/evidence/trials/TRIAL/trial.json
```

The JSON result distinguishes:

- `consistent_record`: required associations, raw observations and ordering
  checks passed. It does not mean any native operation succeeded.
- `complete_evidence`: the record passed those checks and contains no interrupted
  publication. A native refusal with explicit dependent unavailability can pass.
  Missing evidence, failed equipment or unresolved cleanup prevents acceptance.
- `connected_apparatus`: the complete record contains each required call/result
  publication or a justified omission/dependency, including independent cleanup.
- `complete_delegation_sequence`: a complete chain additionally has nonnull
  issuance, framed and accepted transfer with transient byte equality, consume
  return other than signed 64-bit `-1`, no known-byte access before consumption,
  and known bytes with matching identity through a fresh, closed descriptor
  afterward. Missing descriptor coverage or target-integrity findings withhold
  this result. This flag is evidence for that trial, not a matched-control finding.

`raw_outcomes`, `access_observations`, `query_counts`, `errors`, `limits`, and
`integrity_findings` remain separate. An ordinary native issue, query, consume,
open, read or fstat failure is not itself a malformed record. Unexpected observed
file identities or bytes are retained as integrity findings and do not turn
native observations into invented successful access. An optional
`claimed_known_bytes` field, used in constructed false-claim controls, must agree
with the independently checked raw identity and bytes. The native producer does
not need this field. Successful opens require independent close observations;
reusing the same descriptor number after a successful close is permitted.

The reader requires both the actual issuance-result publication and its ordered
links. It checks global emission sequence, each child's producer sequence,
acknowledgement references, preparation/application, query collection before
release, transfer, consumption, and fresh-read boundaries. Sequence numbers do
not substitute for a missing stage. Process identity ties launches, publications,
native reaping and the driver's supervisor observation together. Descriptor
identity is compared independently of the producer's `matches_a`/`matches_b`
flags. Complete snapshots must contain the explicitly installed standard streams;
entry snapshots must also identify the two mapping descriptors.

Query labels follow only the plan's convention: return `0` is `allow`; return
`1` with errno `0` is `deny`; negative returns are `error`; other pairs are
`unclassified`. Unavailable capability remains unavailable. Neither the labels
nor raw queries establish usable issuance or prediction/enforcement agreement.

Exit status is zero for complete evidence, including honest native negative
results, and one for missing/inconsistent evidence, interruption or incomplete
equipment cleanup. The report must still interpret valid contrasts within one
apparatus revision using the plan's decision table.

## Constructed controls

The control program creates token-free records independently of the native
producer, invokes `read.py` as a separate process for each, and retains each
input, command, stdout, stderr, return code, expectation and summary. It preserves
inherited lock descriptors through its reader subprocesses. Use a fresh output
directory for each invocation:

```sh
tests/lib/checkout_lock.sh -- /bin/sh records/browser-trace-investigations/run.sh \
  check --name constructed-reader-controls --script reader_controls.py -- \
  --out records/browser-trace-investigations/evidence/controls/constructed-01
```

The controls reject missing or reordered application/transfer publications,
missing issuance, wrong process/query associations, missing acknowledgements,
inherited or retained target descriptors, unsupported known-byte claims and
unconfirmed cleanup. Reordered controls renumber the emission and producer
sequences and update acknowledgement references, so rejection must include the
actual stage-order diagnostic. Passing controls include native issuance refusal
with explicit unavailable dependents, failed consumption followed by another
fresh read, unavailable queries, query error/unclassified pairs outside the
denial count, consume return zero, and a descriptor number reused after closure.
Unexpected observed bytes are preserved without a known-byte access claim.

These controls establish reader behavior on constructed inputs. They establish
no native semantics and do not replace the actual-record control below.

## One-link control derived from a trial

After a planned trial is accepted as a complete delegation sequence, run:

```sh
tests/lib/checkout_lock.sh -- /bin/sh records/browser-trace-investigations/run.sh \
  check --name derived-reader-control --script reader_controls.py -- \
  --out records/browser-trace-investigations/evidence/controls/derived-TRIAL \
  --derive-from records/browser-trace-investigations/evidence/trials/TRIAL/trial.json
```

The program first reads the original through the reader. It then copies the
record and removes exactly its issuer `issue_result` event. Every other event,
sequence value, recipient observation, trial field and driver observation is
unchanged. The control filename and separate mutation manifest identify it as
derived evidence; it is never added to the trial schedule. The manifest retains
the original file's SHA-256 (not a token hash), the single JSON removal path,
source trial identity and a check that the original bytes stayed unchanged.
Both reader commands and results are retained. The copy must lose complete
delegation acceptance. This operation runs no native trial.
