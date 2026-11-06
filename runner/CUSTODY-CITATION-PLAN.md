# Plan: cite assertions for the actor custody inventory

## Problem and intended result

The generated worker capability inventory in
[WORKER](../docs/WORKER.md#detailed-capability-inventory) describes the actor
authority apparatus in rows `a1`–`a6`, `s19`, `s20` and `s37` and relates them
through edges `W57`–`W61`. Every one of those rows and edges renders as
"Source only; no assertion cited": their entries in
[architecture.json](../docs/architecture.json) carry empty `checks` lists. The
declaration-era rows they replaced during the extension consolidation (see
`git log` for `docs/architecture.json`) cited scoped checks. The consolidation
migrated the resources but not the citations, although the controls that
establish these behaviors exist, are registered and pass in the default battery.

One acquired resource also lost its row. The host duplicates the authority
descriptor with `fcntl(F_DUPFD_CLOEXEC, 64)` in
[ActorSession](Sources/PWRunnerCore/ActorSession.swift), installs it as worker
fd 5 through a spawn file action, and closes the duplicate after spawn or
failure in `closeAuthorityDuplicate`. The reply records those three steps in
each host region's setup cells (`authority_duplicate`, `authority_spawn_dup2`,
`close_launch_duplicate`). The retired `s5` row described the equivalent
duplicate; nothing replaced it.

Intended result: each row and edge above cites the checks whose assertions
cover it, with scope text that says what the assertion establishes and where it
stops; the launch duplicate has a row and a `prepares` edge to `a2`; rows that
no assertion covers stay explicitly source-only.

## Why

The inventory is where a reader learns which resource claims are tested and
which rest on source reading alone. Rendering the custody apparatus as untested
while its controls run in every default battery under-reports existing
verification, and the missing duplicate row leaves one acquired descriptor out
of the resource account.

## Grounding

Read the assertions, not the case descriptions. Cite a check only where its
assertion observes the row's resource at the row's stated stage.

| Rows | Resource | Controls whose assertions to review |
| --- | --- | --- |
| `a1`, `W57` | host authority object, mapping and framing | `runner_unit/host_setup_controls` ([host_setup_controls.py](../tests/suites/runner_unit/host_setup_controls.py), independent descriptor/mapping cleanup receipts); `runner_c_worker_harness/authority_binding` ([authority_binding.c](../tests/fixtures/extension_controls/authority_binding.c), production binding and page-rounded maximum mapping) |
| `a2`, `s19`, `s20`, `a6`, `W61` | worker descriptor, mapping, symbols, core limit, setup trailer | `witness_contract/extension_boundaries` ([check_extension_boundaries.py](../tests/suites/witness_contract/check_extension_boundaries.py) `SETUP_FAILURES`/`check_setup_failure` with [control.c](../tests/fixtures/extension_controls/control.c): exact primary rc/errno, independent cleanup, per-symbol absence); `runner_c_worker_harness/terminal_erasure` ([check_terminal_erasure.py](../tests/suites/runner_c_worker_harness/check_terminal_erasure.py): zero policy-read/compile/apply calls on terminal refusal through `production_worker_main`) |
| `a3`, `a4`, `a5`, `W58`–`W60` | issued token, private custody, inbound delivery and settlement | `runner_c_worker_harness/authority_binding`; `runner_unit/actor_handoff_mutations` ([actor_handoff_mutations.py](../tests/suites/runner_unit/actor_handoff_mutations.py): equal settlement, source acknowledgement, early-erasure/alias/shared-answer mutations); `runner_c_worker_harness/terminal_erasure` ([terminal_control.c](../tests/fixtures/extension_controls/terminal_control.c): full-capacity settled-inbound erasure with host-owned outbound preserved) |
| `s37` | per-reference native handles | `runner_c_worker_harness/actor_operations` ([operation_control.c](../tests/fixtures/extension_controls/operation_control.c), [actor_operations.py](../tests/suites/runner_c_worker_harness/actor_operations.py): production dispatch through `run_attempt`, independent counts, body/dispatch mutants) |
| new duplicate row | host high launch duplicate of the authority descriptor | `runner_unit/host_setup_controls` and `runner_unit/launch_descriptor_controls` (requested dup2 destinations compared with child descriptor metadata; shared-object identity is not established by metadata) |

Citation shape: a `checks` entry needs `path`, `symbol`, `form` and, for
worker rows, nonempty `scope`; the symbol must resolve in the cited file and
name a registered test. The rules are in
[generate_architecture.py](../docs/generate_architecture.py) and the
[generator contracts](../tests/suites/source_drift/README.md#generator-contracts).
Only the manifest is edited; WORKER's table, DOT and SVG are regenerated.

Evidence on hand: [tests/RETAINED.json](../tests/RETAINED.json) pins
`runs/extension-consolidation-battery-01` (run `20261106T164139Z_90ea0f88`),
whose per-case artifacts hold passing observations for every default-selected
control above, and `runs/extension-consolidation-build-refusals-04`. Both are
gitignored and exist only in the local checkout. `actor_handoff_mutations` is
opt-in and absent from that battery; run it fresh if it is cited.

## Approach and limits

1. For each row and edge, add citations with one-sentence scope text naming
   what the assertion observes and its limit. Where no assertion covers the
   row, leave `checks` empty and keep the fact source-only.
2. Add the duplicate row: host owner, authority role, acquired before
   compilation by `F_DUPFD_CLOEXEC` from the region descriptor, held through
   spawn, released by the post-spawn close, reaching the worker as fd 5 which
   `prepare_authority` closes once after mapping. Add its `prepares` edge to `a2`.
3. Regenerate with `tests/lib/python.sh docs/generate_architecture.py`, review
   the rendered rows and figure in context, and keep the authored `Known gap:`
   paragraphs and their links aligned.

Out of scope: new tests, behavior changes, edits to the cited controls, and any
reinstated declaration-era wording. Do not loosen the generator to admit a
citation it rejects.

## Verification

- `tests/lib/python.sh docs/generate_architecture.py --check` and
  `tests/run.sh --suite source_drift` pass: freshness, citation resolution and
  the registered-test requirement.
- Review each new scope sentence against the cited assertion lines; a scope
  that cannot be stated without exceeding what the test asserts means the row
  stays source-only.

Reconsider the plan if a cited control is retired or renamed, or if an
assertion turns out to observe only its fixture path rather than the production
resource the row describes.
