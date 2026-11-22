# Reader probes

These four read-only probes examined the technical accounts and their tests.
Each probe directory holds:

- `KEY.md`: the expected answers, written by the coordinator from source,
  contract rules and existing test expectations;
- `inputs/`: exactly what the readers were given.

The commit that adds a probe's key also adds its inputs, and precedes the
probe's run. Readers worked from a scratch copy of `inputs/`. They were told
not to open any other file and to list every file they opened. Raw answers
and the adjudication table are added after each run.

| Probe | View | Readers |
| --- | --- | --- |
| P1 | ten live run envelopes, plus `docs/RESPONSE.md` | three Sonnet, one Opus control |
| P2 | four contract excerpts, with constructed inputs | three Sonnet, one Opus control |
| P3 | one owner file per reader, and one named rule | eight Sonnet |
| P4 | six test or checker excerpts | three Sonnet, one Opus control |

The P1 envelopes were copied from local development runs
(`product-group-default`, and `controller-c-post-reservation` for E3). Those
runs are gitignored and subject to pruning, so these copies are the retained
form. Absolute paths inside the envelopes refer to the local checkout.

## How the readers ran

Each probe ran as one workflow of four or eight read-only agents, three of
them on 2026-11-20 at `2bcdfeb8`. Every reader was an `Explore` agent. That
built-in type does not receive the repository's `CLAUDE.md`, whose core ideas
state several interpretations P1 tests, such as the limited meaning of
`query_first` and the rule against sandbox-cause attribution. Ordinary agents
would have been primed with them.

Each probe directory adds:

- `answers.json`: the workflow journal's per-agent results;
- `ADJUDICATION.md`: grading against the key, and each lead's verdict and
  destination.

| Probe | Workflow run | Result in one line |
| --- | --- | --- |
| P1 | `wf_c2f2cf78-611` | All four readers kept every targeted limit; one Pass 4 entry (the `test_overrides` echo limit). |
| P2 | `wf_6cabb03c-a2f` | Three gaps, raised by every reader including the control, become Pass 4 entries (`query_mismatch` condition, bracket lists, no client on registry refusal). |
| P3 | `wf_61d89a2f-30c` | The three rules' restatements agree across owners; one rule has a single owner. |
| P4 | `wf_62eae7ce-94a` | One test name overclaims (T4, a build-input test repair); one key line corrected; one finding caused by the constrained view. |
