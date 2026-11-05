# Stage 3 investigator working packet

Baseline: `lookback-ea64218b`, current commit `ea64218be2549fd034096f53ac23d79afac711ae`, compared with `990dc322f9278c6ad44f500fc8663b9419a60def`; actor integration plus both repairs. The coordinator rechecked the baseline hashes and HEAD before dispatch. Only review records are untracked; reviewed code, documents and inputs are unchanged.

## Preparation and sources

Read README.md, AGENTS.md, CONTRIBUTING.md planning guidance, docs/AGENTS.md, records/AGENTS.md and the neutral BASELINE.md in this review directory. Read the component AGENTS/README for code inspected and tests/AGENTS.md, tests/README.md and the owning suite/fixture reference for evidence inspected. Read DOC-LOOKBACK-PLAN.md stage3. You may inspect current implementation, contracts, fixtures, test assertions, generator inputs/owners, git history and retained observations. Use primary platform sources only if a claim requires them, and distinguish platform guarantees from bounded local observations. Do not rely on comments, manifests or resolving citations as behavioral proof.

Reports from stage2 are available under reports/: architecture-ledger.md, worker-ledger.md, limits-ledger.md/json, consistency-report.md and interaction records. Findings are provisional; investigate neutrally rather than proving a reader right. Do not redo the full line audit. Preserve observation/prediction/effect/attribution distinctions.

## Evidence and coordination

The current retained runs are tests/out/runs/actor-passes-default-02 and actor-passes-final-controls-02. These are gitignored and checkout-local. The first run's review/ has exact source and build snapshots; index source:null is not a baseline match. Inspect assertions and raw records as needed. Establish case/configuration, source/dependency/artifact applicability before crediting a historical result. A passing case proves only its asserted behavior in its recorded conditions. The coordinator is checking common snapshot/provenance and will share results; identify your claimed case dependency closure and any remaining doubt. Do not silently reuse evidence because a file name or version matches.

For this initial pass, no tests/builds/native trials, fixture mutations, external runner operations or source/document edits. Send the coordinator exact canonical case selectors and the claim a check would settle if new execution is necessary; include prerequisite/artifact/expected-observation and why retained evidence is insufficient. Coordinator owns the serialized execution queue. New checks, if required, will be authorized in an isolated investigative workspace; no speculative fix enters the reviewed state. Do not unlink checkout locks or alter retained runs.

The three inventory owners ground every assigned entry, including apparently sound entries. Check value/unit/derivation, counting/scope, enforcement/controls and consequence separately. Read actual boundary paths and assertion code. Mark source-inspected behavior, assertion-defined behavior and applicable observed execution distinctly; do not force an execution claim when evidence only supports source inspection. Shortened timeout controls do not verify production duration. Search changed paths independently for missing limits; M hypotheses are a starting list, not an exhaustive search or proof of omission.

## Return and record rules

Write only your explicitly assigned report artifacts in this investigations/ directory. No other files, no subagents. Use inert repository-relative paths for other review records (records inbound links only belong in associated PLAN files). Outward Markdown links must resolve from this directory, three levels below root. State when evidence is local/gitignored.

Return: exact finding/doc/generated IDs; checked claim versus implemented/observed behavior; source paths+symbols and assertions/case commands/evidence paths; evidence strength and limits; confirmed problem/unsupported concern/unresolved question with contrary evidence; plausible documentation/implementation/coordinated/retain/further-evidence remedies with consequences; actual edit owner/affected consumers and later validation. For all assigned limits return a structured per-entry assessment as well as concise readable findings. Include missing-limit search coverage and proposed additions or dismissed hypotheses. Every uncertainty must be bounded enough for coordinator dispatch/decision. Do not choose a remedy solely because it is a smaller patch.

Shared ownership: admission owns reachability/form/meaning and helper input bounds; timing owns clock/budget rules; evidence owns byte/record/region geometry, reply derivation and optional capture/fallback output; authority owns detailed transfer sequencing and resource/handle lifetime. Share cross-cutting facts with coordinator instead of duplicating an entire investigation. No current-behavior findings have yet been established by the review.
