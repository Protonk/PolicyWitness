# RFC: PolicyWitness Lab (dev-only laboratory)

Status: Draft
Owner: PolicyWitness maintainers
Audience: repo contributors, maintainers, and internal tooling developers

## Summary

Create a dev-only "PolicyWitness Lab" surface that turns the repo into a first-class
experimentation environment while keeping the user-facing surface unchanged. The lab
starts with a signpost-focused debugging API and grows into a structured experiment
runner with deterministic evidence capture and artifact outputs.

This RFC proposes a phased rollout (1-4) so we can take stock between milestones and
iterate on the internal surface without expanding the user guide or the shipped UX.

## Motivation

PolicyWitness is a tool for runtime sandbox attribution. The hard problems are evidence
timing, correlation, and model correctness. Today, deterministic capture often requires
manual orchestration (session waits, FIFOs, log capture windows). This is correct, but it
is not ergonomic for repeated experimentation or regression work.

We want the repository itself to be a full-featured lab:

- deterministic evidence capture by default
- rich internal debugging data that does not leak into user-facing UX
- repeatable, structured experiment outputs
- fast iteration on probe instrumentation and evidence handling

## Goals

- Keep user-facing UX and documentation stable (PolicyWitness.md stays minimal).
- Provide a dev-only lab tool that can run and inspect experiments deterministically.
- Add a richer internal signpost API that is reliable and auditable.
- Standardize experiment outputs (lab artifacts) for debugging and regression use.
- Make evidence windows explicit and reproducible.

## Non-goals

- No new user-facing flags or guide changes for lab-only behavior.
- No additional notarized binaries or shipping code paths for end users.
- No attempt to be a general debugger UI.

## Principles

- Separation of surfaces: user vs dev is explicit and gated.
- Determinism over convenience: fences and evidence windows are the default in the lab.
- Evidence over return codes: delta-based results remain the primary truth.
- Small, composable tools: CLI + artifacts; viewers are optional.
- One runtime, two sinks: lab streams mirror the same signpost API as Unified Logging.
- Fence semantics anchor on existing `xpc session` lifecycle events, not a new protocol.

## Proposed architecture

### 1) Dev tool: `pw-lab` (not shipped)

Location: `tools/pwlab/` (Rust or Python; pick the smallest surface).

Commands (initial):

- `pw-lab run <scenario>`: run a fenced experiment with auto-capture and artifacts
- `pw-lab batch <suite>`: run a matrix of scenarios
- `pw-lab inspect <run-dir>`: summarize evidence and key deltas
- `pw-lab diff <runA> <runB>`: compare evidence windows and witness deltas
- `pw-lab timeline <run-dir>`: render signpost spans
- `pw-lab signposts catalog`: validate and list signpost spans

Gating:

- Enabled only when `PW_LAB=1` and the build is lab-enabled (compile-time flag or
  embedded lab marker). Release artifacts ignore `PW_LAB`.
- Not documented in the user guide.

### 2) Lab artifact contract ("labbook")

Each run produces a structured, predictable artifact directory:

- `run.json` (raw PolicyWitness output)
- `signposts.json` (parsed spans; derived from `run.json` or lab stream)
- `sandbox_logs.json` (parsed denies + metadata; derived view)
- `lab_summary.json` (derived conclusions, deltas, uncertainty, `labbook_version`)
- `env.json` (OS build, commit/build id, profile+variant, service bundle id,
  correlation id, build flags, PW binary path)
- `cmd.txt` (invocation and environment)

Paths:

- `.pw_lab/out/<timestamp>_<scenario>/`

Contract notes:

- `run.json` is the single source of truth.
- Derived files (`signposts.json`, `sandbox_logs.json`) must be reproducible from
  `run.json` and the lab stream, and should not diverge in meaning.

### 3) Signpost Lab v1 (dev-only)

Add a deterministic, structured signpost stream in dev mode:

- When `PW_LAB=1`, the service emits structured signpost events to the session
  stream (e.g., `kind: signpost_event`) in addition to Unified Logging signposts.
- The stream must be emitted by the same signpost calls that back Unified Logging
  to avoid drift between lab and shipped behavior.
- This avoids log access issues and ensures span capture is deterministic in the lab.

Add a signpost catalog:

