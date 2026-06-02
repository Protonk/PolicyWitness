# PolicyWitness.md refactor plan

A one-pass reorganization of `PolicyWitness.md` from a 944-line guide
where the central `## Run output (per step)` section carries 46% of
the total content into a structure where each H2 has one job. No new
prose is required for the structural part; the only optional content
work is trimming the case-work/never-tier rationale (called out in
"Optional in-pass cleanups" below).

## Context

`PolicyWitness.md` is the user-facing guide. By construction it
assumes the reader does NOT see `README.md`, `AGENTS.md`,
`QUESTIONS.md`, or any other repo-local docs. It has accumulated
detail through Phase 1 (sysctl_read), Phase 2 (augments + ABI v4 +
exec runtime), and the recent audit-fix passes
(unsupported_operation outcome, path-unresolved prediction gate).

Current top-level shape (line counts include subsections):

| H2 | Lines | Comment |
| --- | --- | --- |
| (intro) | 4 | Too thin |
| `## Choose your runner` | 18 | |
| `## Quick start` | 39 | |
| `## Specimen format` | 212 | Carries Policy + Augments + Probe plan |
| `## Run output (per step)` | **432** | 46% of the doc, three reader audiences land here |
| `## Debug-attach to the worker` | 18 | Orphaned between unrelated sections |
| `## External runners (BYOXPC)` | 169 | Self-contained, well-placed |
| `## Common flags` | 6 | Trivially small |
| `## Troubleshooting` | 45 | |
| **Total** | **944** | |

