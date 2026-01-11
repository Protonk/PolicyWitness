# PolicyWitness Lab (dev-only)

This directory contains dev-only tooling for lab experiments. It is not shipped
with the notarized `.app`, and it is not documented in the user guide.

## Build gating

Lab features require a lab-enabled build plus a runtime opt-in:

- Build: set `PW_LAB_BUILD=1` when invoking `build.sh` (adds `-D PW_LAB_ENABLED`).
- Run: set `PW_LAB=1` to enable lab-only streams (signpost JSONL).

Release builds ignore `PW_LAB`.

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

## Inputs

The lab signpost stream appears in `xpc session` JSONL when `PW_LAB=1` and
signposts are enabled for the session (`PW_ENABLE_SIGNPOSTS=1` or `--signposts`).
The stream uses the same emission sites
as Unified Logging signposts, and is intended as a deterministic, dev-only
timeline source.
