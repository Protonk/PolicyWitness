# PolicyWitness Lab (dev-only)

This directory contains dev-only tooling for lab experiments. It is not shipped
with the notarized `.app`, and it is not documented in the user guide.

The **labbook** (run directory) is the primary artifact for dev analysis. Treat
`lab_summary.json` as the canonical evidence surface; other files are raw or
derived views.

## Build gating

Lab features require a lab-enabled build plus a runtime opt-in:

- Build: set `PW_LAB_BUILD=1` when invoking `build.sh` (adds `-D PW_LAB_ENABLED`).
- Run: set `PW_LAB=1` to enable lab-only streams (signpost JSONL).

Release builds ignore `PW_LAB`.

## Preflight: `inside` (sandboxed harness detection)

In some automation harnesses, the *caller* is already sandboxed by the host.
In that situation, XPC service lookup can fail at the bootstrap boundary
(`error 159: Sandbox restriction`) before any service code runs, and unified-log
based evidence capture may also be blocked.

The lab tool provides a fail-closed preflight called `inside`:

```
tools/pwlab/pw-lab inside --pw PolicyWitness.app/Contents/MacOS/policy-witness --profile minimal
```

- If any sensor indicates the caller is sandboxed (or a sensor is unavailable),
  `inside=true` is emitted and the tool exits immediately.
- Only if all sensors pass does it emit `inside=false`.

By default, `pw-lab run` / `pw-lab batch` perform this preflight before starting
the scenario. If `inside=true`, the run is recorded as `status=blocked` and the
tool exits non-zero so agents can request escalation / rerun outside the harness.

Internal override (dev-only): set `PW_LAB_ALLOW_INSIDE=1` to bypass the preflight.
This is intentionally not user-facing; prefer rerunning outside the harness.

## Default diagnostic sweep (RunKey → capsules → replay)

When debugging drift/flakiness, the recommended workflow is:

1. **Run the fixed sweep** to produce a set of per-run capsule directories
   keyed by a stable `RunKey` hash (the directory name is the `run_id`).
2. **Replay an individual capsule N times** and compare outcomes via witness
   digests (strict/relaxed) instead of eyeballing raw JSON.

Run the sweep:

```
tools/pwlab/pw-lab sweep --pw PolicyWitness.app/Contents/MacOS/policy-witness --runs-root .pw_lab/runs --force
```

- The sweep writes `.pw_lab/runs/sweep_index.json` (authoritative index), plus
  one run directory per `run_id`.
- Each run directory contains `capsule.json`, `env.snapshot`, `process.txt`,
  `host.txt`, `evidence/…`, and raw outputs under `outputs/`.

Replay a single capsule:

```
tools/pwlab/pw-lab replay -n 25 .pw_lab/runs/<run_id>
```

- Writes `replay_matrix.json` into the run directory.
- For `xpc_session` capsules, per-iteration artifacts are written under `replay_runs/iter_*/`.
- Classification is based on `(normalized_outcome, witness_digest_strict)`
  equivalence classes.
- The digest normalization intentionally ignores timestamps/PIDs and excludes
  evidence attachments (sandbox log excerpts, fence timing) so “stable” means
  “semantic witness stability”, not “identical clocks/logs”.

## Signpost lab tools

Print catalog:

```
tools/pwlab/pw-lab signposts catalog
```

Validate a session JSONL stream:

```
tools/pwlab/pw-lab signposts validate --input /path/to/session.jsonl
```

Render a timeline (session events + signposts by default):

```
tools/pwlab/pw-lab timeline --input /path/to/session.jsonl
```

If you want only signpost spans:

```
tools/pwlab/pw-lab timeline --input /path/to/session.jsonl --signposts-only
```

## Scenario runner

Run a scenario:

```
tools/pwlab/pw-lab run pw_lab_signpost_fence
```

Optional sandbox deny capture:

```
tools/pwlab/pw-lab run pw_lab_signpost_fence --capture-sandbox-logs
```

Run a suite:

```
tools/pwlab/pw-lab batch pw_lab_basic
```

Inspect a run directory:

```
tools/pwlab/pw-lab inspect .pw_lab/out/20250110-101010_pw_lab_signpost_fence
```

Diff two run directories:

```
tools/pwlab/pw-lab diff run_a run_b
```

## Evidence ledger TUI

Render a minimal, non-timeline view of evidence per step:

```
tools/pwlab/pw-lab tui .pw_lab/out/20250110-101010_pw_lab_signpost_fence
```

Keys:

- `j`/`k` or arrows: move row
- `tab` / `shift+tab`: move field
- `y`: copy the active cell via `pbcopy`
- `q`: quit

## Scenario format (YAML or JSON)

Minimal XPC session scenario:

```
id: pw_lab_signpost_fence
profile: minimal
steps:
  - probe: probe_catalog
    argv: []
```

Shell-driven scenario (wraps a script):

```
id: q1_dlopen_external
driver: shell
command:
  - bash
  - tests/suites/smoke/q1_dlopen_external.sh
```

Notes:

- YAML support is intentionally minimal (mappings/lists/scalars). Avoid block
  scalars (`|`/`>`) in lab scenario files.

## Labbook outputs

Each run directory includes:

- `plan.json` (resolved scenario plan)
- `run.json` (parsed run output)
- `run.jsonl` (raw session JSONL, if applicable)
- `run.stderr.txt` (stderr capture)
- `lab_summary.json` (evidence summary + uncertainty)
- `env.json` (host/build metadata)

Deterministic replay will consume a replay bundle derived from the labbook; the
draft schema lives in `RFC-PolicyWitness-Lab.md`.

## Inputs

The lab signpost stream appears in `xpc session` JSONL when `PW_LAB=1` and
signposts are enabled for the session (`PW_ENABLE_SIGNPOSTS=1` or `--signposts`).
The stream uses the same emission sites
as Unified Logging signposts, and is intended as a deterministic, dev-only
timeline source.
