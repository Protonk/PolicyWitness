# Sandboxed issuance pilot: Q1 and Q2

## Question status

| Question part | Status | Evidence and scope |
| --- | --- | --- |
| Q1(a): issuance | Not attempted | The apparatus is being prepared. |
| Q1(b): transfer | Not attempted | The apparatus is being prepared. |
| Q1(c): consumption | Not attempted | The apparatus is being prepared. |
| Q1(d): fresh access | Not attempted | The apparatus is being prepared. |
| Q1(e): contrasts | Not attempted | No planned positions have executed. |
| Q2(a): observed queries | Not attempted | No native queries have executed. |
| Q2(b): representation | Not attempted | Source inspection is available; the pilot's exported flag and complete type arguments have not been observed. |

This is an execution record in progress for the
[investigation plan](../../BROWSER-TRACE-INVESTIGATIONS-PLAN.md). The questions
are defined in [TRACES.md](TRACES.md#questions). Q3–Q18 remain outside the active
investigation.

## Equipment and preparation

The pilot uses an independent adaptation of the native fixture. Production
PolicyWitness, the registered fixture, suite checkers and test catalog are not
part of the apparatus revision. All native roles execute the same signed pilot
binary. The initial signing identity selected from the retained context is
`Developer ID Application: Adam Hyland (42D369QV8E)`; the execution equipment
record will retain verification and signature/entitlement read-backs.

The ignore rule for `local/` was committed before any build in `d528e236`.
Products under `local/<apparatus-revision>/` are gitignored and available only
in the local checkout. Committed source, equipment records and trial evidence
must suffice to read the report without those products.

## Coverage and equipment checkpoints

The plan specifies three blocks, each containing C0–C7 once, for 24 planned
positions. Each sequence is retained before its block begins. No planned
positions or diagnostic reruns have executed yet. The first checkpoint follows
the first block's C0 and C1 records; further checkpoints separate blocks.

## Reader controls

The [constructed controls](evidence/controls/constructed-02/summary.json) passed
all 26 scenarios; their source snapshots, inputs and independent reader commands/results are
retained. The [source review](REVIEW.md) records the preparation, channel and
cleanup inspection. A complete native delegation sequence, if one
is accepted, will supply a separately identified copy with exactly one
essential execution link removed. Its reader result must withhold the complete
sequence. The original trial will remain intact.

## Prior evidence and applicability

The retained [v0.3.4 acceptance](../../tests/out/release-acceptance/run-3ab7e31af74345dfa87d1948c56ecb27/)
at commit `0289d9ae8a78be59f9727e6fc2118b3c9b24bcc1` passed the production
`witness_contract/extensions`, `extension_boundaries`,
`extension_combinations` and `extension_directory` cases. Its 201 passing
cases did not include the opt-in native suite.

The retained [native feasibility artifacts](../../tests/out/runs/workset-native-crossed-01/suites/sandbox_extensions_native/feasibility/artifacts/)
contain `lifecycle-plain`: nonnull issuance with errno 0, consume return 1 with
errno 0, failed pre-consume opening, and a later fresh read of 33 known bytes
with matching identity. The fixture and suite source trees at its source commit
`8aa74027` are unchanged at v0.3.4. Both retained contexts record macOS 26.7.1,
build 25G241, arm64 and the signing identity named above. The
[release signing provenance](../../dist/archive/v0.3.4/evidence/provenance.json)
also records that identity.

These paths are gitignored, available only in the local checkout, and retain
their existing managed ownership. They are historical context and do not
replace this pilot's C0, equipment verification or fresh observations.

## Interpretation limits

Preparation resolves native symbols before application. The result will concern
that prepared runtime, these policies and this recorded environment. Descriptor
snapshots and source inspection do not census transient resources, Mach rights
or private library initialization. Queries concern only the live issuer before
issuance. Their raw return/errno pairs are separate from any conventional
allow/deny labels and from usable delegation. No browser runtime is tested.

Final answers will cite raw observations, the applicable decision-table row,
its supported finding, and its withheld column verbatim. Contrasts will be
restricted to a single apparatus revision. Correctly published native failures
will remain observations rather than becoming equipment faults or sandbox-cause
claims.

## Troubleshooting and cleanup

No correction cycles or diagnostic reruns have been used. No pilot resources
have been launched. The driver will retain ownership and cleanup observations;
unconfirmed process absence requires retained paths, pending-cleanup status and
cessation of further trials. Troubleshooting is bounded by two correction and
retry cycles, at most two diagnostic reruns, and 60 cumulative minutes.

## Incidental inventory observations

None yet. Q3–Q18 receive no answers from this pilot.

## Recommendations

Pending the planned observations and equipment checkpoints.
