# Second coalescing pass

Pass 2 of [DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md) is complete
in `f9971216` and `8b4c63e4`, against the ownership map at `5511e9f0`.

The guide now qualifies retained actor rows by identity, launch-association and
action-membership findings. Reporting failure covers validation or encoding,
conditions outcome/exit on an admitted fallback, and connects exhausted writers
to the no-admitted-report account. Its catalog points to that explanation.
Rich/minimal retention and ordinary-versus-degraded checking remain local.

Two maintained restatements were removed: the full attribution paragraph under
`diagnostics.execution.reply_checks`, replaced by a structured `uses` reference
and short explanation; and CONTROLLER's separate completion conclusion, with
its link moved beside the computation. The canonical withholding definition,
rule trigger/effects/context, raw-record and stop-reason retention, tour mechanisms
and evidence limits remain. No generator, app interface or guide command changed.

Snapshot review found only the intended node's prose and `uses` change. Eight
dependent surfaces gain four shared nodes: `diagnostics.issue`, `.subject`,
`.subject.withholding_scope` and `.subject_path`. The existing closure follows
the target's ancestors and their references. No field shape, support owner,
free-text baseline or release history changed. Sol reviewed the guide/tour;
Astra reviewed the public dependency and scope. Both accepted; these reviews
provide source inspection, not new native execution evidence.

## Verification

Both selections used `tests/run.sh`, `PYTHONDONTWRITEBYTECODE=1`,
`PW_TEST_QUIET=1`, fresh `PW_TEST_OUT_DIR` directories and an unsandboxed shell.

| Run | Clean source | Selection and result |
| --- | --- | --- |
| `20261113T163808Z_f1af663c` (`doc-coalescing-pass2`) | `f9971216` | `--suite source_drift`: nine pass, one fail. `generator_contract` found an authored-source link to a generated-only anchor; its case exit also produced `suite_exit`. |
| `20261113T164607Z_f1b7f247` (`doc-coalescing-pass2-links`) | `8b4c63e4` | `--case source_drift/build_contracts --case source_drift/generator_contract`: both pass, no harness errors. |

The correction removes only inline link markup and reflows the same sentence
in the authored surface and regenerated CONTRACT/public snapshot. The structured
reference supplies the rendered link. The first run remains failed; the second
replaces its two affected case results. All selected cases completed, with zero
system sleep and no skips. Contract controls include history and source-copy
freshness; the generator controls include the corrected whole-document link check.

Retained first-run results are `source_drift/runner_source_manifests_agree`,
`source_drift/limits_documentation`, `source_drift/architecture_documentation`,
`source_drift/build_documentation`, `source_drift/markdown_reader`,
`source_drift/direct_python_start`, `source_drift/footprint_documentation` and
`source_drift/porcelain_codec`. Sol and the coordinator reviewed applicability:
the exact three-file correction changes no scanned commands, scalar spans,
copied regions, headings, manifest citations, schemas, scripts or fixtures used
by those cases. Broad document-inventory intersections are reviewed exceptions,
not fresh executions. Runtime code and guide command fences are unchanged, so
native and guide-workflow executions were not added.

The coordinator reviewed both run summaries, the failure diagnostic and replacement
receipts. Two disposable runs and no additional worktrees were created.
`make prune` preview and `make prune APPLY=1` removed both runs without blockers,
preserving the four release archives and protected acceptance. Their raw output
is no longer locally available; the observations above are development evidence.
The final plan/record-only update passed link-resolution and diff-format checks;
it changes no input to the public contract or guide.
