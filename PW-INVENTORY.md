# PolicyWitness Inventory (specimen-first, evidence-first)

This is an internal “lab notebook” for PolicyWitness itself: what the product claims to measure, where the real authority boundaries are, and which artifacts are considered evidence.

It is not a user guide (that is `PolicyWitness.md`). This document exists so contributors and agents can stay honest about attribution: when something looks like “a deny”, is it a seatbelt/App Sandbox deny, a non-sandbox gate, or an environment constraint (like running inside another sandbox)?

The headline change vs the legacy design: PolicyWitness is now **specimen-first**. Sandbox variation is delivered at runtime as SBPL text or compiled profile bytes plus a probe plan. There is one runner service (`PWRunner.xpc`), launched fresh per specimen, that self-applies the policy once and exits.

## Executive summary

- **Unit of policy:** one runner process instance, one sandbox profile applied once; a new specimen always means a new runner instance.
- **Unit of evidence:** one JSON envelope printed to stdout by `policy-witness run` (runner result + best-effort external evidence capture).
- **Attribution discipline:** permission-shaped failures are treated as ambiguous unless PolicyWitness can attach supporting evidence (deny side-effect + log correlation + `sandbox_check` agreement).
- **Environment hazards are first-class:** some automation harnesses run commands inside an OS sandbox; in that context, XPC lookup and unified-log access can be blocked before any runner code executes.

## 1) What is the unit of policy?

This section answers: “what thing is actually being sandboxed?”

- **Process-scoped and one-way:** the macOS sandbox profile applies to a process; it is not dynamically switched. PolicyWitness enforces “one specimen per runner instance” so process-scoped state cannot bleed between specimens.
- **Runner is the witness boundary:** the runner starts unsandboxed, applies the specimen policy to itself (once), executes the plan, returns a structured result, and exits.
- **Controller is not the sandbox:** `policy-witness` orchestrates and records; it is expected to run unsandboxed so it can capture supporting evidence from outside the boundary.

## 2) Where does policy become concrete?

This section answers: “when does an abstract policy become a real enforcement decision?”

- A specimen policy becomes concrete when the runner applies it via libsandbox.
- The runner immediately records a post-apply “am I sandboxed?” confirmation (`sandbox_check` on self) as part of Channel D.
- For each probe step, the runner records both:
  - **D:** `sandbox_check(operation, filter, argument)` prediction, and
  - **A:** the attempted operation outcome (e.g. open/read/write, Mach lookup), including return code + errno/kr.

## 3) What are the authoritative inputs?

This section answers: “what changes a run’s meaning?”

The meaningful input surface is intentionally small and is fully specified by:

- **Specimen JSON** (policy + params + probe plan).
- **App identity** (the built `.app` binaries and embedded evidence manifest).
- **Caller context:** whether the controller is itself sandboxed by an external harness, which can block XPC lookup and log capture before the runner starts.

## 4) Evidence channels (A–D)

This section answers: “what counts as proof?”

Each specimen evaluation is designed to produce four channels:

- **A — Attempt outcome:** what the operation returned (rc/errno/kr), plus a normalized interpretation.
- **B — Deterministic deny side-effect:** if the specimen SBPL uses `send-signal`, the runner records the signal count delta per step (and total).
- **C — External log correlation:** unified-log sandbox reports captured by an unsandboxed observer (the controller launches `sandbox-log-observer`).
- **D — Policy query:** `sandbox_check` predictions (and a post-apply “I am sandboxed” check).

The key rule: **return codes are not evidence**. PolicyWitness treats the B/C/D channels as what make attribution honest.

## 5) Output JSON contract

This section answers: “where do I look first?”

`policy-witness run <request.json>` prints a single JSON envelope to stdout (the artifact). The high-signal fields are:

- `result.ok` / `result.normalized_outcome`: whether the runner executed successfully.
- `data.runner_result`: the runner’s structured JSON witness (policy hash, post-apply sandboxed flag, step results).
- `data.sandbox_log_capture`: best-effort unified-log capture output (or explicit “requested_unavailable” when it could not be collected).

## 6) Environment hazards (nested sandbox / automation harness)

This section answers: “did we ever reach sandboxed code?”

In some automation environments, the controller process itself runs under an OS sandbox. In that world:

- XPC lookup can be blocked before `PWRunner.xpc` launches (no runner PID exists).
- unified-log access can be restricted, which makes “no deny observed” meaningless.

If you are an agent in a sandboxed harness and need to validate behavior, the correct workflow is: **ask for approval/escalation, then re-run once outside the harness sandbox** to confirm the same run in a “normal Terminal world”.

## 7) What this document deliberately does not try to do

- It does not attempt deterministic replay; it documents the evidence surface needed for replay work.
- It does not promise unified-log collection will always succeed (that is environment-dependent).
- It does not enumerate legacy probes/profiles/services; those were removed to keep a single workflow.
