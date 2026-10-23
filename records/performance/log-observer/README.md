# Log-observer pilot procedure

This standalone investigation harness leaves application sources and binaries
unchanged. `LOG-OBSERVER-INVESTIGATION-PLAN.md` in the parent directory owns the
questions, schedule, interpretation and limits. The existing runtime harness
supplies clock, identity, condition and cleanup helpers; its raw evidence is
never edited.

From the repository root, preparation inspects version, hashes, sources and
saved envelopes without a live specimen or unified-log query:

```sh
tests/lib/python.sh records/performance/log-observer/pilot.py prepare
tests/lib/python.sh records/performance/log-observer/pilot.py describe
tests/lib/python.sh records/performance/log-observer/check.py
```

`prepare` owns the generated `pilot-config.json`. `describe` prints the planned
44 entries. `check.py` runs stand-ins only, preserving all attempts under
`records/performance/runs/` and small control ledgers under `evidence/`. Its
whole-driver controls explicitly override executables and shorten delays or
ceilings; nominal preparation values remain in the copied configuration,
while the control note, invocation metadata and run deadline record overrides.

The live pilot is a separate action. Supply a truthful condition note at launch:

```sh
tests/lib/python.sh records/performance/log-observer/pilot.py run \
  --note 'Interactive pilot; agent active. Record current power and any known user/background activity here.'
```

No pre-created output or manual redirects are required. The procedure prints
its fresh raw directory and terminal status. The ceiling is three minutes with
cleanup included; expected duration remains to be measured. Ctrl-C retains
partial evidence and stops further work. Normal log/XPC execution may require
an unsandboxed shell. A refusal is evidence, not a successful empty capture;
follow repository diagnostic/escalation guidance rather than changing binaries.

After the procedure ends, export to a fresh directory outside raw output:

```sh
tests/lib/python.sh records/performance/log-observer/summarize.py \
  records/performance/runs/RUN_ID \
  --out records/performance/evidence/RUN_ID
```

The summary retains per-invocation outcomes, process/whole-capture spans,
actual delay observations, sequence-sensitive line hashes and duplicate counts.
It does not equate exit 0 with observer success, query success with retrieved
events, or retrieved events with completeness. Raw bytes are local-only,
gitignored and created with restricted access; summaries are not a portable copy
of the log records. Review derived evidence before committing it.

The completed two-pilot analysis is reproduced from local raw evidence with:

```sh
tests/lib/python.sh records/performance/log-observer/analyze.py
```

It independently recomputes timing spans, compares original bytes, checks
source/artifact identities and regenerates
`records/performance/evidence/log-observer-pilot-analysis.json`. It makes no live
query. The parent `LOG-OBSERVER-INVESTIGATION-REPORT.md` describes the results.
