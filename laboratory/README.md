# `laboratory/` (lab tooling: view and validate run directories)

This directory contains development tooling that is **not shipped** inside the notarized `.app`. It exists to make specimen runs easy to inspect and compare.

PolicyWitness is specimen-first. The shipped CLI (`policy-witness`) is responsible for creating run directories. `pw-lab` is primarily a viewer/validator.

## Preflight: “inside” (sandboxed harness detection)

Some automation harnesses run commands inside an OS sandbox. In that situation:

- XPC lookup can fail early (`NSCocoaErrorDomain` 4099 / error 159 `"Sandbox restriction"`).
- Unified Logging access can be restricted, making deny-evidence capture impossible from inside the harness.

Use the shipped preflight first:

```sh
PolicyWitness.app/Contents/MacOS/policy-witness inside --bare
```

If it prints `true`, rerun outside the harness (or with escalation) before debugging PolicyWitness itself.

`pw-lab` also provides a compatible preflight:

```sh
laboratory/pw-lab inside --pw PolicyWitness.app/Contents/MacOS/policy-witness
```

## Running a specimen (product path)

Run a specimen evaluation (canonical + instrumented SBPL `message` marker on deny):

```sh
PolicyWitness.app/Contents/MacOS/policy-witness specimen tests/fixtures/pw_runner/specimen_file_read_deny.json \
  --outdir .pw_lab/out/specimen_file_read_deny \
  --force
```

The output directory is the primary artifact. `lab_summary.json` is the canonical summary surface; other files are raw or derived views.

## Evidence ledger TUI

Render a minimal, aggressively boring, non-timeline view of a labbook run directory:

```sh
laboratory/pw-lab tui .pw_lab/out/specimen_file_read_deny
```

Keys:

- `1`/`2`/`3` (or `tab` / `shift+tab`): switch pages (Profile / Program / Results)
- Arrow keys / `j`/`k`: move row (vertical only; no horizontal scrolling)
- `PgUp` / `PgDn`, `Home` / `End`: page/jump
- `Enter`: open a wrapped detail view for the selected row
- `Esc`: return from detail view
- `y`: copy the selected row’s full value via `pbcopy`
- `q`: quit

## Signpost fixtures (optional)

This repo also carries a signpost event stream fixture and a small validator/renderer:

```sh
laboratory/pw-lab signposts validate --input tests/fixtures/pw_lab/signpost_stream.jsonl
laboratory/pw-lab timeline --input tests/fixtures/pw_lab/signpost_stream.jsonl
```
