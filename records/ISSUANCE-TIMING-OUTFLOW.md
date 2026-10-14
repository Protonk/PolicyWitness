# Issuance timing as an experimental event

Recorded 2026-10-14 against source `2582f1e9aa0d2ca7bb867c4b3a22f9bb1b87e7e8`.
Status: deferred investigation, potentially for 0.3.1. The user requested this
standalone outflow note after accepting the completed sandbox-extension plan.
It introduces no new gate for that plan and makes no release commitment.

## Present boundary

[`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)
resolves the target, records metadata and runs a disposable issuer before the
worker is created. Only bounded issuance with a confirmed clean reap permits
delivery. The worker subsequently consumes and releases under its once-applied
policy. All its phase observations occur after issuance has already been
attempted. PW can compare before and after consumption in one worker, but cannot
obtain that worker's pre-issuance baseline.

This is the initial bounded model, not a demonstrated requirement that issuance
must always precede worker creation. The M1 lifetime controls established that
the issuer could exit before consumption in the tested setup; they did not
establish that issuance timing is irrelevant to every experiment.

## Question to return to

Which concrete experiment needs to observe a live, already-sandboxed worker
before and after issuance, separately from delivery and consumption? Examples
include target creation/replacement between observations and issuance, or a
direct control for whether issuance without consumption changes an observation.
Do not assume those effects exist, or that they cannot exist.

Retain the authority separation: native issuance belongs to a separate issuer,
the host orchestrates, and the worker consumes under one fixed policy. Issuance
could become a scheduled host-orchestrated event without moving the issuer's
authority into the worker or sandbox API calls into the host.

## Design work a future experiment would require

- Define target-preparation timing separately from issuance. Preserve submitted
  path, resolved path and observed identity at each relevant boundary; do not
  imply object stability across replacement.
- Establish a pre-issuance worker observation, then an explicit issuance boundary
  and independently published result, followed by later collection before
  consumption. Specify its position relative to the existing query/release
  barrier; naming an action does not establish ordering.
- Redesign bounded token delivery for an existing worker. The current startup
  mapping and validation path assumes issuance has finished. Merely moving the
  `ExtensionSession` constructor into a phase is insufficient. Keep tokens out of
  specimens, arguments, environments, diagnostics and retained evidence.
- Account for issuer deadlines, interruption, cleanup, delivery refusal and
  unavailable dependent actions without discarding earlier phase evidence.
  Preserve one-way sandboxing and a fresh worker per specimen.
- Update admission, protocol/identity, producers, readers, fixtures, signing and
  documentation together if the investigation warrants a public feature. Start
  with one bounded scheduled issuance, not branches or a general dependency
  engine. Keep current pre-worker issuance as the default unless evidence
  justifies changing it.

## Decision carried forward

Keep the current implementation for this completed plan. Revisit timed issuance
only with a discriminating experiment and an explicit evidence contract; 0.3.1
is a possible destination. The separate discussion of `normalized_outcome: ok`
is settled: PW reports execution and native observations, while the caller owns
whether those facts satisfy the experiment's acceptance criteria. Timed issuance
would preserve that distinction.
