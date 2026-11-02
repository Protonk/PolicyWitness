# Independent acceptance assessment

Decision: **accept**. The maintainer accepted this investigation on November 2,
2026, following the independent Codex review recorded here. No corrections,
additional experiments, or production changes are required for acceptance.

This assessment is separate from the investigating agent's [report](REPORT.md)
and [apparatus source review](REVIEW.md). It records the acceptance review
completed in the maintainer conversation before archival work was authorized.
**No native experiments were rerun.** The review did not build or sign software,
modify the repository, or pursue any deferred question. Its commands inspected
retained material and evaluated existing evidence in memory.

## Identities and scope

- Completed investigation reviewed: PolicyWitness commit
  `1de523c8744eafb50302145b0495a70c6f403f50`.
- Executed apparatus: revision `r1`, built from source commit
  `6ea196363dd5007f3d98d72424e0ffd044524ddb`.
- Signed executable SHA-256:
  `67cef267c01dae2002a333ab2a5ddfbeff9f4574e8bc7bd52c3055404b0d017c`.
- The commit first adding this assessment records the later acceptance decision;
  it is neither the experimental source commit nor a new apparatus revision.
  Archival relocation is a separate subsequent operation.

The review assessed this fixture and its recorded macOS environment. It did not
assess a browser's security, establish general macOS properties, or require a
new PolicyWitness capability as an outcome.

## Evidence examined

The review examined the [agreed plan](PLAN.md),
[source traces](TRACES.md), report, native program, driver, reader, control
program, event protocol, source review, and relevant repository guidance and
implementation sources. It inspected the motivating pinned source selections,
the PW validator's query calls, and the historical release/native-suite context
identified by the report.

The retained-evidence audit covered all 24 trial directories, their original
NDJSON and assembled records, ownership records, stderr, reader commands and
outputs, schedules, checkpoints, closed state, equipment commands/read-backs,
and source snapshots. It checked all final constructed controls and the
single-link control derived from an actual C0 trial.

All 12 equipment source snapshots matched their recorded hashes, current files,
and original source commit. The local executable matched its recorded signed
hash. This byte comparison did not rebuild, execute, or re-sign the executable.
All 2,112 assembled events matched the original NDJSON. Evaluating the retained
trial records through the reader reproduced all 24 saved reader outputs.

## Assessment

The execution followed the design: three blocks each contain C0–C7 once, with
varied positions, fresh targets and processes, and no cross-revision contrasts.
Schedules and required checkpoints predate dependent trials. All native trials
use r1; there are no diagnostic reruns, unrun positions, or native correction
cycles. Prebuild reader development is distinct from native apparatus revisions.

The native source connects exact expanded policies to compilation and
application, then to ordered query, issuance, transfer, consumption and access
publications. C0 compiles C1's policy and omits only application. The supervisor
launches fresh siblings, passes apparatus descriptors, and closes target
creation/baseline descriptors before launch. The 168 prescribed descriptor
snapshots support absence of target descriptors at those boundaries. Source
inspection accounts for deliberate operations between snapshots; it is not a
census of private library initialization or transient resources.

The Q1 findings follow from the controlled observations, repeated in every block:

- C0/C1/C2 issue nonnull tokens with errno 0, transfer accepted equal bytes,
  consume with `(return, errno) = (1,0)`, and obtain 37 matching bytes through
  fresh opens with matching descriptor identity and successful closure.
- C3/C4/C5 issue null with errno 1 after, respectively, removing the allowance,
  changing its class predicate, or changing its path predicate. The native call
  continues requesting the read class for A. Dependent stages remain explicitly
  unavailable, and second opens fail.
- C6 accepts delivery but omits consumption and obtains no access. C7 consumes
  with `(1,0)` but obtains no access without the recipient extension predicate.
- Every first recipient open fails with `(-1,1)`. The C2/C6 and C2/C7 contrasts
  therefore support consumption-dependent delegation and a role for the
  recipient predicate in this setup. A consume return alone is not access.

Representative records are [C2](evidence/trials/b1-p4-C2-r1/trial.json),
[C3](evidence/trials/b1-p6-C3-r1/trial.json),
[C4](evidence/trials/b1-p3-C4-r1/trial.json),
[C5](evidence/trials/b1-p8-C5-r1/trial.json),
[C6](evidence/trials/b1-p5-C6-r1/trial.json), and
[C7](evidence/trials/b1-p7-C7-r1/trial.json). The report indexes all repetitions.
These observations do not establish authority exceeding the issuer's own read
access, general policy precedence, or an errno-based kernel cause.

For Q2, both query forms return `(0,0)` in C0/C1 and `(1,0)` in C2–C7. The latter
pattern does not distinguish nonnull issuance in C2/C6/C7 from null issuance in
C3/C4/C5. The recorded flag/type values and native and PW validator call sites
establish the representation limit: no filter argument, or one path argument,
without an extension class alongside it. The report appropriately avoids
prediction/enforcement agreement, disagreement, and general API-impossibility
claims.

The reader checks policy bytes, process associations, required stages,
publication acknowledgements, ordering, transfer linkage, descriptor identity,
and read bytes. Complete evidence is distinct from a complete delegation
sequence, so honest native refusal remains a valid result. The
[final 26 controls](evidence/controls/constructed-02/summary.json) reproduce their
saved outputs. The [actual-record mutation](evidence/controls/derived-from-b1-p1-C0-r1/mutation.json)
removes exactly the issuer's issuance-result event while preserving all other
content; the reader withholds sequence acceptance despite successful recipient
observations. These checks establish interpretation behavior and connection to
the actual record format, not native semantics or exhaustive validation of every
field. The native source and observations remain necessary evidence.

Completion and cleanup are supported beyond summary flags. The records contain
72 distinct process/start identities, 48 ordinary child-exit publications with
matching zero-status reaps, and 24 successful supervisor completions. Driver
observations independently record process-group absence through `ESRCH` and
empty membership enumeration, then target identity checks and successful removal
of files, receipts and directories. All recorded temporary directories were
absent when reviewed. No signal, deadline, or pending cleanup was recorded.
Erasure observations cover owned channel storage and inspected native-string
prefixes; they do not establish erasure of private copies or revocation.

## Nonblocking observations

The earlier 24-control run, `constructed-01`, is historical prebuild evidence.
It lacks the source snapshots retained for `constructed-02`, and its older
baseline does not satisfy the final reader's channel-creation checks. Acceptance
rests on the final 26-control run and actual-record mutation. Making this
distinction explicit is an optional clarification, not a required correction.

The acknowledged limits remain appropriate: one environment and signing context,
prepared native runtime, read-class issuance with flags 0, permissive issuer
ordinary reads, no release comparison, and no browser runtime inference.
Historical release/native-suite evidence is separately managed context; the
pilot's own C0 supplies its baseline. No further research or implementation is
required by this acceptance.
