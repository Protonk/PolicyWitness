# Observer envelope admission before interpretation

Proposed resolution: admit the observer's envelope kind and exact supported
frame version before interpreting any report fields. Retain rejected payloads
as opaque evidence, produce no derived denial observations from them, and
preserve execution results independently. This is a bounded receiver change
with direct regression controls.

Status: resolved and validated 2026-10-06. Observer receiver, supervised timeout/overflow, assembly and independent consumer controls pass.
The final default battery passed 165/165 with no skips. The proposal and
diagnosis below preserve the investigation’s original grounding.

**Proposed change**

1. Place a frame-admission gate between bounded JSON capture and the first
   semantic read in `parse_observer_output`. Require the expected
   `sandbox_log_observer_report` kind and an integer `schema_version` equal
   to the generated controller-envelope constant. Missing, malformed and
   unsupported markers must fail admission before the body is interpreted.
2. After frame admission, check the supported inner report version before
   interpreting its fields. Retain the existing report, identity, window,
   supervision and collection checks for admitted reports. The outer frame
   and inner report identify different contracts.
3. Preserve the intact received JSON as an opaque nested payload, or the raw
   transport evidence already retained when parsing is impossible. Rejection
   must yield no body-derived `observed_deny`, deny events, blocked reason,
   step associations or missing-record conclusions. Opaque payload retention
   must not invite another reader to interpret the rejected body.
4. Use the existing invalid-reply capture path for an intact, successfully
   transported but inadmissible envelope. Independently observed transport
   timeouts, overflow and cleanup failures keep their own status precedence
   and supervision evidence. An inadmissible body cannot supply evidence of
   an inner collection failure or success.
5. Apply the same admission rule to the shared semantic test readers. In
   particular, `consumer.py` must keep an inadmissible nested observer opaque
   during shape validation and log interpretation, and
   `check_observer_report` must check the outer version before the inner body.
   The policy-helper receiver and consumer already provide a local pattern
   for version-gated interpretation of retained nested envelopes.

The intended result is a complete admission fix using the existing capture
and evidence separation. Changing native probe execution, log collection
budgets or the observer's emitted payload is unnecessary. Any additional
public diagnostic fields or status spellings would require their own contract
review; they are not needed to establish admission before interpretation.

**Diagnosis and grounding**

The [wire contract](../docs/CONTRACT.md#what-each-number-identifies) defines
the controller-envelope version as the frame version shared by
`policy-witness`, `sbpl-check` and `sandbox-log-observer`. The observer also
carries its own report version inside `data`. The
[supported-version rule](../docs/CONTRACT.md#supported-versions) requires
semantic readers to accept exactly the supported version and retain
unsupported evidence without interpreting it.

In [sandbox_log.rs](../controller/src/sandbox_log.rs),
`parse_observer_output` captures JSON and immediately extracts
`observed_deny`, log errors, blocked reasons, deny events and window fields.
It checks neither the outer `kind` nor `schema_version` first.
`parse_supervised_observer` subsequently checks the inner
`observer_schema_version`, worker identity and collection metadata, but adds
no outer frame gate. An otherwise acceptable body can therefore be classified
as `captured` despite a missing or unsupported outer version, or the wrong
envelope kind.

The supervised-observer test in the same file constructs a `body` containing
`kind` and `data`, with no outer `schema_version`. Its `complete` scenario
asserts `capture_status == "captured"`. This is an existing test expectation
that endorses acceptance without the marker, not a new test result from this
investigation. The gate is also absent from the source path that expectation
exercises.

In [log_capture_contract.py](../tests/lib/log_capture_contract.py),
`check_observer_report` checks the envelope kind and inner report version but
omits the outer version. In contrast, `supported_outcome` in
[policy_check.rs](../controller/src/policy_check.rs) checks the helper kind
and exact current frame version before reading the outcome, and
`_validate_policy_check_reply` in [consumer.py](../tests/lib/consumer.py)
keeps rejected helper JSON opaque.

The consequence is interpretation across an unsupported or unidentified
contract boundary. It affects confidence in log-capture and correlation
claims. It does not establish that log evidence can change worker execution
results, nor does it establish an observed failure of the currently co-shipped
observer binary.

**Validation for the proposed change**

- Start with a valid current observer response that includes both version
  markers and all required supervision evidence. Keep a positive acceptance
  control so rejection tests cannot pass by disabling observer interpretation.
- Independently remove the outer version, change its type to null, string,
  Boolean or noninteger number, use older and newer integer versions, and
  remove or replace the kind. Also exercise an unsupported inner version
  under an admitted outer frame.
- For each refusal, assert payload retention, absence of body-derived log
  claims and absence of correlation. Put misleading or malformed fields in
  the rejected body to establish that admission precedes interpretation,
  rather than merely overwriting `capture_status` afterward.
- Combine inadmissible payloads with independently observed transport
  failures. Preserve transport status and byte counts without treating
  rejected report fields as evidence about the inner log process.
- Carry these cases through envelope assembly and the shared consumer. Check
  that the serialized execution fields remain identical for accepted,
  rejected and unavailable observer reports, and that opaque rejected bodies
  do not produce downstream shape errors or recovered claims.
- Retain current valid-report, window-mismatch, bounded-capture and cleanup
  controls. The regression does not require a particular kernel denial to
  appear in a live unified-log query.

A documentation-only exception would leave a receiver interpreting a payload
whose frame contract it has not admitted. The proposed stopping point is the
receiver and reader fix, with existing execution/log ownership preserved.