- Canonical catalog in `xpc/signpost_catalog.json` (generated Swift wrapper if needed).
- Each entry: `name`, `category`, `process`, `description`, `ordering` (if any)

Add a timeline renderer:

- `pw-lab timeline` prints an ASCII timeline or produces a small HTML artifact.

### 4) Fenced runs by default in the lab

All `pw-lab run` commands:

- open session
- wait barrier (fence) using `xpc session --wait` and the existing lifecycle events
  (`wait_ready` / `trigger_received`, `probe_starting` / `probe_done`)
- arm collectors (sandbox logs, signposts)
- release fence
- run probe(s)
- stop collectors

The lab summary always includes:

- `evidence_window` (start/end)
- `collector_health` (armed vs unhealthy)
- `window_source` (fence vs explicit vs default)

### 5) Scenario and suite specs

Scenario spec format (YAML):

```
id: signpost_fence_basic
profile: minimal
steps:
  - probe: fs_op
    argv: ["--op", "open_read", "--path", "/path"]
expect:
  evidence:
    - signposts: ["pw.fence.waiting", "pw.probe.exec"]
    - sandbox_logs: { observed_deny: false }
```

Locations:

- `experiments/scenarios/`
- `experiments/suites/`

## Phased rollout

### Phase 1: Signpost Lab

Deliverables:

- Dev-only signpost event stream (session JSONL) that mirrors the Unified Logging
  signpost API (same emission sites)
- Signpost catalog
- `pw-lab signposts catalog` and `pw-lab timeline`

Tests:

- Catalog validation (catalog spans present in at least one run)
- Timeline formatter sanity

Implementation notes (Phase 1):

- `xpc/ProbeServiceSessionHost.swift`: add a lab-only signpost stream (`kind: signpost_event`)
  emitted from the same call sites that emit Unified Logging signposts.
- `xpc/signpost_catalog.json`: add canonical signpost catalog; generate a small Swift
  wrapper if needed.
- `tools/pwlab/` (new): implement `pw-lab signposts catalog` and `pw-lab timeline`
  to consume the lab signpost stream and the catalog.
- `xpc/BuildConfig.swift` (or similar): introduce a compile-time lab-enabled flag
  and gate `PW_LAB=1` on it.

### Phase 2: Lab core

Deliverables:

- `pw-lab run|batch|inspect|diff`
- Labbook artifact outputs
- Scenario spec parsing (YAML)
- Fenced runs default in lab using `xpc session` lifecycle events

Tests:

- Scenario runner validation
- Artifact schema tests (keys and paths)

### Phase 3: Evidence fusion

Deliverables:

- Cross-evidence correlation in `lab_summary.json`
- Explicit uncertainty categories (collector health, window source, confidence)
- Regression archetypes (Q1-Q8 style)

Tests:

- Evidence window correctness
- Uncertainty classification rules

### Phase 4: Power tools

Deliverables:

- Timeline viewer improvements (TUI or HTML)
- Experiment replay with deterministic inputs
- Automated "delta alarms" for key witness changes

Tests:

- Stable diff output for repeated runs
- Playback consistency checks

## Impact on user-facing surface

None. The lab is gated by `PW_LAB=1` and/or dev build flags, and it is documented in
dev-facing docs only (not PolicyWitness.md). Release builds ignore lab gating.

## Risks and mitigations

- Risk: dev-only paths creep into user UX.
  - Mitigation: compile-time lab enablement plus env var gate; no user guide mentions.
- Risk: signpost event stream increases complexity in service code.
  - Mitigation: compile-time or env-gated emission; minimal serialization; single
    signpost API for all sinks to avoid divergence.
- Risk: labbook schema drift.
  - Mitigation: add schema tests and version tag in `lab_summary.json`.

## Open questions

- Should `pw-lab` be Rust or Python? (Rust aligns with runner but Python is faster to iterate.)
- Preferred format for timeline output: ASCII vs HTML.
- Where to store catalog: Swift source vs JSON file.
- Should the lab tool live under `tools/` or `experiments/`?

## Success criteria

- A contributor can run a fenced, deterministic experiment and get a complete
  labbook in one command.
- Signpost evidence is reliable without Unified Logging access.
- User-facing UX and documentation remain unchanged.
- A lab run can prove collectors were armed before the sensitive operation ran.
