# Sandbox extensions out-of-band audits

This is the shared handoff document for the middle and final audits in
[the implementation plan](../SANDBOX-EXTENSIONS-PLAN.md#out-of-band-audit-handoffs).
The executing agent prepares each exchange at its waypoint, identifying the
reviewed source/build and documentation/evidence locations before writing the
questions. The auditor writes answers and additional findings in the same
section. Execution dispositions remain separate from the attributed audit text.

## A1 Middle audit — after M3

Status: awaiting the external auditor's response. M3 implementation and its
rendered-documentation assessment are complete. This handoff is not an audit
answer or A1 closure; execution is standing by before H1 and M4.

### A1 Handoff, questions and auditor answers

Prepared by the executing agent `/root` on 2026-10-13. Please attribute answers
and additional findings to the auditor, with source or retained-evidence
references and any access limitations. Answer beneath each question; the
executing agent's dispositions belong in the separate section below. The
questions identify areas requiring independent judgment, not presumed findings.

#### Candidate and evidence

| Item | Identity |
| --- | --- |
| Reviewed source | `fdbd89b215125b50fc6030e09bdc4a66b56e48f2` |
| Signed app source | `6744f3c0652fac983d2823dfcc9cb848efb105af`, clean stamp `v0.2.8-40-g6744f3c` |
| Local app | `dist/PolicyWitness.app`, version 0.2.8, build 560 |
| Signer | `Developer ID Application: Adam Hyland (42D369QV8E)`; certificate SHA-1 `1A6E85D06FC762993C8BD3E932556DED3985F030` |
| Host | macOS 26.7.1, build 25G241, arm64 |
| Wire versions | Request 4, runner response 17, envelope 7 |
| Worker identity | `12a5db4345b0801bd519224e65955eeb623f06664ed058c9a5c34ba7acbfc91d` |
| Embedded evidence manifest SHA-256 | `0df13c51fa78b5c3b6920c9b329adc9f94c5960e0334f13efdaf48e1410aabb4` |

The reviewed source differs from the signed source only in test code and its
documentation/metadata. Rust changes lie inside the existing `#[cfg(test)]`
module; preceding production bytes and other production inputs are unchanged.
The app's inspected inventories match across the two accepted runs. The commit
preparing this handoff changes only the plan, records and retention index; it
does not claim to be the source of the earlier build or test executions.

| Retained run under `tests/out/runs/` | Run ID and use |
| --- | --- |
| [extensions-m3-accepted-20261013](../tests/out/runs/extensions-m3-accepted-20261013/run.json) | `20261013T143650Z_763cbafa`; all 147 cases passed at clean `6744f3c` against build 560, with no skipped/unrun cases. Includes native/Swift/ABI, admission, independent readers, public CLI, order mutation, BYOXPC, preflight, source-drift, maximum reply and dispatcher coverage. |
| [extensions-m3-phase-logs-20261013](../tests/out/runs/extensions-m3-phase-logs-20261013/run.json) | `20261013T145127Z_5507dc70`; all 13 focused cases passed at clean `fdbd89b` against unchanged build 560. Replaces five unit, six source-drift, signature-preflight and termination/log-correlation credits. |

Each run records exact commands/configuration, canonical cases and artifact
inspection; its `checkpoint/` preserves console and source hashes. The first
also retains the signed-build log and cleanup verification. The second's
[credit manifest](../tests/out/runs/extensions-m3-phase-logs-20261013/checkpoint/acceptance-credits.json)
maps the final 147 credits to 13 replacement and 134 reused results. Its exact
test-only diff accompanies the source snapshot. Reuse includes a reviewed
exception: driver replay executes an unchanged filtered test; build guards copy
the changed test module and documentation but build production code without
`cfg(test)`, and their refusal paths/tool substitutions are unchanged. All unit,
changed live, and source/document checks were rerun. This is an applicability
judgment, separate from file-identity checks. Neither documentation baseline
changed from the M2 acceptance at `ac9c3b5`.

Standard and BYOXPC public CLI controls both observed a real consume handle
followed by release on that handle, with three phases of independent predictions
and fresh accesses in the same once-sandboxed worker. Fresh descriptor identity,
bytes, worker/issuer identity, signing and cleanup observations accompany native
results. Native success is not itself an effective-permission or revocation
claim. The ordinary unlink/unavailable-prediction and resolvable-later-query
controls and bounded lifecycle-placement controls are included in both paths.

The fresh read-only documentation reviewer was `/root/m3_rendered_review`
(`gpt-6-astra` requested; runtime identifier not independently exposed). Reports,
source snapshots, HTML, PDFs, inspected PNGs and manifests are retained in the
[correction run](../tests/out/runs/extensions-m3-review-corrections-20261013/reviews/)
and [final focused run](../tests/out/runs/extensions-m3-phase-logs-20261013/reviews/).
The renderer was Pandoc 3.12, WeasyPrint 70.0 and Poppler 26.10.0. F1–F5 were
corrected and rechecked: fresh-read return wording, issuer validation inventory,
BYOXPC signing/provenance labels, failure-matrix ownership and split guide
paragraphs. Collection-closure wording and the temporary test-helper location
were also corrected. The final three-document phase-log recheck found no issue.
The applicability manifest establishes current hashes for those three documents
and 14 unchanged previously reviewed documents; it does not enlarge the actual
page-inspection coverage. These reviews are separate from this external audit.

The source/test scripts and retention index are committed. The app, run output
and rendered artifacts are gitignored and **available only in this local
checkout**. They have not been published or packaged for another checkout.
HTML links can retain original `/private/tmp` preview paths; retained PDFs/PNGs
and source copies preserve inspected content. If these artifacts are unavailable
to the auditor, record that gap rather than treating the summaries as inspection.
The associated plan links the detailed investigative record and earlier runs.

#### Limitations and adjustments requiring attention

- The M1 allocation controls observed zero callbacks during the native windows,
  which cannot establish absence of private API allocations or other resources.
  The implemented invariant covers bounded, preallocated PW-owned reporting and
  coordination, with no explicit PW allocator use after application. Native API
  internals remain outside that guarantee. This is the plan-authorized,
  evidence-backed revision; no issuer authority was added.
- Native results apply to this host/library and exercised paths. A controlled
  entry/return seam establishes the test intervention and missing-publication
  behavior, not an observation inside Apple's private implementation. Missing
  publication remains unresolved even when the fixture knows a call returned.
- One earlier fixture run, `extensions-m3-native-boundaries3-20261012`
  (`20261013T005937Z_5456c6b2`), created 25 empty POSIX shared-memory objects
  before `fchmod` failed with EINVAL and before ownership names were recorded.
  No mapping, target, token or child was created. Names are unavailable and
  absence is unverified; no prefix-based cleanup was attempted. The fixture now
  records ownership first. All 26 recorded native channels and eight BYOXPC
  sessions in final consolidation have verified cleanup and absent recovery or
  staging paths. Later cleanup does not resolve the earlier unknown objects.
- The user observed and approved a Desktop-access TCC prompt during earlier
  testing. Subsequent phase/extension targets and executed fixture helpers use
  owned `/private/tmp` paths. Earlier stalls are retained without claiming a
  proven TCC cause; timeout controls now require an initial fixture record so a
  blocked launch cannot satisfy the intended intervention.
- Rendered inspection was bounded: unchanged release procedures, all duplicate
  limits pages, some unchanged architecture rows, browser compatibility and
  exhaustive link navigation were not inspected. Available live denial events
  are optional; controlled collector states establish the no-effect-on-execution
  and ambiguous-association rules independently of live retrieval completeness.

#### Questions and attributed auditor answers

**Q1 — Native evidence and independent readers.** Do the producer and readers
preserve the distinction among omitted actions, skipped dependencies, started
but unpublished calls and published native results, including failed consume
without a usable handle and failed release? Can any supported or malformed
record fabricate completion, a handle association or successful fresh access?
Inspect [the native worker](../controller/tools/pw_probe_runner/pw_probe_runner.c),
[Swift evidence tests](../runner/Tests/PWRunnerCoreTests/ExtensionEvidenceTests.swift),
[Rust reader](../controller/src/evidence.rs),
[independent Python reader](../tests/lib/extension_evidence.py) and the
[failure contract](../tests/FAILURE-PROPAGATION-CONTRACT.md). Please distinguish
an actual claim defect from additional combinations assigned to M4.

Auditor answer: pending.

**Q2 — Phase ordering and placement.** Does the public grammar enforce its
single-declaration and consume/release caps and reference order while retaining
all ordinary paired probes? Do phase-local query collection, progression,
unavailable predictions and lifecycle placement support exactly the stated
ordering claims? In particular, can repeated PID/target observations across
phases gain unjustified identity or log attribution? Entry points:
[grammar](../docs/REQUEST-GRAMMAR.md),
[orchestrator](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
[phase controls](../tests/suites/witness_contract/check_phases.py),
[extension controls](../tests/suites/witness_contract/check_extensions.py),
[collector tests](../controller/src/run_flow.rs) and
[live log controls](../tests/suites/witness_contract/check_termination_correlation.py).

Auditor answer: pending.

**Q3 — Token channel, lifetime and interruption.** Are storage bounds, mapping
size, descriptor inheritance, issuer/worker ownership, buffer erasure and reap
conditions sufficient to support the documented confinement claims on both
success and failure? Does unknown cleanup correctly prevent delivery or later
claims? Assess what the native entry/return controls establish and where private
API behavior remains unobserved. Entry points:
[channel ABI](../controller/tools/pw_probe_runner/pw_extension_channel.h),
[issuer](../controller/tools/pw_probe_runner/pw_extension_issuer.c),
[host issuance](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift) and
[boundary controls](../tests/suites/witness_contract/check_extension_boundaries.py).

Auditor answer: pending.

**Q4 — Issuer authority and BYOXPC provenance.** Is issuance kept under its
separate, recorded ordinary authority, with the issuer signed without the
worker's entitlement plist? Do install, read-back, validate, reconcile and older
registry recovery preserve uncertainty when issuer evidence is absent, and
refuse a selected missing capability with the documented code? Review
[runner management](../controller/src/runner_manager.rs),
[bundle inspection](../controller/src/bundle.rs),
[provenance controls](../tests/suites/witness_contract/check_extension_provenance.py)
and the [external-runner account](../docs/PolicyWitness.md#external-runners-byoxpc).

Auditor answer: pending.

**Q5 — Contract, limits and integration.** Are request/response/envelope versions,
C/Swift layouts, admission corpus and independent readers coordinated for the
new actions and records? Does the 52,414,779-byte reply bound cover the actual
encoder and all relevant transport paths within the 152 MiB controller budget,
without hiding truncation or invalid ordering? Are any new build/capability
refusals missing behavioral controls? Start with
[contract owner](../docs/contract.json), [limits owner](../docs/limits.json),
[build owner](../docs/build.json),
[maximum-reply control](../tests/suites/witness_contract/check_max_target_reply.py)
and [coverage](../tests/COVERAGE.md).

Auditor answer: pending.

**Q6 — Account and necessary machinery.** Do the current
[architecture](../docs/ARCHITECTURE.md), [guide](../docs/PolicyWitness.md),
[runner account](../runner/README.md) and generated views describe the same
implemented boundaries? Is the revised PW-owned allocation claim supported
without an implied guarantee about private native calls? Identify unsupported
claims, missing generator ownership, or duplicated/generalized machinery whose
necessity should be examined in H1, citing the concrete path or invariant.

Auditor answer: pending.

**Q7 — Gate evidence and remaining limitations.** Does the accepted evidence,
including the 13 replacement credits and reviewed reuse of 134 earlier results,
establish the M3 gate for this exact candidate? Identify any unsound reuse,
missing discriminating control or inaccessible artifact that prevents that
conclusion. Does the unverified cleanup of 25 empty fixture objects change any
production or gate claim beyond the recorded limitation? Classify findings that
invalidate M3 or block H1/M4 separately from later work, and specify the smallest
correction or experiment needed.

Auditor answer: pending.

#### Additional auditor findings

Pending the returned audit; no executing-agent findings are attributed to the
auditor.

### A1 Execution dispositions and follow-up

Pending the returned audit. No answers have been supplied, dispositioned or
accepted. M3 completion records implementation-gate evidence; A1 remains open.
After answers arrive, preserve their attribution here and record each executing
agent disposition, correction, verification and any auditor follow-up separately.
H1 preparation requires A1 closure; M4 has not started.

## A2 Final audit — after M5.6

Status: not prepared.

### A2 Handoff, questions and auditor answers

To be populated at the waypoint.

### A2 Execution dispositions and follow-up

Pending the returned audit.
