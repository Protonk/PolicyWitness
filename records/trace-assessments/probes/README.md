# Reader probes

These are the read-only reader probes of `records/TRACE-ACCOUNTS-PLAN.md`.
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