The biggest pain point is `## Run output (per step)`: it conflates
envelope shape, the normalized_outcome catalog, the per-step shape,
the filter-kinds catalog, the attempt-kinds catalog, the
deliberately-omitted-kinds rationale, the prediction-unavailable set,
and a `path_diagnostics` deep-dive. Three distinct reader questions
("what does my envelope look like?", "what kinds can I use?", "why
doesn't PW support X?") all hit the same blob.

## Goals

Each goal is tied to a specific structural change; if the change
doesn't deliver the goal during execution, that's a signal to stop
and reassess rather than push through.

1. **One H2 per reader question.** Split the 432-line Run output
   section so envelope-shape readers and catalog-reference readers
   land in different H2 sections.

2. **Reference material clusters as reference material.** The
   filter/attempt-kind catalogs are reference, not narrative; group
   them under one "What PolicyWitness understands" H2 so a reader
   looking up "is X supported?" has one place to skim.

3. **Operational recipes group as operational recipes.** Debug-attach,
   Common flags, and Troubleshooting all serve the reader who's
   *running* PW (vs writing specimens or interpreting output). Cluster
   them under one H2 so the reader who's stuck has one section to
   read.

4. **Discoverability where it's currently buried.** Promote Policy
   preflight from `####` (four-deep) to `###` (peer of Policy and
   Augments). Move `path_diagnostics` from the
   prediction-unavailable section (where it doesn't belong) into the
   per-step shape section (where it does).

5. **Orient the reader at the top.** A 944-line doc deserves a 3-4
   sentence intro that names what PW does, points at the FAQ and
   README for shorter material, and offers three reading paths (try
   it / write a specimen / interpret output). Add a short ToC.

## Non-goals (one-pass discipline)

Listed explicitly so the refactor doesn't grow into other things:

- **No new content.** All prose is moving, not rewriting (with the
  one exception below).
- **No wording polish for its own sake.** If the existing prose is
  clear in its current section, it stays clear in its new section.
- **No examples or copy-paste blocks added or removed** (they move
  with their parent sections).
- **No factual corrections.** If a reader review surfaces a factual
  error elsewhere, that's a separate pass.
- **No changes to envelope shape, attempt-kind contracts, augment
  semantics, or any user-visible behavior.** Documentation only.
- **No cross-repo edits** beyond fixing references that point at
  moved/renamed sections in this file (`runner/README.md`,
  `runner/augments/README.md`, `controller/README.md` — see Risks).

The one in-pass content exception is optional and called out below.

## Proposed structure (after)

```
# PolicyWitness User Guide

[3–4 sentence intro: what PW is, the specimen → run → envelope cycle,
 pointer to QUESTIONS.md for shorter answers and README.md for the
 high-level pitch, and "three reading paths" guidance.]

[Short ToC: 6 top-level destinations]

## Quick start
## Choose your runner

## Specimen format
  ### Top-level shape
  ### Policy
  ### Policy preflight                (was ####; promoted to ###)
  ### Augments
  ### Probe plan steps

## Output envelope                    (NEW H2; carved out of Run output)
  ### Shape and schema_version
  ### Top-level fields                (pid, runner_subprocess,
                                       validator_subprocess,
                                       policy_augmentation)
  ### Per-step shape                  (sandbox_check + attempt + drift)
  ### path_diagnostics                (moved from prediction-unavailable)
  ### normalized_outcome catalog

## What PolicyWitness understands     (NEW H2; carved out of Run output)
  ### Filter kinds the runner predicts
  ### Filter kinds where prediction is unavailable
  ### Attempt kinds the runner implements
  ### Attempt kinds PW deliberately does not implement

## Operating                          (NEW H2; clusters the small sections)
  ### Common flags
  ### Debug-attach to the worker
  ### Troubleshooting

## External runners (BYOXPC)          (unchanged)
  ### What you need
  ### Tested install path
  ### Install a BYOXPC runner
  ### Verify the runner
  ### Use the runner in a specimen
  ### List, validate, or remove runners
```

## Mechanical change list

Each row is a specific section move/relevel. "Source" is the current
heading and line range; "Destination" is its new home.

| # | Source (current) | Lines | Destination (new) | Change type |
| - | --- | --- | --- | --- |
| 1 | (intro, `# PolicyWitness User Guide` body) | 1–5 | Same H1, expanded body | Rewrite intro + add ToC |
| 2 | `## Choose your runner` | 6–22 | `## Choose your runner` | Move to follow Quick start (small) |
| 3 | `## Quick start` | 24–61 | `## Quick start` | Move to first H2 after intro/ToC |
| 4 | `## Specimen format` body | 63–89 | `## Specimen format` → `### Top-level shape` | Promote to its own H3 |
| 5 | `### Policy` body | 91–106 | `### Policy` | No change |
| 6 | `#### Policy preflight diagnostics` | 108–167 | `### Policy preflight` | Promote `####` → `###` |
| 7 | `### Augments` | 169–252 | `### Augments` | No change |
| 8 | `### Probe plan steps` | 254–273 | `### Probe plan steps` | No change |
| 9 | `## Run output (per step)` (preamble + top-level fields) | 275–404 | `## Output envelope` → `### Shape and schema_version` + `### Top-level fields` | Split + new H2 |
| 10 | (per-step shape paragraph + notes) | 406–476 | `## Output envelope` → `### Per-step shape` | Same H2 as above |
| 11 | `path_diagnostics` block (currently inside "Filter kinds where prediction is unavailable") | 661–700 | `## Output envelope` → `### path_diagnostics` | Move out of catalog section |
| 12 | normalized_outcome catalog (currently inline in Run output) | 339–395 | `## Output envelope` → `### normalized_outcome catalog` | Same H2 |
| 13 | `### Filter kinds the runner predicts` | 478–489 | `## What PolicyWitness understands` → same H3 | New H2 parent |
| 14 | `### Filter kinds where prediction is unavailable` (minus path_diagnostics block) | 617–660 | `## What PolicyWitness understands` → same H3 | New H2 parent |
| 15 | `### Attempt kinds the runner implements` | 491–562 | `## What PolicyWitness understands` → same H3 | New H2 parent |
| 16 | `### Attempt kinds PW deliberately does not implement` | 564–615 | `## What PolicyWitness understands` → same H3 | New H2 parent |
| 17 | `## Debug-attach to the worker` | 707–724 | `## Operating` → `### Debug-attach to the worker` | New H2 parent |
| 18 | `## Common flags` | 894–898 | `## Operating` → `### Common flags` | New H2 parent |
| 19 | `## Troubleshooting` | 900–944 | `## Operating` → `### Troubleshooting` | New H2 parent |
| 20 | `## External runners (BYOXPC)` and subsections | 725–893 | Unchanged in place | Move to end after Operating |

## Cross-references that need updating

Internal anchors in PolicyWitness.md:

- Line 402: `[Debug-attach to the worker](#debug-attach-to-the-worker)`
  — anchor moves from `#debug-attach-to-the-worker` to (likely)
  `#debug-attach-to-the-worker` again under the new `## Operating`
  H2. Markdown anchor is based on the H3 text, so the anchor is
  stable; verify after the move.
- Line 404: `[overrides]: AGENTS.md#testing-normalized_outcome-failure-paths-via-_test_overrides`
  — external anchor in AGENTS.md, unchanged.

External cross-references to PolicyWitness.md sections (these point
at section names, not anchors, so they survive heading moves as long
as we keep the section names intact):

- `runner/README.md:130` — "See PolicyWitness.md → Augments"
- `runner/augments/README.md:11` — "See PolicyWitness.md → Augments"
- `runner/augments/README.md:245` — "PolicyWitness.md → Augments should also list…"
- `controller/README.md:115` — "PolicyWitness.md → Augments"

All four point at "Augments" by name; the Augments section is moving
within Specimen format but keeping its heading text, so these stay
correct. No external edits needed unless we rename the section
(we're not).

## Risks during execution

1. **Section moves can leave dangling sentences.** Some sections have
   transition prose like "see the next section" or "as documented
   above." After moves, "next" and "above" may be wrong. Mitigation:
   grep for "above", "below", "previous", "next", "earlier", "later"
   in the diff and rewrite as named cross-references.

2. **Splitting `## Run output (per step)` will require deciding
   what's "envelope shape" vs "catalog" for each paragraph.** Some
   paragraphs (e.g., the discussion of `prediction_unavailable` rc
   sentinel) describe both — they document the per-step shape AND
   reference the catalog. Mitigation: when a paragraph straddles,
   keep it with the per-step shape (Output envelope) and add a
   forward reference to the catalog section.

3. **`normalized_outcome` catalog could go in either H2.** It
   currently lives inside `## Run output (per step)` describing
   envelope values, but a reader thinking of it as "what outcomes
   can PW produce" might expect it under "What PolicyWitness
   understands". Decision: put it in Output envelope because it's a
   per-run envelope field, not a per-step catalog. The H3 title is
   "normalized_outcome catalog" so a reader searching for "what does
   `runner_timeout` mean?" still finds it via ToC + search.

4. **The ToC must stay in sync with the structure.** If we add a ToC
   at the top and then re-level something in the same pass, the ToC
   will drift. Mitigation: add the ToC LAST after all moves are
   done.

5. **Section line counts in this plan are based on the current file
   state.** If anyone edits the file before the refactor lands, the
   line numbers will drift. Mitigation: re-grep for section headings
   at execution time rather than working from these line numbers
   verbatim.

## Validation (how we know the refactor is good)

After the refactor:

- **Three-question test.** Pick three questions a real reader might
  have — "what does `drift=null` mean?", "is there a network attempt
  kind?", "how do I attach lldb?" — and verify each one is findable
  via ToC + first-page-skim in under 30 seconds.
- **No new line-count growth.** Refactor is structural; total line
  count should change by <5% (intro + ToC addition net of removed
  duplicates and tighter cross-references). If it grows materially,
  prose has crept in.
- **No broken anchors.** `grep -rn "PolicyWitness.md#"` across the
  repo + `grep "#" PolicyWitness.md` internal anchors all resolve.
- **Cross-repo references still resolve.** Confirm the four
  references in runner/README.md, runner/augments/README.md, and
  controller/README.md point at sections that still exist with the
  same name.

## Post-edit fidelity audit and repair

This phase runs AFTER the one-pass reorganization and BEFORE calling
the refactor done. Its job is to catch the two failure modes a large
doc move invites: accidentally dropping load-bearing detail, and
inventing plausible-sounding detail that is not actually in the old
guide or the code.

1. **Keep a pre-edit baseline.** Before editing `PolicyWitness.md`,
   save the current file as the comparison source, for example:

   ```sh
   git show HEAD:PolicyWitness.md > /tmp/PolicyWitness.before.md
   ```

   If the refactor is happening on top of uncommitted guide edits,
   use `cp PolicyWitness.md /tmp/PolicyWitness.before.md` instead.

2. **Build a section coverage map.** After the refactor, walk the
   mechanical change list above and mark each old section as:
   `moved intact`, `moved with heading/anchor rewrite`, `compressed by
   approved optional cleanup`, or `intentionally removed`. The last
   category should normally be empty. If a section has no destination,
   repair by moving the missing text back into the closest new section.

3. **Classify factual changes in the diff.** Review
   `git diff --word-diff -- PolicyWitness.md` against the baseline and
   tag each non-move change as one of:

   - intro / ToC orientation;
   - heading or anchor repair;
   - transition wording caused by moved sections;
   - approved optional cleanup;
   - factual claim.

   Every factual claim must either already exist in
   `/tmp/PolicyWitness.before.md` or be verified against a repo source
   of truth. If it is not source-backed, delete it or rewrite it as a
   non-factual orientation sentence.

4. **Reconcile catalogs against code.** For the fields and enumerations
   most likely to hallucinate, compare the new guide against code/tests
   rather than memory:

   - `normalized_outcome`, attempt outcomes, sandbox-check outcomes,
     and schema fields: `runner/PWRunnerAPI.swift` and `tests/INDEX.md`;
   - filter-kind and prediction-unavailable claims:
     `runner/ProbeRunner.swift`, `runner/CWorkerOrchestrator.swift`,
     and `tests/suites/source_drift/check.py`;
   - attempt-kind behavior and exec sentinels:
     `runner/CWorker.swift`,
     `controller/tools/pw_probe_runner/pw_probe_runner.c`, and
     `tests/suites/runner_use_c_worker/run.sh`;
   - augment claims: `runner/augments/exec_baseline.sb`,
     `runner/augments/README.md`, `controller/src/augments.rs`, and the
     evidence-manifest generation in `tests/build-evidence.py`;
   - CLI flags and external-runner commands: `controller/src/main.rs`
     and `controller/README.md`.

   Repair rule: when the guide and code disagree, do not smooth over
   the mismatch. Either restore the old guide text if the refactor
   introduced the drift, or stop and file the factual correction as a
   separate non-refactor task.

5. **Run detail-preservation spot checks.** Answer these from the new
   guide only, then compare against the pre-edit guide and source files:

   - What exact fields appear in `data.policy_augmentation`, and when
     is it absent?
   - Which `(operation, filter_kind)` pairs are
     `prediction_unavailable`, and what rc / drift shape do they
     produce?
   - What are the exec attempt child sentinel values for spawn failure,
     helper non-zero exit, and child deadline expiry?
   - Which attempt kinds are implemented, unsupported, or deliberately
     never implemented?
   - What does `path_diagnostics` contain, and who produces it?
   - What does `exec_baseline` allow, and what override consequence does
     append-last SBPL create?

   If the new guide cannot answer a question the old guide answered,
   reinsert the missing detail. If it answers with a claim not present
   in the old guide or code, remove or verify the claim.

6. **Final repair pass.** After any repairs, rerun the existing
   validation checklist above, especially anchor checks and line-count
   growth. The fidelity audit is allowed to add back lost detail; if
   that pushes the line count over the target, prefer keeping accurate
   detail over meeting the sizing heuristic.

## Optional in-pass cleanups (decide before execution)

These are within scope but I'd like an explicit yes/no rather than
deciding mid-refactor.

1. **Compress the "Attempt kinds PW deliberately does not implement"
   section from 53 lines to ~20.** The corpus-survey rationale (627
   profiles, twelve kinds ranked against five gates) lives in
   `runner/augments/README.md` and the deeper history is in
   `ATTEMPT-KIND-PLAN.md`'s git history. The user-guide reader
   probably wants "PW supports these four kinds; everything else is
   `unsupported` per-step or extensible via exec; here's why
   network/signal/system are never supported." That's ~20 lines.
   The 53-line version reads as architectural justification more
   than user-guide reference.

   - **Recommendation:** compress.
   - **Risk:** loses the gate-by-gate rationale a thoughtful reader
     might want. Mitigation: leave a one-line "see runner/augments/
     README.md for the corpus survey + per-tier gate analysis."

2. **Convert the exec attempt's 5-bullet field list (`child_pid` /
   `child_exit_code` / `child_term_signal` / `stdout` / `stderr`) to
   a small table.** Same content, less visual weight, and the table
   format mirrors the existing per-step-shape table elsewhere.

   - **Recommendation:** convert.
   - **Risk:** tables can be harder to read in narrow terminals or
     plaintext viewers. Mitigation: keep the surrounding prose
     describing semantics; the table just holds the field names +
     types + sentinel values.

3. **Trim `## Choose your runner`'s opening if it duplicates Quick
   start.** Some readers see Quick start first and Choose-your-runner
   afterward; if the latter starts by re-explaining what's already
   established, trim.

   - **Recommendation:** verify during execution; only trim if
     duplication is genuine.

## Sizing

- Structural moves (items 1–20 above): ~60 minutes of careful
  cut/paste with grep checks.
- Intro + ToC + cross-reference fixups: ~15 minutes.
- Optional cleanups (if accepted): +20 minutes for the
  compress-deliberately-not-supported pass, +10 minutes for the
  table conversion.

Total: 75–105 minutes of focused work.

## What we hope to gain, recapped

- A reader asking "what does my envelope look like?" lands in one
  H2 that answers it and nothing else.
- A reader asking "is network supported?" lands in a catalog H2 that
  answers it once, with rationale.
- A reader asking "how do I debug a hung run?" lands in an Operating
  H2 with three subsections all relevant to that question.
- A new reader landing on the doc gets a 3-4 sentence orientation
  and a ToC that names the six places they might want to go.
- The user-facing guide retains its "this is the only doc the end
  user sees" property — nothing moves out, only into better homes.
